"""Run the APP's own branch code over evaluation clips and cache what the out-of-domain gate needs (docs/EXPERIMENTS.md O1).

Per clip: P(video_fake) and the pooled Xception features of every face crop (video_infer.analyse_video_file, the app's path, with
return_features=True); the speech-gate decision, the wav2vec2 embedding and P(audio_fake) (the server's own order: decode, VAD, embed, SVM).
Nothing is fitted here. Output: results/ood_gate/features/<set>.joblib, one list of dicts per set.

Sets (sampling fixed before any gate existed; seeds in the code):
    heldout   eval_heldout/ (80; FF++ test-split video + ASVspoof eval audio: in-domain for BOTH branches)
    fallback  eval_fallback/ (80; FF++ video + different ASVspoof eval utterances: in-domain for both)
    lavdf     eval_lavdf/ (200; LAV-DF TEST split; the set the gate must handle)
    lavdf_dev 200 LAV-DF DEV clips, 50 per category, carved from part .006 (TUNING set: chooses the gate variant)
    timit     the 20 DeepfakeTIMIT clips of eval_hybrid/ (unseen video generator AND unseen genuine speech)
    celebdf   100 Celeb-DF-v2 test videos, 50 real + 50 fake (unseen dataset for the video branch)
    veo       the AI-generated clips in demo_videos/ai_generated_2026/ (informative only)

    /opt/anaconda3/envs/deepfake-detect/bin/python scripts/extract_app_features.py --sets heldout fallback lavdf lavdf_dev timit celebdf veo
"""
import argparse
import json
import random
import sys
import tempfile
import time
from pathlib import Path

import joblib
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import carve_lavdf_parts as carve  # noqa: E402
from audio_branch import embed_waveform, extract_audio_16k, load_encoder, load_trained_svm  # noqa: E402
from vad import analyse as vad_analyse  # noqa: E402
import video_infer as vi  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'results' / 'ood_gate' / 'features'
CELEBDF = Path.home() / 'Downloads' / 'Celeb-DF-v2'
LAVDF_PART = ROOT / 'external_datasets' / 'LAV-DF_parts' / 'LAV-DF.zip.006'
CATS = {'RVRA': (False, False), 'RVFA': (False, True), 'FVRA': (True, False), 'FVFA': (True, True)}


def manifest_clips(name, categories=None):
    m = json.load(open(ROOT / name / 'manifest.json'))['clips']
    return [{'id': c['id'], 'path': ROOT / c['output_path'], 'video_label': c['video_label'], 'audio_label': c['audio_label']}
            for c in m if categories is None or c['category'] in categories]


def lavdf_dev_clips(tmp):
    meta = {r['file']: r for r in json.load(open(ROOT / 'external_datasets' / 'LAV-DF' / 'metadata.json'))}
    buf = LAVDF_PART.read_bytes()
    dev = {}
    for name, method, crc, csize, usize, start in carve.iter_members(buf):
        rel = name.split('/', 1)[1]
        if rel.endswith('.mp4') and meta.get(rel, {}).get('split') == 'dev':
            dev[rel] = (method, crc, usize, bytes(buf[start:start + csize]))
    del buf
    out = []
    for cat, (mv, ma) in CATS.items():
        pool = sorted(f for f in dev if meta[f]['modify_video'] == mv and meta[f]['modify_audio'] == ma)
        for i, rel in enumerate(random.Random(f'ood-dev-{cat}').sample(pool, 50)):
            method, crc, usize, raw = dev[rel]
            data = carve.zlib.decompressobj(-15).decompress(raw) if method == 8 else raw
            assert len(data) == usize and (carve.zlib.crc32(data) & 0xFFFFFFFF) == crc
            p = Path(tmp) / rel.replace('/', '_')
            p.write_bytes(data)
            out.append({'id': f'dev_{cat}_{i:03d}', 'path': p, 'lavdf_file': rel,
                        'video_label': 'fake' if mv else 'real', 'audio_label': 'spoof' if ma else 'bonafide'})
    return out


def celebdf_clips():
    rows = [ln.split(maxsplit=1) for ln in (l.strip() for l in open(CELEBDF / 'List_of_testing_videos.txt')) if ln]
    real = sorted(r[1] for r in rows if r[0] == '1')
    fake = sorted(r[1] for r in rows if r[0] == '0')
    rng = random.Random('ood-celebdf')
    return ([{'id': f'real_{Path(p).stem}', 'path': CELEBDF / p, 'video_label': 'real', 'audio_label': None} for p in rng.sample(real, 50)]
            + [{'id': f'fake_{Path(p).stem}', 'path': CELEBDF / p, 'video_label': 'fake', 'audio_label': None} for p in rng.sample(fake, 50)])


def veo_clips():
    return [{'id': p.stem, 'path': p, 'video_label': 'fake', 'audio_label': None}
            for p in sorted((ROOT / 'demo_videos' / 'ai_generated_2026').glob('*.webm'))]


def run_clip(c, models):
    mtcnn, model, device, fe, enc, svm = models
    r = dict(c, path=str(c['path']))
    v = vi.analyse_video_file(str(c['path']), mtcnn, model, device, max_faces=20, return_features=True)
    r['p_video'] = None if v is None else v['p_fake']
    r['video_features'] = None if v is None else v['features'].astype(np.float16)
    wav = extract_audio_16k(str(c['path']))
    r['speech'], r['p_audio'], r['audio_embedding'] = False, None, None
    if wav is not None and wav.size:
        vres = vad_analyse(wav)
        r['speech'] = bool(vres.has_speech)
        if vres.has_speech:
            emb = embed_waveform(wav, fe, enc, 'cpu')
            r['audio_embedding'] = emb.astype(np.float32)
            r['p_audio'] = float(svm.spoof_probability(emb.reshape(1, -1))[0])
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--sets', nargs='+', required=True)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    mtcnn, model, device = vi.load_models()
    fe, enc, _ = load_encoder('cpu')
    models = (mtcnn, model, device, fe, enc, load_trained_svm())
    with tempfile.TemporaryDirectory() as tmp:
        sources = {'heldout': lambda: manifest_clips('eval_heldout'), 'fallback': lambda: manifest_clips('eval_fallback'),
                   'lavdf': lambda: manifest_clips('eval_lavdf'), 'lavdf_dev': lambda: lavdf_dev_clips(tmp),
                   'timit': lambda: manifest_clips('eval_hybrid', {'FVRA'}), 'celebdf': celebdf_clips, 'veo': veo_clips}
        for s in args.sets:
            dest = OUT / f'{s}.joblib'
            if dest.exists():
                print(f'{s}: cached at {dest}, skipped', flush=True)
                continue
            clips, rows, t0 = sources[s](), [], time.time()
            for i, c in enumerate(clips):
                rows.append(run_clip(c, models))
                if (i + 1) % 20 == 0 or i + 1 == len(clips):
                    print(f'{s}: {i + 1}/{len(clips)} ({time.time() - t0:.0f} s)', flush=True)
            joblib.dump(rows, dest)
            print(f'{s}: {len(rows)} clips, {sum(r["p_video"] is None for r in rows)} without a face, '
                  f'{sum(r["p_audio"] is None for r in rows)} without an audio score -> {dest}', flush=True)


if __name__ == '__main__':
    main()
