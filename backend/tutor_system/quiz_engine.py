class QuizEngine:


    def create_quiz(self, subject):

        if not subject:
            subject = "physics"


        return f"""
Physics Quiz

Question 1:
Explain one important concept about {subject}.


Question 2:
Give a real-life example related to {subject}.


Question 3:
Why is {subject} important?

Answer the questions and Nova will correct your answers.
"""