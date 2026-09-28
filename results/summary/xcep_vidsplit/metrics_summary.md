# Video branch — 3-run summary (seeds [42, 43, 44], variant: xcep_vidsplit)

Data split held fixed (seed 42); training seed varied. std is sample std (ddof=1).

## Video-level (primary — matches app output, n=[44, 44, 44] held-out videos)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.9924 ± 0.0131 | 1.0000 | 1.0000 | 0.9773 |
| f1 | 0.9922 ± 0.0134 | 1.0000 | 1.0000 | 0.9767 |
| precision | 1.0000 ± 0.0000 | 1.0000 | 1.0000 | 1.0000 |
| recall | 0.9848 ± 0.0262 | 1.0000 | 1.0000 | 0.9545 |
| auc_roc | 0.9986 ± 0.0024 | 1.0000 | 1.0000 | 0.9959 |
| eer | 0.0076 ± 0.0131 | 0.0000 | 0.0000 | 0.0227 |

## Frame-level (secondary — pseudo-replicated, ~19 correlated crops/video)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.9472 ± 0.0040 | 0.9512 | 0.9433 | 0.9472 |
| f1 | 0.9476 ± 0.0039 | 0.9520 | 0.9445 | 0.9462 |
| precision | 0.9416 ± 0.0206 | 0.9362 | 0.9242 | 0.9644 |
| recall | 0.9543 ± 0.0221 | 0.9683 | 0.9657 | 0.9288 |
| auc_roc | 0.9930 ± 0.0006 | 0.9937 | 0.9929 | 0.9925 |
