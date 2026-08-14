import json
import os


class Memory:

    def __init__(self):

        self.file = "memory.json"

        if os.path.exists(self.file):

            with open(self.file, "r", encoding="utf8") as f:

                self.data = json.load(f)

        else:

            self.data = []

    def remember(

        self,

        user,

        assistant

    ):

        self.data.append({

            "user": user,

            "assistant": assistant

        })

        self.save()

    def recent(

        self,

        amount=5

    ):

        return self.data[-amount:]

    def save(self):

        with open(

            self.file,

            "w",

            encoding="utf8"

        ) as f:

            json.dump(

                self.data,

                f,

                indent=4
            )