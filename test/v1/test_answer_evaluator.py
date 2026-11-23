from backend.learning.answer_evaluator import AnswerEvaluator


def test_answer_evaluator_matches_whole_words_not_substrings():
    evaluator = AnswerEvaluator()

    assert evaluator.evaluate("biology", "The excellent result was surprising.") == 0
    assert evaluator.evaluate("biology", "A cell is the basic unit of life.") == 20


def test_answer_evaluator_normalizes_topic_aliases_and_case():
    evaluator = AnswerEvaluator()

    assert evaluator.evaluate("Mathematics", "An EQUATION uses a VARIABLE.") == 40
    assert evaluator.evaluate("physique", "Force and mass create motion.") == 60


def test_answer_evaluator_handles_missing_and_unknown_inputs():
    evaluator = AnswerEvaluator()

    assert evaluator.evaluate(None, "some answer") == 50
    assert evaluator.evaluate("unknown subject", "gravity and energy") == 0
    assert evaluator.evaluate("physics", None) == 0
    assert evaluator.evaluate("physics", 123) == 0


def test_answer_evaluator_caps_score_at_one_hundred():
    evaluator = AnswerEvaluator()

    assert evaluator.evaluate(
        "physics",
        "gravity, force, mass, energy and motion",
    ) == 100
