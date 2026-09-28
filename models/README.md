# Models (model card)

The four trained model files the application loads. They are **not in git** (too large); they are published as assets of the GitHub
release tagged `v1.0`. `./setup.sh` or `python3 scripts/download_models.py` downloads them into this folder and checks each against the
SHA-256 below (`--check` verifies without downloading). Every figure here comes from the result
file named beside it; the ledger ids refer to `docs/EXPERIMENTS.md`.

| File | What it is | Size | SHA-256 |
|---|---|---:|---|
| `best_model.pth` | Video classifier: Xception (timm `legacy_xception`) weights, fine-tuned | 83.5 MB | `fdd60748dc1c18441d493fc01ee8eb3e9028e7a5c75a938a79cf846062a75bd4` |
| `audio_spoof_svm.joblib` | Voice classifier: RBF SVM over frozen wav2vec2-base embeddings | 11.6 MB | `fcdea45879c5ddd79f2263c9fb09906a04f4cb33a1167140e21547618845b2fc` |
| `video_ood_gate.joblib` | Out-of-domain check for the picture (Mahalanobis distance) | 16.8 MB | `b8327604346fb0da64f790f3067c721ac80dfd1379fd5d93a3be076f28a198d0` |
| `audio_ood_gate.joblib` | Out-of-domain check for the voice (Mahalanobis distance) | 2.4 MB | `a4e0bf372eff9e838a29f5ed6a2f01b53d3dfb34252c17c580cb3a83d051ed4a` |
| `shipped_model.json` | Which video checkpoint is served, its architecture and the accuracy used as its fusion weight (in git) | | `886a31bab1d4a4314332564276e245174fef56670207af7e2da104896168e4d1` |

Pretrained components that are downloaded rather than trained here: MTCNN (inside `facenet-pytorch`), Silero VAD (`silero-vad`),
`facebook/wav2vec2-base` (Hugging Face) and Llama 3 8B (`llama3:8b` via Ollama). Versions used: facenet-pytorch 2.5.3, silero-vad 6.2.1,
wav2vec2-base revision `0b5b8e868dd84f03fd87d01f9c4ff0f080fecfe8`, Ollama `llama3:8b` model id `365c0bd3c000` (temperature 0.2, seed 42);
Python 3.12.4, torch 2.12.1, on an Apple M2 Pro (video model on MPS).

## Video classifier (`best_model.pth`)

- **Training data:** FaceForensics++ c23, three manipulation methods (Deepfakes, FaceSwap, NeuralTextures), face crops from
  `frames_multi/`, on the identity-disjoint split in `data_splits/` (no identity appears in two partitions). Seed 44.
- **How it was made:** `scripts/run_cell.sh` / `scripts/train.py` (run tag `mm_xcep_vidsplit`), promoted to this file by
  `scripts/ship_model.py`, which wrote `shipped_model.json`.
- **Why this model:** chosen among five backbones against a rule fixed before the runs; EfficientNet-B4 (the proposal's choice) was tested
  twice and failed it (ledger V8 to V14; `docs/decisions/video_backbone_decision.md`).
- **Measured:** clip accuracy 82.8% by 5-fold identity-grouped cross-validation over 400 videos, 95% interval 79.2% to 86.2%
  (`results/cv/cv5_xcep_mm/cv_summary.json`); 59.1% on Celeb-DF-v2 zero-shot (`results/cross_dataset/celebdf_v2__mm_xcep_vidsplit/`).
- **Calibration:** none applied (temperature 1.0; `results/calibration/`, decision D3).

## Voice classifier (`audio_spoof_svm.joblib`)

- **Training data:** ASVspoof 2019 LA, all 25,380 training utterances; evaluated on all 71,237 evaluation utterances
  (`results/audio_branch/metrics.json`).
- **How it was made:** `scripts/train_audio_svm.py`: wav2vec2-base (frozen) embeddings averaged over time, RBF SVM with C = 10 and
  probability outputs, seed 42.
- **Measured:** evaluation EER 3.96%; balanced accuracy 95.7% at P(fake) >= 0.5 (`results/audio_branch/extra_metrics.json`), the figure
  used as its fusion weight.
- **Version note:** saved with scikit-learn 1.4.2 and loaded by the app under 1.9.0; scikit-learn prints an `InconsistentVersionWarning`
  when the model loads. All reported app results were produced this way, so keep the pinned versions.

## Out-of-domain checks (`video_ood_gate.joblib`, `audio_ood_gate.joblib`)

- **What they do:** measure how far a clip's features are from the training data (pooled Mahalanobis distance; the limit is the 97.5th
  percentile of in-domain data). The app shows a warning above the limit and never changes a score (mode `warn`).
- **How they were made:** `scripts/extract_app_features.py`, `scripts/fit_ood_gates.py`; evaluated by `scripts/eval_ood_gate.py`
  (`results/ood_gate/`, ledger O1). Withholding scores instead of warning failed its pre-set rule, so it is not the default.

## Intended use and limits

The weights are shared for non-commercial research and education only: the video classifier and the video out-of-domain check are
derived from FaceForensics++, whose terms of use restrict it to that purpose.

A research prototype for the CM3070 project: it gives likelihoods, not proof. It was trained on three FaceForensics++ methods and one
speech corpus, is at or below chance on the independent LAV-DF set, and may call genuine speech from other corpora synthetic. The full list
of limits is in the root `README.md`.

Loading note: the saved objects record the module names `audio_branch.AudioSpoofSVM` and `ood_gate.MahalanobisGate`, so
`scripts/audio_branch.py` and `scripts/ood_gate.py` must stay importable under those names.

## Publishing the weights (maintainer)

After the repository is on GitHub, attach the four files to a release tagged `v1.0` (GitHub web page: Releases, Draft a new release, or
with the GitHub CLI: `gh release create v1.0 models/best_model.pth models/*.joblib --title "Model weights v1.0"`), then set `GITHUB_REPO`
in `scripts/download_models.py` to `"<owner>/<repo>"` so ZIP downloads, which have no git remote, also know where to look. If a file is
retrained, publish a new tag and update `RELEASE_TAG`, the checksums in the script and the table above together
(`tests/test_download_models.py` fails if the script and this table disagree).
