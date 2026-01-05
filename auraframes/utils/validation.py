"""Shared validation utilities for the Aura Frames client."""
import re

from auraframes.exceptions import ValidationError

# Email validation pattern
EMAIL_PATTERN = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

# Default constraints
DEFAULT_MIN_PASSWORD_LENGTH = 6
DEFAULT_MAX_CAPTION_LENGTH = 140


def validate_email(email: str) -> None:
    """
    Validate email format.

    :param email: Email address to validate
    :raises ValidationError: If email format is invalid
    """
    if not email or not EMAIL_PATTERN.match(email):
        raise ValidationError("Invalid email format")


def validate_password(password: str, min_length: int = DEFAULT_MIN_PASSWORD_LENGTH) -> None:
    """
    Validate password meets minimum requirements.

    :param password: Password to validate
    :param min_length: Minimum required length (default 6)
    :raises ValidationError: If password is too short
    """
    if not password or len(password) < min_length:
        raise ValidationError(f"Password must be at least {min_length} characters")


def validate_non_empty(value: str, field_name: str) -> None:
    """
    Validate that a string value is non-empty.

    :param value: Value to validate
    :param field_name: Name of the field for error messages
    :raises ValidationError: If value is empty or whitespace-only
    """
    if not value or not value.strip():
        raise ValidationError(f"{field_name} cannot be empty")


def validate_id(value: str, field_name: str = "ID") -> None:
    """
    Validate that an ID is non-empty.

    :param value: ID value to validate
    :param field_name: Name of the field for error messages (default "ID")
    :raises ValidationError: If ID is empty
    """
    validate_non_empty(value, field_name)


def validate_caption(
    content: str,
    max_length: int = DEFAULT_MAX_CAPTION_LENGTH
) -> None:
    """
    Validate caption text.

    :param content: Caption content to validate
    :param max_length: Maximum allowed length (default 140)
    :raises ValidationError: If caption is empty or too long
    """
    if not content or not content.strip():
        raise ValidationError("Caption cannot be empty")
    if len(content) > max_length:
        raise ValidationError(f"Caption cannot exceed {max_length} characters")


def validate_string_length(
    value: str,
    field_name: str,
    min_length: int | None = None,
    max_length: int | None = None
) -> None:
    """
    Validate string length is within bounds.

    :param value: String to validate
    :param field_name: Name of the field for error messages
    :param min_length: Minimum length (optional)
    :param max_length: Maximum length (optional)
    :raises ValidationError: If length is outside bounds
    """
    if value is None:
        raise ValidationError(f"{field_name} cannot be None")

    length = len(value)
    if min_length is not None and length < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters")
    if max_length is not None and length > max_length:
        raise ValidationError(f"{field_name} cannot exceed {max_length} characters")
