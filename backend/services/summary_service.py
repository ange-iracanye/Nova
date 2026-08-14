class SummaryService:

    def summarize(

        self,

        facts

    ):

        if len(facts)==0:

            return None

        return "\n".join(

            facts[:3]

        )