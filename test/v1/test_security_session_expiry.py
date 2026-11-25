from datetime import datetime, timedelta, timezone
from threading import RLock
import time

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from backend.security import authenticate_session


def _request(token="session-token"):
    return Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/private",
            "headers": [(b"authorization", f"Bearer {token}".encode("ascii"))],
            "query_string": b"",
            "server": ("testserver", 80),
            "client": ("127.0.0.1", 12345),
            "scheme": "http",
        }
    )


@pytest.mark.parametrize(
    "expires_at",
    [
        (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),
        time.time() - 1,
        10**1000,
        float("inf"),
        float("nan"),
        "not-a-timestamp",
        None,
        "",
    ],
)
def test_authenticate_session_rejects_and_removes_expired_or_invalid_expiry(expires_at):
    sessions = {"session-token": {"email": "student@example.com", "expires_at": expires_at}}

    with pytest.raises(HTTPException) as error:
        authenticate_session(_request(), sessions, RLock())

    assert error.value.status_code == 401
    assert "session-token" not in sessions


def test_authenticate_session_accepts_future_iso_expiry_and_updates_last_seen():
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=5)).isoformat()
    sessions = {"session-token": {"email": "student@example.com", "expires_at": expires_at}}

    result = authenticate_session(_request(), sessions, RLock())

    assert result["email"] == "student@example.com"
    assert result["last_seen_epoch"] > 0
    assert sessions["session-token"]["last_seen_epoch"] == result["last_seen_epoch"]


def test_authenticate_session_accepts_future_epoch_expiry():
    sessions = {
        "session-token": {
            "email": "student@example.com",
            "expires_at": time.time() + 300,
        }
    }

    result = authenticate_session(_request(), sessions, RLock())

    assert result["email"] == "student@example.com"


def test_authenticate_session_removes_session_with_missing_expiry():
    sessions = {"session-token": {"email": "student@example.com"}}

    with pytest.raises(HTTPException) as error:
        authenticate_session(_request(), sessions, RLock())

    assert error.value.status_code == 401
    assert sessions == {}
