from __future__ import annotations

import inspect
import time
import traceback
import uuid

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple


# ============================================================
# MEMORY SYSTEM
# ============================================================

from backend.memory_system.memory_manager import MemoryManager
from backend.memory_system.learning_memory import LearningMemory
from backend.memory_system.conversation_manager import ConversationManager


# ============================================================
# TUTOR SYSTEM
# ============================================================

from backend.tutor_system.tutor_engine import TutorEngine
from backend.tutor_system.tutor_mode import TutorModeDetector
from backend.tutor_system.adaptive_tutor import AdaptiveTutor
from backend.tutor_system.teacher_brain import TeacherBrain


# ============================================================
# BRAIN
# ============================================================

from backend.brain.brain import NovaBrain


# ============================================================
# STUDENT
# ============================================================

from student_profile import StudentProfile
from backend.student.knowledge_map import KnowledgeMap


# ============================================================
# LEARNING
# ============================================================

from backend.learning_graph import LearningGraph
from backend.learning.analyzer import LearningAnalyzer
from backend.learning.understanding import UnderstandingTracker
from backend.learning.understanding import UnderstandingAnalyzer
from backend.learning.session_manager import SessionManager
from backend.learning.progress_tracker import ProgressTracker
from backend.learning.difficulty_engine import DifficultyEngine


# ============================================================
# INPUT ANALYSIS
# ============================================================

from backend.intent_detector import IntentDetector
from backend.subject_detector import SubjectDetector


# ============================================================
# RESPONSE
# ============================================================

from backend.prompt.response_formatter import format_response
from backend.learning.answer_verifier import AnswerVerifier


# ============================================================
# SETTINGS
# ============================================================

from backend.settings import SettingsManager


# ============================================================
# REQUEST CONTEXT
# ============================================================

@dataclass
class NovaRequestContext:
    """
    Runtime context for one Nova request.

    This object prevents the entire processing pipeline from
    depending on dozens of mutable NovaCore attributes.

    NovaCore still keeps compatibility runtime attributes such
    as `current_subject` and `last_response`, but the real
    request state lives here while a request is being processed.
    """

    request_id: str

    started_at: str

    started_timestamp: float

    user_email: str

    conversation_id: Optional[str] = None

    original_message: str = ""

    tutor_message: str = ""

    intent: Optional[str] = None

    mode: Optional[str] = None

    subject: Optional[str] = None

    topic: Optional[str] = None

    strategy: Dict[str, Any] = field(
        default_factory=dict
    )

    difficulty: Any = None

    memory_context: Any = None

    settings: Dict[str, Any] = field(
        default_factory=dict
    )

    teaching_style: Any = None

    profile_analysis: Dict[str, Any] = field(
        default_factory=dict
    )

    answer: str = ""

    verified_answer: str = ""

    understanding: Dict[str, Any] = field(
        default_factory=dict
    )

    confidence: float = 50.0

    stage_times: Dict[str, float] = field(
        default_factory=dict
    )

    stage_status: Dict[str, str] = field(
        default_factory=dict
    )

    warnings: List[str] = field(
        default_factory=list
    )

    errors: List[Dict[str, Any]] = field(
        default_factory=list
    )

    degraded_components: List[str] = field(
        default_factory=list
    )

    completed: bool = False

    success: bool = False

    def add_warning(
        self,
        message: Any
    ) -> None:

        text = str(
            message
        ).strip()

        if text and text not in self.warnings:

            self.warnings.append(
                text
            )

    def add_error(
        self,
        component: str,
        error: Any
    ) -> None:

        self.errors.append({

            "component":
                str(component),

            "error":
                str(error)
        })

    def mark_degraded(
        self,
        component: str
    ) -> None:

        component = str(
            component
        ).strip()

        if (
            component
            and component not in self.degraded_components
        ):

            self.degraded_components.append(
                component
            )

    def mark_stage(
        self,
        stage: str,
        status: str,
        duration_ms: float = 0.0
    ) -> None:

        self.stage_status[
            stage
        ] = status

        self.stage_times[
            stage
        ] = round(
            float(duration_ms),
            3
        )

    def duration_ms(self) -> float:

        return round(
            (
                time.perf_counter()
                - self.started_timestamp
            ) * 1000,
            3
        )


# ============================================================
# COMPONENT HEALTH
# ============================================================

@dataclass
class ComponentHealth:
    """
    Tracks runtime health of one Nova subsystem.
    """

    name: str

    initialized: bool = False

    available: bool = False

    calls: int = 0

    successes: int = 0

    failures: int = 0

    last_error: Optional[str] = None

    last_call_at: Optional[str] = None

    total_duration_ms: float = 0.0

    def record_success(
        self,
        duration_ms: float
    ) -> None:

        self.calls += 1

        self.successes += 1

        self.total_duration_ms += (
            float(duration_ms)
        )

        self.last_call_at = (
            datetime.now().isoformat()
        )

        self.last_error = None

    def record_failure(
        self,
        duration_ms: float,
        error: Any
    ) -> None:

        self.calls += 1

        self.failures += 1

        self.total_duration_ms += (
            float(duration_ms)
        )

        self.last_call_at = (
            datetime.now().isoformat()
        )

        self.last_error = str(
            error
        )

    def average_duration_ms(
        self
    ) -> float:

        if self.calls <= 0:

            return 0.0

        return round(
            self.total_duration_ms
            / self.calls,
            3
        )

    def to_dict(
        self
    ) -> Dict[str, Any]:

        return {

            "name":
                self.name,

            "initialized":
                self.initialized,

            "available":
                self.available,

            "calls":
                self.calls,

            "successes":
                self.successes,

            "failures":
                self.failures,

            "average_duration_ms":
                self.average_duration_ms(),

            "last_error":
                self.last_error,

            "last_call_at":
                self.last_call_at
        }


# ============================================================
# NOVA CORE
# ============================================================

class NovaCore:
    """
    ============================================================
    NOVA CORE V3
    ============================================================

    Central orchestration engine for Nova.

    NovaCore coordinates:

        - memory
        - conversations
        - student profile
        - learning state
        - subject detection
        - intent detection
        - tutor mode
        - NovaBrain
        - adaptive tutoring
        - teaching strategy
        - difficulty
        - long-term memory
        - progress
        - knowledge mapping
        - response generation
        - answer verification
        - response formatting
        - diagnostics

    NovaCore does NOT generate the actual language response.

    The LLM remains behind TutorEngine.

    ------------------------------------------------------------
    ARCHITECTURE
    ------------------------------------------------------------

    Request
        |
        v
    Validation
        |
        v
    User context
        |
        v
    Conversation
        |
        v
    Intent
        |
        v
    Mode
        |
        v
    Subject
        |
        v
    Topic
        |
        v
    Learning analysis
        |
        v
    NovaBrain
        |
        v
    Difficulty
        |
        v
    Memory
        |
        v
    Settings
        |
        v
    TutorEngine
        |
        v
    Verification
        |
        v
    Formatting
        |
        v
    Understanding
        |
        v
    Learning updates
        |
        v
    Conversation persistence
        |
        v
    Structured frontend-ready result

    ------------------------------------------------------------
    DESIGN GOALS
    ------------------------------------------------------------

        - Reliability
        - Clear separation of stages
        - User isolation
        - Graceful degradation
        - Debuggability
        - Compatibility
        - Performance visibility
        - Frontend readiness
        - Future streaming support
        - Future tools support
        - Future API support
    """

    VERSION = "3.0"

    # =========================================================
    # DEFAULT SETTINGS
    # =========================================================

    DEFAULT_SETTINGS = {

        "name": "",

        "language":
            "English",

        "level":
            "High School",

        "teaching_style":
            "adaptive",

        "difficulty":
            "adaptive",

        "hints":
            "when_needed",

        "step_by_step":
            True,

        "adaptive_learning":
            True,

        "response_length":
            "balanced",

        "tone":
            "friendly",

        "use_examples":
            True,

        "use_analogies":
            True,

        "encouragement":
            True,

        "correction_style":
            "explain",

        "show_correct_answer":
            True,

        "creativity":
            "medium",

        "behavior":
            "",

        "custom_instructions":
            ""
    }

    # =========================================================
    # LIMITS
    # =========================================================

    MAX_MESSAGE_LENGTH = 20000

    MAX_EMAIL_LENGTH = 320

    MAX_CONVERSATION_ID_LENGTH = 256

    MAX_MODE_LENGTH = 100

    MAX_SUBJECT_LENGTH = 200

    MAX_TOPIC_LENGTH = 300

    MAX_WARNINGS = 20

    MAX_ERRORS = 20

    MAX_HISTORY = 20

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        demo: bool = False,
        debug: bool = False
    ):

        self.demo = bool(
            demo
        )

        self.debug = bool(
            debug
        )

        self.version = (
            self.VERSION
        )

        self.initialized_at = (
            datetime.now().isoformat()
        )

        self.initialized_timestamp = (
            time.perf_counter()
        )

        # -----------------------------------------------------
        # RUNTIME
        # -----------------------------------------------------

        self.current_request: Optional[
            NovaRequestContext
        ] = None

        self.current_user_email = None

        self.current_conversation_id = None

        self.current_subject = None

        self.current_topic = None

        self.last_intent = None

        self.last_mode = None

        self.last_strategy = None

        self.last_difficulty = None

        self.last_response = None

        self.last_error = None

        self.last_request_id = None

        self.last_request_duration_ms = 0.0

        self.total_requests = 0

        self.successful_requests = 0

        self.failed_requests = 0

        self.degraded_requests = 0

        # -----------------------------------------------------
        # REQUEST HISTORY
        # -----------------------------------------------------

        self.request_history: List[
            Dict[str, Any]
        ] = []

        # -----------------------------------------------------
        # COMPONENT HEALTH
        # -----------------------------------------------------

        self.component_health: Dict[
            str,
            ComponentHealth
        ] = {}

        # -----------------------------------------------------
        # HOOKS
        # -----------------------------------------------------

        self.before_request_hooks: List[
            Callable
        ] = []

        self.after_request_hooks: List[
            Callable
        ] = []

        self.stage_hooks: List[
            Callable
        ] = []

        # -----------------------------------------------------
        # INITIALIZATION
        # -----------------------------------------------------

        self._print_startup()

        self._initialize_components()

        self._register_component_health()

        self._print_ready()

    # =========================================================
    # STARTUP
    # =========================================================

    def _print_startup(
        self
    ) -> None:

        print(
            "\n"
            "=================================================="
        )

        print(
            "Initializing Nova Core..."
        )

        print(
            f"Nova Core version: {self.version}"
        )

        print(
            f"Demo mode: {self.demo}"
        )

        print(
            f"Debug mode: {self.debug}"
        )

    def _print_ready(
        self
    ) -> None:

        print(
            "Nova Core ready."
        )

        print(
            "==================================================\n"
        )

    # =========================================================
    # COMPONENT INITIALIZATION
    # =========================================================

    def _initialize_components(
        self
    ) -> None:

        self._initialize_memory()

        self._initialize_conversations()

        self._initialize_student()

        self._initialize_learning()

        self._initialize_analysis()

        self._initialize_tutor()

        self._initialize_settings()

    # ---------------------------------------------------------

    def _initialize_memory(
        self
    ) -> None:

        self.memory = MemoryManager()

        self.learning_memory = (
            LearningMemory()
        )

    # ---------------------------------------------------------

    def _initialize_conversations(
        self
    ) -> None:

        self.conversations = (
            ConversationManager(
                persist=not self.demo
            )
        )

    # ---------------------------------------------------------

    def _initialize_student(
        self
    ) -> None:

        self.student = StudentProfile()

    # ---------------------------------------------------------

    def _initialize_learning(
        self
    ) -> None:

        self.learning = (
            LearningGraph()
        )

        self.session = (
            SessionManager()
        )

        self.analyzer = (
            LearningAnalyzer()
        )

        self.understanding_tracker = (
            UnderstandingTracker()
        )

        self.understanding = (
            UnderstandingAnalyzer()
        )

        self.difficulty = (
            DifficultyEngine()
        )

        self.adaptive_tutor = (
            AdaptiveTutor()
        )

        self.teacher_brain = (
            TeacherBrain()
        )

        self.brain = (
            NovaBrain()
        )

        self.progress = None

        self.knowledge_map = None

    # ---------------------------------------------------------

    def _initialize_analysis(
        self
    ) -> None:

        self.intent = (
            IntentDetector()
        )

        self.subject = (
            SubjectDetector()
        )

        self.mode = (
            TutorModeDetector()
        )

        self.answer_verifier = (
            AnswerVerifier()
        )

    # ---------------------------------------------------------

    def _initialize_tutor(
        self
    ) -> None:

        self.tutor = (
            TutorEngine(
                student=self.student,
                brain=self.brain
            )
        )

    # ---------------------------------------------------------

    def _initialize_settings(
        self
    ) -> None:

        self.settings = (
            SettingsManager()
        )

    # =========================================================
    # COMPONENT HEALTH REGISTRATION
    # =========================================================

    def _register_component_health(
        self
    ) -> None:

        components = {

            "memory":
                self.memory,

            "learning_memory":
                self.learning_memory,

            "conversations":
                self.conversations,

            "student":
                self.student,

            "learning_graph":
                self.learning,

            "session":
                self.session,

            "learning_analyzer":
                self.analyzer,

            "understanding_tracker":
                self.understanding_tracker,

            "understanding":
                self.understanding,

            "difficulty":
                self.difficulty,

            "adaptive_tutor":
                self.adaptive_tutor,

            "teacher_brain":
                self.teacher_brain,

            "brain":
                self.brain,

            "intent":
                self.intent,

            "subject":
                self.subject,

            "mode":
                self.mode,

            "answer_verifier":
                self.answer_verifier,

            "tutor":
                self.tutor,

            "settings":
                self.settings
        }

        for name, component in components.items():

            self.component_health[
                name
            ] = ComponentHealth(

                name=name,

                initialized=True,

                available=(
                    component is not None
                )
            )

    # =========================================================
    # PUBLIC PROCESS
    # =========================================================

    def process(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        user_email: Optional[str] = None,
        forced_mode: Optional[str] = None
    ) -> Dict[str, Any]:

        request = None

        self.last_error = None

        self.total_requests += 1

        try:

            # =================================================
            # REQUEST CREATION
            # =================================================

            request = (
                self._create_request_context(
                    message=message,
                    user_email=user_email
                )
            )

            self.current_request = request

            self.last_request_id = (
                request.request_id
            )

            # =================================================
            # HOOKS
            # =================================================

            self._run_hooks(
                self.before_request_hooks,
                request
            )

            # =================================================
            # VALIDATION
            # =================================================

            self._run_stage(
                request,
                "validation",
                self._stage_validate,
                conversation_id,
                forced_mode
            )

            # =================================================
            # USER SYSTEMS
            # =================================================

            self._run_stage(
                request,
                "user_context",
                self._stage_user_context
            )

            # =================================================
            # CONVERSATION
            # =================================================

            self._run_stage(
                request,
                "conversation",
                self._stage_conversation
            )

            # =================================================
            # SAVE USER MESSAGE
            # =================================================

            self._run_stage(
                request,
                "save_user_message",
                self._stage_save_user_message
            )

            # =================================================
            # INPUT ANALYSIS
            # =================================================

            self._run_stage(
                request,
                "intent",
                self._stage_intent
            )

            self._run_stage(
                request,
                "mode",
                self._stage_mode,
                forced_mode
            )

            self._run_stage(
                request,
                "subject",
                self._stage_subject
            )

            self._run_stage(
                request,
                "topic",
                self._stage_topic
            )

            # =================================================
            # LEARNING STATE
            # =================================================

            self._run_stage(
                request,
                "session",
                self._stage_session
            )

            self._run_stage(
                request,
                "student_activity",
                self._stage_student_activity
            )

            self._run_stage(
                request,
                "profile",
                self._stage_profile
            )

            self._run_stage(
                request,
                "teaching_style",
                self._stage_teaching_style
            )

            # =================================================
            # BRAIN
            # =================================================

            self._run_stage(
                request,
                "brain",
                self._stage_brain
            )

            # =================================================
            # DIFFICULTY
            # =================================================

            self._run_stage(
                request,
                "difficulty",
                self._stage_difficulty
            )

            # =================================================
            # MEMORY
            # =================================================

            self._run_stage(
                request,
                "memory",
                self._stage_memory
            )

            # =================================================
            # SETTINGS
            # =================================================

            self._run_stage(
                request,
                "settings",
                self._stage_settings
            )

            # =================================================
            # PERSONALIZATION
            # =================================================

            self._run_stage(
                request,
                "personalization",
                self._stage_personalization
            )

            # =================================================
            # GENERATION
            # =================================================

            self._run_stage(
                request,
                "generation",
                self._stage_generation
            )

            # =================================================
            # VERIFICATION
            # =================================================

            self._run_stage(
                request,
                "verification",
                self._stage_verification
            )

            # =================================================
            # FORMATTING
            # =================================================

            self._run_stage(
                request,
                "formatting",
                self._stage_formatting
            )

            # =================================================
            # UNDERSTANDING
            # =================================================

            self._run_stage(
                request,
                "understanding",
                self._stage_understanding
            )

            # =================================================
            # CONFIDENCE
            # =================================================

            self._run_stage(
                request,
                "confidence",
                self._stage_confidence
            )

            # =================================================
            # LEARNING UPDATES
            # =================================================

            self._run_stage(
                request,
                "memory_update",
                self._stage_memory_update
            )

            self._run_stage(
                request,
                "progress",
                self._stage_progress
            )

            self._run_stage(
                request,
                "learning_memory",
                self._stage_learning_memory
            )

            self._run_stage(
                request,
                "knowledge_map",
                self._stage_knowledge_map
            )

            # =================================================
            # UNDERSTANDING TRACKING
            # =================================================

            self._run_stage(
                request,
                "understanding_tracking",
                self._stage_understanding_tracking
            )

            # =================================================
            # SAVE RESPONSE
            # =================================================

            self._run_stage(
                request,
                "save_response",
                self._stage_save_response
            )

            # =================================================
            # RUNTIME STATE
            # =================================================

            self._run_stage(
                request,
                "runtime_state",
                self._stage_runtime_state
            )

            # =================================================
            # COMPLETE
            # =================================================

            request.success = True

            request.completed = True

            self.successful_requests += 1

            if request.degraded_components:

                self.degraded_requests += 1

            result = (
                self._build_result(
                    request
                )
            )

            # =================================================
            # AFTER HOOKS
            # =================================================

            self._run_hooks(
                self.after_request_hooks,
                request
            )

            self._record_request_history(
                request
            )

            return result

        except Exception as error:

            self.failed_requests += 1

            if request is None:

                request = (
                    self._create_emergency_context(
                        message,
                        user_email
                    )
                )

            request.completed = True

            request.success = False

            request.add_error(
                "process",
                error
            )

            self.last_error = str(
                error
            )

            self._handle_process_error(
                error,
                request
            )

            self._record_request_history(
                request
            )

            return (
                self._build_error_result(
                    request
                )
            )

        finally:

            if request is not None:

                self.last_request_duration_ms = (
                    request.duration_ms()
                )

    # =========================================================
    # REQUEST CREATION
    # =========================================================

    def _create_request_context(
        self,
        message,
        user_email
    ) -> NovaRequestContext:

        normalized_email = (
            self._validate_email(
                user_email
            )
        )

        normalized_message = (
            self._normalize_message(
                message
            )
        )

        return NovaRequestContext(

            request_id=self._generate_request_id(),

            started_at=(
                datetime.now().isoformat()
            ),

            started_timestamp=(
                time.perf_counter()
            ),

            user_email=normalized_email,

            original_message=normalized_message
        )

    # ---------------------------------------------------------

    def _create_emergency_context(
        self,
        message,
        user_email
    ) -> NovaRequestContext:

        try:

            email = (
                self._validate_email(
                    user_email
                )
            )

        except Exception:

            email = "unknown"

        try:

            normalized_message = (
                self._normalize_message(
                    message
                )
            )

        except Exception:

            normalized_message = ""

        return NovaRequestContext(

            request_id=self._generate_request_id(),

            started_at=(
                datetime.now().isoformat()
            ),

            started_timestamp=(
                time.perf_counter()
            ),

            user_email=email,

            original_message=normalized_message
        )

    # =========================================================
    # REQUEST ID
    # =========================================================

    def _generate_request_id(
        self
    ) -> str:

        return (
            "nova-"
            + uuid.uuid4().hex
        )

    # =========================================================
    # STAGE RUNNER
    # =========================================================

    def _run_stage(
        self,
        request: NovaRequestContext,
        stage_name: str,
        function: Callable,
        *args
    ) -> Any:

        started = time.perf_counter()

        try:

            self._run_stage_hooks(
                request,
                stage_name,
                "before"
            )

            result = function(
                request,
                *args
            )

            duration_ms = (
                time.perf_counter()
                - started
            ) * 1000

            request.mark_stage(
                stage_name,
                "success",
                duration_ms
            )

            self._run_stage_hooks(
                request,
                stage_name,
                "after"
            )

            return result

        except Exception as error:

            duration_ms = (
                time.perf_counter()
                - started
            ) * 1000

            request.mark_stage(
                stage_name,
                "failed",
                duration_ms
            )

            request.add_error(
                stage_name,
                error
            )

            self._log_error(
                f"Stage failed: {stage_name}",
                error
            )

            raise

    # =========================================================
    # STAGE HOOKS
    # =========================================================

    def _run_stage_hooks(
        self,
        request,
        stage_name,
        event
    ) -> None:

        for hook in list(
            self.stage_hooks
        ):

            try:

                hook(
                    request,
                    stage_name,
                    event
                )

            except Exception as error:

                request.add_warning(
                    f"Stage hook failed: {error}"
                )

                if self.debug:

                    self._log_error(
                        "Stage hook failure",
                        error
                    )

    # =========================================================
    # GENERAL HOOKS
    # =========================================================

    def _run_hooks(
        self,
        hooks,
        request
    ) -> None:

        for hook in list(
            hooks
        ):

            try:

                hook(
                    request
                )

            except Exception as error:

                request.add_warning(
                    f"Request hook failed: {error}"
                )

                if self.debug:

                    self._log_error(
                        "Request hook failure",
                        error
                    )

    # =========================================================
    # STAGE: VALIDATION
    # =========================================================

    def _stage_validate(
        self,
        request,
        conversation_id,
        forced_mode
    ) -> None:

        if conversation_id is not None:

            request.conversation_id = (
                self._normalize_identifier(
                    conversation_id,
                    self.MAX_CONVERSATION_ID_LENGTH
                )
            )

        if forced_mode is not None:

            forced_mode = (
                self._normalize_identifier(
                    forced_mode,
                    self.MAX_MODE_LENGTH
                )
            )

    # =========================================================
    # STAGE: USER CONTEXT
    # =========================================================

    def _stage_user_context(
        self,
        request
    ) -> None:

        self._prepare_user_systems(
            request.user_email
        )

    # =========================================================
    # USER SYSTEMS
    # =========================================================

    def _prepare_user_systems(
        self,
        user_email
    ) -> None:

        self.knowledge_map = (
            KnowledgeMap(
                user_email
            )
        )

        self.progress = (
            ProgressTracker(
                user_email
            )
        )

    # =========================================================
    # STAGE: CONVERSATION
    # =========================================================

    def _stage_conversation(
        self,
        request
    ) -> None:

        conversation_id = (
            request.conversation_id
        )

        if conversation_id is None:

            conversation_id = (
                self._safe_conversation_create(
                    request.user_email
                )
            )

        else:

            conversation_exists = (
                self._safe_conversation_get(
                    request.user_email,
                    conversation_id
                )
            )

            if conversation_exists is None:

                conversation_id = (
                    self._safe_conversation_create(
                        request.user_email
                    )
                )

                request.add_warning(
                    "The requested conversation was unavailable; a new conversation was created."
                )

        request.conversation_id = (
            conversation_id
        )

    # ---------------------------------------------------------

    def _safe_conversation_create(
        self,
        user_email
    ):

        result = (
            self._component_call(
                "conversations",
                self.conversations.create,
                user_email
            )
        )

        if result is None:

            raise RuntimeError(
                "ConversationManager did not return a conversation ID."
            )

        return str(
            result
        )

    # ---------------------------------------------------------

    def _safe_conversation_get(
        self,
        user_email,
        conversation_id
    ):

        return (
            self._component_call(
                "conversations",
                self.conversations.get,
                user_email,
                conversation_id
            )
        )

    # =========================================================
    # COMPONENT CALL
    # =========================================================

    def _component_call(
        self,
        component_name: str,
        function: Callable,
        *args,
        **kwargs
    ) -> Any:

        health = (
            self.component_health.get(
                component_name
            )
        )

        started = time.perf_counter()

        try:

            result = function(
                *args,
                **kwargs
            )

            duration_ms = (
                time.perf_counter()
                - started
            ) * 1000

            if health:

                health.record_success(
                    duration_ms
                )

            return result

        except Exception as error:

            duration_ms = (
                time.perf_counter()
                - started
            ) * 1000

            if health:

                health.record_failure(
                    duration_ms,
                    error
                )

            raise

    # =========================================================
    # STAGE: SAVE USER MESSAGE
    # =========================================================

    def _stage_save_user_message(
        self,
        request
    ) -> None:

        self._component_call(

            "conversations",

            self.conversations.add_message,

            request.user_email,

            request.conversation_id,

            "user",

            request.original_message
        )

    # =========================================================
    # STAGE: INTENT
    # =========================================================

    def _stage_intent(
        self,
        request
    ) -> None:

        request.intent = (
            self._component_call(

                "intent",

                self.intent.detect,

                request.original_message
            )
        )

        request.intent = (
            self._normalize_optional_text(
                request.intent
            )
        )

    # =========================================================
    # STAGE: MODE
    # =========================================================

    def _stage_mode(
        self,
        request,
        forced_mode
    ) -> None:

        forced = (
            self._normalize_optional_text(
                forced_mode
            )
        )

        if forced:

            request.mode = (
                self._normalize_mode(
                    forced
                )
            )

            return

        request.mode = (
            self._component_call(

                "mode",

                self.mode.detect,

                request.original_message
            )
        )

        request.mode = (
            self._normalize_mode(
                request.mode
            )
        )

    # =========================================================
    # STAGE: SUBJECT
    # =========================================================

    def _stage_subject(
        self,
        request
    ) -> None:

        request.subject = (
            self._component_call(

                "subject",

                self.subject.detect,

                request.original_message
            )
        )

        request.subject = (
            self._normalize_optional_text(
                request.subject
            )
        )

    # =========================================================
    # STAGE: TOPIC
    # =========================================================

    def _stage_topic(
        self,
        request
    ) -> None:

        request.topic = (
            self._detect_topic(
                request.original_message,
                request.subject
            )
        )

    # =========================================================
    # TOPIC DETECTION
    # =========================================================

    def _detect_topic(
        self,
        message,
        subject
    ) -> Optional[str]:

        # -----------------------------------------------------
        # Some SubjectDetector implementations may provide
        # topic detection. Use it when available.
        # -----------------------------------------------------

        detector = self.subject

        method = getattr(
            detector,
            "detect_topic",
            None
        )

        if callable(
            method
        ):

            try:

                result = (
                    self._component_call(
                        "subject",
                        method,
                        message,
                        subject
                    )
                )

                normalized = (
                    self._normalize_optional_text(
                        result
                    )
                )

                if normalized:

                    return normalized

            except TypeError:

                try:

                    result = (
                        self._component_call(
                            "subject",
                            method,
                            message
                        )
                    )

                    normalized = (
                        self._normalize_optional_text(
                            result
                        )
                    )

                    if normalized:

                        return normalized

                except Exception as error:

                    self._log_error(
                        "Topic detection fallback failed",
                        error
                    )

            except Exception as error:

                self._log_error(
                    "Topic detection failed",
                    error
                )

        # -----------------------------------------------------
        # Optional generic topic detector.
        # -----------------------------------------------------

        detector_method = getattr(
            self,
            "topic_detector",
            None
        )

        if detector_method:

            try:

                result = (
                    detector_method.detect(
                        message
                    )
                )

                return (
                    self._normalize_optional_text(
                        result
                    )
                )

            except Exception:

                pass

        return None

    # =========================================================
    # STAGE: SESSION
    # =========================================================

    def _stage_session(
        self,
        request
    ) -> None:

        if not request.subject:

            return

        try:

            self._component_call(

                "session",

                self.session.start,

                request.subject,

                request.original_message,

                request.mode
            )

        except Exception as error:

            request.mark_degraded(
                "session"
            )

            request.add_warning(
                "Session tracking was unavailable."
            )

            self._log_error(
                "Session tracking failed",
                error
            )

    # =========================================================
    # STAGE: STUDENT ACTIVITY
    # =========================================================

    def _stage_student_activity(
        self,
        request
    ) -> None:

        try:

            self.student.add_question(
                request.subject
            )

        except Exception as error:

            request.mark_degraded(
                "student_activity"
            )

            request.add_warning(
                "Student activity tracking failed."
            )

            self._log_error(
                "Student activity tracking failed",
                error
            )

        if request.subject:

            try:

                self._component_call(

                    "learning_graph",

                    self.learning.add_subject,

                    request.subject
                )

            except Exception as error:

                request.mark_degraded(
                    "learning_graph"
                )

                request.add_warning(
                    "Learning graph update failed."
                )

                self._log_error(
                    "Learning graph update failed",
                    error
                )

    # =========================================================
    # STAGE: PROFILE
    # =========================================================

    def _stage_profile(
        self,
        request
    ) -> None:

        profile = self._safe_student_profile()

        try:

            analysis = (
                self._component_call(

                    "learning_analyzer",

                    self.analyzer.analyze,

                    profile
                )
            )

        except Exception as error:

            request.mark_degraded(
                "learning_analyzer"
            )

            request.add_warning(
                "Student profile analysis was unavailable."
            )

            self._log_error(
                "Student profile analysis failed",
                error
            )

            analysis = {}

        if not isinstance(
            analysis,
            dict
        ):

            analysis = {}

        request.profile_analysis = (
            dict(
                analysis
            )
        )

        strengths = analysis.get(
            "strengths"
        )

        weaknesses = analysis.get(
            "weaknesses"
        )

        if isinstance(
            strengths,
            list
        ):

            self.student.profile[
                "strengths"
            ] = strengths

        if isinstance(
            weaknesses,
            list
        ):

            self.student.profile[
                "weaknesses"
            ] = weaknesses

        try:

            self.student.save()

        except Exception as error:

            request.mark_degraded(
                "student_profile_save"
            )

            request.add_warning(
                "Student profile could not be saved."
            )

            self._log_error(
                "Student profile save failed",
                error
            )

    # =========================================================
    # STAGE: TEACHING STYLE
    # =========================================================

    def _stage_teaching_style(
        self,
        request
    ) -> None:

        try:

            request.teaching_style = (
                self._component_call(

                    "teacher_brain",

                    self.teacher_brain.decide,

                    self.knowledge_map.get(),

                    request.subject
                )
            )

        except Exception as error:

            request.mark_degraded(
                "teacher_brain"
            )

            request.add_warning(
                "Teaching style analysis was unavailable."
            )

            request.teaching_style = (
                "adaptive"
            )

            self._log_error(
                "Teaching style analysis failed",
                error
            )

    # =========================================================
    # STAGE: BRAIN
    # =========================================================

    def _stage_brain(
        self,
        request
    ) -> None:

        understanding_context = (
            self._safe_understanding_context(
                request.subject
            )
        )

        try:

            # -------------------------------------------------
            # Modern signature:
            #
            # think(student, subject, topic, understanding)
            # -------------------------------------------------

            request.strategy = (
                self._component_call(

                    "brain",

                    self.brain.think,

                    self._safe_student_profile(),

                    request.subject,

                    request.topic,

                    understanding_context
                )
            )

        except TypeError:

            # -------------------------------------------------
            # Compatibility with older NovaBrain signatures.
            # -------------------------------------------------

            try:

                request.strategy = (
                    self._component_call(

                        "brain",

                        self.brain.think,

                        self._safe_student_profile(),

                        request.subject,

                        request.original_message,

                        self._safe_knowledge_map()
                    )
                )

            except Exception as error:

                request.mark_degraded(
                    "brain"
                )

                request.add_warning(
                    "NovaBrain could not determine a strategy."
                )

                request.strategy = {}

                self._log_error(
                    "NovaBrain compatibility call failed",
                    error
                )

        except Exception as error:

            request.mark_degraded(
                "brain"
            )

            request.add_warning(
                "NovaBrain could not determine a strategy."
            )

            request.strategy = {}

            self._log_error(
                "NovaBrain failed",
                error
            )

        if not isinstance(
            request.strategy,
            dict
        ):

            request.strategy = {}

    # =========================================================
    # STAGE: DIFFICULTY
    # =========================================================

    def _stage_difficulty(
        self,
        request
    ) -> None:

        confidence = (
            self._extract_strategy_confidence(
                request.strategy
            )
        )

        try:

            request.difficulty = (
                self._component_call(

                    "difficulty",

                    self.difficulty.decide,

                    confidence
                )
            )

        except Exception as error:

            request.mark_degraded(
                "difficulty"
            )

            request.add_warning(
                "Difficulty adaptation was unavailable."
            )

            request.difficulty = {

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
                        "Use a clear explanation "
                        "appropriate for the student's "
                        "current understanding."
                    )
            }

            self._log_error(
                "Difficulty engine failed",
                error
            )

    # =========================================================
    # STAGE: MEMORY
    # =========================================================

    def _stage_memory(
        self,
        request
    ) -> None:

        if self.demo:

            request.memory_context = (
                "No persistent memory in demo mode."
            )

            return

        try:

            request.memory_context = (
                self._component_call(

                    "memory",

                    self.memory.build_context,

                    email=request.user_email,

                    query=request.original_message,

                    subject=request.subject,

                    limit=8
                )
            )

        except Exception as error:

            request.mark_degraded(
                "memory"
            )

            request.add_warning(
                "Long-term memory was unavailable for this request."
            )

            request.memory_context = (
                "No relevant long-term memory."
            )

            self._log_error(
                "Memory retrieval failed",
                error
            )

    # =========================================================
    # STAGE: SETTINGS
    # =========================================================

    def _stage_settings(
        self,
        request
    ) -> None:

        if self.demo:

            request.settings = (
                self._default_settings()
            )

            return

        try:

            settings = (
                self._component_call(

                    "settings",

                    self.settings.get
                )
            )

        except Exception as error:

            request.mark_degraded(
                "settings"
            )

            request.add_warning(
                "User settings could not be loaded."
            )

            settings = {}

            self._log_error(
                "Settings retrieval failed",
                error
            )

        request.settings = (
            self._merge_settings(
                settings
            )
        )

    # =========================================================
    # STAGE: PERSONALIZATION
    # =========================================================

    def _stage_personalization(
        self,
        request
    ) -> None:

        settings = request.settings

        student_name = (
            settings.get(
                "name",
                ""
            )
        )

        language = (
            settings.get(
                "language",
                "English"
            )
        )

        level = (
            settings.get(
                "level",
                "High School"
            )
        )

        behavior = (
            settings.get(
                "behavior",
                ""
            )
        )

        custom = (
            settings.get(
                "custom_instructions",
                ""
            )
        )

        if not any([
            student_name,
            behavior,
            custom
        ]):

            request.tutor_message = (
                request.original_message
            )

            return

        request.tutor_message = f"""
Student profile:

Name:
{student_name}

Language:
{language}

Academic level:
{level}

Personal preferences:
{behavior}

Custom instructions:
{custom}

Student's original question:

{request.original_message}
""".strip()

    # =========================================================
    # STAGE: GENERATION
    # =========================================================

    def _stage_generation(
        self,
        request
    ) -> None:

        if not request.tutor_message:

            request.tutor_message = (
                request.original_message
            )

        try:

            answer = (
                self._component_call(

                    "tutor",

                    self.tutor.answer,

                    message=request.tutor_message,

                    intent=request.intent,

                    subject=request.subject,

                    mode=request.mode,

                    memory_context=request.memory_context,

                    difficulty=request.difficulty,

                    settings=request.settings,

                    strategy=request.strategy,

                    topic=request.topic
                )
            )

        except TypeError:

            # -------------------------------------------------
            # Older TutorEngine compatibility.
            # -------------------------------------------------

            try:

                answer = (
                    self._component_call(

                        "tutor",

                        self.tutor.answer,

                        request.tutor_message,

                        request.intent,

                        request.subject,

                        request.mode,

                        request.memory_context,

                        request.difficulty,

                        request.settings
                    )
                )

            except Exception as error:

                request.mark_degraded(
                    "tutor"
                )

                request.add_error(
                    "tutor",
                    error
                )

                raise

        except Exception as error:

            request.mark_degraded(
                "tutor"
            )

            request.add_error(
                "tutor",
                error
            )

            raise

        if answer is None:

            raise RuntimeError(
                "TutorEngine returned no response."
            )

        answer = str(
            answer
        ).strip()

        if not answer:

            raise RuntimeError(
                "TutorEngine returned an empty response."
            )

        request.answer = answer

    # =========================================================
    # STAGE: VERIFICATION
    # =========================================================

    def _stage_verification(
        self,
        request
    ) -> None:

        try:

            verified = (
                self._component_call(

                    "answer_verifier",

                    self.answer_verifier.verify,

                    request.original_message,

                    request.answer
                )
            )

            if verified is None:

                raise RuntimeError(
                    "Answer verifier returned no answer."
                )

            request.verified_answer = (
                str(
                    verified
                ).strip()
            )

            if not request.verified_answer:

                request.verified_answer = (
                    request.answer
                )

        except Exception as error:

            # -------------------------------------------------
            # Verification should not destroy an otherwise
            # usable answer.
            # -------------------------------------------------

            request.mark_degraded(
                "answer_verifier"
            )

            request.add_warning(
                "Response verification was unavailable; the generated response was retained."
            )

            request.verified_answer = (
                request.answer
            )

            self._log_error(
                "Answer verification failed",
                error
            )

    # =========================================================
    # STAGE: FORMATTING
    # =========================================================

    def _stage_formatting(
        self,
        request
    ) -> None:

        answer = (
            request.verified_answer
            or request.answer
        )

        try:

            formatted = (
                format_response(
                    answer
                )
            )

        except Exception as error:

            request.mark_degraded(
                "response_formatter"
            )

            request.add_warning(
                "Response formatting was unavailable."
            )

            formatted = answer

            self._log_error(
                "Response formatting failed",
                error
            )

        if formatted is None:

            formatted = answer

        formatted = str(
            formatted
        ).strip()

        if not formatted:

            formatted = answer

        request.answer = formatted

    # =========================================================
    # STAGE: UNDERSTANDING
    # =========================================================

    def _stage_understanding(
        self,
        request
    ) -> None:

        try:

            result = (
                self._component_call(

                    "understanding",

                    self.understanding.analyze,

                    request.subject,

                    request.original_message,

                    request.answer
                )
            )

        except Exception as error:

            request.mark_degraded(
                "understanding"
            )

            request.add_warning(
                "Understanding analysis was unavailable."
            )

            result = {

                "attempts":
                    1,

                "confidence":
                    50,

                "mistakes":
                    [],

                "signals":
                    ["unknown"]
            }

            self._log_error(
                "Understanding analysis failed",
                error
            )

        if not isinstance(
            result,
            dict
        ):

            result = {

                "attempts":
                    1,

                "confidence":
                    50,

                "mistakes":
                    [],

                "signals":
                    ["unknown"]
            }

        request.understanding = (
            dict(
                result
            )
        )

    # =========================================================
    # STAGE: CONFIDENCE
    # =========================================================

    def _stage_confidence(
        self,
        request
    ) -> None:

        request.confidence = (
            self._normalize_percent(
                request.understanding.get(
                    "confidence",
                    50
                )
            )
        )

    # =========================================================
    # STAGE: MEMORY UPDATE
    # =========================================================

    def _stage_memory_update(
        self,
        request
    ) -> None:

        if self.demo:

            return

        try:

            normalized_confidence = (
                request.confidence
                / 100.0
            )

            self._component_call(

                "memory",

                self.memory.remember,

                email=request.user_email,

                user_message=request.original_message,

                assistant_message=request.answer,

                subject=request.subject,

                confidence=normalized_confidence,

                conversation_id=request.conversation_id
            )

        except Exception as error:

            request.mark_degraded(
                "memory_write"
            )

            request.add_warning(
                "The response could not be stored in long-term memory."
            )

            self._log_error(
                "Memory storage failed",
                error
            )

    # =========================================================
    # STAGE: PROGRESS
    # =========================================================

    def _stage_progress(
        self,
        request
    ) -> None:

        if not request.subject:

            return

        if self.progress is None:

            request.mark_degraded(
                "progress"
            )

            return

        try:

            self._component_call(

                "progress",

                self.progress.update,

                request.subject,

                request.original_message,

                request.confidence
            )

        except Exception as error:

            request.mark_degraded(
                "progress"
            )

            request.add_warning(
                "Learning progress could not be updated."
            )

            self._log_error(
                "Progress update failed",
                error
            )

    # =========================================================
    # STAGE: LEARNING MEMORY
    # =========================================================

    def _stage_learning_memory(
        self,
        request
    ) -> None:

        if not request.subject:

            return

        confidence = (
            request.confidence
        )

        try:

            self._component_call(

                "learning_memory",

                self.learning_memory.record_attempt,

                request.subject,

                confidence
            )

        except Exception as error:

            request.mark_degraded(
                "learning_memory"
            )

            request.add_warning(
                "Learning attempt history could not be updated."
            )

            self._log_error(
                "Learning memory attempt failed",
                error
            )

        concept = (
            request.topic
            if request.topic
            else request.original_message
        )

        difficulty_level = (
            self._extract_difficulty_level(
                request.difficulty
            )
        )

        try:

            self._component_call(

                "learning_memory",

                self.learning_memory.update_concept,

                subject=request.subject,

                concept=concept,

                confidence=confidence,

                difficulty=difficulty_level
            )

        except TypeError:

            # -------------------------------------------------
            # Legacy compatibility.
            # -------------------------------------------------

            try:

                self._component_call(

                    "learning_memory",

                    self.learning_memory.update_concept,

                    request.subject,

                    concept,

                    confidence
                )

            except Exception as error:

                request.mark_degraded(
                    "learning_memory_concept"
                )

                self._log_error(
                    "Learning memory concept update failed",
                    error
                )

        except Exception as error:

            request.mark_degraded(
                "learning_memory_concept"
            )

            self._log_error(
                "Learning memory concept update failed",
                error
            )

    # =========================================================
    # STAGE: KNOWLEDGE MAP
    # =========================================================

    def _stage_knowledge_map(
        self,
        request
    ) -> None:

        if not request.subject:

            return

        if self.knowledge_map is None:

            return

        concept = (
            request.topic
            if request.topic
            else request.original_message
        )

        try:

            self._component_call(

                "knowledge_map",

                self.knowledge_map.update,

                request.subject,

                concept,

                request.confidence
            )

        except Exception as error:

            request.mark_degraded(
                "knowledge_map"
            )

            request.add_warning(
                "Knowledge map could not be updated."
            )

            self._log_error(
                "Knowledge map update failed",
                error
            )

    # =========================================================
    # STAGE: UNDERSTANDING TRACKING
    # =========================================================

    def _stage_understanding_tracking(
        self,
        request
    ) -> None:

        if not request.subject:

            return

        tracking_level = (
            self._extract_tracking_level(
                request.difficulty,
                request.confidence
            )
        )

        try:

            self._component_call(

                "understanding_tracker",

                self.understanding_tracker.update,

                request.subject,

                tracking_level
            )

        except Exception as error:

            request.mark_degraded(
                "understanding_tracker"
            )

            request.add_warning(
                "Difficulty tracking could not be updated."
            )

            self._log_error(
                "Understanding tracker update failed",
                error
            )

    # =========================================================
    # STAGE: SAVE RESPONSE
    # =========================================================

    def _stage_save_response(
        self,
        request
    ) -> None:

        self._component_call(

            "conversations",

            self.conversations.add_message,

            request.user_email,

            request.conversation_id,

            "nova",

            request.answer
        )

    # =========================================================
    # STAGE: RUNTIME STATE
    # =========================================================

    def _stage_runtime_state(
        self,
        request
    ) -> None:

        self.current_user_email = (
            request.user_email
        )

        self.current_conversation_id = (
            request.conversation_id
        )

        self.current_subject = (
            request.subject
        )

        self.current_topic = (
            request.topic
        )

        self.last_intent = (
            request.intent
        )

        self.last_mode = (
            request.mode
        )

        self.last_strategy = (
            dict(
                request.strategy
            )
        )

        self.last_difficulty = (
            request.difficulty
        )

        self.last_response = (
            request.answer
        )

        self.last_error = None

    # =========================================================
    # RESULT
    # =========================================================

    def _build_result(
        self,
        request
    ) -> Dict[str, Any]:

        return {

            "success":
                True,

            "answer":
                request.answer,

            "conversation_id":
                request.conversation_id,

            "request_id":
                request.request_id,

            "subject":
                request.subject,

            "topic":
                request.topic,

            "intent":
                request.intent,

            "mode":
                request.mode,

            "difficulty":
                request.difficulty,

            "confidence":
                round(
                    request.confidence
                ),

            "understanding":
                request.understanding,

            "teaching_style":
                request.teaching_style,

            "profile_analysis":
                request.profile_analysis,

            "strategy":
                request.strategy,

            "warnings":
                list(
                    request.warnings
                ),

            "degraded_components":
                list(
                    request.degraded_components
                ),

            "metadata": {

                "request_id":
                    request.request_id,

                "nova_version":
                    self.version,

                "processing_time_ms":
                    request.duration_ms(),

                "started_at":
                    request.started_at,

                "demo":
                    self.demo,

                "debug":
                    self.debug,

                "success":
                    True
            },

            "diagnostics": {

                "stage_times":
                    dict(
                        request.stage_times
                    ),

                "stage_status":
                    dict(
                        request.stage_status
                    )
            },

            "nova_version":
                self.version
        }

    # =========================================================
    # ERROR RESULT
    # =========================================================

    def _build_error_result(
        self,
        request
    ) -> Dict[str, Any]:

        return {

            "success":
                False,

            "answer":
                "Nova couldn't process your request right now.",

            "error":
                "processing_error",

            "request_id":
                request.request_id,

            "conversation_id":
                request.conversation_id,

            "subject":
                request.subject,

            "topic":
                request.topic,

            "mode":
                request.mode,

            "warnings":
                list(
                    request.warnings
                ),

            "metadata": {

                "request_id":
                    request.request_id,

                "nova_version":
                    self.version,

                "processing_time_ms":
                    request.duration_ms(),

                "success":
                    False
            },

            "diagnostics": {

                "stage_times":
                    dict(
                        request.stage_times
                    ),

                "stage_status":
                    dict(
                        request.stage_status
                    )
            },

            "nova_version":
                self.version
        }

    # =========================================================
    # ERROR HANDLING
    # =========================================================

    def _handle_process_error(
        self,
        error,
        request
    ) -> None:

        self.last_error = str(
            error
        )

        self._log_error(
            "NovaCore.process() failed",
            error
        )

        request.add_error(
            "process",
            error
        )

    # =========================================================
    # SAFE STUDENT PROFILE
    # =========================================================

    def _safe_student_profile(
        self
    ) -> Dict[str, Any]:

        try:

            profile = (
                self.student.get()
            )

            if isinstance(
                profile,
                dict
            ):

                return dict(
                    profile
                )

        except Exception as error:

            self._log_error(
                "Could not retrieve student profile",
                error
            )

        return {}

    # =========================================================
    # SAFE KNOWLEDGE MAP
    # =========================================================

    def _safe_knowledge_map(
        self
    ) -> Dict[str, Any]:

        if self.knowledge_map is None:

            return {}

        try:

            result = (
                self.knowledge_map.get()
            )

            if isinstance(
                result,
                dict
            ):

                return dict(
                    result
                )

        except Exception as error:

            self._log_error(
                "Could not retrieve knowledge map",
                error
            )

        return {}

    # =========================================================
    # SAFE UNDERSTANDING CONTEXT
    # =========================================================

    def _safe_understanding_context(
        self,
        subject
    ) -> Dict[str, Any]:

        if not subject:

            return {}

        try:

            data = (
                self.understanding.get()
            )

            if not isinstance(
                data,
                dict
            ):

                return {}

            subject_data = data.get(
                subject
            )

            if isinstance(
                subject_data,
                dict
            ):

                return dict(
                    subject_data
                )

        except Exception as error:

            self._log_error(
                "Could not retrieve understanding context",
                error
            )

        return {}

    # =========================================================
    # CONFIDENCE EXTRACTION
    # =========================================================

    def _extract_strategy_confidence(
        self,
        strategy
    ) -> float:

        if not isinstance(
            strategy,
            dict
        ):

            return 50.0

        value = strategy.get(
            "confidence",
            50
        )

        return (
            self._normalize_percent(
                value
            )
        )

    # =========================================================
    # DIFFICULTY LEVEL
    # =========================================================

    def _extract_difficulty_level(
        self,
        difficulty
    ) -> Optional[str]:

        if isinstance(
            difficulty,
            dict
        ):

            value = difficulty.get(
                "level"
            )

            if value is None:

                return None

            return str(
                value
            ).strip().lower()

        if isinstance(
            difficulty,
            str
        ):

            return (
                difficulty
                .strip()
                .lower()
            )

        return None

    # =========================================================
    # TRACKING LEVEL
    # =========================================================

    def _extract_tracking_level(
        self,
        difficulty,
        confidence
    ) -> str:

        if isinstance(
            difficulty,
            dict
        ):

            value = difficulty.get(
                "tracking_level"
            )

            if isinstance(
                value,
                str
            ):

                value = (
                    value
                    .strip()
                    .lower()
                )

                if value in {
                    "easy",
                    "medium",
                    "hard"
                }:

                    return value

        confidence = (
            self._normalize_percent(
                confidence
            )
        )

        if confidence < 40:

            return "easy"

        if confidence < 70:

            return "medium"

        return "hard"

    # =========================================================
    # SETTINGS
    # =========================================================

    def _default_settings(
        self
    ) -> Dict[str, Any]:

        return dict(
            self.DEFAULT_SETTINGS
        )

    # ---------------------------------------------------------

    def _merge_settings(
        self,
        settings
    ) -> Dict[str, Any]:

        result = (
            self._default_settings()
        )

        if isinstance(
            settings,
            dict
        ):

            result.update(
                settings
            )

        return result

    # =========================================================
    # VALIDATION
    # =========================================================

    def _validate_email(
        self,
        user_email
    ) -> str:

        if user_email is None:

            raise ValueError(
                "A user email is required."
            )

        if not isinstance(
            user_email,
            str
        ):

            raise ValueError(
                "User email must be a string."
            )

        user_email = (
            user_email
            .strip()
            .lower()
        )

        if not user_email:

            raise ValueError(
                "A user email is required."
            )

        if len(
            user_email
        ) > self.MAX_EMAIL_LENGTH:

            raise ValueError(
                "User email is too long."
            )

        # -----------------------------------------------------
        # Deliberately lightweight validation.
        # Do not reject legitimate addresses with an absurdly
        # strict regex.
        # -----------------------------------------------------

        if (
            "@"
            not in user_email
        ):

            raise ValueError(
                "Invalid user email."
            )

        return user_email

    # ---------------------------------------------------------

    def _normalize_message(
        self,
        message
    ) -> str:

        if message is None:

            raise ValueError(
                "A message is required."
            )

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

        if not message:

            raise ValueError(
                "A message is required."
            )

        if len(
            message
        ) > self.MAX_MESSAGE_LENGTH:

            raise ValueError(
                "The message is too long."
            )

        return message

    # ---------------------------------------------------------

    def _normalize_optional_text(
        self,
        value
    ) -> Optional[str]:

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

    # ---------------------------------------------------------

    def _normalize_identifier(
        self,
        value,
        maximum_length
    ) -> str:

        value = (
            self._normalize_optional_text(
                value
            )
        )

        if value is None:

            raise ValueError(
                "Identifier cannot be empty."
            )

        if len(
            value
        ) > maximum_length:

            raise ValueError(
                "Identifier is too long."
            )

        return value

    # ---------------------------------------------------------

    def _normalize_mode(
        self,
        mode
    ) -> str:

        mode = (
            self._normalize_optional_text(
                mode
            )
        )

        if not mode:

            return "adaptive"

        return (
            mode
            .lower()
        )

    # =========================================================
    # NUMBER NORMALIZATION
    # =========================================================

    def _normalize_percent(
        self,
        value
    ) -> float:

        try:

            value = float(
                value
            )

        except (
            TypeError,
            ValueError
        ):

            return 50.0

        if 0 <= value <= 1:

            value *= 100

        return max(
            0.0,
            min(
                100.0,
                value
            )
        )

    # =========================================================
    # REQUEST HISTORY
    # =========================================================

    def _record_request_history(
        self,
        request
    ) -> None:

        summary = {

            "request_id":
                request.request_id,

            "started_at":
                request.started_at,

            "user_email":
                request.user_email,

            "conversation_id":
                request.conversation_id,

            "subject":
                request.subject,

            "topic":
                request.topic,

            "intent":
                request.intent,

            "mode":
                request.mode,

            "success":
                request.success,

            "duration_ms":
                request.duration_ms(),

            "warnings":
                len(
                    request.warnings
                ),

            "errors":
                len(
                    request.errors
                ),

            "degraded_components":
                list(
                    request.degraded_components
                )
        }

        self.request_history.append(
            summary
        )

        if len(
            self.request_history
        ) > self.MAX_HISTORY:

            self.request_history = (
                self.request_history[
                    -self.MAX_HISTORY:
                ]
            )

    # =========================================================
    # HEALTH CHECK
    # =========================================================

    def health_check(
        self
    ) -> Dict[str, Any]:

        systems = {

            "memory":
                self.memory is not None,

            "learning_memory":
                self.learning_memory is not None,

            "conversations":
                self.conversations is not None,

            "student":
                self.student is not None,

            "tutor":
                self.tutor is not None,

            "learning_graph":
                self.learning is not None,

            "intent_detector":
                self.intent is not None,

            "subject_detector":
                self.subject is not None,

            "mode_detector":
                self.mode is not None,

            "understanding":
                self.understanding is not None,

            "difficulty":
                self.difficulty is not None,

            "nova_brain":
                self.brain is not None,

            "answer_verifier":
                self.answer_verifier is not None,

            "settings":
                self.settings is not None
        }

        healthy = all(
            systems.values()
        )

        return {

            "healthy":
                healthy,

            "nova_version":
                self.version,

            "demo":
                self.demo,

            "debug":
                self.debug,

            "systems":
                systems,

            "components":
                {
                    name:
                    health.to_dict()
                    for name, health
                    in self.component_health.items()
                },

            "statistics": {

                "total_requests":
                    self.total_requests,

                "successful_requests":
                    self.successful_requests,

                "failed_requests":
                    self.failed_requests,

                "degraded_requests":
                    self.degraded_requests
            }
        }

    # =========================================================
    # DEEP HEALTH CHECK
    # =========================================================

    def deep_health_check(
        self
    ) -> Dict[str, Any]:

        result = (
            self.health_check()
        )

        checks = {}

        # -----------------------------------------------------
        # Student
        # -----------------------------------------------------

        try:

            profile = (
                self.student.get()
            )

            checks[
                "student_profile_read"
            ] = isinstance(
                profile,
                dict
            )

        except Exception as error:

            checks[
                "student_profile_read"
            ] = False

            self._log_error(
                "Deep health student check failed",
                error
            )

        # -----------------------------------------------------
        # Knowledge map
        # -----------------------------------------------------

        if self.knowledge_map is not None:

            try:

                value = (
                    self.knowledge_map.get()
                )

                checks[
                    "knowledge_map_read"
                ] = isinstance(
                    value,
                    dict
                )

            except Exception:

                checks[
                    "knowledge_map_read"
                ] = False

        else:

            checks[
                "knowledge_map_read"
            ] = False

        result[
            "deep_checks"
        ] = checks

        result[
            "deep_healthy"
        ] = all(
            checks.values()
        )

        return result

    # =========================================================
    # RUNTIME STATE
    # =========================================================

    def get_runtime_state(
        self
    ) -> Dict[str, Any]:

        return {

            "nova_version":
                self.version,

            "initialized_at":
                self.initialized_at,

            "demo":
                self.demo,

            "debug":
                self.debug,

            "current_request_id":
                self.last_request_id,

            "current_conversation_id":
                self.current_conversation_id,

            "current_subject":
                self.current_subject,

            "current_topic":
                self.current_topic,

            "last_intent":
                self.last_intent,

            "last_mode":
                self.last_mode,

            "last_difficulty":
                self.last_difficulty,

            "has_last_response":
                self.last_response is not None,

            "has_last_error":
                self.last_error is not None,

            "last_request_duration_ms":
                self.last_request_duration_ms,

            "total_requests":
                self.total_requests,

            "successful_requests":
                self.successful_requests,

            "failed_requests":
                self.failed_requests,

            "degraded_requests":
                self.degraded_requests
        }

    # =========================================================
    # LAST REQUEST
    # =========================================================

    def get_last_request(
        self
    ) -> Optional[Dict[str, Any]]:

        if not self.request_history:

            return None

        return dict(
            self.request_history[-1]
        )

    # =========================================================
    # REQUEST HISTORY
    # =========================================================

    def get_request_history(
        self
    ) -> List[Dict[str, Any]]:

        return [
            dict(
                item
            )
            for item
            in self.request_history
        ]

    # =========================================================
    # STATISTICS
    # =========================================================

    def get_statistics(
        self
    ) -> Dict[str, Any]:

        success_rate = 0.0

        if self.total_requests > 0:

            success_rate = (
                self.successful_requests
                / self.total_requests
            ) * 100

        return {

            "total_requests":
                self.total_requests,

            "successful_requests":
                self.successful_requests,

            "failed_requests":
                self.failed_requests,

            "degraded_requests":
                self.degraded_requests,

            "success_rate":
                round(
                    success_rate,
                    2
                ),

            "last_request_duration_ms":
                self.last_request_duration_ms
        }

    # =========================================================
    # COMPONENT STATUS
    # =========================================================

    def get_component_status(
        self
    ) -> Dict[str, Any]:

        return {

            name:
            health.to_dict()

            for name, health
            in self.component_health.items()
        }

    # =========================================================
    # STUDENT PROFILE
    # =========================================================

    def get_student_profile(
        self
    ) -> Dict[str, Any]:

        return (
            self._safe_student_profile()
        )

    # =========================================================
    # KNOWLEDGE MAP
    # =========================================================

    def get_knowledge_map(
        self
    ) -> Dict[str, Any]:

        return (
            self._safe_knowledge_map()
        )

    # =========================================================
    # LAST RESPONSE
    # =========================================================

    def get_last_response(
        self
    ) -> Optional[str]:

        return self.last_response

    # =========================================================
    # LAST ERROR
    # =========================================================

    def get_last_error(
        self
    ) -> Optional[str]:

        return self.last_error

    # =========================================================
    # RESET RUNTIME
    # =========================================================

    def reset_runtime_state(
        self
    ) -> None:

        self.current_request = None

        self.current_user_email = None

        self.current_conversation_id = None

        self.current_subject = None

        self.current_topic = None

        self.last_intent = None

        self.last_mode = None

        self.last_strategy = None

        self.last_difficulty = None

        self.last_response = None

        self.last_error = None

        self.last_request_id = None

        self.last_request_duration_ms = 0.0

    # =========================================================
    # RESET METRICS
    # =========================================================

    def reset_statistics(
        self
    ) -> None:

        self.total_requests = 0

        self.successful_requests = 0

        self.failed_requests = 0

        self.degraded_requests = 0

        self.last_request_duration_ms = 0.0

        self.request_history = []

        for health in (
            self.component_health.values()
        ):

            health.calls = 0

            health.successes = 0

            health.failures = 0

            health.last_error = None

            health.last_call_at = None

            health.total_duration_ms = 0.0

    # =========================================================
    # HOOK REGISTRATION
    # =========================================================

    def add_before_request_hook(
        self,
        hook: Callable
    ) -> None:

        if not callable(
            hook
        ):

            raise TypeError(
                "Hook must be callable."
            )

        self.before_request_hooks.append(
            hook
        )

    # ---------------------------------------------------------

    def add_after_request_hook(
        self,
        hook: Callable
    ) -> None:

        if not callable(
            hook
        ):

            raise TypeError(
                "Hook must be callable."
            )

        self.after_request_hooks.append(
            hook
        )

    # ---------------------------------------------------------

    def add_stage_hook(
        self,
        hook: Callable
    ) -> None:

        if not callable(
            hook
        ):

            raise TypeError(
                "Hook must be callable."
            )

        self.stage_hooks.append(
            hook
        )

    # =========================================================
    # SIMPLE ASK
    # =========================================================

    def ask(
        self,
        message,
        user_email
    ) -> str:

        result = self.process(

            message=message,

            user_email=user_email
        )

        if not result.get(
            "success",
            False
        ):

            return result.get(
                "answer",
                "Nova couldn't answer."
            )

        return result.get(
            "answer",
            ""
        )

    # =========================================================
    # DEMO PROCESS
    # =========================================================

    def demo_process(
        self,
        message
    ) -> Dict[str, Any]:

        return self.process(

            message=message,

            user_email="demo@nova.local"
        )

    # =========================================================
    # QUICK ANSWER
    # =========================================================

    def quick_answer(
        self,
        message,
        user_email
    ) -> str:

        return self.ask(
            message,
            user_email
        )

    # =========================================================
    # SYSTEM SUMMARY
    # =========================================================

    def system_summary(
        self
    ) -> Dict[str, Any]:

        health = (
            self.health_check()
        )

        return {

            "name":
                "Nova",

            "version":
                self.version,

            "healthy":
                health.get(
                    "healthy",
                    False
                ),

            "demo":
                self.demo,

            "requests":
                self.total_requests,

            "success_rate":
                self.get_statistics().get(
                    "success_rate",
                    0
                ),

            "components":
                len(
                    self.component_health
                )
        }

    # =========================================================
    # DEBUG REPORT
    # =========================================================

    def debug_report(
        self
    ) -> Dict[str, Any]:

        return {

            "runtime":
                self.get_runtime_state(),

            "statistics":
                self.get_statistics(),

            "health":
                self.health_check(),

            "last_request":
                self.get_last_request(),

            "last_error":
                self.last_error
        }

    # =========================================================
    # FRONTEND STATUS
    # =========================================================

    def frontend_status(
        self
    ) -> Dict[str, Any]:
        """
        Small stable payload intended for the future frontend.

        This intentionally avoids exposing internal objects.
        """

        health = (
            self.health_check()
        )

        return {

            "nova": {

                "name":
                    "Nova",

                "version":
                    self.version,

                "online":
                    health.get(
                        "healthy",
                        False
                    )
            },

            "session": {

                "conversation_id":
                    self.current_conversation_id,

                "subject":
                    self.current_subject,

                "topic":
                    self.current_topic,

                "mode":
                    self.last_mode
            },

            "learning": {

                "difficulty":
                    self.last_difficulty,

                "has_strategy":
                    self.last_strategy is not None
            },

            "performance": {

                "last_request_ms":
                    self.last_request_duration_ms,

                "total_requests":
                    self.total_requests
            }
        }

    # =========================================================
    # FUTURE STREAMING HOOK
    # =========================================================

    def prepare_stream_context(
        self,
        message,
        user_email,
        conversation_id=None
    ) -> Dict[str, Any]:
        """
        Prepare metadata for future streaming responses.

        This does not implement token streaming yet.

        It gives the future frontend/API a stable structure
        without changing the current synchronous pipeline.
        """

        normalized_email = (
            self._validate_email(
                user_email
            )
        )

        normalized_message = (
            self._normalize_message(
                message
            )
        )

        return {

            "request_id":
                self._generate_request_id(),

            "user_email":
                normalized_email,

            "conversation_id":
                conversation_id,

            "message_length":
                len(
                    normalized_message
                ),

            "created_at":
                datetime.now().isoformat(),

            "streaming":
                True,

            "implemented":
                False
        }

    # =========================================================
    # FUTURE TOOL HOOK
    # =========================================================

    def tool_context(
        self,
        request_id=None
    ) -> Dict[str, Any]:

        return {

            "request_id":
                request_id
                or self.last_request_id,

            "nova_version":
                self.version,

            "subject":
                self.current_subject,

            "topic":
                self.current_topic,

            "conversation_id":
                self.current_conversation_id,

            "tools_enabled":
                False
        }

    # =========================================================
    # VERSION
    # =========================================================

    def get_version(
        self
    ) -> str:

        return self.version

    # =========================================================
    # INITIALIZATION STATUS
    # =========================================================

    def is_initialized(
        self
    ) -> bool:

        required = [

            self.memory,

            self.learning_memory,

            self.conversations,

            self.student,

            self.tutor,

            self.learning,

            self.intent,

            self.subject,

            self.mode,

            self.understanding,

            self.difficulty,

            self.brain,

            self.answer_verifier,

            self.settings
        ]

        return all(
            component is not None
            for component in required
        )

    # =========================================================
    # REPRESENTATION
    # =========================================================

    def __repr__(
        self
    ) -> str:

        return (

            f"<NovaCore "

            f"version={self.version!r} "

            f"demo={self.demo!r} "

            f"initialized={self.is_initialized()!r} "

            f"request_id={self.last_request_id!r} "

            f"subject={self.current_subject!r} "

            f"mode={self.last_mode!r}>"
        )

    # =========================================================
    # ERROR LOGGING
    # =========================================================

    def _log_error(
        self,
        message,
        error
    ) -> None:

        print(
            "\n"
            "================ NOVA ERROR ================"
        )

        print(
            str(
                message
            )
        )

        print(
            f"Error: {error}"
        )

        if self.debug:

            traceback.print_exc()

        print(
            "=============================================\n"
        )


# ============================================================
# END NOVA CORE
# ============================================================