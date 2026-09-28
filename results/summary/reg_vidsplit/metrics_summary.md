# Video branch — 3-run summary (seeds [42, 43, 44], variant: reg_vidsplit)

Data split held fixed (seed 42); training seed varied. std is sample std (ddof=1).

## Video-level (primary — matches app output, n=[44, 44, 44] held-out videos)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.9697 ± 0.0131 | 0.9545 | 0.9773 | 0.9773 |
| f1 | 0.9686 ± 0.0141 | 0.9524 | 0.9767 | 0.9767 |
| precision | 1.0000 ± 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| recall | 0.9394 ± 0.0262 | 0.9091 | 0.9545 | 0.9545 |
| auc_roc | 0.9952 ± 0.0052 | 0.9897 | 1.0000 | 0.9959 |
| eer | 0.0227 ± 0.0227 | 0.0455 | 0.0000 | 0.0227 |

## Frame-level (secondary — pseudo-replicated, ~19 correlated crops/video)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.8830 ± 0.0180 | 0.8747 | 0.9037 | 0.8707 |
| f1 | 0.8789 ± 0.0194 | 0.8690 | 0.9012 | 0.8665 |
| precision | 0.9104 ± 0.0146 | 0.9104 | 0.9250 | 0.8958 |
| recall | 0.8496 ± 0.0254 | 0.8311 | 0.8786 | 0.8391 |
| auc_roc | 0.9590 ± 0.0105 | 0.9491 | 0.9700 | 0.9579 |
