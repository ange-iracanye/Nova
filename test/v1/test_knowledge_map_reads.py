from backend.student.knowledge_map import KnowledgeMap


def test_knowledge_map_reads_are_safe_for_malformed_subject_buckets(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    knowledge = KnowledgeMap()
    knowledge.map = {
        "mathematics": "broken",
        "physics": {"motion": {"confidence": 70, "attempts": 2}},
    }

    assert knowledge.get_topic("mathematics", "algebra") is None
    assert knowledge.get_subject("mathematics") == {}
    assert knowledge.get_topic("physics", "motion")["confidence"] == 70
    assert knowledge.remove_topic("mathematics", "algebra") is False


def test_knowledge_map_subject_confidence_ignores_non_finite_values(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    knowledge = KnowledgeMap()
    knowledge.map = {
        "mathematics": {
            "invalid": {"confidence": float("nan")},
            "infinite": {"confidence": float("inf")},
            "algebra": {"confidence": 80},
            "geometry": {"confidence": 60},
        }
    }

    assert knowledge.get_subject_confidence("mathematics") == 70
