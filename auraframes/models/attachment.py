from __future__ import annotations

from pydantic import BaseModel


class Attachment(BaseModel):
    """
    Represents an attachment on an asset. Currently used for captions.
    The 'attachments' framework may support other content types in the future.
    """
    id: str
    asset_id: str
    frame_id: str
    user_id: str
    type: str  # 'caption'
    data: str  # The caption text
    updated_by_user_id: str | None = None
    created_at: str
    updated_at: str
