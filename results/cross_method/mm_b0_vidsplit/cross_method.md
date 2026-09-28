# Per-method detection: mm_b0_vidsplit

Seeds [42, 43, 44]. Trained on all three methods (one per identity pair); tested on test-split identities unseen in training. NOT zero-shot. Test-split identities only (22 real + 22 fake videos per method; one video = 2.3 pp). Clip-level.

| Fake method | Role | AUC-ROC | EER | Accuracy | Fake detection rate | Real specificity |
|---|---|---|---|---|---|---|
| Deepfakes | seen method, unseen identities | 0.966 ± 0.009 | 0.098 ± 0.047 | 0.909 ± 0.039 | 0.909 ± 0.079 | 0.909 ± 0.000 |
| FaceSwap | seen method, unseen identities | 0.897 ± 0.016 | 0.159 ± 0.039 | 0.788 ± 0.013 | 0.667 ± 0.026 | 0.909 ± 0.000 |
| NeuralTextures | seen method, unseen identities | 0.931 ± 0.013 | 0.152 ± 0.013 | 0.841 ± 0.039 | 0.773 ± 0.079 | 0.909 ± 0.000 |
