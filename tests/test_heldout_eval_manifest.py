"""Data-free guard for the held-out four-category evaluation set (eval_heldout/manifest.json).

WHY. The first evaluation set (eval_fallback/) was built before the identity-disjoint split existed and was never re-checked
against it: 57 of its 80 videos turned out to be in the shipped model's TRAINING split (docs/LESSONS.md L29). This test makes that
class of mistake impossible to repeat for the replacement set. It needs only two committed JSON manifests, no video on disk, so it
runs in CI. It is skipped when the held-out set has not been built.
"""
import json
import os
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / 'eval_heldout' / 'manifest.json'
SPLIT = ROOT / 'data_splits' / 'split_v2_identity_grouped.json'

pytestmark = pytest.mark.skipif(not (MANIFEST.exists() and SPLIT.exists()), reason='held-out evaluation set not built')


def _load():
    return json.load(open(MANIFEST)), json.load(open(SPLIT))


def _key(clip):
    return ('real/' if clip['video_label'] == 'real' else 'fake/') + os.path.basename(clip['video_source'])[:-4]


def test_every_video_is_in_the_test_partition_of_the_frozen_split():
    man, split = _load()
    not_test = [c['id'] for c in man['clips'] if split['assignment'].get(_key(c)) != 'test']
    assert not not_test, f'videos outside the test split (the model may have trained on them): {not_test}'


def test_manifest_records_the_hash_of_the_split_it_was_checked_against():
    man, split = _load()
    assert man['split_sha256'] == split['sha256'], 'the split changed since this set was built: re-verify it'


def test_no_identity_in_the_set_appears_in_any_training_or_validation_video():
    man, split = _load()
    non_test = set()
    for k, role in split['assignment'].items():
        if role != 'test':
            non_test |= set(k.split('/', 1)[1].split('_'))
    used = set()
    for c in man['clips']:
        used |= set(os.path.basename(c['video_source'])[:-4].split('_'))
    assert not (used & non_test), f'identities shared with train/val: {sorted(used & non_test)}'


def test_fake_videos_are_distinct_and_cover_all_three_methods():
    man, _ = _load()
    fakes = [c for c in man['clips'] if c['video_label'] == 'fake']
    assert len({c['video_source'] for c in fakes}) == len(fakes), 'a fake video is used twice'
    assert set(Counter(c['video_method'] for c in fakes)) == {'Deepfakes', 'FaceSwap', 'NeuralTextures'}
    assert {c['category'] for c in fakes} == {'FVRA', 'FVFA'}


def test_categories_are_complete_and_audio_comes_from_the_asvspoof_eval_partition():
    man, _ = _load()
    counts = Counter(c['category'] for c in man['clips'])
    assert counts == {'RVRA': 20, 'RVFA': 20, 'FVRA': 20, 'FVFA': 20}
    assert all('ASVspoof2019_LA_eval' in c['audio_source'] for c in man['clips']), 'audio must be from the eval partition'
