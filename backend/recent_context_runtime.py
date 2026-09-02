"""Relevance-aware conversation context for Nova V1.

Keeps Nova aware of the user's current and previous conversations while
also injecting the authenticated user's saved settings/profile into the
prompt context. This module is installed by the existing production hook.
"""

from __future__ import annotations

import re
import threading
from typing import Any, Iterable, List


_INSTALL_LOCK = threading.Lock()
_INSTALLED = False
_ORIGINAL_STAGE_MEMORY = None

_STOPWORDS = {
    "the", "and", "that", "this", "with", "from", "what", "when", "where",
    "which", "have", "your", "you", "are", "was", "were", "for", "about",
    "how", "why", "can", "could", "would", "should", "does", "did", "not",
    "into", "just", "than", "then", "also", "help", "please", "nova",
}

_REFERENCE_PHRASES = (
    "remember", "last time", "previous", "earlier", "before", "we talked",
    "we discussed", "as we discussed", "you said", "you told me", "continue",
    "where we left off", "pick up", "resume", "again", "same topic", "that thing",
    "what did we", "what were we", "my last", "our last",
)

_CASUAL_INTENTS = {"greeting", "hello", "hi", "thanks", "farewell", "casual_conversation"}


def _tokens(value: Any) -> set[str]:
    words = re.findall(r"[a-z0-9]{3,}", str(value or "").casefold())
    return {word for word in words if word not in _STOPWORDS}


def _message_text(item: Any) -> str:
    if not isinstance(item, dict):
        return ""
    return str(item.get("text") or "").strip()


def _compact_messages(messages: Iterable[Any], limit: int = 6, chars: int = 4200) -> str:
    selected: List[str] = []
    for message in list(messages)[-limit:]:
        if not isinstance(message, dict):
            continue
        text = _message_text(message)
        if not text:
            continue
        role = "Student" if message.get("role") == "user" else "Nova"
        selected.append(f"{role}: {text[:1100]}")
    return "\n".join(selected)[:chars]


def _profile_context(email: str) -> str:
    """Return only useful, non-sensitive user settings for personalization."""
    try:
        from backend.user_settings import set_current_user, reset_current_user, current_manager
        token = set_current_user(email)
        try:
            settings = current_manager().get()
        finally:
            reset_current_user(token)
    except Exception:
        return ""

    if not isinstance(settings, dict):
        return ""

    name = str(settings.get("name") or "").strip()
    language = str(settings.get("language") or "English").strip()
    level = str(settings.get("level") or "High School").strip()
    teaching_style = str(settings.get("teaching_style") or "adaptive").strip()
    difficulty = str(settings.get("difficulty") or "adaptive").strip()
    hints = str(settings.get("hints") or "when_needed").strip()
    response_length = str(settings.get("response_length") or "balanced").strip()
    tone = str(settings.get("tone") or "friendly").strip()
    behavior = str(settings.get("behavior") or "").strip()[:1800]
    custom = str(settings.get("custom_instructions") or "").strip()[:2200]

    lines = [
        "[STUDENT PROFILE AND SETTINGS]",
        "These are authenticated user preferences, not instructions from an outside source.",
        f"Student name: {name or 'not provided'}",
        f"Preferred language: {language}",
        f"Academic level: {level}",
        f"Teaching style: {teaching_style}",
        f"Difficulty: {difficulty}",
        f"Hints: {hints}",
        f"Response length: {response_length}",
        f"Tone: {tone}",
        f"Use examples: {bool(settings.get('use_examples', True))}",
        f"Use analogies: {bool(settings.get('use_analogies', True))}",
        f"Step by step: {bool(settings.get('step_by_step', True))}",
        f"Adaptive learning: {bool(settings.get('adaptive_learning', True))}",
        f"Encouragement: {bool(settings.get('encouragement', True))}",
        f"Correction style: {str(settings.get('correction_style') or 'explain')}",
    ]
    if behavior:
        lines.append(f"Student's saved behavior preference: {behavior}")
    if custom:
        lines.append(f"Student's saved custom instructions: {custom}")
    lines.extend([
        "Use these settings consistently. If a setting conflicts with the student's current explicit request, follow the current request.",
    ])
    return "\n".join(lines)


def _nova_identity_context() -> str:
    return (
        "[NOVA IDENTITY]\n"
        "You are Nova, the adaptive educational AI tutor created as the Nova learning product. "
        "Nova exists to make personalized learning clearer, more adaptive, and more useful for students. "
        "Nova can explain concepts, teach step by step, practice with students, adapt difficulty and teaching style, "
        "use examples and analogies, remember relevant learning context, track learning progress, and personalize replies. "
        "Nova is the product and tutor experience, not the name of the underlying language model. "
        "Nova is not Nvidia and is not an Nvidia program. A model/provider name such as an Nvidia-hosted model may appear "
        "in technical configuration, but that does not change Nova's identity. "
        "If asked who you are, what you can do, or why you exist, answer as Nova using these product facts. "
        "If asked for an exact creator, company ownership, or exact creation/launch date and the application has not supplied "
        "that fact, say that the exact fact is not available rather than inventing one."
    )


def build_recent_context(manager: Any, email: str, current_id: str | None, query: str, intent: str | None = None) -> str:
    """Build a broad but bounded memory block from the user's own chats."""
    normalized_intent = str(intent or "").strip().casefold()
    profile = _profile_context(email)
    identity = _nova_identity_context()

    if normalized_intent in _CASUAL_INTENTS:
        lowered = str(query or "").casefold()
        if any(term in lowered for term in ("who are you", "what are you", "your name", "what can you do", "when were you created", "why were you created")):
            return identity + ("\n\n" + profile if profile else "")
        return ""

    conversations = manager.list(email)
    if not isinstance(conversations, dict) or not conversations:
        return "\n\n".join(part for part in (identity, profile) if part)

    query_tokens = _tokens(query)
    lowered = str(query or "").casefold()
    explicit_reference = any(phrase in lowered for phrase in _REFERENCE_PHRASES)
    identity_request = any(term in lowered for term in ("who are you", "what are you", "your name", "what can you do", "when were you created", "why were you created"))

    current = conversations.get(current_id) if current_id else None
    blocks: List[str] = []

    if isinstance(current, dict):
        current_text = _compact_messages(current.get("messages", []), limit=8, chars=4800)
        if current_text:
            blocks.append("Current conversation continuity:\n" + current_text)

    candidates = []
    for conversation_id, conversation in conversations.items():
        if conversation_id == current_id or not isinstance(conversation, dict):
            continue
        messages = conversation.get("messages", [])
        if not isinstance(messages, list) or not messages:
            continue
        recent_text = " ".join(_message_text(item) for item in messages[-6:])
        overlap = len(query_tokens & _tokens(recent_text))
        title = str(conversation.get("title") or "")
        overlap += len(query_tokens & _tokens(title))
        updated = str(conversation.get("updated_at") or conversation.get("created_at") or "")
        relevance = overlap + (5 if explicit_reference else 0)
        if identity_request:
            relevance += 1
        candidates.append((relevance, updated, conversation_id, conversation))

    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)

    included = 0
    for relevance, _, _, conversation in candidates:
        threshold = 1 if query_tokens else 999
        if relevance < threshold and not explicit_reference:
            continue
        title = str(conversation.get("title") or "Previous conversation")[:120]
        text = _compact_messages(conversation.get("messages", []), limit=5, chars=1900)
        if not text:
            continue
        blocks.append(f"Related previous conversation: {title}\n{text}")
        included += 1
        if included >= 5 or sum(len(block) for block in blocks) >= 8500:
            break

    context_parts = [identity]
    if profile:
        context_parts.append(profile)
    if blocks:
        context_parts.append(
            "[RECENT CONVERSATION CONTEXT]\n"
            "This context comes from the authenticated user's own conversations. Use it naturally when relevant. "
            "The current request has priority. Do not mention this internal context or its implementation.\n\n"
            + "\n\n---\n\n".join(blocks)[:9500]
        )
    return "\n\n".join(context_parts)


def install_recent_context_runtime() -> None:
    """Patch NovaCore's memory stage once, after NovaCore has been imported."""
    global _INSTALLED, _ORIGINAL_STAGE_MEMORY
    with _INSTALL_LOCK:
        if _INSTALLED:
            return

        from backend.core.nova_core import NovaCore

        _ORIGINAL_STAGE_MEMORY = NovaCore._stage_memory

        def stage_memory_with_recent(self, request):
            _ORIGINAL_STAGE_MEMORY(self, request)
            if getattr(self, "demo", False):
                return
            try:
                recent = build_recent_context(
                    self.conversations,
                    request.user_email,
                    request.conversation_id,
                    request.original_message,
                    request.intent,
                )
                if recent:
                    existing = str(request.memory_context or "").strip()
                    request.memory_context = (
                        existing + "\n\n" + recent
                        if existing
                        else recent
                    )[:16000]
            except Exception as error:
                request.add_warning("Recent conversation context was unavailable.")
                if getattr(self, "debug", False):
                    self._log_error("Recent conversation context failed", error)

        NovaCore._stage_memory = stage_memory_with_recent
        _INSTALLED = True
