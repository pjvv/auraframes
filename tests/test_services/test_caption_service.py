"""Tests for CaptionService."""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from auraframes.services.caption_service import CaptionService


@pytest.fixture
def mock_client():
    """Create a mock HTTP client."""
    return AsyncMock()


@pytest.fixture
def mock_frame_api():
    """Create a mock FrameApi."""
    return AsyncMock()


@pytest.fixture
def mock_playlist_api():
    """Create a mock PlaylistApi."""
    return AsyncMock()


@pytest.fixture
def mock_attachment_api():
    """Create a mock AttachmentApi."""
    return AsyncMock()


@pytest.fixture
def caption_service(mock_client, mock_frame_api, mock_playlist_api, mock_attachment_api):
    """Create CaptionService with mock dependencies."""
    return CaptionService(
        client=mock_client,
        frame_api=mock_frame_api,
        playlist_api=mock_playlist_api,
        attachment_api=mock_attachment_api
    )


class TestCaptionServiceInit:
    """Tests for CaptionService initialization."""

    def test_stores_dependencies(
        self, mock_client, mock_frame_api, mock_playlist_api, mock_attachment_api
    ):
        """Should store all dependencies."""
        service = CaptionService(
            mock_client, mock_frame_api, mock_playlist_api, mock_attachment_api
        )

        assert service._client is mock_client
        assert service.frame_api is mock_frame_api
        assert service.playlist_api is mock_playlist_api
        assert service.attachment_api is mock_attachment_api


class TestGetAssetAttachmentsMap:
    """Tests for get_asset_attachments_map method."""

    @pytest.mark.asyncio
    async def test_fetches_attachments_for_assets(self, caption_service, mock_client):
        """Should return attachments for specified asset IDs."""
        mock_client.get.return_value = {
            'assets': [
                {'id': 'asset1', 'attachments': [{'id': 'att1', 'type': 'caption'}]},
                {'id': 'asset2', 'attachments': []},
                {'id': 'asset3', 'attachments': [{'id': 'att2', 'type': 'caption'}]},
            ],
            'next_page_cursor': None
        }

        result = await caption_service.get_asset_attachments_map(
            'frame123',
            {'asset1', 'asset2'}
        )

        assert 'asset1' in result
        assert len(result['asset1']) == 1
        assert 'asset2' in result
        assert len(result['asset2']) == 0
        # asset3 not in requested set
        assert 'asset3' not in result

    @pytest.mark.asyncio
    async def test_handles_pagination(self, caption_service, mock_client):
        """Should paginate through all assets."""
        mock_client.get.side_effect = [
            {
                'assets': [{'id': 'asset1', 'attachments': []}],
                'next_page_cursor': 'cursor2'
            },
            {
                'assets': [{'id': 'asset2', 'attachments': []}],
                'next_page_cursor': None
            },
        ]

        result = await caption_service.get_asset_attachments_map(
            'frame123',
            {'asset1', 'asset2'}
        )

        assert 'asset1' in result
        assert 'asset2' in result
        assert mock_client.get.call_count == 2


class TestCaptionAlbum:
    """Tests for caption_album method."""

    @pytest.mark.asyncio
    async def test_captions_all_assets(self, caption_service, mock_client, mock_playlist_api, mock_attachment_api):
        """Should create captions for all assets in playlist."""
        # Setup mocks
        mock_playlist_api.get_playlist_asset_ids.return_value = (['asset1', 'asset2'], None)
        mock_client.get.return_value = {
            'assets': [
                {'id': 'asset1', 'attachments': []},
                {'id': 'asset2', 'attachments': []},
            ],
            'next_page_cursor': None
        }

        result = await caption_service.caption_album(
            'frame123',
            'playlist456',
            'Test Caption'
        )

        assert result == 2
        assert mock_attachment_api.create_caption.call_count == 2

    @pytest.mark.asyncio
    async def test_deletes_existing_captions(self, caption_service, mock_client, mock_playlist_api, mock_attachment_api):
        """Should delete existing captions before creating new ones."""
        mock_playlist_api.get_playlist_asset_ids.return_value = (['asset1'], None)
        mock_client.get.return_value = {
            'assets': [
                {
                    'id': 'asset1',
                    'attachments': [
                        {'id': 'existing_caption', 'type': 'caption'}
                    ]
                },
            ],
            'next_page_cursor': None
        }

        await caption_service.caption_album('frame123', 'playlist456', 'New Caption')

        # Should delete existing caption
        mock_attachment_api.delete_caption.assert_called_with('existing_caption')
        # Should create new caption
        mock_attachment_api.create_caption.assert_called()

    @pytest.mark.asyncio
    async def test_progress_callback_phases(self, caption_service, mock_client, mock_playlist_api, mock_attachment_api):
        """Should call progress callback with correct phases."""
        mock_playlist_api.get_playlist_asset_ids.return_value = (['asset1', 'asset2'], None)
        mock_client.get.return_value = {
            'assets': [
                {'id': 'asset1', 'attachments': []},
                {'id': 'asset2', 'attachments': []},
            ],
            'next_page_cursor': None
        }

        phases_called = []

        def on_progress(phase, current, total):
            phases_called.append(phase)

        await caption_service.caption_album(
            'frame123',
            'playlist456',
            'Test Caption',
            progress_callback=on_progress
        )

        # Should have all three phases
        assert 'fetching' in phases_called
        assert 'deleting' in phases_called
        assert 'captioning' in phases_called

    @pytest.mark.asyncio
    async def test_include_date_appends_date(self, caption_service, mock_client, mock_playlist_api, mock_attachment_api):
        """Should append date to caption when include_date is True."""
        # Create mock asset with taken_at_dt property
        mock_asset = MagicMock()
        mock_asset.id = 'asset1'
        mock_asset.taken_at_dt = datetime(2024, 3, 15)

        mock_playlist_api.get_playlist_asset_ids.return_value = (['asset1'], None)
        mock_client.get.return_value = {
            'assets': [{'id': 'asset1', 'attachments': []}],
            'next_page_cursor': None
        }

        async def mock_get_all_assets(frame_id):
            return [mock_asset]

        await caption_service.caption_album(
            'frame123',
            'playlist456',
            'Test Caption',
            include_date=True,
            get_all_assets=mock_get_all_assets
        )

        # Should include date in caption
        call_args = mock_attachment_api.create_caption.call_args
        assert 'March 2024' in call_args[0][2]

    @pytest.mark.asyncio
    async def test_include_date_requires_get_all_assets(self, caption_service):
        """Should raise ValueError when include_date is True but get_all_assets not provided."""
        with pytest.raises(ValueError, match="get_all_assets callable is required"):
            await caption_service.caption_album(
                'frame123',
                'playlist456',
                'Test Caption',
                include_date=True,
                get_all_assets=None
            )

    @pytest.mark.asyncio
    async def test_handles_caption_failure_gracefully(
        self, caption_service, mock_client, mock_playlist_api, mock_attachment_api
    ):
        """Should continue captioning even if some fail."""
        mock_playlist_api.get_playlist_asset_ids.return_value = (['asset1', 'asset2', 'asset3'], None)
        mock_client.get.return_value = {
            'assets': [
                {'id': 'asset1', 'attachments': []},
                {'id': 'asset2', 'attachments': []},
                {'id': 'asset3', 'attachments': []},
            ],
            'next_page_cursor': None
        }

        # Make asset2 fail
        async def create_caption_side_effect(asset_id, frame_id, caption):
            if asset_id == 'asset2':
                raise Exception("Caption failed")

        mock_attachment_api.create_caption.side_effect = create_caption_side_effect

        result = await caption_service.caption_album('frame123', 'playlist456', 'Test')

        # Should still return total count
        assert result == 3
        # Should have attempted all three
        assert mock_attachment_api.create_caption.call_count == 3
