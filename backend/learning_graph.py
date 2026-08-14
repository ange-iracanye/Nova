import json
from pathlib import Path


class LearningGraph:

    def __init__(self):
        self.path = Path("data/learning/graph.json")

        if not self.path.exists():
            raise FileNotFoundError(
                "Learning graph not found."
            )

        with open(self.path, "r", encoding="utf-8") as file:
            self.graph = json.load(file)

    def save(self):
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(
                self.graph,
                file,
                indent=4,
                ensure_ascii=False
            )

    def add_subject(self, subject):

        if subject not in self.graph["subjects"]:

            self.graph["subjects"][subject] = {
                "mastery": 0,
                "topics": {}
            }

            self.save()

    def add_topic(self, subject, topic):

        self.add_subject(subject)

        if topic not in self.graph["subjects"][subject]["topics"]:

            self.graph["subjects"][subject]["topics"][topic] = {
                "mastery": 0,
                "times_studied": 0,
                "correct_answers": 0,
                "wrong_answers": 0,
                "last_review": ""
            }

            self.save()

    def update_topic(
        self,
        subject,
        topic,
        correct
    ):

        self.add_topic(subject, topic)

        data = self.graph["subjects"][subject]["topics"][topic]

        data["times_studied"] += 1

        if correct:
            data["correct_answers"] += 1
        else:
            data["wrong_answers"] += 1

        total = (
            data["correct_answers"]
            + data["wrong_answers"]
        )

        if total > 0:
            data["mastery"] = round(
                data["correct_answers"] / total * 100,
                1
            )

        self.save()

    def get(self):
        return self.graph