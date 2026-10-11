import argparse
import csv
import io
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml  # noqa: E402

TRANCO_LATEST_ZIP_URL = "https://tranco-list.eu/top-1m.csv.zip"
TRANCO_BY_ID_URL = "https://tranco-list.eu/download/{list_id}/full"


def fetch_tranco_list(list_id: Optional[str]) -> Dict[str, int]:
    """Return {domain: rank} for the Tranco list. Domains are lowercased."""
    if list_id:
        url = TRANCO_BY_ID_URL.format(list_id=list_id)
        print(f"Fetching pinned Tranco list (id={list_id}) from:\n  {url}")
        with urllib.request.urlopen(url) as resp:
            data = resp.read().decode("utf-8", errors="replace")
        reader = csv.reader(io.StringIO(data))
    else:
        print(f"Fetching latest daily Tranco list from:\n  {TRANCO_LATEST_ZIP_URL}")
        with urllib.request.urlopen(TRANCO_LATEST_ZIP_URL) as resp:
            zip_bytes = resp.read()
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
        # Tranco's daily zip historically contains "top-1m.csv".
        inner = next((n for n in zf.namelist() if n.lower().endswith(".csv")), None)
        if inner is None:
            raise RuntimeError("Tranco zip did not contain a CSV file.")
        with zf.open(inner) as f:
            data = f.read().decode("utf-8", errors="replace")
        reader = csv.reader(io.StringIO(data))

    ranks: Dict[str, int] = {}
    for row in reader:
        if len(row) < 2:
            continue
        rank_s, domain = row[0], row[1]
        try:
            ranks[domain.strip().lower()] = int(rank_s)
        except ValueError:
            # Header row or malformed entry
            continue
    if not ranks:
        raise RuntimeError("Parsed 0 Tranco entries — the format may have changed.")
    return ranks


def _split_header(text: str) -> tuple[str, str]:
    """Split a YAML file into (header-comment-block, body)."""
    lines = text.splitlines(keepends=True)
    header_end = 0
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped == "" or stripped == "\n":
            header_end = i + 1
        else:
            break
    return "".join(lines[:header_end]), "".join(lines[header_end:])


def verify_file(path: Path, ranks: Dict[str, int]) -> List[Dict[str, Any]]:
    """Read YAML, look up each entry's domain, write tranco_rank back.

    Returns the list of per-entry summaries for the caller to print.
    """
    text = path.read_text(encoding="utf-8")
    header, body = _split_header(text)
    data = yaml.safe_load(body) or {}
    entries = data.get("high_popularity_references") or []
    if not entries:
        print(f"[skip] {path}: no high_popularity_references key.")
        return []

    print(f"[file] {path}")
    summaries: List[Dict[str, Any]] = []
    for entry in entries:
        brand = entry.get("brand", "?")
        domain = (entry.get("domain") or "").strip().lower()
        if not domain:
            entry["tranco_rank"] = None
            print(f"  [skip] {brand:20s}: no `domain` field; cannot look up Tranco rank.")
            summaries.append({"file": path.name, "brand": brand, "domain": None, "rank": None})
            continue
        rank = ranks.get(domain)
        entry["tranco_rank"] = rank
        if rank is None:
            print(f"  [warn] {brand:20s} ({domain}): NOT in Tranco top 1M")
        else:
            print(f"  {brand:20s} ({domain}): rank {rank:>7,}")
        summaries.append({"file": path.name, "brand": brand, "domain": domain, "rank": rank})

    path.write_text(header + yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return summaries


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("paths", nargs="+", help="brand_references_*.yaml files to verify.")
    parser.add_argument(
        "--list-id",
        help=(
            "Pin a specific Tranco list ID for paper-grade reproducibility "
            "(see https://tranco-list.eu/). Without this flag the latest daily "
            "list is used and the rank you record will drift over time."
        ),
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=10_000,
        help="Warn if any rank is above this threshold (default: 10,000).",
    )
    args = parser.parse_args()

    ranks = fetch_tranco_list(args.list_id)
    print(f"Loaded {len(ranks):,} Tranco entries.\n")

    all_summaries: List[Dict[str, Any]] = []
    for p in args.paths:
        all_summaries.extend(verify_file(Path(p), ranks))
        print()

    # Summary across all files vs. the threshold
    over_threshold = [s for s in all_summaries if s["rank"] is not None and s["rank"] > args.threshold]
    not_found = [s for s in all_summaries if s["domain"] and s["rank"] is None]
    print("=" * 60)
    print(f"Verification summary (Tranco threshold: top {args.threshold:,})")
    print("=" * 60)
    print(f"  Total brands checked:          {len(all_summaries)}")
    print(f"  Within top {args.threshold:>6,}:           {len(all_summaries) - len(over_threshold) - len(not_found)}")
    print(f"  Above threshold (rank > N):    {len(over_threshold)}")
    print(f"  Not found in Tranco 1M:        {len(not_found)}")
    if over_threshold:
        print("\n  Above-threshold brands (consider swapping):")
        for s in over_threshold:
            print(f"    - {s['brand']:20s} ({s['domain']}) in {s['file']}: rank {s['rank']:,}")
    if not_found:
        print("\n  Missing-from-Tranco brands (verify domain or swap):")
        for s in not_found:
            print(f"    - {s['brand']:20s} ({s['domain']}) in {s['file']}")


if __name__ == "__main__":
    main()
