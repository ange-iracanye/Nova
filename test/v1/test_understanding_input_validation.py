import json

from backend.learning import understanding_quality
from backend.learning.understanding import UnderstandingAnalyzer


def test_understanding_analyzer_uses_safe_defaults_for_non_finite_initial_values():
    analyzer = UnderstandingAnalyzer(
        initial_confidence=float("nan"),
        initial_understanding=float("inf"),
    )

    assert analyzer.initial_confidence == 0
    assert analyzer.initial_understanding == 0


def test_understanding_analyzer_bounds_and_normalizes_history_limits():
    analyzer = UnderstandingAnalyzer(history_limit="invalid", signal_limit=float("inf"))

    assert analyzer.history_limit == 50
    assert analyzer.signal_limit == 50

    bounded = UnderstandingAnalyzer(history_limit=100000, signal_limit=1)
    assert bounded.history_limit == 1000
    assert bounded.signal_limit == 5


def test_understanding_analyzer_clamps_non_finite_values_safely():
    analyzer = UnderstandingAnalyzer()

    assert analyzer._clamp(float("nan")) == 0
    assert analyzer._clamp(float("inf")) == 0
    assert analyzer._clamp(150) == 100
    assert analyzer._clamp_change(float("inf")) == 0



def test_recent_understanding_history_rejects_malformed_collections(monkeypatch, tmp_path):
    path = tmp_path / "understanding.json"
    monkeypatch.setattr(understanding_quality, "_file", lambda: path)
    monkeypatch.setattr(understanding_quality, "_PATCHED", False)
    path.write_text(json.dumps({"mathematics": {"history": "not-a-list"}}), encoding="utf-8")
    understanding_quality.install_understanding_quality(UnderstandingAnalyzer)
    analyzer = UnderstandingAnalyzer()

    assert analyzer.get_recent_history("mathematics") == []


def test_recent_understanding_history_filters_invalid_entries_and_bounds_limit(monkeypatch, tmp_path):
    path = tmp_path / "understanding.json"
    monkeypatch.setattr(understanding_quality, "_file", lambda: path)
    monkeypatch.setattr(understanding_quality, "_PATCHED", False)
    path.write_text(json.dumps({
        "mathematics": {
            "history": [
                {"confidence": 60},
                "invalid",
                None,
                {"confidence": 80},
            ]
        }
    }), encoding="utf-8")
    understanding_quality.install_understanding_quality(UnderstandingAnalyzer)
    analyzer = UnderstandingAnalyzer()

    assert analyzer.get_recent_history("mathematics", float("inf")) == [
        {"confidence": 60},
        {"confidence": 80},
    ]
