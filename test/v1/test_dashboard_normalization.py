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
