# Explanation-layer rating packet (16 cases)

Generated: 2026-09-01

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

### Case `spec-01`

*Source: specified (NOT a real detection — audio branch untrained)*  
*video-only, confident FAKE (current pipeline state)*

**Structured input given to the model:**

```
  verdict             : FAKE
  video branch P(fake): 0.970
  audio branch P(fake): not evaluated
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is estimated to be fake with a high likelihood of 0.970. The audio branch was not evaluated, so the overall verdict is based solely on the video branch.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `spec-02`

*Source: specified (NOT a real detection — audio branch untrained)*  
*video-only, confident REAL (current pipeline state)*

**Structured input given to the model:**

```
  verdict             : REAL
  video branch P(fake): 0.030
  audio branch P(fake): not evaluated
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered real. The video branch suggests it's genuine, with a likelihood of 0.030. The audio branch was not evaluated, so the verdict is based solely on the video branch.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `spec-03`

*Source: specified (NOT a real detection — audio branch untrained)*  
*video-only, borderline just above 0.5*

**Structured input given to the model:**

```
  verdict             : FAKE
  video branch P(fake): 0.520
  audio branch P(fake): not evaluated
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered fake by the model, with a 52% likelihood that it was manipulated. The audio branch was not evaluated, so the verdict is based solely on the video branch.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `spec-04`

*Source: specified (NOT a real detection — audio branch untrained)*  
*video-only, borderline just below 0.5*

**Structured input given to the model:**

```
  verdict             : REAL
  video branch P(fake): 0.480
  audio branch P(fake): not evaluated
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered real, and the model's analysis suggests that the visual content is genuine, with a likelihood of 0.480. The audio branch was not evaluated, so the overall verdict is based solely on the video analysis.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `spec-05`

*Source: specified (NOT a real detection — audio branch untrained)*  
*video-only, boundary value 1.0*

**Structured input given to the model:**

```
  verdict             : FAKE
  video branch P(fake): 1.000
  audio branch P(fake): not evaluated
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered fake by the model, with a high likelihood of manipulation estimated at 1.000. The audio branch was not evaluated, so the verdict is based solely on the video branch.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `spec-06`

*Source: specified (NOT a real detection — audio branch untrained)*  
*video-only, boundary value 0.0*

**Structured input given to the model:**

```
  verdict             : REAL
  video branch P(fake): 0.000
  audio branch P(fake): not evaluated
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered real. The video branch suggests that the video is genuine, with a likelihood of 0.000. The audio branch was not evaluated, so the verdict is based solely on the video branch.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `spec-07`

*Source: specified (NOT a real detection — audio branch untrained)*  
*agreement, both high -> FAKE*

**Structured input given to the model:**

```
  verdict             : FAKE
  video branch P(fake): 0.910
  audio branch P(fake): 0.880
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video and audio branches both lean towards being fake, with the video branch estimated to be 91% likely to be manipulated and the audio branch estimated to be 88% likely to be manipulated. Overall, the verdict is that the content is fake.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `spec-08`

*Source: specified (NOT a real detection — audio branch untrained)*  
*agreement, both low -> REAL*

**Structured input given to the model:**

```
  verdict             : REAL
  video branch P(fake): 0.060
  audio branch P(fake): 0.110
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video and audio branches both lean towards being genuine, with estimated probabilities of 0.060 and 0.110 respectively. Overall, the verdict is that the content is real.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `spec-09`

*Source: specified (NOT a real detection — audio branch untrained)*  
*agreement, both near the decision boundary*

**Structured input given to the model:**

```
  verdict             : FAKE
  video branch P(fake): 0.550
  audio branch P(fake): 0.490
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered fake by the model, with a score of 0.550 indicating that it leans towards being manipulated. The audio, on the other hand, is estimated to be genuine, with a score of 0.490.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `spec-10`

*Source: specified (NOT a real detection — audio branch untrained)*  
*disagreement, video implicated (large gap)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.950
  audio branch P(fake): 0.200
  branches disagree   : yes
  modality implicated : video
```

**Generated explanation:**

> The analysis suggests that the video is partially manipulated. The video branch leans towards being fake, with a likelihood of 0.950, indicating that the model estimates this is likely manipulated. The audio branch, on the other hand, leans towards being genuine, with a likelihood of 0.200. Since the branches disagree, the video modality is flagged as more likely manipulated, suggesting that only part of the content may be manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `spec-11`

*Source: specified (NOT a real detection — audio branch untrained)*  
*disagreement, audio implicated (large gap)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.150
  audio branch P(fake): 0.800
  branches disagree   : yes
  modality implicated : audio
```

**Generated explanation:**

> The analysis suggests that the content is partially manipulated. The video branch leans genuine, indicating that the video itself is likely authentic. However, the audio branch leans fake, suggesting that the audio may have been manipulated. Since the branches disagree, it's possible that only the audio was manipulated, and the video remains genuine.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `spec-12`

*Source: specified (NOT a real detection — audio branch untrained)*  
*disagreement, marginal (just over T)*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.700
  audio branch P(fake): 0.540
  branches disagree   : yes
  modality implicated : video
```

**Generated explanation:**

> The analysis suggests that the video and audio content are partially manipulated. The video branch leans towards being fake, with a likelihood of 0.700, while the audio branch also leans towards being fake, with a likelihood of 0.540. The two branches disagree, with the video modality flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `spec-13`

*Source: specified (NOT a real detection — audio branch untrained)*  
*agreement, marginal (just under T)*

**Structured input given to the model:**

```
  verdict             : FAKE
  video branch P(fake): 0.600
  audio branch P(fake): 0.460
  branches disagree   : no
  modality implicated : none
```

**Generated explanation:**

> The video is considered fake by the model, with a score of 0.600 indicating that it is likely manipulated. The audio branch, on the other hand, suggests that the audio is genuine, with a score of 0.460. Since the branches do not disagree, the overall verdict is that the video is fake.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `spec-14`

*Source: specified (NOT a real detection — audio branch untrained)*  
*disagreement, maximal gap*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.990
  audio branch P(fake): 0.010
  branches disagree   : yes
  modality implicated : video
```

**Generated explanation:**

> The analysis suggests that the video is partially manipulated. The video branch leans towards being fake, with a high probability of 0.990. However, the audio branch leans towards being genuine, with a low probability of 0.010. Since the branches disagree, this suggests that only part of the content may be manipulated, and the video modality is flagged as more likely manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `spec-15`

*Source: specified (NOT a real detection — audio branch untrained)*  
*disagreement, audio implicated, both mid-range*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.400
  audio branch P(fake): 0.620
  branches disagree   : yes
  modality implicated : audio
```

**Generated explanation:**

> The analysis suggests that the video and audio may have been manipulated, but to different degrees. The video branch leans towards being genuine, with a likelihood of 0.400, while the audio branch leans towards being fake, with a likelihood of 0.620. Since the branches disagree, it's possible that only the audio was manipulated, and the video remains genuine.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---

### Case `spec-16`

*Source: specified (NOT a real detection — audio branch untrained)*  
*disagreement, video implicated, audio very low*

**Structured input given to the model:**

```
  verdict             : PARTIAL_MANIPULATION
  video branch P(fake): 0.800
  audio branch P(fake): 0.050
  branches disagree   : yes
  modality implicated : video
```

**Generated explanation:**

> The analysis suggests that the video is partially manipulated. The video branch leans towards being fake, with a likelihood of 0.800, indicating that the model estimates this is likely manipulated. However, the audio branch leans towards being genuine, with a likelihood of 0.050, suggesting that the audio content is not manipulated. Since the branches disagree, the video modality is flagged as more likely manipulated, implying that only part of the content may be manipulated.

| Dimension | Your score (0/1/2) |
|---|---|
| Factual grounding | |
| Score accuracy | |
| Absence of hallucination | |

---
