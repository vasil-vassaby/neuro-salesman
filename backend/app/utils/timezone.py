from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from zoneinfo import ZoneInfo

from ..config import settings


_TZ = ZoneInfo(settings.tz or "Europe/Moscow")


def get_tz() -> ZoneInfo:
    return _TZ


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        local = value.replace(tzinfo=_TZ)
    else:
        local = value.astimezone(_TZ)
    return local.astimezone(timezone.utc)


def from_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(_TZ)


def parse_local_datetime(raw: str) -> datetime:
    naive = datetime.fromisoformat(raw)
    if naive.tzinfo is not None:
        return naive.astimezone(timezone.utc)
    local = naive.replace(tzinfo=_TZ)
    return local.astimezone(timezone.utc)


def format_local_datetime(value: Optional[datetime]) -> str:
    local = from_utc(value)
    if local is None:
        return ""
    return local.strftime("%d.%m.%Y %H:%M")

