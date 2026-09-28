"""Compare training variants (baseline vs augmentation-fixed vs regularised).

Answers the question Chapter 5.6 poses but could not yet answer: does fixing
the augmentation-transform bug, and then adding regularisation, actually reduce
the overfitting visible in the baseline training curves -- and at what cost to
test-set performance?

For each variant it reports:
  * test-set metrics as mean +/- std across seeds (from evaluate.py output);
  * the OVERFITTING GAP, defined as final-epoch train_acc minus final-epoch
    val_acc, averaged across seeds. This is the quantity Chapter 5.4 describes
    qualitatively ("training accuracy climbs to 99.93% while validation
    accuracy plateaus around 94.9-95.8%") and is the number that says whether
    the intervention worked;
  * epochs actually run (early stopping makes this vary).

All variants are evaluated on the SAME fixed test split
(tests/test_data_split.py asserts index-identity), so the comparison is valid.

Usage:
    python scripts/compare_variants.py                       # baseline vs aug vs reg
    python scripts/compare_variants.py --variants "" aug     # only those two
    python scripts/compare_variants.py --variants base_vidsplit aug_vidsplit reg_vidsplit \\
        --baseline-tag base_vidsplit --out-name variant_comparison_vidsplit
"""

import os
import sys
import json
import glob
import argparse

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import RUNS_DIR, SUMMARY_DIR

METRICS = ['accuracy', 'f1', 'auc_roc']
VARIANT_LABELS = {
    '': 'baseline (bug present, no reg.)',
    'aug': 'augmentation fixed',
    'reg': 'augmentation fixed + regularised',
    # Identity-disjoint split (leakage fixed); see DEV_LOG 2026-09-19.
    'base_vidsplit': 'baseline (no augmentation), fixed split',
    'aug_vidsplit': 'EfficientNet-B4 (incumbent; augmentation on, fixed split)',
    'reg_vidsplit': 'augmentation + regularised, fixed split',
    # Backbone bake-off (identical recipe to aug_vidsplit, only the architecture varies).
    'b0_vidsplit': 'EfficientNet-B0',
    'r50_vidsplit': 'ResNet-50',
    'xcep_vidsplit': 'Xception',
    'cnxt_vidsplit': 'ConvNeXt-Tiny',
    # Multi-method training (Deepfakes + FaceSwap + NeuralTextures, balanced).
    'mm_r50_vidsplit': 'ResNet-50, multi-method',
    'mm_xcep_vidsplit': 'Xception, multi-method',
    'mm_b0_vidsplit': 'EfficientNet-B0, multi-method',
    'mm_cnxt_vidsplit': 'ConvNeXt-Tiny, multi-method',
}
VIDEO_METRICS = ['accuracy', 'f1', 'auc_roc', 'eer']


def load_variant(tag):
    """Collect per-seed metrics + history for one variant. None if absent."""
    root = RUNS_DIR / tag if tag else RUNS_DIR
    metric_files = sorted(glob.glob(str(root / 'seed*' / 'metrics.json')))
    if not metric_files:
        return None

    runs = []
    for mf in metric_files:
        run_dir = os.path.dirname(mf)
        with open(mf) as f:
            metrics = json.load(f)

        history, config = None, None
        hp = os.path.join(run_dir, 'history.json')
        cp = os.path.join(run_dir, 'train_config.json')
        if os.path.exists(hp):
            with open(hp) as f:
                history = json.load(f)
        if os.path.exists(cp):
            with open(cp) as f:
                config = json.load(f)

        # EER lives in threshold_analysis.json (A2/A3 output), not metrics.json.
        eer = metrics.get('eer')
        tp = os.path.join(run_dir, 'threshold_analysis.json')
        if eer is None and os.path.exists(tp):
            with open(tp) as f:
                eer = json.load(f).get('eer_test')

        runs.append({'metrics': metrics, 'history': history,
                     'config': config, 'eer': eer,
                     'seed': metrics.get('seed')})

    runs.sort(key=lambda r: r['seed'] if r['seed'] is not None else 0)
    return runs


def overfitting_gap(history):
    """final train_acc - final val_acc (percentage points). None if unavailable."""
    if not history or not history.get('train_acc') or not history.get('val_acc'):
        return None
    return (history['train_acc'][-1] - history['val_acc'][-1]) * 100.0


def summarise(runs):
    out = {'seeds': [r['seed'] for r in runs], 'n': len(runs)}

    for m in METRICS:
        vals = np.array([r['metrics'][m] for r in runs if m in r['metrics']], dtype=float)
        if vals.size:
            out[m] = (float(vals.mean()),
                      float(vals.std(ddof=1)) if vals.size > 1 else 0.0)

    eers = np.array([r['eer'] for r in runs if r['eer'] is not None], dtype=float)
    if eers.size:
        out['eer'] = (float(eers.mean()),
                      float(eers.std(ddof=1)) if eers.size > 1 else 0.0)

    gaps = np.array([g for g in (overfitting_gap(r['history']) for r in runs)
                     if g is not None], dtype=float)
    if gaps.size:
        out['gap'] = (float(gaps.mean()),
                      float(gaps.std(ddof=1)) if gaps.size > 1 else 0.0)

    epochs = [len(r['history']['train_acc']) for r in runs if r['history']]
    if epochs:
        out['epochs'] = epochs

    # Video-level metrics (evaluate.py's per-clip aggregation), if present.
    if runs and all('video_level' in r['metrics'] for r in runs):
        out['n_videos'] = runs[0]['metrics']['video_level'].get('n_videos')
        for m in VIDEO_METRICS:
            vals = np.array([r['metrics']['video_level'][m] for r in runs], dtype=float)
            out['v_' + m] = (float(vals.mean()),
                             float(vals.std(ddof=1)) if vals.size > 1 else 0.0)

    # Which epoch each checkpoint criterion would select (1-indexed). Accuracy
    # rule keeps the FIRST epoch reaching the max (train.py saves on strict
    # improvement); loss rule is the epoch of minimum val loss.
    acc_ep, loss_ep = [], []
    for r in runs:
        h = r['history']
        if h and h.get('val_acc') and h.get('val_loss'):
            va, vl = h['val_acc'], h['val_loss']
            acc_ep.append(int(np.argmax(va)) + 1)
            loss_ep.append(int(np.argmin(vl)) + 1)
    if acc_ep:
        out['ckpt_acc_epoch'] = acc_ep
        out['ckpt_loss_epoch'] = loss_ep
    return out


def fmt(stat, pct=False, places=4):
    if stat is None:
        return 'n/a'
    mean, std = stat
    if pct:
        return f'{mean:.2f} ± {std:.2f} pp'
    return f'{mean:.{places}f} ± {std:.{places}f}'


def plot_curves(loaded, out_path):
    """Training vs validation accuracy per variant -- the visual Ch5.4 check."""
    n = len(loaded)
    fig, axes = plt.subplots(1, n, figsize=(5.2 * n, 4.2), squeeze=False)
    for ax, (tag, runs) in zip(axes[0], loaded.items()):
        for r in runs:
            h = r['history']
            if not h:
                continue
            epochs = range(1, len(h['train_acc']) + 1)
            ax.plot(epochs, h['train_acc'], color='steelblue', alpha=0.75,
                    label='train' if r is runs[0] else None)
            ax.plot(epochs, h['val_acc'], color='darkorange', alpha=0.75,
                    linestyle='--', label='validation' if r is runs[0] else None)
        s = summarise(runs)
        gap_txt = fmt(s.get('gap'), pct=True)
        ax.set_title(f'{VARIANT_LABELS.get(tag, tag)}\nfinal gap: {gap_txt}', fontsize=10)
        ax.set_xlabel('epoch')
        ax.set_ylabel('accuracy')
        ax.set_ylim(0.6, 1.02)
        ax.grid(alpha=0.3)
        ax.legend(loc='lower right', fontsize=9)
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def main():
    ap = argparse.ArgumentParser(description='Compare training variants.')
    ap.add_argument('--variants', nargs='+', default=['', 'aug', 'reg'],
                    help="Variant tags to compare ('' = baseline).")
    ap.add_argument('--baseline-tag', default='',
                    help="Tag treated as the baseline for the delta table.")
    ap.add_argument('--out-name', default='variant_comparison',
                    help='Output file stem under results/summary/. Use a distinct '
                         'stem so the reported leaking-split comparison is not overwritten.')
    args = ap.parse_args()

    loaded = {}
    for tag in args.variants:
        runs = load_variant(tag)
        if runs is None:
            print(f'(skipping variant {tag or "baseline"!r}: no runs found)')
            continue
        loaded[tag] = runs

    if not loaded:
        print('No variants found. Run scripts/run_cell.sh first.')
        return 1

    n_crops = next((r['metrics'].get('test_crops') for runs in loaded.values()
                    for r in runs if r['metrics'].get('test_crops')), 'n/a')
    lines = ['# Training-variant comparison — video branch\n',
             f'All variants evaluated on the SAME fixed test split ({n_crops} crops); '
             'std is sample std (ddof=1) across training seeds. Metrics in the '
             'first table are FRAME-level.\n',
             '**Overfitting gap** = final-epoch train accuracy − final-epoch '
             'validation accuracy, in percentage points. Lower is better: this '
             'is the quantity Chapter 5.4 flags qualitatively on the baseline.\n']

    header = ('| Variant | Seeds | Accuracy | F1 | AUC-ROC | EER | '
              'Overfitting gap | Epochs |')
    lines += [header, '|' + '---|' * 8]

    for tag, runs in loaded.items():
        s = summarise(runs)
        lines.append(
            f'| {VARIANT_LABELS.get(tag, tag)} | {s["seeds"]} | '
            f'{fmt(s.get("accuracy"))} | {fmt(s.get("f1"))} | '
            f'{fmt(s.get("auc_roc"))} | {fmt(s.get("eer"))} | '
            f'{fmt(s.get("gap"), pct=True)} | {s.get("epochs", "n/a")} |')

    if any('v_accuracy' in summarise(runs) for runs in loaded.values()):
        lines += ['\n## Video-level (one mean-aggregated score per held-out video; '
                  'matches what the app reports)\n',
                  '| Variant | Videos | Accuracy | F1 | AUC-ROC | EER |',
                  '|' + '---|' * 6]
        for tag, runs in loaded.items():
            s = summarise(runs)
            if 'v_accuracy' not in s:
                continue
            lines.append(
                f'| {VARIANT_LABELS.get(tag, tag)} | {s.get("n_videos", "n/a")} | '
                f'{fmt(s.get("v_accuracy"))} | {fmt(s.get("v_f1"))} | '
                f'{fmt(s.get("v_auc_roc"))} | {fmt(s.get("v_eer"))} |')

    if any('ckpt_acc_epoch' in summarise(runs) for runs in loaded.values()):
        lines += ['\n## Checkpoint criterion: which epoch each rule would select '
                  '(per seed, 1-indexed)\n',
                  '| Variant | Best val accuracy | Lowest val loss |',
                  '|---|---|---|']
        for tag, runs in loaded.items():
            s = summarise(runs)
            if 'ckpt_acc_epoch' in s:
                lines.append(f'| {VARIANT_LABELS.get(tag, tag)} | '
                             f'{s["ckpt_acc_epoch"]} | {s["ckpt_loss_epoch"]} |')

    # Headline deltas vs the baseline, if the baseline is in the comparison.
    if args.baseline_tag in loaded:
        base = summarise(loaded[args.baseline_tag])
        lines.append('\n## Change vs baseline\n')
        lines.append('| Variant | Δ accuracy | Δ overfitting gap |')
        lines.append('|---|---|---|')
        for tag, runs in loaded.items():
            if tag == args.baseline_tag:
                continue
            s = summarise(runs)
            d_acc = (s['accuracy'][0] - base['accuracy'][0]) if (
                'accuracy' in s and 'accuracy' in base) else None
            d_gap = (s['gap'][0] - base['gap'][0]) if (
                'gap' in s and 'gap' in base) else None
            lines.append(
                f'| {VARIANT_LABELS.get(tag, tag)} | '
                f'{f"{d_acc:+.4f}" if d_acc is not None else "n/a"} | '
                f'{f"{d_gap:+.2f} pp" if d_gap is not None else "n/a"} |')

    md = '\n'.join(lines) + '\n'
    os.makedirs(SUMMARY_DIR, exist_ok=True)
    out_md = SUMMARY_DIR / f'{args.out_name}.md'
    with open(out_md, 'w') as f:
        f.write(md)

    fig_path = SUMMARY_DIR / (f'{args.out_name}_curves.png'
                              if args.out_name != 'variant_comparison'
                              else 'variant_training_curves.png')
    plot_curves(loaded, fig_path)

    print(md)
    print(f'Wrote: {out_md}')
    print(f'Wrote: {fig_path}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
