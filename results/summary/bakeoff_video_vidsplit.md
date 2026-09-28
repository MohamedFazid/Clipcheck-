# Training-variant comparison — video branch

All variants evaluated on the SAME fixed test split (758 crops); std is sample std (ddof=1) across training seeds. Metrics in the first table are FRAME-level.

**Overfitting gap** = final-epoch train accuracy − final-epoch validation accuracy, in percentage points. Lower is better: this is the quantity Chapter 5.4 flags qualitatively on the baseline.

| Variant | Seeds | Accuracy | F1 | AUC-ROC | EER | Overfitting gap | Epochs |
|---|---|---|---|---|---|---|---|
| EfficientNet-B4 (incumbent; augmentation on, fixed split) | [42, 43, 44] | 0.8993 ± 0.0099 | 0.8967 ± 0.0109 | 0.9722 ± 0.0044 | 0.0981 ± 0.0176 | 7.07 ± 0.15 pp | [10, 10, 10] |
| EfficientNet-B0 | [42, 43, 44] | 0.9464 ± 0.0156 | 0.9472 ± 0.0147 | 0.9902 ± 0.0036 | 0.0519 ± 0.0110 | 5.81 ± 2.58 pp | [10, 10, 10] |
| ResNet-50 | [42, 43, 44] | 0.9402 ± 0.0008 | 0.9414 ± 0.0008 | 0.9905 ± 0.0015 | 0.0545 ± 0.0042 | 1.46 ± 0.51 pp | [10, 10, 10] |
| Xception | [42, 43, 44] | 0.9472 ± 0.0040 | 0.9476 ± 0.0039 | 0.9930 ± 0.0006 | 0.0475 ± 0.0053 | 3.37 ± 0.70 pp | [10, 10, 10] |
| ConvNeXt-Tiny | [42, 43, 44] | 0.9626 ± 0.0046 | 0.9634 ± 0.0044 | 0.9952 ± 0.0006 | 0.0405 ± 0.0008 | 2.44 ± 0.09 pp | [10, 10, 10] |

## Video-level (one mean-aggregated score per held-out video; matches what the app reports)

| Variant | Videos | Accuracy | F1 | AUC-ROC | EER |
|---|---|---|---|---|---|
| EfficientNet-B4 (incumbent; augmentation on, fixed split) | 44 | 0.9697 ± 0.0131 | 0.9686 ± 0.0141 | 0.9966 ± 0.0043 | 0.0227 ± 0.0227 |
| EfficientNet-B0 | 44 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| ResNet-50 | 44 | 0.9924 ± 0.0131 | 0.9926 ± 0.0128 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 |
| Xception | 44 | 0.9924 ± 0.0131 | 0.9922 ± 0.0134 | 0.9986 ± 0.0024 | 0.0076 ± 0.0131 |
| ConvNeXt-Tiny | 44 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 1.0000 ± 0.0000 | 0.0000 ± 0.0000 |

## Checkpoint criterion: which epoch each rule would select (per seed, 1-indexed)

| Variant | Best val accuracy | Lowest val loss |
|---|---|---|
| EfficientNet-B4 (incumbent; augmentation on, fixed split) | [10, 9, 8] | [9, 4, 10] |
| EfficientNet-B0 | [8, 8, 10] | [8, 8, 4] |
| ResNet-50 | [5, 6, 9] | [9, 6, 9] |
| Xception | [9, 3, 10] | [2, 5, 7] |
| ConvNeXt-Tiny | [5, 9, 5] | [5, 1, 2] |

## Change vs baseline

| Variant | Δ accuracy | Δ overfitting gap |
|---|---|---|
| EfficientNet-B0 | +0.0471 | -1.26 pp |
| ResNet-50 | +0.0409 | -5.60 pp |
| Xception | +0.0479 | -3.70 pp |
| ConvNeXt-Tiny | +0.0633 | -4.63 pp |
