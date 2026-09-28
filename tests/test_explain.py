"""Grounding tests for the explanation layer (scores stated correctly, unevaluated branches reported as such).
Not a quality evaluation; skipped when no local Ollama server is reachable."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from fusion import fuse  # noqa: E402
from explain import (  # noqa: E402
    assess, build_structured_input, build_prompt, explain, explanation_available, format_anomaly_timing,
)
from explain_checks import check_faithfulness  # noqa: E402

ANOMALY = [{'start': 4.0, 'end': 5.0, 'peak_score': 0.95, 'label': 'Elevated visual manipulation likelihood',
           'severity': 'high'}]

LLM_UP = explanation_available()
SKIP_REASON = 'local Ollama server / model not reachable'

try:
    import pytest
    pytestmark = pytest.mark.skipif(not LLM_UP, reason=SKIP_REASON)
except ImportError:      # standalone run without pytest installed
    pytest = None


def _score_mentioned(text: str, score: float) -> bool:
    """True if `text` states `score` in any usual form (0.950, 0.95, 95%, 95 percent)."""
    candidates = {
        f'{score:.3f}', f'{score:.2f}', f'{score:g}',
        f'{score * 100:.1f}', f'{score * 100:.0f}',
    }
    return any(c in text for c in candidates)


# ── Structured input: the constraint boundary (no LLM needed) ────────────────

def test_structured_input_exposes_only_specified_fields():
    """Only the specified fields reach the model; weights, raw gap and notes must not leak."""
    si = build_structured_input(fuse(0.95, 0.30))
    assert set(si) == {'verdict', 'video_score', 'audio_score',
                       'video_assessment', 'audio_assessment', 'video_anomaly_timing',
                       'disagreement', 'implicated_modality'}


# ── The 0.5 comparison, now in code (see explain.assess) and therefore testable ──

def test_assess_above_threshold_leans_fake():
    assert 'FAKE' in assess(0.51)
    assert 'FAKE' in assess(0.999)


def test_assess_below_threshold_leans_genuine():
    assert 'GENUINE' in assess(0.49)
    assert 'GENUINE' in assess(0.001)


def test_assess_handles_boundary_and_missing():
    assert 'boundary' in assess(0.5)
    assert assess(None) == 'was not evaluated'


def test_assess_never_calls_a_sub_half_score_fake():
    """The exact failure the pilot caught: 0.46 and 0.11 described as fake."""
    for score in (0.46, 0.11, 0.20, 0.150, 0.490):
        assert 'FAKE' not in assess(score), \
            f'score {score} below 0.5 was assessed as fake'


def test_structured_input_reports_missing_audio_as_not_evaluated():
    """The live pipeline state: audio SVM untrained -> p_audio=None. This must
    surface as 'not evaluated', never as a number."""
    si = build_structured_input(fuse(0.83, None))
    assert si['audio_score'] == 'not evaluated'


def test_prompt_contains_the_no_fabrication_constraint():
    prompt = build_prompt(fuse(0.83, None))
    assert 'ONLY the fields above' in prompt
    assert 'never as certainties' in prompt


def test_prompt_carries_the_precomputed_direction():
    """The model must be handed the direction, not asked to derive it."""
    prompt = build_prompt(fuse(0.60, 0.46))
    assert 'leans FAKE' in prompt and 'leans GENUINE' in prompt


def test_explain_does_not_call_a_sub_half_audio_score_fake():
    """Regression for the pilot's finding: with video 0.60 / audio 0.46 the audio must be described as genuine-leaning."""
    text = explain(fuse(0.60, 0.46)).lower()
    assert 'audio' in text
    idx = text.find('audio')
    tail = text[idx:idx + 200]
    assert 'genuine' in tail or 'real' in tail or 'authentic' in tail, \
        f'audio (0.46, below 0.5) was not described as genuine-leaning: {text!r}'


# ── Generated output: grounding against the structured input ────────────────

def test_explain_video_only_states_the_real_score():
    r = fuse(0.83, None)
    text = explain(r)
    assert text.strip(), 'explanation was empty'
    assert _score_mentioned(text, 0.83), \
        f'video score 0.83 not faithfully stated in: {text!r}'


def test_explain_video_only_says_audio_not_evaluated():
    """The key anti-fabrication check: with no trained audio branch, the
    explanation must say so rather than implying an audio verdict exists."""
    text = explain(fuse(0.83, None)).lower()
    assert 'audio' in text, f'audio branch not mentioned at all: {text!r}'
    assert any(p in text for p in
               ('not evaluated', 'not been evaluated', "wasn't evaluated",
                'was not evaluated', 'not assessed', 'not analyzed',
                'not analysed')), \
        f'explanation does not state the audio branch was unevaluated: {text!r}'


def test_explain_disagreement_names_implicated_modality():
    r = fuse(0.95, 0.30)          # video >> audio -> video implicated
    assert r.implicated_modality == 'video'
    text = explain(r).lower()
    assert 'video' in text
    assert _score_mentioned(text, 0.95) or _score_mentioned(text, 0.30), \
        f'neither branch score stated in: {text!r}'


def test_explain_disagreement_audio_implicated_names_audio():
    r = fuse(0.20, 0.70)          # audio >> video -> audio implicated
    assert r.implicated_modality == 'audio'
    text = explain(r).lower()
    assert 'audio' in text


def test_explain_agreement_case_runs_and_is_grounded():
    r = fuse(0.90, 0.84, threshold_T=0.5)   # large T forces the agreement branch
    text = explain(r)
    assert text.strip()
    assert _score_mentioned(text, 0.90), f'video score not stated in: {text!r}'


# ── Video anomaly timing: real, timestamped windows the model may state WHEN, never WHAT (no LLM needed) ─────────────

def test_format_anomaly_timing_three_honest_states():
    assert format_anomaly_timing([{'start': 1.0, 'end': 2.0, 'peak_score': 0.9}], video_evaluated=False) == 'video not evaluated'
    assert format_anomaly_timing(None, video_evaluated=True) == 'not available'
    assert format_anomaly_timing([], video_evaluated=True) == 'no elevated-likelihood windows detected'


def test_format_anomaly_timing_states_real_times_never_invented():
    text = format_anomaly_timing(ANOMALY, video_evaluated=True)
    assert '0:04 to 0:05' in text and 'peak 0.95' in text


def test_format_anomaly_timing_caps_and_counts_the_rest():
    many = [{'start': float(i), 'end': float(i) + 0.5, 'peak_score': 0.6} for i in range(6)]
    text = format_anomaly_timing(many, video_evaluated=True)
    assert text.count(' to ') == 4          # MAX_ANOMALY_WINDOWS_SHOWN
    assert '2 more window' in text


def test_prompt_carries_video_anomaly_timing_and_forbids_content_description():
    prompt = build_prompt(fuse(0.90, None), anomalies=ANOMALY)
    assert '0:04 to 0:05' in prompt and 'peak 0.95' in prompt
    assert 'do not describe' in prompt.lower()


def test_prompt_states_no_windows_correctly_when_none_present():
    assert 'no elevated-likelihood windows detected' in build_prompt(fuse(0.90, None), anomalies=[])


def test_explain_may_state_a_given_time_but_never_an_invented_one():
    """End-to-end: real Llama output, screened. If it mentions a time at all, the screen must find it in the input."""
    r = fuse(0.90, None)
    text = explain(r, anomalies=ANOMALY)
    screen = check_faithfulness(text, build_structured_input(r, ANOMALY))
    assert not [v for v in screen['violations'] if v['type'] == 'timing'], (text, screen['violations'])


if __name__ == '__main__':
    if not LLM_UP:
        print(f'SKIP: {SKIP_REASON}')
        print('Start it with:  ollama serve   (and: ollama pull llama3:8b)')
        sys.exit(0)

    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith('test_')]
    failures = 0
    for name, fn in tests:
        try:
            fn()
            print(f'PASS  {name}')
        except AssertionError as e:
            failures += 1
            print(f'FAIL  {name}: {e}')
    print(f'\n{"ALL PASSED" if failures == 0 else f"{failures} FAILED"}')
    sys.exit(1 if failures else 0)
