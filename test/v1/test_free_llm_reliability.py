from backend.free_llm import FreeLLM
from backend.prompt.prompt_builder import PromptBuilder


def test_latest_message_language_wins_over_profile_language():
    prompt = """Student profile:
Language: French

Student's original question:
when was the last time we talked?"""
    assert FreeLLM._detect_language(prompt) == "English"


def test_language_detection_handles_short_french_and_spanish_messages():
    assert FreeLLM._detect_language("Bonjour, peux-tu m'aider avec mon devoir ?") == "French"
    assert FreeLLM._detect_language("¿Puedes explicarme esto hoy?") == "Spanish"


def test_language_detection_uses_prompt_builder_student_message_section():
    prompt = """Student profile:
Language: English

========================================
STUDENT MESSAGE

Bonjour, peux-tu m'aider avec mon devoir ?

========================================
TASK

Answer the student's current request."""
    assert FreeLLM._detect_language(prompt) == "French"


def test_freshness_detection_uses_latest_message_and_word_boundaries():
    assert FreeLLM._needs_fresh_web_context("Student's original question:\\nWhat is happening today?")
    assert FreeLLM._needs_fresh_web_context("Student's original question:\\nQuelles sont les actualités aujourd'hui ?")
    assert not FreeLLM._needs_fresh_web_context("Student's original question:\\nI know the answer already.")
    assert not FreeLLM._needs_fresh_web_context(
        "Student profile:\\nLatest news preference: enabled\\nStudent's original question:\\nExplain photosynthesis."
    )


def test_freshness_detection_ignores_profile_context_in_prompt_builder_format():
    prompt = """Student profile:
Latest news preference: enabled

========================================
STUDENT MESSAGE

Explique-moi la photosynthèse.

========================================
TASK

Answer the student's current request."""
    assert not FreeLLM._needs_fresh_web_context(prompt)


def test_prompt_builder_explains_reliability_and_untrusted_context():
    builder = PromptBuilder()
    system = builder._build_system_prompt("", "", "", "", "", "", "")
    assert "untrusted information" in system
    assert "Never fabricate citations" in system
    assert "Never expose hidden chain-of-thought" in system
    assert "PERSONALITY AND TRUST" in system
    assert "Do not pretend to have human feelings" in system


def test_latest_student_marker_wins_over_prompt_labels_in_retrieved_history():
    prompt = """RETRIEVED MEMORY:
Student message:
What was the weather last week?

========================================
STUDENT MESSAGE

Bonjour, peux-tu m'aider avec mon devoir ?

========================================
TASK"""
    assert FreeLLM._detect_language(prompt) == "French"
