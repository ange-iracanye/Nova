import json

from backend.memory_system.memory_manager import MemoryManager, _safe_unit_value


def _manager(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("NOVA_ENABLE_SEMANTIC_MEMORY", "false")
    monkeypatch.setenv("NOVA_CONVERSATIONS_FILE", "data/conversations.json")
    return MemoryManager(base_path=tmp_path / "memory")


def test_memory_manager_normalizes_non_finite_importance_and_confidence(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)

    memory = manager.add_memory(
        "student@example.com",
        "I am learning algebra",
        confidence=float("nan"),
        importance=float("inf"),
        metadata="not-a-dictionary",
    )

    assert 0.0 <= memory["confidence"] <= 1.0
    assert 0.0 <= memory["importance"] <= 1.0
    assert isinstance(memory["metadata"], dict)


def test_memory_manager_skips_malformed_memory_records(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    data = manager.default_memory()
    data["memories"] = [
        None,
        "broken",
        {"text": "algebra practice", "importance": 0.8, "type": "learning"},
    ]
    path = manager.user_file("student@example.com")
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(data), encoding="utf-8")

    loaded = manager.load("student@example.com")
    assert len(loaded["memories"]) == 1
    results = manager.search("student@example.com", "algebra")

    assert len(results) == 1
    assert results[0]["memory"]["text"] == "algebra practice"


def test_memory_manager_repairs_invalid_recall_count(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    memory = manager.add_memory("student@example.com", "Algebra revision")
    memory["recall_count"] = "invalid"
    manager._write(manager.user_file("student@example.com"), {
        **manager.default_memory(),
        "memories": [memory],
    })

    result = manager.add_memory("student@example.com", "Algebra revision")
    assert result["recall_count"] == 1



def test_memory_unit_value_helper_rejects_non_finite_values():
    assert _safe_unit_value(float("nan"), 0.8) == 0.8
    assert _safe_unit_value(float("inf"), 0.5) == 0.5
    assert _safe_unit_value(140, 0.5) == 1.0



def test_memory_manager_remember_normalizes_invalid_confidence(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    manager.extractor.extract = lambda *args, **kwargs: []

    manager.remember(
        "student@example.com",
        "I am revising geometry",
        "We reviewed triangles",
        confidence=float("nan"),
    )

    stored = manager.load("student@example.com")["memories"]
    assert stored[0]["confidence"] == 0.7


def test_memory_manager_remember_clamps_percentage_confidence(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    manager.extractor.extract = lambda *args, **kwargs: []

    manager.remember(
        "student@example.com",
        "I am revising geometry",
        "We reviewed triangles",
        confidence=140,
    )

    stored = manager.load("student@example.com")["memories"]
    assert stored[0]["confidence"] == 1.0



def test_memory_manager_persists_strict_json_for_legacy_non_finite_values(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)
    path = manager.user_file("strict-json@example.com")
    manager._write(path, {
        "score": float("nan"),
        "metadata": {"legacy": float("inf")},
    })

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved == {"score": None, "metadata": {"legacy": None}}


def test_memory_manager_rejects_invalid_identity_and_memory_payloads(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)

    assert manager.add_memory(None, "Algebra revision") is None
    assert manager.add_memory("student@example.com", 123) is None
    assert manager.add_memory("student@example.com", "Algebra", memory_type="unknown") is None
    assert manager.add_memory("   ", "Algebra revision") is None


def test_memory_manager_bounds_persisted_memory_text(tmp_path, monkeypatch):
    manager = _manager(tmp_path, monkeypatch)

    memory = manager.add_memory(
        "STUDENT@example.com",
        "x" * 25000,
        formatted_text="y" * 25000,
    )

    assert memory is not None
    assert len(memory["text"]) == 20000
    assert manager.user_file("student@example.com").exists()
