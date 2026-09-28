"""Aggregate per-seed evaluation metrics into mean +/- std for the report.

Reads every results/runs/seed*/metrics.json produced by evaluate.py and writes:
  * results/summary/metrics_summary.json  (machine-readable)
  * results/summary/metrics_summary.md    (report-ready table)

Usage:  python scripts/aggregate_runs.py
"""

import os
import sys
import json
import glob
import argparse

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import RUNS_DIR, SUMMARY_DIR

METRICS = ['accuracy', 'f1', 'precision', 'recall', 'auc_roc']


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Aggregate per-seed metrics into mean +/- std.')
    parser.add_argument('--tag', type=str, default='',
                        help='Experiment tag to aggregate. Empty = the reported '
                             'baseline runs in results/runs/seed*.')
    args = parser.parse_args()

    runs_root = RUNS_DIR / args.tag if args.tag else RUNS_DIR
    out_dir = SUMMARY_DIR / args.tag if args.tag else SUMMARY_DIR

    files = sorted(glob.glob(str(runs_root / 'seed*' / 'metrics.json')))
    if not files:
        print(f'No per-seed metrics found under {runs_root}. Run train + evaluate first.')
        return

    runs = []
    for fp in files:
        with open(fp) as f:
            runs.append(json.load(f))
    runs.sort(key=lambda r: r.get('seed', 0))
    seeds = [r.get('seed') for r in runs]
    print(f'Aggregating {len(runs)} run(s): seeds {seeds}')

    summary = {'tag': args.tag, 'seeds': seeds, 'n_runs': len(runs), 'per_metric': {}}
    for m in METRICS:
        vals = np.array([r[m] for r in runs], dtype=float)
        summary['per_metric'][m] = {
            'mean': float(vals.mean()),
            'std':  float(vals.std(ddof=1)) if len(vals) > 1 else 0.0,
            'values': vals.tolist(),
        }

    # ── Video-level metrics (evaluate.py's mean-aggregated-per-clip numbers) ──
    # Primary once present: matches what the deployed pipeline reports (one
    # score per clip) and avoids pseudo-replicating ~19 correlated frames per
    # video as independent test cases.
    if all('video_level' in r for r in runs):
        summary['n_test_videos'] = [r['video_level']['n_videos'] for r in runs]
        summary['per_metric_video'] = {}
        for m in METRICS + ['eer']:
            vals = np.array([r['video_level'][m] for r in runs], dtype=float)
            summary['per_metric_video'][m] = {
                'mean': float(vals.mean()),
                'std':  float(vals.std(ddof=1)) if len(vals) > 1 else 0.0,
                'values': vals.tolist(),
            }

    # ── Fold in EER + selected thresholds from A2/A3 (if present) ─────────────
    eer_vals, youden_thr, f1_thr = [], [], []
    for s in seeds:
        ta = runs_root / f'seed{s}' / 'threshold_analysis.json'
        if ta.exists():
            with open(ta) as f:
                d = json.load(f)
            eer_vals.append(d['eer_test'])
            youden_thr.append(d['threshold_selection']['youden_j']['threshold'])
            f1_thr.append(d['threshold_selection']['f1_optimal']['threshold'])
    if len(eer_vals) == len(seeds) and eer_vals:
        ev = np.array(eer_vals, dtype=float)
        summary['per_metric']['eer_test'] = {
            'mean': float(ev.mean()),
            'std':  float(ev.std(ddof=1)) if len(ev) > 1 else 0.0,
            'values': ev.tolist(),
        }
        summary['selected_thresholds'] = {
            'youden_j':   {'mean': float(np.mean(youden_thr)), 'values': youden_thr},
            'f1_optimal': {'mean': float(np.mean(f1_thr)),     'values': f1_thr},
        }

    os.makedirs(out_dir, exist_ok=True)
    with open(out_dir / 'metrics_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

    # Report-ready markdown table.
    lines = []
    variant = args.tag or 'baseline'
    lines.append(f'# Video branch — {len(runs)}-run summary (seeds {seeds}, variant: {variant})\n')
    lines.append('Data split held fixed (seed 42); training seed varied. '
                 'std is sample std (ddof=1).\n')

    if 'per_metric_video' in summary:
        lines.append(f'## Video-level (primary — matches app output, '
                     f'n={summary["n_test_videos"]} held-out videos)\n')
        header = '| Metric | Mean ± Std | ' + ' | '.join(f'seed {s}' for s in seeds) + ' |'
        sep    = '|' + '---|' * (2 + len(seeds))
        lines.append(header)
        lines.append(sep)
        for m in METRICS + ['eer']:
            s = summary['per_metric_video'][m]
            per = ' | '.join(f'{v:.4f}' for v in s['values'])
            lines.append(f'| {m} | {s["mean"]:.4f} ± {s["std"]:.4f} | {per} |')
        lines.append('')
        lines.append('## Frame-level (secondary — pseudo-replicated, ~19 correlated crops/video)\n')

    header = '| Metric | Mean ± Std | ' + ' | '.join(f'seed {s}' for s in seeds) + ' |'
    sep    = '|' + '---|' * (2 + len(seeds))
    lines.append(header)
    lines.append(sep)
    table_metrics = METRICS + (['eer_test'] if 'eer_test' in summary['per_metric'] else [])
    for m in table_metrics:
        s = summary['per_metric'][m]
        per = ' | '.join(f'{v:.4f}' for v in s['values'])
        lines.append(f'| {m} | {s["mean"]:.4f} ± {s["std"]:.4f} | {per} |')

    if 'selected_thresholds' in summary:
        st = summary['selected_thresholds']
        lines.append('')
        lines.append('**Selected decision thresholds (chosen on the validation split):** '
                     f'Youden-J mean {st["youden_j"]["mean"]:.3f} '
                     f'(per-seed {st["youden_j"]["values"]}); '
                     f'F1-optimal mean {st["f1_optimal"]["mean"]:.3f} '
                     f'(per-seed {st["f1_optimal"]["values"]}). '
                     'EER is threshold-free (lower is better).')
    md = '\n'.join(lines) + '\n'

    with open(out_dir / 'metrics_summary.md', 'w') as f:
        f.write(md)

    print('\n' + md)
    print(f'Wrote: {out_dir / "metrics_summary.json"}')
    print(f'Wrote: {out_dir / "metrics_summary.md"}')


if __name__ == '__main__':
    main()
