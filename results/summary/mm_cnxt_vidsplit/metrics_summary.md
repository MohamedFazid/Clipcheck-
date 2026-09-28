# Video branch — 3-run summary (seeds [42, 43, 44], variant: mm_cnxt_vidsplit)

Data split held fixed (seed 42); training seed varied. std is sample std (ddof=1).

## Video-level (primary — matches app output, n=[44, 44, 44] held-out videos)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.9318 ± 0.0227 | 0.9091 | 0.9318 | 0.9545 |
| f1 | 0.9330 ± 0.0237 | 0.9091 | 0.9333 | 0.9565 |
| precision | 0.9129 ± 0.0038 | 0.9091 | 0.9130 | 0.9167 |
| recall | 0.9545 ± 0.0455 | 0.9091 | 0.9545 | 1.0000 |
| auc_roc | 0.9800 ± 0.0121 | 0.9711 | 0.9752 | 0.9938 |
| eer | 0.0379 ± 0.0131 | 0.0455 | 0.0455 | 0.0227 |

## Frame-level (secondary — pseudo-replicated, ~19 correlated crops/video)

| Metric | Mean ± Std | seed 42 | seed 43 | seed 44 |
|---|---|---|---|---|
| accuracy | 0.8615 ± 0.0259 | 0.8338 | 0.8657 | 0.8850 |
| f1 | 0.8581 ± 0.0296 | 0.8261 | 0.8636 | 0.8846 |
| precision | 0.8338 ± 0.0122 | 0.8213 | 0.8342 | 0.8457 |
| recall | 0.8844 ± 0.0490 | 0.8309 | 0.8950 | 0.9271 |
| auc_roc | 0.9368 ± 0.0135 | 0.9215 | 0.9417 | 0.9473 |
