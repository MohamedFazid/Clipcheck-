"""Shared utilities for the deepfake video branch.

Provides:
  * PROJECT_ROOT / standard directory paths, derived from this file's location
    (no dependence on any hardcoded project-folder path).
  * set_seed(): seed every RNG source so training/eval runs are reproducible.

NOTE on determinism: on the Apple MPS backend full bit-exact determinism is not
guaranteed even with all seeds fixed. Seeding collapses the large run-to-run
variance (classifier-head init, shuffle order, augmentation); any residual tiny
variance is expected and is captured by the mean +/- std reporting in A1.
"""

import json
import os
import random
from pathlib import Path

import numpy as np
import torch

# ── Project paths (script lives in <root>/scripts/) ──────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRAMES_DIR   = PROJECT_ROOT / 'frames'
MODELS_DIR   = PROJECT_ROOT / 'models'
RESULTS_DIR  = PROJECT_ROOT / 'results'
RUNS_DIR     = RESULTS_DIR / 'runs'          # per-seed metrics/plots
SUMMARY_DIR  = RESULTS_DIR / 'summary'       # aggregated mean +/- std
MODEL_RUNS_DIR = MODELS_DIR / 'runs'         # per-seed model checkpoints

# Data split is held FIXED across every run so mean +/- std reflects *training*
# stochasticity on one common test set, not split variation.
SPLIT_SEED = 42


def run_paths(seed: int, tag: str = ''):
    """Return (model_checkpoint_path, results_run_dir) for a training run.

    An empty tag keeps the ORIGINAL baseline layout used by the figures already
    reported in the Draft Project Report:
        models/runs/seed42.pth        results/runs/seed42/
    A non-empty tag isolates a variant in its own subdirectory:
        models/runs/reg/seed42.pth    results/runs/reg/seed42/
    so re-running an experiment can never overwrite the reported baseline
    artifacts.
    """
    if tag:
        return (MODEL_RUNS_DIR / tag / f'seed{seed}.pth',
                RUNS_DIR / tag / f'seed{seed}')
    return MODEL_RUNS_DIR / f'seed{seed}.pth', RUNS_DIR / f'seed{seed}'


def set_seed(seed: int) -> None:
    """Seed Python, NumPy and torch (CPU + MPS/CUDA) for reproducible runs."""
    os.environ['PYTHONHASHSEED'] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if hasattr(torch, 'mps') and torch.backends.mps.is_available():
        torch.mps.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    # cudnn flags are no-ops on MPS but harmless; set for portability.
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def get_device() -> torch.device:
    return torch.device('mps' if torch.backends.mps.is_available() else 'cpu')


def compute_eer(y_true, scores):
    """Equal Error Rate: the operating point where the false-acceptance rate
    (FAR = fpr) equals the false-rejection rate (FRR = 1 - tpr).

    y_true: 1 for the positive (fake) class, 0 otherwise.
    scores: P(fake). Returns (eer, threshold).
    """
    from sklearn.metrics import roc_curve
    fpr, tpr, thr = roc_curve(y_true, scores)
    fnr = 1 - tpr
    idx = int(np.nanargmin(np.abs(fnr - fpr)))
    eer = float((fpr[idx] + fnr[idx]) / 2)
    return eer, float(thr[idx])


def _video_folder_of(path: str) -> str:
    """The per-video folder a frame file lives in, e.g. '.../frames/real/036/
    frame_00000.jpg' -> '036', '.../frames/fake/036_035/frame_00000.jpg' ->
    '036_035'."""
    return Path(path).parts[-2]


def grouped_video_split(dataset, split_seed: int = SPLIT_SEED,
                        train_frac: float = 0.8, val_frac: float = 0.1):
    """Identity-disjoint train/val/test split over an ImageFolder of face
    crops, replacing a frame-level random_split.

    WHY THIS EXISTS: the previous split (torch random_split over every
    individual frame) had no notion of "video" at all. Verified directly:
    100% of the old test split's distinct videos also had frames in the old
    train split, and 100% of the old val split's videos did too, because
    ~19 near-duplicate frames per video (same face, lighting, background)
    were scattered independently across all three sets. A model can then
    partly solve the task by recognising "I've seen this exact video before"
    rather than learning generalisable manipulation artefacts, which
    plausibly explains implausibly high scores (AUC ~0.998), a validation
    set that no longer reveals true overfitting because it leaks the same
    way as the test set, and 3-seed comparisons that vary only training
    stochasticity on an otherwise-identical (leaking) split -- exactly the
    issues raised in supervisor feedback on the Draft Report.

    A second, subtler leak: FF++ Deepfakes videos are released as
    reciprocal identity pairs (both '036_035' and '035_036' exist, i.e. two
    real identities' faces swapped onto each other's footage). Splitting by
    video FOLDER alone would still let identity 036's face appear in both
    train (as real/036 or fake/035_036) and test (as fake/036_035), leaking
    the same face's appearance across the split even with zero literal
    video-file overlap. This function instead groups by underlying identity:
    every real id and every fake pair built from it are assigned to the
    split as one atomic unit, via union-find over the id graph (edges are
    the two ids named in each fake pair folder).

    Group (not frame) count determines the 80/10/10 target, accumulated by
    frame count in shuffled group order, so the realised split sizes won't
    be exactly 80/10/10 (video lengths vary slightly) but are close.

    Returns (train_idx, val_idx, test_idx): plain lists of dataset indices,
    a drop-in replacement for the three lists random_split used to return.
    """
    from collections import defaultdict

    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    video_folders = {_video_folder_of(p) for p, _ in dataset.samples}
    for vf in video_folders:
        parts = vf.split('_')
        if len(parts) == 2:
            union(parts[0], parts[1])
        else:
            find(vf)

    def group_of(vf: str) -> str:
        parts = vf.split('_')
        return find(parts[0]) if len(parts) == 2 else find(vf)

    group_indices = defaultdict(list)
    for idx, (path, _label) in enumerate(dataset.samples):
        group_indices[group_of(_video_folder_of(path))].append(idx)

    groups = list(group_indices.keys())
    random.Random(split_seed).shuffle(groups)

    n_total = len(dataset.samples)
    n_train_target = int(train_frac * n_total)
    n_val_target = int(val_frac * n_total)

    train_idx, val_idx, test_idx = [], [], []
    running = 0
    for g in groups:
        idxs = group_indices[g]
        if running < n_train_target:
            train_idx.extend(idxs)
        elif running < n_train_target + n_val_target:
            val_idx.extend(idxs)
        else:
            test_idx.extend(idxs)
        running += len(idxs)

    return train_idx, val_idx, test_idx


SPLIT_MANIFEST = PROJECT_ROOT / 'data_splits' / 'split_v2_identity_grouped.json'


def split_from_manifest(dataset, manifest_path=None):
    """Train/val/test indices read from the FROZEN split manifest (scripts/freeze_split.py).

    Used for any frames folder other than the default (for example the multi-method folder, where crop
    counts per video differ and a recomputed frame-count split could shift group boundaries). Every
    'class/video-folder' key must exist in the manifest, so a folder that drifts from the frozen split
    fails loudly instead of silently changing the split.
    """
    assign = json.load(open(manifest_path or SPLIT_MANIFEST))['assignment']
    out = {'train': [], 'val': [], 'test': []}
    missing = set()
    for i, (path, label) in enumerate(dataset.samples):
        key = f'{dataset.classes[label]}/{_video_folder_of(path)}'
        split = assign.get(key)
        if split is None:
            missing.add(key)
        else:
            out[split].append(i)
    if missing:
        raise ValueError(f'{len(missing)} video folders are not in the frozen split manifest, e.g. '
                         f'{sorted(missing)[:3]}')
    return out['train'], out['val'], out['test']


def get_split(dataset, frames_dir=None, split_seed: int = SPLIT_SEED, fold=None):
    """Default frames folder: the original recomputed grouped split (keeps every existing result
    reproducible). Any other folder: the frozen manifest. With fold=k: cross-validation fold k from the frozen
    CV manifest (works for any folder that uses the manifest's video names)."""
    if fold is not None:
        return split_from_cv_manifest(dataset, fold)
    if frames_dir is None or Path(frames_dir).resolve() == FRAMES_DIR.resolve():
        return grouped_video_split(dataset, split_seed=split_seed)
    return split_from_manifest(dataset)


CV_MANIFEST = PROJECT_ROOT / 'data_splits' / 'cv5_identity_grouped.json'


def identity_groups_from_keys(keys):
    """Group manifest keys ('real/036', 'fake/036_035') into identity groups by union-find over the ids they name.
    FF++ fakes are reciprocal identity pairs, so a group is 2 real + 2 fake videos. Needs no dataset, only names."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def ids_of(key):
        folder = key.split('/', 1)[1]
        parts = folder.split('_')
        return parts if len(parts) == 2 else [folder]

    for k in keys:
        ids = ids_of(k)
        for other in ids[1:]:
            ra, rb = find(ids[0]), find(other)
            if ra != rb:
                parent[ra] = rb
        find(ids[0])
    groups = {}
    for k in keys:
        groups.setdefault(find(ids_of(k)[0]), []).append(k)
    return groups


def split_from_cv_manifest(dataset, fold, manifest_path=None):
    """Train/val/test indices for one cross-validation fold, from the frozen CV manifest
    (scripts/freeze_cv_folds.py). Every 'class/video-folder' key must be present."""
    roles = json.load(open(manifest_path or CV_MANIFEST))['folds'][str(fold)]
    out = {'train': [], 'val': [], 'test': []}
    missing = set()
    for i, (path, label) in enumerate(dataset.samples):
        key = f'{dataset.classes[label]}/{_video_folder_of(path)}'
        role = roles.get(key)
        if role is None:
            missing.add(key)
        else:
            out[role].append(i)
    if missing:
        raise ValueError(f'{len(missing)} video folders are not in the CV manifest, e.g. {sorted(missing)[:3]}')
    return out['train'], out['val'], out['test']
