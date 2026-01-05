"""
Aura Frames Configuration Settings.

Uses Pydantic Settings for type-safe configuration with environment variable support.

Required environment variables:
- AURA_EMAIL: Account email for authentication
- AURA_PASSWORD: Account password for authentication

Optional environment variables (with defaults):
- AURA_LOCALE: Locale string (default: 'en-US')
- AURA_APP_IDENTIFIER: App identifier (default: 'com.pushd.client')
- AURA_DEVICE_IDENTIFIER: Device identifier (default: '0000000000000000')
- AURA_IMAGE_PROXY_URL: Image proxy base URL (default: 'https://imgproxy.pushd.com')
- AURA_DEBUG: Enable debug logging (default: false)
- AWS_UPLOAD_IDENTITY_POOL_ID: AWS Cognito pool for S3 uploads (optional)
- AWS_SQS_IDENTITY_POOL_ID: AWS Cognito pool for SQS (optional)
"""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',
    )

    # Device emulation settings
    locale: str = Field(default='en-US', alias='AURA_LOCALE')
    app_identifier: str = Field(default='com.pushd.client', alias='AURA_APP_IDENTIFIER')
    device_identifier: str = Field(default='0000000000000000', alias='AURA_DEVICE_IDENTIFIER')

    # API settings
    image_proxy_base_url: str = Field(
        default='https://imgproxy.pushd.com',
        alias='AURA_IMAGE_PROXY_URL'
    )

    # Debug settings
    debug: bool = Field(default=False, alias='AURA_DEBUG')

    # AWS Configuration (optional - only needed for upload functionality)
    aws_upload_identity_pool_id: str | None = Field(
        default=None,
        alias='AWS_UPLOAD_IDENTITY_POOL_ID'
    )
    aws_sqs_identity_pool_id: str | None = Field(
        default=None,
        alias='AWS_SQS_IDENTITY_POOL_ID'
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Backwards-compatible module-level exports
# These access the settings lazily to avoid import-time env var requirements
def _get_locale() -> str:
    return get_settings().locale


def _get_app_identifier() -> str:
    return get_settings().app_identifier


def _get_device_identifier() -> str:
    return get_settings().device_identifier


def _get_image_proxy_base_url() -> str:
    return get_settings().image_proxy_base_url


def _get_aws_upload_pool_id() -> str | None:
    return get_settings().aws_upload_identity_pool_id


def _get_aws_sqs_pool_id() -> str | None:
    return get_settings().aws_sqs_identity_pool_id


# Legacy module-level constants for backwards compatibility
# These are evaluated lazily via __getattr__
_LEGACY_ATTRS = {
    'LOCALE': _get_locale,
    'AURA_APP_IDENTIFIER': _get_app_identifier,
    'DEVICE_IDENTIFIER': _get_device_identifier,
    'IMAGE_PROXY_BASE_URL': _get_image_proxy_base_url,
    'AWS_UPLOAD_IDENTITY_POOL_ID': _get_aws_upload_pool_id,
    'AWS_SQS_IDENTITY_POOL_ID': _get_aws_sqs_pool_id,
}


def __getattr__(name: str):
    """Lazy attribute access for backwards compatibility."""
    if name in _LEGACY_ATTRS:
        return _LEGACY_ATTRS[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
