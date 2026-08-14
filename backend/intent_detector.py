class IntentDetector:

    def detect(self, message):

        text = message.lower()

        if any(x in text for x in [
            "hello",
            "hi",
            "hey"
        ]):
            return "greeting"

        if "thanks" in text:
            return "thanks"

        if "bye" in text:
            return "goodbye"

        if any(x in text for x in [
            "quiz",
            "test",
            "question me",
            "multiple choice"
        ]):
            return "quiz"

        if any(x in text for x in [
            "summarize",
            "summary"
        ]):
            return "summary"

        if any(x in text for x in [
            "explain",
            "teach",
            "what is",
            "define"
        ]):
            return "explanation"

        if any(x in text for x in [
            "translate"
        ]):
            return "translation"

        return "conversation"