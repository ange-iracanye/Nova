class Tutor:

    def teach(self, context):

        knowledge = context["knowledge"]

        if knowledge is None:

            return (
                "I couldn't find enough information."
            )

        answer = ""

        answer += f"Question:\n{context['question']}\n\n"

        answer += "Explanation:\n"

        answer += knowledge

        if context["example"]:

            answer += "\n\nExample:\n"

            if "gravity" in knowledge.lower():

                answer += (
                    "If you throw a ball into the air, "
                    "it always comes back because gravity "
                    "pulls it toward Earth."
                )

        return answer