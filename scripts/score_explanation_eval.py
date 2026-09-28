"""Score the 50-case explanation-eval packet once BOTH human raters have filled their CSVs (Draft Report Ch 3.6).

Reads results/explanation_eval_full/rating_sheet_rater{1,2}.csv. Refuses to run while either sheet still has blank cells
(the packet's own instructions: score independently, in order, before comparing), so it cannot be run early by mistake.

Reports, per dimension (factual_grounding, score_accuracy, absence_of_hallucination) and overall:
  - each rater's mean score (0-2)
  - exact agreement rate (identical score)
  - quadratic-weighted Cohen's Kappa (the standard measure for a 3-point ordinal scale; unweighted kappa treats a
    1-point and 2-point disagreement as equally bad, which is not what this rubric intends)
  - cases where the two raters differ by 2 (a full disagreement, worth resolving by discussion), listed by id
Only the two human sheets are read; no automated or model-generated score enters this report.

    /opt/anaconda3/bin/python scripts/score_explanation_eval.py
"""
import csv
import json
import sys
from pathlib import Path

from sklearn.metrics import cohen_kappa_score

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / 'results' / 'explanation_eval_full'
DIMENSIONS = ('factual_grounding', 'score_accuracy', 'absence_of_hallucination')


def load(path):
    rows = {r['case_id']: r for r in csv.DictReader(open(path))}
    blank = [cid for cid, r in rows.items() if any(r[d].strip() == '' for d in DIMENSIONS)]
    return rows, blank


def main():
    r1, blank1 = load(DIR / 'rating_sheet_rater1.csv')
    r2, blank2 = load(DIR / 'rating_sheet_rater2.csv')
    if blank1 or blank2:
        sys.exit(f'Not ready: rater1 has {len(blank1)} unscored case(s), rater2 has {len(blank2)}. '
                 'Both sheets must be complete (every dimension, every case) before scoring. '
                 f'First unscored: rater1={blank1[:3]} rater2={blank2[:3]}')
    if set(r1) != set(r2):
        sys.exit(f'The two sheets cover different cases: only in rater1 {set(r1) - set(r2)}, only in rater2 {set(r2) - set(r1)}')

    ids = sorted(r1, key=lambda c: int(c.split('-')[1]))
    report = {'n_cases': len(ids), 'dimensions': {}}
    for dim in DIMENSIONS:
        a = [int(r1[c][dim]) for c in ids]
        b = [int(r2[c][dim]) for c in ids]
        for v, who in ((a, 'rater1'), (b, 'rater2')):
            if any(x not in (0, 1, 2) for x in v):
                sys.exit(f'{who}/{dim}: scores must be 0, 1 or 2')
        exact = sum(x == y for x, y in zip(a, b)) / len(ids)
        big_disagree = [ids[i] for i in range(len(ids)) if abs(a[i] - b[i]) == 2]
        report['dimensions'][dim] = {
            'rater1_mean': sum(a) / len(a), 'rater2_mean': sum(b) / len(b), 'exact_agreement': exact,
            'weighted_kappa': float(cohen_kappa_score(a, b, weights='quadratic')),
            'full_disagreements': big_disagree}

    out = DIR / 'scored_report.json'
    json.dump(report, open(out, 'w'), indent=1)
    print(json.dumps(report, indent=1))
    print(f'\n-> {out}')


if __name__ == '__main__':
    main()
