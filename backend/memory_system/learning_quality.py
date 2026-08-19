"""User-isolated learning-memory compatibility layer."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

from backend.user_context import set_active_user, get_active_user

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


def _load(email):
    file = _path(email)
    file.parent.mkdir(parents=True, exist_ok=True)
    if not file.exists():
        return _default()
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else _default()
    except Exception:
        return _default()


def _save(email, data):
    file = _path(email)
    file.parent.mkdir(parents=True, exist_ok=True)
    temporary = file.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=4, ensure_ascii=False), encoding="utf-8")
    temporary.replace(file)


def install_learning_quality(MemoryManager, LearningMemory):
    global _PATCHED
    if _PATCHED:
        return

    original_remember = MemoryManager.remember

    def remember(self, email, *args, **kwargs):
        set_active_user(email)
        return original_remember(self, email, *args, **kwargs)

    MemoryManager.remember = remember

    def record_attempt(self, subject, confidence, correct=None):
        email = get_active_user()
        data = _load(email)
        if not subject:
            return
        subject = str(subject).strip()
        item = data["subjects"].setdefault(subject, {
            "confidence": 50,
            "attempts": 0,
            "correct": 0,
            "incorrect": 0,
            "last_studied": None,
            "study_count": 0,
        })
        try:
            confidence = max(0.0, min(100.0, float(confidence)))
        except (TypeError, ValueError):
            confidence = 50.0
        item["attempts"] += 1
        previous = float(item.get("confidence", 50) or 50)
        rate = 0.35 if item["attempts"] <= 3 else 0.20
        item["confidence"] = round(previous + (confidence - previous) * rate, 1)
        item["last_studied"] = datetime.now().isoformat()
        item["study_count"] += 1
        if correct is True:
            item["correct"] += 1
        elif correct is False:
            item["incorrect"] += 1
        _save(email, data)

    def update_concept(self, subject, concept, confidence, difficulty=None):
        email = get_active_user()
        data = _load(email)
        if not subject or not concept:
            return
        key = f"{subject}::{concept}"
        now = datetime.now().isoformat()
        item = data["concepts"].get(key)
        if not isinstance(item, dict):
            data["concepts"][key] = {
                "subject": subject,
                "concept": concept,
                "confidence": confidence,
                "attempts": 1,
                "difficulty": difficulty,
                "first_seen": now,
                "last_seen": now,
            }
        else:
            attempts = int(item.get("attempts", 0) or 0) + 1
            previous = float(item.get("confidence", 50) or 50)
            target = float(confidence or 50)
            rate = 0.35 if attempts <= 3 else 0.20
            item["confidence"] = round(previous + (target - previous) * rate, 1)
            item["attempts"] = attempts
            item["last_seen"] = now
            if difficulty:
                item["difficulty"] = difficulty
        _save(email, data)

    def record_mistake(self, subject, concept, description):
        email = get_active_user()
        data = _load(email)
        data["mistakes"].append({
            "subject": subject,
            "concept": concept,
            "description": description,
            "timestamp": datetime.now().isoformat(),
        })
        data["mistakes"] = data["mistakes"][-500:]
        _save(email, data)

    def record_strategy(self, strategy, successful=True, subject=None):
        email = get_active_user()
        data = _load(email)
        key = "successful_strategies" if successful else "failed_strategies"
        data[key].append({
            "strategy": strategy,
            "subject": subject,
            "timestamp": datetime.now().isoformat(),
        })
        data[key] = data[key][-200:]
        _save(email, data)

    def get_subject(self, subject):
        return _load(get_active_user())["subjects"].get(subject)

    def get_concept(self, subject, concept):
        return _load(get_active_user())["concepts"].get(f"{subject}::{concept}")

    def get(self):
        return _load(get_active_user())

    LearningMemory.record_attempt = record_attempt
    LearningMemory.update_concept = update_concept
    LearningMemory.record_mistake = record_mistake
    LearningMemory.record_strategy = record_strategy
    LearningMemory.get_subject = get_subject
    LearningMemory.get_concept = get_concept
    LearningMemory.get = get
    _PATCHED = True
