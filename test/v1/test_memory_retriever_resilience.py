from backend.memory_system.memory_retriever import MemoryRetriever


class _MemoryStore:
    def __init__(self, data):
        self.data = data
        self.saved = None

    def load(self, user_email):
        return self.data

    def save(self, user_email, data):
        self.saved = data


class _Embedder:
    def encode(self, query):
        return [1.0, 0.0]


def test_memory_retriever_cosine_rejects_mismatched_and_non_finite_vectors():
    retriever = MemoryRetriever(None, None)

    assert retriever.cosine([1.0, 0.0], [1.0]) == 0.0
    assert retriever.cosine([float("nan")], [1.0]) == 0.0
    assert retriever.cosine([1.0, 0.0], [1.0, 0.0]) == 1.0


def test_memory_retriever_search_skips_malformed_records_and_bounds_limit():
    store = _MemoryStore({
        "facts": [
            None,
            "broken",
            {"content": "Algebra", "embedding": [1.0, 0.0], "importance": 80},
        ],
        "goals": "not-a-list",
    })
    retriever = MemoryRetriever(store, _Embedder())

    result = retriever.search("student@example.com", "algebra", limit=10000)

    assert len(result) == 1
    assert result[0]["access_count"] == 1
    assert store.saved is not None
    assert retriever.search("student@example.com", "algebra", limit=-1) == []


def test_memory_retriever_search_handles_embedder_failures():
    class BrokenEmbedder:
        def encode(self, query):
            raise RuntimeError("embedding service unavailable")

    store = _MemoryStore({"facts": [{"content": "Algebra", "embedding": [1.0]}]})
    retriever = MemoryRetriever(store, BrokenEmbedder())

    assert retriever.search("student@example.com", "algebra") == []


def test_memory_retriever_recency_accepts_naive_iso_timestamps():
    retriever = MemoryRetriever(None, None)

    score = retriever.recency_score("2026-11-23T12:00:00")

    assert 0.0 <= score <= 1.0



def test_memory_retriever_search_handles_provider_specific_exceptions():
    class ProviderError(Exception):
        pass

    class UnavailableEmbedder:
        def encode(self, query):
            raise ProviderError("provider is unavailable")

    store = _MemoryStore({"facts": [{"content": "Algebra", "embedding": [1.0]}]})
    retriever = MemoryRetriever(store, UnavailableEmbedder())

    assert retriever.search("student@example.com", "algebra") == []
    assert store.saved is None
