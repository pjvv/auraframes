import asyncio
from collections.abc import Awaitable, Callable

from loguru import logger

from auraframes.api.attachment_api import AttachmentApi
from auraframes.api.frame_api import FrameApi
from auraframes.api.playlist_api import PlaylistApi
from auraframes.client import Client
from auraframes.models.asset import Asset
from auraframes.utils.dt import format_caption_date
from auraframes.utils.pagination import paginate


class CaptionService:
    """Service for managing captions on assets."""

    def __init__(
        self,
        client: Client,
        frame_api: FrameApi,
        playlist_api: PlaylistApi,
        attachment_api: AttachmentApi
    ):
        """
        Initialize the caption service.

        :param client: HTTP client for direct API calls
        :param frame_api: FrameApi instance
        :param playlist_api: PlaylistApi instance
        :param attachment_api: AttachmentApi instance
        """
        self._client = client
        self.frame_api = frame_api
        self.playlist_api = playlist_api
        self.attachment_api = attachment_api

    async def get_asset_attachments_map(self, frame_id: str, asset_ids: set[str]) -> dict[str, list]:
        """
        Fetch attachments for specific assets from a frame.

        :param frame_id: Frame ID
        :param asset_ids: Set of asset IDs to get attachments for
        :return: Dict mapping asset_id -> list of attachments
        """
        attachments_map: dict[str, list] = {}
        cursor = None

        while True:
            params = {'limit': 200}
            if cursor:
                params['cursor'] = cursor

            response = await self._client.get(f'/frames/{frame_id}/assets.json', query_params=params)
            assets = response.get('assets', [])

            for asset in assets:
                aid = asset.get('id')
                if aid in asset_ids:
                    attachments_map[aid] = asset.get('attachments', [])

            cursor = response.get('next_page_cursor')
            if not cursor or len(attachments_map) >= len(asset_ids):
                break
            await asyncio.sleep(0.3)

        return attachments_map

    async def caption_album(
        self,
        frame_id: str,
        playlist_id: str,
        caption: str,
        include_date: bool = False,
        progress_callback: Callable[[str, int, int], None] | None = None,
        max_workers: int = 10,
        get_all_assets: Callable[[str], Awaitable[list[Asset]]] | None = None
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
        :param get_all_assets: Optional callable to get all assets for a frame (needed for include_date)
        :return: Number of photos captioned
        """
        # Phase 1: Fetching assets
        def on_fetch_progress(count: int) -> None:
            if progress_callback:
                progress_callback("fetching", count, 0)

        # Build map of asset_id -> date for date formatting
        date_map: dict[str, str] = {}
        if include_date:
            if get_all_assets is None:
                raise ValueError("get_all_assets callable is required when include_date is True")
            assets = await get_all_assets(frame_id)
            playlist_asset_ids = set(await paginate(
                self.playlist_api.get_playlist_asset_ids,
                playlist_id, frame_id,
                delay=0.5,
                progress_callback=on_fetch_progress
            ))
            # Filter to only assets in this playlist and build date map
            for asset in assets:
                if asset.id in playlist_asset_ids:
                    date_map[asset.id] = format_caption_date(asset.taken_at_dt)
            asset_ids = list(date_map.keys())
        else:
            asset_ids = await paginate(
                self.playlist_api.get_playlist_asset_ids,
                playlist_id, frame_id,
                delay=0.5,
                progress_callback=on_fetch_progress
            )
        total = len(asset_ids)

        # Pre-fetch all attachments for these assets
        attachments_map = await self.get_asset_attachments_map(frame_id, set(asset_ids))

        # Phase 2: Delete existing captions
        semaphore = asyncio.Semaphore(max_workers)
        deleted = 0

        async def delete_one(asset_id: str) -> None:
            nonlocal deleted
            async with semaphore:
                existing = attachments_map.get(asset_id, [])
                for att in existing:
                    if att.get('type') == 'caption':
                        try:
                            await self.attachment_api.delete_caption(att['id'])
                        except Exception as e:
                            logger.debug(f"Failed to delete caption {att.get('id')}: {e}")
                deleted += 1
                if progress_callback:
                    progress_callback("deleting", deleted, total)

        await asyncio.gather(*[delete_one(aid) for aid in asset_ids])

        # Phase 3: Create new captions
        captioned = 0
        failed = 0

        async def caption_one(asset_id: str) -> None:
            nonlocal captioned, failed
            async with semaphore:
                try:
                    # Format caption with date if requested
                    if include_date and asset_id in date_map:
                        full_caption = f"{caption} ({date_map[asset_id]})"
                    else:
                        full_caption = caption
                    await self.attachment_api.create_caption(asset_id, frame_id, full_caption)
                    captioned += 1
                except Exception as e:
                    logger.debug(f"Failed to caption asset {asset_id}: {e}")
                    failed += 1
                    captioned += 1
                if progress_callback:
                    progress_callback("captioning", captioned, total)

        await asyncio.gather(*[caption_one(aid) for aid in asset_ids])

        if failed > 0:
            logger.warning(f'Failed to caption {failed}/{total} photos')

        return total
