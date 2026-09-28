"""Freeze the identity-disjoint split into data_splits/split_v2_identity_grouped.json with a SHA-256 hash.

    python scripts/freeze_split.py"""
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
