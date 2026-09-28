"""Promote a trained checkpoint to models/best_model.pth and write models/shipped_model.json (dry run unless --apply).

    python scripts/ship_model.py --tag aug_vidsplit --seed 43 [--apply]"""
import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import MODELS_DIR, MODEL_RUNS_DIR, RUNS_DIR, PROJECT_ROOT  # noqa: E402


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', required=True)
    ap.add_argument('--seed', type=int, required=True)
    ap.add_argument('--temperature', type=float, default=1.0,
                    help='Calibration temperature (logits / T before softmax). Default 1.0 = none. See scripts/calibrate_video.py: '
                         'apply one only if held-out calibration improves, since T fitted on a small validation set can be unstable.')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--video-accuracy', type=float, default=None,
                    help='Held-out accuracy fusion.py uses as the video weight. Default: the mean clip-level accuracy over this '
                         "tag's seeds on the 44-video test split. Pass the cross-validated figure instead when one exists: the PPR "
                         'bases the weighting on Large, Lines and Bagnall (2019), who use CROSS-VALIDATED accuracy, and a 44-video '
                         'split is both small and optimistic. Requires --video-accuracy-source.')
    ap.add_argument('--video-accuracy-source', default=None,
                    help='Where --video-accuracy came from, recorded verbatim and shown in the app.')
    args = ap.parse_args()
    if (args.video_accuracy is None) != (args.video_accuracy_source is None):
        sys.exit('--video-accuracy and --video-accuracy-source must be given together')

    ckpt = MODEL_RUNS_DIR / args.tag / f'seed{args.seed}.pth'
    run_dir = RUNS_DIR / args.tag / f'seed{args.seed}'
    if not ckpt.exists() or not (run_dir / 'metrics.json').exists():
        sys.exit(f'missing checkpoint or metrics for {args.tag} seed {args.seed}')
    cfg = json.load(open(run_dir / 'train_config.json')) if (run_dir / 'train_config.json').exists() else {}
    hist = json.load(open(run_dir / 'history.json'))

    seed_dirs = sorted((RUNS_DIR / args.tag).glob('seed*/metrics.json'))
    clip = [json.load(open(p))['video_level']['accuracy'] for p in seed_dirs]
    vl = json.load(open(run_dir / 'metrics.json'))['video_level']
    meta = {
        'shipped_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'tag': args.tag, 'seed': args.seed,
        'arch': cfg.get('arch', 'efficientnet_b4'), 'frames_dir': cfg.get('frames_dir', 'frames'),
        'trained_on': 'multi-method (Deepfakes + FaceSwap + NeuralTextures)' if 'multi' in cfg.get('frames_dir', '')
                      else 'Deepfakes only',
        'checkpoint_sha256': sha256(ckpt),
        'temperature': args.temperature,
        'temperature_source': 'none (T = 1.0)' if args.temperature == 1.0 else 'fitted on validation crops, see results/calibration/',
        'video_accuracy': float(args.video_accuracy if args.video_accuracy is not None else np.mean(clip)),
        'video_accuracy_source': (args.video_accuracy_source or
                                  f'clip-level test accuracy, mean of {len(clip)} seeds of tag {args.tag} on split v2 '
                                  f'({vl["n_videos"]} held-out videos; coarse: one video = {100 / vl["n_videos"]:.1f} pp)'),
        'video_accuracy_alternatives': {
            'clip_level_44_video_test_split_mean_over_seeds': float(np.mean(clip)),
            'note': 'The figure above in video_accuracy is the one fusion.py uses as the weight; this records what else was available.'},
        'selection_evidence': {'val_accuracy_at_best_epoch': float(max(hist['val_acc'])),
                               'val_loss_min': float(min(hist['val_loss'])), 'run_metrics': f'results/runs/{args.tag}/seed{args.seed}/metrics.json'},
    }
    print(json.dumps(meta, indent=2))
    if not args.apply:
        print('\nDry run. Nothing written. Re-run with --apply to promote this model.')
        return

    best = MODELS_DIR / 'best_model.pth'
    if best.exists():
        backup = MODELS_DIR / f'best_model.pth.pre-{datetime.now().strftime("%Y%m%d-%H%M%S")}.bak'
        shutil.move(str(best), str(backup))
        meta['previous_checkpoint_backup'] = backup.name
    shutil.copy2(ckpt, best)
    json.dump(meta, open(MODELS_DIR / 'shipped_model.json', 'w'), indent=2)
    print(f'\nShipped {args.tag} seed {args.seed} -> models/best_model.pth. Restart the server.')


if __name__ == '__main__':
    main()
