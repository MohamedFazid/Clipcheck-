# Video branch — 3-run summary (seeds [42, 43, 44], variant: aug_vidsplit)

Data split held fixed (seed 42); training seed varied. std is sample std (ddof=1).

## Video-level (primary — matches app output, n=[44, 44, 44] held-out videos)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.9697 ± 0.0131 | 0.9545 | 0.9773 | 0.9773 |
| f1 | 0.9686 ± 0.0141 | 0.9524 | 0.9767 | 0.9767 |
| precision | 1.0000 ± 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| recall | 0.9394 ± 0.0262 | 0.9091 | 0.9545 | 0.9545 |
| auc_roc | 0.9966 ± 0.0043 | 0.9917 | 0.9979 | 1.0000 |
| eer | 0.0227 ± 0.0227 | 0.0227 | 0.0455 | 0.0000 |

## Frame-level (secondary — pseudo-replicated, ~19 correlated crops/video)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.8993 ± 0.0099 | 0.8879 | 0.9050 | 0.9050 |
| f1 | 0.8967 ± 0.0109 | 0.8840 | 0.9027 | 0.9032 |
| precision | 0.9203 ± 0.0050 | 0.9153 | 0.9252 | 0.9205 |
| recall | 0.8742 ± 0.0170 | 0.8549 | 0.8813 | 0.8865 |
| auc_roc | 0.9722 ± 0.0044 | 0.9672 | 0.9751 | 0.9743 |
