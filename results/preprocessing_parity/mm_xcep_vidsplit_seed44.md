# Preprocessing parity: mm_xcep_vidsplit seed 44 (legacy_xception)

88 test-split videos (0 dropped for no detected face). A = stored JPEG crops (training/evaluation path), B = the app's in-memory path, C = B's crops JPEG round-tripped.

| Path | AUC (all) | Accuracy at 0.5 | Mean P(fake) on real | FaceSwap detected | NeuralTextures detected | Deepfakes detected |
|---|---|---|---|---|---|---|
| A stored JPEG | 0.986 | 0.909 | 0.075 | 0.91 | 0.86 | 0.86 |
| B app (in memory) | 0.989 | 0.943 | 0.145 | 0.91 | 0.95 | 1.00 |
| C app crops + JPEG | 0.988 | 0.898 | 0.046 | 0.91 | 0.82 | 0.86 |

| Comparison | Mean abs diff in clip P(fake) | Max abs diff | Pearson r | Verdict flips at 0.5 |
|---|---|---|---|---|
| A vs B (everything) | 0.0978 | 0.709 | 0.9300 | 7 of 88 |
| B vs C (JPEG only) | 0.1054 | 0.729 | 0.9174 | 8 of 88 |
| A vs C (sampling only) | 0.0522 | 0.294 | 0.9791 | 1 of 88 |
