"""Nova Fast Response Pipeline.

A latency-first orchestration layer for the existing Nova stack.
It avoids unnecessary work, keeps prompts compact, caches deterministic
responses, and can warm the configured Ollama model before real traffic.

This module is intentionally independent from NovaCore so it can be adopted
incrementally and safely.
"""

from __future__ import annotations

import hashlib
import os
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass(frozen=True)
class FastPathConfig:
    cache_size: int = 128
    cache_ttl_seconds: float = 300.0
    max_user_chars: int = 16_000
    warmup_enabled: bool = True


class TTLResponseCache:
    """Small thread-safe in-memory LRU/TTL cache."""

    def __init__(self, max_size: int = 128, ttl_seconds: float = 300.0):
        self.max_size = max(1, int(max_size))
        self.ttl_seconds = max(0.0, float(ttl_seconds))
        self._items: OrderedDict[str, tuple[float, str]] = OrderedDict()
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[str]:
        now = time.monotonic()
        with self._lock:
            item = self._items.get(key)
            if item is None:
                return None
            created, value = item
            if self.ttl_seconds and now - created > self.ttl_seconds:
                self._items.pop(key, None)
                return None
            self._items.move_to_end(key)
            return value

    def put(self, key: str, value: str) -> None:
        if not value:
            return
        with self._lock:
            self._items[key] = (time.monotonic(), value)
            self._items.move_to_end(key)
            while len(self._items) > self.max_size:
                self._items.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._items)


def _normalize(value: Any) -> str:
    return " ".join(str(value or "").strip().casefold().split())


def _cache_key(model: str, system: str, user: str, creativity: str) -> str:
    payload = "\x1f".join((_normalize(model), system.strip(), user.strip(), _normalize(creativity)))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def is_cacheable_request(user: str, *, mode: str | None = None) -> bool:
    """Only cache ordinary text requests, never interactive/control requests."""
    text = _normalize(user)
    if not text or len(text) > 16_000:
        return False
    if mode and _normalize(mode) in {"quiz", "practice", "exam", "interactive"}:
        return False
    return True


class FastResponsePipeline:
    """Latency wrapper around Nova's existing LLM callable."""

    def __init__(self, config: FastPathConfig | None = None):
        self.config = config or FastPathConfig(
            cache_size=int(os.getenv("NOVA_FAST_CACHE_SIZE", "128")),
            cache_ttl_seconds=float(os.getenv("NOVA_FAST_CACHE_TTL", "300")),
            max_user_chars=int(os.getenv("NOVA_FAST_MAX_CHARS", "16000")),
            warmup_enabled=os.getenv("NOVA_FAST_WARMUP", "1").lower() not in {"0", "false", "no"},
        )
        self.cache = TTLResponseCache(self.config.cache_size, self.config.cache_ttl_seconds)
        self.hits = 0
        self.misses = 0
        self._warmup_started = False
        self._warmup_lock = threading.Lock()

    def key(self, model: str, system: str, user: str, creativity: str = "medium") -> str:
        return _cache_key(model, system, user, creativity)

    def get_cached(self, model: str, system: str, user: str, creativity: str = "medium") -> Optional[str]:
        key = self.key(model, system, user, creativity)
        value = self.cache.get(key)
        if value is None:
            self.misses += 1
            return None
        self.hits += 1
        return value

    def store(self, model: str, system: str, user: str, answer: str, creativity: str = "medium") -> None:
        if is_cacheable_request(user):
            self.cache.put(self.key(model, system, user, creativity), answer)

    def answer(
        self,
        llm_answer: Callable[..., str],
        *,
        model: str,
        system: str,
        user: str,
        creativity: str = "medium",
        mode: str | None = None,
    ) -> str:
        """Return a cached answer immediately or call the existing generator."""
        if len(user) > self.config.max_user_chars:
            user = user[: self.config.max_user_chars]

        cacheable = is_cacheable_request(user, mode=mode)
        if cacheable:
            cached = self.get_cached(model, system, user, creativity)
            if cached is not None:
                return cached

        answer = llm_answer(system=system, user=user, creativity=creativity)
        if cacheable:
            self.store(model, system, user, answer, creativity)
        return answer

    def warmup(self, llm: Any) -> bool:
        """Load the model once in the background; never blocks startup."""
        if not self.config.warmup_enabled:
            return False
        with self._warmup_lock:
            if self._warmup_started:
                return False
            self._warmup_started = True

        def _run() -> None:
            try:
                llm.answer(
                    system="You are Nova. Respond with one short word: ready.",
                    user="ready",
                    creativity="low",
                )
            except Exception:
                # Warmup is an optimization, never a reason to break startup.
                pass

        threading.Thread(target=_run, name="nova-llm-warmup", daemon=True).start()
        return True

    def stats(self) -> dict[str, Any]:
        total = self.hits + self.misses
        return {
            "cache_entries": len(self.cache),
            "cache_hits": self.hits,
            "cache_misses": self.misses,
            "cache_hit_rate": round(self.hits / total, 4) if total else 0.0,
            "warmup_started": self._warmup_started,
        }
