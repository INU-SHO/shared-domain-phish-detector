import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Tuple


CSV_HEADER = [
    "split",
    "url",
    "final_verdict",
    "elapsed_sec",
    "retry_wait_sec",
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "vision_api_calls",
    "cse_api_calls",
    "error",
]


def get_path_by_url(url: str, split_dir: str) -> tuple[str, str]:
    id = ""
    url_list = os.path.join(split_dir, "url_list.csv")
    with open(url_list, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["url"] == url:
                id = row["id"]
                break
    if not id:
        raise ValueError("URL not found in the dataset.")
    img_path = os.path.join(split_dir, "screen", str(id)) + ".png"
    dom_path = os.path.join(split_dir, "html", str(id)) + ".html"
    return img_path, dom_path


def ensure_csv_header(path: str) -> None:
    if os.path.exists(path):
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(CSV_HEADER)


def append_jsonl_row(path: str, record: Dict[str, Any]) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
        f.flush()


def append_csv_row(path: str, row: Dict[str, Any]) -> None:
    """Append a row to the CSV. Keys outside CSV_HEADER are silently dropped."""
    formatted = {**row}
    for key in ("elapsed_sec", "retry_wait_sec"):
        if key in formatted:
            formatted[key] = f"{formatted[key]:.6f}"
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_HEADER, extrasaction="ignore")
        w.writerow(formatted)


def make_output_paths(
    model_name: str,
    *,
    base_dir: str = "results",
    suffix: str = "",
) -> Tuple[Path, Path]:
    stem = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{model_name}{suffix}"
    out_dir = Path(base_dir) / model_name
    out_dir.mkdir(parents=True, exist_ok=True)
    return out_dir / f"{stem}.jsonl", out_dir / f"{stem}.csv"
