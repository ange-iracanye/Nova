from __future__ import annotations

import json
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

        if self.persist:
            self.file.parent.mkdir(parents=True, exist_ok=True)
            with _DATA_LOCK:
                self._reload_locked()
                if not self.file.exists():
                    self.save()

    def _reload_locked(self) -> None:
        if not self.persist or not self.file.exists():
            self.data = {"users": {}}
            return
        try:
            loaded = json.loads(self.file.read_text(encoding="utf-8"))
            self.data = loaded if isinstance(loaded, dict) else {"users": {}}
        except (json.JSONDecodeError, OSError):
            self.data = {"users": {}}
        if not isinstance(self.data.get("users"), dict):
            self.data["users"] = {}

    def save(self):
        if not self.persist:
            return
        with _DATA_LOCK:
            self.file.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.file.with_suffix(self.file.suffix + ".tmp")
            temporary.write_text(
                json.dumps(self.data, indent=4, ensure_ascii=False),
                encoding="utf-8",
            )
            temporary.replace(self.file)

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
            self._reload_locked()
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
            self._reload_locked()
            user = self._user(email)
            conversations = user["conversations"]
            return dict(
                sorted(
                    conversations.items(),
                    key=lambda item: item[1].get("updated_at", "") if isinstance(item[1], dict) else "",
                    reverse=True,
                )
            )

    def add_message(self, email, cid, role, text):
        with _DATA_LOCK:
            self._reload_locked()
            user = self._user(email)
            if cid not in user["conversations"]:
                return False
            conversation = user["conversations"][cid]
            if not isinstance(conversation, dict):
                return False
            conversation.setdefault("messages", [])
            conversation["messages"].append({
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
        title = message.strip().replace("\n", " ")
        if not title:
            return "New Chat"
        title = " ".join(title.split())
        max_length = 45
        if len(title) > max_length:
            title = title[:max_length].rstrip() + "..."
        return title

    def get(self, email, cid):
        with _DATA_LOCK:
            self._reload_locked()
            user = self._user(email)
            return user["conversations"].get(cid)

    def rename(self, email, cid, title):
        with _DATA_LOCK:
            self._reload_locked()
            user = self._user(email)
            if cid not in user["conversations"]:
                return False
            title = title.strip().replace("\n", " ")
            if not title:
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
            self._reload_locked()
            user = self._user(email)
            if cid not in user["conversations"]:
                return False
            del user["conversations"][cid]
            self.save()
            return True
