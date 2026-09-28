# Training-variant comparison — video branch

All variants evaluated on the SAME fixed test split (722 crops); std is sample std (ddof=1) across training seeds. Metrics in the first table are FRAME-level.

**Overfitting gap** = final-epoch train accuracy − final-epoch validation accuracy, in percentage points. Lower is better: this is the quantity Chapter 5.4 flags qualitatively on the baseline.

| Variant | Seeds | Accuracy | F1 | AUC-ROC | EER | Overfitting gap | Epochs |
|---|---|---|---|---|---|---|---|
| ResNet-50, multi-method | [42, 43, 44] | 0.8052 ± 0.0267 | 0.8000 ± 0.0238 | 0.8926 ± 0.0088 | 0.1944 ± 0.0256 | 21.03 ± 1.01 pp | [10, 10, 10] |
| Xception, multi-method | [42, 43, 44] | 0.8827 ± 0.0204 | 0.8759 ± 0.0197 | 0.9623 ± 0.0123 | 0.1141 ± 0.0232 | 13.66 ± 2.45 pp | [10, 10, 10] |
| EfficientNet-B0, multi-method | [42, 43, 44] | 0.7687 ± 0.0228 | 0.7508 ± 0.0249 | 0.8634 ± 0.0239 | 0.2243 ± 0.0159 | 19.36 ± 1.76 pp | [10, 10, 10] |

## Video-level (one mean-aggregated score per held-out video; matches what the app reports)

| Variant | Videos | Accuracy | F1 | AUC-ROC | EER |
|---|---|---|---|---|---|
| ResNet-50, multi-method | 44 | 0.8712 ± 0.0473 | 0.8703 ± 0.0469 | 0.9656 ± 0.0098 | 0.1136 ± 0.0601 |
| Xception, multi-method | 44 | 0.9621 ± 0.0347 | 0.9616 ± 0.0354 | 0.9952 ± 0.0043 | 0.0152 ± 0.0131 |
| EfficientNet-B0, multi-method | 44 | 0.8409 ± 0.0394 | 0.8279 ± 0.0483 | 0.9387 ± 0.0145 | 0.1439 ± 0.0572 |

## Checkpoint criterion: which epoch each rule would select (per seed, 1-indexed)

| Variant | Best val accuracy | Lowest val loss |
|---|---|---|
| ResNet-50, multi-method | [4, 9, 7] | [3, 7, 3] |
| Xception, multi-method | [10, 4, 10] | [1, 1, 2] |
| EfficientNet-B0, multi-method | [10, 7, 5] | [8, 7, 5] |

## Change vs baseline

| Variant | Δ accuracy | Δ overfitting gap |
|---|---|---|
| Xception, multi-method | +0.0776 | -7.37 pp |
| EfficientNet-B0, multi-method | -0.0365 | -1.67 pp |
