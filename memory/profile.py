from memory.storage import load_json, save_json

PATH = "memory/storage/profile.json"

class Profile:

    def __init__(self):

        self.data = load_json(PATH)

    def set_value(self, key, value):

        self.data[key] = value

        save_json(PATH, self.data)

    def get_value(self, key):

        return self.data.get(key)

    def all(self):

        return self.data