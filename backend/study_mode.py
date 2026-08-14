class StudyMode:

    def explain(self, answer):

        return answer

    def summarize(self, answer):

        sentences = answer.split(".")

        return ".".join(sentences[:2])

    def make_quiz(self, topic):

        return (

            f"What is the definition of {topic}?"

        )