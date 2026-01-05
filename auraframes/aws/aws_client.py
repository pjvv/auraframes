"""AWS Cognito client for unauthenticated identity pool access."""
from datetime import datetime, timezone

import boto3
import botocore

from loguru import logger

SESSION_CONFIG = botocore.config.Config(
    user_agent="aws-sdk-android/2.13.1 Linux/5.4.61-android11 Dalvik/2.1.0/0 en_US"
)

# Refresh credentials 5 minutes before expiration
CREDENTIAL_REFRESH_BUFFER_SECONDS = 300


class AWSClient:
    """Base AWS client with Cognito identity pool authentication."""

    def __init__(self, pool_id: str | None = None, region_name: str = 'us-east-1'):
        """
        Initialize AWS client with optional Cognito identity pool.

        :param pool_id: Cognito Identity Pool ID (if provided, authenticates immediately)
        :param region_name: AWS region (default us-east-1)
        """
        self.region_name = region_name
        self.cognito = boto3.client('cognito-identity', region_name=self.region_name)
        self._pool_id: str | None = None
        self._identity_id: str | None = None
        self._credentials: dict | None = None
        self._credentials_expiration: datetime | None = None

        if pool_id:
            self.auth(pool_id)

    def auth(self, pool_id: str) -> None:
        """
        Authenticate with Cognito identity pool and obtain temporary credentials.

        :param pool_id: Cognito Identity Pool ID
        """
        self._pool_id = pool_id
        ident_resp = self.cognito.get_id(IdentityPoolId=pool_id)
        self._identity_id = ident_resp['IdentityId']
        self._refresh_credentials()

    def _refresh_credentials(self) -> None:
        """Refresh temporary AWS credentials from Cognito."""
        if not self._identity_id:
            raise RuntimeError("Cannot refresh credentials without identity. Call auth() first.")

        logger.debug(f"Refreshing AWS credentials for identity {self._identity_id}")
        cred_resp = self.cognito.get_credentials_for_identity(IdentityId=self._identity_id)
        self._credentials = cred_resp['Credentials']
        self._credentials_expiration = cred_resp['Credentials']['Expiration']
        logger.debug(f"Credentials refreshed, expires at {self._credentials_expiration}")

    def is_credentials_expired(self) -> bool:
        """
        Check if credentials are expired or will expire soon.

        :return: True if credentials need refresh
        """
        if not self._credentials_expiration:
            return True

        # Refresh if within buffer period of expiration
        now = datetime.now(timezone.utc)
        expiration = self._credentials_expiration
        if expiration.tzinfo is None:
            expiration = expiration.replace(tzinfo=timezone.utc)

        time_until_expiry = (expiration - now).total_seconds()
        return time_until_expiry < CREDENTIAL_REFRESH_BUFFER_SECONDS

    def refresh_if_needed(self) -> None:
        """Refresh credentials if expired or about to expire."""
        if self.is_credentials_expired():
            self._refresh_credentials()

    @property
    def credentials(self) -> dict:
        """
        Get current credentials, refreshing if needed.

        :return: AWS credentials dict with AccessKeyId, SecretKey, SessionToken
        """
        self.refresh_if_needed()
        if not self._credentials:
            raise RuntimeError("No credentials available. Call auth() first.")
        return self._credentials
