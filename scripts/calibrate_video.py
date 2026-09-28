"""Temperature-scale a trained video model and report calibration before and after.

Why: fusion.py treats each branch's P(fake) as a probability. An over-confident network pushes scores to 0 or 1, which
makes the disagreement gap |P(video) - P(audio)| behave badly and makes displayed scores misleading. Temperature scaling
divides the logits by one scalar T (fitted on the VALIDATION crops only), so it cannot change any decision (the sign of
the logit difference is unchanged, so accuracy, AUC and EER are identical) but it makes the probabilities honest.

Reports, for validation and test crops and for test clips (mean of a video's crop probabilities, the unit the app shows):
NLL, Brier score, and binary ECE (equal-width bins on P(fake)), before and after. Writes results/calibration/<tag>_seed<N>/
calibration.json and a reliability diagram. Clip-level ECE uses only the test videos (about 44), so it is noisy: read it
together with the crop-level figures.

    /opt/anaconda3/bin/python scripts/calibrate_video.py --tag mm_xcep_vidsplit            # best-validation seed
    /opt/anaconda3/bin/python scripts/calibrate_video.py --tag mm_xcep_vidsplit --seed 43
"""
import argparse
import json
import os
import sys

import numpy as np
import torch
import timm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.optimize import minimize_scalar
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import PROJECT_ROOT, RESULTS_DIR, RUNS_DIR, MODEL_RUNS_DIR, FRAMES_DIR, get_device, get_split, _video_folder_of  # noqa: E402

TF = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(),
                         transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])


def best_val_seed(tag):
    best = None
    for d in sorted((RUNS_DIR / tag).glob('seed*')):
        h = json.load(open(d / 'history.json'))
        cand = (max(h['val_acc']), -min(h['val_loss']), int(d.name[4:]))
        best = cand if best is None or cand > best else best
    return best[2]


@torch.no_grad()
def logit_diff(model, dataset, idx, device):
    """z = logit(fake) - logit(real) per crop, labels (1 = fake) and video folder of each crop."""
    loader = DataLoader(Subset(dataset, list(idx)), batch_size=32, shuffle=False, num_workers=0)
    zs, ys = [], []
    for x, y in loader:
        lg = model(x.to(device)).float().cpu()
        zs.append((lg[:, 0] - lg[:, 1]).numpy())
        ys.append((y == 0).numpy().astype(int))            # ImageFolder: class 0 = fake
    folders = [_video_folder_of(dataset.samples[i][0]) for i in idx]
    return np.concatenate(zs), np.concatenate(ys), np.array(folders)


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -60, 60)))


def nll(p, y):
    p = np.clip(p, 1e-7, 1 - 1e-7)
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())


def brier(p, y):
    return float(((p - y) ** 2).mean())


def ece(p, y, bins=15):
    """Binary ECE: bins on P(fake); gap = |mean(y) - mean(p)| weighted by bin size. Also returns bin data."""
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1]), 0, bins - 1)
    total, data = 0.0, []
    for b in range(bins):
        m = idx == b
        if m.any():
            gap = abs(y[m].mean() - p[m].mean())
            total += m.mean() * gap
            data.append({'bin': b, 'n': int(m.sum()), 'mean_p': float(p[m].mean()), 'frac_fake': float(y[m].mean())})
    return float(total), data


def fit_temperature(z, y):
    res = minimize_scalar(lambda lt: nll(sigmoid(z / np.exp(lt)), y), bounds=(-3, 3), method='bounded')
    return float(np.exp(res.x))


def block(z, y, T, bins=15):
    out = {}
    for name, temp in (('before', 1.0), ('after', T)):
        p = sigmoid(z / temp)
        e, data = ece(p, y, bins)
        out[name] = {'nll': nll(p, y), 'brier': brier(p, y), 'ece': e, 'bins': data}
    return out


def clip_block(z, y, folders, T):
    vids = sorted(set(folders))
    yv = np.array([y[folders == v][0] for v in vids])
    out = {'n_videos': len(vids)}
    for name, temp in (('before', 1.0), ('after', T)):
        pv = np.array([sigmoid(z[folders == v] / temp).mean() for v in vids])
        e, _ = ece(pv, yv, 5)
        out[name] = {'brier': brier(pv, yv), 'ece_5bins': e, 'mean_p_fake_on_fakes': float(pv[yv == 1].mean()),
                     'mean_p_fake_on_reals': float(pv[yv == 0].mean())}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', required=True)
    ap.add_argument('--seed', type=int, default=None, help='Default: best validation accuracy.')
    args = ap.parse_args()

    seed = args.seed if args.seed is not None else best_val_seed(args.tag)
    cfg = json.load(open(RUNS_DIR / args.tag / f'seed{seed}' / 'train_config.json'))
    arch, frames_dir = cfg.get('arch', 'efficientnet_b4'), PROJECT_ROOT / cfg.get('frames_dir', 'frames')
    device = get_device()
    print(f'{args.tag} seed {seed} | arch {arch} | frames {frames_dir.name} | device {device}')

    model = timm.create_model(arch, pretrained=False, num_classes=2)
    model.load_state_dict(torch.load(MODEL_RUNS_DIR / args.tag / f'seed{seed}.pth', map_location=device))
    model.to(device).eval()

    ds = datasets.ImageFolder(str(frames_dir), transform=TF)
    tr, va, te = get_split(ds, str(frames_dir))
    zv, yv, _ = logit_diff(model, ds, va, device)
    zt, yt, ft = logit_diff(model, ds, te, device)

    T = fit_temperature(zv, yv)
    res = {'tag': args.tag, 'seed': seed, 'arch': arch, 'frames_dir': frames_dir.name,
           'temperature': T, 'fitted_on': f'validation crops (n={len(zv)})',
           'validation_crops': block(zv, yv, T), 'test_crops': block(zt, yt, T),
           'test_clips': clip_block(zt, yt, ft, T),
           'decision_unchanged': bool(((zt > 0) == (zt / T > 0)).all()),
           'note': 'T is fitted on validation only. Dividing logits by T cannot change any decision at the 0.5 threshold.'}
    out = RESULTS_DIR / 'calibration' / f'{args.tag}_seed{seed}'
    out.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(out / 'calibration.json', 'w'), indent=2)

    fig, ax = plt.subplots(1, 2, figsize=(9, 4), sharey=True)
    for a, name in zip(ax, ('before', 'after')):
        b = res['test_crops'][name]['bins']
        a.plot([0, 1], [0, 1], 'k--', lw=1)
        a.plot([d['mean_p'] for d in b], [d['frac_fake'] for d in b], 'o-', color='steelblue')
        a.set_title(f'{name} (T={T:.2f}): test ECE {res["test_crops"][name]["ece"]:.3f}')
        a.set_xlabel('mean predicted P(fake)')
    ax[0].set_ylabel('observed fraction fake')
    fig.suptitle(f'{args.tag} seed {seed}: reliability on test crops')
    plt.tight_layout()
    plt.savefig(out / 'reliability.png', dpi=140)
    plt.close()

    tb, ta = res['test_crops']['before'], res['test_crops']['after']
    print(f'T = {T:.3f} | test crops ECE {tb["ece"]:.4f} -> {ta["ece"]:.4f} | NLL {tb["nll"]:.4f} -> {ta["nll"]:.4f} | '
          f'Brier {tb["brier"]:.4f} -> {ta["brier"]:.4f} | decisions unchanged: {res["decision_unchanged"]}')
    print(f'saved {out.relative_to(PROJECT_ROOT)}')


if __name__ == '__main__':
    main()
