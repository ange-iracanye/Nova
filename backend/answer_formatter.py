class AnswerFormatter:

    def format(self, question, passages):

        if not passages:

            return (
                "I couldn't find enough information."
            )

        answer = passages[0]

        if len(passages) > 1:

            answer += "\n\nRelated information:\n"

            for p in passages[1:]:

                answer += f"\n• {p}"

        return answer