"""Parse county name from pipeline filenames."""

import os
import re
from typing import List


def extract_county(filename: str) -> str:
    """Extract the county name from a filename.

    County is everything before the FIPS code (e.g. 'ca001').
    For 'los_angeles_ca037_2024_1.cog' → 'los_angeles'.

    Args:
        filename: Filename or full path (any extension).

    Returns:
        County name string.
    """
    basename = os.path.splitext(os.path.basename(filename))[0]
    parts = basename.split("_")
    for i, part in enumerate(parts):
        if re.match(r'^[a-z]{2}\d{3}$', part):
            return "_".join(parts[:i])
    return parts[0]


def parse_county_list(county_list_str: str) -> List[str]:
    """Parse a comma-separated county list string into a list of county names.

    Args:
        county_list_str: Comma-separated county names (e.g. "san_mateo,los_angeles").

    Returns:
        List of stripped, non-empty county name strings.
    """
    return [c.strip() for c in county_list_str.split(",") if c.strip()]


def filter_files_by_county(files: List[str], counties: List[str]) -> List[str]:
    """Filter a list of file paths to those belonging to the given counties.

    Args:
        files:    List of file paths.
        counties: List of county names to keep.

    Returns:
        Filtered list of file paths.
    """
    return [f for f in files if extract_county(f) in counties]
