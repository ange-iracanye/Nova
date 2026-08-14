import math
import re

from datetime import datetime, timezone


class MemorySearch:

    def __init__(
        self,
        embedder=None
    ):

        self.embedder = embedder

    # =====================================
    # EMBEDDING
    # =====================================

    def embed(self, text):

        if (
            self.embedder is None
            or not text
        ):
            return None

        try:

            embedding = self.embedder.encode(
                text,
                normalize_embeddings=True
            )

            if hasattr(embedding, "tolist"):
                return embedding.tolist()

            return list(embedding)

        except Exception as error:

            print(
                "Memory search embedding failed:",
                error
            )

            return None

    # =====================================
    # NORMALIZATION
    # =====================================

    def normalize(self, text):

        if not text:
            return ""

        text = str(text).lower()

        text = re.sub(
            r"\s+",
            " ",
            text
        )

        return text.strip()

    # =====================================
    # TOKENIZATION
    # =====================================

    def tokenize(self, text):

        text = self.normalize(text)

        return set(
            re.findall(
                r"\b\w+\b",
                text
            )
        )

    # =====================================
    # KEYWORD SCORE
    # =====================================

    def keyword_score(
        self,
        query,
        text
    ):

        query_words = self.tokenize(query)

        text_words = self.tokenize(text)

        if not query_words:
            return 0.0

        if not text_words:
            return 0.0

        matches = query_words.intersection(
            text_words
        )

        return (
            len(matches)
            / len(query_words)
        )

    # =====================================
    # SUBJECT SCORE
    # =====================================

    def subject_score(
        self,
        query,
        memory
    ):

        subject = memory.get("subject")

        if not subject:
            return 0.0

        query_words = self.tokenize(query)

        subject_words = self.tokenize(
            subject
        )

        if not query_words:
            return 0.0

        if not subject_words:
            return 0.0

        matches = query_words.intersection(
            subject_words
        )

        if matches:

            return min(
                1.0,
                len(matches)
                / len(subject_words)
            )

        return 0.0

    # =====================================
    # SEMANTIC SCORE
    # =====================================

    def semantic_score(
        self,
        query_embedding,
        memory_embedding
    ):

        if (
            query_embedding is None
            or memory_embedding is None
        ):
            return 0.0

        try:

            score = float(
                sum(
                    a * b
                    for a, b in zip(
                        query_embedding,
                        memory_embedding
                    )
                )
            )

            return max(
                0.0,
                min(
                    1.0,
                    score
                )
            )

        except Exception:

            return 0.0

    # =====================================
    # RECENCY
    # =====================================

    def recency_score(
        self,
        timestamp
    ):

        if not timestamp:
            return 0.0

        try:

            date = datetime.fromisoformat(
                timestamp
            )

            if date.tzinfo is None:

                date = date.replace(
                    tzinfo=timezone.utc
                )

            now = datetime.now(
                timezone.utc
            )

            days = max(
                0,
                (
                    now - date
                ).total_seconds()
                / 86400
            )

            return math.exp(
                -days / 120
            )

        except Exception:

            return 0.0

    # =====================================
    # IMPORTANCE
    # =====================================

    def importance_score(
        self,
        memory
    ):

        try:

            value = float(
                memory.get(
                    "importance",
                    0.5
                )
            )

            return max(
                0.0,
                min(
                    1.0,
                    value
                )
            )

        except Exception:

            return 0.5

    # =====================================
    # MEMORY TYPE SCORE
    # =====================================

    def type_score(
        self,
        memory
    ):

        memory_type = memory.get(
            "type",
            "episode"
        )

        weights = {

            "fact": 1.0,

            "explicit_memory": 1.0,

            "preference": 0.95,

            "goal": 0.95,

            "learning": 0.90,

            "episode": 0.75,

            "conversation": 0.70
        }

        return weights.get(
            memory_type,
            0.70
        )

    # =====================================
    # QUERY EMBEDDING
    # =====================================

    def create_query_embedding(
        self,
        query
    ):

        return self.embed(query)

    # =====================================
    # FINAL SCORE
    # =====================================

    def score(
        self,
        query,
        memory,
        query_embedding=None
    ):

        text = (
            memory.get("text")
            or memory.get("user")
            or ""
        )

        keyword = self.keyword_score(
            query,
            text
        )

        semantic = self.semantic_score(
            query_embedding,
            memory.get("embedding")
        )

        recency = self.recency_score(
            memory.get("created_at")
            or memory.get("timestamp")
        )

        importance = self.importance_score(
            memory
        )

        subject = self.subject_score(
            query,
            memory
        )

        type_weight = self.type_score(
            memory
        )

        # =================================
        # HYBRID RETRIEVAL
        # =================================

        base_score = (

            semantic * 0.50

            + keyword * 0.15

            + subject * 0.10

            + recency * 0.05

            + importance * 0.15

            + type_weight * 0.05
        )

        return max(
            0.0,
            min(
                1.0,
                base_score
            )
        )

    # =====================================
    # SEARCH
    # =====================================

    def search(
        self,
        memories,
        query,
        limit=8,
        minimum_score=0.20
    ):

        if not memories:
            return []

        query_embedding = (
            self.create_query_embedding(
                query
            )
        )

        scored = []

        for memory in memories:

            score = self.score(
                query,
                memory,
                query_embedding
            )

            if score < minimum_score:
                continue

            scored.append({

                "score": round(
                    score,
                    4
                ),

                "memory": memory
            })

        scored.sort(
            key=lambda item: item["score"],
            reverse=True
        )

        return scored[:limit]

    # =====================================
    # SEARCH WITH DIVERSITY
    # =====================================

    def search_diverse(
        self,
        memories,
        query,
        limit=8
    ):

        results = self.search(
            memories,
            query,
            limit=limit * 3
        )

        if not results:
            return []

        selected = []

        subjects = set()

        types = set()

        for result in results:

            memory = result["memory"]

            subject = memory.get(
                "subject"
            )

            memory_type = memory.get(
                "type",
                "episode"
            )

            if (
                subject
                and subject in subjects
                and memory_type in types
            ):
                continue

            selected.append(result)

            if subject:
                subjects.add(subject)

            types.add(memory_type)

            if len(selected) >= limit:
                break

        return selected