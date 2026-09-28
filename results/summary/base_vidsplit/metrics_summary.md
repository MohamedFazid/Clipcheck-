# Video branch — 3-run summary (seeds [42, 43, 44], variant: base_vidsplit)

Data split held fixed (seed 42); training seed varied. std is sample std (ddof=1).

## Video-level (primary — matches app output, n=[44, 44, 44] held-out videos)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.9697 ± 0.0131 | 0.9545 | 0.9773 | 0.9773 |
| f1 | 0.9693 ± 0.0128 | 0.9545 | 0.9767 | 0.9767 |
| precision | 0.9848 ± 0.0262 | 0.9545 | 1.0000 | 1.0000 |
| recall | 0.9545 ± 0.0000 | 0.9545 | 0.9545 | 0.9545 |
| auc_roc | 0.9952 ± 0.0032 | 0.9959 | 0.9979 | 0.9917 |
| eer | 0.0303 ± 0.0131 | 0.0227 | 0.0455 | 0.0227 |

## Frame-level (secondary — pseudo-replicated, ~19 correlated crops/video)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.8681 ± 0.0058 | 0.8747 | 0.8641 | 0.8654 |
| f1 | 0.8622 ± 0.0074 | 0.8707 | 0.8579 | 0.8579 |
| precision | 0.9021 ± 0.0056 | 0.8989 | 0.8988 | 0.9086 |
| recall | 0.8259 ± 0.0165 | 0.8443 | 0.8206 | 0.8127 |
| auc_roc | 0.9541 ± 0.0029 | 0.9510 | 0.9543 | 0.9569 |
