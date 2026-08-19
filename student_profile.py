import hashlib
import json
from pathlib import Path

from backend.user_context import get_active_user


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
                    return
            except Exception:
                pass
        self.profile = self._default()
        self.save()

    def save(self):
        file = self._file()
        file.parent.mkdir(parents=True, exist_ok=True)
        temporary = file.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.profile, indent=4, ensure_ascii=False), encoding="utf-8")
        temporary.replace(file)

    def add_question(self, topic=None):
        self._load()
        self.profile["questions_asked"] = int(self.profile.get("questions_asked", 0) or 0) + 1
        if topic:
            topics = self.profile.setdefault("topics_seen", [])
            if topic not in topics:
                topics.append(topic)
        self.save()

    def set_name(self, name):
        self._load()
        if name:
            self.profile["name"] = str(name).strip()
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
                mastery = float(data.get("confidence", 0) or 0)
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
        snapshot["questions"] = int(snapshot.get("questions_asked", 0) or 0)
        snapshot["strengths"] = strengths
        snapshot["weaknesses"] = weaknesses
        return snapshot
