import json

from backend.learning_graph import LearningGraph


def test_learning_graph_repairs_malformed_nested_records(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    graph = LearningGraph("graph-repair@example.com")
    path = graph._user_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({
        "version": 2,
        "subjects": {
            "Mathematics": {
                "mastery": float("nan"),
                "topics": {
                    "Algebra": {
                        "mastery": float("inf"),
                        "times_studied": "bad",
                        "correct_answers": 3,
                        "wrong_answers": 1,
                        "last_review": None,
                    },
                    "broken": "not-a-record",
                },
            },
            "broken": "not-a-subject",
        },
    }), encoding="utf-8")

    result = graph.get()

    assert result["version"] == 3
    assert result["subjects"]["Mathematics"]["mastery"] == 0
    assert result["subjects"]["Mathematics"]["topics"]["Algebra"] == {
        "mastery": 0,
        "times_studied": 4,
        "correct_answers": 3,
        "wrong_answers": 1,
        "last_review": "",
    }
    assert "broken" not in result["subjects"]["Mathematics"]["topics"]


def test_learning_graph_update_normalizes_names_and_boolean_strings(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    graph = LearningGraph("graph-update@example.com")

    assert graph.update_topic(" Mathematics ", " Algebra ", "false") is True
    result = graph.get()["subjects"]["Mathematics"]["topics"]["Algebra"]

    assert result["times_studied"] == 1
    assert result["correct_answers"] == 0
    assert result["wrong_answers"] == 1


def test_learning_graph_rejects_empty_topic_and_returns_snapshot(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    graph = LearningGraph("graph-snapshot@example.com")

    assert graph.update_topic("Mathematics", "  ", True) is False
    graph.add_topic("Mathematics", "Algebra")
    snapshot = graph.get()
    snapshot["subjects"]["Mathematics"]["topics"]["Algebra"]["mastery"] = 99

    assert graph.get()["subjects"]["Mathematics"]["topics"]["Algebra"]["mastery"] == 0
