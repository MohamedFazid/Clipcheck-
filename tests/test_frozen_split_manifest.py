"""Leakage guarantees checked on the committed split manifest alone (runs in CI without FF++ data):
no video or identity in two splits, fake pairs kept with their real videos, and the stored hash matches."""
import hashlib
import json
from pathlib import Path

MANIFEST = Path(__file__).resolve().parent.parent / 'data_splits' / 'split_v2_identity_grouped.json'


def _load():
    return json.load(open(MANIFEST))


def _ids(video_key):
    folder = video_key.split('/', 1)[1]
    parts = folder.split('_')
    return set(parts) if len(parts) == 2 else {folder}


def test_no_video_or_identity_appears_in_two_splits():
    a = _load()['assignment']
    by_split = {s: [k for k, v in a.items() if v == s] for s in ('train', 'val', 'test')}
    ids = {s: set().union(*(_ids(k) for k in ks)) for s, ks in by_split.items()}
    vids = {s: set(ks) for s, ks in by_split.items()}
    for x, y in (('train', 'val'), ('train', 'test'), ('val', 'test')):
        assert not (vids[x] & vids[y]), f'video in both {x} and {y}'
        assert not (ids[x] & ids[y]), f'identity in both {x} and {y}: {sorted(ids[x] & ids[y])[:5]}'


def test_each_reciprocal_pair_is_wholly_in_one_split():
    a = _load()['assignment']
    for key, split in a.items():
        if key.startswith('fake/'):
            x, y = key.split('/', 1)[1].split('_')
            assert a[f'real/{x}'] == split and a[f'real/{y}'] == split, f'{key} split apart from its real videos'


def test_manifest_hash_matches_its_contents():
    m = _load()
    canon = json.dumps(sorted(m['assignment'].items()), separators=(',', ':')).encode()
    assert hashlib.sha256(canon).hexdigest() == m['sha256'], 'manifest was edited after freezing'


def test_counts_are_consistent():
    m = _load()
    counts = {}
    for v in m['assignment'].values():
        counts[v] = counts.get(v, 0) + 1
    assert counts == m['n_videos']
