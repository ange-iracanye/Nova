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


_CACHE = FastResponsePipeline()
_INSTALL_LOCK = threading.Lock()
_INSTALLED = False
_ORIGINAL_ANSWER = None


def install_fast_runtime() -> None:
    """Install the production LLM model override and response cache once."""
    global _INSTALLED, _ORIGINAL_ANSWER
    with _INSTALL_LOCK:
        if _INSTALLED:
            return

        configured_model = os.getenv("OLLAMA_MODEL", "").strip()
        if configured_model:
            LocalLLM.DEFAULT_MODEL = configured_model

        _ORIGINAL_ANSWER = LocalLLM.answer

        def cached_answer(
            self: LocalLLM,
            system: str,
            user: str,
            creativity: str = "medium",
        ) -> str:
            # Never cache empty, oversized, or interactive requests.
            if not is_cacheable_request(user, mode=None):
                return _ORIGINAL_ANSWER(
                    self,
                    system=system,
                    user=user,
                    creativity=creativity,
                )

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


def stats() -> dict[str, Any]:
    return _CACHE.stats()
