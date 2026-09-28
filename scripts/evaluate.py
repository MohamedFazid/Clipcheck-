import os
import sys
import json
import argparse

import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms
import timm
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    roc_auc_score, confusion_matrix, roc_curve, classification_report
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import (FRAMES_DIR, MODEL_RUNS_DIR, RUNS_DIR, SPLIT_SEED, PROJECT_ROOT,
                   run_paths, get_device, compute_eer, get_split,
                   _video_folder_of)

# ── Args ─────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description='Evaluate a trained video-branch model on the fixed test split.')
parser.add_argument('--seed', type=int, default=42,
                    help='Training seed of the model to evaluate (used to locate the '
                         'checkpoint and to name the output dir).')
parser.add_argument('--tag', type=str, default='',
                    help='Experiment tag, matching the one used for training. Keeps '
                         'variant results isolated from the reported baseline.')
parser.add_argument('--model', type=str, default=None,
                    help='Explicit path to a .pth checkpoint. Defaults to the '
                         'tag/seed-derived path.')
parser.add_argument('--arch', type=str, default=None,
                    help='timm model name. Defaults to the arch recorded in the run\'s '
                         'train_config.json, else efficientnet_b4.')
parser.add_argument('--no-plots', action='store_true',
                    help='Skip figure generation (faster for multi-seed sweeps).')
args = parser.parse_args()

_default_model, out_dir = run_paths(args.seed, args.tag)
MODEL_PATH = args.model or str(_default_model)
os.makedirs(out_dir, exist_ok=True)
_cfg = out_dir / 'train_config.json'
_cfgd = json.load(open(_cfg)) if _cfg.exists() else {}
ARCH = args.arch or _cfgd.get('arch') or 'efficientnet_b4'
FRAMES = (PROJECT_ROOT / _cfgd['frames_dir']) if _cfgd.get('frames_dir') else FRAMES_DIR

IMG_SIZE   = 224
BATCH_SIZE = 32

device = get_device()
print(f'Device: {device} | model: {MODEL_PATH} | split seed: {SPLIT_SEED}')

val_transforms = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

full_dataset = datasets.ImageFolder(str(FRAMES), transform=val_transforms)
class_names  = full_dataset.classes
print(f'Classes (index order): {class_names}')

# Same identity-disjoint split as training -> evaluating on the identical
# held-out test set, with no video (or paired identity) shared with train.
# See utils.grouped_video_split for why this replaced a frame-level split.
FOLD = _cfgd.get('fold')
_, _, test_idx = get_split(full_dataset, str(FRAMES), split_seed=SPLIT_SEED, fold=FOLD)
test_set = Subset(full_dataset, list(test_idx))
test_video_folders = [_video_folder_of(full_dataset.samples[i][0]) for i in test_idx]
n_test_videos = len(set(test_video_folders))
print(f'Test set size: {len(test_set)} crops from {n_test_videos} distinct videos')

test_loader = DataLoader(test_set, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

model = timm.create_model(ARCH, pretrained=False, num_classes=2)
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model = model.to(device)
model.eval()
print('Model loaded.')

all_labels, all_preds, all_probs = [], [], []
with torch.no_grad():
    for images, labels in test_loader:
        images  = images.to(device)
        outputs = model(images)
        probs   = torch.softmax(outputs, dim=1)[:, 0]  # P(fake), index 0
        preds   = outputs.argmax(dim=1)
        all_labels.extend(labels.numpy())
        all_preds.extend(preds.cpu().numpy())
        all_probs.extend(probs.cpu().numpy())

all_labels = np.array(all_labels)
all_preds  = np.array(all_preds)
all_probs  = np.array(all_probs)

acc       = accuracy_score(all_labels, all_preds)
f1        = f1_score(all_labels, all_preds, pos_label=0)
precision = precision_score(all_labels, all_preds, pos_label=0)
recall    = recall_score(all_labels, all_preds, pos_label=0)
auc       = roc_auc_score(all_labels, 1 - all_probs)  # flip: higher = more real
cm        = confusion_matrix(all_labels, all_preds)
# EER on the fake-positive scores (FAR = FRR); threshold-free operating point.
y_true_fake = (all_labels == 0).astype(int)
eer, eer_thr = compute_eer(y_true_fake, all_probs)

# ── Video-level aggregation ──────────────────────────────────────────────────
# Frame-level metrics above treat ~19 correlated crops per video as
# independent samples (pseudo-replication), and are not what the deployed
# system reports: server.py/video_infer.py aggregate per-frame P(video_fake)
# into ONE score per clip. Re-aggregating here evaluates the same unit the
# app actually outputs, on an honest ~n_test_videos independent test cases
# rather than an inflated crop count.
video_true, video_prob = {}, {}
for lbl, prob, vf in zip(all_labels, all_probs, test_video_folders):
    video_true.setdefault(vf, lbl)
    video_prob.setdefault(vf, []).append(prob)
video_ids = sorted(video_prob)
v_labels = np.array([video_true[v] for v in video_ids])
v_probs = np.array([np.mean(video_prob[v]) for v in video_ids])  # mean P(fake)
v_preds = (v_probs < 0.5).astype(int)  # index 0=fake: predict fake if P(fake)>=0.5

v_acc = accuracy_score(v_labels, v_preds)
v_f1 = f1_score(v_labels, v_preds, pos_label=0)
v_precision = precision_score(v_labels, v_preds, pos_label=0)
v_recall = recall_score(v_labels, v_preds, pos_label=0)
v_auc = roc_auc_score(v_labels, 1 - v_probs)
v_eer, v_eer_thr = compute_eer((v_labels == 0).astype(int), v_probs)

metrics = {
    'seed': args.seed,
    'tag': args.tag,
    'arch': ARCH,
    'frames_dir': os.path.relpath(FRAMES, PROJECT_ROOT),
    'fold': FOLD,
    'model_path': os.path.relpath(MODEL_PATH, PROJECT_ROOT),
    'test_crops': int(len(test_set)),
    'n_test_videos': int(len(video_ids)),
    'f1': float(f1),
    'auc_roc': float(auc),
    'eer': float(eer),
    'eer_threshold': float(eer_thr),
    'precision': float(precision),
    'recall': float(recall),
    'accuracy': float(acc),
    'confusion_matrix': cm.tolist(),
    'class_names': class_names,
    'video_level': {
        'note': 'Per-video mean-aggregated P(fake), matching what the deployed '
                'pipeline reports (one score per clip), evaluated on '
                f'{len(video_ids)} independent held-out videos rather than '
                f'{len(test_set)} correlated frame crops.',
        'n_videos': int(len(video_ids)),
        'accuracy': float(v_acc),
        'f1': float(v_f1),
        'precision': float(v_precision),
        'recall': float(v_recall),
        'auc_roc': float(v_auc),
        'eer': float(v_eer),
        'eer_threshold': float(v_eer_thr),
    },
}

print('\n── Evaluation Results — VIDEO level (primary: matches app output) ───')
print(f'N videos  : {len(video_ids)}')
print(f'Accuracy  : {v_acc:.4f}')
print(f'F1 Score  : {v_f1:.4f}')
print(f'AUC-ROC   : {v_auc:.4f}')
print(f'EER       : {v_eer:.4f}  (@thr {v_eer_thr:.3f})')
print(f'Precision : {v_precision:.4f}')
print(f'Recall    : {v_recall:.4f}')

print('\n── Evaluation Results — FRAME level (secondary, pseudo-replicated) ──')
print(f'F1 Score  : {f1:.4f}')
print(f'AUC-ROC   : {auc:.4f}')
print(f'EER       : {eer:.4f}  (@thr {eer_thr:.3f})')
print(f'Precision : {precision:.4f}')
print(f'Recall    : {recall:.4f}')
print(f'Accuracy  : {acc:.4f}  (secondary)')
print(f'\nConfusion Matrix (rows=actual, cols=predicted): {class_names}')
print(cm)
print('\nFull classification report:')
print(classification_report(all_labels, all_preds, target_names=class_names))

with open(out_dir / 'metrics.json', 'w') as f:
    json.dump(metrics, f, indent=2)

# One row per held-out video (mean P(fake) over its crops): lets cross-validation folds be pooled out-of-fold and
# bootstrapped over identity groups (scripts/aggregate_cv.py). class_names[0] is 'fake'.
with open(out_dir / 'per_video_predictions.json', 'w') as f:
    json.dump([{'video': f'{"fake" if video_true[v] == 0 else "real"}/{v}', 'is_fake': int(video_true[v] == 0),
                'p_fake': float(np.mean(video_prob[v])), 'n_crops': len(video_prob[v])} for v in video_ids], f, indent=1)
print(f'Metrics saved: {out_dir / "metrics.json"}')

if not args.no_plots:
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=class_names, yticklabels=class_names, ax=ax)
    ax.set_xlabel('Predicted'); ax.set_ylabel('Actual')
    ax.set_title(f'Confusion Matrix (seed {args.seed}, acc {acc:.4f})')
    plt.tight_layout()
    plt.savefig(out_dir / 'confusion_matrix.png', dpi=150)
    plt.close()

    fpr, tpr, _ = roc_curve(all_labels, 1 - all_probs)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, color='steelblue', lw=2, label=f'AUC = {auc:.4f}')
    ax.plot([0, 1], [0, 1], 'k--', lw=1)
    ax.set_xlabel('False Positive Rate'); ax.set_ylabel('True Positive Rate')
    ax.set_title(f'ROC Curve (seed {args.seed})')
    ax.legend(loc='lower right')
    plt.tight_layout()
    plt.savefig(out_dir / 'roc_curve.png', dpi=150)
    plt.close()
    print(f'Figures saved to {out_dir}')

print('\nDone.')
