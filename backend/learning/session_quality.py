"""Persist current learning session per student."""

from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from pathlib import Path

from backend.user_context import get_active_user


_PATCHED = False


def _file():
    base = Path("data/memory/sessions")
    base.mkdir(parents=True, exist_ok=True)
    email = get_active_user()
    if not email:
        return base / "default.json"
    uid = hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()
    return base / f"{uid}.json"


def _default():
    return {
        "subject": None,
        "topic": None,
        "mode": None,
        "waiting_answer": False,
        "last_question": None,
        "score": 0.0,
        "questions": 0,
    }


def _label(value):
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def _safe_count(value):
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError, OverflowError):
        return 0


def _safe_score(value):
    try:
        score = float(value)
    except (TypeError, ValueError, OverflowError):
        return 0.0
    return score if math.isfinite(score) else 0.0


def _normalize(value):
    result = _default()
    if not isinstance(value, dict):
        return result
    for key in ("subject", "topic", "mode", "last_question"):
        result[key] = _label(value.get(key))
    result["waiting_answer"] = bool(value.get("waiting_answer"))
    result["score"] = _safe_score(value.get("score", 0))
    result["questions"] = _safe_count(value.get("questions", 0))
    return result


def _load():
    file = _file()
    if not file.exists():
        return _default()
    try:
        value = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError, UnicodeError):
        return _default()
    return _normalize(value)


def _save(data):
    file = _file()
    file.parent.mkdir(parents=True, exist_ok=True)
    clean = _normalize(data)
    temporary = file.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(clean, indent=4, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    temporary.replace(file)


def install_session_quality(SessionManager):
    global _PATCHED
    if _PATCHED:
        return

    def start(self, subject, topic, mode):
        self.session = _normalize({
            "subject": subject,
            "topic": topic,
            "mode": mode,
        })
        _save(self.session)
        return self.get()

    def ask(self, question):
        self.session = _load()
        normalized = _label(question)
        if normalized is None:
            self.session["waiting_answer"] = False
            self.session["last_question"] = None
            _save(self.session)
            return False
        self.session["waiting_answer"] = True
        self.session["last_question"] = normalized
        self.session["questions"] = _safe_count(self.session.get("questions")) + 1
        _save(self.session)
        return True

    def finish_question(self):
        self.session = _load()
        self.session["waiting_answer"] = False
        _save(self.session)

    def add_score(self, points):
        self.session = _load()
        try:
            increment = float(points)
        except (TypeError, ValueError, OverflowError):
            return self.session["score"]
        if not math.isfinite(increment):
            return self.session["score"]
        self.session["score"] += increment
        _save(self.session)
        return self.session["score"]

    def waiting(self):
        self.session = _load()
        return bool(self.session["waiting_answer"])

    def get(self):
        self.session = _load()
        return deepcopy(self.session)

    SessionManager.start = start
    SessionManager.ask = ask
    SessionManager.finish_question = finish_question
    SessionManager.add_score = add_score
    SessionManager.waiting = waiting
    SessionManager.get = get
    _PATCHED = True
