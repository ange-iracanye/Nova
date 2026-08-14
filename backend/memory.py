import json
import os


class Memory:

    def __init__(self):

        self.file = "data/memory.json"

        if os.path.exists(self.file):
            with open(self.file, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            self.data = {
                "facts": [],
                "profile": {}
            }

    def save(self):

        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(
                self.data,
                f,
                indent=4
            )

    def remember(self, text):

        if text not in self.data["facts"]:
            self.data["facts"].append(text)
            self.save()

    def recall(self):

        return self.data["facts"]

    def set_profile(self, key, value):

        self.data["profile"][key] = value
        self.save()

    def get_profile(self, key):

        return self.data["profile"].get(key)