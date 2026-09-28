# Video branch — 3-run summary (seeds [42, 43, 44], variant: r50_vidsplit)

Data split held fixed (seed 42); training seed varied. std is sample std (ddof=1).

## Video-level (primary — matches app output, n=[44, 44, 44] held-out videos)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.9924 ± 0.0131 | 1.0000 | 1.0000 | 0.9773 |
| f1 | 0.9926 ± 0.0128 | 1.0000 | 1.0000 | 0.9778 |
| precision | 0.9855 ± 0.0251 | 1.0000 | 1.0000 | 0.9565 |
| recall | 1.0000 ± 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| auc_roc | 1.0000 ± 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| eer | 0.0000 ± 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Frame-level (secondary — pseudo-replicated, ~19 correlated crops/video)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.9402 ± 0.0008 | 0.9406 | 0.9406 | 0.9393 |
| f1 | 0.9414 ± 0.0008 | 0.9413 | 0.9406 | 0.9422 |
| precision | 0.9238 ± 0.0220 | 0.9304 | 0.9418 | 0.8993 |
| recall | 0.9604 ± 0.0260 | 0.9525 | 0.9393 | 0.9894 |
| auc_roc | 0.9905 ± 0.0015 | 0.9904 | 0.9890 | 0.9920 |
