# Per-method detection: aug_vidsplit

Seeds [42, 43, 44]. Trained on Deepfakes only, tested on test-split identities (22 real + 22 fake videos per method; one video = 2.3 pp). Clip-level.

| Fake method | Role | AUC-ROC | EER | Accuracy | Fake detection rate | Real specificity |
|---|---|---|---|---|---|---|
| Deepfakes | in-distribution | 0.997 ± 0.004 | 0.023 ± 0.023 | 0.970 ± 0.013 | 0.939 ± 0.026 | 1.000 ± 0.000 |
| FaceSwap | unseen method | 0.261 ± 0.072 | 0.705 ± 0.060 | 0.500 ± 0.000 | 0.000 ± 0.000 | 1.000 ± 0.000 |
| NeuralTextures | unseen method | 0.794 ± 0.015 | 0.303 ± 0.026 | 0.576 ± 0.013 | 0.152 ± 0.026 | 1.000 ± 0.000 |
