from backend.intent_detector import IntentDetector
from backend.subject_detector import SubjectDetector

class Planner:

    def __init__(self):

        self.intent = IntentDetector()

        self.subject = SubjectDetector()

    def plan(self, message):

        return {

            "intent": self.intent.detect(message),

            "subject": self.subject.detect(message)

        }