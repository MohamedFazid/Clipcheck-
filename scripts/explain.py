"""Constrained natural-language explanation layer (Llama 3 8B Instruct, local).

Implements stage 5 of the pipeline specified in the Draft Project Report,
Chapter 3 (System Architecture):

    verdict + P(video_fake) + P(audio_fake) + disagreement flag/type
        -> fixed structured input
        -> Llama 3 8B Instruct, constrained to template-filling
        -> plain-language explanation for a non-expert user

DESIGN CONSTRAINT (Chapter 3.4, following Wickramasekara, Breitinger and
Scanlon, 2024): the model is NOT allowed to reason freely over raw scores. It
receives exactly the four structured fields the report specifies, and the
prompt explicitly forbids introducing any claim not present in that input,
restating a probability as a certainty, or inventing a score for a branch that
was not evaluated. This reduces, but does not eliminate, hallucination risk —
the residual risk is what the Chapter 3.6 human-evaluation rubric (50 samples,
2 raters, Cohen's Kappa) is designed to measure. That rubric is a separate,
pending piece of work: nothing here claims the explanations have been
validated for quality, only that they are generated under the specified
constraint.

CURRENT REAL STATE (no fabrication): the audio branch's SVM is untrained
(ASVspoof 2019 LA pending), so in practice `fuse()` is called with
p_audio=None and this layer verbalises a genuine single-modality, video-only
result. The prompt handles that case explicitly by requiring the explanation
to say the audio branch was not evaluated, rather than implying an audio
verdict exists.

ADDITION (2026-09-22): a `video_anomaly_timing` field carries real, timestamped windows where the video branch's
per-sampled-frame score was elevated (server.py's `_frame_anomalies`, already shown in the app's Visual tab; never
invented here). The model may state WHEN elevated likelihood occurred, using only the timestamps given; it is
explicitly forbidden from describing WHAT is visible at that time (blinking, lighting, lip movement, and so on),
because no model in this pipeline analyses frame content -- only a per-frame probability exists, never a semantic
description of it. See docs/EXPERIMENTS.md for the rationale and docs/decisions for the related decision record.

Requires a local Ollama server with llama3:8b pulled:
    brew install ollama && ollama serve && ollama pull llama3:8b

Run:  /opt/anaconda3/bin/python scripts/explain.py
"""

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

# Low temperature + fixed seed: the explanation layer verbalises a fixed input,
# so run-to-run variability is a liability here, not a feature. (Chapter 3.4
# specifies template-filling, not creative generation.)
GEN_OPTIONS = {'temperature': 0.2, 'seed': 42, 'num_predict': 220}

# Note for the report: Chapter 3.7's third contingency allows substituting a
# smaller instruction-tuned model, because the contribution rests on the
# constrained-template design rather than the specific model. Set the
# DEEPFAKE_LLM environment variable to swap models without code changes.

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
    """Real, timestamped video-anomaly windows (server.py's _frame_anomalies) as a short phrase for the prompt.

    Three honestly distinct states, never conflated:
      video_evaluated=False        -> 'video not evaluated' (no score exists at all)
      anomalies is None            -> 'not available' (this caller did not supply timing data; NOT the same as
                                       "checked and found none" -- callers other than the live server, e.g. the
                                       standalone plumbing check or older tests, may not pass this)
      anomalies == []              -> 'no elevated-likelihood windows detected' (computed; genuinely zero)
      anomalies non-empty          -> up to MAX_ANOMALY_WINDOWS_SHOWN windows, earliest first, exactly as computed;
                                       never a fabricated time.
    """
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
    """Raised when the local LLM cannot be reached or fails to generate.

    Deliberately a hard failure: callers must surface "explanation
    unavailable" rather than silently substituting canned text, which would
    misrepresent a non-running model as a working one.
    """


def assess(score: Optional[float], decision_threshold: float = 0.5) -> str:
    """Turn a raw P(fake) into the plain-language direction it implies.

    This comparison is done HERE, in deterministic code, and handed to the model
    already resolved -- it is not left for the LLM to work out.

    Rationale (empirical, from the Chapter 3.6 pilot). Earlier revisions stated
    the rule "above 0.5 leans fake, below 0.5 leans genuine" in the prompt and
    asked the model to apply it. Llama 3 8B applied it inconsistently: across
    three successive prompt revisions it variously described 0.46 as "leans
    fake", 0.11 as "leans manipulated", and 0.150 as "likely manipulated",
    with each fix reintroducing a failure elsewhere. Comparing a number to a
    threshold is arithmetic reasoning, and Chapter 3.4 constrains this layer to
    verbalising a fixed structured input rather than reasoning over raw scores.
    Precomputing the direction therefore both fixes the failure and moves the
    implementation closer to the specified design, instead of further from it.
    """
    if score is None:
        return 'was not evaluated'
    if score > decision_threshold:
        return 'leans FAKE (manipulated)'
    if score < decision_threshold:
        return 'leans GENUINE (not manipulated)'
    return 'is exactly on the decision boundary'


def build_structured_input(result: FusionResult, anomalies: Optional[list] = None) -> dict:
    """FusionResult (+ optional real anomaly windows) -> exactly the fields the model is given, as display strings.

    Nothing else from the FusionResult (internal notes, fusion weights, the
    raw gap) is exposed to the model: the constraint is that the LLM
    verbalises this fixed input and nothing more. The two *_assessment fields
    are not extra information -- they are the deterministic reading of the two
    scores already present, resolved in code (see assess()). `video_anomaly_timing`
    is likewise not new information the model could invent from: it is the same
    real per-frame data already shown in the app's Visual tab (see format_anomaly_timing).
    """
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
    """True if the local Ollama server is reachable and has the model pulled.

    Used as a guard by the app and the tests, mirroring app.py's existing
    AUDIO_OK pattern, so a machine without Ollama degrades gracefully instead
    of crashing.
    """
    try:
        resp = requests.get(TAGS_URL, timeout=timeout)
        resp.raise_for_status()
        names = [m.get('name', '') for m in resp.json().get('models', [])]
        return any(n == MODEL_NAME or n.startswith(MODEL_NAME.split(':')[0]) for n in names)
    except Exception:
        return False


def explain(result: FusionResult, *, timeout: float = 120.0, anomalies: Optional[list] = None) -> str:
    """Generate a constrained plain-language explanation of a FusionResult.

    Raises ExplanationUnavailable if the local model cannot be reached or
    returns nothing — never returns fabricated or placeholder prose.
    """
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
