from typing import List, Literal

from pydantic import BaseModel, Field


class ContentReport(BaseModel):
    summary: str = Field(
        description=(
            "Concise description of what kind of page this appears to be, "
            "based on the visible parsed DOM (possibly truncated) and the screenshot word list. "
            "Avoid detailed notes about page structure; focus on the page type and intent. "
        )
    )
    page_structure: str = Field(
        description=(
            "Description of the page structure and any anomalies or inconsistencies observed in the DOM/screenshot. "
            "If no structural concerns are observed, output exactly 'Nothing in particular'."
        )
    )
    sensitive_action_prompting: str = Field(
        description=(
            "Description of whether (and how) this page prompts/leads the user to take security-sensitive actions. "
            "Focus on active steering mechanisms such as clear calls-to-action, gated/step-by-step flows, and on-page action elements "
            "(e.g., forms, password/OTP inputs, install/extension Call to Actions, wallet connect/sign prompts, payment prompts, reward claims tied to sensitive actions). "
            "Include concrete evidence from the parsed DOM and/or screenshot word list (button labels, visible phrases, form/input cues). "
            "If no prompting/leading to security-sensitive actions is observed, output exactly 'Nothing in particular'."
        )
    )

class BrandName(BaseModel):
    is_brand: bool = Field(
        description=(
            "Whether the analyzed page appears to be presenting or indicating a specific brand."
        )
    )
    brand_name: str = Field(
        description="The brand (company, organization, etc.) that this page appears to be presenting or indicating."
    )

class BrandReport(BaseModel):
    is_brand: bool = Field(
        description=(
            "Whether the analyzed page appears to be presenting or indicating a specific brand."
        )
    )
    brand_name: str = Field(
        description="The brand (company, organization, etc.) that this page appears to be presenting or indicating."
    )
    brand_popularity: Literal["high","low","uncertain"] = Field(
        description=(
            "Estimated popularity or scale of the brand, one of: "
            "'high', 'low', or 'uncertain'. "
        )
    )

class FinalReport(BaseModel):
    final_verdict: Literal["malicious", "benign", "suspicious"] = Field(
        description="Final maliciousness judgment result, one of malicious, benign, or suspicious"
    )
    rationale: List[str] = Field(
        description="Rationale for the final judgment result"
    )
