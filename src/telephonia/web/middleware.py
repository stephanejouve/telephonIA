"""Middleware de logging HTTP pour FastAPI."""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

_SILENT_PATHS = {"/api/health"}


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware qui logue chaque requete HTTP avec methode, path, status et duree."""

    async def dispatch(self, request, call_next):
        if request.url.path in _SILENT_PATHS:
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
