# Training-variant comparison — video branch

All variants evaluated on the SAME fixed test split (758 crops); std is sample std (ddof=1) across training seeds. Metrics in the first table are FRAME-level.

**Overfitting gap** = final-epoch train accuracy − final-epoch validation accuracy, in percentage points. Lower is better: this is the quantity Chapter 5.4 flags qualitatively on the baseline.

| Variant | Seeds | Accuracy | F1 | AUC-ROC | EER | Overfitting gap | Epochs |
|---|---|---|---|---|---|---|---|
| baseline (no augmentation), fixed split | [42, 43, 44] | 0.8681 ± 0.0058 | 0.8622 ± 0.0074 | 0.9541 ± 0.0029 | 0.1258 ± 0.0027 | 9.49 ± 0.31 pp | [10, 10, 10] |
| augmentation on, fixed split | [42, 43, 44] | 0.8993 ± 0.0099 | 0.8967 ± 0.0109 | 0.9722 ± 0.0044 | 0.0981 ± 0.0176 | 7.07 ± 0.15 pp | [10, 10, 10] |
| augmentation + regularised, fixed split | [42, 43, 44] | 0.8830 ± 0.0180 | 0.8789 ± 0.0194 | 0.9590 ± 0.0105 | 0.1161 ± 0.0156 | 6.15 ± 0.75 pp | [10, 10, 10] |

## Video-level (one mean-aggregated score per held-out video; matches what the app reports)

| Variant | Videos | Accuracy | F1 | AUC-ROC | EER |
|---|---|---|---|---|---|
| baseline (no augmentation), fixed split | 44 | 0.9697 ± 0.0131 | 0.9693 ± 0.0128 | 0.9952 ± 0.0032 | 0.0303 ± 0.0131 |
| augmentation on, fixed split | 44 | 0.9697 ± 0.0131 | 0.9686 ± 0.0141 | 0.9966 ± 0.0043 | 0.0227 ± 0.0227 |
| augmentation + regularised, fixed split | 44 | 0.9697 ± 0.0131 | 0.9686 ± 0.0141 | 0.9952 ± 0.0052 | 0.0227 ± 0.0227 |

## Checkpoint criterion: which epoch each rule would select (per seed, 1-indexed)

| Variant | Best val accuracy | Lowest val loss |
|---|---|---|
| baseline (no augmentation), fixed split | [10, 5, 5] | [7, 9, 7] |
| augmentation on, fixed split | [10, 9, 8] | [9, 4, 10] |
| augmentation + regularised, fixed split | [10, 10, 10] | [10, 10, 9] |

## Change vs baseline

| Variant | Δ accuracy | Δ overfitting gap |
|---|---|---|
| augmentation on, fixed split | +0.0312 | -2.42 pp |
| augmentation + regularised, fixed split | +0.0150 | -3.34 pp |
