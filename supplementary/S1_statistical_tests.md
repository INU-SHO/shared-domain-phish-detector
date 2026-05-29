# S1. Statistical Comparison of Seen vs Unseen Performance: ML-based vs LLM-based

This document supplements the main paper "Detecting Phishing on
Shared-Domain Hosting Services Using LLM-Based Contextual Mismatch
Reasoning" (ARES 2026) with a statistical comparison of the
Seen-vs-Unseen performance gap between the ML-based baseline
(FreePhish) and our proposed LLM-based method.

---

## S1.1 Motivation

A central claim of this paper is that LLM-based detection methods,
which do not rely on training data of target services, exhibit a
fundamentally different generalization behavior compared to ML-based
methods that are trained on specific services. To support this claim
statistically, we compare the Seen-vs-Unseen F1 difference between
FreePhish [Saha Roy et al., 2023] (the ML-based baseline) and our
proposed method.

We address two related concerns raised in the review:

1. The need for **statistical tests** to assess the significance of
   the Seen vs Unseen difference.
2. The **limited sample size** (5 services per condition, 10 runs).

To partially address the second concern, we use a paired-by-run
analysis that increases statistical power by removing run-level
variance, and we report both **statistical significance** and
**effect size** to distinguish statistical from practical
significance.

---

## S1.2 Methodology

### S1.2.1 Choice of Test: Paired t-test

We use a **paired t-test** with the run (or training seed) as the unit
of analysis. Specifically, for each method:

- Each run produces a Seen-condition F1 and an Unseen-condition F1
  evaluated on the same model.
- The pair (Seen F1, Unseen F1) within a run is treated as a paired
  observation.
- The null hypothesis is `H0: Mean(Seen F1 - Unseen F1) = 0`.

We chose the paired t-test over an unpaired Welch's t-test on
per-service F1 (n=5 vs n=5) for three reasons:

1. **Data structure**: Within each run, the same model processes both
   Seen and Unseen services. The two F1 scores are therefore inherently
   paired, and a substantial portion of the run-to-run variability
   (e.g., LLM non-determinism, training stochasticity) affects both
   conditions identically.

2. **Hypothesis alignment**: Our hypothesis concerns the behavior of
   each *method* across the Seen/Unseen distinction. The natural unit
   of analysis is each evaluation run, not each individual service.

3. **Statistical power**: With only 5 services per condition, an
   unpaired service-level test (n=5 vs n=5) has very limited
   statistical power. The paired-by-run analysis (n=10 pairs)
   substantially improves power by removing the run-level variance
   from the comparison.

### S1.2.2 Effect Size: Cohen's d

To distinguish statistical significance from practical significance,
we compute **Cohen's d** for paired samples:

```
d = Mean(diff) / SD(diff)
```

where `diff = Seen F1 - Unseen F1` within each run.

Cohen's conventional benchmarks are:

| Cohen's d  | Interpretation       |
|------------|----------------------|
| d < 0.2    | negligible           |
| 0.2-0.5    | small                |
| 0.5-0.8    | medium               |
| 0.8-1.2    | large                |
| 1.2-2.0    | very large           |
| d > 2.0    | exceptionally large  |

### S1.2.3 Experimental Setup

- **Models compared**: FreePhish (ML-based), our proposed method (LLM-based, GPT-4.1-mini)
- **Dataset**: The Impersonation dataset (100 samples; 50 Seen, 50 Unseen) from the main paper
- **Number of runs**: 10 per method
  - FreePhish: 10 training seeds (training and prediction stochasticity)
  - Proposed: 10 evaluation cycles (LLM non-determinism)

---

## S1.3 Results

### S1.3.1 FreePhish (ML-based)

**Per-run F1 scores (10 training seeds):**

| Run            | Seen F1 | Unseen F1 | Diff (S-U) |
|----------------|--------:|----------:|-----------:|
| pred_seed_01   |  0.6667 |    0.4444 |    +0.2222 |
| pred_seed_02   |  0.6486 |    0.3871 |    +0.2616 |
| pred_seed_03   |  0.5946 |    0.3636 |    +0.2310 |
| pred_seed_04   |  0.7000 |    0.4865 |    +0.2135 |
| pred_seed_05   |  0.6111 |    0.4706 |    +0.1405 |
| pred_seed_06   |  0.5556 |    0.3636 |    +0.1919 |
| pred_seed_07   |  0.6667 |    0.4118 |    +0.2549 |
| pred_seed_08   |  0.7907 |    0.4211 |    +0.3696 |
| pred_seed_09   |  0.6842 |    0.4118 |    +0.2724 |
| pred_seed_10   |  0.7000 |    0.4324 |    +0.2676 |
| **mean ± std** | **0.6618 ± 0.0655** | **0.4193 ± 0.0412** | **+0.2425 ± 0.0601** |

**Paired t-test result:**

- t = 12.7527, df = 9
- two-tailed *p* < 0.0001
- one-tailed *p* < 0.0001

**Effect size:**

- Cohen's d = 0.2425 / 0.0601 ≈ **4.03** (exceptionally large)

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

- Cohen's d = 0.0128 / 0.0176 ≈ **0.73** (medium-to-large)

### S1.3.3 Summary Comparison

**Table S1.1: Statistical comparison of Seen vs Unseen F1**

| Method                        | Seen F1         | Unseen F1       | Δ (Seen − Unseen) | Paired t   | *p* (two-tailed) | Cohen's d  |
|-------------------------------|-----------------|-----------------|-------------------|-----------:|-----------------:|-----------:|
| FreePhish (ML-based)          | 0.6618 ± 0.0655 | 0.4193 ± 0.0412 | **+0.2425 ± 0.0601** |    12.7527 |        < 0.0001  | **4.03**   |
| Proposed (LLM-based, GPT-4.1-mini) | 0.9691 ± 0.0097 | 0.9562 ± 0.0152 | **+0.0128 ± 0.0176** |     2.3079 |          0.0464  | **0.73**   |

The test script and raw output are available at
[`./scripts/paired_ttest.py`](./scripts/paired_ttest.py).

---

## S1.4 Interpretation

### S1.4.1 Both Methods Show Statistically Significant Differences

Strictly speaking, the paired t-test rejects the null hypothesis
(*p* < 0.05) for **both** methods. Thus, neither method can be said
to have *literally* no difference between Seen and Unseen
performance.

However, statistical significance alone is uninformative about the
**magnitude** of the difference, especially with small variance.
Below we compare the two methods through three complementary lenses:
absolute difference, effect size, and qualitative behavior.

### S1.4.2 The Magnitude of the Difference Differs by Approximately 19-fold

The mean Seen-vs-Unseen difference is:

- FreePhish: **Δ F1 = +0.2425** (Seen substantially higher)
- Proposed: **Δ F1 = +0.0128** (Seen slightly higher)

In absolute terms, FreePhish's gap is approximately **19 times
larger** than the proposed method's gap. For FreePhish, this gap
represents a 24-percentage-point drop in F1 when moving from Seen
to Unseen services—a clear and practically meaningful performance
degradation. For the proposed method, the gap of 1.3 percentage
points is at or below the scale of run-to-run fluctuation in F1.

### S1.4.3 Effect Sizes Differ by Approximately 5.5-fold

In standardized units (Cohen's d):

- FreePhish: **d = 4.03** (exceptionally large)
- Proposed: **d = 0.73** (medium-to-large)

While both effect sizes are non-trivial, FreePhish's effect size is
in the "exceptionally large" range (d > 2.0), well beyond any
conventional benchmark, whereas the proposed method's effect size
falls in the "medium-to-large" range. The ratio is approximately
5.5-fold.

### S1.4.4 Qualitative Behavior: Distributional Overlap

Examining the per-run F1 distributions:

- For **FreePhish**, the Seen-condition F1 range across runs
  ([0.5556, 0.7907]) and the Unseen-condition F1 range
  ([0.3636, 0.4865]) are **completely disjoint**. Every run's
  Seen F1 is strictly higher than every run's Unseen F1.

- For the **proposed method**, the Seen-condition F1 range
  ([0.9615, 0.9804]) and the Unseen-condition F1 range
  ([0.9434, 0.9804]) **overlap almost entirely**. In one run, the
  Unseen F1 even exceeds the Seen F1.

This qualitative contrast—complete separation versus near-complete
overlap—reflects the fundamental difference between training-based
and training-free approaches.

### S1.4.5 Conclusion

We conclude that:

1. The ML-based baseline FreePhish exhibits a substantial,
   statistically significant, and practically meaningful
   generalization gap between training-included (Seen) and
   training-excluded (Unseen) services. This is consistent with the
   expected behavior of a method that learns service-specific
   patterns from its training data.

2. Our proposed LLM-based method shows a statistically detectable
   but practically marginal difference between Seen and Unseen
   services—approximately 19 times smaller in absolute terms and
   5.5 times smaller in effect size compared to FreePhish. This is
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
| Seen      | weebly                 | 0.5179 ± 0.1387 |
| Seen      | blogspot               | 1.0000 ± 0.0000 |
| Seen      | wix                    | 0.3321 ± 0.2242 |
| Seen      | google sites           | 0.6270 ± 0.1858 |
| Seen      | github pages           | 0.5943 ± 0.1845 |
| Unseen    | vercel                 | 0.5933 ± 0.1072 |
| Unseen    | webflow                | 0.4048 ± 0.1150 |
| Unseen    | netlify                | 0.3476 ± 0.0811 |
| Unseen    | strikingly             | 0.0000 ± 0.0000 |
| Unseen    | azure static web apps  | 0.5371 ± 0.1656 |

### S1.5.2 Proposed Method (GPT-4.1-mini)

**Table S1.3: Per-service F1 for the proposed method (mean ± std across 10 cycles)**

| Condition | Service                | F1 (mean ± std) |
|-----------|------------------------|-----------------|
| Seen      | weebly                 | 1.0000 ± 0.0000 |
| Seen      | blogspot               | 1.0000 ± 0.0000 |
| Seen      | wix                    | 0.9273 ± 0.0383 |
| Seen      | google sites           | 0.9273 ± 0.0383 |
| Seen      | github pages           | 1.0000 ± 0.0000 |
| Unseen    | vercel                 | 0.9909 ± 0.0287 |
| Unseen    | webflow                | 0.9636 ± 0.0469 |
| Unseen    | netlify                | 1.0000 ± 0.0000 |
| Unseen    | strikingly             | 0.9273 ± 0.0383 |
| Unseen    | azure static web apps  | 0.9091 ± 0.0000 |


### S1.5.3 Distributional Comparison

Comparing the per-service F1 distributions between FreePhish and the
proposed method highlights the qualitative difference noted in S1.4.4:

- **FreePhish**: Seen-service F1 spans [0.33, 1.00] and Unseen-service
  F1 spans [0.00, 0.59]. The two distributions barely overlap; the
  poorest Seen service (wix, 0.33) is comparable to mid-range Unseen
  services, while the best Unseen service (vercel, 0.59) remains
  below the median Seen service.

- **Proposed method**: Seen-service F1 spans [0.93, 1.00] and
  Unseen-service F1 spans [0.91, 1.00]. The two distributions are
  almost completely overlapping. Notably, one Unseen service
  (netlify.app, 1.00) achieves perfect F1, matching the best Seen
  services.

Per-service confusion matrices are omitted because each service is
evaluated on only 10 samples, making per-service 2x2 cell counts
highly volatile across runs. Per-service F1 with standard deviation
provides a more stable summary of per-service behavior at this
sample size.

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

3. **Single LLM in main comparison**: The proposed method's
   comparison uses GPT-4.1-mini. Behavior with other LLMs (e.g.,
   smaller open-source models) may differ; preliminary results with
   Qwen3-8B suggest that smaller models may exhibit a somewhat larger
   Seen-vs-Unseen difference, though still substantially smaller than
   FreePhish.

4. **Test choice**: We chose the paired t-test for its alignment with
   the data structure and hypothesis. Nonparametric alternatives
   (Wilcoxon signed-rank test) yield qualitatively consistent
   conclusions.

These limitations do not affect the validity of the main conclusion
that the magnitude of the Seen-vs-Unseen difference is fundamentally
different between ML-based and LLM-based approaches.

---

## References

- Saha Roy, S., Karanjit, U., & Nilizadeh, S. (2023). Phishing in the
  Free Waters: A Study of Phishing Attacks Created using Free Website
  Building Services. *Proceedings of the 2023 ACM on Internet
  Measurement Conference (IMC '23)*, 268-281.
  https://doi.org/10.1145/3618257.3624812