# scripts/: what each file is for

Organised 2026-09-25 and tidied 2026-09-28 for the release. Python scripts stay in one folder because they import each other, the tests
import them by name, and the saved models record two of their module names (`audio_branch`, `ood_gate`); only the one-off job launchers
moved (to `launchers/`). Every script starts with a docstring saying what it does and
how to run it. Two Python environments: base `/opt/anaconda3/bin/python` and app `/opt/anaconda3/envs/deepfake-detect/bin/python` (needed
wherever MTCNN, the server or `video_infer` runs; see the root README).

## 1. The pipeline (imported by the app, `server.py`)

| File | Role |
|---|---|
| `video_infer.py` | Face crops (MTCNN) and the shipped video model (Xception); the single video inference path |
| `vad.py` | Speech detection (Silero VAD) that gates the audio branch |
| `audio_branch.py` | wav2vec2 embedding and the RBF SVM that scores the voice |
| `fusion.py` | Disagreement check and accuracy-weighted fusion (T = 0.35) |
| `ood_gate.py` | Out-of-domain gate (Mahalanobis distance per branch); the app runs it in warning mode |
| `explain.py` | Constrained Llama 3 explanation (prompt, structured input, timing field) |
| `explain_checks.py` | Faithfulness screen and the plain-language standard wording (template) |
| `evaluation_view.py` | Builds the Accuracy page tables and the limits list from `results/numbers.json` |
| `utils.py` | Shared paths and helpers |

## 2. Training and model release

| File | Role |
|---|---|
| `train.py`, `run_cell.sh` | Train and evaluate the video model (one training cell: tag and seed) |
| `extract_frames.py`, `build_multimethod_frames.py` | Face crops for training; the three-method training folder |
| `freeze_split.py`, `freeze_cv_folds.py` | Freeze the identity-disjoint split and the 5 cross-validation folds (hashed manifests) |
| `calibrate_video.py` | Temperature-scaling check (decision D3: shipped without) |
| `ship_model.py` | Promote a trained checkpoint to the model the app serves (`models/shipped_model.json`) |
| `train_audio_svm.py` | Train the audio SVM on ASVspoof 2019 LA |
| `download_ff.py`, `download_extra_methods.sh` | FaceForensics++ download helpers |

## 3. Evaluation (each writes under `results/`; see `docs/EXPERIMENTS.md` for the ledger entry)

| File | Role |
|---|---|
| `evaluate.py`, `aggregate_runs.py`, `aggregate_cv.py`, `compare_variants.py` | Video model metrics per run, across seeds, across CV folds, across variants |
| `eval_cross_method.py` | Detection per manipulation method on unseen identities |
| `eval_celebdf.py` | Celeb-DF-v2 zero-shot |
| `eval_audio_metrics.py`, `eval_audio_baseline.py` | Audio branch full metrics; MFCC baseline |
| `compare_audio_encoders.py`, `audio_channel_diagnostic.py` | wav2vec2 against WavLM (A6); codec diagnostic (A5) |
| `build_fallback_eval_set.py`, `build_heldout_eval_set.py`, `build_hybrid_eval_set.py`, `build_lavdf_eval_set.py` | Build the four-category evaluation sets (held-out is authoritative; FakeAVCeleb never arrived) |
| `eval_fallback_4condition.py`, `tune_threshold_fallback.py`, `bootstrap_fusion_advantage.py` | The four-condition comparison, the T grid search, the bootstrap CI of the fusion advantage |
| `extract_app_features.py`, `fit_ood_gates.py`, `eval_ood_gate.py` | Out-of-domain gate: features, fitting, evaluation (O1) |
| `lowres_diagnostic.py`, `audio_lavdf_experiment.py` | LAV-DF diagnostics (F6 addendum, F7); experiments only, nothing shipped |
| `carve_lavdf_parts.py` | Extracts LAV-DF files from individual downloaded pieces of its split zip; used by every LAV-DF builder |
| `explanation_eval.py`, `build_rating_form.py`, `score_explanation_eval.py` | Human evaluation of the explanations: packet, rater form, scoring (E2) |
| `compare_screen_with_raters.py` | The app's faithfulness screen against the two raters' judgements (E2, exploratory) |
| `compare_llms.py` | Explanation model comparison, Llama 3 vs Mistral vs Qwen (M1) |
| `benchmark_latency.py`, `benchmark_app_latency.py` | Per-stage latency; end-to-end latency of the live app (L3) |
| `check_preprocessing_parity.py` | Does the app feed the model what it was evaluated on (D4) |
| `build_numbers.py` | Writes `results/numbers.{json,md}`, the single source of reported numbers |

## 4. User testing and the interface

| File | Role |
|---|---|
| `build_survey_form.py`, `score_user_testing.py` | Survey forms (full and short) and their scorer (U1) |
| `contrast_audit.py` | WCAG contrast of every visible text element in the final interface, to `results/ui_contrast_v4_final.json` (copied from the report's figure scripts) |

## 5. `launchers/`: one-off job queues (already run)

Shell scripts that ran long training and evaluation jobs overnight (19 to 22 Sep). Kept so every result can be traced to the command that
made it. Moved here from `scripts/` on 2026-09-25; the ledger and dev log mention them by their old path `scripts/queue_*.sh`. Each finds the
project root itself, so they still run from anywhere.

`queue_bakeoff_video.sh` (V8), `queue_multimethod.sh` (V10), `queue_mm_convnext.sh` (V11), `queue_mm_b4.sh` and `queue_mm_b4_reg.sh` (V14),
`queue_cv.sh` (V13), `queue_celebdf.sh` (V12), `queue_extract_methods.sh`, `queue_reg_resume.sh`, `queue_shipped_evals.sh`,
and `queue_retune_evals.sh`.
