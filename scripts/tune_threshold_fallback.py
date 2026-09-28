"""Grid-search threshold_T against ANY results file produced by
eval_fallback_4condition.py, replacing FakeAVCeleb in Ch3.6's originally
specified tuning procedure until it (or an equivalent) is obtained.

Dataset-agnostic like eval_fallback_4condition.py: this script only reads
the per_clip_results list and the category labels already in it. Point
--results at whichever dataset's output you want to tune against; no code
change needed to swap datasets.

Criterion (matching Ch3.6's own stated method): select T that maximises F1
on correctly identifying genuine single-modality-manipulation cases (RVFA,
FVRA) as "disagreement", while minimising false-disagreement on genuine
agreement cases (RVRA, FVFA) -- i.e. treat "should this clip disagree" as
the binary target and T as the decision threshold on |p_video - p_audio|.

Run: /opt/anaconda3/bin/python scripts/tune_threshold_fallback.py \\
    [--results results/fallback_eval/fallback_4condition_results.json] \\
    [--out results/fallback_eval/threshold_tuning.json]
(no torch/facenet needed -- just reads the saved JSON)
"""
import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RESULTS_PATH = PROJECT_ROOT / 'results' / 'fallback_eval' / 'fallback_4condition_results.json'
DEFAULT_OUT_PATH = PROJECT_ROOT / 'results' / 'fallback_eval' / 'threshold_tuning.json'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', type=Path, default=DEFAULT_RESULTS_PATH,
                     help='Output of eval_fallback_4condition.py for whichever dataset '
                          'is currently backing the evaluation.')
    ap.add_argument('--out', type=Path, default=DEFAULT_OUT_PATH)
    args = ap.parse_args()

    with open(args.results) as f:
        data = json.load(f)
    rows = [r for r in data['per_clip_results'] if r['p_audio'] is not None]
    source_note = data.get('note', 'unknown source -- results file has no note field')
    print(f'{len(rows)} clips with both scores available')
    print(f'Source: {source_note}\n')

    # ground truth: should this clip register as "disagreement" (genuine
    # single-modality manipulation) -- true for RVFA/FVRA, false for RVRA/FVFA
    for r in rows:
        r['gap'] = abs(r['p_video'] - r['p_audio'])
        r['should_disagree'] = r['category'] in ('RVFA', 'FVRA')

    n_should_disagree = sum(1 for r in rows if r['should_disagree'])
    if n_should_disagree == 0:
        print('WARNING: no RVFA/FVRA clips in this dataset (e.g. DFDC and DeepfakeTIMIT '
              'both lack a real-video/fake-audio category) -- precision/recall against '
              '"should disagree" are meaningless here. Tuning needs a dataset that '
              'covers both single-modality-manipulation directions.')
        return

    candidates = [round(t, 2) for t in [0.05, 0.10, 0.15, 0.20, 0.25, 0.30,
                                          0.35, 0.40, 0.45, 0.50, 0.55, 0.60]]
    print(f'{"T":>5} {"TP":>4} {"FP":>4} {"FN":>4} {"TN":>4} {"precision":>10} {"recall":>8} {"F1":>6}')
    best = None
    for T in candidates:
        tp = sum(1 for r in rows if r['should_disagree'] and r['gap'] >= T)
        fn = sum(1 for r in rows if r['should_disagree'] and r['gap'] < T)
        fp = sum(1 for r in rows if not r['should_disagree'] and r['gap'] >= T)
        tn = sum(1 for r in rows if not r['should_disagree'] and r['gap'] < T)
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        print(f'{T:>5} {tp:>4} {fp:>4} {fn:>4} {tn:>4} {precision:>10.3f} {recall:>8.3f} {f1:>6.3f}')
        if best is None or f1 > best[1]:
            best = (T, f1, precision, recall, tp, fp, fn, tn)

    T, f1, precision, recall, tp, fp, fn, tn = best
    print(f'\nBest T = {T} (F1={f1:.3f}, precision={precision:.3f}, recall={recall:.3f})')
    print(f'  TP={tp} FP={fp} FN={fn} TN={tn}')

    out = {
        'source': source_note,
        'method': 'Grid search over |p_video - p_audio| >= T as the disagreement '
                   'predictor, F1 against ground truth (RVFA/FVRA = should disagree, '
                   'RVRA/FVFA = should not).',
        'candidates': candidates,
        'best_T': T, 'best_F1': round(f1, 4),
        'best_precision': round(precision, 4), 'best_recall': round(recall, 4),
        'confusion': {'TP': tp, 'FP': fp, 'FN': fn, 'TN': tn},
    }
    with open(args.out, 'w') as f:
        json.dump(out, f, indent=2)
    print(f'\nSaved: {args.out}')


if __name__ == '__main__':
    main()
