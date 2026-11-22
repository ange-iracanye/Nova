import hashlib
import json

from backend.learning_graph import LearningGraph


def _user_file(tmp_path, email):
    uid = hashlib.sha256(email.encode("utf-8")).hexdigest()
    return tmp_path / "data" / "learning" / "users" / f"{uid}.json"


def test_learning_graph_repairs_malformed_subject_and_topic_buckets(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    email = "student@example.com"
    path = _user_file(tmp_path, email)
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({
        "version": 3,
        "subjects": {
            "Mathematics": "broken",
            "Physics": {"mastery": 20, "topics": "broken"},
        },
    }), encoding="utf-8")

    graph = LearningGraph(email)
    graph.add_topic("Mathematics", "Algebra")
    graph.update_topic("Mathematics", "Algebra", True)
    graph.add_topic("Physics", "Motion")
    graph.update_topic("Physics", "Motion", False)

    result = graph.get()["subjects"]
    assert result["Mathematics"]["topics"]["Algebra"]["times_studied"] == 1
    assert result["Physics"]["topics"]["Motion"]["wrong_answers"] == 1


def test_learning_graph_synthesis_safely_handles_malformed_progress(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    email = "student@example.com"
    progress_dir = tmp_path / "data" / "memory" / "progress"
    progress_dir.mkdir(parents=True)
    uid = hashlib.sha256(email.encode("utf-8")).hexdigest()
    (progress_dir / f"{uid}.json").write_text(json.dumps({
        "Mathematics": {
            "Algebra": {"attempts": "invalid", "confidence": "nan"},
            "Geometry": {"attempts": 3, "confidence": 80},
        }
    }), encoding="utf-8")

    graph = LearningGraph(email).get()["subjects"]["Mathematics"]["topics"]
    assert graph["Algebra"]["times_studied"] == 0
    assert graph["Algebra"]["mastery"] == 0
    assert graph["Geometry"]["times_studied"] == 3
    assert graph["Geometry"]["mastery"] == 80
