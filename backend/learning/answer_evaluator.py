class AnswerEvaluator:

    def evaluate(
        self,
        expected_topic,
        answer
    ):

        text = answer.lower()

        if expected_topic is None:
            return 50

        keywords = {

            "physics":[
                "gravity",
                "force",
                "mass",
                "energy",
                "motion"
            ],

            "biology":[
                "cell",
                "plant",
                "photosynthesis",
                "dna",
                "organism"
            ],

            "math":[
                "equation",
                "number",
                "solve",
                "variable",
                "formula"
            ]

        }

        score = 0

        for word in keywords.get(expected_topic, []):

            if word in text:
                score += 20

        return min(score,100)