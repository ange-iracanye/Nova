import json
import os


class StudentProfile:

    def __init__(self):

        self.file = "data/student_profile.json"

        if os.path.exists(self.file):

            with open(
                self.file,
                "r",
                encoding="utf-8"
            ) as f:

                self.profile = json.load(f)

        else:

            self.profile = {

                "name": "Student",

                "level": "beginner",

                "strengths": [],

                "weaknesses": [],

                "topics_seen": [],

                "questions_asked": 0

            }

            self.save()

    def save(self):

        os.makedirs(
            "data",
            exist_ok=True
        )

        with open(
            self.file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                self.profile,
                f,
                indent=4
            )

    def add_question(self, topic=None):

        self.profile["questions_asked"] += 1

        if topic:

            if topic not in self.profile["topics_seen"]:

                self.profile["topics_seen"].append(topic)

        self.save()

    def get(self):

        return self.profile