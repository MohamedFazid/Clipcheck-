/* veridex / detection — vanilla JS, no framework. Talks to the FastAPI
 * backend in server.py. Every render function below either uses a real
 * field from the /api/analyze response or renders an explicit "not
 * available" state -- never a fabricated number. */

const state = {
  queue: [],       // [{id, filename, status, verdict, duration}]
  demos: [],       // [{demo_id, name, kind}]
  activeId: null,
  results: {},      // job id -> full result JSON (cached client-side)
  pollTimer: null,  // active /api/progress polling interval, if any
  pollingId: null,  // which job that poll belongs to
};

const el = (id) => document.getElementById(id);
const videoEl = el('video-el');

// ── Nav view switching ────────────────────────────────────────────────────
document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const view = btn.dataset.view;
    ['analyze', 'history', 'evaluation'].forEach(v => {
      el(`view-${v}`).hidden = (v !== view);
    });
    if (view === 'history') renderHistory();
    if (view === 'evaluation') renderEvaluation();
  });
});

// ── Demo clip list: concealed by default, toggled open ────────────────────
el('demo-toggle').addEventListener('click', () => {
  const willShow = el('demo-list').hidden;
  el('demo-list').hidden = !willShow;
  el('demo-toggle').setAttribute('aria-expanded', String(willShow));
});

// ── Model info footer: which pretrained models actually back this app ────
async function loadModelInfo() {
  const info = await (await fetch('/api/model_info')).json();
  el('model-info').innerHTML =
    '<div class="model-info-title">Pretrained models</div>' +
    info.models.map(m => `
      <div class="model-info-row">
        <div class="model-info-stage">${m.stage}</div>
        <div class="model-info-name">${m.name}</div>
        <div class="model-info-status">${m.status}</div>
      </div>`).join('');
}

// ── Demo clip list ────────────────────────────────────────────────────────
async function loadDemoClips() {
  state.demos = await (await fetch('/api/demo_clips')).json();
  el('demo-list').innerHTML = state.demos.map(d => `
    <div class="queue-row" data-demo-id="${d.demo_id}">
      <div class="queue-thumb">&#9654;</div>
      <div class="queue-meta">
        <div class="queue-name" title="${d.name}">${d.name}</div>
        <div class="queue-duration">${d.kind}</div>
      </div>
    </div>`).join('');
  el('demo-list').querySelectorAll('.queue-row').forEach(row => {
    row.addEventListener('click', async () => {
      const demoId = row.dataset.demoId;
      const job = await (await fetch(`/api/demo/${demoId}`, { method: 'POST' })).json();
      await onNewJob(job);
    });
  });
}

// ── Upload ────────────────────────────────────────────────────────────────
const esc = (s) => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

async function loadLimits() {
  try { state.limits = await (await fetch('/api/limits')).json(); } catch (err) { state.limits = null; }
}

function showUploadNotice(message) {
  const n = el('upload-notice');
  n.textContent = message || '';
  n.hidden = !message;
}

el('file-input').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;
  showUploadNotice('');
  const lim = state.limits;
  if (lim && file.size > lim.max_upload_mb * 1024 * 1024) {
    showUploadNotice(`"${file.name}" is ${(file.size / 1048576).toFixed(0)} MB; the limit is ${lim.max_upload_mb} MB.`);
    e.target.value = '';
    return;
  }
  const form = new FormData();
  form.append('file', file);
  try {
    const resp = await fetch('/api/upload', { method: 'POST', body: form });
    const body = await resp.json().catch(() => ({}));
    if (!resp.ok) {
      showUploadNotice(body.detail || `Upload failed (HTTP ${resp.status}).`);
    } else {
      await onNewJob(body);
    }
  } catch (err) {
    showUploadNotice('Upload failed: the server could not be reached.');
  } finally {
    e.target.value = '';
  }
});

async function onNewJob(job) {
  state.queue.push({ id: job.id, filename: job.filename, status: 'pending',
                      verdict: null, duration: job.duration });
  renderQueue();
  selectJob(job.id);
  runAnalysis(job.id);
}

// ── Queue rendering ───────────────────────────────────────────────────────
function renderQueue() {
  el('queue-list').innerHTML = state.queue.map(j => `
    <div class="queue-row ${j.id === state.activeId ? 'active' : ''}" data-id="${j.id}">
      <div class="queue-thumb">&#9654;</div>
      <div class="queue-meta">
        <div class="queue-name" title="${j.filename}">${j.filename}</div>
        <div class="queue-duration">${fmtDuration(j.duration)}</div>
      </div>
      <div class="status-chip ${(j.verdict || 'pending').toLowerCase().replace('_manipulation', '')}">
        ${j.verdict === 'PARTIAL_MANIPULATION' ? 'PARTIAL' : (j.verdict || 'pending')}
      </div>
      <button class="queue-remove" data-remove-id="${j.id}" title="Remove from recents">&times;</button>
    </div>`).join('');
  el('queue-list').querySelectorAll('.queue-row').forEach(row => {
    row.addEventListener('click', () => selectJob(row.dataset.id));
  });
  el('queue-list').querySelectorAll('.queue-remove').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      removeFromQueue(btn.dataset.removeId);
    });
  });
}

async function removeFromQueue(id) {
  if (state.pollingId === id) stopProgressPolling();
  await fetch(`/api/queue/${id}`, { method: 'DELETE' });
  state.queue = state.queue.filter(j => j.id !== id);
  delete state.results[id];
  if (state.activeId === id) {
    state.activeId = null;
    videoEl.removeAttribute('src');
    videoEl.classList.remove('loaded');
    el('empty-state').hidden = false;
    el('verdict-stamp').hidden = true;
    el('timecode-overlay').hidden = true;
    setAnalyzing(false);
    clearAnalysisPanel();
  }
  renderQueue();
}

function fmtDuration(seconds) {
  if (seconds == null) return '--:--';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${String(s).padStart(2, '0')}`;
}

// ── Selecting a job: load video + (cached or fresh) result ───────────────
function selectJob(id) {
  stopProgressPolling();
  state.activeId = id;
  renderQueue();
  videoEl.src = `/api/video/${id}`;
  videoEl.classList.add('loaded');
  el('empty-state').hidden = true;
  el('verdict-stamp').hidden = true;
  el('timecode-overlay').hidden = false;

  const job = state.queue.find(j => j.id === id);
  if (state.results[id]) {
    setAnalyzing(false);
    renderResult(state.results[id]);
  } else if (job && job.status === 'analyzing') {
    // Switched to a job whose analysis is already running elsewhere --
    // resume watching its real progress rather than starting a new one.
    clearAnalysisPanel();
    setAnalyzing(true);
    watchProgress(id);
  } else {
    clearAnalysisPanel();
    // A job can reach here 'pending' if it was uploaded but the page was
    // reloaded before analysis ran (queue rehydration restores the row, but
    // not an in-flight analysis) -- auto-trigger so selecting it isn't a
    // dead end.
    if (job && job.status === 'pending') runAnalysis(id);
    else setAnalyzing(false);
  }
}

// ── Analysis flow ─────────────────────────────────────────────────────────
// The overlay shows genuine pipeline progress (server.py updates job.progress
// at real stage transitions -- including a real per-frame-crop callback
// during the video branch) -- never a simulated/timer-based percentage.
async function runAnalysis(id) {
  const job = state.queue.find(j => j.id === id);
  if (job) { job.status = 'analyzing'; renderQueue(); }
  setAnalyzing(true);
  await fetch(`/api/analyze/${id}`, { method: 'POST' });
  watchProgress(id);
}

function stopProgressPolling() {
  if (state.pollTimer) {
    clearInterval(state.pollTimer);
    state.pollTimer = null;
    state.pollingId = null;
  }
}

function watchProgress(id) {
  stopProgressPolling();
  state.pollingId = id;
  state.pollTimer = setInterval(async () => {
    const p = await (await fetch(`/api/progress/${id}`)).json();
    if (id === state.activeId) {
      el('analyzing-text').textContent = `Analysing ${p.progress}%`;
    }
    if (p.status === 'done' || p.status === 'error') {
      stopProgressPolling();
      const result = await (await fetch(`/api/result/${id}`)).json();
      state.results[id] = result;
      const queueJob = state.queue.find(j => j.id === id);
      if (queueJob) {
        queueJob.status = result.error ? 'error' : 'done';
        queueJob.verdict = result.verdict || null;
        renderQueue();
      }
      if (id === state.activeId) {
        setAnalyzing(false);
        renderResult(result);
      }
    }
  }, 300);
}

function setAnalyzing(on) {
  el('analyzing-backdrop').hidden = !on;
  el('scan-line').hidden = !on;
  el('analyzing-content').hidden = !on;
  if (on) el('analyzing-text').textContent = 'Analysing 0%';
  el('controls').style.pointerEvents = on ? 'none' : '';
  el('controls').style.opacity = on ? '0.4' : '1';
  el('overview-loading').hidden = !on;
  if (on) {
    el('overview-loading').innerHTML =
      '<div class="skeleton-block" style="width:60%"></div>' +
      '<div class="skeleton-block" style="width:90%"></div>' +
      '<div class="skeleton-block" style="width:75%"></div>';
    el('overview-body').style.display = 'none';
  } else {
    el('overview-body').style.display = '';
  }
}

function clearAnalysisPanel() {
  el('overview-body').innerHTML = '<p class="muted">Not yet analyzed.</p>';
  el('visual-body').innerHTML = '';
  el('audio-body').innerHTML = '';
  el('report-body').innerHTML = '';
}

// ── Score threshold coloring (per spec: red >=70%, amber 40-69%, green <40%) ──
function scoreClass(pct) {
  if (pct >= 70) return 'red';
  if (pct >= 40) return 'amber';
  return 'green';
}

// ── Rendering a full result into all four tabs ────────────────────────────
function renderResult(result) {
  if (result.error) {
    el('overview-body').innerHTML = `<p class="muted">${esc(result.error)}</p>`;
    el('visual-body').innerHTML = '';
    el('audio-body').innerHTML = '';
    el('report-body').innerHTML = '';
    return;
  }

  const d = describeVerdict(result);
  const overallPct = result.overall_score != null ? Math.round(result.overall_score * 100) : null;

  // Video overlay: verdict stamp
  el('verdict-stamp').hidden = false;
  el('verdict-stamp').className = `verdict-stamp ${d.tone}`;
  el('verdict-stamp').textContent = d.stamp;

  renderOverview(result, d, overallPct);
  renderVisual(result);
  renderAudio(result);
  renderReport(result);
  renderAnomalyTicks(result.anomalies, videoEl.duration || (result.video ? result.video.per_frame.length : 0));
}

// One place decides the words, tone and stamp for a verdict, from the real result fields only. It distinguishes the
// scenarios the project targets (PPR Ch1): authentic face + synthetic audio, manipulated face + authentic audio,
// both manipulated, plus the single-modality and INCONCLUSIVE cases. Scores are compared with 0.5 only to describe
// which side each branch is on; the verdict itself always comes from the fusion engine.
function describeVerdict(result) {
  const v = result.verdict;
  const pv = (result.video && result.video.p_fake != null) ? result.video.p_fake : null;
  const pa = (result.audio && result.audio.p_audio_fake != null) ? result.audio.p_audio_fake : null;
  const videoWithheld = !!(result.video && result.video.withheld);
  const audioWithheld = !!(result.audio && result.audio.withheld);

  if (v === 'INCONCLUSIVE') {
    const why = [];
    if (!result.video) why.push('no face was detected');
    else if (videoWithheld) why.push('the face footage is unlike the video model\'s training data');
    if (!result.audio || !result.audio.available) why.push('there is no audio track');
    else if (result.audio.gated) why.push('no speech was found');
    else if (audioWithheld) why.push('the speech is unlike the audio model\'s training data');
    return { tone: 'neutral', stamp: 'INCONCLUSIVE', icon: '?', label: 'No verdict',
             sub: 'No score the system can stand behind: ' + (why.join(' and ') || 'neither branch produced a score') };
  }
  const d = v === 'PARTIAL_MANIPULATION' ? describePartial(result, pv, pa)
    : describeVerdictCore(result, v, pv, pa, videoWithheld, audioWithheld, v === 'FAKE');
  const unfamiliar = [];
  if (result.video && result.video.ood && result.video.ood.unfamiliar && !videoWithheld) unfamiliar.push('face footage');
  if (result.audio && result.audio.ood && result.audio.ood.unfamiliar && !audioWithheld) unfamiliar.push('speech');
  if (unfamiliar.length) d.caution = `Unfamiliar input: the ${unfamiliar.join(' and the ')} ${unfamiliar.length > 1 ? 'are' : 'is'} unlike ` +
    'the training data, so this verdict may be wrong. Treat it with caution.';
  return d;
}

function describePartial(result, pv, pa) {
  const imp = result.fusion.implicated_modality;
  let scenario = '';
  if (pv != null && pa != null) {
    if (pv < 0.5 && pa >= 0.5) scenario = ' (authentic-looking face, synthetic-sounding audio)';
    else if (pv >= 0.5 && pa < 0.5) scenario = ' (manipulated-looking face, authentic-sounding audio)';
    else scenario = ' (both scores are on the same side of 0.5 but differ by at least the threshold)';
  }
  return { tone: 'partial', stamp: 'PARTIAL', icon: '&#9888;', label: 'Partial manipulation detected',
           sub: `Branches disagree: the ${imp} scored higher and is the more likely manipulated component${scenario}` };
}

function describeVerdictCore(result, v, pv, pa, videoWithheld, audioWithheld, fake) {
  let sub;
  if (pv == null) sub = 'Audio-branch verdict only: ' + (videoWithheld
    ? 'the video score was withheld because the face footage is unlike the training data' : 'no face was detected in this clip');
  else if (pa == null) sub = 'Video-branch verdict only: ' + (audioWithheld
    ? 'the audio score was withheld because the speech is unlike the training data' : 'the audio branch has no genuine score for this clip');
  else if (fake && pv >= 0.5 && pa >= 0.5) sub = 'Both video and audio are flagged';
  else if (fake) sub = 'Branches agree within the threshold; the combined score is above 0.5';
  else sub = 'Video and audio branches agree';
  return { tone: fake ? 'fake' : 'real', stamp: fake ? 'SYNTHETIC' : 'AUTHENTIC', icon: fake ? '&#9888;' : '&#10003;',
           label: fake ? 'Synthetic media detected' : 'Authentic media', sub };
}

function renderOverview(result, d, overallPct) {
  const audioScorePct = (result.audio && result.audio.p_audio_fake != null)
    ? Math.round(result.audio.p_audio_fake * 100) : null;
  const visualScorePct = (result.video && result.video.p_fake != null) ? Math.round(result.video.p_fake * 100) : null;
  const visualNa = (result.video && result.video.withheld) ? 'withheld (unfamiliar footage)' : 'not available';
  const audioNa = (result.audio && result.audio.withheld) ? 'withheld (unfamiliar speech)' : 'not available';
  const overallLabel = result.verdict === 'PARTIAL_MANIPULATION' ? 'Higher branch score' : 'Overall score';

  const scoreBlock = (label, pct, na = 'not available') => {
    if (pct == null) {
      return `<div class="score-block na">
        <div class="score-label">${label}</div>
        <div class="score-value">${na}</div>
      </div>`;
    }
    const cls = scoreClass(pct);
    return `<div class="score-block">
      <div class="score-label">${label}</div>
      <div class="score-value ${cls}">${pct}%</div>
      <div class="score-bar"><div class="score-bar-fill ${cls}"
        style="width:${pct}%;background:${cls === 'red' ? '#e05252' : cls === 'amber' ? '#d9a441' : '#3fb96a'}"></div></div>
    </div>`;
  };

  const anomalyRows = (result.anomalies && result.anomalies.length)
    ? result.anomalies.map(a => `
        <div class="anomaly-row">
          <div class="anomaly-dot ${a.severity}"></div>
          <div class="anomaly-desc">${a.label} (peak score ${a.peak_score})</div>
          <div class="anomaly-time">${a.start != null ? fmtDuration(a.start) + '–' + fmtDuration(a.end) : ''}</div>
        </div>`).join('')
    : '<div class="anomaly-empty">No elevated-likelihood frames detected.</div>';

  el('overview-body').innerHTML = `
    <div class="verdict-banner ${d.tone === 'fake' ? '' : d.tone}">
      <div class="verdict-banner-left">
        <div class="verdict-icon">${d.icon}</div>
        <div>
          <div class="verdict-text">${d.label}</div>
          <div class="verdict-sub">${d.sub}</div>
          ${d.caution ? `<div class="verdict-caution">&#9888; ${esc(d.caution)}</div>` : ''}
        </div>
      </div>
      <div class="verdict-confidence ${d.tone}">${overallPct != null ? overallPct + '%' : '&mdash;'}</div>
    </div>
    <div class="score-grid">
      ${scoreBlock(overallLabel, overallPct)}
      ${scoreBlock('Visual score', visualScorePct, visualNa)}
      ${scoreBlock('Audio score', audioScorePct, audioNa)}
    </div>
    ${anomalyRows}
    ${limitationsHtml()}
  `;
}

function lineChartSVG(values, w = 600, h = 90) {
  if (!values.length) return '<span class="muted">no frame data</span>';
  const n = values.length;
  const stepX = n > 1 ? w / (n - 1) : 0;
  const y = (v) => (h - v * h).toFixed(1);
  const points = values.map((v, i) => `${(i * stepX).toFixed(1)},${y(v)}`).join(' ');
  const dots = values.map((v, i) => v >= 0.5
    ? `<circle cx="${(i * stepX).toFixed(1)}" cy="${y(v)}" r="2.5" fill="#e05252"/>` : '').join('');
  return `<svg class="frame-line-svg" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">
    <line x1="0" y1="${y(0.7)}" x2="${w}" y2="${y(0.7)}" class="chart-guide guide-red" />
    <line x1="0" y1="${y(0.4)}" x2="${w}" y2="${y(0.4)}" class="chart-guide guide-amber" />
    <polyline points="${points}" fill="none" stroke="#888" stroke-width="1.5" vector-effect="non-scaling-stroke" />
    ${dots}
  </svg>`;
}

function renderVisual(result) {
  if (!result.video) {
    el('visual-body').innerHTML =
      `<p class="muted">No video score: ${esc(result.video_unavailable_reason || 'the video branch produced no result')}. ` +
      'The video branch never guesses a score for a clip it could not analyse.</p>';
    return;
  }
  const perFrame = result.video.per_frame;
  const vood = result.video.ood;
  const withheldHtml = result.video.withheld
    ? `<p class="withheld-notice">Video ${esc(result.video_unavailable_reason || 'score withheld')}. The model's raw score was
        ${Math.round(result.video.p_fake_withheld * 100)}%; it was <b>not used</b> in the verdict. The per-frame scores below are shown
        for transparency only.</p>`
    : (vood && vood.unfamiliar ? `<p class="withheld-notice">Video score ${esc(vood.reason)}.</p>` : '');
  const faceB64 = result.video.sample_face_png_b64;
  const faceHtml = faceB64
    ? `<div class="face-crop-row">
         <img class="face-crop-img" src="data:image/png;base64,${faceB64}" alt="MTCNN face crop" />
         <div class="face-crop-label">MTCNN face crop<br/>(first detected face, as fed to<br/>${result.video.model_name || 'the video model'})</div>
       </div>`
    : '';
  el('visual-body').innerHTML = `
    ${withheldHtml}
    ${faceHtml}
    <div class="chart-caption">Per-sampled-frame P(video_fake) — ${perFrame.length} face crops (line above 0.5 marked)</div>
    ${lineChartSVG(perFrame)}
  `;
}

function renderAudio(result) {
  const a = result.audio;
  if (!a || !a.available) {
    el('audio-body').innerHTML = '<p class="muted">No audio track in this clip.</p>';
    return;
  }
  if (a.gated) {
    el('audio-body').innerHTML = `<p class="muted">Gated off by the voice-activity check — ${a.gate_reason}.
      The spoof classifier only runs on genuine speech, so no score is produced for non-speech audio.</p>`;
    return;
  }
  const spoofPct = a.p_audio_fake != null ? Math.round(a.p_audio_fake * 100) : null;
  const withheldHtml = a.withheld
    ? `<p class="withheld-notice">Audio ${esc(a.ood && a.ood.reason ? a.ood.reason : 'score withheld')}. The classifier's raw
        score was ${Math.round(a.p_audio_fake_withheld * 100)}%; it was <b>not used</b> in the verdict.</p>`
    : (a.ood && a.ood.unfamiliar ? `<p class="withheld-notice">Audio score ${esc(a.ood.reason)}.</p>` : '');
  const scoreHtml = a.withheld
    ? `<div class="score-block na"><div class="score-label">Spoof score</div>
        <div class="score-value">withheld (unfamiliar speech)</div></div>`
    : spoofPct != null
    ? `<div class="score-block"><div class="score-label">Spoof score</div>
        <div class="score-value ${scoreClass(spoofPct)}">${spoofPct}%</div></div>`
    : `<div class="score-block na"><div class="score-label">Spoof score</div>
        <div class="score-value">${a.svm_status === 'untrained' ? 'classifier untrained' : 'not available'}</div></div>`;

  // Lip-sync confidence and AV delta are not produced by this pipeline --
  // omitted rather than fabricated, per the honesty contract.
  const waveform = (a.waveform || []).map(v =>
    `<div class="wf-bar ${spoofPct != null && spoofPct >= 50 ? 'fake' : 'real'}"
       style="height:${Math.max(4, Math.round(v * 100))}%"></div>`).join('');

  el('audio-body').innerHTML = `
    ${withheldHtml}
    <div class="score-grid" style="grid-template-columns:repeat(2,1fr)">${scoreHtml}
      <div class="score-block na"><div class="score-label">Lip-sync / AV-delta</div>
        <div class="score-value">not measured by this pipeline</div></div>
    </div>
    <div class="chart-caption">Waveform amplitude (real decoded audio, ${a.speech_seconds ? a.speech_seconds.toFixed(1) : '?'}s speech detected)</div>
    <div class="waveform">${waveform || '<span class="muted">no waveform data</span>'}</div>
  `;
}

function renderReport(result) {
  const exp = result.explanation;
  if (!exp.available) {
    el('report-body').innerHTML = `<p class="muted">${esc(exp.unavailable_reason || 'Explanation unavailable.')}</p>`;
    return;
  }
  // Which explainer produced this text, and whether it was checked, is always shown (PPR 3.4: the LLM is constrained and
  // its residual hallucination risk is acknowledged; a template is shown instead whenever the LLM text cannot be trusted).
  const isLlm = exp.source === 'llama3';
  const sourceNote = isLlm
    ? `Generated${exp.generation_time_s != null ? ' in ' + exp.generation_time_s + 's' : ''} by Llama 3 8B Instruct, local via Ollama. ` +
      (exp.faithfulness ? 'Checked by the automatic faithfulness screen: passed.' : 'Not checked by the faithfulness screen.')
    : `Template explanation (deterministic, no language model). Llama 3 output was not used: ${esc(exp.fallback_reason || 'unavailable')}.`;
  const text = esc(exp.text.trim());          // LLM text is untrusted input to the page
  const firstStop = text.indexOf('. ');
  let bodyHtml;
  if (firstStop > -1 && firstStop < text.length - 2) {
    bodyHtml = `<b>${text.slice(0, firstStop + 1)}</b> ${text.slice(firstStop + 2)}`;
  } else {
    bodyHtml = `<b>${text}</b>`;
  }
  el('report-body').innerHTML = `
    <div class="report-box">
      <div class="report-header"><span class="sparkle">&#10022;</span> Analysis summary
        <span class="src-badge ${isLlm ? 'llm' : 'template'}">${isLlm ? 'Llama 3' : 'Template'}</span></div>
      <div class="report-body">${bodyHtml}</div>
    </div>
    ${exp.withheld_note ? `<p class="withheld-notice" style="margin-top:8px">${esc(exp.withheld_note)}</p>` : ''}
    ${exp.caution_note ? `<p class="withheld-notice" style="margin-top:8px">${esc(exp.caution_note)}</p>` : ''}
    <p class="chart-caption" style="margin-top:8px">${sourceNote}</p>
  `;
}

function renderAnomalyTicks(anomalies, totalSeconds) {
  const container = el('anomaly-ticks');
  container.innerHTML = '';
  if (!anomalies || !totalSeconds) return;
  anomalies.forEach(a => {
    if (a.start == null) return;
    const pct = Math.min(100, (a.start / totalSeconds) * 100);
    const tick = document.createElement('div');
    tick.className = 'anomaly-tick';
    tick.style.left = `${pct}%`;
    container.appendChild(tick);
  });
}

// ── Video element wiring ──────────────────────────────────────────────────
videoEl.addEventListener('loadedmetadata', () => {
  updateTimeDisplay();
  if (state.activeId && state.results[state.activeId]) {
    renderAnomalyTicks(state.results[state.activeId].anomalies, videoEl.duration);
  }
});
videoEl.addEventListener('timeupdate', updateTimeDisplay);
videoEl.addEventListener('play', () => { el('btn-play').innerHTML = '&#10074;&#10074;'; });
videoEl.addEventListener('pause', () => { el('btn-play').innerHTML = '&#9658;'; });

function updateTimeDisplay() {
  const cur = fmtDuration(videoEl.currentTime || 0);
  const total = fmtDuration(videoEl.duration || 0);
  el('time-display').textContent = `${cur} / ${total}`;
  el('timecode-overlay').textContent = `${cur} / ${total}`;
  if (videoEl.duration) {
    el('progress-fill').style.width = `${(videoEl.currentTime / videoEl.duration) * 100}%`;
  }
}

el('btn-play').addEventListener('click', () => {
  if (videoEl.paused) videoEl.play(); else videoEl.pause();
});
el('btn-back10').addEventListener('click', () => { videoEl.currentTime = Math.max(0, videoEl.currentTime - 10); });
el('btn-fwd10').addEventListener('click', () => { videoEl.currentTime = Math.min(videoEl.duration || 0, videoEl.currentTime + 10); });
el('volume').addEventListener('input', (e) => { videoEl.volume = parseFloat(e.target.value); });
el('btn-download').addEventListener('click', () => {
  if (!state.activeId) return;
  const a = document.createElement('a');
  a.href = `/api/video/${state.activeId}`;
  a.download = '';
  document.body.appendChild(a); a.click(); a.remove();
});

// Draggable progress bar
let dragging = false;
function seekFromEvent(e) {
  const rect = el('progress-track').getBoundingClientRect();
  const frac = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
  if (videoEl.duration) videoEl.currentTime = frac * videoEl.duration;
}
el('progress-track').addEventListener('mousedown', (e) => { dragging = true; seekFromEvent(e); });
window.addEventListener('mousemove', (e) => { if (dragging) seekFromEvent(e); });
window.addEventListener('mouseup', () => { dragging = false; });

// ── Report tab actions ─────────────────────────────────────────────────────
el('btn-copy-json').addEventListener('click', async () => {
  const result = state.results[state.activeId];
  if (!result) return;
  const text = JSON.stringify(result, null, 2);
  let copied = false;
  try {
    await navigator.clipboard.writeText(text);
    copied = true;
  } catch (err) {
    // Clipboard API can be denied (permissions, insecure context, some
    // embedded browser contexts) -- fall back to the older execCommand
    // approach rather than silently doing nothing.
    try {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.focus(); ta.select();
      copied = document.execCommand('copy');
      document.body.removeChild(ta);
    } catch (err2) { copied = false; }
  }
  el('btn-copy-json').textContent = copied ? 'Copied!' : 'Copy failed';
  setTimeout(() => { el('btn-copy-json').textContent = 'Copy JSON'; }, 1200);
});
el('btn-export-pdf').addEventListener('click', () => window.print());

// ── History view ──────────────────────────────────────────────────────────
// ── Evaluation view: every table comes from /api/evaluation (numbers.json); pending sections say why they are withheld ──
async function renderEvaluation() {
  let data;
  try { data = await (await fetch('/api/evaluation')).json(); }
  catch (err) { el('evaluation-body').innerHTML = '<p class="muted">Could not load the evaluation results.</p>'; return; }
  const sh = data.shipped;
  const head = sh
    ? `<p class="eval-intro">Shipped video model: <b>${esc(sh.arch)}</b> (run ${esc(sh.tag)}, seed ${esc(sh.seed)}), trained on ${esc(sh.trained_on)}.</p>`
    : '<p class="eval-intro">No video model has been promoted through the release step yet, so no row below is marked as shipped.</p>';
  el('evaluation-body').innerHTML = head + data.sections.map(s => {
    const pill = `<span class="status-pill ${s.status}">${s.status === 'current' ? 'current' : 'pending'}</span>`;
    if (s.status !== 'current') {
      return `<section class="eval-section"><h3>${esc(s.title)} ${pill}</h3>
        <p class="eval-pending">${esc(s.reason)}</p><div class="eval-src">${esc(s.source)}</div></section>`;
    }
    const cols = s.columns.map(c => `<th>${esc(c)}</th>`).join('');
    const rows = s.rows.map(r => `<tr${String(r[0]).includes('[SHIPPED]') ? ' class="shipped"' : ''}>${r.map(c => `<td>${esc(c)}</td>`).join('')}</tr>`).join('');
    return `<section class="eval-section"><h3>${esc(s.title)} ${pill}</h3>
      <div class="eval-scroll"><table class="eval-table"><thead><tr>${cols}</tr></thead><tbody>${rows}</tbody></table></div>
      ${s.note ? `<p class="eval-note">${esc(s.note)}</p>` : ''}<div class="eval-src">Source: ${esc(s.source)}</div></section>`;
  }).join('') + `<p class="eval-src">Generated ${esc(data.generated_at || 'unknown')} by scripts/build_numbers.py.</p>`;
}

// ── Limitations: shown next to every verdict; each line is grounded in a result file (see /api/limitations) ──
async function loadLimitations() {
  try { state.limitations = await (await fetch('/api/limitations')).json(); } catch (err) { state.limitations = null; }
}

function limitationsHtml() {
  const L = state.limitations;
  if (!L) return '';
  return `<details class="limits" open><summary>How to read this result, and its limits</summary>
    <p class="limits-how">${esc(L.how_to_read)}</p>
    <ul>${L.limitations.map(l => `<li>${esc(l.text)}<span class="limit-src">${esc(l.source)}</span></li>`).join('')}</ul></details>`;
}

function renderHistory() {
  el('history-body').innerHTML = state.queue.map(j => `
    <tr>
      <td>${j.filename}</td>
      <td>${j.verdict || 'pending'}</td>
      <td>${fmtDuration(j.duration)}</td>
      <td>${state.results[j.id] ? new Date(state.results[j.id].analyzed_at).toLocaleString() : '—'}</td>
    </tr>`).join('') || '<tr><td colspan="4" class="muted">No files analyzed yet this session.</td></tr>';
}

// ── Init ───────────────────────────────────────────────────────────────────
async function loadQueue() {
  // The backend's JOBS dict outlives a page reload (it's process-lifetime,
  // not per-request) -- rehydrate the sidebar from it so a refresh doesn't
  // make already-analyzed jobs disappear from view.
  const jobs = await (await fetch('/api/queue')).json();
  state.queue = jobs.map(j => ({ id: j.id, filename: j.filename, status: j.status,
                                   verdict: j.verdict, duration: j.duration }));
  renderQueue();
  for (const j of jobs) {
    if (j.status === 'done') {
      const result = await (await fetch(`/api/result/${j.id}`)).json();
      if (!result.error && result.verdict !== undefined) state.results[j.id] = result;
    }
  }
}

loadModelInfo();
loadLimits();
loadLimitations();
loadDemoClips();
loadQueue();
