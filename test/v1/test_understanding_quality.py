import json

from backend.learning import understanding_quality


def test_understanding_quality_rejects_malformed_history_root(monkeypatch, tmp_path):
    path = tmp_path / "understanding.json"
    monkeypatch.setattr(understanding_quality, "_file", lambda: path)
    path.write_text(json.dumps(["invalid"]), encoding="utf-8")

    assert understanding_quality._load() == {}


def test_understanding_quality_filters_invalid_records_and_global_key(monkeypatch, tmp_path):
    path = tmp_path / "understanding.json"
    monkeypatch.setattr(understanding_quality, "_file", lambda: path)
    path.write_text(json.dumps({
        "Mathematics": {"confidence": 80},
        "broken": "not-a-record",
        "__global__": {"private": True},
    }), encoding="utf-8")

    assert understanding_quality._load() == {
        "Mathematics": {"confidence": 80}
    }


def test_understanding_quality_sanitizes_non_finite_values_on_save(monkeypatch, tmp_path):
    path = tmp_path / "understanding.json"
    monkeypatch.setattr(understanding_quality, "_file", lambda: path)

    understanding_quality._save({
        "Mathematics": {"confidence": float("nan"), "history": [float("inf"), 80]},
        "__global__": {"ignored": True},
    })

    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved == {
        "Mathematics": {"confidence": None, "history": [None, 80]}
    }
