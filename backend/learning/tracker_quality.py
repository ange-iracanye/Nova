"""Persist difficulty exposure per student."""

from __future__ import annotations

import hashlib
import json
import math
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


def _safe_count(value):
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError, OverflowError):
        return 0


def _json_safe(value):
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return None


def _load():
    file = _file()
    if not file.exists():
        return {}
    try:
        value = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError, UnicodeError):
        return {}
    if not isinstance(value, dict):
        return {}
    normalized = {}
    for key, item in value.items():
        if not isinstance(key, str) or not isinstance(item, dict):
            continue
        record = {
            level: _safe_count(item.get(level))
            for level in ("easy", "medium", "hard")
        }
        history = item.get("history")
        if not isinstance(history, list):
            history = []
        record["history"] = [
            {
                "difficulty": entry["difficulty"],
                "timestamp": str(entry.get("timestamp") or ""),
            }
            for entry in history
            if isinstance(entry, dict)
            and isinstance(entry.get("difficulty"), str)
            and entry.get("difficulty") in {"easy", "medium", "hard"}
        ][-100:]
        record["total"] = max(
            _safe_count(item.get("total")),
            record["easy"] + record["medium"] + record["hard"],
        )
        normalized[key] = record
    return normalized


def _save(data):
    file = _file()
    file.parent.mkdir(parents=True, exist_ok=True)
    clean = _json_safe(data if isinstance(data, dict) else {})
    temporary = file.with_suffix(".tmp")
    temporary.write_text(json.dumps(clean, indent=4, ensure_ascii=False, allow_nan=False), encoding="utf-8")
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
