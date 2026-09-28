"""Disagreement-aware fusion: if |P(video) - P(audio)| >= T, report PARTIAL_MANIPULATION and name the higher branch;
otherwise take an accuracy-weighted average (Large, Lines and Bagnall, 2019). T and weights are read from files.
Run: python scripts/fusion.py"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# LEGACY fallback only: the old baseline's frame-level accuracy, measured on the superseded leaking split.
# It is used only when models/shipped_model.json does not exist, and is reported as not measured.
VIDEO_ACCURACY_FALLBACK = 0.9639

_SHIPPED_MODEL_PATH = Path(__file__).resolve().parent.parent / 'models' / 'shipped_model.json'


def _resolve_video_accuracy():
    """Held-out clip-level accuracy of the shipped video model, from models/shipped_model.json
    (keys: video_accuracy, video_accuracy_source). Returns (accuracy, is_measured, source)."""
    if _SHIPPED_MODEL_PATH.exists():
        try:
            with open(_SHIPPED_MODEL_PATH) as f:
                m = json.load(f)
            return (float(m['video_accuracy']), True,
                    str(m.get('video_accuracy_source', 'measured (see models/shipped_model.json)')))
        except (json.JSONDecodeError, KeyError, ValueError, TypeError):
            pass
    return (VIDEO_ACCURACY_FALLBACK, False,
            'FALLBACK (legacy figure from the superseded leaking split; no shipped_model.json yet)')


VIDEO_ACCURACY_DEFAULT, VIDEO_ACCURACY_IS_MEASURED, VIDEO_ACCURACY_SOURCE = _resolve_video_accuracy()

# Fallback when no measured audio accuracy exists: chance level, so an unmeasured branch cannot outweigh video.
AUDIO_ACCURACY_PLACEHOLDER = 0.5

_AUDIO_METRICS_PATH = Path(__file__).resolve().parent.parent / 'results' / 'audio_branch' / 'metrics.json'
_AUDIO_EXTRA_PATH = Path(__file__).resolve().parent.parent / 'results' / 'audio_branch' / 'extra_metrics.json'
# The key in extra_metrics.json measured at the operating point the app actually uses (P(audio_fake) >= 0.5), not at the
# SVM's own decision boundary, so the weight describes the branch as deployed.
_AUDIO_OPERATING_POINT = 'at_probability_0.5 (as the app and fusion use it)'


def _resolve_audio_accuracy():
    """Return (accuracy, is_measured, source) for the audio branch, from a FULL ASVspoof eval run only;
    subsample runs are not accepted as measured and keep the placeholder."""
    if _AUDIO_METRICS_PATH.exists():
        try:
            with open(_AUDIO_METRICS_PATH) as f:
                m = json.load(f)
            acc = float(m['eval_accuracy'])
            if m.get('full_dataset') is True:
                # Use BALANCED accuracy: the ASVspoof eval set is ~90% spoof, so plain accuracy is inflated.
                # Falls back to plain accuracy if extra_metrics.json does not exist (ledger A4).
                if _AUDIO_EXTRA_PATH.exists():
                    try:
                        with open(_AUDIO_EXTRA_PATH) as f:
                            x = json.load(f)
                        bal = float(x[_AUDIO_OPERATING_POINT]['balanced_accuracy'])
                        base = float(x['majority_class_baseline_accuracy'])
                        return bal, True, (f'measured, balanced accuracy at P(fake) >= 0.5 on the full ASVspoof 2019 LA eval '
                                           f'partition (plain accuracy there is {acc:.4f}, but the set is {base * 100:.0f}% spoof, '
                                           f'so plain accuracy overstates the branch)')
                    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
                        pass
                return acc, True, ('measured, plain accuracy on the full ASVspoof 2019 LA eval partition (balanced accuracy '
                                   'unavailable: run scripts/eval_audio_metrics.py)')
            n_sub = m.get('subsampled_per_class')
            return (AUDIO_ACCURACY_PLACEHOLDER, False,
                    f'placeholder (a subsample-only run exists '
                    f'[{n_sub}/class, eval_accuracy={acc:.4f}] but a subset result is '
                    f'not comparable to a full-set figure, so it is not used for weighting)')
        except (json.JSONDecodeError, KeyError, ValueError, TypeError):
            pass
    return AUDIO_ACCURACY_PLACEHOLDER, False, 'placeholder (audio SVM not yet trained)'


AUDIO_ACCURACY, AUDIO_ACCURACY_IS_MEASURED, AUDIO_ACCURACY_SOURCE = _resolve_audio_accuracy()

# Tuned on the shipped model with scripts/tune_threshold_fallback.py (F1 on single-modality cases, 79 clips): best T = 0.35.
# The F1 curve is flat (0.88 to 0.91 for T = 0.20 to 0.60). Re-tune if either branch model changes.
THRESHOLD_T_DEFAULT = 0.35
THRESHOLD_T_SOURCE = ('tuned on the shipped model (Xception multi-method, seed 44) against the self-built fallback '
                      'evaluation set, maximising F1 on identifying genuine single-modality manipulation '
                      '(79 clips; F1 0.907, precision 0.848, recall 0.975); see '
                      'results/fallback_eval_shipped/threshold_tuning.json')


@dataclass
class FusionResult:
    verdict: str                         # 'FAKE' | 'REAL' | 'PARTIAL_MANIPULATION' | 'INCONCLUSIVE'
    gap: Optional[float]                 # |P(video_fake) - P(audio_fake)|, None if single-modality
    disagreement: bool                   # gap >= threshold_T
    p_fake: Optional[float] = None       # fused score; None when partial manipulation (no averaging)
    weights: Optional[dict] = None       # accuracy-derived weights, set only on agreement
    video_score: Optional[float] = None
    audio_score: Optional[float] = None
    implicated_modality: Optional[str] = None  # set only on disagreement
    note: str = ''


def fuse(
    p_video: Optional[float],
    p_audio: Optional[float] = None,
    *,
    threshold_T: float = THRESHOLD_T_DEFAULT,
    decision_threshold: float = 0.5,
    video_accuracy: float = VIDEO_ACCURACY_DEFAULT,
    audio_accuracy: float = AUDIO_ACCURACY,
) -> FusionResult:
    """Fuse the branch fake-probabilities. A None score means that branch did not run (single-modality pass-through);
    both None gives INCONCLUSIVE. threshold_T separates agreement from partial manipulation; accuracies weight the average."""
    if p_video is None and p_audio is None:
        return FusionResult(verdict='INCONCLUSIVE', gap=None, disagreement=False,
                            note='no branch produced a score (no detectable face and no usable speech)')

    if p_video is None:
        if not 0.0 <= p_audio <= 1.0:
            raise ValueError(f'p_audio out of range: {p_audio}')
        return FusionResult(
            verdict='FAKE' if p_audio >= decision_threshold else 'REAL',
            gap=None, disagreement=False, p_fake=float(p_audio), weights={'audio': 1.0},
            audio_score=p_audio,
            note='single-modality (video branch produced no score)')

    if not 0.0 <= p_video <= 1.0:
        raise ValueError(f'p_video out of range: {p_video}')

    # ── Single-modality (audio unavailable): pass the video score through. ──
    if p_audio is None:
        verdict = 'FAKE' if p_video >= decision_threshold else 'REAL'
        return FusionResult(
            verdict=verdict,
            gap=None,
            disagreement=False,
            p_fake=float(p_video),
            weights={'video': 1.0},
            video_score=p_video,
            note='single-modality (audio branch produced no score)',
        )

    if not 0.0 <= p_audio <= 1.0:
        raise ValueError(f'p_audio out of range: {p_audio}')

    gap = abs(p_video - p_audio)
    disagreement = gap >= threshold_T

    # ── Disagreement: no averaging. Flag partial manipulation, name the branch. ──
    if disagreement:
        implicated = 'video' if p_video > p_audio else 'audio'
        return FusionResult(
            verdict='PARTIAL_MANIPULATION',
            gap=gap,
            disagreement=True,
            video_score=p_video,
            audio_score=p_audio,
            implicated_modality=implicated,
            note=f'gap {gap:.3f} >= T {threshold_T:.3f}: branches disagree, '
                 f'"{implicated}" scored higher and is flagged as more likely manipulated',
        )

    # ── Agreement: accuracy-weighted average into one final score. ──
    total = video_accuracy + audio_accuracy
    w_video, w_audio = video_accuracy / total, audio_accuracy / total
    p_fused = w_video * p_video + w_audio * p_audio
    verdict = 'FAKE' if p_fused >= decision_threshold else 'REAL'

    return FusionResult(
        verdict=verdict,
        gap=gap,
        disagreement=False,
        p_fake=float(p_fused),
        weights={'video': round(w_video, 3), 'audio': round(w_audio, 3)},
        video_score=p_video,
        audio_score=p_audio,
        note=f'gap {gap:.3f} < T {threshold_T:.3f}: accuracy-weighted average '
             f'(video_accuracy={video_accuracy}, audio_accuracy={audio_accuracy} '
             f'[video: {VIDEO_ACCURACY_SOURCE}; audio: {AUDIO_ACCURACY_SOURCE}])',
    )


def _plumbing_test():
    print('=' * 72)
    print('FUSION BRANCH -- PLUMBING TEST on SYNTHETIC / placeholder scores')
    print('Proves the disagreement-aware, accuracy-weighted fusion logic runs')
    print('end to end. It is NOT a real fused result -- the audio branch has no')
    print('trained spoof score yet, and audio_accuracy above is a placeholder.')
    print('=' * 72)

    cases = [
        ('video only (audio pending)',      0.92, None),
        ('agree FAKE (gap < T)',            0.90, 0.80),
        ('agree REAL (gap < T)',            0.08, 0.20),
        ('DISAGREE, video higher',          0.95, 0.30),
        ('DISAGREE, audio higher',          0.20, 0.70),
    ]
    for name, pv, pa in cases:
        r = fuse(pv, pa)
        pa_s = 'None' if pa is None else f'{pa:.2f}'
        print(f'\n- {name}')
        print(f'    in : P(video)={pv:.2f}  P(audio)={pa_s}')
        print(f'    out: verdict={r.verdict}  gap={r.gap}  p_fake={r.p_fake}  '
              f'weights={r.weights}  implicated={r.implicated_modality}')
        print(f'    note: {r.note}')

    print('\n>>> Plumbing only. Real fused verdicts need the shipped video model, the trained')
    print('audio SVM, and a threshold T tuned on the shipped model. <<<')


if __name__ == '__main__':
    _plumbing_test()
