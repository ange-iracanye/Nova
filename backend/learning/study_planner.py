from __future__ import annotations

from typing import Any


class StudyPlanner:
    """Create small, explainable study recommendations from a student profile."""

    @staticmethod
    def _topics(value: Any) -> list[str]:
        if not isinstance(value, (list, tuple)):
            return []
        result: list[str] = []
        seen: set[str] = set()
        for item in value:
            if len(result) >= 100:
                break
            if not isinstance(item, str):
                continue
            topic = " ".join(item.split())[:160]
            topic = "".join(
                char for char in topic
                if char.isprintable()
            ).strip()
            key = topic.casefold()
            if topic and key not in seen:
                result.append(topic)
                seen.add(key)
        return result

    def build_plan(self, profile, limit=5):
        """Prioritize weak topics, then due reviews, then new exploration."""
        profile = profile if isinstance(profile, dict) else {}
        try:
            limit = max(1, min(20, int(limit)))
        except (TypeError, ValueError, OverflowError):
            limit = 5

        weaknesses = self._topics(profile.get("weaknesses", []))
        due = self._topics(profile.get("due_topics", []))
        new_topics = self._topics(profile.get("new_topics", []))
        strengths = self._topics(profile.get("strengths", []))
        plan: list[dict[str, str]] = []
        seen: set[str] = set()

        def add(topics, action, reason):
            for topic in topics:
                key = topic.casefold()
                if key in seen or len(plan) >= limit:
                    continue
                plan.append({"topic": topic, "action": action, "reason": reason})
                seen.add(key)

        add(weaknesses, "practice", "Needs more practice")
        add(due, "review", "Ready for a spaced review")
        add(new_topics, "learn", "New topic to explore")
        add(strengths, "reinforce", "Maintain a strong topic")

        if not plan:
            plan.append({
                "topic": "Choose a new topic",
                "action": "explore",
                "reason": "No learning history is available yet",
            })
        return plan[:limit]

    def recommend(self, profile):
        profile = profile if isinstance(profile, dict) else {}
        weaknesses = self._topics(profile.get("weaknesses", []))
        due = self._topics(profile.get("due_topics", []))
        new_topics = self._topics(profile.get("new_topics", []))
        strengths = self._topics(profile.get("strengths", []))
        if weaknesses:
            return "Today's recommendation: practice " + weaknesses[0]
        if due:
            return "Today's recommendation: review " + due[0]
        if new_topics:
            return "Today's recommendation: explore " + new_topics[0]
        if strengths:
            return "Today's recommendation: reinforce " + strengths[0]
        return "Today's recommendation: learn a new topic."
