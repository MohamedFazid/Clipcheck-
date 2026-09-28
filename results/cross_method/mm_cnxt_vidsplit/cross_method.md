# Per-method detection: mm_cnxt_vidsplit

Seeds [42, 43, 44]. Trained on all three methods (one per identity pair); tested on test-split identities unseen in training. NOT zero-shot. Test-split identities only (22 real + 22 fake videos per method; one video = 2.3 pp). Clip-level.

| Fake method | Role | AUC-ROC | EER | Accuracy | Fake detection rate | Real specificity |
|---|---|---|---|---|---|---|
| Deepfakes | seen method, unseen identities | 0.988 ± 0.007 | 0.083 ± 0.052 | 0.932 ± 0.023 | 0.955 ± 0.045 | 0.909 ± 0.000 |
| FaceSwap | seen method, unseen identities | 0.970 ± 0.017 | 0.106 ± 0.026 | 0.894 ± 0.035 | 0.879 ± 0.069 | 0.909 ± 0.000 |
| NeuralTextures | seen method, unseen identities | 0.897 ± 0.055 | 0.182 ± 0.045 | 0.803 ± 0.035 | 0.697 ± 0.069 | 0.909 ± 0.000 |
