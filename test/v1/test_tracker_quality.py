import json

from backend.learning import tracker_quality


def test_tracker_quality_rejects_non_mapping_history(monkeypatch, tmp_path):
    path = tmp_path / "difficulty.json"
    monkeypatch.setattr(tracker_quality, "_file", lambda: path)
    path.write_text(json.dumps(["broken"]), encoding="utf-8")

    assert tracker_quality._load() == {}


def test_tracker_quality_filters_malformed_subject_records(monkeypatch, tmp_path):
    path = tmp_path / "difficulty.json"
    monkeypatch.setattr(tracker_quality, "_file", lambda: path)
    path.write_text(json.dumps({
        "Mathematics": {"easy": 2, "medium": 1},
        "broken": "not-an-object",
    }), encoding="utf-8")

    assert tracker_quality._load() == {
        "Mathematics": {"easy": 2, "medium": 1}
    }


def test_tracker_quality_sanitizes_non_finite_values_on_save(monkeypatch, tmp_path):
    path = tmp_path / "difficulty.json"
    monkeypatch.setattr(tracker_quality, "_file", lambda: path)

    tracker_quality._save({
        "Mathematics": {"easy": float("nan"), "history": [float("inf"), 2]},
    })

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved == {
        "Mathematics": {"easy": None, "history": [None, 2]}
    }
