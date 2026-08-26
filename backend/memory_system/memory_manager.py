import json
import hashlib
from pathlib import Path
from datetime import datetime

import os

from backend.memory_system.memory_search import MemorySearch
from backend.memory_system.memory_extractor import MemoryExtractor


class MemoryManager:

    def __init__(
        self,
        embedder=None,
        base_path="data/memory/users"
    ):

        print("Loading Nova Memory System...")

        self.base_path = Path(base_path)

        self.base_path.mkdir(
            parents=True,
            exist_ok=True
        )

        self.extractor = MemoryExtractor()

        self.embedder = embedder

        self.search_engine = MemorySearch(
            embedder
        )

        print("Nova Memory System ready.")

    # =====================================
    # USER DIRECTORY
    # =====================================

    def user_id(self, email):

        email = (
            email
            .strip()
            .lower()
        )

        return hashlib.sha256(
            email.encode("utf-8")
        ).hexdigest()

    def user_file(self, email):

        uid = self.user_id(email)

        return (
            self.base_path
            / uid
            / "semantic_memory.json"
        )

    # =====================================
    # DEFAULT
    # =====================================

    def default_memory(self):

        return {
            "version": 2,
            "memories": [],
            "facts": [],
            "preferences": [],
            "goals": [],
            "learning": [],
            "episodes": [],
            "statistics": {
                "total_memories": 0,
                "total_episodes": 0,
                "last_updated": None
            }
        }

    # =====================================
    # LOAD
    # =====================================

    def load(self, email):

        file = self.user_file(email)

        file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        if not file.exists():

            memory = self.default_memory()

            self._write(
                file,
                memory
            )

            return memory

        try:

            memory = json.loads(
                file.read_text(
                    encoding="utf-8"
                )
            )

        except Exception:

            memory = self.default_memory()

        return memory

    # =====================================
    # WRITE
    # =====================================

    def _write(self, file, data):

        temporary = file.with_suffix(".tmp")

        temporary.write_text(
            json.dumps(
                data,
                indent=4,
                ensure_ascii=False
            ),
            encoding="utf-8"
        )

        temporary.replace(file)

    # =====================================
    # EMBEDDINGS
    # =====================================

    def _load_embedder(self):

        if self.embedder is not None:
            return

        # The public Render instance has 512 MB RAM. Loading the
        # SentenceTransformer/Torch stack for every first chat request
        # can exhaust that limit and make Render return HTTP 503 while
        # restarting the process. Public V1 therefore uses the existing
        # keyword/recency/importance memory retrieval unless semantic
        # embeddings are explicitly enabled. Local development keeps the
        # previous behavior by default.
        production = os.getenv("NOVA_ENV", "development").strip().lower() == "production"
        enabled = os.getenv(
            "NOVA_ENABLE_SEMANTIC_MEMORY",
            "false" if production else "true",
        ).strip().lower() in {"1", "true", "yes", "on"}
        if not enabled:
            return

        model_path = Path("data/model")

        try:
            from sentence_transformers import SentenceTransformer

            self.embedder = SentenceTransformer(
                str(model_path)
            )

            self.search_engine.embedder = (
                self.embedder
            )

            print(
                "Nova Memory Embeddings ready."
            )

        except Exception as error:

            print(
                "Memory embeddings unavailable:",
                error
            )

            self.embedder = None

    # =====================================
    # EMBED
    # =====================================

    def _embed(self, text):

        self._load_embedder()

        if self.embedder is None:
            return None

        try:

            vector = self.embedder.encode(
                text,
                normalize_embeddings=True
            )

            if hasattr(vector, "tolist"):
                return vector.tolist()

            return list(vector)

        except Exception as error:

            print(
                "Memory embedding failed:",
                error
            )

            return None

    # =====================================
    # ADD MEMORY
    # =====================================

    def add_memory(
        self,
        email,
        text,
        memory_type="episode",
        subject=None,
        conversation_id=None,
        importance=0.5,
        confidence=0.8,
        metadata=None,
        formatted_text=None
    ):

        if not text:
            return None

        data = self.load(email)

        now = datetime.now().isoformat()

        # =================================
        # NORMALIZE CONFIDENCE
        # =================================

        try:

            confidence = float(
                confidence
            )

        except (TypeError, ValueError):

            confidence = 0.8

        if confidence > 1:

            confidence /= 100

        confidence = max(
            0.0,
            min(
                1.0,
                confidence
            )
        )

        # =================================
        # SEARCHABLE TEXT
        # =================================

        if formatted_text is not None:

            search_text = formatted_text.strip()

        else:

            search_text = (
                f"Subject: {subject or ''}\n"
                f"User: {text}\n"
                f"Nova:"
            ).strip()

        # =================================
        # EMBEDDING
        # =================================

        embedding = self.search_engine.embed(
            search_text
        )

        if embedding is None:

            embedding = self._embed(
                search_text
            )

        # =================================
        # MEMORY OBJECT
        # =================================

        memory = {

            "id": hashlib.sha256(
                (
                    email
                    + now
                    + text
                ).encode("utf-8")
            ).hexdigest(),

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

            "embedding": embedding
        }

        # =================================
        # AVOID EXACT DUPLICATES
        # =================================

        normalized = (
            search_text
            .strip()
            .lower()
        )

        for existing in data["memories"]:

            existing_text = (
                existing.get("text", "")
                .strip()
                .lower()
            )

            if existing_text == normalized:

                existing["recall_count"] = (
                    existing.get(
                        "recall_count",
                        0
                    ) + 1
                )

                existing["last_recalled"] = now

                self._write(
                    self.user_file(email),
                    data
                )

                return existing

        # =================================
        # STORE MEMORY
        # =================================

        data["memories"].append(
            memory
        )

        # =================================
        # CATEGORIZE
        # =================================

        if memory_type == "fact":

            data["facts"].append(
                memory["id"]
            )

        elif memory_type == "preference":

            data["preferences"].append(
                memory["id"]
            )

        elif memory_type == "goal":

            data["goals"].append(
                memory["id"]
            )

        elif memory_type == "learning":

            data["learning"].append(
                memory["id"]
            )

        elif memory_type == "episode":

            data["episodes"].append(
                memory["id"]
            )

            data["statistics"][
                "total_episodes"
            ] = len(
                data["episodes"]
            )

        # =================================
        # STATISTICS
        # =================================

        data["statistics"][
            "total_memories"
        ] = len(
            data["memories"]
        )

        data["statistics"][
            "last_updated"
        ] = now

        self._write(
            self.user_file(email),
            data
        )

        return memory

    # =====================================
    # RECORD CONVERSATION
    # =====================================

    def remember(
        self,
        email,
        user_message,
        assistant_message,
        subject=None,
        confidence=None,
        conversation_id=None
    ):

        # =================================
        # NORMALIZE CONFIDENCE
        # =================================

        if confidence is None:

            memory_confidence = 0.7

        else:

            try:

                memory_confidence = float(
                    confidence
                )

            except (TypeError, ValueError):

                memory_confidence = 0.7

        if memory_confidence > 1:

            memory_confidence /= 100

        memory_confidence = max(
            0.0,
            min(
                1.0,
                memory_confidence
            )
        )

        # =================================
        # COMPLETE EPISODE
        # =================================

        search_text = (
            f"Subject: {subject or ''}\n"
            f"User: {user_message}\n"
            f"Nova: {assistant_message}"
        ).strip()

        self.add_memory(

            email,

            user_message,

            memory_type="episode",

            subject=subject,

            conversation_id=conversation_id,

            importance=0.45,

            confidence=memory_confidence,

            formatted_text=search_text
        )

        # =================================
        # EXPLICIT / LONG-TERM MEMORIES
        # =================================

        extracted = self.extractor.extract(
            user_message,
            subject=subject,
            conversation_id=conversation_id
        )

        for item in extracted:

            memory_type = item.get(
                "type",
                "preference"
            )

            if memory_type == "explicit_memory":

                final_type = "fact"
                importance = 1.0

            elif memory_type == "fact":

                final_type = "fact"

                importance = item.get(
                    "importance",
                    0.8
                )

            elif memory_type == "goal":

                final_type = "goal"

                importance = item.get(
                    "importance",
                    0.85
                )

            elif memory_type == "learning":

                final_type = "learning"

                importance = item.get(
                    "importance",
                    0.8
                )

            else:

                final_type = "preference"

                importance = item.get(
                    "importance",
                    0.75
                )

            self.add_memory(

                email,

                item["text"],

                memory_type=final_type,

                subject=subject,

                conversation_id=conversation_id,

                importance=importance,

                confidence=item.get(
                    "confidence",
                    0.8
                )
            )

    # =====================================
    # SEARCH
    # =====================================

    def search(
        self,
        email,
        query,
        limit=8,
        subject=None
    ):

        data = self.load(email)

        memories = data["memories"]

        # =================================
        # SUBJECT FILTER
        # =================================

        if subject:

            subject_memories = [

                memory

                for memory in memories

                if (
                    memory.get("subject")
                    == subject
                    or
                    memory.get("type")
                    in (
                        "fact",
                        "preference",
                        "goal"
                    )
                )
            ]

        else:

            subject_memories = memories

        # =================================
        # SEMANTIC SEARCH
        # =================================

        results = self.search_engine.search(
            subject_memories,
            query,
            limit=limit
        )

        # =================================
        # UPDATE RECALL STATISTICS
        # =================================

        now = datetime.now().isoformat()

        changed = False

        for result in results:

            memory = result["memory"]

            memory["recall_count"] = (
                memory.get(
                    "recall_count",
                    0
                ) + 1
            )

            memory["last_recalled"] = now

            changed = True

        if changed:

            self._write(
                self.user_file(email),
                data
            )

        return results

    # =====================================
    # BUILD CONTEXT
    # =====================================

    def build_context(
        self,
        email,
        query,
        subject=None,
        limit=8,
        max_characters=12000
    ):

        results = self.search(
            email,
            query,
            limit=limit,
            subject=subject
        )

        if not results:

            return (
                "No relevant long-term memory."
            )

        sections = []

        # =================================
        # FACTS
        # =================================

        facts = [

            result["memory"]

            for result in results

            if result["memory"].get("type")
            == "fact"
        ]

        if facts:

            sections.append(
                "LONG-TERM FACTS:"
            )

            for memory in facts:

                sections.append(
                    f"- {memory['text']}"
                )

        # =================================
        # PREFERENCES
        # =================================

        preferences = [

            result["memory"]

            for result in results

            if result["memory"].get("type")
            == "preference"
        ]

        if preferences:

            sections.append(
                "\nSTUDENT PREFERENCES:"
            )

            for memory in preferences:

                sections.append(
                    f"- {memory['text']}"
                )

        # =================================
        # GOALS
        # =================================

        goals = [

            result["memory"]

            for result in results

            if result["memory"].get("type")
            == "goal"
        ]

        if goals:

            sections.append(
                "\nSTUDENT GOALS:"
            )

            for memory in goals:

                sections.append(
                    f"- {memory['text']}"
                )

        # =================================
        # LEARNING
        # =================================

        learning = [

            result["memory"]

            for result in results

            if result["memory"].get("type")
            == "learning"
        ]

        if learning:

            sections.append(
                "\nLEARNING HISTORY:"
            )

            for memory in learning:

                sections.append(
                    f"- {memory['text']}"
                )

        # =================================
        # EPISODES
        # =================================

        episodes = [

            result["memory"]

            for result in results

            if result["memory"].get("type")
            == "episode"
        ]

        if episodes:

            sections.append(
                "\nRELEVANT PREVIOUS DISCUSSIONS:"
            )

            for memory in episodes:

                sections.append(
                    "\n" + memory["text"]
                )

        context = "\n".join(
            sections
        )

        # =================================
        # CONTEXT PROTECTION
        # =================================

        if len(context) > max_characters:

            context = (
                context[:max_characters]
                + "\n[Memory context truncated]"
            )

        return context

    # =====================================
    # FULL MEMORY
    # =====================================

    def get_all(self, email):

        return self.load(email)

    # =====================================
    # DELETE MEMORY
    # =====================================

    def delete_memory(
        self,
        email,
        memory_id
    ):

        data = self.load(email)

        original = len(
            data["memories"]
        )

        data["memories"] = [

            memory

            for memory in data["memories"]

            if memory["id"] != memory_id
        ]

        if len(data["memories"]) == original:

            return False

        valid_ids = {

            memory["id"]

            for memory in data["memories"]
        }

        for key in (
            "facts",
            "preferences",
            "goals",
            "learning",
            "episodes"
        ):

            data[key] = [

                stored_id

                for stored_id in data[key]

                if stored_id in valid_ids
            ]

        data["statistics"][
            "total_memories"
        ] = len(
            data["memories"]
        )

        data["statistics"][
            "total_episodes"
        ] = len(
            data["episodes"]
        )

        data["statistics"][
            "last_updated"
        ] = datetime.now().isoformat()

        self._write(
            self.user_file(email),
            data
        )

        return True