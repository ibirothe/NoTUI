from __future__ import annotations

from datetime import UTC, datetime, tzinfo


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def format_display_time(timestamp: str, timezone: tzinfo | None = None) -> str:
    try:
        value = timestamp.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(value)
        display_time = parsed.astimezone(timezone)
    except ValueError:
        return timestamp
    month = display_time.strftime("%b")
    timezone_name = display_time.strftime("%Z") or display_time.strftime("%z")
    date = f"{month} {display_time.day}, {display_time.year}"
    return f"{date} at {display_time:%H:%M} {timezone_name}"
