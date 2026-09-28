# Per-method detection: b0_vidsplit

Seeds [42, 43, 44]. Trained on Deepfakes only, tested on test-split identities (22 real + 22 fake videos per method; one video = 2.3 pp). Clip-level.

| Fake method | Role | AUC-ROC | EER | Accuracy | Fake detection rate | Real specificity |
|---|---|---|---|---|---|---|
| Deepfakes | in-distribution | 1.000 ± 0.000 | 0.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 | 1.000 ± 0.000 |
| FaceSwap | unseen method | 0.332 ± 0.035 | 0.644 ± 0.057 | 0.500 ± 0.000 | 0.000 ± 0.000 | 1.000 ± 0.000 |
| NeuralTextures | unseen method | 0.773 ± 0.044 | 0.303 ± 0.095 | 0.614 ± 0.000 | 0.227 ± 0.000 | 1.000 ± 0.000 |
