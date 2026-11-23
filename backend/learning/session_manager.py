from __future__ import annotations

import math
from copy import deepcopy
from typing import Any


class SessionManager:
    """Keep a small, validated in-memory state for one learning session."""

    def __init__(self):
        self.session = self._empty_session()

    @staticmethod
    def _empty_session() -> dict[str, Any]:
        return {
            "subject": None,
            "topic": None,
            "mode": None,
            "waiting_answer": False,
            "last_question": None,
            "score": 0.0,
            "questions": 0,
        }

    @staticmethod
    def _safe_count(value: Any) -> int:
        try:
            return max(0, int(value or 0))
        except (TypeError, ValueError, OverflowError):
            return 0

    @staticmethod
    def _safe_score(value: Any) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError, OverflowError):
            return 0.0
        return score if math.isfinite(score) else 0.0

    @staticmethod
    def _label(value: Any) -> str | None:
        if value is None:
            return None
        label = str(value).strip()
        return label or None

    def start(self, subject, topic, mode):
        """Start a fresh session and clear all state from the previous one."""
        self.session = self._empty_session()
        self.session["subject"] = self._label(subject)
        self.session["topic"] = self._label(topic)
        self.session["mode"] = self._label(mode)
        return self.get()

    def ask(self, question):
        normalized = self._label(question)
        if normalized is None:
            self.session["waiting_answer"] = False
            self.session["last_question"] = None
            return False
        self.session["waiting_answer"] = True
        self.session["last_question"] = normalized
        self.session["questions"] = self._safe_count(self.session.get("questions")) + 1
        return True

    def finish_question(self):
        self.session["waiting_answer"] = False

    def add_score(self, points):
        try:
            increment = float(points)
        except (TypeError, ValueError, OverflowError):
            return self.session["score"]
        if not math.isfinite(increment):
            return self.session["score"]
        current_score = self._safe_score(self.session.get("score"))
        updated_score = current_score + increment
        if not math.isfinite(updated_score):
            return current_score
        self.session["score"] = updated_score
        return updated_score

    def waiting(self):
        return bool(self.session.get("waiting_answer"))

    def get(self):
        """Return a snapshot so callers cannot mutate internal session state."""
        return deepcopy(self.session)
