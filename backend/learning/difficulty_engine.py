from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import math
import re


class DifficultyEngine:
    """
    Nova's adaptive difficulty engine.

    The purpose of this class is to determine how difficult the
    next teaching interaction should be.

    The engine combines several signals:

        - current confidence
        - previous confidence
        - confidence trend
        - recent confusion
        - recent understanding
        - number of attempts
        - requested difficulty
        - learning state
        - previous difficulty
        - student performance
        - subject-specific history

    The engine produces a structured decision rather than only
    returning a difficulty string.

    ------------------------------------------------------------
    DIFFICULTY LEVELS
    ------------------------------------------------------------

    Detailed teaching levels:

        beginner
        intermediate
        advanced
        mastery

    Simplified tracking levels:

        easy
        medium
        hard

    ------------------------------------------------------------
    IMPORTANT DESIGN PRINCIPLE
    ------------------------------------------------------------

    Confidence is treated as a useful learning signal, not as
    an absolute measurement of the student's ability.

    The engine should therefore avoid making huge difficulty
    jumps from a single message.

    Example:

        confidence = 82

    does not automatically mean:

        "The student has mastered everything."

    Instead, it means:

        "The available evidence suggests that advanced
         material may currently be appropriate."

    ------------------------------------------------------------
    COMPATIBILITY
    ------------------------------------------------------------

    The existing NovaCore code can continue using:

        difficulty = engine.decide(confidence)

    The returned dictionary still contains:

        level
        tracking_level
        stage
        confidence
        instruction

    Additional fields are provided for the newer Nova systems.
    """

    # ============================================================
    # VERSION
    # ============================================================

    VERSION = "2.0"

    # ============================================================
    # DIFFICULTY LEVELS
    # ============================================================

    LEVEL_BEGINNER = "beginner"
    LEVEL_INTERMEDIATE = "intermediate"
    LEVEL_ADVANCED = "advanced"
    LEVEL_MASTERY = "mastery"

    LEVELS = (
        LEVEL_BEGINNER,
        LEVEL_INTERMEDIATE,
        LEVEL_ADVANCED,
        LEVEL_MASTERY,
    )

    # ============================================================
    # TRACKING LEVELS
    # ============================================================

    TRACKING_EASY = "easy"
    TRACKING_MEDIUM = "medium"
    TRACKING_HARD = "hard"

    # ============================================================
    # LEARNING STAGES
    # ============================================================

    STAGE_FOUNDATION = "foundation"
    STAGE_DEVELOPING = "developing"
    STAGE_STRONG = "strong"
    STAGE_MASTERY = "mastery"

    # ============================================================
    # CONFIDENCE THRESHOLDS
    # ============================================================

    BEGINNER_THRESHOLD = 40
    INTERMEDIATE_THRESHOLD = 70
    ADVANCED_THRESHOLD = 90

    # ============================================================
    # CONFIDENCE LIMITS
    # ============================================================

    MIN_CONFIDENCE = 0.0
    MAX_CONFIDENCE = 100.0

    DEFAULT_CONFIDENCE = 50.0

    # ============================================================
    # TREND SETTINGS
    # ============================================================

    STRONG_IMPROVEMENT = 8.0
    MODERATE_IMPROVEMENT = 3.0

    STRONG_DECLINE = -8.0
    MODERATE_DECLINE = -3.0

    # ============================================================
    # STABILITY SETTINGS
    # ============================================================

    MAX_HISTORY_PER_SUBJECT = 30

    # ============================================================
    # DIFFICULTY MOVEMENT
    # ============================================================

    MAX_LEVEL_JUMP = 1

    # ============================================================
    # INTERNAL WEIGHTS
    # ============================================================

    CONFIDENCE_WEIGHT = 0.60
    TREND_WEIGHT = 0.15
    PERFORMANCE_WEIGHT = 0.10
    SIGNAL_WEIGHT = 0.15

    # ============================================================
    # CONSTRUCTOR
    # ============================================================

    def __init__(
        self,
        default_confidence: float = DEFAULT_CONFIDENCE,
        max_history: int = MAX_HISTORY_PER_SUBJECT
    ):
        """
        Initialize the difficulty engine.

        Parameters
        ----------
        default_confidence:
            Confidence used when no valid confidence is supplied.

        max_history:
            Maximum number of historical decisions kept per subject.
        """

        self.default_confidence = self._normalize_confidence(
            default_confidence
        )

        try:
            max_history = int(max_history)
        except (TypeError, ValueError):
            max_history = self.MAX_HISTORY_PER_SUBJECT

        self.max_history = max(
            5,
            max_history
        )

        # Subject-specific history.
        #
        # Example:
        #
        # {
        #     "physics": [
        #         {...},
        #         {...}
        #     ]
        # }
        self.history: Dict[str, List[Dict[str, Any]]] = {}

        # Global statistics.
        self.statistics: Dict[str, int] = {
            "decisions": 0,
            "level_up": 0,
            "level_down": 0,
            "stable": 0,
            "invalid_inputs": 0,
        }

    # ============================================================
    # PUBLIC API
    # ============================================================

    def decide(
        self,
        confidence: Any,
        subject: Optional[str] = None,
        previous_confidence: Any = None,
        previous_level: Optional[str] = None,
        recent_signals: Any = None,
        attempts: Any = 0,
        performance: Any = None,
        requested_difficulty: Optional[str] = None,
        learning_state: Optional[str] = None,
        allow_mastery: bool = True
    ) -> Dict[str, Any]:
        """
        Determine the appropriate teaching difficulty.

        The original Nova API remains valid:

            decide(confidence)

        More advanced callers can provide additional context.

        Returns
        -------
        dict
            Structured difficulty decision.
        """

        # --------------------------------------------------------
        # SUBJECT
        # --------------------------------------------------------

        subject_key = self.normalize_subject(
            subject
        )

        # --------------------------------------------------------
        # CONFIDENCE
        # --------------------------------------------------------

        normalized_confidence = self.normalize_confidence(
            confidence
        )

        # --------------------------------------------------------
        # PREVIOUS CONFIDENCE
        # --------------------------------------------------------

        normalized_previous = None

        if previous_confidence is not None:

            normalized_previous = (
                self.normalize_confidence(
                    previous_confidence
                )
            )

        # --------------------------------------------------------
        # HISTORY
        # --------------------------------------------------------

        history = self.get_subject_history(
            subject_key
        )

        if normalized_previous is None:

            normalized_previous = (
                self.infer_previous_confidence(
                    history
                )
            )

        # --------------------------------------------------------
        # TREND
        # --------------------------------------------------------

        trend = self.calculate_trend(
            normalized_confidence,
            normalized_previous
        )

        # --------------------------------------------------------
        # SIGNALS
        # --------------------------------------------------------

        signal_data = self.analyze_signals(
            recent_signals
        )

        # --------------------------------------------------------
        # PERFORMANCE
        # --------------------------------------------------------

        performance_score = (
            self.normalize_performance(
                performance
            )
        )

        # --------------------------------------------------------
        # ATTEMPTS
        # --------------------------------------------------------

        attempts_value = self.normalize_attempts(
            attempts
        )

        # --------------------------------------------------------
        # BASE LEVEL
        # --------------------------------------------------------

        base_level = self.level_from_confidence(
            normalized_confidence,
            allow_mastery=allow_mastery
        )

        # --------------------------------------------------------
        # CALCULATE ADAPTIVE SCORE
        # --------------------------------------------------------

        adaptive_score = self.calculate_adaptive_score(

            confidence=
                normalized_confidence,

            trend=
                trend["value"],

            signal_score=
                signal_data["score"],

            performance=
                performance_score
        )

        # --------------------------------------------------------
        # ADAPTIVE LEVEL
        # --------------------------------------------------------

        adaptive_level = self.level_from_score(
            adaptive_score,
            allow_mastery=allow_mastery
        )

        # --------------------------------------------------------
        # APPLY LEARNING STATE
        # --------------------------------------------------------

        adaptive_level = (
            self.apply_learning_state(
                adaptive_level,
                learning_state
            )
        )

        # --------------------------------------------------------
        # APPLY REQUESTED DIFFICULTY
        # --------------------------------------------------------

        adaptive_level = (
            self.apply_requested_difficulty(
                adaptive_level,
                requested_difficulty
            )
        )

        # --------------------------------------------------------
        # APPLY CONFUSION PROTECTION
        # --------------------------------------------------------

        if signal_data["confusion"]:

            adaptive_level = (
                self.reduce_level(
                    adaptive_level,
                    steps=1
                )
            )

        # --------------------------------------------------------
        # PREVENT EXTREME JUMPS
        # --------------------------------------------------------

        if previous_level:

            adaptive_level = (
                self.limit_level_jump(
                    previous_level,
                    adaptive_level
                )
            )

        # --------------------------------------------------------
        # BUILD DECISION
        # --------------------------------------------------------

        decision = self.build_decision(
            level=adaptive_level,
            confidence=normalized_confidence,
            trend=trend,
            signal_data=signal_data,
            adaptive_score=adaptive_score,
            attempts=attempts_value,
            performance=performance_score,
            subject=subject_key,
            base_level=base_level,
            requested_difficulty=requested_difficulty
        )

        # --------------------------------------------------------
        # STORE HISTORY
        # --------------------------------------------------------

        self.record_decision(
            subject_key,
            decision
        )

        # --------------------------------------------------------
        # UPDATE STATISTICS
        # --------------------------------------------------------

        self.update_statistics(
            decision
        )

        return decision

    # ============================================================
    # CONFIDENCE NORMALIZATION
    # ============================================================

    def normalize_confidence(
        self,
        confidence: Any
    ) -> float:
        """
        Convert arbitrary confidence input into a value from
        0 to 100.

        Supported examples:

            75
            75.0
            "75"
            "75%"
            0.75

        Invalid values fall back to the configured default.
        """

        try:

            if isinstance(
                confidence,
                str
            ):

                text = confidence.strip()

                if not text:

                    raise ValueError

                text = text.replace(
                    "%",
                    ""
                )

                confidence = float(
                    text
                )

            else:

                confidence = float(
                    confidence
                )

        except (
            TypeError,
            ValueError,
            OverflowError
        ):

            self.statistics[
                "invalid_inputs"
            ] += 1

            return self.default_confidence

        if not math.isfinite(
            confidence
        ):

            self.statistics[
                "invalid_inputs"
            ] += 1

            return self.default_confidence

        # --------------------------------------------------------
        # SUPPORT 0-1 CONFIDENCE
        # --------------------------------------------------------

        if 0 <= confidence <= 1:

            confidence *= 100

        return max(
            self.MIN_CONFIDENCE,
            min(
                self.MAX_CONFIDENCE,
                confidence
            )
        )

    # ============================================================
    # LEGACY ALIAS
    # ============================================================

    def _normalize_confidence(
        self,
        confidence: Any
    ) -> float:

        try:

            value = float(
                confidence
            )

        except (
            TypeError,
            ValueError,
            OverflowError
        ):

            value = self.DEFAULT_CONFIDENCE

        if not math.isfinite(
            value
        ):

            value = self.DEFAULT_CONFIDENCE

        return max(
            self.MIN_CONFIDENCE,
            min(
                self.MAX_CONFIDENCE,
                value
            )
        )

    # ============================================================
    # SUBJECT NORMALIZATION
    # ============================================================

    def normalize_subject(
        self,
        subject: Any
    ) -> str:
        """
        Normalize a subject name so history remains consistent.
        """

        if subject is None:

            return "general"

        text = str(
            subject
        ).strip().lower()

        if not text:

            return "general"

        # Collapse multiple spaces.
        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text

    # ============================================================
    # ATTEMPTS
    # ============================================================

    def normalize_attempts(
        self,
        attempts: Any
    ) -> int:
        """
        Normalize attempt count.
        """

        try:

            value = int(
                attempts
            )

        except (
            TypeError,
            ValueError,
            OverflowError
        ):

            return 0

        return max(
            0,
            value
        )

    # ============================================================
    # PERFORMANCE
    # ============================================================

    def normalize_performance(
        self,
        performance: Any
    ) -> Optional[float]:
        """
        Normalize performance into 0-100.

        Returns None when no performance information exists.
        """

        if performance is None:

            return None

        # --------------------------------------------------------
        # NUMERIC
        # --------------------------------------------------------

        if isinstance(
            performance,
            (int, float)
        ):

            try:

                value = float(
                    performance
                )

            except (
                TypeError,
                ValueError
            ):

                return None

            if 0 <= value <= 1:

                value *= 100

            return max(
                0,
                min(
                    100,
                    value
                )
            )

        # --------------------------------------------------------
        # DICTIONARY
        # --------------------------------------------------------

        if isinstance(
            performance,
            dict
        ):

            for key in (
                "score",
                "confidence",
                "accuracy",
                "percentage"
            ):

                if key in performance:

                    return self.normalize_performance(
                        performance[key]
                    )

        return None

    # ============================================================
    # LEVEL FROM CONFIDENCE
    # ============================================================

    def level_from_confidence(
        self,
        confidence: float,
        allow_mastery: bool = True
    ) -> str:
        """
        Convert confidence into a basic teaching level.
        """

        confidence = self.normalize_confidence(
            confidence
        )

        if confidence < self.BEGINNER_THRESHOLD:

            return self.LEVEL_BEGINNER

        if confidence < self.INTERMEDIATE_THRESHOLD:

            return self.LEVEL_INTERMEDIATE

        if confidence < self.ADVANCED_THRESHOLD:

            return self.LEVEL_ADVANCED

        if allow_mastery:

            return self.LEVEL_MASTERY

        return self.LEVEL_ADVANCED

    # ============================================================
    # LEVEL FROM ADAPTIVE SCORE
    # ============================================================

    def level_from_score(
        self,
        score: float,
        allow_mastery: bool = True
    ) -> str:
        """
        Convert the adaptive score into a difficulty level.
        """

        return self.level_from_confidence(
            score,
            allow_mastery=allow_mastery
        )

    # ============================================================
    # ADAPTIVE SCORE
    # ============================================================

    def calculate_adaptive_score(
        self,
        confidence: float,
        trend: float = 0,
        signal_score: float = 0,
        performance: Optional[float] = None
    ) -> float:
        """
        Calculate a balanced adaptive score.

        Confidence remains the strongest signal.

        Trend, explicit student signals and performance can
        adjust the score without completely overriding it.
        """

        confidence = self.normalize_confidence(
            confidence
        )

        # --------------------------------------------------------
        # TREND NORMALIZATION
        # --------------------------------------------------------

        trend = max(
            -20,
            min(
                20,
                float(trend or 0)
            )
        )

        trend_component = (
            trend * 1.5
        )

        # --------------------------------------------------------
        # SIGNAL
        # --------------------------------------------------------

        signal_score = max(
            -20,
            min(
                20,
                float(signal_score or 0)
            )
        )

        # --------------------------------------------------------
        # PERFORMANCE
        # --------------------------------------------------------

        if performance is None:

            performance_component = 0

        else:

            performance_component = (
                performance - 50
            )

        # --------------------------------------------------------
        # COMBINE
        # --------------------------------------------------------

        score = (

            confidence
            + (
                trend_component
                * self.TREND_WEIGHT
            )
            + (
                signal_score
                * self.SIGNAL_WEIGHT
            )
            + (
                performance_component
                * self.PERFORMANCE_WEIGHT
            )
        )

        return max(
            0,
            min(
                100,
                score
            )
        )

    # ============================================================
    # TREND
    # ============================================================

    def calculate_trend(
        self,
        current: float,
        previous: Optional[float]
    ) -> Dict[str, Any]:
        """
        Calculate confidence movement.
        """

        current = self.normalize_confidence(
            current
        )

        if previous is None:

            return {
                "value": 0.0,
                "direction": "stable",
                "strength": "unknown"
            }

        previous = self.normalize_confidence(
            previous
        )

        difference = (
            current - previous
        )

        if difference >= self.STRONG_IMPROVEMENT:

            direction = "improving"
            strength = "strong"

        elif difference >= self.MODERATE_IMPROVEMENT:

            direction = "improving"
            strength = "moderate"

        elif difference <= self.STRONG_DECLINE:

            direction = "declining"
            strength = "strong"

        elif difference <= self.MODERATE_DECLINE:

            direction = "declining"
            strength = "moderate"

        else:

            direction = "stable"
            strength = "stable"

        return {
            "value": round(
                difference,
                2
            ),
            "direction": direction,
            "strength": strength
        }

    # ============================================================
    # SIGNAL ANALYSIS
    # ============================================================

    def analyze_signals(
        self,
        signals: Any
    ) -> Dict[str, Any]:
        """
        Analyze recent learning signals.

        Accepted examples:

            ["confusion", "neutral", "understanding"]

        or:

            {
                "confusion": 2,
                "understanding": 5
            }

        Recognized signals:

            confusion
            understanding
            clarification
            mistake
            success
            frustration
            confidence
            neutral
        """

        result = {
            "confusion": False,
            "understanding": False,
            "clarification": False,
            "success": False,
            "mistake": False,
            "frustration": False,
            "score": 0.0,
            "signals": []
        }

        if signals is None:

            return result

        # --------------------------------------------------------
        # DICTIONARY
        # --------------------------------------------------------

        if isinstance(
            signals,
            dict
        ):

            for key, value in signals.items():

                name = str(
                    key
                ).lower()

                try:

                    count = int(
                        value
                    )

                except (
                    TypeError,
                    ValueError
                ):

                    count = 1 if value else 0

                for _ in range(
                    max(
                        0,
                        count
                    )
                ):

                    result["signals"].append(
                        name
                    )

        # --------------------------------------------------------
        # LIST / TUPLE / SET
        # --------------------------------------------------------

        elif isinstance(
            signals,
            (list, tuple, set)
        ):

            for signal in signals:

                if signal is not None:

                    result["signals"].append(
                        str(
                            signal
                        ).strip().lower()
                    )

        # --------------------------------------------------------
        # STRING
        # --------------------------------------------------------

        else:

            result["signals"].append(
                str(
                    signals
                ).strip().lower()
            )

        # --------------------------------------------------------
        # SCORING
        # --------------------------------------------------------

        signal_weights = {

            "confusion": -10,

            "frustration": -8,

            "mistake": -6,

            "clarification": -2,

            "neutral": 0,

            "success": 7,

            "understanding": 8,

            "confidence": 8
        }

        total = 0

        for signal in result["signals"]:

            if signal in signal_weights:

                total += signal_weights[
                    signal
                ]

            if signal == "confusion":

                result["confusion"] = True

            elif signal == "understanding":

                result["understanding"] = True

            elif signal == "clarification":

                result["clarification"] = True

            elif signal == "success":

                result["success"] = True

            elif signal == "mistake":

                result["mistake"] = True

            elif signal == "frustration":

                result["frustration"] = True

        result["score"] = max(
            -20,
            min(
                20,
                total
            )
        )

        return result

    # ============================================================
    # LEARNING STATE
    # ============================================================

    def apply_learning_state(
        self,
        level: str,
        learning_state: Optional[str]
    ) -> str:
        """
        Adjust difficulty based on a broad learning state.
        """

        if not learning_state:

            return level

        state = str(
            learning_state
        ).strip().lower()

        # --------------------------------------------------------
        # STRUGGLING STATES
        # --------------------------------------------------------

        if state in {
            "struggling",
            "confused",
            "weak",
            "foundational",
            "beginner",
            "needs_support"
        }:

            return self.reduce_level(
                level,
                steps=1
            )

        # --------------------------------------------------------
        # STRONG STATES
        # --------------------------------------------------------

        if state in {
            "strong",
            "confident",
            "ready",
            "advanced"
        }:

            return self.increase_level(
                level,
                steps=1
            )

        # --------------------------------------------------------
        # MASTERY
        # --------------------------------------------------------

        if state in {
            "mastery",
            "mastered"
        }:

            return self.LEVEL_MASTERY

        return level

    # ============================================================
    # REQUESTED DIFFICULTY
    # ============================================================

    def apply_requested_difficulty(
        self,
        level: str,
        requested: Optional[str]
    ) -> str:
        """
        Respect an explicit difficulty request when possible.

        Student requests are treated as useful context, but
        safety and learning consistency remain more important.
        """

        if not requested:

            return level

        requested = str(
            requested
        ).strip().lower()

        aliases = {

            "easy":
                self.LEVEL_BEGINNER,

            "simple":
                self.LEVEL_BEGINNER,

            "beginner":
                self.LEVEL_BEGINNER,

            "medium":
                self.LEVEL_INTERMEDIATE,

            "moderate":
                self.LEVEL_INTERMEDIATE,

            "intermediate":
                self.LEVEL_INTERMEDIATE,

            "hard":
                self.LEVEL_ADVANCED,

            "difficult":
                self.LEVEL_ADVANCED,

            "advanced":
                self.LEVEL_ADVANCED,

            "mastery":
                self.LEVEL_MASTERY,

            "expert":
                self.LEVEL_MASTERY
        }

        requested_level = aliases.get(
            requested
        )

        if requested_level is None:

            return level

        return requested_level

    # ============================================================
    # LEVEL INDEX
    # ============================================================

    def level_index(
        self,
        level: Optional[str]
    ) -> int:
        """
        Return the numeric position of a difficulty level.
        """

        if level not in self.LEVELS:

            return 1

        return self.LEVELS.index(
            level
        )

    # ============================================================
    # LEVEL FROM INDEX
    # ============================================================

    def level_from_index(
        self,
        index: int
    ) -> str:
        """
        Convert a numeric difficulty position into a level.
        """

        try:

            index = int(
                index
            )

        except (
            TypeError,
            ValueError
        ):

            index = 1

        index = max(
            0,
            min(
                len(self.LEVELS) - 1,
                index
            )
        )

        return self.LEVELS[
            index
        ]

    # ============================================================
    # INCREASE LEVEL
    # ============================================================

    def increase_level(
        self,
        level: str,
        steps: int = 1
    ) -> str:
        """
        Increase difficulty safely.
        """

        current = self.level_index(
            level
        )

        return self.level_from_index(
            current + max(
                0,
                int(steps)
            )
        )

    # ============================================================
    # REDUCE LEVEL
    # ============================================================

    def reduce_level(
        self,
        level: str,
        steps: int = 1
    ) -> str:
        """
        Decrease difficulty safely.
        """

        current = self.level_index(
            level
        )

        return self.level_from_index(
            current - max(
                0,
                int(steps)
            )
        )

    # ============================================================
    # LIMIT LEVEL JUMP
    # ============================================================

    def limit_level_jump(
        self,
        previous_level: str,
        new_level: str
    ) -> str:
        """
        Prevent Nova from jumping through several difficulty
        levels after one interaction.

        Example:

            beginner -> mastery

        becomes:

            beginner -> intermediate
        """

        previous_index = self.level_index(
            previous_level
        )

        new_index = self.level_index(
            new_level
        )

        difference = (
            new_index - previous_index
        )

        if difference > self.MAX_LEVEL_JUMP:

            new_index = (
                previous_index
                + self.MAX_LEVEL_JUMP
            )

        elif difference < -self.MAX_LEVEL_JUMP:

            new_index = (
                previous_index
                - self.MAX_LEVEL_JUMP
            )

        return self.level_from_index(
            new_index
        )

    # ============================================================
    # TRACKING LEVEL
    # ============================================================

    def tracking_level(
        self,
        level: str
    ) -> str:
        """
        Convert detailed teaching difficulty into the simpler
        tracking categories used by learning statistics.
        """

        if level == self.LEVEL_BEGINNER:

            return self.TRACKING_EASY

        if level == self.LEVEL_INTERMEDIATE:

            return self.TRACKING_MEDIUM

        return self.TRACKING_HARD

    # ============================================================
    # LEARNING STAGE
    # ============================================================

    def learning_stage(
        self,
        level: str
    ) -> str:

        mapping = {

            self.LEVEL_BEGINNER:
                self.STAGE_FOUNDATION,

            self.LEVEL_INTERMEDIATE:
                self.STAGE_DEVELOPING,

            self.LEVEL_ADVANCED:
                self.STAGE_STRONG,

            self.LEVEL_MASTERY:
                self.STAGE_MASTERY
        }

        return mapping.get(
            level,
            self.STAGE_DEVELOPING
        )

    # ============================================================
    # BUILD INSTRUCTION
    # ============================================================

    def build_instruction(
        self,
        level: str,
        trend: Optional[Dict[str, Any]] = None,
        signals: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate detailed teaching instructions for the selected
        difficulty level.
        """

        instructions = {

            self.LEVEL_BEGINNER: (
                "Explain with simple, clear words. "
                "Break difficult ideas into small steps. "
                "Define important vocabulary. "
                "Use a concrete example when useful. "
                "Avoid unnecessary technical detail. "
                "Check the basic idea before moving to harder material."
            ),

            self.LEVEL_INTERMEDIATE: (
                "Explain clearly with moderate depth. "
                "Connect the new concept to ideas the student may "
                "already know. "
                "Use relevant examples. "
                "Introduce technical vocabulary when it improves "
                "precision. "
                "Show important reasoning without over-explaining "
                "basic material."
            ),

            self.LEVEL_ADVANCED: (
                "Explain the concept in greater depth. "
                "Use appropriate technical vocabulary. "
                "Discuss important relationships between concepts. "
                "Include more demanding examples or applications "
                "when useful. "
                "Avoid repeating basic material the student already "
                "appears to understand."
            ),

            self.LEVEL_MASTERY: (
                "Treat the student as highly confident with the "
                "current concept. "
                "Focus on deeper reasoning, advanced applications, "
                "subtle distinctions, edge cases and connections "
                "between related concepts. "
                "Avoid unnecessary introductory explanations. "
                "Use challenging problems when appropriate."
            )
        }

        instruction = instructions.get(
            level,
            instructions[
                self.LEVEL_INTERMEDIATE
            ]
        )

        # --------------------------------------------------------
        # TREND
        # --------------------------------------------------------

        if trend:

            direction = trend.get(
                "direction"
            )

            if direction == "declining":

                instruction += (
                    " The student's recent confidence appears "
                    "to be decreasing, so prioritize clarity and "
                    "reinforcement before increasing difficulty."
                )

            elif direction == "improving":

                instruction += (
                    " The student's recent confidence appears "
                    "to be improving, so difficulty may increase "
                    "gradually when the current concept is secure."
                )

        # --------------------------------------------------------
        # CONFUSION
        # --------------------------------------------------------

        if signals and signals.get(
            "confusion"
        ):

            instruction += (
                " The student has shown a confusion signal. "
                "Prefer a simpler explanation and a different "
                "example rather than merely repeating the same "
                "explanation."
            )

        return instruction

    # ============================================================
    # BUILD DECISION
    # ============================================================

    def build_decision(
        self,
        level: str,
        confidence: float,
        trend: Dict[str, Any],
        signal_data: Dict[str, Any],
        adaptive_score: float,
        attempts: int,
        performance: Optional[float],
        subject: str,
        base_level: str,
        requested_difficulty: Optional[str]
    ) -> Dict[str, Any]:
        """
        Build the complete public difficulty decision.
        """

        tracking = self.tracking_level(
            level
        )

        stage = self.learning_stage(
            level
        )

        instruction = self.build_instruction(
            level,
            trend=trend,
            signals=signal_data
        )

        previous_level = self.get_last_level(
            subject
        )

        if previous_level is None:

            movement = "initial"

        elif self.level_index(level) > self.level_index(
            previous_level
        ):

            movement = "increase"

        elif self.level_index(level) < self.level_index(
            previous_level
        ):

            movement = "decrease"

        else:

            movement = "stable"

        return {

            # ----------------------------------------------------
            # ORIGINAL COMPATIBILITY FIELDS
            # ----------------------------------------------------

            "level":
                level,

            "tracking_level":
                tracking,

            "stage":
                stage,

            "confidence":
                round(
                    confidence,
                    2
                ),

            "instruction":
                instruction,

            # ----------------------------------------------------
            # ADAPTIVE INFORMATION
            # ----------------------------------------------------

            "adaptive_score":
                round(
                    adaptive_score,
                    2
                ),

            "base_level":
                base_level,

            "previous_level":
                previous_level,

            "movement":
                movement,

            "trend":
                trend,

            "signals":
                signal_data,

            "attempts":
                attempts,

            "performance":
                performance,

            "subject":
                subject,

            "requested_difficulty":
                requested_difficulty,

            # ----------------------------------------------------
            # METADATA
            # ----------------------------------------------------

            "engine_version":
                self.VERSION,

            "reason":
                self.build_reason(
                    level=level,
                    confidence=confidence,
                    trend=trend,
                    signal_data=signal_data,
                    movement=movement
                )
        }

    # ============================================================
    # BUILD REASON
    # ============================================================

    def build_reason(
        self,
        level: str,
        confidence: float,
        trend: Dict[str, Any],
        signal_data: Dict[str, Any],
        movement: str
    ) -> str:
        """
        Create a human-readable explanation of the decision.

        Useful for debugging and future teacher-brain systems.
        """

        reasons = []

        reasons.append(
            f"confidence={round(confidence, 1)}"
        )

        if trend["direction"] != "stable":

            reasons.append(
                f"trend={trend['direction']}"
            )

        if signal_data["confusion"]:

            reasons.append(
                "recent confusion detected"
            )

        elif signal_data["understanding"]:

            reasons.append(
                "recent understanding signal detected"
            )

        if movement == "increase":

            reasons.append(
                "difficulty increased gradually"
            )

        elif movement == "decrease":

            reasons.append(
                "difficulty reduced to support learning"
            )

        return (
            "Difficulty selected as "
            f"{level} because "
            + ", ".join(
                reasons
            )
            + "."
        )

    # ============================================================
    # HISTORY
    # ============================================================

    def record_decision(
        self,
        subject: str,
        decision: Dict[str, Any]
    ) -> None:
        """
        Store a difficulty decision for future adaptation.
        """

        if subject not in self.history:

            self.history[
                subject
            ] = []

        history = self.history[
            subject
        ]

        history.append(
            {
                "confidence":
                    decision.get(
                        "confidence"
                    ),

                "adaptive_score":
                    decision.get(
                        "adaptive_score"
                    ),

                "level":
                    decision.get(
                        "level"
                    ),

                "tracking_level":
                    decision.get(
                        "tracking_level"
                    ),

                "movement":
                    decision.get(
                        "movement"
                    ),

                "trend":
                    decision.get(
                        "trend"
                    ),

                "signals":
                    decision.get(
                        "signals"
                    )
            }
        )

        if len(history) > self.max_history:

            self.history[
                subject
            ] = history[
                -self.max_history:
            ]

    # ============================================================
    # GET HISTORY
    # ============================================================

    def get_history(
        self,
        subject: Optional[str] = None
    ):
        """
        Return difficulty history.

        If subject is None, return all history.
        """

        if subject is None:

            return self.history

        subject = self.normalize_subject(
            subject
        )

        return self.history.get(
            subject,
            []
        )

    # ============================================================
    # SUBJECT HISTORY
    # ============================================================

    def get_subject_history(
        self,
        subject: str
    ) -> List[Dict[str, Any]]:

        subject = self.normalize_subject(
            subject
        )

        return self.history.get(
            subject,
            []
        )

    # ============================================================
    # LAST CONFIDENCE
    # ============================================================

    def get_last_confidence(
        self,
        subject: Optional[str] = None
    ) -> Optional[float]:

        history = self.get_history(
            subject
        )

        if not history:

            return None

        value = history[-1].get(
            "confidence"
        )

        if value is None:

            return None

        return self.normalize_confidence(
            value
        )

    # ============================================================
    # LAST LEVEL
    # ============================================================

    def get_last_level(
        self,
        subject: Optional[str] = None
    ) -> Optional[str]:

        history = self.get_history(
            subject
        )

        if not history:

            return None

        level = history[-1].get(
            "level"
        )

        if level in self.LEVELS:

            return level

        return None

    # ============================================================
    # INFER PREVIOUS CONFIDENCE
    # ============================================================

    def infer_previous_confidence(
        self,
        history: List[Dict[str, Any]]
    ) -> Optional[float]:

        if not history:

            return None

        latest = history[-1]

        value = latest.get(
            "confidence"
        )

        if value is None:

            return None

        return self.normalize_confidence(
            value
        )

    # ============================================================
    # RECENT AVERAGE
    # ============================================================

    def recent_average(
        self,
        subject: Optional[str] = None,
        window: int = 5
    ) -> Optional[float]:
        """
        Calculate recent average confidence.
        """

        history = self.get_history(
            subject
        )

        if not history:

            return None

        try:

            window = max(
                1,
                int(window)
            )

        except (
            TypeError,
            ValueError
        ):

            window = 5

        recent = history[
            -window:
        ]

        values = []

        for item in recent:

            value = item.get(
                "confidence"
            )

            if value is None:

                continue

            values.append(
                self.normalize_confidence(
                    value
                )
            )

        if not values:

            return None

        return sum(
            values
        ) / len(
            values
        )

    # ============================================================
    # CONSISTENCY
    # ============================================================

    def confidence_consistency(
        self,
        subject: Optional[str] = None,
        window: int = 5
    ) -> Optional[float]:
        """
        Estimate how stable recent confidence has been.

        Returns a value from 0 to 100.

        Higher means more stable.
        """

        history = self.get_history(
            subject
        )

        if len(history) < 2:

            return None

        try:

            window = max(
                2,
                int(window)
            )

        except (
            TypeError,
            ValueError
        ):

            window = 5

        recent = history[
            -window:
        ]

        values = []

        for item in recent:

            value = item.get(
                "confidence"
            )

            if value is not None:

                values.append(
                    self.normalize_confidence(
                        value
                    )
                )

        if len(values) < 2:

            return None

        average = sum(
            values
        ) / len(
            values
        )

        variance = sum(
            (
                value - average
            ) ** 2
            for value in values
        ) / len(
            values
        )

        deviation = math.sqrt(
            variance
        )

        # 0 deviation = 100 consistency.
        consistency = (
            100
            - (
                deviation
                * 2
            )
        )

        return max(
            0,
            min(
                100,
                consistency
            )
        )

    # ============================================================
    # STATISTICS
    # ============================================================

    def update_statistics(
        self,
        decision: Dict[str, Any]
    ) -> None:

        self.statistics[
            "decisions"
        ] += 1

        movement = decision.get(
            "movement"
        )

        if movement == "increase":

            self.statistics[
                "level_up"
            ] += 1

        elif movement == "decrease":

            self.statistics[
                "level_down"
            ] += 1

        elif movement == "stable":

            self.statistics[
                "stable"
            ] += 1

    # ============================================================
    # GET STATISTICS
    # ============================================================

    def get_statistics(
        self
    ) -> Dict[str, int]:

        return dict(
            self.statistics
        )

    # ============================================================
    # RESET SUBJECT
    # ============================================================

    def reset_subject(
        self,
        subject: str
    ) -> None:
        """
        Reset adaptive history for one subject.
        """

        subject = self.normalize_subject(
            subject
        )

        self.history.pop(
            subject,
            None
        )

    # ============================================================
    # RESET ALL
    # ============================================================

    def reset(
        self
    ) -> None:
        """
        Reset all difficulty history and statistics.
        """

        self.history.clear()

        for key in self.statistics:

            self.statistics[
                key
            ] = 0

    # ============================================================
    # RECOMMEND NEXT LEVEL
    # ============================================================

    def recommend_next_level(
        self,
        subject: Optional[str] = None
    ) -> Optional[str]:
        """
        Recommend the next level based on recent history.
        """

        current = self.get_last_level(
            subject
        )

        if current is None:

            return None

        average = self.recent_average(
            subject
        )

        if average is None:

            return current

        if average >= 90:

            return self.increase_level(
                current
            )

        if average < 40:

            return self.reduce_level(
                current
            )

        return current

    # ============================================================
    # SHOULD_INCREASE
    # ============================================================

    def should_increase(
        self,
        confidence: Any,
        subject: Optional[str] = None
    ) -> bool:
        """
        Determine whether the student's current evidence
        supports gradually increasing difficulty.
        """

        current = self.normalize_confidence(
            confidence
        )

        previous = self.get_last_confidence(
            subject
        )

        if previous is None:

            return current >= (
                self.INTERMEDIATE_THRESHOLD
            )

        trend = self.calculate_trend(
            current,
            previous
        )

        return (
            current >= self.INTERMEDIATE_THRESHOLD
            and trend["direction"] != "declining"
        )

    # ============================================================
    # SHOULD_DECREASE
    # ============================================================

    def should_decrease(
        self,
        confidence: Any,
        subject: Optional[str] = None,
        recent_signals: Any = None
    ) -> bool:
        """
        Determine whether difficulty should probably be reduced.
        """

        current = self.normalize_confidence(
            confidence
        )

        signals = self.analyze_signals(
            recent_signals
        )

        if signals["confusion"]:

            return True

        previous = self.get_last_confidence(
            subject
        )

        if previous is None:

            return current < self.BEGINNER_THRESHOLD

        trend = self.calculate_trend(
            current,
            previous
        )

        return (
            current < self.BEGINNER_THRESHOLD
            or trend["direction"] == "declining"
            and trend["strength"] == "strong"
        )

    # ============================================================
    # SUMMARY
    # ============================================================

    def summary(
        self,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Return a compact summary of the student's recent
        difficulty state.
        """

        return {

            "subject":
                self.normalize_subject(
                    subject
                ),

            "current_level":
                self.get_last_level(
                    subject
                ),

            "current_confidence":
                self.get_last_confidence(
                    subject
                ),

            "recent_average":
                self.recent_average(
                    subject
                ),

            "consistency":
                self.confidence_consistency(
                    subject
                ),

            "recommended_next_level":
                self.recommend_next_level(
                    subject
                )
        }

    # ============================================================
    # DEBUG
    # ============================================================

    def debug_state(
        self,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Return diagnostic information useful during development.
        """

        return {

            "version":
                self.VERSION,

            "subject":
                self.normalize_subject(
                    subject
                ),

            "history":
                self.get_history(
                    subject
                ),

            "summary":
                self.summary(
                    subject
                ),

            "statistics":
                self.get_statistics()
        }

    # ============================================================
    # STRING REPRESENTATION
    # ============================================================

    def __repr__(
        self
    ) -> str:

        return (
            f"<DifficultyEngine "
            f"version={self.VERSION!r} "
            f"subjects={len(self.history)}>"
        )