import csv
import os
import time
from typing import Any, Dict, Iterable, Optional

from langchain_community.callbacks import get_openai_callback

from .api_counter import track_api_calls
from .io_utils import (
    append_csv_row,
    append_jsonl_row,
    ensure_csv_header,
    get_path_by_url,
)
from .ocr import get_wordlist_from_screen
from .retry import (
    MAX_URL_RETRIES,
    is_retriable_error,
    retry_tag,
    retry_wait_for,
)
from .url_utils import extract_apex_domain
from .workflow import State


def run_all(
    workflow,
    *,
    out_jsonl: str,
    out_csv: str,
    data_dir: str,
    splits: Iterable[str],
    limit: int = 0,
) -> None:
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_cse_id = os.getenv("GOOGLE_CSE_ID")
    if not google_api_key or not google_cse_id:
        raise RuntimeError("Set env vars GOOGLE_API_KEY and GOOGLE_CSE_ID.")

    ensure_csv_header(out_csv)
    processed_count = 0

    for split in splits:
        split_dir = os.path.join(data_dir, split)
        csv_path = os.path.join(split_dir, "url_list.csv")

        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"missing: {csv_path}")

        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row in reader:
                url = (row.get("url") or "").strip()
                if not url:
                    continue

                error_msg = ""
                verdict = ""
                prompt_tokens = 0
                completion_tokens = 0
                total_tokens = 0
                vision_calls = 0
                cse_calls = 0
                processing_sec = 0.0
                retry_wait_sec = 0.0
                final_state: Optional[Dict[str, Any]] = None
                last_exc: Optional[BaseException] = None

                for attempt in range(MAX_URL_RETRIES + 1):
                    attempt_start = time.perf_counter()
                    try:
                        with track_api_calls() as api_counts:
                            img_path, dom_path = get_path_by_url(url, split_dir)
                            screenshot_wordlist = get_wordlist_from_screen(img_path)

                            initial_state: State = {
                                "apex_domain": extract_apex_domain(url),
                                "dom_path": dom_path,
                                "screenshot_wordlist": screenshot_wordlist,
                                "content_report": {},
                                "brand_report": {},
                                "final_report": {},
                            }

                            with get_openai_callback() as cb:
                                final_state = workflow.invoke(initial_state)
                                prompt_tokens = cb.prompt_tokens
                                completion_tokens = cb.completion_tokens
                                total_tokens = cb.total_tokens

                        vision_calls = api_counts.vision
                        cse_calls = api_counts.cse
                        processing_sec += time.perf_counter() - attempt_start
                        last_exc = None
                        break

                    except BaseException as e:
                        processing_sec += time.perf_counter() - attempt_start
                        last_exc = e
                        if is_retriable_error(e) and attempt < MAX_URL_RETRIES:
                            wait = retry_wait_for(e)
                            print(
                                f"[{retry_tag(e)}] {url}: {type(e).__name__}; "
                                f"sleeping {wait:.1f}s before URL-level retry "
                                f"{attempt + 1}/{MAX_URL_RETRIES}"
                            )
                            time.sleep(wait)
                            retry_wait_sec += wait
                            continue
                        break

                if last_exc is not None:
                    error_msg = repr(last_exc)
                else:
                    verdict = str((final_state or {}).get("final_report", {}).get("final_verdict", ""))

                state = final_state or {}
                record: Dict[str, Any] = {
                    "split": split,
                    "url": url,
                    "final_verdict": verdict,
                    "elapsed_sec": processing_sec,
                    "retry_wait_sec": retry_wait_sec,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "vision_api_calls": vision_calls,
                    "cse_api_calls": cse_calls,
                    "error": error_msg,
                    "final_report": state.get("final_report", {}),
                    "content_report": state.get("content_report", {}),
                    "brand_report": state.get("brand_report", {}),
                }
                append_jsonl_row(out_jsonl, record)
                append_csv_row(out_csv, record)

                processed_count += 1

                print(
                    f"[{split}] {url} verdict={verdict} "
                    f"elapsed={processing_sec:.3f}s "
                    f"retry_wait={retry_wait_sec:.1f}s "
                    f"error={bool(error_msg)}"
                )

                if limit and processed_count >= limit:
                    return
