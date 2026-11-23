import json

from backend.learning.progress_tracker import ProgressTracker


def test_progress_tracker_recovers_from_non_object_json(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    progress_file = tmp_path / "data" / "memory" / "progress" / "default.json"
    progress_file.parent.mkdir(parents=True)
    progress_file.write_text('["not", "a", "progress", "object"]', encoding="utf-8")

    tracker = ProgressTracker()

    assert tracker.get() == {}
    tracker.update("Mathematics", "Algebra", 75)
    assert tracker.get()["Mathematics"]["Algebra"]["attempts"] == 1


def test_progress_tracker_merges_malformed_legacy_counters_safely(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    progress_file = tmp_path / "data" / "memory" / "progress" / "default.json"
    progress_file.parent.mkdir(parents=True)
    progress_file.write_text(json.dumps({
        "python": {
            "Basics": {
                "attempts": "invalid",
                "confidence": "nan",
                "difficulty_easy": "invalid",
            }
        },
        "quantum computing": {
            "Basics": {
                "attempts": 2,
                "confidence": 80,
                "difficulty_medium": "2",
            }
        },
    }), encoding="utf-8")

    tracker = ProgressTracker()
    topic = tracker.get()["Technology"]["Basics"]

    assert topic["attempts"] == 2
    assert topic["confidence"] == 80
    assert topic["difficulty_easy"] == 0
    assert topic["difficulty_medium"] == 2


def test_progress_tracker_update_repairs_malformed_topic_values(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    progress_file = tmp_path / "data" / "memory" / "progress" / "default.json"
    progress_file.parent.mkdir(parents=True)
    progress_file.write_text(json.dumps({
        "Mathematics": {"Algebra": "broken"}
    }), encoding="utf-8")

    tracker = ProgressTracker()
    tracker.update("Mathematics", "Algebra", 90)

    topic = tracker.get()["Mathematics"]["Algebra"]
    assert topic["attempts"] == 1
    assert topic["confidence"] == 62.0



def test_progress_tracker_update_uses_safe_default_for_non_finite_confidence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = ProgressTracker()

    tracker.update("Mathematics", "NaN input", float("nan"))
    tracker.update("Mathematics", "Infinite input", float("inf"))
    tracker.update("Mathematics", "Invalid input", "not-a-number")

    progress = tracker.get()["Mathematics"]
    assert progress["NaN input"]["confidence"] == 50.0
    assert progress["Infinite input"]["confidence"] == 50.0
    assert progress["Invalid input"]["confidence"] == 50.0


def test_progress_tracker_update_clamps_finite_confidence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = ProgressTracker()

    tracker.update("Mathematics", "Low", -20)
    tracker.update("Mathematics", "High", 140)

    progress = tracker.get()["Mathematics"]
    assert progress["Low"]["confidence"] == 35.0
    assert progress["High"]["confidence"] == 65.0



def test_progress_tracker_recovers_from_invalid_utf8_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    progress_file = tmp_path / "data" / "memory" / "progress" / "default.json"
    progress_file.parent.mkdir(parents=True)
    progress_file.write_bytes(b"\xff\xfe\xfa")

    tracker = ProgressTracker()

    assert tracker.get() == {}
    tracker.update("Physics", "Motion", 70)
    assert tracker.get()["Physics"]["Motion"]["attempts"] == 1


def test_progress_tracker_repairs_malformed_alias_topic_during_merge(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    progress_file = tmp_path / "data" / "memory" / "progress" / "default.json"
    progress_file.parent.mkdir(parents=True)
    progress_file.write_text(json.dumps({
        "tech": {"Basics": "broken"},
        "python": {"Basics": {"attempts": 2, "confidence": 70}},
    }), encoding="utf-8")

    tracker = ProgressTracker()

    topic = tracker.get()["Technology"]["Basics"]
    assert topic["attempts"] == 2
    assert topic["confidence"] == 70



def test_progress_tracker_repairs_non_mapping_topic_data(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = ProgressTracker("repair-topic@example.com")
    tracker.progress = {
        "Mathematics": {
            "broken": "not-an-object",
            "valid": {"attempts": 2, "confidence": 75},
        }
    }

    tracker._merge_subject_aliases()

    assert tracker.progress["Mathematics"]["broken"] == {}
    assert tracker.progress["Mathematics"]["valid"]["confidence"] == 75


def test_progress_tracker_get_returns_an_independent_snapshot(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = ProgressTracker("snapshot@example.com")
    tracker.update("Mathematics", "Algebra", 80)

    snapshot = tracker.get()
    snapshot["Mathematics"]["Algebra"]["confidence"] = 0
    snapshot["Physics"] = {}

    assert tracker.get()["Mathematics"]["Algebra"]["confidence"] != 0
    assert "Physics" not in tracker.progress



def test_progress_tracker_sanitizes_non_finite_legacy_metadata_on_save(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = ProgressTracker("nan-metadata@example.com")
    tracker.progress = {
        "Mathematics": {
            "Algebra": {
                "attempts": 1,
                "confidence": 70,
                "legacy_score": float("nan"),
                "metadata": {"old_value": float("inf")},
            }
        }
    }

    tracker.update("Mathematics", "Algebra", 80)

    saved = json.loads(tracker.file.read_text(encoding="utf-8"))
    topic = saved["Mathematics"]["Algebra"]
    assert topic["legacy_score"] is None
    assert topic["metadata"]["old_value"] is None



def test_progress_tracker_persists_repair_of_malformed_subject_buckets(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    tracker = ProgressTracker("broken-bucket@example.com")
    tracker.progress = {
        "Mathematics": "not-a-topic-map",
        "Physics": {
            "Motion": {"attempts": 2, "confidence": 70},
            "invalid-topic": None,
        },
    }
    tracker._save()

    result = tracker.get()

    assert result == {
        "Mathematics": {},
        "Physics": {"Motion": {"attempts": 2, "confidence": 70}},
    }
    assert json.loads(tracker.file.read_text(encoding="utf-8")) == result
