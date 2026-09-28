# Per-method detection: mm_r50_vidsplit

Seeds [42, 43, 44]. Trained on all three methods (one per identity pair); tested on test-split identities unseen in training. NOT zero-shot. Test-split identities only (22 real + 22 fake videos per method; one video = 2.3 pp). Clip-level.

| Fake method | Role | AUC-ROC | EER | Accuracy | Fake detection rate | Real specificity |
|---|---|---|---|---|---|---|
| Deepfakes | seen method, unseen identities | 0.979 ± 0.007 | 0.083 ± 0.013 | 0.902 ± 0.035 | 0.924 ± 0.026 | 0.879 ± 0.052 |
| FaceSwap | seen method, unseen identities | 0.973 ± 0.009 | 0.106 ± 0.047 | 0.886 ± 0.045 | 0.894 ± 0.052 | 0.879 ± 0.052 |
| NeuralTextures | seen method, unseen identities | 0.905 ± 0.030 | 0.129 ± 0.035 | 0.788 ± 0.035 | 0.697 ± 0.026 | 0.879 ± 0.052 |
