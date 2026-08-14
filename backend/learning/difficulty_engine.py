class DifficultyEngine:
    """
    Determines the appropriate teaching difficulty for the student.

    The engine uses the student's confidence score to choose a
    teaching level.

    There are two difficulty representations:

    1. "level"
       The detailed teaching level used by Nova's teaching system.

       Possible values:
       - beginner
       - intermediate
       - advanced
       - mastery

    2. "tracking_level"
       A simplified difficulty category used by the learning
       tracker.

       Possible values:
       - easy
       - medium
       - hard

    Keeping these two values separate allows Nova to have a
    detailed teaching system while keeping the learning statistics
    simple and consistent.
    """

    # =====================================
    # CONFIDENCE THRESHOLDS
    # =====================================

    BEGINNER_THRESHOLD = 40
    INTERMEDIATE_THRESHOLD = 70
    ADVANCED_THRESHOLD = 90

    # =====================================
    # CONFIDENCE LIMITS
    # =====================================

    MIN_CONFIDENCE = 0
    MAX_CONFIDENCE = 100

    def decide(self, confidence):

        # =====================================
        # NORMALIZE CONFIDENCE
        # =====================================

        try:

            confidence = float(
                confidence
            )

        except (
            TypeError,
            ValueError
        ):

            confidence = 50

        confidence = max(
            self.MIN_CONFIDENCE,
            min(
                self.MAX_CONFIDENCE,
                confidence
            )
        )

        # =====================================
        # BEGINNER
        # =====================================

        if confidence < self.BEGINNER_THRESHOLD:

            return {

                "level":
                    "beginner",

                "tracking_level":
                    "easy",

                "stage":
                    "foundation",

                "confidence":
                    confidence,

                "instruction":
                    (
                        "Explain with very simple words. "
                        "Break the concept into small steps. "
                        "Use basic examples and clear analogies. "
                        "Avoid unnecessary technical vocabulary. "
                        "Focus on building the student's basic "
                        "understanding before introducing more "
                        "complex ideas."
                    )
            }

        # =====================================
        # INTERMEDIATE
        # =====================================

        elif confidence < self.INTERMEDIATE_THRESHOLD:

            return {

                "level":
                    "intermediate",

                "tracking_level":
                    "medium",

                "stage":
                    "developing",

                "confidence":
                    confidence,

                "instruction":
                    (
                        "Explain the concept clearly and "
                        "progressively. Use useful examples "
                        "and connect the new idea to concepts "
                        "the student may already know. "
                        "Introduce important technical vocabulary "
                        "when it helps understanding. "
                        "Avoid making the explanation unnecessarily "
                        "complex."
                    )
            }

        # =====================================
        # ADVANCED
        # =====================================

        elif confidence < self.ADVANCED_THRESHOLD:

            return {

                "level":
                    "advanced",

                "tracking_level":
                    "hard",

                "stage":
                    "strong",

                "confidence":
                    confidence,

                "instruction":
                    (
                        "Explain the concept in greater depth. "
                        "Include relevant technical details, "
                        "connections between ideas, and more "
                        "challenging examples. "
                        "Avoid over-explaining basic concepts "
                        "the student is likely to understand. "
                        "Where appropriate, include a small "
                        "challenge question to test deeper "
                        "understanding."
                    )
            }

        # =====================================
        # MASTERY
        # =====================================

        else:

            return {

                "level":
                    "mastery",

                "tracking_level":
                    "hard",

                "stage":
                    "mastery",

                "confidence":
                    confidence,

                "instruction":
                    (
                        "Treat the student as highly confident "
                        "with the subject. Focus on advanced "
                        "concepts, deeper reasoning, difficult "
                        "applications, edge cases, and connections "
                        "between related ideas. "
                        "Avoid basic explanations unless they are "
                        "necessary. Challenge the student's "
                        "understanding with difficult questions "
                        "or problems when appropriate."
                    )
            }
