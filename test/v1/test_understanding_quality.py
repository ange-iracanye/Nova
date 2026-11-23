import json

from backend.learning import understanding_quality


def test_understanding_quality_repairs_partial_subject_records(monkeypatch, tmp_path):
    path = tmp_path / "understanding.json"
    monkeypatch.setattr(understanding_quality, "_file", lambda: path)
    path.write_text(json.dumps({
        "Mathematics": {
            "attempts": "invalid",
            "confidence": float("nan"),
            "understanding": 72,
            "engagement": float("inf"),
            "history": "broken",
            "question_types": {"why": "3", "how": "invalid"},
        }
    }), encoding="utf-8")

    result = understanding_quality._load()["Mathematics"]

    assert result["attempts"] == 0
    assert result["confidence"] == 50
    assert result["understanding"] == 72
    assert result["engagement"] == 50
    assert result["history"] == []
    assert result["question_types"] == {"why": 3, "how": 0}
    assert result["recommended_action"] == "Continue monitoring."


def test_understanding_quality_keeps_valid_learning_history(monkeypatch, tmp_path):
    path = tmp_path / "understanding.json"
    monkeypatch.setattr(understanding_quality, "_file", lambda: path)
    path.write_text(json.dumps({
        "Physics": {
            "attempts": 4,
            "confidence": 82,
            "understanding": 75,
            "engagement": 60,
            "history": [{"confidence": 80}],
            "signals": [{"type": "clarification"}],
        }
    }), encoding="utf-8")

    result = understanding_quality._load()["Physics"]

    assert result["attempts"] == 4
    assert result["confidence"] == 82
    assert result["history"] == [{"confidence": 80}]
    assert result["signals"] == [{"type": "clarification"}]
