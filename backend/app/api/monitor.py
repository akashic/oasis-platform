"""
OASIS — Real-time transcript monitor WebSocket.

Researchers connect to:
    wss://host/ws/monitor/{session_id}?ticket=<single-use ticket>

FINDING-001: this endpoint streams verbatim participant transcripts (PII),
so it always requires a valid credential — regardless of the admin
dashboard's ``AUTH_ENABLED`` toggle. Connections without one are rejected
with WS close code 4401.

FINDING-008: the credential is no longer the long-lived admin JWT itself.
Browser WebSocket APIs cannot send custom headers, so a JWT accepted
directly in the query string was previously exposed to proxy/CDN/browser
logs for its full (now 2h) lifetime with no way to revoke it. Callers now
call ``POST /api/auth/monitor-ticket`` (an authenticated REST request) to
exchange their admin token for a ticket that is valid for 60 seconds and
can be used exactly once — a captured URL is worthless almost immediately
and cannot be replayed even within that window.

The endpoint streams transcript entries as they are logged by the pipeline.
It also sends the existing transcript first so the researcher sees
the full conversation up to this point.
"""

from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.auth import consume_monitor_ticket
from app.database import async_session_factory
from app.models.session import Session, SessionStatus, TranscriptEntry
from app.realtime import subscribe_transcript

router = APIRouter()


@router.websocket("/ws/monitor/{session_id}")
async def monitor_ws(
    websocket: WebSocket,
    session_id: str,
    ticket: str | None = None,
):
    """
    Real-time transcript monitor for researchers.

    1. Sends the full existing transcript (backfill)
    2. Streams new entries via Redis pub/sub as they arrive
    3. Sends a 'session_ended' event when the session finishes
    """
    # ── Auth check (before accept so we can reject with a close code) ──
    # FINDING-001: unconditional — this plane carries PII independently of
    # whether the admin dashboard's AUTH_ENABLED toggle is set.
    # FINDING-008: a short-lived, single-use ticket rather than the raw JWT.
    if not await consume_monitor_ticket(ticket, session_id):
        # Per RFC 6455, custom close codes 4000-4999 are application defined.
        # 4401 is the de-facto convention for "WebSocket Unauthorized".
        await websocket.close(code=4401)
        logger.warning(
            f"Monitor rejected for session {session_id}: missing/invalid/"
            "expired/already-used ticket"
        )
        return

    await websocket.accept()
    logger.info(f"Monitor connected for session {session_id}")

    try:
        # ── 1. Backfill existing transcript ─────────────────────────
        async with async_session_factory() as db:
            result = await db.execute(
                select(Session)
                .where(Session.id == UUID(session_id))
                .options(selectinload(Session.entries))
            )
            session = result.scalar_one_or_none()

            if not session:
                await websocket.send_json({"type": "error", "message": "Session not found"})
                await websocket.close(code=4004)
                return

            # Send session metadata
            await websocket.send_json({
                "type": "session_info",
                "session_id": str(session.id),
                "agent_id": str(session.agent_id),
                "status": session.status.value,
                "created_at": session.created_at.isoformat(),
            })

            # Send existing transcript entries
            for entry in session.entries:
                await websocket.send_json({
                    "type": "transcript",
                    "role": entry.role.value,
                    "content": entry.content,
                    "sequence": entry.sequence,
                    "spoken_at": entry.spoken_at.isoformat(),
                })

            is_active = session.status == SessionStatus.ACTIVE

        if not is_active:
            # Session already finished — send end signal and close
            await websocket.send_json({
                "type": "session_ended",
                "status": session.status.value,
            })
            await websocket.close()
            return

        # ── 2. Stream live updates via Redis pub/sub ────────────────
        async for event in subscribe_transcript(session_id):
            await websocket.send_json(event)

            # If the session ended, break out of the loop
            if event.get("type") == "session_ended":
                break

    except WebSocketDisconnect:
        logger.info(f"Monitor disconnected for session {session_id}")
    except Exception as exc:
        logger.exception(f"Monitor error for session {session_id}: {exc}")
    finally:
        logger.info(f"Monitor WebSocket closed for session {session_id}")
