"""Production runtime optimizations for Nova.

This module is deliberately small and opt-in. It upgrades the existing LocalLLM
without changing TutorEngine's public API: the configured OLLAMA_MODEL is used
and repeated safe prompts are served from a bounded in-process cache.
"""

from __future__ import annotations

import os
import threading
from typing import Any

from backend.fast_response_pipeline import FastResponsePipeline, is_cacheable_request
from backend.llm import LocalLLM
from backend.recent_context_runtime import install_recent_context_runtime


_CACHE = FastResponsePipeline()
_INSTALL_LOCK = threading.Lock()
_INSTALLED = False
_ORIGINAL_ANSWER = None


def install_fast_runtime() -> None:
    """Install production model overrides, caching, and recent-chat context once."""
    global _INSTALLED, _ORIGINAL_ANSWER
    configured_model = os.getenv("OLLAMA_MODEL", "").strip()
    with _INSTALL_LOCK:
        if configured_model:
            LocalLLM.DEFAULT_MODEL = configured_model
        if _INSTALLED:
            install_recent_context_runtime()
            return

        _ORIGINAL_ANSWER = LocalLLM.answer

        def cached_answer(
            self: LocalLLM,
            system: str,
            user: str,
            creativity: str = "medium",
        ) -> str:
            if not is_cacheable_request(user, mode=None):
                return _ORIGINAL_ANSWER(self, system=system, user=user, creativity=creativity)

            return _CACHE.answer(
                lambda **kwargs: _ORIGINAL_ANSWER(self, **kwargs),
                model=self.get_model(),
                system=system,
                user=user,
                creativity=creativity,
                mode=None,
            )

        LocalLLM.answer = cached_answer
        _INSTALLED = True

    install_recent_context_runtime()


def stats() -> dict[str, Any]:
    return _CACHE.stats()
