"""Audio anti-spoofing branch: wav2vec2-base (frozen) embedding and an RBF SVM trained on ASVspoof 2019 LA.

STATUS (updated 2026-09-25): trained and evaluated on the full ASVspoof 2019 LA partitions (eval EER 3.96%, balanced accuracy 95.7%;
`results/audio_branch/metrics.json`, ledger A-series) and used by the app. The "no trained model" paragraph further down is the
original note from before the dataset arrived; it is kept for the record and no longer describes the code.

Architecture (mirrors the PPR design):
    raw waveform (16 kHz) -> wav2vec2 SSL encoder -> mean-pooled 768-d embedding
    -> SVM (bona-fide vs spoof) -> spoof score -> EER

IMPORTANT (no fabrication): there is NO trained model or real metric here. The
ASVspoof 2019 LA dataset is not available on disk, so this file implements and
*verifies that the pipeline executes end to end*. The __main__ block runs it on
SYNTHETIC placeholder audio — a PLUMBING TEST that proves the code path works, NOT
an anti-spoofing result. A real EER requires training/evaluating on ASVspoof 2019 LA
(specified as a pending experiment in the report).

Run (base env has transformers + soundfile + sklearn):
    /opt/anaconda3/bin/python scripts/audio_branch.py
"""

import os
import sys

# Force transformers to the torch backend only: this base env has a broken
# TensorFlow/protobuf install that otherwise crashes the wav2vec2 import.
os.environ.setdefault('USE_TF', '0')
os.environ.setdefault('USE_FLAX', '0')
os.environ.setdefault('TRANSFORMERS_NO_ADVISORY_WARNINGS', '1')

import numpy as np
import torch
from transformers import AutoModel, AutoFeatureExtractor
from sklearn.svm import SVC
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import compute_eer, set_seed, MODELS_DIR

SR = 16000
MODEL_NAME = 'facebook/wav2vec2-base'   # SSL pretrained encoder (not fine-tuned)
TRAINED_SVM_PATH = MODELS_DIR / 'audio_spoof_svm.joblib'


def load_encoder(device='cpu'):
    """Load the wav2vec2 feature extractor + SSL encoder (downloads on first use)."""
    fe = AutoFeatureExtractor.from_pretrained(MODEL_NAME)
    enc = AutoModel.from_pretrained(MODEL_NAME).to(device).eval()
    return fe, enc, device


def extract_audio_16k(video_path):
    """Decode a video's audio track to a mono 16 kHz float32 waveform.

    Uses the ffmpeg binary bundled by imageio-ffmpeg (no system ffmpeg needed).
    Returns a 1-D np.float32 array, or None if the clip has no decodable audio.
    """
    import subprocess
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [ffmpeg, '-i', str(video_path), '-vn', '-ac', '1', '-ar', str(SR),
           '-f', 'f32le', '-loglevel', 'error', '-']
    proc = subprocess.run(cmd, capture_output=True)
    if proc.returncode != 0 or not proc.stdout:
        return None
    wav = np.frombuffer(proc.stdout, dtype=np.float32).copy()
    return wav if wav.size > 0 else None


@torch.no_grad()
def embed_waveform(waveform, fe, enc, device='cpu', sr=SR):
    """1-D waveform (float32 @ sr) -> mean-pooled 768-d wav2vec2 embedding."""
    inputs = fe(waveform, sampling_rate=sr, return_tensors='pt')
    hidden = enc(inputs.input_values.to(device)).last_hidden_state  # (1, T, 768)
    return hidden.mean(dim=1).squeeze(0).cpu().numpy()              # (768,)


class AudioSpoofSVM:
    """SVM back-end: bona-fide (0) vs spoof (1). Score = signed SVM margin.

    probability=True adds Platt scaling (5-fold internal CV during fit) so
    spoof_probability() can return a calibrated P(spoof) in [0, 1] for fusion;
    it does not touch decision_function() or predict(), so spoof_score(), the
    EER computed from it, and .clf.predict() accuracy are unaffected -- the
    reported ASVspoof metrics (train_audio_svm.py) are identical either way.
    """

    def __init__(self, seed=42):
        self.clf = make_pipeline(
            StandardScaler(),
            SVC(kernel='rbf', C=1.0, random_state=seed, probability=True))

    def fit(self, X, y):
        self.clf.fit(X, y)
        return self

    def spoof_score(self, X):
        return self.clf.decision_function(X)   # higher = more spoof-like

    def spoof_probability(self, X):
        """Calibrated P(spoof) in [0, 1], suitable as P(audio_fake) for fusion.fuse().
        classes_ is [0, 1] (bona fide, spoof), so column 1 is P(spoof)."""
        return self.clf.predict_proba(X)[:, 1]


def load_trained_svm(path=None):
    """Load a trained AudioSpoofSVM checkpoint (scripts/train_audio_svm.py's
    output), or return None if it hasn't been trained yet (ASVspoof pending).

    Built ahead of the data landing, matching this project's pattern elsewhere
    (train_audio_svm.py itself): so the app/report need zero further code
    changes the moment ASVspoof 2019 LA is obtained and the SVM is trained.
    """
    path = path or TRAINED_SVM_PATH
    if not os.path.exists(path):
        return None
    import joblib
    saved = joblib.load(path)
    return saved['model']   # AudioSpoofSVM instance; saved['threshold']/['C'] also available


def _synthetic_clip(kind, seconds=1.0, sr=SR, rng=None):
    """Placeholder audio ONLY for the plumbing test (not real speech)."""
    rng = rng or np.random.default_rng()
    t = np.linspace(0, seconds, int(sr * seconds), endpoint=False)
    if kind == 'tone':
        f = rng.uniform(120, 300)
        wav = 0.5 * np.sin(2 * np.pi * f * t) + 0.01 * rng.standard_normal(t.shape)
    else:  # 'noise'
        wav = rng.standard_normal(t.shape)
    return wav.astype(np.float32)


def _plumbing_test():
    print('=' * 64)
    print('AUDIO BRANCH — PLUMBING TEST on SYNTHETIC audio')
    print('This proves the pipeline executes end to end. It is NOT an')
    print('anti-spoofing metric — a real EER needs ASVspoof 2019 LA (pending).')
    print('=' * 64)
    set_seed(42)
    rng = np.random.default_rng(42)
    fe, enc, device = load_encoder('cpu')
    print(f'Loaded {MODEL_NAME} (hidden size {enc.config.hidden_size}) on {device}')

    # Build a tiny 2-class placeholder set and embed it.
    clips, labels = [], []
    for _ in range(10):
        clips.append(_synthetic_clip('tone', rng=rng)); labels.append(0)   # "bona-fide"
        clips.append(_synthetic_clip('noise', rng=rng)); labels.append(1)  # "spoof"
    X = np.stack([embed_waveform(c, fe, enc, device) for c in clips])
    y = np.array(labels)
    print(f'Embeddings: {X.shape}  (n_clips x wav2vec2 dim)')

    # Split, fit SVM, compute EER — verifies the full code path runs.
    idx = rng.permutation(len(y))
    tr, te = idx[:14], idx[14:]
    model = AudioSpoofSVM(seed=42).fit(X[tr], y[tr])
    scores = model.spoof_score(X[te])
    eer, thr = compute_eer(y[te], scores)
    print(f'Pipeline OK. Held-out EER (SYNTHETIC, meaningless): {eer*100:.2f}%')
    print('\n>>> Pipeline verified. Real evaluation on ASVspoof 2019 LA is PENDING. <<<')


if __name__ == '__main__':
    _plumbing_test()
