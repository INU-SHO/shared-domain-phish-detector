# S1. Statistical Comparison of Seen vs Unseen Performance: ML-based vs LLM-based

This document supplements the main paper "Detecting Phishing on
Shared-Domain Hosting Services Using LLM-Based Contextual Mismatch
Reasoning" (ARES 2026) with a statistical comparison of the
Seen-vs-Unseen performance gap between the ML-based baseline
(FreePhish) and our proposed LLM-based method evaluated under two
LLM configurations (GPT-4.1-mini and Qwen3-8B).

---

## S1.1 Motivation

ML-based methods such as FreePhish [Saha Roy et al., 2023] are
expected to degrade on Unseen services because they depend on
service-specific training data. In contrast, LLM-based methods that
do not require such training are expected to show little degradation.
We test this contrast by comparing the Seen-vs-Unseen F1 difference
between FreePhish and the proposed method under both LLM
configurations.

---

## S1.2 Methodology

### S1.2.1 Choice of Test: Paired t-test

We use a **paired t-test** with the run as the unit of analysis.
Specifically, for each method:

- Each run produces a Seen-condition F1 and an Unseen-condition F1
  evaluated on the same model.
- The pair (Seen F1, Unseen F1) within a run is treated as a paired
  observation.
- The null hypothesis is `H0: Mean(Seen F1 - Unseen F1) = 0`.

### S1.2.2 Effect Size: Cohen's d

To distinguish statistical significance from practical significance,
we compute **Cohen's d** for paired samples:

```
d = Mean(diff) / SD(diff)
```

where `diff = Seen F1 - Unseen F1` within each run.

Cohen's conventional benchmarks are:

| Cohen's d  | Interpretation |
|------------|----------------|
| 0.2        | small          |
| 0.5        | medium         |
| 0.8        | large          |
| 1.2        | very large     |
| 2.0        | huge           |

### S1.2.3 Experimental Setup

- **Methods compared**: FreePhish (ML-based), our proposed method under two LLM configurations (GPT-4.1-mini and Qwen3-8B)
- **Dataset**: The Impersonation dataset (100 samples; 50 Seen, 50 Unseen) from the main paper
- **Number of runs**: 10 per method
  - FreePhish: 10 training seeds (training stochasticity)
  - Proposed (both configurations): 10 evaluation cycles (LLM non-determinism)

---

## S1.3 Results

### S1.3.1 FreePhish (ML-based)

**Per-run F1 scores (10 training seeds):**

| Run   | Seen F1 | Unseen F1 | Diff (S-U) |
|-------|--------:|----------:|-----------:|
| 1     |  0.6667 |    0.4444 |    +0.2222 |
| 2     |  0.6486 |    0.3871 |    +0.2616 |
| 3     |  0.5946 |    0.3636 |    +0.2310 |
| 4     |  0.7000 |    0.4865 |    +0.2135 |
| 5     |  0.6111 |    0.4706 |    +0.1405 |
| 6     |  0.5556 |    0.3636 |    +0.1919 |
| 7     |  0.6667 |    0.4118 |    +0.2549 |
| 8     |  0.7907 |    0.4211 |    +0.3696 |
| 9     |  0.6842 |    0.4118 |    +0.2724 |
| 10    |  0.7000 |    0.4324 |    +0.2676 |
| **mean ± std** | **0.6618 ± 0.0655** | **0.4193 ± 0.0412** | **+0.2425 ± 0.0601** |

**Paired t-test result:**

- t = 12.7527, df = 9
- two-tailed *p* < 0.0001
- one-tailed *p* < 0.0001

**Effect size:**

- Cohen's d = 0.2425 / 0.0601 ≈ **4.03** (huge; well above the 2.0 threshold)

### S1.3.2 Proposed Method (LLM-based, GPT-4.1-mini)

**Per-cycle F1 scores (10 evaluation cycles):**

| Cycle | Seen F1 | Unseen F1 | Diff (S-U) |
|-------|--------:|----------:|-----------:|
| 1     |  0.9615 |    0.9615 |    +0.0000 |
| 2     |  0.9615 |    0.9615 |    +0.0000 |
| 3     |  0.9615 |    0.9804 |    -0.0189 |
| 4     |  0.9804 |    0.9804 |    +0.0000 |
| 5     |  0.9615 |    0.9434 |    +0.0181 |
| 6     |  0.9615 |    0.9434 |    +0.0181 |
| 7     |  0.9804 |    0.9434 |    +0.0370 |
| 8     |  0.9804 |    0.9434 |    +0.0370 |
| 9     |  0.9615 |    0.9434 |    +0.0181 |
| 10    |  0.9804 |    0.9615 |    +0.0189 |
| **mean ± std** | **0.9691 ± 0.0097** | **0.9562 ± 0.0152** | **+0.0128 ± 0.0176** |

**Paired t-test result:**

- t = 2.3079, df = 9
- two-tailed *p* = 0.0464
- one-tailed *p* = 0.0232

**Effect size:**

- Cohen's d = 0.0128 / 0.0176 ≈ **0.73** (between medium and large)

### S1.3.3 Proposed Method (LLM-based, Qwen3-8B)

**Per-cycle F1 scores (10 evaluation cycles):**

| Cycle | Seen F1 | Unseen F1 | Diff (S-U) |
|-------|--------:|----------:|-----------:|
| 1     |  0.8772 |    0.7937 |    +0.0835 |
| 2     |  0.8621 |    0.7813 |    +0.0808 |
| 3     |  0.7813 |    0.8136 |    -0.0323 |
| 4     |  0.8475 |    0.7869 |    +0.0606 |
| 5     |  0.8197 |    0.7742 |    +0.0455 |
| 6     |  0.8333 |    0.7869 |    +0.0464 |
| 7     |  0.8621 |    0.7742 |    +0.0879 |
| 8     |  0.8772 |    0.8065 |    +0.0707 |
| 9     |  0.8772 |    0.8475 |    +0.0297 |
| 10    |  0.8333 |    0.7937 |    +0.0397 |
| **mean ± std** | **0.8471 ± 0.0310** | **0.7958 ± 0.0221** | **+0.0513 ± 0.0355** |

**Paired t-test result:**

- t = 4.5623, df = 9
- two-tailed *p* = 0.0014
- one-tailed *p* = 0.0007

**Effect size:**

- Cohen's d = 0.0513 / 0.0355 ≈ **1.45** (very large in absolute terms, but considerably smaller than FreePhish; see S1.4)

### S1.3.4 Summary Comparison

**Table S1.1: Statistical comparison of Seen vs Unseen F1**

| Method                              | Seen F1         | Unseen F1       | Δ (Seen − Unseen)    | Paired t   | *p* (two-tailed) | Cohen's d  |
|-------------------------------------|-----------------|-----------------|----------------------|-----------:|-----------------:|-----------:|
| FreePhish (ML-based)                | 0.6618 ± 0.0655 | 0.4193 ± 0.0412 | **+0.2425 ± 0.0601** |    12.7527 |        < 0.0001  | **4.03**   |
| Proposed (LLM-based, GPT-4.1-mini)  | 0.9691 ± 0.0097 | 0.9562 ± 0.0152 | **+0.0128 ± 0.0176** |     2.3079 |          0.0464  | **0.73**   |
| Proposed (LLM-based, Qwen3-8B)      | 0.8471 ± 0.0310 | 0.7958 ± 0.0221 | **+0.0513 ± 0.0355** |     4.5623 |          0.0014  | **1.45**   |

---

## S1.4 Interpretation

### S1.4.1 All Three Methods Show Statistically Significant Differences

Strictly speaking, the paired t-test rejects the null hypothesis
(*p* < 0.05) for **all three** methods. Thus, none of the methods can
be said to have *literally* no difference between Seen and Unseen
performance.

However, statistical significance alone is uninformative about the
**magnitude** of the difference, especially with small variance.
Below we compare the methods through three complementary lenses:
absolute difference, effect size, and qualitative behavior.

### S1.4.2 Absolute Difference

The mean Seen-vs-Unseen difference is:

- FreePhish:                  **Δ F1 = +0.2425** (Seen substantially higher)
- Proposed (GPT-4.1-mini):    **Δ F1 = +0.0128** (Seen slightly higher)
- Proposed (Qwen3-8B):        **Δ F1 = +0.0513** (Seen moderately higher)

FreePhish's gap is approximately **19 times larger** than the
GPT-4.1-mini configuration and **4.7 times larger** than the
Qwen3-8B configuration. For FreePhish, this gap represents a
24-percentage-point drop in F1 when moving from Seen to Unseen
services—a clear and practically meaningful performance
degradation. For the proposed method, the gap is between 1.3 and
5.1 percentage points depending on the LLM configuration.

### S1.4.3 Effect Size

In standardized units (Cohen's d):

- FreePhish:                  **d = 4.03** (huge)
- Proposed (GPT-4.1-mini):    **d = 0.73** (between medium and large)
- Proposed (Qwen3-8B):        **d = 1.45** (very large)

While all three effect sizes are non-trivial, FreePhish's effect
size falls into the "huge" category (d > 2.0), with d = 4.03
substantially exceeding even this threshold. The proposed method's
effect sizes fall between "medium" and "very large", **2.8 to 5.5
times smaller than FreePhish**. We note that the Qwen3-8B
configuration exhibits a "very large" effect size in absolute terms,
yet it remains considerably smaller than FreePhish's huge effect,
indicating that the gap between training-based and training-free
approaches is preserved across both LLM configurations of the
proposed method.

### S1.4.4 Qualitative Behavior: Distributional Overlap

Examining the per-run F1 distributions:

- For **FreePhish**, the Seen-condition F1 range across runs
  ([0.5556, 0.7907]) and the Unseen-condition F1 range
  ([0.3636, 0.4865]) are **completely disjoint**. Every run's
  Seen F1 is strictly higher than every run's Unseen F1.

- For the **proposed method with GPT-4.1-mini**, the Seen-condition
  F1 range ([0.9615, 0.9804]) and the Unseen-condition F1 range
  ([0.9434, 0.9804]) **overlap almost entirely**. In one run, the
  Unseen F1 even exceeds the Seen F1.

- For the **proposed method with Qwen3-8B**, the Seen-condition F1
  range ([0.7813, 0.8772]) and the Unseen-condition F1 range
  ([0.7742, 0.8475]) **substantially overlap**, although the
  overlap is less complete than under GPT-4.1-mini. As with
  GPT-4.1-mini, one run shows Unseen F1 exceeding Seen F1.

The contrast between FreePhish's complete separation and the
proposed method's overlapping distributions reflects the
fundamental difference between training-based and training-free
approaches.

### S1.4.5 Conclusion

We conclude that:

1. The ML-based baseline FreePhish exhibits a substantial,
   statistically significant, and practically meaningful
   generalization gap between training-included (Seen) and
   training-excluded (Unseen) services. This is consistent with the
   expected behavior of a method that learns service-specific
   patterns from its training data.

2. Our proposed LLM-based method, under both LLM configurations,
   shows a statistically detectable but considerably smaller
   difference between Seen and Unseen services compared to
   FreePhish—approximately 4.7 to 19 times smaller in absolute
   terms and 2.8 to 5.5 times smaller in effect size. This is
   consistent with the expected behavior of a training-free method,
   for which the Seen/Unseen distinction has no special meaning at
   the algorithmic level.

These results support our claim that LLM-based contextual mismatch
reasoning provides a qualitatively different and more
service-agnostic generalization behavior than ML-based phishing
detection.

---

## S1.5 Per-service F1 Comparison

While the paired-by-run analysis above operates at the run level, the
per-service F1 breakdown provides a complementary view of how each
method behaves on individual services.

### S1.5.1 FreePhish

**Table S1.2: Per-service F1 for FreePhish (mean ± std across 10 seeds)**

| Condition | Service                | F1 (mean ± std) |
|-----------|------------------------|-----------------|
| Seen      | Weebly                 | 0.5179 ± 0.1387 |
| Seen      | Blogspot               | 1.0000 ± 0.0000 |
| Seen      | Wix                    | 0.3321 ± 0.2242 |
| Seen      | Google Sites           | 0.6270 ± 0.1858 |
| Seen      | GitHub Pages           | 0.5943 ± 0.1845 |
| Unseen    | Vercel                 | 0.5933 ± 0.1072 |
| Unseen    | Webflow                | 0.4048 ± 0.1150 |
| Unseen    | Netlify                | 0.3476 ± 0.0811 |
| Unseen    | Strikingly             | 0.0000 ± 0.0000 |
| Unseen    | Azure Static Web Apps  | 0.5371 ± 0.1656 |

### S1.5.2 Proposed Method (GPT-4.1-mini)

**Table S1.3: Per-service F1 for the proposed method, GPT-4.1-mini (mean ± std across 10 cycles)**

| Condition | Service               | F1 (mean ± std) |
|-----------|-----------------------|-----------------|
| Seen      | Weebly                | 1.0000 ± 0.0000 |
| Seen      | Blogspot              | 1.0000 ± 0.0000 |
| Seen      | Wix                   | 0.9273 ± 0.0383 |
| Seen      | Google Sites          | 0.9273 ± 0.0383 |
| Seen      | GitHub Pages          | 1.0000 ± 0.0000 |
| Unseen    | Vercel                | 0.9909 ± 0.0287 |
| Unseen    | Webflow               | 0.9636 ± 0.0469 |
| Unseen    | Netlify               | 1.0000 ± 0.0000 |
| Unseen    | Strikingly            | 0.9273 ± 0.0383 |
| Unseen    | Azure Static Web Apps | 0.9091 ± 0.0000 |

### S1.5.3 Proposed Method (Qwen3-8B)

**Table S1.4: Per-service F1 for the proposed method, Qwen3-8B (mean ± std across 10 cycles)**

| Condition | Service               | F1 (mean ± std) |
|-----------|-----------------------|-----------------|
| Seen      | Weebly                | 0.8648 ± 0.0504 |
| Seen      | Blogspot              | 0.8739 ± 0.0653 |
| Seen      | Wix                   | 0.8636 ± 0.0391 |
| Seen      | Google Sites          | 0.7684 ± 0.0668 |
| Seen      | GitHub Pages          | 0.8879 ± 0.0545 |
| Unseen    | Vercel                | 0.8453 ± 0.0665 |
| Unseen    | Webflow               | 0.8368 ± 0.0572 |
| Unseen    | Netlify               | 0.8435 ± 0.0666 |
| Unseen    | Strikingly            | 0.7315 ± 0.0356 |
| Unseen    | Azure Static Web Apps | 0.7537 ± 0.0391 |

### S1.5.4 Distributional Comparison

Comparing the per-service F1 distributions across the three methods
highlights the qualitative difference noted in S1.4.4:

- **FreePhish**: Seen-service F1 spans [0.33, 1.00] and Unseen-service
  F1 spans [0.00, 0.59]. The two distributions barely overlap; the
  poorest Seen service (Wix, 0.33) is comparable to mid-range Unseen
  services, while the best Unseen service (Vercel, 0.59) remains
  below the median Seen service.

- **Proposed method (GPT-4.1-mini)**: Seen-service F1 spans
  [0.93, 1.00] and Unseen-service F1 spans [0.91, 1.00]. The two
  distributions are almost completely overlapping. Notably, one
  Unseen service (Netlify, 1.00) achieves perfect F1, matching
  the best Seen services.

- **Proposed method (Qwen3-8B)**: Seen-service F1 spans [0.77, 0.89]
  and Unseen-service F1 spans [0.73, 0.85]. The two distributions
  substantially overlap, although the overlap is less complete than
  under GPT-4.1-mini. The best Unseen services (Vercel and
  Netlify, both around 0.84) exceed the worst Seen service
  (Google Sites, 0.77).

---

## S1.6 Limitations

This analysis has the following limitations:

1. **Sample size**: With only 10 runs per method, the statistical
   power for detecting small effects is limited, and rare extreme
   patterns may not be observed. We mitigate this concern by
   reporting effect sizes and absolute differences, which do not
   depend on statistical power in the same way as *p*-values.

2. **Service coverage**: The 5 Seen and 5 Unseen services represent
   a small slice of the broader space of shared-domain hosting
   services. Generalization of this analysis to other services is
   not directly tested.

3. **LLM coverage**: The proposed method was evaluated under two LLM
   configurations (GPT-4.1-mini and Qwen3-8B). Behavior with other
   LLMs may differ from the patterns reported here.

4. **Test choice**: We chose the paired t-test for its alignment with
   the data structure and hypothesis. Other paired tests (e.g., the
   Wilcoxon signed-rank test) could provide a nonparametric robustness
   check.

These limitations do not affect the validity of the main conclusion
that the magnitude of the Seen-vs-Unseen difference is fundamentally
different between ML-based and LLM-based approaches.

---

## References

- Saha Roy, S., et al. (2023). Phishing in the Free Waters: A Study
  of Phishing Attacks Created using Free Website Building Services.
  *Proceedings of the 2023 ACM on Internet Measurement Conference
  (IMC '23)*, 268-281. https://doi.org/10.1145/3618257.3624812