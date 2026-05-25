"""POL-SEC-02 - HTTPS optionnel en production.

Implémenté en tant que pur middleware ASGI pour ne pas interférer
avec CORSMiddleware sur les réponses d'erreur (bug connu de BaseHTTPMiddleware).
"""

import json

from starlette.types import ASGIApp, Receive, Scope, Send

from horizon.core.config import get_settings

settings = get_settings()


class HTTPSEnforcementMiddleware:
    """Pure ASGI middleware — compatible avec CORSMiddleware sans interférence."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        if settings.ENFORCE_HTTPS and scope.get("scheme") != "https":
            body = json.dumps(
                {"detail": "[POL-SEC-02] HTTPS requis. Les connexions non chiffrées sont rejetées."}
            ).encode("utf-8")
            await send({
                "type": "http.response.start",
                "status": 400,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"content-length", str(len(body)).encode()],
                ],
            })
            await send({"type": "http.response.body", "body": body})
            return

        await self.app(scope, receive, send)
