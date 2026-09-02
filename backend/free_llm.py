"""Zero-cost public LLM adapter for Nova V1.

OpenRouter is used because its current free tier is available to users 13+
and does not require paid credits. Nova pins a strong free reasoning model
first, then falls back to OpenRouter's free-model router if that model is
unavailable. No paid model is ever requested by this adapter.
"""

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

    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    DEFAULT_MODEL = "nvidia/nemotron-3-ultra:free"
    FREE_ROUTER_MODEL = "openrouter/free"

    # Provider/model metadata occasionally leaks into the generated text.
    # It is never a valid Nova answer and must not reach the user interface.
    INTERNAL_RESPONSE_PATTERNS = (
        re.compile(r"^user\s+safety\s*:\s*(?:safe|unsafe|unknown)\s*$", re.I),
        re.compile(r"^assistant\s+safety\s*:\s*(?:safe|unsafe|unknown)\s*$", re.I),
        re.compile(r"^safety\s*:\s*(?:safe|unsafe|unknown)\s*$", re.I),
    )

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
        key = str(creativity).strip().lower()
        return dict(self.CREATIVITY_SETTINGS.get(key, self.CREATIVITY_SETTINGS["medium"]))

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
        """Return True when a provider leaked an internal safety/meta field."""
        value = str(text or "").strip()
        if not value:
            return True
        return any(pattern.fullmatch(value) for pattern in cls.INTERNAL_RESPONSE_PATTERNS)

    def _generate(self, system: str, user: str, settings: Dict[str, Any], model: str) -> str:
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY is not configured.")

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": settings["temperature"],
            "top_p": settings["top_p"],
        }
        request = Request(
            self.API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.getenv("NOVA_PUBLIC_URL", "https://nova.onrender.com"),
                "X-Title": "Nova AI Tutor",
            },
            method="POST",
        )
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
            error_detail = data.get("error") or "no choices"
            raise RuntimeError(f"OpenRouter returned no choices: {error_detail}")

        message = choices[0].get("message") or {}
        text = str(message.get("content", "")).strip()
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
        last_error: Optional[Exception] = None
        models = [self.model]
        if self.fallback_model and self.fallback_model != self.model:
            models.append(self.fallback_model)

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


# ============================================================
# PUBLIC DEMO CORE
# ============================================================
#
# The public demo uses the exact same NovaCore orchestration and the exact
# same TutorEngine/NovaBrain/LLM stack as authenticated Nova. The only thing
# removed is persistent memory. This subclass is installed before production
# imports backend.api, so /demo/session receives this implementation when it
# calls NovaCore(demo=True).
#
# Demo conversations remain in-memory through ConversationManager(persist=False)
# and the demo-specific stages in NovaCore already skip long-term memory.
# ============================================================

from backend.core.nova_core import NovaCore as _BaseNovaCore
import backend.core.nova_core as _nova_core_module


class DemoNovaCore(_BaseNovaCore):
    """NovaCore with the same brain/model but no memory subsystem."""

    def _initialize_memory(self) -> None:
        # Do not construct MemoryManager or LearningMemory for demo sessions.
        self.memory = None
        self.learning_memory = None

    def _stage_learning_memory(self, request) -> None:
        # The demo must not create or update long-term learning memory.
        return


# backend.api imports NovaCore directly from backend.core.nova_core.
# Replace that exported class before production.py imports the API module.
_nova_core_module.NovaCore = DemoNovaCore
