"""Validate COG files using rio cogeo."""

import glob
import os
import subprocess


def validate_cogs(cog_directory: str) -> bool:
    """Run ``rio cogeo validate`` on every .cog file in *cog_directory*.

    Args:
        cog_directory: Directory containing .cog files to validate.

    Returns:
        True if all COGs are valid, False if any failed validation.
    """
    cogs = glob.glob(os.path.join(cog_directory, "*.cog"))
    total = len(cogs)
    failures = 0
    print(f"Validating {total} COG files...")

    for i, filename in enumerate(cogs, start=1):
        try:
            result = subprocess.run(
                ["rio", "cogeo", "validate", filename],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            if "is a valid cloud optimized GeoTIFF" in result.stdout:
                print(f"{filename} is a valid COG.")
            elif "is NOT a valid cloud optimized GeoTIFF" in result.stdout:
                raise ValueError(f"{filename} is NOT a valid COG.")
        except Exception as e:
            print(f"Error validating {filename}: {e}")
            failures += 1
    return failures == 0

