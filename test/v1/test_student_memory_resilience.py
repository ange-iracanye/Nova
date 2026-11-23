import json

from backend.memory_system.student_memory import StudentMemory


def test_student_memory_repairs_non_object_root_and_malformed_collections(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    memory = StudentMemory("student@example.com")
    memory.file.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")

    repaired = StudentMemory("student@example.com")

    assert isinstance(repaired.memory["concepts_learned"], dict)
    assert repaired.memory["mistakes"] == []
    assert repaired.memory["facts"] == []
    assert repaired.memory["statistics"]["total_concepts"] == 0


def test_student_memory_save_repairs_invalid_nested_records_and_non_finite_values(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    memory = StudentMemory("student@example.com")
    memory.memory["concepts_learned"] = {
        "Mathematics": {
            "Algebra": {"confidence": float("nan"), "attempts": 2},
            "broken": "not-a-record",
        }
    }
    memory.memory["facts"] = [{"text": "A fact", "confidence": float("inf")}]
    memory.memory["statistics"] = "broken"

    memory.save()
    saved = json.loads(memory.file.read_text(encoding="utf-8"))

    assert saved["concepts_learned"]["Mathematics"] == {
        "Algebra": {"confidence": None, "attempts": 2}
    }
    assert saved["facts"][0]["confidence"] is None
    assert saved["statistics"]["total_concepts"] == 1



def test_student_memory_normalizes_existing_concept_counters_and_scores(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    memory = StudentMemory("concepts@example.com")
    memory.memory["concepts_learned"] = {
        "Mathematics": {
            "Algebra": {
                "confidence": float("nan"),
                "attempts": "broken",
                "first_seen": "2026-01-01",
            }
        }
    }
    memory.save()
    restored = StudentMemory("concepts@example.com")
    restored.learn_concept("Mathematics", "Algebra", float("inf"))

    concept = restored.memory["concepts_learned"]["Mathematics"]["Algebra"]
    assert concept["confidence"] == 50
    assert concept["attempts"] == 1
    assert concept["first_seen"] == "2026-01-01"



def test_student_memory_get_returns_detached_snapshot(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    memory = StudentMemory("snapshot@example.com")
    snapshot = memory.get()
    snapshot["facts"].append({"text": "injected"})

    assert memory.get()["facts"] == []
