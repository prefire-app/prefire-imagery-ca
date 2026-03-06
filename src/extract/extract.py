"""extract.py

Orchestrates the metadata-extraction pipeline for a directory of COGs.

For each *.cog file found in COG_DIRECTORY it:
  1. Reads core raster/spatial metadata       (extract_raster_metadata)
  2. Reads COG-internals                      (extract_cog_metadata)
  3. Assembles the full metadata dict         (build_metadata)
  4. Writes a per-COG JSON sidecar            (write_metadata_json)
  5. Appends a row to the shared CSV summary  (append_metadata_csv)
  6. Builds and writes a STAC Item            (build_stac_item / write_stac_item)

Output layout inside METADATA_DIRECTORY (env var, defaults to ../metadata):
  json/          — one <id>.json per COG
  stac/          — one <id>.stac.json per COG
  summary.csv    — flat CSV summary, one row per COG
"""

from __future__ import annotations

import glob
import os
from pathlib import Path

from dotenv import load_dotenv

from src.shared.validate_env import validate_env
from src.extract.create_metadata import build_metadata, write_metadata_json, append_metadata_csv
from src.extract.create_stac import build_stac_item, write_stac_item


# per cog helper
def extract_cog(
    cog_path: str,
    output_dir: str,
    *,
    s3_uri: str | None = None,
    etag: str | None = None,
    http_uri: str | None = None,
    sid_name: str | None = None,
    geotiff_name: str | None = None,
    acquisition_date: str | None = None,
    collection: str | None = None,
) -> dict:
    stem = Path(cog_path).stem


    metadata = build_metadata(
        cog_path,
        s3_uri=s3_uri,
        etag=etag,
        http_uri=http_uri,
        sid_name=sid_name,
        geotiff_name=geotiff_name,
        acquisition_date=acquisition_date,
        collection=collection,
        compute_checksum=False
    )

    json_path = os.path.join(output_dir, "json",  f"{stem}.json")
    stac_path = os.path.join(output_dir, "stac",  f"{stem}.stac.json")
    csv_path  = os.path.join(output_dir, "summary.csv")

    metadata["stac"]["item_path"] = stac_path

    write_metadata_json(metadata, json_path)
    append_metadata_csv(metadata, csv_path)
    write_stac_item(build_stac_item(metadata), stac_path)

    return metadata


def main(
    cog_uris: dict[str, dict] | None = None,
    collection: str | None = None,
) -> list[dict]:
    load_dotenv()
    if not validate_env():
        return []

    cog_directory = os.getenv("COG_DIRECTORY", "")
    default_metadata_dir = os.path.abspath(
        os.path.join(cog_directory, "..", "metadata")
    )
    output_dir = os.path.abspath(
        os.getenv("METADATA_DIRECTORY", default_metadata_dir)
    )
    cog_uris = cog_uris or {}

    cogs = sorted(glob.glob(os.path.join(cog_directory, "*.cog")))
    if not cogs:
        print(f"No *.cog files found in: {cog_directory}")
        return []

    print(f"Extracting metadata for {len(cogs)} COG(s) → {output_dir}")
    results: list[dict] = []

    for i, cog_path in enumerate(cogs, 1):
        fname = os.path.basename(cog_path)
        print(f"[{i}/{len(cogs)}] {fname}")
        uri_info = cog_uris.get(fname, {})
        try:
            meta = extract_cog(
                cog_path,
                output_dir,
                s3_uri=uri_info.get("s3_uri"),
                etag=uri_info.get("etag"),
                collection=collection,
            )
            results.append(meta)
        except Exception as exc:
            print(f"  ERROR processing {fname}: {exc}")

    print(f"Done. {len(results)}/{len(cogs)} COG(s) processed.")
    return results


if __name__ == "__main__":
    main()
