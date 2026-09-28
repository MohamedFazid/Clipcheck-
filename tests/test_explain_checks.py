"""Tests for the template explainer and faithfulness screen: the template passes on every score combination,
and deliberately unfaithful texts (e.g. 0.46 called "fake") are caught. No Ollama needed."""
import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))

from fusion import fuse  # noqa: E402
from explain import build_structured_input  # noqa: E402
from explain_checks import explain_template, check_faithfulness  # noqa: E402

GRID = [None, 0.001, 0.11, 0.15, 0.29, 0.46, 0.499, 0.5, 0.501, 0.54, 0.7, 0.9, 0.999]


def _case(pv, pa):
    r = fuse(pv, pa)
    return r, build_structured_input(r)


def test_template_is_faithful_on_every_score_combination():
    n = 0
    for pv, pa in itertools.product(GRID, GRID):
        r, s = _case(pv, pa)
        out = check_faithfulness(explain_template(r), s)
        assert out['passed'], f'pv={pv} pa={pa}: {out["violations"]}'
        n += 1
    assert n == len(GRID) ** 2


def test_template_names_every_verdict_type():
    verdicts = {fuse(pv, pa).verdict for pv, pa in itertools.product(GRID, GRID)}
    assert verdicts == {'REAL', 'FAKE', 'PARTIAL_MANIPULATION', 'INCONCLUSIVE'}


def test_screen_catches_the_pilot_failure_score_below_half_called_fake():
    r, s = _case(0.60, 0.46)                       # audio 0.46 leans genuine
    bad = 'The audio analysis scored 0.460 and looks fake. The video analysis scored 0.600 and looks fake.'
    out = check_faithfulness(bad, s)
    assert not out['passed'] and any(v['type'] == 'direction' for v in out['violations'])


def test_screen_catches_a_number_not_in_the_input():
    r, s = _case(0.95, 0.05)
    out = check_faithfulness('The video analysis scored 0.73 and leans fake.', s)
    assert any(v['type'] == 'number' for v in out['violations'])


def test_screen_allows_rounded_scores_and_the_half_boundary():
    r, s = _case(0.954, 0.041)
    ok = 'The video score is 0.95, well above the 0.5 boundary, and the audio score is 0.04.'
    assert not [v for v in check_faithfulness(ok, s)['violations'] if v['type'] == 'number']


def test_screen_catches_certainty_and_unlisted_claims():
    r, s = _case(0.99, None)
    out = check_faithfulness('This is definitely a face-swap made with a GAN.', s)
    types = {v['type'] for v in out['violations']}
    assert 'certainty' in types and 'unlisted' in types


def test_screen_catches_judging_a_branch_that_was_not_evaluated():
    r, s = _case(0.9, None)
    out = check_faithfulness('The video analysis scored 0.900 and leans fake. The audio sounds genuine.', s)
    assert any(v['type'] == 'unevaluated' for v in out['violations'])


def test_screen_catches_disagreement_errors_both_ways():
    r, s = _case(0.95, 0.05)                        # genuine disagreement, video implicated
    assert s['disagreement'] == 'yes' and s['implicated_modality'] == 'video'
    out = check_faithfulness('Video scored 0.950 and audio scored 0.050. The verdict is FAKE.', s)
    assert any(v['type'] == 'disagreement' for v in out['violations'])
    r2, s2 = _case(0.90, 0.85)                      # agreement
    out2 = check_faithfulness('The video and audio analyses disagree with each other.', s2)
    assert any(v['type'] == 'disagreement' for v in out2['violations'])


def test_relative_comparison_is_not_mistaken_for_a_direction_error():
    """Disagreement can implicate a branch that still leans genuine (0.45 vs 0.05): 'more likely manipulated'
    is a relative claim and must not be flagged."""
    r, s = _case(0.45, 0.05)
    assert s['implicated_modality'] == 'video'
    assert check_faithfulness(explain_template(r), s)['passed']


# ── Conjunctive claims: "both are manipulated" when one branch leans genuine (found in the 50-case run) ─────────────

def _si(v, a, verdict='PARTIAL_MANIPULATION', implicated='video'):
    from explain import assess
    return {'verdict': verdict, 'video_score': f'{v:.3f}', 'audio_score': f'{a:.3f}',
            'video_assessment': assess(v), 'audio_assessment': assess(a),
            'disagreement': 'yes' if verdict == 'PARTIAL_MANIPULATION' else 'no',
            'implicated_modality': implicated}


def test_claiming_both_manipulated_is_caught_when_a_branch_leans_genuine():
    """Real Llama 3 output from the 50-case run: it opened with this while the audio branch scored 0.000."""
    r = check_faithfulness('The analysis suggests that the video and audio content are partially manipulated.', _si(0.438, 0.000))
    assert not r['passed']
    assert any(v['type'] == 'direction' and 'both branches are manipulated' in v['detail'] for v in r['violations'])


def test_both_branches_genuine_wording_still_passes():
    """The commonest faithful phrasing in the same run (14 of 50 cases) must not be flagged."""
    for text in ('The video and audio branches both lean towards being genuine.',
                 'Neither the video nor the audio shows signs of manipulation.',
                 'The video and audio branches agree, and the content appears authentic.'):
        assert check_faithfulness(text, _si(0.05, 0.08, verdict='REAL', implicated='none'))['passed'], text


def test_both_manipulated_is_fine_when_both_really_do_lean_fake():
    r = check_faithfulness('Both the video and the audio appear manipulated.', _si(0.91, 0.88, verdict='FAKE', implicated='none'))
    assert r['passed'], r['violations']


def test_single_branch_direction_check_still_works():
    """The pilot's original failure must still be caught."""
    r = check_faithfulness('The video analysis scored 0.460, so the video is fake.', _si(0.46, 0.44, verdict='REAL', implicated='none'))
    assert not r['passed'] and any(v['type'] == 'direction' for v in r['violations'])


# ── Video anomaly timing: a real timestamp is allowed, an invented one is not ─────────────────────────────────────

ANOMALY = [{'start': 4.0, 'end': 5.0, 'peak_score': 0.95, 'label': 'x', 'severity': 'high'}]


def test_template_states_real_timing_and_passes_its_own_screen():
    r = fuse(0.9, None)
    s = build_structured_input(r, ANOMALY)
    text = explain_template(r, ANOMALY)
    assert '0:04 to 0:05' in text
    assert check_faithfulness(text, s)['passed'], check_faithfulness(text, s)['violations']


def test_template_omits_timing_when_there_is_none():
    r = fuse(0.9, None)
    assert 'looked most suspicious at' not in explain_template(r, [])
    assert 'looked most suspicious at' not in explain_template(r, None)


def test_screen_allows_a_time_and_a_peak_that_are_in_the_input():
    s = build_structured_input(fuse(0.9, None), ANOMALY)
    text = 'The video analysis scored 0.900 and leans fake. Elevated likelihood was concentrated at 0:04 to 0:05 (peak 0.95).'
    out = check_faithfulness(text, s)
    assert out['passed'], out['violations']


def test_screen_catches_an_invented_timestamp():
    s = build_structured_input(fuse(0.9, None), ANOMALY)
    text = 'The video analysis scored 0.900 and leans fake. Elevated likelihood was concentrated at 0:12 to 0:13.'
    out = check_faithfulness(text, s)
    assert any(v['type'] == 'timing' for v in out['violations']), out['violations']


def test_screen_does_not_flag_a_peak_score_as_a_hallucinated_number():
    """A peak score can legitimately differ from both branch scores; it must not trip the 'number' check."""
    s = build_structured_input(fuse(0.62, None), ANOMALY)          # peak 0.95 != video_score 0.620
    text = 'The video analysis scored 0.620 and leans fake. Elevated likelihood was concentrated at 0:04 to 0:05 (peak 0.95).'
    out = check_faithfulness(text, s)
    assert not [v for v in out['violations'] if v['type'] == 'number'], out['violations']


def test_negated_disagreement_mention_is_not_a_false_claim():
    """Real Llama 3 output found during the timing-feature regeneration: 'There is no indication that the video and
    audio branches disagree' must NOT be read as the text claiming disagreement."""
    s = {'verdict': 'FAKE', 'video_score': '0.950', 'audio_score': 'not evaluated', 'video_assessment': 'leans FAKE (manipulated)',
         'audio_assessment': 'was not evaluated', 'video_anomaly_timing': 'not available', 'disagreement': 'no',
         'implicated_modality': 'none'}
    text = ('The video branch leans towards being manipulated. There is no indication that the video and audio '
           'branches disagree, and no specific modality is flagged as more likely manipulated.')
    out = check_faithfulness(text, s)
    assert not [v for v in out['violations'] if v['type'] == 'disagreement'], out['violations']


def test_genuinely_claimed_disagreement_is_still_caught_alongside_a_negated_mention():
    """A text can deny disagreement in one clause and wrongly claim it in another; the un-negated claim must still
    be caught."""
    s = {'verdict': 'REAL', 'video_score': '0.900', 'audio_score': '0.850', 'video_assessment': 'leans FAKE (manipulated)',
         'audio_assessment': 'leans FAKE (manipulated)', 'video_anomaly_timing': 'not available', 'disagreement': 'no',
         'implicated_modality': 'none'}
    text = 'There is no reason to think otherwise. The video and audio branches disagree on the outcome.'
    out = check_faithfulness(text, s)
    assert any(v['type'] == 'disagreement' for v in out['violations']), out['violations']


def test_screen_is_unaffected_when_no_timing_was_ever_supplied():
    """Old-style structured dicts (no video_anomaly_timing key, e.g. the stored 50-case packet) must not be flagged
    just because the key is absent, and incidental colon-free text must not trip the new check."""
    out = check_faithfulness('The video analysis scored 0.100 and leans genuine.', _si(0.10, 0.08, verdict='REAL', implicated='none'))
    assert out['passed']



def test_template_is_plain_language():
    """Requirement (24 Sep): the explanation is in layman terms. No system labels or branch jargon, and no 100% / 0%."""
    for pv, pa in itertools.product(GRID, GRID):
        text = explain_template(fuse(pv, pa))
        for jargon in ('FAKE', 'REAL', 'PARTIAL_MANIPULATION', 'INCONCLUSIVE', 'branch', 'analysis', 'modality', 'verbalise', '100%', ' 0%'):
            assert jargon not in text, (pv, pa, jargon, text)


def test_template_timing_passes_the_screen_on_every_score_combination():
    """With real moments supplied (one a single frame), the plain-language template still passes its own screen everywhere."""
    moments = [{'start': 0.0, 'end': 0.3, 'peak_score': 0.6, 'label': 'x', 'severity': 'high'},
               {'start': 4.0, 'end': 5.0, 'peak_score': 0.95, 'label': 'x', 'severity': 'high'}]
    for pv, pa in itertools.product([g for g in GRID if g is not None], GRID):
        r = fuse(pv, pa)
        out = check_faithfulness(explain_template(r, moments), build_structured_input(r, moments))
        assert out['passed'], (pv, pa, out['violations'])
