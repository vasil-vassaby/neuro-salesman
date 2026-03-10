from __future__ import annotations

from datetime import datetime
from typing import Optional

from .utils.timezone import (
    format_local_datetime,
    from_utc,
    get_tz,
    now_utc,
    parse_local_datetime,
    to_utc,
)


def now_local() -> datetime:
    return now_utc().astimezone(get_tz())


def format_local_time(value: Optional[datetime]) -> str:
    local = from_utc(value)
    if local is None:
        return ""
    return local.strftime("%H:%M")

