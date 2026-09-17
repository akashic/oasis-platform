"""
Tests for application configuration and settings.

Pure unit tests — no external services needed.
"""

import os

import pytest


class TestConfig:
    def test_database_url_format(self):
        from app.config import settings

        url = settings.database_url
        assert url.startswith("postgresql+asyncpg://")
        assert settings.postgres_user in url

    def test_database_url_sync_format(self):
        from app.config import settings

        url = settings.database_url_sync
        assert url.startswith("postgresql://")

    def test_redis_url_default(self):
        from app.config import settings

        assert "redis://" in settings.redis_url

    def test_auth_enabled_by_test_env(self):
        """The shared test env explicitly sets AUTH_ENABLED=false in
        conftest.py for local-dev-style test convenience. This does not
        assert the field's own default (see TestSecretKeyValidation /
        FINDING-001 for the secure-by-default field value, now True)."""
        from app.config import settings

        assert settings.auth_enabled is False

    def test_auth_enabled_field_default_is_true(self):
        """FINDING-001: the Settings field itself must default to secure
        (auth required) — only an explicit AUTH_ENABLED=false env var (as
        set by tests/conftest.py) opts out.

        test_REQ_SEC_FINDING_001_auth_enabled_defaults_true
        """
        from app.config import Settings

        assert Settings.model_fields["auth_enabled"].default is True

    def test_scaleway_api_key_property(self):
        from app.config import settings

        # scaleway_api_key is a property that returns scaleway_secret_key
        assert settings.scaleway_api_key == settings.scaleway_secret_key

    def test_gcp_defaults(self):
        from app.config import settings

        assert settings.gcp_location == "us-central1"


class TestCorsAllowedOrigins:
    """FINDING-004: CORS is an explicit allow-list, decoupled from `debug`."""

    def test_default_is_empty(self):
        """test_REQ_SEC_FINDING_004_cors_default_empty"""
        from app.config import Settings

        settings = Settings(
            postgres_host="localhost",
            postgres_user="test",
            postgres_password="test",
            postgres_db="test",
        )
        assert settings.cors_allowed_origins == []

    def test_debug_field_default_is_false(self):
        """FINDING-004 rec. 4: DEBUG must be opt-in, not the default.

        test_REQ_SEC_FINDING_004_debug_defaults_false
        """
        from app.config import Settings

        assert Settings.model_fields["debug"].default is False

    def test_parses_comma_separated_origins(self):
        """test_REQ_SEC_FINDING_004_cors_parses_csv"""
        from app.config import Settings

        # `cors_allowed_origins_raw` has `validation_alias="CORS_ALLOWED_ORIGINS"`
        # so it must be populated by that alias (matches how env vars — the
        # only real-world input path — populate it too).
        settings = Settings(
            **{"CORS_ALLOWED_ORIGINS": "https://a.example.com, https://b.example.com"},
            postgres_host="localhost",
            postgres_user="test",
            postgres_password="test",
            postgres_db="test",
        )
        assert settings.cors_allowed_origins == [
            "https://a.example.com",
            "https://b.example.com",
        ]

    def test_env_var_name_has_no_raw_suffix(self):
        """Operators set CORS_ALLOWED_ORIGINS, not CORS_ALLOWED_ORIGINS_RAW."""
        from app.config import Settings

        os.environ["CORS_ALLOWED_ORIGINS"] = "https://app.example.com"
        try:
            settings = Settings(
                postgres_host="localhost",
                postgres_user="test",
                postgres_password="test",
                postgres_db="test",
            )
            assert settings.cors_allowed_origins == ["https://app.example.com"]
        finally:
            del os.environ["CORS_ALLOWED_ORIGINS"]


class TestSecretKeyValidation:
    """FINDING-002: refuse to start with a weak/placeholder SECRET_KEY
    outside development."""

    def test_placeholder_rejected_outside_development(self):
        from app.config import PLACEHOLDER_SECRET_KEY, Settings

        with pytest.raises(ValueError, match="SECRET_KEY"):
            Settings(
                app_env="production",
                secret_key=PLACEHOLDER_SECRET_KEY,
                postgres_host="localhost",
                postgres_user="test",
                postgres_password="test",
                postgres_db="test",
            )

    def test_empty_secret_key_rejected_outside_development(self):
        from app.config import Settings

        with pytest.raises(ValueError, match="SECRET_KEY"):
            Settings(
                app_env="staging",
                secret_key="",
                postgres_host="localhost",
                postgres_user="test",
                postgres_password="test",
                postgres_db="test",
            )

    def test_short_secret_key_rejected_outside_development(self):
        from app.config import Settings

        with pytest.raises(ValueError, match="SECRET_KEY"):
            Settings(
                app_env="production",
                secret_key="too-short",
                postgres_host="localhost",
                postgres_user="test",
                postgres_password="test",
                postgres_db="test",
            )

    def test_placeholder_in_development_generates_ephemeral_key(self):
        """FINDING-013: the weak-key check is now unconditional. Development
        is no longer an exemption from the *strength* requirement — a weak/
        placeholder/empty SECRET_KEY is replaced with a random ephemeral one
        instead of being accepted as-is, so it is never a guessable public
        constant (previously an empty SECRET_KEY was silently usable to
        forge admin tokens, since `.env.example` ships APP_ENV=development
        with SECRET_KEY= empty).

        test_REQ_SEC_FINDING_013_weak_key_replaced_in_development
        """
        from app.config import PLACEHOLDER_SECRET_KEY, MIN_SECRET_KEY_LENGTH, Settings

        settings = Settings(
            app_env="development",
            secret_key=PLACEHOLDER_SECRET_KEY,
            postgres_host="localhost",
            postgres_user="test",
            postgres_password="test",
            postgres_db="test",
        )
        assert settings.secret_key != PLACEHOLDER_SECRET_KEY
        assert len(settings.secret_key) >= MIN_SECRET_KEY_LENGTH

    def test_empty_secret_key_in_development_generates_ephemeral_key(self):
        """test_REQ_SEC_FINDING_013_empty_key_replaced_in_development"""
        from app.config import MIN_SECRET_KEY_LENGTH, Settings

        settings = Settings(
            app_env="development",
            secret_key="",
            postgres_host="localhost",
            postgres_user="test",
            postgres_password="test",
            postgres_db="test",
        )
        assert settings.secret_key != ""
        assert len(settings.secret_key) >= MIN_SECRET_KEY_LENGTH

    def test_ephemeral_keys_are_not_reused_across_instances(self):
        """Each weak-key instance gets its own random key, not a shared
        fallback constant."""
        from app.config import PLACEHOLDER_SECRET_KEY, Settings

        kwargs = dict(
            app_env="development",
            secret_key=PLACEHOLDER_SECRET_KEY,
            postgres_host="localhost",
            postgres_user="test",
            postgres_password="test",
            postgres_db="test",
        )
        first = Settings(**kwargs)
        second = Settings(**kwargs)
        assert first.secret_key != second.secret_key

    def test_strong_secret_key_unchanged_in_development(self):
        """A strong key in development is left as configured — only a weak
        one is replaced."""
        from app.config import Settings

        settings = Settings(
            app_env="development",
            secret_key="b" * 32,
            postgres_host="localhost",
            postgres_user="test",
            postgres_password="test",
            postgres_db="test",
        )
        assert settings.secret_key == "b" * 32

    def test_strong_secret_key_accepted_outside_development(self):
        from app.config import Settings

        settings = Settings(
            app_env="production",
            secret_key="a" * 32,
            postgres_host="localhost",
            postgres_user="test",
            postgres_password="test",
            postgres_db="test",
        )
        assert settings.secret_key == "a" * 32
