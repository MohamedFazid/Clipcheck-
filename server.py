"""FastAPI backend: a delivery layer over the pipeline modules in scripts/ (no model, threshold or prompt lives here).
Every response field comes from a model that ran on the clip, or is null with a stated reason.
Run: ./run_server.sh"""

import base64
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

os.environ.setdefault('USE_TF', '0')
os.environ.setdefault('USE_FLAX', '0')

import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

PROJECT_ROOT = Path(__file__).resolve().parent
MODEL_PATH = PROJECT_ROOT / 'models' / 'best_model.pth'
# DEEPFAKE_STATIC_DIR serves another copy of the interface with the same backend, e.g. the frozen pre-redesign v1 in
# docs/user_testing/ui_v1_snapshot/ (run_v1_interface.sh), so old-interface screenshots stay reproducible after the redesign.
STATIC_DIR = Path(os.environ['DEEPFAKE_STATIC_DIR']).resolve() if os.environ.get('DEEPFAKE_STATIC_DIR') else PROJECT_ROOT / 'static'

sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
from video_infer import load_models, analyse_video_file, video_model_summary
from evaluation_view import build_evaluation, build_limitations
from fusion import (fuse, THRESHOLD_T_DEFAULT, THRESHOLD_T_SOURCE, AUDIO_ACCURACY, AUDIO_ACCURACY_IS_MEASURED,
                    AUDIO_ACCURACY_SOURCE, VIDEO_ACCURACY_DEFAULT, VIDEO_ACCURACY_IS_MEASURED, VIDEO_ACCURACY_SOURCE)

try:
    from audio_branch import load_encoder, extract_audio_16k, embed_waveform, load_trained_svm
    AUDIO_OK = True
except Exception:
    AUDIO_OK = False

try:
    from vad import analyse as vad_analyse, vad_available
    VAD_OK = vad_available()
except Exception:
    VAD_OK = False

try:
    from explain import explain, explanation_available, ExplanationUnavailable, build_structured_input
    EXPLAIN_OK = True
except Exception:
    EXPLAIN_OK = False

# Deterministic template explainer and the automatic faithfulness screen (scripts/explain_checks.py). The LLM stays the
# primary explainer; these are only a safety net around it (see _explanation_block).
try:
    from explain_checks import check_faithfulness, explain_template
    CHECKS_OK = True
except Exception:
    CHECKS_OK = False

# Upload limits. Analysis samples at most 20 face crops, so length mostly costs decoding time; the caps mainly protect the
# machine and the user from a wrong file. Overridable by environment variable.
MAX_UPLOAD_MB = int(os.environ.get('DEEPFAKE_MAX_UPLOAD_MB', '200'))
MAX_DURATION_S = int(os.environ.get('DEEPFAKE_MAX_DURATION_S', '120'))
ALLOWED_SUFFIXES = ('.mp4', '.mov', '.avi', '.mkv')
UPLOAD_PREFIX = 'deepfake_upload_'          # every temp file this server creates starts with this
STALE_UPLOAD_SECONDS = 24 * 3600            # orphaned temp uploads older than this are removed at startup

app = FastAPI(title='Multimodal Deepfake Detector API')

# ── Lazily-loaded, process-wide models (same one-load pattern as app.py's
# st.cache_resource, just without Streamlit) ──────────────────────────────────
_video_models = None
_audio_encoder = None
_audio_svm = None
_audio_svm_checked = False


def get_video_models():
    global _video_models
    if _video_models is None:
        _video_models = load_models(str(MODEL_PATH))
    return _video_models


def get_audio_encoder():
    global _audio_encoder
    if _audio_encoder is None:
        _audio_encoder = load_encoder('cpu')
    return _audio_encoder


try:
    from ood_gate import clip_video_distance
    OOD_OK = True
except Exception:
    OOD_OK = False

# Out-of-domain gates (ledger O1). DEEPFAKE_OOD_MODE: 'warn' (default, flags unfamiliar input),
# 'withhold' (drops that branch's score; failed its pre-set rule) or 'off'.
OOD_MODE = os.environ.get('DEEPFAKE_OOD_MODE', 'warn').strip().lower()
OOD_GATE_PATHS = {'audio': PROJECT_ROOT / 'models' / 'audio_ood_gate.joblib',
                  'video': PROJECT_ROOT / 'models' / 'video_ood_gate.joblib'}
_ood_gates = None


def get_ood_gates() -> dict:
    """{'audio': saved-gate-dict or None, 'video': ...}; a missing or unreadable file disables that branch's gate only."""
    global _ood_gates
    if _ood_gates is None:
        _ood_gates = {}
        for branch, path in OOD_GATE_PATHS.items():
            try:
                _ood_gates[branch] = (__import__('joblib').load(path)
                                      if OOD_OK and OOD_MODE in ('warn', 'withhold') and path.exists() else None)
            except Exception:
                _ood_gates[branch] = None
    return _ood_gates


OOD_WHAT = {'video': ('face footage', 'FaceForensics++ faces the video model was trained on'),
            'audio': ('speech recording', 'ASVspoof 2019 speech the audio classifier was trained on')}


def _ood_check(branch: str, distance: float) -> dict:
    saved = get_ood_gates()[branch]
    gate = saved['gate']
    unfamiliar = bool(distance > gate.threshold_)
    withheld = unfamiliar and OOD_MODE == 'withhold'
    what, trained = OOD_WHAT[branch]
    where = f'this {what} is unlike the {trained} (out-of-domain distance {distance:.0f}, limit {gate.threshold_:.0f})'
    if withheld:
        reason = f'score withheld: {where}, so the model\'s score on it is not trustworthy'
    elif unfamiliar:
        reason = f'caution: {where}; on unfamiliar input this model\'s scores have proved unreliable, so this score may be wrong'
    else:
        reason = None
    return {'distance': round(float(distance), 1), 'threshold': round(float(gate.threshold_), 1), 'unfamiliar': unfamiliar,
            'withheld': withheld, 'mode': OOD_MODE,
            'method': f'Mahalanobis distance ({gate.kind}), limit = {gate.percentile:g}th percentile of in-domain data',
            'reason': reason}


def get_audio_svm():
    """Same rule as app.py: a checkpoint on disk is not sufficient on its own
    -- it must also be a full-dataset run (AUDIO_ACCURACY_IS_MEASURED), not a
    --max-per-class sanity pass. See fusion.py's _resolve_audio_accuracy."""
    global _audio_svm, _audio_svm_checked
    if not _audio_svm_checked:
        _audio_svm_checked = True
        if AUDIO_OK:
            _audio_svm = load_trained_svm()
    return _audio_svm if AUDIO_ACCURACY_IS_MEASURED else None


# In-memory job store: lives only as long as this server process (not persisted).
JOBS: dict[str, dict] = {}


def _is_browser_safe(path: str, ffmpeg_exe: str) -> bool:
    """Identical logic to app.py's _is_browser_safe -- probes the actual codec
    rather than trusting the file extension (Celeb-DF-v2's .mp4 files hold
    plain 'mpeg4', not H.264, which no browser decodes natively)."""
    suffix = Path(path).suffix.lower()
    if suffix not in ('.mp4', '.webm'):
        return False
    try:
        out = subprocess.run([ffmpeg_exe, '-i', path],
                              capture_output=True, timeout=15).stderr.decode(errors='replace')
    except Exception:
        return False
    video_line = next((l for l in out.splitlines() if 'Video:' in l), '').lower()
    if suffix == '.mp4':
        return 'h264' in video_line
    return 'vp8' in video_line or 'vp9' in video_line


def _previewable_video_path(path: str) -> str:
    """Identical logic to app.py's _previewable_video_path."""
    import imageio_ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    if _is_browser_safe(path, ffmpeg_exe):
        return path
    out_path = str(Path(tempfile.gettempdir()) / f'{Path(path).stem}_preview.mp4')
    try:
        subprocess.run(
            [ffmpeg_exe, '-y', '-i', path,
             '-c:v', 'libx264', '-preset', 'ultrafast', '-c:a', 'aac',
             '-movflags', '+faststart', out_path],
            capture_output=True, check=True, timeout=60,
        )
        return out_path
    except Exception:
        return path


def _probe_duration_and_fps(path: str, ffmpeg_exe: str) -> tuple[Optional[float], Optional[float]]:
    """Duration and fps from ffmpeg's stream info, used only to turn sampled frame indexes into timestamps."""
    try:
        out = subprocess.run([ffmpeg_exe, '-i', path],
                              capture_output=True, timeout=15).stderr.decode(errors='replace')
    except Exception:
        return None, None
    duration = None
    fps = None
    for line in out.splitlines():
        line = line.strip()
        if line.startswith('Duration:'):
            try:
                hms = line.split('Duration:')[1].split(',')[0].strip()
                h, m, s = hms.split(':')
                duration = int(h) * 3600 + int(m) * 60 + float(s)
            except Exception:
                pass
        if 'Video:' in line and 'fps' in line:
            try:
                fps = float(line.split('fps')[0].strip().split(' ')[-1])
            except Exception:
                pass
    return duration, fps


def _frame_anomalies(per_frame: list[float], fps: Optional[float]) -> list[dict]:
    """Turn the per-sampled-frame P(fake) into timestamped anomaly windows (sample indexes if fps is unknown)."""
    interval_seconds = (max(1, int(fps) // 3) / fps) if fps else None
    rows = []
    i = 0
    n = len(per_frame)
    while i < n:
        if per_frame[i] >= 0.5:
            j = i
            peak = per_frame[i]
            while j < n and per_frame[j] >= 0.5:
                peak = max(peak, per_frame[j])
                j += 1
            if interval_seconds:
                rows.append({
                    'start': round(i * interval_seconds, 2),
                    'end': round((j - 1) * interval_seconds + interval_seconds, 2),
                    'label': 'Elevated visual manipulation likelihood',
                    'severity': 'high' if peak >= 0.7 else 'medium',
                    'peak_score': round(peak, 3),
                })
            else:
                rows.append({
                    'start': None, 'end': None,
                    'label': f'Elevated visual manipulation likelihood (sampled frames {i}-{j-1})',
                    'severity': 'high' if peak >= 0.7 else 'medium',
                    'peak_score': round(peak, 3),
                })
            i = j
        else:
            i += 1
    return rows


def _waveform_bars(wav: np.ndarray, n_bars: int = 160) -> list[float]:
    """Real amplitude visualization data, downsampled from the actual decoded
    waveform (the same array embed_waveform() runs on) -- genuine audio data,
    not a fabricated shape. One value per bar, 0..1 normalised."""
    if wav is None or wav.size == 0:
        return []
    chunks = np.array_split(np.abs(wav), n_bars)
    bars = np.array([c.mean() if c.size else 0.0 for c in chunks])
    peak = bars.max()
    if peak > 0:
        bars = bars / peak
    return [round(float(b), 4) for b in bars]


def _overall_score(fusion_result, p_video, p_audio):
    """The single headline P(fake) shown with a verdict. The fused score on agreement or single-modality pass-through;
    on disagreement there is deliberately no fused number (no averaging across a genuine disagreement), so it is the
    higher branch score, labelled as such in the UI; None when neither branch scored (INCONCLUSIVE)."""
    if fusion_result.p_fake is not None:
        return fusion_result.p_fake
    scores = [s for s in (p_video, p_audio) if s is not None]
    return max(scores) if scores else None


def _explanation_block(fusion_result, anomalies=None) -> dict:
    """Stage 5: Llama 3 text if it passes the faithfulness screen, otherwise the template (labelled); `source` says which.
    The rejected LLM text is kept for audit. `anomalies` are the timing windows from the Visual tab."""
    block = {'available': False, 'text': None, 'source': None, 'generation_time_s': None,
             'unavailable_reason': None, 'fallback_reason': None, 'faithfulness': None, 'rejected_llm_text': None}
    llm_text, why_no_llm = None, None
    if fusion_result.verdict == 'INCONCLUSIVE':
        why_no_llm = 'no branch produced a score, so there is nothing for the language model to verbalise'
    elif not EXPLAIN_OK:
        why_no_llm = 'explanation layer unavailable in this environment'
    elif not explanation_available():
        why_no_llm = 'local LLM not reachable (start `ollama serve`)'
    else:
        try:
            t0 = time.perf_counter()
            llm_text = explain(fusion_result, anomalies=anomalies)
            block['generation_time_s'] = round(time.perf_counter() - t0, 1)
        except ExplanationUnavailable as e:
            why_no_llm = str(e)

    if llm_text is not None:
        if not CHECKS_OK:                                    # cannot screen: show it, and say it was not screened
            block.update(available=True, text=llm_text, source='llama3')
            return block
        screen = check_faithfulness(llm_text, build_structured_input(fusion_result, anomalies))
        block['faithfulness'] = screen
        if screen['passed']:
            block.update(available=True, text=llm_text, source='llama3')
            return block
        block['rejected_llm_text'] = llm_text
        why_no_llm = ('the language-model text failed the automatic faithfulness screen ('
                      + ', '.join(sorted({v['type'] for v in screen['violations']})) + ')')

    if CHECKS_OK:
        block.update(available=True, text=explain_template(fusion_result, anomalies), source='template',
                     fallback_reason=why_no_llm)
    else:
        block['unavailable_reason'] = why_no_llm
    return block


def _models_ran_rows(video_result, audio, p_audio_fake, fusion_result, t_video, explanation, video_ood=None, audio_ood=None):
    """Same 'what actually ran, and what it cost' table as app.py's expander,
    just as structured rows instead of a Streamlit st.table."""
    rows = [{'stage': '1', 'model': f'MTCNN + {video_model_summary()["name"]}', 'data_type': 'image',
              'produced': 'P(video_fake)' if video_result else 'no face detected, so no video score',
              'time_s': round(t_video, 2) if video_result else None}]
    if video_ood is not None:
        rows.append({'stage': '1b', 'model': 'Out-of-domain gate (video)', 'data_type': 'image',
                     'produced': (f'score withheld (distance {video_ood["distance"]:.0f} > limit {video_ood["threshold"]:.0f})'
                                  if video_ood['withheld'] else
                                  (f'score kept, flagged unfamiliar (distance {video_ood["distance"]:.0f} > limit {video_ood["threshold"]:.0f})'
                                   if video_ood['unfamiliar'] else
                                   f'score kept (distance {video_ood["distance"]:.0f} <= limit {video_ood["threshold"]:.0f})')),
                     'time_s': None})
    if audio and not audio.get('no_audio'):
        rows.append({'stage': '2a', 'model': 'Silero VAD', 'data_type': 'audio',
                      'produced': 'speech / not speech', 'time_s': round(audio.get('t_vad', 0), 2)})
        if not audio.get('gated'):
            rows.append({'stage': '2b', 'model': 'wav2vec2-base', 'data_type': 'audio',
                          'produced': f'{audio.get("dim", 0)}-d embedding',
                          'time_s': round(audio.get('t_embed', 0), 2)})
            rows.append({'stage': '2c', 'model': 'SVM (ASVspoof)', 'data_type': 'audio',
                          'produced': (f'P(audio_fake) = {p_audio_fake:.3f}'
                                       if p_audio_fake is not None
                                       else 'not run — classifier untrained'),
                          'time_s': round(audio.get('t_svm', 0), 3) if p_audio_fake is not None else None})
            if audio_ood is not None:
                rows.append({'stage': '2d', 'model': 'Out-of-domain gate (audio)', 'data_type': 'audio',
                             'produced': (f'score withheld (distance {audio_ood["distance"]:.0f} > limit {audio_ood["threshold"]:.0f})'
                                          if audio_ood['withheld'] else
                                          (f'score kept, flagged unfamiliar (distance {audio_ood["distance"]:.0f} > limit {audio_ood["threshold"]:.0f})'
                                           if audio_ood['unfamiliar'] else
                                           f'score kept (distance {audio_ood["distance"]:.0f} <= limit {audio_ood["threshold"]:.0f})')),
                             'time_s': None})
    else:
        rows.append({'stage': '2', 'model': 'Audio models', 'data_type': 'audio',
                      'produced': 'not run — clip has no audio track', 'time_s': None})
    rows.append({'stage': '3-4', 'model': 'fusion.py', 'data_type': 'logic',
                  'produced': fusion_result.verdict if fusion_result else '—', 'time_s': 0.0})
    t_explain = explanation.get('generation_time_s')
    if explanation.get('source') == 'llama3':
        rows.append({'stage': '5', 'model': 'Llama 3 8B Instruct', 'data_type': 'text',
                      'produced': ('plain-language explanation (passed the faithfulness screen)'
                                   if explanation.get('faithfulness') else 'plain-language explanation (not screened)'),
                      'time_s': t_explain})
    elif explanation.get('source') == 'template':
        rows.append({'stage': '5', 'model': 'Deterministic template (Llama 3 not used)', 'data_type': 'text',
                      'produced': f'plain-language explanation; reason: {explanation.get("fallback_reason")}',
                      'time_s': t_explain})
    else:
        rows.append({'stage': '5', 'model': 'Llama 3 8B Instruct', 'data_type': 'text',
                      'produced': f'not run: {explanation.get("unavailable_reason")}', 'time_s': None})
    return rows


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get('/')
def index():
    # The stylesheet and script links carry their file's modification time, so a browser never runs an old cached copy against a
    # new page (seen 2026-09-24 after the v2 redesign: new HTML with the cached v1 script rendered an empty page).
    html = (STATIC_DIR / 'index.html').read_text()
    for name in ('style.css', 'app.js'):
        f = STATIC_DIR / name
        if f.exists():
            html = html.replace(f'/static/{name}"', f'/static/{name}?v={int(f.stat().st_mtime)}"')
    return HTMLResponse(html, headers={'Cache-Control': 'no-cache'})


@app.middleware('http')
async def _revalidate_static(request, call_next):
    """Static files may be cached but must be revalidated (ETag) on every load, so an update always reaches the browser."""
    response = await call_next(request)
    if request.url.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'no-cache'
    return response


app.mount('/static', StaticFiles(directory=str(STATIC_DIR)), name='static')


@app.get('/api/model_info')
def model_info():
    """Identifies the actual pretrained models behind each pipeline stage,
    for the sidebar -- not just checkpoint trivia. Every 'status' string is
    read from real on-disk state, never assumed."""
    models = []

    vm = video_model_summary()          # architecture, training data and provenance come from models/shipped_model.json
    video_status = 'checkpoint missing' if not MODEL_PATH.exists() else vm['status']
    models.append({
        'stage': 'Video', 'name': f'{vm["name"]} + MTCNN',
        'status': video_status,
    })

    speech_gate = ('gates the audio branch: no speech, no audio score' if VAD_OK
                   else 'unavailable in this environment (audio branch runs ungated)')
    models.append({'stage': 'Speech gate', 'name': 'Silero VAD', 'status': speech_gate})

    models.append({
        'stage': 'Audio encoder', 'name': 'wav2vec2-base (frozen)',
        'status': 'facebook/wav2vec2-base, not fine-tuned',
    })

    audio_status = 'untrained (ASVspoof 2019 LA pending)'
    audio_metrics_path = PROJECT_ROOT / 'results' / 'audio_branch' / 'metrics.json'
    if audio_metrics_path.exists():
        import json
        with open(audio_metrics_path) as f:
            m = json.load(f)
        if m.get('full_dataset'):
            audio_status = f'trained, {round(m["eval_eer"] * 100, 2)}% EER (ASVspoof 2019 LA)'
        elif m.get('subsampled_per_class'):
            audio_status = f'sanity-run only ({m["subsampled_per_class"]}/class) -- not used for scoring'
    models.append({'stage': 'Audio classifier', 'name': 'SVM (RBF)', 'status': audio_status})

    llm_name = os.environ.get('DEEPFAKE_LLM', 'llama3:8b')
    if EXPLAIN_OK:
        llm_status = f'reachable via Ollama' if explanation_available() else 'Ollama unreachable'
    else:
        llm_status = 'unavailable in this environment'
    models.append({'stage': 'Explanation', 'name': f'Llama 3 8B Instruct ({llm_name})', 'status': llm_status})

    return {'models': models}


# Constructed evaluation clips (FF++ video + ASVspoof audio, scripts/build_fallback_eval_set.py) cover all four PPR categories,
# unlike the silent FF++ demo clips. They live in a git-ignored folder, so the list degrades to the bundled clips without it.
FALLBACK_MANIFEST = PROJECT_ROOT / 'eval_fallback' / 'manifest.json'
LAVDF_MANIFEST = PROJECT_ROOT / 'eval_lavdf' / 'manifest.json'    # independent LAV-DF test clips (F6); same first-3-by-id rule
DEMO_PER_CATEGORY = 3
CATEGORY_LABELS = {'RVRA': 'real video + real audio', 'RVFA': 'real video + fake audio',
                   'FVRA': 'fake video + real audio', 'FVFA': 'fake video + fake audio'}


def _demo_items() -> list:
    """(path, kind) for every demo clip, in a stable order (the demo_id is the index into this list): the bundled clips
    first, then the first DEMO_PER_CATEGORY constructed clips of each category BY ID, a fixed rule chosen before looking at
    any result so the demos are not cherry-picked. The kind states the ground truth of the construction, not a model output."""
    items = []
    for p in sorted((PROJECT_ROOT / 'demo_videos').rglob('*.mp4')):
        s = str(p)
        if 'manipulated' in s:
            kind = 'FAKE clip'
        elif 'original' in s:
            kind = 'REAL clip'
        elif p.name.startswith('composite_'):
            kind = 'COMPOSITE (real video + synthetic speech)'
        elif p.name.startswith('noface_'):
            kind = 'NO-FACE test pattern (no face, no sound)'
        else:
            kind = 'AUDIO-TEST clip'
        items.append((p, kind))
    try:
        clips = json.load(open(FALLBACK_MANIFEST))['clips']
    except (OSError, ValueError, KeyError):
        return items
    picked = {cat: [] for cat in CATEGORY_LABELS}
    for c in sorted(clips, key=lambda c: c['id']):
        if c.get('category') in picked and len(picked[c['category']]) < DEMO_PER_CATEGORY:
            picked[c['category']].append(c)
    for cat, label in CATEGORY_LABELS.items():
        for c in picked[cat]:
            p = PROJECT_ROOT / c['output_path']
            if p.exists():
                items.append((p, f'{cat}: {label} (constructed)'))
    try:
        lav = json.load(open(LAVDF_MANIFEST))['clips']
    except (OSError, ValueError, KeyError):
        lav = []
    picked = {cat: [] for cat in CATEGORY_LABELS}
    for c in sorted(lav, key=lambda c: c['id']):
        if c.get('category') in picked and len(picked[c['category']]) < DEMO_PER_CATEGORY:
            picked[c['category']].append(c)
    for cat, label in CATEGORY_LABELS.items():
        for c in picked[cat]:
            p = PROJECT_ROOT / c['output_path']
            if p.exists():
                items.append((p, f'{cat}: {label} (LAV-DF, independent set)'))
    # Constructed clips on the featured shelf but outside the first-3 rule (27 Sep: FVFA_004), appended last so no other
    # demo_id moves.
    have = {p.name for p, _ in items if 'eval_lavdf' not in p.parts}
    for c in sorted(clips, key=lambda c: c['id']):
        name = Path(c['output_path']).name
        if name in FEATURED_DEMOS and name not in have and c.get('category') in CATEGORY_LABELS:
            p = PROJECT_ROOT / c['output_path']
            if p.exists():
                items.append((p, f"{c['category']}: {CATEGORY_LABELS[c['category']]} (constructed)"))
    return items


def _demo_display_name(p: Path) -> str:
    """LAV-DF clips reuse the constructed set's file names (RVRA_000.mp4), so they are shown with a LAVDF_ prefix."""
    return f'LAVDF_{p.name}' if 'eval_lavdf' in p.parts else p.name


NUMBERS_PATH = PROJECT_ROOT / 'results' / 'numbers.json'
LATENCY_PATH = PROJECT_ROOT / 'results' / 'latency' / 'latency.json'
SHIPPED_PATH = PROJECT_ROOT / 'models' / 'shipped_model.json'
HOW_TO_READ = ('Each score is the model\'s estimate, from 0% to 100%, of how likely the video or the audio is to be manipulated; '
               'near 50% means it is unsure. When the video and the audio disagree, the tool names the part that looks more '
               'manipulated instead of averaging them into one number.')


def _read_json(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def _fusion_info() -> dict:
    return {'threshold_T': THRESHOLD_T_DEFAULT, 'threshold_T_source': THRESHOLD_T_SOURCE,
            'video_accuracy_source': VIDEO_ACCURACY_SOURCE, 'audio_accuracy_source': AUDIO_ACCURACY_SOURCE}


@app.get('/api/evaluation')
def evaluation():
    """The evaluation results behind the app, read from results/numbers.json (generated by scripts/build_numbers.py). Anything
    produced with a superseded video model is withheld as 'pending' rather than shown (see scripts/evaluation_view.py)."""
    out = build_evaluation(_read_json(NUMBERS_PATH) or {}, _read_json(SHIPPED_PATH), _read_json(LATENCY_PATH), _fusion_info())
    # The weights fusion.py actually uses (accuracy-weighted), for the plain-language legend and the Accuracy page.
    total = VIDEO_ACCURACY_DEFAULT + AUDIO_ACCURACY
    out['fusion'] = {'threshold_T': THRESHOLD_T_DEFAULT, 'video_accuracy': VIDEO_ACCURACY_DEFAULT, 'audio_accuracy': AUDIO_ACCURACY,
                     'w_video': VIDEO_ACCURACY_DEFAULT / total, 'w_audio': AUDIO_ACCURACY / total}
    return out


@app.get('/api/limitations')
def limitations():
    """Plain-language limits of the shipped models, each grounded in a result file, plus a short 'how to read this' line."""
    return {'how_to_read': HOW_TO_READ,
            'limitations': build_limitations(_read_json(NUMBERS_PATH) or {}, _read_json(SHIPPED_PATH), _fusion_info())}


# Plain-language names for the example clips, "<scene>, <what was changed>", taken from how each clip was made.
# Testing mode (#testing) shows the neutral codes instead, so names cannot hint at the answer.
_CAT_TITLES = {'RVRA': 'genuine face and voice', 'RVFA': 'voice replaced',
               'FVRA': 'face replaced', 'FVFA': 'face and voice replaced'}
# LAV-DF fakes are Wav2Lip lip-sync and SV2TTS voice cloning of a few words (each fake part under one second), not face swaps.
_LAVDF_CHANGES = {'RVRA': 'genuine face and voice', 'RVFA': 'a few words re-voiced',
                  'FVRA': 'lips briefly re-synced', 'FVFA': 'lips and a few words altered'}
# What was really changed in each clip, from how it was built (never from a model): picture then voice. The demo strips in
# interface v4 show it as a Face light and a Voice light (real, fake, none), hidden in testing mode.
_CAT_CHANGES = {'RVRA': ('genuine', 'genuine'), 'RVFA': ('genuine', 'changed'),
                'FVRA': ('changed', 'genuine'), 'FVFA': ('changed', 'changed')}
_SCENES = {   # display name: (scene, setting)
    'composite_real_video_synthetic_speech.mp4': ('News interview', 'Generated speech added'),
    '183_253.mp4': ('News interview', 'Studio, no sound'), '183.mp4': ('News interview', 'Studio, no sound'),
    '469_481.mp4': ('Vlogger', 'At home, no sound'), '469.mp4': ('Vlogger', 'At home, no sound'),
    '481_469.mp4': ('Newsreader', 'Consumer report, no sound'), '481.mp4': ('Newsreader', 'Consumer report, no sound'),
    '585_599.mp4': ('Newsroom presenter', 'Newsroom, no sound'), '585.mp4': ('Newsroom presenter', 'Newsroom, no sound'),
    '599_585.mp4': ('Talk show guest', 'Blue studio, no sound'), '599.mp4': ('Talk show guest', 'Blue studio, no sound'),
    'sample_with_audio.mp4': ('News interview', 'Sound, but no speech'),
    'RVRA_000.mp4': ('Studio guest', 'TV interview'), 'RVRA_001.mp4': ('News presenter', 'Standing, news ticker'),
    'RVRA_002.mp4': ('Sports presenter', 'Red studio, subtitled'),
    'RVFA_000.mp4': ('Webcam streamer', 'Desk microphone'), 'RVFA_001.mp4': ('Newsreader', 'World-map studio'),
    'RVFA_002.mp4': ('Beauty vlogger', 'Home studio'),
    'FVRA_000.mp4': ('Business newsreader', 'Financial news desk'), 'FVRA_001.mp4': ('News anchor', 'Flag backdrop'),
    'FVRA_002.mp4': ('Cable news host', 'Opinion segment'),
    'FVFA_000.mp4': ('Newsreader', 'News desk, inset picture'), 'FVFA_001.mp4': ('Morning show host', 'TV studio set'),
    'FVFA_002.mp4': ('Vlogger', 'Home webcam'), 'FVFA_004.mp4': ('TV presenter', 'Skyline studio'),
    'LAVDF_RVRA_000.mp4': ('TV interview', ''), 'LAVDF_RVRA_001.mp4': ('Press interview', ''),
    'LAVDF_RVRA_002.mp4': ('Post-match interview', ''),
    'LAVDF_RVFA_000.mp4': ('Post-match interview', ''), 'LAVDF_RVFA_001.mp4': ('Pitch-side interview', ''),
    'LAVDF_RVFA_002.mp4': ('Post-match interview', ''),
    'LAVDF_FVRA_000.mp4': ('Post-match interview', ''), 'LAVDF_FVRA_001.mp4': ('Pitch-side interview', ''),
    'LAVDF_FVRA_002.mp4': ('Post-match interview', ''),
    'LAVDF_FVFA_000.mp4': ('Post-match interview', ''),
    'LAVDF_FVFA_001.mp4': ('Post-match interview', ''), 'LAVDF_FVFA_002.mp4': ('Post-match interview', ''),
}
# The shelf of eight: per category, the first two clips by id the shipped model gets fully right with no warning.
# Chosen for being right, so they illustrate and are not evidence of accuracy (test_featured_shelf_follows_its_rule).
FEATURED_DEMOS = ['RVRA_000.mp4', 'RVFA_000.mp4', 'FVRA_000.mp4', 'FVFA_002.mp4',
                  'RVRA_001.mp4', 'RVFA_001.mp4', 'FVRA_001.mp4', 'FVFA_004.mp4']
SHELF_SKIPPED_FOR_WARNING = ['FVFA_003.mp4']
# Testing mode (#testing) keeps the eight clips the list featured during user-testing rounds 1 and 2 (the shelf before 27 Sep),
# shown by neutral code, so round 3 runs on the same clips; it includes LAVDF_RVRA_000, the wrong verdict task 7 needs.
TESTING_DEMOS = ['RVRA_000.mp4', 'RVFA_000.mp4', 'FVRA_000.mp4', 'FVFA_002.mp4', '183_253.mp4', '183.mp4',
                 'LAVDF_RVRA_000.mp4', 'noface_silent.mp4']
_DURATION_CACHE = {}


def _clip_duration(p: Path):
    key = (str(p), p.stat().st_mtime)
    if key not in _DURATION_CACHE:
        try:
            ffmpeg_exe = __import__('imageio_ffmpeg').get_ffmpeg_exe()
            _DURATION_CACHE[key] = _probe_duration_and_fps(str(p), ffmpeg_exe)[0]
        except Exception:
            _DURATION_CACHE[key] = None
    return _DURATION_CACHE[key]


def _demo_meta(p: Path, kind: str) -> dict:
    cat = kind.split(':')[0]
    scene, setting = _SCENES.get(_demo_display_name(p), ('Clip', ''))
    def meta(change, source, group, changes):
        return {'title': f'{scene}, {change}', 'subtitle': ' · '.join(x for x in (setting, source) if x), 'group': group,
                'changes': {'picture': changes[0], 'voice': changes[1]}}
    if 'eval_lavdf' in p.parts:
        return meta(_LAVDF_CHANGES[cat], 'Unfamiliar footage (LAV-DF)', 'unfamiliar', _CAT_CHANGES[cat])
    if cat in _CAT_TITLES:
        return meta(_CAT_TITLES[cat], 'built test clip', cat, _CAT_CHANGES[cat])
    if kind == 'FAKE clip':
        return meta('face replaced', '', 'picture_only', ('changed', 'absent'))
    if kind == 'REAL clip':
        return meta('unaltered', '', 'picture_only', ('genuine', 'absent'))
    if kind.startswith('COMPOSITE'):
        return meta('voice replaced', '', 'RVFA', ('genuine', 'changed'))
    if kind.startswith('NO-FACE'):
        return {'title': 'Test pattern, no face and no sound', 'subtitle': 'Nothing for the tool to check', 'group': 'no_verdict',
                'changes': {'picture': 'absent', 'voice': 'absent'}}
    # The steady-tone clip's picture has no recorded provenance, so its answer is stated as unknown rather than guessed.
    return meta('steady tone instead of speech', '', 'picture_only', ('unstated', 'absent'))


@app.get('/api/demo_clips')
def demo_clips():
    """Bundled demo clips plus the constructed evaluation clips (see _demo_items), with plain-language names (_demo_meta)."""
    out = []
    for i, (p, kind) in enumerate(_demo_items()):
        name = _demo_display_name(p)
        out.append({'demo_id': i, 'name': name, 'kind': kind, 'code': Path(name).stem, 'duration': _clip_duration(p),
                    'featured': FEATURED_DEMOS.index(name) if name in FEATURED_DEMOS else None,
                    'testing': TESTING_DEMOS.index(name) if name in TESTING_DEMOS else None, **_demo_meta(p, kind)})
    return out


def _new_job_from_path(path: Path, filename: str, duration: Optional[float] = None) -> dict:
    if duration is None:
        ffmpeg_exe = __import__('imageio_ffmpeg').get_ffmpeg_exe()
        duration, _fps = _probe_duration_and_fps(str(path), ffmpeg_exe)
    job_id = uuid.uuid4().hex
    job = {
        'id': job_id, 'filename': filename, 'path': str(path),
        'status': 'pending', 'duration': duration, 'verdict': None,
        'result': None, 'created_at': datetime.now(timezone.utc).isoformat(),
        'progress': 0, 'stage': None,
    }
    JOBS[job_id] = job
    return job


@app.get('/api/limits')
def limits():
    """Upload limits, so the page can refuse an oversized file before sending it."""
    return {'max_upload_mb': MAX_UPLOAD_MB, 'max_duration_s': MAX_DURATION_S,
            'allowed_extensions': list(ALLOWED_SUFFIXES)}


@app.middleware('http')
async def _reject_oversized_upload(request, call_next):
    """Backstop: refuse an upload whose declared size is already over the limit, before it is processed."""
    if request.method == 'POST' and request.url.path == '/api/upload':
        try:
            declared = int(request.headers.get('content-length', '0'))
        except ValueError:
            declared = 0
        if declared > MAX_UPLOAD_MB * 1024 * 1024 + 1_000_000:          # 1 MB slack for multipart framing
            return JSONResponse({'detail': f'File is larger than the {MAX_UPLOAD_MB} MB limit.'}, status_code=413)
    return await call_next(request)


@app.post('/api/upload')
async def upload(file: UploadFile = File(...)):
    suffix = Path(file.filename or '').suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(400, 'Unsupported file type: use MP4, MOV, AVI or MKV.')

    # Stream to disk in chunks with a hard size cap; a rejected upload never leaves a temp file behind.
    limit = MAX_UPLOAD_MB * 1024 * 1024
    written = 0
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix=UPLOAD_PREFIX) as tmp:
        tmp_path = Path(tmp.name)
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            written += len(chunk)
            if written > limit:
                break
            tmp.write(chunk)

    def _reject(status: int, message: str):
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status, message)

    if written > limit:
        _reject(413, f'File is larger than the {MAX_UPLOAD_MB} MB limit.')
    if written == 0:
        _reject(400, 'The uploaded file is empty.')

    ffmpeg_exe = __import__('imageio_ffmpeg').get_ffmpeg_exe()
    duration, _fps = _probe_duration_and_fps(str(tmp_path), ffmpeg_exe)
    if duration is None:
        _reject(400, 'This file could not be read as a video (unsupported codec or corrupt file).')
    if duration > MAX_DURATION_S:
        _reject(400, f'This clip is {duration:.0f} s long; the limit is {MAX_DURATION_S} s.')

    job = _new_job_from_path(tmp_path, file.filename, duration=duration)
    return {'id': job['id'], 'filename': job['filename'], 'duration': job['duration']}


def _sweep_stale_uploads():
    """Remove temp uploads (and their browser-preview transcodes) orphaned by an earlier server process. Only files this
    server created (UPLOAD_PREFIX) and only if older than STALE_UPLOAD_SECONDS, so a second running instance is not hurt."""
    cutoff = time.time() - STALE_UPLOAD_SECONDS
    for p in Path(tempfile.gettempdir()).glob(f'{UPLOAD_PREFIX}*'):
        try:
            if p.is_file() and p.stat().st_mtime < cutoff:
                p.unlink()
        except OSError:
            pass


_sweep_stale_uploads()


@app.post('/api/demo/{demo_id}')
def use_demo_clip(demo_id: int):
    items = _demo_items()
    if demo_id < 0 or demo_id >= len(items):
        raise HTTPException(404, 'No such demo clip.')
    p = items[demo_id][0]
    job = _new_job_from_path(p, _demo_display_name(p))
    return {'id': job['id'], 'filename': job['filename'], 'duration': job['duration']}


@app.get('/api/queue')
def queue():
    return [{'id': j['id'], 'filename': j['filename'], 'status': j['status'],
              'verdict': j['verdict'], 'duration': j['duration']}
             for j in sorted(JOBS.values(), key=lambda j: j['created_at'])]


@app.delete('/api/queue/{job_id}')
def remove_from_queue(job_id: str):
    """Removes a job from the (in-memory, session-lifetime) queue. Only
    deletes the underlying file if it's a temp upload (demo clips live in
    demo_videos/ and must never be deleted from disk)."""
    job = JOBS.pop(job_id, None)
    if job is None:
        raise HTTPException(404, 'No such job.')
    try:
        p = Path(job['path'])
        if p.exists() and str(p).startswith(tempfile.gettempdir()):
            p.unlink()
            (Path(tempfile.gettempdir()) / f'{p.stem}_preview.mp4').unlink(missing_ok=True)   # its browser-preview copy
    except Exception:
        pass
    return {'deleted': job_id}


@app.get('/api/video/{job_id}')
def get_video(job_id: str):
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(404, 'No such job.')
    preview_path = _previewable_video_path(job['path'])
    return FileResponse(preview_path, media_type='video/mp4')


@app.get('/api/result/{job_id}')
def get_result(job_id: str):
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(404, 'No such job.')
    if job['result'] is None:
        return JSONResponse({'status': job['status']}, status_code=202)
    return job['result']


@app.post('/api/analyze/{job_id}')
def analyze(job_id: str):
    """Start the pipeline in a background thread; poll /api/progress/{job_id}, then fetch /api/result/{job_id}."""
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(404, 'No such job.')
    if job['status'] == 'analyzing':
        return {'status': 'already_analyzing'}
    job['status'] = 'analyzing'
    job['progress'] = 0
    job['stage'] = 'starting'
    job['step'], job['faces_found'], job['speech'] = None, None, None
    threading.Thread(target=_run_analysis, args=(job_id,), daemon=True).start()
    return {'status': 'started'}


@app.get('/api/progress/{job_id}')
def get_progress(job_id: str):
    job = JOBS.get(job_id)
    if job is None:
        raise HTTPException(404, 'No such job.')
    return {'status': job['status'], 'progress': job.get('progress', 0),
             'stage': job.get('stage'),
             # for the six-step progress screen: which step is running, faces found so far, and whether speech was found
             'step': job.get('step'), 'faces_found': job.get('faces_found'), 'speech': job.get('speech')}


def _run_analysis_inner(job_id: str):
    """The pipeline, run off the request thread. Every stored field is a real model output or null with a reason;
    progress updates follow real stage transitions."""
    job = JOBS.get(job_id)
    if job is None:
        return
    path = job['path']

    # Stage 1: video -- real per-frame-crop progress via on_progress callback
    def _video_progress(fraction, text):
        job['progress'] = round(5 + fraction * 60)  # video spans 5%-65%
        m = re.search(r'(\d+) face', text or '')
        if m:
            job['faces_found'] = int(m.group(1))
        job['step'] = 'face_check' if (text or '').startswith('Scoring') else 'faces'

    job['stage'] = 'video'
    job['step'] = 'faces'
    mtcnn, model, device = get_video_models()
    gates = get_ood_gates()
    t0 = time.perf_counter()
    video_result = analyse_video_file(path, mtcnn, model, device, max_faces=20,
                                       on_progress=_video_progress, return_features=gates['video'] is not None)
    t_video = time.perf_counter() - t0
    video_ood = None
    if video_result is not None and gates['video'] is not None:
        video_ood = _ood_check('video', clip_video_distance(gates['video']['gate'], video_result['features']))

    anomalies = []
    face_png_b64 = None
    if video_result is None:
        # No detectable face. This is NOT an error: the audio branch may still give a single-modality verdict, and if it
        # cannot either, fuse() returns INCONCLUSIVE. Never a guessed video score.
        pass
    else:
        ffmpeg_exe = __import__('imageio_ffmpeg').get_ffmpeg_exe()
        _duration, fps = _probe_duration_and_fps(path, ffmpeg_exe)
        anomalies = _frame_anomalies(video_result['per_frame'], fps)

        # Real MTCNN face crop (the first successfully detected face), encoded
        # for direct embedding in the JSON response -- not a stand-in image.
        if video_result.get('sample_face') is not None:
            buf = io.BytesIO()
            video_result['sample_face'].save(buf, format='PNG')
            face_png_b64 = base64.b64encode(buf.getvalue()).decode('ascii')

    job['progress'] = 65
    job['stage'] = 'audio'
    job['step'] = 'speech'
    if video_result is None:
        job['faces_found'] = 0

    # Stage 2: audio
    audio = None
    wav_for_waveform = None
    p_audio_fake = None
    svm = get_audio_svm()
    if AUDIO_OK:
        t0 = time.perf_counter()
        wav = extract_audio_16k(path)
        t_decode = time.perf_counter() - t0
        job['progress'] = 75
        if wav is None or wav.size == 0:
            audio = {'no_audio': True}
            job['speech'] = 'no_track'
        else:
            wav_for_waveform = wav
            seconds = wav.size / 16000.0
            t_vad = 0.0
            vad = None
            gated = False
            if VAD_OK:
                t0 = time.perf_counter()
                vad = vad_analyse(wav)
                t_vad = time.perf_counter() - t0
                gated = not vad.has_speech
            job['progress'] = 82
            job['speech'] = 'none' if gated else 'found'
            if not gated:
                job['step'] = 'voice'
            if gated:
                audio = {'seconds': seconds, 'gated': True, 'gate_reason': vad.reason,
                          'speech_seconds': vad.speech_seconds, 't_decode': t_decode, 't_vad': t_vad}
            else:
                fe, enc, dev = get_audio_encoder()
                t0 = time.perf_counter()
                emb = embed_waveform(wav, fe, enc, dev)
                t_embed = time.perf_counter() - t0
                audio = {'seconds': seconds, 'dim': int(emb.shape[0]), 'gated': False,
                          'speech_seconds': vad.speech_seconds if vad else None,
                          't_decode': t_decode, 't_vad': t_vad, 't_embed': t_embed}
                if svm is not None:
                    t0 = time.perf_counter()
                    p_audio_fake = float(svm.spoof_probability(emb.reshape(1, -1))[0])
                    audio['t_svm'] = time.perf_counter() - t0
                if gates['audio'] is not None:
                    audio['ood'] = _ood_check('audio', float(gates['audio']['gate'].distance(emb)[0]))

    job['progress'] = 88
    job['stage'] = 'fusion'
    job['step'] = 'compare'

    # Stages 3-4: fusion. A withheld branch enters fusion as "no score", the same path as no face / no speech.
    p_video_raw = video_result['p_fake'] if video_result is not None else None
    video_withheld = bool(video_ood and video_ood['withheld'])
    if video_withheld:
        anomalies = []      # derived from the per-frame scores that were withheld; showing them would contradict the withholding
    audio_ood = audio.get('ood') if audio else None
    audio_withheld = bool(audio_ood and audio_ood['withheld'] and p_audio_fake is not None)
    p_audio_raw = p_audio_fake
    p_video_fake = None if video_withheld else p_video_raw
    p_audio_fake = None if audio_withheld else p_audio_raw
    fusion_result = fuse(p_video_fake, p_audio_fake)

    job['progress'] = 90
    job['stage'] = 'explanation'
    job['step'] = 'explain'

    # Stage 5: explanation (Llama 3 primary; faithfulness screen and labelled template as the safety net)
    explanation = _explanation_block(fusion_result, anomalies)
    withheld_notes = [f'The {b} score ({raw:.3f}) was not used: {ood["reason"].replace("score withheld: ", "")}.'
                      for b, flag, raw, ood in (('video', video_withheld, p_video_raw, video_ood),
                                                ('audio', audio_withheld, p_audio_raw, audio_ood)) if flag]
    explanation['withheld_note'] = ' '.join(withheld_notes) or None
    caution = [b for b, ood in (('video', video_ood), ('audio', audio_ood)) if ood and ood['unfamiliar'] and not ood['withheld']]
    explanation['caution_note'] = (
        'Caution: the ' + ' and the '.join(f'{b} input' for b in caution) + (' is' if len(caution) == 1 else ' are')
        + ' unlike the data the ' + ('model was' if len(caution) == 1 else 'models were') + ' trained on. On such input the scores have '
        'proved unreliable in testing (on the independent LAV-DF set every wrong verdict carried this flag), so treat this '
        'verdict with caution.') if caution else None
    if fusion_result.verdict == 'INCONCLUSIVE' and (video_withheld or audio_withheld) and explanation.get('source') == 'template':
        # The template's generic INCONCLUSIVE sentence says no branch produced a score; here scores WERE produced and withheld.
        why = [('the face footage was set aside as unlike what the tool learned from' if video_withheld else 'no face was found'),
               ('the speech was set aside as unlike what the tool learned from' if audio_withheld else
                ('no speech was found' if audio and audio.get('gated') else 'there is no usable sound'))]
        explanation['text'] = ('No verdict could be given: ' + ' and '.join(why) + ', so no score is left that the tool can stand '
                               'behind. This is an estimate, not proof: use it as one input to your own judgment.')
        explanation['fallback_reason'] = ('no score was left to verbalise after the out-of-domain gate withheld the unfamiliar '
                                          'branch scores')

    job['progress'] = 99

    # Overall score: the fused score on agreement; on disagreement, the higher branch (labelled as such). None if INCONCLUSIVE.
    overall_score = _overall_score(fusion_result, p_video_fake, p_audio_fake)

    result = {
        'id': job_id,
        'filename': job['filename'],
        'analyzed_at': datetime.now(timezone.utc).isoformat(),
        'verdict': fusion_result.verdict,
        'overall_score': round(overall_score, 4) if overall_score is not None else None,
        'video': None if video_result is None else {
            'p_fake': None if video_withheld else round(video_result['p_fake'], 4),
            'verdict': None if video_withheld else video_result['verdict'],
            'withheld': video_withheld,
            'p_fake_withheld': round(p_video_raw, 4) if video_withheld else None,
            'ood': video_ood,
            'model_name': video_model_summary()['name'],
            'n_faces': video_result['n_faces'],
            'per_frame': [round(x, 4) for x in video_result['per_frame']],
            'stage_time_s': round(t_video, 2),
            'sample_face_png_b64': face_png_b64,
        },
        'video_unavailable_reason': ('no face was detected in the sampled frames' if video_result is None
                                     else (video_ood['reason'] if video_withheld else None)),
        'audio': None if audio is None else {
            'available': not audio.get('no_audio', False),
            'gated': audio.get('gated', False),
            'gate_reason': audio.get('gate_reason'),
            'speech_seconds': audio.get('speech_seconds'),
            'seconds': audio.get('seconds'),
            'p_audio_fake': round(p_audio_fake, 4) if p_audio_fake is not None else None,
            'withheld': audio_withheld,
            'p_audio_fake_withheld': round(p_audio_raw, 4) if audio_withheld else None,
            'ood': audio_ood,
            'svm_status': ('measured' if p_audio_fake is not None
                            else ('withheld_out_of_domain' if audio_withheld
                                  else ('untrained' if svm is None else 'gated_or_no_audio'))),
            'waveform': _waveform_bars(wav_for_waveform) if wav_for_waveform is not None else None,
            'stage_time_s': round(audio.get('t_svm', 0), 3) if p_audio_raw is not None else None,
        },
        'fusion': {
            'disagreement': fusion_result.disagreement,
            'gap': round(fusion_result.gap, 4) if fusion_result.gap is not None else None,
            'threshold_T': THRESHOLD_T_DEFAULT,
            'implicated_modality': fusion_result.implicated_modality,
            'weights': fusion_result.weights,
            'threshold_T_source': THRESHOLD_T_SOURCE,
            'video_accuracy': VIDEO_ACCURACY_DEFAULT,
            'video_accuracy_measured': VIDEO_ACCURACY_IS_MEASURED,
            'video_accuracy_source': VIDEO_ACCURACY_SOURCE,
            'audio_accuracy': AUDIO_ACCURACY,
            'audio_accuracy_measured': AUDIO_ACCURACY_IS_MEASURED,
            'audio_accuracy_source': AUDIO_ACCURACY_SOURCE,
        },
        'explanation': explanation,
        'anomalies': anomalies,
        'models_ran': _models_ran_rows(video_result, audio, p_audio_raw, fusion_result,
                                        t_video, explanation, video_ood, audio_ood),
    }

    job['status'] = 'done'
    job['progress'] = 100
    job['stage'] = 'done'
    job['verdict'] = fusion_result.verdict
    job['result'] = result


def _run_analysis(job_id: str):
    """Thread entry point: the job always ends as 'done' or 'error' (with the exception), never stuck at 'analyzing'."""
    try:
        _run_analysis_inner(job_id)
    except Exception as e:                                   # noqa: BLE001 - the whole point is to catch everything
        traceback.print_exc()
        job = JOBS.get(job_id)
        if job is None:
            return
        message = str(e).strip().splitlines()[0][:200] if str(e).strip() else ''
        job['status'] = 'error'
        job['progress'] = 100
        job['stage'] = 'error'
        job['verdict'] = None
        job['result'] = {
            'id': job_id, 'filename': job.get('filename'), 'verdict': None,
            'error': f'Analysis failed ({type(e).__name__}' + (f': {message})' if message else ')')
                     + '. No verdict is produced rather than a guess.',
        }
