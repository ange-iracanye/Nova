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
