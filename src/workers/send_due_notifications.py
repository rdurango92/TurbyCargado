from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from services.notifications import (
    NotificationError,
    build_end_message,
    build_start_message,
    send_telegram_message,
)
from services.storage import create_storage_from_env
from services.time_ui import from_utc_iso_to_local


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
LOGGER = logging.getLogger("send_due_notifications")


def _build_message(job: dict[str, str]) -> str:
    timezone_name = job["timezone"]
    start_local = from_utc_iso_to_local(job["start_at_utc"], timezone_name)
    end_local = from_utc_iso_to_local(job["end_at_utc"], timezone_name)

    if job["event_type"] == "start":
        return build_start_message(
            start_local=start_local,
            end_local=end_local,
            start_soc=int(job["start_soc"]),
            target_soc=int(job["target_soc"]),
        )

    return build_end_message(
        end_local=end_local,
        target_soc=int(job["target_soc"]),
    )


def main() -> int:
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not telegram_bot_token or not telegram_chat_id:
        raise RuntimeError(
            "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID environment variables."
        )

    storage = create_storage_from_env()
    now_utc = datetime.now(timezone.utc)
    due_jobs = storage.list_due_jobs(now_utc=now_utc, limit=200)
    LOGGER.info("Found %s due jobs", len(due_jobs))

    sent = 0
    failed = 0
    for job in due_jobs:
        job_id = job["id"]
        cycle_id = job["cycle_id"]
        event_type = job["event_type"]

        try:
            message = _build_message(job)
            send_telegram_message(
                bot_token=telegram_bot_token,
                chat_id=telegram_chat_id,
                text=message,
            )
            storage.mark_job_sent(job_id=job_id, sent_at_utc=datetime.now(timezone.utc))
            if event_type == "end":
                storage.mark_cycle_completed(cycle_id=cycle_id)
            sent += 1
        except NotificationError as exc:
            storage.mark_job_failed_attempt(job_id=job_id, error=str(exc), max_attempts=5)
            failed += 1
            LOGGER.error(
                "Notification error for job_id=%s cycle_id=%s event_type=%s error=%s",
                job_id,
                cycle_id,
                event_type,
                exc,
            )
        except Exception as exc:
            storage.mark_job_failed_attempt(job_id=job_id, error=str(exc), max_attempts=5)
            failed += 1
            LOGGER.exception(
                "Unexpected error for job_id=%s cycle_id=%s event_type=%s",
                job_id,
                cycle_id,
                event_type,
            )

    LOGGER.info("Completed dispatch sent=%s failed=%s", sent, failed)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

