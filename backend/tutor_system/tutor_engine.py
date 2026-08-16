from typing import Any, Dict, List, Optional
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

    Central tutoring pipeline between Nova's learning systems and
    the local language model.

    Architecture:

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

    TutorEngine is intentionally NON-STREAMING.

    LocalLLM.answer() is responsible for one complete LLM response.
    API-level streaming belongs to backend.api and should wrap the
    completed response rather than making TutorEngine itself stream.

    ================================================================
    """

    VERSION = "1.0.1"

    # ============================================================
    # DEFAULTS
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
        "high",
    }

    VALID_RESPONSE_LENGTHS = {
        "short",
        "balanced",
        "long",
        "detailed",
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
        "deep",
    }

    QUIZ_MODES = {
        "quiz",
        "practice_quiz",
        "test",
    }

    SIMPLE_MODES = {
        "simple",
    }

    DEEP_MODES = {
        "deep",
        "challenge",
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
        debug=False,
    ):
        print("Loading Tutor Engine...")

        self.debug = bool(debug)

        self.retry_count = self._normalize_retry_count(
            retry_count
        )

        self.retry_delay = self._normalize_retry_delay(
            retry_delay
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
        # LLM
        # --------------------------------------------------------

        self.llm = (
            llm
            if llm is not None
            else LocalLLM()
        )

        # --------------------------------------------------------
        # QUIZ
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
        # STATISTICS
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
            "last_error": None,
        }

        print("Tutor Engine ready.")

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
        topic=None,
    ) -> str:

        start_time = time.perf_counter()

        self.stats["requests"] += 1

        try:
            # ----------------------------------------------------
            # MESSAGE
            # ----------------------------------------------------

            message = self._normalize_message(message)

            if not message:
                self.stats["empty_requests"] += 1
                return self.FALLBACK_EMPTY_REQUEST

            # ----------------------------------------------------
            # INPUTS
            # ----------------------------------------------------

            mode = self._normalize_mode(mode)

            subject = self._normalize_optional_text(subject)
            topic = self._normalize_optional_text(topic)
            intent = self._normalize_optional_text(intent)

            memory_context = self._normalize_memory_context(
                memory_context
            )

            settings = self._normalize_settings(settings)

            # ----------------------------------------------------
            # MODE SETTINGS
            # ----------------------------------------------------

            settings = self._apply_mode_settings(
                settings,
                mode,
            )

            # ----------------------------------------------------
            # QUIZ
            # ----------------------------------------------------

            if self._is_quiz_mode(mode):
                self.stats["quiz_requests"] += 1

                result = self._create_quiz(subject)

                if result == self.FALLBACK_QUIZ_ERROR:
                    self.stats["quiz_failures"] += 1
                else:
                    self.stats["successful_requests"] += 1

                return result

            # ----------------------------------------------------
            # STRATEGY
            # ----------------------------------------------------

            prepared_strategy = self._prepare_strategy(
                strategy=strategy,
                subject=subject,
                topic=topic,
                difficulty=difficulty,
                settings=settings,
                mode=mode,
            )

            # ----------------------------------------------------
            # ADAPTIVE INSTRUCTION
            # ----------------------------------------------------

            adaptive_instruction = (
                self._build_adaptive_instruction(
                    subject=subject,
                    message=message,
                    strategy=prepared_strategy,
                )
            )

            # ----------------------------------------------------
            # MERGE STRATEGY
            # ----------------------------------------------------

            prompt_strategy = self._build_prompt_strategy(
                strategy=prepared_strategy,
                adaptive_instruction=adaptive_instruction,
                mode=mode,
            )

            # ----------------------------------------------------
            # BUILD PROMPT
            # ----------------------------------------------------

            prompt = self._build_prompt(
                message=message,
                intent=intent,
                subject=subject,
                topic=topic,
                mode=mode,
                memory_context=memory_context,
                difficulty=difficulty,
                settings=settings,
                strategy=prompt_strategy,
            )

            prompt = self._validate_prompt(prompt)

            if not prompt:
                self.stats["prompt_failures"] += 1
                return self.FALLBACK_PROMPT_ERROR

            # ----------------------------------------------------
            # GENERATE
            # ----------------------------------------------------

            response = self._generate(
                prompt=prompt,
                settings=settings,
            )

            # ----------------------------------------------------
            # CLEAN
            # ----------------------------------------------------

            response = self._clean_response(response)

            # ----------------------------------------------------
            # VALIDATE
            # ----------------------------------------------------

            if not self._is_valid_response(response):
                self.stats["validation_failures"] += 1
                return self.FALLBACK_INVALID_RESPONSE

            # ----------------------------------------------------
            # SUCCESS
            # ----------------------------------------------------

            self.stats["successful_requests"] += 1

            return response

        except Exception as error:
            self.stats["failed_requests"] += 1

            self._record_error(error)

            self._log_error(
                "TUTOR ENGINE ERROR",
                error,
            )

            return self.FALLBACK_RESPONSE

        finally:
            elapsed = time.perf_counter() - start_time

            self.stats["last_generation_time"] = elapsed

    # ============================================================
    # SIMPLE API
    # ============================================================

    def simple_answer(
        self,
        message,
        subject=None,
        mode="normal",
        settings=None,
    ) -> str:

        return self.answer(
            message=message,
            intent=None,
            subject=subject,
            mode=mode,
            memory_context=None,
            difficulty=None,
            settings=settings,
            strategy=None,
            topic=None,
        )

    # ============================================================
    # LLM TEST
    # ============================================================

    def test_llm(self) -> Dict[str, Any]:

        start = time.perf_counter()

        try:
            response = self.llm.answer(
                system=(
                    "You are testing Nova's local language model."
                ),
                user=(
                    "Reply with exactly: NOVA_LLM_OK"
                ),
                creativity="low",
            )

            elapsed = time.perf_counter() - start

            valid = (
                response is not None
                and bool(str(response).strip())
            )

            return {
                "success": valid,
                "response": (
                    str(response).strip()
                    if response is not None
                    else ""
                ),
                "duration": round(elapsed, 3),
            }

        except Exception as error:

            return {
                "success": False,
                "response": "",
                "duration": round(
                    time.perf_counter() - start,
                    3,
                ),
                "error": str(error),
            }

    # ============================================================
    # STATISTICS
    # ============================================================

    def get_stats(self) -> Dict[str, Any]:

        result = dict(self.stats)

        requests = result.get("requests", 0)
        successful = result.get(
            "successful_requests",
            0,
        )

        if requests:
            result["success_rate"] = round(
                (successful / requests) * 100,
                2,
            )
        else:
            result["success_rate"] = 0.0

        return result

    def reset_stats(self):

        for key in list(self.stats.keys()):

            if key in {
                "total_generation_time",
                "last_generation_time",
            }:
                self.stats[key] = 0.0

            elif key == "last_error":
                self.stats[key] = None

            else:
                self.stats[key] = 0

    # ============================================================
    # NORMALIZATION
    # ============================================================

    def _normalize_message(self, message) -> str:

        if message is None:
            return ""

        if not isinstance(message, str):
            message = str(message)

        message = (
            message
            .replace("\x00", "")
            .strip()
        )

        if len(message) > self.DEFAULT_MAX_MESSAGE_LENGTH:
            message = (
                message[:self.DEFAULT_MAX_MESSAGE_LENGTH]
                + "\n\n[Message truncated by Nova.]"
            )

        return message

    def _normalize_optional_text(
        self,
        value,
    ) -> Optional[str]:

        if value is None:
            return None

        if not isinstance(value, str):
            value = str(value)

        value = (
            value
            .replace("\x00", "")
            .strip()
        )

        return value or None

    def _normalize_mode(self, mode) -> str:

        if mode is None:
            return self.DEFAULT_MODE

        if not isinstance(mode, str):
            mode = str(mode)

        mode = mode.strip().lower()

        return mode or self.DEFAULT_MODE

    def _normalize_settings(
        self,
        settings,
    ) -> Dict[str, Any]:

        if not isinstance(settings, dict):
            settings = {}

        result = dict(settings)

        result.setdefault(
            "language",
            self.DEFAULT_LANGUAGE,
        )

        result.setdefault(
            "level",
            self.DEFAULT_LEVEL,
        )

        result["response_length"] = (
            self._normalize_response_length(
                result.get(
                    "response_length",
                    self.DEFAULT_RESPONSE_LENGTH,
                )
            )
        )

        result["creativity"] = (
            self._normalize_creativity(
                result.get(
                    "creativity",
                    self.DEFAULT_CREATIVITY,
                )
            )
        )

        return result

    def _normalize_creativity(
        self,
        creativity,
    ) -> str:

        if not isinstance(creativity, str):
            return self.DEFAULT_CREATIVITY

        creativity = creativity.strip().lower()

        if creativity not in self.VALID_CREATIVITY:
            return self.DEFAULT_CREATIVITY

        return creativity

    def _normalize_response_length(
        self,
        value,
    ) -> str:

        if not isinstance(value, str):
            return self.DEFAULT_RESPONSE_LENGTH

        value = value.strip().lower()

        if value not in self.VALID_RESPONSE_LENGTHS:
            return self.DEFAULT_RESPONSE_LENGTH

        return value

    def _normalize_memory_context(
        self,
        memory_context,
    ) -> str:

        if memory_context is None:
            return "No previous discussion."

        if not isinstance(memory_context, str):
            memory_context = str(memory_context)

        memory_context = (
            memory_context
            .replace("\x00", "")
            .strip()
        )

        if not memory_context:
            return "No previous discussion."

        if len(memory_context) > self.DEFAULT_MAX_MEMORY_LENGTH:
            memory_context = (
                memory_context[:self.DEFAULT_MAX_MEMORY_LENGTH]
                + "\n\n[Memory context truncated by Nova.]"
            )

        return memory_context

    # ============================================================
    # MODE
    # ============================================================

    def _apply_mode_settings(
        self,
        settings,
        mode,
    ) -> Dict[str, Any]:

        settings = dict(settings)

        if mode in self.SIMPLE_MODES:
            settings["response_length"] = "short"
            settings["step_by_step"] = True

        elif mode in self.DEEP_MODES:
            settings["response_length"] = "detailed"
            settings["creativity"] = "medium"

        return settings

    def _is_quiz_mode(self, mode) -> bool:
        return mode in self.QUIZ_MODES

    # ============================================================
    # QUIZ
    # ============================================================

    def _create_quiz(self, subject) -> str:

        subject = subject or self.DEFAULT_SUBJECT

        try:
            result = self.quiz.create_quiz(subject)

        except Exception as error:

            self._record_error(error)

            self._log_error(
                "QUIZ ENGINE ERROR",
                error,
            )

            return self.FALLBACK_QUIZ_ERROR

        if result is None:
            return self.FALLBACK_QUIZ_ERROR

        result = str(result).strip()

        return result or self.FALLBACK_QUIZ_ERROR

    # ============================================================
    # STRATEGY
    # ============================================================

    def _prepare_strategy(
        self,
        strategy,
        subject,
        topic,
        difficulty,
        settings,
        mode,
    ) -> Dict[str, Any]:

        if not isinstance(strategy, dict):
            strategy = {}

        result = dict(strategy)

        if not result.get("subject"):
            result["subject"] = subject

        if not result.get("topic"):
            result["topic"] = topic

        result["mode"] = mode

        self._merge_difficulty(
            result,
            difficulty,
        )

        confidence = self._normalize_confidence(
            result.get("confidence", 50)
        )

        result["confidence"] = confidence

        result.setdefault(
            "learning_state",
            self._infer_learning_state(confidence),
        )

        result.setdefault(
            "explanation_depth",
            self._infer_explanation_depth(confidence),
        )

        result.setdefault(
            "response_style",
            "clear_instructional",
        )

        result["use_examples"] = self._to_bool(
            result.get("use_examples", True),
            True,
        )

        result["use_analogies"] = self._to_bool(
            result.get("use_analogies", False),
            False,
        )

        result["step_by_step"] = self._to_bool(
            result.get("step_by_step", False),
            False,
        )

        result["challenge"] = self._to_bool(
            result.get("challenge", False),
            False,
        )

        result["reinforcement"] = self._to_bool(
            result.get("reinforcement", False),
            False,
        )

        if settings.get("use_examples") is not None:
            result["use_examples"] = self._to_bool(
                settings.get("use_examples"),
                result["use_examples"],
            )

        if settings.get("use_analogies") is not None:
            result["use_analogies"] = self._to_bool(
                settings.get("use_analogies"),
                result["use_analogies"],
            )

        if settings.get("step_by_step") is not None:
            result["step_by_step"] = self._to_bool(
                settings.get("step_by_step"),
                result["step_by_step"],
            )

        result["approach"] = self._normalize_approach(
            result.get("approach")
        )

        result.setdefault(
            "challenge_level",
            self._infer_challenge_level(confidence),
        )

        result["response_length"] = (
            self._normalize_response_length(
                settings.get(
                    "response_length",
                    self.DEFAULT_RESPONSE_LENGTH,
                )
            )
        )

        return result

    def _merge_difficulty(
        self,
        strategy,
        difficulty,
    ):

        if isinstance(difficulty, dict):

            if not strategy.get("difficulty"):
                strategy["difficulty"] = difficulty.get(
                    "level"
                )

            strategy["tracking_difficulty"] = (
                difficulty.get("tracking_level")
            )

            strategy["difficulty_stage"] = (
                difficulty.get("stage")
            )

            strategy["difficulty_instruction"] = (
                difficulty.get("instruction", "")
            )

        elif isinstance(difficulty, str):

            if not strategy.get("difficulty"):
                strategy["difficulty"] = difficulty

    def _normalize_confidence(
        self,
        confidence,
    ) -> float:

        try:
            confidence = float(confidence)

        except (TypeError, ValueError):
            confidence = 50.0

        if 0 <= confidence <= 1:
            confidence *= 100

        confidence = max(
            0,
            min(100, confidence),
        )

        return round(confidence, 2)

    def _normalize_approach(
        self,
        approach,
    ) -> List[str]:

        if approach is None:
            return []

        if isinstance(approach, str):
            approach = [approach]

        elif not isinstance(approach, list):
            approach = [approach]

        result = []
        seen = set()

        for item in approach:

            if item is None:
                continue

            item = str(item).strip()

            if not item:
                continue

            key = item.lower()

            if key in seen:
                continue

            seen.add(key)
            result.append(item)

        return result

    def _infer_learning_state(
        self,
        confidence,
    ) -> str:

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

    def _infer_explanation_depth(
        self,
        confidence,
    ) -> str:

        if confidence < 30:
            return "very_basic"

        if confidence < 50:
            return "basic"

        if confidence < 70:
            return "balanced"

        if confidence < 85:
            return "deep"

        return "advanced"

    def _infer_challenge_level(
        self,
        confidence,
    ) -> str:

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
        strategy,
    ) -> str:

        try:

            student_data = self._get_student_data()

            try:

                instruction = (
                    self.adaptive_tutor.build_instruction(
                        student_data,
                        subject,
                        message=message,
                    )
                )

            except TypeError:

                instruction = (
                    self.adaptive_tutor.build_instruction(
                        student_data,
                        subject,
                    )
                )

            if instruction is None:
                return ""

            return str(instruction).strip()

        except Exception as error:

            self.stats["adaptive_failures"] += 1

            self._record_error(error)

            self._log_error(
                "ADAPTIVE TUTOR ERROR",
                error,
            )

            return ""

    # ============================================================
    # STUDENT
    # ============================================================

    def _get_student_data(self) -> Dict[str, Any]:

        try:

            if hasattr(self.student, "get"):

                data = self.student.get()

            elif hasattr(self.student, "profile"):

                data = self.student.profile

            else:

                data = {}

        except Exception as error:

            self._log_error(
                "STUDENT PROFILE ERROR",
                error,
            )

            data = {}

        if not isinstance(data, dict):
            return {}

        return dict(data)

    # ============================================================
    # PROMPT STRATEGY
    # ============================================================

    def _build_prompt_strategy(
        self,
        strategy,
        adaptive_instruction,
        mode,
    ) -> Dict[str, Any]:

        result = dict(strategy)

        approach = self._normalize_approach(
            result.get("approach")
        )

        if result.get("use_examples"):
            approach.append(
                "Use a concrete example when it improves understanding."
            )

        if result.get("use_analogies"):
            approach.append(
                "Use a simple analogy only when it genuinely clarifies the concept."
            )

        if result.get("step_by_step"):
            approach.append(
                "Break complex reasoning into clear logical steps."
            )

        if result.get("reinforcement"):
            approach.append(
                "Reinforce important fundamentals before moving to harder material."
            )

        if result.get("challenge"):
            approach.append(
                "Add a small reasoning challenge when appropriate."
            )

        difficulty_instruction = result.get(
            "difficulty_instruction"
        )

        if difficulty_instruction:
            approach.append(
                str(difficulty_instruction).strip()
            )

        if adaptive_instruction:
            approach.append(
                adaptive_instruction
            )

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

        result["approach"] = self._normalize_approach(
            approach
        )

        result["adaptive_instruction"] = (
            adaptive_instruction or ""
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
        strategy,
    ) -> Optional[Dict[str, str]]:

        student = self._get_student_data()

        # --------------------------------------------------------
        # MODERN PROMPT BUILDER
        # --------------------------------------------------------

        try:

            prompt = self.prompt_builder.build(
                student=student,
                subject=subject,
                topic=topic,
                message=message,
                intent=intent,
                mode=mode,
                strategy=strategy,
                memory_context=memory_context,
                difficulty=difficulty,
                settings=settings,
            )

            normalized = self._normalize_prompt(prompt)

            if normalized:
                return normalized

        except TypeError:
            pass

        except Exception as error:

            self.stats["prompt_failures"] += 1

            self._log_error(
                "PROMPT BUILDER ERROR",
                error,
            )

            return None

        # --------------------------------------------------------
        # LEGACY PROMPT BUILDER
        # --------------------------------------------------------

        try:

            prompt = self.prompt_builder.build(
                student=student,
                subject=subject,
                message=message,
                mode=mode,
                strategy=strategy,
                memory_context=memory_context,
                difficulty=difficulty,
                settings=settings,
            )

            normalized = self._normalize_prompt(prompt)

            if normalized:
                return normalized

        except TypeError:
            pass

        except Exception as error:

            self._log_error(
                "LEGACY PROMPT BUILDER ERROR",
                error,
            )

        # --------------------------------------------------------
        # EMERGENCY PROMPT
        # --------------------------------------------------------

        return self._build_emergency_prompt(
            message=message,
            subject=subject,
            topic=topic,
            mode=mode,
            memory_context=memory_context,
            difficulty=difficulty,
            settings=settings,
            strategy=strategy,
        )

    # ============================================================
    # PROMPT NORMALIZATION
    # ============================================================

    def _normalize_prompt(
        self,
        prompt,
    ) -> Optional[Dict[str, str]]:

        if not isinstance(prompt, dict):
            return None

        system = prompt.get("system", "")
        user = prompt.get("user", "")

        if system is None:
            system = ""

        if user is None:
            user = ""

        system = str(system).strip()
        user = str(user).strip()

        if not user:
            return None

        total_length = len(system) + len(user)

        if total_length > self.DEFAULT_MAX_PROMPT_LENGTH:

            user_limit = max(
                1000,
                self.DEFAULT_MAX_PROMPT_LENGTH
                - len(system),
            )

            user = (
                user[:user_limit]
                + "\n\n[Prompt truncated by Nova.]"
            )

        return {
            "system": system,
            "user": user,
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
        strategy,
    ) -> Dict[str, str]:

        language = settings.get(
            "language",
            self.DEFAULT_LANGUAGE,
        )

        level = settings.get(
            "level",
            self.DEFAULT_LEVEL,
        )

        response_length = settings.get(
            "response_length",
            self.DEFAULT_RESPONSE_LENGTH,
        )

        difficulty_name = ""

        if isinstance(difficulty, dict):

            difficulty_name = difficulty.get(
                "level",
                "",
            )

        elif isinstance(difficulty, str):

            difficulty_name = difficulty

        approach = "\n".join(
            f"- {item}"
            for item in strategy.get(
                "approach",
                [],
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
""".strip()

        user = f"""
Previous relevant context:

{memory_context}

Student message:

{message}
""".strip()

        return {
            "system": system,
            "user": user,
        }

    # ============================================================
    # PROMPT VALIDATION
    # ============================================================

    def _validate_prompt(
        self,
        prompt,
    ) -> Optional[Dict[str, str]]:

        if not isinstance(prompt, dict):
            return None

        system = prompt.get("system", "")
        user = prompt.get("user", "")

        if system is None:
            system = ""

        if user is None:
            user = ""

        system = str(system).strip()
        user = str(user).strip()

        if not user:
            return None

        return {
            "system": system,
            "user": user,
        }

    # ============================================================
    # LLM GENERATION
    # ============================================================

    def _generate(
        self,
        prompt,
        settings,
    ) -> str:
        """
        Generate ONE complete response through LocalLLM.

        IMPORTANT:
        TutorEngine does not use streaming here.

        LocalLLM.answer() already communicates with Ollama using
        stream=False. API streaming is handled separately by
        backend.api.
        """

        if not isinstance(prompt, dict):
            return self.FALLBACK_PROMPT_ERROR

        system_prompt = str(
            prompt.get("system", "")
        ).strip()

        user_prompt = str(
            prompt.get("user", "")
        ).strip()

        if not system_prompt:
            system_prompt = self._default_system_prompt(
                settings
            )

        if not user_prompt:
            return self.FALLBACK_EMPTY_REQUEST

        creativity = self._normalize_creativity(
            settings.get(
                "creativity",
                self.DEFAULT_CREATIVITY,
            )
        )

        attempts = self.retry_count + 1

        last_error = None

        for attempt in range(attempts):

            self.stats["llm_calls"] += 1

            start = time.perf_counter()

            try:

                response = self.llm.answer(
                    system=system_prompt,
                    user=user_prompt,
                    creativity=creativity,
                )

                elapsed = time.perf_counter() - start

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

                response = str(response).strip()

                if not response:
                    raise RuntimeError(
                        "LocalLLM returned an empty response."
                    )

                return response

            except Exception as error:

                last_error = error

                self.stats["llm_failures"] += 1

                if attempt < attempts - 1:

                    self.stats["llm_retries"] += 1

                    if self.retry_delay > 0:
                        time.sleep(
                            self.retry_delay
                        )

        if last_error is not None:

            self._record_error(last_error)

            self._log_error(
                "NOVA LLM ERROR",
                last_error,
            )

        return self.FALLBACK_LLM_ERROR

    # ============================================================
    # DEFAULT SYSTEM PROMPT
    # ============================================================

    def _default_system_prompt(
        self,
        settings,
    ) -> str:

        language = settings.get(
            "language",
            self.DEFAULT_LANGUAGE,
        )

        level = settings.get(
            "level",
            self.DEFAULT_LEVEL,
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
        response,
    ) -> str:

        if response is None:
            return self.FALLBACK_RESPONSE

        response = str(response).strip()

        if not response:
            return self.FALLBACK_RESPONSE

        response = response.replace(
            "\x00",
            "",
        )

        response = re.sub(
            r"\n{4,}",
            "\n\n\n",
            response,
        )

        response = self._remove_outer_code_fence(
            response
        )

        response = self._remove_accidental_prefix(
            response
        )

        response = response.strip()

        if len(response) > self.DEFAULT_MAX_RESPONSE_LENGTH:

            response = (
                response[:self.DEFAULT_MAX_RESPONSE_LENGTH]
                + "\n\n[Response truncated by Nova.]"
            )

        return response or self.FALLBACK_RESPONSE

    def _remove_outer_code_fence(
        self,
        response,
    ) -> str:

        if not response.startswith("```"):
            return response

        if not response.endswith("```"):
            return response

        lines = response.splitlines()

        if len(lines) < 3:
            return response

        first = lines[0].strip().lower()
        last = lines[-1].strip()

        if first.startswith("```") and last == "```":

            return "\n".join(
                lines[1:-1]
            ).strip()

        return response

    def _remove_accidental_prefix(
        self,
        response,
    ) -> str:

        prefixes = [
            "Nova's answer:",
            "Nova answer:",
            "Answer:",
            "Response:",
        ]

        for prefix in prefixes:

            if response.lower().startswith(
                prefix.lower()
            ):

                response = response[
                    len(prefix):
                ].strip()

                break

        return response

    # ============================================================
    # RESPONSE VALIDATION
    # ============================================================

    def _is_valid_response(
        self,
        response,
    ) -> bool:

        if response is None:
            return False

        if not isinstance(response, str):
            return False

        response = response.strip()

        if not response:
            return False

        if len(response) < 2:
            return False

        invalid_responses = {
            self.FALLBACK_RESPONSE.lower(),
            self.FALLBACK_LLM_ERROR.lower(),
            self.FALLBACK_PROMPT_ERROR.lower(),
            self.FALLBACK_INVALID_RESPONSE.lower(),
        }

        if response.lower() in invalid_responses:
            return False

        return True

    # ============================================================
    # BOOLEAN
    # ============================================================

    def _to_bool(
        self,
        value,
        default=False,
    ) -> bool:

        if isinstance(value, bool):
            return value

        if value is None:
            return default

        if isinstance(value, str):

            normalized = value.strip().lower()

            if normalized in {
                "true",
                "yes",
                "1",
                "on",
                "enabled",
            }:
                return True

            if normalized in {
                "false",
                "no",
                "0",
                "off",
                "disabled",
            }:
                return False

        return bool(value)

    # ============================================================
    # RETRIES
    # ============================================================

    def _normalize_retry_count(
        self,
        value,
    ) -> int:

        if value is None:
            return self.DEFAULT_RETRY_COUNT

        try:
            value = int(value)

        except (TypeError, ValueError):
            return self.DEFAULT_RETRY_COUNT

        return max(
            0,
            min(5, value),
        )

    def _normalize_retry_delay(
        self,
        value,
    ) -> float:

        if value is None:
            return self.DEFAULT_RETRY_DELAY

        try:
            value = float(value)

        except (TypeError, ValueError):
            return self.DEFAULT_RETRY_DELAY

        return max(
            0.0,
            min(10.0, value),
        )

    # ============================================================
    # ERROR HANDLING
    # ============================================================

    def _record_error(
        self,
        error,
    ):

        try:

            self.stats["last_error"] = str(error)

        except Exception:

            self.stats[
                "last_error"
            ] = "Unknown error."

    def _log_error(
        self,
        title,
        error,
    ):

        print(
            "\n"
            f"========== {title} =========="
        )

        print(str(error))

        if self.debug:
            print(traceback.format_exc())

        print(
            "====================================\n"
        )

    # ============================================================
    # HEALTH CHECK
    # ============================================================

    def health_check(
        self,
    ) -> Dict[str, Any]:

        result = {
            "engine": True,
            "version": self.VERSION,
            "student": False,
            "llm": False,
            "quiz_engine": False,
            "adaptive_tutor": False,
            "prompt_builder": False,
            "stats": self.get_stats(),
        }

        try:

            student = self._get_student_data()

            result["student"] = isinstance(
                student,
                dict,
            )

        except Exception:

            result["student"] = False

        result["llm"] = self.llm is not None
        result["quiz_engine"] = self.quiz is not None
        result["adaptive_tutor"] = (
            self.adaptive_tutor is not None
        )
        result["prompt_builder"] = (
            self.prompt_builder is not None
        )

        result["healthy"] = all(
            [
                result["engine"],
                result["student"],
                result["llm"],
                result["quiz_engine"],
                result["adaptive_tutor"],
                result["prompt_builder"],
            ]
        )

        return result

    # ============================================================
    # DEBUG INFORMATION
    # ============================================================

    def debug_info(
        self,
    ) -> Dict[str, Any]:

        return {
            "version": self.VERSION,
            "retry_count": self.retry_count,
            "retry_delay": self.retry_delay,
            "debug": self.debug,
            "llm_class": type(self.llm).__name__,
            "student_class": type(self.student).__name__,
            "quiz_class": type(self.quiz).__name__,
            "adaptive_tutor_class": (
                type(self.adaptive_tutor).__name__
            ),
            "prompt_builder_class": (
                type(self.prompt_builder).__name__
            ),
            "stats": self.get_stats(),
        }

    # ============================================================
    # STRATEGY SUMMARY
    # ============================================================

    def summarize_strategy(
        self,
        strategy,
    ) -> Dict[str, Any]:

        if not isinstance(strategy, dict):

            return {
                "confidence": 50,
                "learning_state": "developing",
                "difficulty": "medium",
                "challenge": False,
            }

        confidence = self._normalize_confidence(
            strategy.get(
                "confidence",
                50,
            )
        )

        return {
            "subject": strategy.get("subject"),
            "topic": strategy.get("topic"),
            "confidence": confidence,
            "learning_state": strategy.get(
                "learning_state",
                self._infer_learning_state(
                    confidence
                ),
            ),
            "difficulty": strategy.get(
                "difficulty"
            ),
            "explanation_depth": strategy.get(
                "explanation_depth"
            ),
            "challenge": self._to_bool(
                strategy.get("challenge"),
                False,
            ),
            "reinforcement": self._to_bool(
                strategy.get("reinforcement"),
                False,
            ),
        }

    # ============================================================
    # RESPONSE LENGTH
    # ============================================================

    def get_response_length_instruction(
        self,
        settings,
    ) -> str:

        settings = self._normalize_settings(
            settings
        )

        length = settings.get(
            "response_length",
            self.DEFAULT_RESPONSE_LENGTH,
        )

        instructions = {
            "short": (
                "Keep the answer concise and focused."
            ),
            "balanced": (
                "Give enough detail to explain the idea clearly "
                "without unnecessary length."
            ),
            "long": (
                "Give a thorough explanation with useful examples "
                "and reasoning."
            ),
            "detailed": (
                "Give a detailed educational explanation with "
                "clear structure, reasoning, examples, and "
                "important nuances."
            ),
        }

        return instructions.get(
            length,
            instructions["balanced"],
        )

    # ============================================================
    # LANGUAGE
    # ============================================================

    def get_language_instruction(
        self,
        settings,
    ) -> str:

        settings = self._normalize_settings(
            settings
        )

        language = settings.get(
            "language",
            self.DEFAULT_LANGUAGE,
        )

        return f"Respond primarily in {language}."

    # ============================================================
    # LEVEL
    # ============================================================

    def get_level_instruction(
        self,
        settings,
    ) -> str:

        settings = self._normalize_settings(
            settings
        )

        level = settings.get(
            "level",
            self.DEFAULT_LEVEL,
        )

        return (
            "Adapt the explanation to the student's "
            f"academic level: {level}."
        )

    # ============================================================
    # MESSAGE VALIDATION
    # ============================================================

    def validate_message(
        self,
        message,
    ) -> Dict[str, Any]:

        normalized = self._normalize_message(
            message
        )

        try:
            original_length = len(
                str(message)
            )
        except Exception:
            original_length = 0

        return {
            "valid": bool(normalized),
            "length": len(normalized),
            "truncated": (
                original_length
                > self.DEFAULT_MAX_MESSAGE_LENGTH
            ),
        }