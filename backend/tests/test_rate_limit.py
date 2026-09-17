"""
Tests for FINDING-005's Redis-backed rate limiting and login lockout
(app/rate_limit.py). Uses the shared `fake_redis` fixture from conftest.
"""

import pytest

from app.rate_limit import (
    check_fixed_window,
    clear_login_failures,
    get_login_lockout_seconds,
    record_login_failure,
)


@pytest.fixture(autouse=True)
def _patch_redis(fake_redis, monkeypatch):
    import app.rate_limit as rate_limit_module

    async def _fake_get_redis():
        return fake_redis

    monkeypatch.setattr(rate_limit_module, "get_redis", _fake_get_redis)


class TestCheckFixedWindow:
    async def test_allows_under_limit(self):
        """test_REQ_SEC_FINDING_005_rate_limit_allows_under_limit"""
        for _ in range(5):
            allowed, _ = await check_fixed_window("test-key", limit=5, window_seconds=60)
            assert allowed is True

    async def test_blocks_over_limit(self):
        """test_REQ_SEC_FINDING_005_rate_limit_blocks_over_limit"""
        for _ in range(5):
            await check_fixed_window("test-key-2", limit=5, window_seconds=60)
        allowed, retry_after = await check_fixed_window(
            "test-key-2", limit=5, window_seconds=60
        )
        assert allowed is False
        assert retry_after > 0

    async def test_different_keys_are_independent(self):
        for _ in range(5):
            await check_fixed_window("key-a", limit=5, window_seconds=60)
        allowed, _ = await check_fixed_window("key-b", limit=5, window_seconds=60)
        assert allowed is True


class TestLoginLockout:
    async def test_not_locked_out_initially(self):
        """test_REQ_SEC_FINDING_005_no_lockout_initially"""
        assert await get_login_lockout_seconds("1.2.3.4:admin") is None

    async def test_locks_out_after_max_attempts(self):
        """test_REQ_SEC_FINDING_005_locks_out_after_max_attempts"""
        identity = "1.2.3.4:admin"
        for _ in range(5):
            await record_login_failure(identity)
        lockout = await get_login_lockout_seconds(identity)
        assert lockout is not None
        assert lockout > 0

    async def test_fewer_than_max_attempts_does_not_lock(self):
        identity = "5.6.7.8:admin"
        for _ in range(4):
            await record_login_failure(identity)
        assert await get_login_lockout_seconds(identity) is None

    async def test_clear_login_failures_resets_state(self):
        """test_REQ_SEC_FINDING_005_clear_failures_on_success"""
        identity = "9.9.9.9:admin"
        for _ in range(4):
            await record_login_failure(identity)
        await clear_login_failures(identity)
        # A subsequent failure should not immediately trip the lockout
        # since the counter was reset.
        await record_login_failure(identity)
        assert await get_login_lockout_seconds(identity) is None

    async def test_lockout_is_per_identity(self):
        """Different IP+username combinations are throttled independently."""
        for _ in range(5):
            await record_login_failure("1.1.1.1:admin")
        assert await get_login_lockout_seconds("2.2.2.2:admin") is None
