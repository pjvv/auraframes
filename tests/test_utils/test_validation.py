"""Tests for validation utilities."""
import pytest

from auraframes.exceptions import ValidationError
from auraframes.utils.validation import (
    validate_email,
    validate_password,
    validate_non_empty,
    validate_id,
    validate_caption,
    validate_string_length,
)


class TestValidateEmail:
    """Tests for validate_email function."""

    def test_valid_email(self):
        """Valid email should not raise."""
        validate_email("user@example.com")
        validate_email("test.user@domain.org")
        validate_email("a@b.co")

    def test_invalid_email_no_at(self):
        """Email without @ should raise ValidationError."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("userexample.com")

    def test_invalid_email_no_domain(self):
        """Email without domain should raise ValidationError."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("user@")

    def test_invalid_email_empty(self):
        """Empty email should raise ValidationError."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("")

    def test_invalid_email_with_spaces(self):
        """Email with spaces should raise ValidationError."""
        with pytest.raises(ValidationError, match="Invalid email format"):
            validate_email("user @example.com")


class TestValidatePassword:
    """Tests for validate_password function."""

    def test_valid_password(self):
        """Password meeting minimum length should not raise."""
        validate_password("123456")
        validate_password("longerpassword")

    def test_password_too_short(self):
        """Password shorter than minimum should raise ValidationError."""
        with pytest.raises(ValidationError, match="at least 6 characters"):
            validate_password("12345")

    def test_empty_password(self):
        """Empty password should raise ValidationError."""
        with pytest.raises(ValidationError, match="at least 6 characters"):
            validate_password("")

    def test_custom_min_length(self):
        """Custom minimum length should be respected."""
        validate_password("1234567890", min_length=10)
        with pytest.raises(ValidationError, match="at least 10 characters"):
            validate_password("123456789", min_length=10)


class TestValidateNonEmpty:
    """Tests for validate_non_empty function."""

    def test_valid_string(self):
        """Non-empty string should not raise."""
        validate_non_empty("hello", "test_field")
        validate_non_empty("  trimmed  ", "test_field")

    def test_empty_string(self):
        """Empty string should raise ValidationError."""
        with pytest.raises(ValidationError, match="test_field cannot be empty"):
            validate_non_empty("", "test_field")

    def test_whitespace_only(self):
        """Whitespace-only string should raise ValidationError."""
        with pytest.raises(ValidationError, match="test_field cannot be empty"):
            validate_non_empty("   ", "test_field")


class TestValidateId:
    """Tests for validate_id function."""

    def test_valid_id(self):
        """Valid ID should not raise."""
        validate_id("abc123")
        validate_id("123", "asset_id")

    def test_empty_id(self):
        """Empty ID should raise ValidationError."""
        with pytest.raises(ValidationError, match="ID cannot be empty"):
            validate_id("")

    def test_custom_field_name(self):
        """Custom field name should appear in error message."""
        with pytest.raises(ValidationError, match="frame_id cannot be empty"):
            validate_id("", "frame_id")


class TestValidateCaption:
    """Tests for validate_caption function."""

    def test_valid_caption(self):
        """Valid caption should not raise."""
        validate_caption("This is a valid caption")
        validate_caption("a")  # Single character

    def test_empty_caption(self):
        """Empty caption should raise ValidationError."""
        with pytest.raises(ValidationError, match="Caption cannot be empty"):
            validate_caption("")

    def test_whitespace_caption(self):
        """Whitespace-only caption should raise ValidationError."""
        with pytest.raises(ValidationError, match="Caption cannot be empty"):
            validate_caption("   ")

    def test_caption_too_long(self):
        """Caption exceeding max length should raise ValidationError."""
        long_caption = "a" * 141
        with pytest.raises(ValidationError, match="cannot exceed 140 characters"):
            validate_caption(long_caption)

    def test_caption_at_max_length(self):
        """Caption at exactly max length should not raise."""
        validate_caption("a" * 140)

    def test_custom_max_length(self):
        """Custom max length should be respected."""
        validate_caption("short", max_length=10)
        with pytest.raises(ValidationError, match="cannot exceed 5 characters"):
            validate_caption("toolong", max_length=5)


class TestValidateStringLength:
    """Tests for validate_string_length function."""

    def test_valid_string_in_range(self):
        """String within bounds should not raise."""
        validate_string_length("hello", "field", min_length=3, max_length=10)

    def test_string_too_short(self):
        """String below min length should raise ValidationError."""
        with pytest.raises(ValidationError, match="at least 5 characters"):
            validate_string_length("abc", "field", min_length=5)

    def test_string_too_long(self):
        """String above max length should raise ValidationError."""
        with pytest.raises(ValidationError, match="cannot exceed 5 characters"):
            validate_string_length("toolong", "field", max_length=5)

    def test_none_value(self):
        """None value should raise ValidationError."""
        with pytest.raises(ValidationError, match="cannot be None"):
            validate_string_length(None, "field")  # type: ignore

    def test_only_min_length(self):
        """Only min_length constraint should work."""
        validate_string_length("hello", "field", min_length=3)

    def test_only_max_length(self):
        """Only max_length constraint should work."""
        validate_string_length("hi", "field", max_length=10)
