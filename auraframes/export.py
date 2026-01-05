import os
import shutil
from datetime import datetime
from io import BytesIO

from PIL import Image, UnidentifiedImageError
import httpx

from auraframes.exif import ExifWriter
from auraframes.models.asset import Asset
from auraframes.utils import settings


def _get_path_safe_datetime(date_str: datetime) -> str:
    return date_str.strftime('%Y%m%dT%H%M%S')


async def get_thumbnail(
    asset: Asset,
    original_image: BytesIO | None = None,
    client: httpx.AsyncClient | None = None
) -> bytes | None:
    """
    Fetch thumbnail for an asset, generating one from original if needed.

    :param asset: Asset to get thumbnail for
    :param original_image: Optional original image bytes to generate thumbnail from
    :param client: Optional httpx client for connection reuse
    :return: Thumbnail bytes or None
    """
    async def _fetch(http_client: httpx.AsyncClient) -> bytes | None:
        if not asset.thumbnail_url:
            return None
        thumbnail_response = await http_client.get(asset.thumbnail_url)
        thumbnail_bytes = BytesIO(thumbnail_response.content)
        try:
            with Image.open(thumbnail_bytes) as http_thumbnail:
                http_thumbnail.verify()
        except UnidentifiedImageError:
            if not original_image:
                return None
            with Image.open(original_image) as pil_image:
                out_bytes = BytesIO()
                pil_image.thumbnail((100, 100))
                pil_image.save(out_bytes, 'jpeg')
                return out_bytes.getvalue()
        return thumbnail_bytes.getvalue()

    if client:
        return await _fetch(client)
    async with httpx.AsyncClient() as new_client:
        return await _fetch(new_client)


async def get_image_from_asset(
    asset: Asset,
    path: str,
    exif_writer: ExifWriter | None = None,
    ignore_cache: bool = False,
    client: httpx.AsyncClient | None = None
) -> bytes:
    """
    Download and save an image from an asset.

    :param asset: Asset to download image for
    :param path: Directory path to save the image
    :param exif_writer: Optional EXIF writer for metadata
    :param ignore_cache: Whether to re-download even if file exists
    :param client: Optional httpx client for connection reuse
    :return: Original image bytes
    """
    new_filename = os.path.join(path, f'{_get_path_safe_datetime(asset.taken_at_dt)}-{asset.file_name}')
    if os.path.isfile(new_filename) and not ignore_cache:
        with open(new_filename, 'rb') as in_file:
            return in_file.read()

    async def _download(http_client: httpx.AsyncClient) -> bytes:
        response = await http_client.get(
            f'{settings.IMAGE_PROXY_BASE_URL}/{asset.user_id}/{asset.file_name}'
        )
        return response.content

    if client:
        original_image_bytes = await _download(client)
    else:
        async with httpx.AsyncClient() as new_client:
            original_image_bytes = await _download(new_client)

    if exif_writer:
        thumbnail = await get_thumbnail(asset, BytesIO(original_image_bytes), client)
        image = exif_writer.write_exif(original_image_bytes, asset, thumbnail)
        with open(new_filename, 'wb') as out:
            shutil.copyfileobj(image, out)
    else:
        with open(new_filename, 'wb') as out:
            out.write(original_image_bytes)
    return original_image_bytes
