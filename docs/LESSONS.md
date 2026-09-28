# Lessons learned

Append-only. Each entry: what went wrong or was learned, the evidence, and the rule
to follow next time. This is the raw material for the report's methodology and
limitations chapters. Dated 2026-09-19 unless stated.

**L1. Split by identity group, never by frame.**
Frame-level `random_split` put 100% of test-set videos and 100% of val-set videos
in train too (about 19 near-duplicate crops per video). Rule: the split unit is the
identity group, and a test asserts zero overlap (`tests/test_data_split.py`).

**L2. Video-level splitting is not enough for FF++.**
Deepfakes are reciprocal pairs (036_035 and 035_036). Splitting by video folder still
leaks identity 036's face across sets. Rule: union-find over the id graph and assign
whole components.

**L3. Report the unit the system outputs.**
The app emits one score per clip, but metrics were per crop (pseudo-replication).
Rule: report video-level as primary, frame-level as secondary, and never compare
across levels (old 97.67% is frame-level; compare with 89.93%, not 96.97%).

**L4. A leaking validation set hides overfitting.**
The reported gap of 1.95pp was really about 7pp (7.07 ± 0.15). Rule: check the
validation set for leakage before trusting any train/val gap or checkpoint choice.

**L5. Too-good metrics are a finding to investigate, not a result.**
AUC 0.998 on a small single-method dataset should have prompted a leakage check
before the draft report. Rule: sanity-check every implausibly high number.

**L6. A fixed split seed means seeds test only initialisation.**
Three seeds on one split cannot speak to data variability. Rule: use k-fold or
multiple grouped splits when claiming robustness.

**L7. Small test sets quantise metrics.**
44 videos means one video is 2.27pp, so baseline and augmentation looked identical
at video level. Rule: choose the evaluation size deliberately (cross-validation),
and use frame-level or paired analysis to separate variants.

**L8. Constants that mirror results go stale.**
`VIDEO_ACCURACY_DEFAULT = 0.9639` outlived the number it copied. Rule: generate
one `numbers.json` from result files; nothing hand-copies a metric.

**L9. Tests that pin a real-world ordering rot.**
`test_fusion` assumed video accuracy > audio accuracy until the SVM finished.
Rule: pin the mechanism, not the ordering.

**L10. Session-attached background jobs die with the session.**
The training matrix was killed twice. Rule: launch long jobs detached
(`start_new_session`, `caffeinate -i`), make every cell idempotent
(`scripts/run_cell.sh`), keep the Mac awake and plugged in overnight.

**L11. No git, no code provenance.**
Results cannot cite a commit. Rule: `git init` with a `.gitignore` for data,
frames and checkpoints, and record the commit hash in each run's config.

**L12. Cross-dataset generalisation failed on both branches.**
Video: Celeb-DF-v2 61.2% (old model). Audio: DeepfakeTIMIT genuine speech scored
about 0.98 fake. Rule: state in-distribution figures as feasibility only.

**L13. Compare alternatives empirically or say you didn't.**
No other backbone, audio front-end or classifier was ever evaluated; choices rest
on the literature. Rule: run at least a cheap baseline (MFCC + SVM) or state the
limitation plainly.

**L14. Change one variable at a time, and never overwrite.**
The tag system plus superseding old results (not deleting them) made the leakage
comparison possible. Keep doing this.

**L15. Never quote a superseded number.**
When an upstream model changes, every downstream evaluation that consumed it
(4-condition, threshold T, Celeb-DF, hybrid) is stale until re-run.

**L16. Unresolved figures should be flagged, not smoothed over.**
The PPR's F1 0.9632 does not match `results/metrics.json` (0.9601). Verify against
the submitted PDF before repeating it.

**L17. Avoid `!` (and spaces) in folder names.**
The parent folder `Year 3 Sem 2!!!!` triggered shell history expansion when a command was pasted
into an interactive terminal (`!!` was replaced by the previous command), silently corrupting the
path. Rule: keep repository paths free of `!` and spaces, and wrap any unavoidable path in single
quotes, never double quotes.

**L18. In-distribution success is not evidence of general deepfake detection.**
A model at 97% clip accuracy on Deepfakes-method fakes detected 0% of FaceSwap fakes and 15% of
NeuralTextures fakes on unseen identities, with FaceSwap scoring below chance (AUC 0.26). It learned
one generator's artefacts. Rule: always test on unseen manipulation methods, train on several, and
scope any claim to the methods actually covered.

**L19. A failure that survives a change of method is a data property, not a model property.**
Genuine unseen-corpus speech was flagged as spoof by both MFCC + SVM and wav2vec2 + SVM (100 of 100 clips
each), and unseen manipulation methods defeated every video backbone. In both branches the cause is what the
training data covered. Rule: before swapping models, test whether an alternative fails the same way.

**L20. Do not compare metrics across test sets of different composition.**
Multi-method models score lower on the mixed test set (Xception-mm 88% frame accuracy against 94.7% for the
single-method Xception) yet are the only ones that detect FaceSwap at all (88% against 0%). The single-method
number was high because the test contained one easy manipulation family. Rule: compare per-method detection and
say what each test set contains.

**L21. A closed lid or battery power defeats `caffeinate -i`.**
The overnight queue lost about 8 hours (Xception seed 44 ran 05:40 to 13:44) because the Mac slept. Results were
unaffected, only time was lost. Rule: keep the Mac plugged in with the lid open, launch with `caffeinate -s -i`,
and check `events.log` timestamps for unexplained gaps.

**L22. A label that is true for one model can be false for another.**
The cross-method script tagged FaceSwap "unseen method" for every model, which is wrong for models trained on it.
Roles must come from each run's own config, not a constant. Caught before the numbers were quoted.

**L23. A parameter fitted on a small validation set can be worse than none.**
Temperature scaling fitted on 36 validation videos over-corrected an already-calibrated model (test ECE 0.048 -> 0.069),
because validation and test differ in difficulty. Rule: check any fitted post-hoc adjustment on held-out data before
shipping it, and prefer out-of-fold estimates (cross-validation) when the data is small.

**L24. Train-time and inference-time preprocessing must be the same pipeline, and that needs a test.**
Training crops were saved as JPEG; the app fed the model uncompressed in-memory crops. Ranking quality (AUC) survived,
but the operating point shifted: two real videos flipped to fake and 7 of 88 verdicts changed. Rule: write a parity
test between the training path and the serving path before quoting any deployed-system number.

**L25. Test a proposed default against the data before adopting it.**
"Select on validation loss" looked more principled, but on the multi-method problem it would have chosen epoch 1-2
checkpoints and cost 3.8 pp of validation accuracy, because loss rises with over-confidence while accuracy still improves.
Rule: a plan step is a hypothesis; check it on data that cannot leak before making it the default.


**L26. Do not select "safe" tests by name; mark the dangerous ones, and never share a small machine with a training run.**
Filtering the server tests with `-k "not fake_demo and not real_demo and not composite_clip"` still ran three tests that use the real
video model and Ollama, which took a 16 GB Mac into swap and slowed a running training job about 60x for roughly 9 minutes. The claim I
then made ("no GPU used") had not been checked against what the tests actually do. Rule: mark every test that loads a model or calls
a service (`heavy`, skipped by `DEEPFAKE_SKIP_HEAVY=1`), check `ollama ps` and memory pressure before and after running tests during a
long job, and verify a "did not use X" claim from the process list, not from the test names.
\n

**L27. A default that is only correct for today's model is a landmine, and skipped tests hide it.**
`video_infer.load_models` read the architecture from `shipped_model.json` only when `model_path` was None, and fell back to
EfficientNet-B4 whenever a path was passed. `server.py` and `eval_fallback_4condition.py` both pass the shipped path explicitly, so
the first non-B4 model that shipped could not be loaded by either (RuntimeError: size mismatch). It was invisible for months because
B4 was both the default and the shipped model, and my own test runs had skipped the model-loading tests while training used the GPU.
Rule: resolve a property from the manifest by WHAT the artifact is, not by how the caller spelled the path; and before shipping a
change of artifact, run the tests that actually load it, not only the cheap ones.

**L28. A high accuracy can be produced by two failures pointing the same way.**
On the hybrid set, disagreement-aware fusion scored 97.5%, its best figure anywhere, while getting the modality implication wrong on
100% of the category that matters (manipulated video, genuine speech): the video branch missed 14 of 20 fakes and the audio branch
false-alarmed on all 20 genuine clips, so the system flagged the clips for the wrong reason. Rule: when a headline metric improves on
out-of-distribution data, check the sub-metric that encodes the actual mechanism before reporting it, and report both together.

**L29. When the split changes, every evaluation set built before it must be re-checked against it.**
The self-built four-condition set was sampled from all FaceForensics++ videos on 13 Sep. The identity-disjoint split arrived on 19 Sep and the
video model was retrained on it, but nobody asked whether the evaluation set was still held out: 57 of its 80 videos turned out to be in the new
training split. The leakage fix (L1) was applied to training and testing of the video branch and not propagated to the evaluation that answers
the research question. Rule: an evaluation set is data; after any change to the split, re-derive which of its items each model has seen, and
test that with a data-free check like the split manifests already have.

**L30. Do not write a causal explanation into the record until it has been tested.**
When I found that most of the four-condition set's videos were in the training split (L29), I wrote that this "explained" two things: optimistic
absolute figures, and the rise in false disagreement on fake + fake clips. Both explanations were plausible and neither had been checked. The held-out
re-run then showed video-only accuracy was not optimistic (92.5% against 90.0%) and that the fake + fake rate was 10% on held-out video, not 30%; and a
per-clip breakdown showed identities the model had trained on were detected LESS often (62%) than unseen ones (88%). The retractions had to be made in the
ledger, the swap record and the protocol file. Rule: a finding may be logged as a fact; its explanation is a hypothesis until a test could have contradicted
it, and should be labelled that way until then.


**L31. Judge a safety net end to end, not branch by branch.**
The out-of-domain gate was right about the audio almost every time it fired (LAV-DF 185/200, DeepfakeTIMIT 20/20), so withholding the flagged score looked
safe. End to end it was not: withholding one branch hands the verdict to the other, and on the same unfamiliar data the other branch was just as wrong
(DeepfakeTIMIT: 14 confident REAL verdicts on fake clips; held-out FF++: two correct verdicts turned wrong). The rule written before the results (in-domain
accuracy may fall at most 2 pp) caught it. Rule: evaluate any gate, fallback or abstention on the final verdict over in-domain AND out-of-domain sets, with
pass criteria fixed first; prefer a flag that changes no verdict when the alternative has not been shown to help.

**L32. A screen's false-positive rate can hide inside a "success" as easily as a "failure".**
Regenerating the 50-case packet with real timing data raised the automatic faithfulness screen's rejection rate from 8% to 62%.
The instinct was to suspect the new prompt content; the actual cause, found by reading the failing texts rather than trusting
the aggregate number, was two negation-detection gaps in the screen itself (a substring match with no negation handling), newly
triggered because the longer prompt gave Llama more to hedge about, not because it hallucinated more. A controlled A/B test (old
prompt vs new prompt, same score inputs) confirmed the one real behavioural difference (a rote "partially manipulated" opener)
was pre-existing, not new. Rule: when an automated check's pass rate moves sharply, read the actual failing text before
concluding the thing being checked got worse; the check itself is just as likely to be the thing that changed.

**L33. A keyword screen built on one model's outputs is biased towards that model.**
In the explanation LLM comparison (M1), 11 of Qwen 2.5's 19 screen failures at one seed were faithful texts the screen misread (seconds written as "0 to 2
seconds", "since the video and audio branches disagree", "Neither branch disagrees"), against 2 of Llama 3's 24. The screen's rules and its L32 fixes had
been written from Llama 3 text. The raw pass rates therefore understated the challenger by about 22 pp. Rule: when an automatic check is used to compare
models, read and label the failures of every compared model (declared in advance, as M1 did), and treat raw rates as an upper bound on the gap in the
incumbent's favour.

