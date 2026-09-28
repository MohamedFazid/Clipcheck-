"""Per-method detection (Deepfakes, FaceSwap, NeuralTextures) on test-split identities only; n = 22 fake + 22 real per method.

    python scripts/eval_cross_method.py --tags aug_vidsplit"""
import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import torch
import timm
from PIL import Image
from sklearn.metrics import roc_auc_score
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import PROJECT_ROOT, RUNS_DIR, MODEL_RUNS_DIR, SPLIT_SEED, get_device, compute_eer  # noqa: E402

METHODS = ['Deepfakes', 'FaceSwap', 'NeuralTextures']
MANIFEST = PROJECT_ROOT / 'data_splits' / 'split_v2_identity_grouped.json'
OUT_ROOT = PROJECT_ROOT / 'results' / 'cross_method'

TF = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(),
                         transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])


class Crops(Dataset):
    def __init__(self, items):
        self.items = items

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        return TF(Image.open(self.items[i]).convert('RGB'))


def crops_of(folder: Path):
    return sorted(folder.glob('*.jpg'))


def test_videos():
    assign = json.load(open(MANIFEST))['assignment']
    real = sorted(k.split('/', 1)[1] for k, v in assign.items() if k.startswith('real/') and v == 'test')
    fake = sorted(k.split('/', 1)[1] for k, v in assign.items() if k.startswith('fake/') and v == 'test')
    return real, fake


def folder_for(method, pair):
    if method == 'Deepfakes':
        return PROJECT_ROOT / 'frames' / 'fake' / pair
    return PROJECT_ROOT / 'frames_methods' / method / pair


@torch.no_grad()
def score_folders(model, device, folders):
    """Return {folder_name: array of P(fake) per crop}."""
    items, owner = [], []
    for f in folders:
        cs = crops_of(f)
        items += cs
        owner += [f.name] * len(cs)
    probs = []
    for x in DataLoader(Crops(items), batch_size=32, shuffle=False, num_workers=0):
        probs.append(torch.softmax(model(x.to(device)), dim=1)[:, 0].cpu().numpy())  # index 0 = fake
    probs = np.concatenate(probs)
    out = {}
    for name, p in zip(owner, probs):
        out.setdefault(name, []).append(float(p))
    return {k: np.array(v) for k, v in out.items()}


def clip_metrics(real_scores, fake_scores):
    r = np.array([s.mean() for s in real_scores.values()])
    f = np.array([s.mean() for s in fake_scores.values()])
    y = np.r_[np.zeros(len(r)), np.ones(len(f))]
    p = np.r_[r, f]
    eer, _ = compute_eer(y, p)
    return {
        'n_real_videos': int(len(r)), 'n_fake_videos': int(len(f)),
        'auc_roc': float(roc_auc_score(y, p)), 'eer': float(eer),
        'accuracy': float(((p >= 0.5) == (y == 1)).mean()),
        'fake_detection_rate': float((f >= 0.5).mean()), 'real_specificity': float((r < 0.5).mean()),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tags', nargs='+', required=True, help='Run tags, e.g. aug_vidsplit b0_vidsplit')
    ap.add_argument('--seeds', nargs='+', type=int, default=[42, 43, 44])
    args = ap.parse_args()

    device = get_device()
    real_ids, fake_ids = test_videos()
    for m in METHODS[1:]:
        if not (PROJECT_ROOT / 'frames_methods' / m).exists():
            sys.exit(f'missing frames_methods/{m}: run extract_frames.py --fake-method {m} --fake-only --only-split test --out-root frames_methods/{m} (app env)')

    for tag in args.tags:
        per_seed = {}
        multi = False                       # set from the run's train_config (frames_dir contains 'multi')
        for seed in args.seeds:
            cfg_p = RUNS_DIR / tag / f'seed{seed}' / 'train_config.json'
            ckpt = MODEL_RUNS_DIR / tag / f'seed{seed}.pth'
            if not ckpt.exists():
                print(f'skip {tag} seed{seed}: no checkpoint'); continue
            cfg = json.load(open(cfg_p)) if cfg_p.exists() else {}
            arch = cfg.get('arch') or 'efficientnet_b4'
            multi = 'multi' in str(cfg.get('frames_dir', ''))
            model = timm.create_model(arch, pretrained=False, num_classes=2)
            model.load_state_dict(torch.load(ckpt, map_location=device))
            model.to(device).eval()

            real = score_folders(model, device, [PROJECT_ROOT / 'frames' / 'real' / r for r in real_ids])
            res = {'arch': arch}
            for m in METHODS:
                fake = score_folders(model, device, [folder_for(m, p) for p in fake_ids])
                res[m] = clip_metrics(real, fake)
            per_seed[seed] = res
            print(tag, f'seed{seed}', ' | '.join(f"{m}: AUC {res[m]['auc_roc']:.3f} fake-rate {res[m]['fake_detection_rate']:.2f}"
                                                for m in METHODS))
        if not per_seed:
            continue

        summary = {'tag': tag, 'seeds': sorted(per_seed), 'split_manifest': MANIFEST.name,
                   'trained_on_all_three_methods': multi,
                   'note': ('Trained on Deepfakes + FaceSwap + NeuralTextures (one method per identity pair); tested on '
                            'test-split identities never seen in training. Not zero-shot.') if multi else
                           'Zero-shot: trained on Deepfakes only; FaceSwap and NeuralTextures are unseen; tested on test-split identities.',
                   'per_seed': per_seed, 'mean_std': {}}
        for m in METHODS:
            summary['mean_std'][m] = {}
            for k in ('auc_roc', 'eer', 'accuracy', 'fake_detection_rate', 'real_specificity'):
                v = np.array([per_seed[s][m][k] for s in per_seed])
                summary['mean_std'][m][k] = {'mean': float(v.mean()),
                                            'std': float(v.std(ddof=1)) if len(v) > 1 else 0.0}
        out = OUT_ROOT / tag
        out.mkdir(parents=True, exist_ok=True)
        json.dump(summary, open(out / 'cross_method.json', 'w'), indent=2)
        lines = [f'# Per-method detection: {tag}\n',
                 f'Seeds {summary["seeds"]}. ' + ('Trained on all three methods (one per identity pair); tested on '
                 'test-split identities unseen in training. NOT zero-shot. ' if multi else 'Trained on Deepfakes only. ')
                 + 'Test-split identities only (22 real + 22 fake videos per method; one video = 2.3 pp). Clip-level.\n',
                 '| Fake method | Role | AUC-ROC | EER | Accuracy | Fake detection rate | Real specificity |',
                 '|---|---|---|---|---|---|---|']
        for m in METHODS:
            ms = summary['mean_std'][m]
            f = lambda k: f"{ms[k]['mean']:.3f} ± {ms[k]['std']:.3f}"
            lines.append(f"| {m} | {('seen method, unseen identities' if multi else ('in-distribution' if m == 'Deepfakes' else 'UNSEEN method (zero-shot)'))} | "
                         f"{f('auc_roc')} | {f('eer')} | {f('accuracy')} | {f('fake_detection_rate')} | {f('real_specificity')} |")
        (out / 'cross_method.md').write_text('\n'.join(lines) + '\n')
        print('\n'.join(lines))


if __name__ == '__main__':
    main()
