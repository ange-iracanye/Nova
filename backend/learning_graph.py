import hashlib
import json
from pathlib import Path

from backend.user_context import get_active_user


class LearningGraph:
    """User-isolated learning graph with progress-backed compatibility.

    The old graph was a single global JSON file. That made one student's
    learning state visible to every other student and is the main reason the
    dashboard could report bizarre values such as 100% Mathematics for a new
    account. V3 stores a graph per user and can synthesize it from the already
    user-scoped ProgressTracker data.
    """

    def __init__(self, user_email=None):
        self.base_path = Path("data/learning/users")
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.user_email = (
            str(user_email).strip().lower()
            if user_email
            else None
        )

        # Keep a legacy fallback for code that explicitly uses LearningGraph
        # outside a user request. Dashboard/chat requests use active user data.
        self.legacy_path = Path("data/learning/graph.json")

    def _active_email(self):
        return self.user_email or get_active_user()

    def _user_path(self):
        email = self._active_email()
        if not email:
            return self.legacy_path
        uid = hashlib.sha256(email.encode("utf-8")).hexdigest()
        return self.base_path / f"{uid}.json"

    def _default(self):
        return {"version": 3, "subjects": {}}

    def _load(self):
        path = self._user_path()
        if not path.exists():
            return self._synthesize_from_progress()
        try:
            graph = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(graph, dict) and isinstance(graph.get("subjects"), dict):
                return graph
        except Exception:
            pass
        return self._synthesize_from_progress()

    def _synthesize_from_progress(self):
        graph = self._default()
        email = self._active_email()
        if not email:
            return graph

        # ProgressTracker is already user-isolated and therefore is the safe
        # source of truth for dashboard learning state.
        try:
            from backend.learning.progress_tracker import ProgressTracker
            progress = ProgressTracker(email).get()
        except Exception:
            progress = {}

        for subject, topics in (progress or {}).items():
            if not isinstance(topics, dict):
                continue
            subject_node = graph["subjects"].setdefault(
                subject,
                {"mastery": 0.0, "topics": {}},
            )
            weighted_sum = 0.0
            weight_total = 0.0
            for topic, data in topics.items():
                if not isinstance(data, dict):
                    continue
                attempts = max(0, int(data.get("attempts", 0) or 0))
                confidence = max(0.0, min(100.0, float(data.get("confidence", 0) or 0)))
                last_seen = str(data.get("last_seen") or "")
                subject_node["topics"][topic] = {
                    "mastery": round(confidence, 1),
                    "times_studied": attempts,
                    "correct_answers": 0,
                    "wrong_answers": 0,
                    "last_review": last_seen,
                }
                weight = max(1, attempts)
                weighted_sum += confidence * weight
                weight_total += weight
            if weight_total:
                subject_node["mastery"] = round(weighted_sum / weight_total, 1)

        return graph

    def save(self):
        path = self._user_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(self.graph, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )
        temporary.replace(path)

    def _refresh(self):
        self.graph = self._load()
        return self.graph

    def add_subject(self, subject):
        self._refresh()
        subject = str(subject or "").strip()
        if not subject:
            return
        self.graph["subjects"].setdefault(
            subject,
            {"mastery": 0.0, "topics": {}},
        )
        self.save()

    def add_topic(self, subject, topic):
        self._refresh()
        subject = str(subject or "").strip()
        topic = str(topic or "").strip()
        if not subject or not topic:
            return
        self.graph["subjects"].setdefault(
            subject,
            {"mastery": 0.0, "topics": {}},
        )
        self.graph["subjects"][subject]["topics"].setdefault(
            topic,
            {
                "mastery": 0.0,
                "times_studied": 0,
                "correct_answers": 0,
                "wrong_answers": 0,
                "last_review": "",
            },
        )
        self.save()

    def update_topic(self, subject, topic, correct):
        self._refresh()
        self.add_topic(subject, topic)
        self._refresh()
        data = self.graph["subjects"][subject]["topics"][topic]
        data["times_studied"] = int(data.get("times_studied", 0)) + 1
        if correct:
            data["correct_answers"] = int(data.get("correct_answers", 0)) + 1
        else:
            data["wrong_answers"] = int(data.get("wrong_answers", 0)) + 1
        total = data["correct_answers"] + data["wrong_answers"]
        if total:
            data["mastery"] = round(data["correct_answers"] / total * 100, 1)
        self.save()

    def get(self):
        self.graph = self._load()
        return self.graph
