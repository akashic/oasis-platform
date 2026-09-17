"""
Tests for authentication — JWT creation, verification, login endpoint.

Uses the in-memory test fixtures from conftest. No external services needed.
"""

import time

import pytest
from httpx import AsyncClient

from app.auth import create_token, revoke_token, verify_token
from app.config import settings


@pytest.fixture(autouse=True)
def _patch_redis_for_auth_module(fake_redis, monkeypatch):
    """`app.auth.verify_token`/`revoke_token` call `app.redis.get_redis`
    directly (outside FastAPI's dependency-injection graph), so the tests in
    this module that call them without going through the `client`/`app`
    fixture need their own patch onto the shared fake Redis."""
    import app.auth as auth_module

    async def _fake_get_redis():
        return fake_redis

    monkeypatch.setattr(auth_module, "get_redis", _fake_get_redis)


# ── JWT Token Unit Tests ──────────────────────────────────────────

class TestJWT:
    def test_create_token(self):
        token = create_token("testuser")
        assert isinstance(token, str)
        assert len(token) > 20

    async def test_verify_valid_token(self):
        token = create_token("testuser")
        payload = await verify_token(token)
        assert payload is not None
        assert payload["sub"] == "testuser"

    async def test_verify_invalid_token(self):
        payload = await verify_token("not.a.valid.token")
        assert payload is None

    async def test_verify_empty_token(self):
        payload = await verify_token("")
        assert payload is None

    async def test_token_contains_exp(self):
        token = create_token("admin")
        payload = await verify_token(token)
        assert "exp" in payload
        assert payload["exp"] > time.time()

    async def test_token_contains_iat(self):
        token = create_token("admin")
        payload = await verify_token(token)
        assert "iat" in payload
        assert payload["iat"] <= time.time()

    async def test_token_contains_jti(self):
        """test_REQ_SEC_FINDING_008_token_contains_jti"""
        token = create_token("admin")
        payload = await verify_token(token)
        assert "jti" in payload
        assert len(payload["jti"]) > 10

    async def test_two_tokens_have_different_jti(self):
        payload1 = await verify_token(create_token("admin"))
        payload2 = await verify_token(create_token("admin"))
        assert payload1["jti"] != payload2["jti"]

    async def test_token_contains_typ_access(self):
        """FINDING-020: access tokens are marked `typ: "access"`.

        test_REQ_SEC_FINDING_020_token_has_typ_access
        """
        token = create_token("admin")
        payload = await verify_token(token)
        assert payload["typ"] == "access"

    async def test_token_missing_typ_claim_is_rejected(self):
        """A hand-crafted token signed with the real key but missing `typ`
        must not be accepted — forces one re-login rather than trusting an
        unmarked token indefinitely.

        test_REQ_SEC_FINDING_020_missing_typ_rejected
        """
        import time as _time

        import jwt as _jwt

        from app.config import settings as app_settings

        now = int(_time.time())
        legacy_token = _jwt.encode(
            {"sub": "admin", "jti": "legacy-jti", "iat": now, "exp": now + 3600},
            app_settings.secret_key,
            algorithm="HS256",
        )
        assert await verify_token(legacy_token) is None


# ── Monitor ticket cannot be used as an access token (FINDING-020) ────────

class TestTicketCannotBeUsedAsAccessToken:
    async def test_monitor_ticket_is_rejected_by_verify_token(self):
        """A monitor ticket is signed with a structurally distinct key
        (HKDF-derived from SECRET_KEY with a different `info` label) — it
        must never authenticate as an admin access token.

        test_REQ_SEC_FINDING_020_ticket_rejected_by_verify_token
        """
        from app.auth import create_monitor_ticket

        ticket = create_monitor_ticket("some-session-id", requested_by="admin")
        assert await verify_token(ticket) is None

    async def test_ticket_signing_key_differs_from_access_token_key(self):
        """test_REQ_SEC_FINDING_020_distinct_ticket_signing_key"""
        import jwt as _jwt

        from app.auth import create_monitor_ticket
        from app.config import settings as app_settings

        ticket = create_monitor_ticket("some-session-id")
        with pytest.raises(_jwt.InvalidSignatureError):
            _jwt.decode(ticket, app_settings.secret_key, algorithms=["HS256"])

    async def test_monitor_ticket_cannot_mint_a_fresh_ticket(self, client: AsyncClient):
        """FINDING-020: a captured ticket must not be usable to call
        `POST /api/auth/monitor-ticket` and mint another one (the original
        "chainable" exploit).

        test_REQ_SEC_FINDING_020_ticket_cannot_mint_ticket
        """
        from app.auth import create_monitor_ticket

        ticket = create_monitor_ticket("some-session-id", requested_by="admin")
        resp = await client.post(
            "/api/auth/monitor-ticket",
            json={"session_id": "another-session-id"},
            headers={"Authorization": f"Bearer {ticket}"},
        )
        assert resp.status_code == 401

    async def test_monitor_ticket_does_not_authenticate_protected_routes(
        self, client: AsyncClient
    ):
        """FINDING-020: a captured ticket must not be a general-purpose
        admin bearer credential for the other eight admin routers.

        test_REQ_SEC_FINDING_020_ticket_not_a_bearer_credential
        """
        from app.auth import create_monitor_ticket
        from app.config import settings as app_settings

        original = app_settings.auth_enabled
        app_settings.auth_enabled = True
        try:
            ticket = create_monitor_ticket("some-session-id", requested_by="admin")
            resp = await client.get(
                "/api/studies", headers={"Authorization": f"Bearer {ticket}"}
            )
            assert resp.status_code == 401
        finally:
            app_settings.auth_enabled = original


# ── Revocation (FINDING-008) ───────────────────────────────────────

class TestTokenRevocation:
    async def test_REQ_SEC_FINDING_008_revoked_token_is_rejected(self):
        token = create_token("admin")
        payload = await verify_token(token)
        assert payload is not None

        await revoke_token(payload)

        assert await verify_token(token) is None

    async def test_REQ_SEC_FINDING_008_revoking_one_token_does_not_affect_another(self):
        token_a = create_token("admin")
        token_b = create_token("admin")

        payload_a = await verify_token(token_a)
        await revoke_token(payload_a)

        assert await verify_token(token_a) is None
        assert await verify_token(token_b) is not None

    async def test_revoke_token_without_jti_is_a_no_op(self):
        # Defensive: a hand-built payload missing `jti` must not raise.
        await revoke_token({"sub": "admin", "exp": int(time.time()) + 60})


# ── Login Endpoint Tests ──────────────────────────────────────────

class TestLoginEndpoint:
    async def test_login_auth_disabled(self, client: AsyncClient):
        """FINDING-001: when auth is disabled, login must refuse to mint a
        token for arbitrary credentials rather than issuing one as a
        convenience — a forged/guessed token must never be indistinguishable
        from a real one.

        test_REQ_SEC_FINDING_001_login_refuses_when_auth_disabled
        """
        resp = await client.post(
            "/api/auth/login",
            json={"username": "anybody", "password": "anything"},
        )
        assert resp.status_code == 503
        assert "token" not in resp.json()


class TestLoginEndpointAuthEnabled:
    """Login behaviour once AUTH_ENABLED=true (the secure-by-default posture)."""

    def setup_method(self, _method):
        self._orig_enabled = settings.auth_enabled
        self._orig_password = settings.auth_password
        settings.auth_enabled = True
        settings.auth_password = "correct-horse-battery-staple"

    def teardown_method(self, _method):
        settings.auth_enabled = self._orig_enabled
        settings.auth_password = self._orig_password

    async def test_login_returns_valid_token(self, client: AsyncClient):
        """test_REQ_SEC_FINDING_001_login_issues_token_when_auth_enabled"""
        resp = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "correct-horse-battery-staple"},
        )
        assert resp.status_code == 200
        token = resp.json()["token"]
        payload = await verify_token(token)
        assert payload is not None
        assert payload["sub"] == "admin"

    async def test_login_rejects_wrong_password(self, client: AsyncClient):
        resp = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong"},
        )
        assert resp.status_code == 401

    async def test_login_503_when_password_not_configured(self, client: AsyncClient):
        settings.auth_password = ""
        resp = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "anything"},
        )
        assert resp.status_code == 503

    async def test_login_via_argon2_hash(self, client: AsyncClient):
        """FINDING-005: AUTH_PASSWORD_HASH (Argon2id) is the preferred path
        and takes priority over the deprecated plaintext AUTH_PASSWORD.

        test_REQ_SEC_FINDING_005_login_via_argon2_hash
        """
        from app.security import hash_password

        orig_hash = settings.auth_password_hash
        settings.auth_password_hash = hash_password("a-hashed-password")
        try:
            resp = await client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "a-hashed-password"},
            )
            assert resp.status_code == 200
        finally:
            settings.auth_password_hash = orig_hash

    async def test_login_rejects_wrong_password_with_hash_configured(
        self, client: AsyncClient
    ):
        from app.security import hash_password

        orig_hash = settings.auth_password_hash
        settings.auth_password_hash = hash_password("a-hashed-password")
        try:
            resp = await client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "wrong"},
            )
            assert resp.status_code == 401
        finally:
            settings.auth_password_hash = orig_hash


class TestLoginRateLimiting:
    """FINDING-005: no throttling of any kind previously existed on
    POST /api/auth/login."""

    def setup_method(self, _method):
        self._orig_enabled = settings.auth_enabled
        self._orig_password = settings.auth_password
        settings.auth_enabled = True
        settings.auth_password = "correct-horse-battery-staple"

    def teardown_method(self, _method):
        settings.auth_enabled = self._orig_enabled
        settings.auth_password = self._orig_password

    async def test_locks_out_after_repeated_failures(self, client: AsyncClient):
        """test_REQ_SEC_FINDING_005_login_locks_out_after_failures"""
        for _ in range(5):
            resp = await client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "wrong"},
            )
            assert resp.status_code == 401

        # The 6th attempt — even with the CORRECT password — must be
        # blocked while the lockout is active.
        resp = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "correct-horse-battery-staple"},
        )
        assert resp.status_code == 429
        assert "Retry-After" in resp.headers

    async def test_successful_login_clears_failure_counter(self, client: AsyncClient):
        """test_REQ_SEC_FINDING_005_success_clears_failures"""
        for _ in range(3):
            await client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "wrong"},
            )
        ok = await client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "correct-horse-battery-staple"},
        )
        assert ok.status_code == 200

        # Counter reset — a few more failures should not trip the lockout.
        for _ in range(3):
            resp = await client.post(
                "/api/auth/login",
                json={"username": "admin", "password": "wrong"},
            )
            assert resp.status_code == 401


# ── Auth Status Endpoint Tests ────────────────────────────────────

class TestAuthStatus:
    async def test_auth_status_unauthenticated(self, client: AsyncClient):
        """Auth status should return when auth is disabled."""
        resp = await client.get("/api/auth/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "auth_enabled" in data

    async def test_auth_status_authenticated(self, auth_client: AsyncClient):
        resp = await auth_client.get("/api/auth/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "auth_enabled" in data


# ── Logout / Revocation Endpoint Tests (FINDING-008) ───────────────

class TestLogoutEndpoint:
    async def test_REQ_SEC_FINDING_008_logout_revokes_current_token(
        self, auth_client: AsyncClient
    ):
        # The token is valid before logout...
        status_before = await auth_client.get("/api/auth/status")
        assert status_before.json()["authenticated"] is True

        resp = await auth_client.post("/api/auth/logout")
        assert resp.status_code == 204

        # ...and rejected immediately after, even though it has not expired.
        status_after = await auth_client.get("/api/auth/status")
        assert status_after.json()["authenticated"] is False

    async def test_REQ_SEC_FINDING_008_revoked_token_rejected_by_protected_route(
        self, auth_client: AsyncClient
    ):
        await auth_client.post("/api/auth/logout")
        resp = await auth_client.get("/api/studies")
        assert resp.status_code == 401

    async def test_logout_is_a_no_op_when_auth_disabled(self, client: AsyncClient):
        resp = await client.post("/api/auth/logout")
        assert resp.status_code == 204

    async def test_logout_requires_auth_when_enabled(self, client: AsyncClient):
        from app.config import settings

        original = settings.auth_enabled
        settings.auth_enabled = True
        try:
            resp = await client.post("/api/auth/logout")
            assert resp.status_code == 401
        finally:
            settings.auth_enabled = original


# ── Monitor Ticket Endpoint Tests (FINDING-008) ────────────────────

class TestMonitorTicketEndpoint:
    async def test_REQ_SEC_FINDING_008_issues_ticket_for_authenticated_caller(
        self, auth_client: AsyncClient
    ):
        resp = await auth_client.post(
            "/api/auth/monitor-ticket", json={"session_id": "abc-123"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "ticket" in body and len(body["ticket"]) > 20
        assert body["expires_in"] == 60

    async def test_REQ_SEC_FINDING_008_rejects_without_a_valid_token(
        self, client: AsyncClient
    ):
        """Unconditional — unlike most endpoints, this must require a valid
        token even when AUTH_ENABLED=false, matching the monitor WebSocket
        it feeds (FINDING-001)."""
        resp = await client.post(
            "/api/auth/monitor-ticket", json={"session_id": "abc-123"}
        )
        assert resp.status_code == 401

    async def test_ticket_is_rejected_by_the_monitor_endpoint_for_a_different_session(
        self, auth_client: AsyncClient
    ):
        from app.auth import consume_monitor_ticket

        resp = await auth_client.post(
            "/api/auth/monitor-ticket", json={"session_id": "session-a"}
        )
        ticket = resp.json()["ticket"]

        assert await consume_monitor_ticket(ticket, "session-b") is False
        assert await consume_monitor_ticket(ticket, "session-a") is True
