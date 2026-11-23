from backend.memory_system.memory_extractor import MemoryExtractor


def test_memory_extractor_ignores_non_text_inputs():
    extractor = MemoryExtractor()

    assert extractor.extract(None) == []
    assert extractor.extract(123) == []
    assert extractor.extract({}) == []
    assert extractor.extract("   ") == []


def test_memory_extractor_bounds_large_input_and_preserves_extraction():
    extractor = MemoryExtractor()
    message = "I prefer concise explanations. " + ("extra words " * 3000)

    result = extractor.extract(message)

    assert result
    assert result[0]["text"] == "concise explanations"
    assert len(result) <= 1
