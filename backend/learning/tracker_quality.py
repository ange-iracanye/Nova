"""Persist difficulty exposure per student."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from backend.user_context import get_active_user


_PATCHED = False


def _file():
    base = Path("data/memory/difficulty")
    base.mkdir(parents=True, exist_ok=True)
    email = get_active_user()
    if not email:
        return base / "default.json"
    uid = hashlib.sha256(email.encode("utf-8")).hexdigest()
    return base / f"{uid}.json"


def _load():
    file = _file()
    if not file.exists():
        return {}
    try:
        value = json.loads(file.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except Exception:
        return {}


def _save(data):
    file = _file()
    temporary = file.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
    temporary.replace(file)


def install_tracker_quality(UnderstandingTracker):
    global _PATCHED
    if _PATCHED:
        return

    original_update = UnderstandingTracker.update
    original_get = UnderstandingTracker.get

    def update(self, subject, difficulty):
        self.data = _load()
        result = original_update(self, subject, difficulty)
        _save(self.data)
        return result

    def get(self, subject=None):
        self.data = _load()
        return original_get(self, subject)

    UnderstandingTracker.update = update
    UnderstandingTracker.get = get
    _PATCHED = True
