import json

from backend.learning import tracker_quality
from backend.learning.understanding import UnderstandingTracker


def test_tracker_quality_repairs_malformed_counters_before_update(monkeypatch, tmp_path):
    path = tmp_path / "difficulty.json"
    monkeypatch.setattr(tracker_quality, "_file", lambda: path)
    monkeypatch.setattr(tracker_quality, "_PATCHED", False)
    tracker_quality.install_tracker_quality(UnderstandingTracker)
    path.write_text(json.dumps({
        "mathematics": {
            "easy": "invalid",
            "medium": 2,
            "hard": float("nan"),
            "total": "broken",
            "history": "not-a-list",
        }
    }), encoding="utf-8")

    tracker = UnderstandingTracker()
    assert tracker.update("Mathematics", "easy") is True
    result = tracker.get("Mathematics")

    assert result["easy"] == 1
    assert result["medium"] == 2
    assert result["hard"] == 0
    assert result["total"] == 3
    assert len(result["history"]) == 1
