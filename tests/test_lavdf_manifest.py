"""Data-free tests for scripts/build_lavdf_eval_set.py (LAV-DF itself is not needed): the category mapping, the test-split-only
rule, determinism of the draw, and that a malformed flag fails loudly instead of turning clips into 'real'."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
import build_lavdf_eval_set as b  # noqa: E402


def _records():
    out = []
    for split in ('train', 'val', 'test'):
        for v in (False, True):
            for a in (False, True):
                for i in range(6):
                    out.append({'file': f'{split}/{int(v)}{int(a)}_{i}.mp4', 'split': split, 'modify_video': v, 'modify_audio': a})
    return out


def test_only_test_split_and_correct_categories():
    chosen = b.select(_records(), 4, 42)
    assert set(chosen) == {'RVRA', 'RVFA', 'FVRA', 'FVFA'}
    expect = {'RVRA': '00', 'RVFA': '01', 'FVRA': '10', 'FVFA': '11'}
    for cat, (items, available) in chosen.items():
        assert available == 6 and len(items) == 4
        for r in items:
            assert r['split'] == 'test'
            assert f"{int(r['modify_video'])}{int(r['modify_audio'])}" == expect[cat]


def test_draw_is_deterministic_and_independent_of_input_order():
    a = b.select(_records(), 3, 7)
    shuffled = list(reversed(_records()))
    c = b.select(shuffled, 3, 7)
    assert {k: [r['file'] for r in v[0]] for k, v in a.items()} == {k: [r['file'] for r in v[0]] for k, v in c.items()}


def test_too_few_clips_is_an_error():
    with pytest.raises(SystemExit):
        b.select(_records(), 7, 1)


def test_flag_parsing():
    assert b.as_fake(True) and b.as_fake(1) and b.as_fake('True') and not b.as_fake(False) and not b.as_fake('real')
    with pytest.raises(ValueError):
        b.as_fake('maybe')
