"""Convert GeoTIFF (.tif) files to Cloud-Optimized GeoTIFF using GDAL."""

import glob
import os
import signal

from osgeo import gdal

from src.shared.check_if_file_exists import check_if_county_files_exist
from src.shared.parse_county import extract_county, filter_files_by_county
from src.shared.print_progress_bar import print_progress_bar
from src.convert.delete_tmp_files import delete_tmp_files
from typing import List
gdal.UseExceptions()

_cancel_requested = False


def _handle_sigint(signum, frame):
    global _cancel_requested
    _cancel_requested = True
    print("\nCancellation requested, stopping after current GDAL operation...")


def _gdal_progress(complete, message, data):
    """Print GDAL progress as a percentage. Returns 0 to cancel if Ctrl+C was pressed."""
    print(f"\r  COG conversion: {complete * 100:.0f}%", end="", flush=True)
    return 0 if _cancel_requested else 1


def geotiff_to_cog(geotiff_directory: str, cog_directory: str, counties: List[str]) -> bool:
    """Translate GeoTIFFs to COG format.

    Args:
        geotiff_directory: Directory containing .tif files.
        cog_directory:     Output directory for COG files.
        counties:          List of county names to include.

    Returns:
        True if all files converted successfully, False if any failed.
    """
    geotiffs = filter_files_by_county(
        glob.glob(os.path.join(geotiff_directory, "*.tif")), counties
    )
    total = len(geotiffs)
    failures = 0
    print_progress_bar(0, total, prefix='Progress:', suffix='Complete', length=50)

    global _cancel_requested
    _cancel_requested = False
    previous_sigint = signal.signal(signal.SIGINT, _handle_sigint)

    try:
        for i, filename in enumerate(geotiffs, start=1):
            if _cancel_requested:
                break
            county = extract_county(filename)
            if check_if_county_files_exist(county, cog_directory):
                print(f"  COGs for {county} already exist. Skipping.")
                continue
            print(f"\nProcessing {filename}...")
            cog_filename = os.path.join(
                cog_directory,
                os.path.basename(filename).replace(".tif", ".cog"),
            )
            try:
                gdal.Translate(cog_filename, filename, format='COG', creationOptions=['BIGTIFF=YES'], callback=_gdal_progress)
                print()
            except Exception as e:
                print(f"\nError converting {filename} to {cog_filename}: {e}")
                failures += 1
                continue
            print(f"Converted {filename} to {cog_filename}")
            print_progress_bar(i, total, prefix='Progress:', suffix='Complete', length=50)
    finally:
        signal.signal(signal.SIGINT, previous_sigint)

    delete_tmp_files(cog_directory)
    return failures == 0