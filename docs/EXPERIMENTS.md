# Experiment ledger

One row per experiment. Started 2026-09-19. Rows marked **(retroactive)** were
reconstructed from `DEV_LOG.md`, `results/` and file timestamps, not logged at
the time. Live run events (start/done/fail) are appended to
`results/logs/events.log` by `scripts/run_cell.sh`. There is no git repository,
so "code state" is the date of the scripts; see LESSONS.md L11.

**Splits**
- **split v1** (SUPERSEDED, leaky): frame-level `random_split`, seed 42,
  6052/756/758 crops. Verified 100% of test videos and 100% of val videos also
  had frames in train. Do not quote any number produced on it.
- **split v2** (current): `utils.grouped_video_split`, identity-disjoint, seed 42,
  6072/736/758 crops from 320/36/44 videos. Frozen in
  `data_splits/split_v2_identity_grouped.json` (sha256 prefix `d34c8e7a759f`).

**Metric levels.** Video-level = one mean-aggregated P(fake) per held-out video
(the unit the app reports). Frame-level = per crop, pseudo-replicated (about 19
correlated crops per video), secondary. Only frame-level existed before split v2,
so old-vs-new comparisons must be frame-to-frame.

## A. Video branch (EfficientNet-B4, FF++ c23, Deepfakes method only)

| ID | Tag | Split | Recipe | Seeds | Frame acc | Frame EER | Overfit gap | Status |
|---|---|---|---|---|---|---|---|---|
| V0 (retro) | none (PPR prototype, results/metrics.json) | v1 | aug bug present | 1 | 96.17% (F1 in file 0.9601) | n/a | n/a | SUPERSEDED |
| V1 (retro) | `` (baseline) | v1 | aug bug present, no reg | 42-44 | 96.39 ± 1.12pp | 3.65% | 5.17pp | SUPERSEDED (leaky) |
| V2 (retro) | `aug` | v1 | aug fixed | 42-44 | 97.67 ± 0.30pp | 2.03% | 1.95pp | SUPERSEDED (leaky); served by app until replaced |
| V3 (retro) | `reg` | v1 | aug + dropout 0.3, LS 0.1, ES patience 3 | 42-44 | 96.57 ± 0.66pp | 3.43% | 0.63pp | SUPERSEDED (leaky) |
| V4 | `base_vidsplit` | v2 | no augmentation | 42-44 | 86.81 ± 0.58pp | 12.58 ± 0.27% | 9.49 ± 0.31pp | DONE |
| V5 | `aug_vidsplit` | v2 | augmentation on | 42-44 | 89.93 ± 0.99pp | 9.81 ± 1.76% | 7.07 ± 0.15pp | DONE |
| V6 | `reg_vidsplit` | v2 | aug + dropout 0.3, LS 0.1, ES patience 3 | 42-44 | 88.30 ± 1.80pp | 11.61 ± 1.56% | 6.15 ± 0.75pp | DONE (early stopping never triggered in any seed) |

Video-level on split v2 (n=44 videos; one video = 2.27pp):
V4, V5 and V6 are all 96.97 ± 1.31%. V4 and V5 are identical per
seed, so video-level cannot separate them at n=44; use frame-level and the gap.
Details: `results/summary/{base,aug,reg}_vidsplit/metrics_summary.md` and
`results/summary/variant_comparison_vidsplit.md`.

**Decision D1 (2026-09-19, validation evidence only): ship the augmentation recipe,
`aug_vidsplit`, seed 43.** Mean validation accuracy at each variant's saved checkpoint:
aug 92.30%, baseline 90.72%, regularised 90.40% (regularised val loss is not comparable,
label smoothing inflates it). Test frame-level agrees (89.93 vs 86.81 vs 88.30). Seed 43 has
the best validation accuracy (0.9253) and lowest validation loss (0.2247) among the aug seeds.
Regularisation lowers the overfitting gap (6.15 vs 7.07pp) but does not improve accuracy, so
it is reported as no clear benefit, now on trustworthy data. Video-level cannot separate the
three variants at n=44.

Backbone bake-off (RUNNING, launched detached 2026-09-19 21:03 via
`scripts/queue_bakeoff_video.sh`; identical recipe to V5, only `--arch` varies, seeds 42-44):

| ID | Tag | timm arch | Status |
|---|---|---|---|
| V8a | `b0_vidsplit` | efficientnet_b0 | DONE |
| V8b | `r50_vidsplit` | resnet50 | DONE |
| V8c | `xcep_vidsplit` | legacy_xception (the FF++ benchmark baseline) | DONE |
| V8d | `cnxt_vidsplit` | convnext_tiny | DONE: frame acc 96.26 ± 0.46, AUC 0.9952, gap 2.44 pp, val acc 97.78 ± 0.31 (best single-method backbone in-distribution; fails cross-method like the rest: FaceSwap AUC 0.27, NT 0.71) |

Output: `results/summary/bakeoff_video_vidsplit.md` (EfficientNet-B4 = V5 is the incumbent row).

**Bake-off finding (2026-09-20, ConvNeXt pending): the PPR incumbent EfficientNet-B4 is the WORST of
the four finished backbones on this data.** Same recipe, 3 seeds, split v2:

| Backbone | Frame acc | Frame AUC | Frame EER | Mean val acc | Overfit gap | Video acc (n=44) |
|---|---|---|---|---|---|---|
| EfficientNet-B4 (incumbent) | 89.93 ± 0.99 | 0.9722 | 9.81% | 92.30% | 7.07 ± 0.15 pp | 96.97 ± 1.31 |
| EfficientNet-B0 | 94.64 ± 1.56 | 0.9902 | 5.19% | 94.70% | 5.81 ± 2.58 pp | 100.0 ± 0.0 |
| ResNet-50 | 94.02 ± 0.08 | 0.9905 | 5.45% | 98.28% | 1.46 ± 0.51 pp | 99.24 ± 1.31 |
| Xception | 94.72 ± 0.40 | 0.9930 | 4.75% | 96.97% | 3.37 ± 0.70 pp | 99.24 ± 1.31 |

Caveat to state in the report: one shared recipe (lr 1e-4, 10 epochs, 224 px input) may favour
some architectures, and B4's native input is larger than 224. Video-level n=44 saturates, so use
frame-level and validation evidence. The literature argument for B4 (Pokroy and Egorov, DFDC) did
not transfer to FF++ under this protocol.

**Cross-method zero-shot (V9) for the other backbones: identical failure.** FaceSwap AUC B0 0.33,
ResNet-50 0.19, Xception 0.27; NeuralTextures AUC 0.77 to 0.78; unseen fakes detected 0 to 23%
(`results/cross_method/<tag>/`). So the generalisation failure is a property of single-method
training data, not of the architecture.

Planned (not started):
- V7: 5-fold identity-grouped cross-validation on the chosen model, so all 400 videos are
  scored once while unseen.
- V10 (DONE 2026-09-20 14:32): multi-method training (Deepfakes + FaceSwap + NeuralTextures, one method per
  identity pair, class-balanced via `frames_multi/`, `scripts/build_multimethod_frames.py`, assignment in
  `data_splits/multimethod_assignment_v1.json`). Tags `mm_r50_vidsplit`, `mm_xcep_vidsplit`, `mm_b0_vidsplit`.
  Splits come from the frozen manifest (`utils.split_from_manifest`).

  **Per-method detection on unseen identities (clip level, 22 real + 22 fake videos per method; multi-method models
  saw all three methods, so this is NOT zero-shot; single-method rows show the zero-shot failure for comparison):**

| Model (trained on) | Deepfakes AUC | FaceSwap AUC | NeuralTextures AUC | FaceSwap detected | NT detected | Real specificity |
|---|---|---|---|---|---|---|
| ConvNeXt-Tiny (Deepfakes only) | 1.000 | 0.266 | 0.714 | 0% | 9% | 100% |
| Xception (Deepfakes only) | 0.999 | 0.268 | 0.769 | 0% | 17% | 100% |
| **Xception, multi-method** | 0.990 ± 0.010 | **0.992 ± 0.009** | **0.946 ± 0.024** | **88%** | **82%** | 97% |
| ResNet-50, multi-method | 0.979 ± 0.007 | 0.973 ± 0.009 | 0.905 ± 0.030 | 89% | 70% | 88% |
| EfficientNet-B0, multi-method | 0.966 ± 0.009 | 0.897 ± 0.016 | 0.931 ± 0.013 | 67% | 77% | 91% |

  Multi-method training fixes the coverage failure (FaceSwap AUC 0.27 -> 0.99, detection 0% -> 88% for Xception)
  at a small cost on Deepfakes (detection 100% -> 91%). Aggregate metrics on the mixed test set are LOWER than the
  single-method numbers (Xception-mm: frame acc 88.27 ± 2.04, clip acc 96.21 ± 3.47, val acc 86.28, overfit gap
  13.66 pp; ResNet-50-mm: 80.52 / 87.12, gap 21.0; B0-mm: 76.87 / 84.09, gap 19.4) because the mixed problem is
  harder. Do NOT compare those numbers with single-method rows: the test compositions differ. Compare per-method
  detection instead. Xception is the clear multi-method winner on validation (86.28 vs 80.34 B0 vs 76.76 R50).
- **V11 (DONE 2026-09-20 19:06, `scripts/queue_mm_convnext.sh`): multi-method ConvNeXt-Tiny (`mm_cnxt_vidsplit`, seeds 42 to 44),
  same recipe.** Best validation accuracy per seed 87.69 / 89.53 / 89.39 (mean 88.87 ± 1.02, above Xception-mm's 86.28). Clip
  accuracy on the 44 test videos 93.18 ± 2.27%, clip AUC 0.980. Per-method detection (clip level, 22 fakes per method): Deepfakes
  95.5%, FaceSwap 87.9% (AUC 0.970), NeuralTextures 69.7% (AUC 0.897), real specificity 90.9%. Versus Xception-mm: NeuralTextures
  detection and real specificity are worse (81.8% and 97.0%). Source: `results/cross_method/mm_cnxt_vidsplit/cross_method.md`.
- **V12 (DONE 2026-09-20 20:15, `scripts/queue_celebdf.sh`): Celeb-DF-v2 zero-shot for the finalists** (official 518 videos, 178
  real + 340 fake, best-validation seed, training-style JPEG round trip per D4). Output `results/cross_dataset/celebdf_v2__<tag>/`.

  | Model (seed) | Accuracy at 0.5 | AUC | EER | Fake detection | Real specificity |
  |---|---|---|---|---|---|
  | Xception, multi-method (44) | 59.1% | 0.696 | 37.1% | 52.6% | 71.3% |
  | ConvNeXt-Tiny, multi-method (43) | 58.9% | 0.671 | 39.6% | 56.2% | 64.0% |
  | ConvNeXt-Tiny, single-method (44) | 40.3% | 0.650 | 39.4% | 11.5% | 95.5% |

  All three are below the 70 to 75% the literature reports for FF++-trained detectors (Khan and Dang-Nguyen, 2023). Real videos
  are falsely flagged in 29 to 36% of cases for the multi-method models. The single-method model detects 11.5% of Celeb-DF fakes,
  which supports the multi-method decision. The old model's result stays in `results/cross_dataset/celebdf_v2/` (61.2%, produced
  without the D4 preprocessing, so not like-for-like) and is never overwritten.
- **V13 (DONE 2026-09-20 21:06)** is in section J. **V14 (mm_b4_vidsplit)** is below.

**Decision D2 (PROVISIONAL, 2026-09-20): ship a multi-method model, not a single-method one.** A single-method model
misses whole manipulation families (FaceSwap 0%), which is disqualifying for an app that claims to detect
manipulated video, and the PPR scope statement (swap and reenactment deepfakes) would not be true. Final choice is made by the
frozen rule below; select seed by validation accuracy.

**V14 (QUEUED 2026-09-20 22:3x): multi-method EfficientNet-B4 (`mm_b4_vidsplit`).** The PPR and Draft Report promise
EfficientNet-B4. B4 was the worst of five backbones on the SINGLE-method data (V8), but it was never trained on the multi-method
data that the shipping candidates use, so it has not been tested fairly on the problem the app actually solves. Same recipe as
V10 and V11 (`--arch efficientnet_b4 --frames-dir frames_multi --epochs 10`, seeds 42 to 44, 224 px input; only the
architecture changes). Caveat to report either way: one shared recipe and 224 px input (B4's native input is larger) may
disadvantage B4. Script `scripts/queue_mm_b4.sh`.

**FROZEN SHIP RULE for D2 (written 2026-09-20 22:29 +0800, BEFORE any `mm_b4_vidsplit` result exists; do not edit after
results appear, add a dated note instead).** Reference model R = Xception, multi-method (`mm_xcep_vidsplit`; mean validation
accuracy 86.28%; per-method detection FaceSwap 87.9%, NeuralTextures 81.8%, Deepfakes 90.9%; real specificity 97.0%, all from
`results/numbers.md`). Candidate C = EfficientNet-B4, multi-method (the PPR architecture).
1. **Ship C** if BOTH hold: (a) C's mean validation accuracy (best epoch, 3 seeds) is within 2.0 pp of R's; (b) C's mean FaceSwap
   detection, NeuralTextures detection and real specificity (clip level, same test videos) are each no more than 2 test videos
   below R's (one video = 4.5 pp with 22 videos per class per method, so 9.1 pp).
2. **Otherwise ship the better of Xception-mm and ConvNeXt-mm** under criteria set in advance (validation
   accuracy, per-method detection and real specificity, Celeb-DF-v2, latency, calibration), and record the deviation from the PPR
   architecture (register D-C) with the measured evidence. On current numbers Xception-mm and ConvNeXt-mm are mixed
   (ConvNeXt-mm has higher validation accuracy, 88.87% vs 86.28%; Xception-mm has better NeuralTextures detection, 81.8% vs
   69.7%, and real specificity, 97.0% vs 90.9%), so that comparison is made and recorded at that point as a dated note here.
3. Seed choice: best validation accuracy, never test. Celeb-DF-v2, latency and calibration are recorded for the report and
   used only to break a tie in step 2, never to override step 1.
4. If step 1 is met, the PPR architecture ships and no architectural deviation is registered.

**DATED NOTE 2026-09-20 23:05 (addition to the frozen rule; the rule text above is unchanged).** A second B4 candidate, C2 =
regularised B4 multi-method (`mm_b4reg_vidsplit`, `scripts/queue_mm_b4_reg.sh`, starts automatically after the plain run), is
judged by EXACTLY the same step 1 (a) and (b) against the same reference R; no threshold is loosened. Reason: the PPR (Phase 2, Ch4.5)
and Draft Report (Ch4.3) promise B4 WITH dropout 0.3, label smoothing 0.1 and early stopping (patience 3, validation loss), so the
plain recipe is not the complete promised version. If C or C2 meets step 1, B4 ships (the one with the higher mean validation
accuracy if both do); if neither does, step 2 applies. **Disclosures for the report:** (1) B4 therefore gets two attempts, a mild
multiple-comparison advantage that the thresholds do not offset; (2) this note was written while plain B4-mm seed 42 was at epoch 8
(validation accuracy 74.0%, other two seeds not started), so the partial plain result was already visible, although the regularised
recipe was proposed at 23:00 on the PPR's own wording; (3) with early stopping `train.py` selects the checkpoint by validation LOSS,
which decision D5 found costs accuracy on multi-method models (3.8 pp for Xception-mm); that is part of the promised recipe being
tested and will be reported as such. Prior evidence: on single-method data the same regularisation lowered the overfitting gap (6.15
vs 7.07 pp) but did not improve accuracy (88.30 vs 89.93% frame level; V6), and early stopping never triggered.
**Measurement detail for rule (a) (fixed 23:05, before any C2 result):** the validation accuracy used is the one AT THE SAVED
CHECKPOINT. For the plain run that is the epoch with the best validation accuracy; for the regularised run it is the epoch with the
lowest validation loss (the epoch `train.py` saved), read from each seed's `history.json`, NOT the maximum validation accuracy over
epochs (`train_config.json` `best_val_acc` and `build_numbers.py` report that maximum, which is more generous for the regularised
run and must not be used for this rule).

**RESULT, step 1 applied to the plain B4 multi-method run C (2026-09-21 00:16; the regularised run C2 started training at 00:15:21, before this note was written, and no C2 result exists):
NOT MET.** Reference R = Xception-mm; tolerance for rule (b) is exactly 2 test videos (2/22 = 9.09 pp).

| Check | R (Xception-mm) | C (B4-mm plain) | Difference | Result |
|---|---|---|---|---|
| (a) mean validation accuracy at the saved epoch (per seed: R 86.70 / 84.02 / 88.12; C 75.39 / 75.95 / 72.28) | 86.28% | 74.54% | -11.74 pp (limit -2.0) | FAIL |
| (b) FaceSwap fakes detected | 87.9% | 60.6% | -27.3 pp (limit -9.09) | FAIL |
| (b) NeuralTextures fakes detected | 81.8% | 72.7% | -9.09 pp (exactly 2 videos, allowed) | PASS |
| (b) real videos kept real | 97.0% | 98.5% | +1.5 pp | PASS |
| Deepfakes fakes detected (not part of the rule) | 90.9% | 93.9% | +3.0 pp | n/a |

Every B4 seed saved its last epoch (10) as best and validation accuracy was still creeping up (75.4, 76.0, 72.3), so the model is under-trained or
under-fitted on validation while the training accuracy is 95 to 96%: a large generalisation gap, not a lack of capacity. The result is consistent
across the three seeds (the validation spread is about 2 pp against a 12 pp shortfall), so more seeds would not change it. Caveats to report: one shared
recipe (lr 1e-4, 10 epochs, 224 px input, no regularisation) and B4's native input is larger than 224; a different recipe could behave differently.
Decision status: the frozen rule now depends on C2 (regularised B4-mm); if C2 also fails step 1, step 2 applies.

**RESULT, step 1 applied to the regularised B4 multi-method run C2 (2026-09-21 01:46, all three seeds complete): NOT MET.**
Per seed, validation accuracy at the SAVED (lowest-validation-loss) epoch: seed 42 epoch 10 = 70.30, seed 43 epoch 10 = 71.71,
seed 44 epoch 9 = 67.75; mean **69.92%**. Early stopping never triggered in any seed (patience 3 on validation loss), the same as
the single-method regularised runs (V6).

| Check | R (Xception-mm) | C2 (B4-mm regularised) | Difference | Result |
|---|---|---|---|---|
| (a) mean validation accuracy at the saved epoch | 86.28% | 69.92% | -16.36 pp (limit -2.0) | FAIL |
| (b) FaceSwap fakes detected | 87.9% | 60.6% | -27.27 pp (limit -9.09) | FAIL |
| (b) NeuralTextures fakes detected | 81.8% | 66.7% | -15.15 pp | FAIL |
| (b) real videos kept real | 97.0% | 97.0% | 0.00 pp | PASS |
| Deepfakes fakes detected (not part of the rule) | 90.9% | 97.0% | +6.06 pp | n/a |

Regularisation did what it is supposed to do and did not help: the train-minus-validation gap fell (seed 42: 17.7 pp regularised
against 20.4 pp plain) while validation accuracy fell with it (70.30 against 75.39 for the same seed). That reproduces the
single-method finding (V6: gap 6.15 vs 7.07 pp, accuracy 88.30 vs 89.93) on the harder multi-method problem, so B4's weakness here
is not under-regularisation. **Both B4 candidates failed step 1, so step 2 applies and an architectural deviation from the PPR is
registered (D-C) with this measured evidence.**

**DECISION D2 FINAL (2026-09-21 01:47): ship Xception, multi-method (`mm_xcep_vidsplit`), seed 44.** Step 2 comparison of the two
remaining candidates on the criteria set in advance:

| Criterion | Xception-mm | ConvNeXt-mm | Better |
|---|---|---|---|
| 1. Mean validation accuracy (seed choice basis) | 86.28% | **88.87%** | ConvNeXt (+2.59 pp) |
| 2. NeuralTextures detected | **81.8%** | 69.7% | Xception (+12.1 pp, about 2.7 test videos) |
| 2. FaceSwap detected | 87.9% | 87.9% | tie |
| 2. Deepfakes detected | 90.9% | **95.5%** | ConvNeXt (+4.5 pp) |
| 2. Real videos kept real (false-alarm rate) | **97.0%** | 90.9% | Xception (+6.1 pp) |
| 3. Celeb-DF-v2 AUC / real videos kept | **0.696 / 71.3%** | 0.671 / 64.0% | Xception |
| 4. Cross-validation (400 videos, out-of-fold) | **measured: 82.8% (79.2 to 86.2)** | not measured | Xception |
| 6. Calibration | **measured: already calibrated, ships at T = 1.0 (D3)** | not measured | Xception |
| 5. Latency | not measured | not measured | tie (measured after shipping) |
| Clip accuracy on the 44-video test split (secondary) | 96.21 ± 3.47% | 93.18 ± 2.27% | Xception |
| Overfitting gap at the final epoch (secondary) | 13.7 pp | 11.7 pp | ConvNeXt |

ConvNeXt-mm wins criterion 1, which is the criterion the rule uses for SEED choice, and it overfits slightly less. Xception-mm wins
criteria 2 (on the two that matter most for an accusation tool: the hardest manipulation method and the false-alarm rate on genuine
video), 3, 4 and 6. **Reasoning for the choice: for a tool that accuses a video of being manipulated, wrongly flagging genuine
content is the more damaging error, and Xception-mm flags 3.0% of genuine test videos against 9.1% for ConvNeXt-mm (and 28.7%
against 36.0% on Celeb-DF-v2). It is also the only candidate with a cross-validated accuracy interval and a calibration check, so
shipping it means shipping the model the project can actually characterise.** Honest counter-argument to state in the report:
ConvNeXt-mm has the higher validation accuracy, so on criterion 1 alone the choice would go the other way; the decision is a
trade-off made on error type and on evidence coverage, not a clean win, and 44 test videos cannot separate the two on aggregate
accuracy (one video = 2.3 pp).

Seed: **44**, the best validation accuracy among the Xception-mm seeds (88.12 against 86.70 and 84.02), selected on validation only.
It is also the seed already used for the Celeb-DF-v2 run (V12), the calibration check (G/D3) and the preprocessing-parity check
(H/D4), so those results apply to the shipped checkpoint without re-running them.



**V9 (DONE, 2026-09-19): zero-shot cross-method test of `aug_vidsplit` (3 seeds).** Trained on
Deepfakes only. Tested on test-split identities only (22 real + 22 fake videos per method; one
video = 2.3 pp), clip level. `results/cross_method/aug_vidsplit/cross_method.md`. Script:
`scripts/eval_cross_method.py`. Sanity check: the Deepfakes row reproduces `evaluate.py`'s video-level
numbers exactly.

| Fake method | Role | AUC-ROC | Fake detection rate | Real specificity |
|---|---|---|---|---|
| Deepfakes | in-distribution | 0.997 ± 0.004 | 0.939 ± 0.026 | 1.000 |
| FaceSwap | unseen method | **0.261 ± 0.072** | **0.000** | 1.000 |
| NeuralTextures | unseen method | 0.794 ± 0.015 | 0.152 ± 0.026 | 1.000 |

Mean per-crop P(fake): real 0.084, Deepfakes 0.875, NeuralTextures 0.264, FaceSwap 0.019. FaceSwap AUC
below 0.5 means FaceSwap crops score as more real than genuine ones. Crops verified visually (valid
224x224 faces, same extraction as training). Consistent across seeds (0.27, 0.18, 0.33), so systematic.
The model detects Deepfakes-method artefacts, not manipulation in general.

## B. Audio branch

| ID | What | Data | Result | Status |
|---|---|---|---|---|
| A0 (retro) | wav2vec2-base (frozen) mean-pooled 768-d + RBF SVM, 400/class pilot | ASVspoof 2019 LA | eval EER 8.25% | SUPERSEDED by A1 |
| A1 (retro) | same, full dataset (train 25,380 / dev 24,844 / eval 71,237), C=10, seed 42 | ASVspoof 2019 LA | eval EER 3.96%, acc 97.65%, dev EER 1.11% | DONE (`results/audio_branch/metrics.json`) |
| A2 (2026-09-20) | MFCC(20)+delta+delta-delta, mean+std pooled (120-d) + RBF SVM, identical protocol and classifier class (`scripts/eval_audio_baseline.py`) | ASVspoof 2019 LA, full | eval EER **10.25%**, acc 93.20%, dev EER 7.79% (C=0.1) vs wav2vec2 3.96% / 97.65% / 1.11% | DONE (`results/audio_baseline/metrics.md`) |
| A3 (2026-09-20) | False alarms on GENUINE unseen-corpus speech, both front ends, same 100 clips (DeepfakeTIMIT original audio, higher_quality, random sample) | DeepfakeTIMIT | **both flag 100%** as spoof (at P>=0.5 and at own eval-EER threshold); median P(spoof) 1.000 (MFCC) and 0.983 (wav2vec2) | DONE. Extends the 20-clip hybrid finding to 100 clips and shows it is not specific to wav2vec2 |

| A4 (2026-09-20 23:20) | Full metric set for the wav2vec2 + SVM branch from cached eval embeddings (`scripts/eval_audio_metrics.py`, CPU only; PPR 3.6 promises accuracy, F1 and AUC-ROC per branch) | ASVspoof 2019 LA eval, 7,355 bona fide + 63,882 spoof | AUC-ROC 0.9937, EER 3.96%; at the SVM boundary: accuracy 0.9765, balanced accuracy 0.9485, F1(spoof) 0.9869, F1(bona fide) 0.8892, bona fide recall 0.9133; at P(fake) >= 0.5 (what the app and fusion use): accuracy 0.9707, balanced accuracy 0.9569, F1(bona fide) 0.8689, bona fide recall 0.9394. Recomputed EER and accuracy match `metrics.json` exactly. **Always answering "spoof" scores 89.7% accuracy** | DONE (`results/audio_branch/extra_metrics.json`, `numbers.md`) |

**A4 consequence for fusion: RESOLVED 2026-09-21 02:5x (user decision).** `fusion._resolve_audio_accuracy()` now weights the audio
branch by its **balanced accuracy at P(fake) >= 0.5, 0.9569**, read from `results/audio_branch/extra_metrics.json`, not the plain
0.9765 from `metrics.json`. Reason: the eval partition is 7,355 bona fide against 63,882 spoof, so always answering "spoof" scores
89.7% and plain accuracy is close to that trivial baseline, which would overstate the audio branch against a video branch measured
on a balanced set. The operating point chosen is the one the app actually uses (probability >= 0.5), not the SVM's own decision
boundary (balanced accuracy 0.9485 there). Plain accuracy remains the fallback if `extra_metrics.json` is absent, and the source
string says which was used. Fusion weights are now **video 0.464 / audio 0.536** (from 0.459 / 0.541). Pinned by two tests in
`tests/test_fusion.py`.

| A5 (2026-09-21 15:28) | **Is the unseen-corpus failure caused by the CODEC or by the CORPUS?** Re-encoded ASVspoof's OWN eval clips (100 bona fide + 100 spoof, seed 42, same speakers and labels) through AAC 128k/64k and MP3 128k/64k, then re-scored with the shipped SVM, so the codec is the only thing that changed (`scripts/audio_channel_diagnostic.py`) | ASVspoof 2019 LA eval, re-encoded | Bona fide false alarms: clean **5.0%** -> worst codec **7.0%** (+2.0 pp). EER 4.00% clean against 3.50 to 5.00% across codecs; mean P(spoof) on genuine speech 0.065 clean against 0.083 to 0.092 | DONE (`results/audio_channel_diagnostic/diagnostic.json`) |

**A5 verdict: the codec is NOT the cause, so no codec-augmentation retrain was done.** Lossy compression moves the branch by
about 2 percentage points, against the 100% false-alarm rate on DeepfakeTIMIT (A3): it accounts for roughly 2 points of a
95-point gap. The failure is therefore CORPUS mismatch, different speakers, microphones, rooms and recording chains, not the
transport format. The fix that would actually work is more diverse bona fide training data (multiple corpora), which is out of
scope at this stage and is reported as a limitation instead. This is a negative result that saved a day of pointless retraining,
and it is worth reporting as such: the obvious engineering fix was tested cheaply and rejected on evidence before being built.
Practical consequence for users: audio arriving inside a normal MP4 is not itself a problem; audio from an unfamiliar recording
setup is.

| A6 (2026-09-21 16:0x) | **wav2vec2 vs WavLM, the SSL-encoder comparison the project never had** (`scripts/compare_audio_encoders.py`). Identical balanced subsample (train 1500 / dev 500 / eval 1500, seed 42), same decoder, same SVM back end, same C grid selected on dev, eval scored once, both encoders embedded fresh in ONE process so no library version can differ. Both base-sized, both pretrained on the same 960 h LibriSpeech | ASVspoof 2019 LA subsample | **wav2vec2 eval EER 6.60%, AUC 0.9852, balanced acc 93.33%, bona fide false alarms 6.7%. WavLM eval EER 7.20%, AUC 0.9767, balanced acc 91.87%, false alarms 9.9%.** Both selected C=10. On unseen-corpus genuine speech BOTH still flag **100% of 60 clips** (median P(spoof) wav2vec2 0.920, WavLM 0.981) | DONE (`results/audio_encoder_comparison/comparison.json`) |

**A6 conclusions, stated at the strength the evidence supports.**
1. **The shipped encoder is validated, modestly.** wav2vec2 is ahead of WavLM on every metric measured, but by a small margin
   (0.60 pp EER, about 9 clips of 1500). No confidence interval was computed, so the honest claim is "wav2vec2 is not worse and
   the literature-based choice is confirmed on this project's own data", NOT "wav2vec2 is significantly better". The comparison's
   value is that the choice is now tested rather than assumed, which is what the module brief asks for.
2. **A different SSL encoder does NOT fix the real problem.** The branch's serious failure is that it calls genuine speech from an
   unfamiliar corpus spoofed (A3, and the cause of the 0% modality implication in H2). WavLM fails identically, 100% of 60 clips,
   and is if anything more confident while wrong (median P(spoof) 0.981 against 0.920). Together with A5, which ruled out the
   codec, two candidate explanations have now been tested and rejected: the failure is neither the transport format nor the choice
   of encoder. It is the training corpus, and the fix is multi-corpus bona fide data.
3. Both encoders chose the same C and both improved monotonically across the C grid, so neither was starved of tuning.

**These are SUBSAMPLE figures and must never be quoted beside the full-dataset 3.96% EER** in `results/audio_branch/metrics.json`,
which is measured on 71,237 clips. Untested and worth naming as future work: wavlm-base-plus and wavlm-large, both pretrained on
much more data than either model here.

Findings: wav2vec2 wins in-distribution (2.6x lower EER), which is the measured answer to "why
wav2vec2" (also supported by Tak et al., 2022). But BOTH front ends call 100% of genuine unseen-corpus
speech spoof (A3), so the audio branch is a single-corpus detector whichever front end is used.
Candidate mitigations, not done: diverse bona fide sources in training, codec/noise augmentation.
Report as a limitation, not as a solved problem.

## C. Fusion and end-to-end evaluations

| ID | What | Video model used | Result | Status |
|---|---|---|---|---|
| F1 (retro) | 4-condition, self-built fallback set (80 clips, FF++ video + ASVspoof audio) | V2 (leaky) | video-only 100%, audio-only 97.5%, naive fusion 78.5%, disagreement-aware 97.5%; modality implication 100% on both single-modality categories | SUPERSEDED by F3 |
| F2 (retro) | threshold T grid search on F1 scores | V2 (leaky) | raw optimum 0.55, chose T=0.30 | SUPERSEDED by F4 |
| H1 (retro) | hybrid: fallback set with FVRA replaced by paired DeepfakeTIMIT | V2 (leaky) | 91.25 / 72.15 / 93.67 / 98.73%; FVRA video implication 0% | SUPERSEDED by H2 |
| X1 (retro) | Celeb-DF-v2 zero-shot, official test list, 518 videos | V2 (leaky) | acc 61.2%, AUC 0.682, EER 38.65% | SUPERSEDED by V12 |
| **F3** (2026-09-21 02:05) | 4-condition, self-built fallback set, **T = 0.35** | **SHIPPED** Xception-mm seed 44 | **video-only 90.0, audio-only 97.5, naive fusion 73.4, disagreement-aware 97.5%**; implication RVFA 100%, FVRA 95%; false disagreement RVRA 5.3%, FVFA 30% | DONE (`results/fallback_eval_shipped/`) |
| **F4** (2026-09-21 01:55) | threshold T grid search on F3's per-clip scores | SHIPPED | interior optimum **T = 0.35** (F1 0.907, precision 0.848, recall 0.975); flat 0.20 to 0.60 | DONE (`results/fallback_eval_shipped/threshold_tuning.json`) |
| **H2** (2026-09-21 02:08) | hybrid set (FVRA = paired DeepfakeTIMIT), T = 0.35 | SHIPPED | 76.2 / 72.2 / 83.5 / **98.7%**; **FVRA implication 0%** (see the H2 analysis below) | DONE (`results/hybrid_eval_shipped/`) |
| **L2** (2026-09-21 02:02) | per-stage latency, **all 8 stages measured** for the first time | SHIPPED | **9.0 s warm per clip** (video 5.95, Llama 3 2.23, wav2vec2 0.71, decode 0.09, VAD 0.04, SVM 0.007, fusion and screen ~0.001), cold start 3.84 s, M2 Pro / MPS | DONE (`results/latency/latency.json`) |
| **L3** (2026-09-25 11:29) | latency RE-MEASURED after the out-of-domain gate (O1) and explanation timing (T1) were added; benchmark extended to time them with the app's own functions (stages 1b, 1c, 5b; explanation now receives the real moment windows); 5 timed runs, same clip; plus a new end-to-end timing of the live app on the 8 featured examples (3 runs each after a warm-up) | SHIPPED | **7.28 s warm per clip** (video 5.29, Llama 3 1.38, wav2vec2 0.40, face OOD check 0.11, moment windows 0.04, VAD 0.04, decode 0.03, the rest under 0.01), cold start 4.12 s. The two additions cost about 0.15 s; the lower total than L2 is session-to-session variation (mainly a shorter Llama generation, 1.38 against 2.23 s), not a speed-up. End to end in the app: 1.3 to 8.0 s per clip, median 4.4 s (longest: the 13 s FaceForensics++ clips with 20 face frames) | DONE (`results/latency/latency.json`, `results/latency/app_end_to_end.json`; L2 archived in `results/latency/archive/`) |

**F3 CAVEAT, found 2026-09-21 16:15 while writing `docs/decisions/video_backbone_decision.md`: the four-condition set is NOT held out
for the video branch.** `scripts/build_fallback_eval_set.py` (written 13 Sep) samples at random from ALL FaceForensics++ videos; the
identity-disjoint split only appeared on 19 Sep and the set was never re-checked against it. Against `split_v2_identity_grouped.json` and
`multimethod_assignment_v1.json`: **57 of 80 clips use a video from the shipped model's training split, 8 from validation, 15 from test.** By
category (train / val / test): real+real 14/2/4, real video+fake audio 19/1/0, fake video+real audio 9/3/8, fake+fake 15/2/3. Of the 40 fake
videos, 8 are the exact manipulated video the model trained on; most others share an identity pair it trained on through a different method.
The audio side IS held out (ASVspoof eval partition). The superseded B4 had seen every one of these videos through the leaking split.
Consequences: (1) the standard-versus-disagreement-aware comparison stays valid, because both rules receive identical scores; (2) absolute
figures, above all video-only 90.0% and the modality-naming rates, are optimistic **[PARTLY RETRACTED 2026-09-21 17:40, see F5: video-only accuracy was NOT optimistic, 92.5% held-out against 90.0%; the naming rate for fake video + real audio did fall, 95% to 75%]**; (3) this explains the fake+fake false-disagreement rise
(5% old model, 30% shipped: the old model had memorised every Deepfakes video) **[RETRACTED 2026-09-21 17:40, see F5: on held-out video the fake+fake false-disagreement rate is 10%, not 30%; the 30% was a small-sample result, 6 of 20 against 2 of 20, not memorisation]**; (4) it explains H2: the only genuinely unseen video in any
fusion evaluation (DeepfakeTIMIT) is exactly where the video branch fails. **Fix proposed, not run: rebuild the set from test-split identities
(22 real, 66 fakes across three methods) and re-run F3 and F4.** Until then the report must call F3 in-distribution for the video branch. **[DONE 2026-09-21 17:40 as F5 below.]**

**F5 (2026-09-21 17:40): the four-condition evaluation re-run on HELD-OUT video (`eval_heldout/`, `scripts/build_heldout_eval_set.py`,
results in `results/heldout_eval_shipped/`). Same shipped model, same T = 0.35, same audio pipeline; only the video source differs.**
Construction: video only from the TEST partition of the frozen identity-disjoint split (22 real videos; 22 test identity pairs x 3 methods =
66 fakes, of which 40 used, 14 Deepfakes / 13 FaceSwap / 13 NeuralTextures, disjoint between FVRA and FVFA); audio from the ASVspoof eval
partition as before. Verified independently: all 80 videos have role "test", none of the 22 identities appears in any train or validation video
(`tests/test_heldout_eval_manifest.py`, in CI, which would have failed 65 of the 80 clips of the older set). Limitation: only 22 real test
videos exist, so RVRA and RVFA share 18 of 20 videos and differ only in audio. 4 clips have no audio score (speech gate), so 76 enter fusion.

| | Older set (57/80 videos in training) | HELD-OUT set (0/80) |
|---|---|---|
| 1 video-only accuracy | 90.0% | **92.5%** |
| 2 audio-only accuracy | 97.5% | **92.1%** |
| 3 standard (naive) fusion | 73.4% | **76.3%** |
| 4 disagreement-aware fusion | 97.5% | **94.7%** |
| Advantage of 4 over 3 (paired bootstrap, 20,000 resamples) | +24.1 pp, 95% CI [+13.9, +34.2], n = 79 | **+18.4 pp, 95% CI [+7.9, +28.9], n = 76** |
| Correctly named AUDIO (real video + fake audio) | 100% | 100% |
| Correctly named VIDEO (fake video + real audio) | 95% | **75%** (15 of 20) |
| Wrongly reported as disagreement, real + real | 5.3% | 11.1% |
| Wrongly reported as disagreement, fake + fake | 30.0% | **10.0%** |
| T sweep optimum (F1 on the partial-manipulation class) | 0.35 (F1 0.907, n = 79) | **0.35 (F1 0.909, n = 76)** |

**What holds.** The research question's claim survives held-out video: disagreement-aware fusion beats standard fusion by 18.4 points, with an
interval that excludes zero (16 clips only the disagreement-aware rule got right, 2 only the standard rule). The threshold T = 0.35 is
independently re-confirmed as the optimum, so nothing in the app changed. Video-only accuracy did not fall.

**What changed, and the honest reading.** The two intervals overlap heavily (+13.9 to +34.2 against +7.9 to +28.9), so the data do not show that
the older set inflated the advantage. What is measurable: naming the video on fake video + real audio fell from 95% to 75%. Of the 5 held-out
misses, the video branch scored the manipulated video below 0.5 in 4 (three are NeuralTextures, whose held-out detection is 9 of 13 = 69%, against
13 of 14 for Deepfakes and 12 of 13 for FaceSwap), and the audio branch false-alarmed on genuine speech (P above 0.6) in 3: the two failure sources
found in H2. Video branch alone on the 40 held-out fakes: 34 detected = 85.0%; on the 40 real videos: all 40 kept real.

**Where the older set was NOT optimistic, and why (my own analysis, checked against the manifests).** Its 8 video-only errors were all fakes (real
videos were 40 of 40 correct in both sets). Splitting its 40 fakes (all Deepfakes-method) by what the model had seen: the 8 whose exact manipulated
video was in training were all detected (8 of 8, the only place memorisation could help); the 16 whose identity was trained on but under a DIFFERENT
method were detected only 10 of 16 = 62%; the 16 whose identity was never in training were detected 14 of 16 = 88%. Familiar identities were harder,
not easier. Mechanism not established (a plausible hypothesis: the model learned that identity as genuine from its real videos); with n = 16 per
group this is an observation, not a finding.

**Graded picture for the report, in order of distance from the training distribution.** Naming the implicated modality on fake video + genuine
speech: 95% (older set, identities mostly seen) -> 75% (held-out FF++ identities, all three methods) -> 0% (DeepfakeTIMIT, a different dataset, H2).
Unseen identities cost a modest amount; a different dataset removes the ability entirely. This is a cleaner statement of the project's boundary
than H2 alone.

**Standing caveats for the report:** still a self-built set, not FakeAVCeleb; the audio side (ASVspoof eval) was always held out; only 22 real
videos; all intervals are slightly narrow because clips are resampled independently. Corrections made elsewhere: the F3 caveat claims above,
`docs/decisions/video_backbone_decision.md` section 11.

**F3 is the project's core evidence, now on the shipped model: disagreement-aware fusion beats naive fusion by 24.1 points
(97.5% against 73.4%) on exactly the cases the research question is about.** Retuning T from 0.30 to 0.35 raised condition 4 from
96.2% to 97.5% and halved the false-disagreement rate on genuine clips (10.5% to 5.3%) without changing modality implication.
Two caveats travel with it: FVFA false disagreement is 30% (when both modalities are manipulated the branches often differ by
more than T, so a full deepfake is reported as partial), and the video branch scores 90.0% here against the superseded model's
100%, the expected cost of covering three manipulation methods instead of one.

**H2 at T = 0.35: disagreement-aware fusion 98.7%, the highest figure anywhere in the project, with FVRA modality implication
still 0%.** The threshold change improved the headline and did nothing for the failure, which is the point: the analysis below
explains why that number must never be quoted on its own.

Note: `fusion.py` `VIDEO_ACCURACY_DEFAULT = 0.9639` is hardcoded from V1 and must be
updated by hand when the shipped model changes (not auto-resolved like audio).

**H2 (2026-09-21 01:57): hybrid four-condition re-run on the SHIPPED model, and the finding that most qualifies the project's
own claim.** The hybrid set replaces the FVRA category with genuinely paired DeepfakeTIMIT clips (manipulated video, original
unaltered audio), so that category is cross-dataset for BOTH branches at once. Conditions at the tuned T = 0.35: video-only 76.2%, audio-only 72.2%, standard fusion 83.5%, **disagreement-aware fusion 98.7%**.

Taken alone the last number looks like the project's strongest result. It is not, and the report must say why. On the 20 FVRA
clips, where the video is manipulated and the speech is genuine:

| What should happen | What happened |
|---|---|
| video branch scores the manipulated video high | mean P(video_fake) = **0.305**; only **6 of 20** reach 0.5 (FF++-trained model, DeepfakeTIMIT face swaps, unseen generator) |
| audio branch scores the genuine speech low | mean P(audio_fake) = **0.983** on every clip (the single-corpus false alarm, A3) |
| system flags PARTIAL_MANIPULATION and implicates VIDEO | flags PARTIAL_MANIPULATION on 16 of 20 and implicates **AUDIO** on all 16; **FVRA modality implication = 0%** |

So the clip is reported as "not authentic" for the wrong reason: the verdict is driven by a false alarm on genuine audio, not by
detecting the manipulated video, and the one thing this project adds over a binary detector, naming the implicated modality, is
wrong in every case. **Accuracy of 98.7% in condition 4 on this set is therefore not evidence that the disagreement mechanism
works; it is two out-of-distribution failures pointing the same way.** The same 0% was seen with the superseded model (H1), so it
is a property of the branches' training coverage, not of one checkpoint.

Consequence, stated plainly for Chapter 5 and 6: the disagreement mechanism identifies the correct modality only while both
branches are operating within their training distributions (in-distribution fallback set: RVFA 100%, FVRA 95%). Out of
distribution it still produces a plausible-looking verdict, which is the more dangerous failure mode for a forensic tool. Fixing
it needs broader training coverage on both branches (multi-corpus audio, more manipulation families and datasets on video), not a
change to the fusion rule. This is the honest boundary of the project's contribution and should be reported next to the headline
result, not in a footnote.

**F6 (2026-09-22 01:52): the four-condition evaluation on an INDEPENDENT published set, LAV-DF (Cai et al., 2022), test split
(`eval_lavdf/`, `scripts/build_lavdf_eval_set.py`, `scripts/carve_lavdf_parts.py`, results in `results/lavdf_eval_shipped/`). Same shipped
model, T = 0.35, same audio pipeline; run detached, 200 clips in 211 s.** Sampling rule frozen before any model was run on these clips (in the
builder's docstring): test-split clips wholly inside part .006 (2,531), 50 per category by LAV-DF's own `modify_video` / `modify_audio` labels,
`random.Random("42-<category>")`, no filter on duration, speech, face or score. Real generators (SV2TTS audio, Wav2Lip video) on VoxCeleb2
speakers; faces 224x224; fake segments average 0.65 s inside clips of 4.2 to 19.4 s. Not FakeAVCeleb.

**Result: the system has no discriminating power on this set, in either branch.** Whole-set numbers: video-only 43.0%, audio-only 50.0%, standard
fusion 72.0%, disagreement-aware 75.0%. **75.0% is exactly the accuracy of predicting FAKE for every clip** (150 of 200 clips have at least one
manipulated channel), so the fusion figures carry no information. Per branch:

| Branch | Measured |
|---|---|
| Video | AUC 0.377 (below chance); flags 80.0% of REAL-video clips and 66.0% of FAKE-video clips as fake; mean P(video_fake) 0.77 on RVRA |
| Audio | AUC 0.522 (chance); flags 100% of genuine-audio clips AND 100% of spoofed-audio clips; mean P(audio_fake) 0.989 to 0.995 in every category |

By category (disagreement-aware verdict): RVRA 0 of 50 correct (41 FAKE, 9 PARTIAL); RVFA, FVRA, FVFA 50 of 50 "correct" only because any non-REAL verdict
counts as fake. Modality naming: audio named on real video + fake audio 42%, video named on fake video + real audio 0%. False disagreement 18%
(RVRA), 56% (FVFA). Bootstrap of the fusion advantage: +3.0 pp, 95% CI [+0.5, +6.0] (`advantage_bootstrap.json`), **an artefact: the rule labels
PARTIAL as fake, which pushes predictions toward the always-fake baseline, not evidence for the research question. Do not quote it as support.**

What it means. The audio result extends A3, A5 and A6: the SVM saturates on speech outside ASVspoof (here it also scores every genuinely spoofed
clip at about 0.99, so it is uninformative, not merely over-sensitive). The video result is new: the branch that scored 92.5% on held-out FF++ (F5)
is below chance on LAV-DF. **The cause is untested.** Candidates: 224x224 low-resolution faces, Wav2Lip (edits only the mouth region, not a
training method), VoxCeleb2's in-the-wild conditions, or clip-level dilution of 0.65 s fakes. A cheap separating test (downscale FF++ clips to
224x224 and re-score) has not been run. For the report this is a cross-dataset generalisation failure of both branches, consistent with Khan and
Dang-Nguyen (2023) and with Celeb-DF-v2 at 59.1%, and it bounds the project's claim: the disagreement result (F5) holds on FF++ video with ASVspoof
audio; it does not transfer to LAV-DF.

**F6 addendum (2026-09-22 02:13): resolution does NOT explain the LAV-DF video failure** (`scripts/lowres_diagnostic.py`, `results/lowres_diagnostic/diagnostic.json`).
Decision rule written in the script before running: "resolution explains it" if the AUC of the LAV-DF-like version falls more than 0.15 below the original.
The same 59 held-out FF++ videos F5 used (the diagnostic could score 59 of 62: three videos of identity 420 had no face detected after the crop),
scored through the app's own path, unchanged versus cropped to a per-video square around the face (1.45 x the face box), scaled to 224x224 and re-encoded
at 100 kbps H.264 (LAV-DF's own bitrate is about 93 kbps): original accuracy 91.5%, AUC 0.981, real flagged fake 0%,
fakes flagged 86.8%; LAV-DF-like accuracy 86.4%, AUC 0.977, real flagged fake 0%, fakes flagged 78.9%.
AUC drop 0.004. So close-up framing, 224x224 size and heavy compression cost only about 5 points of accuracy and 0.13 of mean fake score, and
create no false alarms on real FF++ faces. **The failure must come from something else: VoxCeleb2's real faces are out of distribution for a model trained on
FF++ (80% of LAV-DF real-video clips flagged fake), Wav2Lip is an unseen manipulation, or the labels are diluted (only 5 to 13% of the duration of a "fake" LAV-DF clip is
manipulated: median fake-period fraction 0.13 RVFA, 0.05 FVRA, 0.12 FVFA, from `eval_lavdf/manifest.json`).** These three have not been separated. Audio is not
affected by image resolution at all; its failure is the corpus mismatch of A3/A5/A6 plus the same label dilution.

**F7 (2026-09-22 02:44): audio SVM trained with VoxCeleb2 speech added, EXPERIMENT ONLY, not shipped** (`scripts/audio_lavdf_experiment.py`, `results/audio_lavdf_experiment/`).
Only the SVM's training data changes; frozen wav2vec2, the RBF recipe and C = 10.0 are the shipped ones. Training clips: 400 + 400 from the LAV-DF DEV split (seeded);
scoring: the 200 `eval_lavdf/` TEST clips (100 genuine-audio, 100 fake-audio), never used for fitting, C or a threshold; speakers are disjoint between LAV-DF splits.
Rule written before running: the corpus explains the failure if B2 cuts genuine false alarms on LAV-DF test below 50% with ASVspoof EER within 1.0 pp of S0.

| Variant | Train bona fide / spoof | Genuine flagged fake | Faked flagged fake | LAV-DF AUC | LAV-DF EER | LAV-DF balanced acc | ASVspoof eval EER | ASVspoof balanced acc |
|---|---|---|---|---|---|---|---|---|
| S0 | 2580 / 22800 | 100% | 100% | 0.522 | 48.5% | 0.50 | 3.96% | 95.69% |
| B2 | 2980 / 22800 | 4% | 4% | 0.478 | 55.5% | 0.50 | 4.07% | 95.69% |
| B1 | 2980 / 23200 | 29% | 87% | 0.898 | 16.5% | 0.79 | 4.77% | 94.69% |

S0 = shipped recipe (control; reproduces F6). B2 = S0 + 400 genuine LAV-DF clips as bona fide. B1 = B2 + 400 fake-audio LAV-DF clips labelled spoof (whole-clip labels).
**Reading.** (1) The pre-registered rule is met (B2: 100% to 4% false alarms; ASVspoof EER +0.11 pp), so **the false alarms are a training-corpus problem, as A3/A5/A6 concluded.**
(2) **B2 alone does not detect anything**: it moves every VoxCeleb2 clip, fake or not, to "genuine" (fake clips flagged 4%, AUC 0.478, balanced accuracy 0.50). The rule
measured false alarms only, and meeting it must not be reported as "the audio branch now works". (3) B1 separates the classes on LAV-DF (AUC 0.898, EER 16.5%, 87% of
fake-audio clips and 29% of genuine clips flagged) **but this is in-domain adaptation: the training fakes come from the same generator (SV2TTS) and corpus as the test fakes,
so it says nothing about unseen deepfake audio, and shortcut cues (clip processing artefacts rather than cloned speech) are not excluded.** It costs ASVspoof EER +0.82 pp
(3.96% to 4.77%) and balanced accuracy -1.0 pp. (4) The 87%/29% figures come from whole-clip labels on clips that are only 5 to 13% cloned, so the encoder's pooled embedding does carry the signal. Not run:
fusion with B1/B2 audio (the video branch still fails on LAV-DF, F6, so a fusion figure would not be interpretable). Shipping B1 or B2 would be a deviation from the PPR's ASVspoof-trained SVM (register entry
needed) and is not proposed: the fix that generalises needs several bona fide corpora AND held-out corpora to test on.

## D. Explanation layer and app

| ID | What | Result | Status |
|---|---|---|---|
| E1 (retro) | 16-case pilot, found sub-0.5 scores described as "fake"; fixed by `explain.assess()` | pilot done | rating CSVs BLANK, unscored |
| E2 | full 50-case human evaluation (Draft Ch 3.6 rubric: factual grounding, score accuracy, absence of hallucination) | 50 cases regenerated 2026-09-22 17:xx with real anomaly timing (T1 addendum; screen rejection 24/50 after two screen bugs fixed); rater form `results/explanation_eval_full/rating_form.html` (built by `scripts/build_rating_form.py`, rebuilt from the corrected `cases.json`: offline, no account, shows only the eight structured-input fields (now including video anomaly timing) and the explanation, never clip ids, ground truth or checks; 2 worked examples from clips outside the 50, one demonstrating the timing rule; downloads the exact CSV the scorer reads; 4 data-free tests); scorer `scripts/score_explanation_eval.py` (weighted Cohen's Kappa, refuses incomplete sheets; 5 tests) | **DONE 2026-09-26 03:09**: both sheets returned (rater 1 saved 02:42, rater 2 03:06), 50/50 complete, values 0 to 2, not copies (differ on 21 of 50 cases); filed unchanged in `results/explanation_eval_full/raw_as_downloaded/` (sha256), blank templates kept in `blank_templates/`. `score_explanation_eval.py` (`scored_report.json`): means rater 1 / rater 2: factual grounding 1.70 / 1.50, score accuracy 1.46 / 1.36, absence of hallucination 1.72 / 1.72; exact agreement 80% / 82% / 96%; quadratic-weighted kappa 0.63 / 0.81 / 0.93; no 2-point disagreements. `compare_screen_with_raters.py` (`screen_vs_raters.json`, exploratory, definitions chosen after seeing the ratings): PARTIAL texts mean total 4.3 / 4.0 of 6 against REAL 5.5 / 5.1 and FAKE 5.6 / 5.6; both raters faulted grounding in 15 of 27 PARTIAL texts and 0 of 23 REAL + FAKE; all 15 were also rejected by the app's screen; the screen passed 26 texts, none faulted by both raters (4 received a 0 from one rater, all on score accuracy by rater 2); the screen rejected 9 texts the raters did not both fault. Raters (user's statement, 26 Sep): rater 1 = the developer (project author); rater 2 = a friend, no ML background. So only one rater is independent of the project; stated as a limitation |
| E3 | (removed 2026-09-22 16:22) an automated run of the app's faithfulness check over the 50 packet cases, done 15:5x, was withdrawn so that the explanation evaluation rests on the two human raters only. Its script and result file were deleted. | n/a | REMOVED |
| U1 | user testing, TWO rounds (v1 current UI, then v2 redesign; 3-5 participants each) | protocol rewritten 2026-09-24 17:06; two-round design, v1 frozen (`docs/user_testing/ui_v1_snapshot/`, `screenshots/v1/`), survey form (SUS + tasks + features) and scorer built 18:34; short form (T2, T3, T7, T8 + SUS) and heuristic evaluation of v1 (`docs/user_testing/heuristic_evaluation_v1.md`, developer-evaluator, 14 findings, not user testing) 19:04 | **Round 1: 4 short sessions run 24 Sep (P1 to P4), PROVISIONAL**: form carry-over defect found (P2/P3 share 29 answers incl. all SUS); awaiting the facilitator's confirmation, see `docs/user_testing/results/round1_data_quality.md`. **v2 built 21:09** (`docs/user_testing/findings.md`: C1 to C16 traced to sources). **Round 2: 4 short sessions run 25 Sep (P5 to P8), scored 20:14, no carry-over**: SUS 87.5, 87.5, 90.0, 90.0 (median 88.75, against round 1's provisional 60.0); T2 and T3 4 of 4 unaided, all named the video; T7 warning seen by all 4 (2 after a hint) but lowered trust for none (round 1: 3 yes, 1 partly); T3 all 4 would publish the partly-manipulated clip (ambiguous); T8 1 unaided, 3 with a hint. Details and reading: `docs/user_testing/findings.md` Round 2 |
| L1 (retro) | latency benchmark, M2 Pro MPS | about 10 s/clip warm, excluding the SVM stage | re-run after shipping |

**O1 (2026-09-22 03:32): out-of-domain gate, built, evaluated against rules fixed before any result, and shipped in WARNING mode**
(`scripts/ood_gate.py`, `scripts/extract_app_features.py`, `scripts/fit_ood_gates.py`, `scripts/eval_ood_gate.py`; `models/{audio,video}_ood_gate.joblib`;
`results/ood_gate/{fit_report,eval_report}.json`, `per_clip.joblib`). Asked for after F6/F7: stop the app giving confident verdicts on input unlike its training data.

Method. Mahalanobis distance (Ledoit-Wolf shrinkage covariance, standardised features) in each branch's own feature space: the frozen wav2vec2
embedding the SVM reads; the Xception pooled 2048-d features (same forward pass, `analyse_video_file(return_features=True)`, identity of outputs tested).
Fit on each branch's own training data (ASVspoof train 25,380; FF++ train-split crops 5,734), threshold = 97.5th percentile on in-domain data it was not
fitted on (ASVspoof dev 24,844; FF++ validation crops 707); a clip's video distance is the median over its crops. Variant (pooled vs class-conditional,
Lee et al., 2018) chosen on 200 LAV-DF DEV tuning clips: flag rates audio 0.88 / 0.88, video 0.315 / 0.31, so pooled for both (tie rule). Thresholds:
audio 43.1, video 99.9. All other sets were scored once. Celeb-DF was first extracted with a bug (Windows line endings in its list file, so no file opened);
fixed and re-extracted before any evaluation.

Pre-set ship criteria and outcome for WITHHOLDING (a flagged branch's score dropped from fusion):

| Criterion (fixed before results) | Measured | Pass |
|---|---|---|
| (a) in-domain withheld rate per branch <= 5% (eval_heldout + eval_fallback, app path) | video 3/160 = 1.9%; audio 6/155 = 3.9% | yes |
| (b) eval_heldout accuracy falls <= 2 pp | 92.5% to 90.0% (-2.5 pp): RVFA_014 and RVFA_016 went PARTIAL to REAL because their in-domain audio was flagged | **no** |
| (c) LAV-DF test confident wrong verdicts fall | 50 to 48 | yes (barely) |

What withholding did elsewhere: LAV-DF test, video withheld 109/200, audio 185/200; verdicts FAKE 82, INCONCLUSIVE 95, REAL 22, PARTIAL 1; accuracy on answered clips
54.3% (chance level). DeepfakeTIMIT (fake video + genuine unseen speech, 20 clips): audio withheld 20/20 (correctly, it was a false alarm), video 0/20, so the
verdict fell to the video branch, which misses these fakes: 14 confident REAL on fake clips, where the ungated system had been "right" for the wrong reason
(PARTIAL naming audio). Celeb-DF (100, silent): video withheld 12; confident wrong 39 to 32; accuracy on answered 61.0% to 63.6%.

**Decision: withholding is NOT the default** (criterion b failed). **Shipped as WARNING mode** (`DEEPFAKE_OOD_MODE`, default `warn`; `withhold` and `off`
remain available): every score and verdict is unchanged, and a branch whose input is out of domain is flagged with its distance and limit, in the verdict
banner, the branch panel and under the explanation. Warning mode was chosen after these results were seen, which is stated here; it changes no verdict, so
no accuracy figure can move. Measured flag behaviour (same per-clip file): eval_heldout 5/80 clips flagged, none of its 6 wrong verdicts flagged, all 5 flagged
verdicts correct; eval_fallback 4/80, 0 of 2 wrong flagged; **LAV-DF test 199/200 flagged, all 50 wrong verdicts flagged**; DeepfakeTIMIT 20/20; Celeb-DF 12/100
flagged, 7 of 39 wrong flagged, accuracy of flagged verdicts 41.7% against 63.6% unflagged; Veo 3/5 (audio). So the flag marks the LAV-DF failure completely
and costs about 5% false caution in domain; it does not mark most Celeb-DF errors (the video gate flags only 31.5% of LAV-DF dev and 12% of Celeb-DF faces).

Why the video branch cannot be "fixed" on LAV-DF by any gate or threshold (measured on `eval_lavdf/manifest.json` against the app's sampling, 20 crops at
fps//3 frames, i.e. 0 to 6.08 s): in fake-video clips only 5.7% (FVRA) and 11.5% (FVFA) of the sampled crops fall inside a manipulated segment; 42/50 and
46/50 clips have at least one such crop; in 4/50 of each the fake lies wholly after the sampled window. Averaging 20 crops cannot flag a clip where one crop
is fake, even with a perfect frame detector. LAV-DF is a temporal-localisation benchmark; the PPR design is clip-level. The 0.40 video score on
LAVDF_FVRA_000 comes from false alarms on genuine VoxCeleb2 frames, not from detecting the fake.

**F8 (2026-09-22 13:23): does adding genuine VoxCeleb2 faces to the video training data fix the false alarms? Probe, analysis only, nothing shipped.**
Frozen Xception pooled features (the O1 caches), a logistic-regression head (standardised, C = 0.05 fixed, not tuned, class-balanced) standing in for
the classifier head. P0 = head on FF++ train-split crops only; P1 = the same plus 1,825 crops from 100 genuine-video LAV-DF DEV clips (RVRA + RVFA),
labelled real. Test sets never used for fitting: eval_heldout (FF++), eval_lavdf (LAV-DF test), 100 Celeb-DF-v2 test videos, 20 DeepfakeTIMIT fakes.

| Measure | P0 (FF++ only) | P1 (+ genuine VoxCeleb2) |
|---|---|---|
| FF++ held-out clip accuracy / AUC | 92.5% / 0.982 | 90.0% / 0.975 |
| LAV-DF test: genuine faces flagged fake | 80% | **5%** |
| LAV-DF test: fake-video clips flagged | 68% | **0%** |
| Celeb-DF-v2 (unseen) accuracy / AUC; genuine flagged | 60.0% / 0.634; 32% | 54.0% / 0.630; 10% |
| DeepfakeTIMIT fakes (unseen) caught | 30% | 15% |

P0 reproduces the shipped model closely (92.5% held-out, 80% LAV-DF genuine flagged, Celeb-DF about 60%, DeepfakeTIMIT 6 of 20), so the probe is a fair stand-in.
**Reading: adding genuine faces from a new source removes the false alarms on that source but the model then flags nothing from that source, and detects
fewer fakes elsewhere (DeepfakeTIMIT 30% to 15%, Celeb-DF accuracy -6 pp).** It learns which dataset a face comes from, not whether it is manipulated: the
same shortcut as the audio experiment (F7, B2: false alarms 100% to 4%, fakes flagged 4%). A fix that generalises needs real AND manipulated data from several
sources (the PPR's mixed-dataset training, register D-E), evaluated on a source never trained on. Resolution is not the cause (F6 addendum), and every face is
resized to 224 x 224 by MTCNN before the model sees it, training crops included (`scripts/extract_frames.py`), so a higher-resolution dataset would not change the input.

**F9 (2026-09-22 13:27): mixed real AND fake training, probe, analysis only, nothing shipped.** Same frozen-feature probe as F8. P2 = FF++ train crops +
1,825 genuine and 202 lip-synced (Wav2Lip, crops inside LAV-DF fake periods) crops from LAV-DF DEV clips. Against P0 (FF++ only):
FF++ held-out 92.5% to 88.8%; LAV-DF test genuine clips flagged 80% to 10%; frame-level AUC lip-synced vs genuine crops 0.317 to 0.605; LAV-DF fake-video
clips flagged by the app's mean over crops 68% to 6% (by max-crop 95% to 85%, but max-crop also flags 97% to 81% of genuine clips); **Celeb-DF-v2 (unseen)
60.0% to 57.0%, AUC 0.634 to 0.617; DeepfakeTIMIT fakes (unseen) 30% to 20%.** Audio: F7's multi-corpus SVM B1 (ASVspoof + LAV-DF dev) flags 95% of 20
genuine DeepfakeTIMIT clips (shipped: 100%) and 2 of 3 Veo synthetic clips (shipped: 3 of 3).
**Reading: adding a dataset, even with both classes, adapts the model to that dataset and does not improve detection on datasets it has not seen
(both unseen sets got worse, for video and audio).** Caveat: a linear head on frozen features cannot learn new visual cues; full fine-tuning might do
better on Wav2Lip, but these probes give no evidence that it would generalise. Cross-dataset generalisation is the known open problem (Khan and
Dang-Nguyen, 2023); the scale that addresses it (for example DFDC, over 100,000 clips) is outside this project.

## E. Interrupted-run log

- 2026-09-20 22:47 to 22:53: `mm_b4_vidsplit` seed 42 (epoch 5) slowed about 60x by memory pressure caused by test runs that loaded the video model
  and Ollama on the same machine (LESSONS L26). The process was not killed; training numbers are unaffected, only wall-clock time (about 9 minutes).

- 2026-09-19 evening: the terminal session ended twice while the matrix ran as a
  session-attached background job (jobs die with the session). `reg_vidsplit` seed 43
  checkpoints from both killed attempts were moved to `models/runs/_partial/` and
  never evaluated. Runs are now launched detached via `scripts/run_cell.sh`.


**T1 (2026-09-22 16:59): video anomaly timing added to the explanation layer (user request).** The explanation could already say
WHETHER a clip was fake but never WHEN in the clip the video branch's per-frame score was elevated, even though that
real, timestamped data already existed (server.py `_frame_anomalies`, shown in the app's Visual tab). Added a
`video_anomaly_timing` field to the structured input Llama receives (`scripts/explain.py` `format_anomaly_timing`),
with an explicit prompt rule: state WHEN, never WHAT (no model in this pipeline analyses frame content, so any
description of what is visible would be invented). Three honestly distinct states, never conflated: "video not
evaluated", "not available" (no timing data supplied), "no elevated-likelihood windows detected" (checked, genuinely
none). The deterministic template states the same real windows. The faithfulness screen
(`scripts/explain_checks.py`) extended with a `timing` violation type: any m:ss timestamp in the text must be one of
the real windows given, checked the same way the existing `number` check already treats scores, and a peak score
(e.g. "peak 0.95") is now an allowed number even though it differs from the two branch scores. 12 new tests (6 data-
free in `test_explain.py`/`test_explain_checks.py`, 2 real-Ollama in `test_explain.py`, 2 server-integration in
`test_server.py` proving the real per-frame data from a real demo clip reaches the explanation text end to end,
verified against real timestamps on the live server). Full suites re-run: 140 passed (1 skipped) base env, 48 passed
app env. Live check (demo clip 183_253.mp4): Llama wrote "two time windows... from 0:00 to 0:03 and from 0:04 to
0:06", matching the real computed windows exactly, and passed its own faithfulness screen. Additive: the field is
appended to the existing structured input, nothing removed, and with no anomalies supplied the behaviour is
unchanged (verified by the score-grid fuzz test in `test_explain_checks.py`, run without anomalies).

**T1 addendum (2026-09-22 17:41): the 50-case explanation packet regenerated with real timing, and two real screen bugs found and fixed.**
`scripts/explanation_eval.py generate --from-results ... --n 50 --with-timing` re-run (same seed 42, same 50 clips as the 21 Sep
packet) to reflect the T1 addition. Raw run: 31 of 50 (62%) failed the automatic screen, sharply up from the 21 Sep packet's 4 of
50 (8%). Investigated rather than accepted, per LESSONS L29/L30 discipline:

1. **Controlled A/B test (10 PARTIAL_MANIPULATION/video-implicated/video-genuine-leaning score pairs, old 7-field prompt
   reconstructed vs the new 8-field prompt, identical Ollama calls): 2/2 failed under BOTH prompts.** This confirms the dominant
   failure mode, Llama opening with "the video has been partially manipulated" regardless of which branch is actually implicated
   or its direction, is a PRE-EXISTING weakness (same family as the already-documented "video and audio content are partially
   manipulated" conjunctive failure), not caused by adding timing. The 21 Sep packet's low rate reflects which of the 50 clips
   happened to be sampled as PARTIAL_MANIPULATION with this exact pattern, not a difference in the underlying model behaviour.
2. **Two genuine `explain_checks.py` false-positive bugs, found by reading the actual failing texts, both fixed:**
   - The `disagreement` check matched the word "disagree" even inside a denial ("There is no indication that the video and audio
     ... disagree"), which real Llama output started producing once the prompt grew a fifth field to discuss. Fixed with a
     negation-window check (`DISAGREEMENT_NEG_RE`) instead of a raw substring search.
   - The per-branch `direction` check had the same gap for "manipulated"/"fake": missed "no indication that ... are manipulated"
     (a phrase longer than the original 40-char window), "unmanipulated" (a `manipulat` substring inside a prefix-negated word,
     no separate negation cue), and "the likelihood of X being manipulated is very low" (a genuine-supporting claim with no literal
     negation word at all). Fixed with a general negation-window helper (`_unnegated_word_hit`, 70-char window) plus two new
     `NEUTRALISE` phrases for the un- prefix and the low-likelihood quantifier construction.
   Both fixes are general mechanisms, not one-off phrase patches for these exact sentences; 4 new regression tests
   (`tests/test_explain_checks.py`); all 21 explain_checks tests still pass, zero regressions on the 50 stored cases (checked by
   re-scoring all 50 against both the old and the fixed screen and diffing: every case that passed before still passes).
3. Re-scored (not re-generated -- the explanation TEXT is unaffected, only the screen's verdict on it): **24 of 50 (48%) still
   fail.** Breakdown: REAL 1/15 (a genuinely confusing self-contradictory sentence, "no elevated-likelihood windows detected...
   but there are some brief periods where the likelihood of manipulation is higher", a legitimate catch, not a screen bug);
   PARTIAL_MANIPULATION 23/27 (the confirmed pre-existing rote-opener issue in point 1); FAKE 0/8.

**Reading.** The screen bugs were real and are fixed; the remaining 48% is not a regression from T1, it is the SAME
PARTIAL_MANIPULATION weakness this project has documented since the 16-case pilot, now more visible because this particular
sample of 50 clips (fixed seed 42) contains more PARTIAL_MANIPULATION cases of exactly this pattern than the API run that
produced the 21 Sep packet showed. Not attempted (time-boxed): further prompt engineering to reduce the underlying weakness
itself. It remains safety-netted in the live app (faithfulness screen + deterministic template fallback, unaffected by any of
this, D-I) and is now real, honest data for the human evaluation (E2) to compare against. `results/explanation_eval_full_pre_timing_2026-09-21/`
keeps the original 21 Sep packet (nothing was rated on it) for comparison if useful.

**M1 (PRE-REGISTERED 2026-09-24 17:50 +08, before any candidate model was downloaded or run): explanation LLM comparison.**
Why: the brief's 1st-class line asks for evidence of exploring the pre-trained models and choosing on evidence. Video (V8 to V14) and audio (A1 to A6)
have that evidence; the text model (Llama 3 8B, chosen in the PPR) was never compared with anything (B8c never run). The comparison was approved on 24 Sep.

- **Candidates:** `llama3:8b` (incumbent, shipped), `mistral:7b` and `qwen2.5:7b` (both local via Ollama, both Apache 2.0, similar size and
  4-bit quantisation). Reference row, not a candidate: the deterministic template (`explain_checks.explain_template`), the app's fallback.
- **Inputs:** the 50 cases of `results/explanation_eval_full/cases.json` (27 PARTIAL_MANIPULATION, 15 REAL, 8 FAKE), rebuilt through
  `fuse()` + `build_structured_input()` with the stored anomaly windows; the script asserts the rebuilt structured input equals the stored one.
- **Prompt and settings:** the app's `PROMPT_TEMPLATE` and `GEN_OPTIONS` unchanged (temperature 0.2, num_predict 220); seeds 42, 43, 44, so 150
  generations per model. One warm-up generation per model is discarded before timing.
- **Primary metric:** pass rate of the app's own faithfulness screen (`check_faithfulness`, unchanged), over the 150 generations.
- **Secondary:** pass rate on PARTIAL cases and on REAL + FAKE cases; violation types; format compliance with prompt rule 9 (2 to 4 sentences,
  no bullets, headings or preamble such as "Here is"), measured automatically; warm latency mean and 95th percentile per generation.
- **Switch rule (all must hold for a candidate to be recommended over Llama 3 8B):**
  (a) screen pass rate at least 10 pp above Llama 3's;
  (b) on the 23 REAL + FAKE cases, no more than 1 extra failure per seed on average compared with Llama 3;
  (c) format compliance at least 90%;
  (d) mean warm latency no more than 2x Llama 3's;
  (e) I read every failing text of Llama 3 and of the best candidate at seed 42 and label each failure either "genuine" (the text misstates the input) or
  "screen false positive" (the text is faithful and the keyword check misfires), writing the label for each case into the results file; the advantage in (a)
  must still be at least 10 pp after screen false positives are removed from both models.
- **Decision:** if exactly one candidate meets every condition, it is RECOMMENDED; if several do, the one with the highest pass rate after (e). The switch is NOT
  made without the developer's decision, for two reasons. (1) The human rating packet (E2) contains Llama 3 text, so switching would leave the human evaluation
  describing a model the app no longer ships. (2) The PPR names Llama 3, so a switch is a deviation (it would be D-O). If no candidate meets the rule,
  Llama 3 8B stays and M1 is reported as the evidence for keeping it.
- **Unchanged by M1:** app code, prompt, screen, tests, the rating packet and form.
- **Declared caveats (before results):** the screen is keyword-based and its two false-positive fixes (L32) were made on Llama 3 texts, so it may
  favour Llama's phrasing or misfire on other models' phrasing; (e) exists for that reason. The screen is an automatic check, not a human judgment,
  and is never mixed into E2. Three seeds at temperature 0.2 measure sampling variation only, not prompt sensitivity. With 50 cases, one case = 2 pp.

**M1 result (2026-09-24 18:11 +08; `scripts/compare_llms.py`, `results/llm_comparison/summary.{json,md}`, `generations.jsonl`, `adjudication_seed42.json`).**
Downloads: `mistral:7b` (4.4 GB, not the 4.1 GB estimated beforehand) and `qwen2.5:7b` (4.7 GB). 450 generations. Reproduction check:
`llama3:8b` at seed 42 gave text identical to the stored packet in 49 of 50 cases, and the same 24 of 50 screen failures as the T1 addendum.

| Model | Screen pass (150) | PARTIAL pass (81) | REAL + FAKE pass (69) | REAL + FAKE failures per seed (42/43/44) | Format ok | Latency mean / p95 |
|---|---|---|---|---|---|---|
| llama3:8b (shipped) | 50.7% | 16.0% | 91.3% | 1 / 0 / 5 | 96.0% | 2.25 / 3.85 s |
| mistral:7b | 50.0% | 40.7% | 60.9% | 9 / 7 / 11 | 57.3% | 4.10 / 6.70 s |
| qwen2.5:7b | 64.0% | 44.4% | 87.0% | 3 / 1 / 5 | 76.7% | 2.98 / 4.70 s |
| template (reference, 50) | 98.0% | 96.3% | 100.0% | 0 | n/a (writes 5+ sentences by design) | none |

Rule check. **mistral:7b** fails (a) (-0.7 pp), (b) (9 extra REAL + FAKE failures per seed on average) and (c). **qwen2.5:7b**: (a) +13.3 pp, pass;
(b) 3.0 against 2.0 failures per seed, exactly the 1 allowed, pass; **(c) 76.7% against the required 90%, FAIL** (every format failure is a fifth sentence,
35 of 150 texts; no bullets, headings or preambles); (d) 2.98 s against the 4.50 s limit, pass; (e) at seed 42, after the failing texts were read and labelled:
Llama 3, 24 failures = 22 genuine + 2 screen false positives (28 of 50 after removal); Qwen, 19 failures = 8 genuine + 11 screen false positives (42 of 50);
advantage +28 pp, pass. **Decision under the pre-registered rule: no candidate meets every condition, so Llama 3 8B stays** (no deviation).

What the comparison shows, at the strength the evidence supports:
1. Llama 3's weakness is concentrated in one pattern: 20 of its 22 genuine seed-42 failures are the rote opener ("The video has been partially manipulated")
   on PARTIAL cases where the video leans genuine. On REAL + FAKE cases it is the most reliable of the three (91.3%) and the best at following the length rule.
2. Qwen 2.5 7B is the strongest alternative: fewer genuine misstatements on PARTIAL cases (it also produces the opener, 5 of its 8 genuine failures), but it
   overruns the 2 to 4 sentence limit in 23% of texts. It fails the rule on the condition that concerns readability for a non-expert reader, not on faithfulness.
   A length constraint could plausibly fix this, but testing that would be a new, separately registered experiment, not a re-reading of this one.
3. The screen misfires more on other models' wording (11 of Qwen's 19 seed-42 failures against 2 of Llama's 24), as the declared caveat predicted: the
   conjunctive direction rule fires on "since the video and audio branches disagree" (6 texts across both models), the number check reads "0 to 2 seconds"
   as scores (Qwen writes windows in seconds, not m:ss), and the disagreement and direction checks miss "Neither branch disagrees" and "is not manipulated".
   The two Llama false positives (eval-20, eval-36) are the conjunctive misfire, which also affects the live app (a faithful Llama text replaced by the
   template). Not fixed here (M1 changes nothing); proposed as a separate screen fix with regression tests.
4. The labels in (e) are the assistant's reading, not a human rater's, and are not part of E2. Only seed 42 was labelled, as registered.

## F. Code changes that affect results (2026-09-20)

- `scripts/fusion.py`: video accuracy is no longer a hardcoded constant. It is read from
  `models/shipped_model.json` (written when a model is promoted; not created yet) and otherwise falls back to the
  legacy 0.9639 flagged `VIDEO_ACCURACY_IS_MEASURED = False`. New verdict INCONCLUSIVE when neither branch scores;
  audio-only pass-through when video has no score. 13 fusion tests pass. **Server and UI wiring of INCONCLUSIVE
  is NOT done**: `server.py` still returns an error for clips with no detectable face.
- `scripts/explain_checks.py` (+ `tests/test_explain_checks.py`, 9 tests): deterministic no-LLM template
  explainer and an automatic faithfulness screen (numbers derivable from input, per-branch direction, certainty,
  unlisted claims, unevaluated branches, disagreement). The template passes the screen on all 169 score
  combinations tested, and the screen catches the pilot's "0.46 described as fake" failure. The LLM comparison
  (Llama 3 vs template, 50 cases) is NOT run yet (needs Ollama free of GPU contention).
- Base-environment test suite: 66 pass (data split 9, fusion 13, audio branch 4, explain checks 9, explain 14,
  VAD 8, audio SVM 9).
- `scripts/build_numbers.py` writes `results/numbers.json` and `numbers.md` from result files (single source
  of every reported number; legacy leaking-split runs are marked SUPERSEDED; single-seed entries show n=1).
- `scripts/ship_model.py` (dry run by default): promotes `models/runs/<tag>/seed<N>.pth` to `models/best_model.pth`,
  backs up the old one, writes `models/shipped_model.json` (arch, checksum, clip-level accuracy that `fusion.py`
  reads, selection evidence). `video_infer.load_models` now reads the architecture from that file, so shipping a
  non-EfficientNet-B4 model works. Pipeline and server tests still pass (14). NOT yet applied: the app still serves
  the old leaking-split model until D2 is decided.
- CI: `.github/workflows/ci.yml` runs compileall plus `tests/test_frozen_split_manifest.py` (new: checks the
  frozen manifest for video and identity leakage and its own hash, with no dataset), `test_fusion`,
  `test_explain_checks`: 26 tests, verified in a clean virtualenv with only pytest, numpy, requests.

**Code change forced by shipping a non-B4 model (2026-09-21 01:50).** `video_infer.load_models` resolved the architecture from
`models/shipped_model.json` only when `model_path` was None. `server.py` and `eval_fallback_4condition.py` pass the shipped path
explicitly, so with Xception shipped both failed with `RuntimeError: size mismatch` (caught immediately: the four-condition re-run
aborted on its first model load). Fixed with `video_infer.is_shipped_checkpoint()`, which compares real paths, so the shipped
architecture and calibration temperature are used however the path is spelled. Regression test in `tests/test_server.py`
(data-free). LESSONS L27. No result was produced with a wrong model: the failure was a hard load error, not a silent fallback.

## G. Calibration (2026-09-20)

`scripts/calibrate_video.py` fits one temperature T on VALIDATION crops (logits / T) and reports NLL, Brier and binary
ECE before and after on validation crops, test crops and test clips. Results in `results/calibration/<tag>_seed<N>/`
(calibration.json + reliability.png). Seed = best validation accuracy. Dividing logits by T cannot change any decision
(checked: unchanged), so accuracy, AUC and EER are identical.

| Model (best-val seed) | T | Test-crop ECE before -> after | Test NLL before -> after | Verdict |
|---|---|---|---|---|
| Xception, multi-method (44) | 2.81 | 0.048 -> 0.069 | 0.237 -> 0.238 | already calibrated; scaling does not help |
| ResNet-50, multi-method (42) | 1.75 | 0.077 -> 0.067 | 0.458 -> 0.444 | small gain |
| EfficientNet-B0, multi-method (42) | 4.15 | 0.146 -> 0.050 | 0.723 -> 0.434 | large gain (over-confident model) |

**Decision D3: ship the leading candidate (Xception, multi-method) with T = 1.0 (no scaling).** Its test ECE is already
0.048 and its reliability curve is accurate at the extremes (p about 0.01 -> 4% fake; p about 0.99 -> 98% fake). The T
fitted on validation (2.81) over-corrects because the validation set is only 36 videos and harder than the test set
(validation ECE 0.090 vs test 0.048). `ship_model.py --temperature` and `video_infer` support a temperature for any model
that needs one (B0 would). A cross-validated temperature (all 400 videos out-of-fold) would be more stable and is the
proper fix if calibration matters more later. Clip-level ECE uses about 44 videos and is noisy; do not over-read it.

## H. Preprocessing parity: does the app see what the model was evaluated on? (2026-09-20)

`scripts/check_preprocessing_parity.py` scores one model (Xception multi-method, seed 44) on 88 test-split videos
(22 real, plus 22 fakes each from Deepfakes, FaceSwap, NeuralTextures) three ways: **A** stored JPEG crops (training and
`evaluate.py` path, 1 fps), **B** the app's path (about 3 fps, MTCNN, in-memory crops, no JPEG), **C** B's crops JPEG
round-tripped at PIL's default quality (75, how `extract_frames.py` saved training crops). Output:
`results/preprocessing_parity/mm_xcep_vidsplit_seed44.{md,json}`.

| Path | AUC | Real videos falsely flagged | Fakes missed (of 66) | Mean P(fake) on real |
|---|---|---|---|---|
| A stored JPEG (evaluated) | 0.986 | 0 / 22 | 8 | 0.075 |
| B app as it was (in memory) | 0.989 | **2 / 22** | 3 | 0.145 |
| C app + JPEG round trip | 0.988 | 0 / 22 | 9 | 0.046 |

Findings: ranking quality (AUC) is unchanged across paths, but the operating point is not. Skipping the JPEG step makes the
model lean more fake (B vs C: mean clip shift 0.105, max 0.73, 8 of 88 verdicts differ); the sampling difference alone is
small (A vs C: mean 0.052, 1 of 88 verdicts). B made fewer total errors than A here (5 vs 8), but that is not a reason to keep
it: the model, its validation and any threshold belong to the JPEG-crop pipeline, and 88 videos cannot justify an unvalidated
shift.

**Decision D4: inference applies the training-style JPEG round trip** (`video_infer.training_style`, on by default,
`match_training_jpeg=False` disables it). `analyse_video_file` was verified to reproduce path C exactly (and path B with
the option off). Consequence: every evaluation that goes through `analyse_video_file` (Celeb-DF, the four-condition and hybrid
evaluations, latency, the app) now uses the matched preprocessing. The earlier Celeb-DF result of the old model (61.2%) and
the fallback and hybrid results were produced WITHOUT it, which is one more reason they must be re-run. Longer term, training
on lossless crops would remove the mismatch at its source and might recover sensitivity; not done.
`sample_face_crops` was split out of `analyse_video_file` so the check tests the real path; `tests/test_pipeline.py` pins the
JPEG quality to `extract_frames.py`'s default.

## I. Checkpoint criterion: best validation accuracy vs lowest validation loss (2026-09-20, closes plan step 4)

The plan proposed switching the default to lowest validation loss. Computed from the saved training histories (validation
only, no test data, no retraining): choosing by loss gives up validation accuracy, most for the model that matters.

| Model | Mean validation accuracy given up by choosing on loss | Epochs the loss rule picks |
|---|---|---|
| Xception, multi-method (shipping candidate) | **3.8 pp** (2.8, 5.9, 2.5) | 1, 1, 2 (barely trained) |
| ResNet-50, multi-method | 1.4 pp | 3, 7, 3 |
| EfficientNet-B0, multi-method | 0.5 pp | 8, 7, 5 |
| EfficientNet-B4, single-method | 0.5 pp | 9, 4, 10 |
| Xception, single-method | 0.2 pp | 2, 5, 7 |

**Decision D5: keep best validation accuracy as the checkpoint rule (a deliberate deviation from the plan).** Validation
loss rises while accuracy keeps improving because the network becomes over-confident on its errors, so on the harder
multi-method problem the loss rule would pick epoch 1-2 checkpoints. The regularised runs already use the loss rule through
the early-stopping path (it never triggered). Report this as evidence that loss-based selection is not automatically better.

## J. Cross-validation (2026-09-20, closes the "seeds are not a data variation" feedback)

Built because every earlier run used ONE split (44 test videos) with the seed varying only the initialisation.
`scripts/freeze_cv_folds.py` freezes `data_splits/cv5_identity_grouped.json` (sha256 prefix `472bcd7d5e44`): 100 identity
groups (a reciprocal FF++ pair = 2 real + 2 fake videos) into 5 folds; per fold 20 groups test, 10 validation (checkpoint
selection only), 70 train = 80 test / 40 val / 280 train videos. Every video is a test video in exactly one fold and no video
or identity crosses roles in any fold (`tests/test_cv_folds_manifest.py`, 5 data-free tests, in CI).
`train.py --fold k` and `evaluate.py` (reads the fold from `train_config.json`, saves `per_video_predictions.json`) use it;
`scripts/aggregate_cv.py` pools out-of-fold predictions and gives cluster-bootstrap 95% CIs over identity groups.

| ID | Tag | Model | Status |
|---|---|---|---|
| V13 | `cv5_xcep_f0` to `cv5_xcep_f4` (seed 42) | Xception, multi-method (`frames_multi`) | **DONE 2026-09-20 21:06** (`scripts/queue_cv.sh`, 22 to 26 min per fold); result in `results/cv/cv5_xcep_mm/cv_summary.md` |

**V13 result (400 videos, each scored once by a model that never saw its identity; clip level; 95% CIs by identity-cluster
bootstrap over 100 groups):** pooled AUC 0.918 (0.891 to 0.942), accuracy at 0.5 82.8% (79.2 to 86.2), real specificity 93.0%
(88.5 to 97.0), fake detection 72.5% (66.0 to 79.0), EER 17.0% (12.8 to 20.2), ECE 0.078. Per method, fakes detected: Deepfakes
77.9%, FaceSwap 77.3%, NeuralTextures 62.1% (50.0 to 73.3). Per fold, accuracy ranges from 75.0% (fold 0, AUC 0.850) to 87.5%
(fold 1, AUC 0.952); fold mean 82.8 ± 4.7%. **The 44-video test split (Xception-mm clip accuracy 96.2%) is more favourable than
the cross-validated figure; the honest headline for this architecture is about 83%.** Caveats: one seed per fold, so the interval
reflects data partition, not training stochasticity; the CV describes the Xception-mm recipe, not any other architecture (do not
attach it to a different shipped model). Fusion implication: the PPR bases
fusion weights on cross-validated accuracy (Large, Lines and Bagnall, 2019), which is the 82.8% figure, not the 44-video mean.

Smoke-tested end to end on fold 0 (1 epoch, throwaway tag, removed). The fold's method assignment is the fixed one from
`multimethod_assignment_v1.json`, so about a third of each fold's fakes come from each method but the balance is not
enforced per fold. Not done: a CV of a second model; CV-fitted calibration (the proper fix for the small-validation-set
temperature problem, L23); CV-based `video_accuracy` for `ship_model.py`.
