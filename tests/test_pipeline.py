"""Integration test for the video branch: real demo clips through sampling, face crops, classification and aggregation."""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from video_infer import load_models, analyse_video_file  # noqa: E402

DEMO = PROJECT_ROOT / 'demo_videos'
FAKE_CLIP = DEMO / 'manipulated_sequences' / 'Deepfakes' / 'c23' / 'videos' / '469_481.mp4'
REAL_CLIP = DEMO / 'original_sequences' / 'youtube' / 'c23' / 'videos' / '183.mp4'

if not (FAKE_CLIP.exists() and REAL_CLIP.exists()):
    import pytest
    pytest.skip('the demo clips are not present (FaceForensics++-derived, not in the repository)', allow_module_level=True)

# Load once for all tests.
_mtcnn, _model, _device = load_models()


def _run(clip):
    assert clip.exists(), f'demo clip missing: {clip}'
    result = analyse_video_file(clip, _mtcnn, _model, _device)
    assert result is not None, 'no faces detected — pipeline returned None'
    # Output contract.
    assert 0.0 <= result['p_fake'] <= 1.0, f'p_fake out of range: {result["p_fake"]}'
    assert result['n_faces'] > 0
    assert len(result['per_frame']) == result['n_faces']
    assert result['verdict'] in ('FAKE', 'REAL')
    return result


def test_fake_clip_predicts_fake():
    r = _run(FAKE_CLIP)
    assert r['verdict'] == 'FAKE', f"expected FAKE, got {r['verdict']} (p={r['p_fake']:.3f})"


def test_real_clip_predicts_real():
    r = _run(REAL_CLIP)
    assert r['verdict'] == 'REAL', f"expected REAL, got {r['verdict']} (p={r['p_fake']:.3f})"


if __name__ == '__main__':
    failures = 0
    for name, fn in [('fake_clip->FAKE', test_fake_clip_predicts_fake),
                     ('real_clip->REAL', test_real_clip_predicts_real)]:
        try:
            fn()
            print(f'PASS  {name}')
        except AssertionError as e:
            failures += 1
            print(f'FAIL  {name}: {e}')
    print(f'\n{"ALL PASSED" if failures == 0 else f"{failures} FAILED"}')
    sys.exit(1 if failures else 0)


def test_inference_jpeg_round_trip_matches_how_training_crops_were_saved():
    """extract_frames.py saved crops with PIL's default JPEG settings; inference must apply the same round trip."""
    import io
    from PIL import Image
    import numpy as np
    from video_infer import training_style, TRAINING_JPEG_QUALITY
    rng = np.random.default_rng(0)
    im = Image.fromarray(rng.integers(0, 255, (224, 224, 3), dtype=np.uint8))
    default_buf, q_buf = io.BytesIO(), io.BytesIO()
    im.save(default_buf, format='JPEG')                       # what extract_frames.py does (no explicit quality)
    im.save(q_buf, format='JPEG', quality=TRAINING_JPEG_QUALITY)
    assert default_buf.getvalue() == q_buf.getvalue(), 'TRAINING_JPEG_QUALITY no longer equals PIL default'
    out = training_style(im)
    assert out.size == im.size and out.mode == 'RGB'
    assert np.abs(np.asarray(out, dtype=int) - np.asarray(im, dtype=int)).mean() > 0, 'round trip changed nothing'
