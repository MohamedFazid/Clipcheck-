/* Clipcheck, interface v2 (2026-09-24). Vanilla JS, no framework; talks to the FastAPI backend in server.py.
 *
 * Honesty contract (unchanged from v1, several parts tested in tests/test_server.py):
 *  - every number shown is a real field from the server, or an explicit "not checked" state, never a made-up value;
 *  - the unfamiliar-input warning is shown whenever the server raises it, as prominently as the verdict;
 *  - the tool says WHEN the picture check was high, never WHAT is visible;
 *  - who wrote the explanation (the AI model, or standard wording) is always shown, with the reason for any fallback;
 *  - limits and technical detail are always one click away (Learn more), in plain words with a legend.
 * Wording follows the design brief (docs/user_testing/design_brief/) and the round 1 user-testing findings. */
'use strict';

const S = {
  demos: [], queue: [], results: {}, limits: null, limitations: null, evaluation: null, modelInfo: null,
  stats: null, fusion: null, typicalSeconds: null, testing: false,
  poll: null, pollId: null, startedAt: {}, showAllExamples: false, learnOpen: false, learnTab: 'legend',
  confirmDelete: null, busy: false,
};

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

// ── Icons (inline SVG, 24 x 24, stroke-based) ─────────────────────────────
const ICONS = {
  logo: '<path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><path d="M9 9h.01"/><path d="M15 9h.01"/>',
  upload: '<path d="M12 13v8"/><path d="m8 17 4-4 4 4"/><path d="M4 14.9A7 7 0 1 1 15.7 8h1.8a4.5 4.5 0 0 1 2.5 8.24"/>',
  film: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M7 3v18M17 3v18M3 7.5h4M3 12h18M3 16.5h4M17 7.5h4M17 16.5h4"/>',
  arrowRight: '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
  arrowLeft: '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
  fileDown: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M12 18v-6"/><path d="m9 15 3 3 3-3"/>',
  copy: '<rect x="8" y="8" width="14" height="14" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
  trash: '<path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><path d="M10 11v6M14 11v6"/>',
  sparkle: '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>',
  template: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M8 13h8M8 17h5"/>',
  face: '<path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><path d="M9 9h.01M15 9h.01"/>',
  voice: '<path d="M2 10v3M6 6v11M10 3v18M14 8v7M18 5v13M22 10v3"/>',
  scale: '<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10M12 3v18M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>',
  link: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
  replay: '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
  chevronDown: '<path d="m6 9 6 6 6-6"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  circle: '<circle cx="12" cy="12" r="9"/>',
  loader: '<path d="M21 12a9 9 0 1 1-6.22-8.56"/>',
  minus: '<path d="M5 12h14"/>',
  partial: '<circle cx="12" cy="12" r="9"/><path d="M12 3a9 9 0 0 1 0 18z" fill="currentColor"/>',
  genuine: '<circle cx="12" cy="12" r="9"/><path d="m8.5 12 2.5 2.5 4.5-5"/>',
  manip: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4M12 17h.01"/>',
  none: '<circle cx="12" cy="12" r="9"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3M12 17h.01"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/>',
  play: '<path d="M7 4.5v15l12-7.5z" fill="currentColor"/>',
  pause: '<path d="M7 4h3v16H7zM14 4h3v16h-3z" fill="currentColor"/>',
};
const icon = (name) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ''}</svg>`;

// ── Formatting ────────────────────────────────────────────────────────────
// A score of 0.9995 is shown as ">99%", not "100%", and 0.002 as "<1%": the tool never gives certainty.
function pct(p) {
  if (p == null || isNaN(p)) return 'n/a';
  if (p >= 0.995) return '>99%';
  if (p < 0.005) return '<1%';
  return `${Math.round(p * 100)}%`;
}
const lean = (p) => (p >= 0.5 ? 'Leans manipulated' : 'Leans genuine');
// Score bar colour: the whole fill is one colour picked from a green (0%) to amber (50%, unsure) to red (100%) scale (owner, 25 Sep).
// Distance from 50% is square-rooted so the colour leaves amber quickly: 60% is already an orange-red, 40% a yellow-green.
const METER_STOPS = [[63, 207, 127], [242, 178, 60], [240, 82, 74]];
function meterColor(p) {
  const d = p - 0.5, t = 0.5 + Math.sign(d) * Math.sqrt(Math.abs(d) * 2) / 2;
  const [a, b, f] = t < 0.5 ? [METER_STOPS[0], METER_STOPS[1], t * 2] : [METER_STOPS[1], METER_STOPS[2], (t - 0.5) * 2];
  return `rgb(${a.map((v, i) => Math.round(v + (b[i] - v) * f)).join(', ')})`;
}
function fmtTime(sec) {
  if (sec == null || isNaN(sec)) return '--:--';
  const m = Math.floor(sec / 60), s = Math.floor(sec % 60);
  return `${m}:${String(s).padStart(2, '0')}`;
}
// A suspicious moment shorter than a second reads "at 0:04", not "0:04 to 0:04" (heuristic finding HE-09).
function fmtWindow(a) {
  if (a.start == null) return `Frames ${a.frames || ''}`;
  const s = fmtTime(a.start), e = fmtTime(a.end);
  return s === e ? `at ${s}` : `${s} to ${e}`;
}
function fmtDateTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return isNaN(d) ? '' : d.toLocaleString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' });
}
const points = (x) => Math.round(x * 100);

// ── Testing mode: neutral example names (the round 1 clip codes), so a name cannot hint at the answer in a session ──
// Works on a fresh load and when the address is changed on an open page (both run through checkTestingSwitch).
function checkTestingSwitch() {
  const h = location.hash;
  try {
    if (h === '#testing' || /[?&]testing\b/.test(location.search)) sessionStorage.setItem('clipcheck-testing', '1');
    if (h === '#testing-off') sessionStorage.removeItem('clipcheck-testing');
    S.testing = sessionStorage.getItem('clipcheck-testing') === '1';
  } catch (e) { if (h === '#testing') S.testing = true; if (h === '#testing-off') S.testing = false; }
  if (h === '#testing' || h === '#testing-off') history.replaceState(null, '', '#/check');
}
checkTestingSwitch();

const demoFor = (filename) => S.demos.find(d => d.name === filename);
function displayName(filename) {
  const d = demoFor(filename);
  if (!d) return filename || 'Untitled clip';
  return S.testing ? d.code : d.title;
}

// ── Data loading ──────────────────────────────────────────────────────────
async function getJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
  return r.json();
}

// Headline figures for the Accuracy page and the legend, read from /api/evaluation (results/numbers.json), never typed in.
function deriveStats(ev) {
  const out = {};
  const sec = (pred) => (ev.sections || []).find(s => s.status === 'current' && pred(s));
  const num = (str) => { const m = String(str || '').match(/-?\d+(\.\d+)?/); return m ? parseFloat(m[0]) : null; };
  const cv = sec(s => s.id.startsWith('cv_'));
  const cvRow = cv && cv.rows.find(r => /^Accuracy/.test(r[0]));
  if (cvRow) {
    const [lo, hi] = String(cvRow[2]).match(/\d+(\.\d+)?/g).map(parseFloat);
    out.acc = num(cvRow[1]); out.lo = lo; out.hi = hi;
  }
  const cel = sec(s => s.id === 'celebdf');
  const celRow = cel && cel.rows.find(r => String(r[0]).includes('[SHIPPED]'));
  if (celRow) {
    const i = cel.columns.indexOf('Accuracy at 0.5'), j = cel.columns.indexOf('Real videos kept real');
    out.celebAcc = num(celRow[i]);
    if (j >= 0) out.celebFalseAlarm = 100 - num(celRow[j]);
  }
  const au = sec(s => s.id === 'audio');
  const auRow = au && au.rows.find(r => /used/.test(r[0]));
  if (auRow) {
    const m = String(auRow[auRow.length - 1]).match(/(\d+)% of (\d+)/);
    if (m) { out.voiceFlagged = Math.round(parseFloat(m[1]) * parseFloat(m[2]) / 100); out.voiceTotal = parseInt(m[2], 10); }
  }
  const lat = sec(s => s.id === 'latency');
  const latRow = lat && lat.rows.find(r => /^Total/.test(r[0]));
  if (latRow) S.typicalSeconds = Math.round(num(latRow[1]));
  return out;
}

async function loadStatic() {
  const [demos, ev, lim, mi, limits] = await Promise.allSettled([
    getJSON('/api/demo_clips'), getJSON('/api/evaluation'), getJSON('/api/limitations'), getJSON('/api/model_info'), getJSON('/api/limits')]);
  if (demos.status === 'fulfilled') S.demos = demos.value;
  if (ev.status === 'fulfilled') { S.evaluation = ev.value; S.fusion = ev.value.fusion || null; S.stats = deriveStats(ev.value); }
  if (lim.status === 'fulfilled') S.limitations = lim.value;
  if (mi.status === 'fulfilled') S.modelInfo = mi.value;
  if (limits.status === 'fulfilled') S.limits = limits.value;
}

async function refreshQueue() {
  try {
    const jobs = await getJSON('/api/queue');
    S.queue = jobs;
    await Promise.all(jobs.filter(j => j.status === 'done' && !S.results[j.id]).map(async j => {
      try { const r = await getJSON(`/api/result/${j.id}`); if (r && r.verdict !== undefined) S.results[j.id] = r; } catch (e) { /* listed without details */ }
    }));
  } catch (e) { /* keep the last known list */ }
}

// ── Verdict wording: one place decides the words for every state (design brief section 07) ─────────────────────────
function missingAudioReason(r) {
  const a = r.audio;
  if (!a || !a.available) return 'the clip has no sound';
  if (a.gated) return 'no speech was found';
  if (a.withheld) return 'the speech is unlike what the tool learned from, so its score was set aside';
  return 'the voice check gave no score';
}
function missingVideoReason(r) {
  if (!r.video) return 'no face was found';
  if (r.video.withheld) return 'the face footage is unlike what the tool learned from, so its score was set aside';
  return 'the picture check gave no score';
}
function describeVerdict(r) {
  const v = r.verdict;
  const pv = (r.video && r.video.p_fake != null) ? r.video.p_fake : null;
  const pa = (r.audio && r.audio.p_audio_fake != null) ? r.audio.p_audio_fake : null;
  const T = (r.fusion && r.fusion.threshold_T != null) ? r.fusion.threshold_T : (S.fusion ? S.fusion.threshold_T : null);
  const d = { pv, pa, T };
  if (v === 'INCONCLUSIVE') {
    const why = [missingVideoReason(r), missingAudioReason(r).replace('the voice check gave no score', 'there is no voice score')];
    return { ...d, tone: 'none', icon: 'none', headline: 'No verdict', chip: 'No verdict',
             reason: `The tool could not check this clip: ${why.join(' and ')}.`, gap: '' };
  }
  const gapPts = (pv != null && pa != null) ? points(Math.abs(pv - pa)) : null;
  if (v === 'PARTIAL_MANIPULATION') {
    const imp = r.fusion.implicated_modality === 'video' ? 'picture' : 'voice';
    const other = imp === 'picture' ? 'voice' : 'picture';
    let headline, reason;
    if (pv != null && pa != null && (pv >= 0.5) !== (pa >= 0.5)) {
      headline = `Partly manipulated: the ${imp}`;
      reason = imp === 'picture'
        ? 'The face looks manipulated but the voice sounds genuine, so only part of this clip may be fake.'
        : 'The voice sounds synthetic but the face looks genuine, so only part of this clip may be fake.';
    } else {
      headline = 'The checks disagree';
      reason = `The ${imp} looks more suspicious than the ${other}, ` +
        ((pv < 0.5 && pa < 0.5) ? 'although neither is clearly manipulated.' : 'although both lean manipulated.');
    }
    const gap = (gapPts != null && T != null)
      ? `The two checks are ${gapPts} points apart. At ${points(T)} or more, the tool reports ${term('partly manipulated', 'partly')} instead of averaging.` : '';
    return { ...d, tone: 'partial', icon: 'partial', headline, reason, gap, chip: headline };
  }
  const fake = v === 'FAKE';
  const headline = fake ? 'Likely manipulated' : 'Likely genuine';
  let reason, gap = '';
  if (pv != null && pa != null) {
    reason = fake ? 'The picture and voice checks agree, and together they point to manipulation.'
                  : 'The picture and voice checks agree, and together they point to a genuine clip.';
    if (gapPts != null && T != null && r.overall_score != null) {
      gap = `The two checks are ${gapPts} points apart, under the ${points(T)}-point line, so the tool ${term('combined', 'combined')} them: ` +
            `${pct(r.overall_score)} chance of manipulation overall.`;
    }
  } else if (pv != null) {
    reason = `Only the picture was checked, because ${missingAudioReason(r)}.`;
  } else {
    reason = `Only the voice was checked, because ${missingVideoReason(r)}.`;
  }
  return { ...d, tone: fake ? 'manip' : 'genuine', icon: fake ? 'manip' : 'genuine', headline, reason, gap, chip: headline };
}
function unfamiliarParts(r) {
  const out = [];
  if (r.video && r.video.ood && r.video.ood.unfamiliar && !r.video.withheld) out.push('face footage');
  if (r.audio && r.audio.ood && r.audio.ood.unfamiliar && !r.audio.withheld) out.push('speech');
  return out;
}
function chipFor(job) {
  const r = S.results[job.id];
  if (job.status === 'analyzing' || job.status === 'pending') return `<span class="chip tone-none">${icon('loader')} Checking</span>`;
  if (job.status === 'error' || (r && r.error)) return `<span class="chip tone-manip">${icon('info')} Could not check</span>`;
  if (r) { const d = describeVerdict(r); return `<span class="chip tone-${d.tone}">${icon(d.icon)} ${esc(d.chip)}</span>`; }
  const map = { REAL: ['genuine', 'Likely genuine'], FAKE: ['manip', 'Likely manipulated'], INCONCLUSIVE: ['none', 'No verdict'],
                PARTIAL_MANIPULATION: ['partial', 'Partly manipulated'] };
  const m = map[job.verdict];
  return m ? `<span class="chip tone-${m[0]}">${icon(m[0])} ${m[1]}</span>` : '';
}

// ── Legend (Learn more and the Accuracy page) ─────────────────────────────
function legendItems() {
  const T = S.fusion ? points(S.fusion.threshold_T) : null;
  const wv = S.fusion ? Math.round(S.fusion.w_video * 100) : null, wa = S.fusion ? Math.round(S.fusion.w_audio * 100) : null;
  const st = S.stats || {};
  const vname = videoModelName();
  return [
    ['deepfake', 'Deepfake', 'A video or audio clip changed by software to show someone doing or saying something they did not.', ''],
    ['manipulated', 'Manipulated', 'Changed after recording, for example a face swapped, a mouth re-animated or a voice replaced.', ''],
    ['picture', 'Picture check', 'The part of the tool that looks at the face in each sampled frame of the clip.', 'video branch'],
    ['voice', 'Voice check', 'The part of the tool that listens to the speech. It only runs when speech is found.', 'audio branch'],
    ['chance', 'Chance of manipulation', "The tool's estimate, from 0% to 100%, that a part of the clip was manipulated. It is an estimate, not proof. Near 50% means the tool is unsure.", 'P(fake)'],
    ['partly', 'Partly manipulated', `The picture and voice checks strongly disagree${T != null ? ` (${T} points or more apart)` : ''}, so only one part may have been changed. The tool names the part that looks more manipulated instead of averaging.`, 'PARTIAL_MANIPULATION (disagreement-aware fusion)'],
    ['combined', 'Combined score', `When the two checks agree, the tool combines them, giving slightly more weight to the check that was more accurate in testing${wv != null ? ` (voice ${wa}%, picture ${wv}%)` : ''}.`, 'accuracy-weighted late fusion'],
    ['noverdict', 'No verdict', 'The tool could not check the clip at all, for example when there is no face and no speech.', 'INCONCLUSIVE'],
    ['unfamiliar', 'Unfamiliar clip', 'The face footage or the speech is unlike anything the tool learned from, so its answer is less reliable. The warning does not change the verdict.', 'out-of-domain input, measured as a distance from the training data'],
    ['moments', 'Suspicious moments', "Times in the clip where the picture check's estimate was 50% or higher. The tool can say when, not what looks wrong.", 'anomaly windows'],
    ['faceswap', 'Face swap', "One person's face replaced with another's.", ''],
    ['lipsync', 'Lip-sync', 'The mouth re-animated to match different words. This tool does not measure lip-sync directly.', ''],
    ['synthetic', 'Voice cloning / synthetic speech', 'Speech generated by software to imitate a person or to sound human.', ''],
    ['explanation', 'Written explanation', 'A short summary written for each clip by an AI language model (Llama 3) from the results only. An automatic check compares it with the results; if it says anything the results do not support, the tool shows standard wording instead.', 'Llama 3 8B via Ollama, faithfulness screen'],
    ['standard', 'Standard wording', "A fixed, pre-written explanation filled in with this clip's results. Shown when the AI model's text did not pass the automatic check, or the model was not available.", 'deterministic template'],
    ['accuracy', 'Accuracy', st.acc != null ? `How often the tool was right in testing. About ${Math.round(st.acc)}% on people it had not seen, meaning roughly ${100 - Math.round(st.acc)} in 100 test videos were judged wrongly.` : 'How often the tool was right in testing.', ''],
    ['range', '95% range', st.lo != null ? `The range the true accuracy probably lies in, given the size of the test (${Math.round(st.lo)}% to ${Math.round(st.hi)}%).` : 'The range the true accuracy probably lies in, given the size of the test.', 'confidence interval'],
    ['falsealarm', 'False alarm', 'A genuine clip wrongly flagged as manipulated.', 'false positive'],
    ['training', 'Training data', 'The example videos and recordings the tool learned from: FaceForensics++ (faces) and ASVspoof 2019 (voices).', ''],
    ['model', 'Model', `A trained AI program that does one step. This tool chains six: MTCNN finds faces; ${vname} judges each face; Silero VAD finds speech; wav2vec2 turns speech into numbers; an SVM judges those numbers; Llama 3 8B writes the explanation.`, ''],
  ];
}
function term(label, key) {
  const item = legendItems().find(i => i[0] === key);
  return `<button type="button" class="term" data-term="${key}" title="${esc(item ? item[2] : '')}">${esc(label)}</button>`;
}
function legendGrid(prefix) {
  return `<div class="legend-grid">${legendItems().map(([key, t, def, tech]) => `
    <div class="legend-item" id="${prefix}-${key}"><h4>${esc(t)}</h4><p>${esc(def)}</p>
      ${tech ? `<p class="tech">Technical name: <code>${esc(tech)}</code></p>` : ''}</div>`).join('')}</div>`;
}
function videoModelName() {
  const v = S.modelInfo && S.modelInfo.models.find(m => m.stage === 'Video');
  return v ? v.name.split(' + ')[0] : 'the video model';
}
function flash(node) {
  if (!node) return;
  node.scrollIntoView({ behavior: 'smooth', block: 'center' });
  node.classList.add('flash');
  setTimeout(() => node.classList.remove('flash'), 1600);
}
document.addEventListener('click', (e) => {
  const t = e.target.closest('.term');
  if (!t) return;
  const key = t.dataset.term;
  if (!$('#view-result').hidden) {
    S.learnOpen = true; S.learnTab = 'legend'; applyLearnState();
    flash($(`#lr-${key}`));
  } else if (!$('#view-accuracy').hidden) {
    flash($(`#la-${key}`));
  }
});

// ── Router ────────────────────────────────────────────────────────────────
const VIEWS = ['check', 'analysing', 'result', 'history', 'accuracy'];
function parseRoute() {
  const parts = (location.hash || '#/check').replace(/^#\/?/, '').split('/');
  const view = VIEWS.includes(parts[0]) ? parts[0] : 'check';
  return { view, id: parts[1] || null };
}
async function render() {
  checkTestingSwitch();
  const { view, id } = parseRoute();
  if (view !== 'analysing') stopPolling();
  VIEWS.forEach(v => { $(`#view-${v}`).hidden = v !== view; });
  const navKey = (view === 'analysing' || view === 'result') ? 'check' : view;
  $$('.nav-link').forEach(a => a.classList.toggle('active', a.dataset.nav === navKey));
  $('#testing-flag').hidden = !S.testing;
  window.scrollTo(0, 0);
  if (view === 'check') { await refreshQueue(); renderCheck(); }
  if (view === 'history') { await refreshQueue(); renderHistory(); }
  if (view === 'accuracy') renderAccuracy();
  if (view === 'analysing') { if (!S.queue.some(j => j.id === id)) await refreshQueue(); renderAnalysing(id); }
  if (view === 'result') await showResult(id);
}
window.addEventListener('hashchange', render);

// ── Check a video ─────────────────────────────────────────────────────────
const GROUPS = [['RVRA', 'Genuine face and voice'], ['RVFA', 'Voice replaced'], ['FVRA', 'Face replaced'], ['FVFA', 'Face and voice replaced'],
                ['picture_only', 'No speech: only the picture can be checked'], ['unfamiliar', 'Unfamiliar footage (LAV-DF collection)'],
                ['no_verdict', 'Nothing to check']];
function exampleRow(d) {
  const title = S.testing ? d.code : d.title;
  const sub = S.testing ? 'Example clip' : d.subtitle;
  return `<button type="button" class="ex-row" data-demo="${d.demo_id}">
    <span class="ex-thumb">${icon('film')}</span>
    <span class="grow"><span class="row-title" style="display:block">${esc(title)}</span>
      <span class="row-sub" style="display:block">${esc(sub)}${d.duration ? ` · ${fmtTime(d.duration)}` : ''}</span></span>
    <span class="ex-arrow">${icon('arrowRight')}</span></button>`;
}
function renderCheck() {
  const featured = S.demos.filter(d => d.featured != null).sort((a, b) => a.featured - b.featured);
  let all = '';
  if (S.showAllExamples) {
    all = S.testing
      ? S.demos.filter(d => d.featured == null).map(exampleRow).join('')
      : GROUPS.map(([g, label]) => {
          const rows = S.demos.filter(d => d.group === g && d.featured == null);
          return rows.length ? `<div class="ex-group">${esc(label)}</div>${rows.map(exampleRow).join('')}` : '';
        }).join('');
  }
  const recent = S.queue.slice().reverse().slice(0, 3);
  const lim = S.limits;
  $('#view-check').innerHTML = `
    <div class="check-grid">
      <div>
        <div class="check-hero">
          <div class="eyebrow">Deepfake checker</div>
          <h1 id="check-title">Check a video</h1>
          <p class="lede">The tool checks the picture and the voice separately and says how likely each is to be manipulated. It gives a likelihood, not proof, and it cannot say how a clip was changed.</p>
        </div>
        <div class="dropzone" id="dropzone">
          <div class="dz-icon">${icon('upload')}</div>
          <div class="dz-title">Drop a video here</div>
          <div class="dz-limits">MP4, MOV, AVI or MKV${lim ? ` · up to ${lim.max_upload_mb} MB and ${lim.max_duration_s} seconds` : ''}</div>
          <button type="button" class="btn btn-primary" id="choose">Choose a file</button>
          <div class="dz-error" id="dz-error" role="alert" hidden></div>
        </div>
        <div class="section-head"><h2>Recent checks</h2>${S.queue.length ? '<a class="link" href="#/history">See all</a>' : ''}</div>
        ${recent.length ? `<div class="list">${recent.map(j => `
          <a class="list-row" href="${j.status === 'done' ? `#/result/${j.id}` : `#/analysing/${j.id}`}">
            <span class="grow row-title">${esc(displayName(j.filename))}</span>${chipFor(j)}</a>`).join('')}</div>`
          : '<div class="list"><div class="empty">No checks yet. Upload a video or try an example.</div></div>'}
      </div>
      <aside class="card examples" aria-label="Examples">
        <div class="examples-head"><h2>Try an example</h2><p>Sample clips that show each kind of result.</p></div>
        ${featured.map(exampleRow).join('')}
        ${all}
        <button type="button" class="ex-more" id="more">${S.showAllExamples ? 'Show fewer examples' : `Show all ${S.demos.length} examples`}</button>
      </aside>
    </div>`;
  const dz = $('#dropzone');
  $('#choose').onclick = () => $('#file-input').click();
  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('drag'));
  dz.addEventListener('drop', e => { e.preventDefault(); dz.classList.remove('drag'); if (e.dataTransfer.files[0]) uploadFile(e.dataTransfer.files[0]); });
  $('#more').onclick = () => { S.showAllExamples = !S.showAllExamples; renderCheck(); };
  $$('.ex-row').forEach(b => b.addEventListener('click', () => startExample(parseInt(b.dataset.demo, 10))));
}
function showUploadError(msg) {
  const n = $('#dz-error');
  if (!n) return;
  n.hidden = !msg;
  n.innerHTML = msg ? `<div class="notice error">${icon('info')}<span>${esc(msg)}</span></div>` : '';
}
$('#file-input').addEventListener('change', (e) => { const f = e.target.files[0]; e.target.value = ''; if (f) uploadFile(f); });
async function uploadFile(file) {
  if (S.busy) return;
  showUploadError('');
  const lim = S.limits;
  if (lim && file.size > lim.max_upload_mb * 1048576) {
    showUploadError(`"${file.name}" is ${(file.size / 1048576).toFixed(0)} MB; the limit is ${lim.max_upload_mb} MB. Trim or compress the clip and try again.`);
    return;
  }
  S.busy = true;
  try {
    const form = new FormData(); form.append('file', file);
    const resp = await fetch('/api/upload', { method: 'POST', body: form });
    const body = await resp.json().catch(() => ({}));
    if (!resp.ok) { showUploadError(body.detail || `The upload failed (HTTP ${resp.status}).`); return; }
    await startJob(body);
  } catch (err) {
    showUploadError('The upload failed: the tool could not be reached. Check that it is still running, then try again.');
  } finally { S.busy = false; }
}
async function startExample(demoId) {
  if (S.busy) return;
  S.busy = true;
  try { const job = await (await fetch(`/api/demo/${demoId}`, { method: 'POST' })).json(); await startJob(job); }
  catch (e) { showUploadError('That example could not be opened. Try again.'); }
  finally { S.busy = false; }
}
async function startJob(job) {
  S.startedAt[job.id] = Date.now();
  await fetch(`/api/analyze/${job.id}`, { method: 'POST' });
  location.hash = `#/analysing/${job.id}`;
}

// ── Analysing: real progress from /api/progress (server.py sets it at real stage transitions) ──────────────────────
const STEPS = [['faces', 'Finding faces'], ['face_check', 'Checking the face'], ['speech', 'Listening for speech'],
               ['voice', 'Checking the voice'], ['compare', 'Comparing the two checks'], ['explain', 'Writing the explanation']];
function stopPolling() { if (S.poll) { clearInterval(S.poll); S.poll = null; S.pollId = null; } }
function renderAnalysing(id) {
  const job = S.queue.find(j => j.id === id);
  const name = job ? displayName(job.filename) : 'Your clip';
  $('#view-analysing').innerHTML = `
    <div class="analysing">
      <div class="eyebrow">Analysing</div>
      <h1>${esc(name)}</h1>
      <p class="timing" id="an-timing"></p>
      <div class="bar" role="progressbar" aria-label="Progress" aria-valuemin="0" aria-valuemax="100"><span id="an-bar" style="width:0%"></span></div>
      <ol class="steps" id="an-steps"></ol>
      <div id="an-error"></div>
    </div>`;
  if (!S.startedAt[id]) S.startedAt[id] = Date.now();
  const tick = async () => {
    let p;
    try { p = await getJSON(`/api/progress/${id}`); }
    catch (e) { stopPolling(); $('#an-error').innerHTML = `<div class="notice error">${icon('info')}<span>This check is no longer available. <a href="#/check">Start again</a>.</span></div>`; return; }
    drawProgress(id, p);
    if (p.status === 'done' || p.status === 'error') {
      stopPolling();
      try { S.results[id] = await getJSON(`/api/result/${id}`); } catch (e) { /* shown by the result view */ }
      await refreshQueue();
      location.replace(`#/result/${id}`);
    }
  };
  stopPolling(); S.pollId = id; S.poll = setInterval(tick, 300); tick();
}
function drawProgress(id, p) {
  const secs = ((Date.now() - S.startedAt[id]) / 1000).toFixed(1);
  $('#an-timing').textContent = `${S.typicalSeconds ? `About ${S.typicalSeconds} seconds is typical · ` : ''}${secs} s so far`;
  const bar = $('#an-bar'); bar.style.width = `${p.status === 'done' ? 100 : (p.progress || 0)}%`;
  bar.parentElement.setAttribute('aria-valuenow', String(p.progress || 0));
  const order = STEPS.map(s => s[0]);
  const cur = p.status === 'done' ? order.length : Math.max(0, order.indexOf(p.step || 'faces'));
  const noFace = p.faces_found === 0, noSpeech = p.speech === 'none' || p.speech === 'no_track';
  $('#an-steps').innerHTML = STEPS.map(([key, label], i) => {
    let state = i < cur ? 'done' : (i === cur ? 'active' : 'pending');
    let note = '';
    if (key === 'faces' && p.faces_found != null) note = p.faces_found === 0 ? 'No face found' : `${p.faces_found} face frame${p.faces_found === 1 ? '' : 's'} found`;
    if (key === 'face_check' && noFace && i < cur) { state = 'skipped'; note = 'No face to check'; }
    if (key === 'speech' && p.speech) note = { found: 'Speech found', none: 'No speech found', no_track: 'No sound track' }[p.speech] || '';
    if (key === 'voice' && noSpeech && i < cur) { state = 'skipped'; note = 'No speech to check'; }
    const ic = { done: 'check', active: 'loader', pending: 'circle', skipped: 'minus' }[state];
    // Finished steps end with a green "Done" (user request 24 Sep); skipped steps say so in grey; the real note (faces found, speech found) stays.
    const tag = state === 'done' ? `<span class="st-tag done">${icon('check')} Done</span>`
      : state === 'skipped' ? '<span class="st-tag skipped">Skipped</span>' : '';
    return `<li class="step ${state}"><span class="st-icon">${icon(ic)}</span><span>${esc(label)}</span>` +
      `<span class="st-end">${note ? `<span class="st-note">${esc(note)}</span>` : ''}${tag}</span></li>`;
  }).join('');
}

// ── Result ────────────────────────────────────────────────────────────────
async function showResult(id) {
  const view = $('#view-result');
  if (!S.results[id]) {
    const resp = await fetch(`/api/result/${encodeURIComponent(id)}`);
    if (resp.status === 202) { location.replace(`#/analysing/${id}`); return; }
    if (!resp.ok) {
      view.innerHTML = `<div class="narrow"><h1 class="page-title">Check not found</h1><p class="page-lede">This check is no longer available (checks are kept while the tool is running). <a href="#/check">Check a video</a>.</p></div>`;
      return;
    }
    S.results[id] = await resp.json();
  }
  if (!S.queue.length) await refreshQueue();
  renderResult(id);
}
function partCard(kind, r) {
  const isPic = kind === 'picture';
  const p = isPic ? (r.video && r.video.p_fake) : (r.audio && r.audio.p_audio_fake);
  const label = `<div class="part-label">${icon(isPic ? 'face' : 'voice')} ${term(isPic ? 'Picture' : 'Voice', isPic ? 'picture' : 'voice')}</div>`;
  if (p == null) {
    const why = isPic ? missingVideoReason(r) : missingAudioReason(r);
    return `<div class="card">${label}<div class="part-lean">Not checked</div><p class="part-sub">${esc(why.charAt(0).toUpperCase() + why.slice(1))}.</p></div>`;
  }
  const ood = isPic ? r.video.ood : r.audio.ood;
  const flag = ood && ood.unfamiliar ? `<div class="part-flag">${icon('manip')} Unfamiliar to the tool</div>` : '';
  return `<div class="card">${label}
    <div class="part-lean">${lean(p)} · ${pct(p)}</div>
    <p class="part-sub">${pct(p)} ${term('chance', 'chance')} the ${isPic ? 'picture' : 'voice'} is manipulated</p>
    <div class="meter" aria-hidden="true"><span style="--w:${Math.round(p * 1000) / 10}%; background:${meterColor(p)}"></span></div>
    <div class="meter-scale"><span>0%</span><span>50%: unsure</span><span>100%</span></div>${flag}</div>`;
}
function plainFallback(reason) {
  const t = String(reason || '').toLowerCase();
  if (t.includes('faithfulness')) return "The AI model's text said something the results do not support, so standard wording is shown.";
  if (t.includes('reach') || t.includes('unavailable') || t.includes('ollama') || t.includes('empty')) return 'The AI model was not available, so standard wording is shown.';
  if (t.includes('withheld') || t.includes('no score') || t.includes('produced a score') || t.includes('nothing for the language model'))
    return 'There were no scores to explain, so standard wording is shown.';
  return reason ? `Standard wording is shown: ${reason}.` : 'Standard wording is shown.';
}
function explanationBadge(exp) {
  if (exp.source === 'llama3') {
    const checked = exp.faithfulness && exp.faithfulness.passed;
    return `<span class="badge">${icon('sparkle')} ${checked ? 'Written by the AI model and checked' : 'Written by the AI model'}</span>`;
  }
  return `<span class="badge">${icon('template')} Standard wording</span>`;
}
function renderResult(id) {
  const r = S.results[id];
  const view = $('#view-result');
  const job = S.queue.find(j => j.id === id);
  const name = displayName(r.filename || (job && job.filename));
  const head = `
    <div class="result-head">
      <a class="icon-btn" href="#/check" aria-label="Back to Check a video">${icon('arrowLeft')}</a>
      <div class="grow"><div class="result-name">${esc(name)}</div><div class="result-when">Checked ${esc(fmtDateTime(r.analyzed_at))}</div></div>
      <div class="result-actions">
        <button type="button" class="btn" id="btn-pdf">${icon('fileDown')} Save as PDF</button>
        <button type="button" class="btn" id="btn-copy">${icon('copy')} <span>Copy data</span></button>
      </div>
    </div>`;
  if (r.error) {
    view.innerHTML = head + `<div class="notice error">${icon('info')}<span>This clip could not be checked: ${esc(r.error)}</span></div>`;
    wireResultButtons(r);
    return;
  }
  const d = describeVerdict(r);
  const unf = unfamiliarParts(r);
  const exp = r.explanation || {};
  const caution = unf.length ? `
    <div class="caution" role="note">${icon('manip')}<div>
      <h3>This result may be wrong</h3>
      <p>This clip's ${unf.join(' and ')} ${unf.length > 1 ? 'are' : 'is'} unlike the videos the tool learned from, so treat the verdict with caution.</p>
      <p>In testing on an unfamiliar video collection, every wrong verdict carried this warning. See ${term('Unfamiliar clip', 'unfamiliar')}.</p>
    </div></div>` : '';
  const withheld = exp.withheld_note ? `<p class="found-foot">${esc(exp.withheld_note)}</p>` : '';
  const found = `
    <div class="card">
      <div class="found-head"><h2 class="card-title">What the tool found</h2>${exp.available ? explanationBadge(exp) : ''}</div>
      <p class="explanation">${exp.available ? esc(exp.text.trim()) : esc(exp.unavailable_reason || 'No written explanation is available for this clip.')}</p>
      ${exp.available && exp.source !== 'llama3' ? `<p class="found-foot">${esc(plainFallback(exp.fallback_reason))} About ${term('standard wording', 'standard')}.</p>`
        : `<p class="found-foot">About the ${term('written explanation', 'explanation')}.</p>`}
      ${withheld}
    </div>`;
  view.innerHTML = head + `
    <div class="result-grid">
      <div class="col">
        <div class="verdict ${d.tone}">
          <div class="v-icon tone-${d.tone}">${icon(d.icon)}</div>
          <div>
            <div class="eyebrow">Verdict</div>
            <h1 class="v-head tone-${d.tone}">${esc(d.headline)}</h1>
            <p class="v-reason">${esc(d.reason)}</p>
            ${d.gap ? `<p class="v-gap">${d.gap}</p>` : ''}
          </div>
        </div>
        ${caution}
        ${found}
        <div class="parts">${partCard('picture', r)}${partCard('voice', r)}</div>
      </div>
      <div class="col">
        ${playerCard(id, r)}
        ${nextCard(r, d, unf)}
      </div>
    </div>
    ${learnCard(r)}`;
  wireResultButtons(r);
  wirePlayer(id, r);
  wireLearn();
}
function wireResultButtons(r) {
  $('#btn-copy').onclick = async () => {
    const ok = await copyText(JSON.stringify(r, null, 2));
    const span = $('#btn-copy span'); span.textContent = ok ? 'Copied' : 'Copy failed';
    setTimeout(() => { span.textContent = 'Copy data'; }, 1400);
  };
  $('#btn-pdf').onclick = () => window.print();
}
async function copyText(text) {
  try { await navigator.clipboard.writeText(text); return true; }
  catch (e) {
    try {
      const ta = document.createElement('textarea'); ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select(); const ok = document.execCommand('copy'); ta.remove(); return ok;
    } catch (e2) { return false; }
  }
}
function playerCard(id, r) {
  const an = r.anomalies || [];
  let notes;
  if (!r.video) notes = '<p class="moments-note">The picture was not checked, so there are no moments to mark.</p>';
  else if (an.length) notes = `<div class="moments">${an.map((a, i) => `
      <button type="button" class="moment" data-seek="${a.start != null ? a.start : ''}" ${a.start == null ? 'disabled' : ''}>
        <span style="display:flex;gap:10px;align-items:center"><span class="m-dot"></span>
          <span class="m-when">${esc(fmtWindow(a))}</span></span>
        <span class="muted">peak ${pct(a.peak_score)}</span></button>`).join('')}</div>`;
  else notes = '<p class="moments-note">No suspicious moments: the picture check did not reach 50% at any point.</p>';
  if (r.audio && r.audio.p_audio_fake != null) notes += '<p class="moments-note">The voice check gives one estimate for the whole clip, so it cannot mark moments.</p>';
  return `
    <div class="card player-card">
      <h2 class="card-title">When in the clip</h2>
      <p class="player-intro">Marks show ${term('when', 'moments')} the picture check's estimate was high, not what looks wrong.</p>
      <div class="player">
        <video id="vid" src="/api/video/${encodeURIComponent(id)}" preload="metadata" playsinline></video>
        <div class="p-controls">
          <button type="button" class="p-play" id="p-play" aria-label="Play">${icon('play')}</button>
          <div class="p-track" id="p-track" role="slider" tabindex="0" aria-label="Position in clip" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">
            <div class="p-rail"></div><div class="p-fill" id="p-fill"></div><div id="p-marks"></div><div class="p-knob" id="p-knob" style="left:0%"></div>
          </div>
          <span class="p-time" id="p-time">0:00 / 0:00</span>
        </div>
      </div>
      ${notes}
    </div>`;
}
function wirePlayer(id, r) {
  const v = $('#vid'); if (!v) return;
  const track = $('#p-track');
  const job = S.queue.find(j => j.id === id);
  const dur = () => v.duration || (job && job.duration) || 0;
  const drawMarks = () => {
    const D = dur(); if (!D) return;
    $('#p-marks').innerHTML = (r.anomalies || []).filter(a => a.start != null).map(a => {
      const left = Math.min(100, a.start / D * 100), width = Math.max(0.8, (a.end - a.start) / D * 100);
      return `<div class="p-mark" style="left:${left}%;width:${Math.min(width, 100 - left)}%"></div>`;
    }).join('');
  };
  const update = () => {
    const D = dur(), t = v.currentTime || 0, f = D ? t / D * 100 : 0;
    $('#p-fill').style.width = `${f}%`; $('#p-knob').style.left = `${f}%`;
    track.setAttribute('aria-valuenow', String(Math.round(f)));
    $('#p-time').textContent = `${fmtTime(t)} / ${fmtTime(D)}`;
  };
  v.addEventListener('loadedmetadata', () => { drawMarks(); update(); });
  v.addEventListener('timeupdate', update);
  v.addEventListener('play', () => { $('#p-play').innerHTML = icon('pause'); $('#p-play').setAttribute('aria-label', 'Pause'); });
  v.addEventListener('pause', () => { $('#p-play').innerHTML = icon('play'); $('#p-play').setAttribute('aria-label', 'Play'); });
  $('#p-play').onclick = () => (v.paused ? v.play() : v.pause());
  const seek = (e) => { const rect = track.getBoundingClientRect(); const f = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width)); if (dur()) v.currentTime = f * dur(); };
  let drag = false;
  track.addEventListener('pointerdown', e => { drag = true; track.setPointerCapture(e.pointerId); seek(e); });
  track.addEventListener('pointermove', e => { if (drag) seek(e); });
  track.addEventListener('pointerup', () => { drag = false; });
  track.addEventListener('keydown', e => {
    if (e.key === 'ArrowRight') v.currentTime = Math.min(dur(), v.currentTime + 1);
    if (e.key === 'ArrowLeft') v.currentTime = Math.max(0, v.currentTime - 1);
  });
  $$('.moment[data-seek]').forEach(b => b.addEventListener('click', () => { if (b.dataset.seek !== '') { v.currentTime = parseFloat(b.dataset.seek); v.play(); } }));
  drawMarks(); update();
}
function nextCard(r, d, unf) {
  const items = [];
  if (unf.length) items.push(['manip', 'Treat this result with extra caution: the clip is unfamiliar to the tool.']);
  items.push(['scale', 'Use this as one input, not proof. The tool gives likelihoods.']);
  items.push(['link', 'Check where the clip came from and whether others have published it.']);
  if (r.anomalies && r.anomalies.length) items.push(['replay', 'Look again at the marked moments.']);
  else if (d.tone === 'partial' && r.fusion && r.fusion.implicated_modality === 'audio') items.push(['replay', 'Listen to the speech again.']);
  else if (d.tone !== 'none') items.push(['replay', 'Watch and listen to the whole clip again.']);
  return `<div class="card"><h2 class="card-title">What to do next</h2>
    <ul class="todo">${items.map(([ic, t]) => `<li>${icon(ic)}<span>${esc(t)}</span></li>`).join('')}</ul></div>`;
}

// ── Learn more ────────────────────────────────────────────────────────────
const TABS = [['legend', 'Legend'], ['findings', 'Findings for this clip'], ['technical', 'Technical details'], ['accuracy', 'Accuracy and limits']];
function learnCard(r) {
  return `
    <section class="card learn" id="learn">
      <div class="learn-head" id="learn-head">
        <div class="grow"><h2>Learn more</h2><p>What the terms mean, full findings, technical details, accuracy and limits.</p></div>
        <button type="button" class="icon-btn" id="learn-toggle" aria-expanded="false" aria-controls="learn-body" aria-label="Show or hide Learn more">${icon('chevronDown')}</button>
      </div>
      <div class="learn-body" id="learn-body" hidden>
        <div class="tabs" role="tablist">${TABS.map(([k, l]) => `<button type="button" class="tab" role="tab" data-tab="${k}" aria-selected="false">${l}</button>`).join('')}</div>
        <div class="tab-panel" data-panel="legend" data-print-title="Legend">${legendGrid('lr')}</div>
        <div class="tab-panel" data-panel="findings" data-print-title="Findings for this clip">${findingsPanel(r)}</div>
        <div class="tab-panel" data-panel="technical" data-print-title="Technical details">${technicalPanel(r)}</div>
        <div class="tab-panel" data-panel="accuracy" data-print-title="Accuracy and limits">${accuracyPanel()}</div>
      </div>
    </section>`;
}
function applyLearnState() {
  const card = $('#learn'); if (!card) return;
  card.classList.toggle('open', S.learnOpen);
  $('#learn-body').hidden = !S.learnOpen;
  $('#learn-toggle').setAttribute('aria-expanded', String(S.learnOpen));
  $$('.tab', card).forEach(t => t.setAttribute('aria-selected', String(t.dataset.tab === S.learnTab)));
  $$('.tab-panel', card).forEach(p => { p.hidden = p.dataset.panel !== S.learnTab; });
}
function wireLearn() {
  $('#learn-head').addEventListener('click', (e) => { if (e.target.closest('.tab')) return; S.learnOpen = !S.learnOpen; applyLearnState(); });
  $$('#learn .tab').forEach(t => t.addEventListener('click', () => { S.learnTab = t.dataset.tab; applyLearnState(); }));
  applyLearnState();
}
// Print (Save as PDF) shows every panel; the print stylesheet does the rest.
window.addEventListener('beforeprint', () => { $$('#learn .tab-panel').forEach(p => { p.dataset.wasHidden = p.hidden ? '1' : ''; p.hidden = false; }); const b = $('#learn-body'); if (b) { b.dataset.wasHidden = b.hidden ? '1' : ''; b.hidden = false; } });
window.addEventListener('afterprint', () => applyLearnState());

function frameChart(values) {
  const W = 600, H = 190, L = 44, B = 26, top = 10;
  const n = values.length, bw = (W - L) / Math.max(n, 1);
  const y = (v) => top + (H - B - top) * (1 - v);
  const every = n > 24 ? Math.ceil(n / 12) : 1;
  const bars = values.map((v, i) => {
    const h = Math.max(1.5, (H - B - top) * v);
    return `<rect class="${v >= 0.5 ? 'bf hi' : 'bf'}" x="${(L + i * bw + bw * 0.18).toFixed(1)}" y="${(y(v) + (v * (H - B - top) < 1.5 ? -1.5 : 0)).toFixed(1)}" width="${(bw * 0.64).toFixed(1)}" height="${h.toFixed(1)}" rx="2"/>` +
      ((i % every === 0) ? `<text x="${(L + i * bw + bw / 2).toFixed(1)}" y="${H - 6}" text-anchor="middle">${i + 1}</text>` : '');
  }).join('');
  return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Chance of manipulation for each checked face frame">
    <text x="${L - 8}" y="${y(1) + 4}" text-anchor="end">100%</text><text x="${L - 8}" y="${y(0.5) + 4}" text-anchor="end">50%</text><text x="${L - 8}" y="${y(0) + 4}" text-anchor="end">0%</text>
    <line class="grid" x1="${L}" x2="${W}" y1="${y(0.5)}" y2="${y(0.5)}"/><line class="axis" x1="${L}" x2="${W}" y1="${y(0)}" y2="${y(0)}"/>${bars}</svg>`;
}
function waveChart(values) {
  const W = 600, H = 110, n = values.length, max = Math.max(...values, 1e-6), bw = W / Math.max(n, 1);
  return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Waveform of the sound track">${values.map((v, i) => {
    const h = Math.max(2, (v / max) * (H - 8));
    return `<rect class="wf" x="${(i * bw + bw * 0.2).toFixed(1)}" y="${((H - h) / 2).toFixed(1)}" width="${Math.max(1, bw * 0.6).toFixed(1)}" height="${h.toFixed(1)}" rx="1"/>`;
  }).join('')}</svg>`;
}
const VIOLATION_WORDS = { direction: 'it described a part as manipulated when the results say it leans genuine (or the reverse)',
  number: 'it gave a number that is not in the results', disagreement: 'it misstated whether the two checks disagree',
  certainty: 'it sounded more certain than the results allow', unlisted: 'it mentioned something the results do not contain',
  timing: 'it gave a time that is not one of the suspicious moments', unevaluated: 'it judged a part that was not checked' };
function familiarity(ood, checked) {
  if (!checked) return 'Not checked';
  if (!ood) return 'Not measured';
  return `${ood.unfamiliar ? '<span class="tone-caution">Unfamiliar to the tool</span>' : 'Within what the tool knows'} <span class="faint">(distance ${esc(ood.distance)}, limit ${esc(ood.threshold)})</span>`;
}
function findingsPanel(r) {
  const v = r.video, a = r.audio || {};
  const pic = v ? `
      <p>${pct(v.p_fake)} chance the picture is manipulated, from ${v.n_faces} face frame${v.n_faces === 1 ? '' : 's'}.</p>
      ${v.sample_face_png_b64 ? `<div class="face"><img src="data:image/png;base64,${v.sample_face_png_b64}" alt="The first face the tool found in this clip"><p>The first face the tool found (224 × 224), as the picture check sees it.</p></div>` : ''}
      <p class="chart-cap">Chance for each checked frame (dashed line: 50%)</p>${frameChart(v.per_frame || [])}`
    : `<p>${esc(missingVideoReason(r).charAt(0).toUpperCase() + missingVideoReason(r).slice(1))}.</p>`;
  const voice = (a.p_audio_fake != null) ? `
      <p>${pct(a.p_audio_fake)} chance the voice is manipulated.</p>
      <p class="muted">${a.speech_seconds != null ? `${a.speech_seconds.toFixed(1)} s of speech found in ${fmtTime(a.seconds)} of sound.` : ''}</p>
      ${(a.waveform && a.waveform.length) ? `<p class="chart-cap" style="margin-top:14px">The sound track</p>${waveChart(a.waveform)}` : ''}`
    : `<p>Not checked: ${esc(missingAudioReason(r))}.</p>${a.speech_seconds != null ? `<p class="muted">${a.speech_seconds.toFixed(1)} s of speech found in ${fmtTime(a.seconds)} of sound.</p>` : ''}`;
  const T = r.fusion && r.fusion.threshold_T;
  const gap = (v && v.p_fake != null && a.p_audio_fake != null && T != null) ? `
      <p>${points(Math.abs(v.p_fake - a.p_audio_fake))} points apart. The line for "partly manipulated" is ${points(T)} points.</p>
      <div class="gapbar" aria-hidden="true"><span style="width:${Math.abs(v.p_fake - a.p_audio_fake) * 100}%"></span><i style="left:${T * 100}%"></i></div>
      <p class="faint">Yellow mark: the ${points(T)}-point line.</p>`
    : '<p>Only one check gave a score, so there is nothing to compare.</p>';
  const an = r.anomalies || [];
  const moments = !v ? '<p>The picture was not checked.</p>' : an.length
    ? `<ul class="limits">${an.map(x => `<li>${esc(fmtWindow(x))}, peak ${pct(x.peak_score)}</li>`).join('')}</ul>`
    : '<p>None marked.</p>';
  const exp = r.explanation || {};
  const f = exp.faithfulness;
  const expBlock = !exp.available ? `<p>${esc(exp.unavailable_reason || 'No explanation.')}</p>` : `
      <div class="kv"><div><b>Written by:</b> ${exp.source === 'llama3' ? 'the AI model (Llama 3 8B)' : 'standard wording (no AI model)'}</div>
      <div><b>Automatic check:</b> ${f ? (f.passed ? 'passed' : 'did not pass') : 'not run'}</div></div>
      ${f && !f.passed && f.violations && f.violations.length ? `<p class="muted" style="margin-top:8px">Why: ${esc([...new Set(f.violations.map(x => VIOLATION_WORDS[x.type] || x.type))].join('; '))}.</p>` : ''}
      ${exp.rejected_llm_text ? `<details class="rejected"><summary>Show the AI model's text that was not used</summary><blockquote>${esc(exp.rejected_llm_text)}</blockquote></details>` : ''}`;
  return `
    <div class="panel-grid">
      <div class="sub-card"><h4>Picture check</h4>${pic}</div>
      <div class="sub-card"><h4>Voice check</h4>${voice}</div>
      <div class="sub-card"><h4>How far apart the checks were</h4>${gap}</div>
      <div class="sub-card"><h4>Suspicious moments</h4>${moments}</div>
      <div class="sub-card"><h4>Familiarity</h4><div class="kv">
        <div><b>Face footage:</b> ${familiarity(v && v.ood, !!v)}</div>
        <div><b>Speech:</b> ${familiarity(a.ood, a.p_audio_fake != null || !!a.withheld)}</div></div></div>
      <div class="sub-card"><h4>The explanation</h4>${expBlock}</div>
    </div>`;
}
function technicalPanel(r) {
  const mi = (S.modelInfo && S.modelInfo.models) || [];
  const st = (stage) => { const m = mi.find(x => x.stage === stage); return m ? m.status : ''; };
  const vname = videoModelName();
  const rows = [
    ['MTCNN', 'Finds faces in each sampled frame.', ''],
    [vname, 'Judges each face and gives a chance of manipulation.', st('Video')],
    ['Silero VAD', 'Finds the parts of the sound track that contain speech.', st('Speech gate')],
    ['wav2vec2-base', 'Turns the speech into numbers a classifier can use.', st('Audio encoder')],
    ['SVM (RBF kernel)', 'Judges those numbers and gives a chance the voice is synthetic.', st('Audio classifier')],
    ['Llama 3 8B', 'Writes the short plain-English explanation from the results only.', st('Explanation')],
  ];
  const sh = S.evaluation && S.evaluation.shipped;
  const fu = r.fusion || {};
  const wv = (fu.video_accuracy && fu.audio_accuracy) ? fu.video_accuracy / (fu.video_accuracy + fu.audio_accuracy) : null;
  const ran = (r.models_ran || []).map(m => `<li><span class="mono">${esc(m.model)}</span><span class="faint">: ${esc(m.produced || '')}</span></li>`).join('');
  return `
    <div class="panel-grid wide-left">
      <div class="stack">
        <div class="sub-card"><h4>Models behind each step</h4>
          <ol class="model-list">${rows.map(([n, d, s], i) => `<li><span class="n">${i + 1}</span><span class="name">${esc(n)}</span>
            <span class="desc">${esc(d)}${s ? `<span class="status">${esc(s)}</span>` : ''}</span></li>`).join('')}</ol></div>
        ${ran ? `<div class="sub-card"><h4>What ran on this clip</h4><ul class="limits">${ran}</ul></div>` : ''}
      </div>
      <div class="stack">
        <div class="sub-card"><h4>Model version</h4><p class="mono">${sh ? esc(String(sh.checkpoint_sha256 || '').slice(0, 12)) : 'not recorded'}</p>
          ${sh ? `<p class="faint" style="margin-top:6px">${esc(sh.arch)}, seed ${esc(sh.seed)}</p>` : ''}</div>
        <div class="sub-card"><h4>Training data</h4><p><span class="mono">FaceForensics++</span> for faces${sh ? `, trained ${esc(sh.trained_on)}` : ''}</p>
          <p><span class="mono">ASVspoof 2019 LA</span> for voices</p></div>
        <div class="sub-card"><h4>Combining the checks</h4>
          <p>${wv != null ? `Weights: voice ${(1 - wv).toFixed(2)}, picture ${wv.toFixed(2)}.` : ''} ${fu.threshold_T != null ? `Disagreement line T = ${fu.threshold_T.toFixed(2)}.` : ''}</p></div>
      </div>
    </div>`;
}
function accuracyPanel() {
  const st = S.stats || {};
  const L = S.limitations;
  return `
    <div class="panel-grid wide-left" style="grid-template-columns:minmax(0,1fr) minmax(0,1.6fr)">
      <div class="sub-card">
        ${st.acc != null ? `<div class="bignum">${Math.round(st.acc)} in 100</div>
          <p class="muted" style="margin-top:8px">judged correctly on people the tool had not seen (95% range ${Math.round(st.lo)}% to ${Math.round(st.hi)}%).</p>` : '<p>Accuracy figures are not available.</p>'}
        <p style="margin-top:16px"><a class="link" href="#/accuracy">Full accuracy page →</a></p>
      </div>
      <div class="sub-card"><h4>Limits</h4>
        ${L ? `<p class="muted" style="margin-bottom:12px">${esc(L.how_to_read)}</p><ul class="limits">${L.limitations.map(l => `<li>${esc(l.text)}</li>`).join('')}</ul>` : '<p>The limits could not be loaded.</p>'}
      </div>
    </div>`;
}

// ── History ───────────────────────────────────────────────────────────────
function renderHistory() {
  const rows = S.queue.slice().reverse();
  $('#view-history').innerHTML = `
    <div class="narrow">
      <h1 class="page-title">Past checks</h1>
      <p class="page-lede">Kept while the tool is running. Open a check to save it as a PDF.</p>
      <div class="list history-list">${rows.length ? rows.map(j => {
        const r = S.results[j.id];
        const href = j.status === 'done' ? `#/result/${j.id}` : `#/analysing/${j.id}`;
        const actions = S.confirmDelete === j.id
          ? `<span class="confirm">Remove this check?
               <button type="button" class="btn btn-danger" data-del-yes="${j.id}">Remove</button>
               <button type="button" class="btn" data-del-no>Cancel</button></span>`
          : `${chipFor(j)}
             <button type="button" class="icon-btn" data-copy="${j.id}" aria-label="Copy the data for this check" ${r ? '' : 'disabled'}>${icon('copy')}</button>
             <button type="button" class="icon-btn" data-del="${j.id}" aria-label="Remove this check">${icon('trash')}</button>`;
        return `<div class="history-row"><a class="open" href="${href}"><div class="row-title">${esc(displayName(j.filename))}</div>
          <div class="row-sub">${r ? esc(fmtDateTime(r.analyzed_at)) : (j.status === 'error' ? 'Could not be checked' : 'Not finished')}</div></a>${actions}</div>`;
      }).join('') : '<div class="empty">No checks yet. <a href="#/check">Check a video</a> to see it here.</div>'}</div>
    </div>`;
  $$('[data-copy]').forEach(b => b.onclick = async () => { const ok = await copyText(JSON.stringify(S.results[b.dataset.copy], null, 2)); b.setAttribute('aria-label', ok ? 'Copied' : 'Copy failed'); b.innerHTML = icon(ok ? 'check' : 'info'); setTimeout(() => { b.innerHTML = icon('copy'); }, 1400); });
  $$('[data-del]').forEach(b => b.onclick = () => { S.confirmDelete = b.dataset.del; renderHistory(); });
  $$('[data-del-no]').forEach(b => b.onclick = () => { S.confirmDelete = null; renderHistory(); });
  $$('[data-del-yes]').forEach(b => b.onclick = async () => {
    const id = b.dataset.delYes;
    await fetch(`/api/queue/${id}`, { method: 'DELETE' });
    delete S.results[id]; S.confirmDelete = null;
    await refreshQueue(); renderHistory();
  });
}

// ── Accuracy page ─────────────────────────────────────────────────────────
function renderAccuracy() {
  const st = S.stats || {};
  const ev = S.evaluation;
  const cards = [];
  if (st.acc != null) cards.push([`${Math.round(st.acc)} in 100`, `Right about ${Math.round(st.acc)} times in 100 on people it has not seen before. The true figure probably lies between ${Math.round(st.lo)} and ${Math.round(st.hi)}.`]);
  if (st.celebAcc != null) cards.push([`${Math.round(st.celebAcc)} in 100`, `On a different video collection (Celeb-DF) it was right only ${Math.round(st.celebAcc)} times in 100.`]);
  if (st.celebFalseAlarm != null) cards.push([`${Math.round(st.celebFalseAlarm)} in 100`, `On that collection, ${Math.round(st.celebFalseAlarm)} in 100 genuine videos were wrongly flagged as manipulated (${'false alarms'}).`]);
  if (st.voiceFlagged != null) cards.push([`${st.voiceFlagged} of ${st.voiceTotal}`, `Genuine voices recorded somewhere unfamiliar can be called synthetic: in one test, ${st.voiceFlagged === st.voiceTotal ? 'all' : st.voiceFlagged + ' of'} ${st.voiceTotal} genuine clips were flagged.`]);
  const fu = S.fusion;
  const tables = ev ? ev.sections.map(s => {
    if (s.status !== 'current') return `<details class="table-card"><summary><h3>${esc(s.title)}</h3></summary><p class="pending">Not shown: ${esc(s.reason || 'pending')}</p></details>`;
    const numCol = (c) => /^[+\-−]?[\d.]/.test(String(c)) || /%|pp\b| s$/.test(String(c));
    return `<details class="table-card"><summary><h3>${esc(s.title)}</h3><span class="faint">${s.rows.length} row${s.rows.length === 1 ? '' : 's'}</span></summary><div class="table-scroll"><table class="data">
      <thead><tr>${s.columns.map(c => `<th>${esc(c)}</th>`).join('')}</tr></thead>
      <tbody>${s.rows.map(r => `<tr${String(r[0]).includes('[SHIPPED]') ? ' class="shipped"' : ''}>${r.map((c, i) => `<td class="${i > 0 && numCol(c) && String(c).length < 40 ? 'num' : ''}">${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>
      ${s.note ? `<p class="t-note">${esc(s.note)}</p>` : ''}<p class="t-src">Source: ${esc(s.source)}</p></details>`;
  }).join('') : '<p class="muted">The evaluation results could not be loaded.</p>';
  $('#view-accuracy').innerHTML = `
    <div class="narrow">
      <div class="eyebrow">Accuracy</div>
      <h1 class="page-title">How accurate is this tool?</h1>
      <p class="page-lede">Useful, but not always right. It works best on clips like the ones it learned from, and it gets worse on unfamiliar footage or recordings.</p>
      <div class="stats">${cards.map(([n, t]) => `<div class="card stat"><div class="bignum">${esc(n)}</div><p>${esc(t)}</p></div>`).join('')}</div>
      <p class="acc-note">It covers three common face-manipulation methods, not every method. Read each figure as an estimate from a limited test.</p>
      ${fu ? `<h2 class="acc-h2">How the two checks are combined</h2>
      <div class="table-card"><div class="table-scroll"><table class="data"><thead><tr><th>Parameter</th><th>Value</th><th>Meaning</th></tr></thead><tbody>
        <tr><td>w_audio</td><td class="num">${fu.w_audio.toFixed(2)}</td><td>Weight of the voice check in the combined score</td></tr>
        <tr><td>w_video</td><td class="num">${fu.w_video.toFixed(2)}</td><td>Weight of the picture check in the combined score</td></tr>
        <tr><td>T</td><td class="num">${fu.threshold_T.toFixed(2)}</td><td>Gap at or above which the result is "partly manipulated"</td></tr>
      </tbody></table></div></div>` : ''}
      <h2 class="acc-h2">For experts: research tables</h2>
      <p class="acc-note" style="margin:-8px 0 18px">Every table the figures above come from. Open one to see it.</p>
      ${tables}
      ${ev ? `<p class="t-src" style="padding:0">Generated ${esc(ev.generated_at || 'unknown')} by scripts/build_numbers.py from results/numbers.json.</p>` : ''}
      <h2 class="acc-h2">Legend</h2>
      ${legendGrid('la')}
    </div>`;
}

// ── Start ─────────────────────────────────────────────────────────────────
$('#brand-mark').innerHTML = icon('logo');
(async function init() {
  await loadStatic();
  await refreshQueue();
  render();
})();
