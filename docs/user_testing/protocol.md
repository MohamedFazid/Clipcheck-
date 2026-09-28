# User testing protocol: Multimodal Deepfake Detector (FastAPI interface)

**Rewritten 2026-09-24** for the current FastAPI + JavaScript interface. The earlier version was written for the retired Streamlit UI
(four-stage status strip, "FAKE clip: 469_481.mp4", tasks about unfinished parts). If the interface is restyled, re-read the task wording
below against the final screen before the first session. The tasks name elements by what they say, not by colour or position, so most of the
wording should still fit after a restyle.

**Purpose.** At the top band, the module brief asks for user testing and for iterating the design on the results. Chapter 3.6 of the
Draft Report specifies a rubric for the explanation layer's factual grounding. That rubric is the separate two-rater evaluation (ledger E2), and nothing in it
tests whether the **interface** can be used and correctly understood by the people the project is for. This protocol does that.

**What this is not.** It is not a controlled study and makes no statistical claim. It is a small formative usability round (3 to 5 participants), reported as such.
Its output is a findings table and at least one documented design change made in response to what participants did or said (ledger U1).

**Target users (Draft Report Chapter 3.2).** Journalists checking a clip before publication, content moderators reviewing a flagged upload,
fact-checkers investigating a viral video: professionals without machine-learning knowledge. Recruit people who are **not** ML or AI students.
The point is to find out whether a non-expert can act correctly on the output.

**Design: two rounds, before and after (decided 2026-09-24).**
1. **Round 1 on the current interface (v1)**, frozen before any session: files copied byte for byte to `docs/user_testing/ui_v1_snapshot/`
   (with `SHA256SUMS`) and screenshots of every task state in `docs/user_testing/screenshots/v1/` (captured with a headless-browser screenshot script).
   Do not change `static/` until round 1 is finished.
2. **Redesign (v2)** from the round 1 findings plus the developer's stated direction (dark but polished, verdict first, technical detail kept visible
   but in plain language). Every change is traced to a finding or to that direction in `findings.md`.
3. **Round 2 on v2**, same tasks and the same survey; ideally new participants (a returning participant already knows the tasks; if one
   returns, the scorer lists them and the report says so). Capture `screenshots/v2/` with the same script.
4. Compare rounds (`scripts/score_user_testing.py` prints medians side by side). With 3 to 5 people per round this is descriptive only.

**Round 3 checklist (added 2026-09-27 19:40; final interface v4, frozen 19:39 in `ui_v4_final_snapshot/`, test `test_final_interface_is_frozen`).**
Purpose: test whether the two changes made after round 2 fixed its two problems (the warning did not lower trust in a wrong verdict, T7; "would you
publish" was ambiguous, T3). Same short form and tasks as rounds 1 and 2, so the rounds compare. Cut-off: Monday 28 Sep 12:00; after that, stop.
1. **Consent first.** Give the participant the information sheet (PR/002) and the consent form (PR/001) from `materials/consent/`. They read the
   sheet, tick "I am signing before my session", sign; you sign the researcher part. Do not write their participant number on the form. Keep the
   signed form outside the project folder (password-protected), never in the repository.
2. The app runs (`~/mdd/run_server.sh`, port 8000). Before the first session analyse any one demo video once and remove it from History (first run
   loads the models). Open `http://localhost:8000/#testing`: the footer shows "Testing mode: neutral demo names" and the demo row shows the SAME
   eight codes as rounds 1 and 2 (RVRA_000, RVFA_000, FVRA_000, FVFA_002, 183_253, 183, LAVDF_RVRA_000, noface_silent). History empty per session.
3. Open `survey_form_short.html`. Choose a NEW participant, **P9 to P12**, **Round 3**, and consent "given: signed consent form (PR/001) before the
   session". New people only (not P1 to P8), none with a machine-learning background if possible; record honestly if one has.
4. Read the framing (below) word for word, then T2, T3, T7, T8, the usability questions, O1, O2, debrief. About 10 to 12 minutes.
   **T3 now has one more question, asked last:** "Would you share this clip as genuine?" (record it under share_as_genuine). Ask "Would you publish
   this clip?" first, exactly as before.
5. Download CSV and put `survey_P<n>_round3.csv` into `responses/`. I file the raw copy, check for carry-over and score.

**Where things are in v4 (the task wording names v1 elements; say the v4 name if the participant asks):** "Demo clips" = the **Demo videos** row
on the Check a video page. The verdict banner = the **verdict at the top of the result** (a warning now appears inside it: "but it may be wrong for
this clip"). "Report" / written summary = the **explanation** beside "Before you share it". The limits panel under the result = the **Details**
button, tab **Accuracy and limits** (T8 survey option "the limits panel under the result"). The Evaluation tab = the **Accuracy** tab (option "the
Evaluation tab"). Export PDF / Copy JSON = **Save as PDF / Copy data**. The survey keeps its v1 option labels so the three rounds stay comparable.

**Round 2 checklist (added 2026-09-25; follow it for every session so round 2 is comparable with round 1).**
1. Before the first session: make sure the app is running (`~/mdd/run_server.sh`), then analyse any one example once and remove it from
   History. The first analysis after a start loads the models and takes longer, so it should not be a participant's.
2. Open the app at `http://localhost:8000/#testing`. The small footer line "Testing mode: neutral example names" must be visible. Examples then
   show codes (RVRA_000, FVRA_000, LAVDF_RVRA_000), as in round 1.
3. History must be empty at the start of each session (History tab, bin icon, Remove).
4. Open `survey_form_short.html` (the same short form as round 1: tasks T2, T3, T7, T8, the usability questions and O1, O2). Choose a NEW
   participant number, **P5 to P9** (P1 to P4 were round 1), and **Round 2**. Each participant has their own sheet, so nothing carries over.
5. Read the framing, run T2, T3, T7, T8 in that order (task wording in the Tasks section; v2 names in the notes above), then the usability
   questions, O1, O2 and the debrief. About 10 to 12 minutes.
6. Press Download CSV and put `survey_P<n>_round2.csv` into `docs/user_testing/responses/`.
Participants should not have ML backgrounds (the protocol's target users); record honestly if one does.

**Never simulate a participant.** Every response sheet must come from a real session with a real person. If fewer than 3 sessions
happen, report the real number.

**Round 2 notes (interface v2, "Clipcheck", built 2026-09-24).** Open the app as `http://localhost:8000/#testing`: example clips then show the same
neutral codes as in round 1 (RVRA_000, FVRA_000, 183_253, LAVDF_RVRA_000), so a descriptive name cannot give the answer away (turn it off with
`#testing-off`). The tasks are unchanged; where they name v1 elements, use the v2 equivalent: "Demo clips" is **Try an example** on the start page;
the verdict banner is the **Verdict** card; "Report" is **What the tool found**; the limits panel is **Learn more, Accuracy and limits** (task 8's
survey option "the limits panel under the result"); the Evaluation tab is the **Accuracy** tab ("the Evaluation tab"); Export PDF / Copy JSON are
**Save as PDF / Copy data**. The survey keeps its v1 option labels so the two rounds stay comparable. Change record: `findings.md`.

---

## Before each session (facilitator checklist, about 5 minutes)

1. Check the server is running: start it with `~/mdd/run_server.sh` and confirm `http://localhost:8000` loads. Check Ollama is running:
   `curl -s localhost:11434/api/tags` should list `llama3:8b`. Out-of-domain mode must be the default `warn`.
2. Open the app in a fresh browser window. Clear the sidebar's recent list (hover a row, "Remove from recents") so the participant starts from an
   empty screen and does not see the previous participant's results.
3. Have the no-face clip (`demo_videos/noface_silent.mp4`) ready to upload (task 6). It is a 6 s test pattern with no face and no sound, built with
   the recipe in `docs/TESTING_GUIDE.md` section 8. It was checked on the live app on 2026-09-24: verdict INCONCLUSIVE, template explanation.
4. Open `docs/user_testing/survey_form.html` (or `survey_form_short.html` for a short session) in a separate browser window (or print it; `response_sheet.md` is the paper fallback). Pick the
   participant number and the round FIRST: each participant and round has its own sheet, and choosing a new number opens a blank one (the first
   version of the form did not do this, and answers carried over between round 1 sessions; see `results/round1_data_quality.md`). Keep the answer key (end of this file) out of their sight; the form itself does not contain it (tested).
   After the session press **Download CSV** and copy `survey_P<n>_round<r>.csv` into `docs/user_testing/responses/`.
5. Read the framing below aloud, word for word, so every session starts the same way.

> "This is a prototype tool that checks whether a video has been manipulated, what people call a deepfake. Imagine you are a journalist and
> someone has sent you these clips; you need to decide whether to trust them before publishing. I will ask you to use the tool and think out loud
> as you go. I am testing the tool, not you. If something is confusing, that is exactly what I need to hear. There are no wrong answers, and you
> can stop at any time. I will not record your name, your voice or your screen, only written notes."

**Do not** explain how the system works, what the scores mean, or what "partial manipulation" is before the tasks. What the participant works out
unaided is the result. If they are fully stuck for about a minute, give the smallest hint that unblocks them and write down that you did.

---

## Tasks (20 to 30 minutes in total; observe, note hesitations and quotes)

**Short session (10 to 12 minutes; added 2026-09-24).** When a participant has little time, run only tasks **2, 3, 7 and 8** (in that order),
then the System Usability Scale and open questions O1 and O2, using `survey_form_short.html`. Skip the rest. The framing, consent, debrief and answer
key are the same. Short and full sessions are pooled item by item by the scorer; the report states how many of each were run. A short session can
also be run over a video call: share your screen, the participant says what to click, and you fill in the form.

Every clip except the task 6 file is in the sidebar under **Demo clips**. The answer key has the ground truth and expected results; do not reveal
them until the debrief.

**Task 1: First impression (no clicking, about 30 s).**
"Look at this screen. Without clicking anything, what do you think this tool does, and where would you start?"
*Probing: are the upload area, the demo list and the Analyze / History / Evaluation tabs understandable to a newcomer?*

**Task 2: A clear case. Clip `RVRA_000.mp4`.**
"Analyse the clip called RVRA_000 and tell me what the tool concluded. How sure is it?"
*Probing: is the verdict banner easy to find and unambiguous; does the participant read the percentages sensibly?*

**Task 3: A split verdict. Clip `FVRA_000.mp4`.**
"Now analyse FVRA_000. What did the tool conclude this time? Which part of the clip does it think is the problem, the picture or the sound?
Would you publish this clip?"
*Probing: this task tests the project's central contribution. The banner says "Partial manipulation detected" and "the video scored higher and
is the more likely manipulated component". Does that make sense to a non-expert, and can they say which part is implicated? Note whether they
notice that the banner percentage is labelled "Higher branch score" rather than an overall score.*

**Task 4: Reading the numbers.** (Same result as task 3.)
"There are three percentages near the top. In your own words, what does each one mean? If one of them said 55%, what would that tell you?"
*Probing: is a probability understandable? Watch for a score being read as a certainty ("it IS fake") or as the percentage of the clip that is fake.*

**Task 5: The explanation and the timing. Clip `183_253.mp4`.**
"Analyse 183_253 and read the written summary under Report. Does it tell you anything the numbers did not? When in the clip did the tool find
something suspicious? Can you check that on the video player?"
*Probing:*
- *Does the plain-language summary add anything beyond the score?*
- *Can they use the stated time windows, the marks on the progress bar and the Visual section to find the moment?*
- *Do they notice the badge saying whether Llama 3 or a template wrote the text?*
- *Do they expect the tool to say WHAT looks wrong? It deliberately cannot; note their reaction.*

**Task 6: No verdict. Upload `noface_silent.mp4`** (hand them the file).
"Upload this file using the upload area and tell me what the tool says about it."
*Probing: can they upload without help? Do they read INCONCLUSIVE ("No verdict ... no face was detected and there is no audio track") as "the
tool cannot judge this", rather than as "authentic" or as an error?*

**Task 7: An unfamiliar clip. Clip `LAVDF_RVRA_000.mp4`.**
"Analyse LAVDF_RVRA_000. What did the tool conclude, and is there anything on the screen that changes how much you would trust it?"
*Probing: this task tests the out-of-domain warning. Do they see the amber "Unfamiliar input ... this verdict may be wrong" line, understand it,
and lower their trust? The clip is genuine and the verdict is wrong; reveal this only at the debrief. This is the highest-value task, because the
warning exists precisely so that a user does not act on a verdict the system has reason to doubt.*

**Task 8: When not to trust it.**
"Suppose your editor asks: how accurate is this tool, and when should we not rely on it? Find the answer in the tool."
*Probing: do they find the panel "How to read this result, and its limits" under the scores, the Evaluation tab, or both? Can they state one limit
in their own words? Examples: about 83% accuracy on people the model has not seen, worse on other kinds of video, genuine voices sometimes flagged.*

**Optional task 9 (only if time allows): keeping a record.**
"You want to keep a copy of the result for your notes. How would you do that?" (History tab, Export PDF, Copy JSON.)

---

## Post-task questions (all in the survey form)

After each task the participant rates its ease (1 = very difficult, 7 = very easy). After the tasks: the 10 standard System Usability Scale
statements (Brooke, 1996; scored 0 to 100), the six project statements below, a usefulness rating for each of 10 features (or "did not notice
it"), and the open questions. Project statements, rated 1 to 5 (1 = strongly disagree, 5 = strongly agree):

| # | Statement |
|---|---|
| Q1 | The final verdict was easy to find and understand. |
| Q2 | When the tool said only one part was manipulated, I could tell whether it meant the video or the audio. |
| Q3 | I understood what the percentage scores meant. |
| Q4 | The written explanation helped me understand the result. |
| Q5 | The tool made it clear when its result should not be trusted. |
| Q6 | If I were verifying a video for work, I would use this tool's output as one input to my decision. |

Open questions:

- **O1.** What was the single most confusing thing on the screen?
- **O2.** What would you change first?
- **O3.** Was there anything you expected the tool to tell you that it did not?
- **O4.** Did anything make you trust it less, or more?

Debrief (after the questions): tell them the ground truth for the clips they saw, including that the task 7 clip is genuine and the tool was wrong.
Note their reaction in one line.

---

## After all sessions: the iteration step (the part the brief rewards)

Collecting feedback is not enough on its own; the brief asks for design changes based on it.

0. Run `/opt/anaconda3/bin/python scripts/score_user_testing.py`: it reads every CSV in `responses/`, refuses incomplete files, and writes
   `docs/user_testing/results/summary.{json,md}` (SUS per participant and median, task outcomes and ease, checks, statements, features, open answers).
1. Tabulate Q1 to Q6 per participant, reporting the individual scores and the median (with 3 to 5 people a mean is not meaningful). Group the
   open answers and observed hesitations into themes, and count how many participants hit each one.
2. Pick the most frequently observed problem and at least one other actionable one.
3. Make the change in `static/`, or in `server.py` for wording that comes from the server. Keep everything on the honesty list:
   verdict tones, scenario sentences, caution and withheld notices, the explanation source badge, the limitations panel, and the "not available / withheld" states.
4. Record each change in `docs/user_testing/findings.md` as: observation (how many participants, a quote) -> change made -> before/after
   screenshot. Log it in `docs/DEV_LOG.md` and update ledger U1 in `docs/EXPERIMENTS.md` with the participant count and findings.
5. Re-run `tests/test_server.py` (app env) after any UI change. If the `describeVerdict` wording changes, re-check it on the 9-case list

6. If time allows, show the changed screen to one participant again (or a new one) and note whether the problem went away. If this re-check
   was not done, say so plainly in the report.

A small change clearly traceable to what participants did is worth more than a large redesign with no evidence behind it.

---

## Ethics and data handling

Participants are adults, not a vulnerable group, and the task involves no personal data.

- Say at the start that notes are anonymous and used only for a university project, and that they can stop at any time. Get a verbal yes
  before starting and tick it on the response sheet.
- No names on response sheets: use P1, P2, P3 and so on. Record occupation or field only in general terms.
- No audio, video or screen recording.
- Participants do not upload videos of themselves or anyone else. Use only the bundled demo clips (FaceForensics++, ASVspoof and LAV-DF
  research data) and the synthetic test pattern. There is a second reason for this rule: the audio branch flags genuine speech from unfamiliar
  recordings as synthetic, so a participant could be told, falsely, that their own voice is fake.

---

## Facilitator answer key (do not show participants)

Expected results come from `docs/TESTING_GUIDE.md` (sections 3, 4, 10 and 11) and from the 2026-09-24 check of the test pattern. Llama text varies
between runs; scores should reproduce to within a few thousandths.

| Task | Clip | Ground truth | Expected on screen |
|---|---|---|---|
| 2 | RVRA_000 | real video, real audio | Authentic media; audio score about 1% |
| 3, 4 | FVRA_000 | fake video, real audio | Partial manipulation detected, video implicated (gap 0.999) |
| 5 | 183_253 | fake video, no audio track | Synthetic media, video about 95%. On 22 Sep the Llama text stated the real time windows ("0:00 to 0:03 and 0:04 to 0:06") |
| 6 | noface_silent (upload) | not a face video | INCONCLUSIVE, no scores, template explanation |
| 7 | LAVDF_RVRA_000 | real video, real audio (LAV-DF) | Synthetic media, which is WRONG (video 0.853, audio 1.000), with the amber unfamiliar-input caution (audio 70 > 43) |

If a result on the day differs from this table, note it on the sheet and do not correct the participant during the task.
