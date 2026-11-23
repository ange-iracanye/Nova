import re


class AnswerEvaluator:
    """A transparent keyword baseline, not a substitute for semantic grading."""

    KEYWORDS = {
        "physics": (
            "gravity", "force", "mass", "energy", "motion",
        ),
        "biology": (
            "cell", "plant", "photosynthesis", "dna", "organism",
        ),
        "math": (
            "equation", "number", "solve", "variable", "formula",
        ),
    }
    TOPIC_ALIASES = {
        "mathematics": "math",
        "mathematical": "math",
        "physique": "physics",
        "biologie": "biology",
    }

    def evaluate(self, expected_topic, answer):
        if expected_topic is None:
            return 50
        topic = str(expected_topic).strip().casefold()
        topic = self.TOPIC_ALIASES.get(topic, topic)
        keywords = self.KEYWORDS.get(topic)
        if not keywords:
            return 0
        text = str(answer or "").casefold()
        score = 0
        for word in keywords:
            pattern = rf"(?<!\w){re.escape(word)}(?!\w)"
            if re.search(pattern, text, flags=re.UNICODE):
                score += 20
        return min(score, 100)
