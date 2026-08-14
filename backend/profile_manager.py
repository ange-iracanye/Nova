from backend.student_profile import StudentProfile


class ProfileManager:

    def __init__(self):
        self.profile = StudentProfile()

    def add_question(self):
        self.profile.add_question()

    def get(self):
        return self.profile.get()