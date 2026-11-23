import hashlib
import json
import math
from copy import deepcopy
from pathlib import Path

from backend.user_context import get_active_user


def _safe_count(value):
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError, OverflowError):
        return 0


class StudentProfile:
    """User-isolated student profile used by the tutor and dashboard."""

    def __init__(self, user_email=None):
        self.base_path = Path("data/memory/profiles")
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.user_email = str(user_email).strip().lower() if user_email else None
        self._load()

    def _active_email(self):
        return self.user_email or get_active_user()

    def _file(self):
        email = self._active_email()
        if not email:
            return self.base_path / "default.json"
        uid = hashlib.sha256(email.encode("utf-8")).hexdigest()
        return self.base_path / f"{uid}.json"

    def _default(self):
        return {
            "name": "Student",
            "level": "beginner",
            "strengths": [],
            "weaknesses": [],
            "topics_seen": [],
            "questions_asked": 0,
        }

    def _load(self):
        file = self._file()
        if file.exists():
            try:
                value = json.loads(file.read_text(encoding="utf-8"))
                if isinstance(value, dict):
                    self.profile = value
                    self._normalize()
                    return
            except Exception:
                pass
        self.profile = self._default()
        self.save()

    def _normalize(self):
        defaults = self._default()
        changed = False
        for key in ("name", "level"):
            value = self.profile.get(key)
            normalized = str(value).strip() if value is not None else ""
            if not normalized:
                normalized = defaults[key]
            if self.profile.get(key) != normalized:
                self.profile[key] = normalized
                changed = True
        for key in ("strengths", "weaknesses", "topics_seen"):
            raw = self.profile.get(key)
            values = raw if isinstance(raw, list) else []
            normalized = []
            seen = set()
            for item in values:
                if not isinstance(item, str):
                    continue
                item = item.strip()
                marker = item.casefold()
                if item and marker not in seen:
                    normalized.append(item)
                    seen.add(marker)
            if raw != normalized:
                self.profile[key] = normalized
                changed = True
        count = _safe_count(self.profile.get("questions_asked"))
        if self.profile.get("questions_asked") != count:
            self.profile["questions_asked"] = count
            changed = True
        if changed:
            self.save()

    def save(self):
        file = self._file()
        file.parent.mkdir(parents=True, exist_ok=True)
        temporary = file.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.profile, indent=4, ensure_ascii=False), encoding="utf-8")
        temporary.replace(file)

    def add_question(self, topic=None):
        self._load()
        self.profile["questions_asked"] = _safe_count(self.profile.get("questions_asked")) + 1
        normalized_topic = str(topic or "").strip()
        if normalized_topic:
            topics = self.profile.get("topics_seen")
            if not isinstance(topics, list):
                topics = []
                self.profile["topics_seen"] = topics
            if normalized_topic.casefold() not in {item.casefold() for item in topics if isinstance(item, str)}:
                topics.append(normalized_topic)
        self.save()

    def set_name(self, name):
        self._load()
        normalized = str(name or "").strip()
        if normalized:
            self.profile["name"] = normalized
            self.save()

    def _learning_snapshot(self):
        try:
            from backend.learning.progress_tracker import ProgressTracker
            progress = ProgressTracker(self._active_email()).get()
        except Exception:
            return [], []

        strengths = []
        weaknesses = []
        for subject, topics in progress.items():
            if not isinstance(topics, dict):
                continue
            for topic, data in topics.items():
                if not isinstance(data, dict):
                    continue
                try:
                    mastery = float(data.get("confidence", 0) or 0)
                except (TypeError, ValueError, OverflowError):
                    continue
                if not math.isfinite(mastery):
                    continue
                mastery = max(0.0, min(100.0, mastery))
                label = f"{subject} / {topic}"
                if mastery >= 75:
                    strengths.append((mastery, label))
                elif mastery < 50:
                    weaknesses.append((mastery, label))

        strengths.sort(reverse=True)
        weaknesses.sort(key=lambda item: item[0])
        return [label for _, label in strengths[:10]], [label for _, label in weaknesses[:10]]

    def get(self):
        self._load()
        strengths, weaknesses = self._learning_snapshot()
        snapshot = dict(self.profile)
        snapshot["questions"] = _safe_count(snapshot.get("questions_asked"))
        snapshot["strengths"] = strengths
        snapshot["weaknesses"] = weaknesses
        return deepcopy(snapshot)
