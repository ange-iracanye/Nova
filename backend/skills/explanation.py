class ExplanationSkill:

    def run(self, passages):

        if not passages:
            return "I couldn't find enough information."

        if isinstance(passages, str):
            return passages

        answer = passages[0]

        if len(passages) > 1:

            answer += "\n\nRelated information:\n"

            for p in passages[1:]:

                answer += f"\n• {p}"

        return answer