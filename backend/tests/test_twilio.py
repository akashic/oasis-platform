"""
Tests for the Twilio integration endpoints.

No Twilio account needed — all external calls are mocked. Signature
validation (FINDING-003) is exercised for real using ``twilio``'s own
``RequestValidator`` so the tests prove the server accepts a genuinely
Twilio-signed request and rejects everything else.
"""

import time
import uuid

import jwt
import pytest
from httpx import AsyncClient
from twilio.request_validator import RequestValidator

from app.config import settings


@pytest.fixture(autouse=True)
def _twilio_configured(monkeypatch):
    """Configure a deterministic Twilio auth token + domain for every test
    in this module, and restore the previous values afterwards."""
    monkeypatch.setattr(settings, "twilio_auth_token", "test-twilio-auth-token")
    monkeypatch.setattr(settings, "domain", "localhost")
    yield


def _signed_headers(path: str, form: dict) -> dict:
    """Compute a valid X-Twilio-Signature header for ``form`` posted to
    ``path``, matching how ``app.api.twilio._public_webhook_url`` builds
    the URL it validates against (http://<domain><path> for domain=localhost).
    """
    url = f"http://localhost{path}"
    validator = RequestValidator(settings.twilio_auth_token)
    signature = validator.compute_signature(url, form)
    return {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Twilio-Signature": signature,
    }


async def _post_signed(client: AsyncClient, path: str, form: dict):
    return await client.post(path, data=form, headers=_signed_headers(path, form))


class TestTwilioWebhookSignatureValidation:
    """FINDING-003: the webhook must validate X-Twilio-Signature before
    doing anything else."""

    async def test_missing_signature_rejected(self, client: AsyncClient):
        """test_REQ_SEC_FINDING_003_webhook_rejects_missing_signature"""
        fake_id = str(uuid.uuid4())
        resp = await client.post(
            f"/api/twilio/voice/{fake_id}",
            data={"From": "+15559876543"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 403

    async def test_invalid_signature_rejected(self, client: AsyncClient):
        """test_REQ_SEC_FINDING_003_webhook_rejects_invalid_signature"""
        fake_id = str(uuid.uuid4())
        resp = await client.post(
            f"/api/twilio/voice/{fake_id}",
            data={"From": "+15559876543"},
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Twilio-Signature": "not-a-real-signature",
            },
        )
        assert resp.status_code == 403

    async def test_valid_signature_accepted(self, client: AsyncClient):
        """test_REQ_SEC_FINDING_003_webhook_accepts_valid_signature"""
        resp = await client.post("/api/studies", json={"title": "Twilio Sig Test"})
        study_id = resp.json()["id"]
        agent_resp = await client.post(
            f"/api/studies/{study_id}/agents",
            json={"name": "Twilio Agent", "status": "active"},
        )
        agent_id = agent_resp.json()["id"]

        resp = await _post_signed(
            client,
            f"/api/twilio/voice/{agent_id}",
            {"From": "+15559876543", "CallSid": "CA1234567890"},
        )
        assert resp.status_code == 200
        assert "<Response>" in resp.text

    async def test_rejected_when_auth_token_not_configured(
        self, client: AsyncClient, monkeypatch
    ):
        """FINDING-003: fail closed when TWILIO_AUTH_TOKEN is unset, even
        with an otherwise well-formed request.

        test_REQ_SEC_FINDING_003_webhook_fails_closed_without_auth_token
        """
        monkeypatch.setattr(settings, "twilio_auth_token", "")
        fake_id = str(uuid.uuid4())
        form = {"From": "+15559876543"}
        resp = await client.post(
            f"/api/twilio/voice/{fake_id}",
            data=form,
            headers=_signed_headers(f"/api/twilio/voice/{fake_id}", form),
        )
        assert resp.status_code == 403

    async def test_stream_url_uses_configured_domain_not_host_header(
        self, client: AsyncClient
    ):
        """FINDING-003: the <Stream> URL must come from settings.domain,
        never from the (spoofable) inbound Host header.

        test_REQ_SEC_FINDING_003_stream_url_ignores_host_header
        """
        resp = await client.post("/api/studies", json={"title": "Twilio Host Spoof"})
        study_id = resp.json()["id"]
        agent_resp = await client.post(
            f"/api/studies/{study_id}/agents",
            json={"name": "Twilio Agent", "status": "active"},
        )
        agent_id = agent_resp.json()["id"]

        form = {"From": "+15559876543"}
        headers = _signed_headers(f"/api/twilio/voice/{agent_id}", form)
        headers["Host"] = "evil.example.com"
        resp = await client.post(
            f"/api/twilio/voice/{agent_id}", data=form, headers=headers
        )
        assert resp.status_code == 200
        assert "evil.example.com" not in resp.text
        assert "ws://localhost/ws/twilio/" in resp.text

    async def test_stream_url_includes_ticket_parameter(self, client: AsyncClient):
        """FINDING-003: a signed stream ticket must accompany the agent_id
        parameter so the WebSocket can authenticate the connection."""
        resp = await client.post("/api/studies", json={"title": "Twilio Ticket Test"})
        study_id = resp.json()["id"]
        agent_resp = await client.post(
            f"/api/studies/{study_id}/agents",
            json={"name": "Twilio Agent", "status": "active"},
        )
        agent_id = agent_resp.json()["id"]

        resp = await _post_signed(
            client, f"/api/twilio/voice/{agent_id}", {"From": "+15559876543"}
        )
        assert resp.status_code == 200
        assert 'Parameter name="ticket"' in resp.text


class TestTwilioEndpoints:
    async def test_voice_webhook_active_agent(self, client: AsyncClient):
        """The voice webhook should return TwiML that connects to a WebSocket."""
        # Create a study and agent
        resp = await client.post("/api/studies", json={"title": "Twilio Test"})
        study_id = resp.json()["id"]

        agent_resp = await client.post(
            f"/api/studies/{study_id}/agents",
            json={
                "name": "Twilio Agent",
                "status": "active",
                "twilio_phone_number": "+15551234567",
            },
        )
        agent_id = agent_resp.json()["id"]

        # Call the voice webhook
        resp = await _post_signed(
            client,
            f"/api/twilio/voice/{agent_id}",
            {"From": "+15559876543", "CallSid": "CA1234567890"},
        )
        # Should return TwiML XML
        assert resp.status_code == 200
        content_type = resp.headers.get("content-type", "")
        assert "xml" in content_type
        assert "<Response>" in resp.text
        assert "Stream" in resp.text

    async def test_voice_webhook_nonexistent_agent(self, client: AsyncClient):
        fake_id = str(uuid.uuid4())
        resp = await _post_signed(
            client, f"/api/twilio/voice/{fake_id}", {"From": "+15559876543"}
        )
        # Should return TwiML that says agent is unavailable (still 200)
        assert resp.status_code == 200
        assert "Sorry" in resp.text or "unavailable" in resp.text

    async def test_voice_webhook_inactive_agent(self, client: AsyncClient):
        """A draft agent should not be connectable via Twilio."""
        resp = await client.post("/api/studies", json={"title": "Twilio Inactive"})
        study_id = resp.json()["id"]

        agent_resp = await client.post(
            f"/api/studies/{study_id}/agents",
            json={"name": "Draft Agent", "status": "draft"},
        )
        agent_id = agent_resp.json()["id"]

        resp = await _post_signed(
            client, f"/api/twilio/voice/{agent_id}", {"From": "+15559876543"}
        )
        # Should indicate agent is unavailable
        assert resp.status_code == 200
        assert "unavailable" in resp.text or "Sorry" in resp.text

    async def test_voice_webhook_rejects_text_agent(self, client: AsyncClient):
        study = await client.post("/api/studies", json={"title": "Twilio Text"})
        agent = await client.post(
            f"/api/studies/{study.json()['id']}/agents",
            json={"name": "Text Agent", "modality": "text"},
        )
        agent_id = agent.json()["id"]

        resp = await _post_signed(client, f"/api/twilio/voice/{agent_id}", {})

        assert resp.status_code == 200
        assert "not currently available" in resp.text

    async def test_voice_webhook_routes_by_to_number(self, client: AsyncClient):
        """When the To number matches another agent, that agent's id is used."""
        resp = await client.post("/api/studies", json={"title": "Twilio To Routing"})
        study_id = resp.json()["id"]

        # Two active agents, distinct Twilio numbers
        a_resp = await client.post(
            f"/api/studies/{study_id}/agents",
            json={
                "name": "Agent A",
                "status": "active",
                "twilio_phone_number": "+15551110000",
            },
        )
        a_id = a_resp.json()["id"]

        b_resp = await client.post(
            f"/api/studies/{study_id}/agents",
            json={
                "name": "Agent B",
                "status": "active",
                "twilio_phone_number": "+15552220000",
            },
        )
        b_id = b_resp.json()["id"]

        # Call agent A's URL but with To=Agent B's number → should resolve to B
        resp = await _post_signed(
            client,
            f"/api/twilio/voice/{a_id}",
            {"From": "+15559876543", "To": "+15552220000", "CallSid": "CA0001"},
        )
        assert resp.status_code == 200
        assert b_id in resp.text
        assert a_id not in resp.text or resp.text.count(a_id) == 0

    async def test_voice_webhook_to_number_normalization(self, client: AsyncClient):
        """Routing should ignore spaces / dashes in the To number."""
        resp = await client.post("/api/studies", json={"title": "Twilio Normalize"})
        study_id = resp.json()["id"]

        a_resp = await client.post(
            f"/api/studies/{study_id}/agents",
            json={
                "name": "Agent X",
                "status": "active",
                "twilio_phone_number": "+1 (555) 333-0000",
            },
        )
        a_id = a_resp.json()["id"]

        fake_id = str(uuid.uuid4())
        resp = await _post_signed(
            client,
            f"/api/twilio/voice/{fake_id}",
            {"From": "+15559876543", "To": "+15553330000"},
        )
        assert resp.status_code == 200
        assert a_id in resp.text


class TestNormalizeE164:
    def test_basic(self):
        from app.api.twilio import _normalize_e164

        assert _normalize_e164("+15551234567") == "+15551234567"
        assert _normalize_e164("15551234567") == "+15551234567"
        assert _normalize_e164("+1 (555) 123-4567") == "+15551234567"
        assert _normalize_e164("") == ""
        assert _normalize_e164(None) == ""


class TestStreamTicket:
    """FINDING-003: short-lived, single-purpose ticket authorizing a media
    stream WebSocket connection for a specific agent."""

    def test_round_trip(self):
        from app.api.twilio import _create_stream_ticket, _verify_stream_ticket

        agent_id = str(uuid.uuid4())
        ticket = _create_stream_ticket(agent_id)
        assert _verify_stream_ticket(ticket, agent_id) is True

    def test_rejects_wrong_agent(self):
        from app.api.twilio import _create_stream_ticket, _verify_stream_ticket

        ticket = _create_stream_ticket(str(uuid.uuid4()))
        assert _verify_stream_ticket(ticket, str(uuid.uuid4())) is False

    def test_rejects_garbage_ticket(self):
        from app.api.twilio import _verify_stream_ticket

        assert _verify_stream_ticket("not-a-jwt", str(uuid.uuid4())) is False

    def test_rejects_missing_ticket(self):
        from app.api.twilio import _verify_stream_ticket

        assert _verify_stream_ticket(None, str(uuid.uuid4())) is False
        assert _verify_stream_ticket("", str(uuid.uuid4())) is False

    def test_rejects_expired_ticket(self):
        from app.api.twilio import _STREAM_TICKET_ALGORITHM, _verify_stream_ticket

        agent_id = str(uuid.uuid4())
        expired_payload = {
            "agent_id": agent_id,
            "purpose": "twilio_stream",
            "iat": int(time.time()) - 120,
            "exp": int(time.time()) - 60,
        }
        expired_ticket = jwt.encode(
            expired_payload, settings.secret_key, algorithm=_STREAM_TICKET_ALGORITHM
        )
        assert _verify_stream_ticket(expired_ticket, agent_id) is False

    def test_rejects_wrong_purpose(self):
        """A token minted for a different purpose (e.g. an admin JWT) must
        never authorize a stream connection."""
        from app.api.twilio import _STREAM_TICKET_ALGORITHM, _verify_stream_ticket

        agent_id = str(uuid.uuid4())
        payload = {
            "agent_id": agent_id,
            "purpose": "something_else",
            "iat": int(time.time()),
            "exp": int(time.time()) + 60,
        }
        ticket = jwt.encode(
            payload, settings.secret_key, algorithm=_STREAM_TICKET_ALGORITHM
        )
        assert _verify_stream_ticket(ticket, agent_id) is False


class TestTwilioWebhookRateLimiting:
    """FINDING-005 (Revision 2): no rate limiting existed on the voice
    webhook. Limits are patched down to a small number for fast tests."""

    async def test_blocked_after_limit_exceeded(self, client: AsyncClient, monkeypatch):
        """test_REQ_SEC_FINDING_005_webhook_rate_limited"""
        import app.api.twilio as twilio_module

        monkeypatch.setattr(twilio_module, "_WEBHOOK_RATE_LIMIT", (2, 60))

        fake_id = str(uuid.uuid4())
        form = {"From": "+15559876543"}
        path = f"/api/twilio/voice/{fake_id}"

        for _ in range(2):
            resp = await client.post(
                path, data=form, headers=_signed_headers(path, form)
            )
            assert resp.status_code != 429

        resp = await client.post(path, data=form, headers=_signed_headers(path, form))
        assert resp.status_code == 429
        assert "Retry-After" in resp.headers

    async def test_rate_limit_checked_before_signature_validation(
        self, client: AsyncClient, monkeypatch
    ):
        """Rate limiting must apply even to unsigned/garbage requests —
        otherwise it does nothing to bound a flood from an attacker who
        never has a valid signature."""
        import app.api.twilio as twilio_module

        monkeypatch.setattr(twilio_module, "_WEBHOOK_RATE_LIMIT", (2, 60))

        fake_id = str(uuid.uuid4())
        for _ in range(2):
            resp = await client.post(
                f"/api/twilio/voice/{fake_id}", data={"From": "+1555"}
            )
            assert resp.status_code == 403  # bad signature, but not rate-limited yet

        resp = await client.post(
            f"/api/twilio/voice/{fake_id}", data={"From": "+1555"}
        )
        assert resp.status_code == 429


class TestTwilioMediaStreamRateLimiting:
    """FINDING-005 (Revision 2): no per-source connection cap existed on
    the media-stream WebSocket, and accept() ran before any check."""

    def test_connection_rejected_before_accept_when_over_limit(
        self, fake_redis, monkeypatch
    ):
        """test_REQ_SEC_FINDING_005_ws_connection_cap"""
        import uuid as _uuid

        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from starlette.websockets import WebSocketDisconnect

        import app.api.twilio as twilio_module
        import app.rate_limit as rate_limit_module

        monkeypatch.setattr(twilio_module, "_WS_RATE_LIMIT", (1, 60))

        async def _fake_get_redis():
            return fake_redis

        monkeypatch.setattr(rate_limit_module, "get_redis", _fake_get_redis)

        test_app = FastAPI()
        test_app.include_router(twilio_module.router)

        with TestClient(test_app) as tc:
            agent_id = str(_uuid.uuid4())
            # First connection consumes the single allowed slot, then
            # disconnects immediately without completing the handshake data.
            with tc.websocket_connect(f"/ws/twilio/{agent_id}"):
                pass

            # Second connection from the same client must be rejected
            # before accept() — a disconnect with a non-1000 close code.
            with pytest.raises(WebSocketDisconnect) as excinfo:
                with tc.websocket_connect(f"/ws/twilio/{agent_id}") as ws:
                    ws.receive_json()
            assert excinfo.value.code == 1013
