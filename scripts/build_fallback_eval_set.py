"""Build a self-constructed four-category set (FF++ video muxed with ASVspoof audio) as a FakeAVCeleb substitute.
Not a benchmark: it tests whether disagreement is detected, not real end-to-end audio-visual deepfakes.
    python scripts/build_fallback_eval_set.py --n-per-category 20"""

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
    """Mux video_path's video with audio_path's audio, trimmed to the shorter duration.
    Uses an explicit -t because -shortest does not trim reliably with -c:v copy."""
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
