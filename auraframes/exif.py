"""EXIF data handling for Aura Frames images."""
import io
import threading
from collections import OrderedDict
from fractions import Fraction
from typing import Any

import piexif
import piexif.helper
from geopy import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable
from loguru import logger

from auraframes.models.asset import Asset

# Most of the exif writing is from:
# https://gitlab.com/searchwing/development/payloads/ros-generic/-/blob/master/searchwing_common_py/scripts/ImageSaverNode.py

# Maximum cache entries to prevent unbounded memory growth
MAX_CACHE_SIZE = 1000


def build_gps_ifd(location_dms: tuple | None) -> dict:
    """Build GPS IFD dictionary from DMS coordinates."""
    if not location_dms:
        return {}

    return {
        piexif.GPSIFD.GPSVersionID: (2, 3, 0, 0),
        piexif.GPSIFD.GPSLatitudeRef: location_dms[0][3],
        piexif.GPSIFD.GPSLatitude: location_dms[0][:-1],
        piexif.GPSIFD.GPSLongitudeRef: location_dms[1][3],
        piexif.GPSIFD.GPSLongitude: location_dms[1][:-1],
        piexif.GPSIFD.GPSAltitudeRef: 0,
        piexif.GPSIFD.GPSAltitude: (0, 1),
        piexif.GPSIFD.GPSStatus: b'A'
    }


class ExifWriter:
    """Writer for EXIF metadata to images.

    Includes geocoding for location names with thread-safe caching.
    """

    def __init__(
        self,
        user_agent: str = "AuraFrames Python Client",
        max_cache_size: int = MAX_CACHE_SIZE
    ):
        """
        Initialize EXIF writer.

        :param user_agent: User agent for Nominatim geocoder
        :param max_cache_size: Maximum number of geocode results to cache
        """
        self._geolocator = Nominatim(user_agent=user_agent)
        self._cache: OrderedDict[str, tuple] = OrderedDict()
        self._max_cache_size = max_cache_size
        self._cache_lock = threading.Lock()

    def _lookup_gps(self, location_name: str, max_retries: int = 2) -> tuple | None:
        """
        Look up GPS coordinates for a location name.

        Uses thread-safe LRU cache to avoid repeated geocoding requests.

        :param location_name: Location name to geocode
        :param max_retries: Maximum retries on timeout (default 2)
        :return: Tuple of (longitude_dms, latitude_dms) or None if not found
        """
        # Check cache first (thread-safe)
        with self._cache_lock:
            if location_name in self._cache:
                # Move to end for LRU behavior
                self._cache.move_to_end(location_name)
                return self._cache[location_name]

        # Geocode with retry on timeout
        location = None
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                location = self._geolocator.geocode(location_name)
                break
            except GeocoderTimedOut as e:
                last_error = e
                if attempt < max_retries:
                    logger.debug(f"Geocoding timeout for '{location_name}', retrying...")
                    continue
                logger.warning(f"Geocoding timed out for '{location_name}' after {max_retries + 1} attempts")
                return None
            except (GeocoderServiceError, GeocoderUnavailable) as e:
                logger.warning(f"Geocoding service error for '{location_name}': {e}")
                return None
            except Exception as e:
                logger.warning(f"Unexpected geocoding error for '{location_name}': {type(e).__name__}: {e}")
                return None

        if not location:
            return None

        longitude_dms = convert_to_rational_dms(to_deg(location.longitude, is_longitude=True))
        latitude_dms = convert_to_rational_dms(to_deg(location.latitude, is_longitude=False))
        result = (longitude_dms, latitude_dms)

        # Add to cache (thread-safe, with LRU eviction)
        with self._cache_lock:
            self._cache[location_name] = result
            # Evict oldest entries if cache is full
            while len(self._cache) > self._max_cache_size:
                self._cache.popitem(last=False)

        return result

    def write_exif(
        self,
        image: bytes,
        asset: Asset,
        thumbnail: bytes | None = None,
        set_gps_ifd: bool = True
    ) -> io.BytesIO:
        """
        Write EXIF metadata to an image.

        :param image: Image data as bytes
        :param asset: Asset model containing metadata
        :param thumbnail: Optional thumbnail image bytes
        :param set_gps_ifd: Whether to add GPS data from location name (default True)
        :return: BytesIO containing the image with EXIF data
        """
        taken_datetime = asset.taken_at_dt.strftime('%Y:%m:%d %H:%M:%S').encode()

        exif_dict: dict[str, Any] = {
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: taken_datetime,
                piexif.ExifIFD.DateTimeDigitized: taken_datetime,
                piexif.ExifIFD.OffsetTime: b'-05:00',
                piexif.ExifIFD.OffsetTimeOriginal: b'-05:00',

            },
            '0th': {
                piexif.ImageIFD.DateTime: taken_datetime,
                piexif.ImageIFD.Artist: asset.user.name if asset.user else None
            }
        }

        if set_gps_ifd and asset.location_name:
            location_dms = self._lookup_gps(asset.location_name)
            exif_dict['GPS'] = build_gps_ifd(location_dms)

        if thumbnail:
            exif_dict['thumbnail'] = thumbnail
            exif_dict['1st'] = {
                piexif.ImageIFD.Make: "Canon",
                piexif.ImageIFD.XResolution: (40, 1),
                piexif.ImageIFD.YResolution: (40, 1),
                piexif.ImageIFD.Software: "piexif"
            }

        new_image = io.BytesIO()
        exif_bytes = piexif.dump(exif_dict)

        try:
            piexif.insert(exif_bytes, image, new_image)
        except (ValueError, TypeError, piexif.InvalidImageDataError) as e:
            logger.warning(f'Failed to write EXIF to image: {e}')

        return new_image

    def clear_cache(self) -> None:
        """Clear the geocoding cache."""
        with self._cache_lock:
            self._cache.clear()


def change_to_rational(number: float) -> tuple[int, int]:
    """Convert a number to a rational tuple (numerator, denominator)."""
    f = Fraction(str(number))
    return f.numerator, f.denominator


def convert_to_rational_dms(dms: tuple[int, int, float, str]) -> tuple:
    """Convert DMS tuple to rational format for EXIF."""
    return change_to_rational(dms[0]), change_to_rational(dms[1]), change_to_rational(dms[2]), dms[3]


def clone_exif(original_path: str, clone_path: str) -> None:
    """Copy EXIF data from one image file to another."""
    piexif.transplant(original_path, clone_path)


def get_readable_exif(image_path: str) -> dict[str, dict]:
    """
    Extract EXIF data from an image as a readable dictionary.

    :param image_path: Path to image file
    :return: Dictionary of EXIF data grouped by IFD
    """
    exif_dict = piexif.load(image_path)
    readable_dict: dict[str, dict] = {}
    for ifd in exif_dict:
        readable_dict[ifd] = {}
        if not exif_dict[ifd]:
            continue
        for tag in exif_dict[ifd]:
            if ifd != 'thumbnail':
                readable_dict[ifd][piexif.TAGS[ifd][tag]["name"]] = exif_dict[ifd][tag]
            else:
                readable_dict[ifd][tag] = exif_dict[ifd][tag]
    return readable_dict


def to_deg(value: float, is_longitude: bool) -> tuple[int, int, float, str]:
    """
    Convert decimal coordinates to degrees, minutes, seconds tuple.

    :param value: Decimal GPS coordinate
    :param is_longitude: True for longitude, False for latitude
    :return: Tuple of (degrees, minutes, seconds, direction)
    """
    loc = ["W", "E"] if is_longitude else ["S", "N"]

    if value < 0:
        loc_value = loc[0]
    elif value > 0:
        loc_value = loc[1]
    else:
        loc_value = ""

    abs_value = abs(value)
    deg = int(abs_value)
    t1 = (abs_value - deg) * 60
    minutes = int(t1)
    sec = round((t1 - minutes) * 60, 5)
    return deg, minutes, sec, loc_value
