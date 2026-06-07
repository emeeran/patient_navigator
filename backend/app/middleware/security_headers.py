"""ASGI middleware that adds security headers to every response."""

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import settings


class SecurityHeadersMiddleware:
    """Add security-related headers to all HTTP responses.

    These headers protect against common web vulnerabilities:
    clickjacking, MIME-type sniffing, referrer leakage, etc.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        async def _send(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = dict(message.get("headers", []))
                header_defaults: list[tuple[str, str]] = [
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"strict-origin-when-cross-origin"),
                    (
                        b"permissions-policy",
                        b"camera=(), microphone=(), geolocation=()",
                    ),
                ]
                # HSTS only in production (must be behind TLS)
                if settings.is_production:
                    header_defaults.append(
                        (b"strict-transport-security", b"max-age=63072000; includeSubDomains; preload")
                    )
                # CSP — relaxed for Swagger docs UI
                csp = (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline'; "
                    "style-src 'self' 'unsafe-inline'; "
                    "img-src 'self' data:; "
                    "connect-src 'self'"
                )
                header_defaults.append((b"content-security-policy", csp.encode()))

                for name, value in header_defaults:
                    # Don't overwrite headers already set by downstream
                    if name not in headers:
                        headers[name] = value

                message["headers"] = list(headers.items())

            await send(message)

        await self.app(scope, receive, _send)
