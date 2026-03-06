from __future__ import annotations

import copy
import csv
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from osgeo import gdal

from src.extract.extract_cog_metadata import extract_cog_metadata
from src.extract.extract_raster_metadata import extract_raster_metadata

_TEMPLATE_PATH = Path(__file__).parent / "metadata_templates" / "template.json"

def _load_template() -> dict:
    with open(_TEMPLATE_PATH) as f:
        return json.load(f)


def _sha256(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()

def _gdal_version() -> str:
    return gdal.VersionInfo("RELEASE_NAME")

def _parse_filename(filename: str) -> dict:
    stem = Path(filename).stem
    parts = stem.split("_")
    return {
        "id": stem,
        "county": parts[0].capitalize() if parts else stem,
        "fips": parts[1] if len(parts) > 1 else None,
        "acquisition_year": parts[2] if len(parts) > 2 else None,
    }

def build_metadata(
    cog_path: str,
    *,
    county: str | None = None,
    fips: str | None = None,
    s3_uri: str | None = None,
    etag: str | None = None,
    http_uri: str | None = None,
    sid_name: str | None = None,
    geotiff_name: str | None = None,
    acquisition_date: str | None = None,
    collection: str | None = None,
    compute_checksum: bool = False,
) -> dict:
    meta = _load_template()
    filename = os.path.basename(cog_path)
    parsed = _parse_filename(filename)

    meta["id"] = parsed["id"]
    meta["county"] = county or parsed["county"]
    meta["fips"] = fips or parsed["fips"] or ""

    meta["uris"]["s3"] = s3_uri
    meta["uris"]["http"] = http_uri
    meta["uris"]["local"] = os.path.abspath(cog_path)

    raster = extract_raster_metadata(cog_path)
    meta["spatial"]["bbox"]       = raster["bbox"]
    meta["spatial"]["footprint"]  = raster["footprint"]
    meta["spatial"]["crs"]        = raster["crs"]
    meta["spatial"]["width"]      = raster["width"]
    meta["spatial"]["height"]     = raster["height"]
    meta["spatial"]["pixel_size"] = raster["pixel_size"]
    meta["spatial"]["transform"]  = raster["transform"]
    meta["raster"]["bands"]       = raster["bands"]
    meta["raster"]["dtype"]       = raster["dtype"]
    meta["raster"]["nodata"]      = raster["nodata"]
    meta["raster"]["colorinterp"] = raster["colorinterp"]

    cog = extract_cog_metadata(cog_path)
    meta["cog"].update(cog)

    if acquisition_date:
        meta["acquisition"]["date"] = acquisition_date
        meta["acquisition"]["source"] = "provided"
    elif parsed["acquisition_year"]:
        meta["acquisition"]["date"] = parsed["acquisition_year"]
        meta["acquisition"]["source"] = "filename"
  

    meta["integrity"]["file_size_bytes"] = os.path.getsize(cog_path)
    meta["integrity"]["etag"] = etag
    if compute_checksum:
        print(f"  Computing SHA-256 for {os.path.basename(cog_path)} (may be slow for large files)...")
        meta["integrity"]["checksum"]["algorithm"] = "sha256"
        meta["integrity"]["checksum"]["value"] = _sha256(cog_path)
    else:
        meta["integrity"]["checksum"]["algorithm"] = None
        meta["integrity"]["checksum"]["value"] = None

    meta["lineage"]["source"]["sid_name"]     = sid_name
    meta["lineage"]["source"]["geotiff_name"] = geotiff_name
    meta["lineage"]["processing"]["processed_at"]      = datetime.now(timezone.utc).isoformat()
    meta["lineage"]["processing"]["tools"]["python"]   = sys.version
    meta["lineage"]["processing"]["tools"]["gdal"]     = _gdal_version()

    if collection:
        meta["stac"]["collection"] = collection

    return meta

def write_metadata_json(metadata: dict, output_path: str) -> None:
    """Serialise *metadata* to a JSON sidecar at *output_path*."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"  Wrote metadata JSON → {output_path}")

_CSV_COLUMNS = [
    "id", "county", "fips", "s3_uri",
    "bbox_min_lon", "bbox_min_lat", "bbox_max_lon", "bbox_max_lat",
    "crs_epsg", "width", "height", "pixel_size_x", "pixel_size_y", "pixel_size_units",
    "bands", "dtype", "nodata",
    "acquisition_date", "acquisition_source",
    "file_size_bytes", "etag", "checksum_algorithm", "checksum_value",
    "cog_is_cog", "cog_layout", "cog_blocksize_x", "cog_blocksize_y",
    "cog_compression", "cog_interleave", "cog_overview_resampling", "cog_overview_count",
    "sid_name", "geotiff_name",
    "processed_at", "python_version", "gdal_version",
]


def _flatten_for_csv(metadata: dict) -> dict:
    bbox = metadata["spatial"]["bbox"]
    ps   = metadata["spatial"]["pixel_size"]
    cog  = metadata["cog"]
    return {
        "id":                   metadata["id"],
        "county":               metadata["county"],
        "fips":                 metadata["fips"],
        "s3_uri":               metadata["uris"]["s3"],
        "bbox_min_lon":         bbox[0],
        "bbox_min_lat":         bbox[1],
        "bbox_max_lon":         bbox[2],
        "bbox_max_lat":         bbox[3],
        "crs_epsg":             metadata["spatial"]["crs"]["epsg"],
        "width":                metadata["spatial"]["width"],
        "height":               metadata["spatial"]["height"],
        "pixel_size_x":         ps["x"],
        "pixel_size_y":         ps["y"],
        "pixel_size_units":     ps["units"],
        "bands":                metadata["raster"]["bands"],
        "dtype":                metadata["raster"]["dtype"],
        "nodata":               metadata["raster"]["nodata"],
        "acquisition_date":     metadata["acquisition"]["date"],
        "acquisition_source":   metadata["acquisition"]["source"],
        "file_size_bytes":      metadata["integrity"]["file_size_bytes"],
        "etag":                 metadata["integrity"]["etag"],
        "checksum_algorithm":   metadata["integrity"]["checksum"]["algorithm"],
        "checksum_value":       metadata["integrity"]["checksum"]["value"],
        "cog_is_cog":           cog["is_cog"],
        "cog_layout":           cog["layout"],
        "cog_blocksize_x":      cog["blocksize"]["x"],
        "cog_blocksize_y":      cog["blocksize"]["y"],
        "cog_compression":      cog["compression"],
        "cog_interleave":       cog["interleave"],
        "cog_overview_resampling": cog["overview_resampling"],
        "cog_overview_count":   len(cog["overview_levels"] or []),
        "sid_name":             metadata["lineage"]["source"]["sid_name"],
        "geotiff_name":         metadata["lineage"]["source"]["geotiff_name"],
        "processed_at":         metadata["lineage"]["processing"]["processed_at"],
        "python_version":       metadata["lineage"]["processing"]["tools"]["python"],
        "gdal_version":         metadata["lineage"]["processing"]["tools"]["gdal"],
    }


def append_metadata_csv(metadata: dict, csv_path: str) -> None:
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    file_exists = os.path.isfile(csv_path)
    row = _flatten_for_csv(metadata)
    with open(csv_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_COLUMNS, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    print(f"  Appended to CSV    → {csv_path}")
