# Video branch — 3-run summary (seeds [42, 43, 44], variant: cnxt_vidsplit)

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
| accuracy | 0.9626 ± 0.0046 | 0.9631 | 0.9670 | 0.9578 |
| f1 | 0.9634 ± 0.0044 | 0.9639 | 0.9675 | 0.9588 |
| precision | 0.9443 ± 0.0086 | 0.9421 | 0.9538 | 0.9370 |
| recall | 0.9833 ± 0.0030 | 0.9868 | 0.9815 | 0.9815 |
| auc_roc | 0.9952 ± 0.0006 | 0.9956 | 0.9954 | 0.9945 |
