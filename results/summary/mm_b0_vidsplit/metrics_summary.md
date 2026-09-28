# Video branch — 3-run summary (seeds [42, 43, 44], variant: mm_b0_vidsplit)

Data split held fixed (seed 42); training seed varied. std is sample std (ddof=1).

## Video-level (primary — matches app output, n=[44, 44, 44] held-out videos)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.8409 ± 0.0394 | 0.8864 | 0.8182 | 0.8182 |
| f1 | 0.8279 ± 0.0483 | 0.8837 | 0.8000 | 0.8000 |
| precision | 0.8942 ± 0.0092 | 0.9048 | 0.8889 | 0.8889 |
| recall | 0.7727 ± 0.0787 | 0.8636 | 0.7273 | 0.7273 |
| auc_roc | 0.9387 ± 0.0145 | 0.9525 | 0.9401 | 0.9236 |
| eer | 0.1439 ± 0.0572 | 0.0909 | 0.2045 | 0.1364 |

## Frame-level (secondary — pseudo-replicated, ~19 correlated crops/video)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.7687 ± 0.0228 | 0.7825 | 0.7812 | 0.7424 |
| f1 | 0.7508 ± 0.0249 | 0.7715 | 0.7577 | 0.7232 |
| precision | 0.7694 ± 0.0304 | 0.7703 | 0.7994 | 0.7386 |
| recall | 0.7337 ± 0.0342 | 0.7726 | 0.7201 | 0.7085 |
| auc_roc | 0.8634 ± 0.0239 | 0.8819 | 0.8719 | 0.8364 |
