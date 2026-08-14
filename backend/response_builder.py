class ResponseBuilder:

    def build(self, question, facts):

        if not facts:
            return "I couldn't find anything."

        answer = ""

        if len(facts) == 1:
            answer += facts[0]

        else:
            answer += facts[0]

            related = facts[1:]

            if related:
                answer += "\n\nRelated information:\n"

                for fact in related:
                    answer += f"- {fact}\n"

        return answer.strip()