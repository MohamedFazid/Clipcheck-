"""Build the four-category evaluation set from LAV-DF (Cai et al., 2022, arXiv 2204.06228): an independent set with real generators.

WHY. Every four-category set so far (eval_fallback/, eval_heldout/) muxes unrelated FF++ video with ASVspoof audio, so the pairing is
artificial and the audio is in the training corpus's domain. LAV-DF is a published set with all four modification types, made with SV2TTS
voice cloning (audio) and Wav2Lip lip-sync (video) on VoxCeleb2 speakers, so it tests both branches on data neither has seen.

SAMPLING RULE (frozen 2026-09-22 before any model was run on these clips; the script takes no score as input):
    population : LAV-DF clips with split == "test" whose bytes lie wholly inside the parts on disk (part .006 gives 2,532)
    categories : RVRA = not modify_video and not modify_audio    RVFA = not modify_video and modify_audio
                 FVRA = modify_video and not modify_audio          FVFA = modify_video and modify_audio
    sample     : 50 per category, random.Random(42) over the file-name-sorted population; NO filter on duration, speech, face or score
    labels     : video_label 'fake' iff modify_video; audio_label 'spoof' iff modify_audio (LAV-DF's own metadata)

KNOWN LIMITS, recorded in the manifest: VoxCeleb2 speakers are unseen by the audio SVM; Wav2Lip is not one of the three training methods
of the video model; fake segments average 0.65 s inside clips of up to 20 s, so whole-clip scores can dilute them; faces are 224x224; the
video-fake and audio-fake segments of one clip need not overlap in time; clips are not FakeAVCeleb.

    /opt/anaconda3/bin/python scripts/build_lavdf_eval_set.py --parts external_datasets/LAV-DF_parts/LAV-DF.zip.006
"""
import argparse
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import carve_lavdf_parts as carve  # noqa: E402

PROJECT_ROOT = carve.PROJECT_ROOT
OUT_DIR = PROJECT_ROOT / 'eval_lavdf'
METADATA = PROJECT_ROOT / 'external_datasets' / 'LAV-DF' / 'metadata.json'
CATEGORIES = {'RVRA': (False, False), 'RVFA': (False, True), 'FVRA': (True, False), 'FVFA': (True, True)}


def as_fake(flag):
    """LAV-DF's modify_video / modify_audio flag as a bool; anything unrecognised is an error, never silently 'real'."""
    if isinstance(flag, bool):
        return flag
    if isinstance(flag, int) and flag in (0, 1):
        return bool(flag)
    if isinstance(flag, str) and flag.strip().lower() in ('true', 'false', '1', '0', 'real', 'fake'):
        return flag.strip().lower() in ('true', '1', 'fake')
    raise ValueError(f'unrecognised LAV-DF modification flag: {flag!r}')


def select(records, n, seed, split='test'):
    """The frozen sampling rule: {category: (chosen records, pool size)}. The pool is the given records of `split` in that category,
    sorted by file name (so input order cannot matter), and n are drawn with random.Random(f'{seed}-{category}')."""
    out = {}
    for cat, (mv, ma) in CATEGORIES.items():
        pool = sorted((r for r in records if r['split'] == split and as_fake(r['modify_video']) == mv
                       and as_fake(r['modify_audio']) == ma), key=lambda r: r['file'])
        if len(pool) < n:
            sys.exit(f'{cat}: only {len(pool)} clips available, need {n}')
        out[cat] = (random.Random(f'{seed}-{cat}').sample(pool, n), len(pool))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--parts', nargs='+', required=True)
    ap.add_argument('--n-per-category', type=int, default=50)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--split', default='test')
    args = ap.parse_args()
    if OUT_DIR.exists() and any(OUT_DIR.rglob('*.mp4')):
        sys.exit(f'{OUT_DIR} already contains clips; refusing to overwrite. Move it aside first.')
    meta = {r['file']: r for r in json.load(open(METADATA))}

    available = {}   # member name -> (buf-path, method, crc, csize, usize, start)
    for part in sorted(args.parts):
        buf = Path(part).read_bytes()
        for name, method, crc, csize, usize, start in carve.iter_members(buf):
            rel = name.split('/', 1)[1]
            if rel.endswith('.mp4') and meta.get(rel, {}).get('split') == args.split:
                available[rel] = (part, method, crc, csize, usize, buf[start:start + csize])
        del buf
    print(f'{len(available)} complete {args.split} clips on disk')

    manifest = []
    selection = select([meta[f] for f in available], args.n_per_category, args.seed, args.split)
    for cat, (mv, ma) in CATEGORIES.items():
        records, pool_size = selection[cat]
        (OUT_DIR / cat).mkdir(parents=True, exist_ok=True)
        for i, rel in enumerate(r['file'] for r in records):
            part, method, crc, csize, usize, raw = available[rel]
            data = carve.zlib.decompressobj(-15).decompress(raw) if method == 8 else raw
            assert len(data) == usize and (carve.zlib.crc32(data) & 0xFFFFFFFF) == crc, f'CRC failure for {rel}'
            out = OUT_DIR / cat / f'{cat}_{i:03d}.mp4'
            out.write_bytes(data)
            m = meta[rel]
            manifest.append({'id': f'{cat}_{i:03d}', 'category': cat,
                             'video_label': 'fake' if mv else 'real', 'audio_label': 'spoof' if ma else 'bonafide',
                             'lavdf_file': rel, 'lavdf_part': Path(part).name, 'duration_s': m['duration'], 'n_fakes': m['n_fakes'],
                             'fake_periods': m['fake_periods'], 'output_path': str(out.relative_to(PROJECT_ROOT))})
        print(f'{cat}: {args.n_per_category} clips written (pool {pool_size})')

    with open(OUT_DIR / 'manifest.json', 'w') as f:
        json.dump({
            'source': ('LAV-DF (Cai et al., 2022), test split, sampled with the frozen rule in scripts/build_lavdf_eval_set.py. NOT '
                       'FakeAVCeleb. Real generators: SV2TTS voice cloning and Wav2Lip lip-sync on VoxCeleb2 speakers.'),
            'description': 'LAV-DF 4-category evaluation set (RVRA, RVFA, FVRA, FVFA), labels from LAV-DF metadata.json.',
            'n_per_category': args.n_per_category, 'seed': args.seed, 'split': args.split,
            'population_size': len(available),
            'limitations': ('Speakers unseen by the audio SVM; Wav2Lip is not a training method of the video model; fake segments '
                            'average 0.65 s inside clips of up to 20 s; 224x224 faces; only the parts on disk are sampled, so the '
                            'population is the clips wholly inside those parts, not the whole test split.'),
            'clips': manifest}, f, indent=2)
    print(f'Total {len(manifest)} clips -> {OUT_DIR / "manifest.json"}')


if __name__ == '__main__':
    main()
