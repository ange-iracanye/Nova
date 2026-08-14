class AnswerBuilder:

    def build(self, question, facts):

        if not facts:

            return "I couldn't find enough information."

        answer = facts[0]

        if len(facts) > 1:

            answer += "\n\nRelated information:\n"

            for fact in facts[1:]:

                answer += f"• {fact}\n"

        return answer