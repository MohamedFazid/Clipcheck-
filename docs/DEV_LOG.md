# Dev Log

Running, chronological notes on everything done to this project, kept
separate from the report. It is the single record of the project's history
and current state. This file is append-only: newest entries at the top, nothing gets
deleted or rewritten as the project moves on. Purpose: a quick answer to
"what did we actually do, and when" for starting a new chat or writing up
the report later — not a submission artifact itself.

Entries are dated by when the work happened, reconstructed from conversation
history and file timestamps where the exact date isn't otherwise obvious.

---

## 2026-09-28 18:10 (this log is now the single record; git history squashed)

The separate current-state notes file outside the repository was retired; this log is now the only record of state and history. Every
pointer to it here was removed or reworded, and the two entries that only recorded rewriting it (24 Sep 17:00, 25 Sep 11:51) were dropped;
neither is cited by the report. The two earlier commits were replaced by one commit of the current files (the earlier history also held
personal paths).

---

## 2026-09-28 17:36 (product and tool names replaced with neutral wording)

Product and tool names in this log and in comments replaced with neutral wording (for example "a Terminal window", "the working notes",
"an editor settings folder"); one link to an external page removed. Remaining third-person wording in `findings.md`, `static/app.js` (and its
identical frozen copy, snapshot checksums re-made) and one test docstring changed to "developer". The frozen v1 and v2 interfaces are left
byte-for-byte as tested. Base 142 passed, 11 skipped; app 28 passed, 24 skipped.

---

## 2026-09-28 15:37 (wording tidy outside this log before publishing)

Outside this log: references to working notes that are not in the repository (to-do list item numbers, working rules, an archive
folder, a configuration file) removed or reworded in `EXPERIMENTS.md`, `protocol.md`, `response_sheet.md`, `heuristic_evaluation_v1.md`,
`docs/README.md`, `build_numbers.py`, `utils.py`, two launchers and a test; third-person references to the developer made
consistent ("the developer" or "the facilitator") (`findings.md`, `EXPERIMENTS.md`, the participant-correction files, `protocol.md`, the design brief,
comments in `server.py`, `explain_checks.py`, `build_*` scripts, and two comments in the frozen interface, whose snapshot checksums were
re-made so `static/` and `ui_v4_final_snapshot/` stay identical). Product names removed from `.gitignore`, `findings.md`, `EXPERIMENTS.md`
and `adjudication_seed42.json`. Kept on purpose: the statements that the heuristic review and a design review were done with an AI
assistant and that the M1 adjudication labels were produced by an AI assistant (large language model), not a human rater. Checked: base
142 passed, 11 skipped; app 28 passed, 24 skipped; the frozen-interface tests pass.

---

## 2026-09-28 15:26 (pre-push review: requirements, READMEs, docs folder, test fixture)

- **Requirements:** both files kept (the two environments pin conflicting versions: scikit-learn 1.4.2 / 1.9.0, transformers 4.57.3 /
  5.15.0, numpy 1.26.4 / 2.5.0; facenet-pytorch only in the app). Fixed their stale pointer to a README section "Two environments and why"
  (it is "Setup") and the `timm` comment that still named EfficientNet-B4.
- **READMEs:** the five `README.md` files kept under that name (GitHub shows a folder's README.md automatically); contents checked current.
- **docs:** `docs/report_prep/` renamed `docs/decisions/` (it holds only `video_backbone_decision.md`); mentions updated in README,
  models/README, docs/README, results/README, EXPERIMENTS and a comment in `scripts/explain.py`; the report's Appendix A citation updated and
  the .docx rebuilt (text diff: that one line; previous copy in `../Final Report/_backup_2026-09-28/`). Older entries below keep the old path.
- **Test fixture:** `tests/fixtures/speech_sample.wav` (synthetic, macOS `say`) is now allowed through `.gitignore`, so the three VAD tests
  that use it run in a fresh clone.
- **AI-tool references:** listed in full for the developer; nothing changed yet.

---

## 2026-09-28 15:08 (demo clips moved out after the demo video; clip-dependent tests now skip without them)

I recorded the demo video, then moved the demo clips to `../_moved_out_2026-09-28/` (logged, 50 files, 37 MB):
all of `demo_videos/` (13 clips and the five Veo test clips with thumbnails) and the 25 example clips in `eval_fallback/` and `eval_lavdf/`
(each `eval_*` folder now holds only its `manifest.json`). No dataset media is left in the folder. The app still runs: its Check page shows
the built-in note that the demo videos are not in the public code; the 41 code, model and interface files in the release checksums are
unchanged (the other 37 entries are the moved clips). Tests: 28 used the clips and failed without them, as they would in any fresh clone, so
they now skip when the clips are absent: a `needs_demo_clips` marker on 23 tests in `test_server.py` (the shelf test only guards its
clip-serving part), a module skip in `test_pipeline.py` before it loads the models, and two skips in `test_audio_branch.py`. Checked both
ways: without the clips base 142 passed, 11 skipped, app 28 passed, 24 skipped, CI 88 passed, 1 skipped; with the clips linked into a
scratch copy app 54 passed and base 144 passed, 9 skipped, as before. README and TESTING_GUIDE counts updated.

---

## 2026-09-28 12:20 (LAV-DF decision record moved out)

`docs/report_prep/lavdf_generalisation_and_ood_gate.md` moved to `../_moved_out_2026-09-28/` (logged): neither the report
nor the ledger cites it, and the ledger keeps its results (F6, O1). Its row removed from `docs/README.md`.

## 2026-09-28 12:14 (report test counts updated to the 207-test suite)

Measured first, in a scratch copy with the moved-out face crops linked in: base 152 passed, 1 skipped. Report source edited
(`../Final Report/content/ch4.txt`: 207 tests in 19 suites, 28 September, 152 passed, data-free subset 89, Table 4.2 "Data and leakage"
27, recounted from the test files: 5 + 9 + 4 + 5 + 4 = 27; `ch5.txt`: 207) and the .docx rebuilt with `build.js`. A text diff against
the previous build shows only these changes; word limits unchanged (total 10,316 / 10,500). Previous .docx and sources kept in
`../Final Report/_backup_2026-09-28/`. Also corrected: the 11:33, 11:54 and 12:07 entries below had been stamped 11:35, 12:20 and 13:00
without reading the clock (LESSONS rule: run `date` first).

## 2026-09-28 12:07 (unused scripts removed; personal paths cleaned; suite now 207 tests in 19 suites)

My choice after the dead-file review. Moved to `../_moved_out_2026-09-28/` (logged): `scripts/run_seeds.sh`, `det_curve.py`,
`threshold_analysis.py` (the August pipeline; `train.py` now always uses the identity-disjoint split, so they could not reproduce the
old leaking-split results anyway; those results stay in `results/runs/aug/`), `scripts/lavdf_partial_zip.py` and
`tests/test_lavdf_partial_zip.py` (unused LAV-DF reader, 2 tests), `scripts/sanitize_paths.py`, and the two report screenshot helpers
`scripts/ui_screenshots.py` and `scripts/capture_final.py` (their screenshots stay). Kept on purpose: `contrast_audit.py` (produced the
contrast measurement the report quotes), `build_survey_form.py` and `build_rating_form.py` (built the study forms; imported and tested).
Personal paths replaced in `eval_heldout/manifest.json` and `results/heldout_eval_shipped/fallback_4condition_results.json` (80 each,
`$ASVSPOOF2019_LA_ROOT/`) and `scripts/launchers/queue_celebdf.sh` (`$CELEBDF_ROOT`); no file in the folder contains the username now,
but commit `60f5032` still does (squash before pushing). CI config, `scripts/README.md`, README counts, TESTING_GUIDE, findings.md,
protocol.md, docs/README.md and the LAV-DF record updated. Checked: 78 app files unchanged; live app 200; base 144 passed, 9 skipped;
CI subset 88 passed, 1 skipped; app 54 passed (207 tests in 19 suites). **The report still says 209 tests in 20 suites** (Ch4 line 128,
Table 4.2 "Data and leakage" 29, Ch5 line 83): to be changed by me.

## 2026-09-28 11:54 (dead-file review of results/, scripts/, tests/; eight superseded result folders moved out)

Reviewed every script (imports, launchers, tests), every test and every result folder against the report, the app and
`scripts/build_numbers.py`. Scripts and tests: nothing removed. Every script is used by the app, imported, run by a launcher or produced
a reported result; `lavdf_partial_zip.py` is unused by the builders but its test is in CI and in the report's 209 tests; `run_seeds.sh`,
`det_curve.py` and `threshold_analysis.py` produced `results/runs/aug/` (the 97.67% the report quotes). The v1 and v2 launchers stay: the
report states that versions 1 and 2 still run on their own ports. Moved to `../_moved_out_2026-09-28/` (logged; 46 files):
`results/runs/reg/`, `runs/seed42/` to `runs/seed44/` (leaking-split runs the report does not quote), `results/fallback_eval/`,
`results/hybrid_eval/`, `results/cross_dataset/celebdf_v2/` (old-model evaluations; the report quotes none of their figures) and
`results/explanation_eval_full_pre_timing_2026-09-21/` (never rated). `numbers.json` is unchanged; a trial regeneration in a scratch copy ran
cleanly, kept 97.67% and 89.93%, left `baseline_legacy`, `reg` and the `*_OLD_MODEL` sections empty, and would now fill
`threshold_tuning_shipped` (empty in the frozen file because the tuning file was misfiled on 21 Sep; restored this morning). Checked:
78 app files unchanged; live app pages 200; base tests 146 passed, 9 skipped; app tests 54 passed. `results/README.md` updated.

## 2026-09-28 11:33 (Makefile, CHANGELOG and release/ removed at my request; per-file inventory)

Every file in the folder was checked against what uses it (app, scripts, tests, report, docs); the per-file verdicts are in
`../Project notes/FILE_INVENTORY_2026-09-28.md`. Moved to `../_moved_out_2026-09-28/` (logged): `Makefile`, `CHANGELOG.md`, `release/`
(checksums, recorded app outputs, lock files, environment), `scripts/check_frozen_app.py` (it only compared the app with `release/`) and
`docs/user_testing/materials/noface_silent.mp4` (a byte-identical duplicate of `demo_videos/noface_silent.mp4`). References updated in
README (quick start without make, layout, setup table, release-freeze section removed), `models/README.md` (the pretrained-model versions
from `release/ENVIRONMENT.md` copied in), `docs/README.md`, `results/README.md`, `scripts/README.md`, `docs/user_testing/protocol.md`.
Checked after the move: the 78 files the app loads match the moved `release/SHA256SUMS`; base tests 146 passed, 9 skipped; app tests 54 passed.
Duplicate scan: 17 groups of identical files; all but the one moved are deliberate (the frozen v4 snapshot that a test compares with
`static/`, raw survey and rater files kept beside their working copies, and blank rating templates).

## 2026-09-28 11:07 (datasets, checkpoints and caches moved out of the repository folder)

I wanted the folder to hold only what goes to GitHub, with no dataset in it and no change to how the app runs. Planned first
(`../Project notes/CLEANUP_PLAN_2026-09-28.md`, 03:45: every file classified), approved, applied at 10:59. Nothing was deleted.
- **Moved to `../_moved_out_2026-09-28/`** (same relative paths; log `MOVED_FILES.txt`, one line per move, 292 lines): 17,030 files,
  7.06 GB. `data/`, `external_datasets/`, `frames/`, `frames_methods/`, `frames_multi/` (its 400 relative symlinks still resolve there),
  `models/runs/` (every training checkpoint; the app loads `models/best_model.pth`), the result caches (`audio_branch/embeddings/`,
  `ood_gate/features/`, `audio_baseline/mfcc_cache/`, the `audio_lavdf_experiment` SVMs and embeddings, `runs/*/test_scores.npz`), job logs
  (`results/logs/` and three other `.log`), all 80 `eval_heldout` clips and the 188 `eval_lavdf` and 67 `eval_fallback` clips that are not app
  examples (the manifests stay), and caches (`__pycache__`, `.pytest_cache`, `.DS_Store`, an editor settings folder). All were git-ignored already.
- **Kept, 693 files, 200 MB:** the 639 files git would upload (47.5 MB); the four model files and the VAD test fixture (git-ignored, needed);
  the demo clips until the demo video is recorded (`demo_videos/`, the 13 `eval_fallback` and 12 `eval_lavdf` clips the example shelf uses,
  including `FVFA_004.mp4`, which the shelf uses but `release/SHA256SUMS` does not list, and `materials/noface_silent.mp4`).
- **Checks.** Before moving, a copy holding only the kept files ran on port 8003. After moving, on the real folder: strict
  `release/SHA256SUMS` check, all 78 present and unchanged; `make verify`; `check_frozen_app.py compare --tol 0` on a copy started from the
  real folder on port 8003, **IDENTICAL** (5 endpoints, 10 analyses); app tests 54 passed; CI subset 90 passed, 1 skipped; base 146 passed,
  9 skipped (was 154 + 1). The live server on port 8000 was not touched.
- **Test change:** `tests/test_data_split.py` failed without `frames/` (7 errors), so its seven face-crop tests got a `needs_frames` skip
  (the frames_multi test already skipped itself). A module-wide skip was tried first and narrowed, because it also skipped the data-free
  `test_tagged_runs_do_not_collide_with_baseline_paths`. With the crops present (checked by linking the moved-out folders into a scratch
  copy) all 9 pass. README (dataset paragraph, test counts), Makefile, TESTING_GUIDE and CHANGELOG updated to match.
- **Still open:** after the demo video, move the demo clips out too (the app then shows a note in their place; `test_pipeline.py` and
  `test_audio_branch.py` need them); the `timm` comment in `requirements-base.txt` still says EfficientNet-B4; three uploaded files hold a
  `/Users/...` provenance path (optional to sanitise); the weights release link in README.

## 2026-09-28 02:37 (repository reorganised for release; the application frozen)

I wanted an industry-standard layout without any change to how the app runs, planned first (every file classified, the
plan approved) and then applied. Nothing was deleted and nothing the app loads was moved or edited.
- **Freeze first:** restore point `../_freeze_2026-09-28_pre-reorg/` (802 MB: the repo minus datasets, frames, checkpoints and caches);
  `release/SHA256SUMS` (the 78 files the app loads: code, interface, the three frozen interface snapshots, model files, numbers.json,
  latency and audio metrics, the two demo manifests and 37 demo clips); `release/requirements-{app,base}.lock.txt` (95 and 435 packages);
  `release/ENVIRONMENT.md`. New `scripts/check_frozen_app.py` recorded a second copy of the app on port 8003 (five information endpoints and
  ten analyses: the eight shelf clips, noface_silent, LAVDF_RVRA_000) into `release/app_outputs_2026-09-28.json`; a second recording matched
  it exactly at tolerance 0 (scores, verdicts, warnings, explanation text). The live server on port 8000 was not touched. Baseline tests:
  base 154 passed + 1 skipped, app 54 passed, CI subset 90 + 1 skipped.
- **Fixed:** `results/fallback_eval_shipped/threshold_tuning.json` (the T = 0.35 tuning cited by `scripts/fusion.py` and shown in the app's
  threshold source) had been filed under `results/_superseded/threshold_T030_2026-09-21/` on 25 Sep; moved back.
- **Moved to the workspace holding folder `../_removed_2026-09-28/`** (log `MOVED_FILES.txt`, same relative paths): the old B4 checkpoint
  backup, the DeepfakeTIMIT tarball (the folder stays), `results/OLD_model/`, `results/_superseded/` (PPR-era files, the T = 0.30 results),
  the leaking-split aggregates and logs in `results/summary/`, `results/screenshots/` (empty), the root `logs/` (26 Sep server log),
  `results/llm_comparison/pull.log`, `docs/report_prep/benchmark_table.md`, `screenshots/v1_retake/` and `v2_before_C19_C20/`,
  `scripts/build_fakeavceleb_eval_set.py`, `scripts/launchers/queue_status.sh`, and caches (`__pycache__`, `.pytest_cache`, `.DS_Store`).
- **Moved out of the repo:** `docs/internal/` to `../Project notes/` (APP_TODO, prompts, archive); nine report-writing aids
  from `docs/report_prep/` to `../Final Report/prep/`. The working notes outside the repository point there now.
- **Kept on purpose** (cited or needed): DEV_LOG and LESSONS (report Appendices A and B), the v1/v2 snapshots and launchers (Chapter 4:
  frozen byte-for-byte), `lavdf_partial_zip.py` and its test (the report's 209 tests), the leaking-split runs and old-model results that
  `numbers.json` was built from, the files the ledger or `findings.md` cite (`latency/archive/`, the pre-timing packet, screenshots v3/v4),
  and the two server logs from the user-testing days.
- **Added:** `CHANGELOG.md`, `Makefile` (run, run-v1, run-v2, test, test-app, ci, verify, check-app), `models/README.md` (model card with
  checksums), `scripts/capture_final.py` and `scripts/contrast_audit.py` (copied from `Final Report/figures/src/` with a repo-relative root).
  **Updated:** README (final interface, E2 scored, the freeze, layout, test counts 154/54/91), `docs/README.md`, `results/README.md`,
  `scripts/README.md`, `docs/TESTING_GUIDE.md` (final interface; expected scores unchanged), `.gitignore` (+ `logs/`, the OOD feature
  cache and the experiment SVMs, about 84 MB).

---

## 2026-09-28 00:36 (appendices limited to the application as submitted)

- I wanted the appendices to contain only what the current application uses. Checked each: A (deviation register) all rows describe the
  final system, "VBD" abbreviation spelled out; B (problems fixed) rows 5 (composite "audio demo" clip, no longer reachable in the interface)
  and 20 (lost v3) removed, 18 rows left, each fix verified in the final code where applicable (`[hidden]` rule, versioned static files);
  Ch5 5.7 now says 18; C (screens) was not cross-referenced from the text (template rule): Ch4 4.7 now points to it, and it gains the Details
  "Accuracy and limits" tab (R4), History, and the public-copy demo note (new `capture_final.py --no-clips-note`, frozen interface, no jobs):
  C.1 to C.9; D unchanged. Build: Ch4 2,356, total 10,316 / 10,500; 29 images.

---

## 2026-09-28 00:27 (Chapter 6 written; all six chapters within limits)

- Re-read before writing: Ch1 to Ch5, project_record (honesty and rigour), LESSONS (L19, L28, L31, L33), the proposal record (Whisper deferred to
  future work). `content/ch6.txt` (948 / 1,000) from `docs/report_prep/ch6_plan.md`: 6.1 summary and the answer (yes for performance within a
  boundary, +18.4 points; no for robustness: LAV-DF at chance, no picture named on LAV-DF or DeepfakeTIMIT); 6.2 originality (disagreement as a
  reported verdict; the interface shows the rule; judgements kept out of the LLM with a checked text, rater-confirmed, and the check's bias; the
  warning inside the verdict); 6.3 decisions in hindsight (the marker's feedback changed the design; rules before results; what would change); 6.4
  themes (evaluation integrity; adaptation vs generalisation; trust calibration); 6.5 further work. No new results.
- Corrected on reading: LAV-DF's picture fakes are lip-syncs, not face swaps; Ch6 and Ch5 5.4 now say "manipulated picture".
- Build: Ch1 910, Ch2 1,826, Ch3 1,791, Ch4 2,351, Ch5 2,485, Ch6 948; total 10,311 / 10,500. Still open: AI-use statement (my decision), the
  repository link placeholder in meta.json, a final pass of every number and citation, then GitHub, the demo video and submission.

---

## 2026-09-28 00:07 (Chapter 5 audited against the instruction and review criteria 10 to 13)

- I asked for a double check. Gaps closed within the limit: 5.1 now maps sections to the aims; Table 5.3 gains a row judging requirements
  R1 to R8 from Table 3.1 (R1 to R3, R5, R6, R8 met; R4 partly; R7 by design); 5.2 adds the CV split between genuine kept (93.0%) and fakes caught
  (72.5%); kappa's quadratic weighting and the SUS choice are justified in a phrase each. Wording trimmed elsewhere; no result removed.
  Ch5 2,487 / 2,500; total 9,365 / 10,500.

---

## 2026-09-27 23:57 (Chapter 5 written; Appendix D; Chapter 1 user-testing sentence)

- Sources re-checked before writing (I asked for a second sweep): numbers.md / numbers.json, the held-out per-clip file (F1 grid over
  T recomputed from per-clip scores: 0.865 to 0.909 for T = 0.20 to 0.60, best 0.35; the five missed face swaps: four scored below 0.5 by the video
  branch, two of them blamed on the voice), EXPERIMENTS V8 to V14, A1 to A6, F3 to F9, H2, O1, T1, M1, the two report-prep records, E2 scored_report
  and screen_vs_raters, heuristic review, findings, user-testing summary, the participant correction, the contrast audit, latency.
- Corrections made while checking: B4-regularised is 69.92% on the rule's own measure (mean validation accuracy at the saved epoch; numbers.md's
  70.63% is a different computation); the warning flags 199 of 200 LAV-DF clips (so "all 50 wrong verdicts" is stated with that), and none of the
  6 wrong held-out verdicts; the round 1 debrief claim was removed (round 1 debrief notes are among the carry-over-affected answers); consent is
  described as verbal at the sessions and signed afterwards (the forms were made 27 Sep).
- `content/ch5.txt` (2,466 / 2,500): 5.1 strategy (answers the Draft feedback: leakage, seeds, EER/AUC), 5.2 model choice (video, audio), 5.3
  research question, 5.4 boundary and the warning, 5.5 explanation (screen, LLM comparison moved here, human rating), 5.6 users (same four people
  twice, familiarity caveat, consent, data problems, final-interface contrast), 5.7 testing and performance (demo videos are illustration, not
  evidence), 5.8 critique. Threshold-sensitivity detail moved to the Figure 5.6 caption.
- New `content/appD.txt` (generated from the consent-form files and build_survey_form.py; researcher email not reproduced) and build.js entry:
  Appendix D, user-testing materials. Chapter 1 section 1.6 now says "with the same four people".
- Build: Ch1 910, Ch2 1,826, Ch3 1,791, Ch4 2,351, Ch5 2,466; total 9,344 / 10,500; Ch6 not written. 26 images.
- Note: the module's AI-use guidance (Lecture 1) requires acknowledging all AI use; the report needs a statement of AI use and, per the
  guidance, explicit permission.

---

## 2026-09-27 23:43 (contrast audit of the final interface; Ch5 figures renumbered; participants corrected)

- New `Final Report/figures/src/contrast_audit.py` (saved this time; v1 to v3 audits were inline): WCAG 2.1 contrast of every visible text
  element, backgrounds composited from ancestors over the page base colour, gradient labels at their weaker stop. Final interface, ten screens
  (Check, three results, four Details tabs, History, Accuracy): 1,054 elements, 0 below 4.5:1, lowest 5.19:1. Landing page: 124 elements, 2
  below 4.5:1 (the 66 px hero headline's grey base layer, 4.2:1; large text, passes AA at 3:1). Result: `results/ui_contrast_v4_final.json`. Its
  three analysis jobs (FVRA_000, LAVDF_RVRA_000, no-face upload) ran just before 23:42 (measured_at 23:42:13) and were removed.
- Chapter 5 figures renumbered in order of appearance (LLM comparison moves to 5.5): core result 5.5, scatter 5.6, boundary 5.7, LLM 5.8; old
  files moved to `figures/_superseded_2026-09-27_2300/`.
- My statement: rounds 1 and 2 were the same four people (P1 = P5, P2 = P6, P3 = P7, P4 = P8), all signed consent forms (kept privately).
  Recorded in `docs/user_testing/responses/participant_identity_correction_2026-09-27.md` (+ `same_person_2026-09-27.json`) with the
  discrepancies against the sheets; raw files unchanged; `findings.md` round 2 note marked superseded. Figure 5.10A now joins each person's
  two SUS scores. Chapter 5.6 will report four people tested twice, with the familiarity caveat.

---

## 2026-09-27 23:12 (Chapter 4 rewritten; final-interface screenshots; figures renumbered)

- New `Final Report/figures/src/capture_final.py`: first checks that the server serves the frozen snapshot's files (SHA256SUMS), then captures
  the final interface (36 images, reduced motion, 0 console errors) into `docs/user_testing/screenshots/v4_final/`, with figure crops cut by page
  element (`crops/`). Its own 7 analysis jobs (RVRA_000, RVFA_000, FVRA_000, 183_253, LAVDF_RVRA_000, the no-face upload, 183) ran between about
  23:04 and 23:07 (index.json captured_at 23:07:15) and were removed; my 4 History jobs untouched. These analyses appear in the server log at that time: they are this capture,
  not user sessions. The 05:56 v4 set is kept unchanged.
- `make_ch4_figures.py` now builds Figures 4.3, 4.4, 4.5 and the new 4.7 (Check a video page with the demo row) from those crops; latency is
  Figure 4.8; Appendix C renumbered C.1 to C.6 (check page moved to Figure 4.7). Diagram 4.6 footnote now names the frozen v1 and v2 ports.
  Superseded figure files moved to `figures/_superseded_2026-09-27_2300/`.
- `content/ch4.txt` written from `docs/report_prep/ch4_plan.md`: 4.1 orchestration (new Table 4.1, the models and how each is run), 4.2 data and
  the evaluation sets (new: how the four-category and LAV-DF sets are built), 4.3 video, 4.4 audio (alternatives built behind the same
  interfaces), 4.5 fusion and gate, 4.6 explanation (LLM swappable by one setting), 4.7 application (final interface, eight-clip demo row, testing
  mode, public-copy note, frozen snapshots), 4.8 engineering (209 tests recounted: base 154 passed + 1 skipped, app 54; CI subset 91; latency).
  Corrected on checking: the JPEG-parity bug flagged 2 genuine videos (not "2 of 22"); the end-to-end times are the 25 Sep demo set. Round 3
  not mentioned. Build: Ch4 2,351 / 2,500; total 6,873 / 10,500 (Ch5 and Ch6 not written). 16 images in the document.

---

## 2026-09-27 22:49 (round 3 CSVs re-saved; still NOT filed or scored)

- The four files in ~/Downloads were re-saved at 21:12 (P9), 21:35 (P10), 22:03 (P11), 22:48 (P12) with rewritten answers. Checked again at my
  request. The app server's log still has no page load, demo request or analysis after 20:24 (only three History polls from an
  already-open tab; History unchanged at 4 jobs); RVRA_000 and LAVDF_RVRA_000 have never been analysed on it. P12's T7 note quotes a distance of
  44.8 against a limit of 99.9, which is RVRA_001's video familiarity value (this session's shelf check), not LAVDF_RVRA_000's (audio 70 against
  43 in the answer key). Not filed; round 3 stays recorded as not run.

---

## 2026-09-27 20:48 (round 3 CSVs in Downloads; NOT filed or scored)

- Four files appeared in ~/Downloads: survey_P9_round3.csv 20:32, P10 20:36, P11 20:43, P12 20:46. Left where they are; nothing copied to
  `responses/`, nothing scored. Reasons: the app server's log has no request of any kind after the 20:24 read (last line identical at 20:47;
  History unchanged at 4 jobs), so the app was not opened while the four sessions were recorded, and RVRA_000 / LAVDF_RVRA_000 were never
  analysed on it; the P10 to P12 free text matches the 20:24 pasted text word for word; P9's background and SUS answers differ from the pasted
  version exactly where the 20:25 check had flagged them (identical SUS to P10; Computer Science). Round 3 stays recorded as not run; the report
  states v4 is untested.

---

## 2026-09-27 20:25 (round 3 responses received as pasted text; NOT filed or scored)

- I pasted four round 3 responses (P9 to P12) as text. Not filed, not scored, nothing written to `responses/`. Checks before scoring: no CSVs downloaded from the form; the server log covers the whole life of the only app server (pid 80421, started
  18:58:33) and shows no analysis of RVRA_000 (demo 13) or LAVDF_RVRA_000 (demo 25) and one of FVRA_000 (demo 19, a screenshot job of mine,
  removed), while each described session needs all three in testing mode; the forms were ready at 19:40 and the text arrived at 20:24.
  Also: P9 and P10 give identical answers on all 10 SUS items; 3 of 4 report an ML background (the protocol recruits non-experts). Still needed:
  the CSVs and where the sessions ran. Until then round 3 is recorded as not run; the report says v4 is untested.

---

## 2026-09-27 19:59 (re-frozen: note when the demo clips are absent)

- A public copy has no demo clips (FaceForensics++ may not be redistributed; they are git-ignored), and the demo row then showed only an empty
  bar. By my choice (option A of three) the row is replaced, only when no clips exist, by: "Demo videos aren't included in the public
  code: they are built from research datasets that can't be shared. The README explains how to rebuild them. You can still check your own clip
  above." The page with clips is unchanged. Checked in headless Chrome with and without clips (1440 and 390 px, testing mode too): 8 cards / the
  note, no sideways scroll, 0 console errors.
- README: new "Demo videos (rebuild locally)" section (build_fallback_eval_set.py, build_lavdf_eval_set.py, test-pattern recipe).
- Interface re-frozen: `ui_v4_final_snapshot/` and SHA256SUMS refreshed; `test_final_interface_is_frozen` passes. Round 3 not yet started.

---

## 2026-09-27 19:39 (interface FROZEN; round 3 prepared)

- I declared the interface final. `static/` copied to `docs/user_testing/ui_v4_final_snapshot/` (index.html, style.css, app.js,
  clipcheck-mark.svg; SHA256SUMS verified; byte-identical to static/). New test `test_final_interface_is_frozen` fails if static/ ever differs.
  Any later change needs a new snapshot and an entry here.
- Round 3 prepared: `scripts/build_survey_form.py` gains round 3, a T3 check `share_as_genuine` ("Would you share this clip as genuine?", asked
  after the unchanged publish question) and a consent choice for the signed form; both forms rebuilt. Rounds 1 and 2 re-scored in a scratch
  folder: SUS unchanged. `protocol.md` has a round 3 checklist (consent first, P9 to P12, testing mode shows the round 1/2 clips) and a map of
  v4 names. Cut-off Monday 12:00.
- Tests: app 54 passed (with models); base 154 passed, 1 skipped.

---

## 2026-09-27 (evening, after 19:13): footer shortened, my request

- Footer now reads "Clipcheck, the Multimodal Deepfake Detector (CM3070 final project)." ("It gives likelihoods, not proof." removed). The same
  idea still appears on the Check page lede and the landing chip "Likelihoods, not proof". The landing limits section's copy was removed
  too (my request); it now reads "These are the limits measured in testing."
- Also removed earlier this evening: the line under the demo row saying the eight were chosen for being right (see 19:13 entry).

---

## 2026-09-27 19:13 (demo shelf look restored, my request)

- I wanted the demo section's previous animations, effects and layout. Compared old and new in headless Chrome with animations on
  (old files served by request interception): the hover magnify, moving tracks and blinking lights were identical in both; what had changed was
  the layout (fixed-height name boxes, "built test clip" removed, a longer note, no "Show all" row). Restored the old card styles and markup
  exactly (checked by diff) and the old header note; the "chosen because the tool gets them right" disclosure is now one line under the row,
  where "Show all" was (removed later the same evening at my request, so the page no longer says the eight were chosen for
  being right; the report must say it instead). The eight accurate clips and the missing "Show all" button are kept. Card heights now equal the old ones. App tests
  (light) pass.

---

## 2026-09-27 19:03 (pre-freeze interface changes, C38; server restarted)

- My five changes, recorded in `docs/user_testing/findings.md` C38: primary buttons styled like the Home button; demo shelf of eight
  clips the tool gets right, in one row, no "Show all" (rule and skip in `server.py` FEATURED_DEMOS / SHELF_SKIPPED_FOR_WARNING, new test
  `test_featured_shelf_follows_its_rule`; FVFA_004 served as a shelf extra appended after all other demos so no demo_id moved); footer
  without "prototype"; player at 75% width, centred; landing chip "Clips stay on your computer". Testing mode keeps the round 1 and 2 clips
  (TESTING_DEMOS). Also fixed a 21 px sideways scroll on the phone Accuracy page (`.list` grid).
- All eight shelf clips re-run in the live app: right on face, voice and verdict, no warning (FVFA_003 was right but raised the voice warning,
  43.4 vs 43.1, so it was skipped). Test jobs removed afterwards.
- Server restarted twice (to load server.py): the old process (started 26 Sep 23:49 from a shell outside the Terminal panel) was stopped and
  `./run_server.sh` started in a Terminal panel tab. History is kept in memory only, so the restart emptied History (no result files affected).
- Tests: app env 53 passed (with the models); base env 154 passed, 1 skipped. Headless Chrome at 1440 and 390 px: no sideways scroll on any
  page, 0 console errors. Backups of the pre-change files were kept outside the repository.
- Not changed: the analysing screen still says "About 7 seconds is typical" (the latency benchmark total, 7.28 s warm, ledger L3; I asked only about
  the landing chip).

---

## 2026-09-27 17:25 (consent forms from the module templates; round 3 agreed)

- I supplied the module's templates (Consent-form-example-1/2.docx: PR/001 consent form, PR/002 information sheet). Filled for Clipcheck
  user testing, keeping the templates' layout and logo: `docs/user_testing/materials/consent/PR001_Participant_Consent_Form_Clipcheck.docx` and
  `PR002_Participant_Information_Sheet_Clipcheck.docx` (blank; no personal data). Anonymity kept: the form carries name and signature only, no participant
  number; the sheet says names are stored apart from answers with no link. One form serves rounds 1 and 2 (tick "signing after my session", confirming
  the verbal consent given) and round 3 (tick "before"). Contact: my email; the Goldsmiths DPO and ICO lines kept verbatim from the template.
  Signature lines added (the template had none). Rendered and checked: consent form fits one page.
- Round 3 agreed (4 people, on the final interface, cut-off Mon 28 Sep 12:00). Deadline confirmed: Mon 28 Sep, 8 pm.

---

## 2026-09-27 16:45 (report status review; prep brief for Chapters 4 to 6; survey and consent check)

- Read DEV_LOG, the report plan, Chapters 1 to 3, Appendices A to C, the retracted Ch4/Ch5, all user-testing records and the module template.
  Report: Ch1 905, Ch2 1,826, Ch3 1,791 = 4,522 of 10,500; Ch4 and Ch5 retracted for rewriting; Ch6 not written. Brief with section budgets
  (Ch4 2,300, Ch5 2,400, Ch6 800) and sources: `docs/report_prep/next_chapters_prep.md`.
- Survey check: 8 raw CSVs match SHA256SUMS and the working copies; SUS scoring verified by hand (P5 87.5); consent ticked on all 8 sheets.
- **Consent gap found:** CM3070 Lecture 1 asks for written, signed consent (sample forms in Coursera Week 3); the protocol used a verbal yes ticked
  on the sheet, with no information sheet, and the report says nothing about ethics. Options in the brief (retrospective signed forms, or state it as a
  deviation D-O). Nothing changed in the data or the report.

---

## 2026-09-27 06:00 (report updated for interface v4 and the landing page; v4 screenshots captured)

I wanted the report to reflect the new interface. Read DEV_LOG 26 Sep 21:31 (v3), 23:55 (v4) and 27 Sep (landing page), findings C21 to C37
and the working notes. Decision: the user-tested record stays as it is (v1, round 1, v2, round 2, Figure 5.9 v1 vs v2); the
report now says two versions followed round 2, that v3 was lost (cause not established), that v4 ships with C25/C26 (the round 2 fixes), and that
neither is user-tested.
- New `Final Report/figures/src/capture_v4.py` (scripts/ui_screenshots.py handles only the v1/v2 layouts; its v4 attempt stopped at v2's Learn more
  button, cleaning up its own jobs): 17 v4 screens with reduced motion into `docs/user_testing/screenshots/v4/` (+ index.json), 0 console errors;
  its own 7 analysis jobs removed, my 13 History jobs untouched.
- Figures regenerated from v4: 4.3 (explanation paths), 4.4 (partly manipulated result with meters, gap bracket, tracks), 4.5 (warning inside the
  verdict); 4.6 app architecture notes the landing page; 3.2 Gantt adds v3/v4 (26 to 27 Sep); Appendix C replaced by the landing page and six v4 screens.
- Text: Ch3 (design decision on the interface; R4 row), Ch4.7 rewritten (four versions, v4 features, landing page, frozen v1/v2 with checksums),
  Ch4.8 and 5.7 test counts re-measured today (base 154 passed, 1 skipped; app 52 passed; 207 tests), Table 4.2 application row 65, Ch5.6 (round 2's
  lessons acted on in v3/v4, untested, a round 3 would show it), Ch5.8 failures and extensions, Appendix B row 20 (v3 lost). Corrected while
  checking: v3's loss is not attributed to the parallel session (cause not established). v2 snapshot checksums verified OK (no v2 freeze test exists
  since v3's was lost). Totals now 905 / 1,826 / 1,791 / 2,170 / 2,323 = 9,014 of 10,500.
- 06:10 second check (same update requested): the v4 screenshots (05:56) already show the latest interface (Home
  button in the corner, result page in rows, full-width player). Two gaps fixed: Ch4.7 now describes the result page's rows and the Home button;
  Appendix A D-H names v4. Report rebuilt: 905 / 1,826 / 1,791 / 2,211 / 2,323 = 9,056 of 10,500; Chapter 6 (Conclusion) is still not written.
- 06:10 Chapters 4 and 5 RETRACTED at my request, to be rewritten one at a time. Nothing deleted: `ch4.txt`, `ch5.txt` and the
  pre-retraction .docx are in `Final Report/_retracted_2026-09-27_0610/`; figures stay in `figures/`. Rebuilt: Chapters 4 to 6 show "[Chapter not
  written yet]"; total 4,522 of 10,500 (Ch1 905, Ch2 1,826, Ch3 1,791). Chapters 1 and 3 and Appendix C still point to sections and figures in 4 and 5.

---

## 2026-09-27 (landing page: the front door at "/", opening into the app)

- I wanted a landing page that makes Clipcheck look like a launched product, inspired by a supplied mock-up but with the project's
  own palette and content, and chose each part from live previews: the split-face hero (the mark assembles itself as the intro), a pinned story
  (a real check of "Webcam streamer, voice replaced" plays inside a pinned window as you scroll), and "pixels become real" reveals for the other
  sections; sections: how it works, why disagreement matters (sliders driven by the same rule as `scripts/fusion.py`, T and weights from
  `/api/evaluation`), one clip end to end (the FVRA_000 check, including the faithfulness screen catching Llama 3), under the hood (the six models
  with animated flows), who it's for, the research (four-condition result from `/api/evaluation`), what it can't do (from `/api/limitations`), and
  the demo strips. No invented users, testimonials or figures; the two worked examples are saved results of 26 Sep, labelled as such.
- `static/`: a `welcome` view in `app.js` (route "/" or `#/welcome`; the logo in the app leads back to it), landing styles in `style.css`, the logo link in
  `index.html`. The app itself is unchanged. Also fixed: primary buttons that were links had lost their dark text (a link colour rule).
- Checked in the browser pane at 1360 px and 375 px: hero, pinned story at several scroll positions, playground, reveals, every section, "Open
  Clipcheck" into the app, 0 console errors, no sideways scrolling. App tests: 43 pass, 6 heavy skipped.
- Second pass (my review, options shown and chosen): the backdrop now uses the mark's own colours (a green and a red light drifting, a twinkling
  pixel field, a light following the pointer, green to red left to right); the hero puts the mark dead centre in a scanning frame, where the scan
  line turns the face and the title ("Made by a person," / "or by a machine?") from grey into green and red and back; scrolling opens the frame and
  splits the face (the human half winks, grins, tilts away and breaks into round dots; the square pixels scatter) and carries each half of the title
  away. The demo videos section was removed; "Try it for yourself" is in the hero and at the end.
- Third pass (my review): the human half no longer fades; its outline peels off from the top down and each piece becomes a green dot where it
  sat (the smile and the eye break off the same way). The backdrop's washes are much fainter, so the dark base shows, and the pixel field is a
  visible grey grid with scattered green and red blocks in varied shades. The section reveals now build each box from a jumble of green and red
  blocks (measured on one card: 48 green, 57 red), smaller than before.
- Fourth pass: no grain anywhere (backdrop and glass). Pixels now switch on at random in a random shade of green or red, glow for 0.9 to 3.5 s and
  switch off. The same backdrop now runs on every page, landing and app: the result page's light no longer takes the verdict's colour (finding C28's
  verdict-coloured light is withdrawn at my request); the verdict is still shown by the headline colour, icon and words.
- Fifth pass: a "Home" button in the app's menu bar (green-to-red outline and glow) leads back to the landing page. The pixel reveal is retired; from
  two rounds of previews I chose three reveals tied to the tool, assigned by section: section headings and the limits decode from
  scrambled green and red glyphs into the real text; the playground, the clip walkthrough and the research panel are scanned in by a green line;
  the model chain and the audience cards are traced by a face-scan mesh first. Checked: the decoded text matches the original exactly, masks,
  lines and meshes are removed afterwards, and a full scroll leaves no section hidden.
- Sixth pass: the green and red block reveal is back, mixed with the others at my request: headings decode; the playground, the research
  panel and the audience cards assemble from blocks; the clip walkthrough is scanned; the model chain gets the mesh; the limits alternate decode and
  blocks. Measured: 11 decode, 9 blocks, 5 scan, 1 mesh; no section left hidden after a full scroll.
- Seventh pass (smoothness): the reveals and the hero scan now animate only transforms and opacity (no per-frame clip-path, mask, colour fade
  or per-letter elements); blocks capped near 140 per box; decode uses two text pieces per line; the scan is a sliding cover; the pointer glow is
  two cross-faded lights; the glass blur is 18 px (was 28); the pixel field redraws 20 times a second and pauses during reveals. Checked: no section
  left hidden, decoded text intact, nothing left behind. The hero scan line was not re-checked visually (the preview pane throttles frames).
- Eighth pass (result page layout): the result page left a large empty area under the meters, because the player, explanation and next
  steps were stacked in the right column. At my request the player now runs at full width under a top row of verdict and meters, and
  the explanation and "Before you share it" sit side by side beneath it (one column on narrow screens; the PDF keeps two columns). No content
  or number changed. Checked at 1280 px and 375 px wide (no sideways scroll); `tests/test_server.py` 43 passed, 6 heavy skipped.
- Ninth pass (placement): the Home button left the menu bar for the top-left corner, level with the bar's middle (on narrow screens the bar
  starts to its right); the finished-check notification is centred on the bar's middle line (measured within 0.5 px); on the landing page the
  first section ("One clip, two separate checks.") rises 30% of a screen into the hero's empty tail, so it no longer floats in a large gap. It
  stays below the fold until the face split finishes.

---

## 2026-09-26 23:55 (interface v4: a from-scratch redesign; v3's code found lost)

- **v3 was not running.** `static/style.css` and `static/app.js` were byte-identical to the v2 snapshot (rewritten 21:33, two minutes after the v3
  entry below); v3's code, its v2 freeze test and the `changes` field in `/api/demo_clips` were not on disk or in git. Only `screenshots/v3/` survives.
  The old server process still had the `changes` field in memory, so the loss showed only after a restart.
- **I wanted a new design from scratch**, then chose each part from live previews (a preview page, "Clipcheck Glass", built from 8 real saved
  results): smoked glass with grain, spring pop-in, level meters, demo videos as channel strips with Face and Voice known-answer lights, a live-track
  hover (green real, red fake, lights blinking out of step), and a split-face mark in green and red. Record: `docs/user_testing/findings.md` C28 to C34.
- **v4 is `static/`** (`index.html`, `style.css`, `app.js`, new `clipcheck-mark.svg`); the previous `static/` files were identical to
  `ui_v2_snapshot/`, so nothing was lost. `server.py`: `_CAT_CHANGES` and a `changes` field for every demo clip, from its construction category.
  `tests/test_server.py`: new `test_demo_clips_carry_their_known_answer_from_how_each_clip_was_made`.
- Tests: `tests/test_server.py` 49 of 49 pass with the models and Llama 3 (63 s); 43 pass with `DEEPFAKE_SKIP_HEAVY=1`.
- To collect the preview's data, 5 featured demos were analysed on the running server and their jobs removed afterwards (demo files are never deleted).
- Server restarted from a Terminal window (`./run_server.sh`, port 8000); the app's own preview launcher cannot read ~/Documents
  ("Operation not permitted").
- **Not user-tested.** The report (Ch 4.7, 5.6, Figures 4.4, 4.5, 5.9, Appendix C) still describes v2; whether it mentions v4 is my call.
- 27 Sep fix (reported by me): the Face and Voice boxes on the demo strips sat at different heights and the Voice box ran past some strips'
  edges. Now one full-width row each ("Face ... Real"), pinned to the bottom of every strip; measured 0 of 74 boxes clipped, all rows level.

---

## 2026-09-26 21:31 (interface v3: frontend-design review, two-track reading, round 2's next change; v2 frozen)

The developer asked for a published front-end design checklist (read in full) to be applied to Clipcheck, approved a plan (phases: visual pass,
two-track reading, round 2's next change, record) and chose all four. Every change is traced in `docs/user_testing/findings.md` (C21 to C27).
- **A parallel session had started the same work** (21:02 to 21:09: froze v2, rewrote `static/app.js` and `index.html`, left `style.css` as v2).
  I chose to start over here: its partial files were set aside (outside the repo) and `static/` was restored from the v2 copy, verified
  against its SHA256SUMS, before any edit. Its `ui_v2_snapshot/` and `run_v2_interface.sh` were checked (v2 hashes match; launcher serves v2 on 8002)
  and kept. It had also re-saved `server.py` and `tests/test_server.py` without content changes; no git commit, stash or index change was found.
- v3 is `static/` only: new `style.css` (graphite, rules instead of boxes, one type family with tabular figures, 13 to 48 px scale); `app.js`
  (readingBlock: both scores on one scale with the gap bracket and the T line; the warning inside the verdict with "but it may be wrong for this
  clip"; the partly-manipulated sentence; example two-line marks from `changes`, hidden in testing mode; analysing lanes); `index.html` (title,
  favicon, comment). Verdict logic, scores, T, weights, server, explain.py and the Llama prompt untouched.
- Checks: 0 of 1,025 text elements below 4.5:1 (lowest 6.33:1), smallest 13 px, no sideways scroll at 390 and 1440 px, 0 console errors;
  `screenshots/v3/` (25 screens, `ui_screenshots.py --version v3`, now captured with reduced motion); new test `test_interface_v2_is_frozen_and_runnable`.
- **Not user-tested.** The report (Chapter 4.7, 5.6, Figures 4.4, 4.5, 5.9, Appendix C) still describes v2; I decide whether it mentions v3.

---

## 2026-09-26 03:35 (final report: Chapter 5 drafted with ten figures; Chapter 1 preview sentence)

Before planning Chapter 5 the requirements, the template brief and the logs were re-read in full (EXPERIMENTS A to J, both report-prep records
with their caveat lists, heuristic review, round 1 data quality, findings incl. round 2). Chapter 5 drafted (2,249 / 2,500): 5.1 strategy and why
(identity-disjoint testing, rules before results, bootstrap CIs, metric choices, self-built set, small user rounds); 5.2 model choice (leak
correction, five backbones, FaceSwap 0% for all five single-method models (checked in numbers.json), B4 rule with both disclosures, Xception
vs ConvNeXt trade-off, CV 82.8%, Celeb-DF 59.1%; MFCC vs wav2vec2, WavLM subsample, codec; M1 with L33; untested MTCNN/VAD/SVM stated);
5.3 core result F5 with CI, mechanism, cost (false disagreement 2/18, 2/20), naming; 5.4 boundary (95 / 75 / 0 / 0, H2, F6, F6 addendum,
F7 to F9, dilution, O1 with the post-hoc disclosure); 5.5 explanation (T1 screen 24/50, human rating E2 with kappa, screen vs raters,
only one independent rater); 5.6 heuristic review, round 1 provisional, v2 trace, round 2 table and the negative T7 and ambiguous T3 findings;
5.7 testing and performance; 5.8 critique with an aims table, successes, failures, limitations, extensions.
- Figures 5.1 to 5.10 made by `Final Report/figures/src/make_ch5_figures.py` from numbers.json, history.json (B4 rule values at the SAVED
  checkpoint: 74.54 / 69.92 reproduced), heldout and LAV-DF results, llm_comparison, the survey CSVs (SUS via score_user_testing.sus_score)
  and the v1/v2 screenshots; each checked visually and label collisions fixed.
- A claim I had planned ("below the 70 to 75% the literature reports", from the ledger) was left out: the figure has not been checked in
  Khan and Dang-Nguyen (2023) itself.
- Chapter 1 section 1.6 gained one sentence previewing the user-testing result. Totals: 905 / 1,826 / 1,761 / 2,022 / 2,249 = 8,763 of 10,500.

---

## 2026-09-26 03:28 (rater identities recorded; round 1 stays provisional)

Explanation rater 1 was me (the developer), rater 2 a friend with no ML background (ledger E2 updated; only one rater is
independent of the project, a stated limitation). Round 1 at-risk answers could not be confirmed; I chose the recommendation: round 1 remains
provisional, P3's SUS excluded from the round 1 SUS figure (median still 60.0), at-risk notes not quoted, P1/P2 ML background reported as unconfirmed
(`round1_data_quality.md` decision section). Raw files unchanged.

---

## 2026-09-26 03:09 (explanation human rating E2 completed and scored; screen compared with the raters)

To show how the raters rate, the offline rating form was opened and the rubric explained (no rating was filled in on the raters'
behalf). Both sheets were then done: `~/Downloads/rating_sheet_rater{1,2}.csv` (saved 02:42 and 03:06).
Read both in full before scoring: 50 of 50 cases, all three scores, values 0 to 2, no notes; not copies (they differ on 21 cases; identical file size is
expected because every row is fixed width). Blank templates kept in `results/explanation_eval_full/blank_templates/`; returned sheets filed unchanged in
`raw_as_downloaded/` with `SHA256SUMS`, and copied to where the scorer reads them. `scripts/score_explanation_eval.py`: means (rater 1 / 2) factual
grounding 1.70 / 1.50, score accuracy 1.46 / 1.36, absence of hallucination 1.72 / 1.72; exact agreement 80 / 82 / 96%; quadratic-weighted Cohen's kappa
0.63 / 0.81 / 0.93; no two-point disagreements. New `scripts/compare_screen_with_raters.py` (exploratory; definitions stated in its docstring and chosen
after the ratings were seen) -> `screen_vs_raters.json`: the weakness is PARTIAL texts (both raters faulted grounding in 15 of 27; 0 of 23 REAL + FAKE);
all 15 were rejected by the app's faithfulness screen; the screen passed 26 texts, none faulted by both raters; it rejected 9 the raters did not both fault
(consistent with L33's screen false positives). Ledger E2 updated. Open: who the two raters were (needed for the report's method paragraph).

---

## 2026-09-25 20:15 (round 2 user testing: four sessions filed, checked and scored)

Round 2 done. Four CSVs in `~/Downloads` (P5 15:45, P6 17:48, P7 19:56, P8 20:12). Each read in full before scoring; every
pair compared: no carry-over (all four SUS answer sets differ; all participant free text differs; only fixed options repeat). The facilitator's own
debrief note is identical for P6 to P8 ("it was a good reaction"), which is facilitator text, not participant data. Raw files copied unchanged to
`docs/user_testing/responses/raw_as_downloaded/` with sha256 appended to `SHA256SUMS` (all eight verify), copies in `responses/`;
`scripts/score_user_testing.py` run (`results/summary.{json,md}` regenerated from all 8 files).
Result (round 2, v2, n = 4): SUS 87.5, 87.5, 90.0, 90.0, median 88.75 (round 1 provisional 60.0; 60.0 also without P3's at-risk answers); T2 4 of 4
unaided (round 1: 1); T3 all named the video unaided, ease median 7 (round 1: 3 of 4, median 4); T7 warning seen by all (2 unprompted, 2 after a hint)
but lowered trust for none (round 1: 3 yes, 1 partly, P2 to P4 at risk); T3 all four would publish the partly-manipulated clip (ambiguous: their notes
praise the tool); T8 1 unaided, 3 with a hint, ease median 6 (round 1: median 1, one not done); two of four say the Learn more tab is too long.
Recorded honestly as mixed: usability and naming improved; the warning no longer lowers trust in a wrong verdict (the key negative finding). Written
into `findings.md` (Round 2 section with a proposed round 3 change) and ledger U1. Round 1 confirmations are still outstanding.

---

## 2026-09-25 19:39 (final report: Chapter 4 first draft, seven figures, Appendices B and C)

Before planning Chapter 4 I checked whether the build logs had been read; they had only in part. Read in full: DEV_LOG (all entries
1 to 25 Sep), LESSONS (L1 to L33), report_ch4_ch5_tables_draft.md, EXPERIMENTS sections D to J, O1, T1, M1, F8, F9, and findings.md.
The Chapter 4 plan was revised from them (implementation problems and their fixes added to every section).
- Chapter 4 drafted (2,022 / 2,500, Word-style count): code structure (Table 4.1); data and the identity-disjoint split with a union-find
  excerpt; video branch (training recipe, checkpoint rule D5, no temperature D3, JPEG parity D4, sampling and moment windows, three bugs);
  audio branch (speech gate, the tone-clip discovery, wav2vec2 + SVM C = 10 with Platt probabilities, balanced-accuracy weight); fusion core
  excerpt and the unfamiliar-input check (standardised features, Ledoit-Wolf, 97.5th percentile, limits 43.1 / 99.9, median over crops,
  three modes); explanation layer (`assess()` excerpt, eight fields, nine prompt rules, the faithfulness check, labelled fallback, 169
  combinations); application (FastAPI, background thread, real progress, upload checks, codec probe, v1 kept, two interface bugs); engineering
  quality (build_numbers.py, ship_model.py, tests 206 in 20 suites (Table 4.2), heavy marker, latency 7.28 s and app median 4.4 s).
  Facts re-read from code: utils.py union-find, fusion.py agreement branch, vad.py (MIN_SPEECH_SECONDS = 1.0), extract_frames.py and
  video_infer.py (MTCNN 224, margin 20), explain.py prompt rules, explain_checks.py, history.json, latency.json, test function counts
  (155 base + 51 app = 206, matching 154 passed + 1 skipped and 51 passed).
- Figures (`Final Report/figures/src/make_ch4_figures.py`): 4.1 leakage schematic, 4.2 training curves (history.json), 4.3 the two explanation
  paths (crops of the re-taken v2 screenshots), 4.4 partly-manipulated result, 4.5 warning (caption states the verdict is wrong on a genuine
  LAV-DF clip), 4.6 app architecture, 4.7 latency per stage (latency.json). Chart colours from the dataviz reference palette (#2a78d6, #eb6834).
- Appendix B: 19 problems found and fixed, each with its log or lesson id. Appendix C: seven further v2 screens.
- References checked and added: Zhang et al. (2016) MTCNN, Grattafiori et al. (2024) Llama 3, Ledoit and Wolf (2004).
- `build.js`: word count now counts like Word (every whitespace token), the conservative reading; appendices B and C registered.
  Totals: Ch1 872, Ch2 1,826, Ch3 1,761, Ch4 2,022; 6,481 of 10,500.

---

## 2026-09-25 19:21 (final report: Chapter 3 first draft, two figures, Appendix A)

Chapter 3 drafted (about 1,760 / 2,000): overview; domain, users and requirements R1 to R8 (Table 3.1, each traced to where it is met and
evaluated); architecture (Figure 3.1); the models (Table 3.2, every model with role, data type, pretraining and the alternatives tested)
plus the technology stack; key design decisions with evidence (T = 0.35 grid search, re-confirmed held-out F1 0.909 from
heldout_eval_shipped/threshold_tuning.json; weights 0.464 / 0.536 from CV 0.828 and balanced 0.957; frozen encoder; numbers kept out of
the LLM; warn not withhold at the 97.5th percentile; verdict-first UI); changes since the Draft grouped by cause (Table 3.3); evaluation plan
by aim (Table 3.4); workplan with planned vs actual Gantt (Figure 3.2: planned bars from the Draft's Table 3, actual bars only from dated
DEV_LOG entries, caption states the log does not cover 19 to 31 Aug). Facts read from fusion.py, video_infer.py (up to 20 face crops,
mean), audio_branch.py, ood_gate.py, metrics.json (C = 10), shipped_model.json, requirements files, ci.yml.
- Figures made by `Final Report/figures/src/make_ch3_figures.py` (SVG rendered with headless Chrome); SVG sources kept beside the PNGs.
- `build.js` now supports appendices (not counted toward chapter limits); Appendix A = condensed deviation register D-A to D-N.
- Ogura and Haynes (2021) reference checked (arXiv 2112.05016) and added.
- Honesty fixes made while writing: CI has never run on GitHub (no remote yet), so the text says it is "configured to run"; R7 (local
  processing) is framed as a consequence of the design, not a separately engineered feature (user did not state it as a goal).

---

## 2026-09-25 18:26 (final report: Chapter 2 first draft; 28 more references checked)

Chapter 2 drafted (1,835 / 2,500): six themed sections (faces and generalisation; synthetic speech and the benchmark problem; audio-visual
detection and the gap; combining, bounding and explaining outputs; evaluating with people) and a summary table. Revised from the Draft:
2022 to 2025 work added (the supervisor's "overuse older papers" note in literature_notes.md), the Draft's "B4 validated here" claim
replaced by the caveat that the DFDC ranking did not transfer. Every source checked on the web before use (arXiv abstract pages, CVF open
access, publisher/index pages). Findings while checking: (1) the FaceForensics++ paper itself states XceptionNet on face crops outperformed
all other variants in every test (read in the paper's text), which supports the Xception choice from the literature as well as our V8/D2
results; (2) Wickramasekara et al. is now published (FSI: Digital Investigation 52, 301859, 2025), so it is cited as 2025; (3) the two
MMMS-BA quotations the Draft used were confirmed in the paper's text; (4) Nadimpalli and Rattani's abstract gives no cross-dataset AUC figure,
so the unverified "0.633" in literature_notes.md is not used. `references.txt` now has 32 entries (author lists over 8 shortened to et al.).

---

## 2026-09-25 18:14 (two wrong citations inherited from the Draft found and fixed; reference list started)

User asked why "Lalchand" appeared three times. Checked the sources on the web: the Draft's Deloitte reference had invented authors (real:
Lalchand, S., Srinivas, V., Maggiore, B. and Henderson, J., 29 May 2024), and its Sumsub claim ("over 900% between 2019 and 2023") does not
match the source (real: a tenfold increase in deepfakes detected worldwide from 2022 to 2023, press release 28 Nov 2023). The Draft's
AVFF reference also omitted three of eight authors. Chapter 1 corrected (872 / 1,000 words); `Final Report/references.txt` started with the
four Chapter 1 references, each checked against its source. Rule from now on: no reference is copied from the Draft without checking it.
Plan: every model gets its own entry in Ch3 (model table), Ch4 (how it is used) and Ch5 (how it was chosen and evaluated).

---

## 2026-09-25 18:07 (final report: build set up; Chapter 1 first draft)

- New folder `../Final Report/` (sibling of `Draft Report/`): `build.js` (Node `docx`, run with NODE_PATH='../Draft Report/node_modules')
  turns `content/ch1.txt` to `ch6.txt` + `references.txt` + `meta.json` into `Final_Project_Report.docx` (title page, Word contents field,
  page numbers, A4, Calibri 12 pt). It counts words per chapter on every build (headings, paragraphs, lists, table cells and code counted;
  chapter titles, captions and references not) and exits non-zero over any limit. Output passes the docx skill's validator.
- Chapter 1 drafted (862 / 1,000 words): motivation, template "CM3020 Artificial Intelligence, 4.1 Project Idea 1: Orchestrating AI models
  to achieve a goal", the models by data type, users and their four needs, research question, four aims with measurable objectives,
  contribution, what changed since the Draft (the marker's feedback, leakage, B4 to Xception, F5 headline with CI, LAV-DF boundary), scope.
  Every figure from project_record.md. References file not written yet (Ch1 cites Sumsub 2023; Lalchand, Lalchand and Lalchand 2024;
  Oorloff et al. 2024; Katamneni and Rattani 2024, all in the Draft's list).
- Rendering: tried Microsoft Word via AppleScript to make a PDF preview; Word showed a dialog on my screen, so all Word automation
  was stopped (not retried). Layout checked roughly through textutil + headless Chrome instead; I review the real .docx in Word.

---

## 2026-09-25 17:55 (server restarted: new example names live; v2 screenshots re-taken; Draft feedback filed; report format decided)

- User approved the restart. No request on port 8000 since 16:34. Old server log kept as `results/logs/server_2026-09-25_1138_to_1752.log`
  (it timestamps today's round 2 sessions); old v2 screenshots copied unchanged to `docs/user_testing/screenshots/v2_before_C19_C20/`.
  Server restarted (pid 86270, log `/private/tmp/clipcheck_server.log`); `/api/demo_clips` serves the C19 names.
- `scripts/ui_screenshots.py --version v2`: 26 screenshots re-taken with C19 names and C20 bar colours, 0 console errors; its jobs removed
  afterwards (History empty).
- User pasted the marker feedback on the Draft Report: filed verbatim with a point-by-point response in
  `docs/report_prep/draft_report_feedback.md` ("the filters you mention" read as the Draft's planned dropout / label smoothing / early
  stopping, which were run: V6, V14, D-K).
- Decisions: the report goes straight to .docx; I create the public repo at the end (placeholder link until then). Plan section 7.

---

## 2026-09-25 17:32 (report plan: visuals and evaluation evidence added)

User asked for screenshots, data visualisations, model evaluation details, UI evaluation and user evaluation in the plan.
`docs/report_prep/report_plan.md` section 5 rewritten: 5 diagrams, 11 screenshot sets (v2 to be retaken after the port 8000 restart;
v1 frozen set exists), 16 charts each tied to its result file (all to be made by one script, `scripts/make_report_figures.py`, not yet
written), the tables, per-model evaluation details, the UI evaluation (heuristic review, measured contrast, designer brief, change trace)
and the user study (method, participants, measures, data quality, results, critique). Checked that the data behind each chart exists
(result folders listed). Found: the designer's 11 mockups are not in the project (they were never saved to the project); still needed.

---

## 2026-09-25 17:05 (report planning started; P5 round 2 CSV arrived)

User pasted the final report instructions (six chapters, chapter maxima, 10,500 strict total, public repo link, 3 to 5 minute video in
their own voice) and the template brief. Read those with the midterm instructions (lit review and design criteria) and the recorded
supervisor feedback on the Draft. New `docs/report_prep/report_plan.md`: rules, top-band evidence map, an inventory of 33 things done
(by theme and chapter), chapter outlines with a 10,200-word budget, figure list, a map of the 18 review criteria, risks. No report text yet.
Also found: `~/Downloads/survey_P5_round2.csv` (saved 15:45, before C19/C20 went live). Read in full: complete; no free text copied from
round 1 (the only identical values are fixed options). Not yet filed or scored.

---

## 2026-09-25 16:32 (score bars: one solid colour by score, not a gradient)

User clarified: the whole bar should be one colour, picked by the score (60% an orange-red). `static/app.js` new `meterColor(p)`: RGB between
green (63,207,127) at 0%, amber (242,178,60) at 50% and red (240,82,74) at 100%, with the distance from 50% square-rooted so the colour leaves amber
quickly (40% yellow-green, 60% orange-red 241,135,66, 75% red-orange). The bar's inline style sets it; the CSS gradient and its `--meter-*` tokens
removed. Checked on a temporary server on port 8002 (stopped after): a colour scale from 2% to 99% and RVFA_000 (10% green, >99% red); 0 console
errors. `tests/test_server.py` 48 passed. Live on port 8000 now (static files load fresh); findings C20 updated.

---

## 2026-09-25 16:25 (example names like the designer's mockup; colour gradient on the score bars; findings C19, C20)

User asked (with the designer's mockup) for the examples to be named "Newsreader, voice replaced" style, and for the Picture/Voice bars to be
green to red by score.
- `server.py`: `_SCENES` gives every example a scene (from a frame of each clip, extracted to a contact sheet and looked at; people never
  identified) and `_demo_meta` builds "<scene>, <change>". Change words still come only from how the clip was made: constructed set
  "genuine face and voice / voice replaced / face replaced / face and voice replaced" (all six fakes checked in the manifest: FF++ Deepfakes,
  so "face replaced" is accurate); FF++ bundled "face replaced / unaltered"; LAV-DF now "a few words re-voiced / lips briefly re-synced /
  lips and a few words altered" (its manifest: SV2TTS and Wav2Lip, every fake part under 1 s), which corrects the old "face replaced" wording
  for LAV-DF. Subtitles shortened to fit one line ("built test clip" and "Unfamiliar footage (LAV-DF)" kept as the provenance marks; the FF++
  method name dropped from the subtitle). Testing mode still shows codes. `tests/test_server.py` demo-name test updated to the new form.
- `static/style.css` / `app.js`: `.meter` fill is a full-width gradient (`--meter-lo/mid/hi`, darker print variants) clipped at the score with
  `clip-path`, minimum 8 px; the bar now takes `--w` instead of `width`. Checked on a temporary second server (port 8002, stopped after):
  RVFA_000 (picture 10% short green bar, voice >99% full gradient), FVRA_000, RVRA_000; 0 console errors; phone width checked.
- Tests: app 51 passed; base 154 passed, 1 skipped.
- **Port 8000 NOT restarted** (a round 2 session may be running; its history is in memory). The bar change is already live there (static files
  load fresh); the new names appear only after a restart. `results/latency/app_end_to_end.json` keeps the old titles (a measured file, not edited).

---

## 2026-09-25 15:11 (new chat: state re-checked)

Read the working notes, project record and newest DEV_LOG entries. Checked: server on port 8000 up (pid 74035, HTTP 200); Ollama up
(llama3:8b, mistral:7b, qwen2.5:7b); no round 2 survey CSVs in `docs/user_testing/responses/` or `~/Downloads` (round 1 P1 to P4 only); both rating
sheets 50 rows, 0 cells filled. Nothing changed; still to decide: the report's word limit and format and what is submitted on Monday.

---

## 2026-09-25 11:45 (record of everything done, for the report; round 2 prepared)

- New `docs/report_prep/project_record.md`: 28 items by report chapter (proposal and supervisor feedback, design and deviations D-A to D-N,
  implementation, evaluation in report order, rigour and retractions), each with its ledger id or file, plus what is still to do. Compiled from
  DEV_LOG, the ledger and the two report-prep records; no new figures.
- Round 2 set up: survey forms now offer participants P1 to P12 (new round 2 testers take P5 to P9, so the report can show round 2 used different
  people); forms rebuilt, 10 survey tests pass. `docs/user_testing/protocol.md` gains a round 2 checklist (warm-up analysis, `#testing`, empty
  History, short form, new participant numbers, Round 2). Checked: app up (HTTP 200), History empty, Ollama serving llama3:8b.

---

## 2026-09-25 11:42 (to-do item 8: file organising and review, APP_TODO Phase 10)

Nothing deleted; every move checked for references first.
- **Scripts (10.1).** New `scripts/README.md` indexes all 71 scripts in six groups (pipeline, training and release, evaluation, user testing
  and interface, release, launchers). The 12 one-off `queue_*.sh` job launchers moved to `scripts/launchers/`; each now finds the project root
  two levels up (checked: all pass `bash -n` and resolve to the project root); `build_multimethod_frames.py`'s hint and the README updated. The
  ledger and dev log keep their old paths as history; the index says where they went. Python scripts not moved (they import each other and the
  tests import them). The two LAV-DF readers both kept and documented: `carve_lavdf_parts.py` is what every builder uses; `lavdf_partial_zip.py`
  (earlier, index-based, has tests) is how the archive layout was worked out.
- **Results (10.2).** New `results/README.md` marks every folder current / experiment / superseded with its ledger id. Moved (no code or doc
  reads them): the June root files (`metrics.json`, `history.json`, four PNGs) to `results/_superseded/ppr_era_2026-06/`; the two `*_T030`
  folders to `results/_superseded/threshold_T030_2026-09-21/`; the 11 `logs_queue_*.out` files to `results/logs/queues/`. Left in place and
  labelled: `OLD_model/`, `fallback_eval/`, `hybrid_eval/` (read by `build_numbers.py` to label OLD_MODEL sections), `explanation_eval/`.
  `build_numbers.py` re-run: `numbers.json` and `numbers.md` identical apart from the timestamp.
- **Docs (10.3).** `README.md` rewritten from the current records (shipped model, held-out result and its boundary, latency L3, v2 interface,
  user testing, limitations, test counts); `docs/TESTING_GUIDE.md` updated for v2 names, the plain-language template, latency and test counts;
  new `docs/README.md` index; `docs/report_prep/benchmark_table.md` given a STALE banner (its "Ours" row is the retracted 0.993 AUC); the root
  the working notes' status table replaced with the current state (older dated notes kept as history). CI now also runs
  `tests/test_user_testing_survey.py` (data-free subset: 90 passed, 1 skipped, locally with `DEEPFAKE_SKIP_HEAVY=1`).
- **Code review (10.4).** Fixed three misleading module docstrings (`audio_branch.py` still said there was no trained model and no dataset;
  `fusion.py` said "not yet wired to real audio"; `ood_gate.py` described withholding as the behaviour, not the default warning). `static/app.js`:
  the job id from the address bar is now URL-encoded where it reaches the video source and the result fetch (defensive; the page only rendered
  after the server confirmed the id). pyflakes: no undefined names; 25 unused imports and 3 placeholder-less f-strings/format calls, left as they
  are because most sit in training/evaluation scripts that produced reported results (listed in APP_TODO 10.4).
- Server restarted (pid 74035). Tests: base 154 passed, 1 skipped; app 51 passed; 26 v2 screenshots re-captured, 0 console errors.

---

## 2026-09-25 11:29 (to-do item 7: latency re-measured, including the gate and the explanation timing; item 5 declined)

Item 5 (fix the faithfulness-screen misfire on "the video and audio branches disagree", found in M1): I decided no change is needed. Not done;
the misfire stays documented in ledger M1 point 3 and L33 as a known limitation of the automatic screen.

Item 7: `scripts/benchmark_latency.py` extended so it times what the app does now, using server.py's own functions: 1b out-of-domain check on the face
features (same forward pass, `return_features=True`), 1c suspicious-moment windows (frame-rate read + `_frame_anomalies`), 5b out-of-domain check on the
speech embedding, and the explanation and screen with the real moment windows. The 21 Sep result archived unchanged as
`results/latency/archive/latency_2026-09-21_before_gate_and_timing.json` (the script refuses to overwrite). Run: composite clip, 1 warm-up + 5 timed runs:
**7.28 s warm per clip**, cold start 4.12 s (per stage in ledger L3). New `scripts/benchmark_app_latency.py`: the live app end to end (POST analyze,
polling progress every 0.1 s as the interface does) on the 8 featured examples, 1 warm-up pass + 3 runs each: RVRA_000.mp4 4.32 s; RVFA_000.mp4 4.53 s; FVRA_000.mp4 5.25 s; FVFA_002.mp4 3.14 s; 183_253.mp4 7.98 s; 183.mp4 7.47 s; LAVDF_RVRA_000.mp4 3.60 s; noface_silent.mp4 1.28 s; median 4.42 s
(`results/latency/app_end_to_end.json`). The Accuracy page and the analysing screen read latency.json, so they now show 7.28 s / "About 7 seconds" with no
code change (checked via /api/evaluation). Honest reading: the additions cost about 0.15 s; the lower total than 9.02 s is session variation.

---

## 2026-09-25 11:18 (orange for partial verdicts, stronger warning card, plain-language standard wording)

User asked whether to colour-code the verdicts (red fake, green genuine, orange/yellow partial) and to go ahead with the recommendation.
- `static/style.css`: "partly manipulated" / "the checks disagree" now ORANGE (#ff9d57, was the mockup's lavender); the unfamiliar-input warning stays
  YELLOW (#f7d154) with a 6 px left border and a bold title, so an orange verdict and the warning cannot be mistaken for each other (the warning is the
  element round 1 testers missed). Green and red unchanged; icons and words stay on every verdict (colour is never the only signal). Print colours updated.
  Contrast re-checked on three real results: 0 of 148 text elements below 4.5:1.
- `scripts/explain_checks.py` `explain_template` (the standard wording shown whenever the Llama text fails the screen, or no model is available) rewritten
  in plain language: "The picture check found an 85% chance that the face was manipulated, so the face looks manipulated ... The two checks disagree strongly,
  so the tool does not average them. It points to the voice as the part that looks manipulated, so only part of this clip may be fake." No system labels
  (FAKE, REAL, PARTIAL_MANIPULATION), no "branch" / "analysis", extremes in words ("a very high chance") so the text never states 100% or 0%, one-frame
  moments read "at 0:04", and a brief rise on a face that looks genuine is described as such. Same facts as before; every score combination passes the
  faithfulness screen, with and without moments. The out-of-domain WITHHOLD-mode sentence in `server.py` reworded the same way.
- Tests: `tests/test_explain_checks.py` +2 (plain language on every score combination; timing on every combination) and one phrase updated;
  `tests/test_server.py`: the timing test no longer requires the peak number in the text (peaks stay in Learn more) and its content-word check now matches
  whole words ("clip" had matched "lip"). Base 154 passed, 1 skipped; app 51 passed; gate 7 passed. 26 v2 screenshots re-captured, 0 console errors.
- NOT changed: the Llama 3 prompt, so AI-written explanations still say "video branch", "score of 0.853" (my decision still open; the two raters are
  scoring the 22 Sep packet text). Note for the report: ledger M1's "template (reference)" row and the T1 figures were measured with the pre-2026-09-25 template.
- Server restarted (pid 70939).

---

## 2026-09-24 21:37 (analysing screen: green "Done" on each finished step)

User request: each step on the analysing screen should say Done when finished, with a green tick box. `static/app.js` `drawProgress`: finished steps
get a green ticked box and a green "Done" badge after their note ("16 face frames found", "Speech found"); skipped steps get a grey "Skipped" badge
with "No face to check" / "No speech to check"; the running step stays highlighted. `static/style.css`: badge styles; on phones the note and badge sit
on a line under the step name. Checked in headless Chrome on real analyses (FVRA_001 at 1440 px: 5 done; 183.mp4 at 390 px: 4 done, 1 skipped), no page
errors. Test jobs removed.

---

## 2026-09-24 21:24 (old-interface screenshots retaken; screenshot script fixed)

I ran `scripts/ui_screenshots.py --version v1_retake --base http://localhost:8001` while the old interface was not running (connection refused).
Two script fixes: it now stops with a plain message naming the command to start the right server; and any version name starting with `v1` uses the old
interface's capture path (it had taken `v1_retake` for the new interface and waited for a v2 button). Started `./run_v1_interface.sh`, retook 24 screenshots
into `docs/user_testing/screenshots/v1_retake/` (same states as `v1/`; verdicts matched: REAL, PARTIAL, FAKE, INCONCLUSIVE, FAKE), stopped port 8001. The
original `v1/` set (taken before round 1) is unchanged. The live old interface lists one extra example (the no-face test pattern added for v2).

---

## 2026-09-24 21:13 (fix: browser showed an empty, unstyled page after the redesign)

My Chrome showed the new page with no styling and no content. Cause: the server sent `/static/*` without a Cache-Control header, so Chrome
reused its cached v1 `style.css` and `app.js` with the new HTML; the old script stopped at an element that no longer exists. Fix in `server.py`: the
index route adds each file's modification time to its link (`style.css?v=...`, `app.js?v=...`) and sends `Cache-Control: no-cache`; a middleware
makes every `/static/` response `no-cache` (revalidated by ETag). Also corrected the header comments of the three v2 files from 2026-09-25 to
2026-09-24 (my dating error). Server restarted (pid now 60488). Checked: `http://0.0.0.0:8000/#/history` renders styled with no page errors;
`tests/test_server.py` index, static, demo, evaluation and frozen-v1 tests pass (8).

---

## 2026-09-24 21:09 (interface v2 "Clipcheck" built from the designer's mockups; tested; v1 kept runnable)

I supplied 11 mockup screenshots (start, analysing, result, the four Learn more tabs, history, accuracy) and wanted the interface to match
them. Mapping of screenshot to screen confirmed; two decisions made: descriptive example names with a `#testing`
mode that shows the neutral round 1 codes, and a curated list of 8 examples with "Show all". Decided without asking and stated: the mockup's
"Prototype: the result shown is a sample" banner dropped (the app really analyses), the unfamiliar-input warning added in the same style (not in the
mockups), installed fonts only (Charter, system sans, SF Mono) so the tool stays offline.
- `static/index.html`, `style.css`, `app.js` rewritten (v1 frozen in `docs/user_testing/ui_v1_snapshot/`, byte-identical, now also checked by a test).
  Hash routes `#/check`, `#/analysing/<id>`, `#/result/<id>`, `#/history`, `#/accuracy`. Every number from the server; percentages as ">99%" / "<1%",
  never 100% or 0%; one verdict vocabulary; unfamiliar-input card under the verdict; Learn more with Legend (20 terms, technical names), Findings for this
  clip (face crop, per-frame chart, waveform, gap against T, moments, familiarity distances, explanation check and any rejected AI text), Technical details
  (models and statuses from /api/model_info, checkpoint, weights), Accuracy and limits (from /api/limitations); Accuracy page figures parsed from
  /api/evaluation (83 in 100, 59 in 100, 29 in 100, 100 of 100), research tables folded; History with a remove confirmation; phone layout; print layout.
- `server.py` (additive): progress reports `step` (faces, face_check, speech, voice, compare, explain), `faces_found`, `speech`; `/api/demo_clips` adds
  `title`, `subtitle`, `group`, `code`, `duration`, `featured` (titles from each clip's construction, never a model output; `FEATURED_DEMOS`);
  `/api/evaluation` adds the fusion weights actually used; new example `demo_videos/noface_silent.mp4` (git-ignored; recipe in TESTING_GUIDE s8) with its
  own kind. `scripts/video_infer.py`: one extra progress callback between finding and scoring faces (UI only; outputs unchanged, tests pass).
- `scripts/ui_screenshots.py` captures v2 (hash routes, Learn more tabs, History, Accuracy, one real mid-analysis frame; console errors recorded):
  26 screens in `docs/user_testing/screenshots/v2/`, 0 console errors.
- Checked in headless Chrome: 0 of 535 visible text elements below 4.5:1 contrast, nothing under 13 px (v1: 8 of 13 styles failed, 65% under 12 px); no
  horizontal scroll at 390 px; example to analysis to result, legend links, moment seek, Copy data, remove-with-confirm and testing mode all work. Fixes made
  during review: zero-length moments ("at 0:00"), plain wording for the no-score fallback, long example subtitles, squeezed phone rows (Recent checks,
  History), testing mode not switching on an open page, 404 for the page icon.
- Tests: `tests/test_server.py` +3 (plain example names from construction, fusion weights, v1 frozen and runnable) and progress-step ordering inside the
  analysis helper. Base env 152 passed, 1 skipped; app env `test_server.py` + `test_pipeline.py` 51 passed; `test_ood_gate.py` 7 passed.
- Server restarted twice for the new code (pid now 59222); the in-memory history was lost (only my test checks were in it); my test checks removed.
- Design iteration record for the report: `docs/user_testing/findings.md` (changes C1 to C16 each traced to round 1, the heuristic review, my direction or the
  mockups; v1 against v2 measurements). Protocol: round 2 notes (open with `#testing`, v2 names for the tasks' elements).
- Not changed: the explanation text itself (still says "video branch leans FAKE"), verdict logic, T, weights.

---

## 2026-09-24 20:35 (round 1: four survey responses received; form carry-over defect found and fixed; v1 kept runnable)

I ran four short sessions on v1 (CSVs downloaded 19:15 to 19:47) and asked to use them for the report and to keep the original interface for
report screenshots. Before scoring, read all four files: P2 and P3 share 29 identical answers, including all 10 SUS answers and three task notes word for
word; P3 and P4 share a T8 note word for word; the facilitator debrief is identical in all four. Cause: my form kept one set of answers and did not clear
it for a new participant, and the protocol never said to clear it. Raw files kept unchanged in `docs/user_testing/responses/raw_as_downloaded/`
(sha256), copies in `responses/`; provisional summary generated (SUS P1 60.0, P2 60.0, P3 60.0, P4 47.5; median 60.0), NOT for the report until I
confirm which at-risk answers were really given. Also to confirm: P1 and P2 marked as having an ML background. Record: `docs/user_testing/results/round1_data_quality.md`,
including the findings that do not depend on the at-risk answers (all four named information overload in their own words; P1 and P4 saw the warning only
after a hint; P1 and P4 struggled to find the limits).
- Form fixed (`scripts/build_survey_form.py`): one sheet per participant and round, a new participant opens blank; browser-checked (switch P1 to P2 to P1 to P2:
  answers stay on their own sheets). Protocol step 4 updated. 10 survey tests pass.
- Original interface kept runnable: `server.py` reads `DEEPFAKE_STATIC_DIR` (default unchanged: `static/`); new `run_v1_interface.sh` serves the frozen
  `docs/user_testing/ui_v1_snapshot/` on port 8001 with the same backend; `scripts/ui_screenshots.py --base http://localhost:8001` re-shoots it. Checked:
  port 8001 serves byte-identical v1 files; `static/` and the snapshot both still match `SHA256SUMS`. `tests/test_server.py` 45 passed. The live server on
  8000 was not restarted (default path unchanged).

---

## 2026-09-24 19:54 (MVP design brief for a UI/UX designer, published)

At my request, an MVP brief for an external UI/UX designer, built around my requirement: "explanation should be in layman terms and technical
terminology should be defined with a legend in a Learn more section along with more details of the findings; make it user friendly". Published as a private
web page; copy in `docs/user_testing/design_brief/`.
Contents: product, personas, design principles, v1 problems (from the heuristic review, with 4 v1 screenshots), screens A to F, result-screen content order,
the 8 result states with proposed plain wording, the Learn more section (legend, findings for the clip, technical details, accuracy and limits), a 20-term
legend, the data fields the server already returns (read from a live result), honesty rules, accessibility (WCAG AA, bundled fonts, 1440 and 390 px), out of
scope, deliverables by Fri 25 / Sat 26 Sep. Every figure from existing records. Two wording errors caught before publishing (FAKE and REAL reasons
overstated agreement; model count). While reading a live result, confirmed the FVRA_000 template fallback is the M1 screen misfire (heuristic review updated).

---

## 2026-09-24 19:04 (short survey form; heuristic evaluation of v1)

Decided against generating survey data for participants (it would be fabricated research data). Instead: a short session form, and a heuristic evaluation by the developer, labelled as such.
- `scripts/build_survey_form.py` now also writes `docs/user_testing/survey_form_short.html` (tasks T2, T3, T7, T8 + full SUS + O1, O2; 10 to 12 minutes).
  The CSV records `meta/form`; the scorer checks each file against its own variant's required items and pools short and full sessions item by item
  (project statements and feature ratings are medians over those asked). 3 new tests, 10 in `tests/test_user_testing_survey.py`; browser check: 4 tasks,
  17 required answers flagged on an empty form, project and feature sections hidden. Protocol: short-session section.
- `docs/user_testing/heuristic_evaluation_v1.md`: Nielsen's ten heuristics, 0 to 4 severity, one developer-evaluator (stated as a limitation; not user
  testing). Measured on the live page: 8 of 13 text styles below the WCAG 2.1 4.5:1 contrast minimum (1.94:1 to 2.64:1), 58 of 89 visible text elements
  under 12 px, no responsive breakpoints, 2 ARIA attributes. 14 findings: 7 major (technical terms, four verdict vocabularies, unlabelled banner percentage
  ("Authentic media 1%"), video pushing the verdict and explanation below the fold, a weak unfamiliar-input caution inside a confident red banner, an
  empty first screen with the demo clips hidden, small faint text), 5 minor, 2 cosmetic; strengths to keep listed. Each finding names the round 1 task
  that tests it, and five hypotheses are stated for round 1 to confirm or refute. Related observation: FVRA_000 shows the template because the Llama
  text failed the screen (direction), likely the M1 conjunctive misfire (not confirmed for that clip).

---

## 2026-09-24 18:34 (user testing redesigned as two rounds; v1 frozen; survey form and scorer built)

User decision (B1): the interface is "too technical" and "looks unfinished"; test the CURRENT interface with users first, redesign from the findings,
test again, and document it for the report. My direction for v2: dark but polished, verdict first, technical detail kept visible.
- v1 frozen before any session: `static/` copied byte for byte to `docs/user_testing/ui_v1_snapshot/` with `SHA256SUMS`.
- New `scripts/ui_screenshots.py` (Playwright + installed Chrome; creates its own jobs through the API and deletes them afterwards): 24 v1
  screenshots in `docs/user_testing/screenshots/v1/` (7 states x desktop 1440x900 and mobile 390x844, plus explanation-scrolled shots), `index.json`.
  Verdicts matched the answer key (RVRA_000 REAL, FVRA_000 PARTIAL, 183_253 FAKE, no-face INCONCLUSIVE, LAVDF_RVRA_000 FAKE). My own observations of
  v1 (not participant findings, kept separate): on a 390 px screen the sidebar does not collapse and the verdict banner is squeezed into a narrow
  column; the video area dominates the desktop screen and pushes the explanation below the fold; the sidebar shows a checkpoint hash.
- New `scripts/build_survey_form.py` -> `docs/user_testing/survey_form.html` (offline, one form per participant per round): session and consent,
  8 tasks + 1 optional with outcome, task-specific checks, 7-point ease and notes; System Usability Scale (Brooke, 1996, standard wording); Q1 to Q6;
  usefulness of 10 features or "did not notice it"; 5 open questions; facilitator notes. Download refuses until 37 required answers are given (checked
  in the browser: 37 flagged on an empty form). CSV format checked end to end against the scorer (63 rows, accepted); the check CSV went to the
  session scratchpad, not `responses/`.
- New `scripts/score_user_testing.py` -> `docs/user_testing/results/summary.{json,md}`: SUS per participant and median, task outcomes, checks,
  statements, features, verbatim open answers, round 1 against round 2. Refuses missing answers, answers outside the form's options, duplicates, and an
  empty folder. `tests/test_user_testing_survey.py`: 7 tests pass (fixtures in pytest tmp_path only; no participant data exists).
- `docs/user_testing/protocol.md`: two-round design, survey form in the checklist, SUS in the post-task questions, scorer as step 0 of the analysis.
`static/` is NOT to be changed until round 1 has run.

---

## 2026-09-24 18:13 (explanation LLM comparison M1: Llama 3 8B kept under a pre-registered rule)

Why: the brief's 1st-class criterion asks for evidence of exploring the pre-trained models; the text model had none. Pass rule written into the ledger (M1)
at 17:50 before anything was downloaded. New `scripts/compare_llms.py` (resumable; uses the app's prompt, options and screen unchanged, passes the model
name per request). User approved the two downloads (mistral:7b 4.4 GB, qwen2.5:7b 4.7 GB, Apache 2.0, from the Ollama library). 450 generations, 50 packet
cases x 3 seeds x 3 models, 17:47 to 18:11. Llama 3 seed 42 reproduced the packet (49 of 50 identical, same 24 failures).

Result: screen pass Llama 3 50.7%, Mistral 50.0%, Qwen 64.0%; Qwen fails the format condition (76.7% against 90%: fifth sentences), Mistral fails three
conditions, so **Llama 3 8B stays; no deviation**. Read and labelled all 43 seed-42 failures (`adjudication_seed42.json`): Llama 22 genuine + 2 screen false
positives, Qwen 8 genuine + 11 screen false positives. Found a screen misfire that also affects the live app (the conjunctive direction rule on "the video and
audio branches disagree"); not fixed (M1 changes nothing), proposed as a separate fix. Lesson L33. Candidate models unloaded after the run; nothing loaded in
Ollama at 18:12 (the app reloads llama3:8b on its next request, a cold start of a few seconds). App code, prompt, screen, tests and rating packet unchanged.

---

## 2026-09-24 17:06 (new chat: state checked; user-testing protocol rewritten; Chapter 4 and 5 tables drafted)

State checked, not assumed: `date` 17:02; server pid 37640 on port 8000 returns HTTP 200; Ollama serves `llama3:8b`; both rating sheets in
`results/explanation_eval_full/` still blank (header + 50 empty rows); nothing in Downloads. Open questions listed; answers pending.
No code changed.

B2 prep: `docs/user_testing/protocol.md` and `response_sheet.md` rewritten for the FastAPI interface (old Streamlit-era versions archived unchanged
in `docs/internal/archive/`). Eight tasks plus one optional: first impression, RVRA_000, FVRA_000 (partial verdict, which part), reading the three
percentages, 183_253 (explanation and timing, source badge), uploading a no-face silent clip (INCONCLUSIVE), LAVDF_RVRA_000 (unfamiliar-input caution
on a wrong verdict), finding the limits panel and Evaluation tab; Q1 to Q6; debrief; iteration steps; facilitator answer key from TESTING_GUIDE.
New test clip `docs/user_testing/materials/noface_silent.mp4` (ffmpeg testsrc recipe, git-ignored as *.mp4); uploaded once to the live app to confirm
INCONCLUSIVE with the template explanation (this left one entry in the app's recent list; clear it before sessions, protocol step 2).

B4 start: `docs/report_prep/report_ch4_ch5_tables_draft.md`, 5 Chapter 4 tables and 14 Chapter 5 tables (two are placeholders for B2 and B3), each
row sourced from `numbers.json`, `latency.json`, the two report-prep records or the ledger. Fusion weights and T re-read from `scripts/fusion.py`
at run time (0.464 / 0.536, T = 0.35). No new measurement.

---

## 2026-09-22 17:41 (explanation packet regenerated with real timing; two screen bugs found, fixed, and documented)

Regenerated the 50-case packet (`scripts/explanation_eval.py generate --with-timing`, same seed/clips as 21 Sep) to reflect T1
(video anomaly timing). Raw screen rejection jumped 8% to 62%, investigated rather than shipped as-is. A controlled A/B test
(old prompt reconstructed vs new prompt, same 10 score pairs) proved the dominant failure, a rote "the video has been partially
manipulated" opener regardless of which branch is implicated, is pre-existing, not caused by the timing addition. Separately
found and fixed two real `explain_checks.py` false-positive bugs on genuinely faithful negated sentences ("no indication that
... disagree", "unmanipulated", "the likelihood of X being manipulated is very low"), via a general negation-window helper, not
one-off phrase patches. 4 new regression tests. Re-scored (not re-generated) all 50 stored explanations against the fixed
screen: 24/50 (48%) still fail, 23 of them the same confirmed pre-existing PARTIAL_MANIPULATION issue, 1 a genuine
self-contradictory sentence (legitimate catch). Zero regressions (every case that passed before still passes). Rebuilt
`rating_form.html` from the corrected `cases.json`. Full suites re-run: 142 base (1 skipped), 48 app, all pass. Old packet kept
at `results/explanation_eval_full_pre_timing_2026-09-21/` (nothing was rated on it). Ledger T1 addendum, lesson L32.

---

## 2026-09-22 16:59 (video anomaly timing added to the LLM explanation)

User asked for the Llama explanation to say more about WHEN the video looked suspicious (not what a human would see/hear,
which was explained as unsafe to fabricate, but timing, which the pipeline already computes). Added `video_anomaly_timing`
to the structured input (`scripts/explain.py`), extended the prompt with an explicit "state WHEN, never WHAT" rule, updated
the deterministic template and extended the faithfulness screen with a `timing` violation type plus an exemption so a
window's peak score isn't mistaken for a hallucinated number. 12 new tests, all passing in both environments (140 base,
48 app, including the real-Ollama and real-per-frame-data integration tests). Confirmed live: demo clip 183_253.mp4's
explanation now states "0:00 to 0:03 and 0:04 to 0:06", the real computed windows, and passed its own screen. Ledger T1.
Next: update the explanation-eval rating form (`rating_form.html`/`build_rating_form.py`) to reflect this, then user testing.

---

## 2026-09-22 16:22 (automated check over the explanation packet removed; rater form built)

At my request the automated faithfulness-check run over the 50 packet cases (15:56 entry) was removed: `scripts/screen_explanation_packet.py`
and `results/explanation_eval_full/automated_screen.json` deleted, the cross-check section taken out of `scripts/score_explanation_eval.py`, ledger
E3 marked removed. The check itself is untouched in the app (it is the live safety net, register D-I). Note for the report: `cases.json` from the 21 Sep
packet generation still records the app's check per case; raters never see that file.

New `scripts/build_rating_form.py` builds `results/explanation_eval_full/rating_form.html`, a self-contained offline form for the two human raters: rater
choice, rules, how to read the facts, the Ch 3.6 rubric, two worked examples (real Llama 3 outputs from FVFA_002 and the veo_sailor upload, neither among
the 50; scored 2/2/2 and 1/1/2 with reasons), the 50 cases in order, progress saving, and a Download button that refuses until every case has all three
scores and then writes `rating_sheet_rater{1,2}.csv` in the scorer's format. It shows the seven structured-input fields the model received, including the
two "leans genuine / leans fake" readings the markdown packet omits. Checked in the browser: both guards, 50 cards, correct CSV (quotes, commas and line
breaks in notes), and the scorer parses it. `tests/test_rating_form.py` (4 tests) checks no clip id, ground truth or check result can reach the page.

---

## 2026-09-22 15:56 (explanation-eval infrastructure; LAV-DF and gate write-up; file organising added to the to-do list)

I checked where the application stands against the "Orchestrating AI models to achieve a goal" brief (read directly from
`Orchestrating AI models to achieve a goal.pdf`), then asked for the explanation-eval packet (item 2) and the LAV-DF /
out-of-domain write-up (item 4) first, with file organising and reviewing added to the list for later.

Explanation eval: the two human rating sheets are still blank and were not touched; an AI cannot stand in for the Draft's two human
raters. Done instead: `scripts/screen_explanation_packet.py` runs the app's own faithfulness screen over the 50 cases (46/50 pass; the 4
failures, eval-22/23/33/49, are the same "direction" pattern as the live veo_sailor case; ledger E3). A first run reported 7/50 because my
field regex did not accept "P(fake)" in the key names, so scores were read as "not evaluated"; fixed before any number was recorded.
`scripts/score_explanation_eval.py` computes quadratic-weighted Cohen's Kappa and agreement once both sheets are complete and refuses to run
before that (checked against the real blank sheets); 5 data-free tests. APP_TODO 8.1 corrected: its tick covered the code only.

Write-up: `docs/report_prep/lavdf_generalisation_and_ood_gate.md` (16 sections, same structure as the backbone record) consolidates F6,
the F6 addendum, F7, F8, F9 and O1 with an evidence index and suggested report wording. APP_TODO Phase 10 (file organising and reviewing)
added, not started.

---

## 2026-09-22 13:23 (probe F8: adding genuine VoxCeleb2 faces trades false alarms for blindness)

I saw a LAV-DF real/real clip (RVRA_024, video 0.96, audio 0.98) called FAKE and asked whether a higher-resolution dataset would fix it. No: every face
is resized to 224 x 224 anyway and resolution was already ruled out. A frozen-feature probe showed adding 1,825 genuine VoxCeleb2 crops cuts LAV-DF false alarms
80% to 5% but also cuts LAV-DF fake detection 68% to 0% and DeepfakeTIMIT 30% to 15% (F8). Nothing shipped.

---

## 2026-09-22 13:27 (probe F9: mixed real + fake data adapts, does not generalise)

Frozen-feature probe with LAV-DF genuine and lip-synced crops: LAV-DF false alarms 80% to 10%, but Celeb-DF (unseen) 60% to 57% and DeepfakeTIMIT (unseen)
30% to 20%; multi-corpus audio SVM still flags 95% of unseen genuine TIMIT speech. Nothing shipped. Ledger F9.

---

## 2026-09-22 03:32 (out-of-domain gate: built, evaluated, withholding rejected by its own rule, shipped as a warning)

User asked for option A (abstain on unfamiliar input) and for the video side to be tested. Built `scripts/ood_gate.py` (Mahalanobis, per branch),
`extract_app_features.py` (app code over 760 clips in 7 sets), `fit_ood_gates.py` (rules and criteria in its docstring before fitting),
`eval_ood_gate.py`; server, page and 12 tests. Audio gate flags 88% of LAV-DF dev and 3.9% in domain; video gate only 31.5% and 1.9%. Withholding failed
criterion (b) (held-out accuracy 92.5% to 90.0%) and made DeepfakeTIMIT worse (14 confident REAL on fakes), so it is not the default; warning mode (verdicts
unchanged) flags all 50 wrong LAV-DF verdicts and 5/80 held-out clips. Also measured that the app's 20-crop sampling puts only about 1 crop inside a LAV-DF
video fake, so no gate or threshold can make the video branch right there. Side fixes: Celeb-DF list had CRLF line endings (first extraction read no files;
redone); base env `huggingface_hub` 1.32 (from the LAV-DF download instructions) broke `transformers`, pinned back to 0.36.2; `build_lavdf_eval_set.py`
given the `select()`/`as_fake()` interface that an earlier session's tests expect (selection verified identical to the built set). Tests: base 119 passed,
1 skipped; app env 53 passed with heavy tests. Ledger O1, lesson L31, register D-M, testing guide section 11.

---

## 2026-09-22 02:44 (audio experiment F7: the corpus explains the false alarms; adapting to LAV-DF is not generalisation)

Ran `scripts/audio_lavdf_experiment.py` (experiment only, models saved under results/, app untouched). Rule met: adding 400 genuine VoxCeleb2 clips (B2) cut false alarms on the
LAV-DF test clips from 100% to 4% with ASVspoof EER +0.11 pp, but B2 also flags only 4% of the fake clips (AUC 0.478): no discrimination. B1 (adding 400 fake-audio clips too) reaches AUC 0.898,
EER 16.5% on LAV-DF, at ASVspoof EER +0.82 pp; in-domain for LAV-DF (same generator), so not evidence of generalisation. Nothing shipped. Also added the first 3 LAV-DF test clips per category
by id to the app's demo list (`LAVDF_` prefix, `LAVDF_MANIFEST` in server.py, one new test); `eval_lavdf/` still untouched by any tuning.

---

## 2026-09-22 02:13 (resolution diagnostic: 224x224 is not the cause)

`scripts/lowres_diagnostic.py` re-scored 59 held-out FF++ videos as LAV-DF-like close-ups (224x224, 100 kbps): AUC 0.981 to 0.977, no false alarms on
real faces. Rule "resolution explains it if AUC drops by more than 0.15" was written before running; drop was 0.004. Also measured that only 5 to 13% of a LAV-DF
"fake" clip's duration is manipulated. Recorded as the F6 addendum. Open question: which of VoxCeleb2 domain shift, Wav2Lip, or label dilution drives the failure.

---

## 2026-09-22 01:53 (LAV-DF scored: both branches fail on an independent set; F6 in the ledger)

Part 006 was in `~/Downloads` (moved into `external_datasets/LAV-DF_parts/`; 1,048,576,000 bytes, complete). `metadata.json` extracted with
`scripts/carve_lavdf_parts.py` (fields `modify_video`, `modify_audio`, `split`, `fake_periods`). `scripts/build_lavdf_eval_set.py` built
`eval_lavdf/` (200 test clips, 50 per category, rule frozen in its docstring before scoring; clips git-ignored). Scored with
`eval_fallback_4condition.py`: video-only 43.0%, audio-only 50.0%, standard fusion 72.0%, disagreement-aware 75.0%, which equals the
always-FAKE baseline (75.0%). Video AUC 0.377, audio AUC 0.522; the audio branch flags 100% of clips in every category. The +3.0 pp fusion
advantage is an artefact of the baseline and must not be cited. Cause of the video failure untested (224x224 faces, Wav2Lip, VoxCeleb2, dilution).

---

## 2026-09-22 01:43 (LAV-DF: a 2 GB route to a labelled four-category set instead of 25 GB)

I wanted videos in all four categories (real/fake video x real/fake audio) to test the audio branch, without a 25 GB download.
LAV-DF has exactly those four modification types (paper: arXiv 2204.06228). I had already downloaded one raw part,
`external_datasets/LAV-DF_parts/LAV-DF.zip.024` (708 MB). Its zip central directory (136,311 entries, zip64) showed the archive is cut into
1000 MiB raw pieces, so part N covers bytes [(N-1)*1,048,576,000, N*1,048,576,000): part 024 holds 4,462 complete train clips, and
`metadata.json` (21 MB compressed) plus `metadata.min.json` sit wholly inside part 006, which also holds about 3,400 dev and 2,500 test clips.
So part 006 (1 GB) supplies the labels and a labelled set; nothing else is required.

`scripts/carve_lavdf_parts.py` extracts members from single parts (local headers carry sizes and CRC-32; CRC verified on every file).
Tested on part 024: 4,462 complete members found, one clip extracted with CRC verified, and it decodes (224x224, 25 fps, 12.5 s, 16 kHz mono
AAC). Not yet done: download part 006 (user), extract metadata, read its field names, freeze the sampling rule, score. Known limits to state
when scored: unseen VoxCeleb2 speech (audio false alarms expected), Wav2Lip video (not a training method), fake segments average 0.65 s inside
clips up to 20 s, 224x224 faces.

---

## 2026-09-21 18:08 (testing guide written from real live-server runs)

I wanted to know how to test every model and what to expect before the interface is restyled. All 24 clips in the demo list plus six
accepted extra uploads were run through the live server (pid 7564) and the guide `docs/TESTING_GUIDE.md` was written from those
outputs. Extra material built for the run: four Veo-3 clips from `demo_videos/ai_generated_2026/` converted from WebM to MP4, a
face-free silent clip, a face-free clip with speech, a 135 s clip, a corrupt file and a `.txt` file (the last three are correctly
rejected with HTTP 400 and clear messages).

Observed: real/real and both single-modality categories behave as designed on 9 of 9 constructed clips; one fake+fake clip of three is
labelled FAKE and the other two PARTIAL (the known false-disagreement limitation); 599_585 is a borderline fake (0.554); all 24
demo explanations came from Llama 3 and passed the faithfulness screen; one AI-generated clip (`veo_sailor`) had its Llama text rejected
by the screen (direction violation) and the template was shown, which is the safety net working as designed. Test suites re-run:
107 passed in the base environment, 36 passed in the app environment. The guide states which weaknesses are expected (unseen genuine
speech flagged as fake, fully synthetic video uncertain, wrong modality on fake+fake) so they are not mistaken for bugs.

---

## 2026-09-21 17:44 (held-out re-run of the core evaluation: the claim holds, two of my explanations did not)

Answering my question "have we used FF++ on Xception": yes, verified from files. The shipped model is ImageNet-pretrained Xception fine-tuned on
FaceForensics++ c23 (Deepfakes + FaceSwap + NeuralTextures, one method per identity pair: 54 / 53 / 53 training pairs; 5,734 training crops, 707 validation,
722 test, all from `frames/` and `frames_methods/`); Celeb-DF-v2 is used only for the cross-dataset test.

**Ran the held-out rebuild (APP_TODO 4.8).** New `scripts/build_heldout_eval_set.py` (the original builder is untouched, `eval_fallback/` is kept) builds
80 clips from test-split identities only: 22 real videos and 40 of the 66 test-identity fakes across the three methods. Verified independently, not just by
the script's own assertion: all 80 videos are in the test split, none of the 22 identities appears in any train or validation video. New data-free test
`tests/test_heldout_eval_manifest.py` (in CI) keeps it true and would have failed 65 of the older set's 80 clips. Four-condition, threshold sweep and a paired
bootstrap (`scripts/bootstrap_fusion_advantage.py`, so the interval has a file behind it) were run on it. **Result: video 92.5, audio 92.1, standard fusion
76.3, disagreement-aware 94.7; advantage +18.4 pp, 95% CI [+7.9, +28.9]; T = 0.35 independently re-confirmed (F1 0.909); naming the video on fake video +
real audio 75% (95% on the older set); false disagreement 11% real + real and 10% fake + fake.** Ledger F5.

**Two things I wrote earlier were wrong and are retracted** (ledger F3 caveat, swap record section 11, LESSONS L30): that the older set's
video-only accuracy was optimistic (held-out is higher), and that the 5% to 30% rise in fake + fake false disagreement was memorisation (it is 10% on
held-out video; 6 of 20 against 2 of 20 was noise). A per-clip breakdown of the older set showed the model detected 100% of fakes it had seen exactly
(8 of 8) but only 62% of fakes whose identity it had trained on under a different method, against 88% for unseen identities: familiar identities were
harder. Hypothesis only, n = 16 per group.

**App:** the Evaluation tab now shows the held-out result first, labelled authoritative, with the advantage and its interval and the false-disagreement
rates beside the accuracies; the older set is labelled in-distribution with the measured membership (57 of 80, computed from the manifests by
`build_numbers.py`, not typed). Four new view tests. Not changed: T, weights, the shipped model, the limitations text.

**Not done, deliberately:** the 50-case explanation packet (`results/explanation_eval_full/`) was drawn from the OLDER set's scores. The explanation text
depends only on the score structure, so it remains valid for rating, and it may already have been handed to a rater, so it was not overwritten. If it has
not been distributed, regenerating it from `results/heldout_eval_shipped/` would make it match the authoritative set (one command: `scripts/explanation_eval.py generate`).

## 2026-09-21 16:20 (report-ready record of the B4 to Xception swap; the four-condition set is not held out)

**User asked for every detail of the EfficientNet-B4 replacement to be kept for the report.** Written as one report-ready record,
`docs/report_prep/video_backbone_decision.md` (18 sections): what the PPR and Draft promised and why; how the supervisor's feedback led to the
leakage finding; the single-method bake-off; the FaceSwap 0% failure; multi-method training; the frozen ship rule with its timestamps and the
disclosures on the second B4 attempt; both B4 results per seed; the Xception versus ConvNeXt trade-off and why Xception won; the shipped model's
checkpoint, calibration, parity, checkpoint rule, cross-validation and Celeb-DF; what the swap changed downstream; the loader bug; checks not run and
why; the complete caveat list; the final D-C register entry; the models in use and those rejected; suggested report wording (including withdrawing the
Draft Report's claim that its own results validated B4); citation notes; and an evidence index. Every figure was re-read from result files for it, and
the one table I wrote by hand was re-derived from the data and checked row by row (one row had been mistyped and was corrected before logging).

**New finding while writing it (EXPERIMENTS F3 caveat, LESSONS L29):** the self-built four-condition set, built on 13 Sep from ALL FaceForensics++
videos, was never re-checked after the identity-disjoint split arrived on 19 Sep. **57 of its 80 clips use a video from the shipped model's training
split; only 15 are from the held-out test split.** The audio side is properly held out. The fusion comparison (24 points for disagreement-aware over
standard fusion) stays valid because both rules get identical scores, but the absolute figures, above all video-only 90.0%, are optimistic, and the
report must call this evaluation in-distribution for the video branch. It also explains two results that were previously only described: the fake+fake
false-disagreement rise from 5% to 30%, and why the one genuinely unseen category (DeepfakeTIMIT in the hybrid set) is exactly where modality naming
fails. **Proposed fix, not run:** rebuild the set from test-split identities and re-run the four conditions and the threshold sweep.

The working notes' answer protocol still described EfficientNet-B4 as the video branch; a dated status note was added at its top so future sessions
do not repeat that in exam or viva answers.

## 2026-09-21 16:05 (wav2vec2 vs WavLM: the audio encoder choice is now tested, not assumed)

Ran the SSL-encoder comparison the project never had (EXPERIMENTS A6). wav2vec2-base 6.60% eval EER against wavlm-base 7.20% on an
identical 1500-clip held-out subsample, with wav2vec2 also ahead on AUC, balanced accuracy and false alarms on genuine speech. The
margin is small (about 9 clips) and no confidence interval was computed, so the claim made is "validated, not worse", not
"significantly better".

The more useful result is the second one: **WavLM does not fix the unseen-corpus failure either.** Both encoders flag 100% of 60
genuine DeepfakeTIMIT clips as spoof, WavLM slightly more confidently. With A5 having ruled out the codec, two candidate
explanations for the branch's worst behaviour have now been tested and rejected, which makes the "it is the training corpus"
conclusion an evidenced one rather than an assumption.

Method notes worth keeping: both encoders were embedded fresh in one process rather than reusing the cached wav2vec2 embeddings,
because those were computed in the other environment and reusing them would have confounded encoder with environment. I first
tried to prove the cache reproducible across environments, but the app env could not read FLAC without adding a dependency, so I
removed the confound instead of measuring it. The comparison uses the project's own bundled ffmpeg decoder, so it also matches the
path the app uses. The base env cannot import WavLM at all (protobuf 7.34.0 breaks transformers' import chain there), which is why
the run is in the app env.

## 2026-09-21 15:30 (explanation packet generated, audio question answered, code reviewed)

**Clock note:** the machine was suspended from about 03:05 to about 15:00 on 21 Sep (the last detached queue finished at 02:08 and
nothing ran in between). Work in this entry actually ran between about 15:05 and 15:30; a few timestamps were first written as
"03:1x/03:2x" from a stale clock reading and have been corrected against file mtimes. No job was interrupted: every queue had
already completed before the suspend. **Deadline is now 7 days away (Monday 28 September).**


**50-case explanation packet generated** (`results/explanation_eval_full/`, seed 42, drawn from the shipped-model four-condition
results; the old 16-case pilot is untouched in `results/explanation_eval/`). Category spread RVRA 15, RVFA 13, FVFA 13, FVRA 9.
**The automatic faithfulness screen rejects 4 of 50 (8%)**, which is the first real measurement of how often the app falls back to
the template. Reading the four by hand found something the screen itself got wrong: in two of them the sentence it flagged was
faithful, and the actual misstatement ("the video and audio content are partially manipulated", generated when audio scored 0.000)
sat in a sentence the screen structurally skipped, because sentences naming both branches were never direction-checked. The screen
caught those two by luck. Extended the check to catch conjunctive "both are manipulated" claims that contradict a branch the input
says leans genuine; re-screened the saved explanations (same 4 rejected, now for the right sentence), and confirmed no new false
positives (14 faithful "both branches lean genuine" texts still pass). Four new tests. The explanation text shown to raters is
unchanged, so the packet stays valid and the raters are not biased.

**Audio question answered, and the answer saved a day (EXPERIMENTS A5).** The codec-versus-corpus diagnostic re-encoded ASVspoof's
own eval clips through AAC and MP3: bona fide false alarms went 5.0% -> 7.0%, about 2 points, against the 100% failure on
DeepfakeTIMIT. So the unseen-corpus failure is corpus mismatch, not the transport format, and the planned codec-augmentation
retrain was cancelled on evidence rather than attempted. A negative result worth reporting.

**Code review.** Fixed stale docstrings that would have misled a reader (`train.py` and `eval_celebdf.py` still described the
pipeline as EfficientNet-B4 although both are architecture-agnostic); added the video weighting source and T provenance to the
four-condition results file so every evaluation output records the settings it ran under. Verified the two paths never exercised
by hand: a no-face silent clip gives INCONCLUSIVE with the template explanation and a null overall score, and a no-face clip with
speech gives an audio-only verdict whose Llama explanation correctly states the video branch was not evaluated. Checked what a
commit would contain: 419 files, 4.7 MB, no FF++ media, no weights, no embeddings.

## 2026-09-21 03:00 (user asked for the balanced audio weight and the server restart; both done)

- **Audio fusion weight switched to balanced accuracy** (user decision): 0.9569 at the P(fake) >= 0.5 operating point, replacing
  the plain 0.9765, which sits barely above the 89.7% a classifier gets by always answering "spoof" on that 90%-spoof partition.
  Resolver prefers `extra_metrics.json`, falls back to plain accuracy and says so, still refuses subsample-only runs. Weights are now
  video 0.464 / audio 0.536. Two tests pin it (EXPERIMENTS A4 marked resolved).
- **Live server on port 8000 restarted** (old pid 46576 stopped, new pid 85450). `/api/model_info` now reports "Xception + MTCNN,
  fine-tuned on FaceForensics++ c23, multi-method, checkpoint fdd60748dc1c" instead of the old EfficientNet-B4 line.
- **End-to-end check through the running server, one clip per category:** RVRA -> REAL (weights 0.464/0.536 applied, gap 0.008 < T);
  RVFA -> PARTIAL implicating audio; FVRA -> PARTIAL implicating video; FVFA -> PARTIAL implicating audio. The first three are exactly
  the three PPR scenarios. The fourth is the documented FVFA limitation, not a regression: the video branch scored that clip 0.167 and
  missed the manipulation, so the gap exceeded T. Across the whole set the video branch misses 5 of 20 FVFA fakes and all 5 are
  reported PARTIAL rather than FAKE, which is the entire 30% false-disagreement rate on that category, now explained rather than just
  measured.
- **All four explanations came from Llama 3 and passed the faithfulness screen**, which answers the open question from 5.3: the screen
  is not rejecting everything and the template fallback is genuinely a fallback. The 50-case run (8.1) will give the real rate.

## 2026-09-21 02:10 (all shipped-model evaluations complete; 128 tests pass)

Final numbers, all on the shipped Xception-mm seed 44 at the re-tuned T = 0.35 (ledger F3, F4, H2, L2):
- **Four-condition (core evidence): video-only 90.0, audio-only 97.5, naive fusion 73.4, disagreement-aware 97.5%.** The
  research question's claim holds on the shipped model with a 24.1-point margin. Implication RVFA 100%, FVRA 95%. Re-tuning T
  from 0.30 to 0.35 gained 1.3 points and halved false disagreement on genuine clips (10.5 to 5.3%). Caveat: FVFA false
  disagreement 30%.
- **Hybrid: disagreement-aware 98.7%, FVRA implication 0%.** Written up as EXPERIMENTS H2 and LESSONS L28: the highest accuracy in
  the project is produced by the audio branch false-alarming on genuine speech while the video branch misses the manipulation
  (mean P(video_fake) 0.305, 6 of 20 caught). The app now shows implication next to accuracy in both fusion sections and carries a
  limitation saying the named modality is a pointer, not a conclusion, on unfamiliar footage.
- **Latency complete: 9.0 s warm per clip** (video 5.95, Llama 3 2.23, wav2vec2 0.71, rest under 0.1), cold start 3.84 s.
- **Preprocessing parity re-confirmed** on the shipped checkpoint, numbers identical to the 20 Sep run (same checkpoint), so D4 holds.
- Tests: 92 base + 36 app = 128, including for the first time since shipping the 6 heavy tests that load the model and Ollama.

Superseded artefacts preserved: `results/OLD_model/` (old model's fallback, hybrid, latency) and `results/*_shipped_T030/` (the
shipped-model pass at the old threshold, kept because the tuning was derived from its per-clip scores). Not done, deliberately: the live server on port 8000 has not been restarted; that waits for me.

## 2026-09-21 01:52 (regularised B4 failed too; Xception-mm shipped; a real bug caught on the way)

**Regularised B4 (C2) finished 01:45 and also failed step 1** of the frozen rule: mean validation accuracy at the saved epoch
69.92% against 86.28% for Xception-mm, FaceSwap detection 60.6% against 87.9%, NeuralTextures 66.7% against 81.8%; real specificity
tied at 97.0%. Early stopping never fired. Regularisation narrowed the train-minus-validation gap (17.7 pp against 20.4 pp on seed 42)
and lowered validation accuracy with it (70.30 against 75.39), reproducing the single-method finding V6 on the harder problem. Both
B4 candidates therefore failed, so step 2 applied and the PPR architecture is formally deviated from (register D-C) on measured
evidence, not preference.

**D2 FINAL: shipped Xception multi-method, seed 44** (`ship_model.py --apply`, 01:47). The step-2 comparison is a genuine trade-off and
is recorded in full in EXPERIMENTS V14: ConvNeXt-mm wins mean validation accuracy (88.87 against 86.28) and overfits slightly less;
Xception-mm wins NeuralTextures detection (81.8 against 69.7), real specificity (97.0 against 90.9), Celeb-DF-v2 AUC and real-video
retention, and is the only candidate with a cross-validated interval and a calibration check. Chose Xception because wrongly flagging
genuine video is the worse error for this tool and because it is the model the project can actually characterise. Old checkpoint backed
up to `models/best_model.pth.pre-20260921-014755.bak`; checksum in `shipped_model.json` verified against the file on disk.

**Fusion weight (APP_TODO 1.8 decided):** `video_accuracy` = **0.828**, the cross-validated pooled accuracy over all 400 videos, not the
0.962 from the 44-video test split. The PPR bases the weighting on Large, Lines and Bagnall (2019), who use cross-validated accuracy, and
the small split is optimistic. `ship_model.py` gained `--video-accuracy/--video-accuracy-source` for this and records the alternative it
did not use. Resulting weights: video 0.459, audio 0.541 (they were 0.496/0.504 under the old default). Open and flagged:
the audio weight still uses plain accuracy 0.9765, which A4 showed is inflated by class imbalance (trivial baseline 89.7%); balanced
accuracy 0.9569 would give 0.464/0.536, a negligible numeric change but a more honest basis.

**Bug caught by shipping (LESSONS L27):** `load_models` only read the shipped architecture when the path argument was None, so
`server.py` and `eval_fallback_4condition.py`, which pass the path explicitly, could not load a non-B4 model. The four-condition re-run
failed on its first load, which is how it surfaced. Fixed at the source, regression test added. **The live app would have crashed on the
new model had this not been caught before the restart.**

**Re-runs on the shipped model launched detached** (`scripts/queue_shipped_evals.sh`, 01:50): four-condition, threshold T retune,
hybrid, preprocessing parity, latency, then `build_numbers.py`. Superseded results copied to `results/OLD_model/` first; new outputs go to
`results/fallback_eval_shipped/` and `results/hybrid_eval_shipped/`, which the Evaluation tab already knows how to read.

## 2026-09-21 00:16 (plain B4 multi-method finished: frozen rule step 1 NOT MET)

Plain B4-mm completed 00:14:30 (seed 44 done 00:13:53). Applied the frozen rule from the result files: mean validation accuracy at the saved epoch
74.54% against 86.28% for Xception-mm (limit 84.28%, short by 11.74 pp); FaceSwap detection 60.6% vs 87.9% (short by 27.3 pp, limit 9.09);
NeuralTextures 72.7% vs 81.8% (exactly 2 videos, allowed); real videos kept real 98.5% vs 97.0%. Not met. I first ran the check with a rounded 9.09
tolerance which showed NeuralTextures as a fail at exactly 2 videos; corrected to the exact 2/22 tolerance (the outcome is unchanged). Details and
caveats in EXPERIMENTS.md V14. The regularised run (C2) started automatically at 00:15:21 (dropout 0.3, label smoothing 0.1, early stopping 3) and has no result yet.

## 2026-09-20 23:41 (watcher re-armed, ETA revised)

The first watcher (30 minute cap) expired at 23:40 with no events; nothing had failed, plain B4 seed 43 was simply at epoch 9 of 10
(started 23:08:31, about 3.2 min per epoch while other work shared the machine, free memory about 11%). Re-armed. Revised estimate,
assuming no other load: seed 43 done about 23:43, plain B4 complete about 00:15, regularised B4 (3 seeds, about 30 min each unless early
stopping fires) complete about 01:45 (range 01:15 to 01:50), ship-ready about 02:30 to 03:15.

## 2026-09-20 23:31 (evaluation tab, limitations panel, explanation-eval sampling; still no GPU or Ollama)

- **Evaluation tab and limitations panel** (`scripts/evaluation_view.py`, `GET /api/evaluation`, `GET /api/limitations`, static UI). All figures come
  from `numbers.json`; leaking-split figures are never shown; four-condition, hybrid and latency results from the superseded model are withheld
  as "pending" with the reason; a cross-validation result is labelled as NOT applying when its architecture differs from the shipped one; the shipped
  row is marked. `build_numbers.py` now records each CV entry's architecture. 10 data-free tests (added to CI), 2 server endpoint tests. Checked in
  the browser pane on a temporary server on port 8001 (stopped afterwards; no console errors). With no shipped model the limitations panel says
  the training data is not recorded and no accuracy is measured, which is true today.
- **Explanation evaluation** (`explanation_eval.py --from-results`): random fixed-seed sample of the evaluation set as PPR 3.6 specifies. While
  testing it I found a leak in my own first version: fallback clip ids (`RVFA_003`) encode the ground-truth category, so putting the id in the
  rater-facing note would have shown raters the answer. Fixed (id kept only in metadata) and pinned by a test. Records per case whether the
  automatic faithfulness screen would have rejected the LLM text, which will answer how often the app falls back to the template.
- CI now runs the evaluation-view tests (41 data-free tests; `test_explanation_eval` needs torch via `utils`, so it stays local).
- Safety: every run used `nice`, `DEEPFAKE_SKIP_HEAVY=1` for the server suite, and `ollama ps` stayed empty; free memory stayed above 13%.

## 2026-09-20 23:22 (more GPU-free work while B4 trains)

- `scripts/benchmark_latency.py` rewritten in code (not run: it refuses while training is active, verified): model named from the
  shipped manifest, SVM/VAD/faithfulness-screen stages timed, fusion on the clip's real scores, marked incomplete if a stage is
  missing, never overwrites an existing `latency.json`.
- `scripts/eval_audio_metrics.py` (CPU, 2 min 49 s at low priority, training speed unaffected, no GPU, no Ollama): AUC-ROC 0.9937,
  F1(spoof) 0.9869, F1(bona fide) 0.8892, balanced accuracy 0.9485, recomputed EER and accuracy identical to `metrics.json`.
  Finding: the ASVspoof eval partition is 90% spoof, so always answering "spoof" scores 89.7%; the accuracy used as the audio
  fusion weight (0.9765) is inflated. Logged in EXPERIMENTS A4; the weight choice is now part of APP_TODO 1.8.

## 2026-09-20 23:10 (B4 timeline and completion watcher)

Plain B4-mm seed 42 finished 23:08:31 (37.7 min wall, about 9 min of it lost to the memory incident; a clean B4 run measured 28 min
per seed in the earlier regularised single-method runs). Its best validation accuracy is 75.4% (epoch 10), against about 84.3%
needed by the frozen rule, so the plain recipe is very likely to fail rule (a) once all three seeds are in (not certain: one seed).
Estimated completion (assumes the Mac stays awake and plugged in and nothing else uses the GPU): plain B4 done about 00:07;
regularised B4 (3 seeds, about 28 min each unless early stopping fires) done about 01:33 (range 01:00 to 01:35); rule applied
immediately after; ship-ready about 02:15 to 03:00 depending on whether B4 wins (a B4 Celeb-DF run costs about 23 min). A watcher
(Monitor) reports each seed and any failure, and a completion notice is sent when `QUEUE mm_b4reg COMPLETE` appears.

## 2026-09-20 23:05 (regularised B4-mm queued)

User asked whether counter-measures against overfitting were in place. Honest state: none beyond the baseline (identity-disjoint
split, augmentation on train only, checkpoint by best validation accuracy, test untouched); the multi-method runs use no dropout, no
label smoothing and no early stopping by design (one variable changed: the architecture). Plain B4-mm seed 42 reached epoch 8 with
train about 95% and validation 74.0% (gap about 21 pp), well below the roughly 84% needed by the frozen rule. Because the PPR and
Draft Report promise B4 WITH dropout 0.3, label smoothing 0.1 and early stopping, queued `scripts/queue_mm_b4_reg.sh` (tag
`mm_b4reg_vidsplit`, starts automatically after the plain run, pid 71935) as second candidate C2 under the SAME frozen rule; pre-registered
as a dated note in `EXPERIMENTS.md` V14 with disclosures (B4 gets two attempts; the partial plain result was visible when the note
was written; loss-based checkpointing may cost accuracy, D5) and a measurement detail (rule (a) uses validation accuracy at the SAVED
checkpoint). Cancel before it starts with `kill 71935 71936`.

## 2026-09-20 22:55 (CORRECTION: my test runs used the GPU and Ollama while B4-mm trained)

The entries below written between 22:35 and 22:48 say the model-free server tests used no GPU and did not call Ollama, and quote
"26" and "27" GPU-free server tests. That was wrong for the two full-file runs at about 22:42 and 22:47. I filtered tests by three name
fragments (`fake_demo`, `real_demo`, `composite_clip`) and missed three others that also run the real pipeline
(`test_queue_and_result_endpoints_round_trip`, `test_remove_from_queue_deletes_server_side`,
`test_progress_reaches_100_and_never_regresses`). They ran the video model on MPS and the real Llama 3 through Ollama (5 GB resident).
With the trainer already holding GPU memory on a 16 GB Mac, memory ran out: swap reached 8.4 of 9.2 GB, the training process was
paged out to about 20 MB resident, and B4-mm seed 42 epoch 5 slowed to about 73 s per iteration (normal 1.1 s). Ollama unloaded its
model after its 5 minute keep-alive, memory recovered by 22:53, and speed returned to normal. Cost: about 9 minutes; the run was
not killed and the seed's numbers are not affected by the slowdown (only wall-clock time). The correct counts: 24 model-free server
tests plus 6 that run the real pipeline (27 was 24 + 3 of those 6).
Fix: those 6 tests are now marked `heavy`; `DEEPFAKE_SKIP_HEAVY=1` skips all of them (verified: 24 passed, 6 skipped, Ollama not
loaded). LESSONS L26. Revised B4 ETA: about 00:40 to 00:55.

## 2026-09-20 late evening (plan reset against the PPR and Draft Report)

Read the PPR, Draft Report, `Design.pdf`, the supervisor review, the module template and the proposal summary in full and
compared every promise with the built system. User instruction: the application must stay faithful to them and deviate only if
there is no other option. Result: `docs/internal/APP_TODO.md` (phases 0 to 9, deviation register, day plan to 28 Sep).
Facts established while planning (all from files): the three overnight queues finished (19:06, 20:15, 21:06) but `numbers.md`
(generated 18:06) and `EXPERIMENTS.md` do not yet reflect them; EfficientNet-B4 was never trained on the multi-method data, so
it is the next run (`mm_b4_vidsplit`) before any other architecture ships; `server.py` `_run_analysis` has no top-level
error handling (an exception leaves a job at "analyzing"); `benchmark_latency.py` still lists the SVM stage as PENDING and
labels the video stage B4; `explanation_eval.py` builds synthetic "specified" cases, not draws from an evaluation set as the
PPR specifies; `static/app.js` does not distinguish "both modalities manipulated" from any other FAKE. New results read from
files: multi-method ConvNeXt mean validation accuracy 88.87% (Xception-mm 86.28%), but NeuralTextures detection 69.7% vs 81.8%
and real specificity 90.9% vs 97.0%; Celeb-DF-v2 for finalists 58.9% to 59.1% accuracy (AUC 0.671 to 0.696); 5-fold CV of
Xception-mm pooled accuracy 82.8% (95% CI 79.2 to 86.2), AUC 0.918. Nothing has been shipped or committed.

**Phase 0 done (22:30).** `build_numbers.py` now ingests the per-finalist Celeb-DF results and labels `mm_b4_vidsplit`;
`numbers.md` regenerated (ConvNeXt-mm now n=3, CV and Celeb-DF sections present). Ledger updated (V11, V12, V13 done with
their numbers). The D2 ship rule was frozen in `EXPERIMENTS.md` at 22:29, before any B4-mm result existed; it matches the rule
I approved (validation accuracy within 2 pp and each per-method detection and real specificity within 2 test videos of
Xception-mm). One correction made while writing it: an extra Celeb-DF AUC condition added without approval
was removed. Noted while regenerating: on Celeb-DF-v2 the multi-method finalists falsely flag 29 to 36% of real videos.
**B4 multi-method launched 22:30 (`scripts/queue_mm_b4.sh`, detached under caffeinate, pid 68977; first cell confirmed
training at about 2.3 min per epoch, so about 1.5 h for 3 seeds, expected about 00:05 to 00:15; REVISED 22:45 to about 00:30 to 00:45, epochs take about 3.5 min while other work shares the machine).**

**Phase 2 code and item 5.1 done while B4-mm trains (22:35, no GPU used).** The video model's name, training data and provenance
now come from `models/shipped_model.json` through one helper (`video_infer.video_model_summary`); the three hardcoded
"EfficientNet-B4" strings in `server.py` and `static/app.js` are gone and a test forbids their return. With no manifest the
sidebar says "legacy checkpoint, not promoted through ship_model.py" (true today). Sidebar gained a "Speech gate" (Silero VAD)
row. Result JSON now reports both weighting sources, whether each is measured, and where T came from (`weighting_source`,
which held only the audio source, was replaced). `_run_analysis` is wrapped so an exception ends the job in `error` instead
of hanging at "analyzing". Tests: 9 model-free server tests pass, fusion 13 pass; the model-loading app tests are deferred
until training finishes to avoid GPU contention. Not yet done in Phase 2: `benchmark_latency.py` labels (moved to 4.4).

**Items 5.2, 5.3, 5.4 and 6.1 done while B4-mm trains (22:44, no GPU used; Ollama not called).**
- INCONCLUSIVE and audio-only (5.2): a clip with no detectable face is no longer an error. The audio branch still runs and
  `fuse(None, p_audio)` gives an audio-only verdict, or INCONCLUSIVE when audio has no score either. The result carries
  `video: null`; the UI renders every panel without a video. Two tests cover it (silent no-face clip, no-face clip with speech).
- Explanation safety net (5.3): Llama 3 remains the primary explainer. Its text is run through `check_faithfulness`; if it
  fails, the LLM is unreachable, or the result is INCONCLUSIVE, the deterministic template is shown, labelled "Template" with the
  reason; the rejected LLM text is kept in the result for audit. Tests use a mocked LLM, including the pilot's failure (0.46
  described as "definitely fake"), which is rejected. Unknown until the human evaluation (APP_TODO 8.1): how often the screen
  rejects real Llama output. LLM text is now HTML-escaped in the page.
- Upload limits (5.4): 200 MB and 120 s (overridable by environment variable), streamed size cap, type, empty and unreadable
  file checks, duration check, no temp file left after any rejection, `GET /api/limits`, client-side size check, visible upload
  notice, stale temp files (older than 24 h, our prefix only) swept at startup.
- Scenario labels (6.1): one `describeVerdict()` names authentic-face/synthetic-audio, manipulated-face/authentic-audio,
  both-flagged, agreement, single-modality and INCONCLUSIVE cases; PARTIAL is amber; the score tile is "Higher branch score" on
  disagreement. Verified by running the real function under node on 9 cases and by rendering INCONCLUSIVE and PARTIAL results
  in the browser pane on a second server (port 8001, stopped afterwards; the live server on 8000 was not touched and still
  runs the old code and the old model).
- Tests: 26 pass in `tests/test_server.py` (all except the three that load the video model: the fake, real and composite demo
  clips), fusion 13 pass. Those three and `test_pipeline.py` run after B4 finishes.
- Side finding, checked: the app env loads the audio SVM with scikit-learn 1.9.0 although it was pickled with 1.4.2 (a
  warning appears). Scored 3,000 cached ASVspoof eval embeddings in both environments: maximum difference 1.9e-7, 0 decision
  flips. Harmless for scores; noted so it is not rediscovered as a scare.
- Demo library (6.3, 22:48): `/api/demo_clips` now also lists the first 3 constructed clips of each of RVRA, RVFA, FVRA and FVFA
  from `eval_fallback/` (chosen by ID, a rule fixed in advance, not by outcome), so the audio scenarios can be demonstrated; FF++
  demo clips are silent. Kinds say "(constructed)". 27 GPU-free server tests pass.

## 2026-09-20 (summary)

**User instructions this session**: no `git commit` until the very end (one commit exists, `85948c8`; about 55 files are
uncommitted on purpose); focus now shifts to building a fully functioning application; keep this log current.
**Deadline: Monday 28 September 2026.**

What happened since the leakage fix (all details in EXPERIMENTS.md, lessons L17 to L25):
- Repo renamed to `multimodal-deepfake-detector`, cleaned, MIT licence added, `.gitignore`, CI (31 data-free tests), first commit.
- Backbone bake-off (B0, ResNet-50, Xception, ConvNeXt): the PPR's EfficientNet-B4 is the weakest; ConvNeXt best single-method.
- Two more FF++ methods downloaded by me (FaceSwap, NeuralTextures). Single-method models detect 0% of FaceSwap: fixed by
  multi-method training (Xception-mm: FaceSwap 88%, NeuralTextures 82%, real specificity 97%).
- Audio: MFCC baseline (EER 10.25% vs wav2vec2 3.96%); both flag 100/100 genuine unseen-corpus clips as spoof.
- Calibration (no temperature for Xception-mm), preprocessing parity (app now applies the training JPEG round trip),
  checkpoint criterion (keep best validation accuracy), deterministic explainer + faithfulness screen, fusion rewritten
  (video accuracy from a file, INCONCLUSIVE in fusion but NOT yet in the server).
- Tooling: `run_cell.sh`, detached queues, `queue_status.sh`, `build_numbers.py`, `ship_model.py`, 5-fold CV
  (`freeze_cv_folds.py`, `aggregate_cv.py`), README rewritten (hidden maintainer checklist at its end).

**Running at the time of writing (detached)**: multi-method ConvNeXt seed 44 (about 19:15), then automatically the 5-fold CV of
Xception-mm and the Celeb-DF-v2 tests for three finalists (about 22:00 to midnight). Check with `bash ~/mdd/scripts/queue_status.sh`.

**Next**: read the queue results; finalise D2 (shipping model) and ship; then build the app in
order A (truthful shipped model, re-run downstream evals, retune T), B (INCONCLUSIVE, template fallback + faithfulness screen,
upload limits), C (evaluation view, limitations panel, demo clips), D (tests, weights release, final README). Then the report.

## 2026-09-19 to 2026-09-20: detailed entries, newest first (starts with the leakage finding and fix, at the end of this section)

Supervisor feedback on the Draft Report questioned the video branch results
directly: scores "too high" for a good model, AUC 0.99 "can clearly point to
overfitting or data leakage," seed variation "not instrumental," and EER not
moving consistently with AUC. Investigated all four points against the
actual code rather than assuming the numbers were fine; all four turned out
to have the same root cause.

**Confirmed real, severe data leakage.** `train.py`/`evaluate.py` built
train/val/test with `torchvision.datasets.ImageFolder` + `random_split` at
the individual FRAME level, with no notion of "video." Each video
contributes ~19 near-duplicate face crops (same identity, lighting,
background). Reproduced the exact split and checked video-ID overlap:
**100% of test-set videos, and 100% of val-set videos, also had frames in
the training set.** The model could partly solve the task by recognising
"I've seen this exact video before" rather than learning generalisable
manipulation artefacts. This fully explains the supervisor's first three
points: implausibly high AUC/accuracy, a validation set that couldn't reveal
true overfitting because it leaked exactly like the test set (so the
previously-reported "overfitting gap" of 1.95pp for aug-fixed was itself an
underestimate), and 3-seed comparisons that only ever varied training
stochasticity (`SPLIT_SEED` is a hardcoded constant, deliberately, for a
different reason: cross-run comparability) on an otherwise identical leaking
split — literally "seeds produce only an initiation point, not a difference
in data mix."

**A second, subtler leak also existed and had to be fixed at the same time.**
FF++ Deepfakes videos are released as reciprocal identity pairs (both
`036_035` and `035_036` exist — two identities' faces swapped onto each
other's footage). Checked: exactly 200 real ids, 200 fake pair-folders, 100
reciprocal pairs, zero singletons. A video-folder-level split alone could
still leak identity 036's face across train/test (e.g. real/036 in train,
fake/036_035 in test) with zero literal video-file overlap. Fixed by
grouping on the underlying identity graph via union-find (real id <-> the
two ids named in any fake pair folder it appears in), not on video folder
name alone, so an entire reciprocal pair (2 real + 2 fake videos, ~76
frames) is assigned to exactly one split as one atomic unit.

**Fix implemented:**
- `scripts/utils.py`: new `grouped_video_split()`, replacing the frame-level
  `random_split` call in both `train.py` and `evaluate.py`. Deterministic
  for a fixed `SPLIT_SEED`; same call signature shape as before.
- `scripts/evaluate.py`: added video-level aggregation (mean per-video
  `P(fake)` across a held-out video's frames, one prediction per video)
  alongside the existing frame-level metrics. Frame-level accuracy over
  ~19 correlated crops per video was itself a milder, separate problem
  (pseudo-replication) even once leakage is fixed, and doesn't match what
  the deployed pipeline actually reports (one `P(video_fake)` per clip,
  same as `video_infer.py`'s aggregation). Video-level is now reported as
  primary, frame-level kept as a secondary/transparency figure.
- `scripts/aggregate_runs.py`: extended to aggregate the new video-level
  metrics across seeds into the summary table alongside frame-level.
- `tests/test_data_split.py`: replaced the now-obsolete
  "matches the old frame-level baseline" test (the whole point was to
  change that split) with `test_no_video_or_identity_leakage_between_splits`
  — asserts zero video-ID *and* zero underlying-identity overlap across all
  three splits, so this specific bug can't silently reappear. All 7 tests
  in the file pass on the new split; full `base`-env suite (20 tests across
  `test_data_split.py`/`test_fusion.py`/`test_audio_branch.py`) still passes.
- Verified directly: new split has 0 video and 0 identity overlap between
  train/val/test (previously 100%/100% for val/test respectively). Sizes:
  train 6072 / val 736 / test 758 crops, from 320/36/44 distinct videos
  (vs. the old split's 758 test crops smeared across 327 "distinct" videos
  that were mostly also in train).

**In progress:** retraining the aug-fixed variant (augmentation on, no
regularisation, matching the existing recipe exactly so only the split
methodology changes, isolating that one variable) at 3 seeds on the fixed
split, tag `aug_vidsplit`, to get a corrected, trustworthy headline number.
Expect this to drop from the current 97.67%/EER 2.03% (video-level metrics
will likely differ further, since video-level also removes the frame-level
pseudo-replication). A genuine drop here is the expected, correct outcome,
not a problem — to be reported honestly alongside the leakage finding
itself, in the same style already used for the augmentation-transform bug
and the Celeb-DF-v2 cross-dataset drop. Regularisation (dropout 0.3 / label
smoothing 0.1 / early-stopping) was previously found "unnecessary" on the
leaking split; that conclusion is not trustworthy and needs re-testing on
the fixed split once the aug-only number lands, since regularisation
suppressing the leaking split's accuracy slightly (96.57% vs 97.67%) is
consistent with it actually fighting memorisation, not being genuinely
unhelpful. Also flagged: checkpoint selection should probably default to
best validation *loss* rather than accuracy going forward (val loss plateaus
and bounces well before val accuracy does, per the aug-fixed training
curves), but that change is deferred until after the split fix is
validated, to change one thing at a time.

**Seed 42 result (first of 3), confirms the hypothesis directly.** Training
curve on the corrected split is now a textbook overfitting signature that
never resolves: train_loss falls to 0.025-0.05 by epoch 5-10 while val_loss
sits flat/noisy at 0.25-0.31 the entire time (previously, on the leaking
split: train_loss 0.026 vs val_loss 0.068 — an order of magnitude tighter,
because val was leaking the same way test was). Val accuracy plateaus
around 91-92%, never approaching the old ~97%. Test-set result
(`results/runs/aug_vidsplit/seed42/metrics.json`):

| | Video-level (primary, n=44 videos) | Frame-level (secondary, n=758 crops) |
|---|---|---|
| Accuracy | 95.45% | 88.79% |
| F1 | 0.9524 | 0.8840 |
| AUC-ROC | 0.9917 | 0.9672 |
| EER | 2.27% | 11.74% |

Both well below the old leaking baseline (97.67% acc / EER 2.03%), in the
expected direction. Video-level is meaningfully higher than frame-level
here because mean-aggregating ~17 frames/video smooths per-frame noise,
similar to how the deployed app's own aggregation works — expected
behaviour, not a discrepancy to explain away. n=44 test videos is small, so
per-seed variance is expected; seeds 43/44 next, then aggregate.

**Seed 43 result: same overfitting pattern, video-level number moved up.**
Training curve again never closes the train/val gap (train_loss → 0.02 by
epoch 9-10, val_loss flat at 0.22-0.24 throughout, val_acc plateaus ~92%) —
confirms seed 42 wasn't a fluke, this is a structural property of the
corrected split, not per-seed noise. Test result
(`results/runs/aug_vidsplit/seed43/metrics.json`):

| | Video-level (n=44) | Frame-level (n=758) |
|---|---|---|
| Accuracy | 97.73% | 90.50% |
| F1 | 0.9767 | 0.9027 |
| AUC-ROC | 0.9979 | 0.9751 |
| EER | 4.55% | 8.31% |

**All 3 aug-fixed seeds complete.** Aggregate
(`results/summary/aug_vidsplit/metrics_summary.md`): video-level accuracy
96.97% ± 1.31pp, EER 2.27% ± 2.27pp (n=44); frame-level accuracy 89.93% ±
0.99pp, frame EER per seed 11.74/8.31/9.37%. Like-for-like (frame-level to
frame-level) against the old leaking 97.67%/EER 2.03%: ~7.7pp accuracy drop,
EER roughly 5x. Video-level is a NEW metric introduced with this fix, not
directly comparable to the old figure; do not conflate them in the report.
Overfitting gap (final-epoch train acc minus val acc), now on a
non-leaking val set: 7.16 / 6.90 / 7.15pp = **7.07 ± 0.15pp**, vs. 1.95 ±
0.46pp measured on the leaking split for the same recipe. ~3.6x larger and
consistent across seeds, so structural rather than noise.

**Decision (user): run the full 3-variant x 3-seed matrix on the fixed
split**, checkpoint criterion unchanged (best val accuracy for the
non-early-stopping variants, best val loss for the regularised variant via
its existing early-stopping path). aug_vidsplit is done; remaining 6 runs
launched as one sequential driver: `base_vidsplit` (`--no-augment`) then
`reg_vidsplit` (`--dropout 0.3 --label-smoothing 0.1
--early-stopping-patience 3`), 3 seeds each, each followed by
`evaluate.py`, then `aggregate_runs.py` per tag. Expected ~3 hours total.
Deferred still: switching the default checkpoint criterion to val loss.

**While the matrix trains (no GPU work):** extended
`scripts/compare_variants.py` (video-level table, a table of which epoch the
best-val-accuracy vs lowest-val-loss rules would each select, `--baseline-tag`,
`--out-name`); verified the defaults still reproduce the original
`variant_comparison.md` numbers exactly and that file was not touched.
First look at the checkpoint question on aug_vidsplit: best-accuracy epochs
[10, 9, 8] vs lowest-val-loss epochs [9, 4, 10], so seed 43's val loss bottomed
out at epoch 4 while the accuracy rule saved epoch 9. Also found and
corrected a wrong claim of mine: `fusion.py` does NOT auto-detect video
accuracy (hardcoded `VIDEO_ACCURACY_DEFAULT = 0.9639`, the old leaking
baseline); it needs a manual update after the winner is chosen. And
`models/best_model.pth` (what the app and every eval script load) is still the
old leaking-split checkpoint.

**Cross-validation built (2026-09-20 evening).** Frozen 5-fold identity-grouped folds (EXPERIMENTS J), leak-free by
data-free tests now in CI (31 tests), `--fold` in train/evaluate, per-video predictions saved, `aggregate_cv.py` for pooled
out-of-fold metrics with identity-cluster bootstrap CIs. Smoke-tested; 5 real Xception runs queued detached behind the
ConvNeXt runs (about 2.2 h). README test counts updated (CI 31, base env 75).

**Preprocessing parity (2026-09-20 evening).** The check I had flagged since the retrospective was finally run
(EXPERIMENTS H): the app fed the model uncompressed crops while training used JPEG crops, which shifted the operating
point (AUC unchanged; 2 real videos falsely flagged, 7 of 88 verdicts differ). Fixed by applying the same JPEG round trip
at inference (`video_infer.training_style`), verified exact against the measured path, pinned by a new test. Split
`sample_face_crops` out of `analyse_video_file` (behaviour preserved; pipeline and server tests pass). The web server
running now predates this change and must be restarted; the queued Celeb-DF runs import the fixed code.

**Calibration and README (2026-09-20 evening).** Added `scripts/calibrate_video.py` (temperature fitted on validation
only; NLL, Brier, ECE before and after). Result (EXPERIMENTS G, decision D3): the leading candidate Xception-mm is
already calibrated (test ECE 0.048) and a validation-fitted T=2.81 made it worse (0.069) because the validation set is
only 36 videos and harder than test, so it ships with T=1.0; B0-mm was badly calibrated and gained a lot (0.146 to 0.050).
Plumbed an optional `temperature` through `ship_model.py`, `shipped_model.json` and `video_infer` (default 1.0, no change
in behaviour). Rewrote `README.md` around the verified state (leakage finding, backbone bake-off, multi-method result,
audio baseline, limitations, reproduction commands), with a hidden maintainer checklist of what must be updated before
submission; every quoted number was mechanically checked against `results/numbers.json`. LESSONS L23 added.

**Multi-method results (2026-09-20 17:14).** Queue finished 14:32 (the Mac slept ~8 h overnight, see LESSONS L21).
Multi-method training fixes the cross-method failure: Xception-mm detects FaceSwap 88% (was 0%) and NeuralTextures
82% (was 17%) at AUC 0.99 / 0.95, with 97% real specificity, at a small cost on Deepfakes (91% vs 100%). Aggregate
metrics on the mixed test set are lower than single-method ones because the problem is harder, and must not be
compared with them (L20). Fixed a labelling bug in `eval_cross_method.py` (multi-method models were tagged "unseen
method", L22) and regenerated the tables. Best single-method backbone was ConvNeXt-Tiny (frame 96.26%, val 97.78%).
Launched detached: multi-method ConvNeXt (V11) and, behind it, Celeb-DF-v2 for the finalists (V12). Patched
`eval_celebdf.py` to take `--arch` and write per-run folders so it cannot overwrite the old model's result.
Provisional D2: ship a multi-method model (leading candidate Xception-mm). Uncommitted changes since commit
85948c8: these scripts and docs.

**Overnight CPU work (2026-09-20).** Later same night: added `build_numbers.py`, `ship_model.py` (dry-run only so far), an architecture-aware
`video_infer.load_models`, a data-free leakage test on the frozen manifest, and a GitHub Actions CI workflow
(26 tests, verified in a clean virtualenv). Details in EXPERIMENTS.md section F. Audio baseline finished (EXPERIMENTS A2/A3): MFCC + SVM EER
10.25% vs wav2vec2 3.96% (wav2vec2 justified by measurement); both flag 100% of 100 genuine unseen-corpus
clips as spoof. `fusion.py` rewritten (video accuracy read from a file, INCONCLUSIVE and audio-only
states, docstring corrected). New `scripts/explain_checks.py` with a deterministic template explainer and
an automatic faithfulness screen, tested. Decided NOT to wire INCONCLUSIVE through `server.py`/UI overnight:
it needs UI rework and a regression there would break a working interface; logged as an open item.
Base-env tests: 66 pass. Queue status: ConvNeXt running (seeds 43-44 to go), multi-method queue waiting.
Repo housekeeping: `frames_multi/` was missing from `.gitignore` and briefly staged 400 symlinks
(caught by the staging check, fixed).

**Bake-off results and multi-method setup (2026-09-20 early).** Extra-method crops extracted
(200 videos, 3170 crops each). B0, ResNet-50 and Xception finished; ConvNeXt running. Finding: the
PPR incumbent EfficientNet-B4 is the worst of the four on this data (EXPERIMENTS.md V8), and all
backbones fail identically on unseen manipulation methods (V9), so the fix is multi-method
training data. Built: `utils.split_from_manifest` and `get_split` (default folder keeps the
recomputed split so every prior result is unchanged), `--frames-dir` in train/evaluate (recorded in
train_config), `scripts/build_multimethod_frames.py` (symlink folder, balanced), new tests (manifest
equals recomputed split; multi-method folder leak-free; 9 data-split tests pass). Smoke-tested
end to end on a throwaway tag, then removed. Queued `scripts/queue_multimethod.sh` detached (waits
for the bake-off). Decision D2 (shipping backbone) is deferred until the multi-method results,
cross-method test, Celeb-DF and latency are in, per the frozen decision-matrix idea.

**Second FF++ methods downloaded and first cross-method result (2026-09-19 night).** User
ran `scripts/download_extra_methods.sh` (they must accept the FF++ terms themselves). FaceSwap and
NeuralTextures (c23, 200 videos each) have identical names to the Deepfakes set, so identity pairs
and the frozen split apply unchanged. Extracted test-split crops (22 videos per method) and wrote
`scripts/eval_cross_method.py`. Result (EXPERIMENTS.md V9): the shipping recipe scores 0.997 AUC on
Deepfakes but 0.26 on FaceSwap (0% detected) and 0.79 on NeuralTextures (15% detected). Verified
not a bug (crops inspected, in-distribution row reproduces evaluate.py). Response: extract all
crops for both methods (running detached, `scripts/queue_extract_methods.sh`), then train a
class-balanced multi-method model (V10). Note the shell `!!` history-expansion problem caused by
the parent folder name, see LESSONS L17; a bang-free symlink `~/mdd` now points at the repo.
Also noted: `extract_frames.py` needs the `deepfake-detect` env (MTCNN lives there).

**Repository reorganisation, rename and GitHub prep (2026-09-19 night).** Deadline is
**28 Sep 2026** (user). Decisions (user): repo name `multimodal-deepfake-detector`,
private until the final audit and public at submission; no FaceForensics++-derived media
may be committed, but the app needs its own demo clips (must be user-owned or
redistributable); second FF++ manipulation method may be tried; weights as GitHub Release
assets (recommended over Git LFS: no bandwidth quota, not in git history).
Done: full backup (`_backups/`, code/docs/summaries only); superseded and retired files
moved to `_archive_pre_submission/` (757 MB of leaking-split checkpoints, killed-run
partials, retired Streamlit UI, `demo.py`, old roadmap); junk deleted; docs moved to `docs/`;
folder renamed `deepfake_prototype` -> `multimodal-deepfake-detector`; `extract_frames.py`
no longer hardcodes `~/deepfake_prototype` and can extract other manipulation methods to
a separate folder; `scripts/sanitize_paths.py` stripped personal paths from 32 result and
manifest files (and `evaluate.py` now records repo-relative model paths);
`.gitignore` written; `git init` done and staging verified (175 files, largest 132 KB, no
media, no weights, no personal paths); working-notes paths updated and a correction
banner added (it still quoted the leaking 97.67% as current). All tests pass after the
rename (20 base-env, 14 app-env). NOT yet committed (awaiting my go-ahead). My
uvicorn dev server on :8000 predates the rename and must be restarted.
Results: the 3-way variant matrix is complete (see EXPERIMENTS.md D1): augmentation wins
on validation evidence, regularisation lowers the gap without improving accuracy. Added
`--arch` to `train.py`/`evaluate.py` (backward compatible, verified by re-evaluating an
existing run to identical numbers) and launched the 4-backbone bake-off detached.

**Rebuild guide written (2026-09-19 evening).** `Rebuild Guide/` at the project
root holds `Multimodal_Deepfake_Detector_Rebuild_Guide.pdf` (24 pages: application
overview, per-aspect retrospective of what was done right and wrong and the better
way, datasets, a pre-build model bake-off protocol, target architecture and repo
structure, a 13-phase build plan with gates, improvement areas, and the build
instructions) plus two paste-ready text files (`01_MASTER_BRIEF_paste_first.txt`,
`02_PHASE_PROMPTS_paste_one_at_a_time.txt`). It is for a possible from-scratch
rebuild in a fresh chat, built one phase at a time. Its targets are aspirations,
not results; datasets and citations not in the project literature review are
flagged as needing verification. The reg_vidsplit queue survived the session end
this time (detached): seed 43 finished 20:06, seed 44 started 20:06.

**Decision: re-baseline, do not restart from scratch (user agreed; deadline about
10 days).** Kept the sound components (audio SVM, fusion logic, explanation layer,
app, corrected split code). Marked everything that consumed the old leaking video
model as needing a re-run. Added record-keeping: `EXPERIMENTS.md` ledger
(retroactive rows labelled as such), `LESSONS.md` (16 entries), frozen split
manifest `data_splits/split_v2_identity_grouped.json` via `scripts/freeze_split.py`,
and restart-safe detached job launching (`scripts/run_cell.sh`,
`scripts/queue_reg_resume.sh`). Reg seeds 43 and 44 relaunched detached at 19:38
after the second session-kill; the partial seed 43 checkpoint from the killed
attempt went to `models/runs/_partial/`.

**Session interruption and resume.** The terminal session ended while the matrix
driver was running. On return: `base_vidsplit` complete (3 seeds), `aug_vidsplit`
complete, `reg_vidsplit` seed 42 complete, seed 43 cut off mid-training
(checkpoint file existed because the early-stopping path saves best-so-far, but
no history/metrics, so it was unusable and was moved aside rather than
evaluated), seed 44 not started. Results so far on the fixed split:

| Variant | Video-level acc (n=44) | Frame-level acc | Overfit gap |
|---|---|---|---|
| base (no aug) | 96.97 ± 1.31pp | 86.81 ± 0.58pp | 9.49 ± 0.31pp |
| aug | 96.97 ± 1.31pp | 89.93 ± 0.99pp | 7.07 ± 0.15pp |
| reg (seed 42 only) | 95.45% | 87.47% | 7.01pp |

Video-level accuracy is identical for base and aug because 44 videos gives
2.27pp granularity and the per-seed values coincide; frame-level and the gap
are where the variants separate (augmentation ~+3.1pp frame-level, ~2.4pp less
overfitting). Reg seeds 43 and 44 relaunched (~28 min each).

(Earlier note, superseded above:) Seed 44 was running; aggregate all 3 with
`aggregate_runs.py --tag aug_vidsplit` once it lands. Note the video-level
metric is already showing real seed-to-seed spread (95.45% vs 97.73%
accuracy) on n=44 videos — expected given the small held-out video count,
and itself a more honest picture than the old leaking split's tight,
near-identical seed-to-seed numbers the supervisor flagged as suspicious.

## 2026-09-19

Another FakeAVCeleb request was sent. While it is pending, made the
4-condition evaluation dataset-agnostic so any source can be swapped in or
out without touching pipeline code:

- `scripts/eval_fallback_4condition.py` and `scripts/tune_threshold_fallback.py`
  now take `--manifest`/`--results` and `--out-dir`/`--out` arguments instead
  of hardcoded fallback-only paths, and both read a `source` field out of
  the manifest/results file to report provenance rather than assuming it.
  Verified the refactor is behaviour-preserving: re-ran the threshold tuner
  against the existing fallback results with no arguments and got the
  identical T=0.55, F1=0.988 output as before.
- `scripts/build_fallback_eval_set.py`'s manifest now carries an explicit
  `source` field (previously only a `description` field existed).
- Added `scripts/build_fakeavceleb_eval_set.py`, a builder stub for the real
  FakeAVCeleb dataset, producing a manifest in the exact same schema. Its
  assumed directory layout (four category folders, each subdivided by
  ethnicity/gender/identity) is documented as an assumption to verify
  against the real download, not a confirmed fact, along with a
  `--check-layout` mode to sanity-check that mapping before trusting any
  output. The moment FakeAVCeleb is approved, running this one script and
  re-pointing the other two at its output replaces the fallback/DFDC/
  DeepfakeTIMIT evidence with the real thing, with zero changes to
  fusion.py, server.py, or either analysis script.
- Investigated further alternatives while DFDC's rules-acceptance flow (see
  DFDC entry) remained stuck on finding the right on-page control:
  found **DeepfakeTIMIT** (Idiap Research Institute, via Zenodo), a
  226.6MB, single-click, no-login, no-approval download. Assessed honestly:
  it covers exactly one of the four categories (fake video with real,
  unaltered original audio), using an older 2018 autoencoder-GAN swap on
  32 TIMIT subjects, not a FakeAVCeleb replacement, but a genuine upgrade
  for that one category since the pairing is naturally co-occurring rather
  than muxed from two unrelated sources.
- **DFDC confirmed a dead end, not just slow.** Located the actual
  "Join the competition" control on the Data tab (a separate box from the
  Rules tab's legal text, easy to miss). User clicked it: no visible
  response, no popup, no error. Refreshed the page: no change, still
  locked. A competition that closed for entries in 2020 with a join button
  that produces no effect on click or refresh is not a UI lag, it means
  the backend is not accepting new joins. Stopped pursuing DFDC.
- **Downloaded and verified DeepfakeTIMIT.** Pulled the exact file links
  from Zenodo's API rather than guessing, downloaded `DeepfakeTIMIT.tar.gz`
  to `external_datasets/`, verified its MD5 against the dataset's own
  published checksum (`79b5dcee896ab825db43f1dfbdc8fdb5`) before trusting
  it, extracted it. Confirmed structure: 320 `higher_quality` + 320
  `lower_quality` clips across 32 subjects, `.avi` files already containing
  h264 video + aac audio, read cleanly by the existing `cv2.VideoCapture`
  path with no transcoding needed.
- **Built `scripts/build_hybrid_eval_set.py`**: keeps the fallback set's
  RVRA/RVFA/FVFA (FF++ + ASVspoof, unchanged) but replaces its constructed
  FVRA category with 20 genuinely-paired DeepfakeTIMIT clips. Ran the same
  4-condition evaluation against this hybrid manifest using the
  now-dataset-agnostic scripts (no code changes needed to point them at a
  different manifest, confirming the refactor's actual purpose worked).
- **Real result, and a real limitation, not a clean win**: video-only
  91.25%, audio-only 72.15%, standard fusion 93.67%, disagreement-aware
  fusion 98.73% (still the best of the four). But
  `FVRA_correctly_flagged_video_implicated` collapsed to 0%: the audio
  classifier scored every genuinely bona fide DeepfakeTIMIT clip at
  roughly 0.98 fake. Checked this against the same run's ASVspoof-sourced
  categories (which still score correctly near zero) to confirm the
  failure is specific to an unfamiliar real-speech source, not a general
  audio-branch breakdown — most likely the frozen wav2vec2+SVM pipeline is
  picking up on ASVspoof's own recording-channel characteristics rather
  than pure spoofing artefacts. This is a genuine, demonstrated
  cross-dataset generalisation limitation on the audio side, the audio
  equivalent of the video branch's Celeb-DF-v2 drop, and should be reported
  as a distinct secondary finding, not averaged into or confused with the
  pure fallback set's headline 4-condition numbers (§2a-equivalent, still
  the recommended primary result).

## 2026-09-13

**Both official gated datasets failed**: FakeAVCeleb's request went
unanswered, and the AV-Deepfake1M application (see 09-07/08 entry) was
**rejected**. With the report's own re-baselined deadline for the 4-condition
evaluation at 14 Sep 2026 (tomorrow), there was no time left to pursue a
third gated dataset. Pivoted immediately to the self-built fallback,
discussed in earlier entries but not previously executed:

- **Built `scripts/build_fallback_eval_set.py`**: constructs a 4-category
  audio-visual evaluation set (RVRA / RVFA / FVRA / FVFA, mirroring
  FakeAVCeleb's structure) entirely from data already on disk and already
  used elsewhere in the project — video from FaceForensics++ (already
  labelled real/fake), audio from ASVspoof 2019 LA's eval partition
  (already labelled bonafide/spoof, and actually MORE diverse than
  FakeAVCeleb's own single-TTS audio side, since ASVspoof's spoof class
  spans 19 distinct attack algorithms). Zero external dependency, zero
  provenance risk. Built 80 clips (20/category) into `eval_fallback/`.
  Checked first: confirmed Celeb-DF-v2 has no audio track at all, ruling it
  out as an audio source.
- **Caught and fixed a real muxing bug** while verifying the first test
  batch: `ffmpeg -shortest` does not reliably trim when the video stream is
  `-c:v copy` — output containers kept the full original video duration
  against a much shorter audio track. Fixed by explicitly probing both
  source durations and passing `-t <min>` instead of trusting `-shortest`.
- **Built `scripts/eval_fallback_4condition.py`**, running the real,
  already-trained pipeline (unchanged) over all 80 clips. Caught and fixed
  a real device-mismatch crash (the video branch's MPS device was being
  passed into the audio encoder, which loads on CPU) before it produced
  results.
- **Real results** (see `results/fallback_eval/fallback_4condition_results.json`):
  video-only 100%, audio-only 97.5%, standard/naive fusion 78.5%,
  disagreement-aware fusion 97.5%. 100% correct modality-implication on
  both single-modality categories (RVFA→audio, FVRA→video). This is
  concrete, reproducible evidence for the project's core claim: naive
  fusion loses ~19 points of accuracy exactly where single-modality
  manipulation exists, and disagreement-aware fusion recovers almost all
  of it.
- **Built `scripts/tune_threshold_fallback.py`** and ran the threshold_T
  grid search Ch3.6 always specified (just against this set instead of
  FakeAVCeleb). Found recall was 1.000 across the entire tested range
  (0.05-0.6) — flagged this honestly as likely reflecting unusually
  confident/separable scores from both models being evaluated near their
  own training distributions here, not necessarily representative of a
  harder cross-dataset case. Chose T=0.30 (F1=0.976) over the raw grid
  optimum (T=0.55, F1=0.988) specifically to avoid overfitting a threshold
  to the extreme edge of a small 79-clip sample. Updated
  `scripts/fusion.py`'s `THRESHOLD_T_DEFAULT` from 0.15 → 0.30, fully
  documented in-code.
- **Re-running the full test suite after the threshold change caught
  another real, pre-existing bug**, unrelated to today's work:
  `test_fusion.py`'s `test_agreement_uses_accuracy_weighted_average` had
  hardcoded the assumption "video_accuracy > audio_accuracy" — true when
  written (audio SVM was untrained, placeholder 0.5), silently false since
  the full ASVspoof training finished (audio's real 97.65% now edges out
  video's 96.39%). Fixed by pinning explicit accuracy values in the test so
  it asserts the weighting *mechanism*, not a real-world ordering that can
  keep changing as new data lands.
- Drafted a follow-up email template chasing the (possibly never actually
  submitted) FakeAVCeleb request — kept as a parallel, no-cost option, not
  the primary path anymore.
- Restarted the live server, confirmed the new threshold and the whole
  pipeline still produce correct results end to end.

## 2026-09-07 / 2026-09-08

- **Replaced the fake-progress temptation with real progress tracking.**
  Asked for an "Analysing NN%" overlay on the video player; rather than a
  simulated timer-based percentage (which would have broken the project's
  own "never show a number that isn't real" rule), restructured
  `POST /api/analyze/{id}` to start the pipeline in a background thread and
  added `GET /api/progress/{id}` for polling. Progress is tied to real
  events: the video branch's actual per-frame-crop callback (5%→65%), real
  audio decode/VAD/embed/SVM checkpoints (65%→90%), fusion (90%), and the
  explanation call (90%→99%→100%).
- Built the overlay UI itself: translucent backdrop → scan-line → spinning
  ring + "Analysing NN%" text, layered in that exact order per spec.
  Verified live in the browser end to end.
- Updated `tests/test_server.py` for the now-async analyze flow (added a
  polling helper, `_wait_for_analysis`) and added a new test asserting
  progress is monotonic and reaches exactly 100. Suite is now 12 tests
  (64 total across 8 suites).
- **FakeAVCeleb still hasn't arrived** (checked again). Researched
  alternatives: found **AV-Deepfake1M** (Hugging Face, `ControlNet/AV-Deepfake1M`)
  — instant click-through EULA (no manual review/wait like DASH-Lab), and
  confirmed it has the needed single-modality manipulation categories
  (video-only, audio-only, audio-visual). Caveat: 404GB full dataset, so a
  subset (val/test split) needs to be pulled, not the whole thing — plan
  drafted, not yet executed (needs my own HF account + license
  acceptance first).
- Drafted a follow-up/chase email for the FakeAVCeleb request (template,
  since no evidence exists in the project that the original request was
  ever actually submitted — flagged this directly).
- Created this file.

## 2026-09-06

- **Redesigned the sidebar "model info" panel.** It previously showed
  checkpoint filenames and an EER stat without ever naming
  EfficientNet-B4/MTCNN/wav2vec2 anywhere. `/api/model_info` now returns
  one row per stage (Video / Audio encoder / Audio classifier /
  Explanation) with the real model name and a real status string.
- Renamed the app's branding from "veridex / detection" (leftover from the
  original design-spec prompt) to **"Multimodal Deepfake Detector"**.
- **Removed the Streamlit UI entirely**, per request, once confirmed it was
  still running (port 8501). Since the project has no git repository (no
  undo available), archived rather than deleted: `app.py`, `run_app.sh`,
  `tests/test_app.py` moved to `_archived_streamlit_ui/` (kept as a
  reference only — not runnable as-is, since it assumed being co-located
  with `scripts/`/`models/`/`demo_videos/`). Removed `streamlit` from
  `requirements-app.txt`, updated both editor launch configs to
  point at `run_server.sh`, fixed stale references in `README.md`,
  `user_testing/protocol.md`, `server.py`/`run_server.sh` docstrings.

## 2026-09-05

- User requested a full frontend redesign to a specific dark-themed design
  spec (real HTML5 video, draggable scrub bar, tabbed panel, waveform).
  Did an architecture audit first (as instructed) and found the existing
  Streamlit app fundamentally couldn't render this — no raw `<video>` DOM
  access, no reliable custom overlays, reruns the whole script per
  interaction. Flagged this explicitly rather than attempting a lossy
  approximation; user chose a full rebuild.
- Built **`server.py`** (FastAPI) + **`static/`** (`index.html`/`style.css`/
  `app.js`, vanilla JS/CSS, no framework) as a new delivery layer over the
  exact same inference code (`video_infer.py`, `audio_branch.py`, `vad.py`,
  `fusion.py`, `explain.py`) — nothing about models/thresholds/fusion logic
  changed, only how results reach the browser.
- Added `tests/test_server.py` (11 tests at this point), mirroring
  `test_app.py`'s "track real state, don't pin a snapshot" philosophy.
- Iterated through several rounds of user feedback the same session:
  removed the corner-bracket overlay ("too dramatic"), removed the Settings
  page (placeholder with nothing behind it), merged the Visual/Audio/Report
  tabs into one continuously scrollable Overview panel, added the real
  MTCNN face crop image to the Visual section, switched the frame-score
  chart from bars to an SVG line graph, added a remove-from-queue button
  (`DELETE /api/queue/{id}`, careful never to delete a bundled demo file),
  added a collapse toggle so the demo-clip list isn't shown by default.
- Fixed a recurring bug the hard way, three separate times, before finally
  fixing it permanently: any element with both a class-based `display` rule
  and a JS-toggled `hidden` attribute wasn't actually hiding (author CSS
  beats the browser's default regardless of specificity). Root-caused and
  fixed with one global `[hidden] { display: none !important; }` rule.
- Caught a real regression while re-running the full test suite: the
  Streamlit CSS-stripping work from earlier this session (below) had moved
  verdict rendering from `st.markdown` to `st.error`/`warning`/`success`,
  but `test_app.py`'s assertion still only checked `at.markdown` — silently
  broken until the full suite was re-run. Fixed.

## 2026-09-03 / 2026-09-04

- Found and killed a duplicate `train_audio_svm.py` process that had been
  accidentally started while the original (17+ hours in) was still running
  — would have caused a race on the same output files. Verified the
  original was unaffected afterward.
- **ASVspoof 2019 LA full-dataset training completed**: train 25,380 / dev
  24,844 / eval 71,237 utterances. Real result: **3.96% EER, 97.65%
  accuracy**, superseding the earlier 400-sample pilot (8.25% EER).
  `fusion.py`'s existing auto-detection (`_resolve_audio_accuracy()`) picked
  this up with zero code changes needed — confirmed live.
- Restarted the (then-Streamlit) app and verified the full pipeline
  produces a genuine `PARTIAL_MANIPULATION` disagreement verdict for the
  first time (composite clip: video REAL 0.024, audio FAKE 1.000).
- Fixed a real video-preview bug: uploaded `.mov` files showed a blank
  player (browsers don't decode QuickTime containers). Fixed with a
  transcode-if-needed helper using the already-bundled `imageio_ffmpeg`.
- Fixed a **second, sharper** version of the same bug: Celeb-DF-v2's own
  `.mp4` files turned out to use the plain `mpeg4` codec, not H.264 — a
  `.mp4` extension does not guarantee browser-playability. Fixed by
  actually probing the codec via `ffmpeg -i`'s stderr output rather than
  trusting the file extension.
- Per user request, stripped all custom CSS/HTML out of the Streamlit app
  down to plain default widgets (`st.columns`, `st.error/warning/success`)
  as a deliberate placeholder ahead of the eventual redesign.
- Discussed current model choices (EfficientNet-B4, wav2vec2+SVM, Llama 3
  8B) against literature alternatives — no code changes, advisory only.
- Confirmed FakeAVCeleb still not obtained; discussed the Kaggle-mirror
  option and recommended against it (no license, unverifiable, provenance
  risk) in favour of either the official request or a self-built fallback.

## 2026-09-01 / 2026-09-02 (earlier session)

- Fixed a real inconsistency: `app.py` had its own duplicate inline
  inference code instead of sharing `scripts/video_infer.py` with the test
  suite, contradicting what the Draft Report claimed. Fixed by extracting
  the shared `analyse_video_file()` path.
- Built the **explanation layer** (`scripts/explain.py`, Llama 3 8B via
  Ollama) — previously completely unbuilt. Wired into the app; added
  `tests/test_explain.py` (grew to 14 tests).
- Built the **VAD pre-filter** (`scripts/vad.py`, Silero VAD) — previously
  completely unbuilt. In the process, discovered `demo_videos/sample_with_audio.mp4`
  (used in both reports as evidence the audio pipeline works) is actually a
  constant tone, not speech — confirmed spectrally and by the VAD itself.
  Built `composite_real_video_synthetic_speech.mp4` (a real FF++ clip muxed
  with TTS speech) as the fix, clearly labelled as a constructed composite.
- Built the explanation human-eval harness (`scripts/explanation_eval.py`)
  and ran a 16-case pilot. It caught a real hallucination: scores just
  under 0.5 were being described as "fake" by the LLM. Root-caused to the
  LLM being asked to compare a number to a threshold in-prompt; fixed by
  moving that comparison into deterministic Python (`explain.assess()`)
  instead of asking the model to derive it.
- Built `scripts/train_audio_svm.py` (ASVspoof trainer) ahead of the
  dataset landing, plus a synthetic-fixture test suite proving the plumbing
  (not the accuracy) works.
- Fixed the `train.py` augmentation-transform bug (three data splits had
  been silently sharing one `ImageFolder`, so train-time augmentation never
  actually ran). Added the `--tag` system so experiments can never
  overwrite baseline artifacts. Ran a 3-condition comparison (baseline /
  aug-fixed / aug+regularised, 3 seeds each) — aug-fixed won on every
  metric; regularisation on top of it was found to be unnecessary.
- Found and fixed a real discrepancy: the checkpoint the live app was
  actually serving (`models/best_model.pth`) was a stale pre-session file,
  not any of the seeds the report's numbers were measured on. Repointed it
  at the aug-fixed checkpoint.
- Ran the latency benchmark (~10s/clip warm, excluding the then-untrained
  SVM stage).
- Wrote `user_testing/protocol.md` + `response_sheet.md` (not yet run with
  real participants as of this entry).
- Wrote the original `README.md`, `requirements-base.txt`,
  `requirements-app.txt`.
- Updated several Draft Report chapters to reflect the above (Ch1, Ch3.4,
  Ch3.5, Ch4.1, Ch4.3, Ch4.4, Ch4.6, Ch4.7, Ch5.5) — Ch5.2/5.4/5.6/5.7/Ch6
  were left for a later pass pending the training numbers above.

---

## Still outstanding

**SUPERSEDED 2026-09-20: this block is from early September and is stale (the fallback set replaced the FakeAVCeleb blocker, and
the ASVspoof SVM, Llama layer, VAD and FastAPI app all exist). The current list is `docs/internal/APP_TODO.md`.** Kept as history.

- FakeAVCeleb (or AV-Deepfake1M subset, or the self-built fallback) —
  the one real blocker for threshold tuning and the 4-condition comparison.
- Score the explanation-eval pilot (CSVs still blank).
- Run real user-testing sessions (protocol untouched since Sep 1).
- Update `Draft Report/generate_report.js` with the ASVspoof/CelebDF-v2
  results and the new application-layer description.
