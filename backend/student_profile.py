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

            # =====================================
            # ENSURE REQUIRED FIELDS EXIST
            # =====================================

            self.profile.setdefault(
                "name",
                "Student"
            )

            self.profile.setdefault(
                "level",
                "beginner"
            )

            self.profile.setdefault(
                "strengths",
                []
            )

            self.profile.setdefault(
                "weaknesses",
                []
            )

            self.profile.setdefault(
                "topics_seen",
                []
            )

            self.profile.setdefault(
                "questions_asked",
                0
            )

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

            self.profile["topics_seen"].append(
                topic
            )

        self.save()

    def get(self):

        return self.profile
