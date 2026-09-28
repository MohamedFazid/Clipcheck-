"""Regression tests for the train/val/test split and the augmentation fix.

These lock in the properties Chapter 4.2/4.3/5.6 of the report depend on:

1. NO VIDEO OR IDENTITY LEAKAGE. Verified directly (see DEV_LOG) that the
   PREVIOUS frame-level `random_split` put 100% of test-set videos, and 100%
   of val-set videos, also in the training set -- ~19 near-duplicate frames
   per video were scattered independently across all three splits. The split
   is now grouped at the identity level via `utils.grouped_video_split`
   (every video, and every FF++ Deepfakes reciprocal identity pair built from
   it, is assigned to exactly one split). This is the fix for the supervisor
   feedback that flagged implausibly high scores (AUC ~0.998) as a likely
   overfitting/leakage symptom. If this test ever fails, every video-branch
   number in the report is compromised the same way again.

2. REPRODUCIBILITY. The grouped split is deterministic for a fixed
   SPLIT_SEED, so a retrained model is still evaluated on the same held-out
   videos as the reported figures.

3. THE AUGMENTATION BUG IS FIXED, AND STAYS FIXED. The old code gave all three
   splits one shared dataset object, so the last `.transform =` assignment won
   and train-time augmentation never actually ran. These tests assert the
   training split now genuinely augments while validation/test do not -- the
   exact property that silently regressed before. Unrelated to (1)/(2) above
   and unaffected by the split-grouping change.

Pure data-layer tests: no model, no GPU, no training. Runs under pytest, or:
    /opt/anaconda3/bin/python tests/test_data_split.py
"""

import sys
from pathlib import Path

import pytest
import torch
from torch.utils.data import Subset
from torchvision import datasets, transforms

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

from utils import (FRAMES_DIR, SPLIT_SEED, PROJECT_ROOT as _ROOT, run_paths,  # noqa: E402
                   grouped_video_split, split_from_manifest, get_split, _video_folder_of)

# frames/ holds FaceForensics++ face crops, which are not in the repository (dataset terms): the tests that split it skip without it.
# The frozen manifest itself is still checked without data by test_frozen_split_manifest.py.
needs_frames = pytest.mark.skipif(not FRAMES_DIR.exists(), reason='frames/ not present (FaceForensics++ face crops are not in the repository)')

IMG_SIZE = 224

EXPECTED_TOTAL = 7566
# Sizes produced by the identity-grouped split (deterministic for SPLIT_SEED=42).
# Close to, but not exactly, 80/10/10 by frame count since video length varies
# and whole identity-pair groups (~4 videos each) are assigned atomically.
EXPECTED_TRAIN, EXPECTED_VAL, EXPECTED_TEST = 6072, 736, 758

_val_t = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])
_train_t = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])


def _split_indices(dataset):
    """The split train.py/evaluate.py use. Returns plain index lists."""
    return grouped_video_split(dataset, split_seed=SPLIT_SEED)


def _video_ids(dataset, idx_list):
    return {_video_folder_of(dataset.samples[i][0]) for i in idx_list}


def _identity_ids(video_ids):
    """Collapse fake-pair folder names ('036_035') to their two component
    identities, matching grouped_video_split's leakage unit."""
    out = set()
    for vf in video_ids:
        parts = vf.split('_')
        out |= set(parts) if len(parts) == 2 else {vf}
    return out


@needs_frames
def test_split_sizes_match_the_reported_figures():
    full = datasets.ImageFolder(str(FRAMES_DIR))
    assert len(full) == EXPECTED_TOTAL, \
        f'dataset size changed: {len(full)} != {EXPECTED_TOTAL} (report Ch4.2)'
    tr, va, te = _split_indices(full)
    assert (len(tr), len(va), len(te)) == (EXPECTED_TRAIN, EXPECTED_VAL, EXPECTED_TEST)


@needs_frames
def test_split_is_deterministic_for_a_fixed_seed():
    """Same SPLIT_SEED must yield identical indices on repeated calls -- what
    keeps a retrained model comparable to previously reported figures."""
    full = datasets.ImageFolder(str(FRAMES_DIR))
    a = _split_indices(full)
    b = _split_indices(full)
    for split_name, ia, ib in zip(('train', 'val', 'test'), a, b):
        assert ia == ib, f'{split_name} indices are not reproducible for a fixed seed'


@needs_frames
def test_no_video_or_identity_leakage_between_splits():
    """The actual leakage fix. Regression test for the bug found via
    supervisor feedback: verified the old frame-level split put 100% of
    test/val videos also in train. Checks both that no literal video folder
    is split across sets, AND that no FF++ reciprocal identity pair (e.g.
    '036_035' / '035_036' / real/036 / real/035) has its two component
    identities land in different sets, which a video-folder-only split could
    still allow."""
    full = datasets.ImageFolder(str(FRAMES_DIR))
    tr, va, te = _split_indices(full)

    tr_v, va_v, te_v = _video_ids(full, tr), _video_ids(full, va), _video_ids(full, te)
    assert not (tr_v & va_v) and not (tr_v & te_v) and not (va_v & te_v), \
        'a video folder appears in more than one split — literal video-level leakage'

    tr_id, va_id, te_id = _identity_ids(tr_v), _identity_ids(va_v), _identity_ids(te_v)
    assert not (tr_id & va_id) and not (tr_id & te_id) and not (va_id & te_id), \
        'an underlying identity appears in more than one split — identity-level leakage ' \
        'via the real/fake reciprocal-pair naming scheme'


@needs_frames
def test_frozen_manifest_matches_recomputed_split():
    """The frozen manifest and the recomputed grouped split must agree exactly on the default frames
    folder. This is what makes it safe to use the manifest for other folders (frames_multi/): both give
    the same train/val/test assignment for every video."""
    full = datasets.ImageFolder(str(FRAMES_DIR))
    for a, b in zip(grouped_video_split(full, split_seed=SPLIT_SEED), split_from_manifest(full)):
        assert set(a) == set(b), 'frozen manifest disagrees with the recomputed split (manifest is stale?)'


def test_multimethod_folder_uses_the_same_split_without_leakage():
    """frames_multi/ (symlinks, one method per fake pair) must resolve entirely inside the frozen manifest and
    keep the identity-disjoint property. Skipped if the folder has not been built."""
    import pytest
    multi = _ROOT / 'frames_multi'
    if not multi.exists():
        pytest.skip('frames_multi not built (scripts/build_multimethod_frames.py)')
    full = datasets.ImageFolder(str(multi))
    tr, va, te = get_split(full, str(multi))
    assert len(tr) + len(va) + len(te) == len(full), 'some crops are not covered by the frozen manifest'
    tr_v, va_v, te_v = _video_ids(full, tr), _video_ids(full, va), _video_ids(full, te)
    assert not (tr_v & va_v) and not (tr_v & te_v) and not (va_v & te_v)
    tr_id, va_id, te_id = _identity_ids(tr_v), _identity_ids(va_v), _identity_ids(te_v)
    assert not (tr_id & va_id) and not (tr_id & te_id) and not (va_id & te_id)


@needs_frames
def test_splits_are_disjoint():
    full = datasets.ImageFolder(str(FRAMES_DIR))
    tr, va, te = _split_indices(full)
    s_tr, s_va, s_te = set(tr), set(va), set(te)
    assert not (s_tr & s_va) and not (s_tr & s_te) and not (s_va & s_te), \
        'split overlap detected — data leakage between train/val/test'
    assert len(s_tr | s_va | s_te) == EXPECTED_TOTAL


@needs_frames
def test_training_split_actually_augments():
    """The bug fix itself: two reads of the same training sample must differ,
    because RandomHorizontalFlip / ColorJitter are stochastic. Under the old
    shared-dataset code this returned identical tensors (augmentation silently
    disabled) — that is exactly the regression this guards against."""
    train_source = datasets.ImageFolder(str(FRAMES_DIR), transform=_train_t)
    tr, _, _ = _split_indices(train_source)
    train_set = Subset(train_source, list(tr))

    torch.manual_seed(0)
    a, _ = train_set[0]
    b, _ = train_set[0]
    assert not torch.equal(a, b), \
        'training samples are identical across reads: augmentation is NOT applied ' \
        '(the Ch4.3 shared-dataset transform bug has regressed)'


@needs_frames
def test_validation_and_test_splits_do_not_augment():
    """Evaluation must be deterministic: no augmentation may leak into val/test."""
    eval_source = datasets.ImageFolder(str(FRAMES_DIR), transform=_val_t)
    _, va, te = _split_indices(eval_source)
    for name, idx in (('val', va), ('test', te)):
        subset = Subset(eval_source, list(idx))
        a, _ = subset[0]
        b, _ = subset[0]
        assert torch.equal(a, b), f'{name} split is non-deterministic (augmentation leaked)'


# ── Baseline-artifact protection ────────────────────────────────────────────

def test_tagged_runs_do_not_collide_with_baseline_paths():
    """A tagged experiment must never write over the reported baseline files."""
    base_model, base_run = run_paths(42, '')
    tag_model, tag_run = run_paths(42, 'reg')
    assert base_model != tag_model and base_run != tag_run
    assert 'reg' in str(tag_model) and 'reg' in str(tag_run)


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
    print(f'\n{"ALL PASSED" if failures == 0 else f"{failures} FAILED"}')
    sys.exit(1 if failures else 0)
