"""Load step: upload COGs → extract metadata → upload metadata to S3.

Required environment variables:
    COG_DIRECTORY       - Directory containing .cog files to upload
    BUCKET_NAME         - Target S3 bucket
    STAC_COLLECTION     - STAC collection ID for metadata
    METADATA_DIRECTORY  - Local directory for metadata output
"""

import os

from src.load.cog_to_s3 import cog_to_s3
from src.load.metadata_to_s3 import metadata_to_s3
from src.extract.extract import run_extract
from src.shared.validate_env import validate_env

REQUIRED_ENV_VARS = [
    "COG_DIRECTORY",
    "BUCKET_NAME",
    "STAC_COLLECTION",
    "METADATA_DIRECTORY",
]


def run_load() -> bool:
    """Upload COGs to S3, extract metadata (using returned URIs), then upload metadata."""
    if not validate_env(REQUIRED_ENV_VARS):
        return False

    cog_dir = os.getenv("COG_DIRECTORY")
    bucket = os.getenv("BUCKET_NAME")
    prefix = "cogs"

    print("--- Load Step ---")

    print("[1/3] Uploading COGs to S3...")
    try:
        cog_uris = cog_to_s3(cog_dir, bucket, prefix)
    except RuntimeError as e:
        print(f"COG upload failed: {e} Aborting load step.")
        return False

    print("[2/3] Extracting metadata...")
    metadata = run_extract(cog_uris=cog_uris)
    if not metadata:
        print("Extract step returned no results. Aborting load step.")
        return False

    print("[3/3] Uploading metadata to S3...")
    metadata_to_s3()

    print("Load step complete.")
    return True
