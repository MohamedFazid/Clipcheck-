"""Data-free tests for scripts/build_rating_form.py: the rater-facing page must never show what raters must not see (clip ids,
ground truth, automated checks), must show every case in order, and must write the CSV header the scorer reads."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
import build_rating_form as brf  # noqa: E402
import score_explanation_eval as sce  # noqa: E402

SECRET_CLIP = 'RVFA_987'


def _cases_json(tmp_path, n=3):
    records = []
    for i in range(1, n + 1):
        records.append({
            'case_id': f'eval-{i:02d}', 'p_video': 0.123456, 'p_audio': 0.987654,
            'meta': {'clip_id': SECRET_CLIP, 'category': 'RVFA', 'video_label': 'real', 'audio_label': 'spoof'},
            'structured_input': {'verdict': 'PARTIAL_MANIPULATION', 'video_score': '0.123', 'audio_score': '0.988',
                                 'video_assessment': 'leans GENUINE (not manipulated)', 'audio_assessment': 'leans FAKE (manipulated)',
                                 'video_anomaly_timing': '1:02 to 1:03 (peak 0.81)',
                                 'disagreement': 'yes', 'implicated_modality': 'audio'},
            'explanation': f'Explanation text number {i}.',
            'faithfulness_screen': {'passed': False, 'violations': [{'type': 'direction', 'detail': 'SCREEN_DETAIL'}]}})
    records.reverse()                                   # stored out of order: the form must still show them in order
    (tmp_path / 'cases.json').write_text(json.dumps({'records': records, 'faithfulness_screen_rejections': 3}))


def _build(tmp_path, monkeypatch):
    _cases_json(tmp_path)
    monkeypatch.setattr(brf, 'DIR', tmp_path)
    return Path(brf.build(brf.load_cases(), tmp_path / 'form.html')).read_text()


def test_nothing_raters_must_not_see_reaches_the_page(tmp_path, monkeypatch):
    html = _build(tmp_path, monkeypatch)
    for secret in (SECRET_CLIP, 'RVFA', 'spoof', 'bonafide', 'faithfulness', 'SCREEN_DETAIL', 'violations', '0.123456', '0.987654'):
        assert secret not in html, secret


def test_every_case_is_shown_in_order_with_its_facts(tmp_path, monkeypatch):
    html = _build(tmp_path, monkeypatch)
    data = json.loads(html.split('<script type="application/json" id="data">')[1].split('</script>')[0])
    assert [c['id'] for c in data['cases']] == ['eval-01', 'eval-02', 'eval-03']
    assert data['cases'][0]['facts']['video_assessment'] == 'leans GENUINE (not manipulated)'
    assert data['cases'][0]['facts']['video_anomaly_timing'] == '1:02 to 1:03 (peak 0.81)'
    assert set(data['cases'][0]) == {'id', 'facts', 'text'}


def test_csv_header_matches_the_scorer(tmp_path, monkeypatch):
    html = _build(tmp_path, monkeypatch)
    assert 'case_id,' + ','.join(sce.DIMENSIONS) + ',notes' in html


def test_worked_examples_are_complete_and_not_among_the_cases():
    for ex in brf.EXAMPLES:
        assert set(ex['scores']) == set(sce.DIMENSIONS) and set(ex['why']) == set(sce.DIMENSIONS)
        assert all(v in (0, 1, 2) for v in ex['scores'].values())
        assert set(ex['facts']) == {k for k, _ in brf.FACT_FIELDS}
