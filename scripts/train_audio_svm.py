"""Train and evaluate the audio anti-spoofing branch on ASVspoof 2019 LA.

Implements the audio half of the pipeline specified in Chapter 3:

    ASVspoof 2019 LA flac -> wav2vec2-base SSL encoder -> mean-pooled 768-d
    embedding -> SVM (bona fide vs spoof) -> P(audio_fake) -> EER

The Logical Access partition is used because its evaluation set contains attack
types never seen in training (Chapter 2), so the reported EER reflects unseen
attacks rather than memorised ones. The three official partitions are honoured
exactly as distributed: train fits the SVM, dev selects hyperparameters, and
eval is scored once at the end and never used for any fitting decision.

EXPECTED LAYOUT. The script targets the dataset as officially distributed:

    <root>/LA/ASVspoof2019_LA_train/flac/*.flac
    <root>/LA/ASVspoof2019_LA_dev/flac/*.flac
    <root>/LA/ASVspoof2019_LA_eval/flac/*.flac
    <root>/LA/ASVspoof2019_LA_cm_protocols/
        ASVspoof2019.LA.cm.train.trn.txt
        ASVspoof2019.LA.cm.dev.trl.txt
        ASVspoof2019.LA.cm.eval.trl.txt

Protocol lines are whitespace-separated, with the utterance id in column 2 and
the bona fide/spoof key in the final column. If the layout differs the script
fails immediately with the paths it tried, rather than silently training on a
partial set. Run --check-layout first to validate a download without waiting
for a full embedding pass.

COST. Embedding is the expensive step, not fitting: the full train partition is
25,380 utterances and wav2vec2 runs per-utterance. Embeddings are therefore
cached to .npy per partition and reused, and --max-per-class subsamples for a
first pass. Any subsampling is recorded in the metrics file, because an EER
computed on a subset is not comparable to a published full-set figure and must
not be reported as though it were.

Usage:
    python scripts/train_audio_svm.py --root ~/data/ASVspoof2019 --check-layout
    python scripts/train_audio_svm.py --root ~/data/ASVspoof2019 --max-per-class 2000
    python scripts/train_audio_svm.py --root ~/data/ASVspoof2019
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path

os.environ.setdefault('USE_TF', '0')
os.environ.setdefault('USE_FLAX', '0')

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import RESULTS_DIR, MODELS_DIR, set_seed, compute_eer

SR = 16000
PARTITIONS = {
    'train': ('ASVspoof2019_LA_train', 'ASVspoof2019.LA.cm.train.trn.txt'),
    'dev':   ('ASVspoof2019_LA_dev',   'ASVspoof2019.LA.cm.dev.trl.txt'),
    'eval':  ('ASVspoof2019_LA_eval',  'ASVspoof2019.LA.cm.eval.trl.txt'),
}
OUT_DIR = RESULTS_DIR / 'audio_branch'
CACHE_DIR = OUT_DIR / 'embeddings'
MODEL_PATH = MODELS_DIR / 'audio_spoof_svm.joblib'


def resolve_paths(root: Path, partition: str):
    """Return (flac_dir, protocol_file) for a partition, or raise with detail."""
    subdir, protocol = PARTITIONS[partition]
    la = root / 'LA'
    base = la if la.is_dir() else root          # tolerate root already being LA/
    flac_dir = base / subdir / 'flac'
    proto = base / 'ASVspoof2019_LA_cm_protocols' / protocol
    missing = [str(p) for p in (flac_dir, proto) if not p.exists()]
    if missing:
        raise FileNotFoundError(
            f'ASVspoof layout not as expected for partition {partition!r}. '
            f'Missing: {missing}. Expected the dataset as officially '
            f'distributed (see this module docstring); pass --root pointing at '
            f'the directory that contains LA/.')
    return flac_dir, proto


def read_protocol(proto_path: Path):
    """Parse a CM protocol file -> [(utt_id, label)] with label 1 = spoof.

    Format: <speaker> <utt_id> <...> <system_id> <bonafide|spoof>
    Only columns 2 and last are used, which is stable across the LA protocol
    files (trn and trl differ in their middle columns).
    """
    items = []
    with open(proto_path) as f:
        for lineno, line in enumerate(f, 1):
            parts = line.split()
            if not parts:
                continue
            if len(parts) < 2:
                raise ValueError(f'{proto_path}:{lineno}: unparseable line: {line!r}')
            utt_id, key = parts[1], parts[-1].lower()
            if key not in ('bonafide', 'spoof'):
                raise ValueError(
                    f'{proto_path}:{lineno}: expected final column to be '
                    f'"bonafide" or "spoof", got {parts[-1]!r}')
            items.append((utt_id, 1 if key == 'spoof' else 0))
    if not items:
        raise ValueError(f'{proto_path}: no entries parsed')
    return items


def subsample(items, max_per_class, seed=42):
    """Balanced subsample. Returns items unchanged when max_per_class is None."""
    if not max_per_class:
        return items
    rng = np.random.default_rng(seed)
    out = []
    for label in (0, 1):
        pool = [it for it in items if it[1] == label]
        if len(pool) > max_per_class:
            idx = rng.choice(len(pool), max_per_class, replace=False)
            pool = [pool[i] for i in sorted(idx)]
        out += pool
    return out


def load_audio(path: Path):
    """Load a flac/wav file as mono float32 at SR."""
    import soundfile as sf
    wav, sr = sf.read(str(path), dtype='float32', always_2d=False)
    if wav.ndim > 1:
        wav = wav.mean(axis=1)
    if sr != SR:
        # ASVspoof LA is distributed at 16 kHz; resample only if that changes.
        import torch
        import torchaudio
        wav = torchaudio.functional.resample(
            torch.from_numpy(wav), sr, SR).numpy()
    return np.ascontiguousarray(wav, dtype=np.float32)


def embed_partition(partition, items, flac_dir, fe, enc, device, force=False):
    """Embed a partition with caching. Returns (X, y, kept_ids)."""
    from audio_branch import embed_waveform

    os.makedirs(CACHE_DIR, exist_ok=True)
    tag = f'{partition}_{len(items)}'
    cache = CACHE_DIR / f'{tag}.npz'
    if cache.exists() and not force:
        d = np.load(cache, allow_pickle=True)
        print(f'  [{partition}] loaded {d["X"].shape[0]} cached embeddings '
              f'from {cache.name}')
        return d['X'], d['y'], list(d['ids'])

    X, y, ids, failed = [], [], [], 0
    t0 = time.time()
    for i, (utt_id, label) in enumerate(items, 1):
        path = flac_dir / f'{utt_id}.flac'
        if not path.exists():
            failed += 1
            continue
        try:
            wav = load_audio(path)
            X.append(embed_waveform(wav, fe, enc, device))
            y.append(label)
            ids.append(utt_id)
        except Exception as e:
            failed += 1
            if failed <= 3:
                print(f'    warning: {utt_id}: {e}')
        if i % 200 == 0 or i == len(items):
            rate = i / max(time.time() - t0, 1e-9)
            eta = (len(items) - i) / max(rate, 1e-9)
            print(f'  [{partition}] {i}/{len(items)} embedded '
                  f'({rate:.1f}/s, eta {eta/60:.1f} min)', flush=True)

    if failed:
        print(f'  [{partition}] WARNING: {failed} utterance(s) missing or unreadable')
    if not X:
        raise RuntimeError(f'[{partition}] no utterances embedded — check the flac directory')

    X = np.stack(X).astype(np.float32)
    y = np.asarray(y, dtype=np.int64)
    np.savez_compressed(cache, X=X, y=y, ids=np.array(ids, dtype=object))
    print(f'  [{partition}] embedded {X.shape[0]}, cached -> {cache.name}')
    return X, y, ids


def main():
    ap = argparse.ArgumentParser(description='Train the ASVspoof 2019 LA audio branch.')
    ap.add_argument('--root', type=str, required=True,
                    help='Directory containing LA/ (or the LA/ directory itself).')
    ap.add_argument('--check-layout', action='store_true',
                    help='Validate the dataset layout and exit without embedding.')
    ap.add_argument('--max-per-class', type=int, default=None,
                    help='Balanced subsample per class per partition (for a fast '
                         'first pass). Recorded in the metrics file.')
    ap.add_argument('--force-reembed', action='store_true')
    ap.add_argument('--device', type=str, default='cpu',
                    help='Device for wav2vec2 (cpu is safest; mps may be faster).')
    ap.add_argument('--seed', type=int, default=42)
    args = ap.parse_args()

    set_seed(args.seed)
    root = Path(os.path.expanduser(args.root)).resolve()

    # ── Layout validation (always runs, so failures are immediate and clear) ──
    print(f'Validating ASVspoof layout under {root} …')
    resolved, protocols = {}, {}
    for part in PARTITIONS:
        flac_dir, proto = resolve_paths(root, part)
        items = read_protocol(proto)
        n_spoof = sum(1 for _, l in items if l == 1)
        resolved[part] = (flac_dir, proto)
        protocols[part] = items
        print(f'  {part:5s}: {len(items):6d} utterances '
              f'({len(items)-n_spoof} bona fide / {n_spoof} spoof)  <- {proto.name}')

    if args.check_layout:
        print('\nLayout OK. Re-run without --check-layout to train.')
        return 0

    from audio_branch import load_encoder, AudioSpoofSVM
    print(f'\nLoading wav2vec2 encoder on {args.device} …')
    fe, enc, device = load_encoder(args.device)

    data = {}
    for part in ('train', 'dev', 'eval'):
        items = subsample(protocols[part], args.max_per_class, args.seed)
        if args.max_per_class:
            print(f'  [{part}] subsampled {len(protocols[part])} -> {len(items)}')
        flac_dir, _ = resolved[part]
        data[part] = embed_partition(part, items, flac_dir, fe, enc, device,
                                     force=args.force_reembed)

    Xtr, ytr, _ = data['train']
    Xdev, ydev, _ = data['dev']
    Xev, yev, _ = data['eval']

    # ── Fit on train, select C on dev, score eval exactly once ───────────────
    print('\nFitting SVM (selecting C on the dev partition) …')
    best = None
    for C in (0.1, 1.0, 10.0):
        model = AudioSpoofSVM(seed=args.seed)
        model.clf.set_params(svc__C=C)
        model.fit(Xtr, ytr)
        dev_eer, _ = compute_eer(ydev, model.spoof_score(Xdev))
        print(f'  C={C:<5} dev EER = {dev_eer*100:.2f}%')
        if best is None or dev_eer < best[0]:
            best = (dev_eer, C, model)
    dev_eer, best_C, model = best
    print(f'Selected C={best_C} (dev EER {dev_eer*100:.2f}%)')

    eval_scores = model.spoof_score(Xev)
    eval_eer, eval_thr = compute_eer(yev, eval_scores)
    eval_acc = float((model.clf.predict(Xev) == yev).mean())
    print(f'\n── Audio branch results (ASVspoof 2019 LA eval) ──')
    print(f'EER      : {eval_eer*100:.2f}%   <- primary metric')
    print(f'Accuracy : {eval_acc:.4f}       (secondary)')

    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)
    import joblib
    joblib.dump({'model': model, 'C': best_C, 'threshold': eval_thr}, MODEL_PATH)

    metrics = {
        'dataset': 'ASVspoof 2019 LA',
        'subsampled_per_class': args.max_per_class,
        'full_dataset': args.max_per_class is None,
        'n_train': int(len(ytr)), 'n_dev': int(len(ydev)), 'n_eval': int(len(yev)),
        'svm_C': best_C,
        'dev_eer': float(dev_eer),
        'eval_eer': float(eval_eer),
        'eval_accuracy': eval_acc,
        'eer_threshold': float(eval_thr),
        'encoder': 'facebook/wav2vec2-base (frozen)',
        'seed': args.seed,
    }
    with open(OUT_DIR / 'metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)

    print(f'\nModel  -> {MODEL_PATH}')
    print(f'Metrics-> {OUT_DIR / "metrics.json"}')
    if args.max_per_class:
        print(f'\nNOTE: trained on a balanced subsample of {args.max_per_class} per '
              'class per partition. This EER is NOT comparable to published '
              'full-set figures and must be reported as a subset result.')
    print('\nNext: wire eval_accuracy into fusion.py in place of '
          'AUDIO_ACCURACY_PLACEHOLDER (Section 4.5).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
