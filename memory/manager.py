from memory.history import History
from memory.profile import Profile
from memory.long_term import LongTermMemory
from memory.short_term import ShortTermMemory

class MemoryManager:

    def __init__(self):

        self.history = History()

        self.profile = Profile()

        self.long_term = LongTermMemory()

        self.short_term = ShortTermMemory()

    def remember_conversation(self, user, assistant):

        self.history.add(user, assistant)

        self.short_term.add(user, assistant)

    def get_recent_messages(self):

        return self.short_term.last()

    def remember_fact(self, fact):

        self.long_term.remember(fact)

    def search_fact(self, text):

        return self.long_term.search(text)

    def set_profile(self, key, value):

        self.profile.set_value(key, value)

    def get_profile(self, key):

        return self.profile.get_value(key)