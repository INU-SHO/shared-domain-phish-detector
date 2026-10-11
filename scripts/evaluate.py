import argparse
import csv
import glob
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sklearn.metrics import (  # noqa: E402
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)
import yaml  # noqa: E402

from phish_detector.services import SEEN_HOSTS, UNSEEN_HOSTS  # noqa: E402


CONDITIONS = ("seen", "unseen", "all")
PRICING_PATH = Path("configs/pricing.yaml")


# ---- I/O helpers ----

def discover_csvs(explicit_paths: List[str]) -> List[Path]:
    out: List[Path] = []
    for pat in explicit_paths:
        out.extend(sorted(Path(p) for p in glob.glob(pat)))
    return out


def detect_model(csv_paths: List[Path]) -> str:
    return csv_paths[0].parent.name


def load_pricing() -> Dict[str, Any]:
    with open(PRICING_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def parse_row(row: Dict[str, str]) -> Dict[str, Any]:
    return {
        "split": row["split"],
        "url": row["url"],
        "verdict": row["final_verdict"],
        "error": row["error"],
        "elapsed": float(row["elapsed_sec"]),
        "prompt": int(row["prompt_tokens"]),
        "completion": int(row["completion_tokens"]),
        "total": int(row["total_tokens"]),
        "vision_calls": int(row["vision_api_calls"]),
        "cse_calls": int(row["cse_api_calls"]),
    }


def load_rows(csv_path: Path) -> List[Dict[str, Any]]:
    with open(csv_path, newline="", encoding="utf-8") as f:
        return [parse_row(r) for r in csv.DictReader(f)]


def classify_url(url: str) -> str:
    host = (urlparse(url).netloc or urlparse("https://" + url).netloc).lower()
    host = host.split("@")[-1].split(":")[0]

    for shs in sorted(SEEN_HOSTS | UNSEEN_HOSTS, key=len, reverse=True):
        if host == shs or host.endswith("." + shs):
            return "seen" if shs in SEEN_HOSTS else "unseen"
    return "unknown"


# ---- Metrics ----

def _to_label(split: str) -> int:
    return 1 if split == "malicious" else 0


def _to_pred(verdict: str) -> int:
    # "malicious" OR "suspicious" is treated as positive.
    return 1 if verdict in ("malicious", "suspicious") else 0


def compute_metrics(
    rows: List[Dict[str, Any]],
    price_in_per_1m: float,
    price_out_per_1m: float,
    price_vision_per_1k: float,
    price_cse_per_1k: float,
) -> Dict[str, Any]:
    y_true: List[int] = []
    y_pred: List[int] = []
    errors = 0
    elapsed: List[float] = []
    prompts: List[int] = []
    completions: List[int] = []
    totals: List[int] = []
    vision_calls: List[int] = []
    cse_calls: List[int] = []

    for r in rows:
        if r["error"]:
            errors += 1
            continue
        y_true.append(_to_label(r["split"]))
        y_pred.append(_to_pred(r["verdict"]))
        elapsed.append(r["elapsed"])
        prompts.append(r["prompt"])
        completions.append(r["completion"])
        totals.append(r["total"])
        vision_calls.append(r["vision_calls"])
        cse_calls.append(r["cse_calls"])

    if y_true:
        accuracy = float(accuracy_score(y_true, y_pred))
        precision = float(precision_score(y_true, y_pred, zero_division=0))
        recall = float(recall_score(y_true, y_pred, zero_division=0))
        f1 = float(f1_score(y_true, y_pred, zero_division=0))
    else:
        # Avoid passing empty arrays to sklearn (which raises).
        accuracy = precision = recall = f1 = 0.0

    avg_elapsed = statistics.mean(elapsed) if elapsed else 0.0
    avg_prompt = statistics.mean(prompts) if prompts else 0.0
    avg_completion = statistics.mean(completions) if completions else 0.0
    avg_total = statistics.mean(totals) if totals else 0.0
    avg_vision = statistics.mean(vision_calls) if vision_calls else 0.0
    avg_cse = statistics.mean(cse_calls) if cse_calls else 0.0

    avg_llm_cost = (avg_prompt * price_in_per_1m + avg_completion * price_out_per_1m) / 1_000_000
    avg_google_cost = (avg_vision * price_vision_per_1k + avg_cse * price_cse_per_1k) / 1_000

    return {
        "n_samples": len(y_true),
        "errors": errors,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "avg_elapsed_sec": avg_elapsed,
        "avg_prompt_tokens": avg_prompt,
        "avg_completion_tokens": avg_completion,
        "avg_total_tokens": avg_total,
        "avg_vision_calls": avg_vision,
        "avg_cse_calls": avg_cse,
        "avg_llm_usd_cost": avg_llm_cost,
        "avg_google_usd_cost": avg_google_cost,
        "avg_usd_cost": avg_llm_cost + avg_google_cost,
    }


def metrics_for_csv(
    csv_path: Path,
    prices: Tuple[float, float, float, float],
) -> Dict[str, Dict[str, Any]]:
    seen: List[Dict[str, Any]] = []
    unseen: List[Dict[str, Any]] = []
    for r in load_rows(csv_path):
        (seen if classify_url(r["url"]) == "seen" else unseen).append(r)
    return {
        "seen":   compute_metrics(seen, *prices),
        "unseen": compute_metrics(unseen, *prices),
        "all":    compute_metrics(seen + unseen, *prices),
    }


def aggregate(cycles: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    if not cycles:
        return {}
    out: Dict[str, Dict[str, float]] = {}
    for k in cycles[0].keys():
        vals = [m[k] for m in cycles]
        if all(isinstance(v, (int, float)) for v in vals):
            out[k] = {
                "mean": statistics.mean(vals),
                "std":  statistics.stdev(vals) if len(vals) > 1 else 0.0,
            }
    return out


# ---- Reporting ----

def print_section(title: str, cycles: List[Dict[str, Any]], agg: Dict[str, Any]) -> None:
    if not cycles:
        print(f"\n=== {title} === (no samples)")
        return

    print(f"\n=== {title} ===")
    for i, m in enumerate(cycles, 1):
        print(f"[cycle {i}]  n={m['n_samples']}  errors={m['errors']}")
        print(f"  acc={m['accuracy']:.4f}  prec={m['precision']:.4f}  "
              f"rec={m['recall']:.4f}  F1={m['f1']:.4f}")
        print(f"  elapsed={m['avg_elapsed_sec']:.3f}s  "
              f"tokens(in/out/total avg)="
              f"{m['avg_prompt_tokens']:.0f}/"
              f"{m['avg_completion_tokens']:.0f}/"
              f"{m['avg_total_tokens']:.0f}  "
              f"calls(V/C avg)={m['avg_vision_calls']:.2f}/{m['avg_cse_calls']:.2f}")
        print(f"  LLM=${m['avg_llm_usd_cost']:.6f}/sample  "
              f"Google=${m['avg_google_usd_cost']:.6f}/sample  "
              f"total=${m['avg_usd_cost']:.6f}/sample")

    if len(cycles) > 1:
        print(f"[mean ± std over {len(cycles)} cycles]")
        print(f"  acc={agg['accuracy']['mean']:.4f}±{agg['accuracy']['std']:.4f}  "
              f"prec={agg['precision']['mean']:.4f}±{agg['precision']['std']:.4f}  "
              f"rec={agg['recall']['mean']:.4f}±{agg['recall']['std']:.4f}  "
              f"F1={agg['f1']['mean']:.4f}±{agg['f1']['std']:.4f}")
        print(f"  elapsed={agg['avg_elapsed_sec']['mean']:.3f}±"
              f"{agg['avg_elapsed_sec']['std']:.3f}s")
        print(f"  LLM=${agg['avg_llm_usd_cost']['mean']:.6f}±"
              f"{agg['avg_llm_usd_cost']['std']:.6f}/sample  "
              f"Google=${agg['avg_google_usd_cost']['mean']:.6f}±"
              f"{agg['avg_google_usd_cost']['std']:.6f}/sample  "
              f"total=${agg['avg_usd_cost']['mean']:.6f}±"
              f"{agg['avg_usd_cost']['std']:.6f}/sample")


# ---- Entry point ----

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute Seen/Unseen/Overall accuracy, precision/recall/F1, latency, and cost from cycle CSVs.",
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help=(
            "One or more CSV paths (shell globs OK). One file = one report; "
            "multiple files are aggregated as cycles. The model name is "
            "inferred from the CSV's parent directory (results/<model>/). "
            "Example: `results/openai/*refs-telecommunication*.csv`."
        ),
    )
    args = parser.parse_args()

    csv_paths = discover_csvs(args.paths)

    if not csv_paths:
        parser.error(f"No CSVs matched the given paths: {args.paths}")

    model = detect_model(csv_paths)
    pricing = load_pricing()
    model_p = pricing.get(model, {})
    price_in = float(model_p.get("prompt", 0.0))
    price_out = float(model_p.get("completion", 0.0))
    google_p = pricing.get("google_apis", {})
    price_vision = float(google_p.get("cloud_vision", 0.0))
    price_cse = float(google_p.get("cse", 0.0))
    print(
        f"Pricing for `{model}`: input ${price_in}/M, output ${price_out}/M "
        f"(from {PRICING_PATH})"
    )
    print(
        f"Google APIs: Cloud Vision ${price_vision}/K, "
        f"Custom Search ${price_cse}/K"
    )
    print(f"Found {len(csv_paths)} CSV file(s) to evaluate.\n")

    prices = (price_in, price_out, price_vision, price_cse)
    per_cycle = [metrics_for_csv(csv_path, prices) for csv_path in csv_paths]

    for c in CONDITIONS:
        cycles = [m[c] for m in per_cycle]
        print_section(f"{c.capitalize()} services", cycles, aggregate(cycles))


if __name__ == "__main__":
    main()
