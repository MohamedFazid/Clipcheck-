"""Tests for the user-testing survey form and scorer (ledger U1). Data-free: fixtures are written to pytest's tmp_path only.

The fixture CSVs here exercise the scorer's arithmetic and refusals; they are not participant data and are never written to
docs/user_testing/responses/ (human evaluations rest on humans only).
"""
import csv
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
from build_survey_form import SURVEY, REQUIRED_TASKS, SHORT_TASK_IDS, build  # noqa: E402
from score_user_testing import sus_score, read_response, score  # noqa: E402


def test_sus_scoring_known_values():
    assert sus_score({f'SUS{i}': '3' for i in range(1, 11)}) == 50.0
    best = {f'SUS{i}': ('5' if i % 2 else '1') for i in range(1, 11)}
    worst = {f'SUS{i}': ('1' if i % 2 else '5') for i in range(1, 11)}
    assert sus_score(best) == 100.0 and sus_score(worst) == 0.0


def test_sus_rejects_out_of_range():
    with pytest.raises(ValueError):
        sus_score({**{f'SUS{i}': '3' for i in range(1, 11)}, 'SUS4': '6'})


def _fixture(path, pid='P1', rnd='1', drop=None):
    rows = [('meta', 'participant', pid), ('meta', 'round', rnd), ('meta', 'consent', 'given')]
    rows += [('task', f'{t}/outcome', 'done unaided') for t in REQUIRED_TASKS]
    rows += [('task', 'T3/named_part', 'the video'), ('task', 'T3/ease', '6')]
    rows += [('sus', f'SUS{i}', '3') for i in range(1, 11)]
    rows += [('project', q, '4') for q, _ in SURVEY['project']]
    rows += [('feature', f, '3') for f, _ in SURVEY['features']]
    rows = [r for r in rows if (r[0], r[1]) != drop]
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['participant', 'round', 'section', 'item', 'value'])
        for sec, item, val in rows:
            w.writerow([pid, rnd, sec, item, val])
    return path


def test_complete_fixture_scores(tmp_path):
    _fixture(tmp_path / 'survey_P1_round1.csv')
    _fixture(tmp_path / 'survey_P2_round1.csv', pid='P2', drop=('task', 'T3/named_part'))
    s = score(tmp_path, tmp_path / 'out')
    r = s['rounds']['1']
    assert r['n'] == 2 and r['sus_median'] == 50.0
    assert r['tasks']['T3']['named_part'] == {'the video': 1, 'not recorded': 1}
    assert (tmp_path / 'out' / 'summary.md').exists()


def test_missing_required_answer_is_refused(tmp_path):
    p = _fixture(tmp_path / 'survey_P1_round1.csv', drop=('sus', 'SUS7'))
    with pytest.raises(ValueError, match='SUS7'):
        read_response(p)


def test_answer_outside_form_options_is_refused(tmp_path):
    p = _fixture(tmp_path / 'survey_P1_round1.csv')
    with open(p, 'a', newline='') as f:
        csv.writer(f).writerow(['P1', '1', 'task', 'T6/inconclusive_reading', 'made up option'])
    with pytest.raises(ValueError, match='not a form option'):
        read_response(p)


def test_no_responses_means_no_score(tmp_path):
    with pytest.raises(SystemExit):
        score(tmp_path, tmp_path / 'out')


def test_form_has_every_item_and_no_answer_key(tmp_path):
    html = build(tmp_path / 'form.html').read_text()
    for t in SURVEY['tasks']:
        assert t['id'] in html
    for q in SURVEY['sus']:
        assert q in html
    # The facilitator's answer key must never reach a page the participant may see.
    for leak in ('ground truth: real', 'WRONG', '0.853', '0.999', 'is genuine and the verdict is wrong', 'answer key:'):
        assert leak not in html


def _short_fixture(path, pid='P3', rnd='1', drop=None):
    rows = [('meta', 'participant', pid), ('meta', 'round', rnd), ('meta', 'consent', 'given'), ('meta', 'form', 'short')]
    rows += [('task', f'{t}/outcome', 'done unaided') for t in SHORT_TASK_IDS]
    rows += [('sus', f'SUS{i}', '4') for i in range(1, 11)]
    rows = [r for r in rows if (r[0], r[1]) != drop]
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['participant', 'round', 'section', 'item', 'value'])
        for sec, item, val in rows:
            w.writerow([pid, rnd, sec, item, val])
    return path


def test_short_form_needs_only_its_own_items(tmp_path):
    r = read_response(_short_fixture(tmp_path / 'survey_P3_round1.csv'))
    assert r['form'] == 'short' and r['sus'] == 50.0
    with pytest.raises(ValueError, match='T7'):
        read_response(_short_fixture(tmp_path / 'survey_P4_round1.csv', pid='P4', drop=('task', 'T7/outcome')))


def test_short_and_full_sessions_pool(tmp_path):
    _fixture(tmp_path / 'survey_P1_round1.csv')
    _short_fixture(tmp_path / 'survey_P3_round1.csv')
    r = score(tmp_path, tmp_path / 'out')['rounds']['1']
    assert r['n'] == 2 and r['forms'] == {'P1': 'full', 'P3': 'short'}
    assert r['project']['Q1']['values'] == {'P1': 4}          # asked of the full-form participant only
    assert r['features']['F_verdict']['asked'] == 1


def test_short_form_page(tmp_path):
    html = build(tmp_path / 'short.html', 'short').read_text()
    assert 'Short version' in html and '"T7"' in html and '"T5"' not in html
    for leak in ('WRONG', '0.853', '0.999', 'answer key:'):
        assert leak not in html
