"""Nova backend package.

The package keeps the public API modules unchanged while providing a small
production runtime hook for the Ollama Python client. When OLLAMA_HOST is set,
all existing ``ollama.chat`` calls are routed through that endpoint.
"""

from __future__ import annotations

import os

try:
    import ollama

    _nova_ollama_host = os.getenv("OLLAMA_HOST", "").strip()

    if _nova_ollama_host:
        _nova_ollama_client = ollama.Client(host=_nova_ollama_host)

        def _nova_remote_chat(*args, **kwargs):
            return _nova_ollama_client.chat(*args, **kwargs)

        ollama.chat = _nova_remote_chat
except Exception:
    # The API can still expose health/readiness information when the LLM
    # dependency is unavailable. NovaCore will report the actual failure.
    pass
