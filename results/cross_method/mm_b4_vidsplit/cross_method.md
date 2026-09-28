# Per-method detection: mm_b4_vidsplit

Seeds [42, 43, 44]. Trained on all three methods (one per identity pair); tested on test-split identities unseen in training. NOT zero-shot. Test-split identities only (22 real + 22 fake videos per method; one video = 2.3 pp). Clip-level.

| Fake method | Role | AUC-ROC | EER | Accuracy | Fake detection rate | Real specificity |
|---|---|---|---|---|---|---|
| Deepfakes | seen method, unseen identities | 0.993 ± 0.005 | 0.030 ± 0.013 | 0.962 ± 0.013 | 0.939 ± 0.026 | 0.985 ± 0.026 |
| FaceSwap | seen method, unseen identities | 0.897 ± 0.029 | 0.242 ± 0.047 | 0.795 ± 0.023 | 0.606 ± 0.069 | 0.985 ± 0.026 |
| NeuralTextures | seen method, unseen identities | 0.897 ± 0.019 | 0.121 ± 0.035 | 0.856 ± 0.035 | 0.727 ± 0.079 | 0.985 ± 0.026 |
