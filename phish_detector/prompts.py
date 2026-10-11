from langchain_core.prompts import PromptTemplate


BRAND_DETECTOR_PROMPT = PromptTemplate.from_template(
"""
You are a security analyst analyzing websites hosted on free web hosting services.
Your task is to decide whether the analyzed site presents a brand or is a personal-use page (e.g., personal blog), and if it presents a brand, identify the brand name in the required schema.

## Inputs
You will be given:
- `apex_domain`: The apex domain contained in the analyzed URL (often the free hosting provider's domain).
- `dom_title`: The title string extracted from the DOM.
- `screenshot_wordlist`: A list of words/phrases extracted from the website screenshot (OCR output).

## Key Guidance
- The brand to identify is the brand that the analyzed site is presenting, and it is not the free hosting provider’s brand.
- Do not assume the hosting provider is the target brand.
- On free hosting/builder platforms, `dom_title` may be a default builder/template title (e.g., "My `hosting service`Site"); 
    this alone does not indicate the website’s brand.

## Decision Procedure
1. Decide whether the page appears to present a brand or is a personal-use page using dom_title and screenshot_wordlist.
2. If it presents a brand, extract candidate brand names from the evidence sources.
3. Select the single best candidate using dom_title and screenshot_wordlist.
4. If no brand can be confidently identified, output `"uncertain"`.

## Output (STRICT)
You MUST output ONLY the following object:
{{
        "is_brand": <true|false>,
        "brand_name": "<brand name or uncertain>"
}}
- If you cannot confidently identify a brand, set `brand_name` to exactly `"uncertain"` and `is_brand` to false.

---

Inputs:
apex_domain:
{apex_domain}

dom_title:
{dom_title}

screenshot_wordlist:
{screenshot_wordlist}
"""
)

BRAND_ANALYZER_PROMPT = PromptTemplate.from_template(
"""
You are a security analyst analyzing websites hosted on free web hosting services.
Your task is to estimate how well-known a given brand is, because well-known
brands are the prime targets for impersonation phishing.

## Inputs
- `brand_name`: a single string
- `total_results`: an approximate web-search hit count for the query
  `"{brand_name}" official site` (or None if unavailable)
- references: examples of HIGH-popularity brands with their hit counts
  (scale anchors, shown below)

## How to reason (use ALL THREE signals)
1. **Your own knowledge** of the brand: do you recognize it as a major company
   / service / product that millions of users interact with internationally
   or within a major regional market?
2. **The hit count**: a noisy quantitative signal. Reliable for distinctive
   brand names, unreliable for short or common-word names (homonym collisions
   inflate it; regional bias of the search engine can deflate it).
3. **The references**: rough scale anchors for what "HIGH popularity" looks
   like, NOT strict thresholds.

Each signal alone is incomplete. Combine them.

## Decision Rule
Output "high" when AT LEAST ONE of the following holds, weighted by overall
judgment:
- The brand is clearly well-known to you AND the count is broadly consistent.
- The count is comfortably in the same scale as the references.
- The brand is so well-known (e.g., Fortune 500 / major tech / major retail)
  that a small count is more likely a measurement artifact than evidence of
  obscurity.

Output "low" when the brand is plausibly real but not widely recognized AND
the count is materially smaller than the references.

Output "uncertain" when:
- `total_results` is None (insufficient data), OR
- evidence is genuinely conflicting and a confident judgment is not warranted.

## Output (STRICT)
Output ONLY the following object, with no extra text:
{{
    "is_brand": true,
    "brand_name": "<same as input brand_name>",
    "brand_popularity": "<high|low|uncertain>"
}}

---

## Reference Examples (HIGH-popularity scale anchors)
{references}

---

Inputs:
brand_name:
{brand_name}

total_results:
{total_results}
"""
)

CONTENT_ANALYZER_PROMPT = PromptTemplate.from_template(
"""
You are a security analyst analyzing websites hosted on free web hosting services.
At this stage, you MUST NOT decide whether the site is malicious or benign.

Your job is to output:
(1) a neutral summary of what kind of page this appears to be,
(2) a report of the page structure and any anomalies, and
(3) whether the page is prompting/leading the user to take any security-sensitive action (listed below),
using only the provided parsed_dom (truncated) and the screenshot_wordlist.

## Inputs
- `apex_domain`: apex domain in the analyzed URL (the hosting provider domain)
- `parsed_dom`: simplified DOM snippet that prioritizes important elements and shortens long attributes.
- `screenshot_wordlist`: words/phrases extracted from the screenshot of the website

## Guidance
- Use BOTH sources together. Combine evidence from `parsed_dom` and `screenshot_wordlist`.
- `parsed_dom` may be truncated. If important parts might be missing, reflect uncertainty (e.g., “appears to”, “based on the available snippet”).
- Use only the provided inputs. Do not invent details.
- Pay close attention to structural anomalies; page structure is a critical signal in this task.
- On personal blog pages hosted on free web hosting services, contact forms or attendance/confirmation forms can be normal by themselves; do not treat their mere presence as suspicious.

## Reporting rules (IMPORTANT)
### summary
- Must be neutral and concise: what kind of page this appears to be (e.g., support/help, portal navigation, login, verification, download/install, wallet connect, payment, reward claim), and what it asks the user to do.
- If the DOM is limited/truncated, reflect uncertainty (e.g., "appears to").

### page_structure
- Describe whether the layout/navigation looks typical and note any suspiciously inconsistent structure.
- If the DOM is too limited to judge, reflect uncertainty.

### sensitive_action_prompting
- Report a security-sensitive action ONLY when the page is actively steering the user to do it.
- Prompting/leading examples: Imperative CTAs ("Sign in", "Continue", "Verify", "Download", "Install", "Add extension", "Connect wallet", "Pay now", "Claim"), gated flows ("To proceed, do X", "Required"), or on-page action elements (forms/inputs, submit buttons, prominent action buttons/links).
- If ANY item in the inventory is prompted/led, you MUST report it in `sensitive_action_prompting`.
- Write "Nothing in particular" ONLY when none of the items are prompted/led in BOTH `parsed_dom` and `screenshot_wordlist`.
- Use short structured text and include concrete evidence (button labels, visible phrases, input types, etc.).
- Example: "Prompted action: authentication/credential entry. Mechanism: on-page form + submit. Evidence: <input type=password>, button 'Sign in'; screenshot shows 'Password'."
- Example: "Prompted action: install (extension). Mechanism: prominent Call to Actions. Evidence: screenshot shows 'Add to Chrome'; DOM contains 'extension'/'Add'."

## Security-sensitive action inventory
Scan BOTH `parsed_dom` and `screenshot_wordlist` and check whether the page is prompting/leading the user to ANY of these actions:

1) Authentication / credential or verification entry
   - email/username/password, 2FA/OTP code, “verify identity”, “unlock/restore access”, password reset.

2) Install or run something on the device/browser
   - download/install/run software, or install/enable a browser extension/add-on.

3) Cryptocurrency wallet connection or signing
   - connect wallet, sign/approve/authorize transactions or messages.

4) Payment or money transfer
   - pay invoice, transfer money, gift cards, crypto transfer.

5) Reward/bonus/redeem flows that drive sensitive actions
    - fake prize/lottery/win/reward claims or redemption codes, especially when paired with login/install/payment/wallet actions.

6) Contact/support flow requesting sensitive info
   - support forms that request credentials, payment details, recovery codes, etc.

## Structural anomaly examples (use as strong cues)
If any structural anomaly is observed, treat the page as suspicious. If the anomaly involves many hidden items (e.g., menu/list entries styled with display:none or otherwise not visible in large numbers), treat it as even more suspicious.
Even a small or partial match to the following patterns should be treated as suspicious; a strong or repeated match is highly suspicious:
1) Many file/download links are embedded across the page (e.g., repeated download links or file-title links in lists).
2) Large menus or item lists (e.g., <ul><li><a>...</a></li></ul>) contain many entries, and among otherwise generic items there are many links that look unrelated to the page topic.
3) Many image links are embedded across the page, especially when the screenshot_wordlist contains sensitive-action cues (e.g., "Free Download") that do NOT appear in parsed_dom, indicating the text may be embedded in images.

## Output (STRICT)
Output ONLY the following object (no extra text):
{{
    "summary": "<neutral concise summary>",
    "page_structure": "<structure notes or 'Nothing in particular'>",
    "sensitive_action_prompting": "<prompting/leading to security-sensitive actions, or 'Nothing in particular'>"
}}

---

Inputs:
apex_domain:
{apex_domain}

parsed_dom:
{parsed_dom}

screenshot_wordlist:
{screenshot_wordlist}
"""
)

JUDGE_PROMPT = PromptTemplate.from_template(
"""
You are a security analyst analyzing websites hosted on free web hosting services.
Your task is to judge whether the analyzed website hosted under the free web hosting apex domain `{apex_domain}` is a malicious site.

## Inputs
- `apex_domain`: the free web hosting provider’s apex domain (infrastructure context; NOT the site’s brand by itself).
- `brand_report`:
  - `is_brand`: whether the page indicates a specific brand
  - `brand_name`: brand the site appears to present (may be "uncertain")
  - `brand_popularity`: high/low/uncertain
- `content_report`:
    - `summary`: neutral description of the page
    - `page_structure`: description of page structure and anomalies
    - `sensitive_action_prompting`: described prompting/leading cues, or "Nothing in particular"

## Core principle (context first)
We are analyzing pages hosted on free web hosting services, which are often used for personal sites.
[Important] Hosting on a free service by itself is NOT evidence of maliciousness.
Do NOT treat weak signals as decisive.

## Hard constraints
1) DO NOT mark suspicious/malicious solely because:
    - the site is hosted on free web hosting (apex_domain context).
    These are weak context only, never standalone reasons.

2) Brand popularity must NEVER be used as a reason for "benign".
    - A well-known brand does not imply legitimacy.
    - If a well-known brand is indicated AND the page prompts sensitive actions, that is a risk amplifier.

3) Absence of threats/urgency must NOT be used as evidence of legitimacy.
    - Many phishing pages have no threats.
    
4) A well-known brand plus a plausible/clean page structure is NOT evidence of legitimacy on free-hosted pages.
    - On free web hosting services, a well-known brand combined with sensitive-action prompting is context-anomalous and suspicious.

5) A page that indicates a well-known brand on a free web hosting service is often suspicious by context alone.
    - Treat this as a risk signal even if the page looks clean; it is common for phishing pages to imitate popular brands on free-hosted domains.

## Special Case: uncertain brand
- If `brand_report.brand_name` is "uncertain" or `brand_report.is_brand` is false, consider the possibility that the page is personal-blog-like and use `content_report` to decide.

## Decision logic (branching)
First, use `brand_report` and `content_report` to decide whether the page indicates a well-known brand, or appears personal-blog-like.
If `sensitive_action_prompting` is "Nothing in particular" but structural anomalies are noted in `content_report.page_structure`, treat the page as suspicious.
1) If the page indicates a well-known brand:
    - Treat well-known brand indication on free-hosted pages as inherently suspicious; do NOT require an explicit sensitive-action prompt.
    - If there is any steering toward sensitive actions (e.g., login links or sign-in entry points), label "malicious".

2) If the page appears to be a personal-blog-like site:
    - Focus the judgment on sensitive-action prompting and structural anomalies.
    - Structural anomalies are a critical signal in this task; weigh page structure heavily.
    - If there is sensitive-action prompting, label "malicious".
    - If any of the Structural anomaly examples (below) apply, label "malicious".
    - The presence of attendance/confirmation forms or contact forms alone does not count as sensitive-action prompting.
    - A login link, attendance/confirmation form, or personal-info input form alone is not sufficient to label it "malicious".

## Security-sensitive action inventory (use as a checklist)
Check whether the page is prompting/leading the user to ANY of these actions:

1) Authentication / credential or verification entry
    - email/username/password, 2FA/OTP code, “verify identity”, “unlock/restore access”, password reset.

2) Install or run something on the device/browser
    - download/install/run software, or install/enable a browser extension/add-on.

3) Cryptocurrency wallet connection or signing
    - connect wallet, sign/approve/authorize transactions or messages.

4) Payment or money transfer
    - pay invoice, transfer money, gift cards, crypto transfer.

5) Reward/bonus/redeem flows that drive sensitive actions
    - claim reward/bonus/redeem code especially when paired with login/install/payment/wallet actions.

6) Contact/support flow requesting sensitive info
    - support forms that request credentials, payment details, recovery codes, etc.

## Structural anomaly examples (use as strong cues)
If any structural anomaly is observed, treat the page as suspicious. If the anomaly involves hidden items (e.g., menu/list entries styled with display:none or otherwise not visible), treat it as even more suspicious.
Even a small or partial match to the following patterns should be treated as suspicious; a strong or repeated match is highly suspicious:
1) Many file/download links are embedded across the page (e.g., repeated download links or file-title links in lists).
2) Large menus or item lists contain many entries, and among otherwise generic items there are many links that look unrelated to the page topic.
3) Many image links are embedded across the page, especially when the screenshot_wordlist contains sensitive-action cues (e.g., "Free Download") that do NOT appear in parsed_dom, indicating the text may be embedded in images.

## Ethical note
- Content that is ethically questionable or adult-themed is not automatically malicious; judge based on the phishing signals above.

## Final labels
- Follow the decision logic above.
- "benign": no malicious criteria are met.
- "suspicious": some malicious criteria are partially met, or evidence is insufficient to conclude "malicious".

## Output (STRICT)
Output ONLY the following object:
{{
  "final_verdict": "malicious" | "benign" | "suspicious",
  "rationale": ["...", "..."]
}}
- rationale must be concrete and grounded ONLY in provided brand_report/content_report.
- Include at least 2 items, each referencing specific action/context cues (not generalities).
- Write each rationale item as a natural sentence (not a bullet-like fragment).

---

Inputs:
apex_domain:
{apex_domain}

brand_report:
{brand_report}

content_report:
{content_report}
"""
)
