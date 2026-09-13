"""Zero-cost public LLM adapter for Nova V1."""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class FreeLLM:
    """OpenRouter free-model adapter used by public V1."""

    CREATIVITY_SETTINGS = {
        "low": {"temperature": 0.2, "top_p": 0.85},
        "medium": {"temperature": 0.5, "top_p": 0.9},
        "high": {"temperature": 0.8, "top_p": 0.95},
    }
    RESPONSE_TOKEN_LIMITS = {
        "short": 1800,
        "concise": 1800,
        "balanced": 3500,
        "long": 5500,
        "detailed": 6500,
    }
    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    DEFAULT_MODEL = "nvidia/nemotron-3-ultra:free"
    FREE_ROUTER_MODEL = "openrouter/free"
    FRESHNESS_TERMS = {"today", "now", "currently", "current", "latest", "recent", "recently", "happening", "news", "breaking", "this week", "this month", "yesterday"}
    INTERNAL_RESPONSE_PATTERNS = (
        re.compile(r"^user\s+safety\s*:\s*(?:safe|unsafe|unknown)\s*$", re.I),
        re.compile(r"^assistant\s+safety\s*:\s*(?:safe|unsafe|unknown)\s*$", re.I),
        re.compile(r"^safety\s*:\s*(?:safe|unsafe|unknown)\s*$", re.I),
    )
    LANGUAGE_WORDS = {
        "English": {"the", "is", "are", "when", "what", "how", "why", "last", "time", "talked", "please", "make", "about", "and", "with", "from"},
        "French": {"le", "la", "les", "des", "est", "sont", "quand", "quoi", "comment", "pourquoi", "dernier", "dernière", "fois", "parlé", "fait", "avec", "dans", "première", "guerre"},
        "Spanish": {"el", "la", "los", "las", "es", "son", "cuando", "qué", "cómo", "por", "qué", "última", "vez", "hablamos", "hacer", "con", "guerra"},
        "German": {"der", "die", "das", "ist", "sind", "wann", "was", "wie", "warum", "letzte", "zeit", "gesprochen", "machen", "mit", "krieg"},
        "Italian": {"il", "lo", "la", "gli", "le", "è", "sono", "quando", "cosa", "come", "perché", "ultima", "volta", "parlato", "fare", "con", "guerra"},
        "Portuguese": {"o", "a", "os", "as", "é", "são", "quando", "que", "como", "porquê", "última", "vez", "falamos", "fazer", "com", "guerra"},
    }

    def __init__(self, model: Optional[str] = None, max_retries: int = 1, retry_delay: float = 1.0):
        self.model = model or os.getenv("NOVA_LLM_MODEL", self.DEFAULT_MODEL)
        self.fallback_model = os.getenv("NOVA_LLM_FALLBACK_MODEL", self.FREE_ROUTER_MODEL)
        self.api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.max_retries = max(0, int(max_retries))
        self.retry_delay = max(0.0, float(retry_delay))
        self.last_error = None
        self.last_response = None
        self.last_generation_time = None
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

    def get_generation_settings(self, creativity: str = "medium") -> Dict[str, float]:
        return dict(self.CREATIVITY_SETTINGS.get(str(creativity).strip().lower(), self.CREATIVITY_SETTINGS["medium"]))

    def get_temperature(self, creativity: str = "medium") -> float:
        return self.get_generation_settings(creativity)["temperature"]

    def set_model(self, model: str) -> None:
        if not isinstance(model, str) or not model.strip():
            raise ValueError("Model name cannot be empty.")
        value = model.strip()
        if value != self.FREE_ROUTER_MODEL and not value.endswith(":free"):
            raise ValueError("Public Nova may only use an OpenRouter free model.")
        self.model = value

    def get_model(self) -> str:
        return self.model

    @classmethod
    def _is_internal_response(cls, text: str) -> bool:
        value = str(text or "").strip()
        return not value or any(pattern.fullmatch(value) for pattern in cls.INTERNAL_RESPONSE_PATTERNS)

    @classmethod
    def _extract_latest_message(cls, user: str) -> str:
        text = str(user or "")
        markers = ("Student's original question:", "Student message:")
        for marker in markers:
            if marker in text:
                value = text.rsplit(marker, 1)[1]
                value = value.split("\n\nFRESH WEB CONTEXT", 1)[0]
                return value.strip()
        return text.strip()

    @classmethod
    def _detect_language(cls, user: str) -> str:
        latest = cls._extract_latest_message(user)
        tokens = set(re.findall(r"\b[\wÀ-ÿ]+\b", latest.lower()))
        scores = {language: len(tokens & words) for language, words in cls.LANGUAGE_WORDS.items()}
        best = max(scores, key=scores.get)
        if scores[best] == 0:
            # Strong script signals cover languages where word overlap is unreliable.
            if re.search(r"[\u4e00-\u9fff]", latest): return "Chinese"
            if re.search(r"[\u3040-\u30ff]", latest): return "Japanese"
            if re.search(r"[\uac00-\ud7af]", latest): return "Korean"
            if re.search(r"[\u0600-\u06ff]", latest): return "Arabic"
            return "English"
        return best

    @classmethod
    def _is_temporal_query(cls, user: str) -> bool:
        latest = cls._extract_latest_message(user).lower()
        tokens = set(re.findall(r"\b[\wÀ-ÿ]+\b", latest))
        temporal = {"when", "last", "previous", "earlier", "before", "date", "time", "talked", "talk", "conversation", "chat", "history", "quand", "dernière", "derniere", "fois", "parlé", "parle", "conversation"}
        return bool(tokens & temporal) or "last time" in latest or "dernière fois" in latest

    @classmethod
    def _extract_temporal_hint(cls, user: str) -> str:
        if not cls._is_temporal_query(user): return ""
        matches = re.findall(r"RELEVANT PREVIOUS CONVERSATION.*?updated ([0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2} UTC)", str(user or ""), flags=re.I | re.S)
        if not matches: return ""
        return matches[0]

    @classmethod
    def _needs_fresh_web_context(cls, user: str) -> bool:
        text = str(user or "").lower()
        if any(term in text for term in cls.FRESHNESS_TERMS): return True
        return bool(re.search(r"\bwhat(?:'s| is) happening\b", text) or re.search(r"\bwhat happened\b", text))

    @classmethod
    def _fetch_web_context(cls, user: str) -> str:
        if not cls._needs_fresh_web_context(user): return ""
        try:
            from ddgs import DDGS
            with DDGS() as ddgs:
                results = list(ddgs.text(cls._extract_latest_message(user), max_results=5))
            if not results: return ""
            lines = []
            for item in results:
                title = str(item.get("title") or "").strip()
                body = str(item.get("body") or "").strip()
                href = str(item.get("href") or "").strip()
                if body: lines.append(f"SOURCE: {title}\nURL: {href}\nSNIPPET: {body}")
            return "\n\n".join(lines)[:7000]
        except Exception:
            return ""

    def _generate(self, system: str, user: str, settings: Dict[str, Any], model: str) -> str:
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured.")
        response_length = str(settings.get("response_length", "balanced")).strip().lower()
        max_tokens = self.RESPONSE_TOKEN_LIMITS.get(response_length, self.RESPONSE_TOKEN_LIMITS["balanced"])
        payload = {
            "model": model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": settings["temperature"],
            "top_p": settings["top_p"],
            "max_tokens": max_tokens,
        }
        request = Request(self.API_URL, data=json.dumps(payload).encode("utf-8"), headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "HTTP-Referer": os.getenv("NOVA_PUBLIC_URL", "https://nova.onrender.com"), "X-Title": "Nova AI Tutor"}, method="POST")
        try:
            with urlopen(request, timeout=90) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:1200]
            raise RuntimeError(f"OpenRouter API HTTP {error.code}: {detail}") from error
        except URLError as error:
            raise RuntimeError(f"OpenRouter connection failed: {error.reason}") from error
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError(f"OpenRouter returned no choices: {data.get('error') or 'no choices'}")
        text = str((choices[0].get("message") or {}).get("content", "")).strip()
        if self._is_internal_response(text):
            raise RuntimeError("OpenRouter returned an internal safety/meta response instead of an assistant answer.")
        return text

    def answer(self, system: str, user: str, creativity: str = "medium") -> str:
        if not isinstance(system, str) or not system.strip():
            raise ValueError("System prompt cannot be empty.")
        if not isinstance(user, str) or not user.strip():
            raise ValueError("User prompt cannot be empty.")
        settings = self.get_generation_settings(creativity)
        self.total_requests += 1
        started = time.perf_counter()
        original_user = user

        latest_language = self._detect_language(original_user)
        language_rule = (
            "CRITICAL OUTPUT LANGUAGE RULE: The language of the student's latest actual message is authoritative. "
            f"The latest message was detected as {latest_language}. Respond entirely in {latest_language}. "
            "Do not switch to the saved UI/profile language and do not copy the language of older memory."
        )
        system = f"{system}\n\n{language_rule}"

        temporal_hint = self._extract_temporal_hint(original_user)
        if temporal_hint:
            system = f"{system}\n\nTEMPORAL MEMORY RULE: A previous conversation timestamp is present in the supplied memory. " \
                     f"The most recent previous conversation timestamp available to Nova is {temporal_hint}. " \
                     "Use that timestamp directly for questions asking when the user last talked to Nova. " \
                     "Do not claim that timestamps are unavailable."

        web_context = self._fetch_web_context(original_user)
        if web_context:
            user = f"{original_user}\n\nFRESH WEB CONTEXT (retrieved for this request):\n{web_context}\n\nUse this context for current/fresh facts. Do not invent facts not supported by it. If sources disagree, say so. Do not mention this internal context unless useful to explain sourcing."
            system = f"{system}\n\nFRESHNESS RULE: Live web context is attached to the user request. Prefer it over stale memory for current events, while still following the latest-message language rule."

        last_error: Optional[Exception] = None
        models = [self.model] + ([self.fallback_model] if self.fallback_model and self.fallback_model != self.model else [])
        for model in models:
            for attempt in range(self.max_retries + 1):
                try:
                    text = self._generate(system, user, settings, model)
                    self.last_response = text
                    self.last_generation_time = time.perf_counter() - started
                    self.last_error = None
                    self.successful_requests += 1
                    return text
                except Exception as error:
                    last_error = error
                    self.last_error = str(error)
                    if attempt < self.max_retries:
                        time.sleep(self.retry_delay * (attempt + 1))
        self.failed_requests += 1
        raise RuntimeError(f"Nova's free AI provider failed: {last_error}") from last_error
