"""Build the rater-facing form for the 50-case explanation evaluation (Draft Report Ch 3.6): one self-contained HTML file.

Each rater opens `results/explanation_eval_full/rating_form.html` in any browser (offline, no account), chooses Rater 1 or Rater 2,
scores every case on the three rubric dimensions, and downloads `rating_sheet_rater1.csv` / `rating_sheet_rater2.csv` in exactly the
format `scripts/score_explanation_eval.py` reads. Progress is kept in that browser only.

What a rater sees per case: the structured input the explanation model was given (all seven fields Chapter 3.4 specifies, including the
two deterministic "leans genuine / leans fake" readings that the markdown packet leaves out) and the generated explanation. What a rater
never sees: the clip id, the ground-truth category or labels, the raw probabilities beyond the input, and any automated check result.
`tests/test_rating_form.py` checks that none of those can leak into the page.

The two worked examples are real Llama 3 outputs from clips that are NOT among the 50, filled in to show the method; they are not
part of the evaluation and are never written to either CSV.

    /opt/anaconda3/bin/python scripts/build_rating_form.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / 'results' / 'explanation_eval_full'

FACT_FIELDS = (('verdict', 'Verdict'), ('video_score', 'Video branch P(fake)'), ('video_assessment', 'Video reading'),
               ('video_anomaly_timing', 'Video anomaly timing'), ('audio_score', 'Audio branch P(fake)'),
               ('audio_assessment', 'Audio reading'), ('disagreement', 'Branches disagree'),
               ('implicated_modality', 'Modality implicated'))

# Real outputs of the live app on 2026-09-21 (clip FVFA_002 and the AI-generated upload veo_sailor), neither among the 50 cases.
EXAMPLES = [
    {'title': 'Example A',
     'facts': {'verdict': 'FAKE', 'video_score': '0.947', 'video_assessment': 'leans FAKE (manipulated)',
               'video_anomaly_timing': '0:00 to 0:03 (peak 1.00), 0:04 to 0:06 (peak 1.00)',
               'audio_score': 'not evaluated', 'audio_assessment': 'was not evaluated', 'disagreement': 'no',
               'implicated_modality': 'none'},
     'text': ('The video is considered fake with a high likelihood of 0.947. The video branch leans towards being '
              'manipulated. There are two time windows where the likelihood of manipulation peaks, from 0:00 to 0:03 '
              'and from 0:04 to 0:06. The audio branch was not evaluated, so the verdict is based solely on the video '
              'branch.'),
     'scores': {'factual_grounding': 2, 'score_accuracy': 2, 'absence_of_hallucination': 2},
     'why': {'factual_grounding': ('The video leans fake, matching the verdict, the audio is correctly stated as not '
                                   'evaluated, and the two time windows quoted exactly match the two windows given.'),
             'score_accuracy': '0.947 is stated as "a likelihood", not a certainty, and both time windows are given exactly.',
             'absence_of_hallucination': ('It says WHEN elevated likelihood occurred (matching the windows given) but '
                                          'never WHAT is visible at those times: no blinking, lighting or other visual '
                                          'detail, since that was never given to it. Saying WHAT would be a hallucination '
                                          'even if the time is correct.')}},
    {'title': 'Example B',
     'facts': {'verdict': 'PARTIAL_MANIPULATION', 'video_score': '0.243', 'video_assessment': 'leans GENUINE (not manipulated)',
               'video_anomaly_timing': 'not available',
               'audio_score': '0.973', 'audio_assessment': 'leans FAKE (manipulated)', 'disagreement': 'yes',
               'implicated_modality': 'audio'},
     'text': ('The analysis suggests that the video and audio content are partially manipulated. The video branch leans towards '
              'being genuine, with a likelihood of 0.243, while the audio branch leans towards being fake, with a likelihood of '
              '0.973. The branches disagree, with the audio modality flagged as more likely manipulated.'),
     'scores': {'factual_grounding': 1, 'score_accuracy': 1, 'absence_of_hallucination': 2},
     'why': {'factual_grounding': ('The first sentence can be read as saying the video is manipulated too, but the facts say the video '
                                   'leans genuine and only the audio is implicated. The rest is accurate, so it overreaches rather '
                                   'than flatly contradicting: 1.'),
             'score_accuracy': ('Both numbers are correct, but 0.243 is the likelihood of FAKE, and the sentence attaches it to '
                                '"genuine", so a reader could take it as a 24% chance of being genuine. Correct value, misleading '
                                'framing: 1.'),
             'absence_of_hallucination': 'No technique, tool, identity or extra detail is invented: 2.'}},
]


def load_cases():
    d = json.load(open(DIR / 'cases.json'))
    out = []
    for r in d['records']:
        s = r['structured_input']
        out.append({'id': r['case_id'], 'facts': {k: s[k] for k, _ in FACT_FIELDS}, 'text': r['explanation']})
    out.sort(key=lambda c: int(c['id'].split('-')[1]))
    return out


def build(cases, dest):
    payload = json.dumps({'fields': FACT_FIELDS, 'cases': cases, 'examples': EXAMPLES}).replace('</', '<\\/')
    html = TEMPLATE.replace('__DATA__', payload).replace('__N__', str(len(cases)))
    Path(dest).write_text(html)
    return dest


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Explanation Rating Form</title>
<style>
:root {
  --bg: #f6f5f2; --surface: #ffffff; --surface-2: #f0eee9; --text: #1d1d1b; --muted: #5d5b55; --line: #dedbd3;
  --accent: #2f5d8a; --accent-soft: #e3ecf5; --ok: #2e7d4f; --warn: #a3661a; --bad: #b3372f; --focus: #2f5d8a;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #151514; --surface: #1f1f1d; --surface-2: #2a2a27; --text: #ecebe6; --muted: #a8a59c; --line: #3a3935;
    --accent: #8db6de; --accent-soft: #23313f; --ok: #6cc58f; --warn: #e0a95a; --bad: #ec7a70; --focus: #8db6de;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text);
  font: 16px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
main { max-width: 820px; margin: 0 auto; padding: 28px 16px 140px; }
h1 { font-size: 1.6rem; margin: 0 0 6px; letter-spacing: -0.01em; }
h2 { font-size: 1.15rem; margin: 36px 0 12px; }
p { margin: 0 0 10px; }
.lede { color: var(--muted); margin-bottom: 20px; }
.card { background: var(--surface); border: 1px solid var(--line); border-radius: 10px; padding: 18px 18px 16px; margin: 0 0 14px; }
.card.done { border-color: color-mix(in srgb, var(--ok) 45%, var(--line)); }
.card.missing { border-color: var(--bad); box-shadow: 0 0 0 2px color-mix(in srgb, var(--bad) 25%, transparent); }
.card.example { background: var(--surface-2); }
.case-head { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; margin-bottom: 10px; }
.case-head h3 { font-size: 1rem; margin: 0; }
.tag { font-size: 0.78rem; color: var(--muted); }
.tag.ok { color: var(--ok); font-weight: 600; }
.tag.ex { color: var(--accent); font-weight: 600; }
ol, ul { margin: 0 0 10px; padding-left: 22px; }
li { margin-bottom: 4px; }
.facts { display: grid; grid-template-columns: max-content 1fr; gap: 3px 16px; margin: 0 0 12px; padding: 10px 12px;
  background: var(--surface-2); border-radius: 8px; font-size: 0.92rem; }
.card.example .facts { background: var(--surface); }
.facts dt { color: var(--muted); }
.facts dd { margin: 0; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.88rem; }
.label { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--muted); margin: 0 0 4px; }
blockquote { margin: 0 0 14px; padding: 10px 14px; border-left: 3px solid var(--accent); background: var(--accent-soft);
  border-radius: 0 8px 8px 0; }
.dim { display: grid; grid-template-columns: 190px 1fr; gap: 8px 12px; align-items: center; padding: 8px 0;
  border-top: 1px solid var(--line); }
.dim-name { font-weight: 600; font-size: 0.93rem; }
.opts { display: flex; gap: 6px; flex-wrap: wrap; }
.opt { position: relative; }
.opt input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.opt span { display: inline-block; padding: 6px 12px; border: 1px solid var(--line); border-radius: 999px; cursor: pointer;
  font-size: 0.88rem; background: var(--surface); user-select: none; }
.opt input:focus-visible + span { outline: 2px solid var(--focus); outline-offset: 2px; }
.opt input:checked + span { background: var(--accent); border-color: var(--accent); color: var(--surface); font-weight: 600; }
.opt input:disabled + span { cursor: default; }
.why { grid-column: 2; font-size: 0.86rem; color: var(--muted); }
textarea { width: 100%; min-height: 54px; margin-top: 10px; padding: 8px 10px; border: 1px solid var(--line); border-radius: 8px;
  background: var(--surface); color: var(--text); font: inherit; font-size: 0.9rem; resize: vertical; }
.rubric-dim { margin-bottom: 12px; }
.rubric-dim b { display: block; margin-bottom: 2px; }
.score-line { font-size: 0.92rem; }
.setup { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
.bar { position: fixed; left: 0; right: 0; bottom: 0; background: var(--surface); border-top: 1px solid var(--line);
  padding: 12px 16px; }
.bar-inner { max-width: 820px; margin: 0 auto; display: flex; gap: 14px; align-items: center; flex-wrap: wrap; }
.progress { flex: 1 1 220px; }
.progress-track { height: 6px; border-radius: 3px; background: var(--surface-2); overflow: hidden; margin-top: 4px; }
.progress-fill { height: 100%; width: 0; background: var(--ok); transition: width .2s; }
button { font: inherit; font-size: 0.92rem; border-radius: 8px; padding: 9px 16px; cursor: pointer; border: 1px solid var(--line);
  background: var(--surface); color: var(--text); }
button.primary { background: var(--accent); border-color: var(--accent); color: var(--surface); font-weight: 600; }
button:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
.msg { font-size: 0.88rem; color: var(--bad); flex-basis: 100%; }
.msg.good { color: var(--ok); }
@media (max-width: 600px) {
  .dim { grid-template-columns: 1fr; gap: 6px; }
  .why { grid-column: 1; }
  .facts { grid-template-columns: 1fr; gap: 0; }
  .facts dd { margin-bottom: 6px; }
}
</style>
</head>
<body>
<main>
  <h1>Explanation Rating Form</h1>
  <p class="lede">A deepfake-detection system looks at a video and produces a few facts: a verdict and two scores. An AI language
  model then writes a short plain-English explanation of those facts. Your job is to judge whether each explanation is faithful
  to the facts it was given. There are __N__ cases; it usually takes 30 to 45 minutes.</p>

  <div class="card">
    <p class="label">Step 1: who are you rating as?</p>
    <div class="setup" role="radiogroup" aria-label="Rater number">
      <label class="opt"><input type="radio" name="rater" value="1"><span>Rater 1</span></label>
      <label class="opt"><input type="radio" name="rater" value="2"><span>Rater 2</span></label>
      <span class="tag">Use the number you were given. It only sets the name of the file you download.</span>
    </div>
  </div>

  <div class="card">
    <p class="label">Step 2: the rules</p>
    <ol>
      <li><b>Judge each explanation only against the facts box above it.</b> Not against whether you think the video is really fake;
        you are not shown the video.</li>
      <li>Work through the cases in order.</li>
      <li>Do not discuss the cases with the other rater until you have both downloaded your answers. The two ratings must be
        independent.</li>
      <li>Every case needs all three scores. Notes are optional but help when a score is borderline.</li>
      <li>Your answers are saved in this browser as you go, so you can close the page and come back on the same device.</li>
    </ol>
  </div>

  <div class="card">
    <p class="label">Reading the facts box</p>
    <ul>
      <li><b>P(fake)</b> is the probability, from 0 to 1, that the system gives to that part being <b>manipulated</b>. 0.5 is the
        line: below it the part "leans genuine", at or above it "leans fake". The two "reading" lines state this for you.</li>
      <li><b>Verdict</b> is REAL, FAKE, or PARTIAL_MANIPULATION (the two parts disagree, and the "implicated" part is the one more
        likely to be manipulated).</li>
      <li><b>not evaluated</b> means that part produced no score (for example, the clip has no speech).</li>
      <li><b>Video anomaly timing</b> lists real moments in the clip where the video's per-frame score was elevated, with a
        peak likelihood for each. "not available" means no timing data was supplied for this case; "no elevated-likelihood
        windows detected" means it was checked and there were none. The AI may say <b>WHEN</b> elevated likelihood occurred
        using these exact times, but must never say <b>WHAT</b> is visible then (no blinking, lighting, lip movement, or
        any other description), because it was never given a description of the frame, only a time and a number. Treat
        any such description as inventing a fact: score it 0 on absence of hallucination.</li>
    </ul>
  </div>

  <h2>The three scores</h2>
  <div class="card" id="rubric">
    <div class="rubric-dim"><b>1. Factual grounding: does every claim match the facts?</b>
      <div class="score-line">2 = every statement can be traced to the facts &middot; 1 = mostly grounded, but one statement
        overreaches or is vague enough to mislead &middot; 0 = contains a claim that contradicts the facts</div></div>
    <div class="rubric-dim"><b>2. Score accuracy: are the numbers right, and given as likelihoods rather than certainties?</b>
      <div class="score-line">2 = values stated accurately (a decimal or its percentage both count) and framed as a likelihood
        &middot; 1 = value correct but framed too strongly ("this is fake" rather than "likely fake") or misleadingly &middot;
        0 = a wrong number, or certainty asserted from a probability</div></div>
    <div class="rubric-dim"><b>3. Absence of hallucination: does it avoid adding anything new?</b>
      <div class="score-line">2 = adds nothing beyond the facts &middot; 1 = adds mild unsupported framing (generic commentary)
        &middot; 0 = invents specifics: a manipulation technique, a tool, an identity, a description of what is visible at a
        given time, or a score for a part marked "not evaluated"</div></div>
    <p class="tag">Score 1 is about whether what it says <i>matches</i> the facts; score 3 is about whether it says things that are
      <i>not in the facts at all</i>. An explanation can get every number right and still invent a detail.</p>
  </div>

  <h2>Two worked examples</h2>
  <p class="lede">These are filled in to show how the rubric is applied. They are real explanations from clips that are
    <b>not</b> among the __N__ cases, and they are not part of your answers.</p>
  <div id="examples"></div>

  <h2>Your __N__ cases</h2>
  <div id="cases"></div>
</main>

<div class="bar">
  <div class="bar-inner">
    <div class="progress">
      <div><b id="count">0</b> of __N__ cases complete</div>
      <div class="progress-track"><div class="progress-fill" id="fill"></div></div>
    </div>
    <button type="button" id="reset">Start over</button>
    <button type="button" class="primary" id="download">Download my ratings</button>
    <div class="msg" id="msg" role="status" aria-live="polite"></div>
  </div>
</div>

<script type="application/json" id="data">__DATA__</script>
<script>
(function () {
  const DATA = JSON.parse(document.getElementById('data').textContent);
  const DIMS = [['factual_grounding', 'Factual grounding'], ['score_accuracy', 'Score accuracy'],
                ['absence_of_hallucination', 'Absence of hallucination']];
  const OPT_LABEL = {0: '0 · fails', 1: '1 · partly', 2: '2 · passes'};
  const KEY = 'deepfake-explanation-rating-v1';
  let state = { rater: null, answers: {} };
  try { const s = JSON.parse(localStorage.getItem(KEY) || 'null'); if (s && s.answers) state = s; } catch (e) {}
  const save = () => { try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {} };

  function el(tag, attrs, children) {
    const n = document.createElement(tag);
    Object.entries(attrs || {}).forEach(([k, v]) => { if (k === 'text') n.textContent = v; else n.setAttribute(k, v); });
    (children || []).forEach(c => n.appendChild(c));
    return n;
  }
  function factsBox(facts) {
    const dl = el('dl', {class: 'facts'});
    DATA.fields.forEach(([key, label]) => { dl.appendChild(el('dt', {text: label})); dl.appendChild(el('dd', {text: facts[key]})); });
    return dl;
  }
  function body(card, facts, text) {
    card.appendChild(el('p', {class: 'label', text: 'Facts the AI was given'}));
    card.appendChild(factsBox(facts));
    card.appendChild(el('p', {class: 'label', text: 'Explanation it wrote'}));
    card.appendChild(el('blockquote', {text: text}));
  }

  // Worked examples (read-only)
  const exWrap = document.getElementById('examples');
  DATA.examples.forEach((ex, i) => {
    const card = el('section', {class: 'card example', 'aria-label': ex.title});
    card.appendChild(el('div', {class: 'case-head'}, [el('h3', {text: ex.title}), el('span', {class: 'tag ex', text: 'Example, filled in'})]));
    body(card, ex.facts, ex.text);
    DIMS.forEach(([key, name]) => {
      const row = el('div', {class: 'dim'});
      row.appendChild(el('div', {class: 'dim-name', text: name}));
      const opts = el('div', {class: 'opts'});
      [0, 1, 2].forEach(v => {
        const input = el('input', {type: 'radio', name: `ex${i}-${key}`, value: String(v), disabled: ''});
        if (ex.scores[key] === v) input.checked = true;
        opts.appendChild(el('label', {class: 'opt'}, [input, el('span', {text: OPT_LABEL[v]})]));
      });
      row.appendChild(opts);
      row.appendChild(el('div', {class: 'why', text: 'Why: ' + ex.why[key]}));
      card.appendChild(row);
    });
    exWrap.appendChild(card);
  });

  // The cases
  const wrap = document.getElementById('cases');
  const cards = {};
  DATA.cases.forEach((c, i) => {
    const a = state.answers[c.id] || (state.answers[c.id] = {notes: ''});
    const status = el('span', {class: 'tag'});
    const card = el('section', {class: 'card', id: c.id, 'aria-label': `Case ${i + 1}`});
    card.appendChild(el('div', {class: 'case-head'}, [el('h3', {text: `Case ${i + 1} of ${DATA.cases.length}`}), status]));
    body(card, c.facts, c.text);
    DIMS.forEach(([key, name]) => {
      const row = el('div', {class: 'dim'});
      row.appendChild(el('div', {class: 'dim-name', id: `${c.id}-${key}-l`, text: name}));
      const opts = el('div', {class: 'opts', role: 'radiogroup', 'aria-labelledby': `${c.id}-${key}-l`});
      [0, 1, 2].forEach(v => {
        const input = el('input', {type: 'radio', name: `${c.id}-${key}`, value: String(v)});
        if (a[key] === v) input.checked = true;
        input.addEventListener('change', () => { a[key] = v; save(); refresh(); });
        opts.appendChild(el('label', {class: 'opt'}, [input, el('span', {text: OPT_LABEL[v]})]));
      });
      row.appendChild(opts);
      card.appendChild(row);
    });
    const notes = el('textarea', {placeholder: 'Notes (optional): anything borderline or worth explaining', 'aria-label': `Notes for case ${i + 1}`});
    notes.value = a.notes || '';
    notes.addEventListener('input', () => { a.notes = notes.value; save(); });
    card.appendChild(notes);
    wrap.appendChild(card);
    cards[c.id] = {card, status};
  });

  document.querySelectorAll('input[name=rater]').forEach(r => {
    if (state.rater === r.value) r.checked = true;
    r.addEventListener('change', () => { state.rater = r.value; save(); setMsg(''); });
  });

  const complete = id => DIMS.every(([k]) => [0, 1, 2].includes((state.answers[id] || {})[k]));
  function refresh() {
    let n = 0;
    DATA.cases.forEach(c => {
      const done = complete(c.id); if (done) n++;
      const {card, status} = cards[c.id];
      card.classList.toggle('done', done); if (done) card.classList.remove('missing');
      status.textContent = done ? 'complete' : 'not finished'; status.className = done ? 'tag ok' : 'tag';
    });
    document.getElementById('count').textContent = n;
    document.getElementById('fill').style.width = (100 * n / DATA.cases.length) + '%';
    return n;
  }
  function setMsg(t, good) { const m = document.getElementById('msg'); m.textContent = t; m.className = good ? 'msg good' : 'msg'; }

  document.getElementById('download').addEventListener('click', () => {
    if (!state.rater) { setMsg('Choose Rater 1 or Rater 2 at the top first.'); window.scrollTo({top: 0, behavior: 'smooth'}); return; }
    const missing = DATA.cases.filter(c => !complete(c.id));
    if (missing.length) {
      missing.forEach(c => cards[c.id].card.classList.add('missing'));
      const nums = missing.map(c => DATA.cases.indexOf(c) + 1);
      setMsg(`${missing.length} case(s) still need all three scores: ${nums.slice(0, 12).join(', ')}${nums.length > 12 ? ` and ${nums.length - 12} more` : ''}.`);
      cards[missing[0].id].card.scrollIntoView({behavior: 'smooth', block: 'center'});
      return;
    }
    const q = s => '"' + String(s || '').replace(/\r?\n/g, ' ').replace(/"/g, '""') + '"';
    const lines = ['case_id,factual_grounding,score_accuracy,absence_of_hallucination,notes'];
    DATA.cases.forEach(c => { const a = state.answers[c.id];
      lines.push([c.id, a.factual_grounding, a.score_accuracy, a.absence_of_hallucination, q(a.notes)].join(',')); });
    const blob = new Blob([lines.join('\n') + '\n'], {type: 'text/csv'});
    const link = el('a', {href: URL.createObjectURL(blob), download: `rating_sheet_rater${state.rater}.csv`});
    document.body.appendChild(link); link.click(); link.remove();
    setMsg(`Downloaded rating_sheet_rater${state.rater}.csv. Send that file back to the student. Thank you!`, true);
  });

  document.getElementById('reset').addEventListener('click', () => {
    if (!confirm('Clear every answer on this page and start again?')) return;
    state = {rater: null, answers: {}}; save(); location.reload();
  });

  refresh();
})();
</script>
</body>
</html>
"""


def main():
    cases = load_cases()
    if len(cases) != 50:
        sys.exit(f'expected 50 cases in cases.json, found {len(cases)}')
    dest = build(cases, DIR / 'rating_form.html')
    print(f'{len(cases)} cases -> {dest}')


if __name__ == '__main__':
    main()
