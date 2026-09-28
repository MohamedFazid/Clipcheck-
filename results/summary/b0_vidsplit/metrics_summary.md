# Video branch — 3-run summary (seeds [42, 43, 44], variant: b0_vidsplit)

Data split held fixed (seed 42); training seed varied. std is sample std (ddof=1).

## Video-level (primary — matches app output, n=[44, 44, 44] held-out videos)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 1.0000 ± 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| f1 | 1.0000 ± 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| precision | 1.0000 ± 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| recall | 1.0000 ± 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| auc_roc | 1.0000 ± 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| eer | 0.0000 ± 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Frame-level (secondary — pseudo-replicated, ~19 correlated crops/video)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.9464 ± 0.0156 | 0.9367 | 0.9644 | 0.9380 |
| f1 | 0.9472 ± 0.0147 | 0.9372 | 0.9640 | 0.9404 |
| precision | 0.9360 ± 0.0345 | 0.9299 | 0.9731 | 0.9049 |
| recall | 0.9595 ± 0.0176 | 0.9446 | 0.9551 | 0.9789 |
| auc_roc | 0.9902 ± 0.0036 | 0.9871 | 0.9941 | 0.9895 |
