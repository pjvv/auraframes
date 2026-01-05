from pydantic import BaseModel


class User(BaseModel):
    id: str
    created_at: str
    updated_at: str
    name: str
    email: str
    short_id: str | None = None
    show_push_prompt: bool = False
    latest_app_version: str | None = None
    attribution_id: str | None = None
    attribution_string: str | None = None
    test_account: bool | None = None
    avatar_file_name: str | None = None
    has_frame: bool | None = None
    analytics_optout: bool | None = None
    admin_account: bool | None = False
    auth_token: str | None = None
