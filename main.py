#!/usr/bin/env python3

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from api import HevyAPIError, HevyClient


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="hevy-export",
        description="Export Hevy workout history to PDF and/or CSV.",
    )
    parser.add_argument(
        "--from",
        dest="date_from",
        metavar="YYYY-MM-DD",
        help="Start date (inclusive). Defaults to all available history.",
    )
    parser.add_argument(
        "--to",
        dest="date_to",
        metavar="YYYY-MM-DD",
        help="End date (inclusive). Defaults to today.",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        metavar="DIR",
        help="Directory to write output files (default: current directory).",
    )
    parser.add_argument(
        "--format",
        choices=["pdf", "csv", "both"],
        default="both",
        help="Output format (default: both).",
    )
    return parser.parse_args()


def _parse_date(value: str, label: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        sys.exit(f"Error: {label} must be in YYYY-MM-DD format, got: {value!r}")


def main() -> None:
    load_dotenv()
    args = parse_args()

    api_key = os.getenv("HEVY_API_KEY")
    if not api_key:
        sys.exit(
            "Error: HEVY_API_KEY environment variable not set.\n"
            "Set it in a .env file or export it in your shell."
        )

    date_from: datetime | None = None
    date_to: datetime | None = None

    if args.date_from:
        date_from = _parse_date(args.date_from, "--from")
    if args.date_to:
        date_to = _parse_date(args.date_to, "--to")
        # make it end-of-day so --to is inclusive
        date_to = date_to.replace(hour=23, minute=59, second=59)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    client = HevyClient(api_key)

    print("Fetching workouts from Hevy API...")
    workouts = []
    try:
        for i, workout in enumerate(client.iter_workouts(date_from, date_to), 1):
            workouts.append(workout)
            print(f"  Fetched {i} workout(s)...", end="\r", flush=True)
    except HevyAPIError as e:
        sys.exit(f"\nAPI error: {e}")

    print(f"\nFetched {len(workouts)} workout(s) total.")

    if not workouts:
        print("No workouts found for the given date range. Nothing to export.")
        return

    workouts.sort(key=lambda w: w.start_time)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    from_label = date_from.strftime("%Y%m%d") if date_from else "all"
    to_label = date_to.strftime("%Y%m%d") if date_to else "today"
    base_name = f"hevy_{from_label}_to_{to_label}_{timestamp}"

    if args.format in ("csv", "both"):
        from exporters.csv import export_sets_csv, export_summary_csv

        sets_path = output_dir / f"{base_name}_sets.csv"
        summary_path = output_dir / f"{base_name}_summary.csv"

        print(f"Writing sets CSV -> {sets_path}")
        export_sets_csv(workouts, str(sets_path))

        print(f"Writing summary CSV -> {summary_path}")
        export_summary_csv(workouts, str(summary_path))

    if args.format in ("pdf", "both"):
        try:
            from exporters.pdf import export_pdf
        except ImportError:
            sys.exit(
                "Error: fpdf2 is not installed. Run: pip install fpdf2\n"
                "Or use --format csv to skip PDF generation."
            )

        pdf_path = output_dir / f"{base_name}.pdf"
        print(f"Writing PDF report -> {pdf_path}")
        export_pdf(workouts, str(pdf_path), date_from, date_to)

    print("\nDone.")


if __name__ == "__main__":
    main()
