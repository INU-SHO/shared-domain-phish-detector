import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from phish_detector.services import SEEN_HOSTS, UNSEEN_HOSTS  # noqa: E402
from phish_detector.urlscan_collector import collect_dataset  # noqa: E402


FREEPHISH_TRAIN_DOMAINS = [
    "weebly.com",
    "000webhostapp.com",
    "blogspot.com",
    "wixsite.com",
    "sites.google.com",
    "github.io",
    "firebaseapp.com",
    "square.site",
    "forms.zohopublic.com",
    "forms.zohopublic.eu",
    "wordpress.com",
    "docs.google.com",
    "sharepoint.com",
    "yolasite.com",
    "godaddysites.com",
    "mailchimpsites.com",
    "glitch.me",
    "hpage.com",
]

SHS_GROUPS = {
    "train": FREEPHISH_TRAIN_DOMAINS,
    "test": sorted(SEEN_HOSTS | UNSEEN_HOSTS),
}


def build_date_filter(date_from: str | None, date_to: str | None) -> str:
    """Build a urlscan.io ``date:[X TO Y]`` query fragment.

    Either bound may be omitted; ``*`` (open-ended) is used in its place.
    """
    return f"date:[{date_from or '*'} TO {date_to or '*'}]"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect a malicious/benign URL dataset from urlscan.io.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Where to save the collected dataset. Will contain "
            "{malicious,benign}/{url_list.csv,html/,screen/}. "
            "Defaults to datasets/<hosts> (e.g., datasets/test for --hosts test)."
        ),
    )
    parser.add_argument(
        "--date-from",
        default=None,
        help="Lower date bound (YYYY-MM-DD). Omit for an open lower bound.",
    )
    parser.add_argument(
        "--date-to",
        default=None,
        help="Upper date bound (YYYY-MM-DD). Omit for an open upper bound.",
    )
    parser.add_argument(
        "--max-per-domain",
        type=int,
        default=100,
        help="Maximum samples saved per SHS per label (default: 100).",
    )
    parser.add_argument(
        "--sleep-sec",
        type=float,
        default=1.0,
        help="Sleep between successful saves to avoid rate-limiting urlscan.io (default: 1.0).",
    )
    parser.add_argument(
        "--hosts",
        choices=sorted(SHS_GROUPS.keys()),
        default="test",
        help=(
            "Which SHS group to collect from (default: test). "
            "'test' = the 10 SHSs used in the paper's evaluation (5 Seen + 5 Unseen); "
            "'train' = FreePhish's 17 training-target SHSs (for the FreePhish baseline)."
        ),
    )
    args = parser.parse_args()

    output_dir = args.output_dir or Path("datasets") / args.hosts
    collect_dataset(
        shs_list=SHS_GROUPS[args.hosts],
        output_dir=output_dir,
        date_filter=build_date_filter(args.date_from, args.date_to),
        max_saved_per_domain=args.max_per_domain,
        sleep_after_save_sec=args.sleep_sec,
    )


if __name__ == "__main__":
    main()
