from __future__ import annotations

import json
from copy import deepcopy
import os
import threading
import uuid
from datetime import datetime
from pathlib import Path


_DATA_LOCK = threading.RLock()


class ConversationManager:
    def __init__(self, persist=True):
        self.persist = persist
        self.file = Path(os.getenv("NOVA_CONVERSATIONS_FILE", "data/memory/conversations.json"))
        self.data = {"users": {}}
        self._file_signature = None

        if self.persist:
            self.file.parent.mkdir(parents=True, exist_ok=True)
            with _DATA_LOCK:
                self._reload_locked()
                if not self.file.exists():
                    self.save()

    def _signature_locked(self):
        if not self.persist or not self.file.exists():
            return None
        try:
            stat = self.file.stat()
            return (stat.st_mtime_ns, stat.st_size)
        except OSError:
            return None

    def _reload_locked(self) -> None:
        if not self.persist or not self.file.exists():
            self.data = {"users": {}}
            self._file_signature = None
            return
        try:
            loaded = json.loads(self.file.read_text(encoding="utf-8"))
            self.data = loaded if isinstance(loaded, dict) else {"users": {}}
        except (json.JSONDecodeError, OSError, UnicodeError):
            self.data = {"users": {}}
        raw_users = self.data.get("users")
        normalized_users = {}
        if isinstance(raw_users, dict):
            for email, user in raw_users.items():
                if not isinstance(email, str) or not isinstance(user, dict):
                    continue
                raw_conversations = user.get("conversations")
                if not isinstance(raw_conversations, dict):
                    continue
                conversations = {}
                for cid, conversation in raw_conversations.items():
                    if not isinstance(cid, str) or not isinstance(conversation, dict):
                        continue
                    normalized = dict(conversation)
                    messages = normalized.get("messages")
                    normalized["messages"] = (
                        [message for message in messages if isinstance(message, dict)]
                        if isinstance(messages, list) else []
                    )
                    title = normalized.get("title")
                    normalized["title"] = title if isinstance(title, str) and title.strip() else "New Chat"
                    conversations[cid] = normalized
                normalized_users[email.strip().lower()] = {"conversations": conversations}
        self.data = {"users": normalized_users}
        self._file_signature = self._signature_locked()

    def _ensure_fresh_locked(self) -> None:
        if self.persist and self._signature_locked() != self._file_signature:
            self._reload_locked()

    def save(self):
        if not self.persist:
            return
        with _DATA_LOCK:
            self.file.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.file.with_suffix(self.file.suffix + ".tmp")
            temporary.write_text(
                json.dumps(self.data, ensure_ascii=False, separators=(",", ":"), allow_nan=False),
                encoding="utf-8",
            )
            temporary.replace(self.file)
            self._file_signature = self._signature_locked()

    def _user(self, email):
        email = email.strip().lower()
        if email not in self.data["users"]:
            self.data["users"][email] = {"conversations": {}}
        user = self.data["users"][email]
        if not isinstance(user, dict) or not isinstance(user.get("conversations"), dict):
            user = {"conversations": {}}
            self.data["users"][email] = user
        return user

    def create(self, email):
        with _DATA_LOCK:
            self._ensure_fresh_locked()
            user = self._user(email)
            cid = str(uuid.uuid4())
            now = datetime.now().isoformat()
            user["conversations"][cid] = {
                "id": cid,
                "title": "New Chat",
                "created_at": now,
                "updated_at": now,
                "messages": [],
            }
            self.save()
            return cid

    def list(self, email):
        with _DATA_LOCK:
            self._ensure_fresh_locked()
            user = self._user(email)
            conversations = user["conversations"]
            return deepcopy(dict(
                sorted(
                    conversations.items(),
                    key=lambda item: item[1].get("updated_at", "") if isinstance(item[1], dict) else "",
                    reverse=True,
                )
            ))

    def add_message(self, email, cid, role, text):
        if not isinstance(text, str) or not text.strip():
            return False
        role = str(role or "").strip().lower()
        if role not in {"user", "assistant", "system", "tool"}:
            return False
        with _DATA_LOCK:
            self._ensure_fresh_locked()
            user = self._user(email)
            if cid not in user["conversations"]:
                return False
            conversation = user["conversations"][cid]
            if not isinstance(conversation, dict):
                return False
            messages = conversation.get("messages")
            if not isinstance(messages, list):
                messages = []
                conversation["messages"] = messages
            messages.append({
                "role": role,
                "text": text,
                "timestamp": datetime.now().isoformat(),
            })
            conversation["updated_at"] = datetime.now().isoformat()
            if role == "user" and conversation.get("title") == "New Chat":
                conversation["title"] = self.generate_title(text)
            self.save()
            return True

    def generate_title(self, message):
        title = str(message or "").strip().replace("\n", " ")
        if not title:
            return "New Chat"
        title = " ".join(title.split())
        max_length = 45
        if len(title) > max_length:
            title = title[:max_length].rstrip() + "..."
        return title

    def get(self, email, cid):
        with _DATA_LOCK:
            self._ensure_fresh_locked()
            user = self._user(email)
            conversation = user["conversations"].get(cid)
            return deepcopy(conversation) if isinstance(conversation, dict) else None

    def rename(self, email, cid, title):
        with _DATA_LOCK:
            self._ensure_fresh_locked()
            user = self._user(email)
            if cid not in user["conversations"]:
                return False
            title = str(title or "").strip().replace("\n", " ")
            if not title or len(title) > 100:
                return False
            conversation = user["conversations"][cid]
            if not isinstance(conversation, dict):
                return False
            conversation["title"] = title
            conversation["updated_at"] = datetime.now().isoformat()
            self.save()
            return True

    def delete(self, email, cid):
        with _DATA_LOCK:
            self._ensure_fresh_locked()
            user = self._user(email)
            if cid not in user["conversations"]:
                return False
            del user["conversations"][cid]
            self.save()
            return True
