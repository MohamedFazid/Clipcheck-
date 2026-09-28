"""Check the app's frame sampling and in-memory crops score the same as the stored JPEG crops the model was evaluated on.

    python scripts/check_preprocessing_parity.py --tag mm_xcep_vidsplit   # app env (needs MTCNN)"""
import argparse
import io
import json
import os
import sys
import time

import numpy as np
import torch
from PIL import Image
from sklearn.metrics import roc_auc_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import PROJECT_ROOT, RESULTS_DIR, RUNS_DIR, MODEL_RUNS_DIR, get_device  # noqa: E402
from video_infer import load_models, sample_face_crops, training_style, _val_transforms  # noqa: E402
import eval_cross_method as X  # noqa: E402

METHODS = ['Deepfakes', 'FaceSwap', 'NeuralTextures']


def video_file(kind, name):
    base = PROJECT_ROOT / 'data'
    if kind == 'real':
        return base / 'original_sequences' / 'youtube' / 'c23' / 'videos' / f'{name}.mp4'
    return base / 'manipulated_sequences' / kind / 'c23' / 'videos' / f'{name}.mp4'


@torch.no_grad()
def mean_p_fake(model, device, pil_crops):
    ps = []
    for im in pil_crops:
        ps.append(torch.softmax(model(_val_transforms(im).unsqueeze(0).to(device)), dim=1)[0, 0].item())
    return float(np.mean(ps)) if ps else None


def stored_crops(kind, name):
    folder = X.PROJECT_ROOT / 'frames' / 'real' / name if kind == 'real' else X.folder_for(kind, name)
    return [Image.open(p).convert('RGB') for p in sorted(folder.glob('*.jpg'))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', required=True)
    ap.add_argument('--seed', type=int, default=None, help='Default: best validation accuracy.')
    args = ap.parse_args()

    from calibrate_video import best_val_seed
    seed = args.seed if args.seed is not None else best_val_seed(args.tag)
    cfg = json.load(open(RUNS_DIR / args.tag / f'seed{seed}' / 'train_config.json'))
    arch = cfg.get('arch', 'efficientnet_b4')
    device = get_device()
    mtcnn, model, _ = load_models(str(MODEL_RUNS_DIR / args.tag / f'seed{seed}.pth'), arch=arch)
    print(f'{args.tag} seed {seed} | {arch} | device {device}', flush=True)

    real_ids, fake_ids = X.test_videos()
    jobs = [('real', r) for r in real_ids] + [(m, p) for m in METHODS for p in fake_ids]
    rows, t0 = [], time.time()
    for i, (kind, name) in enumerate(jobs, 1):
        crops = sample_face_crops(video_file(kind, name), mtcnn, max_faces=20)
        rows.append({'kind': kind, 'video': name, 'n_app_crops': len(crops),
                     'A_stored_jpeg': mean_p_fake(model, device, stored_crops(kind, name)),
                     'B_app_in_memory': mean_p_fake(model, device, crops),
                     'C_app_crops_jpeg': mean_p_fake(model, device, [training_style(c) for c in crops])})
        if i % 10 == 0:
            print(f'  {i}/{len(jobs)} videos ({time.time() - t0:.0f}s)', flush=True)

    ok = [r for r in rows if all(r[k] is not None for k in ('A_stored_jpeg', 'B_app_in_memory', 'C_app_crops_jpeg'))]
    dropped = len(rows) - len(ok)
    A, B, C = (np.array([r[k] for r in ok]) for k in ('A_stored_jpeg', 'B_app_in_memory', 'C_app_crops_jpeg'))
    is_fake = np.array([r['kind'] != 'real' for r in ok]).astype(int)

    def cmp(u, v):
        return {'mean_abs_diff': float(np.abs(u - v).mean()), 'max_abs_diff': float(np.abs(u - v).max()),
                'pearson_r': float(np.corrcoef(u, v)[0, 1]), 'decision_flips_at_0.5': int(((u >= .5) != (v >= .5)).sum())}

    def per_path(p):
        out = {'auc_all': float(roc_auc_score(is_fake, p)), 'accuracy_all': float(((p >= .5) == is_fake).mean()),
               'mean_p_real': float(p[is_fake == 0].mean())}
        for m in METHODS:
            sel = np.array([r['kind'] in ('real', m) for r in ok])
            out[m] = {'auc': float(roc_auc_score(is_fake[sel], p[sel])),
                      'fake_detected': float((p[np.array([r['kind'] == m for r in ok])] >= .5).mean())}
        return out

    res = {'tag': args.tag, 'seed': seed, 'arch': arch, 'n_videos': len(ok), 'dropped_no_face': dropped,
           'path_A_stored_jpeg': per_path(A), 'path_B_app_in_memory': per_path(B), 'path_C_app_crops_jpeg': per_path(C),
           'compare': {'A_vs_B_total_difference': cmp(A, B), 'B_vs_C_jpeg_only': cmp(B, C), 'A_vs_C_sampling_only': cmp(A, C)},
           'app_crops_per_video_mean': float(np.mean([r['n_app_crops'] for r in ok])),
           'per_video': rows}
    out = RESULTS_DIR / 'preprocessing_parity'
    out.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(out / f'{args.tag}_seed{seed}.json', 'w'), indent=2)

    L = [f'# Preprocessing parity: {args.tag} seed {seed} ({arch})\n',
         f'{len(ok)} test-split videos ({dropped} dropped for no detected face). A = stored JPEG crops (training/evaluation path), '
         'B = the app\'s in-memory path, C = B\'s crops JPEG round-tripped.\n',
         '| Path | AUC (all) | Accuracy at 0.5 | Mean P(fake) on real | FaceSwap detected | NeuralTextures detected | Deepfakes detected |',
         '|---|---|---|---|---|---|---|']
    for key, lab in (('path_A_stored_jpeg', 'A stored JPEG'), ('path_B_app_in_memory', 'B app (in memory)'), ('path_C_app_crops_jpeg', 'C app crops + JPEG')):
        r = res[key]
        L.append(f"| {lab} | {r['auc_all']:.3f} | {r['accuracy_all']:.3f} | {r['mean_p_real']:.3f} | {r['FaceSwap']['fake_detected']:.2f} | "
                 f"{r['NeuralTextures']['fake_detected']:.2f} | {r['Deepfakes']['fake_detected']:.2f} |")
    L += ['', '| Comparison | Mean abs diff in clip P(fake) | Max abs diff | Pearson r | Verdict flips at 0.5 |', '|---|---|---|---|---|']
    for key, lab in (('A_vs_B_total_difference', 'A vs B (everything)'), ('B_vs_C_jpeg_only', 'B vs C (JPEG only)'), ('A_vs_C_sampling_only', 'A vs C (sampling only)')):
        c = res['compare'][key]
        L.append(f"| {lab} | {c['mean_abs_diff']:.4f} | {c['max_abs_diff']:.3f} | {c['pearson_r']:.4f} | {c['decision_flips_at_0.5']} of {len(ok)} |")
    (out / f'{args.tag}_seed{seed}.md').write_text('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
