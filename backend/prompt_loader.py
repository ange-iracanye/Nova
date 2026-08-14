import os

class PromptLoader:

    def load(self, name):

        path = os.path.join(
            "backend",
            "prompts",
            name + ".txt"
        )

        if not os.path.exists(path):
            return ""

        with open(path, "r", encoding="utf-8") as f:
            return f.read()