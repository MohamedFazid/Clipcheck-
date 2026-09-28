"""Confidence interval for the research question's headline: how much better is disagreement-aware fusion than standard fusion?

The four-condition evaluation reports two accuracies (docs/EXPERIMENTS.md F3, F5). A gap between two accuracies measured on about 76
to 79 clips needs an interval before it is called a result. This script scores every clip under both rules, exactly as
scripts/eval_fallback_4condition.py does, and bootstraps the paired per-clip difference.

Scoring rules (copied from eval_fallback_4condition.py so the numbers reproduce its output):
    standard fusion      : predicts fake when (p_video + p_audio) / 2 >= 0.5
    disagreement-aware   : predicts fake when the fusion verdict is FAKE or PARTIAL_MANIPULATION
    ground truth         : fake when the video is fake OR the audio is spoofed
Only clips that have BOTH scores enter (a clip whose audio was gated by the speech detector has no audio score).

CAVEATS, recorded in the output file: clips are resampled independently, but real videos repeat across RVRA and RVFA (the
held-out set has only 22 real videos), so the intervals are slightly narrower than the truth; the sets are self-built, not FakeAVCeleb.

    /opt/anaconda3/bin/python scripts/bootstrap_fusion_advantage.py \\
        --results results/heldout_eval_shipped/fallback_4condition_results.json --out results/heldout_eval_shipped/advantage_bootstrap.json
"""
import argparse
import json
from pathlib import Path

import numpy as np

CATEGORIES = ('RVRA', 'RVFA', 'FVRA', 'FVFA')


def per_clip_correctness(rows):
    out = []
    for r in rows:
        if r.get('p_audio') is None:
            continue
        truth_fake = (r['video_label'] == 'fake') or (r['audio_label'] == 'spoof')
        std = int(((r['p_video'] + r['p_audio']) / 2 >= 0.5) == truth_fake)
        da = int((r['fusion_verdict'] in ('FAKE', 'PARTIAL_MANIPULATION')) == truth_fake)
        out.append((std, da, r['category']))
    return out


def bootstrap(pc, boots=20000, seed=0):
    a = np.array([(s, d) for s, d, _ in pc], dtype=float)
    rng = np.random.default_rng(seed)
    n = len(a)
    diffs = np.array([(a[i, 1].mean() - a[i, 0].mean()) * 100 for i in (rng.integers(0, n, n) for _ in range(boots))])
    return [float(x) for x in np.percentile(diffs, [2.5, 97.5])]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--results', required=True, help='a four-condition results JSON (eval_fallback_4condition.py output)')
    ap.add_argument('--out', required=True)
    ap.add_argument('--boots', type=int, default=20000)
    ap.add_argument('--seed', type=int, default=0)
    args = ap.parse_args()

    data = json.load(open(args.results))
    pc = per_clip_correctness(data['per_clip_results'])
    std = float(np.mean([x[0] for x in pc]) * 100)
    da = float(np.mean([x[1] for x in pc]) * 100)
    lo, hi = bootstrap(pc, args.boots, args.seed)
    by = {c: [x for x in pc if x[2] == c] for c in CATEGORIES}
    out = {
        'results_file': str(args.results), 'n_clips_with_both_scores': len(pc), 'bootstrap_resamples': args.boots, 'seed': args.seed,
        'standard_fusion_accuracy_pct': std, 'disagreement_aware_accuracy_pct': da,
        'advantage_pp': da - std, 'advantage_ci95_pp': [lo, hi],
        'ci_excludes_zero': bool(lo > 0),
        'clips_only_disagreement_aware_correct': sum(1 for s, d, _ in pc if d == 1 and s == 0),
        'clips_only_standard_correct': sum(1 for s, d, _ in pc if s == 1 and d == 0),
        'per_category_pct': {c: {'n': len(v), 'standard': float(np.mean([x[0] for x in v]) * 100),
                                 'disagreement_aware': float(np.mean([x[1] for x in v]) * 100)} for c, v in by.items() if v},
        'caveats': ('Clips are resampled independently but real videos repeat across RVRA and RVFA, so the interval is slightly '
                    'narrow. Self-built set, not FakeAVCeleb. Clips without an audio score are excluded.'),
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(args.out, 'w'), indent=2)
    print(f'n={len(pc)}  standard {std:.1f}%  disagreement-aware {da:.1f}%  advantage {da - std:+.1f} pp  '
          f'95% CI [{lo:+.1f}, {hi:+.1f}]  -> {args.out}')


if __name__ == '__main__':
    main()
