import os
from typing import Optional

from googleapiclient.discovery import build

from .api_counter import increment_cse


def search_brand_popularity(
    query: str,
    *,
    api_key: Optional[str] = None,
    cse_id: Optional[str] = None,
    gl: Optional[str] = None,
    hl: Optional[str] = None,
    cr: Optional[str] = None,
    lr: Optional[str] = None,
) -> dict:
    api_key = api_key or os.getenv("GOOGLE_API_KEY")
    cse_id = cse_id or os.getenv("GOOGLE_CSE_ID")
    gl = gl or os.getenv("GOOGLE_CSE_GL")
    hl = hl or os.getenv("GOOGLE_CSE_HL")
    cr = cr or os.getenv("GOOGLE_CSE_CR")
    lr = lr or os.getenv("GOOGLE_CSE_LR")

    params: dict = {"q": query, "cx": cse_id}
    if gl:
        params["gl"] = gl
    if hl:
        params["hl"] = hl
    if cr:
        params["cr"] = cr
    if lr:
        params["lr"] = lr

    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(**params).execute()
    increment_cse()

    total_results: Optional[int] = None
    try:
        total_str = res.get("searchInformation", {}).get("totalResults")
        if total_str is not None:
            total_results = int(total_str)
    except (ValueError, TypeError):
        total_results = None

    return {
        "total_results": total_results,
    }
