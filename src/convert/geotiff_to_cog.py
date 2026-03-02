
from osgeo import gdal
import subprocess
import glob
import os

from src.shared.print_progress_bar import print_progress_bar

def geotiff_to_cog(geotiff_directory, cog_directory):
    geotiffs = glob.glob(os.path.join(geotiff_directory, "*.tif"))
    total = len(geotiffs)
    print_progress_bar(0, total, prefix='Progress:', suffix='Complete', length=50)
    for i, filename in enumerate(geotiffs, start=1):
        print(f"\nProcessing {filename}...")
        cog_filename = os.path.join(cog_directory, os.path.basename(filename).replace(".tif", "_cog.tif"))
        try:
            gdal.Translate(cog_filename, filename, format='COG', creationOptions=['BIGTIFF=YES'])
        except Exception as e:
            print(f"Error converting {filename} to {cog_filename}: {e}")
        print(f"Converted {filename} to {cog_filename}")
        print_progress_bar(i, total, prefix='Progress:', suffix='Complete', length=50)

    print("All files processed (GeoTIFF -> COG).")