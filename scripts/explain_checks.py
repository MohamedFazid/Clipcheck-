"""Deterministic explainer and automatic faithfulness screen for the explanation layer.

Two things, both pure Python (no Ollama needed):

1. explain_template(result): a no-LLM explanation built directly from the structured input
   (explain.build_structured_input). It is faithful by construction and is the BASELINE the LLM must beat:
   if a template is as clear and always faithful, an LLM adds risk without adding value.

2. check_faithfulness(text, structured): an automatic screen for ANY explanation text (template or LLM). It flags:
     number      a number in the text that is not derivable from the input scores (0.5 boundary allowed)
     direction   a sentence about ONE branch that says it looks fake when the input says it leans genuine, or the
                 reverse (the pilot's failure: 0.46 described as "fake")
     certainty   certainty language ("definitely", "proves", ...): the input carries scores, not certainty
     unlisted    claims that are not in the input (generator names, identities, causes)
     unevaluated a branch marked "not evaluated" that the text nevertheless scores or judges
     disagreement  disagreement claimed when the input says none, or not named when the input says yes
     timing      a clip timestamp (m:ss) in the text that is not one of the windows in video_anomaly_timing
   It is a SCREEN, not proof. Sentences naming BOTH branches are only checked for one thing (claiming both are
   manipulated when the input says one leans genuine); no other per-branch direction check is possible on them. A pass does
   not replace the human rubric. A failure is always a genuine reason to look at the text.
"""
import re
from typing import Optional

from explain import build_structured_input

BRANCH_WORDS = {
    'video': ('video', 'visual', 'face', 'facial', 'frame'),
    'audio': ('audio', 'voice', 'speech', 'sound', 'spoken'),
}
FAKE_WORDS = ('fake', 'manipulat', 'synthetic', 'spoof', 'forged', 'altered', 'artificial', 'deepfake', 'tamper')
GENUINE_WORDS = ('genuine', 'authentic', 'unaltered', 'natural', 'real')
# Phrases that contain a fake word but assert the opposite, or make only a relative comparison.
NEUTRALISE = (
    r'not (?:been )?(?:manipulated|fake|altered|synthetic|spoofed|tampered)',
    r'no (?:sign|signs|evidence|indication)s? of (?:manipulation|tampering|forgery|alteration)',
    r'more likely (?:to be )?(?:the )?(?:manipulated|fake|altered)(?: component| one| branch| modality)?',
    r'less likely (?:to be )?(?:manipulated|fake|altered)',
    r'not (?:manipulated|fake)',
    r'partial[- ]manipulation',
    r'un(?:manipulated|altered|tampered|doctored|synthetic|forged)',                # a genuine-word, not a fake claim
    # "the likelihood/probability of X being manipulated is (very) low/small/minimal", either word order
    r'(?:likelihood|probabilit\w+) (?:of|that) (?:it |the \w+ )?(?:being )?(?:manipulated|fake|altered|synthetic|'
    r'spoofed|tampered)(?:,? (?:is|are|was|were))? (?:very |extremely )?(?:low|small|minimal|negligible)',
    r'(?:very |extremely )?(?:low|small|minimal|negligible) (?:likelihood|probabilit\w+) (?:of|that) (?:it |the \w+ )?'
    r'(?:being )?(?:manipulated|fake|altered|synthetic|spoofed|tampered)',
)
# Same idea for the disagreement claim below: a sentence can contain "disagree" (or differ/conflict/...) while actually
# DENYING it ("no indication that the video and audio branches disagree", "does not disagree"), which must not count as
# claiming disagreement. A negation cue anywhere in the same clause (no punctuation between) as the word is enough;
# exact phrase matching is too brittle against ordinary paraphrase ("branches disagree" vs "branches ... disagree").
DISAGREEMENT_NEG_RE = re.compile(
    r'\b(?:no|not|never|nor|n\'t)\b[^.!?;:]{0,60}?\b(disagree\w*|differ\w*|conflict\w*|inconsisten\w*|mismatch\w*)\b')

# A FAKE_WORDS or GENUINE_WORDS hit preceded (within 40 chars, no clause break assumed since callers pass one
# sentence) by a negation cue does not count as claiming that direction. Found live on the video anomaly timing
# feature: "There is no indication that the video and audio are manipulated in different ways" and "but these do
# not suggest manipulation" both slipped past the NEUTRALISE phrase list, which cannot enumerate every paraphrase
# of a negation. This is the general mechanism NEUTRALISE's fixed phrases are specific cases of; kept as a second,
# broader layer rather than replacing NEUTRALISE, which also catches non-negations (relative comparisons).
NEG_CUE_RE = re.compile(r"\b(?:no|not|never|nor|isn't|aren't|wasn't|weren't|doesn't|don't|didn't|n't)\b")


def _unnegated_word_hit(low, words):
    for w in words:
        for m in re.finditer(re.escape(w), low):
            if not NEG_CUE_RE.search(low[max(0, m.start() - 70):m.start()]):
                return True
    return False


CERTAINTY = ('definitely', 'certainly', 'guaranteed', 'undoubtedly', 'without doubt', 'conclusively',
             'beyond doubt', 'proves that', 'proven', '100% sure', 'absolutely')
UNLISTED = ('gan', 'faceswap', 'face swap', 'face-swap', 'deepfakes', 'neural', 'autoencoder', 'diffusion',
            'voice clon', 'text-to-speech', 'tts', 'lip-sync', 'lip sync', 'who ', 'identity', 'person',
            'celebrity', 'politician', 'because the', 'caused by')
BOUNDARY_ALLOWED = {0.5}
NUM_RE = re.compile(r'(?<![\w.])(\d+(?:\.\d+)?)(%?)')
TIME_RE = re.compile(r'\b(\d{1,2}):([0-5]\d)\b')          # m:ss, as format_anomaly_timing writes it
PEAK_RE = re.compile(r'peak (\d+\.\d+)')


def _sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+|\n+', text) if s.strip()]


def _times_in(s):
    """The set of m:ss timestamps appearing in s, normalised (no leading zero on the minute)."""
    return {f'{int(h)}:{mm}' for h, mm in TIME_RE.findall(s or '')}


def _score_values(structured):
    vals = []
    for key in ('video_score', 'audio_score'):
        try:
            vals.append(float(structured[key]))
        except (KeyError, ValueError, TypeError):
            pass
    # Peak scores of the real anomaly windows (video_anomaly_timing) are also legitimate numbers the text may repeat;
    # they are not fabricated just because they differ from the two branch scores above.
    vals += [float(p) for p in PEAK_RE.findall(structured.get('video_anomaly_timing') or '')]
    return vals


def _number_ok(value, is_percent, scores):
    if not is_percent and any(abs(value - c) < 1e-9 for c in BOUNDARY_ALLOWED):
        return True
    for s in scores:
        if is_percent:
            if abs(value - s * 100) <= 0.5:
                return True
        elif abs(value - s) <= 0.0006 or any(abs(value - round(s, d)) < 1e-9 for d in (0, 1, 2)):
            return True
    return False


def _strip(sentence):
    low = sentence.lower()
    for pat in NEUTRALISE:
        low = re.sub(pat, ' ', low)
    return low


def _mentions(low, branch):
    return any(re.search(rf'\b{w}', low) for w in BRANCH_WORDS[branch])


def check_faithfulness(text: str, structured: dict) -> dict:
    violations = []
    low_all = text.lower()
    scores = _score_values(structured)

    # number (a timestamp's digits, e.g. the "4" and "05" of "4:05", are not probability numbers and are
    # checked separately below, not against the branch/peak scores)
    time_spans = [m.span() for m in TIME_RE.finditer(text)]
    for m in NUM_RE.finditer(text):
        if any(a <= m.start() < b for a, b in time_spans):
            continue
        value, pct = float(m.group(1)), m.group(2) == '%'
        if not _number_ok(value, pct, scores):
            violations.append(('number', f'"{m.group(0)}" is not derivable from the input scores'))

    # timing: a clip timestamp the text states must be one of the real windows given, never an invented one
    allowed_times = _times_in(structured.get('video_anomaly_timing'))
    for t in sorted(_times_in(text) - allowed_times):
        violations.append(('timing', f'"{t}" is not one of the timestamps given in video_anomaly_timing'))

    # certainty and unlisted claims
    for w in CERTAINTY:
        if w in low_all:
            violations.append(('certainty', f'certainty language: "{w}"'))
    for w in UNLISTED:
        core = w.strip()
        pat = rf'\b{re.escape(core)}\b' if len(core) <= 4 else rf'(?<![a-z]){re.escape(w)}'
        if re.search(pat, low_all):
            violations.append(('unlisted', f'claim outside the input: "{w.strip()}"'))

    # per-branch direction and not-evaluated
    assessment = {'video': structured.get('video_assessment', ''), 'audio': structured.get('audio_assessment', '')}
    for sent in _sentences(text):
        low = _strip(sent)
        has_v, has_a = _mentions(low, 'video'), _mentions(low, 'audio')
        if has_v and has_a:
            # A sentence naming BOTH branches cannot be direction-checked per branch, but one specific claim can: asserting
            # that both are manipulated when the input says one of them leans genuine. Found in the 50-case run, where
            # "the video and audio content are partially manipulated" was generated for audio = 0.000 (docs/EXPERIMENTS.md E3).
            says_fake_both = _unnegated_word_hit(low, FAKE_WORDS)
            conjunctive = re.search(r'(video and audio|audio and video|both\b)', low)
            genuine_branch = [b for b in ('video', 'audio') if 'GENUINE' in assessment[b]]
            if says_fake_both and conjunctive and genuine_branch and not any(re.search(rf'\b{w}\b', low) for w in GENUINE_WORDS):
                violations.append(('direction', f'text says both branches are manipulated but the input says the '
                                                f'{" and ".join(genuine_branch)} leans genuine: "{sent}"'))
            continue
        if not (has_v or has_a):                 # neither branch named: not direction-checked
            continue
        branch = 'video' if has_v else 'audio'
        a = assessment[branch]
        says_fake = _unnegated_word_hit(low, FAKE_WORDS)
        says_gen = _unnegated_word_hit(low, GENUINE_WORDS)
        if 'not evaluated' in a:
            if says_fake or says_gen or NUM_RE.search(sent):
                if not re.search(r'not (?:been )?evaluated|no (?:score|verdict)|unavailable|no audio|no face', low):
                    violations.append(('unevaluated', f'{branch} was not evaluated but the text judges it: "{sent}"'))
        elif 'GENUINE' in a and says_fake and not says_gen:
            violations.append(('direction', f'{branch} leans genuine but the text says fake: "{sent}"'))
        elif 'FAKE' in a and says_gen and not says_fake:
            violations.append(('direction', f'{branch} leans fake but the text says genuine: "{sent}"'))

    # disagreement: a mention of "disagree" (etc.) inside a negated clause ("no indication that ... disagree") does
    # not count as CLAIMING disagreement; only an un-negated occurrence does.
    disagrees = structured.get('disagreement') == 'yes'
    neg_spans = [m.span(1) for m in DISAGREEMENT_NEG_RE.finditer(low_all)]
    claims_dis = any(not any(a <= m.start() < b for a, b in neg_spans)
                     for m in re.finditer(r'disagree|differ|conflict|inconsisten|mismatch|partial', low_all))
    if disagrees:
        implicated = structured.get('implicated_modality', 'none')
        if not claims_dis:
            violations.append(('disagreement', 'input reports disagreement but the text does not say so'))
        if implicated in BRANCH_WORDS and not any(re.search(rf'\b{w}', low_all) for w in BRANCH_WORDS[implicated]):
            violations.append(('disagreement', f'implicated modality "{implicated}" is not named'))
    elif claims_dis and structured.get('verdict') != 'INCONCLUSIVE':
        violations.append(('disagreement', 'text claims disagreement but the input reports none'))

    return {'passed': not violations, 'violations': [{'type': t, 'detail': d} for t, d in violations]}


_CAUTION = ' This is an estimate, not proof: use it as one input to your own judgment.'


NO_TIMING = ('not available', 'no elevated-likelihood windows detected')
_PEAK_RE = re.compile(r' \(peak [\d.]+\)')


def _chance(score: str) -> str:
    """A score in plain words. Extremes are words, not numbers, so the text never states 100% or 0% (the app shows >99% / <1%);
    other scores are whole percentages, which the faithfulness screen accepts within half a point of the input score."""
    p = float(score)
    if p >= 0.995:
        return 'a very high chance'
    if p < 0.005:
        return 'a very low chance'
    n = round(p * 100)
    return f'{"an" if str(n).startswith("8") or n in (11, 18) else "a"} {n}% chance'


def explain_template(result, anomalies=None) -> str:
    """Deterministic plain-language explanation of a FusionResult (+ optional real anomaly windows), from the structured input only.

    Reworded 2026-09-25 for non-technical readers (the "layman terms" requirement and round 1 user testing): "picture
    check" and "voice check" instead of "video/audio analysis", chances as percentages in words, no system labels (FAKE, REAL,
    PARTIAL_MANIPULATION). The facts stated are unchanged, and tests/test_explain_checks.py runs every score combination through
    the faithfulness screen. Each sentence names at most one of the face and the voice, except where both lean the same way."""
    s = build_structured_input(result, anomalies)
    verdict = s['verdict']
    v_eval, a_eval = 'not evaluated' not in s['video_assessment'], 'not evaluated' not in s['audio_assessment']
    v_fake, a_fake = 'FAKE' in s['video_assessment'], 'FAKE' in s['audio_assessment']

    if verdict == 'INCONCLUSIVE':
        return ('No verdict could be given: neither the picture check nor the voice check produced a score for '
                'this clip.' + _CAUTION)
    parts = []
    if v_eval:
        parts.append(f'The picture check found {_chance(s["video_score"])} that the face was manipulated, so the face '
                     f'{"looks manipulated" if v_fake else "looks genuine"}.')
        if s['video_anomaly_timing'] not in NO_TIMING:
            windows = []
            for w in _PEAK_RE.sub('', s['video_anomaly_timing']).split(', '):
                a_, _, b_ = w.partition(' to ')
                windows.append(a_ if a_ == b_ else w)          # a one-frame moment reads "0:04", not "0:04 to 0:04"
            joined = windows[0] if len(windows) == 1 else ', '.join(windows[:-1]) + ' and ' + windows[-1]
            parts.append(f'The face looked most suspicious at {joined}.' if v_fake
                         else f'Its estimate was briefly higher at {joined}, but not enough to change how the face looks overall.')
    else:
        parts.append('The face could not be checked, so there is no picture score.')
    if a_eval:
        parts.append(f'The voice check found {_chance(s["audio_score"])} that the speech was generated or altered by software, '
                     f'so the voice {"sounds synthetic" if a_fake else "sounds genuine"}.')
    else:
        parts.append('The voice could not be checked, so there is no voice score.')

    if verdict == 'PARTIAL_MANIPULATION':
        imp = s['implicated_modality']
        part, other = ('face', 'voice') if imp == 'video' else ('voice', 'face')
        imp_fake, other_fake = (v_fake, a_fake) if imp == 'video' else (a_fake, v_fake)
        parts.append('The two checks disagree strongly, so the tool does not average them.')
        if imp_fake and not other_fake:
            parts.append(f'It points to the {part} as the part that looks manipulated, so only part of this clip may be fake.')
        elif imp_fake:
            parts.append(f'Both lean towards manipulation, but the {part} much more strongly than the {other}.')
        else:
            parts.append(f'It points to the {part} as the part that looks more suspicious, although both checks still lean genuine.')
    elif not (v_eval and a_eval):
        only = 'face' if v_eval else 'voice'
        parts.append(f'The result rests on the {only} check alone: the clip is likely '
                     f'{"manipulated" if verdict == "FAKE" else "genuine"}.')
    else:
        parts.append(f'The two checks agree, and together they say the clip is likely '
                     f'{"manipulated" if verdict == "FAKE" else "genuine"}.')
    return ' '.join(parts) + _CAUTION
