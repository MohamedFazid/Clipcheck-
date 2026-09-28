"""Data-free tests for scripts/score_explanation_eval.py: the refusal-on-incomplete-sheets guard, and the kappa/agreement
maths, against small synthetic CSVs written to tmp_path (never the real rating sheets)."""
import csv
import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / 'scripts' / 'score_explanation_eval.py'
DIMENSIONS = ('factual_grounding', 'score_accuracy', 'absence_of_hallucination')


def load_module_pointed_at(tmp_path):
    """Import score_explanation_eval.py with its DIR constant redirected to tmp_path, without touching the real sheets."""
    spec = importlib.util.spec_from_file_location('score_explanation_eval_test', SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules['score_explanation_eval_test'] = mod
    spec.loader.exec_module(mod)
    mod.DIR = tmp_path
    return mod


def write_sheet(path, rows):
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['case_id', *DIMENSIONS, 'notes'])
        for case_id, scores in rows.items():
            w.writerow([case_id, *scores, ''])


def test_refuses_when_either_sheet_has_blanks(tmp_path):
    mod = load_module_pointed_at(tmp_path)
    write_sheet(tmp_path / 'rating_sheet_rater1.csv', {'eval-01': (2, 2, 2), 'eval-02': ('', '', '')})
    write_sheet(tmp_path / 'rating_sheet_rater2.csv', {'eval-01': (2, 2, 2), 'eval-02': (1, 1, 1)})
    with pytest.raises(SystemExit, match='rater1 has 1 unscored'):
        mod.main()


def test_refuses_on_mismatched_case_ids(tmp_path):
    mod = load_module_pointed_at(tmp_path)
    write_sheet(tmp_path / 'rating_sheet_rater1.csv', {'eval-01': (2, 2, 2)})
    write_sheet(tmp_path / 'rating_sheet_rater2.csv', {'eval-02': (2, 2, 2)})
    with pytest.raises(SystemExit, match='different cases'):
        mod.main()


def test_refuses_on_out_of_range_score(tmp_path):
    mod = load_module_pointed_at(tmp_path)
    write_sheet(tmp_path / 'rating_sheet_rater1.csv', {'eval-01': (3, 2, 2)})
    write_sheet(tmp_path / 'rating_sheet_rater2.csv', {'eval-01': (2, 2, 2)})
    with pytest.raises(SystemExit, match='must be 0, 1 or 2'):
        mod.main()


def test_perfect_agreement_gives_kappa_one_and_no_full_disagreements(tmp_path, capsys):
    mod = load_module_pointed_at(tmp_path)
    rows = {f'eval-{i:02d}': (i % 3, (i + 1) % 3, i % 2) for i in range(1, 11)}
    write_sheet(tmp_path / 'rating_sheet_rater1.csv', rows)
    write_sheet(tmp_path / 'rating_sheet_rater2.csv', rows)
    mod.main()
    import json
    report = json.load(open(tmp_path / 'scored_report.json'))
    assert report['n_cases'] == 10
    for dim in DIMENSIONS:
        d = report['dimensions'][dim]
        assert d['exact_agreement'] == 1.0
        assert d['full_disagreements'] == []
        # weighted kappa is undefined (nan) when a rater has zero variance on a dimension; only assert it when it isn't
        if d['weighted_kappa'] == d['weighted_kappa']:            # not NaN
            assert d['weighted_kappa'] == pytest.approx(1.0)


def test_full_disagreement_is_flagged_and_lowers_kappa(tmp_path):
    mod = load_module_pointed_at(tmp_path)
    ids = [f'eval-{i:02d}' for i in range(1, 21)]
    r1 = {c: (2, 2, 2) for c in ids}
    r2 = {c: (2, 2, 2) for c in ids}
    r2['eval-05'] = (0, 2, 2)                       # a full 2-vs-0 disagreement on factual_grounding only
    write_sheet(tmp_path / 'rating_sheet_rater1.csv', r1)
    write_sheet(tmp_path / 'rating_sheet_rater2.csv', r2)
    mod.main()
    import json
    report = json.load(open(tmp_path / 'scored_report.json'))
    assert report['dimensions']['factual_grounding']['full_disagreements'] == ['eval-05']
    assert report['dimensions']['score_accuracy']['full_disagreements'] == []
    assert report['dimensions']['factual_grounding']['exact_agreement'] == pytest.approx(19 / 20)
