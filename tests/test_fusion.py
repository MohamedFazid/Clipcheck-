"""Unit tests for disagreement-aware fusion (scripts/fusion.py): weighted average on agreement, named branch on disagreement."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

import fusion  # noqa: E402
from fusion import fuse  # noqa: E402


def test_video_only_passthrough():
    r = fuse(0.92, None)
    assert r.verdict == 'FAKE'
    assert r.p_fake == 0.92
    assert r.gap is None
    assert r.disagreement is False
    assert r.weights == {'video': 1.0}


def test_agreement_uses_accuracy_weighted_average():
    # Explicit accuracies, not the module defaults, so the test checks the weighting mechanism
    # (the fused score sits closer to the more accurate branch), not which branch is currently more accurate.
    r = fuse(0.90, 0.80, threshold_T=0.5, video_accuracy=0.95, audio_accuracy=0.60)
    assert r.verdict == 'FAKE'
    assert r.disagreement is False
    assert r.implicated_modality is None
    unweighted_mean = (0.90 + 0.80) / 2
    assert abs(r.p_fake - 0.90) < abs(unweighted_mean - 0.90), \
        'higher-accuracy branch (video, 0.95 vs 0.60) should pull the fused score closer to it'


def test_agreement_real_verdict():
    r = fuse(0.08, 0.20, threshold_T=0.5)
    assert r.verdict == 'REAL'
    assert r.disagreement is False
    assert r.p_fake < 0.5


def test_disagreement_flags_partial_manipulation_no_averaging():
    r = fuse(0.95, 0.30, threshold_T=0.15)
    assert r.verdict == 'PARTIAL_MANIPULATION'
    assert r.disagreement is True
    assert r.p_fake is None          # no averaging occurs on disagreement
    assert r.weights is None


def test_disagreement_names_higher_scoring_modality_video():
    r = fuse(0.95, 0.30, threshold_T=0.15)
    assert r.implicated_modality == 'video'
    assert r.video_score == 0.95
    assert r.audio_score == 0.30


def test_disagreement_names_higher_scoring_modality_audio():
    r = fuse(0.20, 0.70, threshold_T=0.15)
    assert r.implicated_modality == 'audio'


def test_gap_computed_correctly():
    r = fuse(0.7, 0.4, threshold_T=0.5)
    assert abs(r.gap - 0.3) < 1e-9


def test_weights_sum_to_one_on_agreement():
    r = fuse(0.7, 0.6, threshold_T=0.5)
    assert abs(sum(r.weights.values()) - 1.0) < 1e-6


def test_rejects_out_of_range():
    try:
        fuse(1.5, 0.4)
        assert False, 'expected ValueError for p_video > 1'
    except ValueError:
        pass


if __name__ == '__main__':
    tests = [v for k, v in sorted(globals().items()) if k.startswith('test_')]
    failures = 0
    for fn in tests:
        try:
            fn()
            print(f'PASS  {fn.__name__}')
        except AssertionError as e:
            failures += 1
            print(f'FAIL  {fn.__name__}: {e}')
    print(f'\n{"ALL PASSED" if failures == 0 else f"{failures} FAILED"}')
    sys.exit(1 if failures else 0)


def test_no_branch_score_is_inconclusive():
    r = fuse(None, None)
    assert r.verdict == 'INCONCLUSIVE'
    assert r.p_fake is None and r.gap is None and not r.disagreement


def test_video_missing_falls_back_to_audio_only_and_says_so():
    r = fuse(None, 0.9)
    assert r.verdict == 'FAKE' and r.weights == {'audio': 1.0}
    assert 'single-modality' in r.note and 'video' in r.note
    assert fuse(None, 0.1).verdict == 'REAL'


def test_missing_video_still_validates_audio_range():
    import pytest
    with pytest.raises(ValueError):
        fuse(None, 1.5)


def test_video_accuracy_is_read_from_shipped_model_file_not_hardcoded():
    """The constant must come from models/shipped_model.json when it exists, and say when it is a fallback."""
    import fusion
    acc, measured, src = fusion._resolve_video_accuracy()
    if fusion._SHIPPED_MODEL_PATH.exists():
        assert measured is True
    else:
        assert measured is False and 'FALLBACK' in src
    assert 0.0 < acc <= 1.0


# ── The audio weight must be the balanced figure, not the one inflated by class imbalance ─────────────────────────

def test_audio_weight_uses_balanced_accuracy_not_plain_accuracy(tmp_path, monkeypatch):
    """The ASVspoof eval partition is about 90% spoof, so plain accuracy there (0.9765) is close to the 89.7% a
    classifier scores by always answering "spoof". Fusion must weight the branch by its BALANCED accuracy at the
    operating point the app uses (docs/EXPERIMENTS.md A4)."""
    import importlib, json
    metrics = tmp_path / 'metrics.json'
    extra = tmp_path / 'extra_metrics.json'
    metrics.write_text(json.dumps({'full_dataset': True, 'eval_accuracy': 0.9765}))
    extra.write_text(json.dumps({'majority_class_baseline_accuracy': 0.897,
                                 fusion._AUDIO_OPERATING_POINT: {'balanced_accuracy': 0.9569}}))
    monkeypatch.setattr(fusion, '_AUDIO_METRICS_PATH', metrics)
    monkeypatch.setattr(fusion, '_AUDIO_EXTRA_PATH', extra)
    acc, measured, source = fusion._resolve_audio_accuracy()
    assert measured is True
    assert abs(acc - 0.9569) < 1e-9, 'fusion must use balanced accuracy, not the inflated plain figure'
    assert 'balanced' in source and '90% spoof' in source

    # Without extra_metrics.json it falls back to plain accuracy and says the balanced figure is missing.
    monkeypatch.setattr(fusion, '_AUDIO_EXTRA_PATH', tmp_path / 'absent.json')
    acc, measured, source = fusion._resolve_audio_accuracy()
    assert abs(acc - 0.9765) < 1e-9 and measured is True
    assert 'balanced accuracy unavailable' in source

    # A subsample-only run is still refused, balanced figure present or not.
    metrics.write_text(json.dumps({'full_dataset': False, 'subsampled_per_class': 400, 'eval_accuracy': 0.99}))
    monkeypatch.setattr(fusion, '_AUDIO_EXTRA_PATH', extra)
    acc, measured, source = fusion._resolve_audio_accuracy()
    assert measured is False and acc == fusion.AUDIO_ACCURACY_PLACEHOLDER


def test_audio_weight_in_use_is_the_balanced_one():
    """Guards the live value, not just the resolver."""
    assert fusion.AUDIO_ACCURACY_IS_MEASURED
    assert abs(fusion.AUDIO_ACCURACY - 0.9569) < 5e-4, f'unexpected audio weight in use: {fusion.AUDIO_ACCURACY}'

