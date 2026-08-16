from __future__ import annotations

# ============================================================
# NOVA AI - API SERVER
# ============================================================

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
import asyncio
import time
import uuid
import traceback

from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    Query,
)

from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import (
    StreamingResponse,
    JSONResponse,
)

from fastapi.exceptions import RequestValidationError

from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
)

from backend.core.nova_core import NovaCore

from backend.auth import (
    register_user,
    login_user,
)

from backend.settings import SettingsManager


# ============================================================
# APPLICATION METADATA
# ============================================================

APP_NAME = "Nova AI"
APP_VERSION = "1.0.0"

APP_DESCRIPTION = """
Nova AI educational assistant API.
"""


# ============================================================
# RUNTIME
# ============================================================

SERVER_STARTED_AT = time.time()

SERVER_STARTED_DATETIME = datetime.now(
    timezone.utc
).isoformat()


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ============================================================
# CORS
# ============================================================

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",

    "http://localhost:5173",
    "http://127.0.0.1:5173",

    "http://localhost:5174",
    "http://127.0.0.1:5174",
]


app.add_middleware(
    CORSMiddleware,

    allow_origins=ALLOWED_ORIGINS,

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# NOVA CORE
# ============================================================
#
# IMPORTANT:
#
# NovaCore is intentionally NOT created during module import.
#
# If NovaCore crashes during initialization, FastAPI itself
# must still be able to start so that /health, /status and
# /frontend/ping can tell us what is actually broken.
#
# ============================================================

nova: Optional[NovaCore] = None

nova_init_error: Optional[str] = None


def get_nova() -> NovaCore:
    """
    Lazily initialize NovaCore.

    This prevents a NovaCore initialization error from killing
    the entire FastAPI application during import.
    """

    global nova
    global nova_init_error

    if nova is not None:
        return nova

    try:

        print()
        print("==============================================")
        print("Initializing NovaCore...")
        print("==============================================")

        nova = NovaCore()

        nova_init_error = None

        print("NovaCore initialized successfully.")
        print("==============================================")
        print()

        return nova

    except Exception as error:

        nova = None

        nova_init_error = (
            f"{type(error).__name__}: {error}"
        )

        print()
        print("========== NOVACORE INITIALIZATION ERROR ==========")
        print(nova_init_error)
        print(traceback.format_exc())
        print("====================================================")
        print()

        raise RuntimeError(
            "NovaCore could not be initialized."
        ) from error


# ============================================================
# SETTINGS
# ============================================================

settings_manager = SettingsManager()


# ============================================================
# DEMO SESSIONS
# ============================================================

demo_sessions: Dict[
    str,
    Dict[str, Any]
] = {}

DEMO_SESSION_TIMEOUT = 60 * 60


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatRequest(BaseModel):

    model_config = ConfigDict(
        extra="ignore"
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=12000
    )

    email: str = Field(
        ...,
        min_length=3,
        max_length=320
    )

    conversation_id: Optional[str] = None

    tutor_mode: Optional[str] = None


class DemoChatRequest(BaseModel):

    model_config = ConfigDict(
        extra="ignore"
    )

    message: str = Field(
        ...,
        min_length=1,
        max_length=12000
    )

    session_id: str = Field(
        ...,
        min_length=1,
        max_length=200
    )

    tutor_mode: Optional[str] = None


class UserRequest(BaseModel):

    model_config = ConfigDict(
        extra="ignore"
    )

    email: str = Field(
        ...,
        min_length=3,
        max_length=320
    )

    password: str = Field(
        ...,
        min_length=1,
        max_length=1000
    )


class SettingsRequest(BaseModel):

    model_config = ConfigDict(
        extra="ignore"
    )

    name: str = ""

    language: str = "English"

    level: str = "High School"

    teaching_style: str = "adaptive"

    difficulty: str = "adaptive"

    hints: str = "when_needed"

    step_by_step: bool = True

    adaptive_learning: bool = True

    response_length: str = "balanced"

    tone: str = "friendly"

    use_examples: bool = True

    use_analogies: bool = True

    encouragement: bool = True

    correction_style: str = "explain"

    show_correct_answer: bool = True

    creativity: str = "medium"

    behavior: str = ""

    custom_instructions: str = ""


class ConversationRequest(BaseModel):

    model_config = ConfigDict(
        extra="ignore"
    )

    email: str = Field(
        ...,
        min_length=3,
        max_length=320
    )


class ConversationMessageRequest(BaseModel):

    model_config = ConfigDict(
        extra="ignore"
    )

    email: str = Field(
        ...,
        min_length=3,
        max_length=320
    )

    role: str = Field(
        ...,
        min_length=1,
        max_length=50
    )

    text: str = Field(
        ...,
        min_length=1,
        max_length=12000
    )


class RenameConversationRequest(BaseModel):

    model_config = ConfigDict(
        extra="ignore"
    )

    email: str = Field(
        ...,
        min_length=3,
        max_length=320
    )

    title: str = Field(
        ...,
        min_length=1,
        max_length=200
    )


# ============================================================
# RESPONSE HELPERS
# ============================================================

def utc_now() -> str:

    return datetime.now(
        timezone.utc
    ).isoformat()


def success_response(
    data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:

    response = {
        "success": True,
        "timestamp": utc_now()
    }

    if data:
        response.update(data)

    return response


def error_response(
    message: str,
    code: str = "ERROR",
    status_code: int = 400
) -> JSONResponse:

    return JSONResponse(

        status_code=status_code,

        content={
            "success": False,

            "error": {
                "code": code,
                "message": message,
            },

            "timestamp": utc_now(),
        }
    )


def safe_dict(
    value: Any
) -> Dict[str, Any]:

    if isinstance(value, dict):
        return value

    return {}


def safe_list(
    value: Any
) -> List[Any]:

    if isinstance(value, list):
        return value

    return []


def safe_number(
    value: Any,
    default: float = 0
) -> float:

    if isinstance(value, bool):
        return default

    if isinstance(value, (int, float)):
        return value

    try:
        return float(value)

    except (
        TypeError,
        ValueError
    ):
        return default


def clean_text(
    value: Any,
    default: str = ""
) -> str:

    if value is None:
        return default

    try:
        value = str(value).strip()

    except Exception:
        return default

    return value if value else default


# ============================================================
# DEMO SESSION MANAGEMENT
# ============================================================

def cleanup_demo_sessions() -> None:

    now = time.time()

    expired = []

    for session_id, data in list(
        demo_sessions.items()
    ):

        if not isinstance(data, dict):

            expired.append(session_id)

            continue

        created_at = data.get(
            "created_at",
            now
        )

        last_used = data.get(
            "last_used",
            created_at
        )

        reference_time = max(
            created_at,
            last_used
        )

        if (
            now - reference_time
            > DEMO_SESSION_TIMEOUT
        ):

            expired.append(session_id)

    for session_id in expired:

        demo_sessions.pop(
            session_id,
            None
        )


def create_demo_instance(
    session_id: str
) -> NovaCore:

    try:

        instance = NovaCore(
            demo=True
        )

    except TypeError:

        # Compatibility with NovaCore versions that do not yet
        # accept the demo keyword.

        instance = NovaCore()

    demo_sessions[
        session_id
    ] = {

        "nova": instance,

        "created_at":
            time.time(),

        "last_used":
            time.time()
    }

    return instance


def get_demo_instance(
    session_id: str
) -> NovaCore:

    cleanup_demo_sessions()

    session_id = clean_text(
        session_id
    )

    if not session_id:

        raise HTTPException(
            status_code=400,
            detail="Invalid demo session."
        )

    data = demo_sessions.get(
        session_id
    )

    if not isinstance(data, dict):

        return create_demo_instance(
            session_id
        )

    instance = data.get(
        "nova"
    )

    if not isinstance(
        instance,
        NovaCore
    ):

        return create_demo_instance(
            session_id
        )

    data[
        "last_used"
    ] = time.time()

    return instance


def delete_demo_session(
    session_id: str
) -> bool:

    if session_id in demo_sessions:

        del demo_sessions[
            session_id
        ]

        return True

    return False


# ============================================================
# ERROR HANDLING
# ============================================================

@app.exception_handler(
    RequestValidationError
)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):

    return error_response(

        message="Invalid request data.",

        code="VALIDATION_ERROR",

        status_code=422
    )


@app.exception_handler(
    Exception
)
async def global_exception_handler(
    request: Request,
    exc: Exception
):

    print()
    print("========== API ERROR ==========")

    print(
        f"Path: {request.url.path}"
    )

    print(
        f"Error: {exc}"
    )

    print(
        traceback.format_exc()
    )

    print(
        "==============================="
    )
    print()

    return error_response(

        message="Nova encountered an internal error.",

        code="INTERNAL_ERROR",

        status_code=500
    )


# ============================================================
# MIDDLEWARE
# ============================================================

@app.middleware(
    "http"
)
async def request_timing_middleware(
    request: Request,
    call_next
):

    start = time.perf_counter()

    response = await call_next(
        request
    )

    duration = (
        time.perf_counter()
        - start
    )

    response.headers[
        "X-Nova-Response-Time"
    ] = f"{duration:.4f}"

    response.headers[
        "X-Nova-Version"
    ] = APP_VERSION

    return response


# ============================================================
# ROOT
# ============================================================

@app.get(
    "/",
    tags=["System"]
)
def root():

    return {
        "name": APP_NAME,
        "status": "online",
        "version": APP_VERSION,
        "api": "/docs",
        "timestamp": utc_now()
    }


# ============================================================
# API INFORMATION
# ============================================================

@app.get(
    "/api",
    tags=["System"]
)
def api_info():

    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "online",

        "features": [
            "chat",
            "streaming_chat",
            "demo_mode",
            "authentication",
            "settings",
            "conversations",
            "dashboard",
            "health",
            "statistics",
        ],

        "timestamp": utc_now()
    }


# ============================================================
# HEALTH
# ============================================================

@app.get(
    "/health",
    tags=["System"]
)
def health():

    uptime = (
        time.time()
        - SERVER_STARTED_AT
    )

    return {
        "status": "healthy",
        "service": APP_NAME,
        "version": APP_VERSION,

        "nova_core": (
            "ready"
            if nova is not None
            else "not_initialized"
        ),

        "uptime_seconds": round(
            uptime,
            2
        ),

        "timestamp": utc_now()
    }


# ============================================================
# READINESS
# ============================================================

@app.get(
    "/ready",
    tags=["System"]
)
def readiness():

    if nova is not None:

        return {
            "ready": True,
            "status": "ready",
            "timestamp": utc_now()
        }

    return JSONResponse(

        status_code=503,

        content={
            "ready": False,

            "status": "not_ready",

            "error": nova_init_error,

            "timestamp": utc_now(),
        }
    )


# ============================================================
# RUNTIME STATUS
# ============================================================

@app.get(
    "/status",
    tags=["System"]
)
def status():

    return {

        "status": "online",

        "version": APP_VERSION,

        "server_started_at":
            SERVER_STARTED_DATETIME,

        "uptime_seconds":
            round(
                time.time()
                - SERVER_STARTED_AT,
                2
            ),

        "nova_core": {

            "initialized":
                nova is not None,

            "error":
                nova_init_error,
        },

        "demo_sessions":
            len(demo_sessions),

        "timestamp":
            utc_now()
    }


# ============================================================
# NORMAL CHAT
# ============================================================

@app.post(
    "/chat",
    tags=["Chat"]
)
def chat(
    request: ChatRequest
):

    message = clean_text(
        request.message
    )

    if not message:

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    try:

        core = get_nova()

    except Exception as error:

        print(
            f"[CHAT CORE INIT ERROR] {error}"
        )

        return error_response(

            message=(
                "NovaCore could not be initialized. "
                f"{nova_init_error or str(error)}"
            ),

            code="NOVACORE_UNAVAILABLE",

            status_code=503
        )

    try:

        result = core.process(

            message,

            request.conversation_id,

            user_email=request.email,

            forced_mode=request.tutor_mode
        )

    except Exception as error:

        print()
        print("========== CHAT ERROR ==========")
        print(error)
        print(traceback.format_exc())
        print("================================")
        print()

        return error_response(

            message=(
                "NovaCore failed while processing "
                "the message."
            ),

            code="CHAT_PROCESSING_ERROR",

            status_code=500
        )

    result = safe_dict(
        result
    )

    answer = clean_text(

        result.get(
            "answer"
        ),

        "Nova could not generate an answer."
    )

    conversation_id = clean_text(

        result.get(
            "conversation_id"
        ),

        request.conversation_id or ""
    )

    return {

        "success": True,

        "response": answer,

        "answer": answer,

        "conversation_id":
            conversation_id,

        "timestamp":
            utc_now()
    }


# ============================================================
# STREAMING CHAT
# ============================================================

async def stream_text(
    text: str,
    chunk_size: int = 40,
    delay: float = 0.015
):

    text = clean_text(
        text
    )

    if not text:
        return

    chunk_size = max(
        1,
        int(chunk_size)
    )

    delay = max(
        0,
        float(delay)
    )

    for index in range(
        0,
        len(text),
        chunk_size
    ):

        chunk = text[
            index:
            index + chunk_size
        ]

        yield chunk

        if delay:

            await asyncio.sleep(
                delay
            )


@app.post(
    "/chat/stream",
    tags=["Chat"]
)
async def chat_stream(
    request: ChatRequest
):

    message = clean_text(
        request.message
    )

    if not message:

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    try:

        core = get_nova()

    except Exception as error:

        print(
            f"[STREAM CORE INIT ERROR] {error}"
        )

        return error_response(

            message=(
                "NovaCore could not be initialized. "
                f"{nova_init_error or str(error)}"
            ),

            code="NOVACORE_UNAVAILABLE",

            status_code=503
        )

    try:

        result = core.process(

            message,

            request.conversation_id,

            user_email=request.email,

            forced_mode=request.tutor_mode
        )

    except Exception as error:

        print()
        print("======= STREAM CHAT ERROR =======")
        print(error)
        print(traceback.format_exc())
        print("=================================")
        print()

        return error_response(

            message=(
                "NovaCore failed while processing "
                "the message."
            ),

            code="CHAT_PROCESSING_ERROR",

            status_code=500
        )

    result = safe_dict(
        result
    )

    answer = clean_text(
        result.get(
            "answer"
        )
    )

    conversation_id = clean_text(

        result.get(
            "conversation_id"
        ),

        request.conversation_id or ""
    )

    async def generate():

        async for chunk in stream_text(
            answer
        ):

            yield chunk

    return StreamingResponse(

        generate(),

        media_type="text/plain",

        headers={

            "Cache-Control":
                "no-cache",

            "X-Accel-Buffering":
                "no-cache",

            "X-Conversation-ID":
                conversation_id,

            "X-Nova-Version":
                APP_VERSION
        }
    )


# ============================================================
# DEMO SESSION CREATION
# ============================================================

@app.post(
    "/demo/session",
    tags=["Demo"]
)
def create_demo_session():

    cleanup_demo_sessions()

    session_id = str(
        uuid.uuid4()
    )

    try:

        create_demo_instance(
            session_id
        )

    except Exception as error:

        demo_sessions.pop(
            session_id,
            None
        )

        print(
            f"[DEMO INIT ERROR] {error}"
        )

        return error_response(

            message=(
                "Nova demo could not be initialized."
            ),

            code="DEMO_UNAVAILABLE",

            status_code=503
        )

    return {

        "success": True,

        "session_id":
            session_id,

        "expires_in":
            DEMO_SESSION_TIMEOUT,

        "timestamp":
            utc_now()
    }


# ============================================================
# DEMO SESSION STATUS
# ============================================================

@app.get(
    "/demo/session/{session_id}",
    tags=["Demo"]
)
def demo_session_status(
    session_id: str
):

    cleanup_demo_sessions()

    exists = (
        session_id
        in demo_sessions
    )

    if not exists:

        return {

            "success": False,

            "active": False,

            "session_id":
                session_id
        }

    data = demo_sessions[
        session_id
    ]

    created_at = data.get(
        "created_at",
        time.time()
    )

    last_used = data.get(
        "last_used",
        created_at
    )

    return {

        "success": True,

        "active": True,

        "session_id":
            session_id,

        "age_seconds":
            round(
                time.time()
                - created_at,
                2
            ),

        "idle_seconds":
            round(
                time.time()
                - last_used,
                2
            )
    }


# ============================================================
# DELETE DEMO SESSION
# ============================================================

@app.delete(
    "/demo/session/{session_id}",
    tags=["Demo"]
)
def remove_demo_session(
    session_id: str
):

    deleted = delete_demo_session(
        session_id
    )

    return {

        "success":
            deleted,

        "session_id":
            session_id
    }


# ============================================================
# DEMO CHAT
# ============================================================

@app.post(
    "/demo/chat/stream",
    tags=["Demo"]
)
async def demo_chat_stream(
    request: DemoChatRequest
):

    message = clean_text(
        request.message
    )

    if not message:

        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    try:

        demo_nova = get_demo_instance(
            request.session_id
        )

    except Exception as error:

        print(
            f"[DEMO CORE ERROR] {error}"
        )

        return error_response(

            message=(
                "Nova demo could not be initialized."
            ),

            code="DEMO_UNAVAILABLE",

            status_code=503
        )

    try:

        result = demo_nova.process(

            message,

            user_email=(
                f"demo-{request.session_id}"
            ),

            forced_mode=
                request.tutor_mode
        )

    except Exception as error:

        print()
        print("========= DEMO CHAT ERROR =========")
        print(error)
        print(traceback.format_exc())
        print("====================================")
        print()

        return error_response(

            message=(
                "Nova demo could not process "
                "the message."
            ),

            code="DEMO_CHAT_ERROR",

            status_code=500
        )

    result = safe_dict(
        result
    )

    answer = clean_text(
        result.get(
            "answer"
        )
    )

    conversation_id = clean_text(
        result.get(
            "conversation_id"
        )
    )

    async def generate():

        async for chunk in stream_text(
            answer
        ):

            yield chunk

    return StreamingResponse(

        generate(),

        media_type="text/plain",

        headers={

            "Cache-Control":
                "no-cache",

            "X-Accel-Buffering":
                "no-cache",

            "X-Conversation-ID":
                conversation_id
        }
    )


# ============================================================
# AUTHENTICATION
# ============================================================

@app.post(
    "/register",
    tags=["Authentication"]
)
def register(
    request: UserRequest
):

    email = clean_text(
        request.email
    )

    password = request.password

    if not email:

        raise HTTPException(
            status_code=400,
            detail="Email is required."
        )

    if not password:

        raise HTTPException(
            status_code=400,
            detail="Password is required."
        )

    try:

        success = register_user(
            email,
            password
        )

    except Exception as error:

        print(
            f"[REGISTER ERROR] {error}"
        )

        raise HTTPException(

            status_code=500,

            detail="Registration failed."
        )

    return {
        "success": bool(success)
    }


@app.post(
    "/login",
    tags=["Authentication"]
)
def login(
    request: UserRequest
):

    email = clean_text(
        request.email
    )

    password = request.password

    try:

        success = login_user(
            email,
            password
        )

    except Exception as error:

        print(
            f"[LOGIN ERROR] {error}"
        )

        raise HTTPException(

            status_code=500,

            detail="Login failed."
        )

    return {

        "success":
            bool(success),

        "email":
            email
            if success
            else None
    }


# ============================================================
# CORE HELPER
# ============================================================

def get_safe_core_data(
    attribute: str,
    method: Optional[str] = None,
    default: Any = None
):

    try:

        core = get_nova()

    except Exception as error:

        print(
            f"[CORE DATA] Nova unavailable: {error}"
        )

        return default

    try:

        component = getattr(
            core,
            attribute,
            None
        )

        if component is None:
            return default

        if method:

            function = getattr(
                component,
                method,
                None
            )

            if not callable(function):
                return default

            return function()

        if callable(component):
            return component()

        return component

    except Exception as error:

        print(
            f"[CORE DATA] "
            f"{attribute}: "
            f"{error}"
        )

        return default


# ============================================================
# DASHBOARD HELPERS
# ============================================================

def calculate_subject_statistics(
    learning_graph: Dict[str, Any]
) -> Dict[str, Any]:

    subjects = {}

    graph_subjects = safe_dict(
        learning_graph.get(
            "subjects",
            {}
        )
    )

    for subject, data in graph_subjects.items():

        if not isinstance(data, dict):
            continue

        topics = safe_dict(
            data.get(
                "topics",
                {}
            )
        )

        total_correct = 0
        total_wrong = 0
        total_studied = 0

        topic_list = []

        for topic, topic_data in topics.items():

            if not isinstance(
                topic_data,
                dict
            ):
                continue

            correct = safe_number(
                topic_data.get(
                    "correct_answers",
                    0
                )
            )

            wrong = safe_number(
                topic_data.get(
                    "wrong_answers",
                    0
                )
            )

            studied = safe_number(
                topic_data.get(
                    "times_studied",
                    0
                )
            )

            mastery = safe_number(
                topic_data.get(
                    "mastery",
                    0
                )
            )

            total_correct += correct
            total_wrong += wrong
            total_studied += studied

            topic_list.append({

                "name":
                    topic,

                "mastery":
                    mastery,

                "attempts":
                    studied,

                "correct":
                    correct,

                "wrong":
                    wrong,

                "last_review":
                    clean_text(
                        topic_data.get(
                            "last_review"
                        )
                    )
            })

        total_answers = (
            total_correct
            + total_wrong
        )

        if total_answers:

            calculated_mastery = round(

                (
                    total_correct
                    / total_answers
                ) * 100,

                1
            )

        else:

            calculated_mastery = safe_number(
                data.get(
                    "mastery",
                    0
                )
            )

        subjects[
            subject
        ] = {

            "mastery":
                calculated_mastery,

            "topics":
                topic_list,

            "topics_count":
                len(topic_list),

            "times_studied":
                total_studied,

            "correct_answers":
                total_correct,

            "wrong_answers":
                total_wrong,

            "total_answers":
                total_answers
        }

    return subjects


def calculate_knowledge_subjects(
    knowledge_data: Dict[str, Any]
) -> List[Dict[str, Any]]:

    result = []

    for subject, topics in knowledge_data.items():

        if not isinstance(
            topics,
            dict
        ):
            continue

        confidence_total = 0
        confidence_count = 0
        attempts_total = 0

        for topic_data in topics.values():

            if not isinstance(
                topic_data,
                dict
            ):
                continue

            confidence = topic_data.get(
                "confidence",
                0
            )

            attempts = topic_data.get(
                "attempts",
                0
            )

            if isinstance(
                confidence,
                (int, float)
            ):

                confidence_total += confidence
                confidence_count += 1

            if isinstance(
                attempts,
                (int, float)
            ):

                attempts_total += attempts

        average_confidence = (

            round(

                confidence_total
                / confidence_count,

                1
            )

            if confidence_count
            else 0
        )

        result.append({

            "name":
                subject,

            "topics":
                len(topics),

            "confidence":
                average_confidence,

            "attempts":
                attempts_total
        })

    result.sort(

        key=lambda item:
            item.get(
                "confidence",
                0
            ),

        reverse=True
    )

    return result


def calculate_difficulty_totals(
    difficulty_data: Dict[str, Any]
) -> Dict[str, float]:

    totals = {

        "easy": 0,
        "medium": 0,
        "hard": 0
    }

    for data in difficulty_data.values():

        if not isinstance(
            data,
            dict
        ):
            continue

        for difficulty in totals:

            totals[
                difficulty
            ] += safe_number(

                data.get(
                    difficulty,
                    0
                )
            )

    return totals


def calculate_memory_count(
    memory_data: Any
) -> int:

    if isinstance(
        memory_data,
        dict
    ):

        return len(memory_data)

    if isinstance(
        memory_data,
        list
    ):

        return len(memory_data)

    return 0


# ============================================================
# DASHBOARD
# ============================================================

@app.get(
    "/dashboard",
    tags=["Dashboard"]
)
def dashboard(
    email: Optional[str] = Query(
        default=None
    )
):

    student_data = safe_dict(
        get_safe_core_data(
            "student",
            "get",
            {}
        )
    )

    knowledge_data = safe_dict(
        get_safe_core_data(
            "knowledge_map",
            "get",
            {}
        )
    )

    progress_data = safe_dict(
        get_safe_core_data(
            "progress",
            "get",
            {}
        )
    )

    understanding_data = safe_dict(
        get_safe_core_data(
            "understanding",
            "get",
            {}
        )
    )

    difficulty_data = safe_dict(
        get_safe_core_data(
            "understanding_tracker",
            "get",
            {}
        )
    )

    learning_graph = safe_dict(
        get_safe_core_data(
            "learning",
            "get",
            {
                "subjects": {}
            }
        )
    )

    session_data = safe_dict(
        get_safe_core_data(
            "session",
            "get",
            {}
        )
    )

    memory_data = get_safe_core_data(
        "memory",
        "recall",
        []
    )

    memory_count = calculate_memory_count(
        memory_data
    )

    conversations = []

    if email:

        try:

            core = get_nova()

            conversation_data = (
                core.conversations.list(
                    email
                )
            )

        except Exception as error:

            print(
                f"[DASHBOARD CONVERSATIONS] "
                f"{error}"
            )

            conversation_data = []

        if isinstance(
            conversation_data,
            dict
        ):

            conversations = [

                {
                    "id": key,

                    **(
                        value
                        if isinstance(
                            value,
                            dict
                        )
                        else {}
                    )
                }

                for key, value
                in conversation_data.items()
            ]

        elif isinstance(
            conversation_data,
            list
        ):

            conversations = conversation_data

    subjects = calculate_subject_statistics(
        learning_graph
    )

    knowledge_subjects = (
        calculate_knowledge_subjects(
            knowledge_data
        )
    )

    difficulty_totals = (
        calculate_difficulty_totals(
            difficulty_data
        )
    )

    total_subjects = len(subjects)

    total_topics = 0
    total_study_attempts = 0
    total_correct = 0
    total_wrong = 0

    for data in subjects.values():

        total_topics += int(
            safe_number(
                data.get(
                    "topics_count",
                    0
                )
            )
        )

        total_study_attempts += safe_number(
            data.get(
                "times_studied",
                0
            )
        )

        total_correct += safe_number(
            data.get(
                "correct_answers",
                0
            )
        )

        total_wrong += safe_number(
            data.get(
                "wrong_answers",
                0
            )
        )

    total_answers = (
        total_correct
        + total_wrong
    )

    overall_mastery = (

        round(

            (
                total_correct
                / total_answers
            ) * 100,

            1
        )

        if total_answers
        else 0
    )

    strengths = safe_list(
        student_data.get(
            "strengths",
            []
        )
    )

    weaknesses = safe_list(
        student_data.get(
            "weaknesses",
            []
        )
    )

    confidence_values = []

    total_understanding_attempts = 0

    for data in understanding_data.values():

        if not isinstance(
            data,
            dict
        ):
            continue

        confidence = data.get(
            "confidence"
        )

        attempts = data.get(
            "attempts"
        )

        if isinstance(
            confidence,
            (int, float)
        ):

            confidence_values.append(
                confidence
            )

        if isinstance(
            attempts,
            (int, float)
        ):

            total_understanding_attempts += attempts

    average_confidence = (

        round(

            sum(confidence_values)
            / len(confidence_values),

            1
        )

        if confidence_values
        else 0
    )

    recent_conversations = []

    for conversation in conversations[:10]:

        if not isinstance(
            conversation,
            dict
        ):
            continue

        messages = safe_list(
            conversation.get(
                "messages",
                []
            )
        )

        last_message = ""

        if messages:

            last = messages[-1]

            if isinstance(
                last,
                dict
            ):

                last_message = clean_text(
                    last.get(
                        "text",
                        ""
                    )
                )

        recent_conversations.append({

            "id":
                clean_text(
                    conversation.get(
                        "id"
                    )
                ),

            "title":
                clean_text(
                    conversation.get(
                        "title"
                    ),
                    "New Chat"
                ),

            "last_message":
                last_message,

            "message_count":
                len(messages)
        })

    return {

        "success":
            True,

        "student":
            student_data,

        "stats": {

            "questions":
                safe_number(
                    student_data.get(
                        "questions",
                        0
                    )
                ),

            "total_subjects":
                total_subjects,

            "total_topics":
                total_topics,

            "study_attempts":
                total_study_attempts,

            "correct_answers":
                total_correct,

            "wrong_answers":
                total_wrong,

            "total_answers":
                total_answers,

            "overall_mastery":
                overall_mastery,

            "average_confidence":
                average_confidence,

            "memory_count":
                memory_count,

            "conversation_count":
                len(conversations),

            "understanding_attempts":
                total_understanding_attempts
        },

        "subjects":
            subjects,

        "knowledge_map":
            knowledge_data,

        "knowledge_subjects":
            knowledge_subjects,

        "progress":
            progress_data,

        "understanding":
            understanding_data,

        "difficulty":
            difficulty_totals,

        "strengths":
            strengths,

        "weaknesses":
            weaknesses,

        "session":
            session_data,

        "learning_graph":
            learning_graph,

        "recent_conversations":
            recent_conversations,

        "timestamp":
            utc_now()
    }


# ============================================================
# STATISTICS
# ============================================================

@app.get(
    "/statistics",
    tags=["Dashboard"]
)
def statistics():

    try:

        data = dashboard()

        return {

            "success":
                True,

            "stats":
                data.get(
                    "stats",
                    {}
                ),

            "timestamp":
                utc_now()
        }

    except Exception as error:

        print(
            f"[STATISTICS ERROR] {error}"
        )

        raise HTTPException(

            status_code=500,

            detail="Statistics unavailable."
        )


# ============================================================
# SETTINGS
# ============================================================

@app.get(
    "/settings",
    tags=["Settings"]
)
def get_settings():

    try:

        result = settings_manager.get()

    except Exception as error:

        print(
            f"[SETTINGS GET ERROR] {error}"
        )

        raise HTTPException(

            status_code=500,

            detail="Could not load settings."
        )

    if not isinstance(
        result,
        dict
    ):

        result = {}

    return {

        "success":
            True,

        "settings":
            result,

        "timestamp":
            utc_now()
    }


@app.post(
    "/settings",
    tags=["Settings"]
)
def update_settings(
    request: SettingsRequest
):

    try:

        result = settings_manager.update(

            name=request.name,

            language=request.language,

            level=request.level,

            teaching_style=
                request.teaching_style,

            difficulty=
                request.difficulty,

            hints=
                request.hints,

            step_by_step=
                request.step_by_step,

            adaptive_learning=
                request.adaptive_learning,

            response_length=
                request.response_length,

            tone=
                request.tone,

            use_examples=
                request.use_examples,

            use_analogies=
                request.use_analogies,

            encouragement=
                request.encouragement,

            correction_style=
                request.correction_style,

            show_correct_answer=
                request.show_correct_answer,

            creativity=
                request.creativity,

            behavior=
                request.behavior,

            custom_instructions=
                request.custom_instructions
        )

    except Exception as error:

        print(
            f"[SETTINGS UPDATE ERROR] {error}"
        )

        raise HTTPException(

            status_code=500,

            detail="Could not update settings."
        )

    return {

        "success":
            True,

        "settings":
            result
            if isinstance(
                result,
                dict
            )
            else {},

        "timestamp":
            utc_now()
    }


# ============================================================
# SETTINGS RESET
# ============================================================

@app.post(
    "/settings/reset",
    tags=["Settings"]
)
def reset_settings():

    reset_function = getattr(
        settings_manager,
        "reset",
        None
    )

    if not callable(
        reset_function
    ):

        return error_response(

            "Settings reset is not available yet.",

            code="RESET_NOT_SUPPORTED",

            status_code=501
        )

    try:

        result = reset_function()

    except Exception as error:

        print(
            f"[SETTINGS RESET ERROR] {error}"
        )

        raise HTTPException(

            status_code=500,

            detail="Could not reset settings."
        )

    return {

        "success":
            True,

        "settings":
            result
            if isinstance(
                result,
                dict
            )
            else {},

        "timestamp":
            utc_now()
    }


# ============================================================
# LEGACY MEMORY
# ============================================================

@app.get(
    "/history",
    tags=["Memory"]
)
def history():

    try:

        core = get_nova()

        result = core.memory.recall()

    except Exception as error:

        print(
            f"[HISTORY ERROR] {error}"
        )

        raise HTTPException(

            status_code=500,

            detail="Memory history unavailable."
        )

    return {

        "success":
            True,

        "history":
            result,

        "timestamp":
            utc_now()
    }


# ============================================================
# CONVERSATIONS
# ============================================================

@app.get(
    "/conversations/{email}",
    tags=["Conversations"]
)
def conversations(
    email: str
):

    email = clean_text(
        email
    )

    if not email:

        raise HTTPException(

            status_code=400,

            detail="Email is required."
        )

    try:

        core = get_nova()

        result = core.conversations.list(
            email
        )

    except Exception as error:

        print(
            f"[CONVERSATION LIST ERROR] {error}"
        )

        raise HTTPException(

            status_code=500,

            detail="Could not load conversations."
        )

    return {

        "success":
            True,

        "conversations":
            result,

        "timestamp":
            utc_now()
    }


@app.post(
    "/conversation/new",
    tags=["Conversations"]
)
def new_chat(
    request: ConversationRequest
):

    try:

        core = get_nova()

        conversation_id = (
            core.conversations.create(
                request.email
            )
        )

    except Exception as error:

        print(
            f"[CONVERSATION CREATE ERROR] {error}"
        )

        raise HTTPException(

            status_code=500,

            detail="Could not create conversation."
        )

    return {

        "success":
            True,

        "id":
            conversation_id,

        "conversation_id":
            conversation_id,

        "timestamp":
            utc_now()
    }


@app.get(
    "/conversation/{email}/{cid}",
    tags=["Conversations"]
)
def conversation(
    email: str,
    cid: str
):

    try:

        core = get_nova()

        result = core.conversations.get(
            email,
            cid
        )

    except Exception as error:

        print(
            f"[CONVERSATION GET ERROR] {error}"
        )

        raise HTTPException(

            status_code=500,

            detail="Could not load conversation."
        )

    if result is None:

        raise HTTPException(

            status_code=404,

            detail="Conversation not found."
        )

    return {

        "success":
            True,

        "conversation":
            result,

        "timestamp":
            utc_now()
    }


@app.post(
    "/conversation/{email}/{cid}/message",
    tags=["Conversations"]
)
def add_conversation_message(
    email: str,
    cid: str,
    request: ConversationMessageRequest
):

    role = clean_text(
        request.role
    )

    text = clean_text(
        request.text
    )

    if not role:

        raise HTTPException(

            status_code=400,

            detail="Message role is required."
        )

    if not text:

        raise HTTPException(

            status_code=400,

            detail="Message text is required."
        )

    try:

        core = get_nova()

        success = (
            core.conversations.add_message(

                email,
                cid,
                role,
                text
            )
        )

    except Exception as error:

        print(
            f"[MESSAGE ADD ERROR] {error}"
        )

        raise HTTPException(

            status_code=500,

            detail="Could not add conversation message."
        )

    return {

        "success":
            bool(success),

        "timestamp":
            utc_now()
    }


@app.put(
    "/conversation/{email}/{cid}/rename",
    tags=["Conversations"]
)
def rename_conversation(
    email: str,
    cid: str,
    request: RenameConversationRequest
):

    title = clean_text(
        request.title
    )

    if not title:

        raise HTTPException(

            status_code=400,

            detail="Conversation title is required."
        )

    try:

        core = get_nova()

        success = (
            core.conversations.rename(

                email,
                cid,
                title
            )
        )

    except Exception as error:

        print(
            f"[CONVERSATION RENAME ERROR] {error}"
        )

        raise HTTPException(

            status_code=500,

            detail="Could not rename conversation."
        )

    return {

        "success":
            bool(success),

        "title":
            title,

        "timestamp":
            utc_now()
    }


@app.delete(
    "/conversation/{email}/{cid}",
    tags=["Conversations"]
)
def delete_chat(
    email: str,
    cid: str
):

    try:

        core = get_nova()

        success = (
            core.conversations.delete(

                email,
                cid
            )
        )

    except Exception as error:

        print(
            f"[CONVERSATION DELETE ERROR] {error}"
        )

        raise HTTPException(

            status_code=500,

            detail="Could not delete conversation."
        )

    return {

        "success":
            bool(success),

        "timestamp":
            utc_now()
    }


# ============================================================
# CONVERSATION SEARCH
# ============================================================

@app.get(
    "/conversations/{email}/search",
    tags=["Conversations"]
)
def search_conversations(
    email: str,
    q: str = Query(
        default="",
        max_length=200
    )
):

    query = clean_text(
        q
    ).lower()

    try:

        core = get_nova()

        conversation_data = (
            core.conversations.list(
                email
            )
        )

    except Exception as error:

        print(
            f"[CONVERSATION SEARCH ERROR] {error}"
        )

        raise HTTPException(

            status_code=500,

            detail="Could not search conversations."
        )

    if isinstance(
        conversation_data,
        dict
    ):

        conversation_list = [

            {

                "id":
                    key,

                **(
                    value
                    if isinstance(
                        value,
                        dict
                    )
                    else {}
                )
            }

            for key, value
            in conversation_data.items()
        ]

    elif isinstance(
        conversation_data,
        list
    ):

        conversation_list = (
            conversation_data
        )

    else:

        conversation_list = []

    if not query:

        matches = conversation_list

    else:

        matches = []

        for conversation_data in conversation_list:

            if not isinstance(
                conversation_data,
                dict
            ):
                continue

            title = clean_text(
                conversation_data.get(
                    "title"
                )
            ).lower()

            messages = safe_list(
                conversation_data.get(
                    "messages",
                    []
                )
            )

            searchable = title

            for message in messages:

                if isinstance(
                    message,
                    dict
                ):

                    searchable += (
                        " "
                        + clean_text(
                            message.get(
                                "text"
                            )
                        )
                    )

            if query in searchable.lower():

                matches.append(
                    conversation_data
                )

    return {

        "success":
            True,

        "query":
            q,

        "results":
            matches,

        "count":
            len(matches),

        "timestamp":
            utc_now()
    }


# ============================================================
# FRONTEND CONFIGURATION
# ============================================================

@app.get(
    "/frontend/config",
    tags=["Frontend"]
)
def frontend_config():

    return {

        "success":
            True,

        "app": {

            "name":
                APP_NAME,

            "version":
                APP_VERSION
        },

        "features": {

            "chat":
                True,

            "streaming":
                True,

            "demo":
                True,

            "authentication":
                True,

            "dashboard":
                True,

            "settings":
                True,

            "conversations":
                True,

            "search":
                True
        },

        "limits": {

            "max_message_length":
                12000,

            "max_conversation_title":
                200
        },

        "timestamp":
            utc_now()
    }


# ============================================================
# FRONTEND PING
# ============================================================

@app.get(
    "/frontend/ping",
    tags=["Frontend"]
)
def frontend_ping():

    return {

        "success":
            True,

        "message":
            "Nova API is reachable.",

        "timestamp":
            utc_now()
    }


# ============================================================
# STARTUP
# ============================================================

@app.on_event(
    "startup"
)
async def startup_event():

    cleanup_demo_sessions()

    print()
    print(
        "=================================================="
    )
    print(
        "              NOVA AI API STARTED"
    )
    print(
        "=================================================="
    )
    print(
        f"Version: {APP_VERSION}"
    )
    print(
        "Docs:    /docs"
    )
    print(
        "Health:  /health"
    )
    print(
        "Status:  /status"
    )
    print(
        "=================================================="
    )
    print()

    # Do NOT initialize NovaCore here.
    #
    # It will initialize on the first request that actually
    # needs the AI core.


# ============================================================
# SHUTDOWN
# ============================================================

@app.on_event(
    "shutdown"
)
async def shutdown_event():

    demo_sessions.clear()

    print()
    print(
        "Nova API shutting down."
    )
    print()