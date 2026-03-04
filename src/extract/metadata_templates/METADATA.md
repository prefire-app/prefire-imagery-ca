# COG Metadata Schema

This document describes the per-COG metadata JSON written by the pipeline, based on the template in `template.json`.

## Goals

- Provide a stable, machine-readable metadata record **per COG** (JSON).
- Enable a lightweight **CSV summary** (one row per COG) derived from the JSON.
- Support generation of a **STAC Item** per COG (and optional collection/catalog) from the same source metadata.

## Conventions

- Unless otherwise noted:
  - Spatial coordinates in `bbox`/`footprint` are **WGS84 lon/lat (EPSG:4326)**.
  - Times use **ISO 8601** strings (e.g., `2026-03-02T17:45:00Z`).
  - `null` means “unknown/unavailable”. Prefer `null` over empty strings for unknown numeric/structured values.

## Top-level fields

### `id` (string, required)
Stable identifier for the COG (unique within the dataset). Typically derived from filename + county/fips + acquisition date if available.

### `county` (string, required)
County name (e.g., `Alameda`). Prefer a normalized form used consistently across the pipeline.

### `fips` (string, required)
County FIPS code (string to preserve leading zeros).

## `uris`
URIs/paths pointing to the COG.

- `uris.s3` (string | null): canonical S3 URI, e.g., `s3://bucket/path/file.tif`.
- `uris.http` (string | null): HTTP URL if available (e.g., CloudFront).
- `uris.local` (string | null): local path when running locally.

## `spatial`
Spatial and georeferencing information.

### `spatial.bbox` (array[4] of number, required)
Bounding box in EPSG:4326: `[minLon, minLat, maxLon, maxLat]`.

**Source**: derived from the raster geotransform/extent reprojected to EPSG:4326.

### `spatial.footprint` (GeoJSON Polygon, required)
Footprint geometry in EPSG:4326.

- Minimum implementation: footprint is the bbox polygon.
- Optional enhancement: tighter footprint derived from alpha/nodata mask polygonization.

### `spatial.crs`
- `spatial.crs.epsg` (number | null): EPSG code if known (e.g., `26910`).
- `spatial.crs.wkt` (string | null): WKT representation of CRS.

**Source**: from GDAL/rasterio dataset CRS.

### `spatial.width`, `spatial.height` (integer | null)
Raster dimensions in pixels.

### `spatial.pixel_size`
- `spatial.pixel_size.x` (number | null): pixel width in CRS units.
- `spatial.pixel_size.y` (number | null): pixel height in CRS units (often negative in GDAL geotransform; store the signed value or absolute value consistently).
- `spatial.pixel_size.units` (string | null): units (e.g., `metre`, `degree`) if known.

### `spatial.transform` (array | string | null)
Dataset geotransform. Common representations:
- GDAL 6-element geotransform array
- or a stringified representation

Pick one representation and keep it consistent.

## `raster`
Raster band structure.

- `raster.bands` (integer | null): number of bands.
- `raster.dtype` (string | null): data type (e.g., `Byte`, `UInt16`, `Float32`).
- `raster.nodata` (number | null): nodata value if defined.
- `raster.colorinterp` (array[string] | null): per-band interpretation, e.g., `["Red","Green","Blue","Alpha"]`.

**Source**: from GDAL/rasterio band metadata.

## `acquisition`
Capture/observation date.

- `acquisition.datetime` (string | null): ISO 8601 datetime if available.
- `acquisition.date` (string | null): ISO date (`YYYY-MM-DD`) when time-of-day is unknown.
- `acquisition.source` (string | null): where it came from (e.g., `sid_header`, `filename`, `delivery_manifest`, `geotiff_tag`).

**Recommendation**: extract this as early as possible (SID or delivery manifest) and propagate forward.

## `integrity`
Integrity and size.

- `integrity.file_size_bytes` (integer | null): file size.
  - Local: filesystem stat
  - S3: `ContentLength`
- `integrity.etag` (string | null): S3 ETag if sourced from S3.
  - Note: multipart uploads can make ETag != MD5.
- `integrity.checksum`:
  - `algorithm` (string | null): e.g., `sha256`
  - `value` (string | null): hex digest

**Recommendation**: if you need strong integrity guarantees, compute and store a real checksum (e.g., sha256).

## `cog`
COG validity/performance-related internals.

- `cog.is_cog` (boolean | null): whether validation indicates it is a COG.
- `cog.layout` (string | null): expected `COG`.
- `cog.blocksize`:
  - `x` (integer | null)
  - `y` (integer | null)
- `cog.compression` (string | null): e.g., `LZW`, `DEFLATE`.
- `cog.interleave` (string | null): e.g., `PIXEL`, `BAND`.
- `cog.overview_resampling` (string | null): e.g., `NEAREST`, `CUBIC`.
- `cog.overview_levels` (array | null): overview sizes or decimation factors.

**Source**: from `gdalinfo` Image Structure metadata and overview info.

## `lineage`
Provenance tracking.

### `lineage.source`
- `lineage.source.sid_name` (string | null): original SID filename.
- `lineage.source.geotiff_name` (string | null): intermediate GeoTIFF filename (if any).

### `lineage.processing`
- `lineage.processing.processed_at` (string | null): ISO timestamp of processing.
- `lineage.processing.tools`:
  - `python` (string | null): Python version.
  - `gdal` (string | null): GDAL version.
- `lineage.processing.commands` (array | string | null): key commands or a structured config reference.

**Recommendation**: capture lineage early and carry it forward; conversions can drop metadata tags.

## `stac`
Pointers and conventions for STAC generation.

- `stac.item_path` (string | null): where the STAC Item JSON is written.
- `stac.collection` (string | null): collection id/name.
- `stac.asset_key` (string, required): asset key to use for the COG (default `data`).

## CSV summary guidance

The CSV should be derived from the JSON by flattening a stable subset of fields, e.g.:

- `id`, `county`, `fips`
- `s3_uri` (from `uris.s3`)
- `bbox_min_lon`, `bbox_min_lat`, `bbox_max_lon`, `bbox_max_lat`
- `crs_epsg`, `width`, `height`, `pixel_size_x`, `pixel_size_y`
- `bands`, `dtype`, `nodata`
- `acquisition_date`/`acquisition_datetime`
- `file_size_bytes`, `etag`, `checksum_algorithm`, `checksum_value`
- `cog_blocksize_x`, `cog_blocksize_y`, `cog_compression`, `cog_overview_count`

Keep the CSV schema versioned (even if just via a header comment in code) to avoid silent breaking changes.
