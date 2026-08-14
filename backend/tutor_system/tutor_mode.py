class TutorModeDetector:


    def detect(self, message):

        text = message.lower()


        if any(word in text for word in [
            "quiz",
            "test",
            "question me",
            "practice"
        ]):
            return "quiz"


        if any(word in text for word in [
            "summarize",
            "summary",
            "résumé"
        ]):
            return "summary"


        if any(word in text for word in [
            "correct",
            "check my answer",
            "is this right"
        ]):
            return "correction"


        if any(word in text for word in [
            "explain",
            "teach",
            "understand",
            "don't understand"
        ]):
            return "explanation"


        return "conversation"