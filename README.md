# prefire - **California Geospatial Data Lake Pipeline**

This repo is an orchestrator for the scripts used for the **California Geospatial Data Lake Pipeline**

## Convert

### convert.py

Main script for orchestrating convertions between files types ultimately going from MrSID to GeoTIFF to COG.

### sid_to_geotiff.py

Script for converting MrSID to GeoTIFF

### geotiff_to_cog.py

Script for converting GeoTIFF to Cloud Optimized GeoTIFF

## Extract

You can rename the current file by clicking the file name in the navigation bar or by clicking the **Rename** button in the file explorer.

## Load

You can delete the current file by clicking the **Remove** button in the file explorer. The file will be moved into the **Trash** folder and automatically deleted after 7 days of inactivity.
