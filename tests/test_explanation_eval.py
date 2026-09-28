"""Tests for the evaluation-set sampling mode of scripts/explanation_eval.py (PPR 3.6: 50 explanations drawn from the
evaluation set, rated by two people). No Ollama, no video model, no dataset: the LLM is mocked and the results file is synthetic."""
import argparse
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))

import explanation_eval as ee  # noqa: E402

CATEGORIES = ['RVRA', 'RVFA', 'FVRA', 'FVFA']


def _results_file(tmp_path, n=40):
    clips = []
    for i in range(n):
        cat = CATEGORIES[i % 4]
        clips.append({'id': f'{cat}_{i // 4:03d}', 'category': cat, 'video_label': 'real' if cat[0] == 'R' else 'fake',
                      'audio_label': 'bonafide' if cat[2] == 'R' else 'spoof',
                      'p_video': round(0.9 if cat[0] == 'F' else 0.05, 3), 'p_audio': round(0.95 if cat[2] == 'F' else 0.1, 3)})
    p = tmp_path / 'fallback_4condition_results.json'
    p.write_text(json.dumps({'per_clip_results': clips}))
    return p


def test_sample_is_random_but_reproducible_and_the_right_size(tmp_path):
    rp = _results_file(tmp_path)
    a = ee.build_cases_from_results(rp, n=25, seed=7)
    b = ee.build_cases_from_results(rp, n=25, seed=7)
    c = ee.build_cases_from_results(rp, n=25, seed=8)
    assert a == b and len(a) == 25
    assert [x['meta']['clip_id'] for x in a] != [x['meta']['clip_id'] for x in c]
    assert len({x['meta']['clip_id'] for x in a}) == 25, 'a clip was drawn twice'
    assert a[0]['case_id'] == 'eval-01' and a[-1]['case_id'] == 'eval-25'


def test_cannot_ask_for_more_cases_than_the_evaluation_set_has(tmp_path):
    with pytest.raises(ValueError):
        ee.build_cases_from_results(_results_file(tmp_path, n=10), n=50)


def test_ground_truth_is_kept_out_of_what_raters_read(tmp_path):
    cases = ee.build_cases_from_results(_results_file(tmp_path), n=12, seed=1)
    for c in cases:
        assert c['meta']['category'] in CATEGORIES                     # kept as metadata for analysis
        for shown in (c['note'], c['source']):                          # but never in the text raters see
            assert not any(cat in shown for cat in CATEGORIES)
            assert 'bonafide' not in shown and 'spoof' not in shown


def _args(tmp_path, results, **kw):
    base = dict(n=12, include_real_clips=False, overwrite=False, from_results=str(results), seed=42,
                out_dir=str(tmp_path / 'out'), allow_stale=False)
    base.update(kw)
    return argparse.Namespace(**base)


def _mock_llm(monkeypatch, texts):
    """Pretend Ollama answers with the given texts in turn, without touching the network."""
    it = iter(texts)
    monkeypatch.setattr(ee, 'explanation_available', lambda *a, **k: True)
    monkeypatch.setattr(ee, 'explain', lambda result, **k: next(it))


def test_generate_writes_full_protocol_files_and_records_the_faithfulness_screen(tmp_path, monkeypatch):
    rp = _results_file(tmp_path)
    good = 'The video analysis scored 0.900 and leans FAKE (manipulated).'
    bad = 'The video is definitely fake.'                            # certainty language: the screen must catch it
    _mock_llm(monkeypatch, ([good] * 11) + [bad])
    assert ee.cmd_generate(_args(tmp_path, rp)) == 0
    out = tmp_path / 'out'
    data = json.load(open(out / 'cases.json'))
    assert data['protocol'].startswith('full') and data['n_cases'] == 12 and data['sample_seed'] == 42
    assert data['faithfulness_screen_rejections'] >= 1
    assert all('faithfulness_screen' in r for r in data['records'])
    packet = (out / 'rating_packet.md').read_text()
    assert not any(cat in packet for cat in CATEGORIES), 'ground truth leaked into the rating packet'
    for rater in ('rater1', 'rater2'):
        rows = (out / f'rating_sheet_{rater}.csv').read_text().strip().splitlines()
        assert len(rows) == 1 + 12                                     # header + one row per case


def test_generate_refuses_to_overwrite_an_existing_run(tmp_path, monkeypatch):
    rp = _results_file(tmp_path)
    _mock_llm(monkeypatch, ['The video analysis scored 0.900 and leans FAKE (manipulated).'] * 24)
    assert ee.cmd_generate(_args(tmp_path, rp)) == 0
    assert ee.cmd_generate(_args(tmp_path, rp)) == 2                   # second run into the same folder is refused
    assert ee.cmd_generate(_args(tmp_path, rp, overwrite=True)) == 0
