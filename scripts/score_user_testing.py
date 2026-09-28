"""Score the user-testing survey CSVs in docs/user_testing/responses/ into summary.json and summary.md.

    python scripts/score_user_testing.py"""
import csv
import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_survey_form import SURVEY, variant

ROOT = Path(__file__).resolve().parent.parent
RESP = ROOT / 'docs' / 'user_testing' / 'responses'
OUT = ROOT / 'docs' / 'user_testing' / 'results'
NOT_NOTICED = 'did not notice it'


def sus_score(answers):
    """Brooke (1996): odd items contribute (x - 1), even items (5 - x); the sum times 2.5 gives 0 to 100."""
    total = 0
    for i in range(1, 11):
        x = int(answers[f'SUS{i}'])
        if not 1 <= x <= 5:
            raise ValueError(f'SUS{i} = {x} is outside 1 to 5')
        total += (x - 1) if i % 2 else (5 - x)
    return total * 2.5


def read_response(path):
    rows = list(csv.DictReader(open(path, newline='')))
    if not rows:
        raise ValueError(f'{path.name}: empty')
    a = defaultdict(dict)
    for r in rows:
        a[r['section']][r['item']] = r['value']
    pid, rnd = rows[0]['participant'], rows[0]['round']
    if any(r['participant'] != pid or r['round'] != rnd for r in rows):
        raise ValueError(f'{path.name}: mixes participants or rounds')
    form = a['meta'].get('form', 'full')
    spec, required_tasks = variant(form)
    missing = []
    if not a['meta'].get('consent'):
        missing.append('meta/consent')
    missing += [f'task/{t}/outcome' for t in required_tasks if not a['task'].get(f'{t}/outcome')]
    missing += [f'sus/SUS{i}' for i in range(1, 11) if not a['sus'].get(f'SUS{i}')]
    missing += [f'project/{q}' for q, _ in spec['project'] if not a['project'].get(q)]
    missing += [f'feature/{f}' for f, _ in spec['features'] if not a['feature'].get(f)]
    if missing:
        raise ValueError(f'{path.name}: missing required answers {missing}')
    for t in SURVEY['tasks']:
        o = a['task'].get(f'{t["id"]}/outcome')
        if o and o not in SURVEY['outcomes']:
            raise ValueError(f'{path.name}: {t["id"]} outcome "{o}" is not a form option')
        for c in t['checks']:
            v = a['task'].get(f'{t["id"]}/{c["id"]}')
            if v and v not in c['options']:
                raise ValueError(f'{path.name}: {t["id"]}/{c["id"]} = "{v}" is not a form option')
    for f, v in a['feature'].items():
        if v != NOT_NOTICED and v not in {'1', '2', '3', '4', '5'}:
            raise ValueError(f'{path.name}: feature {f} = "{v}" is not a form option')
    return {'participant': pid, 'round': rnd, 'form': form, 'answers': a, 'sus': sus_score(a['sus'])}


def _median(xs):
    return statistics.median(xs) if xs else None


def summarise_round(resps):
    out = {'n': len(resps), 'participants': sorted(r['participant'] for r in resps),
           'forms': {r['participant']: r['form'] for r in resps}}
    out['sus'] = {r['participant']: r['sus'] for r in resps}
    out['sus_median'] = _median(list(out['sus'].values()))
    out['sus_mean'] = round(statistics.mean(out['sus'].values()), 1) if resps else None
    tasks = {}
    for t in SURVEY['tasks']:
        tid = t['id']
        entry = {'outcomes': dict(Counter(r['answers']['task'].get(f'{tid}/outcome', 'not recorded') for r in resps))}
        eases = [int(r['answers']['task'][f'{tid}/ease']) for r in resps if r['answers']['task'].get(f'{tid}/ease')]
        entry['ease_median_1_to_7'] = _median(eases)
        entry['ease_values'] = eases
        for c in t['checks']:
            entry[c['id']] = dict(Counter(r['answers']['task'].get(f'{tid}/{c["id"]}', 'not recorded') for r in resps))
        entry['notes'] = {r['participant']: r['answers']['task'].get(f'{tid}/notes', '') for r in resps}
        tasks[tid] = entry
    out['tasks'] = tasks
    # Short-form sessions do not ask the project statements or the feature ratings: medians are over those who were asked.
    out['project'] = {q: {'median': _median([int(r['answers']['project'][q]) for r in resps if q in r['answers']['project']]),
                          'values': {r['participant']: int(r['answers']['project'][q]) for r in resps if q in r['answers']['project']}}
                      for q, _ in SURVEY['project']}
    feats = {}
    for f, _ in SURVEY['features']:
        vals = [r['answers']['feature'][f] for r in resps if f in r['answers']['feature']]
        nums = [int(v) for v in vals if v != NOT_NOTICED]
        feats[f] = {'median': _median(nums), 'not_noticed': sum(v == NOT_NOTICED for v in vals), 'asked': len(vals), 'values': vals}
    out['features'] = feats
    out['open'] = {q: {r['participant']: r['answers']['open'].get(q, '') for r in resps} for q, _ in SURVEY['open']}
    out['facilitator'] = {q: {r['participant']: r['answers']['facilitator'].get(q, '') for r in resps} for q, _ in SURVEY['facilitator']}
    out['background'] = {r['participant']: {k: r['answers']['meta'].get(k, '') for k in ('background', 'ml_background', 'checks_videos')}
                         for r in resps}
    return out


def score(resp_dir=RESP, out_dir=OUT):
    files = sorted(resp_dir.glob('survey_P*_round*.csv'))
    if not files:
        raise SystemExit(f'No response files in {resp_dir}. Nothing is scored until real sessions have produced CSVs.')
    resps = [read_response(f) for f in files]
    seen = Counter((r['participant'], r['round']) for r in resps)
    dup = [k for k, n in seen.items() if n > 1]
    if dup:
        raise SystemExit(f'Duplicate participant/round files: {dup}')
    rounds = {rnd: summarise_round([r for r in resps if r['round'] == rnd]) for rnd in sorted({r['round'] for r in resps})}
    summary = {'generated_at': datetime.now().astimezone().isoformat(timespec='seconds'),
               'files': [f.name for f in files], 'rounds': rounds}
    if {'1', '2'} <= set(rounds):
        summary['round1_vs_round2'] = {
            'sus_median': [rounds['1']['sus_median'], rounds['2']['sus_median']],
            'project_median': {q: [rounds['1']['project'][q]['median'], rounds['2']['project'][q]['median']] for q, _ in SURVEY['project']},
            'task_ease_median': {t['id']: [rounds['1']['tasks'][t['id']]['ease_median_1_to_7'], rounds['2']['tasks'][t['id']]['ease_median_1_to_7']]
                                 for t in SURVEY['tasks']},
            'same_participants_in_both': sorted(set(rounds['1']['participants']) & set(rounds['2']['participants'])),
        }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'summary.json').write_text(json.dumps(summary, indent=2))
    (out_dir / 'summary.md').write_text(to_markdown(summary))
    return summary


def to_markdown(s):
    L = ['# User-testing results (generated by scripts/score_user_testing.py; do not edit)', '',
         f'Generated {s["generated_at"]} from {len(s["files"])} response file(s): {", ".join(s["files"])}.', '']
    for rnd, r in s['rounds'].items():
        L += [f'## Round {rnd} (n = {r["n"]}: {", ".join(r["participants"])}; forms {r["forms"]})', '',
              f'SUS per participant: {r["sus"]}; median {r["sus_median"]} (mean {r["sus_mean"]}; n is small, read the individual values).', '',
              '| Task | Outcomes | Ease median (1 to 7) | Checks |', '|---|---|---|---|']
        for t in SURVEY['tasks']:
            e = r['tasks'][t['id']]
            checks = '; '.join(f'{c["id"]}: {e[c["id"]]}' for c in t['checks'])
            L.append(f'| {t["id"]} {t["title"]} | {e["outcomes"]} | {e["ease_median_1_to_7"]} | {checks} |')
        L += ['', '| Statement | Median (1 to 5) | Values |', '|---|---|---|']
        for q, text in SURVEY['project']:
            L.append(f'| {q} {text} | {r["project"][q]["median"]} | {r["project"][q]["values"]} |')
        L += ['', '| Feature | Median usefulness (1 to 5) | Did not notice |', '|---|---|---|']
        for f, text in SURVEY['features']:
            L.append(f'| {text} | {r["features"][f]["median"]} | {r["features"][f]["not_noticed"]} of {r["features"][f]["asked"]} asked |')
        L += ['', 'Open answers (verbatim, for theming):', '']
        for q, text in SURVEY['open']:
            L.append(f'- **{q} {text}**')
            for p, v in r['open'][q].items():
                if v:
                    L.append(f'  - {p}: {v}')
        L.append('')
    if 'round1_vs_round2' in s:
        c = s['round1_vs_round2']
        L += ['## Round 1 against round 2 (medians)', '', f'SUS: {c["sus_median"][0]} to {c["sus_median"][1]}. '
              f'Participants in both rounds: {c["same_participants_in_both"] or "none"}.', '']
    return '\n'.join(L) + '\n'


def main():
    s = score()
    print(to_markdown(s))
    return 0


if __name__ == '__main__':
    sys.exit(main())
