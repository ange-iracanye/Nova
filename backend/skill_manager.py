from backend.skills.summary import SummarySkill
from backend.skills.quiz import QuizSkill


class SkillManager:

    def __init__(self):

        self.summary = SummarySkill()

        self.quiz = QuizSkill()

    def execute(self, intent, passages, topic):

        if intent == "quiz":
            return self.quiz.run(topic)

        if intent == "summary":
            return self.summary.run(passages)

        return passages