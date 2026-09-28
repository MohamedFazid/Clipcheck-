"""Compare local LLMs on the app's explanation prompt and faithfulness screen (ledger M1).

    python scripts/compare_llms.py run --models llama3:8b mistral:7b qwen2.5:7b; python scripts/compare_llms.py summarise"""
import os
import re
import sys
import json
import time
import argparse
import statistics
from datetime import datetime
from pathlib import Path

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fusion import fuse
from explain import build_prompt, build_structured_input, GEN_OPTIONS, GENERATE_URL
from explain_checks import check_faithfulness, explain_template, _sentences

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / 'results' / 'explanation_eval_full' / 'cases.json'
OUT = ROOT / 'results' / 'llm_comparison'
GEN = OUT / 'generations.jsonl'
SEEDS = (42, 43, 44)

BULLET_RE = re.compile(r'^\s*(?:[-*•]|\d+[.)])\s', re.M)
HEADING_RE = re.compile(r'^\s*#', re.M)
PREAMBLE_RE = re.compile(r'^\s*(?:here is|here\'s|sure|certainly|explanation\s*:)', re.I)


def load_cases():
    """The packet's 50 cases, with the structured input rebuilt exactly as the app builds it (asserted equal to the stored one)."""
    records = json.load(open(CASES))['records']
    cases = []
    for r in records:
        result = fuse(r['p_video'], r['p_audio'])
        structured = build_structured_input(result, r.get('anomalies'))
        if structured != r['structured_input']:
            raise SystemExit(f'{r["case_id"]}: rebuilt structured input differs from the stored packet; refusing to run')
        cases.append({'case_id': r['case_id'], 'result': result, 'anomalies': r.get('anomalies'),
                      'structured': structured, 'verdict': structured['verdict']})
    return cases


def format_check(text):
    """Prompt rule 9: 2 to 4 short sentences, no bullets, no headings, no preamble."""
    n = len(_sentences(text))
    problems = []
    if not 2 <= n <= 4:
        problems.append(f'{n} sentences')
    if BULLET_RE.search(text):
        problems.append('bullets')
    if HEADING_RE.search(text):
        problems.append('heading')
    if PREAMBLE_RE.search(text):
        problems.append('preamble')
    return {'ok': not problems, 'n_sentences': n, 'problems': problems}


def generate(model, prompt, seed, timeout=180):
    payload = {'model': model, 'prompt': prompt, 'stream': False, 'keep_alive': '10m',
               'options': {**GEN_OPTIONS, 'seed': seed}}
    t0 = time.perf_counter()
    resp = requests.post(GENERATE_URL, json=payload, timeout=timeout)
    resp.raise_for_status()
    wall = time.perf_counter() - t0
    return resp.json().get('response', '').strip(), wall


def done_keys():
    if not GEN.exists():
        return set()
    return {(d['model'], d['seed'], d['case_id']) for d in (json.loads(l) for l in GEN.read_text().splitlines() if l.strip())}


def cmd_run(args):
    OUT.mkdir(parents=True, exist_ok=True)
    cases = load_cases()
    done = done_keys()
    with open(GEN, 'a') as f:
        for model in args.models:
            todo = [(s, c) for s in SEEDS for c in cases if (model, s, c['case_id']) not in done]
            if not todo:
                print(f'{model}: already complete')
                continue
            print(f'{model}: warm-up (discarded) ...', flush=True)
            generate(model, build_prompt(cases[0]['result'], cases[0]['anomalies']), 0)
            for i, (seed, c) in enumerate(todo, 1):
                text, wall = generate(model, build_prompt(c['result'], c['anomalies']), seed)
                screen = check_faithfulness(text, c['structured'])
                rec = {'model': model, 'seed': seed, 'case_id': c['case_id'], 'verdict': c['verdict'], 'text': text,
                       'latency_s': round(wall, 3), 'screen': screen, 'format': format_check(text),
                       'generated_at': datetime.now().astimezone().isoformat(timespec='seconds')}
                f.write(json.dumps(rec) + '\n')
                f.flush()
                print(f'  [{i}/{len(todo)}] {model} seed {seed} {c["case_id"]} {c["verdict"][:7]}: '
                      f'{"PASS" if screen["passed"] else "FAIL"} {wall:.1f}s', flush=True)
        # Leave Ollama as the live app expects it: candidates unloaded.
        for model in args.models:
            if model != 'llama3:8b':
                try:
                    requests.post(GENERATE_URL, json={'model': model, 'keep_alive': 0}, timeout=30)
                except requests.RequestException:
                    pass
    return 0


def _rate(xs):
    return round(100 * sum(xs) / len(xs), 1) if xs else None


def summarise_rows(rows):
    passed = [r['screen']['passed'] for r in rows]
    partial = [r['screen']['passed'] for r in rows if r['verdict'] == 'PARTIAL_MANIPULATION']
    other = [r['screen']['passed'] for r in rows if r['verdict'] != 'PARTIAL_MANIPULATION']
    lat = sorted(r['latency_s'] for r in rows if r.get('latency_s') is not None)
    vtypes = {}
    for r in rows:
        for t in {v['type'] for v in r['screen']['violations']}:
            vtypes[t] = vtypes.get(t, 0) + 1
    per_seed_other_fail = {}
    for r in rows:
        if r['verdict'] != 'PARTIAL_MANIPULATION' and not r['screen']['passed']:
            per_seed_other_fail[r['seed']] = per_seed_other_fail.get(r['seed'], 0) + 1
    return {
        'n': len(rows),
        'screen_pass_pct': _rate(passed),
        'screen_pass_partial_pct': _rate(partial),
        'screen_pass_real_fake_pct': _rate(other),
        'real_fake_failures_per_seed': {str(s): per_seed_other_fail.get(s, 0) for s in sorted({r['seed'] for r in rows})},
        'format_ok_pct': _rate([r['format']['ok'] for r in rows]),
        'latency_mean_s': round(statistics.mean(lat), 2) if lat else None,
        'latency_p95_s': round(lat[min(len(lat) - 1, int(0.95 * len(lat)))], 2) if lat else None,
        'violations_by_type (texts)': vtypes,
    }


def cmd_summarise(args):
    rows = [json.loads(l) for l in GEN.read_text().splitlines() if l.strip()]
    models = sorted({r['model'] for r in rows}, key=lambda m: (m != 'llama3:8b', m))
    summary = {'protocol': 'docs/EXPERIMENTS.md M1', 'cases': str(CASES.relative_to(ROOT)), 'seeds': list(SEEDS),
               'gen_options': GEN_OPTIONS, 'models': {}}
    for m in models:
        summary['models'][m] = summarise_rows([r for r in rows if r['model'] == m])

    tmpl = []
    for c in load_cases():
        text = explain_template(c['result'], c['anomalies'])
        tmpl.append({'verdict': c['verdict'], 'seed': 0, 'screen': check_faithfulness(text, c['structured']),
                     'format': format_check(text), 'latency_s': None})
    summary['template_reference'] = summarise_rows(tmpl)

    # Reproduction check: llama3 seed 42 against the stored packet text (same model, prompt and options).
    stored = {r['case_id']: r['explanation'] for r in json.load(open(CASES))['records']}
    l42 = [r for r in rows if r['model'] == 'llama3:8b' and r['seed'] == 42]
    if l42:
        summary['llama3_seed42_identical_to_packet'] = f'{sum(r["text"] == stored[r["case_id"]] for r in l42)} of {len(l42)}'

    (OUT / 'summary.json').write_text(json.dumps(summary, indent=2))
    lines = ['# Explanation LLM comparison (ledger M1), generated by scripts/compare_llms.py; do not edit', '',
             f'Generated {datetime.now().astimezone().isoformat(timespec="minutes")}. 50 packet cases x seeds {list(SEEDS)}; '
             'app prompt and options unchanged; screen = app faithfulness check.', '',
             '| Model | n | Screen pass | PARTIAL pass | REAL+FAKE pass | REAL+FAKE failures per seed | Format ok | Latency mean / p95 (s) |',
             '|---|---|---|---|---|---|---|---|']
    for m, s in list(summary['models'].items()) + [('template (reference)', summary['template_reference'])]:
        lines.append(f'| {m} | {s["n"]} | {s["screen_pass_pct"]}% | {s["screen_pass_partial_pct"]}% | {s["screen_pass_real_fake_pct"]}% | '
                     f'{s["real_fake_failures_per_seed"]} | {s["format_ok_pct"]}% | {s["latency_mean_s"]} / {s["latency_p95_s"]} |')
    lines += ['', 'Violation types (number of texts with at least one of that type):', '']
    for m, s in summary['models'].items():
        lines.append(f'- {m}: {s["violations_by_type (texts)"]}')
    if 'llama3_seed42_identical_to_packet' in summary:
        lines += ['', f'Reproduction: llama3:8b seed 42 texts identical to the stored packet: {summary["llama3_seed42_identical_to_packet"]}.']
    (OUT / 'summary.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run')
    r.add_argument('--models', nargs='+', required=True)
    sub.add_parser('summarise')
    args = ap.parse_args()
    return {'run': cmd_run, 'summarise': cmd_summarise}[args.cmd](args)


if __name__ == '__main__':
    sys.exit(main())
