"""Middleware that propagates a unique request ID through the request lifecycle."""

import contextvars
import uuid

from starlette.types import ASGIApp, Message, Receive, Scope, Send

# Shared context var — accessible from any handler or logging formatter
request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar(
    "request_id", default=""
)

HEADER_NAME = b"x-request-id"


class RequestIdMiddleware:
    """Ensure every request has a unique ID for log correlation.

    1. Reads X-Request-ID from incoming headers (set by Nginx or upstream).
    2. Generates a UUID4 if not present.
    3. Stores it in a ContextVar for access in logging.
    4. Adds it to the response headers.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Extract or generate request ID
        rid = ""
        for name, value in scope.get("headers", []):
            if name == HEADER_NAME:
                rid = value.decode("utf-8", errors="replace")
                break
        if not rid:
            rid = uuid.uuid4().hex

        # Store in context var for logging / other middleware
        token = request_id_ctx.set(rid)
        scope["request_id"] = rid  # type: ignore[typeddict-unknown-key]

        async def _send(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                headers[HEADER_NAME] = rid.encode()
                message["headers"] = list(headers.items())
            await send(message)

        try:
            await self.app(scope, receive, _send)
        finally:
            request_id_ctx.reset(token)
