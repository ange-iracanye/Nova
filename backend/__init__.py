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
    pass

try:
    from backend.subject_extension import install_subject_extension
    install_subject_extension()
except Exception:
    pass

try:
    from backend.learning.understanding import UnderstandingAnalyzer
    from backend.learning.understanding_quality import install_understanding_quality
    install_understanding_quality(UnderstandingAnalyzer)
except Exception:
    pass
