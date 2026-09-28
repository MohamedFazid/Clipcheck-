"""Compare the app's faithfulness screen with the two human raters on the 50 explanations (ledger E2); descriptive only.

    python scripts/compare_screen_with_raters.py   # writes results/explanation_eval_full/screen_vs_raters.json"""
import ast
import csv
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / 'results' / 'explanation_eval_full'
DIMS = ('factual_grounding', 'score_accuracy', 'absence_of_hallucination')
# Written into the output file; chosen after the ratings were seen, so the analysis is exploratory.
DEFINITIONS = (
    '(stated here, chosen after the ratings were seen, so this is an exploratory analysis, not a pre-registered test):\n'
    '  total        = factual_grounding + score_accuracy + absence_of_hallucination for one rater (0 to 6)\n'
    '  human-flagged = BOTH raters scored factual_grounding below 2 (the raters agree the text says something the facts do not support)'
)


def sheet(n):
    return {r['case_id']: {d: int(r[d]) for d in DIMS} for r in csv.DictReader(open(DIR / f'rating_sheet_rater{n}.csv'))}


def main():
    cases = json.load(open(DIR / 'cases.json'))['records']
    r1, r2 = sheet(1), sheet(2)
    rows = []
    for c in cases:
        cid = c['case_id']
        si = c['structured_input']
        verdict = (si if isinstance(si, dict) else ast.literal_eval(si))['verdict']
        rows.append({'case_id': cid, 'verdict': verdict, 'screen_passed': bool(c['faithfulness_screen']['passed']),
                     'r1': r1[cid], 'r2': r2[cid],
                     'total_r1': sum(r1[cid].values()), 'total_r2': sum(r2[cid].values()),
                     'human_flagged': r1[cid]['factual_grounding'] < 2 and r2[cid]['factual_grounding'] < 2})

    def summary(sub):
        if not sub:
            return None
        return {'n': len(sub),
                'mean_total_r1': round(statistics.mean(x['total_r1'] for x in sub), 2),
                'mean_total_r2': round(statistics.mean(x['total_r2'] for x in sub), 2),
                'both_full_marks': sum(1 for x in sub if x['total_r1'] == 6 and x['total_r2'] == 6),
                'human_flagged': sum(1 for x in sub if x['human_flagged']),
                **{f'mean_{d}_both': round(statistics.mean((x['r1'][d] + x['r2'][d]) / 2 for x in sub), 2) for d in DIMS}}

    by_verdict = {v: summary([x for x in rows if x['verdict'] == v]) for v in sorted({x['verdict'] for x in rows})}
    by_screen = {'screen_passed': summary([x for x in rows if x['screen_passed']]),
                 'screen_rejected': summary([x for x in rows if not x['screen_passed']])}
    both = lambda a, b: sum(1 for x in rows if x['screen_passed'] == a and x['human_flagged'] == b)
    confusion = {'screen_rejected_and_human_flagged': both(False, True), 'screen_rejected_not_human_flagged': both(False, False),
                 'screen_passed_but_human_flagged': both(True, True), 'screen_passed_not_human_flagged': both(True, False)}
    zero_passed = [x['case_id'] for x in rows if x['screen_passed'] and (0 in x['r1'].values() or 0 in x['r2'].values())]
    out = {'n_cases': len(rows), 'definitions': DEFINITIONS,
           'by_verdict': by_verdict, 'by_screen': by_screen, 'screen_vs_human_flag': confusion,
           'screen_passed_but_a_rater_gave_0': zero_passed, 'per_case': rows}
    (DIR / 'screen_vs_raters.json').write_text(json.dumps(out, indent=1))
    print(json.dumps({k: v for k, v in out.items() if k != 'per_case'}, indent=1))


if __name__ == '__main__':
    main()
