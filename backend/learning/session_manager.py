class SessionManager:

    def __init__(self):

        self.session = {
            "subject": None,
            "topic": None,
            "mode": None,
            "waiting_answer": False,
            "last_question": None,
            "score": 0,
            "questions": 0
        }

    def start(self, subject, topic, mode):

        self.session["subject"] = subject
        self.session["topic"] = topic
        self.session["mode"] = mode

    def ask(self, question):

        self.session["waiting_answer"] = True
        self.session["last_question"] = question
        self.session["questions"] += 1

    def finish_question(self):

        self.session["waiting_answer"] = False

    def add_score(self, points):

        self.session["score"] += points

    def waiting(self):

        return self.session["waiting_answer"]

    def get(self):

        return self.session