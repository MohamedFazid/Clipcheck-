# Testing guide: how to test every model and what to expect

Written 2026-09-21 18:08 (+08). Every "expected" value below was observed on the live server (pid 7564, started 17:44) or
re-run from the repo on that day; nothing is predicted from theory. Where a result is a known weakness it is marked
**KNOWN LIMITATION** so that seeing it does not look like a bug. Start the app with `~/mdd/run_server.sh`, open
http://localhost:8000, and keep the Ollama app running.

> **Updated 2026-09-28 for the final interface (v4, frozen 27 Sep).** The scores and verdicts below are unchanged; only where they appear
> changed. The **Check a video** page shows eight demo clips (the shelf: RVRA_000, RVRA_001, RVFA_000, RVFA_001, FVRA_000, FVRA_001,
> FVFA_002, FVFA_004). Open `http://localhost:8000/#testing` for the clips user testing used, under neutral codes (RVRA_000, RVFA_000,
> FVRA_000, FVFA_002, 183_253, 183, LAVDF_RVRA_000, noface_silent). Any other clip in this guide is tested by uploading its file on the
> Check a video page (for example `eval_lavdf/RVRA/RVRA_001.mp4`; an uploaded clip is shown under its file name, without the `LAVDF_`
> prefix). The verdict says "Likely genuine", "Likely manipulated", "Partly manipulated" or "No verdict", and the unfamiliar-input warning
> sits inside the verdict ("may be wrong for this clip"). Detail (findings, technical detail, accuracy and limits, glossary, familiarity)
> is in the **Details** sheet; the accuracy tables are on the **Accuracy** page. The user-tested interfaces still run: v1 with
> `./run_v1_interface.sh` (port 8001) and v2 with `./run_v2_interface.sh` (port 8002). Latency is 7.3 s warm per clip (section 7; ledger L3).
> The note below describes v2 and is kept for the record.

> **Updated 2026-09-25 for interface v2 ("Clipcheck").** The scores and verdicts below are unchanged; what changed is where they appear.
> Examples are under **Try an example** on the start page (plain names; "Show all" lists every clip; open `http://localhost:8000/#testing`
> to see the codes used below, such as RVRA_000). The verdict card says "Likely genuine", "Likely manipulated", "Partly manipulated: the
> picture / the voice" or "No verdict". Scores are shown as ">99%" and "<1%" at the extremes. Detail (per-frame chart, waveform, distances,
> models) is under **Learn more**; the accuracy tables are on the **Accuracy** page. The original interface still runs with
> `~/mdd/run_v1_interface.sh` on port 8001. Latency is now 7.3 s warm per clip (section 7; ledger L3).

## 0. What "working like we wanted" means

The system promised in the PPR and Draft does five things. Each has a test below.

| # | Promise | Section |
|---|---|---|
| 1 | Video branch scores P(video_fake) from face crops | 1 |
| 2 | Audio branch (speech gate, wav2vec2, SVM) scores P(audio_fake) | 2 |
| 3 | A real face with fake speech, or the reverse, is reported as PARTIAL_MANIPULATION naming the modality | 3 |
| 4 | The explanation is Llama 3, constrained, with a safety net | 4 |
| 5 | The app never invents a number when a branch cannot run | 5 |

Thresholds in force: disagreement T = 0.35; a branch "leans fake" at P >= 0.5; fusion weights video 0.464, audio 0.536.

## 1. Video branch (Xception, FF++ c23, seed 44)

In the final interface these clips are not on the shelf: upload each file from `demo_videos/` on the Check a video page (183_253
and 183 are also in testing mode). These FF++ clips are silent, so the verdict says "Only the picture was
checked, because the clip has no sound".

| Clip | Expected verdict | P(video_fake) |
|---|---|---|
| 183_253, 469_481, 481_469, 585_599 (FAKE) | FAKE | 0.947, 0.956, 0.998, 0.9999 |
| 599_585 (FAKE) | FAKE, but borderline | 0.554 |
| 183, 469, 481, 585, 599 (REAL) | REAL | 0.0025, 0.025, 0.000, 0.002, 0.003 |

Expect about 4.5 to 9 s per clip (warm), and a face crop thumbnail plus a per-frame score strip. The Xception name should
appear under Models, never EfficientNet-B4 (that swap is recorded as deviation D-C).

**KNOWN LIMITATION:** 599_585 is a fake that only just crosses 0.5. The 5-fold cross-validated clip accuracy is 82.8%
(95% CI 79.2 to 86.2), so roughly one clip in six is expected to be wrong. Celeb-DF-v2 (unseen dataset) is 59.1%. These
demo clips were chosen from the FF++ pool; four of five fakes being confident is normal, not a guarantee.

## 2. Audio branch (Silero VAD, wav2vec2-base frozen, RBF SVM)

| Clip | Expected |
|---|---|
| sample_with_audio.mp4 (constant tone) | Audio gated: "no speech detected"; verdict REAL from video alone, weight video 1.0 |
| Any clip with a Veo music-only soundtrack (veo_violinist) | Audio gated the same way, video-only verdict |
| RVRA_000 / 001 / 002 (genuine speech) | P(audio_fake) 0.0105, 0.0097, 0.0019 |
| RVFA_000 / 001 / 002 (spoofed speech) | P(audio_fake) 1.0, 0.952, 0.940 |
| composite_real_video_synthetic_speech | P(audio_fake) 1.0 with 9.5 s of speech |

Speech seconds are shown; short clips (1.4 to 3 s) are normal for the constructed set because ASVspoof utterances are short.

**KNOWN LIMITATION (test this yourself, it matters for the viva):** record a short video of yourself speaking and upload
it. Expect the audio branch to call your genuine voice fake with P near 1.0, and the verdict to become PARTIAL_MANIPULATION
naming audio. On genuine speech from a corpus the SVM never saw, 100 of 100 clips were flagged, for both wav2vec2 and WavLM
(results/audio_encoder_comparison/, results/audio_channel_diagnostic/). The cause is the training corpus, not the codec
(codec re-encoding moved false alarms only from 5.0% to 7.0%). On ASVspoof itself the audio branch is strong (EER 3.96%, accuracy
97.65%), so both statements are true: it works in its own domain and does not transfer. Report it as a limitation, not a bug.

## 3. Disagreement-aware fusion (the research contribution)

Constructed set (real FF++ video muxed with ASVspoof audio), first three of each category in the demo list:

| Category | Ground truth | Expected on the live app (observed) |
|---|---|---|
| RVRA_000, 001, 002 | real video, real audio | REAL x3. RVRA_002 has P(video) 0.248 and gap 0.246, below T so no disagreement |
| RVFA_000, 001, 002 | real video, fake audio | PARTIAL_MANIPULATION, implicated **audio** x3 (gaps 0.90, 0.95, 0.94) |
| FVRA_000, 001, 002 | fake video, real audio | PARTIAL_MANIPULATION, implicated **video** x3 (gaps 0.999, 0.868, 1.000) |
| FVFA_002 | fake video, fake audio | FAKE (both 1.0) |
| FVFA_000 | fake video, fake audio | PARTIAL, implicated audio (video only 0.167) |
| FVFA_001 | fake video, fake audio | PARTIAL, implicated video (audio only 0.110) |

So 9 of 9 real/real and single-modality cases behave as designed, and 1 of 3 fake/fake cases is correct (the other two are the limitation below).

**KNOWN LIMITATION:** when both channels are fake but one branch misses, the system reports PARTIAL naming the branch that
did detect. That is a wrong modality claim (or a partial verdict where the truth is "both"). Held-out rate: 10% false
disagreement on fake+fake clips. The app's Accuracy page states this.

**Where the numbers come from (do not quote the 3-clip tables as results):** 20 clips per category, held-out set
(`eval_heldout/`, all videos in the split's test partition): video-only 92.5%, audio-only 92.1%, standard fusion 76.3%,
disagreement-aware 94.7%. Advantage over standard fusion +18.4 pp, 95% CI [+7.9, +28.9]. Hybrid set (DeepfakeTIMIT, real
manipulated speech+video): 98.7% correct verdicts but 0% correct modality naming, because both channels are fake there.

Optional edge case worth trying: the composite clip (real 183.mp4 face + synthetic speech). Expected PARTIAL/audio with
P(video) 0.0025, P(audio) 1.0, gap 0.9975.

## 4. Explanation layer (Llama 3 8B via Ollama)

Every result shows who wrote the explanation: "Written by the AI model and checked" (Llama 3) or "Standard wording" (the template).

* **"Written by the AI model and checked"**: the normal case. Observed on all 24 demo clips, and on 4 of the 6 extra clips that were accepted for analysis (the other two: a template for no scores, and a template after a screen rejection); all 24 demo clips passed the screen. Text stays inside the structured input, for example for
  RVFA_000: "The video branch leans genuine ... the audio branch leans fake ... the audio is flagged as more likely manipulated."
  Generation takes 1.3 to 6.9 s.
* **"Standard wording" with a reason**: the safety net. Since 25 Sep the standard wording is plain language, for example "The picture
  check found a 95% chance that the face was manipulated, so the face looks manipulated ... The result rests on the face check alone:
  the clip is likely manipulated." Two ways to see it:
  1. **Screen rejection.** Upload `veo_sailor` (AI-generated, see section 6). Llama wrote "the video and audio content are partially
     manipulated", which the faithfulness screen rejected (type: direction; the video leans genuine at 0.243). The app showed the
     deterministic template instead and kept the rejected text (`rejected_llm_text`) for auditing. Llama is not deterministic,
     so on a re-run this clip may pass; if it does, that is also correct.
  2. **Ollama down.** Quit the Ollama app (menu bar) and analyse any clip. Expected: standard wording, labelled "Standard wording", a reason
     saying the language model was unavailable, and no crash (covered by `tests/test_server.py`; not re-run by hand on 21 Sep). Start Ollama again afterwards.
* **INCONCLUSIVE clips** never call the LLM: the template says "No verdict could be given".

Score-versus-threshold wording ("leans genuine / leans fake") comes from deterministic Python (`explain.assess()`), not from Llama.
Human evaluation of explanation quality is **not done**: `results/explanation_eval_full/` has a 50-case packet with empty rating
cells (needs two raters). Do not describe the explanation as human-validated.

## 5. Robustness: what the app does when input is wrong

Each was run against the live server on 21 Sep.

| Input | Expected |
|---|---|
| Face-free video, silent (test pattern) | verdict **INCONCLUSIVE**, no scores shown, template explanation, about 1.5 s |
| Face-free video with speech | **audio-only** verdict (FAKE, P(audio) 1.0 for the synthetic speech used), video card says not evaluated, Llama text states video was not evaluated |
| Random bytes named `.mp4` | HTTP 400 "This file could not be read as a video (unsupported codec or corrupt file)." |
| `.txt` file | HTTP 400 "Unsupported file type: use MP4, MOV, AVI or MKV." |
| 135 s clip | HTTP 400 "This clip is 135 s long; the limit is 120 s." (limit 120 s, size limit 200 MB) |

To build the same files yourself, see the `ffmpeg` recipes in section 8.

## 6. Fully AI-generated video (out of scope, worth knowing)

The four Veo-3 clips in `demo_videos/ai_generated_2026/`, converted to MP4 and uploaded. The system is trained on face-swap
methods, and the PPR scopes out fully synthetic faces, so results here are informative but not a claim.

| Clip | Verdict | P(video) | P(audio) |
|---|---|---|---|
| veo_bar | PARTIAL, audio | 0.453 | 0.983 |
| veo_sailor | PARTIAL, audio (Llama text rejected by screen, template shown) | 0.243 | 0.973 |
| veo_spies | PARTIAL, audio | 0.578 | 0.983 |
| veo_violinist | FAKE (video only; music gated out) | 0.514 | none |

Reading: the video model is uncertain (0.24 to 0.58), the audio branch flags it all as fake. Do not present these as detections
of a fake video; the honest reading is "uncertain video, audio flagged", and the audio flag is unreliable on unseen corpora (section 2).

## 7. Speed

Re-measured 25 Sep (ledger L3), including the out-of-domain checks and moment windows: **7.28 s warm per clip** across 11 timed stages,
4.12 s cold start (`results/latency/latency.json`). End to end in the running app, on the 8 featured examples: 1.3 to 8.0 s, median 4.4 s
(`results/latency/app_end_to_end.json`; the 13 s FaceForensics++ clips are slowest). The first clip after a restart also loads the models.
The 21 Sep figure (9.0 s, 8 stages) is archived in `results/latency/archive/`.

## 8. Commands to reproduce the headline numbers

The project path contains `!!!!`, so use the `~/mdd` symlink.

Unit and integration tests (Ollama and the video model may load, so stop training jobs first):

```bash
cd ~/mdd && /opt/anaconda3/bin/python -m pytest tests -q --ignore=tests/test_server.py --ignore=tests/test_pipeline.py
```

```bash
cd ~/mdd && /opt/anaconda3/envs/deepfake-detect/bin/python -m pytest tests/test_server.py tests/test_pipeline.py -q
```

Observed 25 Sep: 154 passed, 1 skipped (base) and 51 passed (app). Observed 28 Sep, after the datasets were moved out of the folder:
146 passed, 9 skipped (base; eight tests in `test_data_split.py` need `frames/`) and 54 passed (app). After two unused files and their test were removed (28 Sep, 207 tests in 19 suites): 144 passed, 9 skipped
(base), 54 passed (app), CI subset 88 passed, 1 skipped. After the demo clips were
moved out (28 Sep, 15:02): base 142 passed, 11 skipped; app 28 passed, 24 skipped (the tests that run a demo clip skip without it; with
the clips present, 54 passed). Set `DEEPFAKE_SKIP_HEAVY=1` to skip
the tests that load models.

Held-out four-condition evaluation, written to a fresh folder so nothing is overwritten (about 3.5 min). Expect video 92.5,
audio 92.1, standard fusion 76.3, disagreement-aware 94.7:

```bash
cd ~/mdd && /opt/anaconda3/envs/deepfake-detect/bin/python scripts/eval_fallback_4condition.py --manifest eval_heldout/manifest.json --out-dir results/repro_check/heldout
```

Audio branch on the full ASVspoof 2019 LA eval partition (about 3 min). Expect EER 3.96%, accuracy 97.65%:

```bash
cd ~/mdd && /opt/anaconda3/bin/python scripts/eval_audio_metrics.py
```

Bootstrap interval for the fusion advantage on the repro run (expect about +18.4 pp, CI about [+7.9, +28.9]; the exact interval
can move by a fraction of a point if the run differs at all from the stored one):

```bash
cd ~/mdd && /opt/anaconda3/bin/python scripts/bootstrap_fusion_advantage.py --results results/repro_check/heldout/fallback_4condition_results.json --out results/repro_check/heldout/advantage_bootstrap.json
```

Building the robustness clips (needs the project's bundled ffmpeg; `imageio_ffmpeg.get_ffmpeg_exe()` prints its path):

```bash
# no face, silent
ffmpeg -f lavfi -i "testsrc=size=640x480:rate=25:duration=6" -c:v libx264 -pix_fmt yuv420p noface_silent.mp4
# 135 s clip, over the limit
ffmpeg -f lavfi -i "testsrc=size=320x240:rate=5:duration=135" -c:v libx264 -pix_fmt yuv420p too_long.mp4
# corrupt file
head -c 20000 /dev/urandom > corrupt.mp4
```

## 9. Things that are NOT tested by the above (be honest about them)

* FakeAVCeleb: never obtained; every multimodal figure is on self-built or DeepfakeTIMIT-based sets.
* Real-world speech: see the KNOWN LIMITATION in section 2.
* Explanation quality by humans, and real user-testing sessions (protocol written, no participants yet).
* Anything fully synthetic (section 6) is out of scope.

## 10. LAV-DF demo clips (independent set; expect WRONG answers, this is the documented limitation)

The 12 `LAVDF_*` clips (in the final interface only LAVDF_RVRA_000 is listed, in testing mode; upload the others from `eval_lavdf/`) are the first three per category by id from `eval_lavdf/` (LAV-DF test split, real generators:
SV2TTS audio, Wav2Lip video, VoxCeleb2 speakers). Scores from the F6 run (`results/lavdf_eval_shipped/`); the live app should reproduce them to within a
few thousandths. Do not read these as failures of the app: on the full 200 clips both branches are at or near chance (video AUC 0.377, audio AUC 0.522, every clip's audio
scored about 0.99), and only 5% to 13% of each "fake" clip is manipulated.

| Clip | P(video) | P(audio) | Verdict |
|---|---|---|---|
| LAVDF_RVRA_000 | 0.853 | 1.000 | FAKE |
| LAVDF_RVRA_001 | 0.763 | 0.990 | FAKE |
| LAVDF_RVRA_002 | 0.966 | 1.000 | FAKE |
| LAVDF_RVFA_000 | 0.643 | 1.000 | PARTIAL_MANIPULATION (audio) |
| LAVDF_RVFA_001 | 0.432 | 0.988 | PARTIAL_MANIPULATION (audio) |
| LAVDF_RVFA_002 | 0.569 | 0.987 | PARTIAL_MANIPULATION (audio) |
| LAVDF_FVRA_000 | 0.404 | 1.000 | PARTIAL_MANIPULATION (audio) |
| LAVDF_FVRA_001 | 0.714 | 1.000 | FAKE |
| LAVDF_FVRA_002 | 0.918 | 0.993 | FAKE |
| LAVDF_FVFA_000 | 0.135 | 0.995 | PARTIAL_MANIPULATION (audio) |
| LAVDF_FVFA_001 | 0.832 | 1.000 | FAKE |
| LAVDF_FVFA_002 | 0.796 | 0.991 | FAKE |

Two results worth demonstrating in the viva: (1) resolution is not the cause, because FF++ clips cropped to 224x224 and compressed to about 100 kbps still score AUC 0.977 (F6 addendum);
(2) the audio false alarms are a training-corpus problem, because adding 400 genuine VoxCeleb2 clips to the SVM's training data cuts them from 100% to 4% (F7, experiment only, not shipped).

## 11. Out-of-domain warning (added 2026-09-22 03:32; ledger O1)

Every result now carries, per branch, a distance from that branch's training data and a limit. Above the limit the input is "unfamiliar".
Default mode is `warn`: nothing about the verdict or scores changes. In the final interface the warning sits inside the verdict ("may be wrong
for this clip") and the distances are in the Details sheet under Familiarity. In v2, the page showed a yellow "This result may be wrong" card under the verdict
(since 25 Sep; v1 showed an amber line inside the verdict banner), an "Unfamiliar to the tool" flag on the part card, and a first item in
"What to do next"; the distances are under Learn more, Findings for this clip, Familiarity. Observed on the live server:

| Clip | Verdict (unchanged) | Flag |
|---|---|---|
| LAVDF_FVRA_000 | PARTIAL, audio (wrong) | video 122 > 100 and audio 71 > 43: both unfamiliar, caution shown |
| LAVDF_RVRA_000 | FAKE (wrong) | audio 70 > 43: caution shown |
| RVRA_000, RVFA_000, FVRA_000, composite | as in sections 1 to 3 | no flag (video 48 to 74, audio 26 to 37) |

What to expect over whole sets: LAV-DF test 199 of 200 clips flagged, including all 50 wrong verdicts; held-out FF++ 5 of 80 flagged, none of them wrong
(so about 1 in 16 good clips shows an unnecessary caution); Celeb-DF 12 of 100 flagged (the video flag misses most Celeb-DF errors). Your own recorded video
will very likely carry the audio caution. To try the other modes, start the server with `DEEPFAKE_OOD_MODE=withhold ~/mdd/run_server.sh` (flagged
scores are dropped; LAVDF_FVRA_000 becomes INCONCLUSIVE; not the default because it turned two correct held-out verdicts wrong) or `DEEPFAKE_OOD_MODE=off`.

Why the video branch still cannot be right on LAV-DF: the app averages 20 face crops from the first 6 s, and in a LAV-DF fake-video clip only about 1 of
those 20 crops is manipulated (5.7% on average; in 4 of 50 clips the fake is after the sampled window). Detecting it would need frame-level localisation,
which the PPR design does not include.
