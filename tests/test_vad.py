"""Tests for the VAD gate (scripts/vad.py).

These are TRUE correctness tests, not plumbing checks: every case has ground
truth that is definitional rather than assumed.

  * A sine tone, white noise and digital silence are not speech BY
    CONSTRUCTION -- no judgement call is involved in labelling them.
  * tests/fixtures/speech_sample.wav is macOS `say` output: synthetic, but
    acoustically speech (formants, prosody, inter-word pauses), which is
    exactly what a VAD is meant to fire on. Regenerate it with:
        say -v Samantha -o /tmp/s.aiff "…" && ffmpeg -i /tmp/s.aiff \
            -ac 1 -ar 16000 tests/fixtures/speech_sample.wav

The gate's purpose (Ch3.4/Ch4.4) is to stop the untrained-on-non-speech spoof
classifier from being handed music/tones/noise and producing an
out-of-distribution number that would look like a real spoof judgement.

Skips if silero-vad is not installed. Runs under pytest, or:
    /opt/anaconda3/bin/python tests/test_vad.py
"""

import sys
import wave
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from vad import analyse, has_speech, vad_available, SR  # noqa: E402

VAD_UP = vad_available()
SKIP_REASON = 'silero-vad not installed'

try:
    import pytest
    pytestmark = pytest.mark.skipif(not VAD_UP, reason=SKIP_REASON)
except ImportError:
    pytest = None

FIXTURE = PROJECT_ROOT / 'tests' / 'fixtures' / 'speech_sample.wav'
TONE_CLIP = PROJECT_ROOT / 'demo_videos' / 'sample_with_audio.mp4'
_RNG = np.random.default_rng(42)


def _tone(seconds=5.0, freq=200.0):
    t = np.linspace(0, seconds, int(SR * seconds), endpoint=False)
    return (0.5 * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def _noise(seconds=5.0):
    return (_RNG.standard_normal(int(SR * seconds)) * 0.3).astype(np.float32)


def _silence(seconds=5.0):
    return np.zeros(int(SR * seconds), dtype=np.float32)


def _load_wav(path):
    w = wave.open(str(path))
    frames = w.readframes(w.getnframes())
    return np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0


# ── Non-speech must be rejected (the whole point of the gate) ────────────────

def test_pure_tone_is_not_speech():
    r = analyse(_tone())
    assert not r.has_speech, f'a sine tone was accepted as speech: {r}'
    assert r.speech_seconds == 0.0


def test_white_noise_is_not_speech():
    assert not has_speech(_noise()), 'white noise was accepted as speech'


def test_silence_is_not_speech():
    assert not has_speech(_silence()), 'digital silence was accepted as speech'


def test_empty_waveform_is_handled():
    r = analyse(np.array([], dtype=np.float32))
    assert not r.has_speech
    assert r.total_seconds == 0.0


# ── Genuine speech must be accepted ─────────────────────────────────────────

def test_speech_fixture_is_detected_as_speech():
    assert FIXTURE.exists(), f'missing fixture: {FIXTURE} (see module docstring)'
    r = analyse(_load_wav(FIXTURE))
    assert r.has_speech, f'genuine speech was rejected: {r}'
    assert r.speech_seconds >= 1.0
    assert r.segments, 'no speech segments returned for speech input'


def test_speech_ratio_is_high_for_speech_and_zero_for_tone():
    """The gate should separate the two cases by a wide margin, not marginally."""
    speech_ratio = analyse(_load_wav(FIXTURE)).speech_ratio
    tone_ratio = analyse(_tone()).speech_ratio
    assert speech_ratio > 0.5, f'speech ratio unexpectedly low: {speech_ratio:.2%}'
    assert tone_ratio == 0.0
    assert speech_ratio - tone_ratio > 0.4, 'gate does not separate the classes clearly'


# ── The project's own bundled clip: a documented non-speech case ────────────

def test_bundled_sample_with_audio_is_not_speech():
    """The one bundled clip with an audio track carries a constant low-frequency
    tone, not speech (frame-energy dynamic range ~0.2 dB; 84% of energy below
    300 Hz). It therefore exercises exactly the out-of-distribution case Ch3.4
    describes, and the gate must reject it. If this ever fails, the fixture has
    been replaced and the audio-branch documentation needs revisiting."""
    if not TONE_CLIP.exists():
        return
    from audio_branch import extract_audio_16k
    wav = extract_audio_16k(str(TONE_CLIP))
    assert wav is not None, 'expected a decodable audio track in sample_with_audio.mp4'
    r = analyse(wav)
    assert not r.has_speech, \
        f'bundled tone clip was accepted as speech: {r} — gate is not working'


# ── Gate threshold behaviour ────────────────────────────────────────────────

def test_min_speech_seconds_threshold_is_enforced():
    """A clip with real but very brief speech should fail a stricter gate."""
    speech = _load_wav(FIXTURE)
    lenient = analyse(speech, min_speech_seconds=1.0)
    strict = analyse(speech, min_speech_seconds=999.0)
    assert lenient.has_speech
    assert not strict.has_speech, 'min_speech_seconds threshold was ignored'
    # The measurement itself must not change with the threshold, only the verdict.
    assert lenient.speech_seconds == strict.speech_seconds


if __name__ == '__main__':
    if not VAD_UP:
        print(f'SKIP: {SKIP_REASON}  (pip install silero-vad)')
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
