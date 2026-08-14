class Confidence:

    def score(self, facts):

        if not facts:

            return 0

        return min(

            len(facts) * 20,

            100

        )