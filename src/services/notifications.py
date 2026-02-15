from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime

from services.time_ui import format_datetime_12h


class NotificationError(RuntimeError):
    """Raised when a notification cannot be delivered."""


def send_telegram_message(
    bot_token: str,
    chat_id: str,
    text: str,
    timeout_seconds: int = 10,
) -> None:
    """Send a plain-text Telegram message using Bot API."""
    if not bot_token:
        raise ValueError("bot_token is required")
    if not chat_id:
        raise ValueError("chat_id is required")

    payload = json.dumps(
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        url=f"https://api.telegram.org/bot{bot_token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8", errors="replace")
            status = getattr(response, "status", 200)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise NotificationError(f"Telegram HTTP error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise NotificationError(f"Telegram connection error: {exc.reason}") from exc

    if status >= 400:
        raise NotificationError(f"Telegram returned status {status}")

    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise NotificationError("Telegram returned invalid JSON payload") from exc

    if not data.get("ok", False):
        raise NotificationError(f"Telegram API rejected message: {data}")


def build_start_message(
    start_local: datetime,
    end_local: datetime,
    start_soc: int,
    target_soc: int,
) -> str:
    return (
        "Carga iniciada\n"
        f"Inicio: {format_datetime_12h(start_local)}\n"
        f"Bateria: {start_soc}% -> {target_soc}%\n"
        f"Fin estimado: {format_datetime_12h(end_local)}"
    )


def build_end_message(
    end_local: datetime,
    target_soc: int,
) -> str:
    return (
        "Carga estimada completada\n"
        f"Hora estimada: {format_datetime_12h(end_local)}\n"
        f"Objetivo: {target_soc}%"
    )

