import hashlib
import json
import math
from datetime import datetime
from copy import deepcopy
from pathlib import Path

from backend.user_context import get_active_user


def _safe_count(value):
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError, OverflowError):
        return 0


def _safe_confidence(value):
    try:
        confidence = float(value)
    except (TypeError, ValueError, OverflowError):
        return 0.0
    if not math.isfinite(confidence):
        return 0.0
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


def _safe_bool(value):
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


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

    def _normalize_graph(self, graph):
        if not isinstance(graph, dict) or not isinstance(graph.get("subjects"), dict):
            return self._default()
        normalized = self._default()
        for subject, node in graph["subjects"].items():
            if not isinstance(subject, str) or not subject.strip() or not isinstance(node, dict):
                continue
            topics = node.get("topics")
            topics = topics if isinstance(topics, dict) else {}
            normalized_topics = {}
            for topic, data in topics.items():
                if not isinstance(topic, str) or not topic.strip() or not isinstance(data, dict):
                    continue
                correct = _safe_count(data.get("correct_answers"))
                wrong = _safe_count(data.get("wrong_answers"))
                normalized_topics[topic.strip()] = {
                    "mastery": round(_safe_confidence(data.get("mastery", 0)), 1),
                    "times_studied": max(_safe_count(data.get("times_studied")), correct + wrong),
                    "correct_answers": correct,
                    "wrong_answers": wrong,
                    "last_review": str(data.get("last_review") or ""),
                }
            normalized["subjects"][subject.strip()] = {
                "mastery": round(_safe_confidence(node.get("mastery", 0)), 1),
                "topics": normalized_topics,
            }
        normalized["version"] = 3
        return normalized

    def _load(self):
        path = self._user_path()
        if not path.exists():
            return self._synthesize_from_progress()
        try:
            graph = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError, UnicodeError):
            return self._synthesize_from_progress()
        if not isinstance(graph, dict) or not isinstance(graph.get("subjects"), dict):
            return self._synthesize_from_progress()
        return self._normalize_graph(graph)

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
                attempts = _safe_count(data.get("attempts", 0))
                confidence = _safe_confidence(data.get("confidence", 0))
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
            json.dumps(_json_safe(self.graph), indent=4, ensure_ascii=False, allow_nan=False),
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
        node = self.graph["subjects"].get(subject)
        if not isinstance(node, dict):
            self.graph["subjects"][subject] = {"mastery": 0.0, "topics": {}}
        self.save()

    def add_topic(self, subject, topic):
        self._refresh()
        subject = str(subject or "").strip()
        topic = str(topic or "").strip()
        if not subject or not topic:
            return
        node = self.graph["subjects"].get(subject)
        if not isinstance(node, dict):
            node = {"mastery": 0.0, "topics": {}}
            self.graph["subjects"][subject] = node
        if not isinstance(node.get("topics"), dict):
            node["topics"] = {}
        node["topics"].setdefault(
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
        subject = str(subject or "").strip()
        topic = str(topic or "").strip()
        if not subject or not topic:
            return False
        self._refresh()
        self.add_topic(subject, topic)
        self._refresh()
        data = self.graph["subjects"][subject]["topics"][topic]
        data["times_studied"] = _safe_count(data.get("times_studied")) + 1
        if _safe_bool(correct):
            data["correct_answers"] = _safe_count(data.get("correct_answers")) + 1
        else:
            data["wrong_answers"] = _safe_count(data.get("wrong_answers")) + 1
        total = data["correct_answers"] + data["wrong_answers"]
        if total:
            data["mastery"] = round(data["correct_answers"] / total * 100, 1)
        data["last_review"] = datetime.now().isoformat()

        subject_node = self.graph["subjects"][subject]
        weighted_mastery = 0.0
        weight_total = 0
        for topic_data in subject_node["topics"].values():
            if not isinstance(topic_data, dict):
                continue
            weight = max(1, _safe_count(topic_data.get("times_studied")))
            weighted_mastery += _safe_confidence(topic_data.get("mastery")) * weight
            weight_total += weight
        subject_node["mastery"] = (
            round(weighted_mastery / weight_total, 1)
            if weight_total else 0.0
        )
        self.save()
        return True

    def get(self):
        self.graph = self._load()
        return deepcopy(self.graph)
