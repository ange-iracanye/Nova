class ResponseBuilder:

    def build(self, question, context):

        if context is None:
            return (
                "I couldn't find enough information "
                "to answer that question."
            )

        answer = ""

        answer += "Here's what I found:\n\n"

        answer += context

        answer += "\n\n"

        answer += "Explanation:\n"

        answer += (
            "This information answers your question "
            "based on Nova's current knowledge."
        )

        return answer