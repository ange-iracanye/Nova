"""Quality layer for Nova's long-term memory.

The original memory store is intentionally kept compatible. This module adds
memory lifecycle, contradiction handling, recency-aware retrieval and
consolidation without changing the public MemoryManager API.
"""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone, timedelta
from typing import Any


_PATCHED = False
_ORIGINAL_ADD = None
_ORIGINAL_SEARCH = None
_ORIGINAL_BUILD_CONTEXT = None
_ORIGINAL_GET_ALL = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        text = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (TypeError, ValueError):
        return None


def _norm(text: Any) -> str:
    value = str(text or "").casefold().strip()
    value = re.sub(r"\s+", " ", value)
    value = re.sub(r"[^\w\s]", "", value)
    return value


def _canonical_type(memory_type: Any) -> str:
    value = str(memory_type or "episode").strip().casefold()
    aliases = {
        "explicit_memory": "fact",
        "long_term": "fact",
        "long-term": "fact",
        "temporary": "episode",
    }
    return aliases.get(value, value or "episode")


def _importance(memory: dict[str, Any]) -> float:
    try:
        return max(0.0, min(1.0, float(memory.get("importance", 0.5))))
    except (TypeError, ValueError):
        return 0.5


def _confidence(memory: dict[str, Any]) -> float:
    try:
        value = float(memory.get("confidence", 0.7))
        if value > 1:
            value /= 100
        return max(0.0, min(1.0, value))
    except (TypeError, ValueError):
        return 0.7


def _recency(memory: dict[str, Any], half_life_days: float) -> float:
    stamp = _parse(memory.get("last_recalled")) or _parse(memory.get("created_at"))
    if stamp is None:
        return 0.5
    age_days = max(0.0, (_now() - stamp).total_seconds() / 86400.0)
    return math.exp(-math.log(2) * age_days / max(0.1, half_life_days))


def _is_expired(memory: dict[str, Any]) -> bool:
    expires = _parse(memory.get("expires_at"))
    return expires is not None and expires <= _now()


def _is_active(memory: dict[str, Any]) -> bool:
    return not _is_expired(memory) and not memory.get("superseded_by") and memory.get("status", "active") == "active"


def _memory_key(memory: dict[str, Any]) -> tuple[str, str, str]:
    return (
        _canonical_type(memory.get("type")),
        _norm(memory.get("subject")),
        _norm(memory.get("text")),
    )


def _contradiction_key(memory: dict[str, Any]) -> tuple[str, str]:
    """Key for preference/fact/goal replacement.

    Exact semantic contradiction detection is deliberately conservative. We
    only replace memories when they are clearly about the same category and
    subject, avoiding destructive guesses about what the student meant.
    """
    text = _norm(memory.get("text"))
    subject = _norm(memory.get("subject"))
    prefixes = (
        "i prefer ", "i like ", "i dont like ", "i want ",
        "my goal is ", "i am studying ", "im studying ", "i study ",
    )
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    head = " ".join(text.split()[:4])
    return _canonical_type(memory.get("type")), f"{subject}:{head}"


def install_memory_quality(MemoryManager) -> None:
    global _PATCHED, _ORIGINAL_ADD, _ORIGINAL_SEARCH, _ORIGINAL_BUILD_CONTEXT, _ORIGINAL_GET_ALL
    if _PATCHED:
        return

    _ORIGINAL_ADD = MemoryManager.add_memory
    _ORIGINAL_SEARCH = MemoryManager.search
    _ORIGINAL_BUILD_CONTEXT = MemoryManager.build_context
    _ORIGINAL_GET_ALL = MemoryManager.get_all

    def add_memory(self, email, text, memory_type="episode", subject=None,
                   conversation_id=None, importance=0.5, confidence=0.8,
                   metadata=None, formatted_text=None):
        kind = _canonical_type(memory_type)
        importance_f = max(0.0, min(1.0, float(importance or 0.5)))
        confidence_f = float(confidence if confidence is not None else 0.7)
        if confidence_f > 1:
            confidence_f /= 100
        confidence_f = max(0.0, min(1.0, confidence_f))

        # Temporary episodes should not live forever. Long-term memories do.
        expires_at = None
        if kind == "episode":
            expires_at = (_now() + timedelta(days=180)).isoformat()

        result = _ORIGINAL_ADD(
            self, email, text, memory_type=kind, subject=subject,
            conversation_id=conversation_id, importance=importance_f,
            confidence=confidence_f, metadata=metadata, formatted_text=formatted_text,
        )
        if not result:
            return result

        data = self.load(email)
        now = _now().isoformat()
        result["type"] = kind
        result["status"] = "active"
        result["updated_at"] = now
        result["importance"] = importance_f
        result["confidence"] = confidence_f
        result["expires_at"] = expires_at
        result.setdefault("metadata", {})
        result["metadata"].setdefault("memory_version", 3)

        # Repeated long-term statements strengthen one memory instead of
        # creating a graveyard of duplicates.
        if kind in {"fact", "preference", "goal", "learning"}:
            target_key = _contradiction_key(result)
            for existing in data.get("memories", []):
                if existing.get("id") == result.get("id"):
                    continue
                if not _is_active(existing):
                    continue
                if _contradiction_key(existing) != target_key:
                    continue
                if _memory_key(existing) == _memory_key(result):
                    existing["confidence"] = max(_confidence(existing), confidence_f)
                    existing["importance"] = max(_importance(existing), importance_f)
                    existing["updated_at"] = now
                    existing["recall_count"] = existing.get("recall_count", 0) + 1
                    result["status"] = "active"
                    self._write(self.user_file(email), data)
                    return existing
                # Newer explicit information supersedes an older conflicting
                # statement, but the old evidence is retained for auditability.
                if confidence_f >= _confidence(existing) or kind in {"fact", "preference", "goal"}:
                    existing["status"] = "superseded"
                    existing["superseded_by"] = result.get("id")
                    existing["updated_at"] = now

        self._write(self.user_file(email), data)
        return result

    def search(self, email, query, limit=8, subject=None):
        data = self.load(email)
        active = [m for m in data.get("memories", []) if _is_active(m)]
        if active != data.get("memories", []):
            data["memories"] = active
            data["statistics"]["total_memories"] = len(active)
            self._write(self.user_file(email), data)

        results = _ORIGINAL_SEARCH(self, email, query, limit=max(limit * 3, 12), subject=subject)
        rescored = []
        for item in results:
            memory = item.get("memory", {})
            if not _is_active(memory):
                continue
            semantic = float(item.get("score", item.get("similarity", 0.0)) or 0.0)
            recency = _recency(memory, 45.0 if memory.get("type") == "episode" else 365.0)
            importance = _importance(memory)
            confidence = _confidence(memory)
            recall = min(1.0, float(memory.get("recall_count", 0) or 0) / 10.0)
            score = (0.62 * semantic) + (0.16 * recency) + (0.14 * importance) + (0.06 * confidence) + (0.02 * recall)
            item = dict(item)
            item["score"] = score
            rescored.append(item)

        rescored.sort(key=lambda x: x.get("score", 0.0), reverse=True)
        return rescored[:limit]

    def build_context(self, email, query, subject=None, limit=8, max_characters=12000):
        # Use the improved retrieval but keep the original public formatting
        # contract for callers that expect the existing sections.
        results = search(self, email, query, limit=limit, subject=subject)
        if not results:
            return "No relevant long-term memory."
        sections = []
        grouped = {"fact": [], "preference": [], "goal": [], "learning": [], "episode": []}
        for result in results:
            memory = result.get("memory", {})
            grouped.setdefault(_canonical_type(memory.get("type")), []).append(memory)
        labels = {
            "fact": "LONG-TERM FACTS:",
            "preference": "STUDENT PREFERENCES:",
            "goal": "STUDENT GOALS:",
            "learning": "LEARNING PROFILE:",
            "episode": "RELEVANT PREVIOUS DISCUSSIONS:",
        }
        for kind in ("fact", "preference", "goal", "learning", "episode"):
            memories = grouped.get(kind, [])
            if not memories:
                continue
            sections.append(labels[kind])
            for memory in memories:
                text = str(memory.get("text", "")).strip()
                if kind == "episode":
                    text = text[-2200:]
                sections.append(f"- {text}")
        context = "\n".join(sections)
        if len(context) > max_characters:
            context = context[:max_characters].rstrip() + "\n[Memory context truncated]"
        return context

    def get_all(self, email):
        data = self.load(email)
        active = [m for m in data.get("memories", []) if _is_active(m)]
        data["memories"] = active
        data["statistics"]["total_memories"] = len(active)
        return data

    def consolidate(self, email):
        data = self.load(email)
        active = [m for m in data.get("memories", []) if _is_active(m)]
        seen = {}
        removed = 0
        for memory in active:
            key = _memory_key(memory)
            existing = seen.get(key)
            if existing is None:
                seen[key] = memory
                continue
            existing["confidence"] = max(_confidence(existing), _confidence(memory))
            existing["importance"] = max(_importance(existing), _importance(memory))
            existing["recall_count"] = existing.get("recall_count", 0) + memory.get("recall_count", 0)
            memory["status"] = "superseded"
            memory["superseded_by"] = existing.get("id")
            removed += 1
        data["memories"] = [m for m in active if m.get("status") == "active"]
        data["statistics"]["total_memories"] = len(data["memories"])
        data["statistics"]["last_consolidated"] = _now().isoformat()
        self._write(self.user_file(email), data)
        return {"removed": removed, "remaining": len(data["memories"])}

    MemoryManager.add_memory = add_memory
    MemoryManager.search = search
    MemoryManager.build_context = build_context
    MemoryManager.get_all = get_all
    MemoryManager.consolidate = consolidate
    _PATCHED = True
