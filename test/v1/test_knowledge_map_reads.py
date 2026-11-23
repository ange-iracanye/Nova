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



def test_knowledge_map_topic_lists_exclude_non_finite_confidence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    knowledge = KnowledgeMap()
    knowledge.map = {
        "mathematics": {
            "infinite": {"confidence": float("inf")},
            "nan": {"confidence": float("nan")},
            "weak": {"confidence": 20},
            "strong": {"confidence": 90},
        }
    }

    weak = knowledge.get_weak_topics()
    strong = knowledge.get_strong_topics()

    assert [item["topic"] for item in weak] == ["weak"]
    assert [item["topic"] for item in strong] == ["strong"]
    assert strong[0]["confidence"] == 90


def test_knowledge_map_category_results_return_normalized_confidence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    knowledge = KnowledgeMap()
    knowledge.map = {
        "mathematics": {
            "algebra": {"confidence": 140, "category": "mastery"},
            "invalid": {"confidence": float("nan"), "category": "mastery"},
        }
    }

    results = knowledge.get_topics_by_category("mastery")

    assert len(results) == 1
    assert results[0]["confidence"] == 100



def test_knowledge_map_read_methods_return_detached_data(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    knowledge = KnowledgeMap()
    knowledge.map = {
        "mathematics": {
            "algebra": {
                "confidence": 75,
                "history": [{"score": 80}],
            }
        }
    }

    topic = knowledge.get_topic("mathematics", "algebra")
    subject = knowledge.get_subject("mathematics")
    topic["history"][0]["score"] = 0
    subject["algebra"]["confidence"] = 0

    stored = knowledge.map["mathematics"]["algebra"]
    assert stored["confidence"] == 75
    assert stored["history"][0]["score"] == 80
