import math
from datetime import datetime, timezone


class MemoryRetriever:

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

        if not a or not b:
            return 0.0


        dot = sum(
            x * y
            for x, y in zip(a, b)
        )


        norm_a = math.sqrt(
            sum(x * x for x in a)
        )

        norm_b = math.sqrt(
            sum(x * x for x in b)
        )


        if norm_a == 0 or norm_b == 0:
            return 0.0


        return dot / (
            norm_a * norm_b
        )


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

            now = datetime.now(
                timezone.utc
            )

            days = (
                now - created
            ).total_seconds() / 86400


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

        importance = (
            memory.get(
                "importance",
                50
            ) / 100
        )


        confidence = (
            memory.get(
                "confidence",
                1
            )
        )


        recency = (
            self.recency_score(
                memory.get(
                    "created_at"
                )
            )
        )


        access = min(
            memory.get(
                "access_count",
                0
            ) / 10,
            1
        )


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

        memory = (
            self.memory_manager
            .load(user_email)
        )


        query_embedding = (
            self.embedding_model
            .encode(query)
            .tolist()
        )


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

            for item in memory.get(
                category,
                []
            ):

                content = item.get(
                    "content",
                    ""
                )


                if not content:
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


            memory_item[
                "access_count"
            ] = (
                memory_item.get(
                    "access_count",
                    0
                ) + 1
            )


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