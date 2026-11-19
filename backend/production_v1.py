"""Production-safe API endpoints used by the deployed Nova frontend."""

from __future__ import annotations
from typing import Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from backend.tools.registry import ToolRegistry, ToolError
from backend.memory_system.conversation_manager import ConversationManager
from backend import api

router = APIRouter(prefix="/v1", tags=["Production V1"])

# ConversationManager now keeps its data in memory and refreshes only when the
# backing file changes. Reusing one instance removes a full JSON file load from
# every conversation request while preserving persistence and external-change
# detection.
_CONVERSATION_MANAGER = ConversationManager(persist=True)

_TOOL_REGISTRY = ToolRegistry()


class ToolExecutionRequest(BaseModel):
    tool_id: str = Field(..., min_length=1, max_length=80)
    arguments: dict[str, Any] = Field(default_factory=dict)


class RenameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)

def _email(request: Request) -> str:
    session = api.get_auth_session(request)
    if not isinstance(session, dict): raise HTTPException(status_code=401, detail="A valid Nova session is required.")
    email = str(session.get("email") or "").strip().lower()
    if not email: raise HTTPException(status_code=401, detail="A valid Nova session is required.")
    return email

def _manager() -> ConversationManager: return _CONVERSATION_MANAGER

def _items(email: str) -> list[dict[str, Any]]:
    data = _manager().list(email)
    if not isinstance(data, dict): return []
    return [{"id": cid, **(conversation if isinstance(conversation, dict) else {})} for cid, conversation in data.items()]

def _real_usage_metrics(email: str, dashboard: dict[str, Any]) -> None:
    conversations = _items(email)
    question_count = 0
    for conversation in conversations:
        messages = conversation.get("messages") if isinstance(conversation.get("messages"), list) else []
        question_count += sum(1 for message in messages if isinstance(message, dict) and str(message.get("role", "")).lower() == "user")
    stats = dashboard.setdefault("stats", {})
    stats["questions"] = question_count
    stats["conversation_count"] = len(conversations)
    difficulty = {"easy": 0, "medium": 0, "hard": 0}
    subjects = dashboard.get("subjects", {})
    if isinstance(subjects, dict):
        for subject in subjects.values():
            if not isinstance(subject, dict): continue
            topics = subject.get("topics", [])
            if not isinstance(topics, list): continue
            for topic in topics:
                if not isinstance(topic, dict): continue
                attempts = max(1, int(topic.get("attempts", 0) or 0))
                mastery = float(topic.get("mastery", 0) or 0)
                if mastery >= 75: difficulty["easy"] += attempts
                elif mastery < 40: difficulty["hard"] += attempts
                else: difficulty["medium"] += attempts
    dashboard["difficulty"] = difficulty
    stats["difficulty_tracked_attempts"] = sum(difficulty.values())

def _items_for_recent(email: str) -> list[dict[str, Any]]:
    recent = []
    for item in _items(email)[:10]:
        messages = item.get("messages") if isinstance(item.get("messages"), list) else []
        last = messages[-1] if messages else {}
        recent.append({"id": item.get("id"), "title": item.get("title") or "New Chat", "last_message": str(last.get("text") or "")[-160:] if isinstance(last, dict) else "", "message_count": len(messages), "updated_at": item.get("updated_at") or item.get("created_at")})
    return recent

@router.get("/conversations")
def list_conversations(request: Request):
    email = _email(request)
    items = _items(email)
    return {"success": True, "conversations": {str(item["id"]): {key: value for key, value in item.items() if key != "id"} for item in items if item.get("id")}}

@router.post("/conversations")
def create_conversation(request: Request):
    email = _email(request)
    conversation_id = _manager().create(email)
    return {"success": True, "id": conversation_id, "conversation_id": conversation_id}

@router.get("/conversations/{conversation_id}")
def get_conversation(request: Request, conversation_id: str):
    conversation = _manager().get(_email(request), conversation_id)
    if conversation is None: raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"success": True, "conversation": conversation}

@router.put("/conversations/{conversation_id}")
def rename_conversation(request: Request, conversation_id: str, payload: RenameRequest):
    if not _manager().rename(_email(request), conversation_id, payload.title.strip()): raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"success": True, "title": payload.title.strip()}

@router.delete("/conversations/{conversation_id}")
def delete_conversation(request: Request, conversation_id: str):
    if not _manager().delete(_email(request), conversation_id): raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"success": True, "deleted": True}

def _legacy_email(request: Request, supplied_email: str) -> str:
    email = _email(request)
    supplied = str(supplied_email or "").strip().lower()
    if supplied and supplied != email: raise HTTPException(status_code=403, detail="The supplied email does not match the active Nova session.")
    return email

@api.app.post("/conversation/new", tags=["Conversations"])
def legacy_create_conversation(request: Request):
    cid = _manager().create(_email(request))
    return {"success": True, "id": cid, "conversation_id": cid}

@api.app.get("/conversations/{email}", tags=["Conversations"])
def legacy_list_conversations(request: Request, email: str):
    return {"success": True, "conversations": _manager().list(_legacy_email(request, email))}

@api.app.get("/conversation/{email}/{conversation_id}", tags=["Conversations"])
def legacy_get_conversation(request: Request, email: str, conversation_id: str):
    authenticated_email = _legacy_email(request, email)
    conversation = _manager().get(authenticated_email, conversation_id)
    if conversation is None: raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"success": True, "conversation": conversation}

@api.app.put("/conversation/{email}/{conversation_id}/rename", tags=["Conversations"])
def legacy_rename_conversation(request: Request, email: str, conversation_id: str, payload: dict[str, Any]):
    authenticated_email = _legacy_email(request, email)
    title = str(payload.get("title") or "").strip()
    if not title or len(title) > 200: raise HTTPException(status_code=400, detail="A valid conversation title is required.")
    if not _manager().rename(authenticated_email, conversation_id, title): raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"success": True, "title": title}

@api.app.delete("/conversation/{email}/{conversation_id}", tags=["Conversations"])
def legacy_delete_conversation(request: Request, email: str, conversation_id: str):
    authenticated_email = _legacy_email(request, email)
    if not _manager().delete(authenticated_email, conversation_id): raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"success": True, "deleted": True}

def _real_usage_metrics_fallback(email: str, conversations: list[dict[str, Any]]) -> int:
    return sum(
        sum(1 for message in (item.get("messages") if isinstance(item.get("messages"), list) else [])
            if isinstance(message, dict) and message.get("role") == "user")
        for item in conversations
    )

@router.get("/dashboard")
def dashboard(request: Request):
    email = _email(request)
    try:
        from backend.dashboard import _build_dashboard
        result = _build_dashboard(email)
        if isinstance(result, dict):
            result["success"] = True
            _real_usage_metrics(email, result)
            return result
    except Exception as error:
        print(f"[V1 DASHBOARD] primary dashboard builder failed: {type(error).__name__}: {error}", flush=True)
    conversations = _items(email)[:50]
    question_count = _real_usage_metrics_fallback(email, conversations)
    return {"success": True, "student": {"email": email}, "stats": {"questions": question_count, "total_subjects": 0, "total_topics": 0, "study_attempts": 0, "correct_answers": 0, "wrong_answers": 0, "total_answers": 0, "overall_mastery": 0, "average_confidence": 0, "memory_count": 0, "conversation_count": len(conversations), "understanding_attempts": 0, "accuracy": 0}, "subjects": {}, "knowledge_map": {}, "knowledge_subjects": [], "progress": {}, "understanding": {}, "difficulty": {"easy": 0, "medium": 0, "hard": 0}, "strengths": [], "weaknesses": [], "session": {"subject": "None", "topic": "None", "mode": "None", "score": 0}, "learning_graph": {"subjects": {}}, "recent_conversations": _items_for_recent(email)}


@router.get("/tools")
def list_tools(request: Request):
    _email(request)
    return {"success": True, "version": _TOOL_REGISTRY.VERSION, "tools": _TOOL_REGISTRY.list_tools()}


@router.post("/tools/execute")
def execute_tool(request: Request, payload: ToolExecutionRequest):
    _email(request)
    try:
        result = _TOOL_REGISTRY.execute(payload.tool_id, payload.arguments)
    except ToolError as error:
        raise HTTPException(status_code=422, detail=str(error))
    return {"success": True, **result}


@router.get("/integrations")
def list_integrations(request: Request):
    _email(request)
    integrations = [
        {
            "id": "google_calendar",
            "name": "Google Calendar",
            "category": "productivity",
            "status": "not_configured",
            "description": "Read calendar availability and create events after explicit confirmation.",
            "permissions": ["calendar.read", "calendar.events.create"],
            "requires_oauth": True,
            "write_actions_require_confirmation": True,
        },
        {
            "id": "gmail",
            "name": "Gmail",
            "category": "communication",
            "status": "not_configured",
            "description": "Search and summarize email only after the account owner connects Google.",
            "permissions": ["gmail.read"],
            "requires_oauth": True,
            "write_actions_require_confirmation": True,
        },
        {
            "id": "notion",
            "name": "Notion",
            "category": "workspace",
            "status": "not_configured",
            "description": "Search and organize pages in a connected Notion workspace.",
            "permissions": ["pages.read", "pages.write"],
            "requires_oauth": True,
            "write_actions_require_confirmation": True,
        },
        {
            "id": "github",
            "name": "GitHub",
            "category": "development",
            "status": "not_configured",
            "description": "Review repositories and propose code changes in a connected GitHub account.",
            "permissions": ["repositories.read", "pull_requests.write"],
            "requires_oauth": True,
            "write_actions_require_confirmation": True,
        },
    ]
    return {
        "success": True,
        "integrations": integrations,
        "security": {
            "connected_accounts_are_user_scoped": True,
            "write_actions_require_confirmation": True,
            "secrets_are_never_returned_by_this_endpoint": True,
        },
    }
