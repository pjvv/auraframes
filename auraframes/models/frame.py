from enum import Enum

from pydantic import BaseModel

from auraframes.models.meta import create_partial_model
from auraframes.models.user import User


class Feature(Enum):
    SKIP_VIDEO_PRELOAD = 'skip_video_preload'
    UDP_COMMANDS = 'udp_commands'
    MQTT_ENABLED = 'mqtt_enabled'


class Frame(BaseModel):
    id: str
    name: str
    user_id: str
    software_version: str
    build_version: str
    hw_android_version: str
    created_at: str
    updated_at: str
    handled_at: str
    deleted_at: str | None = None
    updated_at_on_client: str | None = None
    orientation: int
    auto_brightness: bool
    min_brightness: int
    max_brightness: int
    brightness: int | None = None
    sense_motion: bool
    default_speed: str | None = None
    slideshow_interval: int
    slideshow_auto: bool
    digits: int
    contributors: list[User] | None = None
    contributor_tokens: list[dict] = []
    hw_serial: str
    matting_color: str
    trim_color: str
    is_handling: bool
    calibrations_last_modified_at: str
    gestures_on: bool
    portrait_pairing_off: bool | None = None
    live_photos_on: bool
    auto_processed_playlist_ids: list[object] = []  # unknown
    time_zone: str
    wifi_network: str
    cold_boot_at: str | None = None
    is_charity_water_frame: bool
    num_assets: int
    thanks_on: bool
    frame_queue_url: str | None = None
    client_queue_url: str
    scheduled_display_sleep: bool
    scheduled_display_on_at: str | None = None
    scheduled_display_off_at: str | None = None
    forced_wifi_state: str | None = None
    forced_wifi_recipient_email: str | None = None
    is_analog_frame: bool
    control_type: str
    display_aspect_ratio: str
    has_claimable_gift: bool | None = None
    gift_billing_hint: str | None = None
    locale: str
    frame_type: int | None = None
    description: str | None = None
    representative_asset_id: str | None = None
    sort_mode: str | None = None
    email_address: str
    features: list[str] | None = None
    letterbox_style: str | None = None
    user: User
    playlists: list[dict] = []  # Playlist model not yet defined
    delivered_frame_gift: dict | None = None  # Gift model not yet defined
    last_feed_item: dict | None = None
    last_impression: dict | None = None
    last_impression_at: str | None = None
    child_albums: list = []
    smart_adds: list = []
    recent_assets: list = []

    def is_portrait(self) -> bool:
        return self.orientation == 2 or self.orientation == 3

    def get_frame_type(self) -> str | int:
        return self.frame_type if self.frame_type else "normal"


FramePartial = create_partial_model(Frame)
