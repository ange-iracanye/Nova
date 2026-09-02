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
from backend.language_support import build_language_policy, parse_translation_mode


class TutorEngine:
    """Nova's tutoring pipeline with a local dev LLM and hosted public LLM."""

    VERSION = "1.0.3"
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
    TRANSLATION_MODE_PREFIX = "translation:"

    VALID_CREATIVITY = {"low", "medium", "high"}
    VALID_RESPONSE_LENGTHS = {"short", "balanced", "long", "detailed"}
    VALID_MODES = {"normal", "adaptive", "personal", "quiz", "practice_quiz", "test", "explain", "teach", "practice", "review", "challenge", "simple", "deep"}
    QUIZ_MODES = {"quiz", "practice_quiz", "test"}
    SIMPLE_MODES = {"simple"}
    DEEP_MODES = {"deep", "challenge"}

    FALLBACK_RESPONSE = "Nova couldn't generate a response right now."
    FALLBACK_EMPTY_REQUEST = "I couldn't understand the request."
    FALLBACK_PROMPT_ERROR = "Nova couldn't prepare the response correctly."
    FALLBACK_QUIZ_ERROR = "I couldn't create the quiz right now."
    FALLBACK_LLM_ERROR = "Nova couldn't generate a response right now."
    FALLBACK_INVALID_RESPONSE = "Nova generated an invalid response."

    def __init__(self, student=None, brain=None, llm=None, quiz_engine=None, adaptive_tutor=None, prompt_builder=None, retry_count=None, retry_delay=None, debug=False):
        print("Loading Tutor Engine...")
        self.debug = bool(debug)
        self.retry_count = self._normalize_retry_count(retry_count)
        self.retry_delay = self._normalize_retry_delay(retry_delay)
        self.student = student if student is not None else StudentProfile()
        if llm is not None:
            self.llm = llm
        elif os.getenv("NOVA_ENV", "development").strip().lower() == "production":
            self.llm = FreeLLM(max_retries=1, retry_delay=0.35)
        else:
            self.llm = LocalLLM(max_retries=1, retry_delay=0.35)
        self.quiz = quiz_engine if quiz_engine is not None else QuizEngine()
        self.adaptive_tutor = adaptive_tutor if adaptive_tutor is not None else AdaptiveTutor()
        self.prompt_builder = prompt_builder if prompt_builder is not None else PromptBuilder()
        self.brain = brain
        self.stats = {"requests": 0, "successful_requests": 0, "failed_requests": 0, "empty_requests": 0, "llm_calls": 0, "llm_failures": 0, "llm_retries": 0, "quiz_requests": 0, "quiz_failures": 0, "prompt_failures": 0, "adaptive_failures": 0, "validation_failures": 0, "total_generation_time": 0.0, "last_generation_time": 0.0, "last_error": None}
        print(f"Using LLM: {type(self.llm).__name__}")
        print("Tutor Engine ready.")

    def answer(self, message, intent=None, subject=None, mode=None, memory_context=None, difficulty=None, settings=None, strategy=None, topic=None) -> str:
        start = time.perf_counter()
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
            prepared = self._prepare_strategy(strategy, subject, topic, difficulty, settings, mode)
            adaptive = self._build_adaptive_instruction(subject, message, prepared)
            strategy_for_prompt = self._build_prompt_strategy(prepared, adaptive, mode)
            prompt = self._validate_prompt(self._build_prompt(message, intent, subject, topic, mode, memory_context, difficulty, settings, strategy_for_prompt))
            if not prompt:
                self.stats["prompt_failures"] += 1
                return self.FALLBACK_PROMPT_ERROR
            prompt = self._apply_language_policy(prompt, mode)
            response = self._clean_response(self._generate(prompt, settings))
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
            elapsed = time.perf_counter() - start
            self.stats["last_generation_time"] = elapsed
            self.stats["total_generation_time"] += elapsed

    def simple_answer(self, message, subject=None, mode="normal", settings=None):
        return self.answer(message, subject=subject, mode=mode, settings=settings)

    def test_llm(self) -> Dict[str, Any]:
        start = time.perf_counter()
        try:
            response = self.llm.answer(system="You are testing Nova's language model.", user="Reply with exactly: NOVA_LLM_OK", creativity="low")
            return {"success": bool(str(response or "").strip()), "response": str(response or "").strip(), "duration": round(time.perf_counter() - start, 3)}
        except Exception as error:
            return {"success": False, "response": "", "duration": round(time.perf_counter() - start, 3), "error": str(error)}

    def get_stats(self):
        result = dict(self.stats)
        requests = result.get("requests", 0)
        result["success_rate"] = round(result.get("successful_requests", 0) / requests * 100, 2) if requests else 0.0
        return result

    def reset_stats(self):
        for key in self.stats:
            self.stats[key] = 0.0 if key in {"total_generation_time", "last_generation_time"} else None if key == "last_error" else 0

    def _normalize_message(self, message):
        if message is None: return ""
        value = str(message).replace("\x00", "").strip()
        return value if len(value) <= self.DEFAULT_MAX_MESSAGE_LENGTH else value[:self.DEFAULT_MAX_MESSAGE_LENGTH] + "\n\n[Message truncated by Nova.]"

    def _normalize_optional_text(self, value):
        if value is None: return None
        value = str(value).replace("\x00", "").strip()
        return value or None

    def _normalize_mode(self, mode):
        value = str(mode or self.DEFAULT_MODE).strip().lower()
        return value or self.DEFAULT_MODE

    def _normalize_settings(self, settings):
        result = dict(settings) if isinstance(settings, dict) else {}
        result.setdefault("language", self.DEFAULT_LANGUAGE)
        result.setdefault("level", self.DEFAULT_LEVEL)
        result["response_length"] = self._normalize_response_length(result.get("response_length", self.DEFAULT_RESPONSE_LENGTH))
        result["creativity"] = self._normalize_creativity(result.get("creativity", self.DEFAULT_CREATIVITY))
        return result

    def _normalize_creativity(self, value):
        value = str(value or self.DEFAULT_CREATIVITY).strip().lower()
        return value if value in self.VALID_CREATIVITY else self.DEFAULT_CREATIVITY

    def _normalize_response_length(self, value):
        value = str(value or self.DEFAULT_RESPONSE_LENGTH).strip().lower()
        return value if value in self.VALID_RESPONSE_LENGTHS else self.DEFAULT_RESPONSE_LENGTH

    def _normalize_memory_context(self, value):
        value = str(value or "No previous discussion.").replace("\x00", "").strip()
        return value[:self.DEFAULT_MAX_MEMORY_LENGTH] if value else "No previous discussion."

    def _apply_mode_settings(self, settings, mode):
        result = dict(settings)
        if mode in self.SIMPLE_MODES:
            result["response_length"] = "short"
            result["step_by_step"] = True
        elif mode in self.DEEP_MODES:
            result["response_length"] = "detailed"
        return result

    def _is_quiz_mode(self, mode):
        return mode in self.QUIZ_MODES

    def _create_quiz(self, subject):
        try:
            result = self.quiz.create_quiz(subject or self.DEFAULT_SUBJECT)
            return str(result).strip() if result else self.FALLBACK_QUIZ_ERROR
        except Exception as error:
            self._record_error(error)
            self._log_error("QUIZ ENGINE ERROR", error)
            return self.FALLBACK_QUIZ_ERROR

    def _prepare_strategy(self, strategy, subject, topic, difficulty, settings, mode):
        result = dict(strategy) if isinstance(strategy, dict) else {}
        result.setdefault("subject", subject)
        result.setdefault("topic", topic)
        result["mode"] = mode
        if isinstance(difficulty, dict):
            result.setdefault("difficulty", difficulty.get("level"))
            result["difficulty_instruction"] = difficulty.get("instruction", "")
        elif difficulty:
            result.setdefault("difficulty", str(difficulty))
        confidence = self._normalize_confidence(result.get("confidence", 50))
        result["confidence"] = confidence
        result.setdefault("learning_state", self._infer_learning_state(confidence))
        result.setdefault("explanation_depth", self._infer_explanation_depth(confidence))
        result.setdefault("use_examples", True)
        result.setdefault("use_analogies", False)
        result.setdefault("step_by_step", False)
        result.setdefault("challenge", False)
        result.setdefault("reinforcement", False)
        result["response_length"] = settings.get("response_length", self.DEFAULT_RESPONSE_LENGTH)
        return result

    def _normalize_confidence(self, value):
        try: value = float(value)
        except (TypeError, ValueError): value = 50.0
        if 0 <= value <= 1: value *= 100
        return round(max(0, min(100, value)), 2)

    def _infer_learning_state(self, confidence):
        if confidence < 25: return "struggling"
        if confidence < 40: return "weak"
        if confidence < 60: return "developing"
        if confidence < 75: return "understanding"
        if confidence < 90: return "strong"
        return "mastery"

    def _infer_explanation_depth(self, confidence):
        if confidence < 30: return "very_basic"
        if confidence < 50: return "basic"
        if confidence < 70: return "balanced"
        if confidence < 85: return "deep"
        return "advanced"

    def _build_adaptive_instruction(self, subject, message, strategy):
        try:
            student = self._get_student_data()
            try:
                result = self.adaptive_tutor.build_instruction(student, subject, message=message)
            except TypeError:
                result = self.adaptive_tutor.build_instruction(student, subject)
            return str(result or "").strip()
        except Exception as error:
            self.stats["adaptive_failures"] += 1
            self._record_error(error)
            return ""

    def _get_student_data(self):
        try:
            data = self.student.get() if hasattr(self.student, "get") else getattr(self.student, "profile", {})
            return dict(data) if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _build_prompt_strategy(self, strategy, adaptive_instruction, mode):
        result = dict(strategy)
        approach = list(result.get("approach", [])) if isinstance(result.get("approach"), list) else []
        if result.get("use_examples"): approach.append("Use a concrete example when it improves understanding.")
        if result.get("use_analogies"): approach.append("Use a simple analogy only when it genuinely clarifies the concept.")
        if result.get("step_by_step"): approach.append("Break complex reasoning into clear logical steps.")
        if result.get("reinforcement"): approach.append("Reinforce important fundamentals before moving to harder material.")
        if result.get("challenge"): approach.append("Add a small reasoning challenge when appropriate.")
        if result.get("difficulty_instruction"): approach.append(str(result["difficulty_instruction"]))
        if adaptive_instruction: approach.append(adaptive_instruction)
        if mode == "simple": approach.append("Prioritize simple vocabulary and short explanations.")
        if mode == "deep": approach.append("Provide deeper reasoning and relevant technical detail.")
        result["approach"] = self._normalize_approach(approach)
        result["adaptive_instruction"] = adaptive_instruction or ""
        return result

    def _normalize_approach(self, approach):
        if approach is None: return []
        if not isinstance(approach, list): approach = [approach]
        result, seen = [], set()
        for item in approach:
            text = str(item).strip()
            if text and text.lower() not in seen:
                seen.add(text.lower()); result.append(text)
        return result

    def _build_prompt(self, message, intent, subject, topic, mode, memory_context, difficulty, settings, strategy):
        student = self._get_student_data()
        try:
            prompt = self.prompt_builder.build(student=student, subject=subject, topic=topic, message=message, intent=intent, mode=mode, strategy=strategy, memory_context=memory_context, difficulty=difficulty, settings=settings)
            normalized = self._normalize_prompt(prompt)
            if normalized: return normalized
        except TypeError:
            pass
        except Exception as error:
            self.stats["prompt_failures"] += 1
            self._log_error("PROMPT BUILDER ERROR", error)
        try:
            prompt = self.prompt_builder.build(student=student, subject=subject, message=message, mode=mode, strategy=strategy, memory_context=memory_context, difficulty=difficulty, settings=settings)
            normalized = self._normalize_prompt(prompt)
            if normalized: return normalized
        except Exception:
            pass
        return self._build_emergency_prompt(message, subject, topic, mode, memory_context, difficulty, settings, strategy)

    def _normalize_prompt(self, prompt):
        if not isinstance(prompt, dict): return None
        system = str(prompt.get("system", "") or "").strip()
        user = str(prompt.get("user", "") or "").strip()
        if not user: return None
        if len(system) + len(user) > self.DEFAULT_MAX_PROMPT_LENGTH:
            user = user[:max(1000, self.DEFAULT_MAX_PROMPT_LENGTH - len(system))] + "\n\n[Prompt truncated by Nova.]"
        return {"system": system, "user": user}

    def _apply_language_policy(self, prompt, mode):
        """Append a high-priority language policy after the existing prompt."""
        if not isinstance(prompt, dict):
            return prompt
        policy = build_language_policy(mode)
        system = str(prompt.get("system", "") or "").strip()
        if policy and policy not in system:
            system = f"{system}\n\n{policy}".strip()
        return {"system": system, "user": prompt.get("user", "")}

    def _build_emergency_prompt(self, message, subject, topic, mode, memory_context, difficulty, settings, strategy):
        difficulty_name = difficulty.get("level", "") if isinstance(difficulty, dict) else str(difficulty or "")
        approach = "\n".join(f"- {item}" for item in strategy.get("approach", []))
        system = f"""You are Nova, an adaptive educational AI tutor.
Student language: {settings.get('language', self.DEFAULT_LANGUAGE)}
Academic level: {settings.get('level', self.DEFAULT_LEVEL)}
Subject: {subject or 'general'}
Topic: {topic or 'not specified'}
Difficulty: {difficulty_name or 'adaptive'}
Response length: {settings.get('response_length', self.DEFAULT_RESPONSE_LENGTH)}
Teaching strategy:
{approach}

Answer the student's actual question accurately and clearly. Do not invent facts.""".strip()
        user = f"Previous relevant context:\n\n{memory_context}\n\nStudent message:\n\n{message}".strip()
        return {"system": system, "user": user}

    def _validate_prompt(self, prompt):
        if not isinstance(prompt, dict): return None
        system = str(prompt.get("system", "") or "").strip()
        user = str(prompt.get("user", "") or "").strip()
        return {"system": system, "user": user} if user else None

    def _generate(self, prompt, settings):
        system = str(prompt.get("system", "") or "").strip()
        user = str(prompt.get("user", "") or "").strip()
        if not system: system = self._default_system_prompt(settings)
        if not user: return self.FALLBACK_EMPTY_REQUEST
        creativity = self._normalize_creativity(settings.get("creativity"))
        attempts = self.retry_count + 1
        for attempt in range(attempts):
            self.stats["llm_calls"] += 1
            started = time.perf_counter()
            try:
                response = self.llm.answer(system=system, user=user, creativity=creativity)
                elapsed = time.perf_counter() - started
                self.stats["total_generation_time"] += elapsed
                self.stats["last_generation_time"] = elapsed
                if not str(response or "").strip(): raise RuntimeError("LLM returned an empty response.")
                return str(response).strip()
            except Exception as error:
                self.stats["llm_failures"] += 1
                if attempt < attempts - 1:
                    self.stats["llm_retries"] += 1
                    if self.retry_delay: time.sleep(self.retry_delay)
                else:
                    self._record_error(error)
                    self._log_error("NOVA LLM ERROR", error)
        return self.FALLBACK_LLM_ERROR

    def _default_system_prompt(self, settings):
        return f"You are Nova, an adaptive educational AI tutor. Respond primarily in the same language as the student's latest message and adapt explanations to {settings.get('level', self.DEFAULT_LEVEL)}. Prioritize accuracy, clarity, useful examples, and honest uncertainty."

    def _clean_response(self, response):
        response = str(response or "").replace("\x00", "").strip()
        response = re.sub(r"\n{4,}", "\n\n\n", response)
        if response.startswith("```") and response.endswith("```"):
            lines = response.splitlines()
            if len(lines) >= 3: response = "\n".join(lines[1:-1]).strip()
        for prefix in ("Nova's answer:", "Nova answer:", "Answer:", "Response:"):
            if response.lower().startswith(prefix.lower()):
                response = response[len(prefix):].strip(); break
        return response[:self.DEFAULT_MAX_RESPONSE_LENGTH] if response else self.FALLBACK_RESPONSE

    def _is_valid_response(self, response):
        if not isinstance(response, str) or len(response.strip()) < 2: return False
        return response.strip().lower() not in {self.FALLBACK_RESPONSE.lower(), self.FALLBACK_LLM_ERROR.lower(), self.FALLBACK_PROMPT_ERROR.lower(), self.FALLBACK_INVALID_RESPONSE.lower()}

    def _to_bool(self, value, default=False):
        if isinstance(value, bool): return value
        if value is None: return default
        if isinstance(value, str):
            if value.strip().lower() in {"true", "yes", "1", "on", "enabled"}: return True
            if value.strip().lower() in {"false", "no", "0", "off", "disabled"}: return False
        return bool(value)

    def _normalize_retry_count(self, value):
        try: value = self.DEFAULT_RETRY_COUNT if value is None else int(value)
        except (TypeError, ValueError): value = self.DEFAULT_RETRY_COUNT
        return max(0, min(3, value))

    def _normalize_retry_delay(self, value):
        try: value = self.DEFAULT_RETRY_DELAY if value is None else float(value)
        except (TypeError, ValueError): value = self.DEFAULT_RETRY_DELAY
        return max(0.0, min(5.0, value))

    def _record_error(self, error):
        self.stats["last_error"] = str(error)

    def _log_error(self, title, error):
        print(f"========== {title} ==========")
        print(str(error))
        if self.debug: print(traceback.format_exc())

    def health_check(self):
        return {"engine": True, "version": self.VERSION, "student": self.student is not None, "llm": self.llm is not None, "quiz_engine": self.quiz is not None, "adaptive_tutor": self.adaptive_tutor is not None, "prompt_builder": self.prompt_builder is not None, "healthy": all((self.student is not None, self.llm is not None, self.quiz is not None, self.adaptive_tutor is not None, self.prompt_builder is not None)), "stats": self.get_stats()}

    def debug_info(self):
        return {"version": self.VERSION, "retry_count": self.retry_count, "retry_delay": self.retry_delay, "debug": self.debug, "llm_class": type(self.llm).__name__, "student_class": type(self.student).__name__, "quiz_class": type(self.quiz).__name__, "adaptive_tutor_class": type(self.adaptive_tutor).__name__, "prompt_builder_class": type(self.prompt_builder).__name__, "stats": self.get_stats()}

    def summarize_strategy(self, strategy):
        if not isinstance(strategy, dict): return {"confidence": 50, "learning_state": "developing", "difficulty": "medium", "challenge": False}
        confidence = self._normalize_confidence(strategy.get("confidence", 50))
        return {"subject": strategy.get("subject"), "topic": strategy.get("topic"), "confidence": confidence, "learning_state": strategy.get("learning_state", self._infer_learning_state(confidence)), "difficulty": strategy.get("difficulty"), "explanation_depth": strategy.get("explanation_depth"), "challenge": self._to_bool(strategy.get("challenge")), "reinforcement": self._to_bool(strategy.get("reinforcement"))}

    def get_response_length_instruction(self, settings):
        return {"short": "Keep the answer concise and focused.", "balanced": "Give enough detail to explain the idea clearly without unnecessary length.", "long": "Give a thorough explanation with useful examples and reasoning.", "detailed": "Give a detailed educational explanation with clear structure and useful examples."}.get(self._normalize_settings(settings).get("response_length"), "Give enough detail to explain the idea clearly without unnecessary length.")

    def get_language_instruction(self, settings):
        return "Reply in the same natural language used by the student's latest message."

    def get_level_instruction(self, settings):
        return f"Adapt the explanation to the student's academic level: {self._normalize_settings(settings).get('level', self.DEFAULT_LEVEL)}."

    def validate_message(self, message):
        normalized = self._normalize_message(message)
        try: original_length = len(str(message))
        except Exception: original_length = 0
        return {"valid": bool(normalized), "length": len(normalized), "truncated": original_length > self.DEFAULT_MAX_MESSAGE_LENGTH}
