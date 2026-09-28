# Heuristic evaluation of interface v1 (before user testing)

Written 2026-09-24 19:03 +08. Interface version: v1, frozen in `docs/user_testing/ui_v1_snapshot/` (sha256 in `SHA256SUMS`). Evidence: the screenshots
in `docs/user_testing/screenshots/v1/` (named below) and measurements taken on the live page on 2026-09-24 about 18:55.

## What this is, and what it is not

A **heuristic evaluation**: an inspection of the interface against Nielsen's ten usability heuristics (Nielsen, 1994), each problem rated on
Nielsen's 0 to 4 severity scale (0 not a problem, 1 cosmetic, 2 minor, 3 major, 4 usability catastrophe). It was carried out by **one evaluator,
the developer** , not by users and not by independent usability experts. Nielsen recommends three to five evaluators because
one finds only part of the problems; a single developer-evaluator also knows how the system works, which hides problems a newcomer would hit.
So this is **not user testing** and is never reported as such. Its job is to (a) document v1's problems with evidence before any change, and
(b) state hypotheses that round 1 of real user testing (ledger U1) confirms or refutes. Every v2 change must trace to a round 1 finding, to this
review, or to the developer's stated direction, and the report says which.

User's direction for v2 (2026-09-24): "too technical, I want it to look user friendly", "it looks unfinished"; dark but polished; verdict first;
technical detail kept visible.

## Measured, not judged

**Text contrast** (WCAG 2.1 success criterion 1.4.3 requires at least 4.5:1 for normal-size text), computed from the live page's computed colours
and the nearest opaque background:

| Text | Contrast | Size | Passes 4.5:1? |
|---|---|---|---|
| Sidebar section labels (QUEUE, DEMO CLIPS) | 2.02:1 | 10 px | no |
| Model details in the sidebar | 2.64:1 | 9.5 px | no |
| Inactive navigation tabs (History, Evaluation) | 2.64:1 | 12 px | no |
| Clip duration in the list | 1.94:1 | 10 px | no |
| Score labels (OVERALL SCORE, VISUAL SCORE, AUDIO SCORE) | 2.53:1 | 10 px | no |
| Section headings (VISUAL, AUDIO, REPORT) | 2.59:1 | 10 px | no |
| Explanation source note | 1.98:1 | 12 px | no |
| Source path under each limitation | 2.00:1 | 10 px | no |
| Verdict sub-line | 5.54:1 | 11 px | yes |
| Explanation text | 6.73:1 | 12 px | yes |
| Time display | 5.45:1 | 11 px | yes |
| Frame anomaly rows | 10.06:1 | 12 px | yes |
| Empty-state message | 12.69:1 | 13 px | yes |

**8 of 13 measured text styles fail the 4.5:1 minimum.** Text size: **58 of 89 visible text elements (65%) are smaller than 12 px** (sizes 8 to
11 px); the largest body text is 13 px. The stylesheet has **no responsive breakpoints** (its only `@media` rule is for printing), and the page has
2 ARIA attributes in total (1 in `index.html`, 1 in `app.js`).

## Strengths to keep (the honesty features; several are covered by tests)

- Real progress while analysing ("Analysing NN%", from the server's stage progress), not a spinner (H1 visibility of system status).
- A limitations panel next to every verdict, open by default, with sources (H10 help; the project's honesty contract).
- INCONCLUSIVE says why ("no face was detected and there is no audio track") instead of guessing (H9 recover from errors).
- "Not available / withheld" score states instead of a fake 0% (H2).
- Explanation source badge (Llama 3 or Template) with the reason a template was used.
- Timeline ticks on the progress bar at the suspicious windows.
- Upload limits (200 MB, 120 s) with readable error messages (H5, H9).

## Findings

| ID | Heuristic | Problem | Evidence | Severity | Proposed v2 change | Round 1 task that tests it |
|---|---|---|---|---|---|---|
| HE-01 | H2 match with the real world | Technical terms on the main screen with no plain-language gloss: checkpoint hash `fdd60748dc1c`, "SVM (RBF)", "3.96% EER", "wav2vec2-base (frozen)", "Spoof score", "Lip-sync / AV-delta", "peak score 1", "leans FAKE (manipulated)" in capitals, "faithfulness screen (direction)". | all `v1/*_desktop.png` (sidebar), `02_*_explanation.png`, `03_*_explanation.png` | 3 | Plain-language label first ("Face analysis", "Voice analysis", "Written explanation"), the technical name kept visible on a second line in smaller but readable text (user wants it visible) | T1, T4, O1 |
| HE-02 | H4 consistency | The verdict has four vocabularies: list chip FAKE / REAL, player stamp SYNTHETIC / AUTHENTIC, banner "Synthetic media detected" / "Authentic media", explanation "considered real / fake". | `02_real_real_desktop.png`, `06_unfamiliar_desktop.png` | 3 | One vocabulary everywhere (for example "Likely manipulated", "Likely authentic", "Partly manipulated: video", "No verdict") | T2, T3 |
| HE-03 | H2 | The banner percentage is unlabelled: "Authentic media ... 1%" reads as "1% authentic" or "1% confident"; on PARTIAL the banner shows "100%" and only the tile below says "Higher branch score". All three tiles are P(fake) but none says "chance of manipulation". | `02_real_real_desktop.png`, `03_partial_video_desktop.png` | 3 | Label every number with what it is ("chance of manipulation: 1%"), and say it in the banner in words | T4 |
| HE-04 | H8 aesthetic and minimalist design; H1 | On a 1440 x 900 screen the video fills the top 57% (about 510 of 900 px); the verdict starts at about 525 px and the written explanation is not visible in any result state without scrolling the results panel. | `02`, `03`, `04`, `06` desktop and `*_explanation.png` | 3 | Verdict-first layout (user's choice): verdict and explanation at the top, a smaller player beside them | T2, T3, T5 |
| HE-05 | H1 visibility; H5 error prevention | The unfamiliar-input caution is one 12 px amber line inside a red "Synthetic media detected" banner with a large "93%": the confident headline outweighs the doubt, on exactly the result that is wrong (LAVDF_RVRA_000 is genuine). | `06_unfamiliar_desktop.png` | 3 | Give the caution its own prominent block above or beside the verdict, in words ("This clip is unlike what the tool was trained on; this result may be wrong") | T7 (the key test) |
| HE-06 | H6 recognition; H10 help | The first screen gives no guidance: a smiley and "No video loaded"; the demo clips (how every task starts) are collapsed behind a 10 px "DEMO CLIPS" label at 2.02:1 contrast with a dot for a chevron; the list is titled "QUEUE" though it holds past results. | `01_empty_desktop.png` | 3 | An empty state that says what to do ("Upload a video or try an example"), demo clips visible by default, "Recent" instead of "Queue" | T1, T2 |
| HE-07 | H8; accessibility | Text too small and too faint to read comfortably (see the measurements above). | measurements | 3 | Minimum 13 to 14 px body text, labels at least 4.5:1 | all; O5 |
| HE-08 | H8 (the developer's "looks unfinished") | Placeholder and empty elements: a "Lip-sync / AV-delta: not measured by this pipeline" tile, empty VISUAL / AUDIO / REPORT headings and active Copy JSON / Export PDF buttons before any clip is chosen, a smiley icon. | `01_empty_desktop.png`, `02_*_explanation.png` | 2 | Hide sections until there is a result; remove the unmeasured placeholder tile (keep the fact in the limitations text) | T1, O5 |
| HE-09 | H4 | The same quantity in two formats: tiles say "100%", the explanation says "0.999"; windows appear as "0:00–0:05" and "0:00 to 0:05"; zero-length windows appear as "0:00–0:00". | `03_*_explanation.png`, `06_unfamiliar_desktop.png` | 2 | One number format on screen (the explanation text itself is generated and screened, so its format is left as it is and noted) | T4, T5 |
| HE-10 | H8; flexibility | No layout for small screens: at 390 px the sidebar fills the first screen and the verdict banner is squeezed into a column about 150 px wide. | `03_partial_video_mobile.png` and all `*_mobile.png` | 2 | A single-column layout below about 800 px, sidebar collapsed | not tested in round 1 (sessions are on a laptop); stated as a design fix |
| HE-11 | H3 user control and freedom; H5 | The x on a result removes it at once, with no confirmation and no undo; getting it back means re-running the analysis. | code: `removeFromQueue` in `static/app.js` | 2 | Ask before removing, or offer undo | none (observed in code) |
| HE-12 | H2 | The Evaluation tab is a research table (validation accuracy, "pp", "train minus validation gap", 13 rows) with no plain-language answer to "how accurate is this tool?". | `07_evaluation_desktop.png` | 2 | A short plain summary at the top (accuracy about 83% on unseen people, worse on other datasets), tables kept below | T8 |
| HE-13 | H1 | Copy JSON with no clip selected does nothing and says nothing; Export PDF with no clip selected prints an empty page. | code: `btn-copy-json`, `btn-export-pdf` handlers | 1 | Disable both until a result exists | T9 |
| HE-14 | H8 | Duplicated information: the time is shown twice (overlay and control bar) and the verdict twice (player corner stamp and banner, in different words, see HE-02). | `02_real_real_desktop.png` | 1 | Keep one of each | none |

Severity count: 3 (major) x 7, 2 (minor) x 5, 1 (cosmetic) x 2; no 4 (catastrophe): nothing observed stops a user from getting a verdict.

## Related observation (not an interface finding)

On FVRA_000 the explanation shown is the Template, because the Llama 3 text "failed the automatic faithfulness screen (direction)" (`03_partial_video_desktop_explanation.png`).
The video leans fake and is implicated in that clip, which matches the screen misfire found in the LLM comparison (ledger M1, point 3: the conjunctive
direction rule fires on "the video and audio branches disagree"). **Confirmed 19:54 24 Sep** from the live result: the violation reads "text says both
branches are manipulated but the input sa[ys the audio leans genuine]", and the rejected Llama text opens "The video has been partially manipulated. The
video branch suggests that the video is likely..." (the video is the implicated, fake-leaning branch, so the text is faithful and the rejection is a false positive). It matters for user testing because participants on task 3 will read template text, not Llama 3 text.

## What round 1 should tell us

Hypotheses from this review, each tied to a survey item, so the sessions test them rather than assume them:
1. Participants will misread the banner percentage (HE-03): T4 `score_reading`, Q3.
2. Participants will miss or discount the unfamiliar-input caution (HE-05): T7 `saw_warning`, `lowered_trust`, Q5.
3. Participants will not find the demo clips or will hesitate at the first screen (HE-06): T1 outcome and ease, T2 outcome.
4. The technical terms will be named as confusing (HE-01): O1, O5, F_models.
5. The mixed verdict words (HE-02) will not by themselves cause wrong answers (T2, T3 should succeed); if they do, HE-02 is more severe than rated.

If round 1 contradicts a hypothesis, the finding's severity is revised in this file (dated), not silently dropped.

## References

Nielsen, J. (1994) 'Enhancing the explanatory power of usability heuristics', *Proceedings of the SIGCHI Conference on Human Factors in Computing
Systems (CHI '94)*. Boston, MA, 24 to 28 April. New York: ACM, pp. 152 to 158.

Nielsen, J. (1994) 'Heuristic evaluation', in Nielsen, J. and Mack, R.L. (eds) *Usability Inspection Methods*. New York: John Wiley and Sons, pp. 25 to 62.
(Source of the 0 to 4 severity scale and the three-to-five evaluator recommendation.)

W3C (2018) *Web Content Accessibility Guidelines (WCAG) 2.1*. World Wide Web Consortium Recommendation, 5 June. Success criterion 1.4.3, Contrast (Minimum).

To verify before the report: page ranges and the chapter details of the second Nielsen item.
