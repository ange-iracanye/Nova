from backend.memory_system.memory_consolidator import MemoryConsolidator


class DummyStudentMemory:
    def __init__(self):
        self.memory = {
            "preferences": "broken",
            "progress": {
                "Mathematics": {
                    "observations": "broken",
                    "attempts": "invalid",
                    "confidence": float("nan"),
                }
            },
        }
        self.facts = []
        self.explicit = []
        self.saved = 0

    def add_fact(self, text, subject=None, confidence=0.8):
        self.facts.append((text, subject, confidence))

    def add_explicit_memory(self, text, subject=None):
        self.explicit.append((text, subject))

    def set_preference(self, key, value):
        self.memory["preferences"].append({key: value})

    def save(self):
        self.saved += 1


def test_consolidator_rejects_malformed_memory_payloads():
    consolidator = MemoryConsolidator(DummyStudentMemory())

    assert consolidator.consolidate(None) is False
    assert consolidator.consolidate("not-a-record") is False
    assert consolidator.consolidate({"type": "learning", "text": "  "}) is False


def test_consolidator_repairs_learning_records_before_appending():
    memory = DummyStudentMemory()
    consolidator = MemoryConsolidator(memory)

    assert consolidator.consolidate({
        "type": "learning",
        "text": "Reviewed linear equations",
    }, subject="Mathematics") is True

    data = memory.memory["progress"]["Mathematics"]
    assert data["observations"] == ["Reviewed linear equations"]
    assert data["attempts"] == 1
    assert data["confidence"] == 50
    assert memory.saved == 1


def test_consolidator_normalizes_fact_confidence_and_preferences():
    memory = DummyStudentMemory()
    consolidator = MemoryConsolidator(memory)

    assert consolidator.consolidate({
        "type": "fact",
        "text": "Student studies biology",
        "confidence": float("inf"),
    }, subject="Biology") is True
    assert memory.facts[0][2] == 0.8

    assert consolidator.consolidate({
        "type": "preference",
        "text": "Short explanations",
    }) is True
    assert isinstance(memory.memory["preferences"], list)
    assert memory.memory["preferences"][0] == {"preference_0": "Short explanations"}
