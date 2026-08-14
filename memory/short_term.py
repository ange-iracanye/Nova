class ShortTermMemory:

    def __init__(self):

        self.messages = []

    def add(self, user, assistant):

        self.messages.append(
            {
                "user": user,
                "assistant": assistant
            }
        )

        if len(self.messages) > 10:

            self.messages.pop(0)

    def last(self):

        return self.messages

    def clear(self):

        self.messages = []