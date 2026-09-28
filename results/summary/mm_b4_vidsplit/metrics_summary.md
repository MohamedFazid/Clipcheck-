# Video branch — 3-run summary (seeds [42, 43, 44], variant: mm_b4_vidsplit)

Data split held fixed (seed 42); training seed varied. std is sample std (ddof=1).

## Video-level (primary — matches app output, n=[44, 44, 44] held-out videos)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.9167 ± 0.0473 | 0.9545 | 0.9318 | 0.8636 |
| f1 | 0.9078 ± 0.0586 | 0.9545 | 0.9268 | 0.8421 |
| precision | 0.9848 ± 0.0262 | 0.9545 | 1.0000 | 1.0000 |
| recall | 0.8485 ± 0.1144 | 0.9545 | 0.8636 | 0.7273 |
| auc_roc | 0.9855 ± 0.0107 | 0.9979 | 0.9793 | 0.9793 |
| eer | 0.0606 ± 0.0262 | 0.0455 | 0.0455 | 0.0909 |

## Frame-level (secondary — pseudo-replicated, ~19 correlated crops/video)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.7687 ± 0.0245 | 0.7950 | 0.7645 | 0.7465 |
| f1 | 0.7501 ± 0.0321 | 0.7830 | 0.7485 | 0.7189 |
| precision | 0.7690 ± 0.0161 | 0.7876 | 0.7598 | 0.7597 |
| recall | 0.7328 ± 0.0483 | 0.7784 | 0.7376 | 0.6822 |
| auc_roc | 0.8525 ± 0.0227 | 0.8780 | 0.8343 | 0.8453 |
