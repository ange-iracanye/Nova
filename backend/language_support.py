"""Language and translation policy helpers for Nova."""

from __future__ import annotations

from typing import Dict, Optional


SUPPORTED_LANGUAGES: Dict[str, str] = {
    "en": "English", "fr": "French", "es": "Spanish", "de": "German",
    "it": "Italian", "pt": "Portuguese", "nl": "Dutch", "pl": "Polish",
    "uk": "Ukrainian", "ru": "Russian", "cs": "Czech", "ro": "Romanian",
    "hu": "Hungarian", "el": "Greek", "sv": "Swedish", "tr": "Turkish",
    "ar": "Arabic", "hi": "Hindi", "zh": "Chinese", "ja": "Japanese",
    "ko": "Korean", "vi": "Vietnamese", "th": "Thai", "id": "Indonesian",
}


def language_name(code: str) -> Optional[str]:
    return SUPPORTED_LANGUAGES.get(str(code or "").strip().lower())


def parse_translation_mode(mode: object) -> Optional[str]:
    value = str(mode or "").strip().lower()
    if not value.startswith("translation:"):
        return None
    code = value.split(":", 1)[1].strip()
    return code if code in SUPPORTED_LANGUAGES else None


def build_language_policy(mode: object) -> str:
    """Return a high-priority output-language instruction.

    The latest user message is intentionally authoritative. Conversation memory
    can contain older messages in another language, but it must never make Nova
    switch languages for the current request.
    """
    target = parse_translation_mode(mode)

    if target:
        name = SUPPORTED_LANGUAGES[target]
        return (
            "HIGHEST-PRIORITY LANGUAGE RULE: TRANSLATION MODE IS ACTIVE. "
            f"Translate the user's requested content into {name}. "
            "Do not answer the underlying question instead of translating it. "
            "Preserve meaning, tone, formatting, lists, markdown, numbers, URLs, "
            "code, formulas, proper nouns, and placeholders whenever applicable. "
            "Do not add commentary before or after the translation unless requested."
        )

    return (
        "HIGHEST-PRIORITY OUTPUT LANGUAGE RULE: The language of the LATEST USER MESSAGE "
        "controls the language of this response. Detect it from the latest user message "
        "itself. Previous conversation messages, memory, the user's saved profile, the "
        "interface/UI language, translation settings, and the language used by Nova in "
        "older turns MUST NOT override the latest user's language. If the latest message "
        "is English, answer entirely in English. If it is French, answer entirely in French, "
        "and so on. If the latest message mixes languages, use the language of its main request. "
        "Do not translate merely because an older turn used another language. Keep technical "
        "terms, code, formulas, URLs, and proper nouns intact unless translation is required."
    )
