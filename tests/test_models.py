"""Tests for Pydantic models - focused on validation behavior."""
import pytest
from pydantic import ValidationError

from auraframes.models.attachment import Attachment


class TestAttachmentModel:
    """Tests for the Attachment model - the simplest model to test."""

    def test_attachment_parses_valid_data(self, sample_attachment_data):
        """Attachment model should parse valid API response data."""
        attachment = Attachment(**sample_attachment_data)

        assert attachment.id == 'attachment-123'
        assert attachment.asset_id == 'asset-123'
        assert attachment.type == 'caption'
        assert attachment.data == 'Test caption text'

    def test_attachment_requires_id(self, sample_attachment_data):
        """Attachment model should require id field."""
        del sample_attachment_data['id']

        with pytest.raises(ValidationError):
            Attachment(**sample_attachment_data)

    def test_attachment_requires_type(self, sample_attachment_data):
        """Attachment model should require type field."""
        del sample_attachment_data['type']

        with pytest.raises(ValidationError):
            Attachment(**sample_attachment_data)

    def test_attachment_requires_data(self, sample_attachment_data):
        """Attachment model should require data field."""
        del sample_attachment_data['data']

        with pytest.raises(ValidationError):
            Attachment(**sample_attachment_data)

    def test_attachment_optional_updated_by_user_id(self, sample_attachment_data):
        """Attachment updated_by_user_id should be optional."""
        sample_attachment_data['updated_by_user_id'] = None
        attachment = Attachment(**sample_attachment_data)

        assert attachment.updated_by_user_id is None


class TestModelImports:
    """Test that all models can be imported without errors."""

    def test_import_frame_model(self):
        """Frame model should be importable."""
        from auraframes.models.frame import Frame, FramePartial
        assert Frame is not None
        assert FramePartial is not None

    def test_import_asset_model(self):
        """Asset model should be importable."""
        from auraframes.models.asset import Asset
        assert Asset is not None

    def test_import_user_model(self):
        """User model should be importable."""
        from auraframes.models.user import User
        assert User is not None

    def test_import_attachment_model(self):
        """Attachment model should be importable."""
        from auraframes.models.attachment import Attachment
        assert Attachment is not None


class TestFramePartialModel:
    """Tests for FramePartial which has all optional fields."""

    def test_frame_partial_accepts_minimal_data(self):
        """FramePartial should accept minimal data."""
        from auraframes.models.frame import FramePartial

        frame = FramePartial(id='frame-123', name='Test Frame')

        assert frame.id == 'frame-123'
        assert frame.name == 'Test Frame'

    def test_frame_partial_all_fields_optional(self):
        """FramePartial should have all fields optional."""
        from auraframes.models.frame import FramePartial

        # Should not raise - all fields optional
        frame = FramePartial()

        assert frame is not None
