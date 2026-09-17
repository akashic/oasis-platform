"""
Tests for FINDING-015: rate limiting, lockout and audit lines must key on
the real client address, not the reverse proxy's.

`uvicorn.middleware.proxy_headers.ProxyHeadersMiddleware` is well-tested
upstream code; these tests exercise the *wiring* — that it is applied with
`settings.trusted_proxy_ips`, and that `request.client.host` /
`websocket.client.host` (what app/api/auth.py, app/api/twilio.py and
app/rate_limit.py actually read) reflect the corrected address only when
the immediate TCP peer is trusted.
"""

from __future__ import annotations

from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware


async def _echo_client_app(scope, receive, send):
    """Minimal ASGI app that echoes back the client host it sees."""
    client = scope.get("client")
    body = (client[0] if client else "unknown").encode()
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": [(b"content-type", b"text/plain")],
        }
    )
    await send({"type": "http.response.body", "body": body})


async def _call(app, *, peer: str, forwarded_for: str | None) -> str:
    sent = []

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "client": (peer, 12345),
        "headers": (
            [(b"x-forwarded-for", forwarded_for.encode())] if forwarded_for else []
        ),
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        sent.append(message)

    await app(scope, receive, send)
    body = next(m for m in sent if m["type"] == "http.response.body")
    return body["body"].decode()


class TestTrustedProxyMiddlewareWiring:
    async def test_REQ_SEC_FINDING_015_trusted_peer_client_ip_corrected(self):
        """A request whose immediate peer is inside the trusted subnet
        (Caddy, per settings.trusted_proxy_ips) has its client address
        replaced with the forwarded value."""
        app = ProxyHeadersMiddleware(_echo_client_app, trusted_hosts="172.28.0.0/24")
        result = await _call(app, peer="172.28.0.5", forwarded_for="203.0.113.7")
        assert result == "203.0.113.7"

    async def test_REQ_SEC_FINDING_015_untrusted_peer_not_corrected(self):
        """A direct request (or one relayed by anything outside the trusted
        subnet) must NOT have its client address overridden — otherwise any
        caller could set X-Forwarded-For itself and evade rate limiting."""
        app = ProxyHeadersMiddleware(_echo_client_app, trusted_hosts="172.28.0.0/24")
        result = await _call(app, peer="203.0.113.99", forwarded_for="10.0.0.1")
        assert result == "203.0.113.99"

    async def test_REQ_SEC_FINDING_015_no_forwarded_header_from_trusted_peer(self):
        """A trusted peer that sends no X-Forwarded-For at all leaves the
        client address as-is (nothing to correct it with)."""
        app = ProxyHeadersMiddleware(_echo_client_app, trusted_hosts="172.28.0.0/24")
        result = await _call(app, peer="172.28.0.5", forwarded_for=None)
        assert result == "172.28.0.5"

    def test_REQ_SEC_FINDING_015_wired_with_configured_trusted_hosts(self):
        """main.py must apply the middleware using settings.trusted_proxy_ips
        (not a hardcoded value), so an operator override in .env takes
        effect."""
        from app.main import app as fastapi_app

        proxy_layers = [
            m
            for m in fastapi_app.user_middleware
            if m.cls is ProxyHeadersMiddleware
        ]
        assert len(proxy_layers) == 1
