from backend.free_llm import FreeLLM


def test_internal_safety_response_is_rejected():
    assert FreeLLM._is_internal_response("User Safety: safe") is True
    assert FreeLLM._is_internal_response("Safety: unsafe") is True
    assert FreeLLM._is_internal_response("Here is the answer.") is False


def test_internal_safety_response_is_retried_before_returning():
    llm = FreeLLM(model="test:free", max_retries=1, retry_delay=0)
    responses = iter(["User Safety: safe", "The answer is 4."])

    llm._generate = lambda system, user, settings, model: next(responses)

    result = llm.answer(
        system="You are Nova.",
        user="What is 2 + 2?",
        creativity="medium",
    )

    assert result == "The answer is 4."
    assert llm.successful_requests == 1
    assert llm.failed_requests == 0
