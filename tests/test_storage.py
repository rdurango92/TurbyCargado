import sqlite3
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from services.storage import ChargeCycleCreate, NotificationJob, Storage


def _build_storage() -> Storage:
    connection = sqlite3.connect(":memory:")
    return Storage(connection=connection, auto_init_schema=True)


def test_storage_insert_cycle_and_list_recent():
    storage = _build_storage()
    cycle = ChargeCycleCreate(
        start_soc=40,
        target_soc=80,
        start_at_local=datetime(2026, 2, 15, 12, 0, tzinfo=ZoneInfo("UTC")),
        timezone="UTC",
        estimated_minutes=120,
    )
    saved_cycle = storage.insert_cycle(cycle=cycle, slope=0.0023)
    rows = storage.list_recent_cycles(limit=30)
    assert saved_cycle["id"] == rows[0]["id"]
    assert rows[0]["start_soc"] == 40
    assert rows[0]["target_soc"] == 80


def test_storage_jobs_lifecycle():
    storage = _build_storage()
    cycle = ChargeCycleCreate(
        start_soc=35,
        target_soc=75,
        start_at_local=datetime(2026, 2, 15, 18, 0, tzinfo=ZoneInfo("UTC")),
        timezone="UTC",
        estimated_minutes=90,
    )
    saved_cycle = storage.insert_cycle(cycle=cycle, slope=0.0023)
    start_job_id = storage.insert_notification_job(
        NotificationJob(
            cycle_id=saved_cycle["id"],
            event_type="start",
            scheduled_at_utc=datetime.now(ZoneInfo("UTC")) - timedelta(minutes=1),
        )
    )
    end_job_id = storage.insert_notification_job(
        NotificationJob(
            cycle_id=saved_cycle["id"],
            event_type="end",
            scheduled_at_utc=datetime.now(ZoneInfo("UTC")) + timedelta(minutes=30),
        )
    )

    due_jobs = storage.list_due_jobs(now_utc=datetime.now(ZoneInfo("UTC")), limit=10)
    assert any(job["id"] == start_job_id for job in due_jobs)
    assert all(job["id"] != end_job_id for job in due_jobs)

    storage.mark_job_sent(start_job_id)
    storage.mark_job_failed_attempt(end_job_id, "temporary error", max_attempts=1)
    due_after_updates = storage.list_due_jobs(now_utc=datetime.now(ZoneInfo("UTC")) + timedelta(hours=1), limit=10)
    assert all(job["id"] != start_job_id for job in due_after_updates)
    assert all(job["id"] != end_job_id for job in due_after_updates)

