"""Is the audio branch's false alarm on unseen speech caused by the codec or by the corpus? Re-scores ASVspoof eval clips after AAC/MP3.

    python scripts/audio_channel_diagnostic.py --root ~/Downloads/LA --n-per-class 100"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import warnings

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import RESULTS_DIR, compute_eer, set_seed  # noqa: E402

OUT_DIR = RESULTS_DIR / 'audio_channel_diagnostic'
SR = 16000
# Bitrates chosen to bracket what a real upload carries: 128k is typical for consumer video, 64k is a poor phone upload.
CODECS = {'aac_128k': ('aac', '128k', '.m4a'), 'aac_64k': ('aac', '64k', '.m4a'),
          'mp3_128k': ('libmp3lame', '128k', '.mp3'), 'mp3_64k': ('libmp3lame', '64k', '.mp3')}


def read_protocol(root, partition='eval'):
    proto = os.path.join(root, 'ASVspoof2019_LA_cm_protocols', f'ASVspoof2019.LA.cm.{partition}.trl.txt')
    if not os.path.exists(proto):
        proto = os.path.join(root, 'ASVspoof2019_LA_cm_protocols', f'ASVspoof2019.LA.cm.{partition}.trn.txt')
    items = []
    with open(proto) as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 5:
                items.append((parts[1], 1 if parts[4] == 'spoof' else 0))
    return items


def transcode(src_flac, ffmpeg, codec, bitrate, suffix):
    """FLAC -> lossy codec -> back to 16 kHz mono float32, i.e. exactly what a clip inside a video file has been through."""
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as t:
        lossy = t.name
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as t:
        back = t.name
    try:
        for cmd in ([ffmpeg, '-y', '-i', src_flac, '-c:a', codec, '-b:a', bitrate, '-ar', str(SR), '-ac', '1', lossy],
                    [ffmpeg, '-y', '-i', lossy, '-f', 'wav', '-acodec', 'pcm_s16le', '-ar', str(SR), '-ac', '1', back]):
            if subprocess.run(cmd, capture_output=True, timeout=60).returncode != 0:
                return None
        import soundfile as sf
        wav, _ = sf.read(back, dtype='float32')
        return wav
    except Exception:
        return None
    finally:
        for p in (lossy, back):
            try:
                os.unlink(p)
            except OSError:
                pass


def metrics(y, scores, probs):
    eer, _ = compute_eer(y, scores)
    pred = (np.asarray(probs) >= 0.5).astype(int)
    y = np.asarray(y)
    bona = y == 0
    return {'eer': float(eer),
            'accuracy_at_0.5': float((pred == y).mean()),
            'bona_fide_false_alarm_rate': float(pred[bona].mean()),          # genuine speech called spoof: the failure in A3
            'spoof_detection_rate': float(pred[~bona].mean()),
            'mean_p_spoof_on_bona_fide': float(np.mean(np.asarray(probs)[bona]))}


def main():
    warnings.filterwarnings('ignore')
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--root', required=True, help='directory containing ASVspoof2019_LA_eval/')
    ap.add_argument('--n-per-class', type=int, default=100)
    ap.add_argument('--seed', type=int, default=42)
    args = ap.parse_args()
    set_seed(args.seed)

    root = os.path.expanduser(args.root)
    flac_dir = os.path.join(root, 'ASVspoof2019_LA_eval', 'flac')
    if not os.path.isdir(flac_dir):
        sys.exit(f'not found: {flac_dir}')

    items = read_protocol(root)
    rng = np.random.default_rng(args.seed)
    bona = [i for i in items if i[1] == 0]
    spoof = [i for i in items if i[1] == 1]
    pick = ([bona[i] for i in rng.choice(len(bona), args.n_per_class, replace=False)] +
            [spoof[i] for i in rng.choice(len(spoof), args.n_per_class, replace=False)])
    print(f'{len(pick)} clips: {args.n_per_class} bona fide + {args.n_per_class} spoof, seed {args.seed}')

    from audio_branch import load_encoder, load_trained_svm
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    svm = load_trained_svm()
    if svm is None:
        sys.exit('no trained SVM')
    fe, enc, dev = load_encoder('cpu')
    import soundfile as sf

    def embed(wav):
        from audio_branch import embed_waveform
        return embed_waveform(wav, fe, enc, dev)

    conditions = ['clean'] + list(CODECS)
    X = {c: [] for c in conditions}
    y = []
    for n, (utt, label) in enumerate(pick, 1):
        src = os.path.join(flac_dir, utt + '.flac')
        if not os.path.exists(src):
            continue
        wav, _ = sf.read(src, dtype='float32')
        row = {'clean': embed(wav)}
        ok = True
        for name, (codec, br, suf) in CODECS.items():
            w = transcode(src, ffmpeg, codec, br, suf)
            if w is None or w.size == 0:
                ok = False
                break
            row[name] = embed(w)
        if not ok:
            continue
        for c in conditions:
            X[c].append(row[c])
        y.append(label)
        if n % 25 == 0:
            print(f'  {n}/{len(pick)}', flush=True)

    y = np.array(y)
    print(f'\nscored {len(y)} clips ({int((y == 0).sum())} bona fide, {int((y == 1).sum())} spoof)\n')
    out = {'n_clips': int(len(y)), 'n_bona_fide': int((y == 0).sum()), 'seed': args.seed,
           'source': 'ASVspoof 2019 LA eval, re-encoded through lossy codecs; same clips, same labels, same corpus',
           'conditions': {}}
    for c in conditions:
        M = np.vstack(X[c])
        out['conditions'][c] = metrics(y, svm.spoof_score(M), svm.spoof_probability(M))

    print(f'{"condition":12s} {"EER":>8s} {"acc@0.5":>9s} {"bona fide false alarm":>22s} {"mean P(spoof)|bona":>20s}')
    for c in conditions:
        m = out['conditions'][c]
        print(f'{c:12s} {m["eer"] * 100:7.2f}% {m["accuracy_at_0.5"] * 100:8.2f}% '
              f'{m["bona_fide_false_alarm_rate"] * 100:21.1f}% {m["mean_p_spoof_on_bona_fide"]:20.4f}')

    base = out['conditions']['clean']['bona_fide_false_alarm_rate']
    worst = max(out['conditions'][c]['bona_fide_false_alarm_rate'] for c in CODECS)
    out['verdict'] = {
        'clean_bona_fide_false_alarm': base, 'worst_codec_bona_fide_false_alarm': worst,
        'increase_pp': (worst - base) * 100,
        'interpretation': ('Lossy coding alone materially increases false alarms on genuine speech, so channel mismatch is at '
                           'least part of the DeepfakeTIMIT failure and codec augmentation is worth trying.'
                           if (worst - base) > 0.10 else
                           'Lossy coding alone does NOT materially change the branch, so the DeepfakeTIMIT failure is corpus '
                           'mismatch (speakers, microphones, recording conditions), not the codec. Codec augmentation would not '
                           'fix it; more diverse bona fide training data would.')}
    print(f'\nBona fide false alarms: clean {base * 100:.1f}% -> worst codec {worst * 100:.1f}% '
          f'({(worst - base) * 100:+.1f} pp)')
    print(out['verdict']['interpretation'])
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_DIR / 'diagnostic.json', 'w') as f:
        json.dump(out, f, indent=2)
    print(f'\nWrote {OUT_DIR / "diagnostic.json"}')


if __name__ == '__main__':
    main()
