# Cross-validation: cv5_xcep_mm

5 folds, seed 42. Every video (400) is scored once by a model that never saw its identity. Clip level (mean P(fake) over a video's crops). 95% intervals: cluster bootstrap over 100 identity groups, 2000 resamples.

## Pooled out-of-fold

| Metric | Value | 95% CI |
|---|---|---|
| AUC-ROC | 0.918 | 0.891 to 0.942 |
| Accuracy at 0.5 | 82.8% | 79.2% to 86.2% |
| Real specificity | 93.0% | 88.5% to 97.0% |
| Fake detection (all) | 72.5% | 66.0% to 79.0% |
| EER | 17.0% | 12.8% to 20.2% |
| Brier score | 0.123 | 0.103 to 0.146 |
| ECE (10 bins) | 0.078 | 0.057 to 0.118 |
| Deepfakes: fakes detected | 77.9% | 68.0% to 87.7% |
| Deepfakes: AUC vs real | 0.941 | 0.906 to 0.971 |
| FaceSwap: fakes detected | 77.3% | 66.2% to 87.5% |
| FaceSwap: AUC vs real | 0.941 | 0.912 to 0.967 |
| NeuralTextures: fakes detected | 62.1% | 50.0% to 73.3% |
| NeuralTextures: AUC vs real | 0.870 | 0.820 to 0.915 |

## Per fold (variation caused by the data partition)

| Fold | Videos | AUC | Accuracy | Real specificity | Fake detection |
|---|---|---|---|---|---|
| 0 | 80 | 0.850 | 75.0% | 80.0% | 70.0% |
| 1 | 80 | 0.952 | 87.5% | 100.0% | 75.0% |
| 2 | 80 | 0.944 | 83.8% | 92.5% | 75.0% |
| 3 | 80 | 0.933 | 85.0% | 92.5% | 77.5% |
| 4 | 80 | 0.941 | 82.5% | 100.0% | 65.0% |
| **mean ± std** | | 0.924 ± 0.042 | 82.8 ± 4.7% | 93.0 ± 8.2% | 72.5 ± 5.0% |
