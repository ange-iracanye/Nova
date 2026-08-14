class NovaBrain:
    """
    Nova's student-analysis and learning-strategy engine.

    NovaBrain does NOT generate the final educational answer.

    Its job is to analyze the student's current learning state and
    decide how Nova should approach the next response.

    Responsibilities:

        - Analyze student level
        - Analyze subject confidence
        - Analyze topic confidence
        - Determine learning state
        - Determine teaching approach
        - Recommend difficulty
        - Recommend explanation depth
        - Recommend examples
        - Recommend analogies
        - Recommend step-by-step teaching
        - Detect when the student may need reinforcement
        - Detect when the student may be ready for a challenge
        - Produce structured strategy data for TutorEngine
    """

    # =====================================
    # INITIALIZATION
    # =====================================

    def __init__(self):

        print(
            "Loading Nova Brain..."
        )

        self.default_confidence = 50

        self.confidence_levels = {

            "very_low": 0,

            "low": 40,

            "medium": 60,

            "high": 80,

            "very_high": 90
        }

    # =====================================
    # MAIN THINKING ENGINE
    # =====================================

    def think(
        self,
        student,
        subject,
        topic,
        understanding
    ):
        """
        Analyze the student's current state.

        Parameters
        ----------
        student:
            Student profile dictionary.

        subject:
            Detected academic subject.

        topic:
            Detected topic/concept.

        understanding:
            Understanding data, normally provided by
            UnderstandingAnalyzer.

        Returns
        -------
        dict
            Structured learning strategy.
        """

        # =====================================
        # NORMALIZE INPUT
        # =====================================

        student = (
            student
            if isinstance(student, dict)
            else {}
        )

        understanding = (
            understanding
            if isinstance(understanding, dict)
            else {}
        )

        # =====================================
        # STUDENT LEVEL
        # =====================================

        student_level = self._get_student_level(
            student
        )

        # =====================================
        # SUBJECT CONFIDENCE
        # =====================================

        subject_confidence = (
            self._get_subject_confidence(
                understanding,
                subject
            )
        )

        # =====================================
        # TOPIC CONFIDENCE
        # =====================================

        topic_confidence = (
            self._get_topic_confidence(
                understanding,
                subject,
                topic,
                subject_confidence
            )
        )

        # =====================================
        # FINAL CONFIDENCE
        # =====================================

        confidence = (
            self._calculate_confidence(
                subject_confidence,
                topic_confidence
            )
        )

        # =====================================
        # LEARNING STATE
        # =====================================

        learning_state = (
            self._determine_learning_state(
                confidence
            )
        )

        # =====================================
        # DIFFICULTY
        # =====================================

        difficulty = (
            self._determine_difficulty(
                confidence,
                student_level
            )
        )

        # =====================================
        # BASE STRATEGY
        # =====================================

        approach = (
            self._build_base_approach(
                confidence,
                learning_state
            )
        )

        # =====================================
        # SUBJECT STRATEGY
        # =====================================

        subject_approach = (
            self._build_subject_strategy(
                subject
            )
        )

        approach.extend(
            subject_approach
        )

        # =====================================
        # TOPIC STRATEGY
        # =====================================

        topic_approach = (
            self._build_topic_strategy(
                topic,
                confidence
            )
        )

        approach.extend(
            topic_approach
        )

        # =====================================
        # EXPLANATION DEPTH
        # =====================================

        explanation_depth = (
            self._determine_explanation_depth(
                confidence
            )
        )

        # =====================================
        # EXAMPLES
        # =====================================

        use_examples = (
            self._should_use_examples(
                confidence
            )
        )

        # =====================================
        # ANALOGIES
        # =====================================

        use_analogies = (
            self._should_use_analogies(
                confidence,
                subject
            )
        )

        # =====================================
        # STEP BY STEP
        # =====================================

        step_by_step = (
            self._should_use_step_by_step(
                confidence,
                subject
            )
        )

        # =====================================
        # CHALLENGE
        # =====================================

        challenge = (
            self._should_challenge(
                confidence
            )
        )

        # =====================================
        # REINFORCEMENT
        # =====================================

        reinforcement = (
            self._needs_reinforcement(
                confidence
            )
        )

        # =====================================
        # QUESTION DIFFICULTY
        # =====================================

        challenge_level = (
            self._determine_challenge_level(
                confidence
            )
        )

        # =====================================
        # RESPONSE STYLE
        # =====================================

        response_style = (
            self._determine_response_style(
                confidence,
                student_level
            )
        )

        # =====================================
        # FINAL STRATEGY
        # =====================================

        strategy = {

            # ---------------------------------
            # STUDENT
            # ---------------------------------

            "student_level":
                student_level,

            # ---------------------------------
            # SUBJECT
            # ---------------------------------

            "subject":
                subject,

            # ---------------------------------
            # TOPIC
            # ---------------------------------

            "topic":
                topic,

            # ---------------------------------
            # CONFIDENCE
            # ---------------------------------

            "confidence":
                confidence,

            "subject_confidence":
                subject_confidence,

            "topic_confidence":
                topic_confidence,

            # ---------------------------------
            # LEARNING STATE
            # ---------------------------------

            "learning_state":
                learning_state,

            # ---------------------------------
            # DIFFICULTY
            # ---------------------------------

            "difficulty":
                difficulty,

            # ---------------------------------
            # TEACHING STRATEGY
            # ---------------------------------

            "approach":
                approach,

            "explanation_depth":
                explanation_depth,

            "response_style":
                response_style,

            # ---------------------------------
            # TEACHING TOOLS
            # ---------------------------------

            "use_examples":
                use_examples,

            "use_analogies":
                use_analogies,

            "step_by_step":
                step_by_step,

            # ---------------------------------
            # LEARNING ACTIONS
            # ---------------------------------

            "challenge":
                challenge,

            "challenge_level":
                challenge_level,

            "reinforcement":
                reinforcement,

            # ---------------------------------
            # METADATA
            # ---------------------------------

            "signals": {

                "needs_help":
                    confidence < 40,

                "needs_examples":
                    use_examples,

                "needs_simple_explanation":
                    confidence < 40,

                "ready_for_depth":
                    confidence >= 70,

                "ready_for_challenge":
                    challenge,

                "needs_reinforcement":
                    reinforcement
            }
        }

        return strategy

    # =====================================
    # STUDENT LEVEL
    # =====================================

    def _get_student_level(
        self,
        student
    ):

        level = student.get(
            "level",
            "beginner"
        )

        if not isinstance(
            level,
            str
        ):

            return "beginner"

        level = level.strip().lower()

        valid_levels = {

            "beginner",
            "elementary",
            "intermediate",
            "advanced",
            "expert",
            "high_school",
            "high school"
        }

        if level not in valid_levels:

            return "beginner"

        return level

    # =====================================
    # SUBJECT CONFIDENCE
    # =====================================

    def _get_subject_confidence(
        self,
        understanding,
        subject
    ):

        if not subject:

            return self.default_confidence

        if subject not in understanding:

            return self.default_confidence

        data = understanding.get(
            subject
        )

        if not isinstance(
            data,
            dict
        ):

            return self.default_confidence

        confidence = data.get(
            "confidence",
            self.default_confidence
        )

        return self._normalize_confidence(
            confidence
        )

    # =====================================
    # TOPIC CONFIDENCE
    # =====================================

    def _get_topic_confidence(
        self,
        understanding,
        subject,
        topic,
        subject_confidence
    ):
        """
        Try to obtain topic-level confidence.

        Current UnderstandingAnalyzer primarily stores
        confidence at subject level, so the subject confidence
        is used as a fallback.

        This keeps Nova compatible with the current system
        while allowing future topic-level learning data.
        """

        if not topic:

            return subject_confidence

        # Possible future structure:

        # understanding = {
        #     "physics": {
        #         "topics": {
        #             "gravity": {
        #                 "confidence": 70
        #             }
        #         }
        #     }
        # }

        subject_data = understanding.get(
            subject
        )

        if not isinstance(
            subject_data,
            dict
        ):

            return subject_confidence

        topics = subject_data.get(
            "topics"
        )

        if not isinstance(
            topics,
            dict
        ):

            return subject_confidence

        topic_data = topics.get(
            topic
        )

        if not isinstance(
            topic_data,
            dict
        ):

            return subject_confidence

        confidence = topic_data.get(
            "confidence"
        )

        if confidence is None:

            return subject_confidence

        return self._normalize_confidence(
            confidence
        )

    # =====================================
    # CONFIDENCE CALCULATION
    # =====================================

    def _calculate_confidence(
        self,
        subject_confidence,
        topic_confidence
    ):
        """
        Combine subject and topic confidence.

        Topic confidence receives slightly more weight because
        understanding an entire subject does not necessarily
        mean understanding one specific concept.
        """

        confidence = (

            (
                subject_confidence
                * 0.40
            )

            +

            (
                topic_confidence
                * 0.60
            )
        )

        return round(
            max(
                0,
                min(
                    100,
                    confidence
                )
            )
        )

    # =====================================
    # NORMALIZE CONFIDENCE
    # =====================================

    def _normalize_confidence(
        self,
        confidence
    ):

        try:

            confidence = float(
                confidence
            )

        except (
            TypeError,
            ValueError
        ):

            return self.default_confidence

        # Convert 0-1 confidence to 0-100.

        if 0 <= confidence <= 1:

            confidence *= 100

        return round(
            max(
                0,
                min(
                    100,
                    confidence
                )
            )
        )

    # =====================================
    # LEARNING STATE
    # =====================================

    def _determine_learning_state(
        self,
        confidence
    ):

        if confidence < 25:

            return "struggling"

        if confidence < 40:

            return "weak"

        if confidence < 60:

            return "developing"

        if confidence < 75:

            return "understanding"

        if confidence < 90:

            return "strong"

        return "mastery"

    # =====================================
    # DIFFICULTY
    # =====================================

    def _determine_difficulty(
        self,
        confidence,
        student_level
    ):

        if confidence < 30:

            return "beginner"

        if confidence < 50:

            return "easy"

        if confidence < 70:

            return "medium"

        if confidence < 85:

            return "advanced"

        # Very strong students should not
        # automatically receive maximum difficulty
        # if their general level is beginner.

        if student_level in {
            "beginner",
            "elementary"
        }:

            return "advanced"

        return "expert"

    # =====================================
    # BASE APPROACH
    # =====================================

    def _build_base_approach(
        self,
        confidence,
        learning_state
    ):

        approach = []

        if learning_state == "struggling":

            approach.append(
                "Start from the absolute basics."
            )

            approach.append(
                "Use very simple vocabulary."
            )

            approach.append(
                "Explain one idea at a time."
            )

            approach.append(
                "Avoid unnecessary technical details."
            )

            approach.append(
                "Check understanding before moving forward."
            )

        elif learning_state == "weak":

            approach.append(
                "Review the fundamental idea first."
            )

            approach.append(
                "Use a simple explanation."
            )

            approach.append(
                "Give a concrete example."
            )

            approach.append(
                "Connect the explanation to something familiar."
            )

        elif learning_state == "developing":

            approach.append(
                "Explain the concept clearly."
            )

            approach.append(
                "Connect the new idea to previous knowledge."
            )

            approach.append(
                "Use at least one useful example."
            )

        elif learning_state == "understanding":

            approach.append(
                "Build on the student's current understanding."
            )

            approach.append(
                "Explain why the concept works."
            )

            approach.append(
                "Use examples to reinforce the idea."
            )

        elif learning_state == "strong":

            approach.append(
                "Avoid repeating basic information unnecessarily."
            )

            approach.append(
                "Introduce deeper connections."
            )

            approach.append(
                "Use more precise terminology."
            )

        elif learning_state == "mastery":

            approach.append(
                "Treat the student as highly competent."
            )

            approach.append(
                "Focus on deeper reasoning."
            )

            approach.append(
                "Introduce challenging applications."
            )

        return approach

    # =====================================
    # SUBJECT STRATEGY
    # =====================================

    def _build_subject_strategy(
        self,
        subject
    ):

        if subject == "physics":

            return [

                "Use real-world physical situations.",

                "Explain relationships between quantities.",

                "Use equations only when they improve understanding.",

                "Connect formulas to what they physically represent."
            ]

        if subject == "biology":

            return [

                "Explain biological processes in logical steps.",

                "Connect structures to their functions.",

                "Use concrete biological examples.",

                "Show how different parts of a system interact."
            ]

        if subject == "chemistry":

            return [

                "Connect microscopic particles to observable effects.",

                "Explain reactions step by step.",

                "Define chemical terminology before using it.",

                "Use equations carefully and explain what they represent."
            ]

        if subject == "math":

            return [

                "Show the solving method clearly.",

                "Explain why each mathematical step is performed.",

                "Separate the method from the final answer.",

                "Use a worked example when appropriate."
            ]

        if subject == "history":

            return [

                "Build a clear chronological structure.",

                "Explain causes and consequences.",

                "Connect events to their historical context.",

                "Distinguish important facts from minor details."
            ]

        if subject == "geography":

            return [

                "Connect geographical concepts to real locations.",

                "Explain relationships between humans and environments.",

                "Use spatial reasoning where useful.",

                "Connect causes to geographical consequences."
            ]

        return [

            "Adapt the explanation to the student's current level.",

            "Focus on understanding rather than memorization."
        ]

    # =====================================
    # TOPIC STRATEGY
    # =====================================

    def _build_topic_strategy(
        self,
        topic,
        confidence
    ):

        if not topic:

            return []

        approach = []

        if confidence < 40:

            approach.append(
                f"Break down the topic '{topic}' into smaller ideas."
            )

        elif confidence < 70:

            approach.append(
                f"Connect '{topic}' to related concepts."
            )

        else:

            approach.append(
                f"Explore deeper applications of '{topic}'."
            )

        return approach

    # =====================================
    # EXPLANATION DEPTH
    # =====================================

    def _determine_explanation_depth(
        self,
        confidence
    ):

        if confidence < 30:

            return "very_basic"

        if confidence < 50:

            return "basic"

        if confidence < 70:

            return "balanced"

        if confidence < 85:

            return "deep"

        return "advanced"

    # =====================================
    # EXAMPLES
    # =====================================

    def _should_use_examples(
        self,
        confidence
    ):

        if confidence < 75:

            return True

        return False

    # =====================================
    # ANALOGIES
    # =====================================

    def _should_use_analogies(
        self,
        confidence,
        subject
    ):

        if confidence < 50:

            return True

        if subject in {
            "physics",
            "biology",
            "chemistry"
        }:

            return confidence < 60

        return False

    # =====================================
    # STEP BY STEP
    # =====================================

    def _should_use_step_by_step(
        self,
        confidence,
        subject
    ):

        if confidence < 60:

            return True

        if subject in {
            "math",
            "chemistry",
            "physics"
        }:

            return confidence < 75

        return False

    # =====================================
    # CHALLENGE
    # =====================================

    def _should_challenge(
        self,
        confidence
    ):

        return confidence >= 75

    # =====================================
    # REINFORCEMENT
    # =====================================

    def _needs_reinforcement(
        self,
        confidence
    ):

        return confidence < 55

    # =====================================
    # CHALLENGE LEVEL
    # =====================================

    def _determine_challenge_level(
        self,
        confidence
    ):

        if confidence < 40:

            return "none"

        if confidence < 65:

            return "small"

        if confidence < 80:

            return "moderate"

        if confidence < 90:

            return "difficult"

        return "expert"

    # =====================================
    # RESPONSE STYLE
    # =====================================

    def _determine_response_style(
        self,
        confidence,
        student_level
    ):

        if confidence < 40:

            return "simple_supportive"

        if confidence < 70:

            return "clear_instructional"

        if confidence < 85:

            return "deep_instructional"

        return "challenging"

    # =====================================
    # QUICK CONFIDENCE
    # =====================================

    def get_confidence(
        self,
        subject,
        understanding
    ):

        if not isinstance(
            understanding,
            dict
        ):

            return self.default_confidence

        return self._get_subject_confidence(
            understanding,
            subject
        )

    # =====================================
    # QUICK STATE
    # =====================================

    def get_learning_state(
        self,
        confidence
    ):

        confidence = (
            self._normalize_confidence(
                confidence
            )
        )

        return self._determine_learning_state(
            confidence
        )

    # =====================================
    # QUICK DIFFICULTY
    # =====================================

    def get_difficulty(
        self,
        confidence,
        student_level="beginner"
    ):

        confidence = (
            self._normalize_confidence(
                confidence
            )
        )

        return self._determine_difficulty(
            confidence,
            student_level
        )