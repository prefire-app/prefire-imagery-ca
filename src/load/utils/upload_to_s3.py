"""Generic S3 upload helper."""

import boto3


def upload_to_s3(file_path: str, bucket_name: str, object_name: str) -> None:
    """Upload a single file to S3.

    Args:
        file_path:   Local path to the file.
        bucket_name: Target S3 bucket.
        object_name: S3 object key.
    """
    s3_client = boto3.client("s3")
    try:
        s3_client.upload_file(file_path, bucket_name, object_name)
        print(f"Uploaded {file_path} → s3://{bucket_name}/{object_name}")
    except Exception as e:
        print(f"Error uploading {file_path}: {e}")
        raise