class ConversationManager:

    def __init__(self):
        self.history = []

    def add(self, user, assistant):

        self.history.append({
            "user": user,
            "assistant": assistant
        })

        if len(self.history) > 20:
            self.history.pop(0)

    def last(self):

        if not self.history:
            return None

        return self.history[-1]

    def history_text(self):

        text = ""

        for item in self.history:
            text += f'User: {item["user"]}\n'
            text += f'Nova: {item["assistant"]}\n\n'

        return text