# Round 1 survey data: quality check (2026-09-24)

Four round 1 sessions were run by the developer on 24 Sep 2026 on the v1 interface, all with the short form (tasks T2, T3, T7, T8, SUS, O1, O2).
The four CSVs were downloaded at 19:15 (P1), 19:28 (P2), 19:31 (P3) and 19:47 (P4). They are kept exactly as downloaded in
`docs/user_testing/responses/raw_as_downloaded/` (sha256 in `SHA256SUMS`); nothing in them has been edited.

## What was found before scoring

Answers identical between consecutive participants (items answered by both; free-text items listed):

| Pair | Identical answers | Identical free text |
|---|---|---|
| P1 and P2 | 17 | facilitator debrief, facilitator "differed" |
| **P2 and P3** | **29** | facilitator debrief and "differed", **task notes for T2, T3 and T7 word for word**; all 10 SUS answers identical |
| P3 and P4 | 16 | facilitator debrief, "differed" and top problem, **task note for T8 word for word** |
| P1 and P4 | 13 | facilitator debrief, "differed" |

Identical rating-scale answers between two people are plausible; identical sentences in free text are not, and the SUS pattern of P2 and P3 matches on all 10 items.

## Cause: a defect in the survey form (the developer's, not the facilitator's)

The first version of `survey_form*.html` kept ONE set of answers in the browser and did not clear it when the facilitator chose a new participant
number. Any answer not re-entered for the next participant was carried over from the previous one, and the protocol did not tell the facilitator to
press "Clear this form" between sessions. The pattern above (carry-over between consecutive sessions only, strongest where sessions were 3 minutes
apart) matches this. Fixed 2026-09-24 about 20:30: each participant and round now has its own sheet; choosing another participant opens a blank sheet
(checked in the browser: a new participant opens blank, and returning to an earlier participant shows only that participant's answers).

## Consequence for the report

- P1's answers are unaffected (first session).
- For P2, P3 and P4, any answer identical to the previous participant's may have been carried over rather than given. Most at risk: **P3's SUS answers
  and its T2, T3 and T7 notes**, and **P4's T8 note**; the facilitator's debrief and "differed" notes are identical in all four.
- Also to confirm: P1 (preschool teacher) and P2 (engineer) are recorded as having a machine-learning background, which the protocol excludes. This may be a
  carried-over or mistaken click.

Status: **provisional**. The provisional summary (`summary.md`) is generated from the files as downloaded. No figure from round 1 goes into the report
until the facilitator has confirmed, from memory or notes, which of the at-risk answers were actually given. Confirmed corrections will be recorded in a
separate corrections file with the facilitator's statement; the raw files stay unchanged. If an answer cannot be confirmed, it is excluded and the
report says how many were excluded.

## Findings that do not depend on the at-risk answers

- In their own words (O1 and O2; each participant's answers differ, so none were carried over), all four named information overload: P1 "the
  information panel is kind of too complicated", P2 "why the evaluation panel is needed", P3 "too many information in the panels for a first time user",
  P4 "the terminology and the results". Three of four named the Evaluation panel or the results panel as the first thing to change.
- P1 and P4 did not find the limits easily in T8 (P1 not done, ease 1; P4 with a hint, ease 3).
- P1 and P4 saw the unfamiliar-input warning only after a hint (T7), which supports heuristic finding HE-05.
- P1, P2 and P4 each asked in T7 for the tool to explain better why a clip is flagged ("could explain in layman terms", P4).

## Decision (2026-09-26 03:28)

The facilitator (the developer) could not confirm the at-risk answers and chose the recommended course: **round 1 stays provisional**. In the report:
P3's SUS answers are excluded from the round 1 SUS figure (median of P1, P2, P4 = 60.0, the same as with P3); P3's T2, T3 and T7 notes and P4's T8 note are
not quoted; P1's and P2's recorded ML background is reported as unconfirmed. Round 1 findings that do not depend on the at-risk answers (listed above) are used.
The raw files are unchanged.
