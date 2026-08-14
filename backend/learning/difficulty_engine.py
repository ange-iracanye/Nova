class DifficultyEngine:


    def decide(self, confidence):

        if confidence < 40:

            return {
                "level": "beginner",
                "instruction":
                "Explain with very simple words. Use analogies and basic examples."
            }


        elif confidence < 70:

            return {
                "level": "intermediate",
                "instruction":
                "Explain clearly. Add examples and connect ideas."
            }


        elif confidence < 90:

            return {
                "level": "advanced",
                "instruction":
                "Explain deeper. Add technical details and ask a small challenge question."
            }


        else:

            return {
                "level": "mastery",
                "instruction":
                "Challenge the student with difficult questions and advanced concepts."
            }