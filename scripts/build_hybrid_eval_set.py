"""Build a hybrid manifest: fallback-set RVRA/RVFA/FVFA plus real DeepfakeTIMIT clips for FVRA (fake video, genuine audio).
Clips have mixed provenance (per-clip "source" field); report FVRA separately.
    python scripts/build_hybrid_eval_set.py"""

import argparse
import json
import random
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FALLBACK_MANIFEST = PROJECT_ROOT / 'eval_fallback' / 'manifest.json'
DEEPFAKETIMIT_ROOT = PROJECT_ROOT / 'external_datasets' / 'DeepfakeTIMIT'
OUT_DIR = PROJECT_ROOT / 'eval_hybrid'


def deepfaketimit_fvra_clips(quality: str, n: int, seed: int):
    """DeepfakeTIMIT videos are already fake-video/real-audio pairs as
    released -- no muxing needed, video_source == audio_source == the
    original file. quality: 'higher_quality' or 'lower_quality'."""
    quality_dir = DEEPFAKETIMIT_ROOT / quality
    if not quality_dir.exists():
        sys.exit(f'{quality_dir} not found -- extract DeepfakeTIMIT.tar.gz into '
                  f'{DEEPFAKETIMIT_ROOT.parent} first')
    clips = sorted(quality_dir.glob('*/*-video-*.avi'))
    rng = random.Random(seed)
    chosen = rng.sample(clips, min(n, len(clips)))
    out = []
    for i, clip in enumerate(chosen):
        out.append({
            'id': f'FVRA_{i:03d}',
            'category': 'FVRA',
            'video_label': 'fake',
            'audio_label': 'bonafide',
            'video_source': str(clip),
            'audio_source': str(clip),
            'output_path': str(clip),
            'source': f'DeepfakeTIMIT ({quality}, Idiap/Zenodo) -- genuinely paired, '
                       'original unaltered audio kept when face was swapped',
        })
    return out, len(clips)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n-per-category', type=int, default=20)
    ap.add_argument('--seed', type=int, default=42)
    ap.add_argument('--quality', choices=['higher_quality', 'lower_quality'], default='higher_quality',
                     help='DeepfakeTIMIT swap fidelity to use. higher_quality is the more '
                          'visually convincing swap, closer to a genuine deepfake attempt.')
    args = ap.parse_args()

    if not FALLBACK_MANIFEST.exists():
        sys.exit(f'{FALLBACK_MANIFEST} not found -- run build_fallback_eval_set.py first')
    with open(FALLBACK_MANIFEST) as f:
        fallback = json.load(f)

    kept = [c for c in fallback['clips'] if c['category'] != 'FVRA']
    for c in kept:
        c.setdefault('source', 'self-constructed fallback (FF++ video muxed with ASVspoof '
                                '2019 LA audio) -- separately-sourced files combined')
    print(f'Kept from fallback set: {len(kept)} clips (RVRA/RVFA/FVFA)')

    fvra_clips, n_available = deepfaketimit_fvra_clips(args.quality, args.n_per_category, args.seed)
    print(f'DeepfakeTIMIT FVRA: {len(fvra_clips)} clips built ({n_available} available in {args.quality})')

    all_clips = kept + fvra_clips

    OUT_DIR.mkdir(exist_ok=True)
    manifest_path = OUT_DIR / 'manifest.json'
    with open(manifest_path, 'w') as f:
        json.dump({
            'source': 'HYBRID: RVRA/RVFA/FVFA self-constructed (FF++ + ASVspoof 2019 LA, see '
                       'build_fallback_eval_set.py), FVRA genuinely paired from DeepfakeTIMIT '
                       '(Idiap/Zenodo, Korshunov and Marcel). NOT a single-provenance dataset -- '
                       'check each clip\'s own "source" field. NOT FakeAVCeleb.',
            'n_per_category': args.n_per_category, 'seed': args.seed, 'clips': all_clips,
        }, f, indent=2)
    print(f'\nTotal: {len(all_clips)} clips. Manifest: {manifest_path}')
    print('\nCitation required if this manifest is used in any report output:')
    print('  P. Korshunov and S. Marcel, "DeepFakes: a New Threat to Face Recognition? '
          'Assessment and Detection," arXiv and Idiap Research Report, 2018.')
    print('  C. Sanderson and B.C. Lovell, "Multi-Region Probabilistic Histograms for Robust '
          'and Scalable Identity Inference," LNCS vol. 5558, pp. 199-208, 2009.')


if __name__ == '__main__':
    main()
