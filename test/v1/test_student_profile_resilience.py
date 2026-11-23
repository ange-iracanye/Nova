import hashlib
import json

from student_profile import StudentProfile


def test_student_profile_repairs_question_counters_and_topic_lists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    profile = StudentProfile("counter-test@example.com")
    profile.profile["questions_asked"] = "not-a-number"
    profile.profile["topics_seen"] = "broken"
    profile.save()

    profile.add_question("Algebra")

    assert profile.profile["questions_asked"] == 1
    assert profile.profile["topics_seen"] == ["Algebra"]


def test_student_profile_learning_snapshot_ignores_non_finite_confidence(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    email = "profile-test@example.com"
    progress_dir = tmp_path / "data" / "memory" / "progress"
    progress_dir.mkdir(parents=True)
    user_id = hashlib.sha256(email.encode("utf-8")).hexdigest()
    (progress_dir / f"{user_id}.json").write_text(json.dumps({
        "Mathematics": {
            "Algebra": {"confidence": float("inf")},
            "Geometry": {"confidence": 85},
            "Fractions": {"confidence": "invalid"},
        }
    }), encoding="utf-8")

    profile = StudentProfile(email)
    snapshot = profile.get()

    assert snapshot["strengths"] == ["Mathematics / Geometry"]
    assert snapshot["weaknesses"] == []


def test_student_profile_question_count_is_safe_for_large_invalid_values(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    profile = StudentProfile("infinite-counter@example.com")
    profile.profile["questions_asked"] = float("inf")
    profile.save()

    assert profile.get()["questions"] == 0



def test_student_profile_repairs_malformed_profile_fields(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    profile = StudentProfile("profile-repair@example.com")
    profile.profile.update({
        "name": "   ",
        "level": None,
        "questions_asked": "bad",
        "topics_seen": [" Algebra ", "algebra", None, 7, "Geometry"],
        "strengths": "broken",
        "weaknesses": ["Physics", "", "physics"],
    })
    profile.save()

    snapshot = profile.get()

    assert snapshot["name"] == "Student"
    assert snapshot["level"] == "beginner"
    assert snapshot["questions"] == 0
    assert snapshot["topics_seen"] == ["Algebra", "Geometry"]
    assert snapshot["strengths"] == []
    assert snapshot["weaknesses"] == ["Physics"]


def test_student_profile_add_question_deduplicates_topics_case_insensitively(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    profile = StudentProfile("topic-dedupe@example.com")

    profile.add_question("Algebra")
    profile.add_question(" algebra ")

    assert profile.profile["questions_asked"] == 2
    assert profile.profile["topics_seen"] == ["Algebra"]


def test_student_profile_get_returns_detached_snapshot(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    profile = StudentProfile("profile-snapshot@example.com")
    snapshot = profile.get()
    snapshot["topics_seen"].append("Injected")

    assert "Injected" not in profile.get()["topics_seen"]



def test_student_profile_sanitizes_non_finite_extra_fields_on_save(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    profile = StudentProfile("profile-nan@example.com")
    profile.profile["legacy_metrics"] = {
        "confidence": float("nan"),
        "history": [float("inf"), 75],
    }

    profile.save()

    saved = json.loads(profile._file().read_text(encoding="utf-8"))
    assert saved["legacy_metrics"] == {
        "confidence": None,
        "history": [None, 75],
    }
