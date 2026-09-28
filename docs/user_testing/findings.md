# Interface v1 to v2: what changed, and why (design iteration record)

Written 2026-09-24 21:10 +08. v1 is frozen in `ui_v1_snapshot/` (runs with `./run_v1_interface.sh` on port 8001); v2 ("Clipcheck") is `static/`.
Screenshots of the same states for both versions: `screenshots/v1/` and `screenshots/v2/` (captured with a headless-browser screenshot script, not part of the submission).

## Inputs to the redesign

1. **Round 1 user testing** on v1, 24 Sep 2026: 4 short sessions (P1 to P4). The data is **provisional**: a survey-form defect carried answers over
   between participants (`results/round1_data_quality.md`). Only findings that do not depend on the at-risk answers are used here:
   - all four named information overload in their own words (O1): "the information panel is kind of too complicated" (P1), "why the evaluation
     panel is needed" (P2), "too many information in the panels for a first time user" (P3), "the terminology and the results" (P4);
   - three of four named the Evaluation panel or the results panel as the first thing to change (O2);
   - P1 and P4 saw the unfamiliar-input warning only after a hint (T7);
   - P1 did not find the limits at all (T8, ease 1 of 7); P4 needed a hint (ease 3);
   - P1, P2 and P4 asked for a clearer, plain explanation of why a clip is flagged (T7 notes; P4: "could explain in layman terms").
2. **Heuristic evaluation of v1** (`heuristic_evaluation_v1.md`; one developer-evaluator, not user testing): 14 findings, HE-01 to HE-14.
3. **The developer's direction** (24 Sep): "too technical", "looks unfinished", dark but polished, verdict first, technical detail kept available,
   "explanation in layman terms and technical terminology defined with a legend in a Learn more section".
4. **The designer's mockups** (11 screens, "Clipcheck"), made from the design brief (`design_brief/`).

## Changes, each traced to its source

| # | Change in v2 | Source |
|---|---|---|
| C1 | Verdict first: the verdict card, the written explanation and the two part-checks sit at the top; the video moved to a smaller "When in the clip" card | HE-04; developer; mockups |
| C2 | One vocabulary for the verdict everywhere ("Likely genuine", "Likely manipulated", "Partly manipulated: the picture / the voice", "The checks disagree", "No verdict") instead of FAKE / SYNTHETIC / "Synthetic media detected" | HE-02 |
| C3 | Every percentage says what it is ("95% chance the picture is manipulated"), with "Leans genuine / Leans manipulated" in words and a 0 / 50%: unsure / 100% scale; >99% and <1% instead of 100% and 0% | HE-03; round 1 T3 (P1 could not say which part was suspect; ease 3 of 7) |
| C4 | The unfamiliar-input warning is its own amber card directly under the verdict ("This result may be wrong"), plus a flag on the affected part and a first item in "What to do next" | HE-05; round 1 T7 (P1 and P4 saw it only after a hint) |
| C5 | Technical detail moved off the main screen into **Learn more** (four tabs: Legend, Findings for this clip, Technical details, Accuracy and limits), still one click from every result; nothing was removed | round 1 O1/O2 (all four: too much information); HE-01; developer (keep technical detail available) |
| C6 | A **legend** of 20 terms, each with a plain definition and its technical name; dotted-underlined terms on the result open their legend entry | developer ("technical terminology defined with a legend"); HE-01 |
| C7 | "How accurate is this tool?" page: four plain figures first (83 in 100, 59 in 100, 29 in 100, 100 of 100, read from `results/numbers.json`), the research tables folded under "For experts" | round 1 (P2 "why the evaluation panel is needed"; P2 and P3 T8: "too many things in the evaluation tab"; P4's identical T8 note is an at-risk answer and is not used); HE-12; mockups |
| C8 | Limits reachable from every result (Learn more, Accuracy and limits tab) and from the Accuracy page | round 1 T8 (P1 could not find them) |
| C9 | Start page says what to do: upload box with the limits, "Try an example" visible by default with plain names (8 featured, all 37 behind "Show all"), recent checks | HE-06; mockups |
| C10 | Analysing screen shows the six real steps with notes ("16 face frames found", "No speech found"), driven by new server progress fields; each finished step ends in a green "Done", skipped steps say "Skipped" | mockups (v1 showed only "Analysing NN%"); developer (Done badges, 24 Sep) |
| C11 | Readable text: all text at least 13 px, contrast at least 4.5:1 (measured below) | HE-07 |
| C12 | Layout for phones (single column below 900 px; checked at 390 px, no sideways scrolling) | HE-10 |
| C13 | Removing a past check asks first ("Remove this check? Remove / Cancel") | HE-11 |
| C14 | Save as PDF and Copy data only appear on a result; the print layout includes every Learn more panel | HE-13 |
| C15 | Duplicates removed (one time display, one verdict statement); zero-length moments read "at 0:00" | HE-14; HE-09 |
| C17 | Colour by verdict: green likely genuine, red likely manipulated, ORANGE partly manipulated / checks disagree, grey no verdict; the unfamiliar-input warning YELLOW with a thick left border, so it cannot be confused with an orange verdict; icons and words always present | developer (2026-09-25); HE-05 |
| C18 | Standard wording (shown when the AI text fails its check) rewritten in plain language: picture check / voice check, chances as percentages in words, no system labels, never 100% or 0% | developer ("explanation in layman terms"); round 1 T7 notes (P4: "could explain in layman terms") |
| C16 | "Testing mode" (`#testing`): examples show neutral codes (as in round 1) so a descriptive name cannot hint at the answer in round 2 | developer decision, 24 Sep |
| C19 | Example names in the mockup's form "scene, what was changed" (for example "Webcam streamer, voice replaced"; subtitle "Desk microphone · built test clip"). Scene words from a frame of each clip, never naming the person; change words from how the clip was made; LAV-DF clips now say what LAV-DF actually changes (lips re-synced, a few words re-voiced), not "face replaced". Testing mode unaffected (codes) | developer, 25 Sep 16:00, from the designer's mockup |
| C20 | Picture and Voice score bars: the whole fill is one solid colour set by the score, green at 0%, amber at 50% (unsure), red at 100%, leaving amber quickly (60% is orange-red); words above the bar unchanged, so colour is not the only signal. Live on port 8000 from about 16:22 (a gradient version, replaced at the developer's request) and in its final solid form from about 16:32 on 2026-09-25 (CSS/JS load fresh on each page), so round 2 sessions after 16:22 saw coloured bars | developer, 25 Sep 16:00 and 16:28 |

## Measured on v2 (headless Chrome, 2026-09-24 21:0x, same method as the v1 measurements)

| Measure | v1 | v2 |
|---|---|---|
| Text styles below WCAG 4.5:1 contrast | 8 of 13 measured styles | 0 of 535 visible text elements (check page 32, result page 46, accuracy page 457) |
| Visible text smaller than 12 px | 58 of 89 elements (65%) | none; smallest 13 px |
| Layout at 390 px | sidebar fills the screen, verdict squeezed to about 150 px | single column, no horizontal scroll |
| Accuracy page height (1440 px wide) | not applicable (research tables in a tab) | 4,275 px with tables folded (10,881 px unfolded) |
| Console errors across 26 captured screens | not measured | 0 |

Functional checks passed (scripted in headless Chrome): an example runs through the real analysis to its result; a legend term opens Learn more on the
right entry; a suspicious moment seeks the video; Copy data copies; removing a check asks first and Cancel keeps it; testing mode switches on and off.

## Not changed, and why

- **The AI model's explanation text.** The standard wording was made plain on 2026-09-25 (C18), but the Llama 3 prompt is unchanged, so AI-written text
  still says things like "the video branch ... with a score of 0.853". Changing the prompt would need its own check (as in ledger M1), and the two
  human raters are scoring the 22 Sep text. Left to the developer's decision.
- **Verdict logic, scores, T and the weights**: untouched (`scripts/fusion.py`).
- **The survey's answer options** keep their v1 labels so round 1 and round 2 answers stay comparable (see `protocol.md`, round 2 notes).

## Round 2 (run 2026-09-25, scored 20:14)

> **Correction 2026-09-27 23:43 (facilitator's statement): rounds 1 and 2 were the SAME four people (P1 = P5, P2 = P6, P3 = P7, P4 = P8).** The
> sentence below saying "different people from round 1" was written from the sheets' background entries and is superseded; see
> `responses/participant_identity_correction_2026-09-27.md` for the statement, the recorded discrepancies and the consequences.

Four short sessions on v2 in testing mode (P5 to P8; CSVs saved 15:45, 17:48, 19:56, 20:12), same tasks (T2, T3, T7, T8), SUS and O1/O2 as round 1,
different people from round 1, none with a machine-learning background (financial advisor, unemployed, business student, accounting student).
Raw files unchanged in `responses/raw_as_downloaded/` (sha256 added to `SHA256SUMS`). Read in full before scoring: no carry-over (every SUS answer set
differs, every participant's free text differs); the facilitator's own debrief note is identical for P6 to P8 ("it was a good reaction"), which is the
facilitator's text, not participant data. Interface during the round: P5 saw v2 before C20 (score bars not yet coloured); P6 to P8 saw the coloured
bars; C19 names were hidden by testing mode throughout.

| Measure | Round 1 (v1, P1 to P4, PROVISIONAL) | Round 2 (v2, P5 to P8) |
|---|---|---|
| SUS per participant | 60.0, 60.0, 60.0, 47.5 (P3's at risk of carry-over) | 87.5, 87.5, 90.0, 90.0 |
| SUS median | 60.0 (60.0 without P3) | 88.75 |
| T2 found the verdict: unaided / with a hint | 1 / 3 | 4 / 0 |
| T3 named the implicated part (the video, correct) | 3 of 4 (1 could not say) | 4 of 4, all unaided; ease median 7 |
| T3 "Would you publish this clip?" (hoped for: no or unsure) | yes 1, unsure 3 | **yes 4** |
| T7 saw the warning: unprompted / after a hint | 2 / 2 | 2 / 2 |
| T7 the warning lowered their trust (hoped for: yes) | yes 3, partly 1 (P2 to P4 at risk) | **no 4** |
| T8 found the limits: unaided / hint / not done; ease median | 2 / 1 / 1; 1 | 1 / 3 / 0; 6 |
| O1/O2 in their own words | 4 of 4: too much information | 2 of 4 (P7, P8): the Learn more tab is too long; 2 of 4 positive |

Reading, at the strength four people support:
1. **What improved.** Finding the verdict, naming the implicated part (the project's contribution, in use) and finding the limits all became easier,
   and perceived usability rose from about 60 to about 89. The information-overload complaint moved from the main screen to the optional Learn more tab.
2. **What did not improve, and got worse.** The warning was seen as often as before, but it no longer lowered anyone's trust in a verdict that is wrong
   (the clip is genuine). Participants' T7 notes call the tool "pretty trustable" and "quite trustable". A calmer, more polished interface may make every
   verdict look more authoritative, including the ones the warning is meant to undercut. This is the most important round 2 finding and it is negative.
3. **Ambiguous.** All four said they would publish FVRA_000, a clip the tool flags as partly manipulated. Their T3 notes praise the tool's accuracy
   ("it detected perfectly"), so they may have answered about the tool rather than the clip; the session notes cannot tell which. Either reading is a
   warning: the question was unclear, or "only part of this clip may be fake" does not discourage publishing.
4. **Next change if there were a round 3:** tie the warning to the verdict itself (for example "Likely manipulated, but unreliable here"), and reword
   the partly-manipulated sentence so it says the clip should not be published as genuine; then re-test T3 and T7 with a clearer publish question.

Limits: n = 4 per round; round 1 provisional until its at-risk answers are confirmed; different people in each round; none are professional
verifiers (the intended users); the developer facilitated, so participants may have been polite; the interface changed once during round 2.

# Interface v2 to v3: what changed, and why (2026-09-26 21:31)

v2 (the version round 2 tested) is frozen byte-for-byte in `ui_v2_snapshot/` (SHA256SUMS, checked by `test_interface_v2_is_frozen_and_runnable`) and
runs with `./run_v2_interface.sh` on port 8002; v3 is `static/`. Screenshots of the same states: `screenshots/v2/` and `screenshots/v3/`.

**v3 has not been user-tested.** Every round 2 figure above (SUS median 88.75, T2 to T8) describes v2. Whether C25 and C26 fix the two round 2
problems is not known; a round 3 would re-test T3 and T7, with a clearer publish question.

## Inputs

1. **A design review of v2 against a checklist of defaults that make generated interfaces look templated**,
   Completed by the developer on 2026-09-26, not by a designer. What it found in v2: a near-black background (#0b0d10) with a serif
   display face; every section inside the same rounded card (one 14 px radius and border for everything, so the verdict and "What to do next" looked
   equally important); capitals-only labels ("DEEPFAKE CHECKER", "VERDICT", "ANALYSING"); dot-joined text ("TV interview · built test clip · 0:03");
   an arrow and the same film icon on every example, which carried no information; a monospace face for times and data labels; and the two scores in
   separate cards on separate scales, so the disagreement the project is about appeared only in a sentence.
2. **Round 2's own findings** (above): the warning no longer lowered trust in a wrong verdict (T7, 0 of 4), and all four participants would
   publish a clip the tool calls partly manipulated (T3). Item 4 of the round 2 reading named the next change; v3 makes it.
3. **The developer's decisions, all kept:** dark, verdict first, green / red / orange / grey verdict colours with words and icons, the yellow warning with
   a thick left edge, technical detail in Learn more with the 20-term legend, testing mode, the C19 example names, the C20 score-bar colours, and all
   plain-language wording except C25 and C26.

## Changes, each traced to its source

| # | Change in v3 | Source |
|---|---|---|
| C21 | Colour and surfaces: graphite page (#1d2023) instead of near-black; a raised surface (#262a2e) only for the verdict panel, the video player and the upload area; every other section divided by rules instead of boxed; radii by role (10 px panels, 7 px controls, round only for the play button) | skill review (card kit; tinted near-black) |
| C22 | Type: one family (the system sans, so the tool still works offline), a fixed scale (13, 14, 16, 18, 21, 24, 30, 36, 48 px) and tabular figures for every percentage and time; the serif and the monospace face removed; no capitals-only labels, no dot-joined text, no arrows; example subtitles shown as plain phrases ("TV interview, built test clip"); the page title no longer uses a dot | skill review |
| C23 | **The two-track reading** (result page): the picture and voice scores drawn as two lanes on one shared 0 to 100% scale, like the picture and sound tracks of an editing timeline, with the C20 bar colours; under them a bracket showing the gap between the two scores and a dashed line of length T drawn from the same end, so "partly manipulated" (bracket at least as long as the line) or "combined" (shorter) can be seen; when the checks are combined, the combined score is a third lane. It replaces the two Picture and Voice cards, keeping their words ("leans manipulated", "Unfamiliar to the tool", "Not checked: ..."). Every number is a field of the result | skill review ("spend boldness in one place", design from the subject); the project's contribution (disagreement-aware fusion) made visible |
| C24 | One piece of motion: on the first view of a result the bars move from 50% (unsure) to their scores and the bracket appears; none with the reduced-motion setting, and screenshots are taken with it set | skill review |
| C25 | The unfamiliar-clip warning is part of the verdict: the headline reads "Likely manipulated," with "but it may be wrong for this clip" in yellow directly beneath, and the yellow warning block sits inside the verdict panel under the headline instead of in a separate card below it; Recent checks and History show the same verdict with ", may be wrong" | round 2 T7 (0 of 4 said the warning lowered trust); round 2 reading, item 4 |
| C26 | "Partly manipulated" results add: "Even one manipulated part means the clip should not be shared as genuine." ("The checks disagree" results, where neither or both parts lean manipulated, are unchanged) | round 2 T3 (4 of 4 would publish); round 2 reading, item 4 |
| C27 | Start and analysing pages: the upload area sits directly under a plain heading; each example shows a small two-line mark (picture above voice, red where that part was changed, dotted where it is absent) drawn from how the clip was made, with a one-line key, and never in testing mode, where it would give the answer; the analysing page groups its six real steps into Picture, Voice and Both lanes (same steps, order, notes and Done badges); the brand mark is two score bars far apart | skill review (information-carrying structure, design from the subject) |

## Measured on v3 (headless Chrome, 2026-09-26, same method as the v1 and v2 measurements)

| Measure | v2 | v3 |
|---|---|---|
| Text elements below WCAG 4.5:1 contrast | 0 of 535 | 0 of 1,025 across ten screens (start 46; results: partly manipulated 44, unfamiliar 58, no verdict 30; Learn more tabs 112, 76, 97, 62; History 35; Accuracy 465); lowest ratio 6.33:1 |
| Smallest visible text | 13 px | 13 px |
| Sideways scrolling at 390 px and 1440 px | none | none (six routes at each width) |
| Console errors across the captured screens | 0 of 26 | 0 of 25 (`screenshots/v3/index.json`) |
| App tests (`tests/test_server.py`, `tests/test_pipeline.py`) | 51 pass | 52 pass (adds the v2 freeze check) |

Functional checks passed (scripted, headless Chrome): a live analysis runs through the three-lane analysing page to its result on desktop and phone
widths; a legend term in the reading opens Learn more on the right entry; the reading shows every result type (agreeing, partly manipulated for the
picture and for the voice, picture only, no verdict, zero-point gap); the frozen v2 launcher serves v2 unchanged on port 8002.

## Not changed, and why

- **Verdict logic, scores, T, the weights and the server**: untouched. v3 is `static/` only, plus a test and a screenshot-script option.
- **The standard wording** (`scripts/explain.py`) still ends "only part of this clip may be fake", without C26's sentence, and the Llama 3 prompt is
  unchanged: both were rated by the two human raters (E2), and changing them would need a new check.
- **The designer's mockups**: v3 departs from their look (card layout, serif headings) but keeps their structure, screens and wording.

# Interface v3 to v4: what changed, and why (2026-09-26 23:55)

**What happened to v3.** On 26 Sep, after the v3 entry above (21:31), `static/style.css` and `static/app.js` were found byte-identical to the v2
snapshot (both rewritten at 21:33; `static/index.html` still carried v3's title and favicon). v3's code, its v2 freeze test and a `changes` field it
relied on in `/api/demo_clips` were not on disk or in git; only `screenshots/v3/` (25 screens) survive. The cause was not established (a parallel
session was editing the same files that evening). v3 therefore stays documented (C21 to C27 and its screenshots) but cannot be run.

**v4 has not been user-tested.** Every round 2 figure (SUS median 88.75, T2 to T8) describes v2, which is still frozen in `ui_v2_snapshot/` and runs
with `./run_v2_interface.sh` on port 8002. v4 is `static/`.

## Inputs

1. **The developer's review of v2 and v3:** both still looked generated, and v3 kept v2's screens, order and boxes, so it read as a repaint rather than
   a redesign. The developer asked for a new design from scratch, with a different typographic feel.
2. **Choices made by the developer from shown options** (live previews built on 26 Sep): a glass look inspired by macOS but not a
   copy of it; smoked glass with film grain (chosen over frosted glass, scanlines and a chromatic edge); the spring pop-in kept; level meters for the
   scores (over a gap band, a two-needle dial and sliders); a demo videos section that names each clip and says whether its face and voice are real or
   fake (the developer rejected four Dock-like variants as not informative enough); a hover in which the tracks move, green for a real part and red for a
   fake one, with the lights blinking at different rhythms; and a mark showing people finding AI-made content (the split face, in green and red,
   chosen over eleven other marks and five other colourways).
3. **Kept from earlier rounds:** round 2's tested wording, C25 and C26, the C20 score colours, the green / red / orange / grey verdict colours with words
   and icons, the unfamiliar-clip warning inside the verdict, testing mode, the C19 demo names, and the honesty contract at the top of `static/app.js`.

## Changes, each traced to its source

| # | Change in v4 | Source |
|---|---|---|
| C28 | Look: one dark theme of smoked glass panels (translucent, blurred, fine grain) over a grainy backdrop lit by one light leak whose colour follows the verdict (amber on the start page; green, red, orange or grey on a result). System fonts only, so the tool still works offline | developer's choice from previews |
| C29 | Scores: segmented level meters (20 segments on the C20 green to amber to red scale) with a white marker at the exact value, on one shared 0 to 100% scale; the gap bracket and the dashed T line underneath (C23's idea kept); the combined score is a third meter when the checks are combined | developer's choice; the project's contribution kept visible |
| C30 | Demo videos: a labelled "Demo videos" row of eight channel strips (all 37 behind a button, grouped as before), each with the clip's name and setting, a Face light and a Voice light saying Real, Fake or None in words and colour (its known answer), a picture track and a voice track, its length, and "Checked" once opened. Hover lifts the strips toward the pointer; the tracks move, green for a real part and red for a fake one (dotted where the clip has none); the lights blink at different rhythms per strip. Testing mode shows only the neutral code, no lights, and grey tracks | developer's request (name and face / voice answer visible); testing mode as in C27 |
| C31 | Result page: the video player's seek bar is the picture track (one bar per checked face frame, suspicious moments marked) and the voice track (waveform), with a playhead that follows playback; a demo's header states its known answer ("face fake, voice real"); Learn more is replaced by a Details sheet (Findings, Technical, Accuracy and limits, Glossary) and by popover definitions on dotted terms; Save as PDF prints on a light page with every Details panel; "What to do next" is renamed "Before you share it" | redesign from scratch; C26's sharing theme |
| C32 | Motion: windows and sheets pop in with a spring; meters light segment by segment on a result's first view; a notification slides in when a check finishes; none of it with the reduced-motion setting | developer's choice (spring kept) |
| C33 | Mark: a split face, half a hand-drawn human face in green (real) and half built from pixels in red (generated), for people finding what AI made; also the favicon (`static/clipcheck-mark.svg`) | developer's request and choice |
| C34 | Server: `/api/demo_clips` returns `changes` (`picture` and `voice`, each `genuine`, `changed`, `absent` or `unstated`), taken from each clip's construction category, never from a model; test `test_demo_clips_carry_their_known_answer_from_how_each_clip_was_made` | C30 needs the known answers |

## Checks on v4 (2026-09-26, a built-in browser against the live server)

- App tests (`tests/test_server.py`): 49 of 49 pass, including the 6 heavy tests that run the models and Llama 3.
- A real analysis of "Business newsreader, face replaced" ran through the three-lane analysing page (real progress from `/api/progress`) to its
  result: "Partly manipulated: the picture", picture >99%, voice <1%, 100 points apart, standard wording (the Llama 3 text failed the faithfulness screen).
- The playhead follows playback on both tracks; Details, History and Accuracy render; testing mode hides every answer; no sideways scrolling at
  375 px; 0 console errors.
- **Not yet re-measured for v4:** the full contrast audit and the screenshot set, as done for v1 to v3.

**C35 (27 Sep): a landing page** at "/" opens into the app (split-face intro, a pinned story playing a real check, pixel reveals; sections chosen by
the developer). Every figure on it comes from `/api/evaluation`, `/api/limitations` or two labelled saved results; the app screens are unchanged. Not user-tested.

**C36 (27 Sep): one backdrop for every page.** The landing page's backdrop (no grain; a grey pixel grid with random green and red pixels switching
on and off; a pointer light; two faint green and red lights) now runs in the app too, replacing C28's verdict-coloured light. Not user-tested.

**C37 (27 Sep): the result page is laid out in rows.** The developer found a large empty area beside the player on the result page. The verdict
and meters now share the top row, the player runs at full width below them, and the explanation and next steps sit side by side under the
player. Same content in a different order. Not user-tested.

**C38 (27 Sep 19:00): the developer's pre-freeze changes, before round 3.** (1) Every white primary button (Choose a file, Try it for yourself,
Open Clipcheck, Run this check yourself, Check a video) now looks like the Home button: green-to-red outline, soft glow, gradient label.
(2) The demo shelf is eight clips in one row, with "Show all 37" removed. At the developer's request they are clips the tool gets right: per
category, the first two by id that the shipped model gets fully right in `results/fallback_eval_shipped` and that raise no unfamiliar-input
warning (FVFA_003 skipped: voice distance 43.4 against 43.1). All eight were re-checked in the live app on 27 Sep and came out right. The
section note says they were chosen for being right and points to the Accuracy page. Testing mode (`#testing`) still shows the eight clips
rounds 1 and 2 used, so round 3 is comparable (`TESTING_DEMOS` in server.py; test `test_featured_shelf_follows_its_rule`). Clearer names
for three clips that were all "Newsreader" (News presenter, Newsreader, News anchor), and FVFA_004 named TV presenter (scene words from a
frame, never the person or channel). A same-height version of the name boxes was tried and withdrawn at the developer's request (19:13): the
cards, boxes, note and hover effects are exactly as before; one line under the row (where "Show all" was) says the eight are clips the tool
gets right and links to the Accuracy page.
(3) Footer: "(CM3070 final project)", no longer "prototype". (4) The result page's player is 75% of the column width, centred (full
width under 900 px). (5) Landing chip "About 7 seconds a clip" replaced by "Clips stay on your computer" (true: every model runs locally,
requirement R7). Also fixed: the Accuracy page scrolled sideways by 21 px on a phone (a long file path in a list). Checked in headless
Chrome at 1440 and 390 px: no sideways scroll on any page, 0 console errors. Tests: app 53 passed, base 154 passed, 1 skipped. Not user-tested.

**Screenshots of v4 (2026-09-27 06:00):** `screenshots/v4/` (17 screens, reduced motion, 0 console errors), captured by `Final Report/figures/src/capture_v4.py` for the report.
