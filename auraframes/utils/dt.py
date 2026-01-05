from datetime import datetime, timezone

AURA_DT_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'


def parse_aura_dt(aura_dt_str: str) -> datetime:
    return datetime.strptime(aura_dt_str, AURA_DT_FORMAT)


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_dt_to_aura(dt: datetime) -> str:
    return dt.strftime(AURA_DT_FORMAT)


def format_caption_date(dt: datetime) -> str:
    """Format datetime for caption display, e.g. 'March 2025'"""
    return dt.strftime('%B %Y')
