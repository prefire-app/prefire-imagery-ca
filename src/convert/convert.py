"""Convert step: SID → GeoTIFF → COG → validate.

Required environment variables:
    SID_DIRECTORY      - Directory containing .sid files
    GEOTIFF_DIRECTORY  - Output directory for GeoTIFF files
    COG_DIRECTORY      - Output directory for COG files
    COUNTY_LIST        - Comma-separated list of counties to process
"""

import os

from src.convert.sid_to_geotiff import sid_to_geotiff
from src.convert.geotiff_to_cog import geotiff_to_cog
from src.convert.validate_cogs import validate_cogs
from src.shared.validate_env import validate_env
from src.shared.parse_county import parse_county_list

REQUIRED_ENV_VARS = [
    "SID_DIRECTORY",
    "GEOTIFF_DIRECTORY",
    "COG_DIRECTORY",
    "COUNTY_LIST",
]


def run_convert() -> bool:
    """Run the full convert pipeline: SID → GeoTIFF → COG → validate."""
    if not validate_env(REQUIRED_ENV_VARS):
        return False

    sid_dir = os.getenv("SID_DIRECTORY")
    geotiff_dir = os.getenv("GEOTIFF_DIRECTORY")
    cog_dir = os.getenv("COG_DIRECTORY")
    counties = parse_county_list(os.getenv("COUNTY_LIST", ""))

    print("--- Convert Step ---")
    print(f"Processing {len(counties)} county/counties: {', '.join(counties)}")

    print("[1/3] Converting SID files to GeoTIFF...")
    if not sid_to_geotiff(sid_dir, geotiff_dir, counties):
        print("SID → GeoTIFF conversion failed. Aborting convert step.")
        return False

    print("[2/3] Converting GeoTIFF files to COG...")
    if not geotiff_to_cog(geotiff_dir, cog_dir, counties):
        print("GeoTIFF → COG conversion failed. Aborting convert step.")
        return False

    print("[3/3] Validating COG files...")
    if not validate_cogs(cog_dir):
        print("COG validation failed. Aborting convert step.")
        return False

    print("Convert step complete.")
    return True