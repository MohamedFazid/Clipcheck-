"""Zero-shot evaluation of the shipped video model on the Celeb-DF-v2 official test list (518 videos).

    python scripts/eval_celebdf.py --root ~/Downloads/Celeb-DF-v2 [--check | --max-videos 20]"""

import os
import sys
import json
import time
import argparse
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    roc_auc_score, confusion_matrix, roc_curve,
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import RESULTS_DIR, MODELS_DIR, PROJECT_ROOT, get_device, compute_eer
from video_infer import load_models, analyse_video_file

OUT_DIR = RESULTS_DIR / 'cross_dataset' / 'celebdf_v2'


def parse_test_list(root: Path):
    """Parse List_of_testing_videos.txt into (video_path, is_fake). Celeb-DF uses 1 = real; the flip to 1 = fake happens here only."""
    list_path = root / 'List_of_testing_videos.txt'
    if not list_path.exists():
        raise FileNotFoundError(
            f'Expected the official test list at {list_path}. '
            f'Is --root pointing at the extracted Celeb-DF-v2 folder '
            f'(the one containing Celeb-real/, Celeb-synthesis/, YouTube-real/)?'
        )
    entries = []
    with open(list_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            celebdf_label, rel_path = line.split(maxsplit=1)
            is_real = int(celebdf_label) == 1
            video_path = root / rel_path
            if not video_path.exists():
                raise FileNotFoundError(
                    f'Test list references {video_path}, which does not exist. '
                    f'The extracted dataset looks incomplete.'
                )
            entries.append((video_path, 0 if is_real else 1))
    return entries


def main():
    ap = argparse.ArgumentParser(description='Cross-dataset eval: FF++-trained video branch on Celeb-DF-v2.')
    ap.add_argument('--root', type=str, required=True,
                     help='Path to the extracted Celeb-DF-v2 folder (contains Celeb-real/, Celeb-synthesis/, YouTube-real/, List_of_testing_videos.txt).')
    ap.add_argument('--model', type=str, default=None,
                     help='Checkpoint to evaluate. Defaults to models/best_model.pth (the currently-served checkpoint).')
    ap.add_argument('--arch', type=str, default=None,
                     help='timm architecture of --model (default efficientnet_b4 for an explicit --model). '
                          'Ignored when --model is omitted: the shipped model uses models/shipped_model.json.')
    ap.add_argument('--out-name', type=str, default='celebdf_v2',
                     help='Output folder under results/cross_dataset/. Use a distinct name per model so a '
                          'new run never overwrites another model\'s result.')
    ap.add_argument('--max-videos', type=int, default=None,
                     help='Cap the number of test videos (sanity pass). Default: all 518.')
    ap.add_argument('--check', action='store_true',
                     help='Only parse and validate the test list + first video; no inference.')
    args = ap.parse_args()

    root = Path(args.root).expanduser().resolve()
    entries = parse_test_list(root)
    n_real = sum(1 for _, y in entries if y == 0)
    n_fake = sum(1 for _, y in entries if y == 1)
    print(f'Official Celeb-DF-v2 test split: {len(entries)} videos ({n_real} real, {n_fake} fake).')

    if args.check:
        sample_path, sample_label = entries[0]
        print(f'Layout OK. Sample entry: {sample_path.name} (label: {"fake" if sample_label else "real"}).')
        print('Not running inference (--check).')
        return

    if args.max_videos:
        entries = entries[:args.max_videos]
        print(f'Sanity pass: capped to first {len(entries)} videos.')

    model_path = args.model or str(MODELS_DIR / 'best_model.pth')
    device = get_device()
    print(f'Device: {device} | model: {model_path}')
    if args.model is None:
        mtcnn, model, _ = load_models(None)                      # shipped model, arch from shipped_model.json
    else:
        mtcnn, model, _ = load_models(model_path, arch=args.arch)
    arch_used = args.arch or ('shipped' if args.model is None else 'efficientnet_b4')

    results = []
    no_face_count = 0
    t0 = time.time()
    for i, (video_path, y_true) in enumerate(entries, 1):
        out = analyse_video_file(str(video_path), mtcnn, model, device, max_faces=20)
        if out is None:
            no_face_count += 1
            print(f'[{i}/{len(entries)}] {video_path.name}: no face detected, skipped.')
            continue
        results.append({
            'video': str(video_path.relative_to(root)),
            'y_true_fake': y_true,
            'p_fake': out['p_fake'],
            'n_faces': out['n_faces'],
        })
        elapsed = time.time() - t0
        avg = elapsed / i
        eta_min = avg * (len(entries) - i) / 60
        if i % 10 == 0 or i == len(entries):
            print(f'[{i}/{len(entries)}] avg {avg:.2f}s/clip, ETA {eta_min:.1f} min, '
                  f'last p_fake={out["p_fake"]:.3f} (true: {"fake" if y_true else "real"})')

    if not results:
        print('No videos produced a result (all skipped). Nothing to evaluate.')
        return

    y_true = np.array([r['y_true_fake'] for r in results])
    p_fake = np.array([r['p_fake'] for r in results])
    y_pred = (p_fake >= 0.5).astype(int)

    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, pos_label=1, zero_division=0)
    precision = precision_score(y_true, y_pred, pos_label=1, zero_division=0)
    recall = recall_score(y_true, y_pred, pos_label=1, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])

    # AUC/EER need both classes present; with --max-videos on a small/skewed
    # subset this can fail, so guard rather than crash a sanity pass.
    auc = eer = eer_thr = None
    if len(set(y_true.tolist())) == 2:
        auc = float(roc_auc_score(y_true, p_fake))
        eer, eer_thr = compute_eer(y_true, p_fake)

    metrics = {
        'dataset': 'Celeb-DF-v2',
        'split': 'official test list (List_of_testing_videos.txt)',
        'model_path': os.path.relpath(model_path, str(PROJECT_ROOT)) if os.path.isabs(model_path) else model_path,
        'arch': arch_used,
        'n_videos_evaluated': len(results),
        'n_videos_skipped_no_face': no_face_count,
        'n_real': int((y_true == 0).sum()),
        'n_fake': int((y_true == 1).sum()),
        'accuracy': float(acc),
        'f1': float(f1),
        'precision': float(precision),
        'recall': float(recall),
        'auc_roc': auc,
        'eer': eer,
        'eer_threshold': eer_thr,
        'confusion_matrix': cm.tolist(),
        'confusion_matrix_labels': ['real', 'fake'],
        'note': 'FF++-trained model, evaluated zero-shot (no retraining/fine-tuning) on Celeb-DF-v2. '
                'Literature (Khan and Dang-Nguyen, 2023) reports FF++-trained detectors typically fall '
                'to 70-75% accuracy on this dataset; compare against that range, not against the '
                '96%+ FF++ in-distribution figure.',
    }

    OUT_DIR = RESULTS_DIR / 'cross_dataset' / args.out_name
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / 'metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
    with open(OUT_DIR / 'per_video_predictions.json', 'w') as f:
        json.dump(results, f, indent=2)

    print('\n── Celeb-DF-v2 cross-dataset results ──')
    print(f'Videos evaluated : {len(results)} ({no_face_count} skipped, no face detected)')
    print(f'Accuracy         : {acc:.4f}')
    print(f'F1               : {f1:.4f}')
    print(f'Precision        : {precision:.4f}')
    print(f'Recall           : {recall:.4f}')
    if auc is not None:
        print(f'AUC-ROC          : {auc:.4f}')
        print(f'EER              : {eer:.4f} (@thr {eer_thr:.3f})')
    else:
        print('AUC-ROC / EER   : not computed (need both classes present in this run)')
    print(f'Confusion matrix (rows=actual, cols=predicted, order=[real,fake]):\n{cm}')
    print(f'\nSaved: {OUT_DIR / "metrics.json"}')


if __name__ == '__main__':
    main()
