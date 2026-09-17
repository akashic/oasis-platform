"""
OASIS — ASGI-level request body size limit.

FINDING-009: the knowledge-base file upload previously read an entire
request body into memory (and decoded it a second time) before any size
check ran, with no declared maximum upload size anywhere in the stack. This
module provides a global backstop, applied to every request before FastAPI
or Starlette parse the body at all (multipart form data, JSON, etc.).

Implemented as a plain ASGI callable rather than Starlette's
``BaseHTTPMiddleware``, which fully buffers the request body in order to
expose it as ``request.body()`` to downstream middleware — doing that here
would defeat the entire purpose of this guard.
"""

from __future__ import annotations

from starlette.types import ASGIApp, Message, Receive, Scope, Send


class RequestBodyTooLarge(Exception):
    """Raised internally once the streamed body crosses the configured cap."""


class MaxBodySizeMiddleware:
    """Reject HTTP request bodies larger than ``max_bytes`` with a 413.

    Two layers, both fail-closed:

    1. A ``Content-Length`` pre-check — rejects before a single byte of the
       body is read when the client declares an oversized body up front.
    2. A running byte counter wrapped around the actual ASGI ``receive``
       stream, which also catches a missing or understated
       ``Content-Length`` (e.g. chunked transfer-encoding) by aborting once
       the true total crosses the cap, even if the header lied or was
       absent.
    """

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = dict(scope.get("headers") or [])
        content_length = headers.get(b"content-length")
        if content_length is not None:
            try:
                declared = int(content_length)
            except ValueError:
                declared = None
            if declared is not None and declared > self.max_bytes:
                await self._reject(send)
                return

        total = 0
        max_bytes = self.max_bytes

        async def _guarded_receive() -> Message:
            nonlocal total
            message = await receive()
            if message["type"] == "http.request":
                total += len(message.get("body") or b"")
                if total > max_bytes:
                    raise RequestBodyTooLarge()
            return message

        try:
            await self.app(scope, _guarded_receive, send)
        except RequestBodyTooLarge:
            await self._reject(send)

    @staticmethod
    async def _reject(send: Send) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": [(b"content-type", b"application/json")],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": b'{"detail":"Request body too large."}',
            }
        )
