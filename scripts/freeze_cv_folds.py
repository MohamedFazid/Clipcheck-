"""Freeze 5-fold identity-grouped cross-validation folds (every one of the 400 videos is tested once, unseen).

    python scripts/freeze_cv_folds.py"""
import hashlib
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import PROJECT_ROOT, SPLIT_MANIFEST, CV_MANIFEST, identity_groups_from_keys  # noqa: E402

N_FOLDS, SEED, VAL_GROUPS = 5, 42, 10


def main():
    keys = sorted(json.load(open(SPLIT_MANIFEST))['assignment'])
    groups = identity_groups_from_keys(keys)
    gids = sorted(groups)
    random.Random(SEED).shuffle(gids)
    fold_of = {g: i % N_FOLDS for i, g in enumerate(gids)}

    folds, test_fold_of_video = {}, {}
    for k in range(N_FOLDS):
        rest = [g for g in gids if fold_of[g] != k]          # shuffled order, so val choice is deterministic
        val = set(rest[:VAL_GROUPS])
        roles = {}
        for g in gids:
            role = 'test' if fold_of[g] == k else ('val' if g in val else 'train')
            for key in groups[g]:
                roles[key] = role
                if role == 'test':
                    test_fold_of_video[key] = k
        folds[str(k)] = dict(sorted(roles.items()))
    canon = json.dumps([[k, sorted(v.items())] for k, v in sorted(folds.items())], separators=(',', ':')).encode()
    digest = hashlib.sha256(canon).hexdigest()
    counts = {k: {r: sum(1 for v in f.values() if v == r) for r in ('train', 'val', 'test')} for k, f in folds.items()}
    json.dump({'name': 'cv5_identity_grouped', 'n_folds': N_FOLDS, 'seed': SEED, 'val_groups_per_fold': VAL_GROUPS,
               'n_groups': len(gids), 'source_manifest': SPLIT_MANIFEST.name, 'sha256': digest,
               'videos_per_role_per_fold': counts, 'test_fold_of_video': dict(sorted(test_fold_of_video.items())),
               'folds': folds}, open(CV_MANIFEST, 'w'), indent=1)
    print(f'sha256 {digest[:12]} | {len(gids)} groups | videos per role per fold: {counts["0"]}')


if __name__ == '__main__':
    main()
