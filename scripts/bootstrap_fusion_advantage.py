"""Bootstrap 95% interval for the accuracy gain of disagreement-aware over standard fusion (paired, per clip).

    python scripts/bootstrap_fusion_advantage.py --results <4-condition results.json> --out <advantage_bootstrap.json>"""
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
