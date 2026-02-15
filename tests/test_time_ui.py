from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from services.time_ui import (
    combine_today_with_time,
    did_cross_midnight,
    from_utc_iso_to_local,
    to_utc_iso,
)


def test_local_to_utc_and_back():
    local_dt = datetime(2026, 2, 15, 10, 30, tzinfo=ZoneInfo("America/Mexico_City"))
    utc_iso = to_utc_iso(local_dt)
    back_local = from_utc_iso_to_local(utc_iso, "America/Mexico_City")
    assert back_local.hour == 10
    assert back_local.minute == 30
    assert back_local.date() == local_dt.date()


def test_cross_midnight_detection():
    now_local = datetime(2026, 2, 15, 23, 50, tzinfo=ZoneInfo("UTC"))
    start_local = combine_today_with_time(time(23, 55), "UTC", now_local=now_local)
    end_local = start_local + timedelta(minutes=10)
    assert did_cross_midnight(start_local, end_local) is True

