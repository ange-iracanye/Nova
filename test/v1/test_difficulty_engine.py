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
