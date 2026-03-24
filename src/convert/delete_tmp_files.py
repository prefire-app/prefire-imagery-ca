"""
On conversion error, delete the temporary files created during the conversion process to prevent clutter and potential confusion in future conversions. 
"""

import os

def delete_tmp_files(dir_path: str):
    """Delete temporary files in the specified directory."""
    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.__contains__('tmp'):
                tmp_file_path = os.path.join(root, file)
                try:
                    os.remove(tmp_file_path)
                    print(f"Deleted temporary file: {tmp_file_path}")
                except Exception as e:
                    print(f"Error deleting file {tmp_file_path}: {e}")