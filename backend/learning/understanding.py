class UnderstandingTracker:

    def __init__(self):
        self.data = {}


    def update(self, subject, difficulty):

        if not subject:
            return

        if subject not in self.data:
            self.data[subject] = {
                "easy": 0,
                "medium": 0,
                "hard": 0
            }

        if difficulty in self.data[subject]:
            self.data[subject][difficulty] += 1


    def get(self):
        return self.data



class UnderstandingAnalyzer:

    def __init__(self):
        self.history = {}


    def analyze(self, subject, question, answer):

        if subject not in self.history:
            self.history[subject] = {
                "attempts": 0,
                "confidence": 50,
                "mistakes": []
            }


        data = self.history[subject]

        data["attempts"] += 1


        if len(answer) < 50:
            data["confidence"] -= 5

        else:
            data["confidence"] += 5


        if data["confidence"] > 100:
            data["confidence"] = 100

        if data["confidence"] < 0:
            data["confidence"] = 0


        return data



    def get(self):
        return self.history