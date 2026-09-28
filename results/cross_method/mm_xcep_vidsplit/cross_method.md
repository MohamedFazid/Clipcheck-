# Per-method detection: mm_xcep_vidsplit

Seeds [42, 43, 44]. Trained on all three methods (one per identity pair); tested on test-split identities unseen in training. NOT zero-shot. Test-split identities only (22 real + 22 fake videos per method; one video = 2.3 pp). Clip-level.

| Fake method | Role | AUC-ROC | EER | Accuracy | Fake detection rate | Real specificity |
|---|---|---|---|---|---|---|
| Deepfakes | seen method, unseen identities | 0.990 ± 0.010 | 0.023 ± 0.023 | 0.939 ± 0.013 | 0.909 ± 0.045 | 0.970 ± 0.026 |
| FaceSwap | seen method, unseen identities | 0.992 ± 0.009 | 0.053 ± 0.035 | 0.924 ± 0.035 | 0.879 ± 0.052 | 0.970 ± 0.026 |
| NeuralTextures | seen method, unseen identities | 0.946 ± 0.024 | 0.121 ± 0.035 | 0.894 ± 0.035 | 0.818 ± 0.045 | 0.970 ± 0.026 |
