import re
import random


class QuizSkill:

    def run(self, topic):

        topic = topic.lower()

        topic = re.sub(
            r"(give me|create|make|a|an|the|quiz|about)",
            "",
            topic
        )

        topic = topic.strip()

        questions = [

            f"What is {topic}?",

            f"Why is {topic} important?",

            f"Which statement about {topic} is correct?"

        ]

        return random.choice(questions)