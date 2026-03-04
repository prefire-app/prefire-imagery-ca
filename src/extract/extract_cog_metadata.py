"""extract_cog_metadata.py

Reads COG-specific internals from a GeoTIFF IMAGE_STRUCTURE metadata domain.
Extracted fields:
  - is_cog (bool): whether LAYOUT == 'COG'
  - layout, compression, interleave, overview_resampling
  - blocksize (x, y) from the first band
  - overview_levels: list of [width, height] per overview level
"""

from __future__ import annotations

from osgeo import gdal

gdal.UseExceptions()


def extract_cog_metadata(cog_path: str) -> dict:
    """Return a dict of COG-internals metadata extracted from *cog_path*.

    Raises:
        IOError: if GDAL cannot open the file.
    """
    ds = gdal.Open(cog_path, gdal.GA_ReadOnly)
    if ds is None:
        raise IOError(f"GDAL could not open: {cog_path}")

    img_struct = ds.GetMetadata("IMAGE_STRUCTURE") or {}

    layout = img_struct.get("LAYOUT")
    is_cog = layout == "COG"
    compression = img_struct.get("COMPRESSION")
    interleave = img_struct.get("INTERLEAVE")
    overview_resampling = img_struct.get("OVERVIEW_RESAMPLING")

    # Blocksize from the first band
    band1 = ds.GetRasterBand(1)
    block_x, block_y = band1.GetBlockSize()

    # Overview levels as [[width, height], ...]
    overview_levels = [
        [band1.GetOverview(i).XSize, band1.GetOverview(i).YSize]
        for i in range(band1.GetOverviewCount())
    ]

    ds = None  # close dataset

    return {
        "is_cog": is_cog,
        "layout": layout,
        "blocksize": {"x": block_x, "y": block_y},
        "compression": compression,
        "interleave": interleave,
        "overview_resampling": overview_resampling,
        "overview_levels": overview_levels,
    }
