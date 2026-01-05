from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator, ValidationInfo

from auraframes.models.user import User
from datetime import datetime

from auraframes.utils.dt import parse_aura_dt


class AssetPadding(BaseModel):
    top: float
    right: float
    bottom: float
    left: float


class AssetSetting(BaseModel):
    added_by_id: str
    asset_id: str
    created_at: str
    frame_id: str
    hidden: bool
    id: str
    last_impression_at: str
    reason: str  # Known values: "user"
    selected: bool
    updated_at: str
    updated_selected_at: str


class Asset(BaseModel):
    auto_landscape_16_10_rect: str | None = None
    auto_portrait_4_5_rect: str | None = None
    burst_id: Any = None
    burst_selection_types: Any = None
    colorized_file_name: str | None = None
    created_at_on_client: str | None = None
    data_uti: str
    duplicate_of_id: str | None = None
    duration: float | None = None
    duration_unclipped: float | None = None
    exif_orientation: int
    favorite: bool | None = None
    file_name: str
    glaciered_at: str
    good_resolution: bool
    handled_at: str | None = None
    hdr: bool | None = None
    height: int
    horizontal_accuracy: float | None = None
    id: str
    ios_media_subtypes: int | None = None
    is_live: bool | None = None
    is_subscription: bool
    landscape_16_10_url: str | None = None
    landscape_16_10_url_padding: AssetPadding | None = None
    landscape_rect: str | None = None
    landscape_url: str | None = None
    landscape_url_padding: AssetPadding | None = None
    live_photo_off: bool | None = None
    local_identifier: str
    location: list[float] | None = None  # Lat/Long
    location_name: str | None = None
    md5_hash: str | None = None
    minibar_landscape_url: str | None = None
    minibar_portrait_url: str | None = None
    minibar_url: str | None = None
    modified_at: str | None = None
    orientation: int | None = None
    original_file_name: str | None = None
    panorama: bool | None = None
    portrait_4_5_url: str | None = None
    portrait_4_5_url_padding: AssetPadding | None = None
    portrait_rect: str | None = None
    portrait_url: str | None = None
    portrait_url_padding: AssetPadding | None = None
    raw_file_name: str | None = None
    represents_burst: Any = None
    rotation_cw: int
    selected: bool
    source_id: str
    taken_at: str
    taken_at_granularity: Any = None
    taken_at_user_override_at: str | None = None
    thumbnail_url: str | None = None
    unglacierable: bool | None = None
    upload_priority: int
    uploaded_at: str
    user: User
    user_id: str
    user_landscape_16_10_rect: str | None = None
    user_landscape_rect: str | None = None
    user_portrait_4_5_rect: str | None = None
    user_portrait_rect: str | None = None
    video_clip_excludes_audio: bool | None = None
    video_clip_start: Any = None
    video_clipped_by_user_at: str | None = None
    video_file_name: str | None = None
    video_url: str | None = None
    widget_url: str | None = None
    width: int
    attachments: list = Field(default_factory=list)  # Captions and other attachments

    @property
    def taken_at_dt(self) -> datetime:
        return parse_aura_dt(self.taken_at)

    @property
    def is_local_asset(self) -> bool:
        return self.id is None


class AssetPartialId(BaseModel):
    id: Optional[str] = None
    local_identifier: Optional[str] = None
    user_id: Optional[str] = None

    @field_validator('id')
    @classmethod
    def check_id_or_local_id(cls, _id, info: ValidationInfo):
        if not info.data.get('local_identifier') and not _id:
            raise ValueError('Either id or local_identifier is required')
        return _id

    def to_request_format(self) -> dict[str, str]:
        """Convert to API request format.

        Returns either asset_id or asset_local_identifier based on available data.
        The field validator ensures at least one identifier is present.
        """
        # 'user_id': user_id # in the iphone version user_id is not passed in
        if self.id:
            return {'asset_id': self.id}
        # Validator ensures local_identifier exists if id is None
        # Use explicit check instead of assertion for runtime safety
        if self.local_identifier is None:
            raise ValueError('AssetPartialId requires either id or local_identifier')
        return {'asset_local_identifier': self.local_identifier}
