"""Language and translation policy helpers for Nova.

This module intentionally contains no third-party dependency.  Language choice
is enforced at the LLM instruction layer so it works with both the local and
hosted Nova providers without adding another network service or package.
"""

from __future__ import annotations

from typing import Dict, Optional


SUPPORTED_LANGUAGES: Dict[str, str] = {
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "pl": "Polish",
    "uk": "Ukrainian",
    "ru": "Russian",
    "cs": "Czech",
    "ro": "Romanian",
    "hu": "Hungarian",
    "el": "Greek",
    "sv": "Swedish",
    "tr": "Turkish",
    "ar": "Arabic",
    "hi": "Hindi",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "vi": "Vietnamese",
    "th": "Thai",
    "id": "Indonesian",
}


def language_name(code: str) -> Optional[str]:
    """Return a safe human-readable language name for an ISO-like code."""
    return SUPPORTED_LANGUAGES.get(str(code or "").strip().lower())


def parse_translation_mode(mode: object) -> Optional[str]:
    """Extract a supported target code from ``translation:<code>`` mode."""
    value = str(mode or "").strip().lower()
    if not value.startswith("translation:"):
        return None
    code = value.split(":", 1)[1].strip()
    return code if code in SUPPORTED_LANGUAGES else None


def build_language_policy(mode: object) -> str:
    """Build the response-language policy injected into every Nova prompt."""
    target = parse_translation_mode(mode)

    if target:
        name = SUPPORTED_LANGUAGES[target]
        return (
            f"TRANSLATION MODE: Translate the user's requested content into {name}. "
            "Preserve meaning, tone, formatting, lists, markdown, numbers, URLs, "
            "code, formulas, proper nouns, and placeholders whenever applicable. "
            "Do not answer the underlying question instead of translating it. "
            "Do not add commentary before or after the translation unless the user asks for it."
        )

    return (
        "LANGUAGE POLICY: Reply in the same natural language used by the user's "
        "latest message. Detect the language from the message itself, not from "
        "the interface language or account settings. If the message contains "
        "multiple languages, use the language of the user's main request. "
        "Keep technical terms, code, formulas, URLs, and proper nouns intact "
        "unless translating them is necessary for the requested answer."
    )
