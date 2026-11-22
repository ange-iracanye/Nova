from copy import deepcopy

from backend.dashboard import _canonical_progress


def test_canonical_progress_merges_aliases_without_mutating_input():
    source = {
        "python": {
            "Foundations": {
                "attempts": 2,
                "confidence": 40,
                "mastered": False,
                "last_seen": "2026-01-01",
            }
        },
        "quantum computing": {
            "Foundations": {
                "attempts": 3,
                "confidence": 80,
                "mastered": True,
                "last_seen": "2026-02-01",
            }
        },
    }
    original = deepcopy(source)

    merged = _canonical_progress(source)

    assert merged["Technology"]["Foundations"]["attempts"] == 5
    assert merged["Technology"]["Foundations"]["confidence"] == 64
    assert merged["Technology"]["Foundations"]["mastered"] is True
    assert merged["Technology"]["Foundations"]["last_seen"] == "2026-02-01"
    assert source == original


def test_canonical_progress_keeps_distinct_topics_separate():
    merged = _canonical_progress({
        "French": {"Verb agreement": {"attempts": 1, "confidence": 55}},
        "Spanish": {"Past tense": {"attempts": 2, "confidence": 70}},
    })

    assert set(merged["Languages"]) == {"Verb agreement", "Past tense"}



def test_canonical_progress_returns_empty_mapping_for_non_object_input():
    assert _canonical_progress(None) == {}
    assert _canonical_progress(["not", "a", "mapping"]) == {}


def test_dashboard_normalization_skips_malformed_graph_topics():
    from backend.dashboard import _canonical_graph

    assert _canonical_graph({
        "subjects": {
            "Mathematics": {"topics": ["invalid", "topic data"]},
            "Physics": {"topics": None},
            "Biology": None,
        }
    }) == {
        "subjects": {
            "Mathematics": {"mastery": 0.0, "topics": {}},
            "Physics": {"mastery": 0.0, "topics": {}},
            "Biology": {"mastery": 0.0, "topics": {}},
        }
    }


def test_dashboard_clamp_replaces_non_finite_values_with_lower_bound():
    from backend.dashboard import _clamp

    assert _clamp(float("nan")) == 0.0
    assert _clamp(float("inf")) == 0.0
    assert _clamp(150) == 100.0
