import hashlib
import json

from student_profile import StudentProfile


def test_student_profile_repairs_question_counters_and_topic_lists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    profile = StudentProfile()
    profile.profile["questions_asked"] = "not-a-number"
    profile.profile["topics_seen"] = "broken"

    profile.add_question("Algebra")

    assert profile.profile["questions_asked"] == 1
    assert profile.profile["topics_seen"] == ["Algebra"]


def test_student_profile_learning_snapshot_ignores_non_finite_confidence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    progress_dir = tmp_path / "data" / "memory" / "progress"
    progress_dir.mkdir(parents=True)
    (progress_dir / "default.json").write_text(json.dumps({
        "Mathematics": {
            "Algebra": {"confidence": float("inf")},
            "Geometry": {"confidence": 85},
            "Fractions": {"confidence": "invalid"},
        }
    }), encoding="utf-8")

    profile = StudentProfile()
    snapshot = profile.get()

    assert snapshot["strengths"] == ["Mathematics / Geometry"]
    assert snapshot["weaknesses"] == []


def test_student_profile_question_count_is_safe_for_large_invalid_values(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    profile = StudentProfile()
    profile.profile["questions_asked"] = float("inf")

    assert profile.get()["questions"] == 0
