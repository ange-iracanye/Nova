from __future__ import annotations

import contextvars
import hashlib
import os
from pathlib import Path
from typing import Any

from backend.settings import SettingsManager

# Keep the settings schema backwards compatible while allowing the public
# language selector to grow without changing the storage format.
SettingsManager.ALLOWED_LANGUAGES = {
    "English",
    "French",
    "Spanish",
    "German",
    "Italian",
    "Portuguese",
    "Dutch",
    "Polish",
    "Turkish",
    "Russian",
    "Arabic",
    "Hindi",
    "Chinese",
    "Japanese",
    "Korean",
}

_current_user: contextvars.ContextVar[str | None] = contextvars.ContextVar("nova_settings_user", default=None)


def set_current_user(email: str | None):
    return _current_user.set(email.strip().lower() if email else None)


def reset_current_user(token) -> None:
    _current_user.reset(token)


def _path_for_user(email: str) -> Path:
    root = Path(os.getenv("NOVA_USER_SETTINGS_DIR", "data/settings/users"))
    user_id = hashlib.sha256(email.encode("utf-8")).hexdigest()
    return root / user_id / "settings.json"


def current_manager() -> SettingsManager:
    email = _current_user.get()
    if not email:
        raise RuntimeError("Nova user settings require an authenticated user context.")
    return SettingsManager(_path_for_user(email))


class UserSettingsProxy:
    """Drop-in settings facade that scopes persistence to the authenticated user."""

    def get(self):
        return current_manager().get()

    def get_value(self, key: str, default: Any = None):
        return current_manager().get_value(key, default)

    def has(self, key: str) -> bool:
        return current_manager().has(key)

    def update(self, **values):
        return current_manager().update(**values)

    def update_dict(self, values: dict[str, Any]):
        return current_manager().update_dict(values)

    def save(self) -> None:
        current_manager().save()

    def reset(self):
        manager = current_manager()
        manager.data = manager.default_settings()
        manager.save()
        return manager.get()
