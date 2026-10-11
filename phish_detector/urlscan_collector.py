import csv
import os
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

import requests

SEARCH_URL = "https://urlscan.io/api/v1/search"

PAGE_SIZE = 10_000
REQUEST_TIMEOUT = 30


def _label_dirs(output_dir: Path, label: str) -> Tuple[Path, Path, Path]:
    """label: 'malicious' or 'benign'."""
    base = output_dir / label
    return base / "url_list.csv", base / "screen", base / "html"


def _ensure_dirs(output_dir: Path) -> None:
    for label in ("malicious", "benign"):
        csv_path, screen_dir, html_dir = _label_dirs(output_dir, label)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        screen_dir.mkdir(parents=True, exist_ok=True)
        html_dir.mkdir(parents=True, exist_ok=True)


def _init_csv(csv_path: Path) -> None:
    if not csv_path.exists():
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=["id", "url"]).writeheader()


def _load_existing_urls(csv_path: Path) -> Set[str]:
    urls: Set[str] = set()
    if not csv_path.exists():
        return urls
    with csv_path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "url" not in (reader.fieldnames or []):
            return urls
        for row in reader:
            url = (row.get("url") or "").strip()
            if url:
                urls.add(url)
    return urls


def _append_csv(csv_path: Path, scan_id: str, url: str) -> None:
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=["id", "url"]).writerow(
            {"id": scan_id, "url": url}
        )


def _build_base_query(entry: str, date_filter: str) -> str:
    if entry.count(".") >= 2:
        target = f'page.domain.keyword:"{entry}"'
    else:
        target = f'page.apexDomain:"{entry}"'
    return f"{target} AND page.status:200 AND {date_filter}"


def _build_query_malicious(entry: str, date_filter: str) -> str:
    base = _build_base_query(entry, date_filter)
    return f"({base}) AND (brand.key:*)"


def _build_query_benign(entry: str, date_filter: str) -> str:
    base = _build_base_query(entry, date_filter)
    return (
        f"({base}) AND "
        f"verdicts.malicious:false AND "
        f"verdicts.score:[-100 TO 0] AND "
        f"NOT brand.key:*"
    )


def _search_scans(session: requests.Session, headers: Dict[str, str], q: str) -> Dict:
    params = {"q": q, "size": PAGE_SIZE, "datasource": "scans"}
    r = session.get(SEARCH_URL, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    return r.json()


def _fetch_bytes(session: requests.Session, headers: Dict[str, str], url: str) -> Optional[bytes]:
    for attempt in range(4):
        r = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        if r.status_code == 429 and attempt < 3:
            wait = 2 ** attempt + 1  # 2s, 3s, 5s
            print(f"[429] {url}: rate limited, sleeping {wait}s")
            time.sleep(wait)
            continue
        if r.status_code != 200 or not r.content:
            return None
        return r.content


def _fetch_screenshot(session: requests.Session, headers: Dict[str, str], scan_id: str) -> Optional[bytes]:
    return _fetch_bytes(session, headers, f"https://urlscan.io/screenshots/{scan_id}.png")


def _fetch_dom(session: requests.Session, headers: Dict[str, str], scan_id: str) -> Optional[bytes]:
    return _fetch_bytes(session, headers, f"https://urlscan.io/dom/{scan_id}/")


def _resolve_api_key(cli_key: Optional[str]) -> str:
    key = cli_key or os.environ.get("URLSCAN_API_KEY", "").strip()
    if not key:
        raise SystemExit(
            "ERROR: no urlscan.io API key. "
            "Set URLSCAN_API_KEY or pass api_key=... to collect_dataset()."
        )
    return key


def collect_dataset(
    shs_list: Iterable[str],
    output_dir: Path,
    date_filter: str,
    *,
    api_key: Optional[str] = None,
    max_saved_per_domain: int = 100,
    sleep_after_save_sec: float = 1.0,
) -> None:
    headers = {"api-key": _resolve_api_key(api_key)}
    output_dir = Path(output_dir)

    print(
        "[note] This script uses urlscan.io Pro-only query operators "
        "(brand.key, verdicts.malicious, large per-query size). With a "
        "free-tier API key the malicious queries will silently return zero hits."
    )

    _ensure_dirs(output_dir)
    csv_mal, _, _ = _label_dirs(output_dir, "malicious")
    csv_ben, _, _ = _label_dirs(output_dir, "benign")
    _init_csv(csv_mal)
    _init_csv(csv_ben)

    existing_urls = _load_existing_urls(csv_mal) | _load_existing_urls(csv_ben)

    with requests.Session() as session:
        for entry in shs_list:
            print(f"\n=== Entry: {entry} ===")
            for label, is_mal in (("malicious", True), ("benign", False)):
                build = _build_query_malicious if is_mal else _build_query_benign
                q = build(entry, date_filter)
                print(f"\n--- label={label} ---\nq = {q}")

                try:
                    data = _search_scans(session, headers, q)
                except Exception as e:
                    print(f"[WARN] search failed for {entry} label={label}: {e}")
                    continue

                results = data.get("results") or []
                csv_path, screen_dir, html_dir = _label_dirs(output_dir, label)
                saved = _persist_results(
                    session=session,
                    headers=headers,
                    results=results,
                    existing_urls=existing_urls,
                    csv_path=csv_path,
                    screen_dir=screen_dir,
                    html_dir=html_dir,
                    max_saved=max_saved_per_domain,
                    sleep_sec=sleep_after_save_sec,
                    label=label,
                    entry=entry,
                )
                print(f"--- {entry} label={label}: saved={saved} / hits={len(results)} ---")


def _persist_results(
    *,
    session: requests.Session,
    headers: Dict[str, str],
    results: List[Dict],
    existing_urls: Set[str],
    csv_path: Path,
    screen_dir: Path,
    html_dir: Path,
    max_saved: int,
    sleep_sec: float,
    label: str,
    entry: str,
) -> int:
    saved = 0
    for item in results:
        if saved >= max_saved:
            break

        scan_id = item.get("_id")
        page_url = (item.get("page") or {}).get("url")
        if not scan_id or not page_url:
            continue
        if page_url in existing_urls:
            continue

        try:
            screenshot = _fetch_screenshot(session, headers, scan_id)
            dom = _fetch_dom(session, headers, scan_id)
        except Exception:
            continue
        if screenshot is None or dom is None:
            continue

        screen_path = screen_dir / f"{scan_id}.png"
        html_path = html_dir / f"{scan_id}.html"

        try:
            screen_path.write_bytes(screenshot)
            html_path.write_bytes(dom)
        except Exception as e:
            for p in (screen_path, html_path):
                try:
                    if p.exists():
                        p.unlink()
                except Exception:
                    pass
            print(f"[WARN] save failed scan_id={scan_id}: {e}")
            continue

        _append_csv(csv_path, scan_id, page_url)
        existing_urls.add(page_url)
        saved += 1
        print(
            f"[OK] entry={entry} label={label} scan_id={scan_id} url={page_url}"
        )
        time.sleep(sleep_sec)
    return saved
