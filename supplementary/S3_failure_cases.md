# S3. Failure Case Analysis

This document supplements the main paper "Detecting Phishing on
Shared-Domain Hosting Services Using LLM-Based Contextual Mismatch
Reasoning" (ARES 2026) with a structured analysis of failure cases
observed in our experiments. We present six representative cases
(three false positives for GPT-4.1-mini, two false positives and
one false negative for Qwen3-8B), showing the per-component outputs
of our pipeline (Brand Analyzer, Content Analyzer, Judge) and
discussing why each case led to a misjudgment.

---

## S3.1 Motivation

A reviewer pointed out that the qualitative case study in the main
paper presents only a single example, and suggested that a
structured comparison of Content/Judge outputs across multiple
failure cases would strengthen the analysis. This document responds
to that suggestion by presenting the per-component outputs and a
short interpretation for each failure case.

We focus on failures rather than successes because failures are
diagnostic: they reveal the conditions under which the pipeline's
reasoning departs from the ground truth and thus suggest concrete
directions for future improvement.

---

## S3.2 Case Selection Criteria

Cases were selected from the 10-run evaluation on the Impersonation
dataset (100 samples) using the following criteria:

- **GPT-4.1-mini, false positives (3 cases)**: Among the false
  positives observed in any of the 10 runs, we selected the three
  benign URLs that were misclassified in **all 10 runs**.
  GPT-4.1-mini produced no false negatives across the 10 runs, so
  no false negative case is reported for this model.

- **Qwen3-8B, false positives (2 cases)**: We selected the two
  benign URLs that were misclassified in **all 10 runs**.

- **Qwen3-8B, false negative (1 case)**: The pipeline produced a
  false negative on **one** malicious URL across the 10 runs. The
  case we report below is that URL; it was misclassified in **4 of
  the 10 runs**, and was the only malicious sample on which any
  false negative occurred in this experiment.

To preserve dataset privacy (the dataset is not yet publicly
released), we do not disclose URLs, DOM contents, or screenshots.
Each case is labeled with an anonymized identifier (FP-G1, FP-G2,
... ; FP-Q1, FP-Q2, ... ; FN-Q1) and described in terms of the
type of web page involved.

---

## S3.3 False Positives — GPT-4.1-mini

### S3.3.1 Case FP-G1: Vendor Support Page on a Free-Hosting Domain

**Page type.** A corporate support page belonging to NCR Voyix, a
provider of digital commerce solutions (POS, payments, etc.). The
page is a legitimate vendor-operated portal that aggregates
navigation to customer login (MyNCR), developer resources,
documentation, and invoice payment. It happens to be hosted on a
Microsoft Azure Static Web Apps subdomain rather than the company's
primary domain.

**Per-component outputs.**

- **Brand Analyzer**: `is_brand = true`, `brand_name = "NCR Voyix"`,
  `brand_popularity = "low"`.
- **Content Analyzer**: Identified two sensitive-action prompts:
  (i) authentication / credential entry via the "Login to MyNCR"
  call-to-action, and (ii) payment / money transfer via the "Pay
  now" button. No structural anomalies were noted.
- **Judge**: `final_verdict = "malicious"`. Rationale: a low-
  popularity brand hosted on a free-hosting apex domain, combined
  with explicit prompts for both credential entry and payment.

**Why it failed.** The Judge's reasoning is internally consistent
with the pipeline's heuristics: NCR Voyix is not in the long tail
of household-name brands, the hosting domain is a free web app
service rather than a corporate domain, and the page actively
solicits both credentials and payment. Each individual signal is a
real risk indicator. The misjudgment arises from the absence of a
positive signal that would establish *vendor legitimacy* —
specifically, the page genuinely belongs to the brand it claims to
represent. The pipeline currently lacks a mechanism to verify this
positive linkage, and so it treats the combination of signals as
sufficient evidence of impersonation.

### S3.3.2 Case FP-G2: Franchise/Restaurant Internal Team Page on a Free-Hosting Domain

**Page type.** A Google Sites page operated by an individual
Chick-fil-A franchise (Chick-fil-A Buda) as an internal
welcome / onboarding resource for its team members. The page
contains corporate values, leadership development resources, and
benefits information, but does not solicit credentials or payment
from external visitors.

**Per-component outputs.**

- **Brand Analyzer**: `is_brand = true`,
  `brand_name = "Chick-fil-A"`, `brand_popularity = "high"`.
- **Content Analyzer**: A standard informational layout with a
  navigation menu and content sections. No structural anomalies
  and no sensitive-action prompting were identified.
- **Judge**: `final_verdict = "suspicious"`. Rationale: a
  well-known brand appearing on a free-hosting apex domain
  (google.com / sites.google.com) is treated as inherently
  context-anomalous, and the Judge declines to label such a page
  benign even in the absence of sensitive-action prompting.

**Why it failed.** This case exposes the conservative bias of the
Judge in the absence of disambiguating signals. The Content
Analyzer correctly observed that nothing actionable is asked of the
visitor, but the Judge's heuristic treats "well-known brand on free
hosting" as sufficient grounds for "suspicious". In reality,
franchise- or location-specific internal pages are a recurring
legitimate use case for shared-domain hosting (Google Sites in
particular), and the pipeline currently has no way to recognize
this pattern.

### S3.3.3 Case FP-G3: Product Promotion Page on a Free-Hosting Domain

**Page type.** A promotional landing page for SNAP Apple Cider
Vinegar Gummies, a dietary supplement product. The page is hosted
on a `mystrikingly.com` subdomain and contains product description,
benefits, usage information, and "Shop Now" / "Submit" buttons that
link to an external e-commerce site for purchase.

**Per-component outputs.**

- **Brand Analyzer**: `is_brand = true`,
  `brand_name = "SNAP Apple Cider Vinegar Gummies"`,
  `brand_popularity = "low"`.
- **Content Analyzer**: Identified a payment/purchase prompt via
  prominent "Shop Now Special Offer" and "Submit" buttons linking
  to an external purchasing URL. No structural anomalies.
- **Judge**: `final_verdict = "malicious"`. Rationale: low-
  popularity brand on a free-hosting apex domain + explicit
  payment/purchase prompting.

**Why it failed.** Conceptually similar to FP-G1: the pipeline
correctly identifies risk indicators (low-popularity brand, free
hosting, prompts that move the user toward a financial action) but
cannot distinguish between (a) impersonation of a real brand for
phishing, and (b) a small/niche brand that legitimately uses
free-hosting services for product promotion. The "Shop Now" button
is structurally identical to a malicious payment redirect, and the
free-hosting domain is structurally identical to a typical phishing
infrastructure choice.

---

## S3.4 False Positives — Qwen3-8B

### S3.4.1 Case FP-Q1: Advocacy / Service Promotion Page on a Free-Hosting Domain

**Page type.** A promotional page for CognetZap, a service related
to internet censorship advocacy/circumvention. The page describes
the project's mission and provides navigation to "Home", "About",
"Zap", and contribution sections. The page is hosted on a
`vercel.app` subdomain.

**Per-component outputs.**

- **Brand Analyzer**: `is_brand = true`, `brand_name = "CognetZap"`,
  `brand_popularity = "uncertain"`.
- **Content Analyzer**: Flagged structural irregularities, including
  repeated "About" navigation entries and duplicated element IDs
  (`items`). These were interpreted as "potential obfuscation
  techniques commonly associated with phishing attempts". No
  sensitive-action prompting was identified.
- **Judge**: `final_verdict = "suspicious"`. Rationale: brand on a
  free-hosting apex domain is context-anomalous, and the structural
  irregularities flagged by the Content Analyzer warrant scrutiny
  despite the absence of direct sensitive-action prompts.

**Why it failed.** The case illustrates two challenges. First, the
Brand Analyzer is uncertain about an unknown small-scale brand, and
the pipeline treats this uncertainty conservatively. Second, the
Content Analyzer's interpretation of duplicated DOM identifiers
("potential obfuscation") is plausible in the abstract but in this
case reflects ordinary developer practice on a small project rather
than an evasion attempt. The Judge then aggregates these two
relatively weak signals into a "suspicious" verdict despite the
lack of any sensitive-action prompting that would normally be
expected of an impersonation page.

### S3.4.2 Case FP-Q2: Vendor Support Page on a Free-Hosting Domain (same URL as FP-G1)

This is the same NCR Voyix support page described in S3.3.1.
Qwen3-8B reaches the same conclusion as GPT-4.1-mini, with very
similar per-component outputs:

- **Brand Analyzer**: `is_brand = true`,
  `brand_name = "NCR Voyix"`, `brand_popularity = "low"`.
- **Content Analyzer**: Identified the same two sensitive-action
  prompts: authentication via "Login to MyNCR" and payment via
  "Pay now" button.
- **Judge**: `final_verdict = "malicious"`. Rationale identical in
  substance to S3.3.1.

**Why it failed.** The same underlying issue as FP-G1 applies: the
combination of a low-popularity brand, free-hosting infrastructure,
and explicit credential and payment prompts cannot, in the present
pipeline, be distinguished from a genuine impersonation page. The
fact that two independently behaving LLMs reach the same wrong
conclusion on this URL suggests that the failure is not specific to
either model but reflects a limitation of the heuristics encoded in
the pipeline's prompts.

---

## S3.5 False Negative — Qwen3-8B

### S3.5.1 Case FN-Q1: Phishing Sign-up Page Mimicking a Major Streaming Service

**Page type.** A phishing page hosted on a `netlify.app` subdomain
that imitates the sign-up flow of a major streaming service
(Netflix). The page presents typical sign-up sections (features,
FAQs, contact information) and prompts the visitor to "finish
sign-up", but is malicious (the goal is to harvest the user's
information through what appears to be a legitimate streaming
service sign-up form).

**Per-component outputs.**

- **Brand Analyzer**: `is_brand = false`, `brand_name = "uncertain"`,
  `brand_popularity = "uncertain"`. **The model failed to identify
  the impersonated brand (Netflix).**
- **Content Analyzer**: Described the page as a typical sign-up
  page for a streaming service. Reported no structural anomalies
  and no sensitive-action prompting; in particular, the sign-up
  flow itself was not flagged as a credential-entry prompt.
- **Judge**: `final_verdict = "benign"`. Rationale: no structural
  anomalies, no sensitive-action prompts, no clear brand
  indication.

**Why it failed.** Two compounding errors led to the false
negative. First, the Brand Analyzer did not recognize the
impersonated brand even though the page text and styling are
clearly Netflix-themed; without a brand attribution, the
"impersonation on a free-hosting domain" check has no anchor.
Second, the Content Analyzer did not flag the sign-up form itself
as a credential-entry / personal-information prompt — its summary
mentions "finish sign-up" but does not classify this as a
sensitive action. Both errors are plausibly attributable to the
smaller model's weaker visual and contextual reasoning on
brand-related cues, since the same dataset is handled correctly by
GPT-4.1-mini in this case.

Notably, this is the **only** malicious sample on which Qwen3-8B
produced a false negative in our 10-run evaluation, and the error
was not consistent: the pipeline misclassified this sample in 4
of the 10 runs and classified it correctly in the remaining 6,
reflecting the run-to-run non-determinism of LLM-based pipelines.

---

## S3.6 Discussion

Looking across the six cases, several patterns emerge.

**Pattern 1: Legitimate small-scale or franchise/branch use of
free hosting is the dominant source of false positives.** All five
false-positive cases (FP-G1, FP-G2, FP-G3, FP-Q1, FP-Q2) involve
benign pages where a real (but small or location-specific) entity
legitimately uses a shared-domain hosting service. The pipeline's
core heuristic — "real brand on free hosting + signals suggestive
of a sensitive flow → suspicious or malicious" — is broadly correct
for genuine impersonation attacks but does not differentiate
sufficiently between impersonation and legitimate niche usage. This
suggests a future direction of incorporating a positive-evidence
check for vendor / franchise legitimacy.

**Pattern 2: Identical failures on the same URL across models
indicate a pipeline-level limitation, not a model-level one.**
Cases FP-G1 and FP-Q2 are the same URL misclassified by two
different LLMs with very similar per-component reasoning. The
failure therefore cannot be resolved simply by switching to a
stronger LLM; it reflects how the available signals are combined in
the Judge's prompt.

**Pattern 3: The false negative reveals a different failure mode:
brand non-recognition.** In contrast to the false positives, the
false negative (FN-Q1) is driven by the Brand Analyzer failing to
identify a major impersonated brand (Netflix). Without that
identification, the rest of the pipeline has no contextual mismatch
to reason about. This failure mode is specific to weaker LLMs in
our experiments and does not occur with GPT-4.1-mini on the same
data.

---

## S3.7 Limitations

This case analysis has the following limitations.

1. **Small number of cases.** Six cases are insufficient to
   characterize the full distribution of failure modes. The cases
   are selected for being representative of consistent or
   near-consistent errors and should not be read as a complete
   taxonomy.

2. **No external validation of the per-component outputs.** The
   per-component outputs reported here are the raw outputs of the
   Brand / Content / Judge components for the case in question; we
   do not independently audit whether each component's reasoning is
   "well-formed" beyond its conclusion.

3. **Dataset privacy.** Because the dataset is not yet publicly
   released, we describe each case in terms of page type and
   component outputs rather than disclosing URLs, DOM contents, or
   screenshots. This limits the ability of external readers to
   verify our characterizations of the pages.

These limitations do not affect the qualitative observations
discussed in S3.6, but they constrain the strength of any
quantitative claim that could be drawn from this case analysis.