from typing import Any, Dict, List, Optional
import os
import time
import re
import traceback

from backend.llm import LocalLLM
from backend.free_llm import FreeLLM
from backend.tutor_system.quiz_engine import QuizEngine
from backend.tutor_system.adaptive_tutor import AdaptiveTutor

from student_profile import StudentProfile

from backend.prompt.prompt_builder import PromptBuilder


class TutorEngine:
    """Central tutoring pipeline between Nova's learning systems and its LLM."""

    VERSION = "1.0.2"

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

    DEFAULT_RETRY_COUNT = 1
    DEFAULT_RETRY_DELAY = 0.25

    VALID_CREATIVITY = {"low", "medium", "high"}
    VALID_RESPONSE_LENGTHS = {"short", "balanced", "long", "detailed"}
    VALID_MODES = {
        "normal", "adaptive", "personal", "quiz", "practice_quiz", "test",
        "explain", "teach", "practice", "review", "challenge", "simple", "deep",
    }
    QUIZ_MODES = {"quiz", "practice_quiz", "test"}
    SIMPLE_MODES = {"simple"}
    DEEP_MODES = {"deep", "challenge"}

    FALLBACK_RESPONSE = "Nova couldn't generate a response right now."
    FALLBACK_EMPTY_REQUEST = "I couldn't understand the request."
    FALLBACK_PROMPT_ERROR = "Nova couldn't prepare the response correctly."
    FALLBACK_QUIZ_ERROR = "I couldn't create the quiz right now."
    FALLBACK_LLM_ERROR = "Nova couldn't generate a response right now."
    FALLBACK_INVALID_RESPONSE = "Nova generated an invalid response."

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
        self.retry_count = self._normalize_retry_count(retry_count)
        self.retry_delay = self._normalize_retry_delay(retry_delay)
        self.student = student if student is not None else StudentProfile()

        if llm is not None:
            self.llm = llm
        elif os.getenv("NOVA_ENV", "development").strip().lower() == "production":
            # Public Render instances do not have Ollama. Use the free hosted
            # adapter directly instead of constructing a dead local-runtime client.
            self.llm = FreeLLM(max_retries=1, retry_delay=0.35)
        else:
            self.llm = LocalLLM(max_retries=1, retry_delay=0.35)

        self.quiz = quiz_engine if quiz_engine is not None else QuizEngine()
        self.adaptive_tutor = adaptive_tutor if adaptive_tutor is not None else AdaptiveTutor()
        self.prompt_builder = prompt_builder if prompt_builder is not None else PromptBuilder()
        self.brain = brain
        self.stats = {
            "requests": 0, "successful_requests": 0, "failed_requests": 0,
            "empty_requests": 0, "llm_calls": 0, "llm_failures": 0,
            "llm_retries": 0, "quiz_requests": 0, "quiz_failures": 0,
            "prompt_failures": 0, "adaptive_failures": 0, "validation_failures": 0,
            "total_generation_time": 0.0, "last_generation_time": 0.0, "last_error": None,
        }
        print(f"Using public LLM: {type(self.llm).__name__}")
        print("Tutor Engine ready.")

    def answer(self, message, intent=None, subject=None, mode=None, memory_context=None, difficulty=None, settings=None, strategy=None, topic=None) -> str:
        start_time = time.perf_counter()
        self.stats["requests"] += 1
        try:
            message = self._normalize_message(message)
            if not message:
                self.stats["empty_requests"] += 1
                return self.FALLBACK_EMPTY_REQUEST
            mode = self._normalize_mode(mode)
            subject = self._normalize_optional_text(subject)
            topic = self._normalize_optional_text(topic)
            intent = self._normalize_optional_text(intent)
            memory_context = self._normalize_memory_context(memory_context)
            settings = self._apply_mode_settings(self._normalize_settings(settings), mode)

            if self._is_quiz_mode(mode):
                self.stats["quiz_requests"] += 1
                result = self._create_quiz(subject)
                if result == self.FALLBACK_QUIZ_ERROR:
                    self.stats["quiz_failures"] += 1
                else:
                    self.stats["successful_requests"] += 1
                return result

            prepared_strategy = self._prepare_strategy(strategy=strategy, subject=subject, topic=topic, difficulty=difficulty, settings=settings, mode=mode)
            adaptive_instruction = self._build_adaptive_instruction(subject=subject, message=message, strategy=prepared_strategy)
            prompt_strategy = self._build_prompt_strategy(strategy=prepared_strategy, adaptive_instruction=adaptive_instruction, mode=mode)
            prompt = self._validate_prompt(self._build_prompt(message=message, intent=intent, subject=subject, topic=topic, mode=mode, memory_context=memory_context, difficulty=difficulty, settings=settings, strategy=prompt_strategy))
            if not prompt:
                self.stats["prompt_failures"] += 1
                return self.FALLBACK_PROMPT_ERROR

            response = self._generate(prompt=prompt, settings=settings)
            response = self._clean_response(response)
            if not self._is_valid_response(response):
                self.stats["validation_failures"] += 1
                return self.FALLBACK_INVALID_RESPONSE
            self.stats["successful_requests"] += 1
            return response
        except Exception as error:
            self.stats["failed_requests"] += 1
            self._record_error(error)
            self._log_error("TUTOR ENGINE ERROR", error)
            return self.FALLBACK_RESPONSE
        finally:
            elapsed = time.perf_counter() - start_time
            self.stats["last_generation_time"] = elapsed
            self.stats["total_generation_time"] += elapsed

    def simple_answer(self, message, subject=None, mode="normal", settings=None) -> str:
        return self.answer(message=message, intent=None, subject=subject, mode=mode, memory_context=None, difficulty=None, settings=settings, strategy=None, topic=None)

    def test_llm(self) -> Dict[str, Any]:
        start = time.perf_counter()
        try:
            response = self.llm.answer(system="You are testing Nova's language model.", user="Reply with exactly: NOVA_LLM_OK", creativity="low")
            elapsed = time.perf_counter() - start
            valid = response is not None and bool(str(response).strip())
            return {"success": valid, "response": str(response).strip() if response is not None else "", "duration": round(elapsed, 3)}
        except Exception as error:
            return {"success": False, "response": "", "duration": round(time.perf_counter() - start, 3), "error": str(error)}

    def get_stats(self) -> Dict[str, Any]:
        result = dict(self.stats)
        requests = result.get("requests", 0)
        successful = result.get("successful_requests", 0)
        result["success_rate"] = round((successful / requests) * 100, 2) if requests else 0.0
        return result

    def reset_stats(self):
        for key in list(self.stats.keys()):
            if key in {"total_generation_time", "last_generation_time"}:
                self.stats[key] = 0.0
            elif key == "last_error":
                self.stats[key] = None
            else:
                self.stats[key] = 0

    def _normalize_message(self, message) -> str:
        if message is None: return ""
        if not isinstance(message, str): message = str(message)
        message = message.replace("\x00", "").strip()
        return message if len(message) <= self.DEFAULT_MAX_MESSAGE_LENGTH else message[:self.DEFAULT_MAX_MESSAGE_LENGTH] + "\n\n[Message truncated by Nova.]"

    def _normalize_optional_text(self, value) -> Optional[str]:
        if value is None: return None
        if not isinstance(value, str): value = str(value)
        value = value.replace("\x00", "").strip()
        return value or None

    def _normalize_mode(self, mode) -> str:
        if mode is None: return self.DEFAULT_MODE
        if not isinstance(mode, str): mode = str(mode)
        return mode.strip().lower() or self.DEFAULT_MODE

    def _normalize_settings(self, settings) -> Dict[str, Any]:
        if not isinstance(settings, dict): settings = {}
        result = dict(settings)
        result.setdefault("language", self.DEFAULT_LANGUAGE)
        result.setdefault("level", self.DEFAULT_LEVEL)
        result["response_length"] = self._normalize_response_length(result.get("response_length", self.DEFAULT_RESPONSE_LENGTH))
        result["creativity"] = self._normalize_creativity(result.get("creativity", self.DEFAULT_CREATIVITY))
        return result

    def _normalize_creativity(self, creativity) -> str:
        if not isinstance(creativity, str): return self.DEFAULT_CREATIVITY
        creativity = creativity.strip().lower()
        return creativity if creativity in self.VALID_CREATIVITY else self.DEFAULT_CREATIVITY

    def _normalize_response_length(self, value) -> str:
        if not isinstance(value, str): return self.DEFAULT_RESPONSE_LENGTH
        value = value.strip().lower()
        return value if value in self.VALID_RESPONSE_LENGTHS else self.DEFAULT_RESPONSE_LENGTH

    def _normalize_memory_context(self, memory_context) -> str:
        if memory_context is None: return "No previous discussion."
        if not isinstance(memory_context, str): memory_context = str(memory_context)
        memory_context = memory_context.replace("\x00", "").strip()
        if not memory_context: return "No previous discussion."
        return memory_context if len(memory_context) <= self.DEFAULT_MAX_MEMORY_LENGTH else memory_context[:self.DEFAULT_MAX_MEMORY_LENGTH] + "\n\n[Memory context truncated by Nova.]"

    def _apply_mode_settings(self, settings, mode) -> Dict[str, Any]:
        settings = dict(settings)
        if mode in self.SIMPLE_MODES:
            settings["response_length"] = "short"
            settings["step_by_step"] = True
        elif mode in self.DEEP_MODES:
            settings["response_length"] = "detailed"
            settings["creativity"] = "medium"
        return settings

    def _is_quiz_mode(self, mode) -> bool: return mode in self.QUIZ_MODES

    def _create_quiz(self, subject) -> str:
        subject = subject or self.DEFAULT_SUBJECT
        try: result = self.quiz.create_quiz(subject)
        except Exception as error:
            self._record_error(error); self._log_error("QUIZ ENGINE ERROR", error); return self.FALLBACK_QUIZ_ERROR
        if result is None: return self.FALLBACK_QUIZ_ERROR
        result = str(result).strip()
        return result or self.FALLBACK_QUIZ_ERROR
