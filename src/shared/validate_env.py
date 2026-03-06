
import os

def validate_env():
    required_env_vars = ["SID_DIRECTORY", "GEOTIFF_DIRECTORY", "COG_DIRECTORY", "COUNTY_LIST"]
    missing_env_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_env_vars:
        print(f"Error: Missing required environment variables: {', '.join(missing_env_vars)}. Please check your .env file.")
        return False
    
    return True