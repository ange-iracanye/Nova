from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import math
import re


class NovaBrain:
    """
    Nova's adaptive learning and teaching-strategy engine.

    NovaBrain does NOT generate the final answer.

    Its job is to analyze the available learning information and
    produce a structured strategy that other Nova systems can use.

    Main responsibilities
    ---------------------

    STUDENT ANALYSIS
        - Normalize student information
        - Interpret academic level
        - Estimate experience
        - Detect strengths and weaknesses

    CONFIDENCE ANALYSIS
        - Subject confidence
        - Topic confidence
        - Historical confidence
        - Confidence signals
        - Confidence trends
        - Confidence stability

    LEARNING STATE
        - Struggling
        - Weak
        - Developing
        - Understanding
        - Strong
        - Mastery

    TEACHING STRATEGY
        - Explanation depth
        - Teaching style
        - Examples
        - Analogies
        - Step-by-step teaching
        - Reinforcement
        - Challenge
        - Hints
        - Practice
        - Retrieval

    SUBJECT STRATEGY
        - Mathematics
        - Physics
        - Chemistry
        - Biology
        - History
        - Geography
        - Languages
        - Programming
        - Generic fallback

    SAFETY / RELIABILITY
        - Input validation
        - Safe defaults
        - Confidence clamping
        - Invalid-data handling
        - Strategy consistency checks

    EXPLAINABILITY
        - Decision reasons
        - Detected signals
        - Recommended actions
        - Strategy summary

    DESIGN PRINCIPLE
    ----------------
    NovaBrain should never blindly trust one number.

    A student's confidence score is useful, but it is only one
    piece of evidence.

    The engine therefore combines:

        profile information
        subject understanding
        topic understanding
        historical signals
        learning trends
        current message signals
        previous attempts
        known strengths
        known weaknesses

    The result is a structured strategy dictionary.

    Example result:

        {
            "confidence": 42,
            "learning_state": "developing",
            "difficulty": "medium",
            "explanation_depth": "balanced",
            "use_examples": True,
            "use_analogies": True,
            "step_by_step": True,
            "reinforcement": True,
            "challenge": False,
            "approach": [...],
            "signals": {...},
            "recommendations": [...],
            "reasons": [...]
        }

    The class intentionally does not call the LLM.

    This keeps reasoning and generation separated.
    """

    # ============================================================
    # VERSION
    # ============================================================

    VERSION = "2.0"

    # ============================================================
    # DEFAULTS
    # ============================================================

    DEFAULT_CONFIDENCE = 50.0

    MIN_CONFIDENCE = 0.0
    MAX_CONFIDENCE = 100.0

    # ============================================================
    # CONFIDENCE THRESHOLDS
    # ============================================================

    VERY_LOW_THRESHOLD = 25
    LOW_THRESHOLD = 40
    DEVELOPING_THRESHOLD = 60
    UNDERSTANDING_THRESHOLD = 75
    STRONG_THRESHOLD = 90

    # ============================================================
    # CONFIDENCE WEIGHTS
    # ============================================================

    SUBJECT_WEIGHT = 0.35
    TOPIC_WEIGHT = 0.50
    HISTORY_WEIGHT = 0.15

    # ============================================================
    # SIGNAL WEIGHTS
    # ============================================================

    CONFUSION_PENALTY = 15
    FRUSTRATION_PENALTY = 10
    CLARIFICATION_PENALTY = 4

    UNDERSTANDING_BONUS = 12
    SUCCESS_BONUS = 8
    MASTERY_BONUS = 5

    # ============================================================
    # LIMITS
    # ============================================================

    MAX_APPROACH_ITEMS = 20
    MAX_REASONS = 20
    MAX_RECOMMENDATIONS = 20
    MAX_HISTORY_ITEMS = 20

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(self):

        print(
            "Loading Nova Brain..."
        )

        self.default_confidence = (
            self.DEFAULT_CONFIDENCE
        )

        self.confidence_levels = {

            "very_low": 0,

            "low": 40,

            "medium": 60,

            "high": 80,

            "very_high": 90
        }

        # --------------------------------------------------------
        # Optional internal analysis history.
        #
        # This is intentionally lightweight and is NOT intended
        # to replace LearningMemory or KnowledgeMap.
        # --------------------------------------------------------

        self.history = {}

        # --------------------------------------------------------
        # Subject aliases
        # --------------------------------------------------------

        self.subject_aliases = {

            "mathematics": "math",
            "mathematics ": "math",
            "maths": "math",

            "physic": "physics",
            "physical science": "physics",

            "chem": "chemistry",

            "bio": "biology",

            "geography ": "geography",

            "computer science": "programming",
            "coding": "programming",
            "software": "programming",

            "english language": "english",
            "french language": "french"
        }

        # --------------------------------------------------------
        # Academic levels
        # --------------------------------------------------------

        self.valid_student_levels = {

            "beginner",
            "elementary",
            "intermediate",
            "advanced",
            "expert",
            "high_school",
            "college",
            "university"
        }

        # --------------------------------------------------------
        # Teaching style preferences
        # --------------------------------------------------------

        self.teaching_styles = {

            "adaptive",
            "direct",
            "step_by_step",
            "socratic",
            "conceptual",
            "practical"
        }

        print(
            "Nova Brain ready."
        )

    # ============================================================
    # MAIN THINKING ENGINE
    # ============================================================

    def think(
        self,
        student,
        subject,
        topic=None,
        understanding=None,
        message=None,
        history=None,
        knowledge=None,
        session=None,
        settings=None
    ):
        """
        Analyze the student's current learning situation.

        Parameters
        ----------
        student:
            Student profile dictionary.

        subject:
            Current subject.

        topic:
            Current topic or concept.

        understanding:
            UnderstandingAnalyzer data.

        message:
            Current student message.

        history:
            Optional previous confidence / learning history.

        knowledge:
            Optional KnowledgeMap data.

        session:
            Optional session information.

        settings:
            Optional student settings.

        Returns
        -------
        dict
            Complete teaching strategy.
        """

        # ========================================================
        # NORMALIZE EVERYTHING
        # ========================================================

        student = self._normalize_dict(
            student
        )

        understanding = self._normalize_dict(
            understanding
        )

        knowledge = self._normalize_dict(
            knowledge
        )

        settings = self._normalize_dict(
            settings
        )

        history = self._normalize_history(
            history
        )

        session = self._normalize_dict(
            session
        )

        subject = self.normalize_subject(
            subject
        )

        topic = self._normalize_text(
            topic
        )

        message = self._normalize_text(
            message
        )

        # ========================================================
        # STUDENT LEVEL
        # ========================================================

        student_level = (
            self._get_student_level(
                student
            )
        )

        # ========================================================
        # SUBJECT CONFIDENCE
        # ========================================================

        subject_confidence = (
            self._get_subject_confidence(
                understanding,
                subject
            )
        )

        # ========================================================
        # TOPIC CONFIDENCE
        # ========================================================

        topic_confidence = (
            self._get_topic_confidence(
                understanding,
                subject,
                topic,
                subject_confidence
            )
        )

        # ========================================================
        # KNOWLEDGE MAP CONFIDENCE
        # ========================================================

        knowledge_confidence = (
            self._get_knowledge_confidence(
                knowledge,
                subject,
                topic
            )
        )

        # ========================================================
        # HISTORICAL CONFIDENCE
        # ========================================================

        historical_confidence = (
            self._get_historical_confidence(
                history,
                subject,
                topic
            )
        )

        # ========================================================
        # CURRENT MESSAGE SIGNALS
        # ========================================================

        signals = (
            self.detect_learning_signals(
                message
            )
        )

        # ========================================================
        # CONFIDENCE TREND
        # ========================================================

        trend = (
            self.analyze_trend(
                history,
                subject,
                topic
            )
        )

        # ========================================================
        # BASE CONFIDENCE
        # ========================================================

        confidence = (
            self._calculate_confidence(
                subject_confidence=
                    subject_confidence,

                topic_confidence=
                    topic_confidence,

                historical_confidence=
                    historical_confidence,

                knowledge_confidence=
                    knowledge_confidence
            )
        )

        # ========================================================
        # APPLY CURRENT MESSAGE SIGNALS
        # ========================================================

        confidence = (
            self._apply_signal_adjustments(
                confidence,
                signals
            )
        )

        # ========================================================
        # APPLY TREND
        # ========================================================

        confidence = (
            self._apply_trend_adjustment(
                confidence,
                trend
            )
        )

        # ========================================================
        # KNOWN STRENGTHS / WEAKNESSES
        # ========================================================

        profile_adjustment = (
            self._calculate_profile_adjustment(
                student,
                subject,
                topic
            )
        )

        confidence = (
            confidence
            + profile_adjustment
        )

        confidence = self._clamp_confidence(
            confidence
        )

        # ========================================================
        # LEARNING STATE
        # ========================================================

        learning_state = (
            self._determine_learning_state(
                confidence,
                signals=signals,
                trend=trend
            )
        )

        # ========================================================
        # DIFFICULTY
        # ========================================================

        difficulty = (
            self._determine_difficulty(
                confidence,
                student_level,
                signals
            )
        )

        # ========================================================
        # EXPLANATION DEPTH
        # ========================================================

        explanation_depth = (
            self._determine_explanation_depth(
                confidence,
                signals
            )
        )

        # ========================================================
        # TEACHING STYLE
        # ========================================================

        teaching_style = (
            self._determine_teaching_style(
                confidence,
                student_level,
                settings,
                signals
            )
        )

        # ========================================================
        # EXAMPLES
        # ========================================================

        use_examples = (
            self._should_use_examples(
                confidence,
                signals
            )
        )

        # ========================================================
        # ANALOGIES
        # ========================================================

        use_analogies = (
            self._should_use_analogies(
                confidence,
                subject,
                signals
            )
        )

        # ========================================================
        # STEP BY STEP
        # ========================================================

        step_by_step = (
            self._should_use_step_by_step(
                confidence,
                subject,
                signals
            )
        )

        # ========================================================
        # HINTS
        # ========================================================

        use_hints = (
            self._should_use_hints(
                confidence,
                signals,
                settings
            )
        )

        # ========================================================
        # REINFORCEMENT
        # ========================================================

        reinforcement = (
            self._needs_reinforcement(
                confidence,
                signals,
                trend
            )
        )

        # ========================================================
        # PRACTICE
        # ========================================================

        practice = (
            self._should_practice(
                confidence,
                signals,
                learning_state
            )
        )

        # ========================================================
        # RETRIEVAL PRACTICE
        # ========================================================

        retrieval = (
            self._should_use_retrieval(
                confidence,
                learning_state,
                signals
            )
        )

        # ========================================================
        # CHALLENGE
        # ========================================================

        challenge = (
            self._should_challenge(
                confidence,
                signals,
                trend,
                student_level
            )
        )

        # ========================================================
        # CHALLENGE LEVEL
        # ========================================================

        challenge_level = (
            self._determine_challenge_level(
                confidence,
                challenge
            )
        )

        # ========================================================
        # CHECK UNDERSTANDING
        # ========================================================

        check_understanding = (
            self._should_check_understanding(
                confidence,
                signals,
                learning_state
            )
        )

        # ========================================================
        # SUBJECT STRATEGY
        # ========================================================

        subject_approach = (
            self._build_subject_strategy(
                subject
            )
        )

        # ========================================================
        # TOPIC STRATEGY
        # ========================================================

        topic_approach = (
            self._build_topic_strategy(
                topic,
                confidence
            )
        )

        # ========================================================
        # BASE STRATEGY
        # ========================================================

        base_approach = (
            self._build_base_approach(
                confidence,
                learning_state,
                signals
            )
        )

        # ========================================================
        # TREND STRATEGY
        # ========================================================

        trend_approach = (
            self._build_trend_strategy(
                trend
            )
        )

        # ========================================================
        # PROFILE STRATEGY
        # ========================================================

        profile_approach = (
            self._build_profile_strategy(
                student,
                subject,
                topic
            )
        )

        # ========================================================
        # COMBINE APPROACHES
        # ========================================================

        approach = self._combine_unique(
            base_approach,
            subject_approach,
            topic_approach,
            trend_approach,
            profile_approach
        )

        # ========================================================
        # AUTOMATIC ACTIONS
        # ========================================================

        actions = (
            self._build_actions(
                confidence=confidence,
                learning_state=learning_state,
                use_examples=use_examples,
                use_analogies=use_analogies,
                step_by_step=step_by_step,
                use_hints=use_hints,
                reinforcement=reinforcement,
                practice=practice,
                retrieval=retrieval,
                challenge=challenge,
                check_understanding=check_understanding
            )
        )

        # ========================================================
        # RESPONSE STYLE
        # ========================================================

        response_style = (
            self._determine_response_style(
                confidence,
                student_level,
                signals
            )
        )

        # ========================================================
        # REASONS
        # ========================================================

        reasons = (
            self._build_reasons(
                confidence=confidence,
                learning_state=learning_state,
                signals=signals,
                trend=trend,
                subject=subject,
                topic=topic
            )
        )

        # ========================================================
        # RECOMMENDATIONS
        # ========================================================

        recommendations = (
            self._build_recommendations(
                confidence=confidence,
                learning_state=learning_state,
                challenge=challenge,
                reinforcement=reinforcement,
                practice=practice,
                check_understanding=check_understanding
            )
        )

        # ========================================================
        # METADATA
        # ========================================================

        metadata = {

            "brain_version":
                self.VERSION,

            "analysis_confidence":
                self._confidence_quality(
                    understanding,
                    knowledge,
                    history
                ),

            "data_sources": (
                self._get_data_sources(
                    understanding,
                    knowledge,
                    history
                )
            ),

            "subject_normalized":
                subject,

            "topic_available":
                bool(topic),

            "message_analyzed":
                bool(message)
        }

        # ========================================================
        # SIGNAL FLAGS
        # ========================================================

        signal_flags = {

            "needs_help":
                confidence < 40,

            "likely_confused":
                signals["confusion"],

            "likely_frustrated":
                signals["frustration"],

            "requested_simplification":
                signals["simplification_request"],

            "requested_detail":
                signals["depth_request"],

            "requested_example":
                signals["example_request"],

            "demonstrated_understanding":
                signals["understanding"],

            "likely_practicing":
                signals["practice_request"],

            "ready_for_depth":
                confidence >= 70,

            "ready_for_challenge":
                challenge,

            "needs_reinforcement":
                reinforcement,

            "needs_step_by_step":
                step_by_step
        }

        # ========================================================
        # FINAL STRATEGY
        # ========================================================

        strategy = {

            # ----------------------------------------------------
            # CORE IDENTITY
            # ----------------------------------------------------

            "student_level":
                student_level,

            "subject":
                subject,

            "topic":
                topic,

            # ----------------------------------------------------
            # CONFIDENCE
            # ----------------------------------------------------

            "confidence":
                confidence,

            "subject_confidence":
                subject_confidence,

            "topic_confidence":
                topic_confidence,

            "knowledge_confidence":
                knowledge_confidence,

            "historical_confidence":
                historical_confidence,

            # ----------------------------------------------------
            # TREND
            # ----------------------------------------------------

            "trend":
                trend["direction"],

            "trend_strength":
                trend["strength"],

            "trend_data":
                trend,

            # ----------------------------------------------------
            # LEARNING STATE
            # ----------------------------------------------------

            "learning_state":
                learning_state,

            # ----------------------------------------------------
            # DIFFICULTY
            # ----------------------------------------------------

            "difficulty":
                difficulty,

            "challenge_level":
                challenge_level,

            # ----------------------------------------------------
            # TEACHING
            # ----------------------------------------------------

            "teaching_style":
                teaching_style,

            "explanation_depth":
                explanation_depth,

            "response_style":
                response_style,

            # ----------------------------------------------------
            # TEACHING TOOLS
            # ----------------------------------------------------

            "use_examples":
                use_examples,

            "use_analogies":
                use_analogies,

            "step_by_step":
                step_by_step,

            "use_hints":
                use_hints,

            "check_understanding":
                check_understanding,

            # ----------------------------------------------------
            # LEARNING ACTIONS
            # ----------------------------------------------------

            "reinforcement":
                reinforcement,

            "practice":
                practice,

            "retrieval":
                retrieval,

            "challenge":
                challenge,

            # ----------------------------------------------------
            # STRATEGY
            # ----------------------------------------------------

            "approach":
                approach,

            "actions":
                actions,

            "recommendations":
                recommendations,

            "reasons":
                reasons,

            # ----------------------------------------------------
            # SIGNALS
            # ----------------------------------------------------

            "signals":
                signal_flags,

            "raw_signals":
                signals,

            # ----------------------------------------------------
            # METADATA
            # ----------------------------------------------------

            "metadata":
                metadata
        }

        # ========================================================
        # STORE LIGHT INTERNAL HISTORY
        # ========================================================

        self._record_internal_analysis(
            subject=subject,
            topic=topic,
            confidence=confidence,
            learning_state=learning_state,
            trend=trend
        )

        # ========================================================
        # VALIDATE FINAL STRATEGY
        # ========================================================

        strategy = self.validate_strategy(
            strategy
        )

        return strategy

    # ============================================================
    # NORMALIZATION
    # ============================================================

    def _normalize_dict(
        self,
        value
    ) -> Dict[str, Any]:

        if not isinstance(
            value,
            dict
        ):
            return {}

        return dict(
            value
        )

    # ============================================================

    def _normalize_text(
        self,
        value,
        default=""
    ) -> str:

        if value is None:
            return default

        if not isinstance(
            value,
            str
        ):
            value = str(
                value
            )

        value = value.strip()

        if not value:
            return default

        return value

    # ============================================================

    def normalize_subject(
        self,
        subject
    ) -> str:

        subject = self._normalize_text(
            subject
        )

        if not subject:
            return ""

        normalized = (
            subject
            .lower()
            .strip()
        )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized
        )

        return self.subject_aliases.get(
            normalized,
            normalized
        )

    # ============================================================

    def _normalize_history(
        self,
        history
    ) -> Dict[str, Any]:

        if history is None:
            return {}

        if isinstance(
            history,
            list
        ):

            return {
                "entries":
                    history
            }

        if isinstance(
            history,
            dict
        ):

            return dict(
                history
            )

        return {}

    # ============================================================
    # STUDENT LEVEL
    # ============================================================

    def _get_student_level(
        self,
        student
    ) -> str:

        level = student.get(
            "level",
            "beginner"
        )

        if not isinstance(
            level,
            str
        ):
            return "beginner"

        level = (
            level
            .strip()
            .lower()
        )

        level = level.replace(
            "-",
            "_"
        )

        level = re.sub(
            r"\s+",
            "_",
            level
        )

        if level in self.valid_student_levels:
            return level

        return "beginner"

    # ============================================================
    # SUBJECT CONFIDENCE
    # ============================================================

    def _get_subject_confidence(
        self,
        understanding,
        subject
    ) -> float:

        if not subject:
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

    # ============================================================
    # TOPIC CONFIDENCE
    # ============================================================

    def _get_topic_confidence(
        self,
        understanding,
        subject,
        topic,
        subject_confidence
    ) -> float:

        if not topic:
            return subject_confidence

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

        # Direct match first.
        topic_data = topics.get(
            topic
        )

        # Case-insensitive fallback.
        if topic_data is None:

            topic_lower = (
                topic.lower()
            )

            for key, value in topics.items():

                if (
                    isinstance(key, str)
                    and key.lower() == topic_lower
                ):

                    topic_data = value
                    break

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

    # ============================================================
    # KNOWLEDGE MAP CONFIDENCE
    # ============================================================

    def _get_knowledge_confidence(
        self,
        knowledge,
        subject,
        topic
    ) -> float:

        if not knowledge:
            return self.default_confidence

        candidates = []

        # --------------------------------------------------------
        # Subject-level structures
        # --------------------------------------------------------

        subject_data = knowledge.get(
            subject
        )

        if isinstance(
            subject_data,
            dict
        ):

            candidates.append(
                subject_data.get(
                    "confidence"
                )
            )

            # Topic data.
            topics = subject_data.get(
                "topics"
            )

            if isinstance(
                topics,
                dict
            ) and topic:

                topic_data = topics.get(
                    topic
                )

                if isinstance(
                    topic_data,
                    dict
                ):

                    candidates.append(
                        topic_data.get(
                            "confidence"
                        )
                    )

        # --------------------------------------------------------
        # Generic top-level confidence
        # --------------------------------------------------------

        candidates.append(
            knowledge.get(
                "confidence"
            )
        )

        valid = []

        for value in candidates:

            if value is None:
                continue

            try:

                valid.append(
                    self._normalize_confidence(
                        value
                    )
                )

            except Exception:
                continue

        if not valid:
            return self.default_confidence

        return round(
            sum(valid) / len(valid)
        )

    # ============================================================
    # HISTORICAL CONFIDENCE
    # ============================================================

    def _get_historical_confidence(
        self,
        history,
        subject,
        topic
    ) -> float:

        if not history:
            return self.default_confidence

        values = []

        # --------------------------------------------------------
        # Subject history
        # --------------------------------------------------------

        subject_data = history.get(
            subject
        )

        if isinstance(
            subject_data,
            dict
        ):

            value = subject_data.get(
                "confidence"
            )

            if value is not None:

                values.append(
                    self._normalize_confidence(
                        value
                    )
                )

            topic_data = (
                subject_data
                .get("topics")
            )

            if (
                isinstance(topic_data, dict)
                and topic
            ):

                topic_entry = (
                    topic_data.get(topic)
                )

                if isinstance(
                    topic_entry,
                    dict
                ):

                    value = (
                        topic_entry.get(
                            "confidence"
                        )
                    )

                    if value is not None:

                        values.append(
                            self._normalize_confidence(
                                value
                            )
                        )

        # --------------------------------------------------------
        # Entry list
        # --------------------------------------------------------

        entries = history.get(
            "entries"
        )

        if isinstance(
            entries,
            list
        ):

            recent = entries[
                -self.MAX_HISTORY_ITEMS:
            ]

            for entry in recent:

                if not isinstance(
                    entry,
                    dict
                ):
                    continue

                entry_subject = (
                    self.normalize_subject(
                        entry.get(
                            "subject"
                        )
                    )
                )

                if (
                    subject
                    and entry_subject
                    and entry_subject != subject
                ):
                    continue

                entry_topic = (
                    self._normalize_text(
                        entry.get(
                            "topic"
                        )
                    )
                )

                if (
                    topic
                    and entry_topic
                    and entry_topic.lower()
                    != topic.lower()
                ):
                    continue

                value = entry.get(
                    "confidence"
                )

                if value is not None:

                    values.append(
                        self._normalize_confidence(
                            value
                        )
                    )

        if not values:
            return self.default_confidence

        # Recent observations should matter more.
        weighted_total = 0.0
        weight_total = 0.0

        for index, value in enumerate(
            values[-10:],
            start=1
        ):

            weighted_total += (
                value * index
            )

            weight_total += index

        if weight_total == 0:
            return self.default_confidence

        return round(
            weighted_total
            / weight_total
        )

    # ============================================================
    # CONFIDENCE CALCULATION
    # ============================================================

    def _calculate_confidence(
        self,
        subject_confidence,
        topic_confidence,
        historical_confidence,
        knowledge_confidence
    ) -> float:

        # Topic is the most important source because students can
        # be strong in a subject while struggling with one concept.

        confidence = (

            subject_confidence
            * self.SUBJECT_WEIGHT

            +

            topic_confidence
            * self.TOPIC_WEIGHT

            +

            historical_confidence
            * self.HISTORY_WEIGHT
        )

        # KnowledgeMap acts as a stabilizing signal rather than
        # receiving another full weight. This prevents it from
        # overpowering current understanding.

        knowledge_difference = (
            knowledge_confidence
            - confidence
        )

        confidence += (
            knowledge_difference
            * 0.10
        )

        return self._clamp_confidence(
            confidence
        )

    # ============================================================
    # CONFIDENCE NORMALIZATION
    # ============================================================

    def _normalize_confidence(
        self,
        confidence
    ) -> float:

        try:

            confidence = float(
                confidence
            )

        except (
            TypeError,
            ValueError
        ):

            return self.default_confidence

        if not math.isfinite(
            confidence
        ):

            return self.default_confidence

        # Convert 0-1 representation to 0-100.
        if 0 <= confidence <= 1:
            confidence *= 100

        return self._clamp_confidence(
            confidence
        )

    # ============================================================

    def _clamp_confidence(
        self,
        confidence
    ) -> float:

        try:

            confidence = float(
                confidence
            )

        except (
            TypeError,
            ValueError
        ):

            confidence = self.default_confidence

        if not math.isfinite(
            confidence
        ):

            confidence = self.default_confidence

        confidence = max(
            self.MIN_CONFIDENCE,
            min(
                self.MAX_CONFIDENCE,
                confidence
            )
        )

        return round(
            confidence
        )

    # ============================================================
    # SIGNAL DETECTION
    # ============================================================

    def detect_learning_signals(
        self,
        message
    ) -> Dict[str, Any]:

        text = (
            self._normalize_text(
                message
            )
            .lower()
        )

        if not text:

            return self._empty_signals()

        # --------------------------------------------------------
        # Phrase groups
        # --------------------------------------------------------

        confusion_phrases = [

            "i don't understand",
            "i do not understand",
            "i don't get it",
            "i do not get it",
            "i'm confused",
            "i am confused",
            "i'm lost",
            "i am lost",
            "too difficult",
            "too hard",
            "this is difficult",
            "this is hard",
            "i can't understand",
            "i cannot understand",
            "i still don't understand",
            "i still do not understand",
            "i still don't get it",
            "i still do not get it"
        ]

        frustration_phrases = [

            "this makes no sense",
            "nothing makes sense",
            "i hate this",
            "i can't do this",
            "i cannot do this",
            "i'm stuck",
            "i am stuck",
            "i keep getting it wrong",
            "i keep getting this wrong"
        ]

        understanding_phrases = [

            "i understand",
            "i do understand",
            "i get it",
            "i get it now",
            "i understand now",
            "that makes sense",
            "this makes sense",
            "now i understand",
            "now i get it",
            "i see",
            "i see now"
        ]

        simplification_phrases = [

            "explain simply",
            "explain it simply",
            "make it simple",
            "simplify",
            "simple explanation",
            "easy words",
            "in simple words",
            "explain like i'm new"
        ]

        depth_phrases = [

            "go deeper",
            "explain deeply",
            "more advanced",
            "more detail",
            "technical details",
            "technical explanation",
            "why exactly",
            "in depth",
            "deeper explanation"
        ]

        example_phrases = [

            "give me an example",
            "give an example",
            "real life example",
            "show me an example",
            "example please"
        ]

        practice_phrases = [

            "give me an exercise",
            "give me a problem",
            "give me a question",
            "let me practice",
            "i want to practice",
            "quiz me",
            "test me",
            "give me practice"
        ]

        help_phrases = [

            "help me",
            "i need help",
            "can you help",
            "help"
        ]

        # --------------------------------------------------------
        # Detection
        # --------------------------------------------------------

        confusion = self._contains_any(
            text,
            confusion_phrases
        )

        frustration = self._contains_any(
            text,
            frustration_phrases
        )

        understanding = self._contains_any(
            text,
            understanding_phrases
        )

        simplification = self._contains_any(
            text,
            simplification_phrases
        )

        depth_request = self._contains_any(
            text,
            depth_phrases
        )

        example_request = self._contains_any(
            text,
            example_phrases
        )

        practice_request = self._contains_any(
            text,
            practice_phrases
        )

        help_request = self._contains_any(
            text,
            help_phrases
        )

        # --------------------------------------------------------
        # Question detection
        # --------------------------------------------------------

        question = (
            "?" in text
            or text.startswith(
                (
                    "why ",
                    "how ",
                    "what ",
                    "when ",
                    "where ",
                    "who "
                )
            )
        )

        # --------------------------------------------------------
        # Explicit request priority
        # --------------------------------------------------------

        return {

            "confusion":
                confusion,

            "frustration":
                frustration,

            "understanding":
                understanding,

            "simplification_request":
                simplification,

            "depth_request":
                depth_request,

            "example_request":
                example_request,

            "practice_request":
                practice_request,

            "help_request":
                help_request,

            "question":
                question,

            "neutral":
                not any([
                    confusion,
                    frustration,
                    understanding,
                    simplification,
                    depth_request,
                    example_request,
                    practice_request,
                    help_request
                ])
        }

    # ============================================================

    def _empty_signals(
        self
    ) -> Dict[str, Any]:

        return {

            "confusion": False,
            "frustration": False,
            "understanding": False,
            "simplification_request": False,
            "depth_request": False,
            "example_request": False,
            "practice_request": False,
            "help_request": False,
            "question": False,
            "neutral": True
        }

    # ============================================================

    def _contains_any(
        self,
        text,
        phrases
    ) -> bool:

        return any(
            phrase in text
            for phrase in phrases
        )

    # ============================================================
    # SIGNAL ADJUSTMENT
    # ============================================================

    def _apply_signal_adjustments(
        self,
        confidence,
        signals
    ) -> float:

        adjustment = 0

        if signals.get(
            "confusion"
        ):
            adjustment -= (
                self.CONFUSION_PENALTY
            )

        if signals.get(
            "frustration"
        ):
            adjustment -= (
                self.FRUSTRATION_PENALTY
            )

        if signals.get(
            "clarification_request"
        ):
            adjustment -= (
                self.CLARIFICATION_PENALTY
            )

        if signals.get(
            "understanding"
        ):
            adjustment += (
                self.UNDERSTANDING_BONUS
            )

        if signals.get(
            "practice_request"
        ):
            adjustment += (
                self.SUCCESS_BONUS
            )

        return self._clamp_confidence(
            confidence + adjustment
        )

    # ============================================================
    # TREND ANALYSIS
    # ============================================================

    def analyze_trend(
        self,
        history,
        subject=None,
        topic=None
    ) -> Dict[str, Any]:

        history = (
            self._normalize_history(
                history
            )
        )

        values = []

        # --------------------------------------------------------
        # Read entry history.
        # --------------------------------------------------------

        entries = history.get(
            "entries"
        )

        if isinstance(
            entries,
            list
        ):

            for entry in entries:

                if not isinstance(
                    entry,
                    dict
                ):
                    continue

                entry_subject = (
                    self.normalize_subject(
                        entry.get(
                            "subject"
                        )
                    )
                )

                if (
                    subject
                    and entry_subject
                    and entry_subject != subject
                ):
                    continue

                entry_topic = (
                    self._normalize_text(
                        entry.get(
                            "topic"
                        )
                    )
                )

                if (
                    topic
                    and entry_topic
                    and entry_topic.lower()
                    != topic.lower()
                ):
                    continue

                confidence = (
                    entry.get(
                        "confidence"
                    )
                )

                if confidence is None:
                    continue

                values.append(
                    self._normalize_confidence(
                        confidence
                    )
                )

        # --------------------------------------------------------
        # Direct confidence history.
        # --------------------------------------------------------

        if not values:

            subject_data = history.get(
                subject
            )

            if isinstance(
                subject_data,
                dict
            ):

                raw_values = (
                    subject_data.get(
                        "confidence_history"
                    )
                )

                if isinstance(
                    raw_values,
                    list
                ):

                    for value in raw_values:

                        values.append(
                            self._normalize_confidence(
                                value
                            )
                        )

        # --------------------------------------------------------
        # Not enough data.
        # --------------------------------------------------------

        if len(values) < 2:

            return {

                "direction":
                    "stable",

                "strength":
                    "unknown",

                "change":
                    0,

                "samples":
                    len(values),

                "recent":
                    values[-5:],

                "reliable":
                    False
            }

        recent = values[
            -min(
                5,
                len(values)
            ):
        ]

        old_average = (
            sum(
                values[
                    :-len(recent)
                ]
            )
            / max(
                1,
                len(
                    values[
                        :-len(recent)
                    ]
                )
            )
        )

        recent_average = (
            sum(recent)
            / len(recent)
        )

        change = (
            recent_average
            - old_average
        )

        # --------------------------------------------------------
        # Direction
        # --------------------------------------------------------

        if change >= 8:

            direction = "improving"

        elif change <= -8:

            direction = "declining"

        else:

            direction = "stable"

        # --------------------------------------------------------
        # Strength
        # --------------------------------------------------------

        magnitude = abs(
            change
        )

        if magnitude >= 20:

            strength = "strong"

        elif magnitude >= 10:

            strength = "moderate"

        elif magnitude >= 5:

            strength = "weak"

        else:

            strength = "minimal"

        return {

            "direction":
                direction,

            "strength":
                strength,

            "change":
                round(
                    change,
                    1
                ),

            "samples":
                len(values),

            "recent":
                recent,

            "reliable":
                len(values) >= 3
        }

    # ============================================================
    # TREND ADJUSTMENT
    # ============================================================

    def _apply_trend_adjustment(
        self,
        confidence,
        trend
    ) -> float:

        if not isinstance(
            trend,
            dict
        ):
            return confidence

        direction = trend.get(
            "direction"
        )

        strength = trend.get(
            "strength"
        )

        adjustment = 0

        if direction == "improving":

            if strength == "strong":
                adjustment += 5

            elif strength == "moderate":
                adjustment += 3

            elif strength == "weak":
                adjustment += 1

        elif direction == "declining":

            if strength == "strong":
                adjustment -= 5

            elif strength == "moderate":
                adjustment -= 3

            elif strength == "weak":
                adjustment -= 1

        return self._clamp_confidence(
            confidence + adjustment
        )

    # ============================================================
    # PROFILE ADJUSTMENT
    # ============================================================

    def _calculate_profile_adjustment(
        self,
        student,
        subject,
        topic
    ) -> float:

        adjustment = 0

        strengths = (
            self._normalize_list(
                student.get(
                    "strengths"
                )
            )
        )

        weaknesses = (
            self._normalize_list(
                student.get(
                    "weaknesses"
                )
            )
        )

        normalized_subject = (
            self.normalize_subject(
                subject
            )
        )

        normalized_topic = (
            self._normalize_text(
                topic
            ).lower()
        )

        # --------------------------------------------------------
        # Strength matching
        # --------------------------------------------------------

        for strength in strengths:

            text = str(
                strength
            ).lower()

            if (
                normalized_subject
                and normalized_subject in text
            ):
                adjustment += 4

            if (
                normalized_topic
                and normalized_topic in text
            ):
                adjustment += 3

        # --------------------------------------------------------
        # Weakness matching
        # --------------------------------------------------------

        for weakness in weaknesses:

            text = str(
                weakness
            ).lower()

            if (
                normalized_subject
                and normalized_subject in text
            ):
                adjustment -= 5

            if (
                normalized_topic
                and normalized_topic in text
            ):
                adjustment -= 4

        return max(
            -10,
            min(
                10,
                adjustment
            )
        )

    # ============================================================
    # LEARNING STATE
    # ============================================================

    def _determine_learning_state(
        self,
        confidence,
        signals=None,
        trend=None
    ) -> str:

        signals = (
            signals
            if isinstance(
                signals,
                dict
            )
            else {}
        )

        trend = (
            trend
            if isinstance(
                trend,
                dict
            )
            else {}
        )

        if signals.get(
            "confusion"
        ):

            if confidence < 45:
                return "struggling"

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

        # A single high score should not automatically
        # be interpreted as mastery if the trend is unstable.

        if (
            trend.get("direction")
            == "declining"
            and trend.get("strength")
            in {"strong", "moderate"}
        ):

            return "strong"

        return "mastery"

    # ============================================================
    # DIFFICULTY
    # ============================================================

    def _determine_difficulty(
        self,
        confidence,
        student_level,
        signals
    ) -> str:

        # Explicit confusion always wins over theoretical
        # confidence.

        if signals.get(
            "confusion"
        ):

            return "beginner"

        if signals.get(
            "simplification_request"
        ):

            return "beginner"

        if confidence < 30:
            return "beginner"

        if confidence < 50:
            return "easy"

        if confidence < 70:
            return "medium"

        if confidence < 85:
            return "advanced"

        if student_level in {
            "beginner",
            "elementary"
        }:

            return "advanced"

        return "expert"

    # ============================================================
    # BASE APPROACH
    # ============================================================

    def _build_base_approach(
        self,
        confidence,
        learning_state,
        signals
    ) -> List[str]:

        approach = []

        if signals.get(
            "simplification_request"
        ):

            approach.extend([

                "Use very simple language.",

                "Reduce the number of ideas introduced at once.",

                "Avoid unnecessary technical vocabulary."
            ])

        elif signals.get(
            "depth_request"
        ):

            approach.extend([

                "Increase conceptual depth.",

                "Explain important reasoning rather than only the conclusion.",

                "Introduce technical terminology when useful."
            ])

        elif learning_state == "struggling":

            approach.extend([

                "Start from the most basic prerequisite.",

                "Explain one idea at a time.",

                "Use very simple vocabulary.",

                "Check understanding before adding complexity."
            ])

        elif learning_state == "weak":

            approach.extend([

                "Review the fundamental idea first.",

                "Use a concrete example.",

                "Connect the idea to something familiar."
            ])

        elif learning_state == "developing":

            approach.extend([

                "Explain the concept clearly.",

                "Connect the new idea to previous knowledge.",

                "Show the reasoning behind the answer."
            ])

        elif learning_state == "understanding":

            approach.extend([

                "Build on existing understanding.",

                "Explain why the concept works.",

                "Use examples to reinforce the idea."
            ])

        elif learning_state == "strong":

            approach.extend([

                "Avoid repeating basic information.",

                "Introduce deeper connections.",

                "Use more precise terminology."
            ])

        elif learning_state == "mastery":

            approach.extend([

                "Focus on advanced reasoning.",

                "Explore difficult applications.",

                "Connect the concept to related ideas."
            ])

        return approach

    # ============================================================
    # SUBJECT STRATEGY
    # ============================================================

    def _build_subject_strategy(
        self,
        subject
    ) -> List[str]:

        strategies = {

            "math": [

                "Show the mathematical method clearly.",

                "Explain why each important step is performed.",

                "Separate the method from the final result.",

                "Check arithmetic and logical consistency."
            ],

            "physics": [

                "Connect equations to physical meaning.",

                "Explain relationships between quantities.",

                "Use real-world physical situations.",

                "Clarify units and assumptions when relevant."
            ],

            "chemistry": [

                "Define important chemical vocabulary.",

                "Connect microscopic particles to observable effects.",

                "Explain reactions logically.",

                "Explain what chemical equations represent."
            ],

            "biology": [

                "Explain biological processes in logical stages.",

                "Connect structures to their functions.",

                "Explain interactions between parts of a system.",

                "Use concrete biological examples."
            ],

            "history": [

                "Keep chronology clear.",

                "Explain causes and consequences.",

                "Separate major events from minor details.",

                "Distinguish facts from interpretation."
            ],

            "geography": [

                "Connect concepts to real locations.",

                "Explain relationships between people and environments.",

                "Use spatial reasoning where useful.",

                "Connect geographical causes to consequences."
            ],

            "programming": [

                "Explain what the code is doing.",

                "Identify the source of errors precisely.",

                "Prefer simple maintainable solutions.",

                "Explain important logic rather than only giving code."
            ],

            "english": [

                "Use clear language examples.",

                "Explain grammar or vocabulary in context.",

                "Distinguish rules from exceptions.",

                "Show how the concept is used naturally."
            ],

            "french": [

                "Use simple examples in context.",

                "Explain grammar clearly.",

                "Distinguish common usage from formal rules.",

                "Correct mistakes while explaining the reason."
            ]
        }

        return strategies.get(
            subject,
            [
                "Adapt the explanation to the student's current level.",

                "Focus on understanding rather than memorization.",

                "Use examples when they improve clarity."
            ]
        )

    # ============================================================
    # TOPIC STRATEGY
    # ============================================================

    def _build_topic_strategy(
        self,
        topic,
        confidence
    ) -> List[str]:

        if not topic:
            return []

        if confidence < 40:

            return [

                f"Break '{topic}' into smaller ideas.",

                f"Identify the prerequisite knowledge for '{topic}'.",

                f"Build understanding of '{topic}' before adding complexity."
            ]

        if confidence < 70:

            return [

                f"Connect '{topic}' to related concepts.",

                f"Use an example that makes '{topic}' concrete.",

                f"Explain the reasoning behind '{topic}'."
            ]

        return [

            f"Explore deeper applications of '{topic}'.",

            f"Connect '{topic}' to more advanced concepts.",

            f"Use challenging examples involving '{topic}'."
        ]

    # ============================================================
    # TREND STRATEGY
    # ============================================================

    def _build_trend_strategy(
        self,
        trend
    ) -> List[str]:

        if not isinstance(
            trend,
            dict
        ):
            return []

        direction = trend.get(
            "direction"
        )

        strength = trend.get(
            "strength"
        )

        if direction == "improving":

            return [

                "Gradually increase difficulty as understanding improves."
            ]

        if direction == "declining":

            if strength in {
                "strong",
                "moderate"
            }:

                return [

                    "Reduce difficulty temporarily.",

                    "Reinforce the fundamentals.",

                    "Check whether a prerequisite concept is causing difficulty."
                ]

            return [

                "Monitor understanding before increasing difficulty."
            ]

        return [

            "Maintain the current level unless the student's message indicates a need to change."
        ]

    # ============================================================
    # PROFILE STRATEGY
    # ============================================================

    def _build_profile_strategy(
        self,
        student,
        subject,
        topic
    ) -> List[str]:

        strengths = (
            self._normalize_list(
                student.get(
                    "strengths"
                )
            )
        )

        weaknesses = (
            self._normalize_list(
                student.get(
                    "weaknesses"
                )
            )
        )

        approach = []

        subject_text = (
            self._normalize_text(
                subject
            ).lower()
        )

        topic_text = (
            self._normalize_text(
                topic
            ).lower()
        )

        for weakness in weaknesses:

            weakness_text = (
                str(
                    weakness
                ).lower()
            )

            if (
                subject_text
                and subject_text in weakness_text
            ) or (
                topic_text
                and topic_text in weakness_text
            ):

                approach.append(
                    "Pay extra attention to the student's known weakness in this area."
                )

        for strength in strengths:

            strength_text = (
                str(
                    strength
                ).lower()
            )

            if (
                subject_text
                and subject_text in strength_text
            ):

                approach.append(
                    "Use the student's existing strength as a bridge to the new concept."
                )

        return approach

    # ============================================================
    # EXPLANATION DEPTH
    # ============================================================

    def _determine_explanation_depth(
        self,
        confidence,
        signals
    ) -> str:

        if signals.get(
            "simplification_request"
        ):
            return "very_basic"

        if signals.get(
            "depth_request"
        ):
            return "advanced"

        if confidence < 30:
            return "very_basic"

        if confidence < 50:
            return "basic"

        if confidence < 70:
            return "balanced"

        if confidence < 85:
            return "deep"

        return "advanced"

    # ============================================================
    # EXAMPLES
    # ============================================================

    def _should_use_examples(
        self,
        confidence,
        signals
    ) -> bool:

        if signals.get(
            "example_request"
        ):
            return True

        if confidence < 75:
            return True

        return False

    # ============================================================
    # ANALOGIES
    # ============================================================

    def _should_use_analogies(
        self,
        confidence,
        subject,
        signals
    ) -> bool:

        if signals.get(
            "simplification_request"
        ):
            return True

        if confidence < 50:
            return True

        if subject in {
            "physics",
            "biology",
            "chemistry"
        }:

            return confidence < 60

        return False

    # ============================================================
    # STEP BY STEP
    # ============================================================

    def _should_use_step_by_step(
        self,
        confidence,
        subject,
        signals
    ) -> bool:

        if signals.get(
            "confusion"
        ):
            return True

        if signals.get(
            "simplification_request"
        ):
            return True

        if confidence < 60:
            return True

        if subject in {
            "math",
            "chemistry",
            "physics",
            "programming"
        }:

            return confidence < 75

        return False

    # ============================================================
    # HINTS
    # ============================================================

    def _should_use_hints(
        self,
        confidence,
        signals,
        settings
    ) -> bool:

        configured = settings.get(
            "hints",
            "when_needed"
        )

        if configured == "never":
            return False

        if configured == "always":
            return True

        if signals.get(
            "practice_request"
        ):
            return True

        return confidence < 60

    # ============================================================
    # REINFORCEMENT
    # ============================================================

    def _needs_reinforcement(
        self,
        confidence,
        signals,
        trend
    ) -> bool:

        if signals.get(
            "confusion"
        ):
            return True

        if confidence < 55:
            return True

        if (
            trend.get("direction")
            == "declining"
        ):

            return True

        return False

    # ============================================================
    # PRACTICE
    # ============================================================

    def _should_practice(
        self,
        confidence,
        signals,
        learning_state
    ) -> bool:

        if signals.get(
            "practice_request"
        ):
            return True

        if learning_state in {
            "understanding",
            "strong"
        }:

            return confidence >= 60

        return False

    # ============================================================
    # RETRIEVAL
    # ============================================================

    def _should_use_retrieval(
        self,
        confidence,
        learning_state,
        signals
    ) -> bool:

        if signals.get(
            "confusion"
        ):
            return False

        return learning_state in {
            "understanding",
            "strong",
            "mastery"
        }

    # ============================================================
    # CHALLENGE
    # ============================================================

    def _should_challenge(
        self,
        confidence,
        signals,
        trend,
        student_level
    ) -> bool:

        # Explicit requests can override normal thresholds.
        if signals.get(
            "depth_request"
        ):

            return confidence >= 60

        if signals.get(
            "confusion"
        ):

            return False

        if (
            trend.get("direction")
            == "declining"
        ):

            return False

        if student_level == "beginner":
            return confidence >= 85

        return confidence >= 75

    # ============================================================
    # CHALLENGE LEVEL
    # ============================================================

    def _determine_challenge_level(
        self,
        confidence,
        challenge
    ) -> str:

        if not challenge:
            return "none"

        if confidence < 65:
            return "small"

        if confidence < 80:
            return "moderate"

        if confidence < 90:
            return "difficult"

        return "expert"

    # ============================================================
    # CHECK UNDERSTANDING
    # ============================================================

    def _should_check_understanding(
        self,
        confidence,
        signals,
        learning_state
    ) -> bool:

        if signals.get(
            "confusion"
        ):
            return True

        if learning_state in {
            "struggling",
            "weak",
            "developing"
        }:

            return True

        if confidence < 70:
            return True

        return False

    # ============================================================
    # TEACHING STYLE
    # ============================================================

    def _determine_teaching_style(
        self,
        confidence,
        student_level,
        settings,
        signals
    ) -> str:

        configured = (
            settings.get(
                "teaching_style"
            )
        )

        if isinstance(
            configured,
            str
        ):

            configured = (
                configured
                .strip()
                .lower()
            )

            if configured in self.teaching_styles:

                if configured != "adaptive":
                    return configured

        if signals.get(
            "confusion"
        ):
            return "step_by_step"

        if confidence < 40:
            return "step_by_step"

        if confidence < 70:
            return "adaptive"

        if confidence < 85:
            return "conceptual"

        return "practical"

    # ============================================================
    # RESPONSE STYLE
    # ============================================================

    def _determine_response_style(
        self,
        confidence,
        student_level,
        signals
    ) -> str:

        if signals.get(
            "simplification_request"
        ):
            return "simple_supportive"

        if signals.get(
            "depth_request"
        ):
            return "deep_instructional"

        if signals.get(
            "confusion"
        ):
            return "simple_supportive"

        if confidence < 40:
            return "simple_supportive"

        if confidence < 70:
            return "clear_instructional"

        if confidence < 85:
            return "deep_instructional"

        return "challenging"

    # ============================================================
    # ACTIONS
    # ============================================================

    def _build_actions(
        self,
        confidence,
        learning_state,
        use_examples,
        use_analogies,
        step_by_step,
        use_hints,
        reinforcement,
        practice,
        retrieval,
        challenge,
        check_understanding
    ) -> List[str]:

        actions = []

        if reinforcement:
            actions.append(
                "reinforce_fundamentals"
            )

        if step_by_step:
            actions.append(
                "teach_step_by_step"
            )

        if use_examples:
            actions.append(
                "use_example"
            )

        if use_analogies:
            actions.append(
                "use_analogy_if_helpful"
            )

        if use_hints:
            actions.append(
                "offer_hint_when_needed"
            )

        if practice:
            actions.append(
                "encourage_practice"
            )

        if retrieval:
            actions.append(
                "use_retrieval_practice"
            )

        if challenge:
            actions.append(
                "add_reasoning_challenge"
            )

        if check_understanding:
            actions.append(
                "check_understanding"
            )

        if learning_state == "mastery":
            actions.append(
                "avoid_basic_repetition"
            )

        return actions

    # ============================================================
    # REASONS
    # ============================================================

    def _build_reasons(
        self,
        confidence,
        learning_state,
        signals,
        trend,
        subject,
        topic
    ) -> List[str]:

        reasons = []

        reasons.append(
            f"Estimated confidence is {confidence}/100."
        )

        reasons.append(
            f"Current learning state is '{learning_state}'."
        )

        if subject:
            reasons.append(
                f"Current subject is '{subject}'."
            )

        if topic:
            reasons.append(
                f"Current topic is '{topic}'."
            )

        if signals.get(
            "confusion"
        ):

            reasons.append(
                "The student's message contains a confusion signal."
            )

        if signals.get(
            "simplification_request"
        ):

            reasons.append(
                "The student explicitly requested a simpler explanation."
            )

        if signals.get(
            "depth_request"
        ):

            reasons.append(
                "The student explicitly requested greater depth."
            )

        if signals.get(
            "example_request"
        ):

            reasons.append(
                "The student requested an example."
            )

        if signals.get(
            "practice_request"
        ):

            reasons.append(
                "The student appears to want active practice."
            )

        direction = trend.get(
            "direction"
        )

        if direction == "improving":

            reasons.append(
                "Recent learning history suggests improvement."
            )

        elif direction == "declining":

            reasons.append(
                "Recent learning history suggests declining confidence."
            )

        return self._limit_unique(
            reasons,
            self.MAX_REASONS
        )

    # ============================================================
    # RECOMMENDATIONS
    # ============================================================

    def _build_recommendations(
        self,
        confidence,
        learning_state,
        challenge,
        reinforcement,
        practice,
        check_understanding
    ) -> List[str]:

        recommendations = []

        if reinforcement:

            recommendations.append(
                "Prioritize foundational understanding before increasing difficulty."
            )

        if learning_state in {
            "struggling",
            "weak"
        }:

            recommendations.append(
                "Reduce cognitive load and introduce fewer ideas at once."
            )

        if learning_state == "developing":

            recommendations.append(
                "Use examples and connect the new concept to existing knowledge."
            )

        if learning_state in {
            "strong",
            "mastery"
        }:

            recommendations.append(
                "Avoid unnecessary repetition of concepts already understood."
            )

        if practice:

            recommendations.append(
                "Use an exercise or short application to reinforce understanding."
            )

        if check_understanding:

            recommendations.append(
                "Use a brief understanding check before moving to harder material."
            )

        if challenge:

            recommendations.append(
                "A controlled challenge is appropriate."
            )

        return self._limit_unique(
            recommendations,
            self.MAX_RECOMMENDATIONS
        )

    # ============================================================
    # CONFIDENCE QUALITY
    # ============================================================

    def _confidence_quality(
        self,
        understanding,
        knowledge,
        history
    ) -> str:

        sources = 0

        if understanding:
            sources += 1

        if knowledge:
            sources += 1

        if history:
            sources += 1

        if sources >= 3:
            return "high"

        if sources == 2:
            return "moderate"

        if sources == 1:
            return "limited"

        return "default"

    # ============================================================
    # DATA SOURCES
    # ============================================================

    def _get_data_sources(
        self,
        understanding,
        knowledge,
        history
    ) -> List[str]:

        sources = []

        if understanding:
            sources.append(
                "understanding"
            )

        if knowledge:
            sources.append(
                "knowledge_map"
            )

        if history:
            sources.append(
                "history"
            )

        if not sources:
            sources.append(
                "default"
            )

        return sources

    # ============================================================
    # INTERNAL HISTORY
    # ============================================================

    def _record_internal_analysis(
        self,
        subject,
        topic,
        confidence,
        learning_state,
        trend
    ):

        if not subject:
            return

        if subject not in self.history:

            self.history[
                subject
            ] = []

        entry = {

            "topic":
                topic,

            "confidence":
                confidence,

            "learning_state":
                learning_state,

            "trend":
                trend.get(
                    "direction",
                    "stable"
                )
        }

        self.history[
            subject
        ].append(
            entry
        )

        if len(
            self.history[subject]
        ) > self.MAX_HISTORY_ITEMS:

            self.history[
                subject
            ] = self.history[
                subject
            ][
                -self.MAX_HISTORY_ITEMS:
            ]

    # ============================================================
    # QUICK CONFIDENCE
    # ============================================================

    def get_confidence(
        self,
        subject,
        understanding
    ) -> float:

        understanding = (
            self._normalize_dict(
                understanding
            )
        )

        subject = (
            self.normalize_subject(
                subject
            )
        )

        return self._get_subject_confidence(
            understanding,
            subject
        )

    # ============================================================
    # QUICK TOPIC CONFIDENCE
    # ============================================================

    def get_topic_confidence(
        self,
        subject,
        topic,
        understanding
    ) -> float:

        understanding = (
            self._normalize_dict(
                understanding
            )
        )

        subject = (
            self.normalize_subject(
                subject
            )
        )

        subject_confidence = (
            self._get_subject_confidence(
                understanding,
                subject
            )
        )

        return self._get_topic_confidence(
            understanding,
            subject,
            topic,
            subject_confidence
        )

    # ============================================================
    # QUICK LEARNING STATE
    # ============================================================

    def get_learning_state(
        self,
        confidence
    ) -> str:

        confidence = (
            self._normalize_confidence(
                confidence
            )
        )

        return self._determine_learning_state(
            confidence
        )

    # ============================================================
    # QUICK DIFFICULTY
    # ============================================================

    def get_difficulty(
        self,
        confidence,
        student_level="beginner"
    ) -> str:

        confidence = (
            self._normalize_confidence(
                confidence
            )
        )

        signals = self._empty_signals()

        return self._determine_difficulty(
            confidence,
            student_level,
            signals
        )

    # ============================================================
    # QUICK EXPLANATION DEPTH
    # ============================================================

    def get_explanation_depth(
        self,
        confidence
    ) -> str:

        confidence = (
            self._normalize_confidence(
                confidence
            )
        )

        return self._determine_explanation_depth(
            confidence,
            self._empty_signals()
        )

    # ============================================================
    # QUICK TEACHING STYLE
    # ============================================================

    def get_teaching_style(
        self,
        confidence,
        student_level="beginner"
    ) -> str:

        confidence = (
            self._normalize_confidence(
                confidence
            )
        )

        return self._determine_teaching_style(
            confidence,
            student_level,
            {},
            self._empty_signals()
        )

    # ============================================================
    # SUBJECT STRATEGY PUBLIC METHOD
    # ============================================================

    def get_subject_strategy(
        self,
        subject
    ) -> List[str]:

        subject = (
            self.normalize_subject(
                subject
            )
        )

        return self._build_subject_strategy(
            subject
        )

    # ============================================================
    # SIGNAL ANALYSIS PUBLIC METHOD
    # ============================================================

    def analyze_message(
        self,
        message
    ) -> Dict[str, Any]:

        return self.detect_learning_signals(
            message
        )

    # ============================================================
    # STRATEGY VALIDATION
    # ============================================================

    def validate_strategy(
        self,
        strategy
    ) -> Dict[str, Any]:

        if not isinstance(
            strategy,
            dict
        ):

            return {
                "confidence":
                    self.default_confidence,

                "learning_state":
                    "developing",

                "difficulty":
                    "medium",

                "approach":
                    []
            }

        result = dict(
            strategy
        )

        # --------------------------------------------------------
        # Confidence
        # --------------------------------------------------------

        result[
            "confidence"
        ] = self._normalize_confidence(
            result.get(
                "confidence",
                self.default_confidence
            )
        )

        # --------------------------------------------------------
        # Lists
        # --------------------------------------------------------

        for key in [
            "approach",
            "actions",
            "recommendations",
            "reasons"
        ]:

            value = result.get(
                key,
                []
            )

            if not isinstance(
                value,
                list
            ):

                value = [
                    str(value)
                ]

            result[key] = (
                self._limit_unique(
                    value,
                    self.MAX_APPROACH_ITEMS
                )
            )

        # --------------------------------------------------------
        # Boolean fields
        # --------------------------------------------------------

        for key in [

            "use_examples",
            "use_analogies",
            "step_by_step",
            "use_hints",
            "check_understanding",
            "reinforcement",
            "practice",
            "retrieval",
            "challenge"
        ]:

            result[key] = bool(
                result.get(
                    key,
                    False
                )
            )

        # --------------------------------------------------------
        # Consistency fixes
        # --------------------------------------------------------

        if result[
            "confidence"
        ] < 50:

            result[
                "challenge"
            ] = False

        if result[
            "confidence"
        ] < 40:

            result[
                "reinforcement"
            ] = True

            result[
                "step_by_step"
            ] = True

        if result[
            "challenge"
        ]:

            result[
                "challenge_level"
            ] = self._determine_challenge_level(
                result[
                    "confidence"
                ],
                True
            )

        else:

            result[
                "challenge_level"
            ] = "none"

        return result

    # ============================================================
    # LIST UTILITIES
    # ============================================================

    def _normalize_list(
        self,
        value
    ) -> List[Any]:

        if value is None:
            return []

        if isinstance(
            value,
            (list, tuple, set)
        ):

            return list(
                value
            )

        return [
            value
        ]

    # ============================================================

    def _combine_unique(
        self,
        *groups
    ) -> List[str]:

        result = []

        for group in groups:

            if not isinstance(
                group,
                (list, tuple, set)
            ):
                continue

            for item in group:

                if item is None:
                    continue

                text = str(
                    item
                ).strip()

                if not text:
                    continue

                if text not in result:

                    result.append(
                        text
                    )

                if len(result) >= (
                    self.MAX_APPROACH_ITEMS
                ):

                    return result

        return result

    # ============================================================

    def _limit_unique(
        self,
        values,
        limit
    ) -> List[str]:

        result = []

        if not isinstance(
            values,
            (list, tuple, set)
        ):
            return result

        for value in values:

            if value is None:
                continue

            text = str(
                value
            ).strip()

            if not text:
                continue

            if text not in result:

                result.append(
                    text
                )

            if len(result) >= limit:
                break

        return result

    # ============================================================
    # INTERNAL STATE ACCESS
    # ============================================================

    def get_history(
        self,
        subject=None
    ):

        if subject is None:

            return {
                key: list(value)
                for key, value
                in self.history.items()
            }

        subject = (
            self.normalize_subject(
                subject
            )
        )

        return list(
            self.history.get(
                subject,
                []
            )
        )

    # ============================================================
    # RESET
    # ============================================================

    def reset_history(
        self,
        subject=None
    ) -> None:

        if subject is None:

            self.history.clear()

            return

        subject = (
            self.normalize_subject(
                subject
            )
        )

        self.history.pop(
            subject,
            None
        )

    # ============================================================
    # DIAGNOSTIC REPORT
    # ============================================================

    def diagnose(
        self,
        student=None,
        subject=None,
        topic=None,
        understanding=None,
        message=None,
        history=None,
        knowledge=None,
        settings=None
    ) -> Dict[str, Any]:
        """
        Return a compact diagnostic report useful for debugging
        Nova's decision-making without exposing internal prompts
        to the LLM.
        """

        strategy = self.think(

            student=
                student,

            subject=
                subject,

            topic=
                topic,

            understanding=
                understanding,

            message=
                message,

            history=
                history,

            knowledge=
                knowledge,

            settings=
                settings
        )

        return {

            "brain_version":
                self.VERSION,

            "subject":
                strategy.get(
                    "subject"
                ),

            "topic":
                strategy.get(
                    "topic"
                ),

            "confidence":
                strategy.get(
                    "confidence"
                ),

            "learning_state":
                strategy.get(
                    "learning_state"
                ),

            "difficulty":
                strategy.get(
                    "difficulty"
                ),

            "teaching_style":
                strategy.get(
                    "teaching_style"
                ),

            "explanation_depth":
                strategy.get(
                    "explanation_depth"
                ),

            "challenge":
                strategy.get(
                    "challenge"
                ),

            "reinforcement":
                strategy.get(
                    "reinforcement"
                ),

            "trend":
                strategy.get(
                    "trend"
                ),

            "actions":
                strategy.get(
                    "actions",
                    []
                ),

            "reasons":
                strategy.get(
                    "reasons",
                    []
                )
        }