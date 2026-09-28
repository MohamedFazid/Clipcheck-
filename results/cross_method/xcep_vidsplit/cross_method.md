# Per-method detection: xcep_vidsplit

Seeds [42, 43, 44]. Trained on Deepfakes only, tested on test-split identities (22 real + 22 fake videos per method; one video = 2.3 pp). Clip-level.

| Fake method | Role | AUC-ROC | EER | Accuracy | Fake detection rate | Real specificity |
|---|---|---|---|---|---|---|
| Deepfakes | in-distribution | 0.999 ± 0.002 | 0.008 ± 0.013 | 0.992 ± 0.013 | 0.985 ± 0.026 | 1.000 ± 0.000 |
| FaceSwap | unseen method | 0.268 ± 0.008 | 0.697 ± 0.026 | 0.500 ± 0.000 | 0.000 ± 0.000 | 1.000 ± 0.000 |
| NeuralTextures | unseen method | 0.769 ± 0.018 | 0.356 ± 0.035 | 0.583 ± 0.069 | 0.167 ± 0.139 | 1.000 ± 0.000 |
