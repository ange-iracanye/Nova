from __future__ import annotations

import os
import sys
from urllib.parse import urlparse


FREE_MODEL_MARKERS = (":free", "openrouter/free")


def require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"MISSING: {name}")
    return value


def main() -> int:
    environment = os.getenv("NOVA_ENV", "").strip().lower()
    if environment != "production":
        raise SystemExit("NOVA_ENV must be 'production'.")

    origins = [item.strip().rstrip("/") for item in require("NOVA_ALLOWED_ORIGINS").split(",") if item.strip()]
    if not origins:
        raise SystemExit("NOVA_ALLOWED_ORIGINS must contain at least one origin.")
    for origin in origins:
        parsed = urlparse(origin)
        if parsed.scheme != "https" or not parsed.netloc:
            raise SystemExit(f"INVALID: NOVA_ALLOWED_ORIGINS contains non-HTTPS origin: {origin}")

    database_url = require("NOVA_DATABASE_URL")
    if not database_url.startswith(("postgresql://", "postgres://")):
        raise SystemExit("INVALID: NOVA_DATABASE_URL must be a PostgreSQL connection string.")

    require("OPENROUTER_API_KEY")
    provider = require("NOVA_LLM_PROVIDER").lower()
    if provider != "openrouter":
        raise SystemExit(f"INVALID: NOVA_LLM_PROVIDER must be openrouter, got {provider!r}.")

    primary = require("NOVA_LLM_MODEL").lower()
    fallback = require("NOVA_LLM_FALLBACK_MODEL").lower()
    for name, model in (("NOVA_LLM_MODEL", primary), ("NOVA_LLM_FALLBACK_MODEL", fallback)):
        if not any(marker in model for marker in FREE_MODEL_MARKERS):
            raise SystemExit(f"COST SAFETY FAILURE: {name} is not explicitly a free OpenRouter model: {model}")

    if os.getenv("NOVA_ENABLE_DEMO", "false").strip().lower() == "true":
        raise SystemExit("PUBLIC DEMO MUST REMAIN DISABLED FOR NOVA V1.")

    if os.getenv("NOVA_ENABLE_DOCS", "false").strip().lower() == "true":
        raise SystemExit("PUBLIC API DOCS MUST REMAIN DISABLED FOR NOVA V1.")

    print("Nova production preflight: PASS")
    print(f"- origins: {len(origins)} HTTPS origin(s)")
    print("- database: PostgreSQL configured")
    print("- provider: OpenRouter")
    print(f"- primary model: {primary}")
    print(f"- fallback model: {fallback}")
    print("- public demo: disabled")
    print("- public API docs: disabled")
    return 0


if __name__ == "__main__":
    sys.exit(main())
