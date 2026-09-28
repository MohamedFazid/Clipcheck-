"""Experiment only (not shipped): does adding LAV-DF speech to the SVM's training data fix its LAV-DF failure? (ledger F6/F7)

    python scripts/audio_lavdf_experiment.py --parts external_datasets/LAV-DF_parts/LAV-DF.zip.006"""
import argparse
import json
import random
import sys
import tempfile
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve

sys.path.insert(0, str(Path(__file__).resolve().parent))
import carve_lavdf_parts as carve  # noqa: E402
from audio_branch import AudioSpoofSVM, embed_waveform, extract_audio_16k, load_encoder  # noqa: E402

ROOT = carve.PROJECT_ROOT
OUT = ROOT / 'results' / 'audio_lavdf_experiment'
EMB = ROOT / 'results' / 'audio_branch' / 'embeddings'
METADATA = ROOT / 'external_datasets' / 'LAV-DF' / 'metadata.json'


def eer(y, s):
    fpr, tpr, _ = roc_curve(y, s)
    i = np.nanargmin(np.abs(fpr - (1 - tpr)))
    return float((fpr[i] + 1 - tpr[i]) / 2)


def embed_files(paths, fe, enc):
    out = []
    for i, p in enumerate(paths):
        wav = extract_audio_16k(str(p))
        out.append(embed_waveform(wav, fe, enc, 'cpu') if wav is not None and wav.size else np.full(768, np.nan, dtype=np.float32))
        if (i + 1) % 100 == 0:
            print(f'  embedded {i + 1}/{len(paths)}', flush=True)
    return np.array(out, dtype=np.float32)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--parts', nargs='+', required=True)
    ap.add_argument('--n-per-label', type=int, default=400)
    ap.add_argument('--seed', type=int, default=42)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / 'results.json').exists():
        sys.exit(f'{OUT / "results.json"} exists; refusing to overwrite')
    meta = {r['file']: r for r in json.load(open(METADATA))}
    C = float(json.load(open(ROOT / 'results' / 'audio_branch' / 'metrics.json'))['svm_C'])
    fe, enc, _ = load_encoder('cpu')

    # ---- LAV-DF dev training clips (fixed, seeded, before any scoring) ----
    train_files = OUT / 'emb_lavdf_dev.npz'
    if train_files.exists():
        d = np.load(train_files, allow_pickle=True)
        Xl, yl, names = d['X'], d['y'], list(d['names'])
    else:
        dev = {}
        for part in sorted(args.parts):
            buf = Path(part).read_bytes()
            for name, method, crc, csize, usize, start in carve.iter_members(buf):
                rel = name.split('/', 1)[1]
                if rel.endswith('.mp4') and meta.get(rel, {}).get('split') == 'dev':
                    dev[rel] = (method, crc, csize, usize, bytes(buf[start:start + csize]))
            del buf
        names, y = [], []
        for label, flag in ((0, False), (1, True)):
            pool = sorted(f for f in dev if meta[f]['modify_audio'] == flag)
            names += random.Random(f'{args.seed}-{label}').sample(pool, args.n_per_label)
            y += [label] * args.n_per_label
        with tempfile.TemporaryDirectory() as tmp:
            paths = []
            for rel in names:
                method, crc, csize, usize, raw = dev[rel]
                data = carve.zlib.decompressobj(-15).decompress(raw) if method == 8 else raw
                assert len(data) == usize and (carve.zlib.crc32(data) & 0xFFFFFFFF) == crc
                p = Path(tmp) / rel.replace('/', '_')
                p.write_bytes(data)
                paths.append(p)
            print(f'embedding {len(paths)} LAV-DF dev clips', flush=True)
            Xl = embed_files(paths, fe, enc)
        yl = np.array(y)
        np.savez(train_files, X=Xl, y=yl, names=np.array(names))
    ok = ~np.isnan(Xl).any(axis=1)
    Xl, yl = Xl[ok], yl[ok]

    # ---- LAV-DF test clips (eval_lavdf, scored only) ----
    test_file = OUT / 'emb_lavdf_test.npz'
    man = json.load(open(ROOT / 'eval_lavdf' / 'manifest.json'))['clips']
    if test_file.exists():
        Xt = np.load(test_file)['X']
    else:
        print(f'embedding {len(man)} LAV-DF test clips', flush=True)
        Xt = embed_files([ROOT / c['output_path'] for c in man], fe, enc)
        np.savez(test_file, X=Xt)
    yt = np.array([1 if c['audio_label'] == 'spoof' else 0 for c in man])
    good = ~np.isnan(Xt).any(axis=1)

    a = np.load(EMB / 'train_25380.npz', allow_pickle=True)
    ev = np.load(EMB / 'eval_71237.npz', allow_pickle=True)
    variants = {
        'S0': (a['X'], a['y']),
        'B2': (np.vstack([a['X'], Xl[yl == 0]]), np.concatenate([a['y'], yl[yl == 0]])),
        'B1': (np.vstack([a['X'], Xl]), np.concatenate([a['y'], yl])),
    }
    results = {'C': C, 'n_lavdf_dev_bonafide': int((yl == 0).sum()), 'n_lavdf_dev_spoof': int((yl == 1).sum()),
               'n_lavdf_test': int(good.sum()), 'variants': {}}
    for name, (X, y) in variants.items():
        m = AudioSpoofSVM(seed=args.seed)
        m.clf.set_params(svc__C=C)
        m.fit(X, y)
        pt = m.spoof_probability(Xt[good])
        y_t = yt[good]
        pe = m.spoof_probability(ev['X'])
        ye = ev['y']
        genuine, faked = pt[y_t == 0], pt[y_t == 1]
        results['variants'][name] = {
            'n_train': int(len(y)), 'n_train_bonafide': int((y == 0).sum()), 'n_train_spoof': int((y == 1).sum()),
            'lavdf_test': {'genuine_clips': int((y_t == 0).sum()), 'genuine_flagged_fake': float((genuine >= 0.5).mean()),
                           'faked_clips': int((y_t == 1).sum()), 'faked_flagged_fake': float((faked >= 0.5).mean()),
                           'balanced_accuracy': float(((genuine < 0.5).mean() + (faked >= 0.5).mean()) / 2),
                           'auc': float(roc_auc_score(y_t, pt)), 'eer': eer(y_t, pt),
                           'mean_p_genuine': float(genuine.mean()), 'mean_p_faked': float(faked.mean())},
            'asvspoof_eval': {'eer': eer(ye, pe), 'accuracy': float(((pe >= 0.5) == ye).mean()),
                              'balanced_accuracy': float(((pe[ye == 0] < 0.5).mean() + (pe[ye == 1] >= 0.5).mean()) / 2)},
        }
        import joblib
        joblib.dump({'model': m, 'C': C}, OUT / f'svm_{name}.joblib')
        print(name, json.dumps(results['variants'][name]), flush=True)
    s0, b2 = results['variants']['S0'], results['variants']['B2']
    results['decision'] = {
        'rule': 'B2 cuts genuine false alarms on LAV-DF test to <50% and ASVspoof EER stays within 1.0 pp of S0',
        'b2_genuine_false_alarm': b2['lavdf_test']['genuine_flagged_fake'],
        'asvspoof_eer_change_pp': (b2['asvspoof_eval']['eer'] - s0['asvspoof_eval']['eer']) * 100,
        'met': bool(b2['lavdf_test']['genuine_flagged_fake'] < 0.5
                    and abs(b2['asvspoof_eval']['eer'] - s0['asvspoof_eval']['eer']) <= 0.01)}
    json.dump(results, open(OUT / 'results.json', 'w'), indent=1)
    print(json.dumps(results['decision'], indent=1))


if __name__ == '__main__':
    main()
