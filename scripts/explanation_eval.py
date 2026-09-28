"""Human evaluation of the explanation layer: `generate` builds cases and a rating packet, `score` computes agreement and kappa.

    python scripts/explanation_eval.py generate --from-results <results.json> --n 50 | score --rater1 <csv> --rater2 <csv>"""

import os
import sys
import csv
import json
import random
import argparse
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import RESULTS_DIR
from fusion import fuse, THRESHOLD_T_DEFAULT
from explain import explain, build_structured_input, explanation_available
from explain_checks import check_faithfulness

EVAL_DIR = RESULTS_DIR / 'explanation_eval'
DIMENSIONS = ['factual_grounding', 'score_accuracy', 'absence_of_hallucination']

RUBRIC = """\
## Rubric (Chapter 3.6)

Score each explanation on THREE dimensions. Judge the explanation ONLY against
the structured input printed above it — not against your own opinion of whether
the video is really fake.

**1. Factual grounding** — does every claim match the structured input?
  - 2 (passes)  : every statement is traceable to a field in the structured input.
  - 1 (partial) : mostly grounded, but one statement overreaches or is vague
                  enough to mislead.
  - 0 (fails)   : contains a claim that contradicts the structured input.

**2. Score accuracy** — are the probabilities stated correctly, and as
   probabilities rather than certainties?
  - 2 (passes)  : values are stated accurately (a decimal or its correct
                  percentage form both count), and framed as a likelihood.
  - 1 (partial) : value correct but framed too strongly ("this is fake" rather
                  than "likely fake"), or rounded misleadingly.
  - 0 (fails)   : states a wrong number, or asserts certainty from a probability.

**3. Absence of hallucination** — does it avoid introducing anything new?
  - 2 (passes)  : introduces no facts beyond the structured input.
  - 1 (partial) : adds mild unsupported framing (e.g. generic commentary not
                  drawn from the input).
  - 0 (fails)   : invents specifics — a manipulation technique, a tool, an
                  identity, a score for a branch marked "not evaluated".

Note the distinction between dimensions 1 and 3: (1) is about whether what it
says MATCHES the input; (3) is about whether it says things that were NOT in
the input at all. An explanation can be fully accurate about the scores (1=2)
while still inventing an unsupported detail (3=0).
"""


def build_cases(n, include_real_clips=False, threshold_T=THRESHOLD_T_DEFAULT):
    """Pilot cases: 'real' from the video branch on bundled clips, 'specified' score pairs covering the fusion decision space."""
    cases = []

    if include_real_clips:
        from pathlib import Path
        from video_infer import load_models, analyse_video_file
        root = Path(__file__).resolve().parent.parent
        clips = sorted((root / 'demo_videos').rglob('*.mp4'))
        if clips:
            mtcnn, model, device = load_models()
            for clip in clips:
                res = analyse_video_file(clip, mtcnn, model, device)
                if res is None:
                    continue
                cases.append({
                    'case_id': f'real-{len(cases)+1:02d}',
                    'source': 'real (live video branch, audio branch untrained)',
                    'p_video': round(res['p_fake'], 4),
                    'p_audio': None,
                    'note': f'clip: {clip.name}',
                })

    # Specified cases covering every branch of the fusion decision logic.
    T = threshold_T
    specified = [
        (0.97, None, 'video-only, confident FAKE (current pipeline state)'),
        (0.03, None, 'video-only, confident REAL (current pipeline state)'),
        (0.52, None, 'video-only, borderline just above 0.5'),
        (0.48, None, 'video-only, borderline just below 0.5'),
        (1.00, None, 'video-only, boundary value 1.0'),
        (0.00, None, 'video-only, boundary value 0.0'),
        (0.91, 0.88, 'agreement, both high -> FAKE'),
        (0.06, 0.11, 'agreement, both low -> REAL'),
        (0.55, 0.49, 'agreement, both near the decision boundary'),
        (0.95, 0.20, 'disagreement, video implicated (large gap)'),
        (0.15, 0.80, 'disagreement, audio implicated (large gap)'),
        (0.70, 0.70 - T - 0.01, 'disagreement, marginal (just over T)'),
        (0.60, 0.60 - T + 0.01, 'agreement, marginal (just under T)'),
        (0.99, 0.01, 'disagreement, maximal gap'),
        (0.40, 0.62, 'disagreement, audio implicated, both mid-range'),
        (0.80, 0.05, 'disagreement, video implicated, audio very low'),
    ]
    for pv, pa, note in specified:
        if len(cases) >= n:
            break
        cases.append({
            'case_id': f'spec-{len([c for c in cases if c["source"].startswith("specified")])+1:02d}',
            'source': 'specified (NOT a real detection — audio branch untrained)',
            'p_video': pv,
            'p_audio': round(pa, 4) if pa is not None else None,
            'note': note,
        })

    return cases[:n]


def build_cases_from_results(results_path, n=50, seed=42, threshold_T=THRESHOLD_T_DEFAULT):
    """Cases drawn at random (fixed seed) from saved 4-condition results. Ground truth stays in metadata and is never shown to raters."""
    d = json.load(open(results_path))
    clips = d['per_clip_results']
    if n > len(clips):
        raise ValueError(f'asked for {n} cases but {results_path} has only {len(clips)} clips')
    rng = random.Random(seed)
    picked = rng.sample(clips, n)
    cases = []
    for i, c in enumerate(picked, 1):
        cases.append({
            'case_id': f'eval-{i:02d}',
            'source': f'evaluation set (real pipeline scores), results file {Path(results_path).name}, sample seed {seed}',
            'p_video': None if c.get('p_video') is None else round(float(c['p_video']), 4),
            'p_audio': None if c.get('p_audio') is None else round(float(c['p_audio']), 4),
            'note': 'evaluation-set clip (clip id withheld: it encodes the ground-truth category)',
            'meta': {'clip_id': c['id'], 'category': c.get('category'), 'video_label': c.get('video_label'),
                     'audio_label': c.get('audio_label')},
            'output_path': c.get('output_path'),
        })
    return cases


def anomalies_for_cases(cases, project_root):
    """Real timing windows per case, by re-running the video branch on each clip as the server does.
    Cases with no clip or no face are left out (the caller then gets None, 'not available')."""
    from video_infer import load_models, analyse_video_file
    sys.path.insert(0, str(project_root))
    import server as server_module           # reuses the exact _frame_anomalies / fps-probing the app itself uses
    import imageio_ffmpeg

    mtcnn, model, device = load_models()
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    out = {}
    for i, c in enumerate(cases, 1):
        if not c.get('output_path'):
            continue
        path = project_root / c['output_path']
        video_result = analyse_video_file(str(path), mtcnn, model, device, max_faces=20)
        if video_result is None:
            continue
        _duration, fps = server_module._probe_duration_and_fps(str(path), ffmpeg_exe)
        out[c['case_id']] = server_module._frame_anomalies(video_result['per_frame'], fps)
        print(f'  [timing {i}/{len(cases)}] {c["case_id"]}: {len(out[c["case_id"]])} window(s)')
    return out


def cmd_generate(args):
    if not explanation_available():
        print('ERROR: local LLM not reachable. Start it with `ollama serve`.')
        return 1

    out_dir = Path(args.out_dir) if args.out_dir else EVAL_DIR
    if (out_dir / 'cases.json').exists() and not args.overwrite:
        print(f'ERROR: {out_dir / "cases.json"} already exists (an earlier pilot, made with an earlier model). Move that folder '
              f'aside (for example to {out_dir}_pilot_old_model), write elsewhere with --out-dir, or pass --overwrite.')
        return 2
    if args.from_results:
        rp = Path(args.from_results)
        shipped = Path(__file__).resolve().parent.parent / 'models' / 'shipped_model.json'
        if shipped.exists() and rp.stat().st_mtime < shipped.stat().st_mtime and not args.allow_stale:
            print(f'ERROR: {rp} is older than models/shipped_model.json, so its scores come from an earlier video model. '
                  'Re-run the four-condition evaluation on the shipped model first (or pass --allow-stale).')
            return 2
        cases = build_cases_from_results(rp, args.n, args.seed)
    else:
        cases = build_cases(args.n, args.include_real_clips)
    os.makedirs(out_dir, exist_ok=True)

    anomalies_by_case = {}
    if getattr(args, 'with_timing', False):
        if not args.from_results:
            print('ERROR: --with-timing needs --from-results (it re-runs the video branch on each case\'s real clip).')
            return 2
        print(f'Computing real anomaly timing for {len(cases)} case(s) (loads the video model once)…')
        anomalies_by_case = anomalies_for_cases(cases, Path(__file__).resolve().parent.parent)

    print(f'Generating explanations for {len(cases)} case(s)…')
    records = []
    for i, c in enumerate(cases, 1):
        result = fuse(c['p_video'], c['p_audio'])
        anomalies = anomalies_by_case.get(c['case_id'])                # None unless --with-timing found real windows
        structured = build_structured_input(result, anomalies)
        text = explain(result, anomalies=anomalies)
        screen = check_faithfulness(text, structured)          # supplementary: would the app have shown this text?
        records.append({**c, 'structured_input': structured, 'explanation': text, 'faithfulness_screen': screen,
                        'anomalies': anomalies})
        print(f'  [{i}/{len(cases)}] {c["case_id"]}: {"screen PASS" if screen["passed"] else "screen FAIL"}: {text[:60]}…')

    # Machine-readable record of exactly what was shown to the raters.
    with open(out_dir / 'cases.json', 'w') as f:
        n_fail = sum(1 for r in records if not r['faithfulness_screen']['passed'])
        json.dump({'generated': date.today().isoformat(),
                   'n_cases': len(records),
                   'protocol': 'full (evaluation-set sample)' if args.from_results else 'pilot (specified and demo cases)',
                   'results_file': str(args.from_results) if args.from_results else None,
                   'sample_seed': args.seed if args.from_results else None,
                   'faithfulness_screen_rejections': n_fail,
                   'records': records}, f, indent=2)
        print(f'\nAutomatic faithfulness screen would have rejected {n_fail} of {len(records)} explanations '
              f'({100 * n_fail / max(1, len(records)):.0f}%); those would be replaced by the template in the app.')

    # Rating packet (what the raters actually read).
    lines = [f'# Explanation-layer rating packet ({len(records)} cases)\n',
             f'Generated: {date.today().isoformat()}\n',
             '**Instructions.** Score every case on all three dimensions using the',
             'rubric below. Work through the cases IN ORDER and do NOT discuss them',
             'with the other rater until both sheets are complete — the whole point',
             'of Cohen\'s Kappa is that the two ratings are independent.\n',
             'Record your scores in your own CSV sheet',
             '(`rating_sheet_rater1.csv` or `rating_sheet_rater2.csv`).\n',
             RUBRIC, '\n---\n']

    for r in records:
        si = r['structured_input']
        lines += [
            f'### Case `{r["case_id"]}`\n',
            f'*Source: {r["source"]}*  \n*{r["note"]}*\n',
            '**Structured input given to the model:**\n',
            '```',
            f'  verdict             : {si["verdict"]}',
            f'  video branch P(fake): {si["video_score"]}',
            f'  video anomaly timing: {si.get("video_anomaly_timing", "not available")}',
            f'  audio branch P(fake): {si["audio_score"]}',
            f'  branches disagree   : {si["disagreement"]}',
            f'  modality implicated : {si["implicated_modality"]}',
            '```\n',
            '**Generated explanation:**\n',
            f'> {r["explanation"]}\n',
            '| Dimension | Your score (0/1/2) |',
            '|---|---|',
            '| Factual grounding | |',
            '| Score accuracy | |',
            '| Absence of hallucination | |',
            '\n---\n',
        ]

    with open(out_dir / 'rating_packet.md', 'w') as f:
        f.write('\n'.join(lines))

    # Blank CSV sheets, one per rater.
    for rater in ('rater1', 'rater2'):
        path = out_dir / f'rating_sheet_{rater}.csv'
        if path.exists() and not args.overwrite:
            print(f'  (kept existing {path.name}; pass --overwrite to regenerate)')
            continue
        with open(path, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['case_id'] + DIMENSIONS + ['notes'])
            for r in records:
                w.writerow([r['case_id'], '', '', '', ''])

    print(f'\nWrote: {out_dir / "cases.json"}')
    print(f'Wrote: {out_dir / "rating_packet.md"}   <- give this to both raters')
    print(f'Wrote: {out_dir / "rating_sheet_rater1.csv"}')
    print(f'Wrote: {out_dir / "rating_sheet_rater2.csv"}')
    print('\nNext: both raters fill in their sheet independently, then run:')
    print('  python scripts/explanation_eval.py score \\\n'
          f'      --rater1 {out_dir / "rating_sheet_rater1.csv"} \\\n'
          f'      --rater2 {out_dir / "rating_sheet_rater2.csv"}')
    return 0


def _read_sheet(path):
    scores = {}
    with open(path, newline='') as f:
        for row in csv.DictReader(f):
            cid = (row.get('case_id') or '').strip()
            if not cid:
                continue
            vals = {}
            for d in DIMENSIONS:
                raw = (row.get(d) or '').strip()
                if raw == '':
                    continue
                try:
                    v = int(raw)
                except ValueError:
                    raise ValueError(f'{path}: case {cid}, {d}: '
                                     f'{raw!r} is not 0, 1 or 2')
                if v not in (0, 1, 2):
                    raise ValueError(f'{path}: case {cid}, {d}: '
                                     f'score {v} outside 0-2')
                vals[d] = v
            if vals:
                scores[cid] = vals
    return scores


def cmd_score(args):
    from sklearn.metrics import cohen_kappa_score
    import numpy as np

    r1 = _read_sheet(args.rater1)
    r2 = _read_sheet(args.rater2)

    common = sorted(set(r1) & set(r2))
    if not common:
        print('ERROR: no cases scored by BOTH raters. Are both sheets filled in?')
        return 1

    only1, only2 = sorted(set(r1) - set(r2)), sorted(set(r2) - set(r1))
    if only1 or only2:
        print(f'WARNING: skipping cases scored by only one rater '
              f'(rater1-only: {only1}, rater2-only: {only2})')

    lines = ['# Explanation-layer human evaluation — results\n',
             f'Cases scored by both raters: **{len(common)}**\n',
             'Dimensions scored 0 (fails) / 1 (partial) / 2 (passes), '
             'per Chapter 3.6.\n']

    lines += ['| Dimension | Rater 1 mean | Rater 2 mean | Raw agreement | '
              "Cohen's κ | Quadratic-weighted κ |", '|' + '---|' * 6]

    pooled_a, pooled_b = [], []
    degenerate = []
    paradoxical = []

    for d in DIMENSIONS:
        a = [r1[c][d] for c in common if d in r1[c] and d in r2[c]]
        b = [r2[c][d] for c in common if d in r1[c] and d in r2[c]]
        if not a:
            lines.append(f'| {d} | (unscored) | | | | |')
            continue
        pooled_a += a
        pooled_b += b

        agree = float(np.mean([x == y for x, y in zip(a, b)]))
        # Kappa is undefined (0/0) when neither rater's scores vary; report that instead of sklearn's misleading nan/0.
        if len(set(a)) == 1 and len(set(b)) == 1:
            k_txt = w_txt = '_undefined_'
            degenerate.append(d)
        else:
            k = cohen_kappa_score(a, b)
            try:
                w = cohen_kappa_score(a, b, weights='quadratic')
                w_txt = f'{w:.3f}'
            except Exception:
                w_txt = 'n/a'
            k_txt = f'{k:.3f}'
            # Kappa paradox: when nearly all ratings are identical, chance agreement is almost as high as observed,
            # so kappa collapses even though the raters agreed.
            if agree >= 0.8 and k < 0.4:
                paradoxical.append((d, agree, k))

        lines.append(f'| {d} | {np.mean(a):.2f} | {np.mean(b):.2f} | '
                     f'{agree:.1%} | {k_txt} | {w_txt} |')

    if pooled_a:
        agree_all = float(np.mean([x == y for x, y in zip(pooled_a, pooled_b)]))
        if len(set(pooled_a)) == 1 and len(set(pooled_b)) == 1:
            pooled_k = '_undefined_ (no score variance)'
        else:
            pooled_k = f'{cohen_kappa_score(pooled_a, pooled_b):.3f}'
        lines += ['', f'**Pooled across all dimensions** '
                      f'({len(pooled_a)} rating pairs): '
                      f'raw agreement {agree_all:.1%}, Cohen\'s κ {pooled_k}.']

    if degenerate:
        lines += ['', '> **Note on undefined κ.** For '
                  + ', '.join(f'`{d}`' for d in degenerate) +
                  ', both raters gave an identical score to every case, so there '
                  'is no score variance for chance-agreement to be estimated '
                  'against and Cohen\'s κ is mathematically undefined (0/0) — '
                  'this is the well-known kappa paradox, NOT a sign of poor '
                  'agreement. The honest reading is that the raters agreed '
                  'completely on a task with no observed disagreement; raw '
                  'agreement is the meaningful statistic here. A rubric that '
                  'produces no variance also cannot discriminate between '
                  'systems, which is itself a finding worth reporting.']

    if paradoxical:
        lines += ['', '> **Note on low κ alongside high agreement.** For '
                  + ', '.join(f'`{d}` (agreement {a:.0%}, κ {k:.3f})'
                              for d, a, k in paradoxical) +
                  ', the raters agreed on the large majority of cases yet κ is '
                  'low or negative. This is the kappa paradox: when nearly every '
                  'rating takes the same value, the chance-agreement term is '
                  'estimated as almost as large as the observed agreement, so κ '
                  'collapses. Reporting such a κ as "poor inter-rater agreement" '
                  'would be a misreading — quote the raw agreement alongside it, '
                  'and treat κ as uninformative under this marginal distribution. '
                  'It is a property of a task where almost everything passes, not '
                  'evidence that the raters disagreed.']

    # Cases where the raters diverged: the useful qualitative material.
    disagreements = [(c, d, r1[c][d], r2[c][d]) for c in common
                     for d in DIMENSIONS
                     if d in r1[c] and d in r2[c] and r1[c][d] != r2[c][d]]
    if disagreements:
        lines += ['', '## Cases where the raters disagreed\n',
                  '| Case | Dimension | Rater 1 | Rater 2 |', '|---|---|---|---|']
        for c, d, x, y in disagreements:
            lines.append(f'| {c} | {d} | {x} | {y} |')
        lines += ['', 'These are the cases to discuss when refining the rubric '
                      'wording — each one marks a point where the descriptors '
                      'were not specific enough to force the same reading.']
    else:
        lines += ['', '_No rating disagreements between the two raters._']

    md = '\n'.join(lines) + '\n'
    os.makedirs(EVAL_DIR, exist_ok=True)
    out = EVAL_DIR / 'human_eval_results.md'
    with open(out, 'w') as f:
        f.write(md)
    print(md)
    print(f'Wrote: {out}')
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)

    g = sub.add_parser('generate', help='generate explanations + rating sheets')
    g.add_argument('--n', type=int, default=16,
                   help='number of cases (Ch3.6 specifies 50 for the full run)')
    g.add_argument('--include-real-clips', action='store_true',
                   help='also run the live video branch over the bundled demo '
                        'clips (needs the env with facenet_pytorch; uses MPS)')
    g.add_argument('--overwrite', action='store_true',
                   help='regenerate rating sheets even if they already exist')
    g.add_argument('--from-results', default=None,
                   help='draw the cases at random from this four-condition results JSON (the PPR 3.6 protocol; use --n 50)')
    g.add_argument('--seed', type=int, default=42, help='random-sample seed for --from-results (recorded in cases.json)')
    g.add_argument('--out-dir', default=None, help='write here instead of results/explanation_eval')
    g.add_argument('--allow-stale', action='store_true',
                   help='allow --from-results with a file older than models/shipped_model.json')
    g.add_argument('--with-timing', action='store_true',
                   help='re-run the real video branch on each --from-results case\'s clip to get real, timestamped '
                        'anomaly windows (server._frame_anomalies), so the explanation may state WHEN elevated '
                        'likelihood occurred; needs the app environment (loads MTCNN + the shipped classifier)')
    g.set_defaults(func=cmd_generate)

    s = sub.add_parser('score', help='score two completed rating sheets')
    s.add_argument('--rater1', required=True)
    s.add_argument('--rater2', required=True)
    s.set_defaults(func=cmd_score)

    args = ap.parse_args()
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
