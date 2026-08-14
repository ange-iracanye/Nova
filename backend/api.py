from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import asyncio
import uuid

from backend.core.nova_core import NovaCore
from backend.auth import register_user, login_user
from backend.settings import SettingsManager


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="Nova AI",
    version="1.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# NOVA
# ============================================================

nova = NovaCore()

settings_manager = SettingsManager()


# ============================================================
# DEMO SESSIONS
# ============================================================

demo_sessions = {}


# ============================================================
# REQUEST MODELS
# ============================================================

class ChatRequest(BaseModel):

    message: str

    email: str

    conversation_id: str | None = None

    tutor_mode: str | None = None


class DemoChatRequest(BaseModel):

    message: str

    session_id: str

    tutor_mode: str | None = None


class UserRequest(BaseModel):

    email: str

    password: str


class SettingsRequest(BaseModel):

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

    email: str


class ConversationMessageRequest(BaseModel):

    email: str

    role: str

    text: str


class RenameConversationRequest(BaseModel):

    email: str

    title: str


# ============================================================
# NORMAL CHAT
# ============================================================

@app.post("/chat")
def chat(request: ChatRequest):

    result = nova.process(
        request.message,
        request.conversation_id,
        user_email=request.email,
        forced_mode=request.tutor_mode
    )

    return {
        "response": result["answer"],
        "conversation_id": result["conversation_id"]
    }


# ============================================================
# STREAMING CHAT
# ============================================================

@app.post("/chat/stream")
async def chat_stream(
    request: ChatRequest
):

    result = nova.process(
        request.message,
        request.conversation_id,
        user_email=request.email,
        forced_mode=request.tutor_mode
    )

    answer = result["answer"]

    conversation_id = result["conversation_id"]

    async def generate():

        chunk_size = 40

        for i in range(
            0,
            len(answer),
            chunk_size
        ):

            yield answer[
                i:i + chunk_size
            ]

            await asyncio.sleep(0.02)

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
# DEMO SESSION
# ============================================================

@app.post("/demo/session")
def create_demo_session():

    session_id = str(
        uuid.uuid4()
    )

    demo_sessions[
        session_id
    ] = NovaCore(
        demo=True
    )

    return {
        "session_id":
            session_id
    }


# ============================================================
# DEMO CHAT
# ============================================================

@app.post("/demo/chat/stream")
async def demo_chat_stream(
    request: DemoChatRequest
):

    if request.session_id not in demo_sessions:

        demo_sessions[
            request.session_id
        ] = NovaCore(
            demo=True
        )

    demo_nova = demo_sessions[
        request.session_id
    ]

    result = demo_nova.process(

        request.message,

        user_email=
            f"demo-{request.session_id}",

        forced_mode=
            request.tutor_mode
    )

    answer = result["answer"]

    async def generate():

        chunk_size = 40

        for i in range(
            0,
            len(answer),
            chunk_size
        ):

            yield answer[
                i:i + chunk_size
            ]

            await asyncio.sleep(0.02)

    return StreamingResponse(

        generate(),

        media_type="text/plain",

        headers={

            "Cache-Control":
                "no-cache",

            "X-Accel-Buffering":
                "no-cache"
        }
    )


# ============================================================
# AUTHENTICATION
# ============================================================

@app.post("/register")
def register(
    request: UserRequest
):

    success = register_user(
        request.email,
        request.password
    )

    return {
        "success":
            success
    }


@app.post("/login")
def login(
    request: UserRequest
):

    success = login_user(
        request.email,
        request.password
    )

    return {
        "success":
            success
    }


# ============================================================
# DASHBOARD
# ============================================================

@app.get("/dashboard")
def dashboard(
    email: str | None = None
):

    # --------------------------------------------------------
    # STUDENT
    # --------------------------------------------------------

    student_data = nova.student.get()

    if not isinstance(
        student_data,
        dict
    ):
        student_data = {}


    # --------------------------------------------------------
    # KNOWLEDGE MAP
    # --------------------------------------------------------

    knowledge_data = (
        nova.knowledge_map.get()
    )

    if not isinstance(
        knowledge_data,
        dict
    ):
        knowledge_data = {}


    # --------------------------------------------------------
    # PROGRESS TRACKER
    # --------------------------------------------------------

    try:

        progress_data = (
            nova.progress.get()
        )

    except Exception:

        progress_data = {}

    if not isinstance(
        progress_data,
        dict
    ):
        progress_data = {}


    # --------------------------------------------------------
    # UNDERSTANDING
    # --------------------------------------------------------

    try:

        understanding_data = (
            nova.understanding.get()
        )

    except Exception:

        understanding_data = {}

    if not isinstance(
        understanding_data,
        dict
    ):
        understanding_data = {}


    # --------------------------------------------------------
    # DIFFICULTY / UNDERSTANDING TRACKER
    # --------------------------------------------------------

    try:

        difficulty_data = (
            nova.understanding_tracker.get()
        )

    except Exception:

        difficulty_data = {}

    if not isinstance(
        difficulty_data,
        dict
    ):
        difficulty_data = {}


    # --------------------------------------------------------
    # LEARNING GRAPH
    # --------------------------------------------------------

    try:

        learning_graph = (
            nova.learning.get()
        )

    except Exception:

        learning_graph = {
            "subjects": {}
        }

    if not isinstance(
        learning_graph,
        dict
    ):
        learning_graph = {
            "subjects": {}
        }


    # --------------------------------------------------------
    # CURRENT SESSION
    # --------------------------------------------------------

    try:

        session_data = (
            nova.session.get()
        )

    except Exception:

        session_data = {}

    if not isinstance(
        session_data,
        dict
    ):
        session_data = {}


    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

    try:

        memory_data = (
            nova.memory.recall()
        )

        if isinstance(
            memory_data,
            dict
        ):

            memory_count = len(
                memory_data
            )

        elif isinstance(
            memory_data,
            list
        ):

            memory_count = len(
                memory_data
            )

        else:

            memory_count = 0

    except Exception:

        memory_count = 0


    # --------------------------------------------------------
    # CONVERSATIONS
    # --------------------------------------------------------

    conversation_count = 0

    conversations = []

    if email:

        try:

            conversation_data = (
                nova.conversations.list(
                    email
                )
            )

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

                conversations = (
                    conversation_data
                )

            conversation_count = len(
                conversations
            )

        except Exception:

            conversations = []


    # --------------------------------------------------------
    # SUBJECT STATISTICS
    # --------------------------------------------------------

    subjects = {}

    graph_subjects = (
        learning_graph.get(
            "subjects",
            {}
        )
    )

    if isinstance(
        graph_subjects,
        dict
    ):

        for subject, data in graph_subjects.items():

            if not isinstance(
                data,
                dict
            ):
                continue

            topics = data.get(
                "topics",
                {}
            )

            if not isinstance(
                topics,
                dict
            ):
                topics = {}

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

                correct = topic_data.get(
                    "correct_answers",
                    0
                )

                wrong = topic_data.get(
                    "wrong_answers",
                    0
                )

                times_studied = topic_data.get(
                    "times_studied",
                    0
                )

                mastery = topic_data.get(
                    "mastery",
                    0
                )

                total_correct += (
                    correct
                    if isinstance(
                        correct,
                        (int, float)
                    )
                    else 0
                )

                total_wrong += (
                    wrong
                    if isinstance(
                        wrong,
                        (int, float)
                    )
                    else 0
                )

                total_studied += (
                    times_studied
                    if isinstance(
                        times_studied,
                        (int, float)
                    )
                    else 0
                )

                topic_list.append({

                    "name":
                        topic,

                    "mastery":
                        mastery,

                    "attempts":
                        times_studied,

                    "correct":
                        correct,

                    "wrong":
                        wrong,

                    "last_review":
                        topic_data.get(
                            "last_review",
                            ""
                        )
                })

            total_answers = (
                total_correct
                + total_wrong
            )

            if total_answers > 0:

                calculated_mastery = round(

                    (
                        total_correct
                        / total_answers
                    ) * 100,

                    1
                )

            else:

                calculated_mastery = (
                    data.get(
                        "mastery",
                        0
                    )
                )

            subjects[subject] = {

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


    # --------------------------------------------------------
    # KNOWLEDGE MAP SUBJECTS
    # --------------------------------------------------------

    knowledge_subjects = []

    for subject, topics in knowledge_data.items():

        if not isinstance(
            topics,
            dict
        ):
            continue

        topic_count = len(
            topics
        )

        confidence_total = 0
        confidence_count = 0
        attempts_total = 0

        for topic, data in topics.items():

            if not isinstance(
                data,
                dict
            ):
                continue

            confidence = data.get(
                "confidence",
                0
            )

            attempts = data.get(
                "attempts",
                0
            )

            if isinstance(
                confidence,
                (int, float)
            ):

                confidence_total += (
                    confidence
                )

                confidence_count += 1

            if isinstance(
                attempts,
                (int, float)
            ):

                attempts_total += (
                    attempts
                )

        average_confidence = (

            round(
                confidence_total
                / confidence_count,
                1
            )

            if confidence_count
            else 0
        )

        knowledge_subjects.append({

            "name":
                subject,

            "topics":
                topic_count,

            "confidence":
                average_confidence,

            "attempts":
                attempts_total
        })


    # --------------------------------------------------------
    # TOTALS
    # --------------------------------------------------------

    total_subjects = len(
        subjects
    )

    total_topics = 0

    total_study_attempts = 0

    total_correct = 0

    total_wrong = 0

    for subject_data in subjects.values():

        total_topics += (
            subject_data.get(
                "topics_count",
                0
            )
        )

        total_study_attempts += (
            subject_data.get(
                "times_studied",
                0
            )
        )

        total_correct += (
            subject_data.get(
                "correct_answers",
                0
            )
        )

        total_wrong += (
            subject_data.get(
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

        if total_answers > 0

        else 0
    )


    # --------------------------------------------------------
    # STRENGTHS / WEAKNESSES
    # --------------------------------------------------------

    strengths = student_data.get(
        "strengths",
        []
    )

    weaknesses = student_data.get(
        "weaknesses",
        []
    )

    if not isinstance(
        strengths,
        list
    ):
        strengths = []

    if not isinstance(
        weaknesses,
        list
    ):
        weaknesses = []


    # --------------------------------------------------------
    # CURRENT UNDERSTANDING
    # --------------------------------------------------------

    confidence_values = []

    total_understanding_attempts = 0

    for subject, data in understanding_data.items():

        if not isinstance(
            data,
            dict
        ):
            continue

        confidence = data.get(
            "confidence",
            0
        )

        attempts = data.get(
            "attempts",
            0
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

            total_understanding_attempts += (
                attempts
            )

    average_confidence = (

        round(

            sum(confidence_values)
            / len(confidence_values),

            1
        )

        if confidence_values

        else 0
    )


    # --------------------------------------------------------
    # DIFFICULTY TOTALS
    # --------------------------------------------------------

    difficulty_totals = {

        "easy": 0,

        "medium": 0,

        "hard": 0
    }

    for subject, data in difficulty_data.items():

        if not isinstance(
            data,
            dict
        ):
            continue

        for difficulty in difficulty_totals:

            value = data.get(
                difficulty,
                0
            )

            if isinstance(
                value,
                (int, float)
            ):

                difficulty_totals[
                    difficulty
                ] += value


    # --------------------------------------------------------
    # RECENT CONVERSATIONS
    # --------------------------------------------------------

    recent_conversations = []

    for conversation in conversations[:5]:

        if not isinstance(
            conversation,
            dict
        ):
            continue

        messages = conversation.get(
            "messages",
            []
        )

        last_message = ""

        if isinstance(
            messages,
            list
        ) and messages:

            last = messages[-1]

            if isinstance(
                last,
                dict
            ):

                last_message = last.get(
                    "text",
                    ""
                )

        recent_conversations.append({

            "id":
                conversation.get(
                    "id",
                    ""
                ),

            "title":
                conversation.get(
                    "title",
                    "New Chat"
                ),

            "last_message":
                last_message,

            "message_count":
                len(messages)
                if isinstance(
                    messages,
                    list
                )
                else 0
        })


    # --------------------------------------------------------
    # RETURN DASHBOARD
    # --------------------------------------------------------

    return {

        "student":
            student_data,

        "stats": {

            "questions":
                student_data.get(
                    "questions",
                    0
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

            "overall_mastery":
                overall_mastery,

            "average_confidence":
                average_confidence,

            "memory_count":
                memory_count,

            "conversation_count":
                conversation_count,

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
            recent_conversations
    }


# ============================================================
# SETTINGS
# ============================================================

@app.get("/settings")
def get_settings():

    return settings_manager.get()


@app.post("/settings")
def update_settings(
    request: SettingsRequest
):

    return settings_manager.update(

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


# ============================================================
# LEGACY MEMORY HISTORY
# ============================================================

@app.get("/history")
def history():

    return nova.memory.recall()


# ============================================================
# CONVERSATIONS
# ============================================================

@app.get("/conversations/{email}")
def conversations(
    email: str
):

    return nova.conversations.list(
        email
    )


@app.post("/conversation/new")
def new_chat(
    request: ConversationRequest
):

    cid = nova.conversations.create(
        request.email
    )

    return {
        "id":
            cid
    }


@app.get(
    "/conversation/{email}/{cid}"
)
def conversation(
    email: str,
    cid: str
):

    result = nova.conversations.get(
        email,
        cid
    )

    if result is None:

        return {
            "error":
                "Conversation not found"
        }

    return result


@app.post(
    "/conversation/{email}/{cid}/message"
)
def add_conversation_message(
    email: str,
    cid: str,
    request: ConversationMessageRequest
):

    success = (
        nova.conversations.add_message(
            email,
            cid,
            request.role,
            request.text
        )
    )

    return {
        "success":
            success
    }


@app.put(
    "/conversation/{email}/{cid}/rename"
)
def rename_conversation(
    email: str,
    cid: str,
    request: RenameConversationRequest
):

    success = (
        nova.conversations.rename(
            email,
            cid,
            request.title
        )
    )

    return {
        "success":
            success
    }


@app.delete(
    "/conversation/{email}/{cid}"
)
def delete_chat(
    email: str,
    cid: str
):

    success = (
        nova.conversations.delete(
            email,
            cid
        )
    )

    return {
        "success":
            success
    }


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():

    return {

        "name":
            "Nova AI",

        "status":
            "online",

        "version":
            "1.0"
    }
