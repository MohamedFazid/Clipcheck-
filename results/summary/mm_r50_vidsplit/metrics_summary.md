# Video branch — 3-run summary (seeds [42, 43, 44], variant: mm_r50_vidsplit)

Data split held fixed (seed 42); training seed varied. std is sample std (ddof=1).

## Video-level (primary — matches app output, n=[44, 44, 44] held-out videos)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.8712 ± 0.0473 | 0.8182 | 0.8864 | 0.9091 |
| f1 | 0.8703 ± 0.0469 | 0.8182 | 0.8837 | 0.9091 |
| precision | 0.8773 ± 0.0513 | 0.8182 | 0.9048 | 0.9091 |
| recall | 0.8636 ± 0.0455 | 0.8182 | 0.8636 | 0.9091 |
| auc_roc | 0.9656 ± 0.0098 | 0.9545 | 0.9690 | 0.9731 |
| eer | 0.1136 ± 0.0601 | 0.1818 | 0.0682 | 0.0909 |

## Frame-level (secondary — pseudo-replicated, ~19 correlated crops/video)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.8052 ± 0.0267 | 0.7839 | 0.8352 | 0.7964 |
| f1 | 0.8000 ± 0.0238 | 0.7892 | 0.8273 | 0.7835 |
| precision | 0.7836 ± 0.0446 | 0.7355 | 0.8237 | 0.7917 |
| recall | 0.8192 ± 0.0392 | 0.8513 | 0.8309 | 0.7755 |
| auc_roc | 0.8926 ± 0.0088 | 0.8832 | 0.9005 | 0.8943 |
