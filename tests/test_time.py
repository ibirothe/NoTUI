from __future__ import annotations

from datetime import UTC, timedelta, timezone

from notui.time import format_display_time

BERLIN_SUMMER = timezone(timedelta(hours=2), "CEST")


def test_format_display_time_formats_utc_timestamp() -> None:
    assert (
        format_display_time("2026-05-25T13:45:12.123456Z", timezone=BERLIN_SUMMER)
        == "May 25, 2026 at 15:45 CEST"
    )


def test_format_display_time_normalizes_offset_to_utc() -> None:
    assert (
        format_display_time("2026-05-25T15:45:12+02:00", timezone=UTC)
        == "May 25, 2026 at 13:45 UTC"
    )


def test_format_display_time_returns_invalid_input() -> None:
    assert format_display_time("not a timestamp") == "not a timestamp"
