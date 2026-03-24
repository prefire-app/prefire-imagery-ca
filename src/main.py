"""Prefire pipeline entry point.

Usage:
    python -m src.main [convert|load|extract|all]

Steps:
    convert  - SID → GeoTIFF → COG → validate
    load     - Upload COGs to S3 → extract metadata → upload metadata to S3
    extract  - Build metadata / STAC / CSV for local COGs (standalone)
    all      - Run convert then load (default)
"""

import argparse
import sys

from dotenv import load_dotenv
from src.shared.check_bucket_status import check_bucket_status

def main():
    """Parse arguments and run the requested pipeline step(s)."""
    load_dotenv()
    args = _parse_args(sys.argv[1:])

    if not check_bucket_status():
        print("Issues found in S3 bucket. Would you like to cancel? (y/n)")
        choice = input().lower()
        if choice == "y":
            print("Exiting.")
            return

    if args.command == "convert":
        if not _run_convert():
            sys.exit(1)
    elif args.command == "load":
        if not _run_load():
            sys.exit(1)
    elif args.command == "extract":
        _run_extract()
    elif args.command == "all":
        if not _run_convert():
            print("Convert step failed. Skipping load step.")
            sys.exit(1)
        _run_load()  # load calls extract internally


def _run_convert() -> bool:
    """Run the convert step."""
    from src.convert.convert import run_convert
    return run_convert()


def _run_load() -> bool:
    """Run the load step (includes extract)."""
    from src.load.load import run_load
    return run_load()


def _run_extract():
    """Run the extract step standalone."""
    from src.extract.extract import run_extract
    run_extract()


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Prefire pipeline")
    parser.add_argument(
        "command",
        nargs="?",
        default="all",
        choices=["convert", "extract", "load", "all"],
        help="Pipeline step to run (default: all)",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    main()