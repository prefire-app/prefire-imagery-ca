"""Upload COG files to S3 and return a URI / ETag map."""

import glob
import os

import boto3

from src.load.utils.upload_to_s3 import upload_to_s3
from src.shared.parse_county import extract_county


def _existing_counties(s3_client, bucket_name: str, prefix: str) -> set[str]:
    """Return the set of county names already present under *prefix* in S3."""
    counties: set[str] = set()
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket_name, Prefix=f"{prefix}/"):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            fname = key.rsplit("/", 1)[-1]
            county = extract_county(fname)
            if county:
                counties.add(county)
    return counties


def cog_to_s3(cog_directory: str, bucket_name: str, prefix: str) -> dict[str, dict]:
    """Upload every .cog in *cog_directory* to S3, skipping counties already present.

    Args:
        cog_directory: Local directory containing .cog files.
        bucket_name:   Target S3 bucket.
        prefix:        S3 key prefix (e.g. "cogs").

    Returns:
        Dict mapping filename → {"s3_uri": ..., "etag": ...}.
    """
    s3_client = boto3.client("s3")
    cogs = sorted(glob.glob(os.path.join(cog_directory, "*.cog")))

    existing = _existing_counties(s3_client, bucket_name, prefix)
    to_upload = []
    for cog in cogs:
        county = extract_county(os.path.basename(cog))
        if county in existing:
            print(f"Skipping {os.path.basename(cog)} (county '{county}' already in S3)")
        else:
            to_upload.append(cog)

    total = len(to_upload)
    uri_map: dict[str, dict] = {}
    failures = 0

    for i, cog in enumerate(to_upload, 1):
        fname = os.path.basename(cog)
        object_name = f"{prefix}/{fname}"
        try:
            print(f"[{i}/{total}] Uploading {fname} → s3://{bucket_name}/{object_name}")
            upload_to_s3(cog, bucket_name, object_name)
            head = s3_client.head_object(Bucket=bucket_name, Key=object_name)
            uri_map[fname] = {
                "s3_uri": f"s3://{bucket_name}/{object_name}",
                "etag":   head.get("ETag", "").strip('"'),
            }
        except Exception as e:
            print(f"  ERROR uploading {fname}: {e}")
            failures += 1

    if failures:
        raise RuntimeError(f"{failures}/{total} COG(s) failed to upload to S3.")
    return uri_map
