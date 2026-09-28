"""Audio baseline: MFCC + SVM versus the wav2vec2 + SVM incumbent, on identical protocol.

Answers "why wav2vec2?" with a measurement instead of a citation. Same data (ASVspoof 2019 LA), same partitions
(train fits, dev selects C from (0.1, 1, 10), eval scored once), same classifier class (AudioSpoofSVM: StandardScaler
+ RBF SVC + Platt scaling), same metrics (eval EER, accuracy). Only the front end differs.

Front end here: MFCC(20) + delta + delta-delta = 60 coefficients per frame, mean and std pooled over time -> 120-d.

Second criterion, generalisation: false-alarm rate on GENUINE speech from a corpus neither model has seen
(DeepfakeTIMIT's untouched original audio). The wav2vec2 pipeline scored this kind of audio at about 0.98 fake in
the hybrid evaluation (results/hybrid_eval), a channel-mismatch failure. Both models are scored on the same
clips, at two operating points: probability >= 0.5 (what fusion uses) and the model's own eval-EER threshold.

    /opt/anaconda3/bin/python scripts/eval_audio_baseline.py --root /Users/<you>/Downloads
    /opt/anaconda3/bin/python scripts/eval_audio_baseline.py --root ... --max-per-class 100 --out-name smoke   # quick check
"""
import argparse
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

os.environ.setdefault('USE_TF', '0')
os.environ.setdefault('USE_FLAX', '0')

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import PROJECT_ROOT, RESULTS_DIR, set_seed, compute_eer  # noqa: E402
from train_audio_svm import PARTITIONS, resolve_paths, read_protocol, load_audio, subsample, SR  # noqa: E402

_MFCC = None


def _init_worker():
    import torch
    torch.set_num_threads(1)


def mfcc_vector(wav):
    """1-D float32 waveform @16 kHz -> 120-d pooled MFCC descriptor."""
    global _MFCC
    import torch
    import torchaudio
    if _MFCC is None:
        _MFCC = torchaudio.transforms.MFCC(sample_rate=SR, n_mfcc=20,
                                           melkwargs=dict(n_fft=512, win_length=400, hop_length=160, n_mels=40))
    m = _MFCC(torch.from_numpy(wav).unsqueeze(0))
    d1 = torchaudio.functional.compute_deltas(m)
    d2 = torchaudio.functional.compute_deltas(d1)
    f = torch.cat([m, d1, d2], dim=1)[0]
    return torch.cat([f.mean(1), f.std(1, unbiased=False)]).numpy().astype(np.float32)


def _work(path):
    return mfcc_vector(load_audio(Path(path)))


def features_for(part, items, flac_dir, cache_dir, workers):
    cache = cache_dir / f'{part}_{len(items)}.npz'
    if cache.exists():
        z = np.load(cache)
        return z['X'], z['y']
    paths = [str(flac_dir / f'{u}.flac') for u, _ in items]
    y = np.array([l for _, l in items], dtype=np.int64)
    t0 = time.time()
    with Pool(workers, initializer=_init_worker) as pool:
        X = []
        for i, v in enumerate(pool.imap(_work, paths, chunksize=64), 1):
            X.append(v)
            if i % 5000 == 0:
                print(f'  [{part}] {i}/{len(paths)} ({time.time() - t0:.0f}s)', flush=True)
    X = np.stack(X)
    cache_dir.mkdir(parents=True, exist_ok=True)
    np.savez(cache, X=X, y=y)
    return X, y


def timit_clips(n, seed=42):
    root = PROJECT_ROOT / 'external_datasets' / 'DeepfakeTIMIT' / 'higher_quality'
    clips = sorted(root.glob('*/*-video-*.avi'))
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(clips), min(n, len(clips)), replace=False)
    return [clips[i] for i in sorted(idx)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True, help='Directory containing LA/ (ASVspoof 2019).')
    ap.add_argument('--max-per-class', type=int, default=None)
    ap.add_argument('--workers', type=int, default=4)
    ap.add_argument('--timit-n', type=int, default=100)
    ap.add_argument('--out-name', default='audio_baseline')
    ap.add_argument('--seed', type=int, default=42)
    args = ap.parse_args()
    set_seed(args.seed)

    out = RESULTS_DIR / args.out_name
    out.mkdir(parents=True, exist_ok=True)
    root = Path(os.path.expanduser(args.root)).resolve()

    from audio_branch import AudioSpoofSVM, extract_audio_16k, load_trained_svm, load_encoder, embed_waveform

    data = {}
    for part in ('train', 'dev', 'eval'):
        flac_dir, proto = resolve_paths(root, part)
        items = subsample(read_protocol(proto), args.max_per_class, args.seed)
        print(f'[{part}] {len(items)} utterances: extracting MFCC descriptors', flush=True)
        data[part] = features_for(part, items, flac_dir, out / 'mfcc_cache', args.workers)
    (Xtr, ytr), (Xdev, ydev), (Xev, yev) = data['train'], data['dev'], data['eval']

    print('Fitting MFCC + SVM (C selected on dev)', flush=True)
    best = None
    for C in (0.1, 1.0, 10.0):
        m = AudioSpoofSVM(seed=args.seed)
        m.clf.set_params(svc__C=C)
        t0 = time.time()
        m.fit(Xtr, ytr)
        dev_eer, _ = compute_eer(ydev, m.spoof_score(Xdev))
        print(f'  C={C:<5} dev EER = {dev_eer * 100:.2f}%  ({time.time() - t0:.0f}s)', flush=True)
        if best is None or dev_eer < best[0]:
            best = (dev_eer, C, m)
    dev_eer, best_C, mfcc_svm = best
    ev_scores = mfcc_svm.spoof_score(Xev)
    ev_eer, ev_thr = compute_eer(yev, ev_scores)
    ev_acc = float((mfcc_svm.clf.predict(Xev) == yev).mean())
    print(f'MFCC + SVM eval EER {ev_eer * 100:.2f}%  acc {ev_acc:.4f}  (C={best_C})', flush=True)

    # --- unseen-corpus false alarms on genuine speech (both models, same clips) ---------------------------
    clips = timit_clips(args.timit_n, args.seed)
    waves = [w for w in (extract_audio_16k(c) for c in clips) if w is not None]
    print(f'DeepfakeTIMIT genuine audio: {len(waves)}/{len(clips)} clips decoded', flush=True)
    Xm = np.stack([mfcc_vector(w) for w in waves])
    res = {'n_clips': len(waves),
           'mfcc_svm': {'fa_at_p0.5': float((mfcc_svm.spoof_probability(Xm) >= 0.5).mean()),
                        'fa_at_eer_threshold': float((mfcc_svm.spoof_score(Xm) >= ev_thr).mean()),
                        'median_p_spoof': float(np.median(mfcc_svm.spoof_probability(Xm)))}}

    w2v = load_trained_svm()
    w2v_metrics = json.load(open(RESULTS_DIR / 'audio_branch' / 'metrics.json'))
    if w2v is not None:
        fe, enc, dev = load_encoder('cpu')
        Xw = np.stack([embed_waveform(w, fe, enc, dev) for w in waves])
        import joblib
        thr = joblib.load(PROJECT_ROOT / 'models' / 'audio_spoof_svm.joblib')['threshold']
        res['wav2vec2_svm'] = {'fa_at_p0.5': float((w2v.spoof_probability(Xw) >= 0.5).mean()),
                               'fa_at_eer_threshold': float((w2v.spoof_score(Xw) >= thr).mean()),
                               'median_p_spoof': float(np.median(w2v.spoof_probability(Xw)))}

    metrics = {
        'protocol': 'ASVspoof 2019 LA: train fits, dev selects C in (0.1, 1, 10), eval scored once',
        'subsampled_per_class': args.max_per_class, 'full_dataset': args.max_per_class is None,
        'n_train': int(len(ytr)), 'n_dev': int(len(ydev)), 'n_eval': int(len(yev)),
        'mfcc_svm': {'features': 'MFCC20 + delta + delta-delta, mean and std pooled (120-d)', 'svm_C': best_C,
                     'dev_eer': float(dev_eer), 'eval_eer': float(ev_eer), 'eval_accuracy': ev_acc},
        'wav2vec2_svm': {k: w2v_metrics[k] for k in ('svm_C', 'dev_eer', 'eval_eer', 'eval_accuracy')},
        'unseen_corpus_genuine_speech': {'corpus': 'DeepfakeTIMIT original audio (higher_quality, random sample)',
                                        **res},
        'seed': args.seed,
    }
    json.dump(metrics, open(out / 'metrics.json', 'w'), indent=2)

    a, b = metrics['mfcc_svm'], metrics['wav2vec2_svm']
    u = metrics['unseen_corpus_genuine_speech']
    lines = ['# Audio front-end baseline: MFCC + SVM vs wav2vec2 + SVM\n',
             f'Identical protocol and classifier class; only the front end differs. Full dataset: '
             f'{metrics["full_dataset"]}. n_eval = {metrics["n_eval"]}.\n',
             '| Front end | Eval EER | Eval accuracy | Dev EER | C |', '|---|---|---|---|---|',
             f'| MFCC + delta + delta-delta (120-d) | {a["eval_eer"] * 100:.2f}% | {a["eval_accuracy"]:.4f} | {a["dev_eer"] * 100:.2f}% | {a["svm_C"]} |',
             f'| wav2vec2-base, frozen (768-d) | {b["eval_eer"] * 100:.2f}% | {b["eval_accuracy"]:.4f} | {b["dev_eer"] * 100:.2f}% | {b["svm_C"]} |',
             '', f'## False alarms on genuine, unseen-corpus speech (n = {u["n_clips"]} clips, lower is better)\n',
             '| Front end | False-alarm rate at P(spoof) >= 0.5 | at own eval-EER threshold | Median P(spoof) |', '|---|---|---|---|']
    for k, lab in (('mfcc_svm', 'MFCC + SVM'), ('wav2vec2_svm', 'wav2vec2 + SVM')):
        if k in u:
            lines.append(f'| {lab} | {u[k]["fa_at_p0.5"]:.3f} | {u[k]["fa_at_eer_threshold"]:.3f} | {u[k]["median_p_spoof"]:.3f} |')
    (out / 'metrics.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
