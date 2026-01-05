"""S3 client for uploading images to Aura's bucket."""
import base64
import hashlib
import uuid

import boto3

from auraframes.aws.aws_client import AWSClient
from auraframes.exceptions import ConfigurationError
from auraframes.utils.settings import AWS_UPLOAD_IDENTITY_POOL_ID

BUCKET_KEY = 'images.senseapp.co'
AWS_UPLOAD_PART_SIZE = 16384


def get_md5(data: bytes) -> str:
    """Calculate base64-encoded MD5 hash of data."""
    return base64.b64encode(hashlib.md5(data).digest()).decode('utf-8')


class S3Client(AWSClient):
    """S3 client for uploading images to Aura's image bucket."""

    def __init__(self, pool_id: str | None = None, region_name: str = 'us-east-1'):
        """
        Initialize S3 client with Cognito identity pool.

        :param pool_id: Cognito Identity Pool ID (defaults to AWS_UPLOAD_IDENTITY_POOL_ID env var)
        :param region_name: AWS region (default us-east-1)
        :raises ConfigurationError: If pool_id not provided and env var not set
        """
        effective_pool_id = pool_id or AWS_UPLOAD_IDENTITY_POOL_ID
        if not effective_pool_id:
            raise ConfigurationError(
                "AWS_UPLOAD_IDENTITY_POOL_ID environment variable is required for S3 uploads"
            )
        self._s3_client = None
        super().__init__(effective_pool_id, region_name)

    def _get_s3_client(self):
        """Get S3 client, recreating if credentials were refreshed."""
        # Always check credentials and refresh if needed
        self.refresh_if_needed()

        # Recreate client if credentials changed or not created yet
        if self._s3_client is None:
            creds = self.credentials
            self._s3_client = boto3.client(
                's3',
                aws_access_key_id=creds['AccessKeyId'],
                aws_secret_access_key=creds['SecretKey'],
                aws_session_token=creds['SessionToken']
            )
        return self._s3_client

    def _refresh_credentials(self) -> None:
        """Override to invalidate S3 client when credentials refresh."""
        super()._refresh_credentials()
        self._s3_client = None  # Force recreation on next use

    def upload_file(self, data: bytes, extension: str) -> tuple[str, str]:
        """
        Upload file data to S3.

        :param data: File data as bytes
        :param extension: File extension (e.g., '.jpg')
        :return: Tuple of (filename, md5_hash)
        """
        filename = f'{str(uuid.uuid4())}{extension}'
        self._get_s3_client().put_object(Body=data, Bucket=BUCKET_KEY, Key=filename)
        return filename, get_md5(data)

    def get_file(self, filename: str) -> dict:
        """
        Get file metadata from S3.

        :param filename: S3 object key
        :return: S3 head_object response
        """
        return self._get_s3_client().head_object(Bucket=BUCKET_KEY, Key=filename)
