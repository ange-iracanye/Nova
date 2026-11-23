"""User-isolated learning-memory compatibility layer."""

from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from datetime import datetime
from pathlib import Path

from backend.user_context import get_active_user, user_context

_PATCHED = False


def _path(email: str | None) -> Path:
    base = Path("data/memory/users")
    base.mkdir(parents=True, exist_ok=True)
    if not email:
        return base / "default-learning.json"
    uid = hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()
    return base / uid / "learning_memory.json"


def _default():
    return {
        "version": 3,
        "subjects": {},
        "concepts": {},
        "mistakes": [],
        "successful_strategies": [],
        "failed_strategies": [],
    }


def _safe_count(value):
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError, OverflowError):
        return 0


def _safe_confidence(value, default=50.0):
    try:
        confidence = float(value)
    except (TypeError, ValueError, OverflowError):
        return default
    if not math.isfinite(confidence):
        return default
    return max(0.0, min(100.0, confidence))


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


def _normalize(data):
    normalized = _default()
    if not isinstance(data, dict):
        return normalized

    subjects = data.get("subjects")
    if isinstance(subjects, dict):
        for subject, raw in subjects.items():
            if not isinstance(subject, str) or not subject.strip() or not isinstance(raw, dict):
                continue
            normalized["subjects"][subject.strip()] = {
                "confidence": _safe_confidence(raw.get("confidence", 50)),
                "attempts": _safe_count(raw.get("attempts")),
                "correct": _safe_count(raw.get("correct")),
                "incorrect": _safe_count(raw.get("incorrect")),
                "last_studied": str(raw.get("last_studied") or "") or None,
                "study_count": _safe_count(raw.get("study_count")),
            }

    concepts = data.get("concepts")
    if isinstance(concepts, dict):
        for key, raw in concepts.items():
            if not isinstance(key, str) or not isinstance(raw, dict):
                continue
            normalized["concepts"][key] = {
                "subject": str(raw.get("subject") or ""),
                "concept": str(raw.get("concept") or ""),
                "confidence": _safe_confidence(raw.get("confidence", 50)),
                "attempts": _safe_count(raw.get("attempts")),
                "difficulty": str(raw.get("difficulty") or "") or None,
                "first_seen": str(raw.get("first_seen") or ""),
                "last_seen": str(raw.get("last_seen") or ""),
            }

    for key in ("mistakes", "successful_strategies", "failed_strategies"):
        values = data.get(key)
        normalized[key] = [
            _json_safe(item) for item in values if isinstance(item, dict)
        ][-500:] if isinstance(values, list) else []

    normalized["version"] = 3
    return normalized


def _load(email):
    file = _path(email)
    file.parent.mkdir(parents=True, exist_ok=True)
    if not file.exists():
        return _default()
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError, UnicodeError):
        return _default()
    return _normalize(data)


def _save(email, data):
    file = _path(email)
    file.parent.mkdir(parents=True, exist_ok=True)
    clean = _json_safe(_normalize(data))
    temporary = file.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(clean, indent=4, ensure_ascii=False, allow_nan=False),
        encoding="utf-8",
    )
    temporary.replace(file)


def install_learning_quality(MemoryManager, LearningMemory):
    global _PATCHED
    if _PATCHED:
        return

    original_remember = MemoryManager.remember

    def remember(self, email, *args, **kwargs):
        with user_context(email):
            return original_remember(self, email, *args, **kwargs)

    MemoryManager.remember = remember

    def record_attempt(self, subject, confidence, correct=None):
        email = get_active_user()
        data = _load(email)
        subject = str(subject or "").strip()
        if not subject:
            return False
        item = data["subjects"].setdefault(subject, {
            "confidence": 50,
            "attempts": 0,
            "correct": 0,
            "incorrect": 0,
            "last_studied": None,
            "study_count": 0,
        })
        item["attempts"] = _safe_count(item.get("attempts")) + 1
        item["study_count"] = _safe_count(item.get("study_count")) + 1
        target = _safe_confidence(confidence)
        previous = _safe_confidence(item.get("confidence", 50))
        rate = 0.35 if item["attempts"] <= 3 else 0.20
        item["confidence"] = round(previous + (target - previous) * rate, 1)
        item["last_studied"] = datetime.now().isoformat()
        if correct is True:
            item["correct"] = _safe_count(item.get("correct")) + 1
        elif correct is False:
            item["incorrect"] = _safe_count(item.get("incorrect")) + 1
        _save(email, data)
        return True

    def update_concept(self, subject, concept, confidence, difficulty=None):
        email = get_active_user()
        data = _load(email)
        subject = str(subject or "").strip()
        concept = str(concept or "").strip()
        if not subject or not concept:
            return False
        key = f"{subject}::{concept}"
        now = datetime.now().isoformat()
        item = data["concepts"].get(key)
        target = _safe_confidence(confidence)
        if not isinstance(item, dict):
            data["concepts"][key] = {
                "subject": subject,
                "concept": concept,
                "confidence": target,
                "attempts": 1,
                "difficulty": str(difficulty or "") or None,
                "first_seen": now,
                "last_seen": now,
            }
        else:
            attempts = _safe_count(item.get("attempts")) + 1
            previous = _safe_confidence(item.get("confidence", 50))
            rate = 0.35 if attempts <= 3 else 0.20
            item["confidence"] = round(previous + (target - previous) * rate, 1)
            item["attempts"] = attempts
            item["last_seen"] = now
            if difficulty:
                item["difficulty"] = str(difficulty)
        _save(email, data)
        return True

    def record_mistake(self, subject, concept, description):
        email = get_active_user()
        data = _load(email)
        data["mistakes"].append({
            "subject": str(subject or ""),
            "concept": str(concept or ""),
            "description": str(description or ""),
            "timestamp": datetime.now().isoformat(),
        })
        data["mistakes"] = data["mistakes"][-500:]
        _save(email, data)

    def record_strategy(self, strategy, successful=True, subject=None):
        email = get_active_user()
        data = _load(email)
        key = "successful_strategies" if successful else "failed_strategies"
        data[key].append({
            "strategy": str(strategy or ""),
            "subject": str(subject or "") or None,
            "timestamp": datetime.now().isoformat(),
        })
        data[key] = data[key][-200:]
        _save(email, data)

    def get_subject(self, subject):
        item = _load(get_active_user())["subjects"].get(subject)
        return deepcopy(item) if isinstance(item, dict) else None

    def get_concept(self, subject, concept):
        item = _load(get_active_user())["concepts"].get(f"{subject}::{concept}")
        return deepcopy(item) if isinstance(item, dict) else None

    def get(self):
        return deepcopy(_load(get_active_user()))

    LearningMemory.record_attempt = record_attempt
    LearningMemory.update_concept = update_concept
    LearningMemory.record_mistake = record_mistake
    LearningMemory.record_strategy = record_strategy
    LearningMemory.get_subject = get_subject
    LearningMemory.get_concept = get_concept
    LearningMemory.get = get
    _PATCHED = True
