"""Voice-activity gate (Silero VAD): the audio branch only scores clips that contain speech.

    python scripts/vad.py"""

import os
import sys
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SR = 16000

# At least 1 s of speech, matching ASVspoof utterances (about 1 to 10 s).
MIN_SPEECH_SECONDS = 1.0

_model = None


def load_vad():
    """Load (and cache) the Silero VAD model. Downloads once, then offline."""
    global _model
    if _model is None:
        from silero_vad import load_silero_vad
        _model = load_silero_vad()
    return _model


def vad_available() -> bool:
    """True if the VAD dependency is importable, mirroring the app's other guards."""
    try:
        load_vad()
        return True
    except Exception:
        return False


@dataclass
class VADResult:
    has_speech: bool
    speech_seconds: float
    total_seconds: float
    speech_ratio: float                       # fraction of the clip that is speech
    segments: List[dict] = field(default_factory=list)   # [{'start': s, 'end': s}]
    reason: str = ''

    def __str__(self):
        return (f'VADResult(has_speech={self.has_speech}, '
                f'speech={self.speech_seconds:.2f}s/{self.total_seconds:.2f}s, '
                f'ratio={self.speech_ratio:.2%}, segments={len(self.segments)})')


def analyse(waveform: np.ndarray, sr: int = SR,
            min_speech_seconds: float = MIN_SPEECH_SECONDS) -> VADResult:
    """Detect speech in a 1-D float32 waveform; returns the gate decision and the evidence behind it."""
    import torch

    if waveform is None or waveform.size == 0:
        return VADResult(False, 0.0, 0.0, 0.0, [], 'empty waveform')

    total_seconds = float(waveform.size) / sr
    model = load_vad()
    from silero_vad import get_speech_timestamps

    audio = torch.from_numpy(np.ascontiguousarray(waveform, dtype=np.float32))
    stamps = get_speech_timestamps(audio, model, sampling_rate=sr,
                                   return_seconds=True)

    segments = [{'start': float(s['start']), 'end': float(s['end'])} for s in stamps]
    speech_seconds = float(sum(s['end'] - s['start'] for s in segments))
    ratio = speech_seconds / total_seconds if total_seconds > 0 else 0.0
    ok = speech_seconds >= min_speech_seconds

    if ok:
        reason = (f'{speech_seconds:.2f}s of speech detected across '
                  f'{len(segments)} segment(s)')
    elif not segments:
        reason = 'no speech detected — audio appears to be non-speech (music, tone or noise)'
    else:
        reason = (f'only {speech_seconds:.2f}s of speech detected '
                  f'(minimum {min_speech_seconds:.1f}s)')

    return VADResult(ok, speech_seconds, total_seconds, ratio, segments, reason)


def has_speech(waveform: np.ndarray, sr: int = SR,
               min_speech_seconds: float = MIN_SPEECH_SECONDS) -> bool:
    """Convenience boolean gate."""
    return analyse(waveform, sr, min_speech_seconds).has_speech


def _demo():
    """Run the gate on signals with known answers: a tone and noise (not speech) and the text-to-speech fixture (speech)."""
    import wave
    from pathlib import Path

    root = Path(__file__).resolve().parent.parent
    print('=' * 72)
    print('VAD GATE — behaviour on known-ground-truth signals')
    print('=' * 72)

    if not vad_available():
        print('FAIL: silero-vad not installed (pip install silero-vad)')
        return 1

    rng = np.random.default_rng(42)
    t = np.linspace(0, 5.0, SR * 5, endpoint=False)

    cases = [('sine tone 200Hz (NOT speech)',
              (0.5 * np.sin(2 * np.pi * 200 * t)).astype(np.float32)),
             ('white noise (NOT speech)',
              rng.standard_normal(t.shape).astype(np.float32) * 0.3),
             ('digital silence (NOT speech)',
              np.zeros(SR * 5, dtype=np.float32))]

    fixture = root / 'tests' / 'fixtures' / 'speech_sample.wav'
    if fixture.exists():
        w = wave.open(str(fixture))
        a = (np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
             .astype(np.float32) / 32768.0)
        cases.append(('speech fixture (IS speech)', a))

    demo_clip = root / 'demo_videos' / 'sample_with_audio.mp4'
    if demo_clip.exists():
        from audio_branch import extract_audio_16k
        wav = extract_audio_16k(str(demo_clip))
        if wav is not None:
            cases.append(("bundled 'sample_with_audio.mp4'", wav))

    for name, wav in cases:
        r = analyse(wav)
        verdict = 'SPEECH -> audio branch RUNS' if r.has_speech else 'NO SPEECH -> branch GATED OFF'
        print(f'\n- {name}')
        print(f'    {r}')
        print(f'    {verdict}  ({r.reason})')

    print('\n>>> The gate lets the audio branch run only on genuine speech, closing')
    print('the speech-only assumption stated in Ch3.4/Ch4.4. It says nothing about')
    print('whether that speech is bona-fide or spoofed — that is the SVM\'s job. <<<')
    return 0


if __name__ == '__main__':
    sys.exit(_demo())
