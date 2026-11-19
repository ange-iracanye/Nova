from backend.free_llm import FreeLLM


def test_latest_message_language_wins_over_profile_language():
    prompt = """Student profile:\nLanguage:\nFrench\n\nStudent's original question:\nwhen was the last time we talked?"""
    assert FreeLLM._detect_language(prompt) == "English"


def test_temporal_memory_hint_uses_previous_conversation_timestamp():
    prompt = """Student's original question:\nwhen was the last time we talked?\n\nRELEVANT PREVIOUS CONVERSATION (0.01 relevance; updated 2026-09-03 13:19 UTC):\n[2026-09-03 13:19 UTC] User: hello"""
    assert FreeLLM._extract_temporal_hint(prompt) == "2026-09-03 13:19 UTC"


def test_response_token_limits_support_detailed_answers():
    assert FreeLLM.RESPONSE_TOKEN_LIMITS["detailed"] >= 6000


def test_language_detection_handles_short_french_and_spanish_messages():
    assert FreeLLM._detect_language("Bonjour, peux-tu m'aider avec mon devoir ?") == "French"
    assert FreeLLM._detect_language("¿Puedes explicarme esto hoy?") == "Spanish"


def test_freshness_detection_uses_latest_message_and_word_boundaries():
    assert FreeLLM._needs_fresh_web_context("Student's original question:\nWhat is happening today?")
    assert FreeLLM._needs_fresh_web_context("Student's original question:\nQuelles sont les actualités aujourd'hui ?")
    assert not FreeLLM._needs_fresh_web_context("Student's original question:\nI know the answer already.")
    assert not FreeLLM._needs_fresh_web_context("Student profile:\nLatest news preference: enabled\nStudent's original question:\nExplain photosynthesis.")


def test_language_detection_uses_latest_message_from_prompt_builder_format():
    prompt = """Student profile:
Language: English

========================================
STUDENT MESSAGE

Bonjour, peux-tu m'aider avec mon devoir ?

========================================
TASK

Answer the student's current request."""
    assert FreeLLM._detect_language(prompt) == "French"


def test_freshness_detection_ignores_profile_context_when_prompt_builder_format_is_used():
    prompt = """Student profile:
Latest news preference: enabled

========================================
STUDENT MESSAGE

Explique-moi la photosynthèse.

========================================
TASK

Answer the student's current request."""
    assert not FreeLLM._needs_fresh_web_context(prompt)
