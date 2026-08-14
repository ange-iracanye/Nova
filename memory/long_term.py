from memory.storage import load_json, save_json

PATH = "memory/storage/facts.json"

class LongTermMemory:

    def __init__(self):

        self.data = load_json(PATH)

        if "facts" not in self.data:
            self.data["facts"] = []

    def remember(self, fact):

        self.data["facts"].append(fact)

        save_json(PATH, self.data)

    def search(self, text):

        text = text.lower()

        results = []

        for fact in self.data["facts"]:

            if text in fact.lower():

                results.append(fact)

        return results

    def delete(self, fact):

        if fact in self.data["facts"]:

            self.data["facts"].remove(fact)

            save_json(PATH, self.data)