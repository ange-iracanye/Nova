"""Persist UnderstandingAnalyzer per student instead of globally."""

from __future__ import annotations

import hashlib
import json
import math
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


def _safe_count(value):
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError, OverflowError):
        return 0


def _safe_score(value, default=50):
    try:
        score = float(value)
    except (TypeError, ValueError, OverflowError):
        return default
    if not math.isfinite(score):
        return default
    return max(0, min(100, int(score)))


def _normalize_record(value):
    defaults = {
        "attempts": 0,
        "confidence": 50,
        "understanding": 50,
        "engagement": 50,
        "difficulty": "medium",
        "learning_state": "developing",
        "trend": "stable",
        "mistakes": [],
        "signals": [],
        "last_signals": [],
        "question_types": {},
        "history": [],
        "recommended_action": "Continue monitoring.",
    }
    if not isinstance(value, dict):
        return defaults
    result = dict(value)
    result["attempts"] = _safe_count(value.get("attempts"))
    for key in ("confidence", "understanding", "engagement"):
        result[key] = _safe_score(value.get(key, defaults[key]), defaults[key])
    for key in ("difficulty", "learning_state", "trend", "recommended_action"):
        item = value.get(key)
        result[key] = item.strip() if isinstance(item, str) and item.strip() else defaults[key]
    for key in ("mistakes", "signals", "last_signals", "history"):
        item = value.get(key)
        result[key] = [entry for entry in item if isinstance(entry, dict)] if isinstance(item, list) else []
    question_types = value.get("question_types")
    result["question_types"] = {
        str(key): _safe_count(count)
        for key, count in question_types.items()
    } if isinstance(question_types, dict) else {}
    return _json_safe(result)


def _json_safe(value):
    if isinstance(value, dict):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
            if key != "__global__"
        }
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
    return {
        str(key): _normalize_record(item)
        for key, item in value.items()
        if isinstance(key, str) and key != "__global__" and isinstance(item, dict)
    }


def _save(history):
    file = _file()
    history = history if isinstance(history, dict) else {}
    clean = {
        key: _json_safe(value)
        for key, value in history.items()
        if isinstance(key, str) and key != "__global__" and isinstance(value, dict)
    }
    temporary = file.with_suffix(".tmp")
    temporary.write_text(json.dumps(clean, indent=4, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    temporary.replace(file)


def install_understanding_quality(UnderstandingAnalyzer):
    global _PATCHED
    if _PATCHED:
        return

    original_analyze = UnderstandingAnalyzer.analyze
    original_get = UnderstandingAnalyzer.get
    original_reset_subject = UnderstandingAnalyzer.reset_subject
    original_reset = UnderstandingAnalyzer.reset

    def analyze(self, subject, question, answer):
        self.history = _load()
        result = original_analyze(self, subject, question, answer)
        _save(self.history)
        return result

    def get(self, subject=None):
        self.history = _load()
        return original_get(self, subject)

    def reset_subject(self, subject):
        self.history = _load()
        result = original_reset_subject(self, subject)
        _save(self.history)
        return result

    def reset(self):
        self.history = _load()
        result = original_reset(self)
        _save(self.history)
        return result

    UnderstandingAnalyzer.analyze = analyze
    UnderstandingAnalyzer.get = get
    UnderstandingAnalyzer.reset_subject = reset_subject
    UnderstandingAnalyzer.reset = reset
    _PATCHED = True
