# Per-method detection: mm_b4reg_vidsplit

Seeds [42, 43, 44]. Trained on all three methods (one per identity pair); tested on test-split identities unseen in training. NOT zero-shot. Test-split identities only (22 real + 22 fake videos per method; one video = 2.3 pp). Clip-level.

| Fake method | Role | AUC-ROC | EER | Accuracy | Fake detection rate | Real specificity |
|---|---|---|---|---|---|---|
| Deepfakes | seen method, unseen identities | 0.994 ± 0.009 | 0.030 ± 0.026 | 0.970 ± 0.013 | 0.970 ± 0.026 | 0.970 ± 0.026 |
| FaceSwap | seen method, unseen identities | 0.906 ± 0.041 | 0.159 ± 0.068 | 0.788 ± 0.047 | 0.606 ± 0.114 | 0.970 ± 0.026 |
| NeuralTextures | seen method, unseen identities | 0.908 ± 0.025 | 0.129 ± 0.047 | 0.818 ± 0.000 | 0.667 ± 0.026 | 0.970 ± 0.026 |
