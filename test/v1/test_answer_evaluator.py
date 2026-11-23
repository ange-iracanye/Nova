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



def test_evaluator_supports_common_math_topic_aliases():
    evaluator = AnswerEvaluator()

    assert evaluator.evaluate("Algebra", "The equation has a variable.") == 40
    assert evaluator.evaluate("calculus", "A derivative is a rate of change.") == 20


def test_evaluator_supports_additional_school_subjects():
    evaluator = AnswerEvaluator()

    assert evaluator.evaluate("chemistry", "An atom has an electron and proton.") == 40
    assert evaluator.evaluate("history", "The revolution changed the empire.") == 40
    assert evaluator.evaluate("geography", "The river crosses the country.") == 40
    assert evaluator.evaluate("computer science", "An algorithm uses a loop.") == 40


def test_evaluator_supports_french_subject_aliases():
    evaluator = AnswerEvaluator()

    assert evaluator.evaluate("chimie", "An atom is part of a molecule.") == 40
    assert evaluator.evaluate("géographie", "A continent has many countries.") == 40
