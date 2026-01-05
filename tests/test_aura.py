"""Integration tests for the Aura class."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestAuraCaptionAlbum:
    """Tests for the caption_album method."""

    @pytest.fixture
    def mock_aura(self):
        """Create an Aura instance with mocked dependencies."""
        with patch('auraframes.aura.Client'):
            from auraframes.aura import Aura

            aura = Aura()
            aura.playlist_api = MagicMock()
            aura.playlist_api.get_playlist_asset_ids = AsyncMock()
            aura.attachment_api = MagicMock()
            aura.attachment_api.create_caption = AsyncMock()
            aura.attachment_api.delete_caption = AsyncMock()
            # Mock _client.get for get_asset_attachments_map
            aura._client = MagicMock()
            aura._client.get = AsyncMock(return_value={'assets': [], 'next_page_cursor': None})
            # Update caption_service to use the mocked APIs
            aura.caption_service.playlist_api = aura.playlist_api
            aura.caption_service.attachment_api = aura.attachment_api
            aura.caption_service._client = aura._client
            yield aura

    @pytest.mark.asyncio
    async def test_caption_album_fetches_all_asset_ids(self, mock_aura):
        """caption_album should paginate through all asset IDs."""
        # First page returns 2 assets and a cursor
        # Second page returns 1 asset and no cursor
        mock_aura.playlist_api.get_playlist_asset_ids.side_effect = [
            (['asset-1', 'asset-2'], 'cursor-1'),
            (['asset-3'], None),
        ]

        count = await mock_aura.caption_album('frame-123', 'playlist-123', 'Test caption')

        assert count == 3
        assert mock_aura.playlist_api.get_playlist_asset_ids.call_count == 2

    @pytest.mark.asyncio
    async def test_caption_album_creates_captions_for_all_assets(self, mock_aura):
        """caption_album should create captions for all assets."""
        mock_aura.playlist_api.get_playlist_asset_ids.return_value = (
            ['asset-1', 'asset-2', 'asset-3'], None
        )

        await mock_aura.caption_album('frame-123', 'playlist-123', 'Test caption')

        assert mock_aura.attachment_api.create_caption.call_count == 3

    @pytest.mark.asyncio
    async def test_caption_album_calls_progress_callback(self, mock_aura):
        """caption_album should call progress callback for each phase."""
        mock_aura.playlist_api.get_playlist_asset_ids.return_value = (
            ['asset-1', 'asset-2'], None
        )
        progress_calls = []

        def progress_callback(phase, current, total):
            progress_calls.append((phase, current, total))

        await mock_aura.caption_album(
            'frame-123', 'playlist-123', 'Test caption',
            progress_callback=progress_callback
        )

        # Should have calls for fetching, deleting (2), and captioning (2)
        phases = [call[0] for call in progress_calls]
        assert 'fetching' in phases
        assert 'deleting' in phases
        assert 'captioning' in phases
        # Final captioning call should show 2/2
        captioning_calls = [c for c in progress_calls if c[0] == 'captioning']
        assert ('captioning', 2, 2) in captioning_calls

    @pytest.mark.asyncio
    async def test_caption_album_handles_failures_gracefully(self, mock_aura):
        """caption_album should continue even if some captions fail."""
        mock_aura.playlist_api.get_playlist_asset_ids.return_value = (
            ['asset-1', 'asset-2', 'asset-3'], None
        )
        # Second caption fails
        mock_aura.attachment_api.create_caption.side_effect = [
            MagicMock(),
            Exception("API Error"),
            MagicMock(),
        ]

        # Should not raise, should continue
        count = await mock_aura.caption_album('frame-123', 'playlist-123', 'Test caption')

        assert count == 3  # Still returns total count
        assert mock_aura.attachment_api.create_caption.call_count == 3

    @pytest.mark.asyncio
    async def test_caption_album_uses_concurrent_tasks(self, mock_aura):
        """caption_album should use asyncio for concurrency."""
        mock_aura.playlist_api.get_playlist_asset_ids.return_value = (
            ['asset-1', 'asset-2', 'asset-3', 'asset-4', 'asset-5'], None
        )

        await mock_aura.caption_album(
            'frame-123', 'playlist-123', 'Test caption',
            max_workers=3
        )

        # All assets should be captioned
        assert mock_aura.attachment_api.create_caption.call_count == 5

    @pytest.mark.asyncio
    async def test_caption_album_respects_max_workers(self, mock_aura):
        """caption_album should respect the max_workers parameter."""
        mock_aura.playlist_api.get_playlist_asset_ids.return_value = (
            ['asset-1', 'asset-2'], None
        )

        # This should work with any max_workers value
        await mock_aura.caption_album(
            'frame-123', 'playlist-123', 'Test caption',
            max_workers=1
        )

        assert mock_aura.attachment_api.create_caption.call_count == 2


class TestAuraGetAllAssets:
    """Tests for the get_all_assets method."""

    @pytest.fixture
    def mock_aura(self):
        """Create an Aura instance with mocked dependencies."""
        with patch('auraframes.aura.Client'):
            from auraframes.aura import Aura

            aura = Aura()
            aura.frame_api = MagicMock()
            aura.frame_api.get_assets = AsyncMock()
            yield aura

    @pytest.mark.asyncio
    async def test_get_all_assets_paginates(self, mock_aura, sample_asset_data):
        """get_all_assets should paginate through all pages."""
        from auraframes.models.asset import Asset

        asset1 = Asset(**{**sample_asset_data, 'id': 'asset-1'})
        asset2 = Asset(**{**sample_asset_data, 'id': 'asset-2'})

        mock_aura.frame_api.get_assets.side_effect = [
            ([asset1], 'cursor-1'),
            ([asset2], None),
        ]

        assets = await mock_aura.get_all_assets('frame-123')

        assert len(assets) == 2
        assert assets[0].id == 'asset-1'
        assert assets[1].id == 'asset-2'


class TestAuraLogin:
    """Tests for the login method."""

    @pytest.fixture
    def mock_aura(self):
        """Create an Aura instance with mocked dependencies."""
        with patch('auraframes.aura.Client') as mock_client_class:
            from auraframes.aura import Aura

            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            aura = Aura()
            aura._client = mock_client
            aura.account_api = MagicMock()
            aura.account_api.login = AsyncMock()
            yield aura

    @pytest.mark.asyncio
    async def test_login_sets_auth_headers(self, mock_aura, sample_user_data):
        """login should set auth headers on the client."""
        from auraframes.models.user import User

        user = User(**sample_user_data)
        mock_aura.account_api.login.return_value = user

        result = await mock_aura.login('test@example.com', 'password')

        mock_aura._client.add_default_headers.assert_called_once_with({
            'x-token-auth': 'test-auth-token-12345',
            'x-user-id': 'user-123'
        })

    @pytest.mark.asyncio
    async def test_login_returns_self(self, mock_aura, sample_user_data):
        """login should return the Aura instance for chaining."""
        from auraframes.models.user import User

        user = User(**sample_user_data)
        mock_aura.account_api.login.return_value = user

        result = await mock_aura.login('test@example.com', 'password')

        assert result is mock_aura
