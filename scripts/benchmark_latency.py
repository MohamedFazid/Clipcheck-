"""Per-stage inference latency benchmark (Chapter 3.6).

Chapter 3.6 commits to timing each pipeline stage separately on a fixed test
clip and reporting total end-to-end latency alongside the hardware
configuration, because the system targets journalists and moderators making
time-sensitive decisions: a tool whose processing time is incompatible with
practical use fails regardless of its accuracy.

WHAT IS TIMED, AND THE DISTINCTION THAT MATTERS MOST. Model loading and
per-clip inference are reported separately. Loading the video model, wav2vec2,
MTCNN and the VAD costs seconds, but it happens once per session, not once per
clip; the figure that governs whether the tool is usable is the WARM per-clip
time. Reporting a single blended number would either overstate the cost of
analysing a clip or hide the startup cost entirely, so both are given.

Stages (the video model is whichever one is shipped, named from models/shipped_model.json):
    1. Face extraction (MTCNN) + video-model scoring        -- measured together,
       since they interleave per sampled frame and cannot be cleanly separated
       without changing the inference path the rest of the project uses.
    2. Audio decode (ffmpeg) -> waveform
    3. VAD gate (Silero)
    4. wav2vec2 embedding
    5. SVM spoof prediction (trained on ASVspoof 2019 LA)
    6. Fusion decision (on the REAL video and audio scores of the clip)
    7. Llama 3 explanation generation (real fusion result, local Ollama)
    8. Faithfulness screen on that explanation
Added 2026-09-25, so the benchmark times what the app does now (the 21 Sep figure predates both additions):
    1b. Out-of-domain check on the face features (ledger O1; features come from the same forward pass as stage 1)
    1c. Suspicious-moment windows from the per-frame scores (ledger T1; includes reading the clip's frame rate)
    5b. Out-of-domain check on the speech embedding
    and stages 7 and 8 now receive the real moment windows, as the app's explanation does.
The functions are imported from server.py, so the timed code is the app's own code, not a copy.

A stage that cannot run in the current environment (for example Ollama not reachable) is reported as pending, never
estimated, and the result is then marked complete_pipeline = false.

Refuses to run while a training job is active (latency measured against a busy GPU is meaningless, and running the model
while training swapped the trainer out once, LESSONS L26), and refuses to overwrite an existing latency.json (archive the
old one first, LESSONS L14).

Usage:
    /opt/anaconda3/envs/deepfake-detect/bin/python scripts/benchmark_latency.py
    ... --clip demo_videos/composite_real_video_synthetic_speech.mp4 --runs 5
"""

import os
import sys
import json
import time
import platform
import argparse
from pathlib import Path

os.environ.setdefault('USE_TF', '0')
os.environ.setdefault('USE_FLAX', '0')

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import RESULTS_DIR, MODELS_DIR

OUT_DIR = RESULTS_DIR / 'latency'
DEFAULT_CLIP = 'demo_videos/composite_real_video_synthetic_speech.mp4'


class Timer:
    """Accumulates repeated timings for one stage."""

    def __init__(self, name, note=''):
        self.name, self.note = name, note
        self.samples = []

    def __call__(self, fn):
        t0 = time.perf_counter()
        out = fn()
        self.samples.append(time.perf_counter() - t0)
        return out

    def stats(self):
        if not self.samples:
            return None
        a = np.array(self.samples)
        return {'mean_s': float(a.mean()),
                'std_s': float(a.std(ddof=1)) if a.size > 1 else 0.0,
                'min_s': float(a.min()), 'max_s': float(a.max()),
                'n': int(a.size)}


def hardware_info():
    """Record the machine, since a latency figure is meaningless without it."""
    import torch
    info = {
        'platform': platform.platform(),
        'machine': platform.machine(),
        'processor': platform.processor() or 'Apple Silicon',
        'python': platform.python_version(),
        'torch': torch.__version__,
        'torch_device': 'mps' if torch.backends.mps.is_available() else 'cpu',
    }
    try:
        import subprocess
        cpu = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'],
                             capture_output=True, text=True).stdout.strip()
        if cpu:
            info['cpu'] = cpu
    except Exception:
        pass
    return info


def main():
    ap = argparse.ArgumentParser(description='Per-stage latency benchmark.')
    ap.add_argument('--clip', default=DEFAULT_CLIP,
                    help='Fixed test clip. Default carries speech so the audio '
                         'stages are actually exercised.')
    ap.add_argument('--runs', type=int, default=3, help='Timed repetitions per stage.')
    ap.add_argument('--warmup', type=int, default=1,
                    help='Untimed warm-up runs, discarded. Excluding these '
                         'matters: the first pass pays lazy-init costs that a '
                         'user only meets once.')
    ap.add_argument('--out', default=str(OUT_DIR / 'latency.json'),
                    help='Output file. An existing file is never overwritten silently: archive it or pass --overwrite.')
    ap.add_argument('--overwrite', action='store_true', help='Allow replacing an existing output file.')
    ap.add_argument('--allow-busy', action='store_true',
                    help='Run even if a training job is active (the numbers will not be valid).')
    args = ap.parse_args()

    import subprocess
    if not args.allow_busy and subprocess.run(['pgrep', '-f', 'scripts/train.py'], capture_output=True).returncode == 0:
        print('ERROR: a training job is running; latency measured now would be meaningless (and loading the models '
              'could slow the run). Wait for it to finish, or pass --allow-busy to override.')
        return 3
    out_path = Path(args.out)
    if out_path.exists() and not args.overwrite:
        print(f'ERROR: {out_path} already exists (likely a measurement of an earlier model). Move it to '
              f'{out_path.parent}/OLD_model/ first, or pass --overwrite.')
        return 2

    root = Path(__file__).resolve().parent.parent
    clip = (root / args.clip) if not os.path.isabs(args.clip) else Path(args.clip)
    if not clip.exists():
        print(f'ERROR: clip not found: {clip}')
        return 1

    print('=' * 74)
    print('PER-STAGE LATENCY BENCHMARK')
    print(f'Clip : {clip.name}')
    print(f'Runs : {args.runs} timed (+{args.warmup} warm-up discarded)')
    print('=' * 74)

    hw = hardware_info()
    for k, v in hw.items():
        print(f'  {k:14s}: {v}')

    # ── Cold start: model loading, once per session ──────────────────────────
    print('\n── Cold start (once per session, not per clip) ──')
    load_times = {}

    t0 = time.perf_counter()
    from video_infer import load_models, analyse_video_file, video_model_summary
    vm = video_model_summary()
    mtcnn, model, device = load_models()
    video_key = f'video_models_mtcnn_{vm["arch"]}'
    load_times[video_key] = time.perf_counter() - t0
    print(f'  MTCNN + {vm["name"]:14s}: {load_times[video_key]:6.2f}s'
          + ('' if vm['shipped'] else '   (legacy checkpoint, no shipped_model.json)'))

    from audio_branch import load_encoder, extract_audio_16k, embed_waveform, load_trained_svm
    from fusion import AUDIO_ACCURACY_IS_MEASURED
    t0 = time.perf_counter()
    svm = load_trained_svm() if AUDIO_ACCURACY_IS_MEASURED else None
    if svm is not None:
        load_times['audio_svm'] = time.perf_counter() - t0
        print(f'  audio SVM               : {load_times["audio_svm"]:6.2f}s')
    else:
        print('  audio SVM               : not trained on the full dataset (stage will be reported as pending)')
    t0 = time.perf_counter()
    fe, enc, adevice = load_encoder('cpu')
    load_times['wav2vec2'] = time.perf_counter() - t0
    print(f'  wav2vec2                : {load_times["wav2vec2"]:6.2f}s')

    vad_ok = False
    try:
        from vad import load_vad, analyse as vad_analyse
        t0 = time.perf_counter()
        load_vad()
        load_times['silero_vad'] = time.perf_counter() - t0
        vad_ok = True
        print(f'  Silero VAD              : {load_times["silero_vad"]:6.2f}s')
    except Exception as e:
        print(f'  Silero VAD              : unavailable ({e})')

    from fusion import fuse
    try:
        from explain import explain, explanation_available, build_structured_input
        from explain_checks import check_faithfulness
        llm_ok = explanation_available()
    except Exception:
        llm_ok = False
    print(f'  Llama 3 (Ollama)        : {"reachable" if llm_ok else "NOT reachable"}'
          ' (model resident in the Ollama server, not loaded here)')

    total_cold = sum(load_times.values())
    # Out-of-domain gates and moment windows: the app's own functions (server.py), so the timed path is the app's path.
    t0 = time.perf_counter()
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))      # server.py lives in the project root
    from server import get_ood_gates, _ood_check, _frame_anomalies, _probe_duration_and_fps
    from ood_gate import clip_video_distance
    gates = get_ood_gates()
    load_times['ood_gates'] = time.perf_counter() - t0
    total_cold = sum(load_times.values())
    print(f'  OOD gates (+ server import): {load_times["ood_gates"]:6.2f}s   video {"on" if gates["video"] else "off"}, '
          f'audio {"on" if gates["audio"] else "off"}')
    print(f'  {"TOTAL cold start":24s}: {total_cold:6.2f}s')

    # ── Warm per-clip stages ─────────────────────────────────────────────────
    t_video = Timer(f'face_extraction_and_{vm["arch"]}')
    t_decode = Timer('audio_decode_ffmpeg')
    t_vad = Timer('vad_gate')
    t_embed = Timer('wav2vec2_embedding')
    t_svm = Timer('svm_spoof_prediction')
    t_vood = Timer('ood_check_video')
    t_moments = Timer('moment_windows')
    t_aood = Timer('ood_check_audio')
    t_fuse = Timer('fusion_decision')
    t_llm = Timer('llama3_explanation')
    t_screen = Timer('faithfulness_screen')

    print(f'\n── Warm per-clip stages ──')
    for i in range(args.warmup + args.runs):
        timed = i >= args.warmup
        label = 'timed' if timed else 'warm-up'
        print(f'  pass {i+1}/{args.warmup + args.runs} ({label})…', flush=True)

        def run_video():
            return analyse_video_file(clip, mtcnn, model, device, max_faces=20, return_features=gates['video'] is not None)
        vres = t_video(run_video) if timed else run_video()

        if vres is not None and gates['video'] is not None:
            def run_vood():
                return _ood_check('video', clip_video_distance(gates['video']['gate'], vres['features']))
            _ = t_vood(run_vood) if timed else run_vood()

        anomalies = []
        if vres is not None:
            def run_moments():
                import imageio_ffmpeg
                _dur, fps = _probe_duration_and_fps(str(clip), imageio_ffmpeg.get_ffmpeg_exe())
                return _frame_anomalies(vres['per_frame'], fps)
            anomalies = t_moments(run_moments) if timed else run_moments()

        def run_decode():
            return extract_audio_16k(str(clip))
        wav = t_decode(run_decode) if timed else run_decode()

        vad_res = None
        if vad_ok and wav is not None:
            def run_vad():
                return vad_analyse(wav)
            vad_res = t_vad(run_vad) if timed else run_vad()

        emb = None
        if wav is not None and (vad_res is None or vad_res.has_speech):
            def run_embed():
                return embed_waveform(wav, fe, enc, adevice)
            emb = t_embed(run_embed) if timed else run_embed()

        p_audio = None
        if emb is not None and svm is not None:
            def run_svm():
                return float(svm.spoof_probability(emb.reshape(1, -1))[0])
            p_audio = t_svm(run_svm) if timed else run_svm()
        if emb is not None and gates['audio'] is not None:
            def run_aood():
                return _ood_check('audio', float(gates['audio']['gate'].distance(emb)[0]))
            _ = t_aood(run_aood) if timed else run_aood()

        # The clip's real scores go into fusion and the explanation, as in the app (no invented 0.5 for a missing video score).
        p_video = vres['p_fake'] if vres else None

        def run_fuse():
            return fuse(p_video, p_audio)
        fres = t_fuse(run_fuse) if timed else run_fuse()

        if llm_ok:
            def run_llm():
                return explain(fres, anomalies=anomalies)
            text = t_llm(run_llm) if timed else run_llm()

            def run_screen():
                return check_faithfulness(text, build_structured_input(fres, anomalies))
            _ = t_screen(run_screen) if timed else run_screen()

    # ── Report ───────────────────────────────────────────────────────────────
    stages = [
        (f'1. Face extraction + {vm["name"]}', t_video, f'MTCNN crop + {vm["name"]} scoring, up to 20 frames'),
        ('1b. Unfamiliar-input check (face)', t_vood, 'Mahalanobis distance of the face features to the training data'),
        ('1c. Suspicious-moment windows', t_moments, 'frame rate read + per-frame scores grouped into timed windows'),
        ('2. Audio decode (ffmpeg)', t_decode, 'video -> mono 16 kHz waveform'),
        ('3. VAD gate (Silero)', t_vad, 'speech / non-speech decision'),
        ('4. wav2vec2 embedding', t_embed, '768-d mean-pooled SSL embedding'),
        ('5. SVM spoof prediction', t_svm, 'RBF SVM on the embedding (ASVspoof 2019 LA)'),
        ('5b. Unfamiliar-input check (speech)', t_aood, 'Mahalanobis distance of the speech embedding to the training data'),
        ('6. Fusion decision', t_fuse, 'disagreement check + weighting, on the clip\'s real scores'),
        ('7. Llama 3 explanation', t_llm, 'constrained generation via local Ollama, with the real moment windows'),
        ('8. Faithfulness screen', t_screen, 'automatic check of the generated explanation'),
    ]

    print('\n' + '=' * 74)
    print('RESULTS — warm per-clip latency (mean ± std over '
          f'{args.runs} run{"s" if args.runs != 1 else ""})')
    print('=' * 74)
    print(f'{"Stage":40s} {"Mean":>9s} {"Std":>8s}')
    print('-' * 74)

    measured_total = 0.0
    rows = []
    for label, timer, note in stages:
        st = timer.stats() if timer is not None else None
        if st is None:
            print(f'{label:40s} {"pending":>9s} {"":>8s}   {note}')
            rows.append({'stage': label, 'status': 'pending', 'note': note})
            continue
        measured_total += st['mean_s']
        print(f'{label:40s} {st["mean_s"]:8.3f}s {st["std_s"]:7.3f}s   {note}')
        rows.append({'stage': label, 'status': 'measured', 'note': note, **st})

    print('-' * 74)
    print(f'{"TOTAL (measured stages, warm)":40s} {measured_total:8.3f}s')
    print(f'{"Cold start (once per session)":40s} {total_cold:8.3f}s')

    pending = [r['stage'] for r in rows if r['status'] == 'pending']
    print('\nInterpretation:')
    print(f'  A clip takes ~{measured_total:.1f}s to analyse once the models are warm.')
    if t_llm.stats() and measured_total > 0:
        share = 100 * t_llm.stats()['mean_s'] / measured_total
        print(f'  Explanation generation is {share:.0f}% of that; it is also the '
              'stage most\n  easily made optional or streamed, since the verdict '
              'is available before it runs.')
    if pending:
        print('  INCOMPLETE: stage(s) not measured in this run: ' + '; '.join(pending) + '. The total excludes them and must not be '
              'quoted as a\n  complete pipeline figure.')

    os.makedirs(out_path.parent, exist_ok=True)
    payload = {
        'clip': str(clip.name),
        'video_model': vm,
        'runs': args.runs, 'warmup_discarded': args.warmup,
        'hardware': hw,
        'cold_start_s': load_times,
        'cold_start_total_s': total_cold,
        'stages': rows,
        'measured_total_warm_s': measured_total,
        'complete_pipeline': not pending,
        'pending_stages': pending,
    }
    with open(out_path, 'w') as f:
        json.dump(payload, f, indent=2)
    print(f'\nWrote: {out_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
