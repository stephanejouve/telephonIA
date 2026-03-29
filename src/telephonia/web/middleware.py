"""Middleware de logging HTTP pour FastAPI."""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

_SILENT_PATHS = {"/api/health"}
_STATIC_EXTENSIONS = (".js", ".css", ".ico", ".png", ".svg", ".map", ".woff", ".woff2")


def _should_log(path: str) -> bool:
    """Determine si une requete doit etre loguee."""
    if path in _SILENT_PATHS:
        return False
    if path.startswith("/assets/") or path.endswith(_STATIC_EXTENSIONS):
        return False
    return True


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware qui logue chaque requete HTTP avec methode, path, status et duree."""

    async def dispatch(self, request, call_next):
        if not _should_log(request.url.path):
            return await call_next(request)

        start = time.monotonic()
        response = await call_next(request)
        duration_ms = (time.monotonic() - start) * 1000

        status = response.status_code
        if status >= 500:
            level = logging.ERROR
        elif status >= 400:
            level = logging.WARNING
        else:
            level = logging.INFO

        logger.log(
            level,
            "%s %s → %d (%.0fms)",
            request.method,
            request.url.path,
            status,
            duration_ms,
        )
        return response
