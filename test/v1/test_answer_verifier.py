from backend.learning.answer_verifier import AnswerVerifier


def test_answer_verifier_corrects_incorrect_fibonacci_claim():
    verifier = AnswerVerifier()

    assert verifier.verify(
        "What is Fibonacci(8)?",
        "Fibonacci(8) is 20.",
    ) == "Fibonacci(8) = 21."


def test_answer_verifier_preserves_correct_claims_and_unrelated_answers():
    verifier = AnswerVerifier()

    correct = "Fibonacci(8) equals 21."
    assert verifier.verify("Fibonacci(8)", correct) == correct
    assert verifier.verify("Explain gravity", "Gravity attracts masses.") == (
        "Gravity attracts masses."
    )


def test_answer_verifier_handles_invalid_input_types():
    verifier = AnswerVerifier()

    assert verifier.verify(None, "answer") == "answer"
    assert verifier.verify("Fibonacci(8)", None) is None
    assert verifier.verify(123, 456) == 456


def test_answer_verifier_skips_excessively_large_fibonacci_indices():
    verifier = AnswerVerifier()

    assert verifier.verify(
        "Fibonacci(100000000)",
        "The result is 0.",
    ) == "The result is 0."
