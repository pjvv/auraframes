"""SQS client for receiving frame update messages."""
from typing import Any

import boto3

from auraframes.aws.aws_client import AWSClient
from auraframes.exceptions import ConfigurationError
from auraframes.utils.settings import AWS_SQS_IDENTITY_POOL_ID


class SQSClient(AWSClient):
    """SQS client for polling frame update queues."""

    def __init__(self, pool_id: str | None = None, region_name: str = 'us-east-1'):
        """
        Initialize SQS client with Cognito identity pool.

        :param pool_id: Cognito Identity Pool ID (defaults to AWS_SQS_IDENTITY_POOL_ID env var)
        :param region_name: AWS region (default us-east-1)
        :raises ConfigurationError: If pool_id not provided and env var not set
        """
        effective_pool_id = pool_id or AWS_SQS_IDENTITY_POOL_ID
        if not effective_pool_id:
            raise ConfigurationError(
                "AWS_SQS_IDENTITY_POOL_ID environment variable is required for SQS operations"
            )
        self._sqs_client = None
        super().__init__(effective_pool_id, region_name)

    def _get_sqs_client(self):
        """Get SQS client, recreating if credentials were refreshed."""
        # Always check credentials and refresh if needed
        self.refresh_if_needed()

        # Recreate client if credentials changed or not created yet
        if self._sqs_client is None:
            creds = self.credentials
            self._sqs_client = boto3.client(
                'sqs',
                aws_access_key_id=creds['AccessKeyId'],
                aws_secret_access_key=creds['SecretKey'],
                aws_session_token=creds['SessionToken'],
                region_name=self.region_name
            )
        return self._sqs_client

    def _refresh_credentials(self) -> None:
        """Override to invalidate SQS client when credentials refresh."""
        super()._refresh_credentials()
        self._sqs_client = None  # Force recreation on next use

    def get_queue_url(self, frame_id: str) -> str:
        """
        Get the SQS queue URL for a frame.

        :param frame_id: Frame ID
        :return: Queue URL
        """
        return self._get_sqs_client().get_queue_url(
            QueueName=f'frame-{frame_id}-client'
        ).get('QueueUrl')

    def receive_message(
        self,
        queue_url: str,
        max_num_messages: int = 10,
        wait_time_seconds: int = 20
    ) -> dict[str, Any]:
        """
        Receive messages from SQS queue.

        :param queue_url: Queue URL to poll
        :param max_num_messages: Maximum messages to receive (default 10)
        :param wait_time_seconds: Long polling timeout (default 20)
        :return: SQS receive_message response
        """
        return self._get_sqs_client().receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=max_num_messages,
            WaitTimeSeconds=wait_time_seconds,
            AttributeNames=['All']
        )
