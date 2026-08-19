"""Nova backend package initialization and runtime compatibility hooks."""

from __future__ import annotations

import os

# The repository ships with qwen2.5:3b as the practical local development
# baseline. Production explicitly overrides this with OLLAMA_MODEL (for
# example the configured cloud model), so this never overrides deployment
# configuration.
os.environ.setdefault("OLLAMA_MODEL", "qwen2.5:3b")

try:
    import ollama
    _nova_ollama_host = os.getenv("OLLAMA_HOST", "").strip()
    _nova_ollama_api_key = os.getenv("OLLAMA_API_KEY", "").strip()
    if _nova_ollama_host:
        _nova_headers = {}
        if _nova_ollama_api_key:
            _nova_headers["Authorization"] = f"Bearer {_nova_ollama_api_key}"
        _nova_ollama_client = ollama.Client(host=_nova_ollama_host, headers=_nova_headers or None)

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
    from backend.learning.understanding import UnderstandingAnalyzer, UnderstandingTracker
    from backend.learning.understanding_quality import install_understanding_quality
    from backend.learning.tracker_quality import install_tracker_quality
    install_understanding_quality(UnderstandingAnalyzer)
    install_tracker_quality(UnderstandingTracker)
except Exception:
    pass

try:
    from backend.learning.session_manager import SessionManager
    from backend.learning.session_quality import install_session_quality
    install_session_quality(SessionManager)
except Exception:
    pass
