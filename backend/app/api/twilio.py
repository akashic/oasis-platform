"""
OASIS — Twilio integration endpoints.

Provides two endpoints for Twilio Media Streams:

1. POST /api/twilio/voice/{agent_id}
   - TwiML webhook that Twilio calls when a phone call comes in.
   - Returns TwiML XML that connects the call to our WebSocket.

2. WS /ws/twilio/{agent_id}
   - WebSocket endpoint that handles Twilio Media Streams protocol.
   - Receives μ-law 8kHz audio from Twilio, converts to PCM16,
     runs through Pipecat pipeline, and sends audio back.

Setup:
  1. Configure your Twilio phone number's Voice webhook to point to:
       https://your-domain.com/api/twilio/voice/{agent_id}
  2. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN in your .env

FINDING-003 remediation: the webhook validates Twilio's ``X-Twilio-Signature``
before doing anything else, and the returned ``<Stream>`` URL is built from
the trusted, operator-configured ``DOMAIN`` setting rather than the
inbound (attacker-controllable) ``Host`` header. The webhook also mints a
short-lived, single-use signed "stream ticket" and passes it to the media
stream as a ``<Parameter>``; the WebSocket endpoint verifies it before
creating any Session row or booting the pipeline.
"""

import asyncio
import json
import secrets
import time
import uuid
from datetime import datetime, timezone

import jwt
from fastapi import APIRouter, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from loguru import logger
from sqlalchemy import select
from twilio.request_validator import RequestValidator

from app.config import settings
from app.database import async_session_factory
from app.models.agent import Agent, AgentStatus, ParticipantIdMode
from app.models.session import Session, SessionStatus, aggregate_session_tokens
from app.providers.validate import validate_agent_pipeline_config
from app.rate_limit import check_fixed_window
from app.realtime import publish_transcript_event

router = APIRouter()

# Maximum pipeline runtime (seconds)
_MAX_PIPELINE_SECONDS = 7200

# FINDING-005 (Revision 2): no limiter of any kind previously existed on
# either the voice webhook or the media-stream WebSocket. Limits are
# generous — Twilio's own signature/ticket checks are the real defense —
# these exist to cap the resource cost (connection slots, log volume,
# DB writes) of a flood from a single source.
_WEBHOOK_RATE_LIMIT = (60, 60)  # 60 requests / 60s per source IP
_WS_RATE_LIMIT = (30, 60)  # 30 connection attempts / 60s per source IP

# Stream ticket signing (FINDING-003) — short-lived, single-purpose JWT
# minted by the (now signature-verified) voice webhook and checked by the
# media-stream WebSocket before it creates a Session or boots a pipeline.
_STREAM_TICKET_TTL_SECONDS = 60
_STREAM_TICKET_ALGORITHM = "HS256"
_STREAM_TICKET_PURPOSE = "twilio_stream"

_LOCAL_HOSTS = ("localhost", "127.0.0.1")


def _public_webhook_url(request: Request) -> str:
    """Reconstruct the exact public URL Twilio signed.

    Uses the operator-configured ``DOMAIN`` setting rather than the inbound
    ``Host`` header, which is attacker-controllable and previously drove
    both the returned ``<Stream>`` URL and (if used here) signature
    validation itself.
    """
    scheme = "http" if settings.domain in _LOCAL_HOSTS else "https"
    return f"{scheme}://{settings.domain}{request.url.path}"


def _validate_twilio_signature(request: Request, form) -> bool:
    """Validate ``X-Twilio-Signature`` against the trusted webhook URL.

    Fails closed: returns False (never raises) when TWILIO_AUTH_TOKEN is
    unset, the header is missing, or the signature does not match.
    """
    if not settings.twilio_auth_token:
        logger.error("Twilio webhook rejected: TWILIO_AUTH_TOKEN is not configured")
        return False

    signature = request.headers.get("X-Twilio-Signature", "")
    if not signature:
        return False

    validator = RequestValidator(settings.twilio_auth_token)
    return validator.validate(_public_webhook_url(request), form, signature)


def _create_stream_ticket(agent_id: str) -> str:
    """Mint a short-lived, single-purpose ticket authorizing exactly one
    media-stream connection for ``agent_id``."""
    payload = {
        "agent_id": agent_id,
        "purpose": _STREAM_TICKET_PURPOSE,
        "iat": int(time.time()),
        "exp": int(time.time()) + _STREAM_TICKET_TTL_SECONDS,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=_STREAM_TICKET_ALGORITHM)


def _verify_stream_ticket(ticket: str | None, agent_id: str) -> bool:
    """Verify a stream ticket was issued for this exact ``agent_id`` and
    has not expired or been tampered with."""
    if not ticket:
        return False
    try:
        payload = jwt.decode(
            ticket, settings.secret_key, algorithms=[_STREAM_TICKET_ALGORITHM]
        )
    except jwt.InvalidTokenError:
        return False
    return (
        payload.get("purpose") == _STREAM_TICKET_PURPOSE
        and payload.get("agent_id") == agent_id
    )


def _normalize_e164(value: str | None) -> str:
    """Normalize a phone number for comparison.

    Strips spaces, dashes and parentheses; ensures a leading ``+``. Empty
    inputs return ``""`` so they never match.
    """
    if not value:
        return ""
    cleaned = "".join(c for c in value if c.isdigit() or c == "+")
    if not cleaned:
        return ""
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned
    return cleaned


async def _resolve_twilio_agent(
    db, agent_id: str, called_number: str | None
) -> Agent | None:
    """Resolve the agent for an inbound Twilio call.

    Preference order:
      1. An ACTIVE agent whose ``twilio_phone_number`` matches the called
         number (E.164 normalized). Useful when several agents share the
         same backend webhook URL but use different Twilio numbers.
      2. The ACTIVE agent identified by ``agent_id`` in the URL path.
    """
    normalized = _normalize_e164(called_number)
    if normalized:
        result = await db.execute(
            select(Agent).where(Agent.status == AgentStatus.ACTIVE.value)
        )
        for candidate in result.scalars().all():
            if _normalize_e164(candidate.twilio_phone_number) == normalized:
                return candidate

    result = await db.execute(
        select(Agent).where(
            Agent.id == uuid.UUID(agent_id),
            Agent.status == AgentStatus.ACTIVE.value,
        )
    )
    return result.scalar_one_or_none()


async def _agent_config_errors(agent: Agent) -> list[str]:
    modality = (
        agent.modality.value if hasattr(agent.modality, "value") else agent.modality
    )
    pipeline_type = (
        agent.pipeline_type.value
        if hasattr(agent.pipeline_type, "value")
        else agent.pipeline_type
    )
    return await validate_agent_pipeline_config(
        modality=modality,
        pipeline_type=pipeline_type,
        llm_model=agent.llm_model,
        stt_provider=agent.stt_provider,
        stt_model=agent.stt_model,
        tts_provider=agent.tts_provider,
        tts_model=agent.tts_model,
        tts_voice=agent.tts_voice,
    )


@router.post("/api/twilio/voice/{agent_id}")
async def twilio_voice_webhook(agent_id: str, request: Request):
    """
    TwiML webhook that Twilio calls when a phone call arrives.

    Returns TwiML XML instructing Twilio to connect the call to
    our WebSocket endpoint via Media Streams.
    """
    # FINDING-005: rate limit by source IP before doing any work at all
    # (signature validation still runs afterwards and is the real gate).
    client_ip = request.client.host if request.client else "unknown"
    limit, window = _WEBHOOK_RATE_LIMIT
    allowed, retry_after = await check_fixed_window(
        f"twilio:webhook:{client_ip}", limit=limit, window_seconds=window
    )
    if not allowed:
        logger.warning(f"Twilio webhook rate-limited: ip={client_ip}")
        raise HTTPException(
            status_code=429,
            detail="Too many requests",
            headers={"Retry-After": str(retry_after)},
        )

    # FINDING-003: verify this request actually came from Twilio before
    # doing anything else — agent lookup, To-number routing and TwiML
    # generation are all gated on a valid signature.
    try:
        form = await request.form()
    except Exception:
        form = {}

    if not _validate_twilio_signature(request, form):
        logger.warning(
            f"Twilio webhook rejected for agent {agent_id}: missing/invalid "
            "X-Twilio-Signature"
        )
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    # Twilio posts the called number as the ``To`` form field. We use this
    # to route to the right agent when several share the same webhook URL.
    called_number = form.get("To")

    async with async_session_factory() as db:
        agent = await _resolve_twilio_agent(db, agent_id, called_number)

    modality = (
        agent.modality.value
        if agent and hasattr(agent.modality, "value")
        else agent.modality if agent else None
    )
    if not agent or modality != "voice" or await _agent_config_errors(agent):
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say>Sorry, this interview agent is not currently available. Please try again later.</Say>
  <Hangup/>
</Response>"""
        return Response(content=twiml, media_type="application/xml")

    # Build the WebSocket URL using the resolved agent's id (which may
    # differ from the path's agent_id if To-number routing matched).
    # FINDING-003: built from the trusted, operator-configured DOMAIN
    # setting — never from the inbound (forgeable) Host header.
    resolved_agent_id = str(agent.id)
    ws_scheme = "ws" if settings.domain in _LOCAL_HOSTS else "wss"
    ws_url = f"{ws_scheme}://{settings.domain}/ws/twilio/{resolved_agent_id}"

    # Short-lived, single-purpose ticket the media-stream WebSocket must
    # present in its "start" event before we create a Session or boot a
    # pipeline for it.
    ticket = _create_stream_ticket(resolved_agent_id)

    logger.info(
        f"Twilio voice webhook: path_agent={agent_id}, resolved_agent={resolved_agent_id}, "
        f"called_number={called_number}, ws_url={ws_url}"
    )

    # Return TwiML that connects the call to our WebSocket
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Connect>
    <Stream url="{ws_url}">
      <Parameter name="agent_id" value="{resolved_agent_id}" />
      <Parameter name="ticket" value="{ticket}" />
    </Stream>
  </Connect>
</Response>"""

    return Response(content=twiml, media_type="application/xml")


@router.websocket("/ws/twilio/{agent_id}")
async def twilio_media_stream(websocket: WebSocket, agent_id: str):
    """
    WebSocket endpoint for Twilio Media Streams.

    Twilio connects here after the TwiML <Connect><Stream> instruction.
    The protocol flow:
      1. Twilio sends a "connected" event
      2. Twilio sends a "start" event with streamSid, callSid, etc.
      3. Twilio sends "media" events with base64 μ-law audio
      4. We send "media" events back with base64 μ-law audio
      5. Twilio sends a "stop" event when the call ends
    """
    # FINDING-005 (Revision 2): per-source connection cap, checked BEFORE
    # accept() so an excess connection from a given IP never holds a slot
    # at all (closing pre-accept sends a plain "websocket.close" ASGI
    # message rather than completing the handshake).
    client_ip = websocket.client.host if websocket.client else "unknown"
    limit, window = _WS_RATE_LIMIT
    allowed, retry_after = await check_fixed_window(
        f"twilio:ws:{client_ip}", limit=limit, window_seconds=window
    )
    if not allowed:
        logger.warning(f"Twilio media-stream WebSocket rate-limited: ip={client_ip}")
        await websocket.close(code=1013, reason="Too many requests")
        return

    await websocket.accept()

    # ── 1. Wait for Twilio's initial handshake events ─────────────
    stream_sid = None
    call_sid = None
    custom_params = {}

    try:
        # Read initial messages until we get the "start" event
        while True:
            raw = await asyncio.wait_for(websocket.receive_text(), timeout=10)
            msg = json.loads(raw)
            event = msg.get("event")

            if event == "connected":
                logger.info(f"Twilio connected: protocol={msg.get('protocol')}")
                continue

            if event == "start":
                start_data = msg.get("start", {})
                stream_sid = start_data.get("streamSid")
                call_sid = start_data.get("callSid")
                custom_params = start_data.get("customParameters", {})
                logger.info(
                    f"Twilio stream started: stream_sid={stream_sid}, "
                    f"call_sid={call_sid}, params={custom_params}"
                )
                break

            logger.debug(f"Twilio pre-start event: {event}")

    except asyncio.TimeoutError:
        logger.error("Twilio WebSocket: timed out waiting for start event")
        await websocket.close()
        return
    except WebSocketDisconnect:
        logger.info("Twilio WebSocket: disconnected before start")
        return

    if not stream_sid:
        logger.error("Twilio WebSocket: no stream_sid received")
        await websocket.close()
        return

    # ── 1b. Verify the stream ticket (FINDING-003) ─────────────────
    # Minted by the signature-verified voice webhook. Checked before any
    # Session row is created or pipeline is booted, so an arbitrary
    # WebSocket client that merely emits a Twilio-shaped "start" frame can
    # no longer create fabricated sessions or spend provider API credits.
    ticket = custom_params.get("ticket") if isinstance(custom_params, dict) else None
    if not _verify_stream_ticket(ticket, agent_id):
        logger.warning(
            f"Twilio WebSocket rejected for agent {agent_id}: missing/invalid/"
            "expired stream ticket"
        )
        await websocket.close(code=4401)
        return

    # ── 2. Resolve agent ──────────────────────────────────────────
    async with async_session_factory() as db:
        result = await db.execute(
            select(Agent).where(
                Agent.id == uuid.UUID(agent_id),
                Agent.status == AgentStatus.ACTIVE.value,
            )
        )
        agent = result.scalar_one_or_none()

        if not agent:
            logger.error(f"Twilio: agent {agent_id} not found or inactive")
            await websocket.close(code=4004)
            return

        modality = (
            agent.modality.value if hasattr(agent.modality, "value") else agent.modality
        )
        if modality != "voice":
            await websocket.close(code=4005, reason="Wrong modality")
            return

        pipeline_type = (
            agent.pipeline_type.value
            if hasattr(agent.pipeline_type, "value")
            else agent.pipeline_type
        )
        errors = await _agent_config_errors(agent)
        if errors:
            await websocket.close(code=4006, reason="Invalid agent configuration")
            return

        # Snapshot agent config
        agent_cfg = {
            "id": agent.id,
            "study_id": agent.study_id,
            "system_prompt": agent.system_prompt,
            "welcome_message": agent.welcome_message,
            "pipeline_type": pipeline_type,
            "llm_model": agent.llm_model,
            "stt_provider": agent.stt_provider,
            "stt_model": agent.stt_model,
            "tts_provider": agent.tts_provider,
            "tts_model": agent.tts_model,
            "tts_voice": agent.tts_voice,
            "turn_detection": getattr(agent, "turn_detection", "local"),
            "language": agent.language,
            "max_duration_seconds": agent.max_duration_seconds,
            "interview_mode": (
                agent.interview_mode.value
                if hasattr(agent.interview_mode, "value")
                else (agent.interview_mode or "free_form")
            ),
            "interview_guide": agent.interview_guide,
        }

        # ── 3. Create session ─────────────────────────────────────
        # For phone calls, use Twilio's callSid as a reference
        participant_id = f"twilio:{call_sid}" if call_sid else secrets.token_urlsafe(8)

        session = Session(
            id=uuid.uuid4(),
            agent_id=agent_cfg["id"],
            status=SessionStatus.ACTIVE,
            participant_id=participant_id,
        )
        db.add(session)
        await db.commit()
        session_id = session.id
        start_time = datetime.now(timezone.utc)

    logger.info(
        f"Twilio interview started: session={session_id}, agent={agent_cfg['id']}, "
        f"call_sid={call_sid}, stream_sid={stream_sid}"
    )

    # ── 4. Build & run Pipecat pipeline with Twilio serializer ────
    final_status = SessionStatus.COMPLETED
    try:
        from pipecat.pipeline.runner import PipelineRunner
        from app.pipeline.runner import build_twilio_pipeline

        async def _notify(payload: dict):
            await publish_transcript_event(str(session_id), payload)

        task = await build_twilio_pipeline(
            websocket=websocket,
            session_id=session_id,
            system_prompt=agent_cfg["system_prompt"],
            welcome_message=agent_cfg["welcome_message"],
            pipeline_type=agent_cfg["pipeline_type"],
            llm_model=agent_cfg["llm_model"],
            stt_provider=agent_cfg["stt_provider"],
            stt_model=agent_cfg["stt_model"],
            tts_provider=agent_cfg["tts_provider"],
            tts_model=agent_cfg["tts_model"],
            tts_voice=agent_cfg["tts_voice"],
            language=agent_cfg["language"],
            max_duration_seconds=agent_cfg["max_duration_seconds"],
            notify_callback=_notify,
            interview_mode=agent_cfg.get("interview_mode"),
            interview_guide=agent_cfg.get("interview_guide"),
            turn_detection=agent_cfg.get("turn_detection", "local"),
            stream_sid=stream_sid,
            call_sid=call_sid,
            study_id=agent_cfg["study_id"],
        )

        runner = PipelineRunner(handle_sigint=False, handle_sigterm=False)

        timeout = agent_cfg["max_duration_seconds"] or _MAX_PIPELINE_SECONDS
        timeout = min(timeout + 60, _MAX_PIPELINE_SECONDS)
        try:
            await asyncio.wait_for(runner.run(task), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Twilio interview {session_id}: hard timeout after {timeout}s")
            final_status = SessionStatus.TIMED_OUT

    except WebSocketDisconnect:
        logger.info(f"Twilio interview {session_id}: call disconnected")
    except asyncio.CancelledError:
        logger.info(f"Twilio interview {session_id}: task cancelled")
    except Exception as exc:
        logger.exception(f"Twilio interview {session_id}: pipeline error — {exc}")
        final_status = SessionStatus.ERROR
    finally:
        # ── 5. Finalise session ───────────────────────────────────
        try:
            end_time = datetime.now(timezone.utc)
            duration = (end_time - start_time).total_seconds()

            async with async_session_factory() as db:
                sess = await db.get(Session, session_id)
                if sess:
                    sess.status = final_status
                    sess.ended_at = end_time
                    sess.duration_seconds = duration
                    sess.total_tokens = await aggregate_session_tokens(db, session_id)
                    await db.commit()

            await publish_transcript_event(
                str(session_id),
                {
                    "type": "session_ended",
                    "status": final_status.value,
                    "duration_seconds": round(duration, 1),
                },
            )

            logger.info(
                f"Twilio interview ended: session={session_id}, "
                f"status={final_status.value}, duration={duration:.1f}s"
            )
        except Exception as cleanup_exc:
            logger.error(
                f"Twilio interview {session_id}: failed to finalise — {cleanup_exc}"
            )
