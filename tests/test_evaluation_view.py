"""Data-free tests for scripts/evaluation_view.py: the in-app Evaluation tab and Limitations panel must show only numbers that
come from result files, withhold anything produced with a superseded model, and never attach a result to the wrong model."""
import copy
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'scripts'))
import evaluation_view as ev  # noqa: E402


def _entry(label, frames_dir, split='v2 identity-disjoint', val=0.86, clip=0.96):
    m = lambda v: {'mean': v, 'std': 0.02, 'n': 3}
    return {'label': label, 'split': split, 'frames_dir': frames_dir, 'arch': 'legacy_xception',
            'frame_level': {'accuracy': m(0.88)}, 'video_level': {'n_videos': 44, 'accuracy': m(clip)},
            'overfitting_gap_pp': m(13.0), 'val_accuracy_at_best_epoch': m(val)}


def _numbers():
    det = lambda v: {'mean': v, 'std': 0.05, 'n': 3}
    meth = {m: {'fake_detection_rate': det(0.85), 'real_specificity': det(0.97)} for m in ('Deepfakes', 'FaceSwap', 'NeuralTextures')}
    return {
        'generated_at': '2026-09-20T00:00:00+00:00',
        'video': {'mm_xcep_vidsplit': _entry('Xception, multi-method', 'frames_multi'),
                  'xcep_vidsplit': _entry('Xception', 'frames'),
                  'baseline_legacy': _entry('baseline (aug bug)', 'frames', split='v1 (leaking, SUPERSEDED)', val=0.97, clip=0.99)},
        'cross_method': {'mm_xcep_vidsplit': {'mean_std': meth}, 'xcep_vidsplit': {'mean_std': meth}},
        'cross_validation': {'cv5_xcep_mm': {'arch': 'legacy_xception', 'pooled_out_of_fold': {'n_videos': 400, 'accuracy': 0.828, 'auc': 0.918},
                                             'ci95_cluster_bootstrap': {'accuracy': [0.792, 0.862], 'auc': [0.891, 0.942]}}},
        'cross_dataset_celebdf_v2': {'mm_xcep_vidsplit': {'seed': 44, 'accuracy': 0.591, 'auc_roc': 0.696, 'eer': 0.371,
                                                          'fake_detection': 0.526, 'real_specificity': 0.713}},
        'audio': {'baseline_comparison': {'mfcc_svm': {'eval_eer': 0.1025, 'eval_accuracy': 0.932},
                                          'wav2vec2_svm': {'eval_eer': 0.0396, 'eval_accuracy': 0.9765},
                                          'unseen_corpus_genuine_speech': {'n_clips': 100, 'mfcc_svm': {'fa_at_p0.5': 1.0},
                                                                            'wav2vec2_svm': {'fa_at_p0.5': 1.0}}},
                  'wav2vec2_svm_extra': {'majority_class_baseline_accuracy': 0.897,
                                         'at_probability_0.5 (as the app and fusion use it)': {'balanced_accuracy': 0.957}}},
        'fallback_4condition_OLD_MODEL': {'1_video_only_accuracy': 1.0},
        'hybrid_4condition_OLD_MODEL': {'1_video_only_accuracy': 0.91},
    }


SHIPPED = {'tag': 'mm_xcep_vidsplit', 'arch': 'legacy_xception', 'trained_on': 'multi-method (Deepfakes + FaceSwap + NeuralTextures)'}
FUSION = {'threshold_T': 0.30, 'threshold_T_source': 'tuned on the superseded model', 'video_accuracy_source': 'v', 'audio_accuracy_source': 'a'}


def _by_id(e):
    return {s['id']: s for s in e['sections']}


def test_leaking_split_figures_are_never_shown():
    e = ev.build_evaluation(_numbers(), SHIPPED, None, FUSION)
    labels = [r[0] for r in _by_id(e)['video_models']['rows']]
    assert not any('aug bug' in l or 'baseline' in l for l in labels)
    assert len(labels) == 2


def test_old_model_evidence_is_withheld_not_shown():
    e = _by_id(ev.build_evaluation(_numbers(), SHIPPED, None, FUSION))
    for sid in ('four_condition', 'hybrid'):
        assert e[sid]['status'] == 'pending' and 'rows' not in e[sid]
        assert 'superseded' in e[sid]['reason']
    assert e['latency']['status'] == 'pending'


def test_current_fusion_evidence_appears_once_it_exists_without_the_old_suffix():
    n = _numbers()
    n['fallback_4condition'] = {'1_video_only_accuracy': 0.9, '2_audio_only_accuracy': 0.95,
                                '3_standard_fusion_accuracy': 0.8, '4_disagreement_aware_fusion_accuracy': 0.94}
    e = _by_id(ev.build_evaluation(n, SHIPPED, None, FUSION))
    assert e['four_condition']['status'] == 'current' and len(e['four_condition']['rows']) == 4
    assert e['hybrid']['status'] == 'pending'


def test_fusion_sections_show_modality_implication_not_only_accuracy():
    """The project's contribution is naming the implicated modality, so accuracy must never be shown without it."""
    n = _numbers()
    n['fallback_4condition'] = {'1_video_only_accuracy': 0.9, '4_disagreement_aware_fusion_accuracy': 0.96}
    n['fallback_4condition_implication'] = {'RVFA_correctly_flagged_audio_implicated': 1.0,
                                            'FVRA_correctly_flagged_video_implicated': 0.95}
    sec = _by_id(ev.build_evaluation(n, SHIPPED, None, FUSION))['four_condition']
    labels = [r[0] for r in sec['rows']]
    assert any('Correctly named AUDIO' in l for l in labels) and any('Correctly named VIDEO' in l for l in labels)


def test_out_of_distribution_wrong_modality_limitation_appears_only_when_implication_fails():
    n = _numbers()
    n['hybrid_4condition_implication'] = {'FVRA_correctly_flagged_video_implicated': 0.0}
    lim = {l['id']: l['text'] for l in ev.build_limitations(n, SHIPPED, FUSION)}
    assert 'wrong_modality_out_of_distribution' in lim
    assert 'name the wrong part' in lim['wrong_modality_out_of_distribution'] and '0%' in lim['wrong_modality_out_of_distribution']
    n['hybrid_4condition_implication'] = {'FVRA_correctly_flagged_video_implicated': 0.95}
    assert 'wrong_modality_out_of_distribution' not in {l['id'] for l in ev.build_limitations(n, SHIPPED, FUSION)}


def test_shipped_model_is_marked_in_every_table():
    e = _by_id(ev.build_evaluation(_numbers(), SHIPPED, None, FUSION))
    for sid in ('video_models', 'per_method', 'celebdf'):
        marked = [r for r in e[sid]['rows'] if 'SHIPPED' in r[0]]
        assert len(marked) == 1 and marked[0][0].startswith('Xception, multi-method'), sid


def test_cross_validation_is_not_attached_to_a_different_architecture():
    other = dict(SHIPPED, arch='efficientnet_b4', tag='mm_b4_vidsplit')
    cvs = [s for s in ev.build_evaluation(_numbers(), other, None, FUSION)['sections'] if s['id'].startswith('cv_')][0]
    assert 'NOT the shipped model' in cvs['note']
    same = [s for s in ev.build_evaluation(_numbers(), SHIPPED, None, FUSION)['sections'] if s['id'].startswith('cv_')][0]
    assert 'matches the shipped architecture' in same['note']
    lim = {l['id']: l['text'] for l in ev.build_limitations(_numbers(), other, FUSION)}
    assert 'cross-validation' not in lim['accuracy'], 'Xception CV must not be quoted for a B4 model'


def test_latency_is_shown_only_for_the_shipped_model_and_only_if_complete():
    lat = {'complete_pipeline': True, 'video_model': {'tag': 'mm_xcep_vidsplit'}, 'measured_total_warm_s': 9.5, 'cold_start_total_s': 5.0,
           'hardware': {'cpu': 'Apple M2 Pro', 'torch_device': 'mps'},
           'stages': [{'stage': '1. Face extraction', 'status': 'measured', 'mean_s': 7.0, 'std_s': 0.1}]}
    assert _by_id(ev.build_evaluation(_numbers(), SHIPPED, lat, FUSION))['latency']['status'] == 'current'
    assert _by_id(ev.build_evaluation(_numbers(), dict(SHIPPED, tag='other'), lat, FUSION))['latency']['status'] == 'pending'
    assert _by_id(ev.build_evaluation(_numbers(), SHIPPED, dict(lat, complete_pipeline=False), FUSION))['latency']['status'] == 'pending'


def test_limitations_are_grounded_in_the_numbers():
    lim = {l['id']: l['text'] for l in ev.build_limitations(_numbers(), SHIPPED, FUSION)}
    assert 'three of the four' in lim['coverage'] and 'Face2Face' in lim['coverage']
    assert '83%' in lim['accuracy'] and '79%' in lim['accuracy'] and '400 videos' in lim['accuracy']
    assert '59%' in lim['other_datasets'] and '29%' in lim['other_datasets']      # 1 - 0.713 real specificity
    assert '100%' in lim['audio_corpus'] and '100 genuine' in lim['audio_corpus']
    assert '0.30' in lim['threshold'] and 'superseded' in lim['threshold']


def test_limitations_say_so_when_there_is_no_evidence():
    n = _numbers()
    n['cross_validation'] = {}
    n['cross_dataset_celebdf_v2'] = {}
    n['video'] = {}
    lim = {l['id']: l['text'] for l in ev.build_limitations(n, SHIPPED, None)}
    assert 'No measured accuracy' in lim['accuracy']
    assert 'not been measured' in lim['other_datasets']
    single = {l['id']: l['text'] for l in ev.build_limitations(n, dict(SHIPPED, trained_on='Deepfakes only'), None)}
    assert 'single manipulation method' in single['coverage']
    none = {l['id']: l['text'] for l in ev.build_limitations(n, None, None)}
    assert 'not recorded' in none['coverage']


def test_no_em_dashes_and_no_mutation_of_the_input():
    n = _numbers()
    before = copy.deepcopy(n)
    e = ev.build_evaluation(n, SHIPPED, None, FUSION)
    lim = ev.build_limitations(n, SHIPPED, FUSION)
    assert n == before
    blob = repr(e) + repr(lim)
    assert '—' not in blob


def test_empty_inputs_do_not_crash():
    e = _by_id(ev.build_evaluation({}, None, None, None))
    for sid in ('video_models', 'per_method', 'celebdf', 'audio', 'four_condition', 'hybrid', 'latency'):
        assert e[sid]['status'] == 'pending', sid                       # no evidence, so nothing is presented as a result
    assert not any(k.startswith('cv_') for k in e) and 'fusion_settings' not in e
    assert len(ev.build_limitations({}, None, None)) >= 5


# ── Held-out four-condition set: authoritative when present; the older set is labelled in-distribution ─────────────

def _heldout_numbers():
    n = _numbers()
    conds = {'1_video_only_accuracy': 0.925, '2_audio_only_accuracy': 0.92, '3_standard_fusion_accuracy': 0.76,
             '4_disagreement_aware_fusion_accuracy': 0.947}
    imp = {'RVFA_correctly_flagged_audio_implicated': 1.0, 'FVRA_correctly_flagged_video_implicated': 0.75,
           'RVRA_false_disagreement_rate (should be low)': 0.11, 'FVFA_false_disagreement_rate (should be low)': 0.10}
    n['fallback_4condition'], n['fallback_4condition_implication'] = dict(conds, **{'1_video_only_accuracy': 0.90}), dict(imp)
    n['heldout_4condition'], n['heldout_4condition_implication'] = conds, imp
    n['heldout_advantage_bootstrap'] = {'advantage_pp': 18.4, 'advantage_ci95_pp': [7.9, 28.9], 'n_clips_with_both_scores': 76}
    n['fallback_set_video_membership'] = {'n_clips': 80, 'train': 57, 'val': 8, 'test': 15}
    return n


def test_heldout_section_is_shown_first_and_carries_the_interval():
    e = ev.build_evaluation(_heldout_numbers(), SHIPPED, None, FUSION)
    ids = [s['id'] for s in e['sections']]
    assert ids.index('four_condition_heldout') < ids.index('four_condition')
    rows = {r[0]: r[1] for r in _by_id(e)['four_condition_heldout']['rows']}
    adv = next(v for k, v in rows.items() if k.startswith('Advantage'))
    assert '+18.4 pp' in adv and '7.9' in adv and '28.9' in adv and '76 clips' in adv


def test_older_fusion_set_is_labelled_in_distribution_using_the_measured_membership():
    sec = _by_id(ev.build_evaluation(_heldout_numbers(), SHIPPED, None, FUSION))['four_condition']
    assert 'in-distribution' in sec['title'].lower()
    assert '57 of these 80 videos' in sec['note'] and 'Read the held-out version above' in sec['note']


def test_false_disagreement_rates_are_shown_beside_accuracy():
    """The fake+fake false-disagreement rate (30% on the older set) was easy to miss when only accuracy and implication were shown."""
    labels = [r[0] for r in _by_id(ev.build_evaluation(_heldout_numbers(), SHIPPED, None, FUSION))['four_condition_heldout']['rows']]
    assert any('Wrongly reported as disagreement, fake video + fake audio' in l for l in labels)
    assert any('Wrongly reported as disagreement, real video + real audio' in l for l in labels)


def test_without_a_heldout_run_the_older_set_keeps_its_plain_title_but_still_carries_the_caveat():
    n = _heldout_numbers()
    for k in ('heldout_4condition', 'heldout_4condition_implication', 'heldout_advantage_bootstrap'):
        n.pop(k)
    e = _by_id(ev.build_evaluation(n, SHIPPED, None, FUSION))
    assert 'four_condition_heldout' not in e
    assert '57 of these 80 videos' in e['four_condition']['note']

