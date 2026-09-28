# Explanation-layer rating packet (50 cases)

Generated: 2026-09-22

**Instructions.** Score every case on all three dimensions using the
rubric below. Work through the cases IN ORDER and do NOT discuss them
with the other rater until both sheets are complete — the whole point
of Cohen's Kappa is that the two ratings are independent.

Record your scores in your own CSV sheet
(`rating_sheet_rater1.csv` or `rating_sheet_rater2.csv`).

## Rubric (Chapter 3.6)

Score each explanation on THREE dimensions. Judge the explanation ONLY against
the structured input printed above it — not against your own opinion of whether
the video is really fake.

**1. Factual grounding** — does every claim match the structured input?
  - 2 (passes)  : every statement is traceable to a field in the structured input.
  - 1 (partial) : mostly grounded, but one statement overreaches or is vague
                  enough to mislead.
  - 0 (fails)   : contains a claim that contradicts the structured input.

**2. Score accuracy** — are the probabilities stated correctly, and as
   probabilities rather than certainties?
  - 2 (passes)  : values are stated accurately (a decimal or its correct
                  percentage form both count), and framed as a likelihood.
  - 1 (partial) : value correct but framed too strongly ("this is fake" rather
                  than "likely fake"), or rounded misleadingly.
  - 0 (fails)   : states a wrong number, or asserts certainty from a probability.

**3. Absence of hallucination** — does it avoid introducing anything new?
  - 2 (passes)  : introduces no facts beyond the structured input.
  - 1 (partial) : adds mild unsupported framing (e.g. generic commentary not
                  drawn from the input).
  - 0 (fails)   : invents specifics — a manipulation technique, a tool, an
                  identity, a score for a branch marked "not evaluated".

Note the distinction between dimensions 1 and 3: (1) is about whether what it
says MATCHES the input; (3) is about whether it says things that were NOT in
the input at all. An explanation can be fully accurate about the scores (1=2)
while still inventing an unsupported detail (3=0).


---

### Case `eval-01`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : REAL
  video branch P(fake): 0.000
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): not evaluated
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered real. The video branch suggests that the video is genuine, with a very low likelihood of manipulation. The audio branch was not evaluated, so the verdict is based solely on the video branch.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-02`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : REAL
  video branch P(fake): 0.080
  video anomaly timing: 0:02 to 0:02 (peak 0.70)
  audio branch P(fake): 0.000
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered real, and the model estimates that the likelihood of manipulation is low. The video branch suggests that the video is genuine, and the audio branch also suggests that the audio is genuine. There is no indication that the video and audio are manipulated in different ways.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-03`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.025
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): 1.000
  branches disagree   : yes
  modality implicated : audio
```

**Generated explanation:**

> The analysis suggests that the video is partially manipulated. The video branch leans genuine, indicating that the video itself is likely authentic. However, the audio branch leans fake, suggesting that the audio may have been manipulated. Since the branches disagree, it's possible that only part of the content is manipulated, and the audio is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-04`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.000
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): 1.000
  branches disagree   : yes
  modality implicated : audio
```

**Generated explanation:**

> The video has been partially manipulated. The video branch suggests it's genuine, but the audio branch indicates it's likely fake. The two branches disagree, and the audio modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-05`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.243
  video anomaly timing: 0:00 to 0:01 (peak 0.77), 0:02 to 0:03 (peak 0.99)
  audio branch P(fake): 1.000
  branches disagree   : yes
  modality implicated : audio
```

**Generated explanation:**

> The video has been partially manipulated. The video branch leans towards being genuine, but the audio branch suggests it's fake. The two branches disagree, and the audio modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-06`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : REAL
  video branch P(fake): 0.001
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): 0.000
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered real, and both the video and audio branches suggest it is genuine. The model estimates that the likelihood of the video being manipulated is very low, with scores of 0.001 for both the video and audio branches.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-07`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : REAL
  video branch P(fake): 0.001
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): 0.000
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered real, and both the video and audio branches suggest it is genuine. The model estimates that the likelihood of the video being manipulated is very low, with scores of 0.001 for both the video and audio branches.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-08`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.157
  video anomaly timing: 0:00 to 0:01 (peak 0.80), 0:01 to 0:01 (peak 0.62)
  audio branch P(fake): 1.000
  branches disagree   : yes
  modality implicated : audio
```

**Generated explanation:**

> The video has been partially manipulated. The video branch leans towards being genuine, but the audio branch suggests it's fake. The two branches disagree, and the audio modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-09`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : REAL
  video branch P(fake): 0.025
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): 0.000
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered real, and both the video and audio branches suggest it is genuine. The video branch has a low probability of being manipulated, at 0.025, which leans towards being genuine. The audio branch also has a very low probability of being manipulated, at 0.000, which further supports the video being genuine.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-10`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.983
  video anomaly timing: 0:00 to 0:02 (peak 1.00)
  audio branch P(fake): 0.116
  branches disagree   : yes
  modality implicated : video
```

**Generated explanation:**

> The video is partially manipulated. The video branch suggests that the video is likely fake, with a score of 0.983. The audio branch, on the other hand, leans towards being genuine, with a score of 0.116. The branches disagree, and the video modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-11`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : REAL
  video branch P(fake): 0.000
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): 0.000
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered real, and both the video and audio branches suggest it is genuine. The model didn't detect any unusual timing patterns or anomalies in the video. Overall, the analysis indicates that the video is not manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-12`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : FAKE
  video branch P(fake): 0.997
  video anomaly timing: 0:00 to 0:03 (peak 1.00)
  audio branch P(fake): 1.000
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered fake, with a high likelihood of manipulation estimated by the model. The video branch leans fake, with a score of 0.997, indicating a strong indication of manipulation. The audio branch also leans fake, with a score of 1.000. There is no disagreement between the video and audio branches, and no modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-13`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : FAKE
  video branch P(fake): 0.883
  video anomaly timing: 0:00 to 0:01 (peak 1.00), 0:01 to 0:02 (peak 0.97), 0:02 to 0:06 (peak 1.00)
  audio branch P(fake): 1.000
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered fake, with a high likelihood of manipulation. The video branch suggests that the video is likely manipulated, with a score of 0.883. The audio branch also suggests that the audio is likely manipulated, with a score of 1.000. There is no disagreement between the video and audio branches, and no modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-14`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.070
  video anomaly timing: 0:02 to 0:02 (peak 0.70)
  audio branch P(fake): 0.968
  branches disagree   : yes
  modality implicated : audio
```

**Generated explanation:**

> The video has been partially manipulated. The video branch suggests that the video is genuine, but the audio branch indicates that the audio is likely fake. The two branches disagree, and the audio modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-15`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.001
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): 1.000
  branches disagree   : yes
  modality implicated : audio
```

**Generated explanation:**

> The analysis suggests that the video is partially manipulated. The video branch leans genuine, indicating that the video itself is likely authentic. However, the audio branch leans fake, suggesting that the audio may have been manipulated. Since the branches disagree, it's possible that only part of the content is manipulated, and the audio is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-16`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : FAKE
  video branch P(fake): 0.911
  video anomaly timing: 0:00 to 0:00 (peak 0.99), 0:01 to 0:02 (peak 1.00)
  audio branch P(fake): 1.000
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered fake, with a high likelihood of manipulation. The video branch leans fake, with a score of 0.911, indicating a strong indication of manipulation. The audio branch also leans fake, with a score of 1.000. There is no disagreement between the video and audio branches, and no modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-17`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : FAKE
  video branch P(fake): 0.981
  video anomaly timing: 0:00 to 0:06 (peak 1.00)
  audio branch P(fake): 1.000
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered fake, with a high likelihood of manipulation estimated by the model. The video branch leans towards being fake, with a score of 0.981, indicating a strong indication of manipulation. The audio branch also leans towards being fake, with a score of 1.000. There is no disagreement between the video and audio branches, and no modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-18`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : FAKE
  video branch P(fake): 0.806
  video anomaly timing: 0:00 to 0:01 (peak 0.99)
  audio branch P(fake): 1.000
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered fake, with a high likelihood of manipulation estimated by the model. The video branch leans towards being fake, with a score of 0.806, indicating a strong indication of manipulation. The audio branch also leans towards being fake, with a score of 1.000, further supporting the overall verdict.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-19`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : REAL
  video branch P(fake): 0.004
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): 0.000
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered real, and both the video and audio branches suggest it is genuine. The video branch has a low probability of being manipulated, at 0.004, and the audio branch has an even lower probability, at 0.000. There are no time windows where the likelihood of manipulation is elevated, and the audio and video branches agree on the verdict.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-20`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.994
  video anomaly timing: 0:00 to 0:05 (peak 1.00)
  audio branch P(fake): 0.000
  branches disagree   : yes
  modality implicated : video
```

**Generated explanation:**

> The video has been partially manipulated. The video branch suggests that the video is likely fake, with a high probability of 0.994. There is a peak in the likelihood of manipulation between 0:00 and 0:05. The audio branch, on the other hand, indicates that the audio is genuine, with a low probability of 0.000. The video and audio branches disagree, suggesting that only part of the content may be manipulated. The video modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-21`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.887
  video anomaly timing: 0:00 to 0:02 (peak 1.00)
  audio branch P(fake): 0.019
  branches disagree   : yes
  modality implicated : video
```

**Generated explanation:**

> The video is partially manipulated. The video branch suggests that the video is likely fake, with a score of 0.887. The audio branch, on the other hand, leans towards being genuine, with a score of 0.019. The branches disagree, with the video modality flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-22`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.438
  video anomaly timing: 0:00 to 0:00 (peak 0.87), 0:00 to 0:01 (peak 0.76), 0:01 to 0:02 (peak 0.94), 0:02 to 0:03 (peak 0.96), and 2 more window(s) not shown
  audio branch P(fake): 0.000
  branches disagree   : yes
  modality implicated : video
```

**Generated explanation:**

> The video has been partially manipulated. The video branch suggests that the video is genuine, but the audio branch also leans towards being genuine. The two branches disagree, and the video modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-23`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.000
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): 0.960
  branches disagree   : yes
  modality implicated : audio
```

**Generated explanation:**

> The video has been partially manipulated. The video branch suggests it's genuine, but the audio branch indicates it's likely fake. The two branches disagree, and the audio modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-24`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.015
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): 1.000
  branches disagree   : yes
  modality implicated : audio
```

**Generated explanation:**

> The analysis suggests that the video is partially manipulated. The video branch leans towards being genuine, but the audio branch strongly suggests that it's manipulated. The two branches disagree, and the audio modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-25`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.183
  video anomaly timing: 0:01 to 0:02 (peak 0.52)
  audio branch P(fake): 1.000
  branches disagree   : yes
  modality implicated : audio
```

**Generated explanation:**

> The video has been partially manipulated. The video branch suggests that the video is genuine, but the audio branch indicates that the audio is likely fake. The two branches disagree, and the audio modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-26`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.492
  video anomaly timing: 0:00 to 0:00 (peak 0.98), 0:02 to 0:03 (peak 0.96)
  audio branch P(fake): 1.000
  branches disagree   : yes
  modality implicated : audio
```

**Generated explanation:**

> The video has been partially manipulated. The video branch leans genuine, but the audio branch leans fake, suggesting that the audio content is more likely manipulated. The video and audio branches disagree, which flags the audio modality as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-27`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.170
  video anomaly timing: 0:01 to 0:02 (peak 0.70)
  audio branch P(fake): 1.000
  branches disagree   : yes
  modality implicated : audio
```

**Generated explanation:**

> The video has been partially manipulated. The video branch suggests that the video is genuine, but the audio branch indicates that the audio is likely fake. The two branches disagree, and the audio modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-28`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : FAKE
  video branch P(fake): 0.999
  video anomaly timing: 0:00 to 0:05 (peak 1.00)
  audio branch P(fake): 0.965
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered fake, with a high likelihood of manipulation. The video branch suggests a strong indication of manipulation, with a score of 0.999. The audio branch also leans towards manipulation, with a score of 0.965. There is no disagreement between the video and audio branches, and no modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-29`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : REAL
  video branch P(fake): 0.238
  video anomaly timing: 0:00 to 0:00 (peak 0.88), 0:04 to 0:04 (peak 0.63), 0:04 to 0:05 (peak 0.52)
  audio branch P(fake): 0.003
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered real, and both the video and audio branches suggest it is genuine. The video branch leans towards being genuine, with a score of 0.238, and the audio branch also leans towards being genuine, with a score of 0.003. There are some anomalies in the video timing, with elevated likelihood scores at 0:00 to 0:00, 0:04 to 0:04, and 0:04 to 0:05, but these do not suggest manipulation.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-30`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : REAL
  video branch P(fake): 0.011
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): 0.011
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered real, and both the video and audio branches suggest it is genuine, with a low likelihood of manipulation. There are no unusual timing patterns detected in the video, and the audio analysis also points to a genuine video.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-31`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 1.000
  video anomaly timing: 0:00 to 0:03 (peak 1.00)
  audio branch P(fake): 0.000
  branches disagree   : yes
  modality implicated : video
```

**Generated explanation:**

> The video is partially manipulated. The video branch suggests that the video is fake, with a high likelihood of 1.000. The audio branch, on the other hand, indicates that the audio is genuine, with a low likelihood of 0.000. The branches disagree, with the video modality flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-32`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : REAL
  video branch P(fake): 0.000
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): 0.001
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered real, and both the video and audio branches suggest it is genuine. The video and audio branches both lean towards the video being unmanipulated, with very low probabilities of it being fake. There are no time windows where the likelihood of manipulation is elevated, and the branches do not disagree.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-33`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.372
  video anomaly timing: 0:00 to 0:01 (peak 1.00), 0:02 to 0:02 (peak 0.94)
  audio branch P(fake): 0.001
  branches disagree   : yes
  modality implicated : video
```

**Generated explanation:**

> The video has been partially manipulated. The video branch suggests that the video is genuine, but the audio branch also leans towards being genuine. The two branches disagree, and the video modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-34`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : FAKE
  video branch P(fake): 0.962
  video anomaly timing: 0:00 to 0:04 (peak 1.00), 0:04 to 0:06 (peak 1.00)
  audio branch P(fake): 1.000
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is likely fake, with a high probability of manipulation estimated by the model. The video branch leans towards being fake, with a score of 0.962, and the audio branch also leans towards being fake, with a score of 1.000. There is no disagreement between the video and audio branches, and no modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-35`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.000
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): 0.952
  branches disagree   : yes
  modality implicated : audio
```

**Generated explanation:**

> The video has been partially manipulated. The video branch suggests it's genuine, but the audio branch indicates it's likely fake. The two branches disagree, and the audio modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-36`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.994
  video anomaly timing: 0:00 to 0:04 (peak 1.00)
  audio branch P(fake): 0.109
  branches disagree   : yes
  modality implicated : video
```

**Generated explanation:**

> The video has been partially manipulated. The video branch suggests that the video is likely fake, with a high probability of 0.994. The audio branch, on the other hand, indicates that the audio is genuine, with a probability of 0.109. The video and audio branches disagree, suggesting that only part of the content may be manipulated. The video modality is flagged as more likely manipulated, with an elevated likelihood occurring from 0:00 to 0:04.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-37`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : REAL
  video branch P(fake): 0.281
  video anomaly timing: 0:00 to 0:01 (peak 0.77), 0:02 to 0:03 (peak 0.99), 0:03 to 0:04 (peak 0.96), 0:04 to 0:04 (peak 0.73)
  audio branch P(fake): 0.026
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The overall verdict is that the video is real. The video branch suggests it's genuine, with a score of 0.281, which leans towards being genuine. There's also a peak in the video anomaly timing from 0:00 to 0:04, with peaks at 0:00, 0:02, and 0:03. The audio branch also suggests it's genuine, with a score of 0.026.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-38`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : FAKE
  video branch P(fake): 0.987
  video anomaly timing: 0:00 to 0:01 (peak 1.00)
  audio branch P(fake): 1.000
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered fake, with a high likelihood of manipulation. The video branch suggests a strong indication of manipulation, with a score of 0.987. The audio branch also leans towards manipulation, with a score of 1.000. There is no disagreement between the video and audio branches, and no modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-39`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.167
  video anomaly timing: 0:00 to 0:01 (peak 0.99)
  audio branch P(fake): 1.000
  branches disagree   : yes
  modality implicated : audio
```

**Generated explanation:**

> The video has been partially manipulated. The video branch suggests that the video is genuine, but the audio branch indicates that the audio is likely fake. The two branches disagree, and the audio modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-40`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : REAL
  video branch P(fake): 0.012
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): 0.000
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered real, and both the video and audio branches suggest it is genuine. The video branch has a low probability of being manipulated, and the audio branch has an even lower probability. There are no signs of manipulation in the timing of the video, and the overall verdict is that the video is not manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-41`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : REAL
  video branch P(fake): 0.042
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): 0.001
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered real, and both the video and audio branches suggest it is genuine. The video branch has a low probability of being manipulated, at 0.042, and the audio branch has an even lower probability, at 0.001. There are no time windows where the likelihood of manipulation is elevated, and the audio and video branches agree on the verdict.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-42`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.000
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): 1.000
  branches disagree   : yes
  modality implicated : audio
```

**Generated explanation:**

> The video has been partially manipulated. The video branch suggests it's genuine, but the audio branch indicates it's likely fake. The two branches disagree, and the audio modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-43`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 1.000
  video anomaly timing: 0:00 to 0:05 (peak 1.00)
  audio branch P(fake): 0.001
  branches disagree   : yes
  modality implicated : video
```

**Generated explanation:**

> The video is partially manipulated. The video branch suggests that the video is fake, with a high likelihood of 1.000. The audio branch, on the other hand, indicates that the audio is genuine, with a low likelihood of 0.001. The two branches disagree, with the video modality flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-44`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.001
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): 0.940
  branches disagree   : yes
  modality implicated : audio
```

**Generated explanation:**

> The video has been partially manipulated. The video branch suggests it's genuine, but the audio branch indicates it's likely fake. The two branches disagree, and the audio modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-45`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.000
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): 1.000
  branches disagree   : yes
  modality implicated : audio
```

**Generated explanation:**

> The video has been partially manipulated. The video branch suggests it's genuine, but the audio branch indicates it's likely fake. The two branches disagree, and the audio modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-46`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : REAL
  video branch P(fake): 0.000
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): 0.332
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The overall verdict is that the video is real. The video branch suggests that the video is genuine, with a low probability of manipulation. The audio branch also leans towards being genuine, with a moderate probability of manipulation. The two branches agree, and no modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-47`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : REAL
  video branch P(fake): 0.248
  video anomaly timing: 0:01 to 0:01 (peak 0.81), 0:03 to 0:04 (peak 0.99)
  audio branch P(fake): 0.002
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered real, with a high likelihood of being genuine. The video and audio branches both lean towards genuineness, with scores of 0.248 and 0.002, respectively. There are no elevated-likelihood windows detected in the video, but there are some brief periods where the likelihood of manipulation is higher, specifically from 0:01 to 0:01 and from 0:03 to 0:04.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-48`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.018
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): 1.000
  branches disagree   : yes
  modality implicated : audio
```

**Generated explanation:**

> The analysis suggests that the video is partially manipulated. The video branch leans towards being genuine, but the audio branch is highly likely to be manipulated. The two branches disagree, and the audio modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-49`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.000
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): 0.539
  branches disagree   : yes
  modality implicated : audio
```

**Generated explanation:**

> The video has been partially manipulated. The video branch suggests it's genuine, but the audio branch indicates it's likely fake. The two branches disagree, and the audio modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `eval-50`

*Source: evaluation set (real pipeline scores), results file fallback_4condition_results.json, sample seed 42*  
*evaluation-set clip (clip id withheld: it encodes the ground-truth category)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.003
  video anomaly timing: no elevated-likelihood windows detected
  audio branch P(fake): 0.960
  branches disagree   : yes
  modality implicated : audio
```

**Generated explanation:**

> The video has been partially manipulated. The video branch suggests that the video is genuine, but the audio branch indicates that the audio is likely manipulated. The two branches disagree, and the audio modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---
