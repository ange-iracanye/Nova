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



def test_evaluator_recognizes_french_answers_for_supported_subjects():
    evaluator = AnswerEvaluator()

    assert evaluator.evaluate("mathématiques", "Une équation contient une variable.") == 40
    assert evaluator.evaluate("physique", "La gravité agit sur la masse et le mouvement.") == 60
    assert evaluator.evaluate("biologie", "La cellule contient de l'ADN.") == 40
    assert evaluator.evaluate("chimie", "Une molécule contient un atome et une liaison.") == 60



def test_evaluator_does_not_double_count_duplicate_translated_keywords():
    evaluator = AnswerEvaluator()

    assert evaluator.evaluate("physics", "The force acts on the mass.") == 40
    assert evaluator.evaluate("math", "A fraction is part of mathematics.") == 20
