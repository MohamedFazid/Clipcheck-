"""Controlled comparison of self-supervised audio encoders behind the SVM back end (wav2vec2 vs WavLM).

WHY. The PPR justifies wav2vec2 from the literature (Tak et al., 2022; Li, Ahmadiadli and Zhang, 2025) and the project measured
it against a hand-crafted MFCC baseline (docs/EXPERIMENTS.md A2), but it never compared it with another SSL encoder. The module
brief asks for evidence that several pretrained models were tried and chosen between, so this closes that gap for the audio branch.

WHAT MAKES IT FAIR. Everything except the encoder is held constant:
  * the same balanced subsample of ASVspoof 2019 LA (same clips, same labels, same seed) for every encoder;
  * the same decoder (the project's own bundled ffmpeg path, scripts/audio_branch.extract_audio_16k);
  * the same back end (scripts/audio_branch.AudioSpoofSVM: StandardScaler + RBF SVC), the same C grid, C selected on dev,
    eval scored once;
  * the same environment and process, so no library-version difference can creep in.

Both encoders are embedded FRESH here. The cached full-dataset wav2vec2 embeddings are deliberately NOT reused: they were made in
a different environment, and reusing them would confound the encoder with the environment. Consequence to respect when reading the
output: these are SUBSAMPLE numbers and are NOT comparable with the full-dataset figures in results/audio_branch/metrics.json
(eval EER 3.96%), which are measured on 71,237 clips. Compare the encoders with each other here, nothing else.

Both models are base-sized and pretrained on the same 960 hours of LibriSpeech, so this is a like-for-like comparison. Larger and
better-pretrained variants exist (wavlm-base-plus, wavlm-large) and are not tested here.

Run (app env, which is the one whose transformers can import WavLM):
    /opt/anaconda3/envs/deepfake-detect/bin/python scripts/compare_audio_encoders.py --root ~/Downloads/LA --per-class 500
"""
import argparse
import json
import os
import sys
import time
import warnings

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import RESULTS_DIR, compute_eer, set_seed  # noqa: E402

OUT_DIR = RESULTS_DIR / 'audio_encoder_comparison'
ENCODERS = {
    'wav2vec2-base': 'facebook/wav2vec2-base',      # what the project ships
    'wavlm-base': 'microsoft/wavlm-base',           # the untested alternative, same pretraining data and size
}
C_GRID = (0.1, 1.0, 10.0)
PARTITION_DIRS = {'train': ('ASVspoof2019_LA_train', 'ASVspoof2019.LA.cm.train.trn.txt'),
                  'dev': ('ASVspoof2019_LA_dev', 'ASVspoof2019.LA.cm.dev.trl.txt'),
                  'eval': ('ASVspoof2019_LA_eval', 'ASVspoof2019.LA.cm.eval.trl.txt')}


def read_protocol(path):
    items = []
    with open(path) as f:
        for line in f:
            p = line.split()
            if len(p) >= 5:
                items.append((p[1], 1 if p[4] == 'spoof' else 0))
    return items


def balanced_subsample(items, per_class, seed):
    """Same rule as train_audio_svm.subsample: equal numbers of each class, deterministic for a seed."""
    rng = np.random.default_rng(seed)
    out = []
    for label in (0, 1):
        pool = [i for i in items if i[1] == label]
        if len(pool) > per_class:
            pool = [pool[i] for i in sorted(rng.choice(len(pool), per_class, replace=False))]
        out += pool
    return out


def load_encoder(model_id, device='cpu'):
    from transformers import AutoFeatureExtractor
    if 'wavlm' in model_id:
        from transformers.models.wavlm import WavLMModel as Model
    else:
        from transformers import Wav2Vec2Model as Model
    fe = AutoFeatureExtractor.from_pretrained(model_id)
    enc = Model.from_pretrained(model_id).to(device).eval()
    return fe, enc


def embed_all(waveforms, fe, enc, device='cpu'):
    """Mean-pooled last hidden state, exactly as scripts/audio_branch.embed_waveform does it for the shipped branch."""
    import torch
    out = []
    with torch.no_grad():
        for w in waveforms:
            inp = fe(w, sampling_rate=16000, return_tensors='pt')
            h = enc(inp.input_values.to(device)).last_hidden_state
            out.append(h.mean(dim=1).squeeze(0).cpu().numpy())
    return np.vstack(out)


def fit_and_score(Xtr, ytr, Xdev, ydev, Xev, yev, seed):
    """Identical back end and selection protocol for every encoder: C chosen on dev EER, eval scored once."""
    from audio_branch import AudioSpoofSVM
    best = None
    dev_by_c = {}
    for C in C_GRID:
        m = AudioSpoofSVM(seed=seed)
        m.clf.set_params(svc__C=C)
        m.fit(Xtr, ytr)
        eer, _ = compute_eer(ydev, m.spoof_score(Xdev))
        dev_by_c[C] = float(eer)
        if best is None or eer < best[0]:
            best = (eer, C, m)
    dev_eer, C, model = best
    scores, probs = model.spoof_score(Xev), model.spoof_probability(Xev)
    eer, _ = compute_eer(yev, scores)
    pred = (probs >= 0.5).astype(int)
    yev = np.asarray(yev)
    bona = yev == 0
    from sklearn.metrics import balanced_accuracy_score, f1_score, roc_auc_score
    return model, {
        'selected_C': C, 'dev_eer_by_C': dev_by_c, 'dev_eer': float(dev_eer),
        'eval_eer': float(eer), 'eval_auc_roc': float(roc_auc_score(yev, scores)),
        'eval_accuracy_at_0.5': float((pred == yev).mean()),
        'eval_balanced_accuracy': float(balanced_accuracy_score(yev, pred)),
        'eval_f1_spoof': float(f1_score(yev, pred)),
        'bona_fide_false_alarm_rate': float(pred[bona].mean()),
        'spoof_detection_rate': float(pred[~bona].mean()),
    }


def unseen_corpus_false_alarms(model, fe, enc, device, n, seed):
    """The branch's known failure (docs/EXPERIMENTS.md A3): genuine speech from another corpus scored as spoof.
    Returns None if DeepfakeTIMIT is not present. Uses the ORIGINAL audio of DeepfakeTIMIT clips, which is real speech."""
    from audio_branch import extract_audio_16k
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'external_datasets', 'DeepfakeTIMIT', 'higher_quality')
    if not os.path.isdir(root):
        return None
    clips = []
    for d, _, fs in os.walk(root):
        clips += [os.path.join(d, f) for f in fs if f.endswith('.avi')]
    if not clips:
        return None
    clips = sorted(clips)
    rng = np.random.default_rng(seed)
    clips = [clips[i] for i in rng.choice(len(clips), min(n, len(clips)), replace=False)]
    waves = [w for w in (extract_audio_16k(c) for c in clips) if w is not None and w.size > 0]
    if not waves:
        return None
    probs = model.spoof_probability(embed_all(waves, fe, enc, device))
    return {'corpus': 'DeepfakeTIMIT original audio (genuine speech)', 'n_clips': len(waves),
            'false_alarm_rate_at_0.5': float((probs >= 0.5).mean()),
            'median_p_spoof': float(np.median(probs))}


def main():
    warnings.filterwarnings('ignore')
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--root', required=True, help='ASVspoof 2019 LA root')
    ap.add_argument('--per-class', type=int, default=500, help='clips per class for train and eval')
    ap.add_argument('--dev-per-class', type=int, default=250)
    ap.add_argument('--unseen-clips', type=int, default=60, help='DeepfakeTIMIT genuine clips for the false-alarm check')
    ap.add_argument('--seed', type=int, default=42)
    args = ap.parse_args()
    set_seed(args.seed)
    root = os.path.expanduser(args.root)
    from audio_branch import extract_audio_16k

    # One subsample, decoded once, shared by every encoder: the clips are identical across the comparison.
    data = {}
    for part, (sub, proto) in PARTITION_DIRS.items():
        items = read_protocol(os.path.join(root, 'ASVspoof2019_LA_cm_protocols', proto))
        per = args.dev_per_class if part == 'dev' else args.per_class
        picked = balanced_subsample(items, per, args.seed)
        flac = os.path.join(root, sub, 'flac')
        waves, labels, ids = [], [], []
        t0 = time.time()
        for utt, lab in picked:
            w = extract_audio_16k(os.path.join(flac, utt + '.flac'))
            if w is not None and w.size > 0:
                waves.append(w)
                labels.append(lab)
                ids.append(utt)
        data[part] = (waves, np.array(labels), ids)
        print(f'{part:5s}: decoded {len(waves)} clips '
              f'({int((np.array(labels) == 0).sum())} bona fide / {int((np.array(labels) == 1).sum())} spoof) '
              f'in {time.time() - t0:.0f}s', flush=True)

    out = {'protocol': ('Identical balanced subsample of ASVspoof 2019 LA for every encoder; same decoder, same SVM back end '
                        '(StandardScaler + RBF SVC), C selected on dev EER, eval scored once. Subsample figures: NOT comparable '
                        'with the full-dataset numbers in results/audio_branch/metrics.json.'),
           'seed': args.seed, 'per_class_train_eval': args.per_class, 'dev_per_class': args.dev_per_class,
           'n_train': int(len(data['train'][1])), 'n_dev': int(len(data['dev'][1])), 'n_eval': int(len(data['eval'][1])),
           'encoders': {}}

    for name, model_id in ENCODERS.items():
        print(f'\n=== {name} ({model_id})', flush=True)
        t0 = time.time()
        fe, enc = load_encoder(model_id)
        X = {}
        for part in ('train', 'dev', 'eval'):
            X[part] = embed_all(data[part][0], fe, enc)
            print(f'   embedded {part}: {X[part].shape} ({time.time() - t0:.0f}s elapsed)', flush=True)
        model, m = fit_and_score(X['train'], data['train'][1], X['dev'], data['dev'][1],
                                 X['eval'], data['eval'][1], args.seed)
        m['model_id'] = model_id
        m['embedding_dim'] = int(X['eval'].shape[1])
        m['embed_seconds_per_clip'] = float((time.time() - t0) / max(1, sum(len(data[p][0]) for p in data)))
        unseen = unseen_corpus_false_alarms(model, fe, enc, 'cpu', args.unseen_clips, args.seed)
        if unseen:
            m['unseen_corpus_genuine_speech'] = unseen
        out['encoders'][name] = m
        print(f'   dev EER {m["dev_eer"] * 100:.2f}% (C={m["selected_C"]})  ->  eval EER {m["eval_eer"] * 100:.2f}%, '
              f'balanced acc {m["eval_balanced_accuracy"] * 100:.2f}%', flush=True)

    print('\n' + '=' * 96)
    print(f'{"encoder":16s} {"eval EER":>9s} {"AUC":>7s} {"bal acc":>9s} {"F1 spoof":>9s} {"bona fide FA":>13s} {"unseen-corpus FA":>18s}')
    for name, m in out['encoders'].items():
        u = m.get('unseen_corpus_genuine_speech')
        print(f'{name:16s} {m["eval_eer"] * 100:8.2f}% {m["eval_auc_roc"]:7.4f} {m["eval_balanced_accuracy"] * 100:8.2f}% '
              f'{m["eval_f1_spoof"]:9.4f} {m["bona_fide_false_alarm_rate"] * 100:12.1f}% '
              f'{"n/a" if not u else f"{u['false_alarm_rate_at_0.5'] * 100:.0f}% of {u['n_clips']}":>18s}')

    names = list(out['encoders'])
    if len(names) == 2:
        a, b = (out['encoders'][n]['eval_eer'] for n in names)
        diff_pp = (b - a) * 100
        n_eval = out['n_eval']
        out['verdict'] = {
            'shipped': names[0], 'alternative': names[1], 'eer_difference_pp': diff_pp,
            'interpretation': (
                f'{names[1]} is {abs(diff_pp):.2f} pp {"better" if diff_pp < 0 else "worse"} than the shipped {names[0]} on '
                f'{n_eval} held-out clips. One misclassified clip is about {100 / n_eval:.2f} pp, so a difference below roughly '
                f'{200 / n_eval:.2f} pp is within the noise of this subsample and should not be called a win either way.')}
        print('\n' + out['verdict']['interpretation'])

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_DIR / 'comparison.json', 'w') as f:
        json.dump(out, f, indent=2)
    print(f'\nWrote {OUT_DIR / "comparison.json"}')


if __name__ == '__main__':
    main()
