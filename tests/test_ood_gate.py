"""The out-of-domain gate (scripts/ood_gate.py): the maths on synthetic data (no files, runs in CI), plus one heavy check that asking the
video model for its features does not change its score."""
import os
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
from ood_gate import MahalanobisGate, clip_video_distance  # noqa: E402

heavy = pytest.mark.skipif(os.environ.get('DEEPFAKE_SKIP_HEAVY') == '1', reason='loads the real video model')


def _gaussian(n, d=8, shift=0.0, seed=0):
    return np.random.default_rng(seed).normal(shift, 1.0, size=(n, d))


def test_threshold_sets_the_in_domain_abstention_rate():
    g = MahalanobisGate('pooled', 97.5).fit(_gaussian(4000, seed=1)).calibrate(_gaussian(4000, seed=2))
    rate = g.is_out_of_domain(g.distance(_gaussian(4000, seed=3))).mean()
    assert 0.01 < rate < 0.045, rate            # about 2.5% on fresh in-domain data


def test_far_away_inputs_are_flagged():
    g = MahalanobisGate('pooled', 97.5).fit(_gaussian(2000, seed=1)).calibrate(_gaussian(2000, seed=2))
    assert g.is_out_of_domain(g.distance(_gaussian(200, shift=4.0, seed=3))).mean() > 0.95


def test_class_variant_uses_the_nearest_class():
    a, b = _gaussian(1000, shift=0.0, seed=1), _gaussian(1000, shift=6.0, seed=2)
    X, y = np.vstack([a, b]), np.array([0] * 1000 + [1] * 1000)
    pooled = MahalanobisGate('pooled').fit(X, y)
    cls = MahalanobisGate('class').fit(X, y)
    centre_b = np.full((1, 8), 6.0)
    # the class variant measures from B's own centre; the pooled variant measures from the mixture's centre
    assert cls.distance(centre_b)[0] < 0.2 and cls.distance(centre_b)[0] < pooled.distance(centre_b)[0] / 5


def test_class_variant_needs_labels_and_unknown_kind_is_refused():
    with pytest.raises(ValueError):
        MahalanobisGate('class').fit(_gaussian(50))
    with pytest.raises(ValueError):
        MahalanobisGate('knn')


def test_uncalibrated_gate_refuses_to_decide():
    g = MahalanobisGate().fit(_gaussian(100))
    with pytest.raises(RuntimeError):
        g.is_out_of_domain([1.0])


def test_one_odd_crop_cannot_flag_a_clip():
    g = MahalanobisGate('pooled', 97.5).fit(_gaussian(2000, seed=1)).calibrate(_gaussian(2000, seed=2))
    crops = _gaussian(20, seed=3)
    crops[0] += 50.0                               # one wild crop (blur, profile view)
    assert clip_video_distance(g, crops) <= g.threshold_


@heavy
def test_asking_for_features_does_not_change_the_video_score():
    pytest.importorskip('facenet_pytorch')          # the video stack lives in the app environment only
    import torch
    import video_infer as vi
    _, model, device = vi.load_models()
    x = torch.randn(2, 3, 224, 224).to(device)
    with torch.no_grad():
        assert torch.equal(model(x), model.forward_head(model.forward_features(x)))
    clip = Path(__file__).resolve().parent.parent / 'demo_videos' / 'composite_real_video_synthetic_speech.mp4'
    mtcnn = vi.load_models()[0]
    plain = vi.analyse_video_file(str(clip), mtcnn, model, device, max_faces=5)
    with_f = vi.analyse_video_file(str(clip), mtcnn, model, device, max_faces=5, return_features=True)
    assert plain['per_frame'] == with_f['per_frame']
    assert with_f['features'].shape == (5, 2048) and 'features' not in plain
