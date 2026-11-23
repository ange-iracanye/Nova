import math
from datetime import datetime, timezone


class MemoryRetriever:
    MAX_RESULTS = 50

    @staticmethod
    def _number(value, default=0.0):
        try:
            number = float(value)
        except (TypeError, ValueError, OverflowError):
            return default
        return number if math.isfinite(number) else default

    @staticmethod
    def _count(value):
        try:
            return max(0, int(value or 0))
        except (TypeError, ValueError, OverflowError):
            return 0

    def __init__(
        self,
        memory_manager,
        embedding_model
    ):

        self.memory_manager = (
            memory_manager
        )

        self.embedding_model = (
            embedding_model
        )


    # =====================================
    # COSINE
    # =====================================

    def cosine(
        self,
        a,
        b
    ):

        if a is None or b is None:
            return 0.0

        try:
            if len(a) != len(b) or len(a) == 0:
                return 0.0
            vector_a = [float(value) for value in a]
            vector_b = [float(value) for value in b]
            if not all(math.isfinite(value) for value in vector_a + vector_b):
                return 0.0

            dot = math.fsum(x * y for x, y in zip(vector_a, vector_b))
            norm_a = math.sqrt(math.fsum(x * x for x in vector_a))
            norm_b = math.sqrt(math.fsum(y * y for y in vector_b))
            if norm_a == 0 or norm_b == 0:
                return 0.0

            score = dot / (norm_a * norm_b)
            if not math.isfinite(score):
                return 0.0
            return max(-1.0, min(1.0, score))
        except (TypeError, ValueError, OverflowError):
            return 0.0


    # =====================================
    # RECENCY
    # =====================================

    def recency_score(
        self,
        timestamp
    ):

        if not timestamp:
            return 0.1


        try:

            created = datetime.fromisoformat(
                timestamp
            )

            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            days = max(0.0, (now - created).total_seconds() / 86400)


            return max(
                0.05,
                math.exp(
                    -days / 180
                )
            )

        except Exception:

            return 0.1


    # =====================================
    # SCORE
    # =====================================

    def score(
        self,
        semantic,
        memory
    ):

        if not isinstance(memory, dict):
            return 0.0

        semantic = max(-1.0, min(1.0, self._number(semantic)))
        importance = max(0.0, min(1.0, self._number(memory.get("importance", 50), 50) / 100))
        confidence = self._number(memory.get("confidence", 1), 1)
        if confidence > 1:
            confidence /= 100
        confidence = max(0.0, min(1.0, confidence))
        recency = self.recency_score(memory.get("created_at"))
        access = min(self._count(memory.get("access_count")) / 10, 1.0)


        return (

            semantic * 0.55

            +

            importance * 0.20

            +

            confidence * 0.10

            +

            recency * 0.10

            +

            access * 0.05
        )


    # =====================================
    # SEARCH
    # =====================================

    def search(
        self,
        user_email,
        query,
        limit=12
    ):

        try:
            limit = int(limit)
        except (TypeError, ValueError, OverflowError):
            return []
        if limit <= 0:
            return []
        limit = min(limit, self.MAX_RESULTS)
        if not isinstance(query, str) or not query.strip():
            return []

        try:
            memory = self.memory_manager.load(user_email)
            if not isinstance(memory, dict):
                return []
            encoded = self.embedding_model.encode(query)
            query_embedding = encoded.tolist() if hasattr(encoded, "tolist") else list(encoded)
        except (AttributeError, TypeError, ValueError, RuntimeError):
            return []

        candidates = []


        categories = [

            "facts",
            "preferences",
            "goals",
            "relationships",
            "events",
            "mistakes",
            "episodes",
            "summaries"
        ]


        for category in categories:

            items = memory.get(category, [])
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict):
                    continue

                content = item.get("content", "")
                if not isinstance(content, str) or not content.strip():
                    continue


                embedding = item.get(
                    "embedding"
                )


                if not embedding:

                    continue


                semantic = self.cosine(
                    query_embedding,
                    embedding
                )


                final_score = self.score(
                    semantic,
                    item
                )


                candidates.append({

                    "score":
                        final_score,

                    "memory":
                        item
                })


        candidates.sort(
            key=lambda x:
                x["score"],
            reverse=True
        )


        results = []


        for item in candidates[:limit]:

            memory_item = item[
                "memory"
            ]


            memory_item["access_count"] = self._count(memory_item.get("access_count")) + 1


            memory_item[
                "last_accessed"
            ] = datetime.now(
                timezone.utc
            ).isoformat()


            results.append(
                memory_item
            )


        self.memory_manager.save(
            user_email,
            memory
        )


        return results