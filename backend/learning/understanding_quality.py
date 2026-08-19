"""Persist UnderstandingAnalyzer per student instead of globally."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from backend.user_context import get_active_user


_PATCHED = False


def _file():
    base = Path("data/memory/understanding")
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


def _save(history):
    file = _file()
    clean = {
        key: value
        for key, value in history.items()
        if key != "__global__" and isinstance(value, dict)
    }
    temporary = file.with_suffix(".tmp")
    temporary.write_text(json.dumps(clean, indent=4, ensure_ascii=False), encoding="utf-8")
    temporary.replace(file)


def install_understanding_quality(UnderstandingAnalyzer):
    global _PATCHED
    if _PATCHED:
        return

    original_analyze = UnderstandingAnalyzer.analyze
    original_get = UnderstandingAnalyzer.get

    def analyze(self, subject, question, answer):
        self.history = _load()
        result = original_analyze(self, subject, question, answer)
        _save(self.history)
        return result

    def get(self, subject=None):
        self.history = _load()
        return original_get(self, subject)

    UnderstandingAnalyzer.analyze = analyze
    UnderstandingAnalyzer.get = get
    _PATCHED = True
