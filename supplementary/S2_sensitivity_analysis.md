# S2. Sensitivity Analysis: Impact of Reference Brand Selection

This document supplements the main paper "Detecting Phishing on
Shared-Domain Hosting Services Using LLM-Based Contextual Mismatch
Reasoning" (ARES 2026) with a sensitivity analysis on the choice of
reference brands used in the Brand Analyzer's popularity judgment.

---

## S2.1 Motivation

The Brand Analyzer estimates the popularity of the brand under analysis
by combining the LLM's internal knowledge with search hit counts of
well-known reference brands. In the main paper, three major global
telecommunications providers were used as reference brands. This raises
a natural question: how sensitive is the detection performance to the
choice of these reference brands?

We prepare three sets of reference brands, each drawn from a different
industry. We then conduct the experiment under two LLM configurations
(GPT-4.1-mini and Qwen3-8B) and, for each configuration, compare the
variation in detection accuracy caused by switching between the three
sets against the variation caused by LLM non-determinism within a
single set.

---

## S2.2 Experimental Setup

### S2.2.1 Industry Selection

We selected the three industries identified as the most frequently
targeted by phishing in the distribution chart reported in KnowPhish
[Li et al., 2024]: **Financial**, **Online Service**, and **Telecommunication**.

### S2.2.2 Reference Brand Selection

For each industry, we selected three representative brands whose
official websites rank within the **top 10,000 of the Tranco list**,
ensuring they are widely recognized.

**Table S2.1: Reference brands used for each industry**

| Industry | Brand | Domain | Total search results | Tranco rank |
| --- | --- | --- | --- | --- |
| Financial | PayPal | paypal.com | 81,800,000 | 155 |
| Financial | Visa | visa.com | 198,000,000 | 2,805 |
| Financial | HSBC | hsbc.com | 4,710,000 | 7,336 |
| Online Service | Microsoft | microsoft.com | 336,000,000 | 6 |
| Online Service | Google | google.com | 1,640,000,000 | 1 |
| Online Service | Apple | apple.com | 881,000,000 | 11 |
| Telecommunication | AT&T | att.com | 6,500,000 | 1,436 |
| Telecommunication | Verizon | verizon.com | 7,270,000 | 2,203 |
| Telecommunication | T-Mobile | t-mobile.com | 12,500,000 | 443 |

### S2.2.3 Evaluation Protocol

- **Models**: GPT-4.1-mini, Qwen3-8B
- **Dataset**: The Impersonation dataset (100 samples) from the main paper
- **Trials per industry**: 10 independent runs
- **Metrics**: Accuracy, Precision, Recall, F1-score

---

## S2.3 Results

### S2.3.1 Results with GPT-4.1-mini

**Table S2.2: Detection performance (GPT-4.1-mini, mean ± std, n=10 runs)**

| Industry | Accuracy | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| Financial | 0.9590 ± 0.0099 | 0.9245 ± 0.0173 | 1.0000 ± 0.0000 | 0.9607 ± 0.0093 |
| Online Service | 0.9620 ± 0.0103 | 0.9297 ± 0.0179 | 1.0000 ± 0.0000 | 0.9635 ± 0.0096 |
| Telecommunication | 0.9610 ± 0.0099 | 0.9279 ± 0.0173 | 1.0000 ± 0.0000 | 0.9625 ± 0.0093 |

### S2.3.2 Results with Qwen3-8B

**Table S2.3: Detection performance (Qwen3-8B, mean ± std, n=10 runs)**

| Industry | Accuracy | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| Financial | 0.7910 ± 0.0251 | 0.7076 ± 0.0236 | 0.9940 ± 0.0097 | 0.8265 ± 0.0183 |
| Online Service | 0.8090 ± 0.0300 | 0.7273 ± 0.0310 | 0.9920 ± 0.0103 | 0.8390 ± 0.0220 |
| Telecommunication | 0.7830 ± 0.0275 | 0.7008 ± 0.0261 | 0.9900 ± 0.0105 | 0.8205 ± 0.0200 |

### S2.3.3 Statistical Test

We conducted statistical tests on Accuracy as the representative metric.
The null hypothesis is that the three industry groups have the same
distribution of Accuracy values. We applied the **Kruskal-Wallis H-test**
as the primary test (non-parametric, robust to non-normality), and
**One-way ANOVA** as a cross-check.

**Table S2.4: Statistical test results (KW = Kruskal-Wallis)**

| Model | Range of means | Within-std (mean) | KW H | KW *p* | ANOVA F | ANOVA *p* |
| --- | --- | --- | --- | --- | --- | --- |
| GPT-4.1-mini | 0.0030 | 0.0101 | 0.5649 | 0.7539 | 0.2299 | 0.7961 |
| Qwen3-8B | 0.0260 | 0.0275 | 3.6735 | 0.1593 | 2.3254 | 0.1170 |

For both models, *p* > 0.05 in both tests; we fail to reject the null
hypothesis. **There is no statistically significant difference in
Accuracy among the three reference brand industries** in either model.

The test script and raw output are available at
[`./scripts/sensitivity_test.py`](./scripts/sensitivity_test.py).

---

## S2.4 Discussion

### S2.4.1 GPT-4.1-mini

The mean within-industry standard deviation of Accuracy (caused by
LLM non-determinism) is **0.0101**, while the range of mean Accuracy
across the three industries is only **0.0030**. The within-industry
variability is therefore approximately **3.36 times larger** than the
between-industry variation in means. Combined with the non-significant
Kruskal-Wallis result (*p* = 0.7539), the choice of reference brand
industry has limited impact on detection performance.

### S2.4.2 Qwen3-8B

The qualitative conclusion is the same, but the gap between within-
and between-industry variability is smaller. The within-industry
standard deviation (0.0275) and the range of mean Accuracy across
industries (0.0260) are of comparable magnitude. The Kruskal-Wallis
test still does not detect a significant difference (p = 0.1593),
but the effect is closer to the threshold than in GPT-4.1-mini.

### S2.4.3 Cross-Model Conclusion

Across both models, the conclusion is consistent: **the choice of
reference brand industry does not produce a statistically significant
difference in detection accuracy**, supporting the robustness of the
Brand Analyzer's design with respect to this particular configuration
choice.

---

## S2.5 Limitations

This sensitivity analysis has the following limitations:

1. **Industry coverage**: Only three industries (Financial, Online
Service, Telecommunication) were tested. Other industries,
especially those with lower brand recognition or more diverse
popularity distributions, are not covered.
2. **Brand popularity range**: All reference brands selected rank
within the top 10,000 of the Tranco list, representing globally
well-known companies. The effect of using less-recognized brands
as references remains unexplored.
3. **Sample size**: With 10 runs per industry, the statistical power
to detect small effects is limited. In particular, the
non-significant result for Qwen3-8B (p = 0.1593) does not
definitively rule out a small industry effect; a larger number of
runs would be needed to confirm this.
4. **Model coverage**: Only two LLMs (GPT-4.1-mini and Qwen3-8B) were
tested. Sensitivity patterns may differ for other LLMs.

These limitations suggest directions for future work but do not affect
the validity of the conclusion within the tested scope.

---

## References

- Li, Y., et al. (2024). KnowPhish: Large Language Models Meet
Multimodal Knowledge Graphs for Enhancing Reference-Based Phishing
Detection. *USENIX Security 2024*.
https://www.usenix.org/conference/usenixsecurity24/presentation/li-yuexin