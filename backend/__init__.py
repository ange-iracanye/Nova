"""Nova backend package initialization and free-tier runtime hooks."""

from __future__ import annotations

import atexit
import os
import threading
import time
from pathlib import Path

# Local development baseline. Public V1 overrides the provider explicitly.
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

# ---------------------------------------------------------------------------
# Free public deployment support
# ---------------------------------------------------------------------------
# Render Free has an ephemeral filesystem. When NOVA_DATABASE_URL is present,
# mirror runtime files to free PostgreSQL and restore them at process startup.
# This lets the existing JSON-based Nova architecture survive free-host
# restarts without a paid persistent disk.

try:
    if os.getenv("NOVA_DATABASE_URL", "").strip():
        from backend.free_persistence import DatabaseSessionStore, FreePostgresStore
        import backend.persistent_sessions as _persistent_sessions

        _nova_free_store = FreePostgresStore()
        _nova_data_root = Path(os.getenv("NOVA_DATA_DIR", "data"))
        _nova_free_store.restore(_nova_data_root)

        # Production imports this symbol after backend package initialization.
        _persistent_sessions.PersistentSessionStore = DatabaseSessionStore

        def _nova_sync_runtime_data() -> None:
            try:
                _nova_free_store.sync(_nova_data_root)
            except Exception as _error:
                print(f"Nova free persistence sync warning: {_error}")

        def _nova_sync_loop() -> None:
            while True:
                time.sleep(10)
                _nova_sync_runtime_data()

        _nova_sync_thread = threading.Thread(target=_nova_sync_loop, name="nova-free-persistence", daemon=True)
        _nova_sync_thread.start()
        atexit.register(_nova_sync_runtime_data)

        print("Nova free persistence enabled.")
except Exception as _error:
    print(f"Nova free persistence unavailable: {_error}")

# Public V1 uses the free Gemini provider. Patch the existing TutorEngine
# dependency without changing its public API or the large tutoring pipeline.
try:
    if os.getenv("NOVA_LLM_PROVIDER", "").strip().lower() == "gemini":
        from backend.free_llm import FreeLLM
        import backend.tutor_system.tutor_engine as _nova_tutor_engine
        _nova_tutor_engine.LocalLLM = FreeLLM
        print("Nova free Gemini provider enabled.")
except Exception as _error:
    print(f"Nova free Gemini provider unavailable: {_error}")
