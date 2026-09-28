# Per-method detection: r50_vidsplit

Seeds [42, 43, 44]. Trained on Deepfakes only, tested on test-split identities (22 real + 22 fake videos per method; one video = 2.3 pp). Clip-level.

| Fake method | Role | AUC-ROC | EER | Accuracy | Fake detection rate | Real specificity |
|---|---|---|---|---|---|---|
| Deepfakes | in-distribution | 1.000 ± 0.000 | 0.000 ± 0.000 | 0.992 ± 0.013 | 1.000 ± 0.000 | 0.985 ± 0.026 |
| FaceSwap | unseen method | 0.191 ± 0.048 | 0.735 ± 0.086 | 0.492 ± 0.013 | 0.000 ± 0.000 | 0.985 ± 0.026 |
| NeuralTextures | unseen method | 0.774 ± 0.020 | 0.303 ± 0.026 | 0.568 ± 0.000 | 0.152 ± 0.026 | 0.985 ± 0.026 |
