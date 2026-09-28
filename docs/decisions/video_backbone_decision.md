# Video backbone: from EfficientNet-B4 (proposed) to Xception (shipped)

Report-ready record, written 2026-09-21. Every figure here was read from a result file on that date (evidence index at the end).
Purpose: state the architecture change completely and accurately in Chapters 3 to 6 of the final report, with nothing left out
and nothing overstated. Use this file, not memory or the Draft Report, as the source.

---

## 1. Summary

The PPR and Draft Report specified **EfficientNet-B4** as the video classifier, justified by Pokroy and Egorov (2021). That choice
was reopened after the supervisor's feedback on the Draft Report led to the discovery that the original data split leaked every
test video into training. On the corrected, identity-disjoint split, B4 was the weakest of five backbones tested under one shared
recipe. A second, independent problem then appeared: every model trained on a single manipulation method detected **none** of the
FaceSwap fakes, so the video branch was retrained on three methods. Because the PPR names B4, B4 was then given a fair chance on the
new data, twice (the plain recipe and the PPR's own regularised recipe), against a ship rule written down **before** either result
existed. It failed both times. **Xception, trained on three manipulation methods, seed 44, was shipped** on 2026-09-21 at 01:47 +08,
chosen over ConvNeXt-Tiny on false-alarm rate and evidence coverage. This is recorded as deviation **D-C**, forced by measurement.

---

## 2. What was promised

| Document | Section | What it says |
|---|---|---|
| PPR | 3.3, 3.5 | Video branch: face crops through EfficientNet-B4, ImageNet-pretrained, fine-tuned on FaceForensics++ (c23), giving P(video_fake) |
| PPR | 3.4 | "EfficientNet-B4 over B7": Pokroy and Egorov (2021) found B4 and B5 outperform B7 on DFDC, with no monotonic gain from size, so B4 is "not a compromise choice but an evidence-based one" and cheaper to fine-tune |
| PPR | 2 (Visual) | States its own caveat: Pokroy and Egorov trained on DFDC, not FF++, "so the B4 advantage requires empirical validation in this project's setup rather than being assumed to transfer" |
| PPR | Phase 2 workplan, 4.5 | Retrain B4 with dropout (p = 0.3), label smoothing (0.1) and early stopping on validation loss to address overfitting |
| Draft Report | 2, 3.4 | Claims the B4 choice was **validated** by the project's own results: "B4 fine-tuned on FF++ achieves a mean AUC-ROC of 0.993 across three independent training seeds" |
| Draft Report | 5.2, 6 | Headline: 96.39% mean accuracy, F1 0.9651, AUC 0.9929, EER 3.65% (3 seeds) |

**The Draft Report's validation claim must be withdrawn in the final report.** The 0.993 AUC and 96.39% accuracy were measured on the
leaking split (Section 3), so they did not validate B4. The PPR's own caveat (that the DFDC result needed testing on FF++) turned out to be
exactly the right caution.

---

## 3. Why the question was reopened

1. **Supervisor feedback on the Draft Report** questioned the video results directly: scores too high for the task, AUC of 0.99 pointing to
   overfitting or data leakage, seed variation "not instrumental", and EER not moving consistently with AUC.
2. **Investigation confirmed severe leakage.** Training, validation and test sets were built by a frame-level random split with no notion of
   video. About 19 near-duplicate crops come from each video, and **100% of test videos and 100% of validation videos also had frames in
   training**. A second leak existed: FaceForensics++ Deepfakes are reciprocal identity pairs (036_035 and 035_036), so even a video-level split
   leaks faces across sets.
3. **Fix:** an identity-disjoint split built by union-find over the identity graph, frozen as `data_splits/split_v2_identity_grouped.json`
   (sha256 prefix d34c8e7a759f): 320 / 36 / 44 videos, 6,072 / 736 / 758 crops. Leakage is guarded by data-free tests in CI.
4. **Effect on B4 (same recipe, frame level, 3 seeds):** 97.67% on the leaking split fell to **89.93 ± 0.99%** on the corrected split. The
   train-minus-validation gap was really **7.07 ± 0.15 pp**, not the 1.95 pp the leaking validation set had shown.
5. **The PPR's regularisation plan, tested on the corrected split (V6):** dropout 0.3, label smoothing 0.1 and early stopping gave 88.30 ± 1.80%
   frame accuracy with a gap of 6.15 pp. It narrowed the gap slightly and did not improve accuracy; early stopping never triggered in any seed.

---

## 4. Stage 1: backbone bake-off on the corrected split (single manipulation method, V8)

Five ImageNet-pretrained backbones (timm), one shared recipe: Adam, learning rate 1e-4, StepLR (halve every 3 epochs), batch 32, 10 epochs,
224 x 224 input, training augmentation on, checkpoint at best validation accuracy, seeds 42, 43, 44. Trained on the Deepfakes method only. Only
the architecture changes between rows.

| Backbone | Frame accuracy | Frame AUC | Frame EER | Validation accuracy | Train minus validation gap | Clip accuracy (44 videos) |
|---|---|---|---|---|---|---|
| **EfficientNet-B4 (PPR choice)** | **89.93 ± 0.99%** | 0.9722 | 9.81% | 92.30% | 7.07 pp | 96.97% |
| EfficientNet-B0 | 94.64 ± 1.56% | 0.9902 | 5.19% | 94.70% | 5.81 pp | 100.00% |
| ResNet-50 | 94.02 ± 0.08% | 0.9905 | 5.45% | 98.28% | 1.46 pp | 99.24% |
| Xception | 94.72 ± 0.40% | 0.9930 | 4.75% | 96.97% | 3.37 pp | 99.24% |
| ConvNeXt-Tiny | 96.26 ± 0.46% | 0.9952 | 4.05% | 97.78% | 2.44 pp | 100.00% |

**B4 was the weakest of the five on every frame-level measure and on validation accuracy.** Clip accuracy on 44 test videos saturates (one
video is 2.3 pp), so it cannot separate the models; frame-level and validation evidence are used instead.

---

## 5. Stage 2: single-method models fail on unseen manipulation methods (V9)

Each single-method model was tested on FaceSwap and NeuralTextures fakes it had never seen (test-split identities, 22 real + 22 fake videos per
method, clip level).

| Model (trained on Deepfakes only) | Deepfakes detected | FaceSwap detected (AUC) | NeuralTextures detected (AUC) |
|---|---|---|---|
| EfficientNet-B4 | 93.9% | **0.0%** (0.261) | 15.2% (0.794) |
| Xception | 98.5% | **0.0%** (0.268) | 16.7% (0.769) |
| ConvNeXt-Tiny | 100.0% | **0.0%** (0.266) | 9.1% (0.714) |

Every backbone detected **0% of FaceSwap** fakes, with AUC below 0.5 (FaceSwap faces scored as more real than genuine ones). The failure is a
property of single-method training data, not of any architecture. A model that misses a whole family of face swaps would make the PPR's scope
statement ("swap and reenactment-based deepfakes") untrue, so the video branch was retrained on multiple methods.

---

## 6. Stage 3: multi-method training (V10, V11)

Data design: Deepfakes, FaceSwap and NeuralTextures (all FF++ c23), **one method per identity pair**, class-balanced, using the same frozen
identity-disjoint split (`data_splits/multimethod_assignment_v1.json`; train pairs 54 / 53 / 53 by method). Same recipe as Stage 1.

| Model (trained on 3 methods) | Validation accuracy (mean of seeds) | Per seed | Clip accuracy | FaceSwap detected | NeuralTextures detected | Deepfakes detected | Real videos kept real |
|---|---|---|---|---|---|---|---|
| **Xception** | **86.28%** | 86.70 / 84.02 / 88.12 | 96.21 ± 3.47% | 87.9% | 81.8% | 90.9% | 97.0% |
| ConvNeXt-Tiny | 88.87% | 87.69 / 89.53 / 89.39 | 93.18 ± 2.27% | 87.9% | 69.7% | 95.5% | 90.9% |
| EfficientNet-B0 | 80.34% | 81.05 / 80.91 / 79.07 | 84.09 ± 3.94% | 66.7% | 77.3% | 90.9% | 90.9% |
| ResNet-50 | 76.76% | 77.65 / 77.37 / 75.25 | 87.12 ± 4.73% | 89.4% | 69.7% | 92.4% | 87.9% |

Multi-method training fixed the coverage failure (Xception: FaceSwap 0% to 87.9%) at a small cost on Deepfakes. **Do not compare these accuracies
with Stage 1:** the multi-method test set contains three manipulation families and is harder. Compare per-method detection.

---

## 7. Stage 4: EfficientNet-B4 given a fair chance on the multi-method data (V14)

B4 was never trained on the multi-method data; only the four backbones above were. The standing rule for this project is to stay faithful to the
PPR and deviate only when the promised version has been tried and failed. So B4 was tested before being dropped.

### 7.1 The ship rule, frozen before any B4 result existed

Written into `docs/EXPERIMENTS.md` (V14) on **2026-09-20 at 22:29 +08**, before the first B4 multi-method run started (22:30). Reference model R =
Xception multi-method. Candidate C = EfficientNet-B4 multi-method.

1. **Ship C** if both hold: (a) C's mean validation accuracy is within 2.0 pp of R's (86.28%, so at least 84.28%); (b) C's FaceSwap detection,
   NeuralTextures detection and real specificity are each no more than 2 test videos below R's (2/22 = 9.09 pp).
2. Otherwise ship the better of Xception-mm and ConvNeXt-mm under the criteria in Section 8, and register the deviation.
3. Seed chosen by validation accuracy, never test.

### 7.2 A second candidate, added with disclosures

At 23:05 the same night the PPR's own regularised recipe was added as candidate C2 (dropout 0.3, label smoothing 0.1, early stopping with patience
3 on validation loss), judged by exactly the same thresholds. Reason: the PPR promises B4 **with** that regularisation, so the plain recipe was not
the complete promised version. Recorded with three disclosures for the report:
1. B4 therefore got two attempts, a mild multiple-comparison advantage that the thresholds do not offset.
2. The note was written while plain B4 seed 42 was at epoch 8 (validation 74.0%), so part of the plain result was already visible.
3. With early stopping, the saved checkpoint is chosen by validation **loss**, which decision D5 found costs accuracy on multi-method models.

Measurement detail, fixed at the same time: rule (a) uses validation accuracy **at the saved epoch**, not the best over all epochs.

### 7.3 Results

| Candidate | Validation accuracy at saved epoch (per seed) | Mean | Rule (a) limit 84.28% | FaceSwap | NeuralTextures | Real kept real | Deepfakes | Verdict |
|---|---|---|---|---|---|---|---|---|
| R: Xception-mm | 86.70 / 84.02 / 88.12 | 86.28% | n/a | 87.9% | 81.8% | 97.0% | 90.9% | reference |
| C: B4-mm plain | 75.39 / 75.95 / 72.28 | **74.54%** | FAIL (-11.74 pp) | 60.6% FAIL | 72.7% pass (exactly 2 videos) | 98.5% pass | 93.9% | **NOT MET** |
| C2: B4-mm regularised | 70.30 / 71.71 / 67.75 | **69.92%** | FAIL (-16.36 pp) | 60.6% FAIL | 66.7% FAIL | 97.0% pass | 97.0% | **NOT MET** |

Other measurements of the two B4 runs: clip accuracy 91.67% for both; train-minus-validation gap 21.31 pp (plain) and 17.67 pp (regularised).
Plain B4 saved epoch 10 in every seed (validation still rising slowly). Regularised B4 saved epochs 10, 10 and 9; **early stopping never fired**.

**What the regularisation did:** it narrowed the overfitting gap (seed 42: 17.72 pp against 20.36 pp plain) and lowered validation accuracy with it
(70.30% against 75.39% for the same seed). This reproduces the Stage 1 finding (V6) on the harder problem: B4's weakness here is not a lack of
regularisation. The shortfall (12 to 16 pp) is far larger than the seed-to-seed spread (about 2 to 4 pp), so more seeds would not change it.

---

## 8. Stage 5: choosing between the remaining two (step 2 of the rule)

| Criterion | Xception-mm | ConvNeXt-mm | Better |
|---|---|---|---|
| Mean validation accuracy | 86.28% | **88.87%** | ConvNeXt (+2.59 pp) |
| NeuralTextures detected | **81.8%** | 69.7% | Xception (+12.1 pp) |
| FaceSwap detected | 87.9% | 87.9% | tie |
| Deepfakes detected | 90.9% | **95.5%** | ConvNeXt |
| Real videos kept real (false-alarm rate) | **97.0%** (3.0% flagged) | 90.9% (9.1% flagged) | Xception |
| Celeb-DF-v2 zero-shot: AUC / real videos kept real | **0.696 / 71.3%** | 0.671 / 64.0% | Xception |
| 5-fold cross-validation | **measured** (Section 9) | not measured | Xception |
| Calibration check | **measured**, ships uncalibrated by design (D3) | not measured | Xception |
| Clip accuracy on 44 test videos (secondary) | 96.21% | 93.18% | Xception |
| Train minus validation gap (secondary) | 13.66 pp | 11.66 pp | ConvNeXt |
| Latency | not measured per candidate | not measured | n/a |

**Decision D2 (2026-09-21 01:47): ship Xception, multi-method, seed 44.** Reasoning: for a tool that accuses a video of being manipulated, wrongly
flagging genuine content is the more damaging error, and Xception-mm flags 3.0% of genuine test videos against 9.1% for ConvNeXt-mm (28.7% against
36.0% on Celeb-DF-v2). It is also the only candidate with a cross-validated accuracy interval and a calibration check, so it is the model the
project can actually characterise.

**Counter-argument to state honestly:** ConvNeXt-mm has the higher validation accuracy, so on that criterion alone the choice would go the other way.
The decision is a trade-off on error type and evidence coverage, not a clean win, and 44 test videos cannot separate the two on aggregate accuracy.

**Seed 44** has the best validation accuracy of the three Xception-mm seeds (88.12 against 86.70 and 84.02), selected on validation only. It is also
the seed already used for the Celeb-DF-v2 run, the calibration check and the preprocessing-parity check, so those results apply to the shipped file.

---

## 9. The shipped model and how it was characterised

| Item | Value | Source |
|---|---|---|
| Architecture | Xception (timm `legacy_xception`), 20.8 M parameters (B4: 17.6 M; ConvNeXt-Tiny: 27.8 M) | `models/shipped_model.json`, timm |
| Pretraining | ImageNet | timm |
| Fine-tuning data | FaceForensics++ c23, Deepfakes + FaceSwap + NeuralTextures, one method per identity pair | `data_splits/multimethod_assignment_v1.json` |
| Run | tag `mm_xcep_vidsplit`, seed 44 | `models/shipped_model.json` |
| Checkpoint | 83.5 MB, sha256 fdd60748dc1c18441d493fc01ee8eb3e9028e7a5c75a938a79cf846062a75bd4 (verified against the file) | `models/shipped_model.json` |
| Previous checkpoint | leaking-split EfficientNet-B4, 70.9 MB, kept as `models/best_model.pth.pre-20260921-014755.bak` | `models/` |
| Shipped | 2026-09-21 01:47 +08 (manifest records 17:47:55 UTC on 20 Sep) | `models/shipped_model.json` |
| Face crops | MTCNN (facenet-pytorch), 224 x 224, margin 20; up to 20 faces sampled at about 3 per second | `scripts/video_infer.py` |

**5-fold identity-grouped cross-validation (V13).** Every one of the 400 videos is scored once by a model that never saw its identity; 95% intervals
by cluster bootstrap over 100 identity groups. Accuracy **82.8%** (79.2 to 86.2), AUC 0.918 (0.891 to 0.942), real videos kept real 93.0%
(88.5 to 97.0), fakes detected 72.5% (66.0 to 79.0), EER 17.0% (12.8 to 20.2), ECE 0.078. Fakes detected by method: Deepfakes 77.9%, FaceSwap 77.3%,
NeuralTextures 62.1% (50.0 to 73.3). Accuracy per fold: 75.0, 87.5, 83.8, 85.0, 82.5%. **The honest headline accuracy for the shipped architecture
is about 83%, not the 96.2% from the single 44-video test split.** Caveat: one seed per fold, and this CV describes Xception-mm only.

**Cross-dataset: Celeb-DF-v2, zero-shot (V12)**, official test list, 178 real + 340 fake videos, no retraining: accuracy **59.1%**, AUC 0.696,
EER 37.1%, fakes detected 52.6%, real videos kept real 71.3%. Below the 70 to 75% the literature reports for FF++-trained detectors (Khan and
Dang-Nguyen, 2023). For context, the superseded leaking-split B4 scored 61.2% (AUC 0.682), measured without the preprocessing fix below, so the two
are not like-for-like.

**Decision D3, calibration: shipped with no temperature (T = 1.0).** A temperature fitted on validation crops (T = 2.81, n = 707) improved validation
calibration (ECE 0.090 to 0.066) but made the held-out test crops worse (ECE 0.048 to 0.069; NLL 0.237 to 0.238) and worsened the clip-level Brier
score (0.0272 to 0.0461). The validation set is only 36 videos and harder than test, so the fitted value over-corrects. The model is already well
calibrated on held-out data. Dividing logits by T never changes a decision at 0.5.

**Decision D4, preprocessing parity:** training crops were saved as JPEG (quality 75) but the app fed the model uncompressed crops, which shifted the
operating point (7 of 88 verdicts changed, 2 genuine videos flagged). Inference now applies the same JPEG round trip. Re-checked on the shipped
checkpoint: sampling alone changes 1 of 88 verdicts; JPEG alone changes 8 of 88; AUC is unaffected (0.986 to 0.989).

**Decision D5, checkpoint rule:** keep best validation accuracy. Choosing on validation loss would pick epoch 1 or 2 for Xception-mm and give up 3.8 pp
of validation accuracy, because loss rises with over-confidence while accuracy still improves.

**Fusion weight:** fusion weights the video branch by **0.828**, the cross-validated accuracy, not the 0.962 from the 44-video split, because the PPR's
weighting basis (Large, Lines and Bagnall, 2019) is cross-validated accuracy and the small split is optimistic. With the audio branch weighted by its
balanced accuracy (0.9569), the weights are **video 0.464 / audio 0.536**.

---

## 10. What changing the model changed elsewhere

Every evaluation that consumed the video model was re-run on the shipped model on 21 Sep. The superseded outputs are preserved in
`results/OLD_model/`.

| Result | Superseded B4 (leaking split) | Shipped Xception-mm | Note |
|---|---|---|---|
| Four-condition: video only | 100.0% | 90.0% | see Section 11 |
| Four-condition: audio only | 97.5% | 97.5% | audio unchanged |
| Four-condition: standard (unweighted) fusion | 78.5% | 73.4% | |
| Four-condition: disagreement-aware fusion | 97.5% (T = 0.30) | **97.5%** (T = 0.35) | core claim holds: +24.1 pp over standard fusion |
| Correctly named audio (real video + fake audio) | 100% | 100% | |
| Correctly named video (fake video + real audio) | 100% | 95% | |
| False disagreement, real + real | 10.5% | 5.3% | |
| False disagreement, fake + fake | **5.0%** | **30.0%** | 10.0% on held-out video; see Section 11 |
| Hybrid: disagreement-aware fusion | 98.7% | 98.7% | modality named correctly on fake-video/genuine-audio: **0% for both** |
| Disagreement threshold T | 0.30 | **0.35** | retuned on the shipped model; interior F1 optimum 0.907 |
| Latency, video stage (warm) | 7.69 s | 5.95 s | measured 2 Sep vs 21 Sep; the old run had no JPEG round trip and no SVM stage, so treat as indicative |
| Latency, whole pipeline (warm) | 10.07 s, incomplete (SVM pending) | **9.02 s, all 8 stages** | first complete measurement |

The four-condition figures in this table come from the older set, which is in-distribution for the video branch. The held-out versions, which are the authoritative ones, are in Section 11 (disagreement-aware fusion 94.7% against 76.3% for standard fusion, an advantage of +18.4 pp, 95% interval +7.9 to +28.9).

**Code bug exposed by the swap (LESSONS L27).** `video_infer.load_models` read the shipped architecture from `models/shipped_model.json` only when it
was called without a path, and otherwise assumed EfficientNet-B4. `server.py` and the four-condition script both pass the path explicitly, so neither
could load the Xception checkpoint (a hard `RuntimeError: size mismatch`, caught on the first evaluation run, before the app was restarted). Fixed by
recognising the shipped checkpoint however its path is written; covered by a regression test. No result was produced with the wrong model.

**App changes that follow from the swap:** every place that named the video model now reads it from the manifest (a test forbids the string
"EfficientNet-B4" in `server.py` and `static/app.js`); the sidebar, "models that ran" table and face-crop caption show Xception; the Evaluation tab marks
the shipped row; the limitations panel quotes the cross-validation and Celeb-DF figures only because they were measured on this architecture.

---

## 11. The four-condition set was not held out for the video branch: found, fixed and re-run (2026-09-21)

**Finding.** The self-built evaluation set (`eval_fallback/`, 80 clips) was built on 13 Sep by sampling at random from **all** FaceForensics++ videos
(`scripts/build_fallback_eval_set.py`). The identity-disjoint split did not exist until 19 Sep, and when the video model was retrained on it nobody
re-checked whether the evaluation set was still held out. Checked against the frozen split manifests, **57 of the 80 clips (71%) use a video from the
shipped model's training split**, 8 from validation and 15 from test. By category (train / validation / test): real + real 14 / 2 / 4; real video + fake
audio 19 / 1 / 0; fake video + real audio 9 / 3 / 8; fake + fake 15 / 2 / 3. Of the 40 fakes (all Deepfakes-method), 8 were the exact manipulated video the
model trained on. The audio side was always held out (ASVspoof 2019 LA eval partition). The lesson is LESSONS L29.

**Fix.** A replacement set, `eval_heldout/` (`scripts/build_heldout_eval_set.py`), built only from the TEST partition: 22 real videos, and the 22 test
identity pairs in each of the three manipulation methods (66 fakes, 40 used, 14 Deepfakes / 13 FaceSwap / 13 NeuralTextures, disjoint between the two fake
categories). Verified independently: all 80 videos are in the test split, none of the 22 identities appears in any training or validation video. A data-free
test (`tests/test_heldout_eval_manifest.py`, run in CI) keeps this true, and would have failed 65 of the 80 clips of the older set. Limitation: only 22 real
test videos exist, so the two real-video categories share 18 of 20 videos and differ only in audio; 4 clips have no audio score (speech gate), leaving 76
in the fusion conditions.

**Result (same shipped model, same T = 0.35, same audio pipeline; only the video source differs).**

| | Older set (57 of 80 videos in training) | Held-out set (0 of 80) |
|---|---|---|
| Video-only accuracy | 90.0% | 92.5% |
| Audio-only accuracy | 97.5% | 92.1% |
| Standard (unweighted) fusion | 73.4% | 76.3% |
| Disagreement-aware fusion | 97.5% | 94.7% |
| **Advantage of disagreement-aware over standard fusion** (paired bootstrap) | +24.1 pp, 95% CI [+13.9, +34.2], n = 79 | **+18.4 pp, 95% CI [+7.9, +28.9], n = 76** |
| Correctly named audio (real video + fake audio) | 100% | 100% |
| Correctly named video (fake video + real audio) | 95% | 75% (15 of 20) |
| Wrongly reported as disagreement, real + real | 5.3% | 11.1% |
| Wrongly reported as disagreement, fake + fake | 30.0% | 10.0% |
| Best disagreement threshold T (F1 on the partial-manipulation class) | 0.35 | 0.35 |

**What this means, stated at the strength the evidence supports.**
1. **The research question's claim holds on held-out video.** The advantage is 18.4 points with an interval that excludes zero. The two intervals overlap
   heavily, so the data do not show that the earlier set inflated it.
2. **T = 0.35 is independently re-confirmed** as the optimum on the held-out set (F1 0.909), so the deployed threshold did not change.
3. **Held-out video-only accuracy did not fall** (92.5% against 90.0%). Real videos were 40 of 40 correct in both sets, so the difference comes entirely from fakes,
   and the sets differ in composition (Deepfakes-method only against three methods).
4. **Video branch alone on the 40 held-out fakes: 34 detected (85.0%)**: Deepfakes 13 of 14, FaceSwap 12 of 13, NeuralTextures 9 of 13 (69%); all 40 real
   videos were kept real. NeuralTextures is the weakest method, consistent with the per-method tests in Section 6.
5. **Why naming the video fell from 95% to 75%:** of the 5 held-out misses, the video branch scored the manipulated video below 0.5 in 4 (three
   NeuralTextures), and the audio branch false-alarmed on genuine speech in 3. These are the two failure sources found in the hybrid evaluation.
6. **Graded degradation, useful for the limitations chapter.** Naming the implicated modality on fake video with genuine speech: 95% (older set, most
   identities seen in training) to 75% (held-out FaceForensics++ identities) to **0%** (DeepfakeTIMIT, a different dataset). Unseen identities cost a modest
   amount; a different dataset removes the ability entirely.

**Two explanations I wrote earlier were wrong and are retracted.** First, I said the older set's absolute figures, especially video-only 90.0%, were optimistic;
held-out video-only accuracy is higher. Second, I said the rise in false disagreement on fake + fake clips (5% with the superseded model, 30% with the shipped one)
was memorisation by the old model; on held-out video that rate is 10%, so the 30% was a small-sample result (6 of 20 clips against 2 of 20). What the analysis of the
older set did show: its 8 exact-trained fakes were all detected (8 of 8), but the 16 fakes whose identity was trained on under a *different* method were detected only
62% (10 of 16) against 88% (14 of 16) for identities never seen. Familiar identities were harder, not easier. The mechanism is not established (a plausible
hypothesis is that the model learned those identities as genuine from their real videos); with 16 clips per group it is an observation, not a finding.

**How to describe the two sets in the report.** Present the held-out set (`results/heldout_eval_shipped/`) as the authoritative four-condition evaluation,
and the older set as in-distribution for the video branch, kept for comparison. Both are self-built and neither is FakeAVCeleb.

---

## 12. Checks deliberately not run, and why

| Check | Why not | Effect on the decision |
|---|---|---|
| Calibration of the two B4 runs | B4 failed step 1, which is a gate; calibration only breaks ties in step 2 | none |
| Celeb-DF-v2 for the B4 runs | same reason | none |
| Calibration of ConvNeXt-mm | ConvNeXt lost step 2 on false alarms and evidence coverage | none |
| Latency of each finalist | superseded by measuring the shipped model (9.02 s) | none |
| Cross-validation of any architecture other than Xception | Xception shipped, so its CV is the one that applies | none |
| B4 at its native 380 px input | every crop is stored at 224 x 224, so training at 380 would only upsample; a fair test needs all crops re-extracted and the app path changed | stated as a limitation of the protocol |

---

## 13. Caveats to state in the report (complete)

1. **One shared recipe for every backbone** (learning rate, schedule, 10 epochs, 224 px input). It may favour some architectures. The pipeline
   extracts faces at 224 x 224, so B4 never used its 380 px native input; that is a property of the protocol, not a judgement on B4 at its best.
2. **Pokroy and Egorov (2021) measured on DFDC, not FF++.** The PPR said so; this project's result is consistent with that caution.
3. **B4 got two attempts** and the second was added after part of the first result was visible (Section 7.2).
4. **Small test sets.** 44 test videos (one video = 2.3 pp); per-method tests use 22 fakes per method (one video = 4.5 pp).
5. **Step 2 is a trade-off,** not a clean win: ConvNeXt-mm has higher validation accuracy.
6. **Headline accuracy is about 83% (cross-validated),** not 96.2% from the 44-video split.
7. **Cross-dataset accuracy is 59.1%** on Celeb-DF-v2, below the literature's 70 to 75%.
8. **Coverage:** three of the four FF++ methods; Face2Face and other generators are not covered.
9. **The four-condition evaluation exists in two versions** (Section 11): the older set is in-distribution for the video branch; the held-out set is authoritative. Both are self-built, and the held-out set has only 22 real videos.
10. **The self-built set is not FakeAVCeleb,** which was never obtained (deviation D-A).

---

## 14. Deviation register entry D-C (final)

| Promise | Reality | Forced or chosen | Evidence |
|---|---|---|---|
| EfficientNet-B4 as the video backbone (PPR 3.3, 3.4, 3.5; Draft 3.4) | Xception, three-method training, seed 44 | **Forced by measurement:** B4 tested with the plain and the PPR's regularised recipe against a rule frozen beforehand, failed both | `docs/EXPERIMENTS.md` V8, V9, V10, V11, V13, V14; this file |

---

## 15. Models in the system

### In use

| Stage | Model |
|---|---|
| Face detection | MTCNN (facenet-pytorch) |
| Video classifier | Xception (timm `legacy_xception`), ImageNet-pretrained, fine-tuned on FaceForensics++ c23 (Deepfakes, FaceSwap, NeuralTextures), seed 44 |
| Speech detection | Silero VAD |
| Audio encoder | wav2vec2-base (`facebook/wav2vec2-base`), frozen |
| Audio classifier | RBF-kernel SVM (scikit-learn), trained on ASVspoof 2019 LA |
| Explanation | Llama 3 8B Instruct (`llama3:8b` via Ollama, 4-bit Q4_0) |

Five of these are pretrained (MTCNN, Xception, Silero VAD, wav2vec2, Llama 3) across image, audio and text; the SVM is trained by the project.

### Evaluated and not used

| Stage | Model | Why not used |
|---|---|---|
| Video | EfficientNet-B4 (PPR choice) | weakest single-method backbone; failed the frozen ship rule twice on three-method data |
| Video | ConvNeXt-Tiny | higher validation accuracy, but more false alarms (9.1% vs 3.0%), worse NeuralTextures detection, no CV or calibration evidence |
| Video | EfficientNet-B0 | 80.34% validation accuracy on three-method data |
| Video | ResNet-50 | 76.76% validation accuracy on three-method data |
| Audio | WavLM-base (`microsoft/wavlm-base`) | subsample comparison: EER 7.20% vs 6.60% for wav2vec2; same failure on unseen genuine speech |
| Audio | MFCC features (hand-crafted baseline, not pretrained) | EER 10.25% vs 3.96% for wav2vec2 on the full evaluation set |

---

## 16. Suggested wording for the report (adapt, do not paste)

**Design (Chapter 3):**
> The proposal specified EfficientNet-B4, following Pokroy and Egorov (2021), with the explicit caveat that their result was measured on DFDC and would
> need confirming on FaceForensics++. That confirmation was carried out (Chapter 5) and did not hold: the final system uses Xception, trained on three
> manipulation methods.

**Implementation or Evaluation (Chapter 4 or 5):**
> To keep the comparison fair, all five backbones were trained under one recipe, and a rule for replacing the proposed architecture was written down
> before its results existed. EfficientNet-B4 was trained with both the plain recipe and the regularised recipe the proposal specified; it reached
> 74.5% and 69.9% mean validation accuracy against a threshold of 84.3%, and detected 60.6% of FaceSwap fakes against 87.9% for Xception.

**Limitations:**
> All backbones saw 224-pixel face crops, so EfficientNet-B4 was not evaluated at its native resolution; the result should be read as a comparison
> under one protocol rather than as the best B4 can achieve.

**Retraction of the Draft Report claim:**
> The draft reported that the project's own results validated the choice of B4 (AUC 0.993). Those figures were produced on a split that placed every
> test video in the training set, and are withdrawn.

---

## 17. Citation notes

* **Pokroy and Egorov (2021):** in the literature review; cite for the original B4 choice only.
* **Rössler et al. (2019):** in the literature review. FaceForensics++ benchmarked detectors including XceptionNet, which is why Xception was included in
  the bake-off. **Check the exact claim against the paper before citing it** (for example, which detector performed best at c23).
* **Chollet (2017), the Xception paper:** not in the current reference list. Add it if Xception's design is described.
* **Khan and Dang-Nguyen (2023)** for the 70 to 75% cross-dataset range; **Large, Lines and Bagnall (2019)** for cross-validated accuracy weighting.

---

## 18. Evidence index

| Claim | File |
|---|---|
| Leakage and corrected split | `docs/DEV_LOG.md` (19 to 20 Sep), `data_splits/split_v2_identity_grouped.json`, `tests/test_frozen_split_manifest.py` |
| Stage 1 bake-off | `results/summary/bakeoff_video_vidsplit.md`, `results/numbers.json` (`video`) |
| Stage 2 cross-method failure | `results/cross_method/{aug,xcep,cnxt}_vidsplit/cross_method.json` |
| Stage 3 multi-method | `results/summary/multimethod_vidsplit.md`, `results/cross_method/mm_*_vidsplit/cross_method.json` |
| Frozen rule, dated notes, results, decision | `docs/EXPERIMENTS.md` V14 |
| B4 runs, per seed | `results/runs/mm_b4_vidsplit/seed*/`, `results/runs/mm_b4reg_vidsplit/seed*/` (`history.json`, `train_config.json`, `metrics.json`) |
| Cross-validation | `results/cv/cv5_xcep_mm/cv_summary.json` |
| Celeb-DF-v2 | `results/cross_dataset/celebdf_v2__mm_xcep_vidsplit/metrics.json` (and `__mm_cnxt_vidsplit`, `__cnxt_vidsplit`, `celebdf_v2/` for the old model) |
| Calibration | `results/calibration/mm_xcep_vidsplit_seed44/calibration.json` |
| Preprocessing parity | `results/preprocessing_parity/mm_xcep_vidsplit_seed44.{md,json}` |
| Shipped model | `models/shipped_model.json` |
| Downstream re-runs | `results/fallback_eval_shipped/`, `results/hybrid_eval_shipped/`, `results/latency/latency.json`; superseded in `results/OLD_model/` |
| Held-out check (Section 11) | `eval_fallback/manifest.json` against `data_splits/split_v2_identity_grouped.json` and `multimethod_assignment_v1.json` |
| Held-out four-condition evaluation, threshold sweep and interval | `eval_heldout/manifest.json`, `results/heldout_eval_shipped/{fallback_4condition_results,threshold_tuning,advantage_bootstrap}.json`, `scripts/build_heldout_eval_set.py`, `scripts/bootstrap_fusion_advantage.py`, guard `tests/test_heldout_eval_manifest.py` |
| Encoder comparison | `results/audio_encoder_comparison/comparison.json`, `results/audio_baseline/metrics.json` |
| Lessons | `docs/LESSONS.md` L1 to L4 (leakage), L18 to L20 (coverage), L25 (checkpoint rule), L27 (loader bug), L29 (evaluation set not re-checked against the split), L30 (untested explanation) |
