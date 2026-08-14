from memory.storage import load_json, save_json

PATH = "memory/storage/chat_history.json"

class History:

    def __init__(self):
        self.data = load_json(PATH)

        if "messages" not in self.data:
            self.data["messages"] = []

    def add(self, user, assistant):

        self.data["messages"].append(
            {
                "user": user,
                "assistant": assistant
            }
        )

        save_json(PATH, self.data)

    def last(self, limit=10):

        return self.data["messages"][-limit:]

    def clear(self):

        self.data["messages"] = []

        save_json(PATH, self.data)