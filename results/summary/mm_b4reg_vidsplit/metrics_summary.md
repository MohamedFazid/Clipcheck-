# Video branch — 3-run summary (seeds [42, 43, 44], variant: mm_b4reg_vidsplit)

Data split held fixed (seed 42); training seed varied. std is sample std (ddof=1).

## Video-level (primary — matches app output, n=[44, 44, 44] held-out videos)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.9167 ± 0.0347 | 0.9545 | 0.9091 | 0.8864 |
| f1 | 0.9109 ± 0.0394 | 0.9545 | 0.9000 | 0.8780 |
| precision | 0.9673 ± 0.0285 | 0.9545 | 1.0000 | 0.9474 |
| recall | 0.8636 ± 0.0787 | 0.9545 | 0.8182 | 0.8182 |
| auc_roc | 0.9814 ± 0.0095 | 0.9897 | 0.9835 | 0.9711 |
| eer | 0.0530 ± 0.0347 | 0.0455 | 0.0227 | 0.0909 |

## Frame-level (secondary — pseudo-replicated, ~19 correlated crops/video)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.7539 ± 0.0208 | 0.7756 | 0.7521 | 0.7341 |
| f1 | 0.7350 ± 0.0287 | 0.7652 | 0.7316 | 0.7082 |
| precision | 0.7512 ± 0.0107 | 0.7608 | 0.7531 | 0.7397 |
| recall | 0.7201 ± 0.0458 | 0.7697 | 0.7114 | 0.6793 |
| auc_roc | 0.8340 ± 0.0224 | 0.8598 | 0.8188 | 0.8236 |
