class NovaBrain:

    def __init__(self):
        print("Loading Nova Brain...")


    def think(
        self,
        student,
        subject,
        topic,
        understanding
    ):

        confidence = 50

        if understanding:

            if subject in understanding:

                confidence = understanding[subject].get(
                    "confidence",
                    50
                )


        strategy = {
            "level": student.get(
                "level",
                "beginner"
            ),

            "subject": subject,

            "topic": topic,

            "confidence": confidence,

            "approach": []
        }


        if confidence < 40:

            strategy["approach"].append(
                "Explain from the absolute basics"
            )

            strategy["approach"].append(
                "Use very simple examples"
            )


        elif confidence < 70:

            strategy["approach"].append(
                "Explain clearly with examples"
            )


        else:

            strategy["approach"].append(
                "Use deeper explanations and challenges"
            )


        if subject == "physics":

            strategy["approach"].append(
                "Use real world physics examples"
            )


        elif subject == "biology":

            strategy["approach"].append(
                "Explain biological processes step by step"
            )


        elif subject == "math":

            strategy["approach"].append(
                "Show the solving method"
            )


        return strategy