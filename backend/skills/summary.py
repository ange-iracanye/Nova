class SummarySkill:

    def run(self, passages):

        if not passages:
            return "I couldn't find enough information."

        if isinstance(passages, str):
            return passages

        return passages[0]