import json
import hashlib
from pathlib import Path
from datetime import datetime

from backend.user_context import set_active_user


class ProgressTracker:
    """Persistent, user-isolated learning progress tracker."""

    def __init__(self, user_email=None):
        self.base_path = Path("data/memory/progress")
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.user_email = (
            user_email.strip().lower()
            if user_email
            else None
        )

        # This also selects the active user for the legacy LearningGraph
        # adapter used by the dashboard.
        if self.user_email:
            set_active_user(self.user_email)

        self.file = self._get_file()

        if self.file.exists():
            try:
                self.progress = json.loads(
                    self.file.read_text(encoding="utf-8")
                )
            except Exception:
                self.progress = {}
        else:
            self.progress = {}
            self._save()

    def _get_file(self):
        if not self.user_email:
            return self.base_path / "default.json"

        user_id = hashlib.sha256(
            self.user_email.encode("utf-8")
        ).hexdigest()
        return self.base_path / f"{user_id}.json"

    def _save(self):
        temporary = self.file.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                self.progress,
                indent=4,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        temporary.replace(self.file)

    def update(self, subject, topic, confidence):
        if not subject or not topic:
            return

        subject = str(subject).strip()
        topic = str(topic).strip()
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
        data["attempts"] += 1

        # Confidence is evidence, not a binary mastery switch. Repeated
        # observations converge smoothly instead of making one answer 100%.
        previous = float(data.get("confidence", 50) or 50)
        attempts = int(data.get("attempts", 1) or 1)
        learning_rate = 0.35 if attempts <= 3 else 0.20
        data["confidence"] = round(
            previous + (confidence - previous) * learning_rate,
            1,
        )
        data["mastered"] = (
            data["confidence"] >= 85
            and attempts >= 5
        )
        data["last_seen"] = datetime.now().isoformat()

        self._save()

    def get(self):
        return self.progress
