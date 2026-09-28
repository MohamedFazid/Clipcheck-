"""Tests for train_audio_svm.py on a synthetic mini-dataset in the official ASVspoof 2019 LA layout.
Checks the code path end to end and clear failures on bad layouts; says nothing about spoofing accuracy."""

import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from train_audio_svm import (  # noqa: E402
    PARTITIONS, resolve_paths, read_protocol, subsample, load_audio, SR,
)

SPEC = {'train': 8, 'dev': 4, 'eval': 4}   # utterances per partition (half spoof)


def _write_clip(path, kind, seconds=0.5, rng=None):
    import soundfile as sf
    rng = rng or np.random.default_rng(0)
    t = np.linspace(0, seconds, int(SR * seconds), endpoint=False)
    if kind == 'bonafide':
        wav = 0.4 * np.sin(2 * np.pi * rng.uniform(150, 250) * t)
    else:
        wav = 0.4 * rng.standard_normal(t.shape)
    sf.write(str(path), wav.astype(np.float32), SR, format='FLAC')


def build_fixture(root: Path):
    """Create a synthetic dataset mirroring the official LA layout."""
    rng = np.random.default_rng(42)
    la = root / 'LA'
    proto_dir = la / 'ASVspoof2019_LA_cm_protocols'
    proto_dir.mkdir(parents=True, exist_ok=True)

    for part, n in SPEC.items():
        subdir, proto_name = PARTITIONS[part]
        flac_dir = la / subdir / 'flac'
        flac_dir.mkdir(parents=True, exist_ok=True)
        lines = []
        for i in range(n):
            is_spoof = i % 2 == 1
            kind = 'spoof' if is_spoof else 'bonafide'
            utt = f'LA_{part[:1].upper()}_{i:07d}'
            _write_clip(flac_dir / f'{utt}.flac', kind, rng=rng)
            sys_id = f'A{i:02d}' if is_spoof else '-'
            # Official column order: speaker, utt_id, ..., system_id, key
            lines.append(f'LA_0001 {utt} - {sys_id} {kind}')
        (proto_dir / proto_name).write_text('\n'.join(lines) + '\n')
    return root


# ── Layout + protocol handling ──────────────────────────────────────────────

def test_resolve_paths_finds_official_layout():
    with tempfile.TemporaryDirectory() as td:
        root = build_fixture(Path(td))
        for part in PARTITIONS:
            flac_dir, proto = resolve_paths(root, part)
            assert flac_dir.is_dir() and proto.exists()


def test_resolve_paths_accepts_root_that_is_already_LA():
    """A common download shape: the user points at LA/ itself."""
    with tempfile.TemporaryDirectory() as td:
        root = build_fixture(Path(td))
        flac_dir, proto = resolve_paths(root / 'LA', 'train')
        assert flac_dir.is_dir() and proto.exists()


def test_missing_layout_fails_loudly_with_paths():
    with tempfile.TemporaryDirectory() as td:
        try:
            resolve_paths(Path(td), 'train')
            assert False, 'expected FileNotFoundError for an empty directory'
        except FileNotFoundError as e:
            assert 'Missing' in str(e), 'error should name the paths it tried'


def test_read_protocol_parses_ids_and_labels():
    with tempfile.TemporaryDirectory() as td:
        root = build_fixture(Path(td))
        _, proto = resolve_paths(root, 'train')
        items = read_protocol(proto)
        assert len(items) == SPEC['train']
        assert all(l in (0, 1) for _, l in items)
        assert sum(l for _, l in items) == SPEC['train'] // 2, 'expected half spoof'


def test_read_protocol_rejects_unknown_key():
    """A malformed key must fail rather than be silently coerced to a class."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / 'bad.txt'
        p.write_text('LA_0001 LA_T_0000001 - A01 notakey\n')
        try:
            read_protocol(p)
            assert False, 'expected ValueError for an unrecognised label'
        except ValueError as e:
            assert 'bonafide' in str(e)


def test_subsample_is_balanced_and_deterministic():
    items = [(f'u{i}', i % 2) for i in range(100)]
    a = subsample(items, 10, seed=42)
    b = subsample(items, 10, seed=42)
    assert a == b, 'subsampling must be reproducible for a fixed seed'
    assert sum(1 for _, l in a if l == 0) == 10
    assert sum(1 for _, l in a if l == 1) == 10
    assert subsample(items, None) is items, 'None must pass items through unchanged'


def test_load_audio_returns_mono_float32_at_16k():
    with tempfile.TemporaryDirectory() as td:
        root = build_fixture(Path(td))
        flac_dir, proto = resolve_paths(root, 'train')
        utt = read_protocol(proto)[0][0]
        wav = load_audio(flac_dir / f'{utt}.flac')
        assert wav.dtype == np.float32 and wav.ndim == 1 and wav.size > 0


# ── End-to-end: embed -> fit -> EER over the synthetic layout ───────────────

def test_end_to_end_pipeline_over_synthetic_dataset():
    """Drives the real embed/fit/score path. Proves the plumbing works before
    the real data lands; says nothing about spoofing accuracy (see docstring)."""
    from audio_branch import load_encoder, AudioSpoofSVM
    from train_audio_svm import embed_partition
    from utils import compute_eer
    import train_audio_svm as tas

    with tempfile.TemporaryDirectory() as td:
        root = build_fixture(Path(td))
        # Redirect the embedding cache into the temp dir so the test leaves
        # nothing behind in results/.
        original_cache = tas.CACHE_DIR
        tas.CACHE_DIR = Path(td) / 'cache'
        try:
            fe, enc, device = load_encoder('cpu')
            out = {}
            for part in ('train', 'eval'):
                flac_dir, proto = resolve_paths(root, part)
                items = read_protocol(proto)
                out[part] = embed_partition(part, items, flac_dir, fe, enc, device)

            Xtr, ytr, _ = out['train']
            Xev, yev, _ = out['eval']
            assert Xtr.shape[1] == 768, f'expected 768-d embeddings, got {Xtr.shape}'
            assert len(ytr) == SPEC['train']

            model = AudioSpoofSVM(seed=42).fit(Xtr, ytr)
            scores = model.spoof_score(Xev)
            assert scores.shape == (SPEC['eval'],)
            eer, thr = compute_eer(yev, scores)
            assert 0.0 <= eer <= 1.0, f'EER out of range: {eer}'
        finally:
            tas.CACHE_DIR = original_cache


def test_embedding_cache_is_reused():
    """Second pass must hit the cache: re-embedding 25k utterances by accident
    would cost hours."""
    from audio_branch import load_encoder
    from train_audio_svm import embed_partition
    import train_audio_svm as tas

    with tempfile.TemporaryDirectory() as td:
        root = build_fixture(Path(td))
        original_cache = tas.CACHE_DIR
        tas.CACHE_DIR = Path(td) / 'cache'
        try:
            fe, enc, device = load_encoder('cpu')
            flac_dir, proto = resolve_paths(root, 'train')
            items = read_protocol(proto)
            X1, y1, _ = embed_partition('train', items, flac_dir, fe, enc, device)
            cached = sorted(tas.CACHE_DIR.glob('*.npz'))
            assert cached, 'no cache file written'
            X2, y2, _ = embed_partition('train', items, flac_dir, fe, enc, device)
            assert np.allclose(X1, X2) and np.array_equal(y1, y2)
        finally:
            tas.CACHE_DIR = original_cache


if __name__ == '__main__':
    tests = [(k, v) for k, v in sorted(globals().items()) if k.startswith('test_')]
    failures = 0
    for name, fn in tests:
        try:
            fn()
            print(f'PASS  {name}')
        except AssertionError as e:
            failures += 1
            print(f'FAIL  {name}: {e}')
        except Exception as e:
            failures += 1
            print(f'ERROR {name}: {type(e).__name__}: {e}')
    print(f'\n{"ALL PASSED" if failures == 0 else f"{failures} FAILED"}')
    sys.exit(1 if failures else 0)
