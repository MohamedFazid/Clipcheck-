"""Pool cross-validation folds into out-of-fold results with identity-cluster bootstrap confidence intervals.

Reads results/runs/<prefix><k>/seed<seed>/per_video_predictions.json for each fold k (written by evaluate.py) and reports:
  * pooled out-of-fold metrics over ALL videos (every video is scored once, by a model that never saw its identity);
  * the same per fold, as mean and std: this spread comes from the DATA partition, not just the random seed, which is the
    variation a single split with several seeds cannot show;
  * 95% confidence intervals from a cluster bootstrap that resamples whole identity groups (a reciprocal FF++ pair = 2 real +
    2 fake videos), because videos of one identity are not independent;
  * per-method fake detection, using data_splits/multimethod_assignment_v1.json;
  * clip-level Brier score and binary ECE on all pooled videos (a far larger sample than the 44-video test set).

    /opt/anaconda3/bin/python scripts/aggregate_cv.py --prefix cv5_xcep_f --name cv5_xcep_mm
"""
import argparse
import json
import os
import sys

import numpy as np
from sklearn.metrics import roc_auc_score

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import PROJECT_ROOT, RESULTS_DIR, RUNS_DIR, compute_eer, identity_groups_from_keys  # noqa: E402

METHOD_FILE = PROJECT_ROOT / 'data_splits' / 'multimethod_assignment_v1.json'


def ece_binary(p, y, bins=10):
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    return float(sum((idx == b).mean() * abs(y[idx == b].mean() - p[idx == b].mean()) for b in range(bins) if (idx == b).any()))


def metrics(y, p, meth):
    real, fake = y == 0, y == 1
    out = {'n_videos': int(len(y)), 'auc': float(roc_auc_score(y, p)), 'accuracy': float(((p >= .5) == y).mean()),
           'real_specificity': float((p[real] < .5).mean()), 'fake_detection': float((p[fake] >= .5).mean()),
           'eer': float(compute_eer(y, p)[0]), 'brier': float(((p - y) ** 2).mean()), 'ece10': ece_binary(p, y)}
    for m in ('Deepfakes', 'FaceSwap', 'NeuralTextures'):
        sel = fake & (meth == m)
        if sel.any():
            out[f'detect_{m}'] = float((p[sel] >= .5).mean())
            both = real | sel
            out[f'auc_{m}'] = float(roc_auc_score(y[both], p[both]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--prefix', required=True, help='Run-tag prefix; fold k lives in <prefix><k>, e.g. cv5_xcep_f')
    ap.add_argument('--name', required=True, help='Output folder name under results/cv/')
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--n-folds', type=int, default=5)
    ap.add_argument('--boot', type=int, default=2000)
    ap.add_argument('--allow-partial', action='store_true', help='Use the folds that exist (smoke tests only).')
    args = ap.parse_args()

    method_of = json.load(open(METHOD_FILE))['method_per_pair']
    rows = []
    for k in range(args.n_folds):
        f = RUNS_DIR / f'{args.prefix}{k}' / f'seed{args.seed}' / 'per_video_predictions.json'
        if not f.exists():
            if args.allow_partial:
                continue
            sys.exit(f'missing fold {k}: {f}')
        for r in json.load(open(f)):
            r['fold'] = k
            rows.append(r)
    folds_present = sorted({r['fold'] for r in rows})

    y = np.array([r['is_fake'] for r in rows])
    p = np.array([r['p_fake'] for r in rows])
    meth = np.array(['real' if r['is_fake'] == 0 else method_of[r['video'].split('/', 1)[1]] for r in rows])
    fold = np.array([r['fold'] for r in rows])
    keys = [r['video'] for r in rows]
    gid_of_key = {k: g for g, ks in identity_groups_from_keys(keys).items() for k in ks}
    gids = np.array([gid_of_key[k] for k in keys])
    assert len(set(keys)) == len(keys), 'a video was scored in more than one fold'

    pooled = metrics(y, p, meth)
    per_fold = [dict(fold=int(k), **metrics(y[fold == k], p[fold == k], meth[fold == k])) for k in folds_present]
    spread = {m: {'mean': float(np.mean([f[m] for f in per_fold if m in f])), 'std': float(np.std([f[m] for f in per_fold if m in f], ddof=1))}
              for m in ('auc', 'accuracy', 'real_specificity', 'fake_detection') if len(per_fold) > 1}

    rng = np.random.default_rng(0)
    uniq = np.unique(gids)
    by_g = {g: np.where(gids == g)[0] for g in uniq}
    boot = {}
    for _ in range(args.boot):
        pick = rng.choice(uniq, len(uniq), replace=True)
        ix = np.concatenate([by_g[g] for g in pick])
        if len(set(y[ix])) < 2:
            continue
        for name, val in metrics(y[ix], p[ix], meth[ix]).items():
            if name != 'n_videos':
                boot.setdefault(name, []).append(val)
    ci = {k: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))] for k, v in boot.items()}

    out = RESULTS_DIR / 'cv' / args.name
    out.mkdir(parents=True, exist_ok=True)
    res = {'name': args.name, 'folds': folds_present, 'seed': args.seed, 'pooled_out_of_fold': pooled,
           'ci95_cluster_bootstrap': ci, 'bootstrap_resamples': args.boot, 'n_identity_groups': int(len(uniq)),
           'per_fold': per_fold, 'fold_spread': spread}
    json.dump(res, open(out / 'cv_summary.json', 'w'), indent=2)

    def line(label, key, pct=True):
        v = pooled[key]
        lo, hi = ci[key]
        return f'| {label} | {v * 100:.1f}% | {lo * 100:.1f}% to {hi * 100:.1f}% |' if pct else f'| {label} | {v:.3f} | {lo:.3f} to {hi:.3f} |'

    L = [f'# Cross-validation: {args.name}\n',
         f'{len(folds_present)} folds, seed {args.seed}. Every video ({pooled["n_videos"]}) is scored once by a model that never saw '
         f'its identity. Clip level (mean P(fake) over a video\'s crops). 95% intervals: cluster bootstrap over '
         f'{len(uniq)} identity groups, {args.boot} resamples.\n',
         '## Pooled out-of-fold', '', '| Metric | Value | 95% CI |', '|---|---|---|',
         line('AUC-ROC', 'auc', False), line('Accuracy at 0.5', 'accuracy'), line('Real specificity', 'real_specificity'),
         line('Fake detection (all)', 'fake_detection'), line('EER', 'eer'), line('Brier score', 'brier', False), line('ECE (10 bins)', 'ece10', False)]
    for m in ('Deepfakes', 'FaceSwap', 'NeuralTextures'):
        if f'detect_{m}' in pooled:
            L += [line(f'{m}: fakes detected', f'detect_{m}'), line(f'{m}: AUC vs real', f'auc_{m}', False)]
    L += ['', '## Per fold (variation caused by the data partition)', '', '| Fold | Videos | AUC | Accuracy | Real specificity | Fake detection |', '|---|---|---|---|---|---|']
    for f in per_fold:
        L.append(f"| {f['fold']} | {f['n_videos']} | {f['auc']:.3f} | {f['accuracy'] * 100:.1f}% | {f['real_specificity'] * 100:.1f}% | {f['fake_detection'] * 100:.1f}% |")
    if spread:
        L.append(f"| **mean ± std** | | {spread['auc']['mean']:.3f} ± {spread['auc']['std']:.3f} | {spread['accuracy']['mean'] * 100:.1f} ± {spread['accuracy']['std'] * 100:.1f}% | "
                 f"{spread['real_specificity']['mean'] * 100:.1f} ± {spread['real_specificity']['std'] * 100:.1f}% | {spread['fake_detection']['mean'] * 100:.1f} ± {spread['fake_detection']['std'] * 100:.1f}% |")
    (out / 'cv_summary.md').write_text('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
