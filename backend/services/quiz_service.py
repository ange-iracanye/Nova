import random


class QuizService:

    def make(

        self,

        facts

    ):

        if len(facts)==0:

            return None

        fact=random.choice(facts)

        return (

            "Question:\n"

            +fact+

            "\n\nExplain it in your own words."

        )