"""Nova backend package initialization and free-tier runtime hooks."""

from __future__ import annotations

import atexit
import os
import threading
import time
from pathlib import Path

os.environ.setdefault("OLLAMA_MODEL", "qwen2.5:3b")

try:
    import ollama
    _nova_ollama_host = os.getenv("OLLAMA_HOST", "").strip()
    _nova_ollama_api_key = os.getenv("OLLAMA_API_KEY", "").strip()
    if _nova_ollama_host:
        _nova_headers = {"Authorization": f"Bearer {_nova_ollama_api_key}"} if _nova_ollama_api_key else None
        _nova_ollama_client = ollama.Client(host=_nova_ollama_host, headers=_nova_headers)
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

# Render Free has an ephemeral filesystem. When NOVA_DATABASE_URL is present,
# restore runtime files from PostgreSQL and keep syncing generated user data.
try:
    if os.getenv("NOVA_DATABASE_URL", "").strip():
        from backend.free_persistence import DatabaseSessionStore, FreePostgresStore
        import backend.persistent_sessions as _persistent_sessions
        from backend import auth as _auth

        _nova_free_store = FreePostgresStore()
        _nova_data_root = Path(os.getenv("NOVA_DATA_DIR", "data"))
        _nova_free_store.restore(_nova_data_root)
        _persistent_sessions.PersistentSessionStore = DatabaseSessionStore

        def _nova_sync_runtime_data() -> None:
            try:
                _nova_free_store.sync(_nova_data_root)
            except Exception as _error:
                print(f"Nova free persistence sync warning: {_error}")

        _nova_original_save_users = _auth.save_users
        def _nova_save_users_and_sync(data):
            result = _nova_original_save_users(data)
            _nova_sync_runtime_data()
            return result
        _auth.save_users = _nova_save_users_and_sync

        def _nova_sync_loop() -> None:
            while True:
                time.sleep(10)
                _nova_sync_runtime_data()

        threading.Thread(target=_nova_sync_loop, name="nova-free-persistence", daemon=True).start()
        atexit.register(_nova_sync_runtime_data)
        print("Nova free persistence enabled.")
except Exception as _error:
    print(f"Nova free persistence unavailable: {_error}")

# Public V1 uses the OpenRouter free-model provider without changing
# TutorEngine's existing LocalLLM interface.
try:
    if os.getenv("NOVA_LLM_PROVIDER", "").strip().lower() == "openrouter":
        from backend.free_llm import FreeLLM
        import backend.tutor_system.tutor_engine as _nova_tutor_engine
        _nova_tutor_engine.LocalLLM = FreeLLM
        print("Nova OpenRouter free provider enabled.")
except Exception as _error:
    print(f"Nova OpenRouter free provider unavailable: {_error}")
