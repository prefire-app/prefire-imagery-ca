from __future__ import annotations

import json
import os

STAC_VERSION = "1.0.0"
_EXTENSIONS = [
    "https://stac-extensions.github.io/projection/v1.1.0/schema.json",
]

def build_stac_item(metadata: dict) -> dict:
    spatial   = metadata["spatial"]
    raster    = metadata["raster"]
    cog       = metadata["cog"]
    acq       = metadata["acquisition"]
    lineage   = metadata["lineage"]
    stac_cfg  = metadata["stac"]
    uris      = metadata["uris"]

    stac_datetime = acq.get("datetime") or acq.get("date") or None

    asset_href = uris.get("s3") or uris.get("http") or uris.get("local")

    item: dict = {
        "type": "Feature",
        "stac_version": STAC_VERSION,
        "stac_extensions": _EXTENSIONS,
        "id": metadata["id"],
        "bbox": spatial["bbox"],
        "geometry": spatial["footprint"],
        "properties": {
            "datetime": stac_datetime,
            "created":  lineage["processing"]["processed_at"],
            "county": metadata["county"],
            "fips":   metadata["fips"],
            "proj:epsg":      spatial["crs"]["epsg"],
            "proj:wkt2":      spatial["crs"]["wkt"],
            "proj:shape":     [spatial["height"], spatial["width"]],   
            "proj:transform": spatial["transform"],
            "gsd":    spatial["pixel_size"]["x"],   
            "bands":  raster["bands"],
            "dtype":  raster["dtype"],
            "cog:is_cog":             cog["is_cog"],
            "cog:blocksize_x":        cog["blocksize"]["x"],
            "cog:blocksize_y":        cog["blocksize"]["y"],
            "cog:compression":        cog["compression"],
            "cog:interleave":         cog["interleave"],
            "cog:overview_resampling": cog["overview_resampling"],
            "cog:overview_count":     len(cog["overview_levels"] or []),
            "lineage:sid_name":        lineage["source"]["sid_name"],
            "lineage:geotiff_name":    lineage["source"]["geotiff_name"],
            "lineage:processed_at":    lineage["processing"]["processed_at"],
        },
        "assets": {
            stac_cfg["asset_key"]: {
                "href": asset_href,
                "type": "image/tiff; application=geotiff; profile=cloud-optimized",
                "roles": ["data"],
                "title": metadata["id"],
            }
        },
        "links": [],
    }

    if stac_cfg.get("collection"):
        item["collection"] = stac_cfg["collection"]

    return item

def write_stac_item(stac_item: dict, output_path: str) -> None:
    """Serialise *stac_item* to JSON at *output_path*."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(stac_item, f, indent=2)
    print(f"  Wrote STAC Item    → {output_path}")
