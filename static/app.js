/* Clipcheck, interface v4 (2026-09-26). Vanilla JS, no framework; talks to the FastAPI backend in server.py.
 * Redesigned from scratch after a design review (docs/user_testing/findings.md, C28 onward). NOT user-tested: round 2 tested v2,
 * frozen in docs/user_testing/ui_v2_snapshot/ (./run_v2_interface.sh, port 8002).
 *
 * Honesty contract (unchanged since v1, several parts tested in tests/test_server.py):
 *  - every number shown is a real field from the server, or an explicit "not checked" state, never a made-up value;
 *  - the unfamiliar-input warning is shown whenever the server raises it, inside the verdict;
 *  - the tool says WHEN the picture check was high, never WHAT is visible;
 *  - who wrote the explanation (the AI model, or standard wording) is always shown, with the reason for any fallback;
 *  - limits and technical detail are always one click away (Details, and the Accuracy page), in plain words with a glossary. */
'use strict';

const S = {
  demos: [], queue: [], results: {}, limits: null, limitations: null, evaluation: null, modelInfo: null, stats: {}, fusion: null,
  testing: false, poll: null, startedAt: {}, tab: 'findings', busy: false, confirmDelete: null,
  shown: new Set(), notified: new Set(), popAnchor: null, lastFocus: null, view: 'check', cur: null,
};

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const RM = matchMedia('(prefers-reduced-motion: reduce)');
const stage = $('#stage');

// ── Icons (inline SVG, 24 x 24, stroke-based) ─────────────────────────────
const ICONS = {
  upload: '<path d="M12 13v8"/><path d="m8 17 4-4 4 4"/><path d="M4 14.9A7 7 0 1 1 15.7 8h1.8a4.5 4.5 0 0 1 2.5 8.24"/>',
  arrowLeft: '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
  copy: '<rect x="8" y="8" width="14" height="14" rx="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/>',
  fileDown: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M12 18v-6"/><path d="m9 15 3 3 3-3"/>',
  details: '<rect x="3" y="4" width="18" height="16" rx="3"/><path d="M3 10h18"/><path d="M8 14h8M8 17h5"/>',
  trash: '<path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><path d="M10 11v6M14 11v6"/>',
  x: '<path d="M18 6 6 18M6 6l12 12"/>',
  face: '<path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><path d="M9 9h.01M15 9h.01"/>',
  voice: '<path d="M2 10v3M6 6v11M10 3v18M14 8v7M18 5v13M22 10v3"/>',
  merge: '<path d="M6 3v5a6 6 0 0 0 6 6 6 6 0 0 0 6-6V3"/><path d="M12 14v7"/>',
  alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4M12 17h.01"/>',
  genuine: '<circle cx="12" cy="12" r="9.5"/><path d="m8 12.2 2.8 2.8L16.2 9.4"/>',
  manip: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4M12 17h.01"/>',
  partial: '<circle cx="12" cy="12" r="9.5"/><path d="M12 2.5a9.5 9.5 0 0 1 0 19z" fill="currentColor"/>',
  none: '<circle cx="12" cy="12" r="9.5"/><path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3M12 17h.01"/>',
  info: '<circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/>',
  loader: '<path d="M21 12a9 9 0 1 1-6.22-8.56"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  minus: '<path d="M5 12h14"/>',
  pen: '<path d="M12 20h9"/><path d="M16.4 3.6a2 2 0 0 1 2.8 2.8L7 18.6 3 19.6l1-4z"/>',
  template: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M8 13h8M8 17h5"/>',
  scale: '<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10M12 3v18M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>',
  link: '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
  replay: '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
  play: '<path d="M7 4.5v15l12-7.5z" fill="currentColor"/>',
  pause: '<path d="M7 4h3v16H7zM14 4h3v16h-3z" fill="currentColor"/>',
};
const icon = (name) => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ''}</svg>`;
// The mark (also static/clipcheck-mark.svg): half a human face drawn by hand (green, real), half built from pixels (red, generated).
const BRAND = (() => {
  let px = '';
  for (let y = 14; y <= 48; y += 5.5) for (let x = 34; x <= 50; x += 5.5) {
    const dx = (x + 2 - 32) / 18, dy = (y + 2 - 32) / 20;
    if (dx * dx + dy * dy > 1) continue;
    const key = (Math.abs(x - 39.5) < 1 && Math.abs(y - 25) < 1) || (Math.abs(y - 41.5) < 1 && x < 42);
    px += `<rect x="${x}" y="${y}" width="4.2" height="4.2" rx="1" fill="#ff8279" opacity="${key ? 1 : 0.6}"/>`;
  }
  return '<svg viewBox="0 0 64 64" aria-hidden="true"><rect x="1" y="1" width="62" height="62" rx="15" fill="#1f2328" stroke="rgba(255,255,255,.16)"/>'
    + '<path d="M31 12A18 20 0 0 0 31 52" fill="none" stroke="#63d493" stroke-width="4" stroke-linecap="round"/><circle cx="24.5" cy="28" r="2.6" fill="#63d493"/>'
    + `<path d="M24 41q4 3 7 2.6" fill="none" stroke="#63d493" stroke-width="3" stroke-linecap="round"/>${px}</svg>`;
})();

// ── Formatting ────────────────────────────────────────────────────────────
// A score of 0.9995 is shown as ">99%", not "100%", and 0.002 as "<1%": the tool never gives certainty.
function pct(p) {
  if (p == null || isNaN(p)) return 'n/a';
  if (p >= 0.995) return '>99%';
  if (p < 0.005) return '<1%';
  return `${Math.round(p * 100)}%`;
}
const points = (x) => Math.round(x * 100);
const lean = (p) => (p >= 0.5 ? 'Leans manipulated' : 'Leans genuine');
const cap1 = (s) => s.charAt(0).toUpperCase() + s.slice(1);
const nice = (s) => String(s || '').replace(/ · /g, ', ');
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
function fmtDate(iso) {
  const d = new Date(String(iso || '').replace(/\.(\d{3})\d+/, '.$1'));
  return isNaN(d) ? '' : d.toLocaleString('en-GB', { day: 'numeric', month: 'long', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}
// Score colour: green (0%) to amber (50%, unsure) to red (100%), square-rooted so it leaves amber quickly (25 Sep).
const METER_STOPS = [[63, 207, 127], [242, 178, 60], [240, 82, 74]];
function meterColor(p) {
  const d = p - 0.5, t = 0.5 + Math.sign(d) * Math.sqrt(Math.abs(d) * 2) / 2;
  const [a, b, f] = t < 0.5 ? [METER_STOPS[0], METER_STOPS[1], t * 2] : [METER_STOPS[1], METER_STOPS[2], (t - 0.5) * 2];
  return `rgb(${a.map((v, i) => Math.round(v + (b[i] - v) * f)).join(', ')})`;
}

// ── Testing mode: neutral demo names (the round 1 clip codes), so a name cannot hint at the answer in a session ──
function checkTestingSwitch() {
  const h = location.hash;
  try {
    if (h === '#testing' || /[?&]testing\b/.test(location.search)) sessionStorage.setItem('clipcheck-testing', '1');
    if (h === '#testing-off') sessionStorage.removeItem('clipcheck-testing');
    S.testing = sessionStorage.getItem('clipcheck-testing') === '1';
  } catch (e) { if (h === '#testing') S.testing = true; if (h === '#testing-off') S.testing = false; }
  if (h === '#testing' || h === '#testing-off') history.replaceState(null, '', '#/check');
}
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
// Headline figures for the Accuracy page and the glossary, read from /api/evaluation (results/numbers.json), never typed in.
function deriveStats(ev) {
  const secs = (ev.sections || []).filter(s => s.status === 'current');
  const find = pred => secs.find(pred);
  const num = s => { const m = String(s == null ? '' : s).match(/[-+]?\d+(\.\d+)?/); return m ? parseFloat(m[0]) : null; };
  const out = {};
  const cv = find(s => s.id.startsWith('cv_')), cvr = cv && cv.rows.find(r => /^Accuracy/.test(r[0]));
  if (cvr) { out.acc = num(cvr[1]); const m = String(cvr[2]).match(/\d+(\.\d+)?/g); if (m) { out.lo = +m[0]; out.hi = +m[1]; } }
  const cel = find(s => s.id === 'celebdf'), cr = cel && cel.rows.find(r => String(r[0]).includes('[SHIPPED]'));
  if (cr) { out.celeb = num(cr[cel.columns.indexOf('Accuracy at 0.5')]); const k = cel.columns.indexOf('Real videos kept real'); if (k >= 0) out.celebFA = 100 - num(cr[k]); }
  const au = find(s => s.id === 'audio'), ar = au && au.rows.find(r => /used/.test(r[0]));
  if (ar) { const m = String(ar[ar.length - 1]).match(/(\d+)% of (\d+)/); if (m) { out.vTot = +m[2]; out.vFlag = Math.round(+m[1] * +m[2] / 100); } }
  const fc = find(s => s.id === 'four_condition_heldout');
  if (fc) {
    const g = re => { const r = fc.rows.find(x => re.test(x[0])); return r ? r[1] : null; };
    out.four = [['Picture check alone', num(g(/^Video only/))], ['Voice check alone', num(g(/^Audio only/))],
                ['Averaging the two checks', num(g(/^Standard/))], ['Naming the part when they disagree', num(g(/^Disagreement-aware/))]];
    const m = String(g(/^Advantage/) || '').match(/\+?([\d.]+) pp \(95% interval \+?([\d.]+) to \+?([\d.]+), (\d+) clips\)/);
    if (m) out.adv = { d: +m[1], lo: +m[2], hi: +m[3], n: +m[4] };
    out.namedAudio = num(g(/named AUDIO/)); out.namedVideo = num(g(/named VIDEO/));
  }
  const lat = find(s => s.id === 'latency'), lr = lat && lat.rows.find(r => /^Total/i.test(r[0]));
  if (lr) out.typical = num(lr[1]);
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

// ── Verdict wording: one place decides the words for every state (round 2's tested wording plus its two follow-ups) ──
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
function describe(r) {
  const v = r.verdict;
  const pv = r.video && r.video.p_fake != null ? r.video.p_fake : null;
  const pa = r.audio && r.audio.p_audio_fake != null ? r.audio.p_audio_fake : null;
  const T = r.fusion && r.fusion.threshold_T != null ? r.fusion.threshold_T : (S.fusion ? S.fusion.threshold_T : null);
  const d = { pv, pa, T };
  if (v === 'INCONCLUSIVE') {
    const why = [missingVideoReason(r), missingAudioReason(r).replace('the voice check gave no score', 'there is no voice score')];
    return { ...d, tone: 'none', icon: 'none', headline: 'No verdict', reason: `The tool could not check this clip: ${why.join(' and ')}.`, gap: '' };
  }
  const gapPts = pv != null && pa != null ? points(Math.abs(pv - pa)) : null;
  if (v === 'PARTIAL_MANIPULATION') {
    const imp = r.fusion.implicated_modality === 'video' ? 'picture' : 'voice', other = imp === 'picture' ? 'voice' : 'picture';
    let headline, reason;
    if (pv != null && pa != null && (pv >= 0.5) !== (pa >= 0.5)) {
      headline = `Partly manipulated: the ${imp}`;
      reason = (imp === 'picture' ? 'The face looks manipulated but the voice sounds genuine, so only part of this clip may be fake.'
        : 'The voice sounds synthetic but the face looks genuine, so only part of this clip may be fake.')
        + ' Even one manipulated part means the clip should not be shared as genuine.';
    } else {
      headline = 'The checks disagree';
      reason = `The ${imp} looks more suspicious than the ${other}, ` + (pv < 0.5 && pa < 0.5 ? 'although neither is clearly manipulated.' : 'although both lean manipulated.');
    }
    const gap = gapPts != null && T != null ? `The two checks are ${gapPts} points apart. At ${points(T)} or more, the tool reports ${term('partly manipulated', 'partly')} instead of averaging.` : '';
    return { ...d, tone: 'partial', icon: 'partial', headline, reason, gap };
  }
  const fake = v === 'FAKE';
  let reason, gap = '';
  if (pv != null && pa != null) {
    reason = fake ? 'The picture and voice checks agree, and together they point to manipulation.' : 'The picture and voice checks agree, and together they point to a genuine clip.';
    if (gapPts != null && T != null && r.overall_score != null)
      gap = `The two checks are ${gapPts} points apart, under the ${points(T)}-point line, so the tool ${term('combined', 'combined')} them: ${pct(r.overall_score)} chance of manipulation overall.`;
  } else if (pv != null) reason = `Only the picture was checked, because ${missingAudioReason(r)}.`;
  else reason = `Only the voice was checked, because ${missingVideoReason(r)}.`;
  return { ...d, tone: fake ? 'manip' : 'genuine', icon: fake ? 'manip' : 'genuine', headline: fake ? 'Likely manipulated' : 'Likely genuine', reason, gap };
}
function unfamiliarParts(r) {
  const out = [];
  if (r.video && r.video.ood && r.video.ood.unfamiliar && !r.video.withheld) out.push('face footage');
  if (r.audio && r.audio.ood && r.audio.ood.unfamiliar && !r.audio.withheld) out.push('speech');
  return out;
}
function verdictChip(job) {
  const r = S.results[job.id];
  if (job.status === 'analyzing' || job.status === 'pending') return `<span class="vchip tone-none">${icon('loader')} Checking</span>`;
  if (job.status === 'error' || (r && r.error)) return `<span class="vchip tone-manip">${icon('info')} Could not check</span>`;
  if (r) { const d = describe(r); return `<span class="vchip tone-${d.tone}">${icon(d.icon)} ${esc(d.headline)}${unfamiliarParts(r).length ? ', may be wrong' : ''}</span>`; }
  const map = { REAL: ['genuine', 'Likely genuine'], FAKE: ['manip', 'Likely manipulated'], INCONCLUSIVE: ['none', 'No verdict'], PARTIAL_MANIPULATION: ['partial', 'Partly manipulated'] };
  const m = map[job.verdict];
  return m ? `<span class="vchip tone-${m[0]}">${icon(m[0])} ${m[1]}</span>` : '';
}

// ── Glossary (opened from any dotted term as a popover; also in Details and on the Accuracy page) ──
function videoModelName() {
  const v = S.modelInfo && S.modelInfo.models.find(m => m.stage === 'Video');
  return v ? v.name.split(' + ')[0] : 'the video model';
}
function legend() {
  const F = S.fusion, st = S.stats || {};
  const T = F && F.threshold_T != null ? points(F.threshold_T) : null;
  const wv = F ? Math.round(F.w_video * 100) : null, wa = F ? Math.round(F.w_audio * 100) : null;
  return {
    deepfake: ['Deepfake', 'A video or audio clip changed by software to show someone doing or saying something they did not.', ''],
    picture: ['Picture check', 'The part of the tool that looks at the face in each sampled frame of the clip.', 'video branch'],
    voice: ['Voice check', 'The part of the tool that listens to the speech. It only runs when speech is found.', 'audio branch'],
    chance: ['Chance of manipulation', "The tool's estimate, from 0% to 100%, that a part of the clip was manipulated. It is an estimate, not proof. Near 50% means the tool is unsure.", 'P(fake)'],
    partly: ['Partly manipulated', `The picture and voice checks strongly disagree${T != null ? ` (${T} points or more apart)` : ''}, so only one part may have been changed. The tool names the part that looks more manipulated instead of averaging.`, 'PARTIAL_MANIPULATION (disagreement-aware fusion)'],
    combined: ['Combined score', `When the two checks agree, the tool combines them, giving slightly more weight to the check that was more accurate in testing${wv != null ? ` (voice ${wa}%, picture ${wv}%)` : ''}.`, 'accuracy-weighted late fusion'],
    noverdict: ['No verdict', 'The tool could not check the clip at all, for example when there is no face and no speech.', 'INCONCLUSIVE'],
    unfamiliar: ['Unfamiliar clip', 'The face footage or the speech is unlike anything the tool learned from, so its answer is less reliable. The warning does not change the verdict.', 'out-of-domain input, measured as a distance from the training data'],
    moments: ['Suspicious moments', "Times in the clip where the picture check's estimate was 50% or higher. The tool can say when, not what looks wrong.", 'anomaly windows'],
    explanation: ['Written explanation', 'A short summary written for each clip by an AI language model (Llama 3) from the results only. An automatic check compares it with the results; if it says anything the results do not support, the tool shows standard wording instead.', 'Llama 3 8B via Ollama, faithfulness screen'],
    standard: ['Standard wording', "A fixed, pre-written explanation filled in with this clip's results. Shown when the AI model's text did not pass the automatic check, or the model was not available.", 'deterministic template'],
    accuracy: ['Accuracy', st.acc != null ? `How often the tool was right in testing. About ${Math.round(st.acc)}% on people it had not seen, meaning roughly ${100 - Math.round(st.acc)} in 100 test videos were judged wrongly.` : 'How often the tool was right in testing.', ''],
    falsealarm: ['False alarm', 'A genuine clip wrongly flagged as manipulated.', 'false positive'],
    training: ['Training data', 'The example videos and recordings the tool learned from: FaceForensics++ (faces) and ASVspoof 2019 (voices).', ''],
    model: ['Model', `A trained AI program that does one step. This tool chains six: MTCNN finds faces; ${videoModelName()} judges each face; Silero VAD finds speech; wav2vec2 turns speech into numbers; an SVM judges those numbers; Llama 3 8B writes the explanation.`, ''],
  };
}
const term = (label, key) => `<button type="button" class="term" data-term="${key}">${esc(label)}</button>`;
const popEl = $('#pop');
function openPop(anchor, html) {
  popEl.innerHTML = html; popEl.hidden = false; popEl.classList.remove('show');
  const r = anchor.getBoundingClientRect(), w = popEl.offsetWidth, h = popEl.offsetHeight;
  const left = Math.min(Math.max(16, r.left + r.width / 2 - w / 2), innerWidth - w - 16);
  let top = r.bottom + 10, origin = 'top';
  if (top + h > innerHeight - 16) { top = Math.max(16, r.top - h - 10); origin = 'bottom'; }
  popEl.style.left = `${left}px`; popEl.style.top = `${top}px`;
  popEl.style.transformOrigin = `${Math.round(r.left + r.width / 2 - left)}px ${origin}`;
  void popEl.offsetWidth; popEl.classList.add('show'); S.popAnchor = anchor;
}
function closePop() { popEl.hidden = true; S.popAnchor = null; }
document.addEventListener('click', e => {
  const t = e.target.closest('.term');
  if (t) {
    if (S.popAnchor === t) { closePop(); return; }
    const L = legend()[t.dataset.term]; if (!L) return;
    openPop(t, `<h4>${esc(L[0])}</h4><p>${esc(L[1])}</p>${L[2] ? `<p class="tech">Technical name: ${esc(L[2])}</p>` : ''}`);
    return;
  }
  if (!e.target.closest('#pop')) closePop();
});
addEventListener('scroll', () => { if (S.popAnchor) closePop(); }, { passive: true });
document.addEventListener('keydown', e => { if (e.key === 'Escape') { if (!popEl.hidden) closePop(); else closeSheet(); } });
// Glass light that follows the pointer.
document.addEventListener('pointermove', e => {
  const g = e.target.closest && e.target.closest('.glass'); if (!g) return;
  const r = g.getBoundingClientRect();
  g.style.setProperty('--mx', `${e.clientX - r.left}px`); g.style.setProperty('--my', `${e.clientY - r.top}px`);
}, { passive: true });

// ── Router ────────────────────────────────────────────────────────────────
// "/" opens the landing page (welcome); every app address (#/check, #/result/...) works as before.
const VIEWS = ['welcome', 'check', 'analysing', 'result', 'history', 'accuracy'];
function parseRoute() {
  const parts = location.hash.replace(/^#\/?/, '').split('/');
  const view = VIEWS.includes(parts[0]) ? parts[0] : (parts[0] ? 'check' : 'welcome');
  return { view, id: parts[1] || null };
}
const setTone = (t) => { document.body.dataset.tone = t || ''; };
function moveThumb(seg, el) {
  const th = seg && $('.thumb', seg); if (!th || !el) return;
  th.style.left = `${el.offsetLeft}px`; th.style.width = `${el.offsetWidth}px`;
}
function syncNav() {
  const key = S.view === 'analysing' || S.view === 'result' ? 'check' : S.view;
  let cur = null;
  $$('#nav a').forEach(a => { const on = a.dataset.nav === key; if (on) { a.setAttribute('aria-current', 'page'); cur = a; } else a.removeAttribute('aria-current'); });
  moveThumb($('#nav'), cur);
}
async function render() {
  checkTestingSwitch();
  const { view, id } = parseRoute();
  if (view !== 'analysing') stopPolling();
  closePop(); closeSheet();
  S.view = view; document.body.dataset.view = view; syncNav();
  $('#testing-flag').hidden = !S.testing;
  if (view !== 'result') setTone('');
  scrollTo(0, 0);
  if (view === 'welcome') { await refreshQueue(); renderWelcome(); }
  if (view === 'check') { await refreshQueue(); renderCheck(); }
  if (view === 'history') { await refreshQueue(); renderHistory(); }
  if (view === 'accuracy') renderAccuracy();
  if (view === 'analysing') { if (!S.queue.some(j => j.id === id)) await refreshQueue(); renderAnalysing(id); }
  if (view === 'result') await showResult(id);
}
addEventListener('hashchange', render);
addEventListener('resize', () => { syncNav(); const s = $('#sheet .seg'); if (s) moveThumb(s, $('[aria-selected="true"]', s)); });

// ── Check a video: the upload panel and the demo videos ───────────────────
const TRUTH = { changed: ['fake', 'Fake'], genuine: ['real', 'Real'], absent: ['none', 'None'] };
const truth = (s) => TRUTH[s] || ['unknown', 'Unknown'];
// A track per part: flat and grey at rest; on hover it moves, green if that part is real and red if fake. Dotted: the clip has none.
function track(kind, n, seed) {
  if (kind === 'none') return '<span class="mt none"></span>';
  return `<span class="mt ${kind}">${Array.from({ length: n }, (_, k) => {
    const h = (k * 37 + seed * 53) % 100;
    return `<i style="--t:${(0.32 + (h % 45) / 100).toFixed(2)}s;--d:${(-(h % 60) / 100).toFixed(2)}s"></i>`;
  }).join('')}</span>`;
}
// A demo video as a channel strip: name on top, a track and a light each for face and voice (known answers), its length.
// In testing mode the strip shows only the neutral code, so it cannot give the answer away.
function strip(d) {
  const i = d.demo_id;
  const checked = S.queue.some(j => j.filename === d.name && j.status === 'done');
  const foot = `<span class="s-foot"><span class="tnum">${fmtTime(d.duration)}</span>${checked ? `<span class="done">${icon('check')} Checked</span>` : ''}</span>`;
  if (S.testing) {
    return `<button type="button" class="strip" data-demo="${i}" aria-label="${esc(d.code)}">
      <span class="scribble" style="--truth:var(--ink-3)"><b>${esc(d.code)}</b><small>Demo video</small></span>
      <span class="mini" aria-hidden="true">${track('neutral', 12, i)}${track('neutral', 20, i + 3)}</span>${foot}</button>`;
  }
  const c = d.changes || {}, f = truth(c.picture), v = truth(c.voice);
  const tone = f[0] === 'fake' || v[0] === 'fake' ? 'var(--manip)' : f[0] === 'real' || v[0] === 'real' ? 'var(--genuine)' : 'var(--ink-3)';
  const kind = (k) => (k === 'unknown' ? 'neutral' : k);
  return `<button type="button" class="strip" data-demo="${i}" aria-label="${esc(d.title)}. Face: ${f[1]}. Voice: ${v[1]}.">
    <span class="scribble" style="--truth:${tone}"><b>${esc(d.title.split(', ')[0])}</b><small>${esc(nice(d.subtitle))}</small></span>
    <span class="mini" aria-hidden="true">${track(kind(f[0]), 12, i)}${track(kind(v[0]), 20, i + 3)}</span>
    <span class="leds"><span class="led ${f[0]}" style="--bt:${(0.8 + (i % 3) * 0.17).toFixed(2)}s;--bd:${((i * 0.11) % 0.5).toFixed(2)}s"><span>Face</span><b>${f[1]}</b></span><span class="led ${v[0]}" style="--bt:${(0.55 + (i % 4) * 0.13).toFixed(2)}s;--bd:${((i * 0.23) % 0.6).toFixed(2)}s"><span>Voice</span><b>${v[1]}</b></span></span>
    ${foot}</button>`;
}
function renderCheck() {
  // Eight demo videos in one row (27 Sep). Testing mode shows the eight clips user-testing rounds 1 and 2 used, by neutral code.
  const key = S.testing ? 'testing' : 'featured';
  const featured = S.demos.filter(d => d[key] != null).sort((a, b) => a[key] - b[key]);
  const lim = S.limits;
  const recent = S.queue.slice().reverse().slice(0, 3);
  stage.innerHTML = `
    <section class="home">
      <div class="win glass drop pop-in">
        <h1 class="large" id="check-title">Check a video</h1>
        <p class="lede">The tool checks the picture and the voice separately and says how likely each is to be manipulated. It gives a likelihood, not proof, and it cannot say how a clip was changed.</p>
        <div class="dz" id="dropzone">
          <span class="dz-ico">${icon('upload')}</span>
          <span class="grow"><b>Drop a video here</b><small>MP4, MOV, AVI or MKV${lim ? `, up to ${lim.max_upload_mb} MB and ${lim.max_duration_s} seconds` : ''}</small></span>
          <button type="button" class="btn btn-primary" id="choose"><span>Choose a file</span></button>
        </div>
        <div class="dz-error" id="dz-error" role="alert" hidden></div>
        ${recent.length ? `<div class="recent"><div class="recent-h"><h2 class="h3">Recent checks</h2><a class="link" href="#/history">See all</a></div>
          ${recent.map(j => `<a class="recent-row" href="${j.status === 'done' ? `#/result/${j.id}` : `#/analysing/${j.id}`}"><span class="grow">${esc(displayName(j.filename))}</span>${verdictChip(j)}</a>`).join('')}</div>` : ''}
      </div>
      <section class="desk-area pop-in d2" aria-labelledby="desk-h">
        <div class="desk-head"><h2 class="h2" id="desk-h">Demo videos</h2>
          ${featured.length ? `<p class="note">${S.testing ? 'Clips to try the tool on.' : 'Clips with known answers. Each shows whether its face and voice are real or fake, so you can judge whether the tool gets it right.'}</p>` : ''}</div>
        ${featured.length ? `<div class="desk glass" id="desk">${featured.map(strip).join('')}</div>`
          // A copy from the public repository has no demo clips: they are built from research datasets that cannot be shared (27 Sep).
          : `<div class="desk-empty glass"><p>Demo videos aren't included in the public code: they are built from research datasets that can't be shared. The README explains how to rebuild them. You can still check your own clip above.</p></div>`}
      </section>
    </section>`;
  const dz = $('#dropzone');
  $('#choose').onclick = () => $('#file-input').click();
  dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag'); });
  dz.addEventListener('dragleave', () => dz.classList.remove('drag'));
  dz.addEventListener('drop', e => { e.preventDefault(); dz.classList.remove('drag'); if (e.dataTransfer.files[0]) uploadFile(e.dataTransfer.files[0]); });
  wireDesk();
}
// The featured strips lift and grow toward the pointer (inspired by the Dock); every strip starts its check on click.
function wireDesk() {
  $$('.strip').forEach(s => s.addEventListener('click', () => startDemo(+s.dataset.demo, s)));
  const desk = $('#desk'); if (!desk) return;
  const strips = $$('.strip', desk);
  const fine = matchMedia('(hover: hover) and (pointer: fine)'), oneRow = matchMedia('(min-width: 1101px)');
  let base = null;
  desk.addEventListener('pointerenter', () => {
    if (RM.matches || !fine.matches || !oneRow.matches) return;
    base = strips.map(s => s.offsetLeft + s.offsetWidth / 2); strips.forEach(s => s.classList.add('mag'));
  });
  desk.addEventListener('pointermove', e => {
    if (!base) return;
    const x = e.clientX - desk.getBoundingClientRect().left;
    strips.forEach((s, k) => {
      const f = Math.max(0, Math.cos(Math.min(1, Math.abs(x - base[k]) / 170) * Math.PI / 2));
      s.style.transform = `translateY(${(-10 * f).toFixed(1)}px) scale(${(1 + 0.07 * f).toFixed(3)})`;
    });
  });
  desk.addEventListener('pointerleave', () => { base = null; strips.forEach(s => { s.classList.remove('mag'); s.style.transform = ''; }); });
}
addEventListener('dragover', e => e.preventDefault());
addEventListener('drop', e => e.preventDefault());
function showUploadError(msg) {
  const n = $('#dz-error'); if (!n) return;
  n.hidden = !msg;
  n.innerHTML = msg ? `<div class="notice">${icon('info')}<span>${esc(msg)}</span></div>` : '';
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
async function startDemo(demoId, el) {
  if (S.busy) return;
  S.busy = true;
  try {
    if (el && !RM.matches) { el.classList.remove('bounce'); void el.offsetWidth; el.classList.add('bounce'); await new Promise(r => setTimeout(r, 600)); }
    const resp = await fetch(`/api/demo/${demoId}`, { method: 'POST' });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    await startJob(await resp.json());
  } catch (e) { showUploadError('That demo video could not be opened. Try again.'); }
  finally { S.busy = false; }
}
async function startJob(job) {
  S.startedAt[job.id] = Date.now();
  await fetch(`/api/analyze/${job.id}`, { method: 'POST' });
  location.hash = `#/analysing/${job.id}`;
}

// ── Analysing: real progress from /api/progress (server.py sets it at real stage transitions) ──
const STEPS = [['faces', 'Finding faces', 0], ['face_check', 'Checking the face', 0], ['speech', 'Listening for speech', 1],
               ['voice', 'Checking the voice', 1], ['compare', 'Comparing the two checks', 2], ['explain', 'Writing the explanation', 2]];
const LANES = ['Picture', 'Voice', 'Both checks'];
function stopPolling() { if (S.poll) { clearInterval(S.poll); S.poll = null; } }
function renderAnalysing(id) {
  const job = S.queue.find(j => j.id === id);
  const name = job ? displayName(job.filename) : 'Your clip';
  stage.innerHTML = `
    <section class="center"><div class="win glass an pop-in" aria-live="polite">
      <div class="an-bar" role="progressbar" aria-label="Progress" aria-valuemin="0" aria-valuemax="100"><span id="an-fill"></span></div>
      <h1 class="title1">${esc(name)}</h1>
      <p class="sub" id="an-timing"></p>
      <div class="lanes">${LANES.map((l, n) => `<div class="lane-col"><h3>${l}</h3>${STEPS.map(([k, label, lane]) => lane === n
        ? `<div class="step" id="st-${k}"><span class="st"></span><span><b>${label}</b><small></small></span></div>` : '').join('')}</div>`).join('')}</div>
      <div id="an-error"></div>
    </div></section>`;
  if (!S.startedAt[id]) S.startedAt[id] = Date.now();
  const tick = async () => {
    let p;
    try { p = await getJSON(`/api/progress/${id}`); }
    catch (e) { stopPolling(); $('#an-error').innerHTML = `<div class="notice" style="margin-top:18px">${icon('info')}<span>This check is no longer available. <a href="#/check">Start again</a>.</span></div>`; return; }
    if (!$('#an-fill')) { stopPolling(); return; }
    drawProgress(id, p);
    if (p.status === 'done' || p.status === 'error') {
      stopPolling();
      try { S.results[id] = await getJSON(`/api/result/${id}`); } catch (e) { /* shown by the result view */ }
      await refreshQueue();
      notify(id);
      location.replace(`#/result/${id}`);
    }
  };
  stopPolling(); S.poll = setInterval(tick, 300); tick();
}
function drawProgress(id, p) {
  const secs = ((Date.now() - S.startedAt[id]) / 1000).toFixed(1);
  $('#an-timing').textContent = `${S.stats.typical ? `About ${Math.round(S.stats.typical)} seconds is typical. ` : ''}${secs} s so far.`;
  const pc = p.status === 'done' ? 100 : (p.progress || 0);
  $('#an-fill').style.width = `${pc}%`;
  $('.an-bar').setAttribute('aria-valuenow', String(pc));
  const order = STEPS.map(s => s[0]);
  const cur = p.status === 'done' ? order.length : Math.max(0, order.indexOf(p.step || 'faces'));
  const noFace = p.faces_found === 0, noSpeech = p.speech === 'none' || p.speech === 'no_track';
  STEPS.forEach(([key], i) => {
    let state = i < cur ? 'done' : (i === cur ? 'active' : 'pending');
    let note = '';
    if (key === 'faces' && p.faces_found != null) note = p.faces_found === 0 ? 'No face found' : `${p.faces_found} face frame${p.faces_found === 1 ? '' : 's'} found`;
    if (key === 'face_check' && noFace && i < cur) { state = 'skipped'; note = 'No face to check'; }
    if (key === 'speech' && p.speech) note = { found: 'Speech found', none: 'No speech found', no_track: 'No sound track' }[p.speech] || '';
    if (key === 'voice' && noSpeech && i < cur) { state = 'skipped'; note = 'No speech to check'; }
    if (!note && state === 'done') note = 'Done';
    const el = $(`#st-${key}`); if (!el) return;
    if (el.dataset.state !== state) {       // only on a change, so the tick animation does not replay on every poll
      el.dataset.state = state; el.className = `step ${state}`;
      $('.st', el).innerHTML = state === 'done' ? icon('check') : state === 'skipped' ? icon('minus') : '';
    }
    $('small', el).textContent = note;
  });
}

// ── Notification when a check finishes ────────────────────────────────────
let notifyTimer = null;
function notify(id) {
  const r = S.results[id]; if (!r || S.notified.has(id)) return;
  S.notified.add(id);
  const n = $('#notify'), job = S.queue.find(j => j.id === id);
  const name = displayName(r.filename || (job && job.filename));
  const d = r.error ? { tone: 'manip', headline: 'Could not check' } : describe(r);
  n.innerHTML = `<span class="n-ico">${BRAND}</span><span><span class="n-top"><span>Clipcheck</span><span>now</span></span>
    <span class="n-title tone-${d.tone}">${esc(d.headline)}</span><span class="n-body">${esc(name)}</span></span>`;
  n.setAttribute('aria-label', `Check finished: ${d.headline}, ${name}`);
  n.hidden = false; n.classList.remove('hide', 'show'); void n.offsetWidth; n.classList.add('show');
  // Centre the notification on the menu bar's middle line.
  const bar = $$('.bar, .ln-head').find(e => e.offsetParent !== null);
  if (bar) { const b = bar.getBoundingClientRect(); n.style.top = `${Math.max(2, b.top + b.height / 2 - n.offsetHeight / 2).toFixed(1)}px`; }
  clearTimeout(notifyTimer); notifyTimer = setTimeout(hideNotify, 4600);
  n.onclick = hideNotify;
}
function hideNotify() {
  const n = $('#notify'); if (n.hidden) return;
  n.classList.remove('show'); n.classList.add('hide');
  setTimeout(() => { n.hidden = true; }, RM.matches ? 0 : 340);
}

// ── Result ────────────────────────────────────────────────────────────────
async function showResult(id) {
  if (!S.results[id]) {
    const resp = await fetch(`/api/result/${encodeURIComponent(id)}`);
    if (resp.status === 202) { location.replace(`#/analysing/${id}`); return; }
    if (!resp.ok) {
      stage.innerHTML = `<section class="center"><div class="win glass hist pop-in"><h1 class="title1">Check not found</h1>
        <p class="sub">This check is no longer available (checks are kept while the tool is running). <a href="#/check">Check a video</a>.</p></div></section>`;
      return;
    }
    S.results[id] = await resp.json();
  }
  if (!S.queue.length) await refreshQueue();
  renderResult(id);
}
function scores(r, d, anim) {
  const { pv, pa, T } = d;
  const SEG = 20;
  const meter = (p, label) => {
    const n = p > 0 ? Math.max(1, Math.ceil(p * SEG - 1e-9)) : 0;
    return `<div class="meter ${anim ? 'anim' : ''}" data-n="${n}" style="--p:${p.toFixed(4)}" role="img" aria-label="${label}: ${pct(p)} chance of manipulation">${
      Array.from({ length: SEG }, (_, k) => `<i class="${!anim && k < n ? 'on' : ''}" style="--sc:${meterColor((k + 0.5) / SEG)}"></i>`).join('')}<span class="half"></span><span class="peak"></span></div>`;
  };
  const row = kind => {
    const pic = kind === 'picture', p = pic ? pv : pa;
    const lab = `${icon(pic ? 'face' : 'voice')} ${term(pic ? 'Picture' : 'Voice', pic ? 'picture' : 'voice')}`;
    if (p == null) return `<div class="cc-row off"><div class="head">${lab}<span class="lean">Not checked</span></div>
      <div class="cc-grid"><div class="meter off"><span class="cap-none">${esc(cap1(pic ? missingVideoReason(r) : missingAudioReason(r)))}</span></div><div></div></div></div>`;
    const ood = pic ? r.video.ood : r.audio.ood;
    return `<div class="cc-row"><div class="head">${lab}<span class="lean">${lean(p)}${ood && ood.unfamiliar ? ', <span class="tone-caution">unfamiliar</span>' : ''}</span></div>
      <div class="cc-grid">${meter(p, pic ? 'Picture' : 'Voice')}<div class="cap-val">${pct(p)}</div></div></div>`;
  };
  let gap = '';
  if (pv != null && pa != null && T != null) {
    const x1 = Math.min(pv, pa) * 100, x2 = Math.max(pv, pa) * 100, t = T * 100, c = (x1 + x2) / 2;
    const toRight = x1 + t <= 100, rs = toRight ? x1 : x2 - t;
    const bl = c < 22 ? `left:${x1}%` : c > 78 ? `right:${100 - x2}%` : `left:${c}%;transform:translateX(-50%)`;
    const rl = toRight ? (x1 + t <= 70 ? `left:calc(${x1 + t}% + 8px)` : `right:calc(${100 - x1}% + 8px)`) : `right:calc(${100 - rs}% + 8px)`;
    gap = `<div class="cc-grid"><div class="cc-gap" aria-hidden="true">
      <span class="bracket ${anim ? 'grow-in' : ''}" style="left:${x1}%;width:${Math.max(x2 - x1, 0.6)}%"></span>
      <span class="b-label ${anim ? 'fade-in' : ''}" style="${bl}">${points(Math.abs(pv - pa))} points apart</span>
      <span class="ruler ${toRight ? '' : 'from-right'} ${anim ? 'grow-in' : ''}" style="left:${rs}%;width:${t}%"></span>
      <span class="r-label ${anim ? 'fade-in' : ''}" style="${rl}">${points(T)}-point line</span>
    </div><div></div></div>`;
  }
  let comb = '';
  if (pv != null && pa != null && r.verdict !== 'PARTIAL_MANIPULATION' && r.overall_score != null) {
    const w = (r.fusion && r.fusion.weights) || {};
    comb = `<div class="cc-row"><div class="head">${icon('merge')} ${term('Combined', 'combined')}<span class="lean">${w.audio != null ? `voice counts ${Math.round(w.audio * 100)}%, picture ${Math.round(w.video * 100)}%` : ''}</span></div>
      <div class="cc-grid">${meter(r.overall_score, 'Combined')}<div class="cap-val">${pct(r.overall_score)}</div></div></div>`;
  }
  return `<div class="cc inset">
    <div class="cc-grid"><div class="cc-scale" aria-hidden="true"><span>0%</span><span>50%: unsure</span><span>100%</span></div><div></div></div>
    ${row('picture')}${row('voice')}${gap}${comb}</div>
    ${d.gap ? `<p class="gap-text">${d.gap}</p>` : ''}`;
}
function plainFallback(reason) {
  const t = String(reason || '').toLowerCase();
  if (t.includes('faithfulness')) return "The AI model's text said something the results do not support, so standard wording is shown.";
  if (t.includes('reach') || t.includes('unavailable') || t.includes('ollama') || t.includes('empty')) return 'The AI model was not available, so standard wording is shown.';
  if (t.includes('withheld') || t.includes('no score') || t.includes('produced a score') || t.includes('nothing for the language model'))
    return 'There were no scores to explain, so standard wording is shown.';
  return reason ? `Standard wording is shown: ${reason}.` : 'Standard wording is shown.';
}
function explanation(r) {
  const e = r.explanation || {};
  if (!e.available) return `<section class="sec"><h2 class="h2">What the tool found</h2><p>${esc(e.unavailable_reason || 'No written explanation is available for this clip.')}</p></section>`;
  const llm = e.source === 'llama3';
  const by = llm ? `<span class="byline">${icon('pen')} ${e.faithfulness && e.faithfulness.passed ? 'Written by Llama 3 8B, checked against the results' : 'Written by Llama 3 8B'}</span>`
    : `<span class="byline">${icon('template')} Standard wording</span>`;
  return `<section class="sec"><div class="sec-h"><h2 class="h2">What the tool found</h2>${by}</div>
    <p class="explain-text">${esc(e.text.trim())}</p>
    <p class="note">${llm ? `About the ${term('written explanation', 'explanation')}.` : `${esc(plainFallback(e.fallback_reason))} About ${term('standard wording', 'standard')}.`}</p>
    ${e.withheld_note ? `<p class="note">${esc(e.withheld_note)}</p>` : ''}
    ${e.rejected_llm_text ? `<details class="rej"><summary>Show the AI model's text that was not used</summary><blockquote>${esc(e.rejected_llm_text)}</blockquote></details>` : ''}
  </section>`;
}
function momentMarks(r, dur) {
  return (r.anomalies || []).filter(m => m.start != null && dur).map(m => {
    const L = Math.min(100, m.start / dur * 100), W = Math.max(1.5, Math.min(100 - L, (m.end - m.start) / dur * 100));
    return `<span class="mom" style="left:${L}%;width:${W}%"></span>`;
  }).join('');
}
function playerSection(id, r, dur) {
  const v = r.video, a = r.audio || {};
  const an = (r.anomalies || []).filter(m => m.start != null);
  const frames = v && v.per_frame && v.per_frame.length
    ? `<div class="frames">${v.per_frame.map(p => `<i class="${p >= 0.5 ? 'hi' : ''}" style="height:${Math.max(5, p * 100).toFixed(1)}%"></i>`).join('')}</div>`
    : '<span class="trk-none">No face found</span>';
  const wmax = a.waveform && a.waveform.length ? Math.max(...a.waveform, 1e-6) : 1;
  const wave = a.waveform && a.waveform.length
    ? `<div class="wave">${a.waveform.map(x => `<i style="height:${Math.max(5, x / wmax * 100).toFixed(1)}%"></i>`).join('')}</div>`
    : `<span class="trk-none">${a.available === false ? 'No sound track' : 'No speech found'}</span>`;
  const chips = !v ? '<p class="note">The picture was not checked, so there are no moments to mark.</p>'
    : an.length ? `<div class="chips">${an.map((m, k) => `<button type="button" class="chip-btn" data-seek="${m.start}"><i></i>${esc(fmtWindow(m))} <span>peak ${pct(m.peak_score)}</span></button>`).join('')}</div>`
      : '<p class="note">No suspicious moments: the picture check did not reach 50% at any point.</p>';
  return `<section class="sec res-play"><div class="play-h"><h2 class="h2">When in the clip</h2>
    <p class="note">Marks show ${term('when', 'moments')} the picture check's estimate was high, not what looks wrong. Each bar on the picture track is one checked face frame, in order. Click the tracks to move through the clip.</p></div>
    <div class="player inset">
      <video id="vid" src="/api/video/${encodeURIComponent(id)}" preload="metadata" playsinline></video>
      <div class="p-row"><button type="button" class="round" id="p-play" aria-label="Play">${icon('play')}</button><span class="p-time tnum" id="p-time">0:00 / ${fmtTime(dur)}</span></div>
      <div class="tl-lanes" id="tl-lanes" role="slider" tabindex="0" aria-label="Position in clip" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">
        <div class="tl-row"><span>Picture</span><div class="trk" id="trk-pic">${frames}<span id="moms">${momentMarks(r, dur)}</span></div></div>
        <div class="tl-row"><span>Voice</span><div class="trk">${wave}</div></div>
        <span class="playhead" id="playhead"></span>
      </div>
      <div class="tl-time tnum"><span>0:00</span><span id="tl-end">${fmtTime(dur)}</span></div>
    </div>
    <div class="p-foot">${chips}
    ${a.p_audio_fake != null ? '<p class="note">The voice check gives one estimate for the whole clip, so it cannot mark moments.</p>' : ''}</div>
  </section>`;
}
function wirePlayer(r, dur0) {
  const v = $('#vid'); if (!v) return;
  const lanes = $('#tl-lanes'), ph = $('#playhead');
  const dur = () => v.duration || dur0 || 0;
  const draw = () => {
    const D = dur(), f = D ? Math.min(1, (v.currentTime || 0) / D) : 0;
    ph.style.left = `calc(62px + (100% - 62px) * ${f.toFixed(4)})`;
    lanes.setAttribute('aria-valuenow', String(Math.round(f * 100)));
    $('#p-time').textContent = `${fmtTime(v.currentTime || 0)} / ${fmtTime(D)}`;
  };
  let raf = null;
  const loop = () => { draw(); raf = v.paused ? null : requestAnimationFrame(loop); };
  const setBtn = (playing) => { const b = $('#p-play'); b.innerHTML = icon(playing ? 'pause' : 'play'); b.setAttribute('aria-label', playing ? 'Pause' : 'Play'); };
  v.addEventListener('play', () => { setBtn(true); if (!raf) loop(); });
  v.addEventListener('pause', () => { setBtn(false); draw(); });
  v.addEventListener('seeked', draw);
  v.addEventListener('loadedmetadata', () => { $('#moms').innerHTML = momentMarks(r, dur()); $('#tl-end').textContent = fmtTime(dur()); draw(); });
  const toggle = () => (v.paused ? v.play() : v.pause());
  $('#p-play').onclick = toggle;
  v.addEventListener('click', toggle);
  const seek = (e) => {
    const b = $('#trk-pic').getBoundingClientRect();
    const f = Math.min(1, Math.max(0, (e.clientX - b.left) / b.width));
    if (dur()) { v.currentTime = f * dur(); draw(); }
  };
  let drag = false;
  lanes.addEventListener('pointerdown', e => { drag = true; lanes.setPointerCapture(e.pointerId); seek(e); });
  lanes.addEventListener('pointermove', e => { if (drag) seek(e); });
  lanes.addEventListener('pointerup', () => { drag = false; });
  lanes.addEventListener('keydown', e => {
    if (e.key === 'ArrowRight') { v.currentTime = Math.min(dur(), v.currentTime + 1); e.preventDefault(); }
    if (e.key === 'ArrowLeft') { v.currentTime = Math.max(0, v.currentTime - 1); e.preventDefault(); }
    if (e.key === ' ') { toggle(); e.preventDefault(); }
  });
  $$('.chip-btn[data-seek]').forEach(b => b.addEventListener('click', () => { v.currentTime = parseFloat(b.dataset.seek); v.play(); }));
  draw();
}
function nextSteps(r, d, unf) {
  const it = [];
  if (unf.length) it.push(['alert', 'Treat this result with extra caution: the clip is unfamiliar to the tool.']);
  it.push(['scale', 'Use this as one input, not proof. The tool gives likelihoods.']);
  it.push(['link', 'Check where the clip came from and whether others have published it.']);
  if (r.anomalies && r.anomalies.length) it.push(['replay', 'Look again at the marked moments.']);
  else if (d.tone === 'partial' && r.fusion && r.fusion.implicated_modality === 'audio') it.push(['replay', 'Listen to the speech again.']);
  else if (d.tone !== 'none') it.push(['replay', 'Watch and listen to the whole clip again.']);
  return `<section class="sec"><h2 class="h2">Before you share it</h2><ul class="todo">${it.map(([ic, t]) => `<li>${icon(ic)}<span>${esc(t)}</span></li>`).join('')}</ul></section>`;
}
function renderResult(id) {
  const r = S.results[id];
  const job = S.queue.find(j => j.id === id);
  const filename = r.filename || (job && job.filename);
  const name = displayName(filename);
  const demo = demoFor(filename);
  const word = (s) => ({ changed: 'fake', genuine: 'real', absent: 'none' }[s] || 'unknown');
  const known = demo && demo.changes && !S.testing ? `Demo video; known answer: face ${word(demo.changes.picture)}, voice ${word(demo.changes.voice)}. ` : '';
  const head = `
    <div class="res-head">
      <a class="round" id="back" href="#/check" aria-label="Back to Check a video">${icon('arrowLeft')}</a>
      <div class="grow"><div class="res-name">${esc(name)}</div><div class="res-when">${esc(known)}Checked ${esc(fmtDate(r.analyzed_at))}</div></div>
      <div class="res-actions">
        <button type="button" class="btn" id="btn-details">${icon('details')} Details</button>
        <button type="button" class="btn" id="btn-pdf">${icon('fileDown')} Save as PDF</button>
        <button type="button" class="btn" id="btn-copy">${icon('copy')} <span>Copy data</span></button>
      </div>
    </div>`;
  S.cur = id;
  if (r.error) {
    setTone('manip');
    stage.innerHTML = `<article class="win glass res pop-in">${head}<div class="notice" style="margin-top:20px">${icon('info')}<span>This clip could not be checked: ${esc(r.error)}</span></div></article>`;
    wireResultButtons(r);
    return;
  }
  const d = describe(r), unf = unfamiliarParts(r);
  const anim = !S.shown.has(id) && !RM.matches;
  S.shown.add(id);
  setTone(d.tone);
  const dur = (job && job.duration) || (r.audio && r.audio.seconds) || 0;
  stage.innerHTML = `
    <article class="win glass res pop-in" aria-labelledby="v-head">
      ${head}
      <div class="res-top">
        <div class="verdict">
          <span class="v-ico tone-${d.tone}">${icon(d.icon)}</span>
          <div>
            <h1 class="v-head tone-${d.tone}" id="v-head">${esc(d.headline)}</h1>
            ${unf.length ? '<p class="maybe">but it may be wrong for this clip</p>' : ''}
            <p class="v-reason">${esc(d.reason)}</p>
            ${unf.length ? `<div class="caution" role="note">${icon('alert')}<div><h3>Treat this verdict with caution</h3>
              <p>This clip's ${unf.join(' and ')} ${unf.length > 1 ? 'are' : 'is'} unlike what the tool learned from. In testing on an unfamiliar video collection, every wrong verdict carried this warning. See ${term('Unfamiliar clip', 'unfamiliar')}.</p></div></div>` : ''}
          </div>
        </div>
        <div class="col">${scores(r, d, anim)}</div>
      </div>
      ${playerSection(id, r, dur)}
      <div class="res-more">
        ${explanation(r)}
        ${nextSteps(r, d, unf)}
      </div>
      <section class="print-only" aria-hidden="true">
        <h2 class="h2">Findings for this clip</h2>${findings(r)}
        <h2 class="h2">Technical details</h2>${technical(r)}
        <h2 class="h2">Accuracy and limits</h2>${limitsPanel()}
        <h2 class="h2">Glossary</h2>${glossary()}
      </section>
    </article>`;
  wireResultButtons(r);
  wirePlayer(r, dur);
  // Meters light segment by segment on the first view, like a level meter taking a signal.
  if (anim) $$('.meter[data-n]').forEach(m => $$('i', m).slice(0, +m.dataset.n).forEach((seg, k) => setTimeout(() => seg.classList.add('on'), 250 + k * 38)));
}
function wireResultButtons(r) {
  $('#btn-copy').onclick = async () => {
    const ok = await copyText(JSON.stringify(r, null, 2));
    const span = $('#btn-copy span'); span.textContent = ok ? 'Copied' : 'Copy failed';
    setTimeout(() => { span.textContent = 'Copy data'; }, 1400);
  };
  $('#btn-pdf').onclick = () => window.print();
  $('#btn-details').onclick = () => openSheet();
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

// ── Details sheet (findings, technical details, accuracy and limits, glossary) ──
const TABS = [['findings', 'Findings'], ['technical', 'Technical'], ['limits', 'Accuracy and limits'], ['glossary', 'Glossary']];
function openSheet(tab) {
  if (S.cur == null || !S.results[S.cur]) return;
  closePop(); if (tab) S.tab = tab;
  S.lastFocus = document.activeElement;
  const job = S.queue.find(j => j.id === S.cur);
  const s = document.createElement('div');
  s.className = 'scrim'; s.id = 'sheet';
  s.innerHTML = `<div class="sheet glass" role="dialog" aria-modal="true" aria-labelledby="sh-t">
    <div class="sheet-head"><div><h2 class="h2" id="sh-t">Details</h2><p class="note">${esc(displayName(S.results[S.cur].filename || (job && job.filename)))}</p></div>
      <div class="seg" role="tablist" aria-label="Details">${TABS.map(([k, l]) => `<button type="button" role="tab" data-tab="${k}">${l}</button>`).join('')}<span class="thumb" aria-hidden="true"></span></div>
      <button type="button" class="round" id="sh-x" aria-label="Close details">${icon('x')}</button></div>
    <div id="sh-body"></div></div>`;
  document.body.appendChild(s);
  $$('[role="tab"]', s).forEach(b => b.addEventListener('click', () => { S.tab = b.dataset.tab; renderTab(); }));
  $('#sh-x', s).onclick = closeSheet;
  s.addEventListener('click', e => { if (e.target === s) closeSheet(); });
  renderTab(); $('#sh-x', s).focus();
}
function closeSheet() {
  const s = $('#sheet'); if (!s) return;
  s.id = ''; s.classList.add('closing'); setTimeout(() => s.remove(), RM.matches ? 0 : 200);
  if (S.lastFocus && S.lastFocus.focus && document.contains(S.lastFocus)) S.lastFocus.focus();
}
function renderTab() {
  const s = $('#sheet'); if (!s) return;
  const r = S.results[S.cur];
  $$('[role="tab"]', s).forEach(b => b.setAttribute('aria-selected', String(b.dataset.tab === S.tab)));
  moveThumb($('.seg', s), $('[aria-selected="true"]', s));
  $('#sh-body', s).innerHTML = { findings, technical, limits: limitsPanel, glossary }[S.tab](r);
}
const VIOLATION_WORDS = { direction: 'it described a part as manipulated when the results say it leans genuine (or the reverse)',
  number: 'it gave a number that is not in the results', disagreement: 'it misstated whether the two checks disagree',
  certainty: 'it sounded more certain than the results allow', unlisted: 'it mentioned something the results do not contain',
  timing: 'it gave a time that is not one of the suspicious moments', unevaluated: 'it judged a part that was not checked' };
function familiarity(ood, checked) {
  if (!checked) return 'Not checked';
  if (!ood) return 'Not measured';
  return `${ood.unfamiliar ? '<span class="tone-caution">Unfamiliar to the tool</span>' : 'Within what the tool knows'} <span class="note">(distance ${esc(ood.distance)}, limit ${esc(ood.threshold)})</span>`;
}
function findings(r) {
  const v = r.video, a = r.audio || {}, T = r.fusion && r.fusion.threshold_T, e = r.explanation || {}, f = e.faithfulness;
  const an = r.anomalies || [];
  return `<div class="grid2">
    <div class="cell inset"><h4>Picture check</h4>${v ? `<p>${pct(v.p_fake)} chance the picture is manipulated, from ${v.n_faces} face frame${v.n_faces === 1 ? '' : 's'}.</p>` : `<p>${esc(cap1(missingVideoReason(r)))}.</p>`}</div>
    <div class="cell inset"><h4>Voice check</h4>${a.p_audio_fake != null ? `<p>${pct(a.p_audio_fake)} chance the voice is manipulated.</p>` : `<p>Not checked: ${esc(missingAudioReason(r))}.</p>`}
      ${a.speech_seconds != null ? `<p class="note">${a.speech_seconds.toFixed(1)} s of speech found in ${fmtTime(a.seconds)} of sound.</p>` : ''}</div>
    <div class="cell inset"><h4>How far apart the checks were</h4>${v && v.p_fake != null && a.p_audio_fake != null && T != null
      ? `<p>${points(Math.abs(v.p_fake - a.p_audio_fake))} points apart. The line for "partly manipulated" is ${points(T)} points.</p>` : '<p>Only one check gave a score, so there is nothing to compare.</p>'}</div>
    <div class="cell inset"><h4>Suspicious moments</h4>${!v ? '<p>The picture was not checked.</p>' : an.length ? `<ul class="list">${an.map(x => `<li>${esc(fmtWindow(x))}, peak ${pct(x.peak_score)}</li>`).join('')}</ul>` : '<p>None marked.</p>'}</div>
    <div class="cell inset"><h4>Familiarity</h4><div class="kv"><div><b>Face footage:</b> ${familiarity(v && v.ood, !!v)}</div><div><b>Speech:</b> ${familiarity(a.ood, a.p_audio_fake != null || !!a.withheld)}</div></div></div>
    <div class="cell inset"><h4>The explanation</h4>${!e.available ? `<p>${esc(e.unavailable_reason || 'No explanation.')}</p>` : `
      <div class="kv"><div><b>Written by:</b> ${e.source === 'llama3' ? 'the AI model (Llama 3 8B)' : 'standard wording (no AI model)'}</div><div><b>Automatic check:</b> ${f ? (f.passed ? 'passed' : 'did not pass') : 'not run'}</div></div>
      ${f && !f.passed && f.violations && f.violations.length ? `<p class="note">Why: ${esc([...new Set(f.violations.map(x => VIOLATION_WORDS[x.type] || x.type))].join('; '))}.</p>` : ''}`}</div>
  </div>`;
}
function technical(r) {
  const mi = (S.modelInfo && S.modelInfo.models) || [], sh = S.evaluation && S.evaluation.shipped, fu = r.fusion || {};
  const wv = fu.video_accuracy && fu.audio_accuracy ? fu.video_accuracy / (fu.video_accuracy + fu.audio_accuracy) : null;
  return `<div class="grid2">
    <div class="cell inset"><h4>Models behind each step</h4><ul class="models">${mi.map(m => `<li><span>${esc(m.name)}<small>${esc(m.stage)}</small></span><span>${esc(m.status)}</span></li>`).join('')}</ul></div>
    <div class="cell inset"><h4>What ran on this clip</h4><ul class="models">${(r.models_ran || []).map(m => `<li><span>${esc(m.model)}</span><span>${esc(m.produced || '')}${m.time_s != null ? `<small class="tnum">${m.time_s} s</small>` : ''}</span></li>`).join('')}</ul></div>
    <div class="cell inset"><h4>Model version</h4><p class="tnum">${sh ? esc(String(sh.checkpoint_sha256 || '').slice(0, 12)) : 'not recorded'}</p>${sh ? `<p class="note">${esc(sh.arch)}, seed ${esc(sh.seed)}, trained on ${esc(sh.trained_on)}</p>` : ''}</div>
    <div class="cell inset"><h4>Combining the checks</h4><p>${wv != null ? `Weights: voice ${(1 - wv).toFixed(2)}, picture ${wv.toFixed(2)}.` : ''} ${fu.threshold_T != null ? `Disagreement line T = ${fu.threshold_T.toFixed(2)}.` : ''}</p>
      <p class="note">Faces: FaceForensics++. Voices: ASVspoof 2019 LA.</p></div>
  </div>`;
}
function limitsPanel() {
  const L = S.limitations, st = S.stats || {};
  return `<div class="grid2">
    <div class="cell inset">${st.acc != null ? `<div class="widget" style="padding:0"><div class="big">${Math.round(st.acc)} in 100</div><p>judged correctly on people the tool had not seen (95% range ${Math.round(st.lo)}% to ${Math.round(st.hi)}%).</p></div>` : '<p>Accuracy figures are not available.</p>'}
      <p style="margin-top:14px"><a class="btn sec-print-hide" href="#/accuracy">Open the Accuracy page</a></p></div>
    <div class="cell inset"><h4>Limits</h4>${L ? `<p class="note">${esc(L.how_to_read)}</p><ul class="list" style="margin-top:10px">${L.limitations.map(l => `<li>${esc(l.text)}</li>`).join('')}</ul>` : '<p>The limits could not be loaded.</p>'}</div>
  </div>`;
}
function glossary() {
  return `<div class="gloss">${Object.values(legend()).map(([t, def, tech]) => `<div class="cell inset"><h4>${esc(t)}</h4><p>${esc(def)}</p>${tech ? `<p class="note">Technical name: ${esc(tech)}</p>` : ''}</div>`).join('')}</div>`;
}

// ── History ───────────────────────────────────────────────────────────────
function renderHistory() {
  const rows = S.queue.slice().reverse();
  stage.innerHTML = `<section class="center"><div class="win glass hist pop-in">
    <h1 class="title1">Past checks</h1>
    <p class="sub">Kept while the tool is running. Open a check to save it as a PDF.</p>
    ${rows.length ? `<div class="h-list">${rows.map(j => {
      const r = S.results[j.id], d = r && !r.error ? describe(r) : null;
      const href = j.status === 'done' ? `#/result/${j.id}` : `#/analysing/${j.id}`;
      const actions = S.confirmDelete === j.id
        ? `<span class="confirm">Remove this check?
             <button type="button" class="btn btn-danger" data-del-yes="${j.id}">Remove</button>
             <button type="button" class="btn" data-del-no>Cancel</button></span>`
        : `${verdictChip(j)}
           <button type="button" class="icon-btn" data-copy="${j.id}" aria-label="Copy the data for this check" ${r ? '' : 'disabled'}>${icon('copy')}</button>
           <button type="button" class="icon-btn" data-del="${j.id}" aria-label="Remove this check">${icon('trash')}</button>`;
      return `<div class="h-row inset"><a class="h-open" href="${href}"><span class="h-gly ${d ? `tone-${d.tone}` : 'tone-none'}">${icon(d ? d.icon : 'loader')}</span>
        <span class="grow"><b>${esc(displayName(j.filename))}</b><small>${r ? esc(fmtDate(r.analyzed_at)) : (j.status === 'error' ? 'Could not be checked' : 'Not finished')}</small></span></a>
        <span class="h-actions">${actions}</span></div>`;
    }).join('')}</div>`
      : '<div class="empty inset"><p>No checks yet. Upload a video or open a demo video to see it here.</p><a class="btn btn-primary" href="#/check"><span>Check a video</span></a></div>'}
  </div></section>`;
  $$('[data-copy]').forEach(b => b.onclick = async () => {
    const ok = await copyText(JSON.stringify(S.results[b.dataset.copy], null, 2));
    b.setAttribute('aria-label', ok ? 'Copied' : 'Copy failed'); b.innerHTML = icon(ok ? 'check' : 'info');
    setTimeout(() => { b.innerHTML = icon('copy'); b.setAttribute('aria-label', 'Copy the data for this check'); }, 1400);
  });
  $$('[data-del]').forEach(b => b.onclick = () => { S.confirmDelete = b.dataset.del; renderHistory(); });
  $$('[data-del-no]').forEach(b => b.onclick = () => { S.confirmDelete = null; renderHistory(); });
  $$('[data-del-yes]').forEach(b => b.onclick = async () => {
    const id = b.dataset.delYes;
    await fetch(`/api/queue/${id}`, { method: 'DELETE' });
    delete S.results[id]; S.confirmDelete = null;
    await refreshQueue(); renderHistory();
  });
}

// ── Accuracy ──────────────────────────────────────────────────────────────
function renderAccuracy() {
  const st = S.stats || {}, ev = S.evaluation, F = S.fusion, L = S.limitations;
  const w = [];
  if (st.acc != null) w.push([`${Math.round(st.acc)} in 100`, `judged correctly on people it had not seen. The true figure is probably between ${Math.round(st.lo)} and ${Math.round(st.hi)}.`]);
  if (st.celeb != null) w.push([`${Math.round(st.celeb)} in 100`, 'right on a different video collection (Celeb-DF) that it never learned from.']);
  if (st.celebFA != null) w.push([`${Math.round(st.celebFA)} in 100`, `genuine videos in that collection wrongly flagged as manipulated (${term('false alarms', 'falsealarm')}).`]);
  if (st.vFlag != null) w.push([`${st.vFlag} of ${st.vTot}`, 'genuine voices recorded somewhere unfamiliar were called synthetic.']);
  const four = st.four && st.four.every(x => x[1] != null) ? `
    <div class="widget inset wide">
      <h3>Why it names the part instead of averaging</h3>
      <p>Accuracy on ${st.adv ? st.adv.n : 'the'} built test clips of people the tool had not seen, mixing genuine and replaced faces and voices.</p>
      <div class="bars">${st.four.map(([l, v], k) => `<div class="bar-row ${k === 3 ? 'best' : ''}"><span>${esc(l)}</span><span class="bar-track"><span style="--w:${v}%"></span></span><span class="val">${v}%</span></div>`).join('')}</div>
      ${st.adv ? `<p class="note" style="margin-top:12px">Naming the part was ${st.adv.d} points more accurate than averaging (95% range ${st.adv.lo} to ${st.adv.hi}). It named the voice correctly in ${st.namedAudio}% of clips with a replaced voice, and the face in ${st.namedVideo}% of clips with a replaced face.</p>` : ''}
    </div>` : '';
  const tables = ev ? ev.sections.map(s => {
    if (s.status !== 'current') return `<details class="table-card inset"><summary><h3>${esc(s.title)}</h3></summary><p class="pending">Not shown: ${esc(s.reason || 'pending')}</p></details>`;
    const numCol = (c) => /^[+\-−]?[\d.]/.test(String(c)) || /%|pp\b| s$/.test(String(c));
    return `<details class="table-card inset"><summary><h3>${esc(s.title)}</h3><span class="note">${s.rows.length} row${s.rows.length === 1 ? '' : 's'}</span></summary><div class="table-scroll"><table class="data">
      <thead><tr>${s.columns.map(c => `<th>${esc(c)}</th>`).join('')}</tr></thead>
      <tbody>${s.rows.map(r => `<tr${String(r[0]).includes('[SHIPPED]') ? ' class="shipped"' : ''}>${r.map((c, i) => `<td class="${i > 0 && numCol(c) && String(c).length < 40 ? 'num' : ''}">${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>
      ${s.note ? `<p class="t-note">${esc(s.note)}</p>` : ''}<p class="t-src">Source: ${esc(s.source)}</p></details>`;
  }).join('') : '<p class="note">The evaluation results could not be loaded.</p>';
  stage.innerHTML = `<section class="center"><div class="win glass acc pop-in">
    <h1 class="title1">How accurate is this tool?</h1>
    <p class="sub">Useful, but not always right. It works best on clips like the ones it learned from, and it gets worse on unfamiliar footage or recordings.</p>
    <div class="widgets">${w.map(([n, t]) => `<div class="widget inset"><div class="big">${esc(n)}</div><p>${t}</p></div>`).join('')}${four}</div>
    <p class="note" style="margin-top:14px">It covers three common face-manipulation methods, not every method. Read each figure as an estimate from a limited test.</p>
    ${F ? `<div class="acc-sec"><h2 class="h2">How the two checks are combined</h2>
      <div class="cell inset"><div class="kv">
        <div><b>Disagreement line:</b> ${points(F.threshold_T)} points. At or above it the result is ${term('partly manipulated', 'partly')}.</div>
        <div><b>Weights when they agree:</b> voice ${F.w_audio.toFixed(2)}, picture ${F.w_video.toFixed(2)}, from each check's measured accuracy.</div></div></div></div>` : ''}
    ${L ? `<div class="acc-sec"><h2 class="h2">Limits</h2><div class="cell inset"><ul class="list">${L.limitations.map(l => `<li>${esc(l.text)}</li>`).join('')}</ul></div></div>` : ''}
    <div class="acc-sec"><h2 class="h2">For experts: research tables</h2><p class="note">Every table the figures above come from. Open one to see it.</p><div class="tables">${tables}</div>
      ${ev ? `<p class="t-src" style="padding:0">Generated ${esc(ev.generated_at || 'unknown')} by scripts/build_numbers.py from results/numbers.json.</p>` : ''}</div>
    <div class="acc-sec"><h2 class="h2">Glossary</h2>${glossary()}</div>
  </div></section>`;
}

// ── Landing page: the front door at "/", which opens into the app ─────────
// Two real checks used as worked examples: saved results of 26 Sep 2026 from /api/result (checking the demo again gives today's
// numbers). The verdicts are not stored here; they are worked out below with the same rule as scripts/fusion.py.
const WORKED = {
  voice: { code: 'RVFA_000', pv: 0.0984, pa: 1.0 },                                                        // Webcam streamer, voice replaced
  face: { code: 'FVRA_000', pv: 0.9995, pa: 0.0007, faces: 16, speech: 3.664, sound: 4.864, from: 0, to: 5.12 }, // Business newsreader, face replaced
};
// scripts/fusion.py's rule: a gap of T or more is "partly manipulated" (the higher part named); otherwise an accuracy-weighted average.
function fuse(pv, pa) {
  const F = S.fusion || {}, T = F.threshold_T;
  const r = { video: { p_fake: pv }, audio: { available: true, p_audio_fake: pa }, fusion: { threshold_T: T, weights: { video: F.w_video, audio: F.w_audio } } };
  if (T != null && Math.abs(pv - pa) >= T) { r.verdict = 'PARTIAL_MANIPULATION'; r.fusion.implicated_modality = pv > pa ? 'video' : 'audio'; }
  else { r.overall_score = F.w_video * pv + F.w_audio * pa; r.verdict = r.overall_score >= 0.5 ? 'FAKE' : 'REAL'; }
  return r;
}
const meterMarkup = (id) => `<div class="meter" id="${id}">${Array.from({ length: 20 }, (_, k) => `<i style="--sc:${meterColor((k + 0.5) / 20)}"></i>`).join('')}<span class="half"></span></div>`;
function setMeter(el, p) {
  if (!el) return;
  const n = p > 0 ? Math.max(1, Math.ceil(p * 20 - 1e-9)) : 0;
  $$('i', el).forEach((seg, k) => seg.classList.toggle('on', k < n));
}
const demoByCode = (code) => S.demos.find(d => d.code === code);
// The hero: the mark in a scanning frame. The human half winks; the scan line turns the face and the title from grey into their real
// colours and back; scrolling splits the face (the human half grins, tilts away and breaks into round dots; the machine half's square
// pixels scatter) and carries each half of the title away with it.
const HERO_PX = [];
for (let y = 14; y <= 48; y += 5.5) for (let x = 34; x <= 50; x += 5.5) {
  const dx = (x + 2 - 32) / 18, dy = (y + 2 - 32) / 20;
  if (dx * dx + dy * dy <= 1) HERO_PX.push({ x, y, k: (Math.abs(x - 39.5) < 1 && Math.abs(y - 25) < 1) || (Math.abs(y - 41.5) < 1 && x < 42),
    dx: 6 + Math.random() * 30, dy: Math.random() * 36 - 18, r: Math.random() * 200 - 100 });
}
// Dots spaced along the outline (top to bottom) and the smile; each flies off from exactly where it sat on the face.
const HERO_ARC = Array.from({ length: 22 }, (_, i) => { const t = -Math.PI / 2 + Math.PI * i / 21;
  return { x: 31 - 18 * Math.cos(t), y: 32 + 20 * Math.sin(t), dx: -(8 + Math.random() * 26), dy: Math.random() * 30 - 15 }; });
const HERO_SMILE = [[24.4, 41.3], [27.6, 43.4], [30.8, 43.6]].map(([x, y]) => ({ x, y, dx: -(10 + Math.random() * 22), dy: 8 + Math.random() * 16 }));
// Two blinks every 4.4 s; every eye on the page shares the document timeline, so the grey, coloured and split faces blink together.
const WINK = '<animate attributeName="ry" values="2.2;2.2;0.25;2.2;2.2;0.25;2.2;2.2" keyTimes="0;.42;.46;.5;.86;.9;.94;1" dur="4.4s" repeatCount="indefinite"/>';
function heroFace(hc, pc, glow) {
  const g = (c) => (glow ? ` style="filter:drop-shadow(0 0 2.5px ${c})"` : '');
  return `<svg viewBox="0 0 64 64" aria-hidden="true"><g${g(hc)}><path d="M31 12A18 20 0 0 0 31 52" fill="none" stroke="${hc}" stroke-width="3" stroke-linecap="round"/>
    <ellipse cx="24.5" cy="28" rx="2.2" ry="2.2" fill="${hc}">${RM.matches ? '' : WINK}</ellipse><path d="M24 41q4 3 7 2.6" fill="none" stroke="${hc}" stroke-width="2.4" stroke-linecap="round"/></g>
    <g${g(pc)}>${HERO_PX.map(p => `<rect x="${p.x}" y="${p.y}" width="4.2" height="4.2" rx="1" fill="${pc}" opacity="${p.k ? 1 : 0.62}"/>`).join('')}</g></svg>`;
}
function heroSplitSvg() {
  return `<svg id="hf-split" viewBox="0 0 64 64" aria-hidden="true"><g id="hs-h" style="filter:drop-shadow(0 0 2.5px #63d493)">
    <path id="hs-arc" d="M31 12A18 20 0 0 0 31 52" fill="none" stroke="#63d493" stroke-width="3" stroke-linecap="round" pathLength="100"/>
    <ellipse id="hs-eye" cx="24.5" cy="28" rx="2.2" ry="2.2" fill="#63d493">${RM.matches ? '' : WINK}</ellipse>
    <path id="hs-mouth" d="M24 41q4 3 7 2.6" fill="none" stroke="#63d493" stroke-width="2.4" stroke-linecap="round" pathLength="100"/>
    ${HERO_ARC.map(a => `<circle class="hs-dot" cx="${a.x.toFixed(2)}" cy="${a.y.toFixed(2)}" r="1.5" fill="#63d493" opacity="0"/>`).join('')}
    ${HERO_SMILE.map(a => `<circle class="hs-sdot" cx="${a.x}" cy="${a.y}" r="1.2" fill="#63d493" opacity="0"/>`).join('')}</g>
    <g style="filter:drop-shadow(0 0 2.5px #ff8279)">${HERO_PX.map(p => `<rect class="hs-px" x="${p.x}" y="${p.y}" width="4.2" height="4.2" rx="1" fill="#ff8279" opacity="${p.k ? 1 : 0.62}"/>`).join('')}</g></svg>`;
}
function heroMarkup() {
  const st = S.stats || {};
  return `
    <section class="ln-hero2" id="ln-hero">
      <div class="hero-pin">
        <div class="hero-stage">
          <div class="hero-frame ln-fade" id="hero-frame" style="animation-fill-mode:backwards"><svg viewBox="0 0 170 160" preserveAspectRatio="none" aria-hidden="true"><g fill="none" stroke="#eef1f4" stroke-width="2.4" stroke-linecap="round" opacity=".8"><path d="M1 22V1h21M148 1h21v21M169 138v21h-21M22 159H1v-21"/></g></svg></div>
          <div class="hero-face" role="img" aria-label="The Clipcheck mark being scanned: half a human face, half built from pixels">
            <div class="hf" id="hf-grey">${heroFace('#8e98a2', '#8e98a2')}</div>
            <div class="hf hf-win" id="hf-col"><div class="hf-inner" id="hf-coli">${heroFace('#63d493', '#ff8279', true)}</div></div>
            <span class="hf-line" id="hf-line"></span>
            ${heroSplitSvg()}
          </div>
          <h1 class="sr-only">Made by a person, or made by a machine?</h1>
          <div class="hero-w hero-wl ln-fade" id="hw-l" style="animation-delay:.5s" aria-hidden="true"><span class="hw-base">Made by <br>a person,</span><span class="hw-ink"><span class="hw-inner"><span>Made by</span> <br><span class="tone-genuine">a person,</span></span></span></div>
          <div class="hero-w hero-wr ln-fade" id="hw-r" style="animation-delay:.75s" aria-hidden="true"><span class="hw-base">or by a <br>machine?</span><span class="hw-ink"><span class="hw-inner"><span>or by a</span> <br><span class="tone-manip">machine?</span></span></span></div>
          <p class="hero-tag" id="hero-tag">Clipcheck shows you where the face and the voice part ways.</p>
        </div>
        <div class="hero-under" id="hero-under">
          <p class="ln-lede ln-fade" style="animation-delay:1s">Clipcheck looks at the face and listens to the voice, separately, then tells you which part looks changed.</p>
          <div class="ln-ctas ln-fade" style="animation-delay:1.15s"><a class="btn btn-primary btn-lg" href="#/check"><span>Try it for yourself</span></a><button type="button" class="btn btn-lg" data-go="ln-how">See how it works</button></div>
          <div class="ln-facts ln-fade" style="animation-delay:1.3s"><span>Face and voice checked separately</span><span>Clips stay on your computer</span><span>Likelihoods, not proof</span></div>
        </div>
      </div>
    </section>`;
}
const heroEase = (t) => 1 - Math.pow(1 - t, 3), clamp01 = (v) => Math.min(1, Math.max(0, v));
const narrowHero = matchMedia('(max-width: 700px)');
// Scroll-driven: split the face and move the title halves (0 at the top of the page, 1 when the hero has scrolled through).
function heroFrame() {
  const hero = $('#ln-hero'); if (!hero) return;
  const r = hero.getBoundingClientRect();
  const q = heroEase(clamp01(-r.top / Math.max(1, r.height - innerHeight)));
  S.heroQ = q;
  const a = clamp01(q / 0.45), b = clamp01((q - 0.4) / 0.6), on = q > 0.02;
  const fr = $('#hero-frame');
  fr.style.transform = `translate(-50%,-50%) scale(${(1 + q * 0.35).toFixed(3)})`; fr.style.opacity = (1 - q * 0.9).toFixed(3);
  ['#hf-grey', '#hf-col', '#hf-line'].forEach(sel => { $(sel).style.opacity = on ? 0 : 1; });
  $('#hf-split').style.opacity = on ? 1 : 0;
  $('#hs-h').setAttribute('transform', `translate(${(-q * 20).toFixed(2)} 0) rotate(${(-a * 12).toFixed(1)} 31 32)`);
  $('#hs-mouth').setAttribute('d', `M${(24 - a * 2).toFixed(2)} ${(41 - a * 1.2).toFixed(2)}q${(4 + a * 2).toFixed(2)} ${(3 + a * 3).toFixed(2)} ${(7 + a * 2.4).toFixed(2)} ${(2.6 - a * 0.8).toFixed(2)}`);
  // Nothing fades: the outline is cut back from the top and each cut piece becomes a dot that flies off from where it was.
  const peel = (el, cut) => { el.style.strokeDasharray = `${Math.max(0, 100 - cut).toFixed(2)} ${(cut + 1).toFixed(2)}`; el.style.strokeDashoffset = (-cut).toFixed(2); el.setAttribute('opacity', cut >= 99.5 ? 0 : 1); };
  const arcCut = clamp01(b / 0.7), n = HERO_ARC.length;
  peel($('#hs-arc'), arcCut * 100);
  $$('.hs-dot').forEach((d, i) => {
    const p = HERO_ARC[i], start = (i / (n - 1)) * 0.7, l = heroEase(clamp01((b - start) / 0.3)), off = b <= start;
    d.setAttribute('cx', (p.x + p.dx * l).toFixed(2)); d.setAttribute('cy', (p.y + p.dy * l).toFixed(2)); d.setAttribute('opacity', off ? 0 : 1);
  });
  const smileCut = clamp01((b - 0.45) / 0.3);
  peel($('#hs-mouth'), smileCut * 100);
  $$('.hs-sdot').forEach((d, i) => {
    const p = HERO_SMILE[i], start = 0.45 + i * 0.1, l = heroEase(clamp01((b - start) / 0.3));
    d.setAttribute('cx', (p.x + p.dx * l).toFixed(2)); d.setAttribute('cy', (p.y + p.dy * l).toFixed(2)); d.setAttribute('opacity', b <= start ? 0 : 1);
  });
  const el = heroEase(clamp01((b - 0.25) / 0.45)), eye = $('#hs-eye');   // the eye lets go as a dot of its own
  eye.setAttribute('cx', (24.5 - el * 22).toFixed(2)); eye.setAttribute('cy', (28 - el * 9).toFixed(2));
  $$('.hs-px').forEach((el, i) => { const p = HERO_PX[i]; const x = p.x + q * 20 + p.dx * b * 0.8, y = p.y + p.dy * b * 0.8;
    el.setAttribute('x', x.toFixed(2)); el.setAttribute('y', y.toFixed(2)); el.setAttribute('transform', `rotate(${(p.r * b).toFixed(1)} ${(x + 2).toFixed(2)} ${(y + 2).toFixed(2)})`); });
  const wl = $('#hw-l'), wr = $('#hw-r');
  if (narrowHero.matches) { wl.style.transform = `translateY(${(-q * 30).toFixed(1)}px)`; wr.style.transform = `translateY(${(q * 30).toFixed(1)}px)`; }
  else { wl.style.transform = `translateY(-50%) translateX(${(-q * 150).toFixed(1)}px)`; wr.style.transform = `translateY(-50%) translateX(${(q * 150).toFixed(1)}px)`; }
  $('#hero-tag').style.opacity = clamp01((q - 0.5) / 0.4).toFixed(2);
  $('#hero-under').style.opacity = (1 - clamp01((q - 0.15) / 0.35)).toFixed(2);
}
// Time-driven: the scan line sweeps down and back up (3.6 s each way); above it the face and the title show their real colours.
function heroScan(t) {
  const face = $('.hero-face'), line = $('#hf-line'); if (!face || !line) return;
  const full = RM.matches || (S.heroQ || 0) > 0.02;
  let e = 1;
  if (!RM.matches) { const u = (t / 3600) % 2, tri = u <= 1 ? u : 2 - u; e = (1 - Math.cos(Math.PI * tri)) / 2; }
  // Reads first, then only transforms and opacity are written: nothing here makes the browser lay out or repaint the page.
  const fr = face.getBoundingClientRect(), H = fr.height, lineY = fr.top + e * H;
  const words = $$('.hw-ink').map(ink => ({ ink, r: ink.parentElement.getBoundingClientRect() }));
  const slide = (win, inner, shown, h) => { const d = (shown - 1) * h; win.style.transform = `translate3d(0,${d.toFixed(1)}px,0)`; inner.style.transform = `translate3d(0,${(-d).toFixed(1)}px,0)`; };
  line.style.transform = `translate3d(0,${(e * H).toFixed(1)}px,0)`; line.style.opacity = full ? 0 : 1;
  slide($('#hf-col'), $('#hf-coli'), full ? 1 : e, H);
  words.forEach(({ ink, r }) => slide(ink, ink.firstElementChild, full || narrowHero.matches ? 1 : clamp01((lineY - r.top) / r.height), r.height));
}
// The backdrop on every page: a faint grey pixel grid where random pixels switch on in a random shade of green or red, glow, and
// switch off again; a light that follows the pointer (green on the left, the human side, to red on the right, the machine side);
// and two faint drifting lights in the same colours (those are CSS).
S.fx = 0;   // reveals in progress; the pixel field holds still while any is playing, so the glass above it is not re-blurred
const BG = { x: innerWidth / 2, y: innerHeight * 0.4, gx: innerWidth / 2, gy: innerHeight * 0.4, px: null, raf: null, last: 0 };
const LIGHTS = [[99, 212, 147], [255, 130, 121]];
const ptrColor = (f) => { const a = LIGHTS[0], b = LIGHTS[1], t = clamp01(f); return a.map((v, i) => Math.round(v + (b[i] - v) * t)); };
addEventListener('pointermove', e => { BG.x = e.clientX; BG.y = e.clientY; }, { passive: true });
function newLight(P, t, still) {
  const base = LIGHTS[Math.random() < 0.5 ? 0 : 1], f = 0.5 + Math.random() * 0.5;
  return { i: Math.floor(Math.random() * P.n), c: base.map(v => Math.round(v * f)), t0: t, dur: still ? Infinity : 900 + Math.random() * 2600, peak: 0.4 + Math.random() * 0.45 };
}
function sizePix() {
  const c = $('#ln-pix'); if (!c) return;
  c.width = innerWidth; c.height = innerHeight;
  const s = 22, cols = Math.ceil(innerWidth / s), rows = Math.ceil(innerHeight / s);
  const base = document.createElement('canvas'); base.width = c.width; base.height = c.height;   // the grey grid, drawn once
  const bx = base.getContext('2d'); bx.fillStyle = 'rgba(238,241,244,0.04)';
  for (let y = 0; y < rows; y++) for (let x = 0; x < cols; x++) bx.fillRect(x * s + 5, y * s + 5, s - 10, s - 10);
  BG.px = { s, cols, rows, n: cols * rows, base, lights: [] };
  if (RM.matches) for (let k = 0; k < BG.px.n * 0.05; k++) BG.px.lights.push(newLight(BG.px, 0, true));
}
addEventListener('resize', () => { sizePix(); if (RM.matches) drawPix(0); });
function drawPix(t) {
  const c = $('#ln-pix'), P = BG.px; if (!c || !P) return;
  const x = c.getContext('2d'), s = P.s;
  x.clearRect(0, 0, c.width, c.height);
  x.drawImage(P.base, 0, 0);
  if (!RM.matches) {   // about 0.07% of the grid switches on each frame; each light lasts 0.9 to 3.5 s
    const want = P.n * 0.0007; let k = Math.floor(want) + (Math.random() < want % 1 ? 1 : 0);
    while (k--) P.lights.push(newLight(P, t));
    P.lights = P.lights.filter(L => t - L.t0 < L.dur);
  }
  P.lights.forEach(L => {
    const u = L.dur === Infinity ? 0.5 : (t - L.t0) / L.dur;
    const env = u < 0.1 ? u / 0.1 : u > 0.72 ? (1 - u) / 0.28 : 1;   // quick on, hold, fade off
    x.fillStyle = `rgba(${L.c[0]},${L.c[1]},${L.c[2]},${(L.peak * env).toFixed(3)})`;
    x.fillRect((L.i % P.cols) * s + 5, Math.floor(L.i / P.cols) * s + 5, s - 10, s - 10);
  });
  const mix = ptrColor(BG.gx / innerWidth), R = 180;   // pixels near the pointer light up in its colour
  const c0 = Math.max(0, Math.floor((BG.gx - R) / s)), c1 = Math.min(P.cols - 1, Math.ceil((BG.gx + R) / s));
  const r0 = Math.max(0, Math.floor((BG.gy - R) / s)), r1 = Math.min(P.rows - 1, Math.ceil((BG.gy + R) / s));
  for (let yy = r0; yy <= r1; yy++) for (let xx = c0; xx <= c1; xx++) {
    const near = 1 - Math.hypot(xx * s - BG.gx, yy * s - BG.gy) / R; if (near <= 0) continue;
    x.fillStyle = `rgba(${mix[0]},${mix[1]},${mix[2]},${(near * 0.22).toFixed(3)})`;
    x.fillRect(xx * s + 5, yy * s + 5, s - 10, s - 10);
  }
}
function movePtr() {
  BG.gx += (BG.x - BG.gx) * 0.12; BG.gy += (BG.y - BG.gy) * 0.12;
  const g = $('#ln-ptr-g'), r = $('#ln-ptr-r'); if (!g || !r) return;
  const pos = `translate3d(${(BG.gx - 280).toFixed(1)}px,${(BG.gy - 280).toFixed(1)}px,0)`, f = clamp01(BG.gx / innerWidth);
  g.style.transform = r.style.transform = pos; g.style.opacity = (0.1 * (1 - f)).toFixed(3); r.style.opacity = (0.1 * f).toFixed(3);
}
// Started once for the whole app; the hero's scan runs in the same loop while the landing page is showing.
function startBackdrop() {
  if (BG.started) return;
  BG.started = true;
  $('.wall').insertAdjacentHTML('beforeend', '<div class="ln-bg"><canvas class="ln-pix" id="ln-pix"></canvas><span class="ln-ptr" id="ln-ptr-g"></span><span class="ln-ptr" id="ln-ptr-r"></span></div>');
  sizePix();
  if (RM.matches) { drawPix(0); return; }
  const loop = (t) => {
    if (S.view === 'welcome') heroScan(t);
    if (t - BG.last > 50) { BG.last = t; movePtr(); if (!S.fx) drawPix(t); }
    BG.raf = requestAnimationFrame(loop);
  };
  BG.raf = requestAnimationFrame(loop);
}
function startLanding() { startBackdrop(); if (RM.matches) heroScan(0); }

function hoodSvg() {
  const T = S.fusion ? points(S.fusion.threshold_T) : 35;
  const N = [['MTCNN', 'finds the faces', 20, 40], [videoModelName(), 'scores each face', 235, 40],
             ['Silero VAD', 'finds the speech', 20, 170], ['wav2vec2', 'turns speech into numbers', 235, 170], ['SVM', 'scores the voice', 450, 170],
             ['Compare', `gap against the ${T}-point line`, 680, 105], ['Llama 3 8B', 'writes the explanation', 900, 105]];
  const P = [['M210 71H235', 'pic'], ['M425 71C560 71 560 136 680 136', 'pic'], ['M210 201H235', 'voi'], ['M425 201H450', 'voi'],
             ['M640 201C662 201 660 136 680 136', 'voi'], ['M870 136H900', 'both']];
  return `<svg viewBox="0 0 1110 250" role="img" aria-label="How the six models connect: picture and voice checked separately, then compared, then explained">
    <text class="lane" x="20" y="28">Picture</text><text class="lane" x="20" y="158">Voice</text><text class="lane" x="680" y="93">Both</text>
    ${P.map(([d]) => `<path class="flow" d="${d}"/>`).join('')}${P.map(([d, c]) => `<path class="pulse ${c}" d="${d}"/>`).join('')}
    ${N.map(([t, sub, x, y]) => `<g class="node"><rect x="${x}" y="${y}" width="190" height="62" rx="14"/><text class="t" x="${x + 14}" y="${y + 26}">${esc(t)}</text><text class="s" x="${x + 14}" y="${y + 46}">${esc(sub)}</text></g>`).join('')}
  </svg>
  <ol class="hood-list">${N.map(([t, sub]) => `<li><b>${esc(t)}</b> ${esc(sub)}</li>`).join('')}</ol>`;
}
const LIMIT_TITLES = { coverage: 'Three face methods, not all', accuracy: 'Right most of the time, not always', other_datasets: 'Weaker on other footage',
  audio_corpus: 'One voice corpus', wrong_modality_out_of_distribution: 'It can name the wrong part', audio_speech_only: 'The voice needs speech',
  scope: 'No live scanning', threshold: 'A tuned line' };
function renderWelcome() {
  const st = S.stats || {}, F = S.fusion || {}, T = F.threshold_T != null ? points(F.threshold_T) : null;
  const V = WORKED.voice, Fc = WORKED.face;
  const dv = describe(fuse(V.pv, V.pa)), df = describe(fuse(Fc.pv, Fc.pa));
  const gapV = points(Math.abs(V.pv - V.pa)), gapF = points(Math.abs(Fc.pv - Fc.pa));
  const faceDemo = demoByCode(Fc.code);
  const limits = S.limitations ? S.limitations.limitations.filter(l => LIMIT_TITLES[l.id]).slice(0, 6) : [];
  const x1 = Math.min(V.pv, V.pa) * 100, x2 = Math.max(V.pv, V.pa) * 100, t = (F.threshold_T || 0) * 100;
  stage.innerHTML = `
  <div class="ln">
    <header class="ln-head glass">
      <a class="brand" href="#/welcome" aria-label="Clipcheck home">${BRAND}<span class="brand-name">Clipcheck</span></a>
      <nav class="ln-links" aria-label="On this page">
        <button type="button" data-go="ln-how">How it works</button><button type="button" data-go="ln-why">Why it matters</button>
        <button type="button" data-go="ln-hood">Under the hood</button><button type="button" data-go="ln-limits">Limits</button></nav>
      <a class="btn btn-primary" href="#/check"><span>Open Clipcheck</span></a>
    </header>

${heroMarkup()}

    <section class="ln-sec" id="ln-how" aria-labelledby="how-h">
      <div class="ln-sh px"><h2 class="ln-h2" id="how-h">One clip, two separate checks.</h2><p class="ln-p">Scroll to watch a real check of one of the demo videos unfold.</p></div>
      <div class="ln-story ${RM.matches ? 'static' : ''}" id="ln-story">
        <div class="story-pin">
          <div>
            <div class="story-num" aria-hidden="true"><i></i><i></i><i></i><i></i></div>
            <div class="story-steps">
              <div class="story-step"><h3>It checks the face.</h3><p>Faces are found in sampled frames, and each one is scored for signs of manipulation. Here: ${pct(V.pv)}, so the face leans genuine.</p></div>
              <div class="story-step"><h3>It listens to the voice.</h3><p>When there is speech, a separate model scores how synthetic it sounds. Here: ${pct(V.pa)}.</p></div>
              <div class="story-step"><h3>It compares the two.</h3><p>${gapV} points apart${T != null ? `, past the ${T}-point line` : ''}. A gap that big is a finding, not noise.</p></div>
              <div class="story-step"><h3>It names the part.</h3><p>Instead of averaging the two into one number, it says which part looks changed: ${dv.headline.includes('voice') ? 'the voice' : 'the picture'}.</p></div>
            </div>
          </div>
          <div class="story-win glass">
            <div class="sw-name">Webcam streamer, voice replaced</div>
            <div class="sw-known">A real check of a demo video. Known answer: face real, voice fake.</div>
            <div class="cc">
              <div class="cc-grid"><div class="cc-scale" aria-hidden="true"><span>0%</span><span>50%: unsure</span><span>100%</span></div><div></div></div>
              <div class="cc-row"><div class="head">${icon('face')} Picture<span class="lean" id="sw-pl"></span></div><div class="cc-grid">${meterMarkup('sw-pic')}<div class="cap-val" id="sw-pv"></div></div></div>
              <div class="cc-row"><div class="head">${icon('voice')} Voice<span class="lean" id="sw-al"></span></div><div class="cc-grid">${meterMarkup('sw-voi')}<div class="cap-val" id="sw-av"></div></div></div>
              <div class="cc-grid"><div class="cc-gap" aria-hidden="true">
                <span class="bracket" id="sw-br" style="left:${x1}%;width:0"></span><span class="b-label" id="sw-bl" style="left:${(x1 + x2) / 2}%;transform:translateX(-50%);opacity:0">${gapV} points apart</span>
                <span class="ruler" id="sw-ru" style="left:${x1}%;width:0"></span><span class="r-label" id="sw-rl" style="left:calc(${x1 + t}% + 8px);opacity:0">${T != null ? `${T}-point line` : ''}</span>
              </div><div></div></div>
            </div>
            <div class="sw-verdict tone-${dv.tone}" id="sw-verdict">${icon(dv.icon)} ${esc(dv.headline)}</div>
          </div>
        </div>
      </div>
    </section>

    <section class="ln-sec" id="ln-why" aria-labelledby="why-h">
      <div class="ln-sh px"><h2 class="ln-h2" id="why-h">When the face and the voice disagree, the disagreement is the answer.</h2>
        <p class="ln-p">Move the two scores. ${T != null ? `Under ${T} points apart, the tool combines them; at ${T} or more, it names the part that looks changed.` : ''} This is the same rule the app uses.</p></div>
      <div class="play">
        <div class="play-in glass px">
          <div class="slider"><label for="pl-v">${icon('face')} <span class="grow">Picture score</span><span class="tnum" id="pl-vo"></span></label><input type="range" id="pl-v" min="0" max="100" step="1" value="${Math.round(V.pv * 100)}">${meterMarkup('pl-m1')}</div>
          <div class="slider"><label for="pl-a">${icon('voice')} <span class="grow">Voice score</span><span class="tnum" id="pl-ao"></span></label><input type="range" id="pl-a" min="0" max="100" step="1" value="${Math.round(V.pa * 100)}">${meterMarkup('pl-m2')}</div>
          <p class="note">Starts at the webcam streamer's real scores.</p>
        </div>
        <div class="play-out glass px" aria-live="polite">
          <div class="play-verdict" id="pl-verdict"></div>
          <p class="play-why" id="pl-why"></p>
          <p class="play-avg" id="pl-avg"></p>
        </div>
      </div>
    </section>

    <section class="ln-sec" id="ln-e2e" aria-labelledby="e2e-h">
      <div class="ln-sh px"><h2 class="ln-h2" id="e2e-h">One clip, start to finish.</h2><p class="ln-p">Every step of a real check on one demo video, including the moment the tool caught its own AI model getting it wrong.</p></div>
      <div class="e2e">
        <div class="e2e-row"><span class="e2e-dot">${icon('upload')}</span><div class="e2e-card glass px"><h4>The clip</h4><div class="big">Business newsreader</div><p>A financial news desk. Known answer: the face was replaced; the voice is real.</p></div></div>
        <div class="e2e-row"><span class="e2e-dot tone-manip">${icon('face')}</span><div class="e2e-card glass px"><h4>Picture check</h4><div class="big tone-manip">${pct(Fc.pv)}</div><p>chance the face is manipulated, across ${Fc.faces} face frames; most suspicious from ${fmtTime(Fc.from)} to ${fmtTime(Fc.to)}.</p></div></div>
        <div class="e2e-row"><span class="e2e-dot tone-genuine">${icon('voice')}</span><div class="e2e-card glass px"><h4>Voice check</h4><div class="big tone-genuine">${pct(Fc.pa)}</div><p>chance the voice is synthetic, from ${Fc.speech.toFixed(1)} s of speech in ${Fc.sound.toFixed(1)} s of sound.</p></div></div>
        <div class="e2e-row"><span class="e2e-dot tone-partial">${icon('merge')}</span><div class="e2e-card glass px"><h4>Compared</h4><div class="big tone-${df.tone}">${esc(df.headline)}</div><p>${gapF} points apart${T != null ? `, well past the ${T}-point line` : ''}, so the tool does not average them.</p></div></div>
        <div class="e2e-row"><span class="e2e-dot">${icon('pen')}</span><div class="e2e-card glass px"><h4>Explained</h4><div class="big">A mistake, caught</div><p>Llama 3 wrote a summary saying both parts were manipulated. The automatic check saw that the results say the voice leans genuine, so the tool showed its standard wording instead.</p></div></div>
      </div>
      <div class="e2e-foot"><p class="note">From a real check on 26 September 2026. Run it again to see today's numbers.</p>${faceDemo ? `<button type="button" class="btn btn-primary" id="run-face"><span>Run this check yourself</span></button>` : ''}</div>
    </section>

    <section class="ln-sec" id="ln-hood" aria-labelledby="hood-h">
      <div class="ln-sh px"><h2 class="ln-h2" id="hood-h">Six models, one answer.</h2><p class="ln-p">Two models for the picture, three for the voice, and a language model that writes it up in plain words, checked against the results before you see it.</p></div>
      <div class="hood glass px">${hoodSvg()}</div>
    </section>

    <section class="ln-sec" id="ln-who" aria-labelledby="who-h">
      <div class="ln-sh px"><h2 class="ln-h2" id="who-h">For anyone about to press share.</h2></div>
      <div class="ln-cards">
        <div class="ln-card glass px">${icon('link')}<h3>Before you share a clip</h3><p>A second opinion on a video before you forward it. If one part looks changed, it tells you which one.</p></div>
        <div class="ln-card glass px">${icon('details')}<h3>Newsrooms and fact-checkers</h3><p>A first pass that says when, not what: the moments worth a second look, and how sure the tool is.</p></div>
        <div class="ln-card glass px">${icon('scale')}<h3>Classrooms</h3><p>A way to show that a deepfake can fake one part of a clip and leave the other real.</p></div>
      </div>
    </section>

    <section class="ln-sec" id="ln-research" aria-labelledby="res-h">
      <div class="ln-sh px"><h2 class="ln-h2" id="res-h">The research behind it.</h2></div>
      <div class="research glass px">
        <div><p class="q">Does checking the face and the voice separately, and saying when they disagree, catch fakes that one combined score misses?</p>
          <p class="credit">Clipcheck is a CM3070 final-year project (BSc Computer Science, University of London).${st.adv ? ` Its answer, on ${st.adv.n} built test clips of people the tool had not seen:` : ''}</p></div>
        <div>${st.four && st.four.every(x => x[1] != null) ? `<div class="bars">${st.four.map(([l, v], k) => `<div class="bar-row ${k === 3 ? 'best' : ''}"><span>${esc(l)}</span><span class="bar-track"><span style="--w:${v}%"></span></span><span class="val">${v}%</span></div>`).join('')}</div>
          ${st.adv ? `<p class="note" style="margin-top:12px">${st.adv.d} points better than averaging (95% range ${st.adv.lo} to ${st.adv.hi}).</p>` : ''}` : '<p class="note">The results could not be loaded.</p>'}
          <p style="margin-top:16px"><a class="btn" href="#/accuracy">See every figure</a></p></div>
      </div>
    </section>

    <section class="ln-sec" id="ln-limits" aria-labelledby="lim-h">
      <div class="ln-sh px"><h2 class="ln-h2" id="lim-h">What it can't do.</h2><p class="ln-p">These are the limits measured in testing.</p></div>
      <div class="ln-cards">${limits.map(l => `<div class="ln-card glass px">${icon('alert')}<h3>${esc(l.id === 'accuracy' && st.acc != null ? `Right about ${Math.round(st.acc)} in 100` : LIMIT_TITLES[l.id])}</h3><p>${esc(l.text)}</p></div>`).join('')}</div>
    </section>

    <section class="ln-close px" id="ln-try">
      <p class="ln-p">Upload your own clip, or pick one of the demo videos with known answers.</p>
      <a class="btn btn-primary btn-lg" href="#/check"><span>Try it for yourself</span></a>
    </section>
  </div>`;
  $$('[data-go]').forEach(b => b.addEventListener('click', () => { const el = $(`#${b.dataset.go}`); if (el) el.scrollIntoView({ behavior: RM.matches ? 'auto' : 'smooth', block: 'start' }); }));
  const run = $('#run-face'); if (run) run.onclick = () => startDemo(faceDemo.demo_id, run);
  ['pl-v', 'pl-a'].forEach(id => $(`#${id}`).addEventListener('input', drawPlay));
  drawPlay();
  startLanding();
  setupPixelReveals();
  landingFrame();
}
function drawPlay() {
  const pv = +$('#pl-v').value / 100, pa = +$('#pl-a').value / 100;
  const d = describe(fuse(pv, pa));
  $('#pl-vo').textContent = pct(pv); $('#pl-ao').textContent = pct(pa);
  setMeter($('#pl-m1'), pv); setMeter($('#pl-m2'), pa);
  const v = $('#pl-verdict'); v.textContent = d.headline; v.className = `play-verdict tone-${d.tone}`;
  $('#pl-why').innerHTML = d.gap || d.reason;
  const avg = (pv + pa) / 2;
  $('#pl-avg').textContent = `Averaging the two would give ${pct(avg)}: "${avg >= 0.5 ? 'likely manipulated' : 'likely genuine'}", with nothing about which part.`;
}
// Scroll-driven parts: the hero pixels drift apart as the page leaves the hero, and the pinned story plays the real check.
let lnRaf = null;
function onLandingScroll() {
  revealCheck();
  if (S.view !== 'welcome' || lnRaf) return;
  lnRaf = requestAnimationFrame(() => { lnRaf = null; landingFrame(); });
}
addEventListener('scroll', onLandingScroll, { passive: true });
addEventListener('resize', onLandingScroll);
function landingFrame() {
  if (S.view !== 'welcome') return;
  heroFrame();
  const story = $('#ln-story'); if (!story) return;
  const V = WORKED.voice, F = S.fusion || {};
  let p = 1;
  if (!story.classList.contains('static')) { const r = story.getBoundingClientRect(); p = Math.min(1, Math.max(0, -r.top / Math.max(1, r.height - innerHeight))); }
  const seg = (a, b) => Math.min(1, Math.max(0, (p - a) / (b - a)));
  const step = p < 0.25 ? 0 : p < 0.5 ? 1 : p < 0.75 ? 2 : 3;
  $$('.story-step', story).forEach((el, i) => el.classList.toggle('on', i === step));
  $$('.story-num i', story).forEach((el, i) => el.classList.toggle('on', i <= step));
  const a = seg(0.04, 0.2), b = seg(0.29, 0.45), g = seg(0.54, 0.7);
  setMeter($('#sw-pic'), V.pv * a); $('#sw-pv').textContent = a >= 1 ? pct(V.pv) : ''; $('#sw-pl').textContent = a >= 1 ? lean(V.pv) : '';
  setMeter($('#sw-voi'), V.pa * b); $('#sw-av').textContent = b >= 1 ? pct(V.pa) : ''; $('#sw-al').textContent = b >= 1 ? lean(V.pa) : '';
  $('#sw-br').style.width = `${(Math.abs(V.pa - V.pv) * 100 * g).toFixed(1)}%`;
  $('#sw-ru').style.width = `${((F.threshold_T || 0) * 100 * g).toFixed(1)}%`;
  $('#sw-bl').style.opacity = g >= 1 ? 1 : 0; $('#sw-rl').style.opacity = g >= 1 ? 1 : 0;
  $('#sw-br').style.opacity = g > 0 ? 1 : 0; $('#sw-ru').style.opacity = g > 0 ? 1 : 0;
  $('#sw-verdict').classList.toggle('on', p >= 0.78);
}
// Scroll reveals, each tied to what Clipcheck does, mixed across the page (chosen 27 Sep): headings DECODE from scrambled
// machine characters into the real words; the playground, the research panel and the audience cards assemble from green and red BLOCKS;
// the clip walkthrough is SCANNED in; the model chain is traced by a FACE-SCAN MESH; the limits alternate decode and blocks.
// Checked on every scroll event and by a timer backstop, so a section can never be left hidden.
const REVEALS = [['.ln-sh', 'decode'], ['.play-in, .play-out', 'pixel'], ['.e2e-card', 'scan'], ['.research', 'pixel'],
                 ['.hood', 'mesh'], ['#ln-who .ln-card', 'pixel'], ['#ln-limits .ln-card', 'decode|pixel'], ['.ln-close', 'decode']];
function setupPixelReveals() {
  if (RM.matches) return;
  REVEALS.forEach(([sel, kind]) => $$(`.ln ${sel}`).forEach((el, i) => { const k = kind.split('|'); el.dataset.reveal = k[i % k.length]; el.classList.add('px', 'px-wait'); }));
  setTimeout(revealCheck, 60);
  clearInterval(S.pxTimer);
  S.pxTimer = setInterval(() => { if (S.view !== 'welcome' || !$('.ln .px.px-wait')) { clearInterval(S.pxTimer); return; } revealCheck(); }, 400);
}
function revealCheck() {
  if (S.view !== 'welcome') return;
  const vh = innerHeight;
  $$('.ln .px.px-wait').forEach(el => {
    if (el.dataset.revealing) return;
    const r = el.getBoundingClientRect();
    if (r.top < vh * 0.88 && r.bottom > 0) { el.dataset.revealing = '1'; ({ decode: decodeReveal, scan: scanReveal, mesh: meshReveal, pixel: pixelReveal }[el.dataset.reveal] || scanReveal)(el); }
  });
}
// Decode: every character starts as a random machine glyph (green or red) and resolves into the real text, left to right.
const GLYPHS = '@#$%&*<>/\\|=+?![]{}01';
function decodeReveal(el) {
  const nodes = [], walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT, { acceptNode: n => (n.nodeValue.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT) });
  while (walker.nextNode()) nodes.push(walker.currentNode);
  const total = Math.max(1, nodes.reduce((sum, n) => sum + n.nodeValue.length, 0));
  let offset = 0;
  const items = nodes.map(n => {
    const w = document.createElement('span'), done = document.createElement('span'), todo = document.createElement('span');
    todo.className = 'dec-todo'; w.append(done, todo); n.parentNode.replaceChild(w, n);
    const it = { n, w, done, todo, s: n.nodeValue, o: offset }; offset += n.nodeValue.length; return it;
  });
  const scramble = (str) => str.replace(/\S/g, () => GLYPHS[Math.floor(Math.random() * GLYPHS.length)]);
  const d = Math.min(1500, 650 + total * 2.5), start = performance.now();
  let last = -1e9, over = false;
  const finish = () => { if (over) return; over = true; items.forEach(it => it.w.replaceWith(it.n)); S.fx--; };
  const paint = (now) => {
    const u = Math.min(1, (now - start) / d);
    items.forEach(it => {
      const k = Math.max(0, Math.min(it.s.length, Math.ceil(((u - 0.15) / 0.8) * total - it.o)));
      it.done.textContent = it.s.slice(0, k); it.todo.textContent = scramble(it.s.slice(k));
    });
    return u;
  };
  const frame = (now) => { if (over) return; if (now - last > 45) { last = now; if (paint(now) >= 1) { finish(); return; } } requestAnimationFrame(frame); };
  S.fx++; paint(start); el.classList.remove('px-wait');
  requestAnimationFrame(frame); setTimeout(finish, d + 900);   // the timer is a backstop if frames are paused
}
// Scan pass: a green line sweeps down the box; above it the box is sharp, below it still faint.
function scanReveal(el) {
  const veil = document.createElement('span'); veil.className = 'scan-veil'; veil.setAttribute('aria-hidden', 'true');
  veil.innerHTML = '<span class="scan-cover"></span>';
  el.appendChild(veil); el.classList.remove('px-wait'); S.fx++;
  let over = false;
  const finish = () => { if (over) return; over = true; veil.remove(); S.fx--; };
  veil.firstChild.animate([{ transform: 'translate3d(0,0,0)' }, { transform: 'translate3d(0,101%,0)' }],
    { duration: 1150, easing: 'cubic-bezier(.22,.8,.24,1)', fill: 'forwards' }).onfinish = finish;
  setTimeout(finish, 2200);
}
// Blocks: the box assembles from a jumble of green and red blocks that fly into place, turn to glass, then give way to the content.
function pixelReveal(el) {
  const w = el.offsetWidth, h = el.offsetHeight;
  if (!w || !h) { el.classList.remove('px-wait'); return; }
  const size = Math.max(18, Math.sqrt(w * h / 140), Math.min(40, Math.sqrt(w * h / 110)));
  const cols = Math.max(1, Math.round(w / size)), rows = Math.max(1, Math.round(h / size)), cw = w / cols, ch = h / rows;
  const tones = ['99,212,147', '72,176,118', '140,228,176', '255,130,121', '222,94,88', '255,168,158'];
  const layer = document.createElement('div'); layer.className = 'px-layer'; layer.setAttribute('aria-hidden', 'true');
  let html = '';
  for (let y = 0; y < rows; y++) for (let x = 0; x < cols; x++)
    html += `<i style="background:rgb(${tones[Math.floor(Math.random() * tones.length)]});left:${(x * cw).toFixed(1)}px;top:${(y * ch).toFixed(1)}px;width:${(cw - 3).toFixed(1)}px;height:${(ch - 3).toFixed(1)}px"></i>`;
  layer.innerHTML = html; el.appendChild(layer); S.fx++;
  $$('i', layer).forEach((b, k) => {
    const x = k % cols, dx = (Math.random() - 0.5) * 320, dy = (Math.random() - 0.5) * 220 + 80, r = (Math.random() - 0.5) * 200;
    const delay = Math.random() * 350 + (x / cols) * 150;
    b.animate([{ transform: `translate3d(${dx.toFixed(0)}px,${dy.toFixed(0)}px,0) rotate(${r.toFixed(0)}deg)`, opacity: 0 }, { transform: 'translate3d(0,0,0) rotate(0deg)', opacity: 0.9 }],
      { duration: 750, delay, easing: 'cubic-bezier(.34,1.56,.64,1)', fill: 'both' });
    b.animate([{ opacity: 0.9 }, { opacity: 0 }], { duration: 420, delay: 1150 + (k % 7) * 30, easing: 'ease', fill: 'forwards' });
  });
  setTimeout(() => el.classList.remove('px-wait'), 1150);
  setTimeout(() => { layer.remove(); S.fx--; }, 1850);
}
// Face-scan mesh: a green landmark mesh draws itself across the box point by point, then dissolves as the real content settles in.
function meshReveal(el) {
  const W = el.offsetWidth, H = el.offsetHeight;
  if (!W || !H) { el.classList.remove('px-wait'); return; }
  const cols = Math.max(3, Math.round(W / 95)), rows = Math.max(2, Math.round(H / 75)), pts = [];
  for (let y = 0; y <= rows; y++) for (let x = 0; x <= cols; x++) {
    const inner = x > 0 && x < cols && y > 0 && y < rows;
    pts.push([x * W / cols + (inner ? (Math.random() - 0.5) * W / cols * 0.5 : 0), y * H / rows + (inner ? (Math.random() - 0.5) * H / rows * 0.5 : 0)]);
  }
  const at = (x, y) => y * (cols + 1) + x, edges = [];
  for (let y = 0; y <= rows; y++) for (let x = 0; x <= cols; x++) {
    if (x < cols) edges.push([at(x, y), at(x + 1, y)]);
    if (y < rows) edges.push([at(x, y), at(x, y + 1)]);
    if (x < cols && y < rows) edges.push((x + y) % 2 ? [at(x, y), at(x + 1, y + 1)] : [at(x + 1, y), at(x, y + 1)]);
  }
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('class', 'px-layer mesh'); svg.setAttribute('viewBox', `0 0 ${W} ${H}`); svg.setAttribute('aria-hidden', 'true');
  svg.innerHTML = edges.map(([p, q]) => `<line x1="${pts[p][0].toFixed(1)}" y1="${pts[p][1].toFixed(1)}" x2="${pts[q][0].toFixed(1)}" y2="${pts[q][1].toFixed(1)}" pathLength="1" data-x="${Math.min(pts[p][0], pts[q][0]).toFixed(0)}"/>`).join('')
    + pts.map(p => `<circle cx="${p[0].toFixed(1)}" cy="${p[1].toFixed(1)}" r="2.4" data-x="${p[0].toFixed(0)}"/>`).join('');
  el.appendChild(svg); S.fx++;
  const span = 700 / Math.max(1, W);   // the mesh sweeps left to right in about 0.7 s whatever the box's width
  $$('line', svg).forEach(l => l.animate([{ strokeDashoffset: 1 }, { strokeDashoffset: 0 }], { duration: 420, delay: +l.dataset.x * span, easing: 'cubic-bezier(.22,.8,.24,1)', fill: 'both' }));
  $$('circle', svg).forEach(c => c.animate([{ opacity: 0, transform: 'scale(0)' }, { opacity: 1, transform: 'scale(1.7)', offset: 0.5 }, { opacity: 0.9, transform: 'scale(1)' }],
    { duration: 380, delay: +c.dataset.x * span, fill: 'both' }));
  setTimeout(() => el.classList.remove('px-wait'), 950);
  svg.animate([{ opacity: 1 }, { opacity: 1, offset: 0.62 }, { opacity: 0 }], { duration: 1900, fill: 'forwards' });
  setTimeout(() => { svg.remove(); S.fx--; }, 2000);
}

// ── Start ─────────────────────────────────────────────────────────────────
$('#brand-mark').innerHTML = BRAND;
startBackdrop();
(async function init() {
  await loadStatic();
  await refreshQueue();
  render();
})();
