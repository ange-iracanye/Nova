from datetime import datetime
import math


class MemoryConsolidator:
    """Move validated memory records into the legacy student-memory schema."""

    def __init__(self, student_memory):
        self.student_memory = student_memory

    @staticmethod
    def _confidence(value, default=0.8):
        try:
            confidence = float(value)
        except (TypeError, ValueError, OverflowError):
            return default
        if not math.isfinite(confidence):
            return default
        if confidence > 1:
            confidence /= 100
        return max(0.0, min(1.0, confidence))

    @staticmethod
    def _count(value):
        try:
            return max(0, int(value or 0))
        except (TypeError, ValueError, OverflowError):
            return 0

    def consolidate(self, memory, subject=None):
        if not isinstance(memory, dict):
            return False
        memory_type = str(memory.get("type", "episode") or "episode").strip().lower()
        text = memory.get("text")
        if not isinstance(text, str) or not text.strip():
            return False
        text = text.strip()

        if memory_type == "fact":
            self.student_memory.add_fact(
                text,
                subject=subject,
                confidence=self._confidence(memory.get("confidence", 0.8)),
            )
            return True
        if memory_type == "preference":
            self._store_preference(text)
            return True
        if memory_type == "learning":
            self._store_learning(subject, text)
            return True
        if memory_type == "explicit_memory":
            self.student_memory.add_explicit_memory(text, subject=subject)
            return True
        return False

    def _store_preference(self, text):
        memory = self.student_memory.memory
        if not isinstance(memory, dict):
            memory = {}
            self.student_memory.memory = memory
        preferences = memory.get("preferences")
        if not isinstance(preferences, list):
            preferences = []
            memory["preferences"] = preferences
        key = "preference_" + str(len(preferences))
        self.student_memory.set_preference(key, text)

    def _store_learning(self, subject, text):
        subject = str(subject or "general").strip() or "general"
        memory = self.student_memory.memory
        if not isinstance(memory, dict):
            memory = {}
            self.student_memory.memory = memory
        progress = memory.get("progress")
        if not isinstance(progress, dict):
            progress = {}
            memory["progress"] = progress

        data = progress.get(subject)
        if not isinstance(data, dict):
            data = {
                "observations": [],
                "attempts": 0,
                "confidence": 50,
                "last_updated": None,
            }
            progress[subject] = data

        observations = data.get("observations")
        if not isinstance(observations, list):
            observations = []
            data["observations"] = observations
        observations.append(text)
        data["attempts"] = self._count(data.get("attempts")) + 1
        data["confidence"] = self._confidence(data.get("confidence", 0.5), 0.5) * 100
        data["last_updated"] = datetime.now().isoformat()
        data["observations"] = observations[-100:]
        self.student_memory.save()
