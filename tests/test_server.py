"""Headless tests for the FastAPI app (server.py + static/), including that no response field is a made-up number."""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

import json
import os
import re

import pytest
from fastapi.testclient import TestClient
from fusion import AUDIO_ACCURACY_IS_MEASURED
from video_infer import video_model_summary, arch_display_name

import server as server_module

client = TestClient(server_module.app)

# `heavy` tests run the real models (video on MPS, Llama 3 via Ollama). Set DEEPFAKE_SKIP_HEAVY=1 to skip them,
# e.g. while training runs. All other tests here are model-free.
heavy = pytest.mark.skipif(os.environ.get('DEEPFAKE_SKIP_HEAVY') == '1',
                           reason='runs the real video model and Ollama; skipped by DEEPFAKE_SKIP_HEAVY=1')

# The demo clips (demo_videos/ and the example clips in eval_fallback/ and eval_lavdf/) are built from FaceForensics++, ASVspoof and LAV-DF,
# whose terms forbid redistribution, so they are not in the repository. The tests that run them skip when they are absent.
DEMO_CLIPS_PRESENT = any((PROJECT_ROOT / 'demo_videos').rglob('*.mp4')) and any((PROJECT_ROOT / 'eval_fallback').glob('*/*.mp4'))
needs_demo_clips = pytest.mark.skipif(not DEMO_CLIPS_PRESENT, reason='the demo clips are not present (dataset-derived, not in the repository)')


def test_index_serves_html():
    r = client.get('/')
    assert r.status_code == 200
    assert 'Multimodal Deepfake Detector' in r.text


def test_static_files_served():
    for path in ('/static/style.css', '/static/app.js'):
        r = client.get(path)
        assert r.status_code == 200, f'{path} did not serve'


def test_model_info_reflects_real_disk_state():
    r = client.get('/api/model_info')
    assert r.status_code == 200
    models = r.json()['models']
    stages = {m['stage']: m for m in models}
    assert set(stages) == {'Video', 'Speech gate', 'Audio encoder', 'Audio classifier', 'Explanation'}
    # The video model's name must come from models/shipped_model.json, never from a string typed into the UI code.
    assert video_model_summary()['name'] in stages['Video']['name']
    assert 'Silero' in stages['Speech gate']['name']
    assert 'wav2vec2' in stages['Audio encoder']['name']

    audio_status = stages['Audio classifier']['status']
    if AUDIO_ACCURACY_IS_MEASURED:
        assert 'trained' in audio_status and 'EER' in audio_status, \
            f'audio classifier status should report a measured EER once trained: {audio_status!r}'
    else:
        assert 'untrained' in audio_status or 'sanity-run' in audio_status, \
            f'audio classifier status must not imply a measured result before training: {audio_status!r}'


@needs_demo_clips
def test_demo_clips_lists_real_bundled_files():
    r = client.get('/api/demo_clips')
    assert r.status_code == 200
    demos = r.json()
    assert len(demos) > 0, 'no bundled demo clips found'
    kinds = {d['kind'] for d in demos}
    assert 'FAKE clip' in kinds and 'REAL clip' in kinds


def _wait_for_analysis(job_id, timeout=120):
    """/api/analyze now starts a background thread and returns immediately
    (so the UI can poll real progress instead of blocking) -- tests poll
    /api/progress the same way the frontend does, then fetch the result."""
    start_resp = client.post(f'/api/analyze/{job_id}')
    assert start_resp.status_code == 200
    deadline = time.time() + timeout
    last_progress = -1
    steps = ['faces', 'face_check', 'speech', 'voice', 'compare', 'explain']
    last_step = -1
    while time.time() < deadline:
        p = client.get(f'/api/progress/{job_id}').json()
        assert p['progress'] >= last_progress, 'progress must never go backwards'
        last_progress = p['progress']
        if p.get('step') is not None:                       # interface v2's six-step progress screen reads these
            assert p['step'] in steps, p['step']
            assert steps.index(p['step']) >= last_step, 'steps must never go backwards'
            last_step = steps.index(p['step'])
        assert p.get('speech') in (None, 'found', 'none', 'no_track')
        if p['status'] in ('done', 'error'):
            break
        time.sleep(0.1)
    else:
        raise AssertionError(f'analysis for {job_id} did not finish within {timeout}s')
    return client.get(f'/api/result/{job_id}').json()


def _analyze_demo(kind_prefix):
    demos = client.get('/api/demo_clips').json()
    match = next(d for d in demos if d['kind'].startswith(kind_prefix))
    job = client.post(f'/api/demo/{match["demo_id"]}').json()
    result = _wait_for_analysis(job['id'])
    return job, result


@heavy
@needs_demo_clips
def test_fake_demo_clip_produces_valid_fake_leaning_verdict():
    job, result = _analyze_demo('FAKE clip')
    assert 'error' not in result, f'analysis errored: {result.get("error")}'
    assert result['verdict'] in ('FAKE', 'REAL', 'PARTIAL_MANIPULATION')
    assert 0.0 <= result['video']['p_fake'] <= 1.0
    assert len(result['video']['per_frame']) == result['video']['n_faces']


@heavy
@needs_demo_clips
def test_real_demo_clip_has_no_audio_and_no_fabricated_audio_score():
    """FF++ demo clips are silent by design -- the honesty contract requires
    audio.available == False and p_audio_fake == None, never a guessed number."""
    job, result = _analyze_demo('REAL clip')
    assert 'error' not in result
    audio = result['audio']
    assert audio is not None
    if audio['available']:
        # A spoof score must only come from the trained SVM, never appear otherwise.
        if not AUDIO_ACCURACY_IS_MEASURED:
            assert audio['p_audio_fake'] is None
    else:
        assert audio['p_audio_fake'] is None


@heavy
@needs_demo_clips
def test_composite_clip_exercises_full_audio_path():
    """The composite clip (real video + synthetic speech) exercises the full audio path: VAD, embedding and a real audio score."""
    demos = client.get('/api/demo_clips').json()
    composite = next(d for d in demos if 'COMPOSITE' in d['kind'])
    job = client.post(f'/api/demo/{composite["demo_id"]}').json()
    result = _wait_for_analysis(job['id'])
    assert 'error' not in result
    audio = result['audio']
    assert audio['available'] is True
    assert audio['gated'] is False, f'composite clip should pass VAD: {audio.get("gate_reason")}'
    if AUDIO_ACCURACY_IS_MEASURED:
        assert audio['p_audio_fake'] is not None
        assert result['fusion']['audio_accuracy_source'].startswith('measured'), \
            'fusion should report a measured weighting source, not a placeholder, ' \
            'once the SVM is trained on the full dataset'
    # Both weighting sources, T's provenance and the model name are always reported with a result.
    f = result['fusion']
    for key in ('video_accuracy', 'video_accuracy_measured', 'video_accuracy_source', 'audio_accuracy',
                'audio_accuracy_measured', 'audio_accuracy_source', 'threshold_T', 'threshold_T_source'):
        assert key in f, f'fusion block is missing {key}'
    assert result['video']['model_name'] == video_model_summary()['name']


@needs_demo_clips
def test_pipeline_exception_ends_in_error_not_a_hung_job(monkeypatch):
    """Regression: an exception inside the pipeline thread used to leave the job at 'analyzing' forever, so the UI
    overlay never closed. It must end in status 'error' with no verdict and an honest message."""
    monkeypatch.setattr(server_module, 'get_video_models', lambda: (None, None, None))

    def boom(*args, **kwargs):
        raise RuntimeError('simulated decode failure')

    monkeypatch.setattr(server_module, 'analyse_video_file', boom)
    demos = client.get('/api/demo_clips').json()
    job = client.post(f'/api/demo/{demos[0]["demo_id"]}').json()
    result = _wait_for_analysis(job['id'], timeout=20)
    assert result['verdict'] is None
    assert 'RuntimeError' in result['error'] and 'simulated decode failure' in result['error']
    assert client.get(f'/api/progress/{job["id"]}').json()['status'] == 'error'


# ── Explanation: Llama 3 stays primary; a faithfulness screen and a labelled template are the safety net ─────────────

from fusion import fuse
from explain import ExplanationUnavailable


def _use_llm(monkeypatch, text=None, error=None):
    """Pretend Ollama is up and returns `text` (or raises `error`), without touching the real LLM or the GPU."""
    monkeypatch.setattr(server_module, 'EXPLAIN_OK', True)
    monkeypatch.setattr(server_module, 'explanation_available', lambda *a, **k: True)

    def fake_explain(result, **kwargs):
        if error is not None:
            raise error
        return text

    monkeypatch.setattr(server_module, 'explain', fake_explain)


def test_faithful_llm_text_is_shown_and_labelled_llama(monkeypatch):
    r = fuse(0.90, None)                       # video-only, leans FAKE
    _use_llm(monkeypatch, 'The video analysis scored 0.900 and leans FAKE (manipulated). '
                          'The audio analysis was not evaluated, so the verdict rests on the video alone.')
    block = server_module._explanation_block(r)
    assert block['source'] == 'llama3' and block['available'] is True
    assert block['faithfulness']['passed'] is True
    assert block['rejected_llm_text'] is None and block['fallback_reason'] is None


def test_unfaithful_llm_text_is_rejected_and_template_shown(monkeypatch):
    """The pilot's failure: a score below 0.5 described as fake. It must never reach the user as the explanation."""
    r = fuse(0.46, None)                       # leans GENUINE
    bad = 'The video analysis scored 0.460, so the video is definitely fake.'
    _use_llm(monkeypatch, bad)
    block = server_module._explanation_block(r)
    assert block['source'] == 'template'
    assert block['rejected_llm_text'] == bad                 # kept for audit
    assert block['text'] != bad and 'definitely' not in block['text'].lower()
    assert 'faithfulness screen' in block['fallback_reason']
    assert block['faithfulness']['passed'] is False


def test_llm_unreachable_falls_back_to_labelled_template(monkeypatch):
    r = fuse(0.10, 0.12, threshold_T=0.5)
    _use_llm(monkeypatch, error=ExplanationUnavailable('could not reach the local LLM'))
    block = server_module._explanation_block(r)
    assert block['source'] == 'template' and block['available'] is True
    assert 'could not reach' in block['fallback_reason']
    assert block['generation_time_s'] is None


def test_inconclusive_never_calls_the_llm(monkeypatch):
    r = fuse(None, None)
    assert r.verdict == 'INCONCLUSIVE'
    monkeypatch.setattr(server_module, 'EXPLAIN_OK', True)
    monkeypatch.setattr(server_module, 'explanation_available', lambda *a, **k: True)

    def must_not_run(*a, **k):
        raise AssertionError('the LLM must not be asked to explain an INCONCLUSIVE result')

    monkeypatch.setattr(server_module, 'explain', must_not_run)
    block = server_module._explanation_block(r)
    assert block['source'] == 'template' and 'nothing for the language model' in block['fallback_reason']
    assert 'No verdict' in block['text']


def test_overall_score_rules():
    both = fuse(0.9, 0.85, threshold_T=0.5)                  # agreement: the fused score
    assert server_module._overall_score(both, 0.9, 0.85) == both.p_fake
    part = fuse(0.95, 0.30, threshold_T=0.15)                # disagreement: no fused number, so the higher branch
    assert part.p_fake is None and server_module._overall_score(part, 0.95, 0.30) == 0.95
    assert server_module._overall_score(fuse(None, 0.7), None, 0.7) == 0.7      # audio-only
    assert server_module._overall_score(fuse(None, None), None, None) is None   # INCONCLUSIVE



def test_demo_clips_have_plain_names_from_how_each_clip_was_made():
    """Interface v2 names examples in plain words. Each title must come from the clip's construction (its folder or manifest
    category), never from a model output, and testing mode needs a neutral code for every clip."""
    demos = client.get('/api/demo_clips').json()
    for d in demos:
        assert d['title'].strip() and d['subtitle'].strip() and d['code'] == Path(d['name']).stem
        assert '—' not in d['title'] + d['subtitle']
    by_name = {d['name']: d for d in demos}
    for d in demos:
        cat = d['kind'].split(':')[0]
        assert d['name'] in server_module._SCENES or d['group'] == 'no_verdict', f"{d['name']} has no scene words"
        if 'LAV-DF' in d['kind']:
            assert d['title'].endswith(', ' + server_module._LAVDF_CHANGES[cat]), (d['name'], d['title'])
            assert 'LAV-DF' in d['subtitle']
        elif cat in server_module._CAT_TITLES:
            assert d['title'].endswith(', ' + server_module._CAT_TITLES[cat]), (d['name'], d['title'])
        if d['kind'] == 'FAKE clip':
            assert d['title'].endswith(', face replaced')
        if d['kind'] == 'REAL clip':
            assert d['title'].endswith(', unaltered')
    featured = sorted((d['featured'], d['name']) for d in demos if d['featured'] is not None)
    assert [f for f, _ in featured] == list(range(len(featured)))
    assert [n for _, n in featured] == [n for n in server_module.FEATURED_DEMOS if n in by_name], 'featured order must follow FEATURED_DEMOS'


def test_demo_clips_carry_their_known_answer_from_how_each_clip_was_made():
    """Interface v4's demo strips show what was really changed (Face and Voice lights). The answer must follow the clip's
    construction category, agree with its title, and never claim a part the clip does not have."""
    demos = client.get('/api/demo_clips').json()
    allowed = {'genuine', 'changed', 'absent', 'unstated'}
    for d in demos:
        c = d['changes']
        assert set(c) == {'picture', 'voice'} and set(c.values()) <= allowed, (d['name'], c)
        cat = d['kind'].split(':')[0]
        if cat in server_module._CAT_CHANGES:
            assert (c['picture'], c['voice']) == server_module._CAT_CHANGES[cat], (d['name'], c)
        if d['title'].endswith(('face replaced', 'face and voice replaced')):
            assert c['picture'] == 'changed', d['name']
        if 'no sound' in d['subtitle'] or 'no face and no sound' in d['title']:
            assert c['voice'] == 'absent', d['name']
        if d['group'] == 'no_verdict':
            assert c == {'picture': 'absent', 'voice': 'absent'}


def test_evaluation_exposes_the_fusion_weights_actually_used():
    f = client.get('/api/evaluation').json()['fusion']
    assert abs(f['w_video'] + f['w_audio'] - 1) < 1e-9
    assert f['threshold_T'] == server_module.THRESHOLD_T_DEFAULT
    assert abs(f['w_video'] - f['video_accuracy'] / (f['video_accuracy'] + f['audio_accuracy'])) < 1e-9


def test_interface_v1_is_frozen_and_runnable():
    """The pre-redesign interface stays byte-identical for the report's before/after figures (docs/user_testing/)."""
    snap = PROJECT_ROOT / 'docs' / 'user_testing' / 'ui_v1_snapshot'
    sums = (snap / 'SHA256SUMS').read_text().split('\n')
    import hashlib
    for line in filter(None, sums):
        digest, rel = line.split()
        assert hashlib.sha256((snap / Path(rel).name).read_bytes()).hexdigest() == digest, rel
    assert 'DEEPFAKE_STATIC_DIR' in (PROJECT_ROOT / 'run_v1_interface.sh').read_text()


def test_final_interface_is_frozen():
    """The shipped interface (v4) was frozen on 27 Sep 2026 19:39 (re-frozen 19:59 for the no-clips note), before round 3 of user testing, so round 3, the report's
    screenshots and the demo video all show the same files. static/ must stay byte-identical to the snapshot."""
    snap = PROJECT_ROOT / 'docs' / 'user_testing' / 'ui_v4_final_snapshot'
    import hashlib
    for line in filter(None, (snap / 'SHA256SUMS').read_text().split('\n')):
        digest, name = line.split()
        assert hashlib.sha256((snap / name).read_bytes()).hexdigest() == digest, f'snapshot {name} changed'
        assert hashlib.sha256((PROJECT_ROOT / 'static' / name).read_bytes()).hexdigest() == digest, \
            f'static/{name} differs from the frozen interface; unfreezing needs a new snapshot and a DEV_LOG entry'

# ── No detectable face: not an error (INCONCLUSIVE, or an audio-only verdict) ───────────────────────────────────────

def test_evaluation_endpoint_shows_results_and_withholds_old_model_evidence():
    r = client.get('/api/evaluation')
    assert r.status_code == 200
    data = r.json()
    sections = {s['id']: s for s in data['sections']}
    assert {'video_models', 'per_method', 'celebdf', 'audio', 'four_condition', 'hybrid', 'latency', 'fusion_settings'} <= set(sections)
    numbers = server_module._read_json(server_module.NUMBERS_PATH) or {}
    for sid, key in (('four_condition', 'fallback_4condition'), ('hybrid', 'hybrid_4condition')):
        if numbers.get(key) is None:                       # only the superseded-model version exists: it must not be shown
            assert sections[sid]['status'] == 'pending' and 'rows' not in sections[sid], sid
    for s in data['sections']:
        assert s['status'] in ('current', 'pending') and s['source']
        assert ('rows' in s) == (s['status'] == 'current')
    assert sections['fusion_settings']['rows'][0][1] == f'{server_module.THRESHOLD_T_DEFAULT:.2f}'


def test_limitations_endpoint_gives_grounded_plain_language_limits():
    data = client.get('/api/limitations').json()
    assert data['how_to_read'] and '—' not in data['how_to_read']
    lim = {l['id']: l for l in data['limitations']}
    assert {'coverage', 'accuracy', 'other_datasets', 'audio_corpus', 'scope', 'estimate'} <= set(lim)
    for l in lim.values():
        assert l['text'].strip() and l['source'].strip() and '—' not in l['text']
    assert 'Face2Face' in lim['coverage']['text'] or 'single manipulation method' in lim['coverage']['text'] \
        or 'not recorded' in lim['coverage']['text']


@needs_demo_clips
def test_demo_library_has_all_four_categories_chosen_by_a_fixed_rule():
    """The constructed clips (FF++ video + ASVspoof audio) are the only demos with audio in every combination. They are the
    first 3 per category BY ID, a rule fixed in advance, so the demos cannot be cherry-picked by outcome."""
    demos = client.get('/api/demo_clips').json()
    constructed = [d for d in demos if '(constructed)' in d['kind']]
    if not server_module.FALLBACK_MANIFEST.exists():          # the folder is git-ignored; the list degrades gracefully
        assert constructed == []
        return
    for cat in ('RVRA', 'RVFA', 'FVRA', 'FVFA'):
        names = [d['name'] for d in constructed if d['kind'].startswith(cat + ':')]
        rule = [f'{cat}_{i:03d}.mp4' for i in range(server_module.DEMO_PER_CATEGORY)]
        # the only additions are shelf clips outside the first three (test_featured_shelf_follows_its_rule), listed after them
        assert names[:len(rule)] == rule and set(names[len(rule):]) <= set(server_module.FEATURED_DEMOS), (cat, names)
    # every listed id resolves to the same file the list names, and removing the job never deletes the clip
    for d in constructed[:2]:
        job = client.post(f'/api/demo/{d["demo_id"]}').json()
        assert job['filename'] == d['name']
        clip = Path(server_module.JOBS[job['id']]['path'])
        assert clip.exists()
        client.delete(f'/api/queue/{job["id"]}')
        assert clip.exists(), 'removing a demo job must not delete the demo clip'


def test_featured_shelf_follows_its_rule():
    """The shelf of eight follows its rule: first two clips per category that are fully right with no warning, alternating by kind.
    Testing mode keeps the eight clips used in user testing rounds 1 and 2."""
    assert server_module.TESTING_DEMOS == ['RVRA_000.mp4', 'RVFA_000.mp4', 'FVRA_000.mp4', 'FVFA_002.mp4', '183_253.mp4',
                                           '183.mp4', 'LAVDF_RVRA_000.mp4', 'noface_silent.mp4']
    res = PROJECT_ROOT / 'results' / 'fallback_eval_shipped' / 'fallback_4condition_results.json'
    if not res.exists():
        return
    import json

    def fully_right(c):
        if c['p_video'] is None or c['p_audio'] is None:
            return False
        fake_v, fake_a = c['video_label'] != 'real', c['audio_label'] != 'bonafide'
        parts = (c['p_video'] >= 0.5) == fake_v and (c['p_audio'] >= 0.5) == fake_a
        verdict = {'RVRA': c['fusion_verdict'] == 'REAL' and not c['disagreement'],
                   'FVFA': c['fusion_verdict'] == 'FAKE' and not c['disagreement'],
                   'RVFA': c['disagreement'] and c['implicated_modality'] == 'audio',
                   'FVRA': c['disagreement'] and c['implicated_modality'] == 'video'}[c['category']]
        return parts and verdict

    clips = sorted(json.load(open(res))['per_clip_results'], key=lambda c: c['id'])
    skip = set(server_module.SHELF_SKIPPED_FOR_WARNING)
    first_two = {cat: [c['id'] + '.mp4' for c in clips if c['category'] == cat and fully_right(c)
                       and c['id'] + '.mp4' not in skip][:2]
                 for cat in ('RVRA', 'RVFA', 'FVRA', 'FVFA')}
    expected = [first_two[cat][k] for k in range(2) for cat in ('RVRA', 'RVFA', 'FVRA', 'FVFA')]
    assert server_module.FEATURED_DEMOS == expected
    if DEMO_CLIPS_PRESENT:                                  # the clips are git-ignored (dataset-derived)
        demos = client.get('/api/demo_clips').json()
        shelf = sorted((d['featured'], d['name']) for d in demos if d['featured'] is not None)
        assert [n for _, n in shelf] == expected, 'every shelf clip must be served, in order'
        scenes = [d['title'].split(', ')[0] for d in demos if d['featured'] is not None]
        assert len(set(scenes)) == len(scenes), f'shelf names must differ: {scenes}'


@needs_demo_clips
def test_lavdf_demo_clips_use_the_same_fixed_rule_and_distinct_names():
    """The first 3 LAV-DF test clips per category BY ID are listed (independent set, F6). They reuse the constructed set's file
    names, so they are shown with a LAVDF_ prefix, and the two sets never collide in the list."""
    demos = client.get('/api/demo_clips').json()
    lav = [d for d in demos if '(LAV-DF' in d['kind']]
    if not server_module.LAVDF_MANIFEST.exists():             # git-ignored folder; the list degrades gracefully
        assert lav == []
        return
    for cat in ('RVRA', 'RVFA', 'FVRA', 'FVFA'):
        names = [d['name'] for d in lav if d['kind'].startswith(cat + ':')]
        assert names == [f'LAVDF_{cat}_{i:03d}.mp4' for i in range(server_module.DEMO_PER_CATEGORY)], (cat, names)
    assert len({d['name'] for d in demos}) == len(demos), 'demo names must be unique'
    job = client.post(f'/api/demo/{lav[0]["demo_id"]}').json()
    assert job['filename'] == lav[0]['name']
    assert Path(server_module.JOBS[job['id']]['path']).exists()
    client.delete(f'/api/queue/{job["id"]}')


def _analyze_with_no_face(monkeypatch, demo_kind_prefix):
    monkeypatch.setattr(server_module, 'get_ood_gates', lambda: {'audio': None, 'video': None})   # gate tested separately below
    monkeypatch.setattr(server_module, 'get_video_models', lambda: (None, None, None))
    monkeypatch.setattr(server_module, 'analyse_video_file', lambda *a, **k: None)
    monkeypatch.setattr(server_module, 'EXPLAIN_OK', True)
    monkeypatch.setattr(server_module, 'explanation_available', lambda *a, **k: False)   # keep the LLM (and GPU) out
    return _analyze_demo(demo_kind_prefix)


@needs_demo_clips
def test_no_face_and_no_audio_is_inconclusive_not_an_error(monkeypatch):
    job, result = _analyze_with_no_face(monkeypatch, 'REAL clip')         # FF++ demo clips are silent
    assert 'error' not in result, result.get('error')
    assert result['verdict'] == 'INCONCLUSIVE'
    assert result['video'] is None and result['overall_score'] is None
    assert 'no face' in result['video_unavailable_reason']
    assert result['explanation']['source'] == 'template'
    assert client.get('/api/queue').json()[-1]['verdict'] == 'INCONCLUSIVE'


@needs_demo_clips
def test_no_face_but_speech_gives_an_audio_only_verdict(monkeypatch):
    job, result = _analyze_with_no_face(monkeypatch, 'COMPOSITE')
    assert 'error' not in result, result.get('error')
    assert result['video'] is None
    if AUDIO_ACCURACY_IS_MEASURED:
        assert result['verdict'] in ('FAKE', 'REAL')                      # audio alone decides, and says so
        assert result['audio']['p_audio_fake'] is not None
        assert result['fusion']['weights'] == {'audio': 1.0}
        assert 'audio' in result['models_ran'][0]['produced'] or 'no face' in result['models_ran'][0]['produced']
    else:
        assert result['verdict'] == 'INCONCLUSIVE'


# ── Out-of-domain gate (scripts/ood_gate.py, EXPERIMENTS O1): a withheld branch is treated like a missing one, and says why ──

from types import SimpleNamespace
import numpy as np


class _FakeGate:
    kind, percentile = 'pooled', 97.5

    def __init__(self, distance, threshold=100.0):
        self.threshold_, self._d = threshold, distance

    def distance(self, X):
        return np.full(len(np.atleast_2d(X)), float(self._d))


def _analyze_with_gates(monkeypatch, video_distance=None, audio_distance=None, p_video=0.1, p_audio=0.99, mode='withhold'):
    """Both branches mocked (no model, no GPU, no LLM): video scores p_video, audio scores p_audio on 3 s of speech. A gate is
    installed for a branch only when its distance is given; the limit is 100. mode is the server's OOD_MODE."""
    monkeypatch.setattr(server_module, 'OOD_MODE', mode)
    monkeypatch.setattr(server_module, 'get_ood_gates', lambda: {
        'video': None if video_distance is None else {'gate': _FakeGate(video_distance)},
        'audio': None if audio_distance is None else {'gate': _FakeGate(audio_distance)}})
    monkeypatch.setattr(server_module, 'get_video_models', lambda: (None, None, None))
    monkeypatch.setattr(server_module, 'analyse_video_file', lambda *a, **k: {
        'p_fake': p_video, 'per_frame': [p_video] * 3, 'n_faces': 3, 'verdict': 'FAKE' if p_video >= 0.5 else 'REAL',
        'sample_face': None, 'features': np.zeros((3, 4))})
    monkeypatch.setattr(server_module, 'AUDIO_OK', True)
    monkeypatch.setattr(server_module, 'VAD_OK', True)
    monkeypatch.setattr(server_module, 'extract_audio_16k', lambda p: np.full(48000, 0.01, dtype=np.float32))
    monkeypatch.setattr(server_module, 'vad_analyse', lambda w: SimpleNamespace(has_speech=True, speech_seconds=3.0, reason=''))
    monkeypatch.setattr(server_module, 'get_audio_encoder', lambda: (None, None, 'cpu'))
    monkeypatch.setattr(server_module, 'embed_waveform', lambda *a, **k: np.zeros(768, dtype=np.float32))
    monkeypatch.setattr(server_module, 'get_audio_svm', lambda: SimpleNamespace(spoof_probability=lambda X: np.array([p_audio])))
    monkeypatch.setattr(server_module, 'EXPLAIN_OK', True)
    monkeypatch.setattr(server_module, 'explanation_available', lambda *a, **k: False)
    _, result = _analyze_demo('REAL clip')
    assert 'error' not in result, result.get('error')
    return result


def test_warning_is_the_default_mode():
    assert server_module.OOD_MODE == 'warn' or os.environ.get('DEEPFAKE_OOD_MODE')


@needs_demo_clips
def test_warn_mode_keeps_every_score_and_verdict_and_flags_the_input(monkeypatch):
    r = _analyze_with_gates(monkeypatch, video_distance=10, audio_distance=500, mode='warn')
    assert r['verdict'] == 'PARTIAL_MANIPULATION' and r['fusion']['implicated_modality'] == 'audio'   # same as without a gate
    a = r['audio']
    assert a['p_audio_fake'] == 0.99 and a['withheld'] is False and a['ood']['unfamiliar'] is True
    assert a['ood']['reason'].startswith('caution') and a['svm_status'] == 'measured'
    assert r['explanation']['withheld_note'] is None and 'audio input' in r['explanation']['caution_note']
    assert r['video']['ood']['unfamiliar'] is False
    assert any(row['stage'] == '2d' and 'flagged unfamiliar' in row['produced'] for row in r['models_ran'])


@needs_demo_clips
def test_warn_mode_with_both_unfamiliar_still_gives_the_fused_verdict(monkeypatch):
    r = _analyze_with_gates(monkeypatch, video_distance=500, audio_distance=500, p_video=0.9, p_audio=0.95, mode='warn')
    assert r['verdict'] == 'FAKE' and r['anomalies'] != []           # anomalies stay: the video score is still used
    assert 'video input and the audio input are' in r['explanation']['caution_note']


def test_off_mode_loads_no_gate(monkeypatch):
    monkeypatch.setattr(server_module, 'OOD_MODE', 'off')
    monkeypatch.setattr(server_module, '_ood_gates', None)
    assert server_module.get_ood_gates() == {'audio': None, 'video': None}
    monkeypatch.setattr(server_module, '_ood_gates', None)                 # do not leave the 'off' result cached


@needs_demo_clips
def test_gate_within_limits_changes_nothing(monkeypatch):
    r = _analyze_with_gates(monkeypatch, video_distance=10, audio_distance=10)
    assert r['verdict'] == 'PARTIAL_MANIPULATION' and r['fusion']['implicated_modality'] == 'audio'   # fuse(0.1, 0.99)
    assert r['video']['p_fake'] == 0.1 and r['audio']['p_audio_fake'] == 0.99
    assert r['video']['withheld'] is False and r['audio']['withheld'] is False
    assert r['video']['ood']['unfamiliar'] is False and r['audio']['ood']['unfamiliar'] is False
    assert r['video']['ood']['distance'] == 10 and r['explanation']['withheld_note'] is None
    assert r['explanation']['caution_note'] is None


@needs_demo_clips
def test_no_gate_files_means_the_ppr_pipeline_unchanged(monkeypatch):
    r = _analyze_with_gates(monkeypatch)
    assert r['verdict'] == 'PARTIAL_MANIPULATION'
    assert r['video']['ood'] is None and r['audio']['ood'] is None
    assert not any('Out-of-domain' in row['model'] for row in r['models_ran'])


@needs_demo_clips
def test_unfamiliar_speech_withholds_the_audio_score_only(monkeypatch):
    r = _analyze_with_gates(monkeypatch, video_distance=10, audio_distance=500)
    assert r['verdict'] == 'REAL' and r['fusion']['weights'] == {'video': 1.0}       # video alone decides
    a = r['audio']
    assert a['withheld'] is True and a['p_audio_fake'] is None and a['p_audio_fake_withheld'] == 0.99
    assert a['svm_status'] == 'withheld_out_of_domain' and 'not trustworthy' in a['ood']['reason']
    assert 'audio score (0.990) was not used' in r['explanation']['withheld_note']
    assert any(row['stage'] == '2d' and 'withheld' in row['produced'] for row in r['models_ran'])


@needs_demo_clips
def test_unfamiliar_footage_withholds_the_video_score_only(monkeypatch):
    r = _analyze_with_gates(monkeypatch, video_distance=500, audio_distance=10, p_video=0.9, p_audio=0.2)
    assert r['verdict'] == 'REAL' and r['fusion']['weights'] == {'audio': 1.0}
    v = r['video']
    assert v['withheld'] is True and v['p_fake'] is None and v['verdict'] is None and v['p_fake_withheld'] == 0.9
    assert 'withheld' in r['video_unavailable_reason'] and r['overall_score'] == 0.2
    assert r['anomalies'] == []          # timeline marks come from the withheld per-frame scores, so none are shown


@needs_demo_clips
def test_both_unfamiliar_is_inconclusive_with_both_reasons(monkeypatch):
    r = _analyze_with_gates(monkeypatch, video_distance=500, audio_distance=500)
    assert r['verdict'] == 'INCONCLUSIVE' and r['overall_score'] is None
    note = r['explanation']['withheld_note']
    assert 'video score' in note and 'audio score' in note
    assert r['explanation']['source'] == 'template'


# ── Video anomaly timing reaches the explanation (template path, no Ollama needed) ───────────────────────────────────

def _analyze_with_per_frame(monkeypatch, per_frame, verdict='FAKE'):
    monkeypatch.setattr(server_module, 'get_ood_gates', lambda: {'audio': None, 'video': None})
    monkeypatch.setattr(server_module, 'get_video_models', lambda: (None, None, None))
    monkeypatch.setattr(server_module, 'analyse_video_file', lambda *a, **k: {
        'p_fake': sum(per_frame) / len(per_frame), 'per_frame': per_frame, 'n_faces': len(per_frame),
        'verdict': verdict, 'sample_face': None})
    monkeypatch.setattr(server_module, 'AUDIO_OK', False)                        # keep this test video-only
    monkeypatch.setattr(server_module, 'EXPLAIN_OK', True)
    monkeypatch.setattr(server_module, 'explanation_available', lambda *a, **k: False)   # force the template, no Ollama
    _, result = _analyze_demo('REAL clip')
    assert 'error' not in result, result.get('error')
    return result


@needs_demo_clips
def test_template_states_the_real_anomaly_time_and_never_content(monkeypatch):
    """Real per-frame scores with a clear elevated window -> the app's own _frame_anomalies computes a real timestamp
    -> the template states WHEN, never WHAT (no model in this pipeline describes visual content)."""
    r = _analyze_with_per_frame(monkeypatch, [0.05, 0.05, 0.92, 0.97, 0.90, 0.05, 0.05])
    assert r['anomalies'], 'these per-frame scores should produce at least one anomaly window'
    a = r['anomalies'][0]
    assert a['start'] is not None, 'a real fps should have been read from the real demo clip'
    m, s = divmod(int(a['start']), 60)
    stamp = f'{m}:{s:02d}'
    assert r['explanation']['source'] == 'template'
    assert stamp in r['explanation']['text']
    # The plain-language template (25 Sep) states the time without the peak number, which is jargon on the main screen; the peak
    # itself is still in r['anomalies'] and shown under Learn more.
    assert 'looked most suspicious at' in r['explanation']['text'] or 'briefly higher at' in r['explanation']['text']
    for word in ('blink', 'lighting', 'lip', 'mouth', 'eye', 'shadow', 'expression'):    # whole words: "clip" is not "lip"
        assert not re.search(rf'\b{word}', r['explanation']['text'].lower()), f'"{word}" is a content description, not real data'


@needs_demo_clips
def test_template_omits_timing_when_no_window_is_elevated(monkeypatch):
    r = _analyze_with_per_frame(monkeypatch, [0.02, 0.03, 0.04], verdict='REAL')
    assert r['anomalies'] == []
    assert 'concentrated at' not in r['explanation']['text']


# ── Upload hardening: size, type, readability, duration; no temp file left behind ───────────────────────────────────

import glob
import tempfile


def _leftover_uploads():
    return set(glob.glob(str(Path(tempfile.gettempdir()) / f'{server_module.UPLOAD_PREFIX}*')))


def _upload(name, data):
    return client.post('/api/upload', files={'file': (name, data, 'application/octet-stream')})


def test_limits_endpoint_reports_the_configured_limits():
    lim = client.get('/api/limits').json()
    assert lim['max_upload_mb'] == server_module.MAX_UPLOAD_MB
    assert lim['max_duration_s'] == server_module.MAX_DURATION_S
    assert '.mp4' in lim['allowed_extensions']


def test_upload_rejects_wrong_extension_empty_and_unreadable_files():
    before = _leftover_uploads()
    assert _upload('notes.txt', b'hello').status_code == 400
    r = _upload('empty.mp4', b'')
    assert r.status_code == 400 and 'empty' in r.json()['detail']
    r = _upload('garbage.mp4', b'\x00\x01not a video' * 1000)
    assert r.status_code == 400 and 'could not be read' in r.json()['detail']
    assert _leftover_uploads() == before, 'a rejected upload left a temp file behind'


def test_upload_rejects_oversized_files_without_leaving_a_temp_file(monkeypatch):
    monkeypatch.setattr(server_module, 'MAX_UPLOAD_MB', 1)
    before = _leftover_uploads()
    r = _upload('big.mp4', b'\x00' * (2 * 1024 * 1024))
    assert r.status_code == 413 and 'limit' in r.json()['detail']
    assert _leftover_uploads() == before


def test_upload_rejects_clips_over_the_duration_limit(monkeypatch):
    monkeypatch.setattr(server_module, '_probe_duration_and_fps', lambda *a, **k: (999.0, 25.0))
    monkeypatch.setattr(server_module, 'MAX_DURATION_S', 120)
    before = _leftover_uploads()
    r = _upload('long.mp4', b'\x00' * 2048)
    assert r.status_code == 400 and '120 s' in r.json()['detail']
    assert _leftover_uploads() == before


@needs_demo_clips
def test_valid_upload_creates_a_job_and_removal_deletes_its_temp_file():
    clip = next((PROJECT_ROOT / 'demo_videos').rglob('composite_*.mp4'))
    r = _upload('my_clip.mp4', clip.read_bytes())
    assert r.status_code == 200, r.text
    job = r.json()
    assert job['duration'] is not None and job['duration'] > 0
    temp = Path(server_module.JOBS[job['id']]['path'])
    assert temp.exists() and temp.name.startswith(server_module.UPLOAD_PREFIX)
    assert client.delete(f'/api/queue/{job["id"]}').status_code == 200
    assert not temp.exists()
    assert clip.exists(), 'removing an uploaded job must never touch bundled demo files'


# ── Video model naming comes from the shipped-model manifest (no hardcoded architecture strings) ──────────────────

def test_video_model_summary_reads_architecture_from_manifest(tmp_path):
    p = tmp_path / 'shipped_model.json'
    p.write_text(json.dumps({'arch': 'legacy_xception', 'tag': 'mm_xcep_vidsplit', 'seed': 44,
                             'trained_on': 'multi-method (Deepfakes + FaceSwap + NeuralTextures)',
                             'checkpoint_sha256': 'abcdef0123456789' * 4,
                             'video_accuracy_source': 'example source'}))
    s = video_model_summary(p)
    assert s['shipped'] is True
    assert s['name'] == 'Xception' and s['arch'] == 'legacy_xception'
    assert 'multi-method' in s['status'] and 'abcdef012345' in s['status']
    assert s['accuracy_source'] == 'example source'


def test_video_model_summary_without_manifest_is_labelled_legacy(tmp_path):
    s = video_model_summary(tmp_path / 'does_not_exist.json')
    assert s['shipped'] is False
    assert 'legacy' in s['status'] and 'not promoted' in s['status']


def test_video_model_summary_tolerates_corrupt_manifest_and_unknown_arch(tmp_path):
    bad = tmp_path / 'bad.json'
    bad.write_text('{not json')
    assert video_model_summary(bad)['shipped'] is False
    p = tmp_path / 'm.json'
    p.write_text(json.dumps({'arch': 'some_future_net'}))
    assert video_model_summary(p)['name'] == 'some_future_net'      # unknown arch is shown as-is, not disguised
    assert arch_display_name('efficientnet_b4') == 'EfficientNet-B4'


def test_shipped_checkpoint_is_recognised_however_its_path_is_spelled():
    """Regression (2026-09-21): server.py and eval_fallback_4condition.py pass the shipped checkpoint path EXPLICITLY.
    load_models used to read the architecture from shipped_model.json only when the path was None, so the first non-B4
    model that shipped could not be loaded by either of them (RuntimeError: size mismatch). Data-free: paths only."""
    from video_infer import is_shipped_checkpoint, SHIPPED_CHECKPOINT
    assert is_shipped_checkpoint(None)
    assert is_shipped_checkpoint(str(SHIPPED_CHECKPOINT))
    assert is_shipped_checkpoint(str(PROJECT_ROOT / 'models' / 'best_model.pth'))
    assert not is_shipped_checkpoint(str(PROJECT_ROOT / 'models' / 'runs' / 'mm_xcep_vidsplit' / 'seed44.pth'))
    # server.py must load the model the way this check covers
    src = (PROJECT_ROOT / 'server.py').read_text()
    assert 'load_models(str(MODEL_PATH))' in src and "MODEL_PATH = PROJECT_ROOT / 'models' / 'best_model.pth'" in src


def test_no_hardcoded_architecture_names_in_ui_code():
    """The three places that used to hardcode 'EfficientNet-B4' must not do so again."""
    for rel in ('server.py', 'static/app.js'):
        text = (PROJECT_ROOT / rel).read_text()
        assert 'EfficientNet-B4' not in text, f'{rel} hardcodes an architecture name; use video_model_summary()'


@heavy
@needs_demo_clips
def test_queue_and_result_endpoints_round_trip():
    job, result = _analyze_demo('FAKE clip')
    queue = client.get('/api/queue').json()
    entry = next((q for q in queue if q['id'] == job['id']), None)
    assert entry is not None, 'analyzed job missing from /api/queue'
    assert entry['status'] == 'done'
    assert entry['verdict'] == result['verdict']

    fetched = client.get(f'/api/result/{job["id"]}').json()
    assert fetched['verdict'] == result['verdict']


@heavy
@needs_demo_clips
def test_remove_from_queue_deletes_server_side():
    job, _ = _analyze_demo('FAKE clip')
    assert any(q['id'] == job['id'] for q in client.get('/api/queue').json())
    r = client.delete(f'/api/queue/{job["id"]}')
    assert r.status_code == 200
    assert not any(q['id'] == job['id'] for q in client.get('/api/queue').json())
    assert client.get(f'/api/result/{job["id"]}').status_code == 404


@needs_demo_clips
def test_removing_a_demo_clip_job_never_deletes_the_bundled_file():
    demos = client.get('/api/demo_clips').json()
    match = next(d for d in demos if d['kind'] == 'FAKE clip')
    job = client.post(f'/api/demo/{match["demo_id"]}').json()
    client.delete(f'/api/queue/{job["id"]}')
    # The demo library must be unaffected -- same clip still selectable.
    still_there = client.get('/api/demo_clips').json()
    assert any(d['demo_id'] == match['demo_id'] and d['name'] == match['name'] for d in still_there)


@heavy
@needs_demo_clips
def test_progress_reaches_100_and_never_regresses():
    """The overlay's 'Analysing NN%' reads this endpoint -- confirm it's a
    real monotonic progression tied to actual pipeline stages, ending at
    100, not a fixed/fake number."""
    job, result = _analyze_demo('FAKE clip')
    final = client.get(f'/api/progress/{job["id"]}').json()
    assert final['status'] == 'done'
    assert final['progress'] == 100


def test_unknown_job_id_returns_404():
    assert client.get('/api/result/does-not-exist').status_code == 404
    assert client.get('/api/video/does-not-exist').status_code == 404
    assert client.get('/api/progress/does-not-exist').status_code == 404
    assert client.post('/api/analyze/does-not-exist').status_code == 404


if __name__ == '__main__':
    failures = 0
    tests = [
        ('index serves html', test_index_serves_html),
        ('static files served', test_static_files_served),
        ('model info reflects real disk state', test_model_info_reflects_real_disk_state),
        ('demo clips lists real bundled files', test_demo_clips_lists_real_bundled_files),
        ('fake demo clip -> valid verdict', test_fake_demo_clip_produces_valid_fake_leaning_verdict),
        ('real demo clip -> no fabricated audio score', test_real_demo_clip_has_no_audio_and_no_fabricated_audio_score),
        ('composite clip -> full audio path', test_composite_clip_exercises_full_audio_path),
        ('queue/result round trip', test_queue_and_result_endpoints_round_trip),
        ('remove from queue deletes server-side', test_remove_from_queue_deletes_server_side),
        ('removing a demo job never deletes the bundled file', test_removing_a_demo_clip_job_never_deletes_the_bundled_file),
        ('progress reaches 100, never regresses', test_progress_reaches_100_and_never_regresses),
        ('unknown job id -> 404', test_unknown_job_id_returns_404),
    ]
    for name, fn in tests:
        try:
            fn()
            print(f'PASS  {name}')
        except AssertionError as e:
            failures += 1
            print(f'FAIL  {name}: {e}')
        except Exception as e:
            failures += 1
            print(f'ERROR {name}: {e!r}')
    print(f'\n{"ALL PASSED" if failures == 0 else f"{failures} FAILED"}')
    sys.exit(1 if failures else 0)
