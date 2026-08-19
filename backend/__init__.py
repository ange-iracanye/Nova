"""Nova backend package.

The production runtime hook routes the existing Ollama integration through a
configured remote Ollama host when OLLAMA_HOST is present. Local development
continues to use the normal local Ollama client.
"""

from __future__ import annotations

import os

try:
    import ollama

    _nova_ollama_host = os.getenv("OLLAMA_HOST", "").strip()
    _nova_ollama_api_key = os.getenv("OLLAMA_API_KEY", "").strip()

    if _nova_ollama_host:
        _nova_headers = {}
        if _nova_ollama_api_key:
            _nova_headers["Authorization"] = f"Bearer {_nova_ollama_api_key}"

        _nova_ollama_client = ollama.Client(
            host=_nova_ollama_host,
            headers=_nova_headers or None,
        )

        def _nova_remote_chat(*args, **kwargs):
            return _nova_ollama_client.chat(*args, **kwargs)

        ollama.chat = _nova_remote_chat
except Exception:
    # Health/readiness endpoints must remain importable even if the optional
    # LLM client cannot initialize. NovaCore reports the actual LLM failure.
    pass

# These extensions are intentionally loaded at package import time so every
# SubjectDetector instance gets the expanded taxonomy without requiring a
# second subject-detection code path.
try:
    from backend.subject_extension import install_subject_extension
    install_subject_extension()
except Exception:
    # Subject detection remains available with the original taxonomy if the
    # optional extension cannot load.
    pass
