"""Tests for datetime utilities."""
from datetime import datetime, timezone

import pytest

from auraframes.utils.dt import (
    parse_aura_dt,
    get_utc_now,
    format_dt_to_aura,
    format_caption_date,
    AURA_DT_FORMAT,
)


class TestParseAuraDt:
    """Tests for parse_aura_dt function."""

    def test_parse_valid_datetime(self):
        """Should parse valid Aura datetime string."""
        dt_str = "2024-03-15T10:30:45.123456Z"
        result = parse_aura_dt(dt_str)

        assert result.year == 2024
        assert result.month == 3
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30
        assert result.second == 45
        assert result.microsecond == 123456

    def test_parse_midnight(self):
        """Should parse midnight datetime."""
        dt_str = "2024-01-01T00:00:00.000000Z"
        result = parse_aura_dt(dt_str)

        assert result.hour == 0
        assert result.minute == 0
        assert result.second == 0

    def test_parse_invalid_format(self):
        """Should raise ValueError for invalid format."""
        with pytest.raises(ValueError):
            parse_aura_dt("2024-03-15")

    def test_parse_invalid_string(self):
        """Should raise ValueError for invalid string."""
        with pytest.raises(ValueError):
            parse_aura_dt("not a date")


class TestGetUtcNow:
    """Tests for get_utc_now function."""

    def test_returns_utc_datetime(self):
        """Should return current UTC datetime."""
        result = get_utc_now()

        assert result.tzinfo == timezone.utc

    def test_returns_recent_time(self):
        """Should return approximately current time."""
        before = datetime.now(timezone.utc)
        result = get_utc_now()
        after = datetime.now(timezone.utc)

        assert before <= result <= after


class TestFormatDtToAura:
    """Tests for format_dt_to_aura function."""

    def test_format_datetime(self):
        """Should format datetime to Aura string format."""
        dt = datetime(2024, 3, 15, 10, 30, 45, 123456)
        result = format_dt_to_aura(dt)

        assert result == "2024-03-15T10:30:45.123456Z"

    def test_format_midnight(self):
        """Should format midnight datetime."""
        dt = datetime(2024, 1, 1, 0, 0, 0, 0)
        result = format_dt_to_aura(dt)

        assert result == "2024-01-01T00:00:00.000000Z"

    def test_roundtrip(self):
        """Should roundtrip parse and format."""
        original = "2024-06-20T14:25:30.987654Z"
        parsed = parse_aura_dt(original)
        formatted = format_dt_to_aura(parsed)

        assert formatted == original


class TestFormatCaptionDate:
    """Tests for format_caption_date function."""

    def test_format_date(self):
        """Should format datetime to month year string."""
        dt = datetime(2024, 3, 15, 10, 30, 45)
        result = format_caption_date(dt)

        assert result == "March 2024"

    def test_format_january(self):
        """Should format January correctly."""
        dt = datetime(2025, 1, 1)
        result = format_caption_date(dt)

        assert result == "January 2025"

    def test_format_december(self):
        """Should format December correctly."""
        dt = datetime(2023, 12, 31)
        result = format_caption_date(dt)

        assert result == "December 2023"
