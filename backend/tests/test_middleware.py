"""
Tests for the global request body size limit middleware.

FINDING-009: the knowledge-base file upload previously read an entire
request body into memory before any size check ran, with no declared
maximum anywhere in the stack. These tests exercise
``app.middleware.MaxBodySizeMiddleware`` directly, against a minimal ASGI
app, independent of the full FastAPI application.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.middleware import MaxBodySizeMiddleware


async def _echo_app(scope, receive, send):
    """Minimal ASGI app that reads the whole body and echoes its length."""
    body = b""
    while True:
        message = await receive()
        body += message.get("body", b"")
        if not message.get("more_body", False):
            break
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"text/plain")],
        }
    )
    await send({"type": "http.response.body", "body": str(len(body)).encode()})


@pytest.fixture
def small_limit_app():
    return MaxBodySizeMiddleware(_echo_app, max_bytes=16)


class TestMaxBodySizeMiddleware:
    async def test_REQ_SEC_FINDING_009_body_within_limit_passes(self, small_limit_app):
        transport = ASGITransport(app=small_limit_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/", content=b"short")
        assert resp.status_code == 200
        assert resp.text == "5"

    async def test_REQ_SEC_FINDING_009_content_length_over_limit_rejected(
        self, small_limit_app
    ):
        """A declared Content-Length above the cap is rejected before the
        body is read at all."""
        transport = ASGITransport(app=small_limit_app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/", content=b"x" * 100)
        assert resp.status_code == 413
        assert "too large" in resp.json()["detail"].lower()

    async def test_REQ_SEC_FINDING_009_streamed_body_over_limit_rejected(self):
        """Even without (or with an understated) Content-Length, the actual
        byte stream is policed — protects against chunked-transfer bodies
        that never declare their true size up front."""
        middleware = MaxBodySizeMiddleware(_echo_app, max_bytes=16)

        chunks = [b"x" * 10, b"y" * 10, b"z" * 10]  # 30 bytes total, no Content-Length

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/",
            "headers": [],  # no content-length declared
        }

        sent = []
        remaining = list(chunks)

        async def receive():
            if remaining:
                chunk = remaining.pop(0)
                return {
                    "type": "http.request",
                    "body": chunk,
                    "more_body": bool(remaining),
                }
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            sent.append(message)

        await middleware(scope, receive, send)

        start = next(m for m in sent if m["type"] == "http.response.start")
        assert start["status"] == 413

    async def test_REQ_SEC_FINDING_009_non_http_scope_passes_through(self):
        """Non-HTTP scopes (e.g. websocket, lifespan) are not touched."""
        calls = []

        async def app(scope, receive, send):
            calls.append(scope["type"])

        middleware = MaxBodySizeMiddleware(app, max_bytes=16)
        await middleware({"type": "lifespan"}, None, None)
        assert calls == ["lifespan"]
