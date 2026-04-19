"""POL-SEC-02 - HTTPS optionnel en production."""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from horizon.core.config import get_settings

settings = get_settings()


class HTTPSEnforcementMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if settings.ENFORCE_HTTPS:
            if request.url.scheme != "https":
                return JSONResponse(
                    status_code=400,
                    content={
                        "detail": "[POL-SEC-02] HTTPS requis. Les connexions non chiffrées sont rejetées."
                    },
                )
        return await call_next(request)
