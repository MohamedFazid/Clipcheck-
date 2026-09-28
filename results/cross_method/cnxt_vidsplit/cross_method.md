# Per-method detection: cnxt_vidsplit

Seeds [42, 43, 44]. Trained on Deepfakes only, tested on test-split identities (22 real + 22 fake videos per method; one video = 2.3 pp). Clip-level.

| Fake method | Role | AUC-ROC | EER | Accuracy | Fake detection rate | Real specificity |
|---|---|---|---|---|---|---|
| Deepfakes | in-distribution | 1.000 ± 0.000 | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 |
| FaceSwap | unseen method | 0.266 ± 0.067 | 0.689 ± 0.066 | 0.500 ± 0.000 | 0.000 ± 0.000 | 1.000 ± 0.000 |
| NeuralTextures | unseen method | 0.714 ± 0.006 | 0.341 ± 0.023 | 0.545 ± 0.023 | 0.091 ± 0.045 | 1.000 ± 0.000 |
