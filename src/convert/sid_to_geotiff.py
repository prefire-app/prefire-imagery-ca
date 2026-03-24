"""Convert MrSID (.sid) files to GeoTIFF (.tif) using mrsidgeodecode."""

import glob
import os
import subprocess

from src.convert.delete_tmp_files import delete_tmp_files
from src.shared.check_if_file_exists import check_if_county_files_exist
from src.shared.parse_county import extract_county, filter_files_by_county
from src.shared.print_progress_bar import print_progress_bar
from typing import List


def sid_to_geotiff(sid_directory: str, geotiff_directory: str, counties: List[str]) -> bool:
    """Decode MrSID files to GeoTIFF for the specified counties.

    Args:
        sid_directory:     Directory containing .sid files.
        geotiff_directory: Output directory for .tif files.
        counties:          List of county names to include.

    Returns:
        True if all files converted successfully, False if any failed.
    """
    all_sid_files = glob.glob(os.path.join(sid_directory, "*.sid"))
    sid_files = filter_files_by_county(all_sid_files, counties)
    total = len(sid_files)
    failures = 0
    print_progress_bar(0, total, prefix='Progress:', suffix='Complete', length=50)

    for i, filename in enumerate(sid_files, start=1):
        county = extract_county(filename)
        if check_if_county_files_exist(county, geotiff_directory):
            print(f"  GeoTIFFs for {county} already exist. Skipping.")
            continue

        print(f"\nProcessing {filename}...")
        geotiff_filename = os.path.join(
            geotiff_directory,
            os.path.basename(filename).replace(".sid", ".tif"),
        )
        result = subprocess.run(["mrsidgeodecode", "-i", filename, "-o", geotiff_filename])
        if result.returncode != 0:
            print(f"  ERROR converting {filename} (exit code {result.returncode})")
            failures += 1
        else:
            print(f"Converted {filename} to {geotiff_filename}")
        print_progress_bar(i, total, prefix='Progress:', suffix='Complete', length=50)
    delete_tmp_files(geotiff_directory)
    return failures == 0