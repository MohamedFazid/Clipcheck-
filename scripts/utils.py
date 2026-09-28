"""Shared paths and helpers for the video branch (seeding, splits, EER).
MPS is not bit-exact even when seeded, so results are reported as mean +/- std over seeds."""

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
    """Return (checkpoint_path, results_dir): an empty tag keeps the original layout, a tag gets its own subfolder."""
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
    """Equal Error Rate: where false-acceptance equals false-rejection. y_true 1 = fake, scores = P(fake); returns (eer, threshold)."""
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
    """Identity-disjoint train/val/test split: each real identity and every fake pair built from it (union-find) stays in one split.
    Replaces a frame-level random_split that leaked every test video into training. Returns (train_idx, val_idx, test_idx)."""
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
    """Train/val/test indices from the frozen split manifest; fails loudly if a folder is not in it."""
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
