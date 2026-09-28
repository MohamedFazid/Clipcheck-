"""Pipeline-correctness tests for the audio branch (scripts/audio_branch.py).

IMPORTANT (no fabrication): these are PIPELINE CORRECTNESS tests only. They
verify that extract_audio_16k(), embed_waveform(), and AudioSpoofSVM execute
correctly and produce outputs of the right shape/type. They are NOT
anti-spoofing validation and prove nothing about spoof-detection accuracy:
AudioSpoofSVM here is fit on tiny synthetic random data, not ASVspoof 2019 LA,
and its scores carry no genuine bona-fide/spoof meaning. Real anti-spoofing
evaluation remains pending (see Chapter 5 of the Draft Project Report).

Runs under pytest, or standalone:
    /opt/anaconda3/bin/python tests/test_audio_branch.py
"""

import os
import sys
from pathlib import Path

import pytest

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from audio_branch import extract_audio_16k, embed_waveform, load_encoder, AudioSpoofSVM, SR  # noqa: E402

DEMO = PROJECT_ROOT / 'demo_videos'
# FaceForensics++ demo clips are silent by design (confirmed empirically: see
# app.py's own comment on this). sample_with_audio.mp4 is the one bundled clip
# with a real audio track.
SILENT_CLIP = DEMO / 'original_sequences' / 'youtube' / 'c23' / 'videos' / '183.mp4'
AUDIO_CLIP = DEMO / 'sample_with_audio.mp4'

# Loaded once for all tests (wav2vec2 encoder load is the expensive part).
_fe, _enc, _device = load_encoder('cpu')


@pytest.mark.skipif(not SILENT_CLIP.exists(), reason='demo clip not present (dataset-derived, not in the repository)')
def test_extract_audio_16k_returns_none_for_silent_clip():
    assert SILENT_CLIP.exists(), f'demo clip missing: {SILENT_CLIP}'
    wav = extract_audio_16k(str(SILENT_CLIP))
    assert wav is None, 'expected None for a FaceForensics++ demo clip (silent by design)'


@pytest.mark.skipif(not AUDIO_CLIP.exists(), reason='demo clip not present (dataset-derived, not in the repository)')
def test_extract_audio_16k_returns_waveform_for_clip_with_audio():
    assert AUDIO_CLIP.exists(), f'demo clip missing: {AUDIO_CLIP}'
    wav = extract_audio_16k(str(AUDIO_CLIP))
    assert wav is not None
    assert isinstance(wav, np.ndarray)
    assert wav.dtype == np.float32
    assert wav.ndim == 1
    assert wav.size > 0


def test_embed_waveform_returns_768d_embedding():
    # Synthetic tone, matching the shape/kind of placeholder audio the module's
    # own plumbing test uses -- not real speech.
    t = np.linspace(0, 1.0, SR, endpoint=False)
    wav = (0.5 * np.sin(2 * np.pi * 200 * t)).astype(np.float32)
    emb = embed_waveform(wav, _fe, _enc, _device)
    assert isinstance(emb, np.ndarray)
    assert emb.shape == (768,)
    assert np.all(np.isfinite(emb))


def test_audio_spoof_svm_fit_and_score_run_without_error():
    # Small synthetic 2-class embedding-shaped dataset (768-d random vectors).
    # This is NOT real audio embeddings and NOT a spoofing-detection
    # validation -- it only checks the sklearn wrapper's fit/score plumbing.
    rng = np.random.default_rng(42)
    X = rng.standard_normal((20, 768)).astype(np.float32)
    y = np.array([0, 1] * 10)
    model = AudioSpoofSVM(seed=42).fit(X, y)
    scores = model.spoof_score(X)
    assert isinstance(scores, np.ndarray)
    assert scores.shape == (20,)
    assert np.all(np.isfinite(scores)), 'spoof_score produced NaN/inf on a well-formed input'


if __name__ == '__main__':
    failures = 0
    for name, fn in [
        ('extract_audio_16k -> None for silent clip', test_extract_audio_16k_returns_none_for_silent_clip),
        ('extract_audio_16k -> waveform for clip with audio', test_extract_audio_16k_returns_waveform_for_clip_with_audio),
        ('embed_waveform -> 768-d embedding', test_embed_waveform_returns_768d_embedding),
        ('AudioSpoofSVM.fit/.spoof_score run without error', test_audio_spoof_svm_fit_and_score_run_without_error),
    ]:
        try:
            fn()
            print(f'PASS  {name}')
        except AssertionError as e:
            failures += 1
            print(f'FAIL  {name}: {e}')
    print(f'\n{"ALL PASSED" if failures == 0 else f"{failures} FAILED"}')
    sys.exit(1 if failures else 0)
