import argparse
import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv  # noqa: E402
import yaml  # noqa: E402

load_dotenv(Path(__file__).resolve().parent.parent / ".env", override=True)

from phish_detector.search import search_brand_popularity  # noqa: E402


def _split_header(text: str) -> tuple[str, str]:
    """Split a YAML file into (top-of-file comment block, remainder)."""
    lines = text.splitlines(keepends=True)
    header_end = 0
    for i, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped == "" or stripped == "\n":
            header_end = i + 1
        else:
            break
    return "".join(lines[:header_end]), "".join(lines[header_end:])


def refresh_file(path: Path) -> int:
    """Refresh one YAML file. Returns the number of brands updated."""
    print(f"[file] {path}")
    text = path.read_text(encoding="utf-8")
    header, body = _split_header(text)
    data = yaml.safe_load(body) or {}
    refs: List[dict] = data.get("high_popularity_references") or []
    if not refs:
        print(f"  [skip] no 'high_popularity_references' key")
        return 0

    updated = 0
    for r in refs:
        brand = r.get("brand")
        if not brand:
            continue
        query = f'"{brand}" official site'
        try:
            result = search_brand_popularity(query)
        except Exception as e:
            print(f"  [error] {brand}: {e!r}")
            continue
        n = result.get("total_results")
        if n is None:
            print(f"  [warn]  {brand:30s} -> no result (keeping {r.get('total_results', 0)})")
            continue
        old = r.get("total_results", 0)
        r["total_results"] = int(n)
        updated += 1
        print(f"  {brand:30s} -> {int(n):>14,}   (was {old:,})")

    # Re-emit YAML body while preserving the top comment block.
    new_body = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
    path.write_text(header + new_body, encoding="utf-8")
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="YAML files to refresh (e.g., configs/brand_references_financial.yaml).",
    )
    args = parser.parse_args()

    total = 0
    for p in args.paths:
        total += refresh_file(Path(p))
    print(f"\nDone. Updated {total} brand entry(ies) across {len(args.paths)} file(s).")


if __name__ == "__main__":
    main()
