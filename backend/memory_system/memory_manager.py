from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from backend.memory_system.conversation_manager import ConversationManager
from backend.memory_system.memory_extractor import MemoryExtractor
from backend.memory_system.memory_search import MemorySearch


class MemoryManager:
    """Persistent user memory plus retrieval across every saved conversation."""

    def __init__(self, embedder=None, base_path="data/memory/users"):
        print("Loading Nova Memory System...")
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.extractor = MemoryExtractor()
        self.embedder = embedder
        self.search_engine = MemorySearch(embedder)
        self.conversations = ConversationManager(persist=True)
        print("Nova Memory System ready.")

    def user_id(self, email):
        return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()

    def user_file(self, email):
        return self.base_path / self.user_id(email) / "semantic_memory.json"

    def default_memory(self):
        return {
            "version": 3,
            "memories": [],
            "facts": [],
            "preferences": [],
            "goals": [],
            "learning": [],
            "episodes": [],
            "statistics": {"total_memories": 0, "total_episodes": 0, "last_updated": None},
        }

    def load(self, email):
        file = self.user_file(email)
        file.parent.mkdir(parents=True, exist_ok=True)
        if not file.exists():
            memory = self.default_memory()
            self._write(file, memory)
            return memory
        try:
            memory = json.loads(file.read_text(encoding="utf-8"))
        except Exception:
            memory = self.default_memory()
        if not isinstance(memory, dict):
            memory = self.default_memory()
        for key in ("memories", "facts", "preferences", "goals", "learning", "episodes"):
            if not isinstance(memory.get(key), list):
                memory[key] = []
        if not isinstance(memory.get("statistics"), dict):
            memory["statistics"] = self.default_memory()["statistics"]
        return memory

    def _write(self, file, data):
        temporary = file.with_suffix(".tmp")
        temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(file)

    def _load_embedder(self):
        if self.embedder is not None:
            return
        production = os.getenv("NOVA_ENV", "development").strip().lower() == "production"
        enabled = os.getenv("NOVA_ENABLE_SEMANTIC_MEMORY", "false" if production else "true").strip().lower() in {"1", "true", "yes", "on"}
        if not enabled:
            return
        try:
            from sentence_transformers import SentenceTransformer
            self.embedder = SentenceTransformer(str(Path("data/model")))
            self.search_engine.embedder = self.embedder
            print("Nova Memory Embeddings ready.")
        except Exception as error:
            print("Memory embeddings unavailable:", error)
            self.embedder = None

    def _embed(self, text):
        self._load_embedder()
        if self.embedder is None:
            return None
        try:
            vector = self.embedder.encode(text, normalize_embeddings=True)
            return vector.tolist() if hasattr(vector, "tolist") else list(vector)
        except Exception as error:
            print("Memory embedding failed:", error)
            return None

    def add_memory(self, email, text, memory_type="episode", subject=None,
                   conversation_id=None, importance=0.5, confidence=0.8,
                   metadata=None, formatted_text=None):
        if not text:
            return None
        data = self.load(email)
        now = datetime.now().isoformat()
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.8
        if confidence > 1:
            confidence /= 100
        confidence = max(0.0, min(1.0, confidence))
        search_text = (formatted_text or f"Subject: {subject or ''}\nUser: {text}\nNova:").strip()
        embedding = self.search_engine.embed(search_text) or self._embed(search_text)
        memory = {
            "id": hashlib.sha256((email + now + text).encode("utf-8")).hexdigest(),
            "type": memory_type,
            "text": search_text,
            "subject": subject,
            "conversation_id": conversation_id,
            "importance": importance,
            "confidence": confidence,
            "created_at": now,
            "last_recalled": None,
            "recall_count": 0,
            "metadata": metadata or {},
            "embedding": embedding,
        }
        normalized = search_text.lower().strip()
        for existing in data["memories"]:
            if str(existing.get("text", "")).lower().strip() == normalized:
                existing["recall_count"] = existing.get("recall_count", 0) + 1
                existing["last_recalled"] = now
                self._write(self.user_file(email), data)
                return existing
        data["memories"].append(memory)
        category = {"fact": "facts", "preference": "preferences", "goal": "goals", "learning": "learning", "episode": "episodes"}.get(memory_type)
        if category:
            data[category].append(memory["id"])
        data["statistics"]["total_memories"] = len(data["memories"])
        data["statistics"]["total_episodes"] = len(data["episodes"])
        data["statistics"]["last_updated"] = now
        self._write(self.user_file(email), data)
        return memory

    def remember(self, email, user_message, assistant_message, subject=None,
                 confidence=None, conversation_id=None):
        try:
            confidence = 0.7 if confidence is None else float(confidence)
        except (TypeError, ValueError):
            confidence = 0.7
        if confidence > 1:
            confidence /= 100
        confidence = max(0.0, min(1.0, confidence))
        search_text = f"Subject: {subject or ''}\nUser: {user_message}\nNova: {assistant_message}".strip()
        self.add_memory(email, user_message, "episode", subject, conversation_id,
                        importance=0.45, confidence=confidence, formatted_text=search_text)
        for item in self.extractor.extract(user_message, subject=subject, conversation_id=conversation_id):
            kind = item.get("type", "preference")
            final_type = "fact" if kind == "explicit_memory" else kind if kind in {"fact", "goal", "learning", "preference"} else "preference"
            self.add_memory(email, item.get("text", ""), final_type, subject, conversation_id,
                            importance=item.get("importance", 1.0 if final_type == "fact" else 0.8),
                            confidence=item.get("confidence", 0.8))

    def search(self, email, query, limit=8, subject=None):
        data = self.load(email)
        memories = data["memories"]
        if subject:
            memories = [m for m in memories if m.get("subject") == subject or m.get("type") in {"fact", "preference", "goal"}]
        results = self.search_engine.search(memories, query, limit=limit)
        if results:
            now = datetime.now().isoformat()
            for result in results:
                memory = result["memory"]
                memory["recall_count"] = memory.get("recall_count", 0) + 1
                memory["last_recalled"] = now
            self._write(self.user_file(email), data)
        return results

    @staticmethod
    def _tokens(text):
        return set(re.findall(r"\b\w+\b", str(text or "").lower()))

    @classmethod
    def _keyword_score(cls, query, text):
        q = cls._tokens(query)
        if not q:
            return 0.0
        return len(q & cls._tokens(text)) / len(q)

    @staticmethod
    def _conversation_text(conversation):
        return "\n".join(f"{m.get('role', 'user').title()}: {m.get('text', '')}" for m in conversation.get("messages", []) if isinstance(m, dict))

    @staticmethod
    def _format_date(value):
        """Return an unambiguous human-readable timestamp for the model."""
        if not value:
            return "unknown date"
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        except (TypeError, ValueError):
            return str(value)

    def _conversation_context(self, email, query, max_characters):
        conversations = self.conversations.list(email)
        if not conversations:
            return ""

        ordered = list(conversations.values())
        ordered.sort(key=lambda c: c.get("updated_at", "") if isinstance(c, dict) else "", reverse=True)
        current = ordered[0] if ordered else None
        sections = [
            "MEMORY DATE RULE: Conversation timestamps below are authoritative metadata. "
            "Use them to answer questions about when the user previously talked to Nova. "
            "Do not claim that you cannot know a date when a relevant timestamp is present."
        ]

        if current:
            messages = [m for m in current.get("messages", []) if isinstance(m, dict)]
            if messages:
                sections.append(
                    f"CURRENT CONVERSATION (highest priority; updated {self._format_date(current.get('updated_at'))}):"
                )
                recent = messages[-12:]
                for message in recent:
                    role = "User" if message.get("role") == "user" else "Nova"
                    timestamp = self._format_date(message.get("timestamp"))
                    sections.append(f"[{timestamp}] {role}: {str(message.get('text', '')).strip()}")

        candidates = []
        for conversation in ordered[1:]:
            if not isinstance(conversation, dict):
                continue
            messages = [m for m in conversation.get("messages", []) if isinstance(m, dict)]
            if not messages:
                continue
            text = self._conversation_text(conversation)
            relevance = self._keyword_score(query, text)
            if relevance <= 0:
                continue
            updated = conversation.get("updated_at", "")
            candidates.append((relevance, updated, conversation, messages))
        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)

        for relevance, _, conversation, messages in candidates[:6]:
            sections.append(
                f"\nRELEVANT PREVIOUS CONVERSATION ({relevance:.2f} relevance; "
                f"updated {self._format_date(conversation.get('updated_at'))}):"
            )
            scores = [(self._keyword_score(query, m.get("text", "")), i) for i, m in enumerate(messages)]
            scores.sort(reverse=True)
            chosen = set()
            for score, index in scores[:3]:
                if score > 0:
                    chosen.add(index)
                    if index > 0:
                        chosen.add(index - 1)
            for index in sorted(chosen):
                message = messages[index]
                role = "User" if message.get("role") == "user" else "Nova"
                timestamp = self._format_date(message.get("timestamp"))
                sections.append(f"[{timestamp}] {role}: {str(message.get('text', '')).strip()}")

        context = "\n".join(sections).strip()
        if len(context) > max_characters:
            context = context[:max_characters].rstrip() + "\n[Conversation memory context truncated]"
        return context

    def build_context(self, email, query, subject=None, limit=8, max_characters=12000):
        sections = []
        results = self.search(email, query, limit=limit, subject=subject)
        if results:
            grouped = {
                "fact": ("LONG-TERM FACTS:", []),
                "preference": ("STUDENT PREFERENCES:", []),
                "goal": ("STUDENT GOALS:", []),
                "learning": ("LEARNING HISTORY:", []),
                "episode": ("RELEVANT PREVIOUS DISCUSSIONS:", []),
            }
            for result in results:
                memory = result["memory"]
                kind = memory.get("type", "episode")
                if kind in grouped:
                    grouped[kind][1].append(memory.get("text", ""))
            for _, (heading, items) in grouped.items():
                if items:
                    sections.append(heading)
                    sections.extend(f"- {item}" for item in items)

        conversation_context = self._conversation_context(email, query, max_characters)
        if conversation_context:
            sections.append(conversation_context)
        if not sections:
            return "No relevant long-term memory or previous conversation context."
        context = "\n".join(sections)
        if len(context) > max_characters:
            context = context[:max_characters].rstrip() + "\n[Memory context truncated]"
        return context

    def get_all(self, email):
        return self.load(email)

    def delete_memory(self, email, memory_id):
        data = self.load(email)
        original = len(data["memories"])
        data["memories"] = [m for m in data["memories"] if m.get("id") != memory_id]
        if len(data["memories"]) == original:
            return False
        valid = {m.get("id") for m in data["memories"]}
        for key in ("facts", "preferences", "goals", "learning", "episodes"):
            data[key] = [item for item in data[key] if item in valid]
        data["statistics"]["total_memories"] = len(data["memories"])
        data["statistics"]["total_episodes"] = len(data["episodes"])
        data["statistics"]["last_updated"] = datetime.now().isoformat()
        self._write(self.user_file(email), data)
        return True
