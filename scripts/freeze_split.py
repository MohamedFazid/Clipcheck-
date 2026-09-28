"""Freeze the current identity-grouped split into a manifest with a hash.

Writes data_splits/split_v2_identity_grouped.json: for every video folder, which
split it belongs to, plus per-split counts and a SHA-256 over the sorted
(video, split) assignments. Any result can then cite "split v2, hash <first 12>",
and tests/CI can assert the hash has not silently changed.

split v1 = the original frame-level random_split (leaky, SUPERSEDED, kept only
as a description; it is not regenerated here).
split v2 = utils.grouped_video_split (identity-disjoint), SPLIT_SEED=42.

Run:  /opt/anaconda3/bin/python scripts/freeze_split.py
"""
import hashlib
import json
import os
import sys
from collections import defaultdict

from torchvision import datasets

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import FRAMES_DIR, PROJECT_ROOT, SPLIT_SEED, grouped_video_split, _video_folder_of

ds = datasets.ImageFolder(str(FRAMES_DIR))
train_idx, val_idx, test_idx = grouped_video_split(ds, split_seed=SPLIT_SEED)

assignment, frames = {}, defaultdict(lambda: defaultdict(int))
for name, idxs in (('train', train_idx), ('val', val_idx), ('test', test_idx)):
    for i in idxs:
        path, label = ds.samples[i]
        vf = _video_folder_of(path)
        key = f'{ds.classes[label]}/{vf}'
        assignment[key] = name
        frames[name][key] += 1

canon = json.dumps(sorted(assignment.items()), separators=(',', ':')).encode()
digest = hashlib.sha256(canon).hexdigest()

out = {
    'name': 'split_v2_identity_grouped',
    'supersedes': 'split_v1 (frame-level random_split, leaked: 100% of test and val videos also in train)',
    'generator': 'scripts/utils.py::grouped_video_split',
    'split_seed': SPLIT_SEED,
    'sha256': digest,
    'n_frames': {k: sum(v.values()) for k, v in frames.items()},
    'n_videos': {k: len(v) for k, v in frames.items()},
    'classes': ds.classes,
    'assignment': dict(sorted(assignment.items())),
}
dest = PROJECT_ROOT / 'data_splits'
dest.mkdir(exist_ok=True)
with open(dest / 'split_v2_identity_grouped.json', 'w') as f:
    json.dump(out, f, indent=1)
print('sha256', digest[:12], '| frames', out['n_frames'], '| videos', out['n_videos'])
