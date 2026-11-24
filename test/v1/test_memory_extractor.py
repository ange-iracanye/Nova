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


def test_memory_extractor_recognizes_french_preferences_and_goals():
    extractor = MemoryExtractor()

    result = extractor.extract(
        "Je préfère les explications courtes. "
        "Mon objectif est d'apprendre les mathématiques. "
        "J'aime les exercices pratiques."
    )

    assert [(item["type"], item["text"]) for item in result] == [
        ("preference", "les explications courtes"),
        ("goal", "apprendre les mathématiques"),
        ("preference", "les exercices pratiques"),
    ]


def test_memory_extractor_recognizes_french_explicit_memories():
    extractor = MemoryExtractor()

    result = extractor.extract("Souviens-toi que je révise le français chaque soir.")

    assert len(result) == 1
    assert result[0]["type"] == "explicit_memory"
    assert result[0]["text"] == "je révise le français chaque soir"


def test_memory_extractor_recognizes_french_student_facts():
    extractor = MemoryExtractor()

    result = extractor.extract(
        "Je m'appelle Camille. J'étudie la biologie. "
        "J'habite à Lyon. J'utilise un ordinateur portable."
    )

    assert [(item["type"], item["text"]) for item in result] == [
        ("fact", "Camille"),
        ("fact", "la biologie"),
        ("fact", "Lyon"),
        ("fact", "un ordinateur portable"),
    ]


def test_memory_extractor_recognizes_french_intentions():
    extractor = MemoryExtractor()

    result = extractor.extract("J'essaie de mieux organiser mes révisions.")

    assert len(result) == 1
    assert result[0]["type"] == "goal"
    assert result[0]["text"] == "mieux organiser mes révisions"
