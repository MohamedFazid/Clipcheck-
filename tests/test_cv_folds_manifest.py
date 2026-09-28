"""Guarantees of the frozen 5-fold cross-validation manifest, checked from names alone (no dataset), so CI runs them.

Cross-validation is only worth reporting if every fold is leak-free and every video is scored out-of-fold exactly once.
"""
import hashlib
import json
from pathlib import Path

CV = Path(__file__).resolve().parent.parent / 'data_splits' / 'cv5_identity_grouped.json'


def _load():
    return json.load(open(CV))


def _ids(key):
    folder = key.split('/', 1)[1]
    parts = folder.split('_')
    return set(parts) if len(parts) == 2 else {folder}


def test_every_video_is_a_test_video_in_exactly_one_fold():
    m = _load()
    n_test = {}
    for k, roles in m['folds'].items():
        for key, role in roles.items():
            if role == 'test':
                n_test[key] = n_test.get(key, 0) + 1
    assert set(n_test) == set(m['folds']['0']), 'some video is never a test video'
    assert set(n_test.values()) == {1}, 'some video is a test video in more than one fold'


def test_no_video_or_identity_crosses_roles_within_any_fold():
    for k, roles in _load()['folds'].items():
        by_role = {r: [key for key, v in roles.items() if v == r] for r in ('train', 'val', 'test')}
        ids = {r: set().union(*(_ids(key) for key in ks)) for r, ks in by_role.items()}
        for a, b in (('train', 'val'), ('train', 'test'), ('val', 'test')):
            assert not (set(by_role[a]) & set(by_role[b])), f'fold {k}: video in both {a} and {b}'
            assert not (ids[a] & ids[b]), f'fold {k}: identity in both {a} and {b}: {sorted(ids[a] & ids[b])[:5]}'


def test_each_reciprocal_pair_has_one_role_in_every_fold():
    for k, roles in _load()['folds'].items():
        for key, role in roles.items():
            if key.startswith('fake/'):
                x, y = key.split('/', 1)[1].split('_')
                assert roles[f'real/{x}'] == role and roles[f'real/{y}'] == role, f'fold {k}: {key} split from its real videos'


def test_folds_are_balanced_and_sized_as_documented():
    m = _load()
    per = m['videos_per_role_per_fold']
    assert len(m['folds']) == m['n_folds'] == 5
    for k, c in per.items():
        assert c == {'train': 280, 'val': 40, 'test': 80}, f'fold {k} sizes {c}'


def test_manifest_hash_matches_its_contents():
    m = _load()
    canon = json.dumps([[k, sorted(v.items())] for k, v in sorted(m['folds'].items())], separators=(',', ':')).encode()
    assert hashlib.sha256(canon).hexdigest() == m['sha256'], 'CV manifest was edited after freezing'
