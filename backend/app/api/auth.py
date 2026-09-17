"""
OASIS — Authentication endpoints.

POST /api/auth/login           — Verify credentials, return JWT
GET  /api/auth/status          — Return auth configuration and current auth state
POST /api/auth/logout          — Revoke the caller's own token (FINDING-008)
POST /api/auth/monitor-ticket  — Exchange a valid token for a short-lived,
                                  single-use monitor WebSocket ticket (FINDING-008)

FINDING-005 remediation: the single operator credential is verified with a
constant-time comparison (or an Argon2id hash, when AUTH_PASSWORD_HASH is
configured), and login attempts are throttled and logged.
"""

import hmac

from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger

from app.config import settings
from app.auth import (
    create_monitor_ticket,
    create_token,
    require_auth,
    require_valid_token,
    revoke_token,
    verify_token,
)
from app.rate_limit import (
    clear_login_failures,
    get_login_lockout_seconds,
    record_login_failure,
)
from app.security import verify_password


router = APIRouter(prefix="/auth", tags=["Authentication"])

_security = HTTPBearer(auto_error=False)


def _verify_credentials(username: str, password: str) -> bool:
    """Constant-time-ish credential check (FINDING-005).

    Username is always compared with `hmac.compare_digest`. Password is
    verified against `AUTH_PASSWORD_HASH` (Argon2id, preferred) when set;
    otherwise it falls back to the deprecated plaintext `AUTH_PASSWORD`
    path, also compared with `hmac.compare_digest` rather than `!=`.
    """
    username_ok = hmac.compare_digest(
        username.encode("utf-8"), settings.auth_username.encode("utf-8")
    )

    if settings.auth_password_hash:
        password_ok = verify_password(password, settings.auth_password_hash)
    elif settings.auth_password:
        logger.warning(
            "auth.login: AUTH_PASSWORD (plaintext) is configured — this is a "
            "deprecated migration path. Set AUTH_PASSWORD_HASH (Argon2id, "
            "see app/security.py) instead."
        )
        password_ok = hmac.compare_digest(
            password.encode("utf-8"), settings.auth_password.encode("utf-8")
        )
    else:
        password_ok = False

    return username_ok and password_ok


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str
    expires_in: int = 7200  # 2 hours — FINDING-008 (was 24 hours)


class AuthStatusResponse(BaseModel):
    auth_enabled: bool
    authenticated: bool
    username: str | None = None


class MonitorTicketRequest(BaseModel):
    session_id: str


class MonitorTicketResponse(BaseModel):
    ticket: str
    expires_in: int = 60


@router.post("/login", response_model=LoginResponse)
async def login(data: LoginRequest, request: Request):
    """
    Authenticate with username/password and receive a JWT token.

    FINDING-001: when AUTH_ENABLED is false this endpoint refuses to mint a
    token for arbitrary credentials — a forged/guessed token would otherwise
    still be indistinguishable from a real one if auth were later toggled
    on without rotating the signing key. Login is only meaningful, and only
    available, while auth is enabled.

    FINDING-005: throttled and logged. Failed attempts are counted per
    client-IP + username; five failures within 15 minutes lock that
    identity out for 15 minutes (`app/rate_limit.py`).
    """
    if not settings.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is disabled (AUTH_ENABLED=false); login is unavailable.",
        )

    if not settings.auth_password_hash and not settings.auth_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AUTH_ENABLED is true but no AUTH_PASSWORD_HASH/AUTH_PASSWORD is set in .env",
        )

    client_ip = _client_ip(request)
    identity = f"{client_ip}:{data.username}"

    lockout_seconds = await get_login_lockout_seconds(identity)
    if lockout_seconds is not None:
        logger.warning(
            f"auth.login.blocked ip={client_ip} username={data.username!r} "
            f"reason=locked_out retry_after={lockout_seconds}"
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again later.",
            headers={"Retry-After": str(lockout_seconds)},
        )

    if not _verify_credentials(data.username, data.password):
        await record_login_failure(identity)
        logger.warning(
            f"auth.login.failed ip={client_ip} username={data.username!r}"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    await clear_login_failures(identity)
    logger.info(f"auth.login.success ip={client_ip} username={data.username!r}")

    token = create_token(data.username)
    return LoginResponse(token=token, username=data.username)


@router.get("/status", response_model=AuthStatusResponse)
async def auth_status(
    credentials: HTTPAuthorizationCredentials | None = Depends(_security),
):
    """
    Public endpoint — no auth required.

    Returns whether auth is enabled and whether the caller's token (if any) is valid.
    This lets the frontend decide whether to show the login page.
    """
    if not settings.auth_enabled:
        return AuthStatusResponse(
            auth_enabled=False,
            authenticated=True,
            username=None,
        )

    # Auth is enabled — check if a valid token was provided
    if credentials:
        payload = await verify_token(credentials.credentials)
        if payload:
            return AuthStatusResponse(
                auth_enabled=True,
                authenticated=True,
                username=payload.get("sub"),
            )

    # No token or invalid token
    return AuthStatusResponse(
        auth_enabled=True,
        authenticated=False,
        username=None,
    )


@router.post("/logout", status_code=204)
async def logout(payload: dict | None = Depends(require_auth)):
    """
    FINDING-008: invalidate the caller's own token immediately, rather than
    relying on the client discarding it. Adds the token's `jti` to a
    Redis-backed denylist for its remaining lifetime — `verify_token`
    rejects it from this point on even though its signature and `exp` are
    still valid.

    A no-op (still 204) when AUTH_ENABLED is false, since `require_auth`
    passes every request through unauthenticated in that mode.
    """
    if payload:
        await revoke_token(payload)
        logger.info(f"auth.logout username={payload.get('sub')!r}")


@router.post("/monitor-ticket", response_model=MonitorTicketResponse)
async def monitor_ticket(
    data: MonitorTicketRequest,
    payload: dict = Depends(require_valid_token),
):
    """
    FINDING-008: issue a short-lived (60s), single-use ticket for the
    transcript monitor WebSocket, so the long-lived admin bearer token is
    never placed in a URL — query strings are the single most commonly
    logged, cached and forwarded field in any proxy, CDN, WAF or browser
    history.

    Requires a valid token unconditionally (via `require_valid_token`),
    independent of `AUTH_ENABLED` — the monitor WebSocket itself has always
    enforced this regardless of the toggle (FINDING-001), because it
    streams participant PII.
    """
    ticket = create_monitor_ticket(data.session_id, requested_by=payload.get("sub"))
    logger.info(
        f"auth.monitor_ticket_issued username={payload.get('sub')!r} "
        f"session_id={data.session_id!r}"
    )
    return MonitorTicketResponse(ticket=ticket)
