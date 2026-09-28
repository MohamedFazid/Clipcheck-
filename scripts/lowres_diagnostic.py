"""Why does the video branch fail on LAV-DF? Re-score held-out FF++ videos after making them LAV-DF-like.

Docs/EXPERIMENTS.md F6: the shipped video model scores 92.5% on held-out FF++ (F5) but has AUC 0.377 on LAV-DF. LAV-DF frames are 224x224
close-ups: the face fills most of the frame and the clip is a ~100 kbps H.264 re-encode. This script takes the SAME videos F5 used (unique FF++
videos in eval_heldout/manifest.json, all test-split identities) and re-scores them through the app's own path (video_infer.analyse_video_file):

    original  : the FF++ video unchanged (must reproduce F5's video-branch behaviour)
    closeup   : per-video fixed square crop around the MTCNN face box (side = SIDE x the larger box dimension), scaled to 224x224, H.264 at 100 kbps,
                audio dropped. A crop, resize and bitrate change only; the manipulation content is untouched.

If closeup scores collapse relative to original, resolution, framing and compression alone break the model, independent of the manipulation
method (Wav2Lip) or the speakers (VoxCeleb2). If they hold, those are the suspects instead. Decided before running: the diagnostic is read as
"resolution explains it" when closeup AUC falls by more than 0.15 from original AUC.

    /opt/anaconda3/envs/deepfake-detect/bin/python scripts/lowres_diagnostic.py
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))
import video_infer as vi  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def face_box(video_path, mtcnn, n_frames=8):
    """Mean (cx, cy, size) of the MTCNN box over n_frames evenly spaced frames; None if no face."""
    cap = cv2.VideoCapture(str(video_path))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    boxes = []
    for idx in np.linspace(0, max(total - 1, 0), n_frames).astype(int):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ok, frame = cap.read()
        if not ok:
            continue
        b, _ = mtcnn.detect(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
        if b is not None and len(b):
            x0, y0, x1, y1 = max(b, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
            boxes.append(((x0 + x1) / 2, (y0 + y1) / 2, max(x1 - x0, y1 - y0)))
    h, w = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)), int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    cap.release()
    return (np.mean(boxes, axis=0), w, h) if boxes else (None, w, h)


def make_closeup(src, dst, ffmpeg, mtcnn, side_factor, bitrate):
    box, w, h = face_box(src, mtcnn)
    if box is None:
        return False
    cx, cy, size = box
    side = int(min(size * side_factor, w, h)) // 2 * 2
    x = int(np.clip(cx - side / 2, 0, w - side))
    y = int(np.clip(cy - side / 2, 0, h - side))
    subprocess.run([ffmpeg, '-y', '-i', str(src), '-vf', f'crop={side}:{side}:{x}:{y},scale=224:224', '-an', '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p', '-b:v', bitrate, '-r', '25', str(dst)], check=True, capture_output=True)
    return True


def summarise(rows):
    y = np.array([r['label'] == 'fake' for r in rows])
    p = np.array([r['p_video'] for r in rows])
    return {'n': len(rows), 'accuracy': float(((p >= 0.5) == y).mean()), 'auc': float(roc_auc_score(y, p)),
            'mean_p_real': float(p[~y].mean()), 'mean_p_fake': float(p[y].mean()),
            'real_flagged_fake': float((p[~y] >= 0.5).mean()), 'fake_flagged': float((p[y] >= 0.5).mean())}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--manifest', default=str(PROJECT_ROOT / 'eval_heldout' / 'manifest.json'))
    ap.add_argument('--side', type=float, default=1.45)
    ap.add_argument('--bitrate', default='100k')
    ap.add_argument('--out', default=str(PROJECT_ROOT / 'results' / 'lowres_diagnostic' / 'diagnostic.json'))
    args = ap.parse_args()
    out = Path(args.out)
    if out.exists():
        sys.exit(f'{out} exists; refusing to overwrite')
    clips = json.load(open(args.manifest))['clips']
    videos = sorted({(c['video_source'], c['video_label']) for c in clips})
    ffmpeg = __import__('imageio_ffmpeg').get_ffmpeg_exe()
    mtcnn, model, device = vi.load_models()
    rows = {'original': [], 'closeup': []}
    skipped = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, (src, label) in enumerate(videos):
            srcp = PROJECT_ROOT / src
            dst = Path(tmp) / f'{i}.mp4'
            if not make_closeup(srcp, dst, ffmpeg, mtcnn, args.side, args.bitrate):
                skipped.append(src)
                continue
            for cond, path in (('original', srcp), ('closeup', dst)):
                r = vi.analyse_video_file(str(path), mtcnn, model, device, max_faces=20)
                if r is None:
                    skipped.append(f'{cond}:{src}')
                    continue
                rows[cond].append({'video': src, 'label': label, 'p_video': r['p_fake'], 'n_faces': r['n_faces']})
            print(f'[{i + 1}/{len(videos)}] {label} {Path(src).name}: '
                  f'orig {rows["original"][-1]["p_video"]:.3f}  closeup {rows["closeup"][-1]["p_video"]:.3f}', flush=True)
    both = {r['video'] for r in rows['original']} & {r['video'] for r in rows['closeup']}
    res = {cond: summarise([r for r in rs if r['video'] in both]) for cond, rs in rows.items()}
    res['settings'] = {'side_factor': args.side, 'bitrate': args.bitrate, 'videos_scored_both_ways': len(both), 'skipped': skipped}
    res['auc_drop'] = res['original']['auc'] - res['closeup']['auc']
    res['reading'] = ('resolution/framing/compression explains the failure' if res['auc_drop'] > 0.15
                      else 'closeup framing, resolution and bitrate alone do NOT explain the failure')
    res['per_video'] = rows
    out.parent.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps({k: v for k, v in res.items() if k != 'per_video'}, indent=1))


if __name__ == '__main__':
    main()
