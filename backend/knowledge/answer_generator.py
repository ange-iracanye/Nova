class AnswerGenerator:

    def build(self, question, facts):

        if not facts:
            return "I couldn't find anything."

        answer = []

        answer.append(f"### {question}\n")

        for fact in facts:

            answer.append(f"- {fact}")

        return "\n".join(answer)