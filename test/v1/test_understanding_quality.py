import json

from backend.learning import understanding_quality
from backend.learning.understanding import UnderstandingAnalyzer


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



def test_understanding_reset_subject_persists_deletion(monkeypatch, tmp_path):
    path = tmp_path / "understanding.json"
    monkeypatch.setattr(understanding_quality, "_file", lambda: path)
    monkeypatch.setattr(understanding_quality, "_PATCHED", False)
    understanding_quality.install_understanding_quality(UnderstandingAnalyzer)
    analyzer = UnderstandingAnalyzer()
    analyzer.analyze("Mathematics", "Can you explain algebra?", "Algebra uses variables.")

    assert "Mathematics" in understanding_quality._load()
    assert analyzer.reset_subject("Mathematics") is True
    assert "Mathematics" not in understanding_quality._load()


def test_understanding_reset_persists_clearing_all_subjects(monkeypatch, tmp_path):
    path = tmp_path / "understanding.json"
    monkeypatch.setattr(understanding_quality, "_file", lambda: path)
    monkeypatch.setattr(understanding_quality, "_PATCHED", False)
    understanding_quality.install_understanding_quality(UnderstandingAnalyzer)
    analyzer = UnderstandingAnalyzer()
    analyzer.analyze("Mathematics", "Can you explain algebra?", "Algebra uses variables.")
    analyzer.analyze("Physics", "How does gravity work?", "Gravity is a force.")

    analyzer.reset()

    assert understanding_quality._load() == {}



def test_understanding_import_persists_validated_data_for_current_student(monkeypatch, tmp_path):
    path = tmp_path / "understanding.json"
    import_path = tmp_path / "import.json"
    monkeypatch.setattr(understanding_quality, "_file", lambda: path)
    monkeypatch.setattr(understanding_quality, "_PATCHED", False)
    import_path.write_text(json.dumps({
        "Mathematics": {
            "attempts": 3,
            "confidence": 85,
            "history": [{"confidence": 80}],
        },
        "__global__": {"attempts": 999},
    }), encoding="utf-8")
    understanding_quality.install_understanding_quality(UnderstandingAnalyzer)
    analyzer = UnderstandingAnalyzer()

    assert analyzer.import_data(import_path) is True
    saved = understanding_quality._load()
    assert saved["Mathematics"]["confidence"] == 85
    assert "__global__" not in saved


def test_understanding_import_rejects_invalid_utf8_without_replacing_state(monkeypatch, tmp_path):
    path = tmp_path / "understanding.json"
    import_path = tmp_path / "invalid.json"
    monkeypatch.setattr(understanding_quality, "_file", lambda: path)
    monkeypatch.setattr(understanding_quality, "_PATCHED", False)
    understanding_quality.install_understanding_quality(UnderstandingAnalyzer)
    analyzer = UnderstandingAnalyzer()
    analyzer.analyze("Physics", "How does gravity work?", "Gravity is a force.")
    before = understanding_quality._load()
    import_path.write_bytes(b"\xff\xfe")

    assert analyzer.import_data(import_path) is False
    assert understanding_quality._load() == before
