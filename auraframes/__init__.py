"""Aura Frames API Client.

A Python client for the Aura Frames (PUSHD) API, providing programmatic
access to photo frame management functionality.

Example usage:
    from auraframes import Aura

    async with Aura() as aura:
        await aura.login(email="user@example.com", password="password")
        frames = await aura.frame_api.get_frames()
        for frame in frames:
            print(f"Frame: {frame.name}")
"""

from auraframes.aura import Aura
from auraframes.client import Client
from auraframes.exceptions import (
    AuraError,
    AuthenticationError,
    APIError,
    ConfigurationError,
    ValidationError,
    NetworkError,
)

# Models
from auraframes.models.asset import Asset, AssetPartialId
from auraframes.models.frame import Frame, FramePartial
from auraframes.models.user import User
from auraframes.models.activity import Activity
from auraframes.models.attachment import Attachment

# Services
from auraframes.services.image_service import ImageService
from auraframes.services.caption_service import CaptionService

__version__ = "0.1.0"

__all__ = [
    # Main entry point
    "Aura",
    "Client",
    # Exceptions
    "AuraError",
    "AuthenticationError",
    "APIError",
    "ConfigurationError",
    "ValidationError",
    "NetworkError",
    # Models
    "Asset",
    "AssetPartialId",
    "Frame",
    "FramePartial",
    "User",
    "Activity",
    "Attachment",
    # Services
    "ImageService",
    "CaptionService",
]
