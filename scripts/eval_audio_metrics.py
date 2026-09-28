"""Full audio metrics (accuracy, balanced accuracy, F1, AUC) from the cached eval embeddings; writes extra_metrics.json.

    python scripts/eval_audio_metrics.py"""
import json
import os
import sys
import warnings

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import RESULTS_DIR, compute_eer  # noqa: E402

EMB = RESULTS_DIR / 'audio_branch' / 'embeddings' / 'eval_71237.npz'
METRICS = RESULTS_DIR / 'audio_branch' / 'metrics.json'
OUT = RESULTS_DIR / 'audio_branch' / 'extra_metrics.json'


def main():
    warnings.filterwarnings('ignore')
    from sklearn.metrics import (accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score,
                                 precision_score, recall_score, roc_auc_score)
    from audio_branch import load_trained_svm

    d = np.load(EMB, allow_pickle=True)
    X, y = d['X'], d['y'].astype(int)
    reported = json.load(open(METRICS))
    svm = load_trained_svm()
    if svm is None:
        sys.exit('no trained SVM found')
    print(f'{len(y)} eval utterances: {int((y == 0).sum())} bona fide, {int((y == 1).sum())} spoof', flush=True)

    scores = svm.spoof_score(X)                       # decision score (EER, AUC)
    pred = svm.clf.predict(X)                         # what train_audio_svm.py used for eval_accuracy
    prob = svm.spoof_probability(X)                   # what the app and fusion use (P(audio_fake))
    eer, _ = compute_eer(y, scores)

    def block(p):
        tn, fp, fn, tp = confusion_matrix(y, p, labels=[0, 1]).ravel()
        return {'accuracy': float(accuracy_score(y, p)), 'balanced_accuracy': float(balanced_accuracy_score(y, p)),
                'precision_spoof': float(precision_score(y, p, zero_division=0)),
                'recall_spoof': float(recall_score(y, p)),
                'f1_spoof': float(f1_score(y, p)),
                'f1_bonafide': float(f1_score(y, p, pos_label=0)),
                'f1_macro': float(f1_score(y, p, average='macro')),
                'specificity_bonafide_recall': float(tn / (tn + fp)),
                'confusion_matrix_[bonafide,spoof]x[pred_bonafide,pred_spoof]': [[int(tn), int(fp)], [int(fn), int(tp)]]}

    out = {
        'dataset': 'ASVspoof 2019 LA eval (full)', 'n_eval': int(len(y)), 'n_bonafide': int((y == 0).sum()),
        'n_spoof': int((y == 1).sum()),
        'majority_class_baseline_accuracy': float(max((y == 1).mean(), (y == 0).mean())),
        'auc_roc': float(roc_auc_score(y, scores)), 'eer': float(eer),
        'at_svm_decision_boundary (clf.predict, as in metrics.json)': block(pred),
        'at_probability_0.5 (as the app and fusion use it)': block((prob >= 0.5).astype(int)),
        'consistency_with_metrics_json': {
            'eer_recomputed': float(eer), 'eer_reported': reported['eval_eer'],
            'accuracy_recomputed': float(accuracy_score(y, pred)), 'accuracy_reported': reported['eval_accuracy']},
        'note': 'Computed by scripts/eval_audio_metrics.py from cached embeddings and the saved SVM. metrics.json is untouched.',
    }
    c = out['consistency_with_metrics_json']
    c['agrees'] = bool(abs(c['eer_recomputed'] - c['eer_reported']) < 5e-4 and abs(c['accuracy_recomputed'] - c['accuracy_reported']) < 5e-4)
    json.dump(out, open(OUT, 'w'), indent=2)
    print(json.dumps({k: v for k, v in out.items() if not k.startswith('at_')}, indent=2))
    for k in ('at_svm_decision_boundary (clf.predict, as in metrics.json)', 'at_probability_0.5 (as the app and fusion use it)'):
        b = out[k]
        print(f'\n{k}\n  acc {b["accuracy"]:.4f}  balanced acc {b["balanced_accuracy"]:.4f}  F1(spoof) {b["f1_spoof"]:.4f}  '
              f'F1(bona fide) {b["f1_bonafide"]:.4f}  macro F1 {b["f1_macro"]:.4f}  bona fide recall {b["specificity_bonafide_recall"]:.4f}')
    print(f'\nWrote {OUT}')


if __name__ == '__main__':
    main()
