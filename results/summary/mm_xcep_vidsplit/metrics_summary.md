# Video branch — 3-run summary (seeds [42, 43, 44], variant: mm_xcep_vidsplit)

Data split held fixed (seed 42); training seed varied. std is sample std (ddof=1).

## Video-level (primary — matches app output, n=[44, 44, 44] held-out videos)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.9621 ± 0.0347 | 0.9318 | 0.9545 | 1.0000 |
| f1 | 0.9616 ± 0.0354 | 0.9302 | 0.9545 | 1.0000 |
| precision | 0.9690 ± 0.0269 | 0.9524 | 0.9545 | 1.0000 |
| recall | 0.9545 ± 0.0455 | 0.9091 | 0.9545 | 1.0000 |
| auc_roc | 0.9952 ± 0.0043 | 0.9938 | 0.9917 | 1.0000 |
| eer | 0.0152 ± 0.0131 | 0.0227 | 0.0227 | 0.0000 |

## Frame-level (secondary — pseudo-replicated, ~19 correlated crops/video)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.8827 ± 0.0204 | 0.8670 | 0.8753 | 0.9058 |
| f1 | 0.8759 ± 0.0197 | 0.8580 | 0.8729 | 0.8970 |
| precision | 0.8837 ± 0.0450 | 0.8709 | 0.8466 | 0.9338 |
| recall | 0.8698 ± 0.0283 | 0.8455 | 0.9009 | 0.8630 |
| auc_roc | 0.9623 ± 0.0123 | 0.9510 | 0.9604 | 0.9753 |
