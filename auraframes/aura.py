import os
import sys
from collections.abc import Callable

from loguru import logger

from auraframes.api.account_api import AccountApi
from auraframes.api.activity_api import ActivityApi
from auraframes.api.asset_api import AssetApi
from auraframes.api.attachment_api import AttachmentApi
from auraframes.api.frame_api import FrameApi
from auraframes.api.playlist_api import PlaylistApi
from auraframes.client import Client
from auraframes.exif import ExifWriter
from auraframes.models.asset import Asset
from auraframes.services.caption_service import CaptionService
from auraframes.services.image_service import ImageService
from auraframes.utils.io import build_path, write_model
from auraframes.utils.pagination import paginate
from auraframes.utils.settings import get_settings


class Aura:
    """
    Main orchestrator for the Aura Frames API.

    Provides a high-level interface for interacting with Aura frames,
    including authentication, asset management, and bulk operations.
    """

    def __init__(self) -> None:
        self._init_logger()
        self._client = Client()

        # Initialize API clients
        self.account_api = AccountApi(self._client)
        self.frame_api = FrameApi(self._client)
        self.activity_api = ActivityApi(self._client)
        self.asset_api = AssetApi(self._client)
        self.attachment_api = AttachmentApi(self._client)
        self.playlist_api = PlaylistApi(self._client)

        # Initialize services
        self.exif_writer = ExifWriter()
        self.image_service = ImageService(self.exif_writer)
        self.caption_service = CaptionService(
            self._client,
            self.frame_api,
            self.playlist_api,
            self.attachment_api
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.close()

    async def __aenter__(self) -> "Aura":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def login(self, email: str | None = None, password: str | None = None) -> "Aura":
        """
        Authenticate with the Aura API.

        :param email: The email of the account to authenticate with, defaults to AURA_EMAIL env var
        :param password: The password of the account to authenticate with, defaults to AURA_PASSWORD env var
        :return: Authenticated Aura object
        :raises ValueError: If email or password is not provided and not set in environment
        """
        email = email or os.getenv('AURA_EMAIL')
        password = password or os.getenv('AURA_PASSWORD')

        if not email or not password:
            raise ValueError(
                "Email and password are required. Provide them as arguments or "
                "set AURA_EMAIL and AURA_PASSWORD environment variables."
            )

        user = await self.account_api.login(email, password)

        self._client.add_default_headers({
            'x-token-auth': user.auth_token,
            'x-user-id': user.id
        })

        return self

    async def get_all_assets(self, frame_id: str) -> list[Asset]:
        """Get all assets from a frame, handling pagination."""
        return await paginate(self.frame_api.get_assets, frame_id, delay=1.0)

    async def dump_frame(
        self,
        frame_id: str,
        path: str,
        download_images: bool = True,
        download_activities: bool = True
    ) -> None:
        """
        Export a frame's data and optionally download all images.

        :param frame_id: Frame ID to export
        :param path: Base path to save exported data
        :param download_images: Whether to download images (default True)
        :param download_activities: Whether to download activities (default True)
        """
        frame, _ = await self.frame_api.get_frame(frame_id)
        frame_dir = build_path(path, f'{frame.name}-{frame.id}/')

        write_model(frame, build_path(frame_dir, 'frame.json'))

        if download_activities:
            activities, _ = await self.frame_api.get_activities(frame.id)
            write_model(activities, build_path(frame_dir, 'activities.json'))

        assets = await self.get_all_assets(frame_id)
        write_model(assets, build_path(frame_dir, 'assets.json'))

        if download_images:
            await self.image_service.download_images(assets, build_path(frame_dir, 'asset_images/'))

    async def download_images_from_assets(
        self,
        assets: list[Asset],
        base_path: str,
        max_workers: int = 5,
        progress_callback: Callable[[int, int, int], None] | None = None
    ) -> list[Asset]:
        """
        Download images from assets concurrently.

        :param assets: List of assets to download
        :param base_path: Directory to save images
        :param max_workers: Number of concurrent downloads (default 5)
        :param progress_callback: Optional callback(current, total, failed) for progress
        :return: List of assets that failed to download
        """
        return await self.image_service.download_images(
            assets, base_path, max_workers, progress_callback
        )

    async def caption_album(
        self,
        frame_id: str,
        playlist_id: str,
        caption: str,
        include_date: bool = False,
        progress_callback: Callable[[str, int, int], None] | None = None,
        max_workers: int = 10
    ) -> int:
        """
        Add the same caption to all photos in an album/playlist.
        Replaces any existing captions on the photos.

        :param frame_id: Frame ID containing the album
        :param playlist_id: Playlist/album ID
        :param caption: Caption text to apply to all photos
        :param include_date: If True, append photo date to caption, e.g. "(March 2025)"
        :param progress_callback: Optional callback(phase, current, total) for progress updates
            phase: "fetching", "deleting", "captioning"
        :param max_workers: Number of concurrent workers (default 10, used as semaphore limit)
        :return: Number of photos captioned
        """
        return await self.caption_service.caption_album(
            frame_id=frame_id,
            playlist_id=playlist_id,
            caption=caption,
            include_date=include_date,
            progress_callback=progress_callback,
            max_workers=max_workers,
            get_all_assets=self.get_all_assets
        )

    def _init_logger(self) -> None:
        """Configure logging based on AURA_DEBUG environment variable.

        If AURA_DEBUG is set to a truthy value, enables DEBUG level logging.
        Otherwise, only WARNING and above are shown.
        """
        logger.remove()
        settings = get_settings()
        level = "DEBUG" if settings.debug else "WARNING"
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ) if settings.debug else "<level>{message}</level>"
        logger.add(sys.stderr, level=level, format=log_format)
