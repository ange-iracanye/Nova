class UnderstandingAnalyzer:

    def __init__(self):
        self.history = {}

    def analyze(self, subject, question, answer):

        if subject not in self.history:
            self.history[subject] = {
                "attempts": 0,
                "confidence": 50,
                "mistakes": [],
                "signals": []
            }

        data = self.history[subject]

        data["attempts"] += 1

        question_text = (
            question
            .strip()
            .lower()
        )

        # =====================================
        # UNDERSTANDING SIGNALS
        # =====================================

        confusion_signals = [
            "i don't understand",
            "i do not understand",
            "i don't get it",
            "i do not get it",
            "i'm confused",
            "i am confused",
            "i'm lost",
            "i am lost",
            "too difficult",
            "too hard",
            "this is difficult",
            "this is hard",
            "can you explain simply",
            "explain it simply",
            "explain that again",
            "explain again",
            "i still don't understand",
            "i still do not understand",
            "i still don't get it",
            "i still do not get it",
            "i'm still confused",
            "i am still confused"
        ]

        understanding_signals = [
            "i understand",
            "i do understand",
            "i get it",
            "i get it now",
            "i understand now",
            "that makes sense",
            "this makes sense",
            "now i understand",
            "now i get it",
            "i see",
            "i see now"
        ]

        clarification_signals = [
            "can you explain",
            "can you clarify",
            "what does that mean",
            "what do you mean",
            "why is that",
            "why does that happen",
            "how does that work",
            "can you give an example",
            "give me an example"
        ]

        # =====================================
        # DETECT SIGNALS
        # =====================================

        confusion_detected = any(
            signal in question_text
            for signal in confusion_signals
        )

        understanding_detected = any(
            signal in question_text
            for signal in understanding_signals
        )

        clarification_detected = any(
            signal in question_text
            for signal in clarification_signals
        )

        # =====================================
        # UPDATE CONFIDENCE
        # =====================================

        confidence_change = 0

        if confusion_detected:

            confidence_change = -10

            data["signals"].append(
                "confusion"
            )

        elif understanding_detected:

            confidence_change = 10

            data["signals"].append(
                "understanding"
            )

        elif clarification_detected:

            confidence_change = -3

            data["signals"].append(
                "clarification"
            )

        else:

            data["signals"].append(
                "neutral"
            )

        data["confidence"] += confidence_change

        # =====================================
        # KEEP CONFIDENCE VALID
        # =====================================

        data["confidence"] = max(
            0,
            min(
                100,
                data["confidence"]
            )
        )

        # =====================================
        # LIMIT SIGNAL HISTORY
        # =====================================

        if len(data["signals"]) > 20:

            data["signals"] = (
                data["signals"][-20:]
            )

        return data

    def get(self):
        return self.history


class UnderstandingTracker:

    def __init__(self):
        self.data = {}

    def update(self, subject, difficulty):

        if not subject:
            return

        if subject not in self.data:
            self.data[subject] = {
                "easy": 0,
                "medium": 0,
                "hard": 0
            }

        if difficulty in self.data[subject]:

            self.data[subject][difficulty] += 1

    def get(self):
        return self.data