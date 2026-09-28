"""Four-condition comparison over ANY manifest matching the schema in
build_fallback_eval_set.py -- video/audio label pairs with a category tag
(RVRA/RVFA/FVRA/FVFA). Deliberately dataset-agnostic: this script does not
care whether the manifest came from the constructed fallback set, DFDC,
DeepfakeTIMIT, or (if it ever arrives) FakeAVCeleb itself. Swapping the
evaluation dataset means running a different build_*.py script to produce a
manifest in this same schema, then pointing --manifest here at it. No
change to this file, fusion.py, or any other pipeline code is needed.

Runs the REAL, already-trained/evaluated pipeline (same code the live app
uses -- video_infer.py, audio_branch.py, vad.py, fusion.py) over every clip
in the manifest and computes:
  1. Video-only accuracy (video score vs video_label)
  2. Audio-only accuracy (audio score vs audio_label)
  3. Standard (naive) fusion: simple average of the two scores, evaluated
     against "is either modality manipulated" (the ground truth a
     non-disagreement-aware system would be trying to predict)
  4. Disagreement-aware fusion (this project's fuse()): same binary accuracy
     for a direct comparison, PLUS the metric that actually matters for this
     project's research question -- on genuinely single-modality-manipulated
     clips (RVFA, FVRA), does fuse() correctly flag disagreement AND name
     the correct implicated modality? This is the fallback-set equivalent of
     the "partial-manipulation F1" Ch3.6 specifies against FakeAVCeleb.

HONESTY NOTE: every number below comes from running the real pipeline on
whichever dataset produced the manifest passed in. Report the manifest's own
"source" field as the provenance, never assume or imply FakeAVCeleb unless
the manifest actually says so.

Run (needs facenet-pytorch + transformers, i.e. the deepfake-detect env):
    /opt/anaconda3/envs/deepfake-detect/bin/python scripts/eval_fallback_4condition.py \\
        [--manifest eval_fallback/manifest.json] [--out-dir results/fallback_eval]
"""

import argparse
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / 'models' / 'best_model.pth'
DEFAULT_MANIFEST_PATH = PROJECT_ROOT / 'eval_fallback' / 'manifest.json'
DEFAULT_OUT_DIR = PROJECT_ROOT / 'results' / 'fallback_eval'

sys.path.insert(0, str(PROJECT_ROOT / 'scripts'))
from video_infer import load_models, analyse_video_file
from audio_branch import load_encoder, extract_audio_16k, embed_waveform, load_trained_svm
from vad import analyse as vad_analyse, vad_available
from fusion import fuse, AUDIO_ACCURACY_IS_MEASURED, AUDIO_ACCURACY_SOURCE, VIDEO_ACCURACY_SOURCE, THRESHOLD_T_DEFAULT, THRESHOLD_T_SOURCE


def run_pipeline(video_path, mtcnn, model, video_device, fe, enc, audio_device, svm):
    """Runs the real 5-stage pipeline on one clip. Returns dict of raw
    per-branch outputs, or None if the video branch found no faces.

    video_device and audio_device are deliberately separate: the video
    model runs on whatever load_models() picked (MPS on this Mac), but the
    audio encoder is loaded via load_encoder('cpu') -- passing the video
    device into embed_waveform() crashes with a device-mismatch error
    (caught by actually running this, not assumed)."""
    video_result = analyse_video_file(str(video_path), mtcnn, model, video_device, max_faces=20)
    if video_result is None:
        return None
    p_video = video_result['p_fake']

    p_audio = None
    wav = extract_audio_16k(str(video_path))
    if wav is not None and wav.size > 0:
        if vad_available():
            vad = vad_analyse(wav)
            if vad.has_speech:
                emb = embed_waveform(wav, fe, enc, audio_device)
                if svm is not None:
                    p_audio = float(svm.spoof_probability(emb.reshape(1, -1))[0])
    return {'p_video': p_video, 'p_audio': p_audio}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', type=Path, default=DEFAULT_MANIFEST_PATH,
                     help='Path to a manifest.json in build_fallback_eval_set.py\'s schema. '
                          'Swap datasets by pointing this at a different builder\'s output.')
    ap.add_argument('--out-dir', type=Path, default=DEFAULT_OUT_DIR)
    args = ap.parse_args()

    if not args.manifest.exists():
        sys.exit(f'{args.manifest} not found -- run the matching build_*.py script first')
    with open(args.manifest) as f:
        manifest = json.load(f)
    clips = manifest['clips']
    source = manifest.get('source', manifest.get('description', 'unknown -- manifest has no source field'))
    print(f'Loaded manifest: {len(clips)} clips')
    print(f'Dataset source: {source}')

    print('Loading models...')
    mtcnn, model, video_device = load_models(str(MODEL_PATH))
    fe, enc, audio_device = load_encoder('cpu')
    svm = load_trained_svm() if AUDIO_ACCURACY_IS_MEASURED else None
    if svm is None:
        print('WARNING: audio SVM not available/not measured -- audio-only and '
              'fusion conditions will be skipped. Video-only will still run.')

    rows = []
    t0 = time.time()
    for i, clip in enumerate(clips):
        video_path = PROJECT_ROOT / clip['output_path']
        result = run_pipeline(video_path, mtcnn, model, video_device, fe, enc, audio_device, svm)
        if result is None:
            print(f'  [{i+1}/{len(clips)}] {clip["id"]}: NO FACES FOUND, skipped')
            continue
        fusion_result = fuse(result['p_video'], result['p_audio'])
        rows.append({**clip, 'p_video': result['p_video'], 'p_audio': result['p_audio'],
                     'fusion_verdict': fusion_result.verdict,
                     'disagreement': fusion_result.disagreement,
                     'implicated_modality': fusion_result.implicated_modality})
        print(f'  [{i+1}/{len(clips)}] {clip["id"]} ({clip["category"]}): '
              f'p_video={result["p_video"]:.3f} p_audio={result["p_audio"]} '
              f'-> {fusion_result.verdict}')
    elapsed = time.time() - t0
    print(f'\nProcessed {len(rows)}/{len(clips)} clips in {elapsed:.1f}s')

    # ── Condition 1: video-only ──────────────────────────────────────────
    v_correct = sum(1 for r in rows if (r['p_video'] >= 0.5) == (r['video_label'] == 'fake'))
    v_acc = v_correct / len(rows) if rows else 0.0

    # ── Condition 2: audio-only (only rows with a genuine audio score) ───
    audio_rows = [r for r in rows if r['p_audio'] is not None]
    a_correct = sum(1 for r in audio_rows if (r['p_audio'] >= 0.5) == (r['audio_label'] == 'spoof'))
    a_acc = a_correct / len(audio_rows) if audio_rows else None

    # ── Condition 3: standard (naive) fusion -- simple average vs "any
    # modality manipulated" ──────────────────────────────────────────────
    naive_rows = audio_rows  # only rows where both scores exist
    naive_correct = 0
    for r in naive_rows:
        naive_score = (r['p_video'] + r['p_audio']) / 2
        ground_truth_fake = (r['video_label'] == 'fake') or (r['audio_label'] == 'spoof')
        naive_correct += int((naive_score >= 0.5) == ground_truth_fake)
    naive_acc = naive_correct / len(naive_rows) if naive_rows else None

    # ── Condition 4: disagreement-aware fusion ───────────────────────────
    # (a) same binary accuracy for direct comparison with condition 3
    da_correct = 0
    for r in naive_rows:
        ground_truth_fake = (r['video_label'] == 'fake') or (r['audio_label'] == 'spoof')
        predicted_fake = r['fusion_verdict'] in ('FAKE', 'PARTIAL_MANIPULATION')
        da_correct += int(predicted_fake == ground_truth_fake)
    da_acc = da_correct / len(naive_rows) if naive_rows else None

    # (b) the metric that actually matters: correct disagreement + correct
    # implicated modality on genuinely single-modality-manipulated clips
    rvfa = [r for r in naive_rows if r['category'] == 'RVFA']  # video real, audio fake
    fvra = [r for r in naive_rows if r['category'] == 'FVRA']  # video fake, audio real
    rvra = [r for r in naive_rows if r['category'] == 'RVRA']  # both genuine -- should NOT disagree
    fvfa = [r for r in naive_rows if r['category'] == 'FVFA']  # both fake -- should NOT disagree

    def rate(items, cond):
        return (sum(1 for r in items if cond(r)) / len(items)) if items else None

    rvfa_correct = rate(rvfa, lambda r: r['disagreement'] and r['implicated_modality'] == 'audio')
    fvra_correct = rate(fvra, lambda r: r['disagreement'] and r['implicated_modality'] == 'video')
    rvra_false_disagreement = rate(rvra, lambda r: r['disagreement'])
    fvfa_false_disagreement = rate(fvfa, lambda r: r['disagreement'])

    summary = {
        'note': f'Dataset source: {source}. Never report this as a FakeAVCeleb result '
                'unless the manifest\'s own source field says so.',
        'n_clips_processed': len(rows),
        'n_clips_total': len(clips),
        'audio_weighting_source': AUDIO_ACCURACY_SOURCE,
        'video_weighting_source': VIDEO_ACCURACY_SOURCE,
        'threshold_T': THRESHOLD_T_DEFAULT,
        'threshold_T_source': THRESHOLD_T_SOURCE,
        'conditions': {
            '1_video_only_accuracy': round(v_acc, 4),
            '2_audio_only_accuracy': round(a_acc, 4) if a_acc is not None else None,
            '3_standard_fusion_accuracy': round(naive_acc, 4) if naive_acc is not None else None,
            '4_disagreement_aware_fusion_accuracy': round(da_acc, 4) if da_acc is not None else None,
        },
        'core_research_question_metrics': {
            'RVFA_correctly_flagged_audio_implicated': round(rvfa_correct, 4) if rvfa_correct is not None else None,
            'FVRA_correctly_flagged_video_implicated': round(fvra_correct, 4) if fvra_correct is not None else None,
            'RVRA_false_disagreement_rate (should be low)': round(rvra_false_disagreement, 4) if rvra_false_disagreement is not None else None,
            'FVFA_false_disagreement_rate (should be low)': round(fvfa_false_disagreement, 4) if fvfa_false_disagreement is not None else None,
        },
        'per_clip_results': rows,
    }

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / 'fallback_4condition_results.json'
    with open(out_path, 'w') as f:
        json.dump(summary, f, indent=2)

    print('\n' + '=' * 70)
    print('RESULTS (self-constructed fallback set -- NOT FakeAVCeleb)')
    print('=' * 70)
    for k, v in summary['conditions'].items():
        print(f'  {k}: {v}')
    print('\nCore research-question metrics:')
    for k, v in summary['core_research_question_metrics'].items():
        print(f'  {k}: {v}')
    print(f'\nFull results: {out_path}')


if __name__ == '__main__':
    main()
