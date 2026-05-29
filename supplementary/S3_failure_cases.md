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

The main paper presents a single qualitative case study to
illustrate how the Brand Analyzer, Content Analyzer, and Judge
interact when making a decision. Due to page-limit constraints, we
were unable to include further qualitative examples in the main
text. This supplementary document complements the main case study
by presenting additional cases — specifically, the failure cases
observed in our evaluation — together with the raw per-component
outputs that led to each misjudgment.

We focus on failure cases rather than successes because failures
are diagnostic: they reveal the conditions under which the
pipeline's reasoning departs from the ground truth and thus suggest
concrete directions for future improvement.

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

### S3.3.1 Case FP-G1: Vendor Support Page

**Page type.** A corporate support page belonging to NCR Voyix, a
provider of digital commerce solutions (POS, payments, etc.). The
page is a legitimate vendor-operated portal that aggregates
navigation to customer login (MyNCR), developer resources,
documentation, and invoice payment. It happens to be hosted on a
Microsoft Azure Static Web Apps subdomain rather than the company's
primary domain.

**Per-component outputs.**

- **Brand Analyzer**

```
"brand_report": {"is_brand": true, "brand_name": "NCR Voyix", "brand_popularity": "low"}
```

- **Content Analyzer**

```
"content_report": {"summary": "This appears to be a corporate support information page for NCR Voyix Corporation, providing access links to customer login, developer portal, information products, and additional support resources. It mainly offers navigation to resources and portals without direct forms on this page.", "page_structure": "The page has a well-structured navigation bar with categorized dropdown menus for Restaurant, Retail, Banking, and Company information. The main section includes tiles with images and descriptive texts linking to external or internal portals. No obvious structural anomalies are evident from the available snippet and screenshot wordlist.", "sensitive_action_prompting": "Prompted action: authentication/credential entry. Mechanism: prominent navigational links directing users to login portals. Evidence: button labeled 'Access log in' linking to 'https://mylogin.ncr.com/', also screenshot shows 'Login to MyNCR', 'Sign into MyNCR to access customer information'. Additionally, a 'Pay now' link leads to an invoice payment portal, which prompts payment action. Thus, payment action is also prompted."}
```

- **Judge**

```
"final_verdict": "malicious", "rationale": ["The page indicates a specific brand, NCR Voyix, hosted on a free web hosting apex domain, which raises suspicion as per the context for brand impersonation attempts on free hosting.", "There are explicit prompts for sensitive actions including authentication via navigational links to login portals and a 'Pay now' link leading to a payment action, which meets criteria for malicious classification due to steering towards credential entry and payment transfer."]
```

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

### S3.3.2 Case FP-G2: Franchise Internal Team Page

**Page type.** A Google Sites page operated by an individual
Chick-fil-A franchise (Chick-fil-A Buda) as an internal
welcome / onboarding resource for its team members. The page
contains corporate values, leadership development resources, and
benefits information, but does not solicit credentials or payment
from external visitors.

**Per-component outputs.**

- **Brand Analyzer**

```
"brand_report": {"is_brand": true, "brand_name": "Chick-fil-A", "brand_popularity": "high"}
```

- **Content Analyzer**

```
"content_report": {"summary": "This appears to be a corporate or organizational informational website for Chick-fil-A Buda, providing team welcome messages, company history, leadership development resources, and benefits information. It invites users to explore various sections about vision, values, and growth opportunities but does not appear to request direct user input or actions beyond navigation.", "page_structure": "The page has a typical corporate informational website structure with a fixed navigation menu on the left side including multiple nested sections and subpages related to company vision, leadership development, benefits, and resources. The content sections are well-organized with headings, paragraphs, and images, and include some interactive elements like expandable menus. There is no indication of structural anomalies or suspicious inconsistencies.", "sensitive_action_prompting": "Nothing in particular"}
```

- **Judge**

```
"final_verdict": "suspicious", "rationale": ["The website indicates a well-known brand, Chick-fil-A, hosted on a free web hosting apex domain google.com, which inherently signals suspicion according to the analysis context.", "Despite the absence of sensitive-action prompting and structural anomalies, the presence of a well-known brand on a free-hosted domain is considered a risk factor and thus renders the site suspicious rather than benign."]
```

**Why it failed.** This case exposes the conservative bias of the
Judge in the absence of disambiguating signals. The Content
Analyzer correctly observed that nothing actionable is asked of the
visitor, but the Judge's heuristic treats "well-known brand on free
hosting" as sufficient grounds for "suspicious". In reality,
franchise- or location-specific internal pages are a recurring
legitimate use case for shared-domain hosting (Google Sites in
particular), and the pipeline currently has no way to recognize
this pattern.

### S3.3.3 Case FP-G3: Product Promotion Page

**Page type.** A promotional landing page for SNAP Apple Cider
Vinegar Gummies, a dietary supplement product. The page is hosted
on a `mystrikingly.com` subdomain and contains product description,
benefits, usage information, and "Shop Now" / "Submit" buttons that
link to an external e-commerce site for purchase.

**Per-component outputs.**

- **Brand Analyzer**

```
"brand_report": {"is_brand": true, "brand_name": "SNAP Apple Cider Vinegar Gummies", "brand_popularity": "low"}
```

- **Content Analyzer**

```
"content_report": {"summary": "This appears to be a promotional product webpage for SNAP Apple Cider Vinegar Gummies, describing the product's benefits, composition, usage, and where to buy it, with calls to action directing users to an external website for purchase.", "page_structure": "The page has a typical product landing page structure with a navigation menu, product title and image, extensive product information sections, and multiple links to external purchase pages. There are no obvious structural anomalies based on the provided DOM and screenshot wordlist.", "sensitive_action_prompting": "Prompted action: payment/purchase. Mechanism: prominent links and buttons labeled 'Submit' and 'Shop Now Special Offer' linking to external purchasing websites. Evidence: DOM contains multiple anchor links to 'perfecthealthtalk.com/get_snap-apple-cider-vinegar-gummies' and button labeled 'Submit'; screenshot shows phrases like 'Submit', 'Shop Now Special Offer', and product purchase related wording."}
```

- **Judge**

```
"final_verdict": "malicious", "rationale": ["The website indicates a specific brand named 'SNAP Apple Cider Vinegar Gummies' hosted on a free web hosting domain mystrikingly.com, which is a risk signal as such brand indication on free hosted pages is inherently suspicious.", "The page prompts a sensitive-action related to payment/purchase with multiple prominent links and buttons labeled 'Submit' and 'Shop Now Special Offer' leading to external purchase websites, which combined with the brand indication and hosting context, justifies labeling it malicious."]
```

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

### S3.4.1 Case FP-Q1: Advocacy / Service Promotion Page

**Page type.** A promotional page for CognetZap, a service related
to internet censorship advocacy/circumvention. The page describes
the project's mission and provides navigation to "Home", "About",
"Zap", and contribution sections. The page is hosted on a
`vercel.app` subdomain.

**Per-component outputs.**

- **Brand Analyzer**

```
"brand_report": {"is_brand": true, "brand_name": "CognetZap", "brand_popularity": "uncertain"}
```

- **Content Analyzer**

```
"content_report": {"summary": "Promotional/mission page for CognetZap, appears to focus on internet censorship advocacy and service promotion. Contains links to Home, About, Zap, and contribution sections.", "page_structure": "Multiple links with identical IDs ('items') and repeated 'About' navigation entries suggest potential structural inconsistencies. Excessive use of absolute positioning and hidden elements may indicate unusual layout patterns.", "sensitive_action_prompting": "Nothing in particular"}
```

- **Judge**

```
"final_verdict": "suspicious", "rationale": ["The page structure contains repeated 'About' navigation entries and identical IDs ('items'), which suggest potential obfuscation techniques commonly associated with phishing attempts.", "A brand named 'CognetZap' is presented on a free web hosting domain (vercel.app), which is context-anomalous and warrants scrutiny despite the absence of direct sensitive-action prompts."]
```

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

### S3.4.2 Case FP-Q2: Vendor Support Page (same URL as FP-G1)

This is the same NCR Voyix support page described in S3.3.1.
Qwen3-8B reaches the same conclusion as GPT-4.1-mini, with very
similar per-component outputs.

**Per-component outputs.**

- **Brand Analyzer**

```
"brand_report": {"is_brand": true, "brand_name": "NCR Voyix", "brand_popularity": "low"}
```

- **Content Analyzer**

```
"content_report": {"summary": "Support page for NCR Voyix Corporation, appears to provide information and links to login portals, developer resources, and payment options.", "page_structure": "Navigation menu with sections for Restaurant, Retail, Banking, and Company, containing multiple sub-links organized under headings. Layout appears typical with repeated navbar overlays and standard section grouping. No obvious structural anomalies detected.", "sensitive_action_prompting": "Prompted action: authentication/credential entry. Mechanism: visible login CTA. Evidence: 'Login to MyNCR' section with 'Access log in' button; screenshot shows 'Sign into MyNCR to access customer information'. Prompted action: payment/money transfer. Mechanism: explicit CTA. Evidence: 'Pay your invoice' section with 'Pay now' button; screenshot shows 'Pay now' button text."}
```

- **Judge**

```
"final_verdict": "malicious", "rationale": ["The page contains a visible login CTA ('Login to MyNCR') with explicit credential entry prompts, matching security-sensitive action inventory item 1.", "Payment/money transfer is explicitly prompted via 'Pay now' button in a dedicated section, matching security-sensitive action inventory item 4."]
```

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

- **Brand Analyzer**

```
"brand_report": {"is_brand": false, "brand_name": "uncertain", "brand_popularity": "uncertain"}
```

- **Content Analyzer**

```
"content_report": {"summary": "A sign-up page for a streaming service (likely Netflix) prompting the user to finish sign-up.", "page_structure": "The layout is typical with sections for features, FAQs, and contact info. No structural anomalies detected.", "sensitive_action_prompting": "Nothing in particular"}
```

- **Judge**

```
"final_verdict": "benign", "rationale": ["The page structure shows no structural anomalies, with typical sections for features, FAQs, and contact info that align with legitimate sign-up pages.", "No sensitive-action prompting was identified, and the content does not include authentication fields or cryptocurrency wallet interaction cues."]
```

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