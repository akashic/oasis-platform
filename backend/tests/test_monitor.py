"""
Tests for the live transcript monitor WebSocket — focused on the auth gate.

The monitor endpoint is mounted at ``/ws/monitor/{session_id}``.

FINDING-001 remediation: this endpoint streams participant PII (verbatim
transcripts), so it must reject connections without a valid credential
*unconditionally* — independent of the admin dashboard's ``AUTH_ENABLED``
toggle. Previously it only enforced this when ``AUTH_ENABLED`` was true,
which meant the default (disabled) posture streamed live transcripts to
anyone who knew or guessed a session id.

FINDING-008 remediation: the credential is a short-lived (60s), single-use
ticket minted by ``POST /api/auth/monitor-ticket`` (see test_auth.py),
passed as ``?ticket=``, rather than the long-lived admin JWT itself.

We only test the gate itself: actual backfill and live-streaming behaviour
is exercised end-to-end in higher-level tests. Using a non-existent
session id lets us assert the WS was upgraded (server sends an in-band
error and closes 4004) vs rejected before upgrade (4401).
"""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import fakeredis.aioredis
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

import app.api.monitor as monitor_module
import app.auth as auth_module
from app.api.monitor import router as monitor_router
from app.auth import create_monitor_ticket
from app.config import settings


@pytest.fixture
def fake_redis(monkeypatch):
    """Route app.auth's Redis calls (ticket single-use tracking) to a fake
    in-memory client, isolated per test."""
    redis = fakeredis.aioredis.FakeRedis(decode_responses=True)

    async def _get_redis():
        return redis

    monkeypatch.setattr(auth_module, "get_redis", _get_redis)
    yield redis


@pytest.fixture
def app_no_lifespan(monkeypatch, fake_redis) -> FastAPI:
    """Minimal FastAPI app with just the monitor router and no lifespan.

    We replace ``async_session_factory`` with a stub that always yields a
    session whose ``execute`` returns no rows so the handler immediately
    sends ``Session not found`` and closes — no real DB needed.
    """
    fake_result = MagicMock()
    fake_result.scalar_one_or_none = MagicMock(return_value=None)

    fake_session = MagicMock()
    fake_session.execute = AsyncMock(return_value=fake_result)

    @asynccontextmanager
    async def _fake_factory_cm():
        yield fake_session

    def _fake_factory():
        return _fake_factory_cm()

    monkeypatch.setattr(monitor_module, "async_session_factory", _fake_factory)

    app = FastAPI()
    app.include_router(monitor_router)
    return app


@pytest.fixture
def fresh_session_id() -> str:
    """A random UUID — the session won't exist in the DB."""
    return str(uuid.uuid4())


class TestMonitorAuthUnconditional:
    """AUTH_ENABLED=false must NOT bypass the monitor's ticket check.

    test_REQ_SEC_FINDING_001_monitor_requires_token_when_auth_disabled
    """

    def setup_method(self, _method):
        self._was_enabled = settings.auth_enabled
        settings.auth_enabled = False

    def teardown_method(self, _method):
        settings.auth_enabled = self._was_enabled

    def test_missing_ticket_rejected_even_with_auth_disabled(
        self, app_no_lifespan, fresh_session_id
    ):
        assert settings.auth_enabled is False
        with TestClient(app_no_lifespan) as tc:
            with pytest.raises(WebSocketDisconnect) as excinfo:
                with tc.websocket_connect(f"/ws/monitor/{fresh_session_id}") as ws:
                    ws.receive_json()
            assert excinfo.value.code == 4401

    def test_valid_ticket_still_passes_gate_with_auth_disabled(
        self, app_no_lifespan, fresh_session_id
    ):
        # A valid ticket is still honoured when AUTH_ENABLED=false — only
        # the "no credential at all" bypass is closed.
        ticket = create_monitor_ticket(fresh_session_id)
        with TestClient(app_no_lifespan) as tc:
            with tc.websocket_connect(
                f"/ws/monitor/{fresh_session_id}?ticket={ticket}"
            ) as ws:
                msg = ws.receive_json()
                assert msg["type"] == "error"
                assert "Session not found" in msg["message"]


class TestMonitorAuthEnabled:
    def setup_method(self, _method):
        self._was_enabled = settings.auth_enabled
        settings.auth_enabled = True

    def teardown_method(self, _method):
        settings.auth_enabled = self._was_enabled

    def test_missing_ticket_is_rejected(self, app_no_lifespan, fresh_session_id):
        with TestClient(app_no_lifespan) as tc:
            with pytest.raises(WebSocketDisconnect) as excinfo:
                with tc.websocket_connect(
                    f"/ws/monitor/{fresh_session_id}"
                ) as ws:
                    ws.receive_json()
            assert excinfo.value.code == 4401

    def test_garbage_ticket_is_rejected(self, app_no_lifespan, fresh_session_id):
        with TestClient(app_no_lifespan) as tc:
            with pytest.raises(WebSocketDisconnect) as excinfo:
                with tc.websocket_connect(
                    f"/ws/monitor/{fresh_session_id}?ticket=not-a-jwt"
                ) as ws:
                    ws.receive_json()
            assert excinfo.value.code == 4401

    def test_ticket_for_different_session_is_rejected(
        self, app_no_lifespan, fresh_session_id
    ):
        """test_REQ_SEC_FINDING_008_monitor_ticket_scoped_to_session"""
        other_session_id = str(uuid.uuid4())
        ticket = create_monitor_ticket(other_session_id)
        with TestClient(app_no_lifespan) as tc:
            with pytest.raises(WebSocketDisconnect) as excinfo:
                with tc.websocket_connect(
                    f"/ws/monitor/{fresh_session_id}?ticket={ticket}"
                ) as ws:
                    ws.receive_json()
            assert excinfo.value.code == 4401

    def test_valid_ticket_passes_gate(self, app_no_lifespan, fresh_session_id):
        # Valid ticket → the gate accepts the upgrade. Since the session
        # doesn't exist, the server then sends an in-band error frame and
        # closes with 4004 — proving the auth gate let it through.
        ticket = create_monitor_ticket(fresh_session_id)
        with TestClient(app_no_lifespan) as tc:
            with tc.websocket_connect(
                f"/ws/monitor/{fresh_session_id}?ticket={ticket}"
            ) as ws:
                msg = ws.receive_json()
                assert msg["type"] == "error"
                assert "Session not found" in msg["message"]

    def test_ticket_cannot_be_replayed(self, app_no_lifespan, fresh_session_id):
        """test_REQ_SEC_FINDING_008_monitor_ticket_single_use

        A captured URL — the exact scenario the finding is about (proxy
        logs, browser history) — must not be reusable even within its TTL.
        """
        ticket = create_monitor_ticket(fresh_session_id)
        with TestClient(app_no_lifespan) as tc:
            # First use succeeds (gate passes; session lookup fails → 4004).
            with tc.websocket_connect(
                f"/ws/monitor/{fresh_session_id}?ticket={ticket}"
            ) as ws:
                ws.receive_json()

            # Second use of the *same* ticket must be rejected outright.
            with pytest.raises(WebSocketDisconnect) as excinfo:
                with tc.websocket_connect(
                    f"/ws/monitor/{fresh_session_id}?ticket={ticket}"
                ) as ws:
                    ws.receive_json()
            assert excinfo.value.code == 4401
