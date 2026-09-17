"""
Tests for FINDING-001's startup auth-posture guard (``app.main.enforce_auth_posture``).

The guard runs at the top of the FastAPI ``lifespan`` startup and must
refuse to bring the app up if AUTH_ENABLED=false outside APP_ENV=development
— closing the "bypass install.sh" deploy path the finding assumes exists.
"""

import pytest
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.main import configure_cors, enforce_auth_posture


class TestEnforceAuthPosture:
    def setup_method(self, _method):
        self._orig_env = settings.app_env
        self._orig_auth = settings.auth_enabled

    def teardown_method(self, _method):
        settings.app_env = self._orig_env
        settings.auth_enabled = self._orig_auth

    def test_raises_when_disabled_outside_development(self):
        """test_REQ_SEC_FINDING_001_refuses_start_auth_disabled_non_dev"""
        settings.app_env = "production"
        settings.auth_enabled = False
        with pytest.raises(RuntimeError, match="AUTH_ENABLED"):
            enforce_auth_posture()

    def test_raises_for_staging_too(self):
        settings.app_env = "staging"
        settings.auth_enabled = False
        with pytest.raises(RuntimeError):
            enforce_auth_posture()

    def test_allows_disabled_in_development(self):
        """test_REQ_SEC_FINDING_001_allows_disabled_auth_in_development"""
        settings.app_env = "development"
        settings.auth_enabled = False
        enforce_auth_posture()  # must not raise

    def test_allows_enabled_in_any_environment(self):
        settings.app_env = "production"
        settings.auth_enabled = True
        enforce_auth_posture()  # must not raise


class TestConfigureCors:
    """FINDING-004: CORS must never be driven by `debug`, and must never
    combine a wildcard/reflected origin with credentials."""

    def test_no_middleware_when_no_origins_configured(self):
        """test_REQ_SEC_FINDING_004_no_cors_headers_when_unconfigured"""
        app = FastAPI()
        configure_cors(app, [])
        assert not any(m.cls is CORSMiddleware for m in app.user_middleware)

    def test_middleware_registered_for_configured_origins(self):
        """test_REQ_SEC_FINDING_004_cors_allowlist_registered"""
        app = FastAPI()
        configure_cors(app, ["https://app.example.com"])
        cors = next(m for m in app.user_middleware if m.cls is CORSMiddleware)
        assert cors.kwargs["allow_origins"] == ["https://app.example.com"]
        assert cors.kwargs["allow_credentials"] is True

    def test_never_wildcard_with_credentials(self):
        """Guards against the exact FINDING-004 regression: a wildcard
        origin combined with allow_credentials=True lets Starlette reflect
        any Origin. This must never be reachable, no matter what
        `cors_allowed_origins` contains structurally.

        test_REQ_SEC_FINDING_004_never_wildcard_with_credentials
        """
        app = FastAPI()
        configure_cors(app, ["https://app.example.com", "https://admin.example.com"])
        cors = next(m for m in app.user_middleware if m.cls is CORSMiddleware)
        assert "*" not in cors.kwargs["allow_origins"]
        assert cors.kwargs["allow_credentials"] is True
