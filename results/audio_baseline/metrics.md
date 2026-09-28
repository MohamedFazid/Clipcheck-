# Audio front-end baseline: MFCC + SVM vs wav2vec2 + SVM

Identical protocol and classifier class; only the front end differs. Full dataset: True. n_eval = 71237.

| Front end | Eval EER | Eval accuracy | Dev EER | C |
|---|---|---|---|---|
| MFCC + delta + delta-delta (120-d) | 10.25% | 0.9320 | 7.79% | 0.1 |
| wav2vec2-base, frozen (768-d) | 3.96% | 0.9765 | 1.11% | 10.0 |

## False alarms on genuine, unseen-corpus speech (n = 100 clips, lower is better)

| Front end | False-alarm rate at P(spoof) >= 0.5 | at own eval-EER threshold | Median P(spoof) |
|---|---|---|---|
| MFCC + SVM | 1.000 | 1.000 | 1.000 |
| wav2vec2 + SVM | 1.000 | 1.000 | 0.983 |
