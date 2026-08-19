"""Persist current learning session per student."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from backend.user_context import get_active_user


_PATCHED = False


def _file():
    base = Path("data/memory/sessions")
    base.mkdir(parents=True, exist_ok=True)
    email = get_active_user()
    if not email:
        return base / "default.json"
    uid = hashlib.sha256(email.encode("utf-8")).hexdigest()
    return base / f"{uid}.json"


def _default():
    return {"subject": None, "topic": None, "mode": None, "waiting_answer": False, "last_question": None, "score": 0, "questions": 0}


def _load():
    file = _file()
    if not file.exists():
        return _default()
    try:
        value = json.loads(file.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else _default()
    except Exception:
        return _default()


def _save(data):
    file = _file()
    temporary = file.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
    temporary.replace(file)


def install_session_quality(SessionManager):
    global _PATCHED
    if _PATCHED:
        return

    def start(self, subject, topic, mode):
        self.session = _load()
        self.session["subject"] = subject
        self.session["topic"] = topic
        self.session["mode"] = mode
        _save(self.session)

    def ask(self, question):
        self.session = _load()
        self.session["waiting_answer"] = True
        self.session["last_question"] = question
        self.session["questions"] = int(self.session.get("questions", 0) or 0) + 1
        _save(self.session)

    def finish_question(self):
        self.session = _load()
        self.session["waiting_answer"] = False
        _save(self.session)

    def add_score(self, points):
        self.session = _load()
        self.session["score"] = float(self.session.get("score", 0) or 0) + float(points or 0)
        _save(self.session)

    def waiting(self):
        self.session = _load()
        return bool(self.session.get("waiting_answer"))

    def get(self):
        self.session = _load()
        return dict(self.session)

    SessionManager.start = start
    SessionManager.ask = ask
    SessionManager.finish_question = finish_question
    SessionManager.add_score = add_score
    SessionManager.waiting = waiting
    SessionManager.get = get
    _PATCHED = True
