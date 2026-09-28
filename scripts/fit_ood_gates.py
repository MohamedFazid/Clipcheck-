"""Fit and calibrate the two out-of-domain gates (scripts/ood_gate.py; docs/EXPERIMENTS.md O1). Rules fixed 2026-09-22 03:10, before any gate
was fitted and before any gate result on any set existed.

DATA ROLES (no set plays two roles):
    fit        audio: ASVspoof 2019 LA TRAIN embeddings (the SVM's own training data, cached)
               video: FF++ TRAIN-split face crops of frames_multi/ (the shipped Xception's own training crops), frozen split manifest
    calibrate  audio: ASVspoof DEV embeddings; video: FF++ VALIDATION-split crops. Threshold = 97.5th percentile of their distances
               (expected in-domain abstention about 2.5% per sample; a clip's video distance is the MEDIAN over its crops, so fewer clips).
    choose     variant 'pooled' vs 'class' (scripts/ood_gate.py) per branch, on the LAV-DF DEV tuning clips only
               (results/ood_gate/features/lavdf_dev.joblib): the variant that flags MORE of them; tie -> 'pooled'.
    test       everything else (scripts/eval_ood_gate.py): LAV-DF TEST (eval_lavdf/), DeepfakeTIMIT, Celeb-DF-v2, the in-domain sets.

SHIP CRITERIA (checked by scripts/eval_ood_gate.py, stated here so they cannot move):
    (a) per branch, in-domain abstention on eval_heldout/ + eval_fallback/ clips through the app path <= 5%; a branch failing it is not shipped
    (b) disagreement-aware accuracy on eval_heldout/, counting INCONCLUSIVE as not correct, falls by no more than 2 pp
    (c) on LAV-DF TEST, the number of confident WRONG verdicts (a REAL/FAKE/PARTIAL verdict that is wrong) falls

    /opt/anaconda3/envs/deepfake-detect/bin/python scripts/fit_ood_gates.py
"""
import json
import subprocess
import sys
from pathlib import Path

import joblib
import numpy as np
import torch
from torch.utils.data import DataLoader, Subset
from torchvision import datasets

sys.path.insert(0, str(Path(__file__).resolve().parent))
import video_infer as vi  # noqa: E402
from ood_gate import MahalanobisGate, clip_video_distance  # noqa: E402
from utils import split_from_manifest  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FEAT = ROOT / 'results' / 'ood_gate' / 'features'
EMB = ROOT / 'results' / 'audio_branch' / 'embeddings'
PERCENTILE = 97.5


def ffpp_crop_features():
    cache = FEAT / 'ffpp_crops.npz'
    if cache.exists():
        d = np.load(cache)
        return d['Xtr'], d['ytr'], d['Xva'], d['yva']
    _, model, device = vi.load_models()
    ds = datasets.ImageFolder(str(ROOT / 'frames_multi'), transform=vi._val_transforms)
    tr, va, _ = split_from_manifest(ds)
    out = []
    for idx in (tr, va):
        X, y = [], []
        for xb, yb in DataLoader(Subset(ds, idx), batch_size=32, num_workers=0):
            with torch.no_grad():
                X.append(model.forward_head(model.forward_features(xb.to(device)), pre_logits=True).float().cpu().numpy())
            y.append(yb.numpy())
        out += [np.vstack(X), np.concatenate(y)]
    np.savez(cache, Xtr=out[0], ytr=out[1], Xva=out[2], yva=out[3])
    return out


def main():
    FEAT.mkdir(parents=True, exist_ok=True)
    dev = joblib.load(FEAT / 'lavdf_dev.joblib')
    report = {'percentile': PERCENTILE, 'rules': 'see module docstring', 'branches': {}}

    # ---- audio ----
    tr = np.load(EMB / 'train_25380.npz', allow_pickle=True)
    cal = np.load(EMB / 'dev_24844.npz', allow_pickle=True)['X']
    tune = np.array([r['audio_embedding'] for r in dev if r['audio_embedding'] is not None])
    cands = {}
    for kind in ('pooled', 'class'):
        g = MahalanobisGate(kind, PERCENTILE).fit(tr['X'], tr['y']).calibrate(cal)
        cands[kind] = (g, float(g.is_out_of_domain(g.distance(tune)).mean()))
    chosen = 'class' if cands['class'][1] > cands['pooled'][1] else 'pooled'
    report['branches']['audio'] = {'fit': 'ASVspoof 2019 LA train (25,380)', 'calibrate': 'ASVspoof 2019 LA dev (24,844)',
                                   'tuning_clips_lavdf_dev': int(len(tune)),
                                   'flag_rate_on_tuning': {k: v[1] for k, v in cands.items()}, 'chosen': chosen,
                                   'threshold': cands[chosen][0].threshold_}
    audio_gate = cands[chosen][0]

    # ---- video ----
    Xtr, ytr, Xva, _ = ffpp_crop_features()
    tune_v = [r['video_features'].astype(np.float32) for r in dev if r['video_features'] is not None]
    cands = {}
    for kind in ('pooled', 'class'):
        g = MahalanobisGate(kind, PERCENTILE).fit(Xtr, ytr).calibrate(Xva)
        cands[kind] = (g, float(np.mean([clip_video_distance(g, f) > g.threshold_ for f in tune_v])))
    chosen = 'class' if cands['class'][1] > cands['pooled'][1] else 'pooled'
    report['branches']['video'] = {'fit': f'FF++ train-split crops of frames_multi ({len(Xtr)})',
                                   'calibrate': f'FF++ validation-split crops ({len(Xva)})', 'clip_rule': 'median over crops',
                                   'tuning_clips_lavdf_dev': len(tune_v),
                                   'flag_rate_on_tuning': {k: v[1] for k, v in cands.items()}, 'chosen': chosen,
                                   'threshold': cands[chosen][0].threshold_}
    video_gate = cands[chosen][0]

    stamp = subprocess.check_output(['date', '+%F %H:%M']).decode().strip()
    for name, g in (('audio', audio_gate), ('video', video_gate)):
        joblib.dump({'gate': g, 'fitted_at': stamp, 'report': report['branches'][name]}, ROOT / 'models' / f'{name}_ood_gate.joblib')
    report['fitted_at'] = stamp
    json.dump(report, open(ROOT / 'results' / 'ood_gate' / 'fit_report.json', 'w'), indent=1)
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
