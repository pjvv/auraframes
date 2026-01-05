"""Tests for API classes."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from auraframes.api.frame_api import FrameApi
from auraframes.api.playlist_api import PlaylistApi
from auraframes.api.attachment_api import AttachmentApi
from auraframes.api.account_api import AccountApi


class TestFrameApi:
    """Tests for the FrameApi class."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client with async methods."""
        client = MagicMock()
        client.get = AsyncMock()
        client.post = AsyncMock()
        client.put = AsyncMock()
        client.delete = AsyncMock()
        return client

    @pytest.fixture
    def frame_api(self, mock_client):
        """Create a FrameApi with mocked client."""
        return FrameApi(mock_client)

    @pytest.mark.asyncio
    async def test_get_frames_returns_list(self, frame_api, mock_client, sample_frame_data):
        """get_frames should return a list of Frame objects."""
        mock_client.get.return_value = {'frames': [sample_frame_data]}

        frames = await frame_api.get_frames()

        assert len(frames) == 1
        assert frames[0].id == sample_frame_data['id']
        assert frames[0].name == sample_frame_data['name']
        mock_client.get.assert_called_once_with('/frames.json')

    @pytest.mark.asyncio
    async def test_get_frame_returns_tuple(self, frame_api, mock_client, sample_frame_data):
        """get_frame should return a Frame and asset count."""
        mock_client.get.return_value = {
            'frame': sample_frame_data,
            'total_asset_count': 100
        }

        frame, count = await frame_api.get_frame('frame-123')

        assert frame.id == sample_frame_data['id']
        assert count == 100
        mock_client.get.assert_called_once_with('/frames/frame-123.json')

    @pytest.mark.asyncio
    async def test_get_assets_with_pagination(self, frame_api, mock_client, sample_asset_data):
        """get_assets should handle pagination cursor."""
        mock_client.get.return_value = {
            'assets': [sample_asset_data],
            'next_page_cursor': 'cursor-123'
        }

        assets, cursor = await frame_api.get_assets('frame-123')

        assert len(assets) == 1
        assert cursor == 'cursor-123'

    @pytest.mark.asyncio
    async def test_get_assets_without_cursor(self, frame_api, mock_client, sample_asset_data):
        """get_assets should return None cursor when no more pages."""
        mock_client.get.return_value = {
            'assets': [sample_asset_data],
            'next_page_cursor': None
        }

        assets, cursor = await frame_api.get_assets('frame-123')

        assert len(assets) == 1
        assert cursor is None


class TestPlaylistApi:
    """Tests for the PlaylistApi class."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client with async methods."""
        client = MagicMock()
        client.get = AsyncMock()
        return client

    @pytest.fixture
    def playlist_api(self, mock_client):
        """Create a PlaylistApi with mocked client."""
        return PlaylistApi(mock_client)

    @pytest.mark.asyncio
    async def test_get_playlist_asset_ids_returns_ids(self, playlist_api, mock_client):
        """get_playlist_asset_ids should return list of asset IDs."""
        mock_client.get.return_value = {
            'asset_settings': [
                {'asset_id': 'asset-1'},
                {'asset_id': 'asset-2'},
                {'asset_id': 'asset-3'},
            ],
            'next_page_cursor': None
        }

        asset_ids, cursor = await playlist_api.get_playlist_asset_ids('playlist-123', 'frame-123')

        assert asset_ids == ['asset-1', 'asset-2', 'asset-3']
        assert cursor is None

    @pytest.mark.asyncio
    async def test_get_playlist_asset_ids_with_pagination(self, playlist_api, mock_client):
        """get_playlist_asset_ids should handle pagination."""
        mock_client.get.return_value = {
            'asset_settings': [{'asset_id': 'asset-1'}],
            'next_page_cursor': 'next-cursor'
        }

        asset_ids, cursor = await playlist_api.get_playlist_asset_ids(
            'playlist-123', 'frame-123', cursor='prev-cursor'
        )

        assert cursor == 'next-cursor'
        # Verify cursor was passed to API
        call_kwargs = mock_client.get.call_args.kwargs
        assert call_kwargs['query_params']['cursor'] == 'prev-cursor'


class TestAttachmentApi:
    """Tests for the AttachmentApi class."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client with async methods."""
        client = MagicMock()
        client.post = AsyncMock()
        client.put = AsyncMock()
        client.delete = AsyncMock()
        return client

    @pytest.fixture
    def attachment_api(self, mock_client):
        """Create an AttachmentApi with mocked client."""
        return AttachmentApi(mock_client)

    @pytest.mark.asyncio
    async def test_create_caption_sends_correct_data(self, attachment_api, mock_client, sample_attachment_data):
        """create_caption should send correct data structure."""
        mock_client.post.return_value = {'attachment': sample_attachment_data}

        result = await attachment_api.create_caption('asset-123', 'frame-123', 'Test caption')

        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args.kwargs
        assert call_kwargs['data']['asset_id'] == 'asset-123'
        assert call_kwargs['data']['frame_id'] == 'frame-123'
        assert call_kwargs['data']['type'] == 'caption'
        assert call_kwargs['data']['text'] == 'Test caption'

    @pytest.mark.asyncio
    async def test_create_caption_returns_attachment(self, attachment_api, mock_client, sample_attachment_data):
        """create_caption should return an Attachment object."""
        mock_client.post.return_value = {'attachment': sample_attachment_data}

        result = await attachment_api.create_caption('asset-123', 'frame-123', 'Test caption')

        assert result.id == 'attachment-123'
        assert result.type == 'caption'
        assert result.data == 'Test caption text'

    @pytest.mark.asyncio
    async def test_delete_caption(self, attachment_api, mock_client):
        """delete_caption should call correct endpoint."""
        mock_client.delete.return_value = {'success': True}

        result = await attachment_api.delete_caption('attachment-123')

        mock_client.delete.assert_called_once_with('/attachments/attachment-123.json')


class TestAccountApi:
    """Tests for the AccountApi class."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock client with async methods."""
        client = MagicMock()
        client.post = AsyncMock()
        return client

    @pytest.fixture
    def account_api(self, mock_client):
        """Create an AccountApi with mocked client."""
        return AccountApi(mock_client)

    @pytest.mark.asyncio
    async def test_login_returns_user(self, account_api, mock_client, sample_user_data):
        """login should return a User object."""
        mock_client.post.return_value = {
            'error': False,
            'result': {'current_user': sample_user_data}
        }

        user = await account_api.login('test@example.com', 'password123')

        assert user.id == 'user-123'
        assert user.email == 'test@example.com'
        assert user.auth_token == 'test-auth-token-12345'

    @pytest.mark.asyncio
    async def test_login_sends_credentials(self, account_api, mock_client, sample_user_data):
        """login should send email and password."""
        mock_client.post.return_value = {
            'error': False,
            'result': {'current_user': sample_user_data}
        }

        await account_api.login('test@example.com', 'password123')

        # Login passes data as positional arg: post('/login.json', login_payload)
        call_args = mock_client.post.call_args.args
        login_payload = call_args[1]
        assert login_payload['user']['email'] == 'test@example.com'
        assert login_payload['user']['password'] == 'password123'
