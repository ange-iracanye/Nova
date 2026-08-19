import json
import hashlib
from pathlib import Path
from datetime import datetime

from backend.user_context import set_active_user


_SUBJECT_ALIASES = {
    "math": "Mathematics",
    "mathematics": "Mathematics",
    "algebra": "Mathematics",
    "calculus": "Mathematics",
    "geometry": "Mathematics",
    "statistics": "Mathematics",
    "stats": "Mathematics",
    "physics": "Physics",
    "biology": "Biology",
    "chemistry": "Chemistry",
    "geography": "Geography",
    "history": "History",
    "tech": "Technology",
    "technology": "Technology",
    "computer science": "Technology",
    "programming": "Technology",
    "coding": "Technology",
    "software development": "Technology",
    "software engineering": "Technology",
    "python": "Technology",
    "javascript": "Technology",
    "typescript": "Technology",
    "java": "Technology",
    "c++": "Technology",
    "c#": "Technology",
    "rust": "Technology",
    "golang": "Technology",
    "cybersecurity": "Technology",
    "cyber security": "Technology",
    "networking": "Technology",
    "web development": "Technology",
    "machine learning": "Technology",
    "artificial intelligence": "Technology",
}


def canonical_subject(subject):
    value = " ".join(str(subject or "").strip().split())
    if not value:
        return ""
    return _SUBJECT_ALIASES.get(value.casefold(), value)


class ProgressTracker:
    """Persistent, user-isolated learning progress tracker."""

    def __init__(self, user_email=None):
        self.base_path = Path("data/memory/progress")
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.user_email = user_email.strip().lower() if user_email else None
        if self.user_email:
            set_active_user(self.user_email)
        self.file = self._get_file()
        if self.file.exists():
            try:
                self.progress = json.loads(self.file.read_text(encoding="utf-8"))
            except Exception:
                self.progress = {}
        else:
            self.progress = {}
            self._save()

    def _get_file(self):
        if not self.user_email:
            return self.base_path / "default.json"
        user_id = hashlib.sha256(self.user_email.encode("utf-8")).hexdigest()
        return self.base_path / f"{user_id}.json"

    def _save(self):
        temporary = self.file.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.progress, indent=4, ensure_ascii=False), encoding="utf-8")
        temporary.replace(self.file)

    def _merge_subject_aliases(self):
        """Merge legacy aliases without deleting any learning evidence."""
        merged = {}
        changed = False
        for subject, topics in self.progress.items():
            target = canonical_subject(subject)
            if target != subject:
                changed = True
            bucket = merged.setdefault(target, {})
            if not isinstance(topics, dict):
                continue
            for topic, data in topics.items():
                if topic not in bucket:
                    bucket[topic] = data
                    continue
                old = bucket[topic]
                if not isinstance(old, dict) or not isinstance(data, dict):
                    continue
                old_attempts = int(old.get("attempts", 0) or 0)
                new_attempts = int(data.get("attempts", 0) or 0)
                total = old_attempts + new_attempts
                if total:
                    old_conf = float(old.get("confidence", 50) or 50)
                    new_conf = float(data.get("confidence", 50) or 50)
                    old["confidence"] = round((old_conf * old_attempts + new_conf * new_attempts) / total, 1)
                old["attempts"] = total
                old["last_seen"] = max(str(old.get("last_seen") or ""), str(data.get("last_seen") or ""))
        if changed:
            self.progress = merged
            self._save()

    def update(self, subject, topic, confidence):
        subject = canonical_subject(subject)
        topic = " ".join(str(topic or "").strip().split())
        if not subject or not topic:
            return
        self._merge_subject_aliases()
        try:
            confidence = max(0.0, min(100.0, float(confidence)))
        except (TypeError, ValueError):
            confidence = 50.0
        if subject not in self.progress:
            self.progress[subject] = {}
        if topic not in self.progress[subject]:
            self.progress[subject][topic] = {
                "attempts": 0,
                "confidence": 50,
                "mastered": False,
                "first_seen": datetime.now().isoformat(),
                "last_seen": None,
            }
        data = self.progress[subject][topic]
        data["attempts"] = int(data.get("attempts", 0) or 0) + 1
        previous = float(data.get("confidence", 50) or 50)
        attempts = int(data["attempts"])
        learning_rate = 0.35 if attempts <= 3 else 0.20
        data["confidence"] = round(previous + (confidence - previous) * learning_rate, 1)
        data["mastered"] = data["confidence"] >= 85 and attempts >= 5
        data["last_seen"] = datetime.now().isoformat()
        self._save()

    def get(self):
        self._merge_subject_aliases()
        return self.progress
