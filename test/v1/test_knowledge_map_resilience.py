import json

from backend.student.knowledge_map import KnowledgeMap


def test_knowledge_map_uses_safe_confidence_for_non_finite_inputs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    knowledge = KnowledgeMap()

    knowledge.update("Mathematics", "NaN", float("nan"))
    knowledge.update("Mathematics", "Infinity", float("inf"))
    knowledge.update("Mathematics", "Invalid", "not-a-number")

    topics = knowledge.get()["mathematics"]
    for topic in ("nan", "infinity", "invalid"):
        assert topics[topic]["confidence"] == 50
        assert topics[topic]["category"] == "developing"


def test_knowledge_map_repairs_malformed_subject_and_topic_entries(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "data" / "memory" / "knowledge_maps" / "default.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({
        "mathematics": "broken",
        "physics": {"motion": "broken"},
    }), encoding="utf-8")

    knowledge = KnowledgeMap()
    knowledge.update("Mathematics", "Algebra", 80)
    knowledge.update("Physics", "Motion", 70)

    assert knowledge.get_topic("mathematics", "algebra")["attempts"] == 1
    assert knowledge.get_topic("physics", "motion")["attempts"] == 1


def test_knowledge_map_recovers_from_invalid_utf8(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    path = tmp_path / "data" / "memory" / "knowledge_maps" / "default.json"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"\xff\xfe")

    knowledge = KnowledgeMap()
    knowledge.update("Biology", "Cells", 75)

    assert knowledge.get_topic("biology", "cells")["confidence"] == 75
