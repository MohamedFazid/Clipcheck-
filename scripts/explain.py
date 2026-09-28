"""Constrained explanation layer: Llama 3 8B (local, via Ollama) fills a template from a fixed structured input.
The prompt forbids unlisted claims; timing windows say WHEN a score was high, never WHAT is visible.
Needs: ollama pull llama3:8b. Run: python scripts/explain.py"""

import os
import sys
from typing import Optional

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fusion import FusionResult, fuse

OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
GENERATE_URL = f'{OLLAMA_HOST}/api/generate'
TAGS_URL = f'{OLLAMA_HOST}/api/tags'
MODEL_NAME = os.environ.get('DEEPFAKE_LLM', 'llama3:8b')

# Low temperature and a fixed seed: the layer fills a template, so run-to-run variation is unwanted.
GEN_OPTIONS = {'temperature': 0.2, 'seed': 42, 'num_predict': 220}

# Set DEEPFAKE_LLM to try another model without code changes.

PROMPT_TEMPLATE = """You are the explanation stage of a deepfake-detection pipeline. \
A journalist or content moderator with no technical background will read your output.

You are given a STRUCTURED ANALYSIS RESULT. Your only job is to state what it says in plain English.

STRUCTURED ANALYSIS RESULT:
- Overall verdict: {verdict}
- Video branch P(fake): {video_score}  ->  this branch {video_assessment}
- Video anomaly timing: {video_anomaly_timing}
- Audio branch P(fake): {audio_score}  ->  this branch {audio_assessment}
- Branches disagree: {disagreement}
- Modality flagged as more likely manipulated: {implicated_modality}

RULES (follow all of them):
1. Use ONLY the fields above. Do not add any fact, cause, technique name, or detail that is not listed there.
2. Do not speculate about HOW the video was manipulated, what tool made it, or who is in it. You were not given that information.
3. State probabilities as probabilities, never as certainties. A score of {video_score} means "the model estimates that likelihood", not "this is definitely fake".
4. If a branch's score is "not evaluated", say plainly that this branch was not evaluated and that the verdict therefore rests on the other branch alone. Never invent or estimate a score for it.
5. If the branches disagree, say which modality is flagged and that this suggests only part of the content may be manipulated.
6. Each branch's direction has ALREADY been worked out for you and is written after the arrow. Repeat that direction as given. Do not re-interpret a score yourself, and never describe a branch in a way that contradicts the direction stated after its arrow.
7. If "Video anomaly timing" lists one or more time windows, you MAY mention WHEN in the clip the elevated likelihood occurred, using exactly the timestamps given and no others. Do NOT describe WHAT is visible at that time (no mention of blinking, lighting, facial movement, expression, or any other visual detail) -- you were only given a probability and a time, never a description of the frame itself.
8. If "Video anomaly timing" says "no elevated-likelihood windows detected", "video not evaluated" or "not available", do not mention timing at all.
9. Write 2 to 4 short sentences. No bullet points, no headings, no preamble such as "Here is the explanation".

Write the explanation now."""

MAX_ANOMALY_WINDOWS_SHOWN = 4


def _mmss(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f'{m}:{s:02d}'


def format_anomaly_timing(anomalies: Optional[list], video_evaluated: bool) -> str:
    """Timing windows as a short phrase: 'video not evaluated', 'not available' (None), 'no elevated-likelihood windows' ([]),
    or up to MAX_ANOMALY_WINDOWS_SHOWN real windows, earliest first."""
    if not video_evaluated:
        return 'video not evaluated'
    if anomalies is None:
        return 'not available'
    if not anomalies:
        return 'no elevated-likelihood windows detected'
    rows = sorted(anomalies, key=lambda a: (a.get('start') is None, a.get('start')))[:MAX_ANOMALY_WINDOWS_SHOWN]
    parts = []
    for a in rows:
        if a.get('start') is not None:
            parts.append(f'{_mmss(a["start"])} to {_mmss(a["end"])} (peak {a["peak_score"]:.2f})')
        else:
            parts.append(f'an unspecified time (peak {a["peak_score"]:.2f})')
    text = ', '.join(parts)
    more = len(anomalies) - len(rows)
    if more > 0:
        text += f', and {more} more window(s) not shown'
    return text


class ExplanationUnavailable(RuntimeError):
    """Raised when the local LLM cannot be reached or fails; callers show "explanation unavailable", never canned text."""


def assess(score: Optional[float], decision_threshold: float = 0.5) -> str:
    """Turn a P(fake) into the direction it implies ('leans fake' / 'leans genuine') in code, not in the prompt.
    Llama 3 8B compared scores with 0.5 unreliably in the pilot (e.g. 0.46 called fake), so this is precomputed."""
    if score is None:
        return 'was not evaluated'
    if score > decision_threshold:
        return 'leans FAKE (manipulated)'
    if score < decision_threshold:
        return 'leans GENUINE (not manipulated)'
    return 'is exactly on the decision boundary'


def build_structured_input(result: FusionResult, anomalies: Optional[list] = None) -> dict:
    """FusionResult (+ optional timing windows) -> exactly the fields the model sees, as strings.
    Weights, the raw gap and notes are never exposed; the *_assessment fields come from assess()."""
    if result.audio_score is None:
        audio_score = 'not evaluated'
    else:
        audio_score = f'{result.audio_score:.3f}'

    return {
        'verdict': result.verdict,
        'video_score': f'{result.video_score:.3f}' if result.video_score is not None else 'not evaluated',
        'audio_score': audio_score,
        'video_assessment': assess(result.video_score),
        'audio_assessment': assess(result.audio_score),
        'video_anomaly_timing': format_anomaly_timing(anomalies, result.video_score is not None),
        'disagreement': 'yes' if result.disagreement else 'no',
        'implicated_modality': result.implicated_modality or 'none',
    }


def build_prompt(result: FusionResult, anomalies: Optional[list] = None) -> str:
    """Fill the fixed template with the structured input (no free-form text)."""
    return PROMPT_TEMPLATE.format(**build_structured_input(result, anomalies))


def explanation_available(timeout: float = 3.0) -> bool:
    """True if the local Ollama server is reachable and has the model, so the app degrades gracefully without it."""
    try:
        resp = requests.get(TAGS_URL, timeout=timeout)
        resp.raise_for_status()
        names = [m.get('name', '') for m in resp.json().get('models', [])]
        return any(n == MODEL_NAME or n.startswith(MODEL_NAME.split(':')[0]) for n in names)
    except Exception:
        return False


def explain(result: FusionResult, *, timeout: float = 120.0, anomalies: Optional[list] = None) -> str:
    """Generate a constrained explanation; raises ExplanationUnavailable rather than returning placeholder text."""
    payload = {
        'model': MODEL_NAME,
        'prompt': build_prompt(result, anomalies),
        'stream': False,
        'options': GEN_OPTIONS,
    }
    try:
        resp = requests.post(GENERATE_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
        text = resp.json().get('response', '').strip()
    except requests.RequestException as e:
        raise ExplanationUnavailable(
            f'could not reach the local LLM at {GENERATE_URL} ({e}). '
            'Is `ollama serve` running?') from e

    if not text:
        raise ExplanationUnavailable('the local LLM returned an empty response')
    return text


def _plumbing_test():
    print('=' * 72)
    print('EXPLANATION LAYER -- generation check on representative fusion results')
    print(f'Model: {MODEL_NAME} via {OLLAMA_HOST}')
    print('Explanations below are REAL model output. Their *quality* is not')
    print('validated here -- that is the pending Ch3.6 human-eval rubric.')
    print('=' * 72)

    if not explanation_available():
        print(f'\nFAIL: {MODEL_NAME} not reachable at {OLLAMA_HOST}.')
        print('Start it with:  ollama serve   (and: ollama pull llama3:8b)')
        return 1

    cases = [
        ('video-only FAKE (the current real pipeline state)', fuse(0.999, None)),
        ('video-only REAL (the current real pipeline state)', fuse(0.041, None)),
        ('agreement, both high (needs a trained audio branch)', fuse(0.90, 0.84)),
        ('DISAGREEMENT, video implicated (needs a trained audio branch)', fuse(0.95, 0.30)),
        ('DISAGREEMENT, audio implicated (needs a trained audio branch)', fuse(0.20, 0.70)),
    ]

    for name, result in cases:
        print(f'\n--- {name}')
        print(f'    structured input: {build_structured_input(result)}')
        try:
            print(f'    explanation: {explain(result)}')
        except ExplanationUnavailable as e:
            print(f'    ERROR: {e}')
            return 1

    print('\n>>> Generation verified. Note the last three cases use illustrative')
    print('audio scores: the audio SVM is untrained, so only the first two')
    print('reflect what the live pipeline currently produces. <<<')
    return 0


if __name__ == '__main__':
    sys.exit(_plumbing_test())
