class StudyPlanner:

    def recommend(self, profile):

        weaknesses = profile.get(
            "weaknesses",
            []
        )

        if weaknesses:

            return (
                "Today's recommendation: review "
                + weaknesses[0]
            )

        return (
            "Today's recommendation: learn a new topic."
        )