from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class FreeLLM:
    """Gemini Developer API free-tier adapter used by public V1."""

    CREATIVITY_SETTINGS = {
        "low": {"temperature": 0.2, "top_p": 0.85},
        "medium": {"temperature": 0.5, "top_p": 0.9},
        "high": {"temperature": 0.8, "top_p": 0.95},
    }

    def __init__(self, model: Optional[str] = None, max_retries: int = 2, retry_delay: float = 0.8):
        self.model = model or os.getenv("NOVA_LLM_MODEL", "gemini-3.1-flash-lite")
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.max_retries = max(0, int(max_retries))
        self.retry_delay = max(0.0, float(retry_delay))
        self.last_error = None
        self.last_response = None
        self.last_generation_time = None
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0

    def get_generation_settings(self, creativity: str = "medium") -> Dict[str, float]:
        key = str(creativity).strip().lower()
        return dict(self.CREATIVITY_SETTINGS.get(key, self.CREATIVITY_SETTINGS["medium"]))

    def get_temperature(self, creativity: str = "medium") -> float:
        return self.get_generation_settings(creativity)["temperature"]

    def set_model(self, model: str) -> None:
        if not isinstance(model, str) or not model.strip():
            raise ValueError("Model name cannot be empty.")
        self.model = model.strip()

    def get_model(self) -> str:
        return self.model

    def _generate(self, system: str, user: str, settings: Dict[str, Any]) -> str:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": settings["temperature"], "topP": settings["top_p"]},
        }
        request = Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urlopen(request, timeout=90) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:1200]
            raise RuntimeError(f"Gemini API HTTP {error.code}: {detail}") from error
        except URLError as error:
            raise RuntimeError(f"Gemini API connection failed: {error.reason}") from error
        candidates = data.get("candidates") or []
        if not candidates:
            raise RuntimeError("Gemini returned no candidates.")
        parts = ((candidates[0].get("content") or {}).get("parts") or [])
        text = "".join(str(part.get("text", "")) for part in parts).strip()
        if not text:
            raise RuntimeError("Gemini returned an empty response.")
        return text

    def answer(self, system: str, user: str, creativity: str = "medium") -> str:
        if not isinstance(system, str) or not system.strip():
            raise ValueError("System prompt cannot be empty.")
        if not isinstance(user, str) or not user.strip():
            raise ValueError("User prompt cannot be empty.")
        settings = self.get_generation_settings(creativity)
        self.total_requests += 1
        started = time.perf_counter()
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                text = self._generate(system, user, settings)
                self.last_response = text
                self.last_generation_time = time.perf_counter() - started
                self.last_error = None
                self.successful_requests += 1
                return text
            except Exception as error:
                last_error = error
                self.last_error = str(error)
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
        self.failed_requests += 1
        raise RuntimeError(f"Nova's free AI provider failed: {last_error}") from last_error
