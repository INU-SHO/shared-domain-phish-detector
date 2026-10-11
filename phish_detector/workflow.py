from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, START, StateGraph

from .dom_utils import get_parsed_dom, get_title_from_dom
from .prompts import (
    BRAND_ANALYZER_PROMPT,
    BRAND_DETECTOR_PROMPT,
    CONTENT_ANALYZER_PROMPT,
    JUDGE_PROMPT,
)
from .references import format_references
from .schemas import BrandName, BrandReport, ContentReport, FinalReport
from .search import search_brand_popularity


class State(TypedDict):
    apex_domain: str
    dom_path: str
    screenshot_wordlist: List[str]
    content_report: dict
    brand_report: dict
    final_report: dict


def build_workflow(
    llm,
    parsed_dom_max_chars: int = 500_000,
    *,
    brand_references: List[Dict[str, Any]],
):
    analyzer_tpl = BRAND_ANALYZER_PROMPT.partial(references=format_references(brand_references))

    def brand_analyzer(state: State):
        title = get_title_from_dom(state["dom_path"])
        structured_llm = llm.with_structured_output(BrandName)
        response = structured_llm.invoke(
            BRAND_DETECTOR_PROMPT.format(
                apex_domain=state["apex_domain"],
                dom_title=title,
                screenshot_wordlist=state["screenshot_wordlist"]
            )
        )
        brand_name = response.model_dump() # type: ignore
        if (not brand_name.get("is_brand")) or brand_name["brand_name"] == "uncertain":
            return {
                "brand_report": {
                    "is_brand": False,
                    "brand_name": "uncertain",
                    "brand_popularity": "uncertain"
                }
            }
        structured_llm = llm.with_structured_output(BrandReport)
        total_results = search_brand_popularity(
            f'"{brand_name["brand_name"]}" official site'
        ).get("total_results")
        response = structured_llm.invoke(
            analyzer_tpl.format(
                brand_name=brand_name["brand_name"],
                total_results=total_results
            )
        )
        brand_report = response.model_dump() # type: ignore
        return {"brand_report": brand_report}
    
    def content_analyzer(state: State):
        parsed_dom = get_parsed_dom(state["dom_path"], max_chars=parsed_dom_max_chars)
        llm_structured = llm.with_structured_output(ContentReport)
        response = llm_structured.invoke(
            CONTENT_ANALYZER_PROMPT.format(
                apex_domain=state["apex_domain"],
                parsed_dom=parsed_dom,
                screenshot_wordlist=state["screenshot_wordlist"]
            )
        )
        content_report = response.model_dump() # type: ignore
        return {"content_report": content_report}

    def judge(state: State):
        brand_report = state["brand_report"]
        content_report = state["content_report"]
        structured_llm = llm.with_structured_output(FinalReport)
        response = structured_llm.invoke(
            JUDGE_PROMPT.format(
                apex_domain=state["apex_domain"],
                brand_report=brand_report,
                content_report=content_report,
            )
        )
        final_report = response.model_dump() # type: ignore
        return {"final_report": final_report}

    builder = StateGraph(State)
    builder.add_node("content_analyzer", content_analyzer)
    builder.add_node("brand_analyzer", brand_analyzer)
    builder.add_node("judge", judge)
    builder.add_edge(START, "content_analyzer")
    builder.add_edge(START, "brand_analyzer")
    builder.add_edge("content_analyzer", "judge")
    builder.add_edge("brand_analyzer", "judge")
    builder.add_edge("judge", END)
    return builder.compile()
