import asyncio
from collections.abc import Callable

import httpx
from loguru import logger

from auraframes.exif import ExifWriter
from auraframes.export import get_image_from_asset
from auraframes.models.asset import Asset


class ImageService:
    """Service for downloading and processing images from assets."""

    def __init__(self, exif_writer: ExifWriter | None = None):
        """
        Initialize the image service.

        :param exif_writer: ExifWriter instance for writing EXIF data to downloaded images
        """
        self.exif_writer = exif_writer or ExifWriter()

    async def download_images(
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
        failed_to_retrieve: list[Asset] = []
        completed = 0
        total = len(assets)
        semaphore = asyncio.Semaphore(max_workers)

        async def download_one(asset: Asset, client: httpx.AsyncClient) -> None:
            nonlocal completed
            async with semaphore:
                try:
                    await get_image_from_asset(asset, base_path, self.exif_writer, client=client)
                except Exception as e:
                    logger.debug(f"Failed to download asset {asset.id}: {e}")
                    failed_to_retrieve.append(asset)
                completed += 1
                if progress_callback:
                    progress_callback(completed, total, len(failed_to_retrieve))

        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            await asyncio.gather(*[download_one(asset, client) for asset in assets])

        if len(failed_to_retrieve) > 0:
            logger.warning(f'Failed to retrieve {len(failed_to_retrieve)}/{total} assets.')

        return failed_to_retrieve
