# docs/: index

Where two files disagree, the order of authority is: `EXPERIMENTS.md`, then `DEV_LOG.md`, then `../results/numbers.md`.

## Records kept throughout the project

| File | What it is |
|---|---|
| `EXPERIMENTS.md` | The ledger: every experiment, decision and retraction, with its pass rule and result (V, A, F, H, O, T, M, L, E, U series) |
| `DEV_LOG.md` | What was done and when, newest first (append-only); the report's appendices cite it by date |
| `LESSONS.md` | What went wrong and the rule that follows (L1 to L33) |
| `TESTING_GUIDE.md` | How to test every model and the app, and what to expect from each demo clip |

## Decision records (`decisions/`)

| File | What it is |
|---|---|
| `video_backbone_decision.md` | EfficientNet-B4 to Xception: evidence, caveats (s13), suggested wording (s16) |

## User testing and the interface (`user_testing/`)

| File / folder | What it is |
|---|---|
| `protocol.md`, `response_sheet.md` | Session protocol (rounds 1 to 3; short and full sessions) and paper fallback sheet |
| `survey_form.html`, `survey_form_short.html` | Offline survey forms (one sheet per participant and round; built by `../scripts/build_survey_form.py`) |
| `materials/` | Blank consent form and information sheet (`consent/`); the no-face clip used in task 6 is `../demo_videos/noface_silent.mp4` |
| `responses/` | Survey CSVs; `raw_as_downloaded/` keeps them exactly as received (SHA256SUMS); the participant-identity correction of 27 Sep |
| `results/` | Scored summaries and `round1_data_quality.md` (the carry-over defect and what can be used) |
| `heuristic_evaluation_v1.md` | Heuristic review of v1 (one developer-evaluator; not user testing) |
| `findings.md` | The design iteration record: every interface change traced to its source (C1 to C38), with before/after measurements |
| `design_brief/` | The MVP brief given to the UI/UX designer |
| `ui_v1_snapshot/`, `ui_v2_snapshot/` | The two user-tested interfaces, byte for byte (run them with `../run_v1_interface.sh`, `../run_v2_interface.sh`) |
| `ui_v4_final_snapshot/` | The final interface as frozen on 27 Sep; `tests/test_server.py` fails if `static/` differs from it |
| `screenshots/v1`, `v2` | The two user-tested interfaces (Figure 5.9 compares them) |
| `screenshots/v3`, `v4` | The two untested versions after round 2, the evidence behind `findings.md` C21 to C34 (v3's code was lost) |
| `screenshots/v4_final` | The final interface, with figure crops (report Figures 4.3 to 4.5, 4.7 and Appendix C) |

Working notes and report-writing aids are kept outside the repository.
