import io
import json
from unittest.mock import patch
import urllib.error

import pytest

from services.notifications import NotificationError, send_telegram_message


class _FakeResponse:
    def __init__(self, payload: dict):
        self.status = 200
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_send_telegram_message_success():
    with patch("urllib.request.urlopen", return_value=_FakeResponse({"ok": True, "result": {}})):
        send_telegram_message("token", "chat", "hello")


def test_send_telegram_message_http_error():
    http_error = urllib.error.HTTPError(
        url="https://api.telegram.org",
        code=400,
        msg="Bad Request",
        hdrs=None,
        fp=io.BytesIO(b'{"ok":false,"description":"Bad Request"}'),
    )
    with patch("urllib.request.urlopen", side_effect=http_error):
        with pytest.raises(NotificationError, match="HTTP error"):
            send_telegram_message("token", "chat", "hello")

