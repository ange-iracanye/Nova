from backend.memory_system.memory_search import MemorySearch


def test_semantic_score_rejects_vectors_with_different_dimensions():
    search = MemorySearch()

    assert search.semantic_score([0.5, 0.5, 0.5], [0.5, 0.5]) == 0.0


def test_semantic_score_rejects_non_numeric_and_non_finite_values():
    search = MemorySearch()

    assert search.semantic_score([0.5, "not-a-number"], [0.5, 0.5]) == 0.0
    assert search.semantic_score([float("inf")], [1.0]) == 0.0


def test_semantic_score_keeps_valid_normalized_vectors():
    search = MemorySearch()

    assert search.semantic_score([0.6, 0.8], [0.6, 0.8]) == 1.0
    assert search.semantic_score([1.0, 0.0], [-1.0, 0.0]) == 0.0



def test_importance_score_uses_default_for_non_finite_values():
    search = MemorySearch()

    assert search.importance_score({"importance": float("nan")}) == 0.5
    assert search.importance_score({"importance": float("inf")}) == 0.5
    assert search.importance_score({"importance": "invalid"}) == 0.5


def test_search_skips_malformed_memories_and_validates_limits():
    search = MemorySearch()

    results = search.search(
        [None, "broken", {"text": "algebra practice", "importance": 0.8}],
        "algebra",
        limit=5,
        minimum_score=0,
    )

    assert len(results) == 1
    assert results[0]["memory"]["text"] == "algebra practice"
    assert search.search([{"text": "algebra"}], "algebra", limit=-1) == []
    assert search.search([{"text": "algebra"}], "algebra", limit="invalid") == []
    assert search.search([{"text": "algebra"}], "algebra", limit=0) == []


def test_search_clamps_invalid_minimum_score():
    search = MemorySearch()

    assert search.search([{"text": "algebra"}], "algebra", minimum_score=float("nan"))
    assert search.search([{"text": "algebra"}], "algebra", minimum_score=2) == []



def test_diverse_search_validates_limit_before_expanding_candidates():
    search = MemorySearch()
    memories = [{"text": "algebra practice", "subject": "Mathematics"}]

    assert search.search_diverse(memories, "algebra", limit="invalid") == []
    assert search.search_diverse(memories, "algebra", limit=-3) == []
    assert search.search_diverse(memories, "algebra", limit=0) == []
    assert len(search.search_diverse(memories, "algebra", limit=1)) == 1
