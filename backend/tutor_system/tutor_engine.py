from typing import Any, Dict, List, Optional

from backend.llm import LocalLLM
from backend.tutor_system.quiz_engine import QuizEngine
from backend.tutor_system.adaptive_tutor import AdaptiveTutor

from student_profile import StudentProfile

from backend.prompt.prompt_builder import PromptBuilder


class TutorEngine:
    """
    Nova Tutor Engine

    This class is responsible for transforming Nova's learning
    analysis into an actual tutoring response.

    Main responsibilities
    ----------------------

    1. Receive the student's request.
    2. Receive information from NovaCore and NovaBrain.
    3. Adapt the teaching strategy to the student's current state.
    4. Build a structured prompt.
    5. Send the prompt to the local LLM.
    6. Clean and validate the generated response.
    7. Handle temporary failures without crashing NovaCore.

    TutorEngine intentionally does NOT own long-term student
    learning data.

    Long-term learning state belongs to systems such as:

        - StudentProfile
        - KnowledgeMap
        - LearningMemory
        - ProgressTracker
        - NovaBrain

    TutorEngine is the bridge between those systems and the LLM.
    """

    # =========================================================
    # CONSTANTS
    # =========================================================

    DEFAULT_CREATIVITY = "medium"

    VALID_CREATIVITY = {
        "low",
        "medium",
        "high"
    }

    DEFAULT_MODE = "normal"

    FALLBACK_RESPONSE = (
        "Nova couldn't generate a response right now."
    )

    FALLBACK_PROMPT_ERROR = (
        "Nova couldn't build the response prompt."
    )

    FALLBACK_EMPTY_REQUEST = (
        "I couldn't understand the request."
    )

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        student=None,
        brain=None,
        llm=None,
        quiz_engine=None,
        adaptive_tutor=None,
        prompt_builder=None
    ):
        """
        Initialize the TutorEngine.

        Optional dependencies can be injected for testing.

        Example:

            TutorEngine(
                student=my_student,
                llm=my_test_llm
            )

        This makes the engine easier to test without requiring
        Ollama or other external components.
        """

        print(
            "Loading Tutor Engine..."
        )

        # -----------------------------------------------------
        # STUDENT
        # -----------------------------------------------------

        if student is None:

            self.student = StudentProfile()

        else:

            self.student = student

        # -----------------------------------------------------
        # LOCAL LLM
        # -----------------------------------------------------

        if llm is None:

            self.llm = LocalLLM()

        else:

            self.llm = llm

        # -----------------------------------------------------
        # QUIZ ENGINE
        # -----------------------------------------------------

        if quiz_engine is None:

            self.quiz = QuizEngine()

        else:

            self.quiz = quiz_engine

        # -----------------------------------------------------
        # ADAPTIVE TUTOR
        # -----------------------------------------------------

        if adaptive_tutor is None:

            self.adaptive_tutor = AdaptiveTutor()

        else:

            self.adaptive_tutor = adaptive_tutor

        # -----------------------------------------------------
        # PROMPT BUILDER
        # -----------------------------------------------------

        if prompt_builder is None:

            self.prompt_builder = PromptBuilder()

        else:

            self.prompt_builder = prompt_builder

        # -----------------------------------------------------
        # OPTIONAL BRAIN
        # -----------------------------------------------------

        self.brain = brain

        print(
            "Tutor Engine ready."
        )

    # =========================================================
    # MAIN ANSWER PIPELINE
    # =========================================================

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
    ):
        """
        Generate a tutoring response.

        The pipeline is:

            normalize input
                    ↓
            detect special mode
                    ↓
            prepare strategy
                    ↓
            adaptive tutor
                    ↓
            build prompt strategy
                    ↓
            build prompt
                    ↓
            call LLM
                    ↓
            clean response
                    ↓
            return response

        Parameters
        ----------
        message:
            Student's original message.

        intent:
            Detected user intent.

        subject:
            Detected subject.

        mode:
            Tutor mode.

        memory_context:
            Relevant long-term memory.

        difficulty:
            DifficultyEngine result.

        settings:
            Student settings.

        strategy:
            NovaBrain strategy.

        topic:
            Current learning topic.

        Returns
        -------
        str
            Nova's generated response.
        """

        # =====================================================
        # NORMALIZE INPUT
        # =====================================================

        message = self._normalize_message(
            message
        )

        if not message:

            return self.FALLBACK_EMPTY_REQUEST

        mode = self._normalize_mode(
            mode
        )

        settings = self._normalize_settings(
            settings
        )

        subject = self._normalize_optional_text(
            subject
        )

        topic = self._normalize_optional_text(
            topic
        )

        # =====================================================
        # SPECIAL MODES
        # =====================================================

        if self._is_quiz_mode(mode):

            return self._create_quiz(
                subject
            )

        # =====================================================
        # PREPARE STRATEGY
        # =====================================================

        prepared_strategy = (
            self._prepare_strategy(
                strategy=strategy,
                subject=subject,
                topic=topic,
                difficulty=difficulty
            )
        )

        # =====================================================
        # ADAPTIVE TUTOR
        # =====================================================

        adaptive_instruction = (
            self._build_adaptive_instruction(
                subject=subject,
                message=message,
                strategy=prepared_strategy
            )
        )

        # =====================================================
        # COMBINE STRATEGIES
        # =====================================================

        prompt_strategy = (
            self._build_prompt_strategy(
                strategy=prepared_strategy,
                adaptive_instruction=
                    adaptive_instruction
            )
        )

        # =====================================================
        # BUILD PROMPT
        # =====================================================

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

        # =====================================================
        # GENERATE
        # =====================================================

        response = (
            self._generate(
                prompt=prompt,
                settings=settings
            )
        )

        # =====================================================
        # CLEAN
        # =====================================================

        response = (
            self._clean_response(
                response
            )
        )

        return response

    # =========================================================
    # NORMALIZATION
    # =========================================================

    def _normalize_message(
        self,
        message
    ) -> str:
        """
        Safely normalize the student's message.
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

        return message.strip()

    # ---------------------------------------------------------

    def _normalize_optional_text(
        self,
        value
    ) -> Optional[str]:
        """
        Normalize optional text fields such as subject/topic.
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

        value = value.strip()

        if not value:

            return None

        return value

    # ---------------------------------------------------------

    def _normalize_mode(
        self,
        mode
    ) -> str:
        """
        Normalize tutor mode.
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

        mode = mode.strip().lower()

        if not mode:

            return self.DEFAULT_MODE

        return mode

    # ---------------------------------------------------------

    def _normalize_settings(
        self,
        settings
    ) -> Dict[str, Any]:
        """
        Ensure settings are always represented as a dictionary.
        """

        if not isinstance(
            settings,
            dict
        ):

            return {}

        return dict(
            settings
        )

    # =========================================================
    # QUIZ SYSTEM
    # =========================================================

    def _is_quiz_mode(
        self,
        mode
    ) -> bool:
        """
        Determine whether the current request requires quiz
        generation.
        """

        return mode in {
            "quiz",
            "practice_quiz",
            "test"
        }

    # ---------------------------------------------------------

    def _create_quiz(
        self,
        subject
    ) -> str:
        """
        Generate a quiz safely.

        Quiz generation is isolated from the normal LLM
        generation pipeline.
        """

        if not subject:

            subject = "general"

        try:

            result = self.quiz.create_quiz(
                subject
            )

        except Exception as error:

            self._log_error(
                "QUIZ ENGINE ERROR",
                error
            )

            return (
                "I couldn't create the quiz right now."
            )

        if result is None:

            return (
                "I couldn't create the quiz right now."
            )

        result = str(
            result
        ).strip()

        if not result:

            return (
                "I couldn't create the quiz right now."
            )

        return result

    # =========================================================
    # STRATEGY PREPARATION
    # =========================================================

    def _prepare_strategy(
        self,
        strategy,
        subject,
        topic,
        difficulty
    ) -> Dict[str, Any]:
        """
        Normalize NovaBrain's strategy.

        This method ensures PromptBuilder always receives a
        predictable structure even if NovaBrain provides only
        partial information.
        """

        if not isinstance(
            strategy,
            dict
        ):

            strategy = {}

        strategy = dict(
            strategy
        )

        # -----------------------------------------------------
        # SUBJECT
        # -----------------------------------------------------

        if not strategy.get(
            "subject"
        ):

            strategy[
                "subject"
            ] = subject

        # -----------------------------------------------------
        # TOPIC
        # -----------------------------------------------------

        if not strategy.get(
            "topic"
        ):

            strategy[
                "topic"
            ] = topic

        # -----------------------------------------------------
        # DIFFICULTY
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # CONFIDENCE
        # -----------------------------------------------------

        confidence = strategy.get(
            "confidence",
            50
        )

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
            0,
            min(
                100,
                confidence
            )
        )

        strategy[
            "confidence"
        ] = confidence

        # -----------------------------------------------------
        # LEARNING STATE
        # -----------------------------------------------------

        strategy.setdefault(
            "learning_state",
            self._infer_learning_state(
                confidence
            )
        )

        # -----------------------------------------------------
        # EXPLANATION DEPTH
        # -----------------------------------------------------

        strategy.setdefault(
            "explanation_depth",
            self._infer_explanation_depth(
                confidence
            )
        )

        # -----------------------------------------------------
        # RESPONSE STYLE
        # -----------------------------------------------------

        strategy.setdefault(
            "response_style",
            "clear_instructional"
        )

        # -----------------------------------------------------
        # BOOLEAN SETTINGS
        # -----------------------------------------------------

        strategy[
            "use_examples"
        ] = self._to_bool(
            strategy.get(
                "use_examples",
                True
            ),
            default=True
        )

        strategy[
            "use_analogies"
        ] = self._to_bool(
            strategy.get(
                "use_analogies",
                False
            ),
            default=False
        )

        strategy[
            "step_by_step"
        ] = self._to_bool(
            strategy.get(
                "step_by_step",
                False
            ),
            default=False
        )

        strategy[
            "challenge"
        ] = self._to_bool(
            strategy.get(
                "challenge",
                False
            ),
            default=False
        )

        strategy[
            "reinforcement"
        ] = self._to_bool(
            strategy.get(
                "reinforcement",
                False
            ),
            default=False
        )

        # -----------------------------------------------------
        # APPROACH
        # -----------------------------------------------------

        approach = strategy.get(
            "approach",
            []
        )

        if approach is None:

            approach = []

        elif isinstance(
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
                str(
                    approach
                )
            ]

        strategy[
            "approach"
        ] = [
            str(item).strip()
            for item in approach
            if str(item).strip()
        ]

        return strategy

    # =========================================================
    # LEARNING STATE INFERENCE
    # =========================================================

    def _infer_learning_state(
        self,
        confidence
    ) -> str:
        """
        Convert confidence into a simple learning state.
        """

        if confidence < 30:

            return "struggling"

        if confidence < 50:

            return "developing"

        if confidence < 70:

            return "progressing"

        if confidence < 90:

            return "strong"

        return "mastery"

    # ---------------------------------------------------------

    def _infer_explanation_depth(
        self,
        confidence
    ) -> str:
        """
        Select a reasonable explanation depth based on
        demonstrated confidence.
        """

        if confidence < 40:

            return "foundational"

        if confidence < 70:

            return "balanced"

        if confidence < 90:

            return "deep"

        return "advanced"

    # =========================================================
    # ADAPTIVE TUTOR
    # =========================================================

    def _build_adaptive_instruction(
        self,
        subject,
        message,
        strategy
    ) -> str:
        """
        Ask AdaptiveTutor to determine how Nova should teach.

        IMPORTANT:

        The student's current message is passed into
        AdaptiveTutor.

        This allows explicit requests such as:

            "Explain simply."

            "I don't understand."

            "Go deeper."

            "Give me technical details."

        to override a generic student profile level.
        """

        try:

            instruction = (
                self.adaptive_tutor
                .build_instruction(
                    self.student.get(),
                    subject,
                    message=message
                )
            )

        except TypeError:

            # -------------------------------------------------
            # BACKWARDS COMPATIBILITY
            # -------------------------------------------------

            try:

                instruction = (
                    self.adaptive_tutor
                    .build_instruction(
                        self.student.get(),
                        subject
                    )
                )

            except Exception as error:

                self._log_error(
                    "ADAPTIVE TUTOR ERROR",
                    error
                )

                instruction = ""

        except Exception as error:

            self._log_error(
                "ADAPTIVE TUTOR ERROR",
                error
            )

            instruction = ""

        if instruction is None:

            return ""

        return str(
            instruction
        ).strip()

    # =========================================================
    # PROMPT STRATEGY
    # =========================================================

    def _build_prompt_strategy(
        self,
        strategy,
        adaptive_instruction
    ) -> Dict[str, Any]:
        """
        Merge NovaBrain's strategy with AdaptiveTutor's
        teaching instruction.
        """

        result = dict(
            strategy
        )

        result[
            "adaptive_instruction"
        ] = adaptive_instruction

        # -----------------------------------------------------
        # APPROACH
        # -----------------------------------------------------

        approach = result.get(
            "approach",
            []
        )

        if not isinstance(
            approach,
            list
        ):

            approach = [
                str(
                    approach
                )
            ]

        # -----------------------------------------------------
        # AUTOMATIC EXAMPLES
        # -----------------------------------------------------

        if result.get(
            "use_examples"
        ):

            approach.append(
                "Use concrete examples when they improve understanding."
            )

        # -----------------------------------------------------
        # AUTOMATIC ANALOGIES
        # -----------------------------------------------------

        if result.get(
            "use_analogies"
        ):

            approach.append(
                "Use a simple analogy when it genuinely clarifies the concept."
            )

        # -----------------------------------------------------
        # STEP-BY-STEP
        # -----------------------------------------------------

        if result.get(
            "step_by_step"
        ):

            approach.append(
                "Break the explanation into clear logical steps."
            )

        # -----------------------------------------------------
        # REINFORCEMENT
        # -----------------------------------------------------

        if result.get(
            "reinforcement"
        ):

            approach.append(
                "Reinforce fundamental ideas before introducing harder material."
            )

        # -----------------------------------------------------
        # CHALLENGE
        # -----------------------------------------------------

        if result.get(
            "challenge"
        ):

            approach.append(
                "Include a small reasoning challenge when appropriate."
            )

        # -----------------------------------------------------
        # DIFFICULTY INSTRUCTION
        # -----------------------------------------------------

        difficulty_instruction = (
            result.get(
                "difficulty_instruction"
            )
        )

        if difficulty_instruction:

            approach.append(
                str(
                    difficulty_instruction
                )
            )

        # -----------------------------------------------------
        # ADAPTIVE INSTRUCTION
        # -----------------------------------------------------

        if adaptive_instruction:

            approach.append(
                adaptive_instruction
            )

        # -----------------------------------------------------
        # REMOVE DUPLICATES
        # -----------------------------------------------------

        unique = []

        seen = set()

        for item in approach:

            item = str(
                item
            ).strip()

            if not item:

                continue

            normalized = (
                item.lower()
            )

            if normalized in seen:

                continue

            seen.add(
                normalized
            )

            unique.append(
                item
            )

        result[
            "approach"
        ] = unique

        return result

    # =========================================================
    # PROMPT BUILDING
    # =========================================================

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
    ) -> Dict[str, Any]:
        """
        Build the final prompt.

        PromptBuilder owns the actual prompt architecture.

        TutorEngine only prepares the information it needs.
        """

        if memory_context is None:

            memory_context = (
                "No previous discussion."
            )

        # -----------------------------------------------------
        # MODERN PROMPT BUILDER
        # -----------------------------------------------------

        try:

            prompt = (
                self.prompt_builder.build(

                    student=
                        self.student.get(),

                    subject=
                        subject,

                    topic=
                        topic,

                    message=
                        message,

                    intent=
                        intent,

                    mode=
                        mode,

                    strategy=
                        strategy,

                    memory_context=
                        memory_context,

                    difficulty=
                        difficulty,

                    settings=
                        settings
                )
            )

            if isinstance(
                prompt,
                dict
            ):

                return prompt

        except TypeError:

            # The installed PromptBuilder may still use the
            # older function signature.

            pass

        except Exception as error:

            self._log_error(
                "PROMPT BUILDER ERROR",
                error
            )

            return {
                "system": "",
                "user": ""
            }

        # -----------------------------------------------------
        # BACKWARDS COMPATIBILITY
        # -----------------------------------------------------

        try:

            prompt = (
                self.prompt_builder.build(

                    student=
                        self.student.get(),

                    subject=
                        subject,

                    message=
                        message,

                    mode=
                        mode,

                    strategy=
                        strategy,

                    memory_context=
                        memory_context,

                    difficulty=
                        difficulty,

                    settings=
                        settings
                )
            )

            if isinstance(
                prompt,
                dict
            ):

                return prompt

        except Exception as error:

            self._log_error(
                "LEGACY PROMPT BUILDER ERROR",
                error
            )

        return {
            "system": "",
            "user": ""
        }

    # =========================================================
    # LLM GENERATION
    # =========================================================

    def _generate(
        self,
        prompt,
        settings
    ) -> str:
        """
        Send the prepared prompt to the local LLM.
        """

        if not isinstance(
            prompt,
            dict
        ):

            return self.FALLBACK_PROMPT_ERROR

        # -----------------------------------------------------
        # SYSTEM PROMPT
        # -----------------------------------------------------

        system_prompt = prompt.get(
            "system",
            ""
        )

        # -----------------------------------------------------
        # USER PROMPT
        # -----------------------------------------------------

        user_prompt = prompt.get(
            "user",
            ""
        )

        if system_prompt is None:

            system_prompt = ""

        if user_prompt is None:

            user_prompt = ""

        system_prompt = str(
            system_prompt
        ).strip()

        user_prompt = str(
            user_prompt
        ).strip()

        # -----------------------------------------------------
        # FALLBACK SYSTEM PROMPT
        # -----------------------------------------------------

        if not system_prompt:

            system_prompt = """
You are Nova, an adaptive educational AI tutor.

Answer the student's current question clearly,
accurately, and at an appropriate level.

Do not invent information.
"""

        # -----------------------------------------------------
        # EMPTY USER REQUEST
        # -----------------------------------------------------

        if not user_prompt:

            return self.FALLBACK_EMPTY_REQUEST

        # -----------------------------------------------------
        # CREATIVITY
        # -----------------------------------------------------

        creativity = (
            settings.get(
                "creativity",
                self.DEFAULT_CREATIVITY
            )
        )

        if not isinstance(
            creativity,
            str
        ):

            creativity = (
                self.DEFAULT_CREATIVITY
            )

        creativity = (
            creativity.strip().lower()
        )

        if creativity not in self.VALID_CREATIVITY:

            creativity = (
                self.DEFAULT_CREATIVITY
            )

        # -----------------------------------------------------
        # LLM CALL
        # -----------------------------------------------------

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

        except Exception as error:

            self._log_error(
                "NOVA LLM ERROR",
                error
            )

            return self.FALLBACK_RESPONSE

        # -----------------------------------------------------
        # VALIDATE RESULT
        # -----------------------------------------------------

        if response is None:

            return self.FALLBACK_RESPONSE

        response = str(
            response
        ).strip()

        if not response:

            return self.FALLBACK_RESPONSE

        return response

    # =========================================================
    # RESPONSE CLEANING
    # =========================================================

    def _clean_response(
        self,
        response
    ) -> str:
        """
        Clean common accidental formatting problems.

        This method deliberately avoids aggressive rewriting.

        The LLM's actual content should remain intact.
        """

        if response is None:

            return self.FALLBACK_RESPONSE

        response = str(
            response
        ).strip()

        if not response:

            return self.FALLBACK_RESPONSE

        # -----------------------------------------------------
        # REMOVE ACCIDENTAL OUTER CODE FENCE
        # -----------------------------------------------------

        if (
            response.startswith("```")
            and response.endswith("```")
        ):

            lines = (
                response.splitlines()
            )

            if len(lines) >= 3:

                first_line = (
                    lines[0]
                    .strip()
                    .lower()
                )

                last_line = (
                    lines[-1]
                    .strip()
                )

                if (
                    first_line.startswith("```")
                    and last_line == "```"
                ):

                    response = (
                        "\n".join(
                            lines[1:-1]
                        )
                        .strip()
                    )

        # -----------------------------------------------------
        # FINAL VALIDATION
        # -----------------------------------------------------

        if not response:

            return self.FALLBACK_RESPONSE

        return response

    # =========================================================
    # SIMPLE ANSWER
    # =========================================================

    def simple_answer(
        self,
        message,
        subject=None,
        mode="normal",
        settings=None
    ) -> str:
        """
        Convenience method for callers that do not have
        the complete NovaCore pipeline.

        Useful for:

            - quick tests
            - development
            - debugging
            - small scripts
            - terminal testing
        """

        return self.answer(

            message=
                message,

            intent=
                None,

            subject=
                subject,

            mode=
                mode,

            memory_context=
                None,

            difficulty=
                None,

            settings=
                settings,

            strategy=
                None,

            topic=
                None
        )

    # =========================================================
    # UTILITY METHODS
    # =========================================================

    def _to_bool(
        self,
        value,
        default=False
    ) -> bool:
        """
        Safely convert common values into booleans.
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
                value.strip().lower()
            )

            if normalized in {
                "true",
                "yes",
                "1",
                "on"
            }:

                return True

            if normalized in {
                "false",
                "no",
                "0",
                "off"
            }:

                return False

        return bool(
            value
        )

    # ---------------------------------------------------------

    def _log_error(
        self,
        title,
        error
    ):
        """
        Centralized error logging.

        Keeps terminal debugging readable while avoiding
        exceptions escaping from optional tutoring components.
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

        print(
            "====================================\n"
        )