from backend.learning.understanding import UnderstandingAnalyzer


def test_understanding_analyzer_uses_safe_defaults_for_non_finite_initial_values():
    analyzer = UnderstandingAnalyzer(
        initial_confidence=float("nan"),
        initial_understanding=float("inf"),
    )

    assert analyzer.initial_confidence == 0
    assert analyzer.initial_understanding == 0


def test_understanding_analyzer_bounds_and_normalizes_history_limits():
    analyzer = UnderstandingAnalyzer(history_limit="invalid", signal_limit=float("inf"))

    assert analyzer.history_limit == 50
    assert analyzer.signal_limit == 50

    bounded = UnderstandingAnalyzer(history_limit=100000, signal_limit=1)
    assert bounded.history_limit == 1000
    assert bounded.signal_limit == 5


def test_understanding_analyzer_clamps_non_finite_values_safely():
    analyzer = UnderstandingAnalyzer()

    assert analyzer._clamp(float("nan")) == 0
    assert analyzer._clamp(float("inf")) == 0
    assert analyzer._clamp(150) == 100
    assert analyzer._clamp_change(float("inf")) == 0
