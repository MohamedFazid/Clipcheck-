"""Build a self-constructed 4-category audio-visual evaluation set.

WHY THIS EXISTS (read before touching): the project's four-condition
evaluation (Ch3.6/Ch3.7) was designed around FakeAVCeleb, which requires
gated author approval. As of this script's creation, TWO separate official
requests have failed to produce data in time for the project deadline: the
FakeAVCeleb request went unanswered, and a subsequent AV-Deepfake1M request
was rejected. This script builds a substitute evaluation set from datasets
ALREADY on disk and already used elsewhere in this project -- no new
external dependency, no provenance risk, fully auditable.

Method: FakeAVCeleb's four categories are (real video, real audio),
(real video, fake audio), (fake video, real audio), (fake video, fake
audio). This script reproduces that same 2x2 structure by muxing:
  - video track from FaceForensics++ (already labelled real/fake, the same
    data the video branch is trained and evaluated on)
  - audio track from ASVspoof 2019 LA's eval partition (already labelled
    bonafide/spoof, the same data the audio branch is trained and
    evaluated on -- and MORE diverse than FakeAVCeleb's own audio side,
    since ASVspoof's spoof class spans 19 distinct attack algorithms
    (A01-A19: various TTS/voice-conversion systems), vs FakeAVCeleb's
    single SV2TTS method)

HONESTY NOTE: this is a constructed evaluation set, not a benchmark dataset.
It demonstrates the disagreement-aware fusion mechanism against real,
correctly-labelled single-modality manipulation cases; it does not carry
FakeAVCeleb's external validity (its clips are not adversarially designed
audio-visual deepfakes -- they are independently-real video paired with
independently-real/spoofed audio, which is exactly what's needed to test
"does disagreement between two real, correctly-labelled signals get
detected," but not a claim that this matches the difficulty of a genuine
end-to-end audio-visual deepfake). Report this distinction explicitly.

Run (no torch/facenet needed -- just file listing + ffmpeg subprocess calls,
works in either conda env; base is used here for consistency):
    /opt/anaconda3/bin/python scripts/build_fallback_eval_set.py --n-per-category 20
"""

import argparse
import json
import random
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FF_REAL_DIR = PROJECT_ROOT / 'data' / 'original_sequences' / 'youtube' / 'c23' / 'videos'
FF_FAKE_DIR = PROJECT_ROOT / 'data' / 'manipulated_sequences' / 'Deepfakes' / 'c23' / 'videos'
ASVSPOOF_ROOT = Path.home() / 'Downloads' / 'LA'
ASVSPOOF_PROTOCOL = ASVSPOOF_ROOT / 'ASVspoof2019_LA_cm_protocols' / 'ASVspoof2019.LA.cm.eval.trl.txt'
ASVSPOOF_FLAC_DIR = ASVSPOOF_ROOT / 'ASVspoof2019_LA_eval' / 'flac'
OUT_DIR = PROJECT_ROOT / 'eval_fallback'
FFMPEG = 'ffmpeg'  # relies on system ffmpeg (confirmed present at /opt/homebrew/bin/ffmpeg)


def parse_asvspoof_protocol():
    """Returns (bonafide_utt_ids, spoof_utt_ids) from the eval protocol.
    Format per line: '<speaker> <utt_id> - <attack_id> <bonafide|spoof>'."""
    bonafide, spoof = [], []
    with open(ASVSPOOF_PROTOCOL) as f:
        for line in f:
            parts = line.split()
            if len(parts) != 5:
                continue
            utt_id, label = parts[1], parts[4]
            (bonafide if label == 'bonafide' else spoof).append(utt_id)
    return bonafide, spoof


def _probe_duration(path: Path) -> float:
    out = subprocess.run(
        ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', str(path)],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    return float(out)


def mux(video_path: Path, audio_path: Path, out_path: Path):
    """Video track from video_path + audio track from audio_path, trimmed to
    the shorter of the two. NOTE: `-shortest` alone does NOT reliably trim
    when the video stream is `-c:v copy` (confirmed by testing -- the
    container kept the full original video duration with a much shorter
    audio track). Fixed by explicitly probing both durations and passing
    `-t <min>` rather than trusting `-shortest`."""
    duration = min(_probe_duration(video_path), _probe_duration(audio_path))
    cmd = [
        FFMPEG, '-y', '-i', str(video_path), '-i', str(audio_path),
        '-map', '0:v:0', '-map', '1:a:0',
        '-c:v', 'copy', '-c:a', 'aac', '-t', f'{duration:.3f}',
        '-loglevel', 'error', str(out_path),
    ]
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n-per-category', type=int, default=20)
    ap.add_argument('--seed', type=int, default=42)
    args = ap.parse_args()

    if not ASVSPOOF_PROTOCOL.exists():
        sys.exit(f'ASVspoof protocol not found at {ASVSPOOF_PROTOCOL} -- check --root path')
    if not FF_REAL_DIR.exists() or not FF_FAKE_DIR.exists():
        sys.exit('FF++ real/fake video directories not found under data/')

    rng = random.Random(args.seed)

    bonafide_ids, spoof_ids = parse_asvspoof_protocol()
    print(f'ASVspoof eval: {len(bonafide_ids)} bonafide, {len(spoof_ids)} spoof utterances available')

    real_videos = sorted(FF_REAL_DIR.glob('*.mp4'))
    fake_videos = sorted(FF_FAKE_DIR.glob('*.mp4'))
    print(f'FF++: {len(real_videos)} real videos, {len(fake_videos)} fake (Deepfakes) videos available')

    n = args.n_per_category
    categories = {
        'RVRA': ('real', 'bonafide', rng.sample(real_videos, n), rng.sample(bonafide_ids, n)),
        'RVFA': ('real', 'spoof', rng.sample(real_videos, n), rng.sample(spoof_ids, n)),
        'FVRA': ('fake', 'bonafide', rng.sample(fake_videos, n), rng.sample(bonafide_ids, n)),
        'FVFA': ('fake', 'spoof', rng.sample(fake_videos, n), rng.sample(spoof_ids, n)),
    }

    OUT_DIR.mkdir(exist_ok=True)
    manifest = []
    for cat, (v_label, a_label, videos, utt_ids) in categories.items():
        cat_dir = OUT_DIR / cat
        cat_dir.mkdir(exist_ok=True)
        for i, (video_path, utt_id) in enumerate(zip(videos, utt_ids)):
            audio_path = ASVSPOOF_FLAC_DIR / f'{utt_id}.flac'
            if not audio_path.exists():
                print(f'  WARNING: missing {audio_path}, skipping')
                continue
            out_name = f'{cat}_{i:03d}.mp4'
            out_path = cat_dir / out_name
            try:
                mux(video_path, audio_path, out_path)
            except subprocess.CalledProcessError as e:
                print(f'  WARNING: mux failed for {out_name}: {e}')
                continue
            manifest.append({
                'id': f'{cat}_{i:03d}',
                'category': cat,
                'video_label': v_label,
                'audio_label': a_label,
                'video_source': str(video_path.relative_to(PROJECT_ROOT)),
                'audio_source': str(audio_path),
                'output_path': str(out_path.relative_to(PROJECT_ROOT)),
            })
        print(f'{cat}: {sum(1 for m in manifest if m["category"] == cat)}/{n} clips built')

    manifest_path = OUT_DIR / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump({
            'source': 'self-constructed fallback (FF++ video muxed with ASVspoof 2019 LA audio) '
                       '-- NOT FakeAVCeleb, NOT DFDC, NOT any real jointly-manipulated dataset. '
                       'RVFA/FVRA pairings are two separately-sourced files combined, not naturally '
                       'co-occurring manipulation.',
            'description': 'Self-constructed fallback 4-category evaluation set '
                            '(FakeAVCeleb unanswered, AV-Deepfake1M rejected). '
                            'Video from FaceForensics++, audio from ASVspoof 2019 LA eval.',
            'n_per_category': n, 'seed': args.seed, 'clips': manifest,
        }, f, indent=2)
    print(f'\nTotal: {len(manifest)} clips. Manifest: {manifest_path}')


if __name__ == '__main__':
    main()
