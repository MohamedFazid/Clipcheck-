"""Builds the in-app Evaluation tab and the per-verdict Limitations panel from results/numbers.json.

Pure Python (no torch, no dataset), so it is unit-testable and cheap to import. The governing rule (docs/LESSONS.md L8, L15):
every figure shown comes from a result file via numbers.json, never typed in here, and anything produced with a superseded
video model is WITHHELD (status "pending") instead of shown, so a stale number cannot be quoted from the app.

    build_evaluation(numbers, shipped, latency, fusion_info) -> {'shipped': ..., 'sections': [...]}
    build_limitations(numbers, shipped, fusion_info)          -> [{'id', 'text', 'source'}, ...]

`shipped` is models/shipped_model.json (or None), `latency` is results/latency/latency.json (or None), `fusion_info` is a dict with
threshold_T, threshold_T_source, video_accuracy_source, audio_accuracy_source. Text produced here uses no em dashes.
"""
from typing import Optional

# Display order: single-method models first, then the multi-method ones. Unknown tags are appended.
_TAG_ORDER = ['aug_vidsplit', 'base_vidsplit', 'reg_vidsplit', 'b0_vidsplit', 'r50_vidsplit', 'xcep_vidsplit', 'cnxt_vidsplit',
              'mm_b4_vidsplit', 'mm_b4reg_vidsplit', 'mm_b0_vidsplit', 'mm_r50_vidsplit', 'mm_xcep_vidsplit', 'mm_cnxt_vidsplit']
_METHODS = ('Deepfakes', 'FaceSwap', 'NeuralTextures')


def _pct(x, places=1):
    return 'n/a' if x is None else f'{x * 100:.{places}f}%'


def _ms(e, pct=True, places=1):
    """mean +- std of a {'mean','std','n'} entry; a single seed shows (n=1) instead of an implied zero spread."""
    if not e:
        return 'n/a'
    if e.get('n', 2) < 2:
        return (f'{e["mean"] * 100:.{places}f}%' if pct else f'{e["mean"]:.3f}') + ' (n=1)'
    return (f'{e["mean"] * 100:.{places}f} ± {e["std"] * 100:.{places}f}%' if pct else f'{e["mean"]:.3f} ± {e["std"]:.3f}')


def _ordered(tags):
    known = [t for t in _TAG_ORDER if t in tags]
    return known + sorted(t for t in tags if t not in _TAG_ORDER)


def _section(sid, title, status, source, columns=None, rows=None, note='', reason=''):
    s = {'id': sid, 'title': title, 'status': status, 'source': source, 'note': note}
    if status == 'current':
        s['columns'], s['rows'] = columns or [], rows or []
    else:
        s['reason'] = reason
    return s


def _is_shipped(tag, shipped):
    return bool(shipped and shipped.get('tag') == tag)


def build_evaluation(numbers: dict, shipped: Optional[dict], latency: Optional[dict] = None,
                     fusion_info: Optional[dict] = None) -> dict:
    numbers = numbers or {}
    sections = []
    video = {t: e for t, e in (numbers.get('video') or {}).items() if str(e.get('split', '')).startswith('v2')}

    # 1. Video model comparison (identity-disjoint split only; the earlier leaking-split figures are not shown)
    rows = []
    for t in _ordered(video):
        e = video[t]
        vl = e.get('video_level')
        rows.append([e['label'] + ('  [SHIPPED]' if _is_shipped(t, shipped) else ''),
                     'multi-method' if 'multi' in str(e.get('frames_dir', '')) else 'Deepfakes only',
                     _ms(e.get('val_accuracy_at_best_epoch')), _ms(vl['accuracy']) if vl else 'n/a',
                     _ms(e['frame_level'].get('accuracy')),
                     f'{e["overfitting_gap_pp"]["mean"]:.1f} pp' if e.get('overfitting_gap_pp') else 'n/a'])
    sections.append(_section(
        'video_models', 'Video model comparison', 'current' if rows else 'pending', 'results/numbers.json (video)',
        ['Model', 'Trained on', 'Validation accuracy', 'Clip accuracy (44 test videos)', 'Frame accuracy', 'Train minus validation gap'],
        rows, note=('Identity-disjoint split: no video or identity is shared between train, validation and test. 3 seeds, one shared '
                    'recipe. One test video is 2.3 percentage points. Multi-method rows are scored on a harder mixed test set, so '
                    'do not compare their accuracy with single-method rows; compare per-method detection below. Figures from the '
                    'earlier split that leaked test videos into training are superseded and are not shown.'),
        reason='no results found'))

    # 2. Per-method detection
    cm = numbers.get('cross_method') or {}
    rows = []
    for t in _ordered(cm):
        ms = cm[t]['mean_std']
        multi = 'multi' in str((video.get(t) or {}).get('frames_dir', ''))
        role = 'all three methods seen in training' if multi else 'FaceSwap and NeuralTextures never seen'
        rows.append([(video.get(t) or {}).get('label', t) + ('  [SHIPPED]' if _is_shipped(t, shipped) else ''), role]
                    + [_ms(ms[m]['fake_detection_rate']) for m in _METHODS] + [_ms(ms['Deepfakes'].get('real_specificity'))])
    sections.append(_section(
        'per_method', 'Detection by manipulation method', 'current' if rows else 'pending', 'results/numbers.json (cross_method)',
        ['Model', 'Test condition'] + [f'{m} fakes detected' for m in _METHODS] + ['Real videos kept real'], rows,
        note='Test videos are unseen identities (22 real + 22 fake per method). A single-method model fails on methods it never saw.',
        reason='no results found'))

    # 3. Cross-validation (only ever described for the architecture it was measured on)
    for name, cv in (numbers.get('cross_validation') or {}).items():
        po, ci = cv['pooled_out_of_fold'], cv['ci95_cluster_bootstrap']
        applies = bool(shipped and cv.get('arch') and shipped.get('arch') == cv.get('arch'))
        rows = []
        for key, lab, pct in (('accuracy', 'Accuracy at 0.5', True), ('auc', 'AUC-ROC', False), ('real_specificity', 'Real videos kept real', True),
                              ('fake_detection', 'Fakes detected', True), ('detect_FaceSwap', 'FaceSwap detected', True),
                              ('detect_NeuralTextures', 'NeuralTextures detected', True), ('eer', 'EER', True)):
            if key in po:
                f = (lambda v: f'{v * 100:.1f}%') if pct else (lambda v: f'{v:.3f}')
                rows.append([lab, f(po[key]), f'{f(ci[key][0])} to {f(ci[key][1])}' if key in ci else 'n/a'])
        sections.append(_section(
            f'cv_{name}', f'Cross-validation ({cv.get("arch") or "unknown architecture"}, {po["n_videos"]} videos)', 'current',
            f'results/cv/{name}/cv_summary.json', ['Metric', 'Pooled out-of-fold', '95% interval'], rows,
            note=('Every video is scored once by a model that never saw its identity; intervals resample whole identity groups. '
                  + ('This matches the shipped architecture.' if applies else
                     'This describes ' + str(cv.get('arch')) + ' only, NOT the shipped model; do not read it as the shipped model\'s accuracy.'))))

    # 4. Cross-dataset
    cd = numbers.get('cross_dataset_celebdf_v2') or {}
    rows = []
    for t in _ordered(cd):
        c = cd[t]
        rows.append([(video.get(t) or {}).get('label', t) + ('  [SHIPPED]' if _is_shipped(t, shipped) else ''), str(c.get('seed')),
                     _pct(c['accuracy']), f'{c["auc_roc"]:.3f}', _pct(c['eer']), _pct(c['fake_detection']), _pct(c['real_specificity'])])
    sections.append(_section(
        'celebdf', 'Different dataset: Celeb-DF-v2 (zero-shot)', 'current' if rows else 'pending', 'results/cross_dataset/celebdf_v2__*/metrics.json',
        ['Model', 'Seed', 'Accuracy at 0.5', 'AUC-ROC', 'EER', 'Fakes detected', 'Real videos kept real'], rows,
        note='Official test list: 178 real + 340 fake videos, no retraining. The literature reports about 70 to 75% for FaceForensics++-trained '
             'detectors (Khan and Dang-Nguyen, 2023).', reason='not measured'))

    # 5. Audio branch
    audio = numbers.get('audio') or {}
    base, extra = audio.get('baseline_comparison'), audio.get('wav2vec2_svm_extra')
    rows = []
    if base:
        u = base['unseen_corpus_genuine_speech']
        rows.append(['MFCC + SVM (baseline)', _pct(base['mfcc_svm']['eval_eer'], 2), _pct(base['mfcc_svm']['eval_accuracy'], 2), 'n/a',
                     f'{u["mfcc_svm"]["fa_at_p0.5"] * 100:.0f}% of {u["n_clips"]}'])
        w = base['wav2vec2_svm']
        rows.append(['wav2vec2 + SVM (used)', _pct(w['eval_eer'], 2), _pct(w['eval_accuracy'], 2),
                     f'{extra["at_probability_0.5 (as the app and fusion use it)"]["balanced_accuracy"] * 100:.1f}%' if extra else 'n/a',
                     f'{u["wav2vec2_svm"]["fa_at_p0.5"] * 100:.0f}% of {u["n_clips"]}'])
    sections.append(_section(
        'audio', 'Audio branch (ASVspoof 2019 LA)', 'current' if rows else 'pending', 'results/audio_baseline/metrics.json, results/audio_branch/',
        ['Front end', 'EER', 'Accuracy', 'Balanced accuracy', 'Genuine speech from another corpus flagged as spoof'], rows,
        note=('The evaluation set is mostly spoofed audio, so always answering "spoof" scores '
              + (f'{extra["majority_class_baseline_accuracy"] * 100:.1f}%' if extra else 'a high figure')
              + ' accuracy; balanced accuracy is the fairer figure. The classifier is single-corpus: it called every genuine clip from a '
                'different corpus spoofed.'), reason='no results found'))

    # 6. Fusion evidence: shown only when produced with the shipped model; otherwise withheld
    old_only = lambda key: (numbers.get(key) is None) and (numbers.get(key + '_OLD_MODEL') is not None)
    member = numbers.get('fallback_set_video_membership') or {}

    def fusion_rows(cur, imp, boot):
        rows = [[lab, f'{cur[k] * 100:.1f}%'] for k, lab in (('1_video_only_accuracy', 'Video only'), ('2_audio_only_accuracy', 'Audio only'),
                                                          ('3_standard_fusion_accuracy', 'Standard (unweighted) fusion'),
                                                          ('4_disagreement_aware_fusion_accuracy', 'Disagreement-aware fusion')) if k in cur]
        if boot:
            lo, hi = boot['advantage_ci95_pp']
            rows.append(['Advantage of disagreement-aware over standard fusion',
                         f'{boot["advantage_pp"]:+.1f} pp (95% interval {lo:+.1f} to {hi:+.1f}, {boot["n_clips_with_both_scores"]} clips)'])
        # Accuracy is not the contribution; naming the right modality is. Show both, always, and show the false alarms too.
        for k, lab in (('RVFA_correctly_flagged_audio_implicated', 'Correctly named AUDIO on real video + fake audio'),
                       ('FVRA_correctly_flagged_video_implicated', 'Correctly named VIDEO on fake video + real audio'),
                       ('RVRA_false_disagreement_rate (should be low)', 'Wrongly reported as disagreement, real video + real audio'),
                       ('FVFA_false_disagreement_rate (should be low)', 'Wrongly reported as disagreement, fake video + fake audio')):
            if k in imp:
                rows.append([lab, f'{imp[k] * 100:.0f}%'])
        return rows

    held = numbers.get('heldout_4condition')
    if held:
        sections.append(_section(
            'four_condition_heldout', 'Four-condition comparison, HELD-OUT video (authoritative)', 'current', 'results/heldout_eval_shipped/',
            ['Measure', 'Value'], fusion_rows(held, numbers.get('heldout_4condition_implication') or {}, numbers.get('heldout_advantage_bootstrap')),
            note=('Every video is from the TEST partition of the frozen identity-disjoint split, so the video model never saw it or its '
                  'identity (checked by tests/test_heldout_eval_manifest.py). Only 22 real test videos exist, so the real-video categories '
                  'share most of their videos. Self-built set (FF++ video + ASVspoof audio), not FakeAVCeleb, which was never obtained.')))
    for key, sid, title in (('fallback_4condition', 'four_condition',
                             'Four-condition comparison, earlier set (in-distribution for the video model)' if held else 'Four-condition comparison (constructed evaluation set)'),
                            ('hybrid_4condition', 'hybrid', 'Four-condition comparison with genuine speech from another corpus')):
        cur = numbers.get(key)
        if cur:
            imp = numbers.get(key + '_implication') or {}
            note = 'Self-built set (FF++ video + ASVspoof audio), not FakeAVCeleb, which was never obtained.'
            if sid == 'four_condition' and member.get('train') is not None:
                note = (f'{member["train"]} of these {member["n_clips"]} videos were in the video model\'s training split, so this set is '
                        f'in-distribution for the video branch (the audio side is held out). The comparison between fusion rules is still valid, '
                        f'because both rules receive identical scores, but the absolute figures are not held-out figures.'
                        + (' Read the held-out version above.' if held else ''))
            if sid == 'hybrid':
                note = ('The fake-video clips here come from a different dataset (DeepfakeTIMIT), so both branches are out of their '
                        'training distribution. Read the accuracy together with the row below it: the high accuracy is produced by the '
                        'audio branch false-alarming on genuine speech at the same time as the video branch misses the manipulation, '
                        'so the tool reaches "not authentic" while naming the wrong modality.')
            boot = numbers.get('fallback_advantage_bootstrap') if sid == 'four_condition' else None
            sections.append(_section(sid, title, 'current', f'results/{key}', ['Measure', 'Value'], fusion_rows(cur, imp, boot), note=note))
        else:
            sections.append(_section(sid, title, 'pending', f'results/{key}', reason=(
                'Existing results were produced with the superseded video model and are withheld until re-run on the shipped model.'
                if old_only(key) else 'Not run yet.')))

    # 7. Latency: only if complete and measured on the shipped model
    if latency and latency.get('complete_pipeline') and (not shipped or (latency.get('video_model') or {}).get('tag') == shipped.get('tag')):
        rows = [[r['stage'], f'{r["mean_s"]:.2f} s', f'{r["std_s"]:.2f} s'] for r in latency['stages'] if r.get('status') == 'measured']
        rows.append(['Total (warm, per clip)', f'{latency["measured_total_warm_s"]:.2f} s', ''])
        hw = latency.get('hardware') or {}
        sections.append(_section('latency', 'Latency per stage', 'current', 'results/latency/latency.json', ['Stage', 'Mean', 'Std'], rows,
                                 note=f'Measured on {hw.get("cpu", "unknown CPU")} ({hw.get("torch_device", "?")}); cold start '
                                      f'{latency.get("cold_start_total_s", 0):.1f} s once per session.'))
    else:
        sections.append(_section('latency', 'Latency per stage', 'pending', 'results/latency/latency.json',
                                 reason='Not measured for the shipped model yet (an earlier figure measured a different video model and no audio classifier).'))

    # 8. Fusion settings, with provenance
    if fusion_info:
        sections.append(_section('fusion_settings', 'Fusion settings and where they come from', 'current', 'scripts/fusion.py',
                                 ['Setting', 'Value', 'Source'],
                                 [['Disagreement threshold T', f'{fusion_info["threshold_T"]:.2f}', fusion_info['threshold_T_source']],
                                  ['Video weight basis', '', fusion_info['video_accuracy_source']],
                                  ['Audio weight basis', '', fusion_info['audio_accuracy_source']]]))
    return {'generated_at': numbers.get('generated_at'), 'shipped': shipped, 'sections': sections}


def build_limitations(numbers: dict, shipped: Optional[dict], fusion_info: Optional[dict] = None) -> list:
    """Plain-language limits shown next to every verdict. Each is grounded in a file; where no number exists it says so."""
    numbers = numbers or {}
    out = []
    trained_on = (shipped or {}).get('trained_on')
    if trained_on and 'multi' in trained_on:
        text = ('The video model was trained on three of the four FaceForensics++ manipulation methods (Deepfakes, FaceSwap, '
                'NeuralTextures). Face2Face and manipulations made by other tools are not covered.')
    elif trained_on:
        text = ('The video model was trained on a single manipulation method (' + trained_on + '). Other methods are largely '
                'undetected: in testing, an earlier single-method model detected none of the FaceSwap fakes.')
    else:
        text = 'The training data of this video checkpoint is not recorded, so its coverage of manipulation methods is unknown.'
    out.append({'id': 'coverage', 'text': text, 'source': 'models/shipped_model.json; results/cross_method/'})

    tag = (shipped or {}).get('tag')
    cv = next((c for c in (numbers.get('cross_validation') or {}).values() if shipped and c.get('arch') == shipped.get('arch')), None)
    vid = (numbers.get('video') or {}).get(tag) if tag else None
    if cv:
        po, ci = cv['pooled_out_of_fold'], cv['ci95_cluster_bootstrap']
        text = (f'Estimated accuracy on people the model has not seen is about {po["accuracy"] * 100:.0f}% (95% interval '
                f'{ci["accuracy"][0] * 100:.0f}% to {ci["accuracy"][1] * 100:.0f}%), from cross-validation over {po["n_videos"]} videos.')
        src = 'results/cv/'
    elif vid and vid.get('video_level'):
        n, a = vid['video_level']['n_videos'], vid['video_level']['accuracy']['mean']
        text = (f'Measured accuracy is {a * 100:.0f}% on {n} held-out test videos. That is a small test set (one video is '
                f'{100 / n:.1f} percentage points), so treat it as a rough estimate.')
        src = 'results/runs/' + tag
    else:
        text, src = 'No measured accuracy is available for this video model.', 'none'
    out.append({'id': 'accuracy', 'text': text, 'source': src})

    c = (numbers.get('cross_dataset_celebdf_v2') or {}).get(tag) if tag else None
    if c:
        text = (f'On a different dataset (Celeb-DF-v2) this model\'s accuracy fell to {c["accuracy"] * 100:.0f}% and '
                f'{(1 - c["real_specificity"]) * 100:.0f}% of genuine videos were flagged as fake. Results on other kinds of video can be much worse.')
    else:
        text = 'This model has not been measured on a different dataset, so its accuracy on other kinds of video is unknown.'
    out.append({'id': 'other_datasets', 'text': text, 'source': 'results/cross_dataset/'})

    base = (numbers.get('audio') or {}).get('baseline_comparison')
    if base:
        u = base['unseen_corpus_genuine_speech']
        fa = u['wav2vec2_svm']['fa_at_p0.5']
        text = (f'The audio classifier was trained on one speech corpus. It flagged {fa * 100:.0f}% of {u["n_clips"]} genuine clips from '
                'a different corpus as spoofed, so a genuine voice can be wrongly reported as synthetic.')
    else:
        text = 'The audio classifier was trained on a single speech corpus; its behaviour on other recordings is not measured.'
    out.append({'id': 'audio_corpus', 'text': text, 'source': 'results/audio_baseline/metrics.json'})

    imp = numbers.get('hybrid_4condition_implication') or {}
    fvra = imp.get('FVRA_correctly_flagged_video_implicated')
    if fvra is not None and fvra < 0.5:
        out.append({'id': 'wrong_modality_out_of_distribution',
                    'text': ('When a clip is unlike the data these models were trained on, the tool can still report a confident verdict '
                             'but name the wrong part. On a test using video from another dataset with genuine speech, it named the '
                             f'manipulated part correctly in {fvra * 100:.0f}% of cases: it blamed the audio, which was real. Treat the '
                             'named modality as a pointer, not a conclusion, especially for footage unlike a news-style talking head.'),
                    'source': 'results/hybrid_eval_shipped/, docs/EXPERIMENTS.md H2'})

    out.append({'id': 'audio_speech_only', 'text': 'Audio is only scored when speech is detected. A clip with music or no speech has no audio score, '
                'and the verdict then rests on the video alone.', 'source': 'scripts/vad.py, PPR 3.4'})
    out.append({'id': 'scope', 'text': 'Fully synthetic faces (no source face) and live scanning are outside the scope of this tool.',
                'source': 'PPR Ch1 (Scope)'})
    if fusion_info:
        out.append({'id': 'threshold', 'text': f'The disagreement threshold T = {fusion_info["threshold_T"]:.2f} was {fusion_info["threshold_T_source"]}.',
                    'source': 'scripts/fusion.py'})
    out.append({'id': 'estimate', 'text': 'Scores are estimates, not proof. The written explanation is generated text that is automatically checked '
                'against the scores; when the check fails a fixed template is shown instead. Use the result as one input to human judgment.',
                'source': 'PPR 3.4'})
    return out
