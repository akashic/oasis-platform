"""
Tests for the Twilio media-stream WebSocket's ticket gate (FINDING-003).

The endpoint must accept() (Twilio's protocol requires reading the "start"
frame after upgrade), but it must verify the signed stream ticket carried
in that frame's customParameters *before* resolving the agent, creating a
Session row, or booting a pipeline. We only test the gate here — full
pipeline behaviour is out of scope for these tests (no Twilio account or
LLM/STT/TTS providers needed).
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.api.twilio import _create_stream_ticket, router as twilio_router


@pytest.fixture
def twilio_app(fake_redis, monkeypatch) -> FastAPI:
    # FINDING-005: the media-stream WebSocket now checks a per-source
    # connection-rate limit (via app/rate_limit.py) before accept(). This
    # standalone app (unlike the `app` fixture in conftest.py) doesn't go
    # through the full dependency-override wiring, so patch the Redis
    # accessor `app.rate_limit` uses directly.
    import app.rate_limit as _rate_limit_module

    async def _fake_get_redis():
        return fake_redis

    monkeypatch.setattr(_rate_limit_module, "get_redis", _fake_get_redis)

    app = FastAPI()
    app.include_router(twilio_router)
    return app


class TestTwilioStreamTicketGate:
    def test_missing_ticket_closes_connection(self, twilio_app):
        """test_REQ_SEC_FINDING_003_ws_rejects_missing_ticket"""
        agent_id = str(uuid.uuid4())
        with TestClient(twilio_app) as tc:
            with pytest.raises(WebSocketDisconnect) as excinfo:
                with tc.websocket_connect(f"/ws/twilio/{agent_id}") as ws:
                    ws.send_json({"event": "connected", "protocol": "Call"})
                    ws.send_json(
                        {
                            "event": "start",
                            "start": {
                                "streamSid": "SS1",
                                "callSid": "CA1",
                                "customParameters": {},
                            },
                        }
                    )
                    ws.receive_json()
            assert excinfo.value.code == 4401

    def test_ticket_for_different_agent_closes_connection(self, twilio_app):
        """test_REQ_SEC_FINDING_003_ws_rejects_ticket_for_wrong_agent"""
        agent_id = str(uuid.uuid4())
        ticket_for_other_agent = _create_stream_ticket(str(uuid.uuid4()))
        with TestClient(twilio_app) as tc:
            with pytest.raises(WebSocketDisconnect) as excinfo:
                with tc.websocket_connect(f"/ws/twilio/{agent_id}") as ws:
                    ws.send_json(
                        {
                            "event": "start",
                            "start": {
                                "streamSid": "SS1",
                                "callSid": "CA1",
                                "customParameters": {"ticket": ticket_for_other_agent},
                            },
                        }
                    )
                    ws.receive_json()
            assert excinfo.value.code == 4401

    def test_garbage_ticket_closes_connection(self, twilio_app):
        agent_id = str(uuid.uuid4())
        with TestClient(twilio_app) as tc:
            with pytest.raises(WebSocketDisconnect) as excinfo:
                with tc.websocket_connect(f"/ws/twilio/{agent_id}") as ws:
                    ws.send_json(
                        {
                            "event": "start",
                            "start": {
                                "streamSid": "SS1",
                                "callSid": "CA1",
                                "customParameters": {"ticket": "not-a-jwt"},
                            },
                        }
                    )
                    ws.receive_json()
            assert excinfo.value.code == 4401
