"""Tests for ImageService."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from auraframes.services.image_service import ImageService


@pytest.fixture
def mock_exif_writer():
    """Create a mock ExifWriter."""
    return MagicMock()


@pytest.fixture
def image_service(mock_exif_writer):
    """Create ImageService with mock dependencies."""
    return ImageService(exif_writer=mock_exif_writer)


@pytest.fixture
def sample_asset():
    """Create a sample asset for testing."""
    return MagicMock(id="asset123", file_name="test.jpg")


class TestImageServiceInit:
    """Tests for ImageService initialization."""

    def test_creates_default_exif_writer(self):
        """Should create default ExifWriter if not provided."""
        service = ImageService()
        assert service.exif_writer is not None

    def test_uses_provided_exif_writer(self, mock_exif_writer):
        """Should use provided ExifWriter."""
        service = ImageService(exif_writer=mock_exif_writer)
        assert service.exif_writer is mock_exif_writer


class TestDownloadImages:
    """Tests for download_images method."""

    @pytest.mark.asyncio
    async def test_downloads_all_assets(self, image_service):
        """Should attempt to download all assets."""
        assets = [MagicMock(id=f"asset{i}") for i in range(3)]

        with patch('auraframes.services.image_service.get_image_from_asset', new_callable=AsyncMock) as mock_download:
            failed = await image_service.download_images(assets, "/base/path", max_workers=2)

            assert len(failed) == 0
            assert mock_download.call_count == 3

    @pytest.mark.asyncio
    async def test_returns_failed_assets(self, image_service):
        """Should return list of failed assets."""
        assets = [MagicMock(id=f"asset{i}") for i in range(3)]

        async def fail_on_second(asset, *args, **kwargs):
            if asset.id == "asset1":
                raise Exception("Download failed")

        with patch('auraframes.services.image_service.get_image_from_asset', side_effect=fail_on_second):
            failed = await image_service.download_images(assets, "/base/path")

            assert len(failed) == 1
            assert failed[0].id == "asset1"

    @pytest.mark.asyncio
    async def test_calls_progress_callback(self, image_service):
        """Should call progress callback with correct values."""
        assets = [MagicMock(id=f"asset{i}") for i in range(3)]
        progress_calls = []

        def on_progress(completed, total, failed):
            progress_calls.append((completed, total, failed))

        with patch('auraframes.services.image_service.get_image_from_asset', new_callable=AsyncMock):
            await image_service.download_images(
                assets, "/base/path",
                max_workers=1,
                progress_callback=on_progress
            )

        # Should have been called 3 times (once per asset)
        assert len(progress_calls) == 3
        # All calls should have total=3
        assert all(call[1] == 3 for call in progress_calls)
        # Last call should have completed=3
        assert progress_calls[-1][0] == 3

    @pytest.mark.asyncio
    async def test_limits_concurrency(self, image_service):
        """Should respect max_workers limit."""
        import asyncio
        concurrent_count = 0
        max_concurrent = 0

        async def track_concurrent(asset, *args, **kwargs):
            nonlocal concurrent_count, max_concurrent
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
            await asyncio.sleep(0.01)
            concurrent_count -= 1

        assets = [MagicMock(id=f"asset{i}") for i in range(10)]

        with patch('auraframes.services.image_service.get_image_from_asset', side_effect=track_concurrent):
            await image_service.download_images(assets, "/base/path", max_workers=3)

        # Should never exceed max_workers
        assert max_concurrent <= 3

    @pytest.mark.asyncio
    async def test_empty_assets_list(self, image_service):
        """Should handle empty assets list."""
        with patch('auraframes.services.image_service.get_image_from_asset', new_callable=AsyncMock) as mock_download:
            failed = await image_service.download_images([], "/base/path")

            assert failed == []
            mock_download.assert_not_called()
