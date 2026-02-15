from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def get_timezone(timezone_name: str) -> ZoneInfo:
    """Return a valid timezone; fallback to UTC for unknown names."""
    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def round_time_to_step(value: time, step_minutes: int = 5) -> time:
    """Round a time value to the nearest N-minute boundary."""
    if step_minutes <= 0:
        raise ValueError("step_minutes must be a positive integer")

    total_minutes = value.hour * 60 + value.minute
    rounded = int(round(total_minutes / step_minutes) * step_minutes)
    rounded = max(0, min(rounded, (24 * 60) - step_minutes))
    return time(hour=rounded // 60, minute=rounded % 60)


def add_minutes_to_time(base_time: time, minutes: int) -> time:
    """Add minutes to a time, wrapping around midnight."""
    total = (base_time.hour * 60 + base_time.minute + minutes) % (24 * 60)
    return time(hour=total // 60, minute=total % 60)


def combine_today_with_time(
    selected_time: time,
    timezone_name: str,
    now_local: datetime | None = None,
) -> datetime:
    """Combine today's date with selected local time in the requested timezone."""
    tz = get_timezone(timezone_name)
    reference = now_local.astimezone(tz) if now_local else datetime.now(tz)
    return datetime.combine(reference.date(), selected_time, tzinfo=tz)


def did_cross_midnight(start_local: datetime, end_local: datetime) -> bool:
    """Return True when end datetime occurs on a different date than start."""
    return end_local.date() > start_local.date()


def format_time_12h(value: time) -> str:
    """Format time in 12-hour notation."""
    return value.strftime("%I:%M %p")


def format_datetime_12h(value: datetime) -> str:
    """Format datetime in day + 12-hour notation."""
    return value.strftime("%Y-%m-%d %I:%M %p")


def to_utc_iso(local_datetime: datetime) -> str:
    """Convert timezone-aware datetime to UTC ISO string."""
    if local_datetime.tzinfo is None:
        raise ValueError("local_datetime must be timezone-aware")
    return local_datetime.astimezone(timezone.utc).isoformat(timespec="seconds")


def parse_iso_datetime(value: str) -> datetime:
    """Parse an ISO datetime and support trailing Z notation."""
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def from_utc_iso_to_local(utc_iso: str, timezone_name: str) -> datetime:
    """Convert a UTC ISO datetime string to a local datetime."""
    parsed = parse_iso_datetime(utc_iso)
    tz = get_timezone(timezone_name)
    return parsed.astimezone(tz)

