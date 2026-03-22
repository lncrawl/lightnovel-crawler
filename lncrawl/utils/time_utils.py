from datetime import datetime, timezone
from typing import Any, Optional

import humanize
from dateutil.parser import parse


def utc_now():
    return datetime.now(timezone.utc)


def current_timestamp():
    """Current UNIX timestamp in milliseconds"""
    return round(1000 * utc_now().timestamp())


def as_datetime(time: Any) -> Optional[datetime]:
    try:
        if isinstance(time, datetime):
            return time
        if isinstance(time, int) or isinstance(time, float):
            if time > 1e11:  # millisecond threshold
                time /= 1000
            return datetime.fromtimestamp(time, timezone.utc)
        if isinstance(time, str):
            return parse(time)
    except Exception:
        pass
    return None


def as_unix_time(time: Any) -> Optional[int]:
    dt = as_datetime(time)
    if not dt:
        return None
    return round(1000 * time.timestamp())


def format_time(time: Any) -> Optional[str]:
    dt = as_datetime(time)
    if dt is None:
        return None
    return humanize.naturaltime(dt)


def format_from_now(time: Any) -> Optional[str]:
    dt = as_datetime(time)
    if dt is None:
        return None
    return humanize.naturaltime(utc_now() - dt)
