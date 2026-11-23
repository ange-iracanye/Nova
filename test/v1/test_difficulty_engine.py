import math

from backend.learning.difficulty_engine import DifficultyEngine


def test_performance_normalization_rejects_non_finite_numbers():
    engine = DifficultyEngine()

    assert engine.normalize_performance(float("nan")) is None
    assert engine.normalize_performance(float("inf")) is None
    assert engine.normalize_performance(float("-inf")) is None
    assert engine.normalize_performance(True) is None


def test_performance_normalization_accepts_fractions_and_percentages():
    engine = DifficultyEngine()

    assert engine.normalize_performance(0.85) == 85
    assert engine.normalize_performance(85) == 85
    assert engine.normalize_performance({"accuracy": 0.92}) == 92


def test_performance_normalization_clamps_finite_out_of_range_values():
    engine = DifficultyEngine()

    assert engine.normalize_performance(140) == 100
    assert engine.normalize_performance(-5) == 0


def test_confidence_normalization_remains_finite():
    engine = DifficultyEngine()

    assert math.isfinite(engine.normalize_confidence(float("nan")))
    assert engine.normalize_confidence(float("nan")) == engine.DEFAULT_CONFIDENCE



def test_performance_normalization_accepts_numeric_strings():
    engine = DifficultyEngine()

    assert engine.normalize_performance("85") == 85
    assert engine.normalize_performance("0.85") == 85
    assert engine.normalize_performance("not-a-number") is None



def test_difficulty_engine_caps_history_and_signal_work():
    engine = DifficultyEngine(max_history=10**9)

    assert engine.max_history == engine.MAX_HISTORY_LIMIT
    result = engine.analyze_signals({"confusion": 10**9})
    assert len(result["signals"]) == engine.MAX_SIGNALS_PER_DECISION
    assert result["score"] == -20


def test_difficulty_engine_signal_sets_are_deterministic():
    engine = DifficultyEngine()
    first = engine.analyze_signals({"success", "confusion", "understanding"})
    second = engine.analyze_signals({"understanding", "success", "confusion"})

    assert first == second
    assert first["signals"] == ["confusion", "success", "understanding"]


def test_difficulty_engine_level_steps_handle_invalid_and_unbounded_values():
    engine = DifficultyEngine()

    assert engine.increase_level("beginner", float("inf")) == "intermediate"
    assert engine.reduce_level("mastery", "invalid") == "advanced"
    assert engine.increase_level("beginner", 10**9) == "mastery"


def test_difficulty_engine_caps_large_signal_collections():
    engine = DifficultyEngine()
    result = engine.analyze_signals(["confusion"] * 5000)

    assert len(result["signals"]) == engine.MAX_SIGNALS_PER_DECISION
    assert result["score"] == -20
