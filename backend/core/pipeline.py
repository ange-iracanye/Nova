"""
Nova AI - Request Pipeline
==========================

Central orchestration utilities for NovaCore.

This module is intentionally independent from NovaCore's concrete
components. It provides:

- a structured request context
- deterministic request classification
- memory-retrieval policy
- prompt/context size protection
- stage timing
- stage status tracking
- warnings and degraded-component tracking
- safe hook execution
- result normalization
- lightweight greeting/casual-request handling
- diagnostics
- compatibility with synchronous Nova components

Important:
    This file does NOT replace NovaCore, TutorEngine, MemoryManager,
    or LocalLLM. NovaCore must explicitly use NovaPipeline.

The design goal is to prevent a simple request such as "Hello Nova"
from triggering every expensive subsystem and dumping unrelated
long-term memory into the LLM prompt.
"""

from __future__ import annotations

import re
import time
import uuid

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional


# ============================================================
# CONSTANTS
# ============================================================

PIPELINE_VERSION = "1.0.0"

DEFAULT_MAX_MESSAGE_CHARS = 12_000
DEFAULT_MAX_CONTEXT_CHARS = 24_000
DEFAULT_MAX_MEMORY_ITEMS = 8
DEFAULT_MAX_MEMORY_CHARS = 8_000
DEFAULT_MAX_HISTORY_ITEMS = 12
DEFAULT_MAX_HISTORY_CHARS = 10_000

GREETING_INTENTS = {
    "greeting",
    "hello",
    "hi",
    "welcome",
}

LIGHTWEIGHT_INTENTS = {
    "greeting",
    "casual_conversation",
    "simple_acknowledgement",
    "thanks",
    "farewell",
}

LEARNING_INTENTS = {
    "learning",
    "question",
    "homework",
    "explanation",
    "practice",
    "quiz",
    "correction",
    "problem_solving",
    "study",
}

GREETING_PATTERNS = (
    r"^(hi|hello|hey|hiya|yo|howdy)[!.?,\s]*$",
    r"^(hello|hi|hey)\s+(nova|there)[!.?,\s]*$",
    r"^(good\s+(morning|afternoon|evening))[!.?,\s]*$",
)

THANKS_PATTERNS = (
    r"^(thanks|thank you|thx|ty)[!.?,\s]*$",
    r"^(thanks|thank you)\s+(nova|so much)[!.?,\s]*$",
)

FAREWELL_PATTERNS = (
    r"^(bye|goodbye|see you|see ya|good night)[!.?,\s]*$",
)

QUESTION_MARK_RE = re.compile(r"\?\s*$")


# ============================================================
# SMALL UTILITIES
# ============================================================

def _now_iso() -> str:
    return datetime.now().isoformat()


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y", "on"}:
            return True
        if lowered in {"false", "0", "no", "n", "off"}:
            return False
    return bool(value)


def _truncate(text: Any, limit: int) -> str:
    value = _clean_text(text)

    if limit <= 0:
        return ""

    if len(value) <= limit:
        return value

    if limit <= 40:
        return value[:limit]

    return value[: limit - 40].rstrip() + "\n...[truncated]"


def _dedupe_strings(values: Iterable[Any]) -> List[str]:
    result: List[str] = []
    seen = set()

    for value in values:
        text = _clean_text(value)
        if not text:
            continue

        key = text.casefold()

        if key in seen:
            continue

        seen.add(key)
        result.append(text)

    return result


def _safe_mapping(value: Any) -> Dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)

    return {}


def _matches_any(text: str, patterns: Iterable[str]) -> bool:
    lowered = text.strip().casefold()

    for pattern in patterns:
        if re.fullmatch(pattern, lowered):
            return True

    return False


# ============================================================
# REQUEST CLASSIFICATION
# ============================================================

def classify_request(message: str) -> Dict[str, Any]:
    """
    Classify only what can be determined safely from the current
    message.

    This is deliberately conservative.

    Long-term memory must NOT be used to decide whether a message
    is a greeting, because that can cause old information to leak
    into simple requests.
    """

    text = _clean_text(message)
    lowered = text.casefold()

    if not text:
        return {
            "intent": "invalid",
            "kind": "invalid",
            "lightweight": False,
            "needs_memory": False,
            "needs_learning_context": False,
            "confidence": 100.0,
        }

    if _matches_any(text, GREETING_PATTERNS):
        return {
            "intent": "greeting",
            "kind": "greeting",
            "lightweight": True,
            "needs_memory": False,
            "needs_learning_context": False,
            "confidence": 98.0,
        }

    if _matches_any(text, THANKS_PATTERNS):
        return {
            "intent": "thanks",
            "kind": "casual",
            "lightweight": True,
            "needs_memory": False,
            "needs_learning_context": False,
            "confidence": 98.0,
        }

    if _matches_any(text, FAREWELL_PATTERNS):
        return {
            "intent": "farewell",
            "kind": "casual",
            "lightweight": True,
            "needs_memory": False,
            "needs_learning_context": False,
            "confidence": 98.0,
        }

    learning_signals = (
        "explain",
        "why",
        "how",
        "solve",
        "calculate",
        "help me",
        "teach me",
        "study",
        "quiz",
        "exercise",
        "homework",
        "question",
        "understand",
        "don't understand",
        "do not understand",
        "correct",
        "mistake",
        "formula",
        "definition",
        "what is",
        "what are",
    )

    likely_learning = any(
        signal in lowered
        for signal in learning_signals
    )

    has_question = bool(QUESTION_MARK_RE.search(text))

    if likely_learning or has_question:
        return {
            "intent": "learning",
            "kind": "learning",
            "lightweight": False,
            "needs_memory": True,
            "needs_learning_context": True,
            "confidence": 75.0,
        }

    return {
        "intent": "general",
        "kind": "general",
        "lightweight": False,
        "needs_memory": False,
        "needs_learning_context": False,
        "confidence": 55.0,
    }


# ============================================================
# MEMORY POLICY
# ============================================================

@dataclass(frozen=True)
class MemoryPolicy:
    """
    Decides how much historical information is allowed to enter
    the current request.

    This is a policy object, not a memory database.
    """

    enabled: bool = True
    max_items: int = DEFAULT_MAX_MEMORY_ITEMS
    max_chars: int = DEFAULT_MAX_MEMORY_CHARS
    include_for_greetings: bool = False
    include_for_casual: bool = False
    include_for_general: bool = False
    include_for_learning: bool = True

    @classmethod
    def for_request(
        cls,
        classification: Mapping[str, Any],
    ) -> "MemoryPolicy":
        intent = _clean_text(
            classification.get("intent")
        ).casefold()

        if intent in GREETING_INTENTS:
            return cls(
                enabled=False,
                max_items=0,
                max_chars=0,
            )

        if intent in {
            "thanks",
            "farewell",
            "casual_conversation",
        }:
            return cls(
                enabled=False,
                max_items=0,
                max_chars=0,
            )

        if intent == "learning":
            return cls(
                enabled=True,
                max_items=6,
                max_chars=6_000,
            )

        return cls(
            enabled=False,
            max_items=0,
            max_chars=0,
        )


def select_memory(
    memory: Any,
    policy: MemoryPolicy,
) -> Any:
    """
    Safely reduce memory before it reaches the LLM.

    Supports:
        - strings
        - lists / tuples
        - dictionaries
        - arbitrary objects

    The function never mutates the original memory object.
    """

    if not policy.enabled:
        return []

    if policy.max_items <= 0 or policy.max_chars <= 0:
        return []

    if memory is None:
        return []

    if isinstance(memory, str):
        return _truncate(
            memory,
            policy.max_chars,
        )

    if isinstance(memory, Mapping):
        output: Dict[str, Any] = {}
        total = 0

        for key, value in memory.items():
            key_text = _clean_text(key)

            if isinstance(value, str):
                value = _truncate(
                    value,
                    min(2_000, policy.max_chars),
                )

            serialized = _clean_text(value)

            if total + len(key_text) + len(serialized) > policy.max_chars:
                break

            output[key_text] = value
            total += len(key_text) + len(serialized)

        return output

    if isinstance(memory, (list, tuple, set)):
        output: List[Any] = []
        total = 0

        for item in memory:
            if len(output) >= policy.max_items:
                break

            if isinstance(item, str):
                cleaned = _truncate(
                    item,
                    min(1_500, policy.max_chars),
                )
                item_size = len(cleaned)

                if total + item_size > policy.max_chars:
                    break

                output.append(cleaned)
                total += item_size
                continue

            if isinstance(item, Mapping):
                safe_item = dict(item)
                serialized = _clean_text(safe_item)

                if (
                    total + len(serialized)
                    > policy.max_chars
                ):
                    break

                output.append(safe_item)
                total += len(serialized)
                continue

            text = _truncate(
                item,
                min(1_500, policy.max_chars),
            )

            if total + len(text) > policy.max_chars:
                break

            output.append(text)
            total += len(text)

        return output

    return _truncate(
        memory,
        policy.max_chars,
    )


# ============================================================
# CONTEXT
# ============================================================

@dataclass
class PipelineContext:
    """
    All state associated with one request.

    This class intentionally mirrors the important fields already
    used by NovaCore, while remaining independent of NovaCore.
    """

    message: str
    user_email: str

    conversation_id: Optional[str] = None
    forced_mode: Optional[str] = None

    request_id: str = field(
        default_factory=lambda: (
            "nova-" + uuid.uuid4().hex
        )
    )

    started_at: str = field(
        default_factory=_now_iso
    )

    classification: Dict[str, Any] = field(
        default_factory=dict
    )

    intent: Optional[str] = None
    mode: Optional[str] = None
    subject: Optional[str] = None
    topic: Optional[str] = None

    user_context: Any = None
    conversation_context: Any = None
    student_context: Any = None
    profile_analysis: Dict[str, Any] = field(
        default_factory=dict
    )

    strategy: Dict[str, Any] = field(
        default_factory=dict
    )

    difficulty: Any = None
    teaching_style: Any = None
    settings: Dict[str, Any] = field(
        default_factory=dict
    )

    raw_memory: Any = None
    memory_context: Any = None

    answer: str = ""
    verified_answer: str = ""

    warnings: List[str] = field(
        default_factory=list
    )

    errors: List[Dict[str, str]] = field(
        default_factory=list
    )

    degraded_components: List[str] = field(
        default_factory=list
    )

    stage_times: Dict[str, float] = field(
        default_factory=dict
    )

    stage_status: Dict[str, str] = field(
        default_factory=dict
    )

    metadata: Dict[str, Any] = field(
        default_factory=dict
    )

    completed: bool = False
    success: bool = False

    def warn(self, message: Any) -> None:
        text = _clean_text(message)

        if text and text not in self.warnings:
            self.warnings.append(text)

    def error(
        self,
        component: str,
        error: Any,
    ) -> None:
        self.errors.append(
            {
                "component": _clean_text(component),
                "error": _clean_text(error),
            }
        )

    def degrade(self, component: str) -> None:
        name = _clean_text(component)

        if (
            name
            and name not in self.degraded_components
        ):
            self.degraded_components.append(name)

    def mark_stage(
        self,
        name: str,
        status: str,
        duration_ms: float,
    ) -> None:
        self.stage_status[name] = status
        self.stage_times[name] = round(
            float(duration_ms),
            3,
        )

    def total_duration_ms(self) -> float:
        return round(
            (
                time.perf_counter()
                - self.metadata.get(
                    "_started_perf",
                    time.perf_counter(),
                )
            )
            * 1000,
            3,
        )

    def public_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "conversation_id": self.conversation_id,
            "intent": self.intent,
            "mode": self.mode,
            "subject": self.subject,
            "topic": self.topic,
            "warnings": list(self.warnings),
            "errors": list(self.errors),
            "degraded_components": list(
                self.degraded_components
            ),
            "stage_times": dict(self.stage_times),
            "stage_status": dict(self.stage_status),
            "metadata": {
                key: value
                for key, value in self.metadata.items()
                if not key.startswith("_")
            },
            "success": self.success,
            "completed": self.completed,
        }


# ============================================================
# STAGE
# ============================================================

@dataclass
class PipelineStage:
    """
    A named pipeline operation.

    `required=False` means the stage may fail without killing
    the entire request.
    """

    name: str
    handler: Callable[[PipelineContext], Any]

    required: bool = True

    enabled: bool = True

    continue_on_error: bool = False


# ============================================================
# PIPELINE
# ============================================================

class NovaPipeline:
    """
    Generic synchronous orchestration pipeline for Nova.

    NovaCore should inject its existing systems as stage handlers.

    Example:

        pipeline = NovaPipeline()

        pipeline.add_stage(
            "intent",
            lambda ctx: ...
        )

        result = pipeline.run(ctx)

    The pipeline does not know how IntentDetector, MemoryManager,
    TutorEngine, or NovaBrain work internally.
    """

    VERSION = PIPELINE_VERSION

    def __init__(
        self,
        *,
        max_message_chars: int = DEFAULT_MAX_MESSAGE_CHARS,
        max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS,
        max_memory_items: int = DEFAULT_MAX_MEMORY_ITEMS,
        max_memory_chars: int = DEFAULT_MAX_MEMORY_CHARS,
        max_history_items: int = DEFAULT_MAX_HISTORY_ITEMS,
        max_history_chars: int = DEFAULT_MAX_HISTORY_CHARS,
        strict: bool = False,
    ):
        self.max_message_chars = max(
            100,
            _safe_int(
                max_message_chars,
                DEFAULT_MAX_MESSAGE_CHARS,
            ),
        )

        self.max_context_chars = max(
            1_000,
            _safe_int(
                max_context_chars,
                DEFAULT_MAX_CONTEXT_CHARS,
            ),
        )

        self.max_memory_items = max(
            0,
            _safe_int(
                max_memory_items,
                DEFAULT_MAX_MEMORY_ITEMS,
            ),
        )

        self.max_memory_chars = max(
            0,
            _safe_int(
                max_memory_chars,
                DEFAULT_MAX_MEMORY_CHARS,
            ),
        )

        self.max_history_items = max(
            0,
            _safe_int(
                max_history_items,
                DEFAULT_MAX_HISTORY_ITEMS,
            ),
        )

        self.max_history_chars = max(
            0,
            _safe_int(
                max_history_chars,
                DEFAULT_MAX_HISTORY_CHARS,
            ),
        )

        self.strict = bool(strict)

        self.stages: List[PipelineStage] = []

        self.calls = 0
        self.successes = 0
        self.failures = 0

        self.last_context: Optional[PipelineContext] = None
        self.last_error: Optional[str] = None

    # ========================================================
    # STAGE REGISTRATION
    # ========================================================

    def add_stage(
        self,
        name: str,
        handler: Callable[[PipelineContext], Any],
        *,
        required: bool = True,
        enabled: bool = True,
        continue_on_error: bool = False,
    ) -> "NovaPipeline":
        if not _clean_text(name):
            raise ValueError(
                "Pipeline stage name cannot be empty."
            )

        if not callable(handler):
            raise TypeError(
                f"Pipeline handler for '{name}' "
                "must be callable."
            )

        self.stages.append(
            PipelineStage(
                name=_clean_text(name),
                handler=handler,
                required=bool(required),
                enabled=bool(enabled),
                continue_on_error=bool(
                    continue_on_error
                ),
            )
        )

        return self

    def remove_stage(
        self,
        name: str,
    ) -> bool:
        target = _clean_text(name).casefold()

        original = len(self.stages)

        self.stages = [
            stage
            for stage in self.stages
            if stage.name.casefold() != target
        ]

        return len(self.stages) != original

    def clear_stages(self) -> None:
        self.stages.clear()

    # ========================================================
    # INPUT
    # ========================================================

    def create_context(
        self,
        message: Any,
        user_email: Any,
        *,
        conversation_id: Optional[str] = None,
        forced_mode: Optional[str] = None,
    ) -> PipelineContext:
        normalized_message = _clean_text(message)
        normalized_email = _clean_text(user_email)

        if not normalized_email:
            raise ValueError(
                "A user email is required."
            )

        if not normalized_message:
            raise ValueError(
                "A message is required."
            )

        if len(normalized_message) > self.max_message_chars:
            raise ValueError(
                "Message exceeds Nova's maximum allowed "
                f"length of {self.max_message_chars} characters."
            )

        context = PipelineContext(
            message=normalized_message,
            user_email=normalized_email,
            conversation_id=conversation_id,
            forced_mode=forced_mode,
        )

        context.metadata["_started_perf"] = (
            time.perf_counter()
        )

        context.metadata["pipeline_version"] = (
            self.VERSION
        )

        context.metadata["message_length"] = (
            len(normalized_message)
        )

        return context

    # ========================================================
    # BUILT-IN PREPROCESSING
    # ========================================================

    def preprocess(
        self,
        context: PipelineContext,
    ) -> PipelineContext:
        """
        Perform cheap deterministic preprocessing.

        This should happen before expensive Nova components.
        """

        message = _clean_text(
            context.message
        )

        context.message = message

        classification = classify_request(
            message
        )

        context.classification = classification

        context.intent = classification.get(
            "intent"
        )

        context.metadata[
            "request_kind"
        ] = classification.get(
            "kind"
        )

        context.metadata[
            "lightweight_request"
        ] = bool(
            classification.get(
                "lightweight",
                False,
            )
        )

        context.metadata[
            "needs_memory"
        ] = bool(
            classification.get(
                "needs_memory",
                False,
            )
        )

        context.metadata[
            "needs_learning_context"
        ] = bool(
            classification.get(
                "needs_learning_context",
                False,
            )
        )

        return context

    # ========================================================
    # MEMORY
    # ========================================================

    def apply_memory_policy(
        self,
        context: PipelineContext,
        memory: Any = None,
    ) -> Any:
        """
        Apply the request-specific memory policy.

        Greetings and other lightweight requests receive NO
        long-term memory.

        Learning requests receive a small, bounded amount.
        """

        policy = MemoryPolicy.for_request(
            context.classification
        )

        if (
            policy.enabled
            and self.max_memory_items >= 0
        ):
            policy = MemoryPolicy(
                enabled=policy.enabled,
                max_items=min(
                    policy.max_items,
                    self.max_memory_items,
                ),
                max_chars=min(
                    policy.max_chars,
                    self.max_memory_chars,
                ),
                include_for_greetings=(
                    policy.include_for_greetings
                ),
                include_for_casual=(
                    policy.include_for_casual
                ),
                include_for_general=(
                    policy.include_for_general
                ),
                include_for_learning=(
                    policy.include_for_learning
                ),
            )

        context.raw_memory = memory

        context.memory_context = select_memory(
            memory,
            policy,
        )

        context.metadata[
            "memory_enabled"
        ] = policy.enabled

        context.metadata[
            "memory_items_limit"
        ] = policy.max_items

        context.metadata[
            "memory_chars_limit"
        ] = policy.max_chars

        return context.memory_context

    # ========================================================
    # CONTEXT LIMITING
    # ========================================================

    def limit_history(
        self,
        history: Any,
    ) -> Any:
        """
        Keep conversation history bounded.

        The newest entries are preferred.
        """

        if history is None:
            return []

        if isinstance(history, str):
            return _truncate(
                history,
                self.max_history_chars,
            )

        if not isinstance(
            history,
            (list, tuple),
        ):
            return history

        items = list(history)

        if self.max_history_items > 0:
            items = items[
                -self.max_history_items:
            ]

        output: List[Any] = []
        total = 0

        for item in items:
            if isinstance(item, Mapping):
                safe = dict(item)
                text = _clean_text(
                    safe.get("content")
                    or safe.get("text")
                    or safe
                )
            else:
                safe = item
                text = _clean_text(item)

            if (
                total + len(text)
                > self.max_history_chars
            ):
                break

            output.append(safe)
            total += len(text)

        return output

    def build_context_snapshot(
        self,
        context: PipelineContext,
    ) -> Dict[str, Any]:
        """
        Build a bounded, model-facing snapshot.

        This is intentionally smaller than the full PipelineContext.
        """

        snapshot = {
            "current_message": context.message,
            "intent": context.intent,
            "mode": context.mode,
            "subject": context.subject,
            "topic": context.topic,
            "difficulty": context.difficulty,
            "teaching_style": context.teaching_style,
            "strategy": context.strategy,
            "settings": context.settings,
            "student_context": context.student_context,
            "profile_analysis": context.profile_analysis,
            "memory": context.memory_context,
        }

        return self._bound_object(
            snapshot,
            self.max_context_chars,
        )

    def _bound_object(
        self,
        value: Any,
        max_chars: int,
    ) -> Any:
        if max_chars <= 0:
            return {}

        if isinstance(value, str):
            return _truncate(
                value,
                max_chars,
            )

        if isinstance(value, Mapping):
            output: Dict[str, Any] = {}
            total = 0

            for key, item in value.items():
                key_text = _clean_text(key)

                if isinstance(item, Mapping):
                    item = self._bound_object(
                        item,
                        max(500, max_chars // 3),
                    )
                elif isinstance(item, list):
                    item = self._bound_object(
                        item,
                        max(500, max_chars // 3),
                    )
                elif isinstance(item, str):
                    item = _truncate(
                        item,
                        max(2_000, max_chars // 4),
                    )

                size = len(
                    _clean_text(item)
                )

                if total + size > max_chars:
                    break

                output[key_text] = item
                total += size

            return output

        if isinstance(value, (list, tuple)):
            output = []
            total = 0

            for item in value:
                bounded = self._bound_object(
                    item,
                    max(500, max_chars // 4),
                )

                size = len(
                    _clean_text(bounded)
                )

                if total + size > max_chars:
                    break

                output.append(bounded)
                total += size

            return output

        return _truncate(
            value,
            max_chars,
        )

    # ========================================================
    # HOOK EXECUTION
    # ========================================================

    def run_stage(
        self,
        context: PipelineContext,
        stage: PipelineStage,
    ) -> bool:
        """
        Execute one stage with timing and failure tracking.
        """

        if not stage.enabled:
            context.mark_stage(
                stage.name,
                "skipped",
                0.0,
            )
            return True

        started = time.perf_counter()

        try:
            result = stage.handler(
                context
            )

            # A stage may return a replacement context.
            if isinstance(
                result,
                PipelineContext,
            ) and result is not context:
                context = result

            duration_ms = (
                time.perf_counter()
                - started
            ) * 1000

            context.mark_stage(
                stage.name,
                "success",
                duration_ms,
            )

            return True

        except Exception as error:
            duration_ms = (
                time.perf_counter()
                - started
            ) * 1000

            context.mark_stage(
                stage.name,
                "failed",
                duration_ms,
            )

            context.error(
                stage.name,
                error,
            )

            context.degrade(
                stage.name
            )

            if stage.required and self.strict:
                raise

            if (
                stage.required
                and not stage.continue_on_error
            ):
                return False

            return True

    # ========================================================
    # RUN
    # ========================================================

    def run(
        self,
        context: PipelineContext,
        *,
        preprocess: bool = True,
        memory: Any = None,
    ) -> PipelineContext:
        """
        Execute the registered stages.

        `preprocess=True` performs the cheap request classifier
        before any expensive custom stages.

        `memory` is passed through the bounded memory policy.
        """

        if not isinstance(
            context,
            PipelineContext,
        ):
            raise TypeError(
                "NovaPipeline.run() requires "
                "a PipelineContext."
            )

        self.calls += 1
        self.last_context = context
        self.last_error = None

        try:
            if preprocess:
                started = time.perf_counter()

                self.preprocess(
                    context
                )

                context.mark_stage(
                    "preprocess",
                    "success",
                    (
                        time.perf_counter()
                        - started
                    ) * 1000,
                )

            # Apply memory policy before custom stages.
            started = time.perf_counter()

            self.apply_memory_policy(
                context,
                memory,
            )

            context.mark_stage(
                "memory_policy",
                "success",
                (
                    time.perf_counter()
                    - started
                ) * 1000,
            )

            for stage in self.stages:
                ok = self.run_stage(
                    context,
                    stage,
                )

                if not ok:
                    context.success = False
                    context.completed = True
                    self.failures += 1
                    self.last_error = (
                        context.errors[-1]["error"]
                        if context.errors
                        else "Pipeline stage failed."
                    )
                    return context

            context.success = not bool(
                context.errors
            )

            context.completed = True

            if context.success:
                self.successes += 1
            else:
                self.failures += 1

            return context

        except Exception as error:
            context.error(
                "pipeline",
                error,
            )

            context.degrade(
                "pipeline"
            )

            context.success = False
            context.completed = True

            self.failures += 1
            self.last_error = str(error)

            if self.strict:
                raise

            return context

    # ========================================================
    # LIGHTWEIGHT RESPONSE
    # ========================================================

    @staticmethod
    def lightweight_response(
        context: PipelineContext,
        *,
        name: Optional[str] = None,
        language: str = "English",
    ) -> Optional[str]:
        """
        Return a deterministic short response for very simple
        conversational requests.

        This avoids spending a full LLM generation on trivial
        messages.

        Returns None when the request should go to the LLM.
        """

        if not context.metadata.get(
            "lightweight_request",
            False,
        ):
            return None

        intent = _clean_text(
            context.intent
        ).casefold()

        student_name = _clean_text(
            name
        )

        # The current V1 backend is English-first.
        # We keep the parameter for future localization.
        _ = language

        if intent == "greeting":
            if student_name:
                return (
                    f"Hello {student_name}! "
                    "How can I help you today?"
                )

            return (
                "Hello! How can I help you today?"
            )

        if intent == "thanks":
            return "You're welcome."

        if intent == "farewell":
            return "Goodbye!"

        return None

    # ========================================================
    # RESULT HELPERS
    # ========================================================

    def diagnostics(
        self,
        context: Optional[PipelineContext] = None,
    ) -> Dict[str, Any]:
        target = (
            context
            or self.last_context
        )

        if target is None:
            return {
                "pipeline_version": self.VERSION,
                "calls": self.calls,
                "successes": self.successes,
                "failures": self.failures,
                "last_error": self.last_error,
                "stages": [],
            }

        return {
            "pipeline_version": self.VERSION,
            "request_id": target.request_id,
            "calls": self.calls,
            "successes": self.successes,
            "failures": self.failures,
            "last_error": self.last_error,
            "stage_times": dict(
                target.stage_times
            ),
            "stage_status": dict(
                target.stage_status
            ),
            "warnings": list(
                target.warnings
            ),
            "errors": list(
                target.errors
            ),
            "degraded_components": list(
                target.degraded_components
            ),
            "metadata": {
                key: value
                for key, value in target.metadata.items()
                if not key.startswith("_")
            },
        }

    def health(self) -> Dict[str, Any]:
        return {
            "name": "NovaPipeline",
            "version": self.VERSION,
            "healthy": True,
            "calls": self.calls,
            "successes": self.successes,
            "failures": self.failures,
            "last_error": self.last_error,
            "registered_stages": [
                stage.name
                for stage in self.stages
                if stage.enabled
            ],
        }


# ============================================================
# COMPATIBILITY ALIAS
# ============================================================

Pipeline = NovaPipeline


__all__ = [
    "PIPELINE_VERSION",
    "PipelineContext",
    "PipelineStage",
    "MemoryPolicy",
    "NovaPipeline",
    "Pipeline",
    "classify_request",
    "select_memory",
]
