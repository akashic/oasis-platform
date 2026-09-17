"""
OASIS — Simple JWT-based authentication.

Provides a basic security layer that can be toggled via environment variables:
  AUTH_ENABLED=true
  AUTH_USERNAME=admin
  AUTH_PASSWORD=your-password

When AUTH_ENABLED is false (default), all routes are accessible without login.

FINDING-008 remediation:
  - Every token carries a `jti`. `POST /api/auth/logout` adds it to a
    Redis-backed denylist for its remaining lifetime, so a leaked or stolen
    token can be revoked before it expires — previously the only way to
    invalidate a token at all was rotating SECRET_KEY and restarting, which
    invalidates every session at once.
  - The access-token lifetime is shortened from 24h to 2h, reducing the
    blast radius of a leaked token now that revocation exists and the
    monitor WebSocket no longer accepts the token itself in a URL (below).
  - The transcript monitor WebSocket no longer accepts the long-lived admin
    bearer token in its `?token=` query string — the single most commonly
    logged/cached/forwarded field in any proxy, CDN, WAF or browser history.
    Callers now exchange an authenticated REST call
    (`POST /api/auth/monitor-ticket`) for a short-lived (60s), single-use
    ticket instead, the same pattern already used for Twilio media streams
    (see app/api/twilio.py).

FINDING-020 remediation: the FINDING-008 monitor ticket above was minted
with the *same* signing key and algorithm as an admin access token,
distinguished only by a `purpose` claim that `verify_token` never checked —
so a captured 60s ticket was a fully general admin bearer credential, and
could mint further tickets indefinitely via `POST /api/auth/monitor-ticket`.
Three independent layers now close this:
  - Access tokens carry `typ: "access"`, which `verify_token` requires.
  - Monitor tickets are signed with a *separate* key, HKDF-derived from
    `settings.secret_key` with a distinct `info` label — a ticket is
    structurally incapable of verifying as an access token regardless of
    any claim it carries.
  - `verify_token` additionally rejects a payload carrying
    `purpose == "monitor_ws"` outright, as defence in depth.
  - Tickets carry `sub` (the operator who minted them, from their own
    access token), logged at mint (`api/auth.py`) and at consume (below),
    closing the "unattributable in the audit trail" gap.
"""

import secrets
import time

import jwt
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger

from app.config import settings
from app.redis import get_redis

# JWT settings
_JWT_ALGORITHM = "HS256"
# FINDING-008: reduced from 24h. No refresh-token rotation yet (tracked as a
# residual — see hand-off report) — 2h balances a materially smaller leaked
# -token window against not forcing an admin to re-authenticate mid-task.
_JWT_EXPIRY_HOURS = 2
# FINDING-020: access tokens are marked with this `typ` claim; `verify_token`
# rejects anything else (including a monitor ticket, defence in depth on top
# of the separate signing key below).
_ACCESS_TOKEN_TYPE = "access"

_security = HTTPBearer(auto_error=False)

# ── Revocation denylist (FINDING-008) ─────────────────────────────────────
_DENYLIST_PREFIX = "oasis:auth:denylist"

# ── Monitor WebSocket tickets (FINDING-008 / FINDING-020) ─────────────────
_MONITOR_TICKET_PURPOSE = "monitor_ws"
_MONITOR_TICKET_TTL_SECONDS = 60
_MONITOR_TICKET_USED_PREFIX = "oasis:auth:monitor-ticket-used"
# FINDING-020: tickets are signed with a key derived from — but distinct
# from — the access-token signing key, via HKDF with a purpose-specific
# `info` label (the same technique `app/crypto.py` uses for the Redis
# credential-encryption key, independent of this use). This makes a ticket
# structurally unverifiable as an access token: `verify_token` uses
# `settings.secret_key` directly, so a ticket JWT fails signature
# verification there regardless of its claims.
_TICKET_HKDF_INFO = b"oasis-monitor-ticket-signing-key-v1"


def _ticket_signing_key() -> str:
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=_TICKET_HKDF_INFO)
    return hkdf.derive(settings.secret_key.encode("utf-8")).hex()


def create_token(username: str) -> str:
    """Create a signed JWT access token for the given username."""
    now = int(time.time())
    payload = {
        "sub": username,
        "typ": _ACCESS_TOKEN_TYPE,
        "jti": secrets.token_urlsafe(16),
        "iat": now,
        "exp": now + (_JWT_EXPIRY_HOURS * 3600),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=_JWT_ALGORITHM)


async def verify_token(token: str) -> dict | None:
    """Verify and decode a JWT access token. Returns the payload or None.

    FINDING-008: also rejects a token whose `jti` has been revoked via
    `revoke_token` (wired up to `POST /api/auth/logout`), even when the
    token's signature and expiry are otherwise still valid.

    FINDING-020: requires `typ: "access"` — a monitor ticket already fails
    signature verification here (it is signed with a different, HKDF
    -derived key), but a missing/wrong `typ` or a `purpose: "monitor_ws"`
    claim is rejected explicitly too, as defence in depth. Tokens minted
    before this change (no `typ` claim) are treated as invalid, forcing one
    re-login rather than trusting an unmarked token indefinitely.
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[_JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

    if payload.get("typ") != _ACCESS_TOKEN_TYPE:
        return None
    if payload.get("purpose") == _MONITOR_TICKET_PURPOSE:
        return None

    jti = payload.get("jti")
    if jti and await _is_revoked(jti):
        return None
    return payload


async def _is_revoked(jti: str) -> bool:
    redis = await get_redis()
    return bool(await redis.exists(f"{_DENYLIST_PREFIX}:{jti}"))


async def revoke_token(payload: dict) -> None:
    """Add a decoded token's `jti` to the Redis denylist for its remaining
    lifetime (FINDING-008). No-op for a payload without a `jti` (should not
    occur for tokens minted by `create_token`)."""
    jti = payload.get("jti")
    if not jti:
        return
    exp = payload.get("exp")
    ttl = max(int(exp - time.time()), 1) if exp else _JWT_EXPIRY_HOURS * 3600
    redis = await get_redis()
    await redis.set(f"{_DENYLIST_PREFIX}:{jti}", "1", ex=ttl)


async def require_auth(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
) -> dict | None:
    """
    FastAPI dependency that enforces authentication when AUTH_ENABLED is true.

    When auth is disabled, returns None (all requests pass).
    When auth is enabled, validates the JWT Bearer token.
    """
    if not settings.auth_enabled:
        return None  # Auth disabled — allow all

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = await verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


async def require_valid_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
) -> dict:
    """FastAPI dependency requiring a valid, non-revoked JWT, unconditionally
    — independent of `AUTH_ENABLED`.

    Used only by `POST /api/auth/monitor-ticket`, mirroring the transcript
    monitor WebSocket's own pre-existing unconditional check (FINDING-001):
    that plane carries participant PII regardless of the admin dashboard's
    auth toggle, so minting a ticket for it must require a real token too.
    """
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Valid token required")
    payload = await verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Valid token required")
    return payload


# ── Monitor WebSocket tickets (FINDING-008 / FINDING-020) ─────────────────

def create_monitor_ticket(session_id: str, *, requested_by: str | None = None) -> str:
    """Mint a short-lived, single-use ticket authorizing exactly one
    connection to the transcript monitor WebSocket for `session_id`.

    Callers must already hold a valid admin token — obtained via an
    authenticated call to `POST /api/auth/monitor-ticket` — so the token
    itself never has to travel in a URL.

    FINDING-020: signed with a key structurally distinct from the access
    -token key (see `_ticket_signing_key`), and binds `sub` to
    `requested_by` (the minting operator's own token `sub`) so the
    connection is attributable — logged here at mint and again in
    `consume_monitor_ticket` at connect time.
    """
    now = int(time.time())
    payload = {
        "session_id": session_id,
        "purpose": _MONITOR_TICKET_PURPOSE,
        "jti": secrets.token_urlsafe(16),
        "iat": now,
        "exp": now + _MONITOR_TICKET_TTL_SECONDS,
    }
    if requested_by:
        # Omitted entirely (rather than set to `None`) when unknown — PyJWT
        # requires the `sub` claim to be a string when present at all.
        payload["sub"] = requested_by
    return jwt.encode(payload, _ticket_signing_key(), algorithm=_JWT_ALGORITHM)


async def consume_monitor_ticket(ticket: str | None, session_id: str) -> bool:
    """Verify a monitor ticket for `session_id` and atomically mark it used.

    Returns False for a missing, invalid, expired, mismatched, or replayed
    ticket. Single-use is enforced with a Redis `SET ... NX`, which is
    atomic — the first caller to consume a given `jti` gets `True`, any
    replay (including a concurrent one) gets `False`.
    """
    if not ticket:
        return False
    try:
        payload = jwt.decode(ticket, _ticket_signing_key(), algorithms=[_JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        return False

    if payload.get("purpose") != _MONITOR_TICKET_PURPOSE:
        return False
    if payload.get("session_id") != session_id:
        return False

    jti = payload.get("jti")
    if not jti:
        return False

    redis = await get_redis()
    first_use = await redis.set(
        f"{_MONITOR_TICKET_USED_PREFIX}:{jti}",
        "1",
        nx=True,
        ex=_MONITOR_TICKET_TTL_SECONDS,
    )
    if first_use:
        # FINDING-020: attribute the connection to the operator who minted
        # the ticket, closing the "unattributable in the audit trail" gap.
        logger.info(
            f"auth.monitor_ticket_consumed session_id={session_id!r} "
            f"sub={payload.get('sub')!r}"
        )
    return bool(first_use)
