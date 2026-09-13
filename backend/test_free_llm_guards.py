from backend.free_llm import FreeLLM


def test_latest_message_language_wins_over_profile_language():
    prompt = """Student profile:\nLanguage:\nFrench\n\nStudent's original question:\nwhen was the last time we talked?"""
    assert FreeLLM._detect_language(prompt) == "English"


def test_temporal_memory_hint_uses_previous_conversation_timestamp():
    prompt = """Student's original question:\nwhen was the last time we talked?\n\nRELEVANT PREVIOUS CONVERSATION (0.01 relevance; updated 2026-09-03 13:19 UTC):\n[2026-09-03 13:19 UTC] User: hello"""
    assert FreeLLM._extract_temporal_hint(prompt) == "2026-09-03 13:19 UTC"


def test_response_token_limits_support_detailed_answers():
    assert FreeLLM.RESPONSE_TOKEN_LIMITS["detailed"] >= 6000
