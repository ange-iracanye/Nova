"""Request-local user context shared by lightweight persistence adapters.

NovaCore already serializes multi-user processing at the API boundary. This
module gives persistence components a tiny, dependency-free way to know which
user is active without threading email arguments through every legacy API.
"""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from collections.abc import Iterator


_ACTIVE_USER: ContextVar[str | None] = ContextVar(
    "nova_active_user",
    default=None,
)


def normalize_user(email: str | None) -> str | None:
    if not email:
        return None
    value = str(email).strip().lower()
    return value or None


def set_active_user(email: str | None) -> str | None:
    value = normalize_user(email)
    _ACTIVE_USER.set(value)
    return value


def get_active_user() -> str | None:
    return _ACTIVE_USER.get()


def clear_active_user() -> None:
    _ACTIVE_USER.set(None)


@contextmanager
def user_context(email: str | None) -> Iterator[str | None]:
    """Temporarily bind a user and restore the previous context on exit.

    ContextVar tokens make nested scopes safe and prevent a completed
    operation from leaving its user attached to later work in the same
    execution context.
    """
    token: Token[str | None] = _ACTIVE_USER.set(normalize_user(email))
    try:
        yield _ACTIVE_USER.get()
    finally:
        _ACTIVE_USER.reset(token)
