import argparse
import csv
import glob
import math
import statistics
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scipy.stats import ttest_rel  # noqa: E402

from phish_detector.services import SEEN_HOSTS, UNSEEN_HOSTS  # noqa: E402


_ALL_HOSTS_SORTED = sorted(SEEN_HOSTS | UNSEEN_HOSTS, key=len, reverse=True)


def discover_csvs(paths: List[str]) -> List[Path]:
    out: List[Path] = []
    for pat in paths:
        matched = sorted(Path(p) for p in glob.glob(pat))
        out.extend(matched)
    return out


def load_rows(csv_path: Path) -> List[Dict[str, str]]:
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def cycle_pooled_seen_unseen_f1(
    rows: List[Dict[str, str]]
) -> Tuple[float, float]:
    first = rows[0]
    if "final_verdict" in first:
        return _cycle_f1_proposed(rows)
    if "pred" in first:
        return _cycle_f1_freephish(rows)
    raise ValueError(
        "Unknown CSV format."
    )


def extract_service(url: str) -> str:
    host = (urlparse(url).netloc or urlparse("https://" + url).netloc).lower()
    host = host.split("@")[-1].split(":")[0]
    for shs in _ALL_HOSTS_SORTED:
        if host == shs or host.endswith("." + shs):
            return shs
    return ""


def _safe_f1(tp: int, fp: int, fn: int) -> float:
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    return 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0


def _cycle_f1_proposed(rows: List[Dict[str, str]]) -> Tuple[float, float]:
    tp_s = fp_s = fn_s = 0
    tp_u = fp_u = fn_u = 0
    for r in rows:
        if (r.get("error") or "").strip():
            continue
        service = extract_service(r.get("url") or "")
        y = 1 if (r.get("split") or "").strip() == "malicious" else 0
        verdict = (r.get("final_verdict") or "").strip()
        yhat = 1 if verdict in ("malicious", "suspicious") else 0
        if service in SEEN_HOSTS:
            if y == 1 and yhat == 1:
                tp_s += 1
            elif y == 0 and yhat == 1:
                fp_s += 1
            elif y == 1 and yhat == 0:
                fn_s += 1
        elif service in UNSEEN_HOSTS:
            if y == 1 and yhat == 1:
                tp_u += 1
            elif y == 0 and yhat == 1:
                fp_u += 1
            elif y == 1 and yhat == 0:
                fn_u += 1
    return _safe_f1(tp_s, fp_s, fn_s), _safe_f1(tp_u, fp_u, fn_u)


def _cycle_f1_freephish(rows: List[Dict[str, str]]) -> Tuple[float, float]:
    tp_s = fp_s = fn_s = 0
    tp_u = fp_u = fn_u = 0
    for r in rows:
        group = (r.get("group") or "").strip().lower()
        try:
            y = int((r.get("label") or "0").strip())
            yhat = int((r.get("pred") or "0").strip())
        except ValueError:
            continue
        if group == "seen":
            if y == 1 and yhat == 1:
                tp_s += 1
            elif y == 0 and yhat == 1:
                fp_s += 1
            elif y == 1 and yhat == 0:
                fn_s += 1
        elif group == "unseen":
            if y == 1 and yhat == 1:
                tp_u += 1
            elif y == 0 and yhat == 1:
                fp_u += 1
            elif y == 1 and yhat == 0:
                fn_u += 1
    return _safe_f1(tp_s, fp_s, fn_s), _safe_f1(tp_u, fp_u, fn_u)


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Paired t-test on per-cycle pooled F1 between Seen and Unseen "
            "services."
        ),
    )
    parser.add_argument("paths", nargs="+", help="Cycle CSV paths or globs.")
    args = parser.parse_args()

    csv_paths = discover_csvs(args.paths)
    if not csv_paths:
        parser.error(f"No CSVs matched: {args.paths}")
    print(f"Loaded {len(csv_paths)} cycle CSV(s).")

    run_pairs: List[Tuple[str, float, float]] = []
    for p in csv_paths:
        rows = load_rows(p)
        s_f1, u_f1 = cycle_pooled_seen_unseen_f1(rows)
        run_pairs.append((p.stem, s_f1, u_f1))

    if len(run_pairs) < 2:
        parser.error("Paired t-test requires at least 2 cycle CSVs.")

    label_width = max(len("cycle (file stem)"), *(len(label) for label, _, _ in run_pairs))

    print()
    print(f"## Per-cycle pooled F1 (n_cycles = {len(run_pairs)})")
    print()
    print(
        f"  {'cycle (file stem)':<{label_width}} "
        f"{'Seen F1':>10} {'Unseen F1':>10} {'Diff (S-U)':>12}"
    )
    diffs: List[float] = []
    for label, s_f1, u_f1 in run_pairs:
        diff = s_f1 - u_f1
        diffs.append(diff)
        print(
            f"  {label:<{label_width}} "
            f"{s_f1:>10.4f} {u_f1:>10.4f} {diff:>+12.4f}"
        )
    seen_per_cycle = [s for _, s, _ in run_pairs]
    unseen_per_cycle = [u for _, _, u in run_pairs]
    seen_mean = statistics.mean(seen_per_cycle)
    seen_sd = statistics.stdev(seen_per_cycle)
    unseen_mean = statistics.mean(unseen_per_cycle)
    unseen_sd = statistics.stdev(unseen_per_cycle)
    diff_mean = statistics.mean(diffs)
    diff_sd = statistics.stdev(diffs)
    print(
        f"  {'mean':<{label_width}} "
        f"{seen_mean:>10.4f} {unseen_mean:>10.4f} {diff_mean:>+12.4f}"
    )
    print(
        f"  {'sd':<{label_width}} "
        f"{seen_sd:>10.4f} {unseen_sd:>10.4f} {diff_sd:>12.4f}"
    )

    res_paired = ttest_rel(seen_per_cycle, unseen_per_cycle, alternative="greater")
    t_paired = float(res_paired.statistic)  # type: ignore[attr-defined]
    p_paired = float(res_paired.pvalue)  # type: ignore[attr-defined]
    df_paired = len(run_pairs) - 1

    print()
    print("## Paired t-test (paired by cycle, one-tailed)")
    print()
    print(f"  n pairs    : {len(run_pairs)}")
    print(f"  Mean(diff) : {diff_mean:+.4f}")
    print(f"  SD(diff)   : {diff_sd:.4f}")
    print()
    print("  H0: mean(Seen F1 - Unseen F1) == 0")
    print("  H1: mean(Seen F1 - Unseen F1) >  0")
    print(f"  t  = {t_paired:.4f}")
    print(f"  df = {df_paired}")
    print(f"  p  = {p_paired:.4f}")

    n1 = n2 = len(run_pairs)
    sd_pooled = math.sqrt(
        ((n1 - 1) * seen_sd ** 2 + (n2 - 1) * unseen_sd ** 2) / (n1 + n2 - 2)
    )
    cohen_d = diff_mean / sd_pooled if sd_pooled > 0 else float("inf")

    print()
    print("## Cohen's d (pooled SD, Bessel-corrected)")
    print()
    print("  SD_pooled = sqrt( ((n1-1)*SD_Seen^2 + (n2-1)*SD_Unseen^2) / (n1+n2-2) )")
    print(f"            = {sd_pooled:.4f}")
    print(f"  d         = Mean(diff) / SD_pooled = {cohen_d:.4f}")
    print()


if __name__ == "__main__":
    main()
