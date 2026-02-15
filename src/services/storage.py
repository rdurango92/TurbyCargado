from __future__ import annotations

import importlib
import os
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS charge_cycles (
  id TEXT PRIMARY KEY,
  created_at_utc TEXT NOT NULL,
  timezone TEXT NOT NULL,
  start_at_utc TEXT NOT NULL,
  end_at_utc TEXT NOT NULL,
  start_soc INTEGER NOT NULL CHECK (start_soc BETWEEN 0 AND 100),
  target_soc INTEGER NOT NULL CHECK (target_soc BETWEEN 0 AND 100),
  estimated_minutes INTEGER NOT NULL CHECK (estimated_minutes >= 0),
  slope REAL NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('scheduled','completed','cancelled'))
);

CREATE TABLE IF NOT EXISTS notification_jobs (
  id TEXT PRIMARY KEY,
  cycle_id TEXT NOT NULL,
  event_type TEXT NOT NULL CHECK (event_type IN ('start','end')),
  scheduled_at_utc TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pending','sent','failed')),
  attempt_count INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  sent_at_utc TEXT,
  FOREIGN KEY (cycle_id) REFERENCES charge_cycles(id)
);

CREATE INDEX IF NOT EXISTS idx_jobs_due
ON notification_jobs (status, scheduled_at_utc);

CREATE UNIQUE INDEX IF NOT EXISTS uq_cycle_event
ON notification_jobs (cycle_id, event_type);
"""


def _to_utc_iso(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("Datetime values must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat(timespec="seconds")


def _row_to_dict(row: Any) -> dict[str, Any]:
    if isinstance(row, sqlite3.Row):
        return dict(row)
    if isinstance(row, dict):
        return row
    if hasattr(row, "keys"):
        return {key: row[key] for key in row.keys()}
    raise TypeError(f"Unsupported row type for direct conversion: {type(row)!r}")


def _rows_to_dicts(rows: list[Any], columns: list[str] | None = None) -> list[dict[str, Any]]:
    """Convert DB rows from sqlite or libsql to dictionaries."""
    items: list[dict[str, Any]] = []
    for row in rows:
        try:
            items.append(_row_to_dict(row))
            continue
        except TypeError:
            pass

        if columns:
            items.append(dict(zip(columns, row)))
        else:
            raise TypeError(f"Cannot map row type without columns: {type(row)!r}")
    return items


@dataclass(frozen=True)
class ChargeCycleCreate:
    start_soc: int
    target_soc: int
    start_at_local: datetime
    timezone: str
    estimated_minutes: int

    def validate(self) -> None:
        if self.start_at_local.tzinfo is None:
            raise ValueError("start_at_local must be timezone-aware")
        if not (0 <= self.start_soc <= 100 and 0 <= self.target_soc <= 100):
            raise ValueError("SOC values must be in [0, 100]")
        if self.target_soc <= self.start_soc:
            raise ValueError("target_soc must be greater than start_soc")
        if self.estimated_minutes < 0:
            raise ValueError("estimated_minutes must be >= 0")


@dataclass(frozen=True)
class NotificationJob:
    cycle_id: str
    event_type: str
    scheduled_at_utc: datetime
    status: str = "pending"
    attempt_count: int = 0

    def validate(self) -> None:
        if self.event_type not in {"start", "end"}:
            raise ValueError("event_type must be one of: start, end")
        if self.status not in {"pending", "sent", "failed"}:
            raise ValueError("status must be one of: pending, sent, failed")
        if self.scheduled_at_utc.tzinfo is None:
            raise ValueError("scheduled_at_utc must be timezone-aware")


class Storage:
    def __init__(self, connection: Any, auto_init_schema: bool = True):
        self.conn = connection
        if hasattr(self.conn, "row_factory"):
            self.conn.row_factory = sqlite3.Row
        if auto_init_schema:
            self.initialize_schema()

    def initialize_schema(self) -> None:
        if hasattr(self.conn, "executescript"):
            self.conn.executescript(SCHEMA_SQL)
        else:
            cursor = self.conn.cursor()
            for statement in [stmt.strip() for stmt in SCHEMA_SQL.split(";") if stmt.strip()]:
                cursor.execute(statement)
        self.conn.commit()

    def insert_cycle(self, cycle: ChargeCycleCreate, slope: float) -> dict[str, Any]:
        cycle.validate()
        if slope <= 0:
            raise ValueError("slope must be > 0")

        cycle_id = uuid.uuid4().hex
        created_at_utc = datetime.now(timezone.utc)
        end_at_local = cycle.start_at_local + timedelta(minutes=cycle.estimated_minutes)
        start_at_utc = cycle.start_at_local.astimezone(timezone.utc)
        end_at_utc = end_at_local.astimezone(timezone.utc)

        self.conn.execute(
            """
            INSERT INTO charge_cycles (
                id, created_at_utc, timezone, start_at_utc, end_at_utc,
                start_soc, target_soc, estimated_minutes, slope, status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'scheduled')
            """,
            (
                cycle_id,
                _to_utc_iso(created_at_utc),
                cycle.timezone,
                _to_utc_iso(start_at_utc),
                _to_utc_iso(end_at_utc),
                cycle.start_soc,
                cycle.target_soc,
                cycle.estimated_minutes,
                slope,
            ),
        )
        self.conn.commit()

        return {
            "id": cycle_id,
            "created_at_utc": created_at_utc,
            "start_at_local": cycle.start_at_local,
            "end_at_local": end_at_local,
            "start_at_utc": start_at_utc,
            "end_at_utc": end_at_utc,
            "start_soc": cycle.start_soc,
            "target_soc": cycle.target_soc,
            "estimated_minutes": cycle.estimated_minutes,
            "timezone": cycle.timezone,
            "status": "scheduled",
        }

    def insert_notification_job(self, job: NotificationJob) -> str:
        job.validate()
        job_id = uuid.uuid4().hex
        self.conn.execute(
            """
            INSERT INTO notification_jobs (
                id, cycle_id, event_type, scheduled_at_utc, status, attempt_count
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                job_id,
                job.cycle_id,
                job.event_type,
                _to_utc_iso(job.scheduled_at_utc),
                job.status,
                job.attempt_count,
            ),
        )
        self.conn.commit()
        return job_id

    def list_due_jobs(self, now_utc: datetime, limit: int = 100) -> list[dict[str, Any]]:
        cursor = self.conn.execute(
            """
            SELECT
                j.id, j.cycle_id, j.event_type, j.scheduled_at_utc, j.status,
                j.attempt_count, j.last_error, j.sent_at_utc,
                c.timezone, c.start_at_utc, c.end_at_utc, c.start_soc, c.target_soc, c.status AS cycle_status
            FROM notification_jobs AS j
            INNER JOIN charge_cycles AS c ON c.id = j.cycle_id
            WHERE j.status = 'pending' AND j.scheduled_at_utc <= ?
            ORDER BY j.scheduled_at_utc ASC
            LIMIT ?
            """,
            (_to_utc_iso(now_utc), limit),
        )
        rows = cursor.fetchall()
        columns = [col[0] for col in (cursor.description or [])]
        return _rows_to_dicts(rows, columns=columns)

    def mark_job_sent(self, job_id: str, sent_at_utc: datetime | None = None) -> None:
        sent_at_utc = sent_at_utc or datetime.now(timezone.utc)
        self.conn.execute(
            """
            UPDATE notification_jobs
            SET status = 'sent', sent_at_utc = ?, last_error = NULL
            WHERE id = ?
            """,
            (_to_utc_iso(sent_at_utc), job_id),
        )
        self.conn.commit()

    def mark_job_failed_attempt(self, job_id: str, error: str, max_attempts: int = 5) -> None:
        self.conn.execute(
            """
            UPDATE notification_jobs
            SET
                attempt_count = attempt_count + 1,
                last_error = ?,
                status = CASE
                    WHEN attempt_count + 1 >= ? THEN 'failed'
                    ELSE 'pending'
                END
            WHERE id = ?
            """,
            (error[:1000], max_attempts, job_id),
        )
        self.conn.commit()

    def mark_cycle_completed(self, cycle_id: str) -> None:
        self.conn.execute(
            "UPDATE charge_cycles SET status = 'completed' WHERE id = ?",
            (cycle_id,),
        )
        self.conn.commit()

    def list_recent_cycles(self, limit: int = 30) -> list[dict[str, Any]]:
        cursor = self.conn.execute(
            """
            SELECT
                id, created_at_utc, timezone, start_at_utc, end_at_utc,
                start_soc, target_soc, estimated_minutes, slope, status
            FROM charge_cycles
            ORDER BY created_at_utc DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()
        columns = [col[0] for col in (cursor.description or [])]
        return _rows_to_dicts(rows, columns=columns)

    def close(self) -> None:
        if hasattr(self.conn, "close"):
            self.conn.close()


def _connect_via_libsql(url: str, auth_token: str) -> Any:
    try:
        module = importlib.import_module("libsql_experimental")
    except ImportError as exc:
        raise RuntimeError(
            "libsql_experimental is not installed. Add libsql-experimental to requirements."
        ) from exc

    connect = getattr(module, "connect", None)
    if connect is None:
        raise RuntimeError("libsql_experimental.connect is unavailable")

    attempts: list[tuple[tuple[Any, ...], dict[str, Any]]] = [
        ((url,), {"auth_token": auth_token}),
        ((), {"database": url, "auth_token": auth_token}),
        ((), {"url": url, "auth_token": auth_token}),
        ((url,), {"token": auth_token}),
        ((), {"database": url, "token": auth_token}),
        ((url,), {}),
    ]

    last_error: Exception | None = None
    for args, kwargs in attempts:
        try:
            conn = connect(*args, **kwargs)
            if conn is not None:
                return conn
        except TypeError as exc:
            last_error = exc
            continue
        except Exception as exc:
            last_error = exc
            break

    raise RuntimeError(f"Unable to connect to Turso/libSQL: {last_error}")


def create_storage_from_turso(url: str, auth_token: str) -> Storage:
    if not url:
        raise ValueError("Missing Turso URL")
    if not auth_token:
        raise ValueError("Missing Turso auth token")
    connection = _connect_via_libsql(url=url, auth_token=auth_token)
    return Storage(connection=connection, auto_init_schema=True)


def create_storage_from_env() -> Storage:
    url = os.getenv("TURSO_URL", "").strip()
    auth_token = os.getenv("TURSO_AUTH_TOKEN", "").strip()
    return create_storage_from_turso(url=url, auth_token=auth_token)
