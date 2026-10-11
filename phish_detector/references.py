from pathlib import Path
from typing import Any, Dict, List

import yaml


def load_references(path: Path) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data["high_popularity_references"]


def format_references(references: List[Dict[str, Any]]) -> str:
    return "\n".join(
        f'- "{r["brand"]} official site" -> total_results = {r["total_results"]:,}'
        for r in references
    )


def reference_tag(path: Any) -> str:
    return Path(str(path)).stem.removeprefix("brand_references_")
