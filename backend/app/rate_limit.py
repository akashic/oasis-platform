"""
OASIS — Redis-backed rate limiting and login lockout.

FINDING-005: there was no rate limiting, lockout or throttling anywhere in
the repository, on the admin login endpoint, the Twilio voice webhook, or
the Twilio media-stream WebSocket. Redis is already a dependency, so it is
used here as the shared counter store (works across multiple backend
replicas, unlike an in-process counter).
"""

import time

from app.redis import get_redis

_WINDOW_PREFIX = "oasis:ratelimit"


async def check_fixed_window(key: str, *, limit: int, window_seconds: int) -> tuple[bool, int]:
    """Fixed-window counter shared across all backend instances.

    Returns ``(allowed, retry_after_seconds)``. ``retry_after_seconds`` is
    only meaningful when ``allowed`` is ``False``.
    """
    redis = await get_redis()
    window = int(time.time()) // window_seconds
    redis_key = f"{_WINDOW_PREFIX}:{key}:{window}"

    count = await redis.incr(redis_key)
    if count == 1:
        await redis.expire(redis_key, window_seconds)

    if count > limit:
        ttl = await redis.ttl(redis_key)
        return False, max(ttl, 1)
    return True, 0


# ── Login attempt throttling + lockout (FINDING-005) ─────────────────────

_LOGIN_MAX_ATTEMPTS = 5
_LOGIN_FAILURE_WINDOW_SECONDS = 900  # 15 minutes
_LOGIN_LOCKOUT_SECONDS = 900  # 15 minutes

_LOGIN_FAILURES_PREFIX = "oasis:auth:failures"
_LOGIN_LOCKOUT_PREFIX = "oasis:auth:lockout"


async def get_login_lockout_seconds(identity: str) -> int | None:
    """Return remaining lockout seconds for ``identity`` (client IP +
    username), or ``None`` if not currently locked out."""
    redis = await get_redis()
    ttl = await redis.ttl(f"{_LOGIN_LOCKOUT_PREFIX}:{identity}")
    return ttl if ttl and ttl > 0 else None


async def record_login_failure(identity: str) -> None:
    """Record a failed login attempt for ``identity``. Trips a lockout once
    ``_LOGIN_MAX_ATTEMPTS`` is reached within the failure window."""
    redis = await get_redis()
    failures_key = f"{_LOGIN_FAILURES_PREFIX}:{identity}"

    count = await redis.incr(failures_key)
    if count == 1:
        await redis.expire(failures_key, _LOGIN_FAILURE_WINDOW_SECONDS)

    if count >= _LOGIN_MAX_ATTEMPTS:
        await redis.set(
            f"{_LOGIN_LOCKOUT_PREFIX}:{identity}", "1", ex=_LOGIN_LOCKOUT_SECONDS
        )
        await redis.delete(failures_key)


async def clear_login_failures(identity: str) -> None:
    """Reset the failure counter for ``identity`` after a successful login."""
    redis = await get_redis()
    await redis.delete(f"{_LOGIN_FAILURES_PREFIX}:{identity}")
