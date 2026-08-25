"""Production-safe API endpoints used by the deployed Nova frontend.

These endpoints deliberately avoid the legacy conversation/dashboard routes.
The legacy routes instantiate NovaCore just to perform CRUD operations, which
makes a simple history request depend on the entire LLM runtime. V1 CRUD is
kept independent from NovaCore so authentication, chat history, and the
Dashboard remain usable while the model runtime is warming or degraded.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.memory_system.conversation_manager import ConversationManager


router = APIRouter(prefix="/v1", tags=["Production V1"])


class RenameRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


def _email(request: Request) -> str:
    from backend import api

    session = api.get_auth_session(request)
    if not isinstance(session, dict):
        raise HTTPException(status_code=401, detail="A valid Nova session is required.")

    email = str(session.get("email") or "").strip().lower()
    if not email:
        raise HTTPException(status_code=401, detail="A valid Nova session is required.")
    return email


def _manager() -> ConversationManager:
    # A fresh manager reloads the JSON file so it sees messages written by
    # NovaCore's own ConversationManager instance during /chat requests.
    return ConversationManager(persist=True)


def _items(email: str) -> list[dict[str, Any]]:
    data = _manager().list(email)
    if not isinstance(data, dict):
        return []
    return [
        {"id": cid, **(conversation if isinstance(conversation, dict) else {})}
        for cid, conversation in data.items()
    ]


@router.get("/conversations")
def list_conversations(request: Request):
    email = _email(request)
    items = _items(email)
    conversations = {
        str(item["id"]): {key: value for key, value in item.items() if key != "id"}
        for item in items
        if item.get("id")
    }
    return {"success": True, "conversations": conversations}


@router.post("/conversations")
def create_conversation(request: Request):
    email = _email(request)
    conversation_id = _manager().create(email)
    return {
        "success": True,
        "id": conversation_id,
        "conversation_id": conversation_id,
    }


@router.get("/conversations/{conversation_id}")
def get_conversation(request: Request, conversation_id: str):
    email = _email(request)
    conversation = _manager().get(email, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"success": True, "conversation": conversation}


@router.put("/conversations/{conversation_id}")
def rename_conversation(request: Request, conversation_id: str, payload: RenameRequest):
    email = _email(request)
    title = payload.title.strip()
    success = _manager().rename(email, conversation_id, title)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"success": True, "title": title}


@router.delete("/conversations/{conversation_id}")
def delete_conversation(request: Request, conversation_id: str):
    email = _email(request)
    success = _manager().delete(email, conversation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"success": True, "deleted": True}


@router.get("/dashboard")
def dashboard(request: Request):
    email = _email(request)

    try:
        from backend.dashboard import _build_dashboard
        result = _build_dashboard(email)
        if isinstance(result, dict):
            result["success"] = True
            return result
    except Exception as error:
        print(f"[V1 DASHBOARD] primary dashboard builder failed: {type(error).__name__}: {error}", flush=True)

    # The Dashboard is a read-only view. If one optional learning subsystem
    # is unavailable, still return a usable dashboard instead of a 500.
    conversations = _items(email)[:50]
    recent = []
    for item in conversations[:10]:
        messages = item.get("messages") if isinstance(item.get("messages"), list) else []
        last = messages[-1] if messages else {}
        recent.append({
            "id": item.get("id"),
            "title": item.get("title") or "New Chat",
            "last_message": str(last.get("text") or "")[-160:] if isinstance(last, dict) else "",
            "message_count": len(messages),
            "updated_at": item.get("updated_at") or item.get("created_at"),
        })

    return {
        "success": True,
        "student": {"email": email},
        "stats": {
            "questions": 0,
            "total_subjects": 0,
            "total_topics": 0,
            "study_attempts": 0,
            "correct_answers": 0,
            "wrong_answers": 0,
            "total_answers": 0,
            "overall_mastery": 0,
            "average_confidence": 0,
            "memory_count": 0,
            "conversation_count": len(conversations),
            "understanding_attempts": 0,
        },
        "subjects": {},
        "knowledge_map": {},
        "knowledge_subjects": [],
        "progress": {},
        "understanding": {},
        "difficulty": {"easy": 0, "medium": 0, "hard": 0},
        "strengths": [],
        "weaknesses": [],
        "session": {"subject": "None", "topic": "None", "mode": "None", "score": 0},
        "learning_graph": {"subjects": {}},
        "recent_conversations": recent,
    }
