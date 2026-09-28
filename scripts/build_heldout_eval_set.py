"""Build the four-category evaluation set from HELD-OUT video only (the corrected version of eval_fallback/).

WHY THIS EXISTS. scripts/build_fallback_eval_set.py (13 Sep) samples videos at random from ALL FaceForensics++ files. The
identity-disjoint split arrived on 19 Sep and the video model was retrained on it, but the set was never re-checked: 57 of its 80
videos turned out to belong to the shipped model's TRAINING split (docs/EXPERIMENTS.md F3 caveat, docs/LESSONS.md L29). The
comparison between standard and disagreement-aware fusion stays valid (both rules get identical scores), but every absolute
figure was optimistic for the video branch.

WHAT THIS DOES DIFFERENTLY. Video is drawn ONLY from videos whose identity group is in the TEST partition of
data_splits/split_v2_identity_grouped.json, so no model trained or validated on this project's split has seen any of them:
    real videos : the 22 test-split real videos
    fake videos : the 22 test-split identity pairs, in each of the three manipulation methods the shipped model was trained on
                  (Deepfakes, FaceSwap, NeuralTextures) = 66 fakes; none of these identities was in training under ANY method
Audio is unchanged from the original set: ASVspoof 2019 LA eval partition (the SVM trained on the train partition only).

Every chosen video is asserted to be in the test split before anything is written, and the manifest records the split file's
hash, so tests/test_heldout_eval_manifest.py can re-verify it later without any video on disk.

LIMITATIONS, stated so they are not rediscovered as flaws:
  * Only 22 real videos exist in the test split, so RVRA and RVFA (20 clips each) draw from the same 22 and share most videos; only
    the audio differs. Video scores for a shared real video are identical, so the effective number of distinct real videos is 22.
  * FVRA and FVFA use DISJOINT fake videos (40 distinct of the 66 available), stratified across the three methods.
  * Still a self-constructed set, not FakeAVCeleb, and the pairing of a video with unrelated audio is artificial.

    /opt/anaconda3/bin/python scripts/build_heldout_eval_set.py --n-per-category 20
"""
import argparse
import json
import random
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_fallback_eval_set as fb  # noqa: E402  (its helpers and paths; its main() is not run)

PROJECT_ROOT = fb.PROJECT_ROOT
OUT_DIR = PROJECT_ROOT / 'eval_heldout'
SPLIT_PATH = PROJECT_ROOT / 'data_splits' / 'split_v2_identity_grouped.json'
METHODS = ('Deepfakes', 'FaceSwap', 'NeuralTextures')
# FVRA takes 7/7/6 fakes per method and FVFA 7/6/7, so each method contributes 13 or 14 of the 40 fakes.
QUOTA = {'FVRA': {'Deepfakes': 7, 'FaceSwap': 7, 'NeuralTextures': 6},
         'FVFA': {'Deepfakes': 7, 'FaceSwap': 6, 'NeuralTextures': 7}}


def test_split_members():
    """(real_ids, fake_pairs) in the test partition of the frozen identity-disjoint split."""
    split = json.load(open(SPLIT_PATH))
    real = sorted(k.split('/', 1)[1] for k, v in split['assignment'].items() if k.startswith('real/') and v == 'test')
    fake = sorted(k.split('/', 1)[1] for k, v in split['assignment'].items() if k.startswith('fake/') and v == 'test')
    return real, fake, split['sha256']


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--n-per-category', type=int, default=20)
    ap.add_argument('--seed', type=int, default=42)
    args = ap.parse_args()
    n = args.n_per_category
    if n != 20:
        sys.exit('the fake-video quotas are defined for 20 clips per category')
    if not fb.ASVSPOOF_PROTOCOL.exists():
        sys.exit(f'ASVspoof protocol not found at {fb.ASVSPOOF_PROTOCOL}')
    if OUT_DIR.exists() and any(OUT_DIR.rglob('*.mp4')):
        sys.exit(f'{OUT_DIR} already contains clips; refusing to overwrite. Move it aside first.')

    rng = random.Random(args.seed)
    real_ids, fake_pairs, split_sha = test_split_members()
    real_paths = [fb.FF_REAL_DIR / f'{i}.mp4' for i in real_ids]
    fake_paths = {m: [PROJECT_ROOT / 'data' / 'manipulated_sequences' / m / 'c23' / 'videos' / f'{p}.mp4' for p in fake_pairs]
                  for m in METHODS}
    missing = [p for p in real_paths + [q for v in fake_paths.values() for q in v] if not p.exists()]
    if missing:
        sys.exit(f'{len(missing)} test-split videos missing on disk, for example {missing[0]}')
    print(f'test split: {len(real_paths)} real videos, {len(fake_pairs)} identity pairs x {len(METHODS)} methods = '
          f'{sum(len(v) for v in fake_paths.values())} fakes (split sha256 {split_sha[:12]})')

    bonafide_ids, spoof_ids = fb.parse_asvspoof_protocol()
    used = {m: set() for m in METHODS}

    def draw_fakes(cat):
        picked = []
        for m in METHODS:
            pool = [p for p in fake_paths[m] if p not in used[m]]
            take = rng.sample(pool, QUOTA[cat][m])
            used[m].update(take)
            picked += [(p, m) for p in take]
        rng.shuffle(picked)
        return picked

    real_a = rng.sample(real_paths, n)
    real_b = rng.sample(real_paths, n)
    fakes_ra, fakes_fa = draw_fakes('FVRA'), draw_fakes('FVFA')
    categories = {
        'RVRA': ('real', 'bonafide', [(p, 'original') for p in real_a], rng.sample(bonafide_ids, n)),
        'RVFA': ('real', 'spoof', [(p, 'original') for p in real_b], rng.sample(spoof_ids, n)),
        'FVRA': ('fake', 'bonafide', fakes_ra, rng.sample(bonafide_ids, n)),
        'FVFA': ('fake', 'spoof', fakes_fa, rng.sample(spoof_ids, n)),
    }

    # The guarantee this whole script exists for: assert it, do not assume it.
    split = json.load(open(SPLIT_PATH))['assignment']
    for cat, (_, _, vids, _) in categories.items():
        for path, _ in vids:
            key = ('real/' if cat.startswith('RV') else 'fake/') + path.stem
            assert split.get(key) == 'test', f'{path} is not in the test split (role {split.get(key)})'

    OUT_DIR.mkdir(exist_ok=True)
    manifest = []
    for cat, (v_label, a_label, vids, utt_ids) in categories.items():
        (OUT_DIR / cat).mkdir(exist_ok=True)
        for i, ((video_path, method), utt_id) in enumerate(zip(vids, utt_ids)):
            audio_path = fb.ASVSPOOF_FLAC_DIR / f'{utt_id}.flac'
            if not audio_path.exists():
                print(f'  WARNING: missing {audio_path}, skipping')
                continue
            out_path = OUT_DIR / cat / f'{cat}_{i:03d}.mp4'
            try:
                fb.mux(video_path, audio_path, out_path)
            except subprocess.CalledProcessError as e:
                print(f'  WARNING: mux failed for {out_path.name}: {e}')
                continue
            manifest.append({'id': f'{cat}_{i:03d}', 'category': cat, 'video_label': v_label, 'audio_label': a_label,
                             'video_method': method, 'video_source': str(video_path.relative_to(PROJECT_ROOT)),
                             'audio_source': str(audio_path), 'output_path': str(out_path.relative_to(PROJECT_ROOT))})
        print(f'{cat}: {sum(1 for m in manifest if m["category"] == cat)}/{n} clips built')

    with open(OUT_DIR / 'manifest.json', 'w') as f:
        json.dump({
            'source': ('HELD-OUT self-constructed set: FF++ c23 video drawn ONLY from the test partition of '
                       'data_splits/split_v2_identity_grouped.json, muxed with ASVspoof 2019 LA eval audio. NOT FakeAVCeleb. '
                       'Supersedes eval_fallback/ for every claim about the video branch; eval_fallback/ is kept as the '
                       'in-distribution version.'),
            'description': 'Held-out 4-category evaluation set (RVRA, RVFA, FVRA, FVFA), 20 clips each.',
            'split_manifest': 'data_splits/split_v2_identity_grouped.json', 'split_sha256': split_sha,
            'test_split_real_videos': len(real_ids), 'test_split_fake_pairs': len(fake_pairs),
            'methods': list(METHODS), 'n_per_category': n, 'seed': args.seed,
            'limitations': ('Only 22 real test videos exist, so RVRA and RVFA share most of their videos and differ only in '
                            'audio. FVRA and FVFA use disjoint fakes. Video and audio are unrelated recordings paired '
                            'artificially.'),
            'clips': manifest}, f, indent=2)
    print(f'\nTotal: {len(manifest)} clips. Manifest: {OUT_DIR / "manifest.json"}')


if __name__ == '__main__':
    main()
