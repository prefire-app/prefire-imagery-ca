from dotenv import load_dotenv
import os
from src.convert.sid_to_geotiff import sid_to_geotiff
from src.convert.geotiff_to_cog import geotiff_to_cog

def main():
    '''
    Main function to run the convert pipeline
    '''
    load_dotenv()

    print("Running the convert pipeline...")
    sid_to_geotiff(os.getenv("SID_DIRECTORY"), os.getenv("GEOTIFF_DIRECTORY"), os.getenv("COUNTY_LIST"))
    geotiff_to_cog(os.getenv("GEOTIFF_DIRECTORY"), os.getenv("COG_DIRECTORY"))

if __name__ == "__main__":
    main()