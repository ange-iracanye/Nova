class AdaptiveTutor:


    def choose_level(self, student):

        level = student.get("level", "beginner")


        if level is None:
            level = "beginner"


        level = level.lower()


        if level == "advanced":

            return "advanced"


        if level == "intermediate":

            return "intermediate"


        return "beginner"



    def build_instruction(self, student, subject):

        level = self.choose_level(student)


        if level == "beginner":

            return (
                "Explain simply. "
                "Use easy words. "
                "Give a real life example."
            )


        if level == "advanced":

            return (
                "Explain deeply. "
                "Use technical vocabulary. "
                "Include theory and details."
            )


        return (
            "Explain clearly. "
            "Use moderate detail. "
            "Include examples."
        )