from typing import Any, Dict, List, Optional, Tuple
import time
import re
import traceback


from backend.llm import LocalLLM
from backend.tutor_system.quiz_engine import QuizEngine
from backend.tutor_system.adaptive_tutor import AdaptiveTutor

from student_profile import StudentProfile

from backend.prompt.prompt_builder import PromptBuilder


class TutorEngine:
    """
    ================================================================
    NOVA TUTOR ENGINE
    ================================================================

    The TutorEngine is the central bridge between Nova's internal
    learning systems and the local language model.

    It does NOT own long-term student memory.

    It does NOT decide the student's complete learning profile.

    It does NOT replace NovaBrain.

    Instead, it receives information from Nova's other systems and
    transforms that information into a reliable tutoring response.

    Main responsibilities
    ---------------------

        1. Validate incoming requests.
        2. Normalize input data.
        3. Interpret tutor mode.
        4. Prepare learning strategy.
        5. Incorporate adaptive tutoring instructions.
        6. Build a structured prompt.
        7. Send the prompt to LocalLLM.
        8. Retry temporary generation failures.
        9. Validate the generated answer.
        10. Clean accidental formatting.
        11. Protect NovaCore from optional subsystem failures.
        12. Collect runtime statistics.
        13. Provide debugging information.
        14. Support compatibility with older Nova components.

    Architecture
    ------------

        NovaCore
            |
            v
        NovaBrain
            |
            v
        TutorEngine
            |
            +-------------------+
            |                   |
            v                   v
        AdaptiveTutor      PromptBuilder
                                |
                                v
                            LocalLLM
                                |
                                v
                            Ollama
                                |
                                v
                             Answer

    Design goals
    ------------

        Reliability
        ----------
        A failure in an optional component should not immediately
        destroy the entire tutoring pipeline.

        Compatibility
        -------------
        Older versions of PromptBuilder and AdaptiveTutor may still
        use different method signatures. TutorEngine therefore tries
        modern interfaces first and gracefully falls back to older
        ones.

        Determinism
        -----------
        Normalization and validation happen before and after the LLM.

        Extensibility
        -------------
        Future Nova versions can add:
            - streaming
            - tool use
            - citations
            - answer scoring
            - hallucination checks
            - conversation summaries
            - richer learning strategies
            - model routing

        Safety
        ------
        The engine avoids blindly trusting malformed values returned
        by other components.

    ================================================================
    """

    # ============================================================
    # VERSION
    # ============================================================

    VERSION = "1.0.0"

    # ============================================================
    # DEFAULT VALUES
    # ============================================================

    DEFAULT_MODE = "normal"

    DEFAULT_SUBJECT = "general"

    DEFAULT_CREATIVITY = "medium"

    DEFAULT_LANGUAGE = "English"

    DEFAULT_LEVEL = "High School"

    DEFAULT_RESPONSE_LENGTH = "balanced"

    DEFAULT_MAX_MESSAGE_LENGTH = 12000

    DEFAULT_MAX_MEMORY_LENGTH = 12000

    DEFAULT_MAX_PROMPT_LENGTH = 50000

    DEFAULT_MAX_RESPONSE_LENGTH = 30000

    DEFAULT_RETRY_COUNT = 2

    DEFAULT_RETRY_DELAY = 0.35

    # ============================================================
    # VALID VALUES
    # ============================================================

    VALID_CREATIVITY = {
        "low",
        "medium",
        "high"
    }

    VALID_RESPONSE_LENGTHS = {
        "short",
        "balanced",
        "long",
        "detailed"
    }

    VALID_MODES = {
        "normal",
        "adaptive",
        "personal",
        "quiz",
        "practice_quiz",
        "test",
        "explain",
        "teach",
        "practice",
        "review",
        "challenge",
        "simple",
        "deep"
    }

    QUIZ_MODES = {
        "quiz",
        "practice_quiz",
        "test"
    }

    SIMPLE_MODES = {
        "simple"
    }

    DEEP_MODES = {
        "deep",
        "challenge"
    }

    # ============================================================
    # FALLBACK RESPONSES
    # ============================================================

    FALLBACK_RESPONSE = (
        "Nova couldn't generate a response right now."
    )

    FALLBACK_EMPTY_REQUEST = (
        "I couldn't understand the request."
    )

    FALLBACK_PROMPT_ERROR = (
        "Nova couldn't prepare the response correctly."
    )

    FALLBACK_QUIZ_ERROR = (
        "I couldn't create the quiz right now."
    )

    FALLBACK_LLM_ERROR = (
        "Nova couldn't generate a response right now."
    )

    FALLBACK_INVALID_RESPONSE = (
        "Nova generated an invalid response."
    )

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(
        self,
        student=None,
        brain=None,
        llm=None,
        quiz_engine=None,
        adaptive_tutor=None,
        prompt_builder=None,
        retry_count=None,
        retry_delay=None,
        debug=False
    ):
        """
        Initialize TutorEngine.

        Dependencies can be injected.

        This is important because Nova will eventually need tests.

        Example:

            TutorEngine(
                student=my_student,
                llm=my_fake_llm
            )

        """

        print(
            "Loading Tutor Engine..."
        )

        # --------------------------------------------------------
        # DEBUG
        # --------------------------------------------------------

        self.debug = bool(
            debug
        )

        # --------------------------------------------------------
        # RETRY CONFIGURATION
        # --------------------------------------------------------

        self.retry_count = (
            self._normalize_retry_count(
                retry_count
            )
        )

        self.retry_delay = (
            self._normalize_retry_delay(
                retry_delay
            )
        )

        # --------------------------------------------------------
        # STUDENT
        # --------------------------------------------------------

        self.student = (
            student
            if student is not None
            else StudentProfile()
        )

        # --------------------------------------------------------
        # LOCAL LLM
        # --------------------------------------------------------

        self.llm = (
            llm
            if llm is not None
            else LocalLLM()
        )

        # --------------------------------------------------------
        # QUIZ ENGINE
        # --------------------------------------------------------

        self.quiz = (
            quiz_engine
            if quiz_engine is not None
            else QuizEngine()
        )

        # --------------------------------------------------------
        # ADAPTIVE TUTOR
        # --------------------------------------------------------

        self.adaptive_tutor = (
            adaptive_tutor
            if adaptive_tutor is not None
            else AdaptiveTutor()
        )

        # --------------------------------------------------------
        # PROMPT BUILDER
        # --------------------------------------------------------

        self.prompt_builder = (
            prompt_builder
            if prompt_builder is not None
            else PromptBuilder()
        )

        # --------------------------------------------------------
        # OPTIONAL BRAIN
        # --------------------------------------------------------

        self.brain = brain

        # --------------------------------------------------------
        # RUNTIME STATISTICS
        # --------------------------------------------------------

        self.stats = {
            "requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "empty_requests": 0,
            "llm_calls": 0,
            "llm_failures": 0,
            "llm_retries": 0,
            "quiz_requests": 0,
            "quiz_failures": 0,
            "prompt_failures": 0,
            "adaptive_failures": 0,
            "validation_failures": 0,
            "total_generation_time": 0.0,
            "last_generation_time": 0.0,
            "last_error": None
        }

        print(
            "Tutor Engine ready."
        )

    # ============================================================
    # PUBLIC API
    # ============================================================

    def answer(
        self,
        message,
        intent=None,
        subject=None,
        mode=None,
        memory_context=None,
        difficulty=None,
        settings=None,
        strategy=None,
        topic=None
    ) -> str:
        """
        Main tutoring pipeline.

        This method intentionally remains compatible with the
        current NovaCore call:

            tutor.answer(
                message,
                intent,
                subject,
                mode,
                memory_context,
                difficulty,
                settings
            )

        Additional strategy/topic parameters are optional.
        """

        start_time = time.perf_counter()

        self.stats["requests"] += 1

        try:

            # ====================================================
            # STEP 1
            # NORMALIZE MESSAGE
            # ====================================================

            message = self._normalize_message(
                message
            )

            if not message:

                self.stats["empty_requests"] += 1

                return self.FALLBACK_EMPTY_REQUEST

            # ====================================================
            # STEP 2
            # NORMALIZE INPUT
            # ====================================================

            mode = self._normalize_mode(
                mode
            )

            subject = self._normalize_optional_text(
                subject
            )

            topic = self._normalize_optional_text(
                topic
            )

            intent = self._normalize_optional_text(
                intent
            )

            memory_context = (
                self._normalize_memory_context(
                    memory_context
                )
            )

            settings = (
                self._normalize_settings(
                    settings
                )
            )

            # ====================================================
            # STEP 3
            # APPLY MODE OVERRIDES
            # ====================================================

            settings = (
                self._apply_mode_settings(
                    settings,
                    mode
                )
            )

            # ====================================================
            # STEP 4
            # SPECIAL MODES
            # ====================================================

            if self._is_quiz_mode(
                mode
            ):

                self.stats["quiz_requests"] += 1

                result = self._create_quiz(
                    subject
                )

                if result == self.FALLBACK_QUIZ_ERROR:

                    self.stats[
                        "quiz_failures"
                    ] += 1

                else:

                    self.stats[
                        "successful_requests"
                    ] += 1

                return result

            # ====================================================
            # STEP 5
            # PREPARE STRATEGY
            # ====================================================

            prepared_strategy = (
                self._prepare_strategy(
                    strategy=strategy,
                    subject=subject,
                    topic=topic,
                    difficulty=difficulty,
                    settings=settings,
                    mode=mode
                )
            )

            # ====================================================
            # STEP 6
            # ADAPTIVE TUTOR
            # ====================================================

            adaptive_instruction = (
                self._build_adaptive_instruction(
                    subject=subject,
                    message=message,
                    strategy=prepared_strategy
                )
            )

            # ====================================================
            # STEP 7
            # MERGE STRATEGIES
            # ====================================================

            prompt_strategy = (
                self._build_prompt_strategy(
                    strategy=prepared_strategy,
                    adaptive_instruction=
                        adaptive_instruction,
                    mode=mode
                )
            )

            # ====================================================
            # STEP 8
            # BUILD PROMPT
            # ====================================================

            prompt = (
                self._build_prompt(
                    message=message,
                    intent=intent,
                    subject=subject,
                    topic=topic,
                    mode=mode,
                    memory_context=memory_context,
                    difficulty=difficulty,
                    settings=settings,
                    strategy=prompt_strategy
                )
            )

            # ====================================================
            # STEP 9
            # VALIDATE PROMPT
            # ====================================================

            prompt = (
                self._validate_prompt(
                    prompt
                )
            )

            if not prompt:

                self.stats[
                    "prompt_failures"
                ] += 1

                return self.FALLBACK_PROMPT_ERROR

            # ====================================================
            # STEP 10
            # GENERATE
            # ====================================================

            response = (
                self._generate(
                    prompt=prompt,
                    settings=settings
                )
            )

            # ====================================================
            # STEP 11
            # CLEAN
            # ====================================================

            response = (
                self._clean_response(
                    response
                )
            )

            # ====================================================
            # STEP 12
            # VALIDATE RESPONSE
            # ====================================================

            if not self._is_valid_response(
                response
            ):

                self.stats[
                    "validation_failures"
                ] += 1

                return self.FALLBACK_INVALID_RESPONSE

            # ====================================================
            # SUCCESS
            # ====================================================

            self.stats[
                "successful_requests"
            ] += 1

            return response

        except Exception as error:

            self.stats[
                "failed_requests"
            ] += 1

            self._record_error(
                error
            )

            self._log_error(
                "TUTOR ENGINE ERROR",
                error
            )

            return self.FALLBACK_RESPONSE

        finally:

            elapsed = (
                time.perf_counter()
                - start_time
            )

            self.stats[
                "last_generation_time"
            ] = elapsed

    # ============================================================
    # SIMPLE PUBLIC API
    # ============================================================

    def simple_answer(
        self,
        message,
        subject=None,
        mode="normal",
        settings=None
    ) -> str:
        """
        Convenience method for terminal testing and development.
        """

        return self.answer(

            message=message,

            intent=None,

            subject=subject,

            mode=mode,

            memory_context=None,

            difficulty=None,

            settings=settings,

            strategy=None,

            topic=None
        )

    # ============================================================
    # TEST CONNECTION
    # ============================================================

    def test_llm(
        self
    ) -> Dict[str, Any]:
        """
        Test whether the configured LocalLLM can respond.

        This does not require NovaCore.

        Useful for debugging Ollama.
        """

        start = time.perf_counter()

        try:

            response = self.llm.answer(

                system=(
                    "You are testing Nova's local language model."
                ),

                user=(
                    "Reply with exactly: NOVA_LLM_OK"
                ),

                creativity="low"
            )

            elapsed = (
                time.perf_counter()
                - start
            )

            valid = (
                response is not None
                and bool(
                    str(response).strip()
                )
            )

            return {

                "success": valid,

                "response":
                    str(response).strip()
                    if response is not None
                    else "",

                "duration":
                    round(
                        elapsed,
                        3
                    )
            }

        except Exception as error:

            return {

                "success": False,

                "response": "",

                "duration":
                    round(
                        time.perf_counter()
                        - start,
                        3
                    ),

                "error":
                    str(error)
            }

    # ============================================================
    # STATISTICS
    # ============================================================

    def get_stats(
        self
    ) -> Dict[str, Any]:
        """
        Return a safe copy of runtime statistics.
        """

        result = dict(
            self.stats
        )

        requests = result.get(
            "requests",
            0
        )

        successful = result.get(
            "successful_requests",
            0
        )

        if requests:

            result[
                "success_rate"
            ] = round(
                (
                    successful
                    / requests
                ) * 100,
                2
            )

        else:

            result[
                "success_rate"
            ] = 0.0

        return result

    # ============================================================
    # RESET STATISTICS
    # ============================================================

    def reset_stats(
        self
    ):
        """
        Reset runtime statistics.

        This does not affect student data.
        """

        keys = list(
            self.stats.keys()
        )

        for key in keys:

            if key in {
                "total_generation_time",
                "last_generation_time"
            }:

                self.stats[key] = 0.0

            elif key == "last_error":

                self.stats[key] = None

            else:

                self.stats[key] = 0

    # ============================================================
    # MESSAGE NORMALIZATION
    # ============================================================

    def _normalize_message(
        self,
        message
    ) -> str:
        """
        Normalize the student's message.

        Prevents enormous accidental inputs from destroying
        the context window.
        """

        if message is None:

            return ""

        if not isinstance(
            message,
            str
        ):

            message = str(
                message
            )

        message = (
            message
            .replace(
                "\x00",
                ""
            )
            .strip()
        )

        if len(message) > (
            self.DEFAULT_MAX_MESSAGE_LENGTH
        ):

            message = (
                message[
                    :self.DEFAULT_MAX_MESSAGE_LENGTH
                ]
                + "\n\n[Message truncated by Nova.]"
            )

        return message

    # ============================================================
    # OPTIONAL TEXT NORMALIZATION
    # ============================================================

    def _normalize_optional_text(
        self,
        value
    ) -> Optional[str]:
        """
        Normalize optional text values.
        """

        if value is None:

            return None

        if not isinstance(
            value,
            str
        ):

            value = str(
                value
            )

        value = (
            value
            .replace(
                "\x00",
                ""
            )
            .strip()
        )

        if not value:

            return None

        return value

    # ============================================================
    # MODE NORMALIZATION
    # ============================================================

    def _normalize_mode(
        self,
        mode
    ) -> str:
        """
        Normalize tutor mode.

        Unknown modes are allowed rather than causing a crash.
        This makes future Nova modes possible without modifying
        this method immediately.
        """

        if mode is None:

            return self.DEFAULT_MODE

        if not isinstance(
            mode,
            str
        ):

            mode = str(
                mode
            )

        mode = (
            mode
            .strip()
            .lower()
        )

        if not mode:

            return self.DEFAULT_MODE

        return mode

    # ============================================================
    # SETTINGS NORMALIZATION
    # ============================================================

    def _normalize_settings(
        self,
        settings
    ) -> Dict[str, Any]:
        """
        Normalize settings into a predictable dictionary.
        """

        if not isinstance(
            settings,
            dict
        ):

            settings = {}

        result = dict(
            settings
        )

        result.setdefault(
            "language",
            self.DEFAULT_LANGUAGE
        )

        result.setdefault(
            "level",
            self.DEFAULT_LEVEL
        )

        result.setdefault(
            "response_length",
            self.DEFAULT_RESPONSE_LENGTH
        )

        result[
            "creativity"
        ] = self._normalize_creativity(
            result.get(
                "creativity"
            )
        )

        result[
            "response_length"
        ] = self._normalize_response_length(
            result.get(
                "response_length"
            )
        )

        return result

    # ============================================================
    # CREATIVITY
    # ============================================================

    def _normalize_creativity(
        self,
        creativity
    ) -> str:
        """
        Normalize LLM creativity.
        """

        if not isinstance(
            creativity,
            str
        ):

            return self.DEFAULT_CREATIVITY

        creativity = (
            creativity
            .strip()
            .lower()
        )

        if creativity not in (
            self.VALID_CREATIVITY
        ):

            return self.DEFAULT_CREATIVITY

        return creativity

    # ============================================================
    # RESPONSE LENGTH
    # ============================================================

    def _normalize_response_length(
        self,
        value
    ) -> str:
        """
        Normalize requested response length.
        """

        if not isinstance(
            value,
            str
        ):

            return self.DEFAULT_RESPONSE_LENGTH

        value = (
            value
            .strip()
            .lower()
        )

        if value not in (
            self.VALID_RESPONSE_LENGTHS
        ):

            return self.DEFAULT_RESPONSE_LENGTH

        return value

    # ============================================================
    # MEMORY NORMALIZATION
    # ============================================================

    def _normalize_memory_context(
        self,
        memory_context
    ) -> str:
        """
        Prevent excessive memory from consuming the prompt.
        """

        if memory_context is None:

            return "No previous discussion."

        if not isinstance(
            memory_context,
            str
        ):

            memory_context = str(
                memory_context
            )

        memory_context = (
            memory_context
            .replace(
                "\x00",
                ""
            )
            .strip()
        )

        if not memory_context:

            return "No previous discussion."

        if len(memory_context) > (
            self.DEFAULT_MAX_MEMORY_LENGTH
        ):

            memory_context = (
                memory_context[
                    :self.DEFAULT_MAX_MEMORY_LENGTH
                ]
                + "\n\n[Memory context truncated by Nova.]"
            )

        return memory_context

    # ============================================================
    # MODE SETTINGS
    # ============================================================

    def _apply_mode_settings(
        self,
        settings,
        mode
    ) -> Dict[str, Any]:
        """
        Apply explicit tutor-mode behavior.

        Explicit user/system mode should have priority over
        generic defaults.
        """

        settings = dict(
            settings
        )

        if mode in self.SIMPLE_MODES:

            settings[
                "response_length"
            ] = "short"

            settings[
                "step_by_step"
            ] = True

        elif mode in self.DEEP_MODES:

            settings[
                "response_length"
            ] = "detailed"

            settings[
                "creativity"
            ] = "medium"

        return settings

    # ============================================================
    # QUIZ DETECTION
    # ============================================================

    def _is_quiz_mode(
        self,
        mode
    ) -> bool:
        """
        Determine whether the request is a quiz request.
        """

        return mode in self.QUIZ_MODES

    # ============================================================
    # QUIZ GENERATION
    # ============================================================

    def _create_quiz(
        self,
        subject
    ) -> str:
        """
        Generate a quiz using QuizEngine.

        Quiz generation remains separate from LLM generation.
        """

        if not subject:

            subject = self.DEFAULT_SUBJECT

        try:

            result = (
                self.quiz.create_quiz(
                    subject
                )
            )

        except Exception as error:

            self._record_error(
                error
            )

            self._log_error(
                "QUIZ ENGINE ERROR",
                error
            )

            return self.FALLBACK_QUIZ_ERROR

        if result is None:

            return self.FALLBACK_QUIZ_ERROR

        result = str(
            result
        ).strip()

        if not result:

            return self.FALLBACK_QUIZ_ERROR

        return result

    # ============================================================
    # STRATEGY PREPARATION
    # ============================================================

    def _prepare_strategy(
        self,
        strategy,
        subject,
        topic,
        difficulty,
        settings,
        mode
    ) -> Dict[str, Any]:
        """
        Normalize and complete NovaBrain strategy data.
        """

        if not isinstance(
            strategy,
            dict
        ):

            strategy = {}

        result = dict(
            strategy
        )

        # --------------------------------------------------------
        # SUBJECT
        # --------------------------------------------------------

        if not result.get(
            "subject"
        ):

            result[
                "subject"
            ] = subject

        # --------------------------------------------------------
        # TOPIC
        # --------------------------------------------------------

        if not result.get(
            "topic"
        ):

            result[
                "topic"
            ] = topic

        # --------------------------------------------------------
        # MODE
        # --------------------------------------------------------

        result[
            "mode"
        ] = mode

        # --------------------------------------------------------
        # DIFFICULTY
        # --------------------------------------------------------

        self._merge_difficulty(
            result,
            difficulty
        )

        # --------------------------------------------------------
        # CONFIDENCE
        # --------------------------------------------------------

        confidence = (
            result.get(
                "confidence",
                50
            )
        )

        confidence = (
            self._normalize_confidence(
                confidence
            )
        )

        result[
            "confidence"
        ] = confidence

        # --------------------------------------------------------
        # LEARNING STATE
        # --------------------------------------------------------

        result.setdefault(
            "learning_state",
            self._infer_learning_state(
                confidence
            )
        )

        # --------------------------------------------------------
        # EXPLANATION DEPTH
        # --------------------------------------------------------

        result.setdefault(
            "explanation_depth",
            self._infer_explanation_depth(
                confidence
            )
        )

        # --------------------------------------------------------
        # RESPONSE STYLE
        # --------------------------------------------------------

        result.setdefault(
            "response_style",
            "clear_instructional"
        )

        # --------------------------------------------------------
        # BOOLEAN STRATEGIES
        # --------------------------------------------------------

        result[
            "use_examples"
        ] = self._to_bool(
            result.get(
                "use_examples",
                True
            ),
            True
        )

        result[
            "use_analogies"
        ] = self._to_bool(
            result.get(
                "use_analogies",
                False
            ),
            False
        )

        result[
            "step_by_step"
        ] = self._to_bool(
            result.get(
                "step_by_step",
                False
            ),
            False
        )

        result[
            "challenge"
        ] = self._to_bool(
            result.get(
                "challenge",
                False
            ),
            False
        )

        result[
            "reinforcement"
        ] = self._to_bool(
            result.get(
                "reinforcement",
                False
            ),
            False
        )

        # --------------------------------------------------------
        # SETTINGS OVERRIDES
        # --------------------------------------------------------

        if settings.get(
            "use_examples"
        ) is not None:

            result[
                "use_examples"
            ] = self._to_bool(
                settings.get(
                    "use_examples"
                ),
                result[
                    "use_examples"
                ]
            )

        if settings.get(
            "use_analogies"
        ) is not None:

            result[
                "use_analogies"
            ] = self._to_bool(
                settings.get(
                    "use_analogies"
                ),
                result[
                    "use_analogies"
                ]
            )

        if settings.get(
            "step_by_step"
        ) is not None:

            result[
                "step_by_step"
            ] = self._to_bool(
                settings.get(
                    "step_by_step"
                ),
                result[
                    "step_by_step"
                ]
            )

        # --------------------------------------------------------
        # APPROACH
        # --------------------------------------------------------

        result[
            "approach"
        ] = self._normalize_approach(
            result.get(
                "approach"
            )
        )

        # --------------------------------------------------------
        # CHALLENGE LEVEL
        # --------------------------------------------------------

        result.setdefault(
            "challenge_level",
            self._infer_challenge_level(
                confidence
            )
        )

        # --------------------------------------------------------
        # RESPONSE LENGTH
        # --------------------------------------------------------

        result[
            "response_length"
        ] = self._normalize_response_length(
            settings.get(
                "response_length",
                self.DEFAULT_RESPONSE_LENGTH
            )
        )

        return result

    # ============================================================
    # DIFFICULTY MERGING
    # ============================================================

    def _merge_difficulty(
        self,
        strategy,
        difficulty
    ):
        """
        Merge DifficultyEngine output into the strategy.
        """

        if isinstance(
            difficulty,
            dict
        ):

            if not strategy.get(
                "difficulty"
            ):

                strategy[
                    "difficulty"
                ] = difficulty.get(
                    "level"
                )

            strategy[
                "tracking_difficulty"
            ] = difficulty.get(
                "tracking_level"
            )

            strategy[
                "difficulty_stage"
            ] = difficulty.get(
                "stage"
            )

            strategy[
                "difficulty_instruction"
            ] = difficulty.get(
                "instruction",
                ""
            )

        elif isinstance(
            difficulty,
            str
        ):

            if not strategy.get(
                "difficulty"
            ):

                strategy[
                    "difficulty"
                ] = difficulty

    # ============================================================
    # CONFIDENCE NORMALIZATION
    # ============================================================

    def _normalize_confidence(
        self,
        confidence
    ) -> float:
        """
        Convert confidence to a safe 0-100 value.

        Supports both:

            0.0 - 1.0

        and:

            0 - 100
        """

        try:

            confidence = float(
                confidence
            )

        except (
            TypeError,
            ValueError
        ):

            confidence = 50.0

        if 0 <= confidence <= 1:

            confidence *= 100

        confidence = max(
            0,
            min(
                100,
                confidence
            )
        )

        return round(
            confidence,
            2
        )

    # ============================================================
    # APPROACH NORMALIZATION
    # ============================================================

    def _normalize_approach(
        self,
        approach
    ) -> List[str]:
        """
        Convert strategy approach data into a clean list.
        """

        if approach is None:

            return []

        if isinstance(
            approach,
            str
        ):

            approach = [
                approach
            ]

        elif not isinstance(
            approach,
            list
        ):

            approach = [
                approach
            ]

        result = []

        seen = set()

        for item in approach:

            if item is None:

                continue

            item = str(
                item
            ).strip()

            if not item:

                continue

            key = (
                item.lower()
            )

            if key in seen:

                continue

            seen.add(
                key
            )

            result.append(
                item
            )

        return result

    # ============================================================
    # LEARNING STATE
    # ============================================================

    def _infer_learning_state(
        self,
        confidence
    ) -> str:
        """
        Infer learning state from confidence.
        """

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

    # ============================================================
    # EXPLANATION DEPTH
    # ============================================================

    def _infer_explanation_depth(
        self,
        confidence
    ) -> str:
        """
        Infer explanation depth.
        """

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
    # CHALLENGE LEVEL
    # ============================================================

    def _infer_challenge_level(
        self,
        confidence
    ) -> str:
        """
        Infer appropriate challenge intensity.
        """

        if confidence < 40:

            return "none"

        if confidence < 65:

            return "small"

        if confidence < 80:

            return "moderate"

        if confidence < 90:

            return "difficult"

        return "expert"

    # ============================================================
    # ADAPTIVE TUTOR
    # ============================================================

    def _build_adaptive_instruction(
        self,
        subject,
        message,
        strategy
    ) -> str:
        """
        Obtain adaptive teaching instructions.

        Modern AdaptiveTutor interface:

            build_instruction(
                student,
                subject,
                message=message
            )

        Legacy interface:

            build_instruction(
                student,
                subject
            )
        """

        try:

            student_data = (
                self._get_student_data()
            )

            try:

                instruction = (
                    self.adaptive_tutor
                    .build_instruction(
                        student_data,
                        subject,
                        message=message
                    )
                )

            except TypeError:

                instruction = (
                    self.adaptive_tutor
                    .build_instruction(
                        student_data,
                        subject
                    )
                )

            if instruction is None:

                return ""

            return str(
                instruction
            ).strip()

        except Exception as error:

            self.stats[
                "adaptive_failures"
            ] += 1

            self._record_error(
                error
            )

            self._log_error(
                "ADAPTIVE TUTOR ERROR",
                error
            )

            return ""

    # ============================================================
    # STUDENT DATA
    # ============================================================

    def _get_student_data(
        self
    ) -> Dict[str, Any]:
        """
        Safely obtain the student profile.

        Supports StudentProfile.get().
        """

        try:

            if hasattr(
                self.student,
                "get"
            ):

                data = (
                    self.student.get()
                )

            elif hasattr(
                self.student,
                "profile"
            ):

                data = (
                    self.student.profile
                )

            else:

                data = {}

        except Exception as error:

            self._log_error(
                "STUDENT PROFILE ERROR",
                error
            )

            data = {}

        if not isinstance(
            data,
            dict
        ):

            return {}

        return dict(
            data
        )

    # ============================================================
    # PROMPT STRATEGY
    # ============================================================

    def _build_prompt_strategy(
        self,
        strategy,
        adaptive_instruction,
        mode
    ) -> Dict[str, Any]:
        """
        Merge all teaching instructions into one strategy object.
        """

        result = dict(
            strategy
        )

        approach = (
            self._normalize_approach(
                result.get(
                    "approach"
                )
            )
        )

        # --------------------------------------------------------
        # EXAMPLES
        # --------------------------------------------------------

        if result.get(
            "use_examples"
        ):

            approach.append(
                "Use a concrete example when it improves understanding."
            )

        # --------------------------------------------------------
        # ANALOGIES
        # --------------------------------------------------------

        if result.get(
            "use_analogies"
        ):

            approach.append(
                "Use a simple analogy only when it genuinely clarifies the concept."
            )

        # --------------------------------------------------------
        # STEP BY STEP
        # --------------------------------------------------------

        if result.get(
            "step_by_step"
        ):

            approach.append(
                "Break complex reasoning into clear logical steps."
            )

        # --------------------------------------------------------
        # REINFORCEMENT
        # --------------------------------------------------------

        if result.get(
            "reinforcement"
        ):

            approach.append(
                "Reinforce important fundamentals before moving to harder material."
            )

        # --------------------------------------------------------
        # CHALLENGE
        # --------------------------------------------------------

        if result.get(
            "challenge"
        ):

            approach.append(
                "Add a small reasoning challenge when appropriate."
            )

        # --------------------------------------------------------
        # DIFFICULTY
        # --------------------------------------------------------

        difficulty_instruction = (
            result.get(
                "difficulty_instruction"
            )
        )

        if difficulty_instruction:

            approach.append(
                str(
                    difficulty_instruction
                ).strip()
            )

        # --------------------------------------------------------
        # ADAPTIVE INSTRUCTION
        # --------------------------------------------------------

        if adaptive_instruction:

            approach.append(
                adaptive_instruction
            )

        # --------------------------------------------------------
        # MODE
        # --------------------------------------------------------

        if mode == "simple":

            approach.append(
                "Prioritize simple vocabulary and short explanations."
            )

        elif mode == "deep":

            approach.append(
                "Provide deeper reasoning and relevant technical detail."
            )

        elif mode == "challenge":

            approach.append(
                "Push the student's reasoning without making the answer unnecessarily difficult."
            )

        # --------------------------------------------------------
        # DEDUPLICATE
        # --------------------------------------------------------

        result[
            "approach"
        ] = self._normalize_approach(
            approach
        )

        result[
            "adaptive_instruction"
        ] = (
            adaptive_instruction
            or ""
        )

        return result

    # ============================================================
    # PROMPT BUILDING
    # ============================================================

    def _build_prompt(
        self,
        message,
        intent,
        subject,
        topic,
        mode,
        memory_context,
        difficulty,
        settings,
        strategy
    ) -> Optional[Dict[str, str]]:
        """
        Build prompt using PromptBuilder.

        Multiple signatures are attempted for compatibility.
        """

        student = (
            self._get_student_data()
        )

        # --------------------------------------------------------
        # MODERN SIGNATURE
        # --------------------------------------------------------

        try:

            prompt = (
                self.prompt_builder.build(

                    student=student,

                    subject=subject,

                    topic=topic,

                    message=message,

                    intent=intent,

                    mode=mode,

                    strategy=strategy,

                    memory_context=memory_context,

                    difficulty=difficulty,

                    settings=settings
                )
            )

            normalized = (
                self._normalize_prompt(
                    prompt
                )
            )

            if normalized:

                return normalized

        except TypeError:

            pass

        except Exception as error:

            self.stats[
                "prompt_failures"
            ] += 1

            self._log_error(
                "PROMPT BUILDER ERROR",
                error
            )

            return None

        # --------------------------------------------------------
        # LEGACY SIGNATURE
        # --------------------------------------------------------

        try:

            prompt = (
                self.prompt_builder.build(

                    student=student,

                    subject=subject,

                    message=message,

                    mode=mode,

                    strategy=strategy,

                    memory_context=memory_context,

                    difficulty=difficulty,

                    settings=settings
                )
            )

            normalized = (
                self._normalize_prompt(
                    prompt
                )
            )

            if normalized:

                return normalized

        except TypeError:

            pass

        except Exception as error:

            self._log_error(
                "LEGACY PROMPT BUILDER ERROR",
                error
            )

        # --------------------------------------------------------
        # MINIMAL FALLBACK
        # --------------------------------------------------------

        return self._build_emergency_prompt(
            message=message,
            subject=subject,
            topic=topic,
            mode=mode,
            memory_context=memory_context,
            difficulty=difficulty,
            settings=settings,
            strategy=strategy
        )

    # ============================================================
    # PROMPT NORMALIZATION
    # ============================================================

    def _normalize_prompt(
        self,
        prompt
    ) -> Optional[Dict[str, str]]:
        """
        Normalize PromptBuilder output.

        Expected:

            {
                "system": "...",
                "user": "..."
            }
        """

        if not isinstance(
            prompt,
            dict
        ):

            return None

        system = prompt.get(
            "system",
            ""
        )

        user = prompt.get(
            "user",
            ""
        )

        if system is None:

            system = ""

        if user is None:

            user = ""

        system = str(
            system
        ).strip()

        user = str(
            user
        ).strip()

        if not user:

            return None

        # --------------------------------------------------------
        # PROMPT SIZE PROTECTION
        # --------------------------------------------------------

        total_length = (
            len(system)
            + len(user)
        )

        if total_length > (
            self.DEFAULT_MAX_PROMPT_LENGTH
        ):

            user_limit = max(
                1000,
                self.DEFAULT_MAX_PROMPT_LENGTH
                - len(system)
            )

            user = (
                user[
                    :user_limit
                ]
                + "\n\n[Prompt truncated by Nova.]"
            )

        return {

            "system":
                system,

            "user":
                user
        }

    # ============================================================
    # EMERGENCY PROMPT
    # ============================================================

    def _build_emergency_prompt(
        self,
        message,
        subject,
        topic,
        mode,
        memory_context,
        difficulty,
        settings,
        strategy
    ) -> Dict[str, str]:
        """
        Emergency prompt used if PromptBuilder fails.

        This is deliberately simple.

        It prevents a PromptBuilder bug from making Nova completely
        unusable.
        """

        language = (
            settings.get(
                "language",
                self.DEFAULT_LANGUAGE
            )
        )

        level = (
            settings.get(
                "level",
                self.DEFAULT_LEVEL
            )
        )

        response_length = (
            settings.get(
                "response_length",
                self.DEFAULT_RESPONSE_LENGTH
            )
        )

        difficulty_name = ""

        if isinstance(
            difficulty,
            dict
        ):

            difficulty_name = (
                difficulty.get(
                    "level",
                    ""
                )
            )

        elif isinstance(
            difficulty,
            str
        ):

            difficulty_name = difficulty

        approach = "\n".join(
            f"- {item}"
            for item in strategy.get(
                "approach",
                []
            )
        )

        system = f"""
You are Nova, an adaptive educational AI tutor.

Your job is to help a student understand concepts accurately.

Student language:
{language}

Academic level:
{level}

Subject:
{subject or "general"}

Topic:
{topic or "not specified"}

Difficulty:
{difficulty_name or "adaptive"}

Response length:
{response_length}

Teaching strategy:
{approach}

Rules:
- Answer the student's actual question.
- Explain clearly.
- Do not invent facts.
- Do not pretend to know something you do not know.
- Use simple language when the student appears confused.
- Use step-by-step reasoning when useful.
- Do not unnecessarily repeat information.
"""

        user = f"""
Previous relevant context:

{memory_context}

Student message:

{message}
"""

        return {
            "system": system.strip(),
            "user": user.strip()
        }

    # ============================================================
    # PROMPT VALIDATION
    # ============================================================

    def _validate_prompt(
        self,
        prompt
    ) -> Optional[Dict[str, str]]:
        """
        Validate final prompt before sending it to the LLM.
        """

        if not isinstance(
            prompt,
            dict
        ):

            return None

        system = prompt.get(
            "system",
            ""
        )

        user = prompt.get(
            "user",
            ""
        )

        if system is None:

            system = ""

        if user is None:

            user = ""

        system = str(
            system
        ).strip()

        user = str(
            user
        ).strip()

        if not user:

            return None

        return {

            "system":
                system,

            "user":
                user
        }

    # ============================================================
    # LLM GENERATION
    # ============================================================

    def _generate(
        self,
        prompt,
        settings
    ) -> str:
        """
        Generate the final answer.

        Retries are performed when LocalLLM raises an exception.
        """

        if not isinstance(
            prompt,
            dict
        ):

            return self.FALLBACK_PROMPT_ERROR

        system_prompt = (
            str(
                prompt.get(
                    "system",
                    ""
                )
            )
            .strip()
        )

        user_prompt = (
            str(
                prompt.get(
                    "user",
                    ""
                )
            )
            .strip()
        )

        if not system_prompt:

            system_prompt = self._default_system_prompt(
                settings
            )

        if not user_prompt:

            return self.FALLBACK_EMPTY_REQUEST

        creativity = (
            self._normalize_creativity(
                settings.get(
                    "creativity"
                )
            )
        )

        attempts = (
            self.retry_count
            + 1
        )

        last_error = None

        for attempt in range(
            attempts
        ):

            self.stats[
                "llm_calls"
            ] += 1

            start = time.perf_counter()

            try:

                response = (
                    self.llm.answer(

                        system=
                            system_prompt,

                        user=
                            user_prompt,

                        creativity=
                            creativity
                    )
                )

                elapsed = (
                    time.perf_counter()
                    - start
                )

                self.stats[
                    "total_generation_time"
                ] += elapsed

                self.stats[
                    "last_generation_time"
                ] = elapsed

                if response is None:

                    raise RuntimeError(
                        "LocalLLM returned None."
                    )

                response = str(
                    response
                ).strip()

                if not response:

                    raise RuntimeError(
                        "LocalLLM returned an empty response."
                    )

                return response

            except Exception as error:

                last_error = error

                self.stats[
                    "llm_failures"
                ] += 1

                if attempt < (
                    attempts - 1
                ):

                    self.stats[
                        "llm_retries"
                    ] += 1

                    time.sleep(
                        self.retry_delay
                    )

        if last_error is not None:

            self._record_error(
                last_error
            )

            self._log_error(
                "NOVA LLM ERROR",
                last_error
            )

        return self.FALLBACK_LLM_ERROR

    # ============================================================
    # DEFAULT SYSTEM PROMPT
    # ============================================================

    def _default_system_prompt(
        self,
        settings
    ) -> str:
        """
        Fallback system prompt if PromptBuilder produces no
        system instructions.
        """

        language = (
            settings.get(
                "language",
                self.DEFAULT_LANGUAGE
            )
        )

        level = (
            settings.get(
                "level",
                self.DEFAULT_LEVEL
            )
        )

        return f"""
You are Nova, an adaptive educational AI tutor.

Student language:
{language}

Student academic level:
{level}

Your responsibilities:

1. Answer the student's actual question.
2. Prioritize accuracy.
3. Explain ideas clearly.
4. Adapt explanations to the student's level.
5. Use examples when useful.
6. Use step-by-step explanations when useful.
7. Avoid unnecessary complexity.
8. Do not invent information.
9. If information is uncertain, state that clearly.
10. Focus on helping the student understand rather than merely
    producing an answer.
""".strip()

    # ============================================================
    # RESPONSE CLEANING
    # ============================================================

    def _clean_response(
        self,
        response
    ) -> str:
        """
        Clean common accidental formatting problems.

        The method deliberately avoids rewriting the answer's
        meaning.
        """

        if response is None:

            return self.FALLBACK_RESPONSE

        response = str(
            response
        ).strip()

        if not response:

            return self.FALLBACK_RESPONSE

        # --------------------------------------------------------
        # REMOVE NULL CHARACTERS
        # --------------------------------------------------------

        response = response.replace(
            "\x00",
            ""
        )

        # --------------------------------------------------------
        # REMOVE EXCESSIVE EMPTY LINES
        # --------------------------------------------------------

        response = re.sub(
            r"\n{4,}",
            "\n\n\n",
            response
        )

        # --------------------------------------------------------
        # REMOVE OUTER CODE FENCE
        # --------------------------------------------------------

        response = (
            self._remove_outer_code_fence(
                response
            )
        )

        # --------------------------------------------------------
        # REMOVE ACCIDENTAL LEADING LABEL
        # --------------------------------------------------------

        response = (
            self._remove_accidental_prefix(
                response
            )
        )

        # --------------------------------------------------------
        # FINAL STRIP
        # --------------------------------------------------------

        response = response.strip()

        # --------------------------------------------------------
        # RESPONSE LENGTH PROTECTION
        # --------------------------------------------------------

        if len(response) > (
            self.DEFAULT_MAX_RESPONSE_LENGTH
        ):

            response = (
                response[
                    :self.DEFAULT_MAX_RESPONSE_LENGTH
                ]
                + "\n\n[Response truncated by Nova.]"
            )

        if not response:

            return self.FALLBACK_RESPONSE

        return response

    # ============================================================
    # CODE FENCE REMOVAL
    # ============================================================

    def _remove_outer_code_fence(
        self,
        response
    ) -> str:
        """
        Remove a markdown code fence if the entire response was
        accidentally wrapped in one.
        """

        if not response.startswith(
            "```"
        ):

            return response

        if not response.endswith(
            "```"
        ):

            return response

        lines = (
            response.splitlines()
        )

        if len(lines) < 3:

            return response

        first = (
            lines[0]
            .strip()
            .lower()
        )

        last = (
            lines[-1]
            .strip()
        )

        if (
            first.startswith("```")
            and last == "```"
        ):

            return (
                "\n".join(
                    lines[1:-1]
                )
                .strip()
            )

        return response

    # ============================================================
    # PREFIX CLEANING
    # ============================================================

    def _remove_accidental_prefix(
        self,
        response
    ) -> str:
        """
        Remove harmless accidental prefixes sometimes produced
        by local models.

        Only extremely obvious prefixes are removed.
        """

        prefixes = [

            "Nova's answer:",

            "Nova answer:",

            "Answer:",

            "Response:"

        ]

        for prefix in prefixes:

            if response.lower().startswith(
                prefix.lower()
            ):

                response = (
                    response[
                        len(prefix):
                    ]
                    .strip()
                )

                break

        return response

    # ============================================================
    # RESPONSE VALIDATION
    # ============================================================

    def _is_valid_response(
        self,
        response
    ) -> bool:
        """
        Basic structural validation.

        This does NOT attempt to verify factual correctness.
        That belongs to AnswerVerifier or a future verification
        subsystem.
        """

        if response is None:

            return False

        if not isinstance(
            response,
            str
        ):

            return False

        response = response.strip()

        if not response:

            return False

        if len(response) < 2:

            return False

        # --------------------------------------------------------
        # KNOWN FAILURE STRINGS
        # --------------------------------------------------------

        invalid_responses = {

            self.FALLBACK_RESPONSE.lower(),

            self.FALLBACK_LLM_ERROR.lower(),

            self.FALLBACK_PROMPT_ERROR.lower(),

            self.FALLBACK_INVALID_RESPONSE.lower()

        }

        if response.lower() in (
            invalid_responses
        ):

            return False

        return True

    # ============================================================
    # BOOLEAN NORMALIZATION
    # ============================================================

    def _to_bool(
        self,
        value,
        default=False
    ) -> bool:
        """
        Convert common values into booleans.
        """

        if isinstance(
            value,
            bool
        ):

            return value

        if value is None:

            return default

        if isinstance(
            value,
            str
        ):

            normalized = (
                value
                .strip()
                .lower()
            )

            if normalized in {
                "true",
                "yes",
                "1",
                "on",
                "enabled"
            }:

                return True

            if normalized in {
                "false",
                "no",
                "0",
                "off",
                "disabled"
            }:

                return False

        return bool(
            value
        )

    # ============================================================
    # RETRY NORMALIZATION
    # ============================================================

    def _normalize_retry_count(
        self,
        value
    ) -> int:
        """
        Normalize retry count.
        """

        if value is None:

            return self.DEFAULT_RETRY_COUNT

        try:

            value = int(
                value
            )

        except (
            TypeError,
            ValueError
        ):

            return self.DEFAULT_RETRY_COUNT

        return max(
            0,
            min(
                5,
                value
            )
        )

    # ============================================================
    # RETRY DELAY
    # ============================================================

    def _normalize_retry_delay(
        self,
        value
    ) -> float:
        """
        Normalize retry delay.
        """

        if value is None:

            return self.DEFAULT_RETRY_DELAY

        try:

            value = float(
                value
            )

        except (
            TypeError,
            ValueError
        ):

            return self.DEFAULT_RETRY_DELAY

        return max(
            0.0,
            min(
                10.0,
                value
            )
        )

    # ============================================================
    # ERROR RECORDING
    # ============================================================

    def _record_error(
        self,
        error
    ):
        """
        Store the latest error without allowing error logging
        itself to crash Nova.
        """

        try:

            self.stats[
                "last_error"
            ] = str(
                error
            )

        except Exception:

            self.stats[
                "last_error"
            ] = "Unknown error."

    # ============================================================
    # ERROR LOGGING
    # ============================================================

    def _log_error(
        self,
        title,
        error
    ):
        """
        Centralized error logging.

        Debug mode includes traceback information.
        """

        print(
            "\n"
            f"========== {title} =========="
        )

        print(
            str(
                error
            )
        )

        if self.debug:

            print(
                traceback.format_exc()
            )

        print(
            "====================================\n"
        )

    # ============================================================
    # HEALTH CHECK
    # ============================================================

    def health_check(
        self
    ) -> Dict[str, Any]:
        """
        Check the main TutorEngine dependencies.

        Returns structured diagnostic information instead of
        raising exceptions.
        """

        result = {

            "engine": True,

            "version":
                self.VERSION,

            "student": False,

            "llm": False,

            "quiz_engine": False,

            "adaptive_tutor": False,

            "prompt_builder": False,

            "stats":
                self.get_stats()
        }

        # --------------------------------------------------------
        # STUDENT
        # --------------------------------------------------------

        try:

            student = (
                self._get_student_data()
            )

            result[
                "student"
            ] = isinstance(
                student,
                dict
            )

        except Exception:

            result[
                "student"
            ] = False

        # --------------------------------------------------------
        # LLM
        # --------------------------------------------------------

        result[
            "llm"
        ] = self.llm is not None

        # --------------------------------------------------------
        # QUIZ
        # --------------------------------------------------------

        result[
            "quiz_engine"
        ] = self.quiz is not None

        # --------------------------------------------------------
        # ADAPTIVE
        # --------------------------------------------------------

        result[
            "adaptive_tutor"
        ] = self.adaptive_tutor is not None

        # --------------------------------------------------------
        # PROMPT
        # --------------------------------------------------------

        result[
            "prompt_builder"
        ] = self.prompt_builder is not None

        result[
            "healthy"
        ] = all(
            [
                result["engine"],
                result["student"],
                result["llm"],
                result["quiz_engine"],
                result["adaptive_tutor"],
                result["prompt_builder"]
            ]
        )

        return result

    # ============================================================
    # DEBUG INFORMATION
    # ============================================================

    def debug_info(
        self
    ) -> Dict[str, Any]:
        """
        Return safe diagnostic information.

        No student message or private memory is returned.
        """

        return {

            "version":
                self.VERSION,

            "retry_count":
                self.retry_count,

            "retry_delay":
                self.retry_delay,

            "debug":
                self.debug,

            "llm_class":
                type(
                    self.llm
                ).__name__,

            "student_class":
                type(
                    self.student
                ).__name__,

            "quiz_class":
                type(
                    self.quiz
                ).__name__,

            "adaptive_tutor_class":
                type(
                    self.adaptive_tutor
                ).__name__,

            "prompt_builder_class":
                type(
                    self.prompt_builder
                ).__name__,

            "stats":
                self.get_stats()
        }

    # ============================================================
    # STRATEGY SUMMARY
    # ============================================================

    def summarize_strategy(
        self,
        strategy
    ) -> Dict[str, Any]:
        """
        Return a compact summary of a NovaBrain strategy.

        Useful for debugging and UI display.
        """

        if not isinstance(
            strategy,
            dict
        ):

            return {

                "confidence":
                    50,

                "learning_state":
                    "developing",

                "difficulty":
                    "medium",

                "challenge":
                    False
            }

        confidence = (
            self._normalize_confidence(
                strategy.get(
                    "confidence",
                    50
                )
            )
        )

        return {

            "subject":
                strategy.get(
                    "subject"
                ),

            "topic":
                strategy.get(
                    "topic"
                ),

            "confidence":
                confidence,

            "learning_state":
                strategy.get(
                    "learning_state",
                    self._infer_learning_state(
                        confidence
                    )
                ),

            "difficulty":
                strategy.get(
                    "difficulty"
                ),

            "explanation_depth":
                strategy.get(
                    "explanation_depth"
                ),

            "challenge":
                self._to_bool(
                    strategy.get(
                        "challenge"
                    ),
                    False
                ),

            "reinforcement":
                self._to_bool(
                    strategy.get(
                        "reinforcement"
                    ),
                    False
                )
        }

    # ============================================================
    # RESPONSE LENGTH INSTRUCTION
    # ============================================================

    def get_response_length_instruction(
        self,
        settings
    ) -> str:
        """
        Convert response_length setting into a prompt instruction.
        """

        settings = (
            self._normalize_settings(
                settings
            )
        )

        length = (
            settings.get(
                "response_length",
                self.DEFAULT_RESPONSE_LENGTH
            )
        )

        instructions = {

            "short":
                "Keep the answer concise and focused.",

            "balanced":
                "Give enough detail to explain the idea clearly without unnecessary length.",

            "long":
                "Give a thorough explanation with useful examples and reasoning.",

            "detailed":
                "Give a detailed educational explanation with clear structure, reasoning, examples, and important nuances."
        }

        return instructions.get(
            length,
            instructions[
                "balanced"
            ]
        )

    # ============================================================
    # LANGUAGE INSTRUCTION
    # ============================================================

    def get_language_instruction(
        self,
        settings
    ) -> str:
        """
        Return a language instruction for PromptBuilder or future
        prompt systems.
        """

        settings = (
            self._normalize_settings(
                settings
            )
        )

        language = (
            settings.get(
                "language",
                self.DEFAULT_LANGUAGE
            )
        )

        return (
            f"Respond primarily in {language}."
        )

    # ============================================================
    # LEVEL INSTRUCTION
    # ============================================================

    def get_level_instruction(
        self,
        settings
    ) -> str:
        """
        Return an academic-level instruction.
        """

        settings = (
            self._normalize_settings(
                settings
            )
        )

        level = (
            settings.get(
                "level",
                self.DEFAULT_LEVEL
            )
        )

        return (
            f"Adapt the explanation to the student's academic level: {level}."
        )

    # ============================================================
    # PUBLIC VALIDATION
    # ============================================================

    def validate_message(
        self,
        message
    ) -> Dict[str, Any]:
        """
        Validate a message without generating a response.

        Useful for frontend/API layers.
        """

        normalized = (
            self._normalize_message(
                message
            )
        )

        return {

            "valid":
                bool(
                    normalized
                ),

            "length":
                len(
                    normalized
                ),

            "truncated":
                len(
                    str(
                        message
                    )
                )
                > self.DEFAULT_MAX_MESSAGE_LENGTH
                if message is not None
                else False
        }