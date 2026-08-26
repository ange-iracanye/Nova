"""Register analytics once the FastAPI application object exists."""

from backend.analytics import analytics_middleware, router
from backend import api

try:
    api.app.include_router(router)
    api.app.middleware("http")(analytics_middleware)
except Exception as exc:  # pragma: no cover
    print(f"Nova analytics bootstrap warning: {type(exc).__name__}: {exc}", flush=True)
