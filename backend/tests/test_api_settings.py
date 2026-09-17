"""
Tests for the Settings API (API key management).

Uses fake Redis from conftest — no real Redis needed.
"""

import pytest
from httpx import AsyncClient


class TestSettingsAPI:
    async def test_list_api_keys(self, client: AsyncClient):
        resp = await client.get("/api/settings/keys")
        assert resp.status_code == 200
        data = resp.json()
        assert "keys" in data
        keys = data["keys"]
        assert isinstance(keys, list)
        assert len(keys) > 0

        # Check that known fields are present
        field_names = [k["field"] for k in keys]
        assert "openai_api_key" in field_names
        assert "deepgram_api_key" in field_names
        assert "elevenlabs_api_key" in field_names

    async def test_api_key_status_fields(self, client: AsyncClient):
        resp = await client.get("/api/settings/keys")
        data = resp.json()
        key = data["keys"][0]

        assert "field" in key
        assert "env_var" in key
        assert "is_set" in key
        assert "source" in key
        assert "masked_value" in key
        assert key["source"] in ("env", "dashboard", "none")

    async def test_update_api_key(self, client: AsyncClient):
        resp = await client.put(
            "/api/settings/keys",
            json={"openai_api_key": "sk-new-test-key-12345678"},
        )
        assert resp.status_code == 200
        data = resp.json()
        keys = data["keys"]
        openai_key = next(k for k in keys if k["field"] == "openai_api_key")
        assert openai_key["is_set"] is True

    async def test_clear_api_key_override(self, client: AsyncClient):
        # First set an override
        await client.put(
            "/api/settings/keys",
            json={"deepgram_api_key": "dg-override-key"},
        )

        # Then clear it with empty string
        resp = await client.put(
            "/api/settings/keys",
            json={"deepgram_api_key": ""},
        )
        assert resp.status_code == 200

    async def test_auth_config(self, client: AsyncClient):
        resp = await client.get("/api/settings/auth")
        assert resp.status_code == 200
        data = resp.json()
        assert "auth_enabled" in data
        assert "username" in data


class TestFlagsAPI:
    """Tests for the boolean feature flag endpoints (data residency, etc.)."""

    async def test_list_flags(self, client: AsyncClient):
        resp = await client.get("/api/settings/flags")
        assert resp.status_code == 200
        data = resp.json()
        assert "flags" in data
        flags = data["flags"]
        assert isinstance(flags, list)
        names = [f["field"] for f in flags]
        assert "openai_use_eu" in names

    async def test_flag_default_is_off(self, client: AsyncClient):
        resp = await client.get("/api/settings/flags")
        flag = next(f for f in resp.json()["flags"] if f["field"] == "openai_use_eu")
        assert flag["enabled"] is False
        assert flag["source"] in ("env", "default")
        assert flag["env_var"] == "OPENAI_USE_EU"

    async def test_enable_flag_via_dashboard(self, client: AsyncClient):
        resp = await client.put(
            "/api/settings/flags",
            json={"openai_use_eu": True},
        )
        assert resp.status_code == 200
        flag = next(f for f in resp.json()["flags"] if f["field"] == "openai_use_eu")
        assert flag["enabled"] is True
        assert flag["source"] == "dashboard"

    async def test_disable_flag_via_dashboard(self, client: AsyncClient):
        # Enable then disable — both should land as dashboard overrides.
        await client.put("/api/settings/flags", json={"openai_use_eu": True})
        resp = await client.put(
            "/api/settings/flags",
            json={"openai_use_eu": False},
        )
        flag = next(f for f in resp.json()["flags"] if f["field"] == "openai_use_eu")
        assert flag["enabled"] is False
        assert flag["source"] == "dashboard"

    async def test_get_effective_flag_helper(self, client: AsyncClient):
        from app.api.settings import get_effective_flag

        # Default
        assert await get_effective_flag("openai_use_eu") is False

        # Enable via API
        await client.put("/api/settings/flags", json={"openai_use_eu": True})
        assert await get_effective_flag("openai_use_eu") is True


class TestAudioStorageSettingsAPI:
    async def test_list_audio_storage_settings(self, client: AsyncClient):
        resp = await client.get("/api/settings/audio-storage")
        assert resp.status_code == 200
        data = resp.json()
        assert "settings" in data
        fields = [s["field"] for s in data["settings"]]
        assert "audio_storage_backend" in fields
        assert "audio_s3_bucket" in fields
        assert "audio_s3_secret_access_key" in fields

    async def test_update_audio_storage_backend(self, client: AsyncClient):
        resp = await client.put(
            "/api/settings/audio-storage",
            json={"audio_storage_backend": "s3"},
        )
        assert resp.status_code == 200
        row = next(
            s for s in resp.json()["settings"] if s["field"] == "audio_storage_backend"
        )
        assert row["display_value"] == "s3"
        assert row["source"] == "dashboard"

    async def test_invalid_audio_storage_backend(self, client: AsyncClient):
        resp = await client.put(
            "/api/settings/audio-storage",
            json={"audio_storage_backend": "azure"},
        )
        assert resp.status_code == 400

    async def test_get_effective_audio_setting_helper(self, client: AsyncClient):
        from app.api.settings import get_effective_audio_setting

        await client.put(
            "/api/settings/audio-storage",
            json={"audio_s3_bucket": "my-test-bucket"},
        )
        assert await get_effective_audio_setting("audio_s3_bucket") == "my-test-bucket"

    async def test_sensitive_field_masked(self, client: AsyncClient):
        await client.put(
            "/api/settings/audio-storage",
            json={"audio_s3_secret_access_key": "supersecretkey123456"},
        )
        resp = await client.get("/api/settings/audio-storage")
        row = next(
            s
            for s in resp.json()["settings"]
            if s["field"] == "audio_s3_secret_access_key"
        )
        assert row["sensitive"] is True
        assert "••••" in row["display_value"]
        assert "supersecret" not in row["display_value"]

    async def test_sensitive_field_stored_encrypted_in_redis(
        self, client: AsyncClient, fake_redis
    ):
        """FINDING-006: S3 credentials must not be stored in plaintext.

        test_REQ_SEC_FINDING_006_audio_storage_secret_encrypted
        """
        await client.put(
            "/api/settings/audio-storage",
            json={"audio_s3_secret_access_key": "supersecretkey123456"},
        )
        raw = await fake_redis.hget(
            "oasis:settings:audio_storage", "audio_s3_secret_access_key"
        )
        assert raw is not None
        assert "supersecretkey123456" not in raw

    async def test_get_effective_audio_setting_decrypts(self, client: AsyncClient):
        from app.api.settings import get_effective_audio_setting

        await client.put(
            "/api/settings/audio-storage",
            json={"audio_s3_secret_access_key": "supersecretkey123456"},
        )
        assert (
            await get_effective_audio_setting("audio_s3_secret_access_key")
            == "supersecretkey123456"
        )


class TestAudioS3EndpointUrlValidation:
    """FINDING-007 (Revision 4 residual): audio_s3_endpoint_url receives
    every recorded participant audio file plus the S3 credentials, but was
    previously unvalidated and unconfirmed, unlike the five provider URL
    fields on PUT /api/settings/keys."""

    async def test_ssrf_url_rejected(self, client: AsyncClient):
        """test_REQ_SEC_FINDING_007_audio_s3_endpoint_ssrf_rejected"""
        resp = await client.put(
            "/api/settings/audio-storage",
            json={
                "audio_s3_endpoint_url": "http://169.254.169.254/latest/meta-data/",
                "confirm_endpoint_change": True,
            },
        )
        assert resp.status_code == 400

    async def test_sibling_container_url_rejected(self, client: AsyncClient):
        """test_REQ_SEC_FINDING_007_audio_s3_endpoint_sibling_rejected"""
        resp = await client.put(
            "/api/settings/audio-storage",
            json={
                "audio_s3_endpoint_url": "http://redis:6379",
                "confirm_endpoint_change": True,
            },
        )
        assert resp.status_code == 400

    async def test_changing_url_without_confirm_rejected(self, client: AsyncClient):
        """test_REQ_SEC_FINDING_007_audio_s3_endpoint_confirm_required"""
        resp = await client.put(
            "/api/settings/audio-storage",
            json={"audio_s3_endpoint_url": "https://example.com:9000"},
        )
        assert resp.status_code == 400
        assert "confirm_endpoint_change" in resp.json()["detail"]

    async def test_changing_url_with_confirm_succeeds(self, client: AsyncClient):
        """test_REQ_SEC_FINDING_007_audio_s3_endpoint_confirm_allows_change"""
        resp = await client.put(
            "/api/settings/audio-storage",
            json={
                "audio_s3_endpoint_url": "https://example.com:9000",
                "confirm_endpoint_change": True,
            },
        )
        assert resp.status_code == 200
        row = next(
            s for s in resp.json()["settings"] if s["field"] == "audio_s3_endpoint_url"
        )
        assert row["is_set"] is True

    async def test_clearing_url_does_not_require_confirm(self, client: AsyncClient):
        await client.put(
            "/api/settings/audio-storage",
            json={
                "audio_s3_endpoint_url": "https://example.com:9000",
                "confirm_endpoint_change": True,
            },
        )
        resp = await client.put(
            "/api/settings/audio-storage",
            json={"audio_s3_endpoint_url": ""},
        )
        assert resp.status_code == 200


class TestApiKeyEncryption:
    """FINDING-006: provider credential overrides must be encrypted at rest
    in Redis, not stored in plaintext."""

    async def test_api_key_stored_encrypted_in_redis(
        self, client: AsyncClient, fake_redis
    ):
        """test_REQ_SEC_FINDING_006_api_key_encrypted_in_redis"""
        await client.put(
            "/api/settings/keys",
            json={"openai_api_key": "sk-plaintext-should-not-appear-1234"},
        )
        raw = await fake_redis.hget("oasis:settings:api_keys", "openai_api_key")
        assert raw is not None
        assert "sk-plaintext-should-not-appear-1234" not in raw

    async def test_get_effective_key_decrypts_transparently(self, client: AsyncClient):
        """test_REQ_SEC_FINDING_006_get_effective_key_decrypts"""
        from app.api.settings import get_effective_key

        await client.put(
            "/api/settings/keys",
            json={"openai_api_key": "sk-round-trip-test-key-1234"},
        )
        assert await get_effective_key("openai_api_key") == "sk-round-trip-test-key-1234"

    async def test_legacy_plaintext_override_still_readable(
        self, client: AsyncClient, fake_redis
    ):
        """Values written before FINDING-006's encryption fix must remain
        readable (decrypt_secret falls back to returning them unchanged).

        test_REQ_SEC_FINDING_006_legacy_override_readable
        """
        from app.api.settings import get_effective_key

        await fake_redis.hset(
            "oasis:settings:api_keys", "deepgram_api_key", "dg-legacy-plaintext-value"
        )
        assert await get_effective_key("deepgram_api_key") == "dg-legacy-plaintext-value"


class TestProviderEndpointUrlValidation:
    """FINDING-007: provider endpoint URLs are validated against SSRF and
    require explicit confirmation to change."""

    async def test_ssrf_url_rejected(self, client: AsyncClient):
        """test_REQ_SEC_FINDING_007_ssrf_url_rejected_on_write"""
        resp = await client.put(
            "/api/settings/keys",
            json={
                "self_hosted_stt_url": "http://169.254.169.254/latest/meta-data/",
                "confirm_endpoint_change": True,
            },
        )
        assert resp.status_code == 400

    async def test_sibling_container_url_rejected(self, client: AsyncClient):
        """test_REQ_SEC_FINDING_007_sibling_container_rejected_on_write"""
        resp = await client.put(
            "/api/settings/keys",
            json={
                "self_hosted_stt_url": "http://redis:6379",
                "confirm_endpoint_change": True,
            },
        )
        assert resp.status_code == 400

    async def test_changing_url_without_confirm_rejected(self, client: AsyncClient):
        """test_REQ_SEC_FINDING_007_confirm_required_to_change_url"""
        resp = await client.put(
            "/api/settings/keys",
            json={"self_hosted_stt_url": "https://192.168.1.5:8000/v1"},
        )
        assert resp.status_code == 400
        assert "confirm_endpoint_change" in resp.json()["detail"]

    async def test_changing_url_with_confirm_succeeds(self, client: AsyncClient):
        """test_REQ_SEC_FINDING_007_confirm_allows_url_change"""
        resp = await client.put(
            "/api/settings/keys",
            json={
                "self_hosted_stt_url": "https://example.com/v1",
                "confirm_endpoint_change": True,
            },
        )
        assert resp.status_code == 200
        keys = resp.json()["keys"]
        row = next(k for k in keys if k["field"] == "self_hosted_stt_url")
        assert row["is_set"] is True

    async def test_clearing_url_does_not_require_confirm(self, client: AsyncClient):
        """Clearing an override (empty string) is always allowed without
        confirmation — only *changing to a new value* requires it."""
        await client.put(
            "/api/settings/keys",
            json={
                "self_hosted_stt_url": "https://example.com/v1",
                "confirm_endpoint_change": True,
            },
        )
        resp = await client.put(
            "/api/settings/keys",
            json={"self_hosted_stt_url": ""},
        )
        assert resp.status_code == 200

    async def test_resubmitting_same_url_does_not_require_confirm(
        self, client: AsyncClient
    ):
        """Re-sending the same value that's already in effect isn't a
        change, so no confirmation is required."""
        await client.put(
            "/api/settings/keys",
            json={
                "self_hosted_stt_url": "https://example.com/v1",
                "confirm_endpoint_change": True,
            },
        )
        resp = await client.put(
            "/api/settings/keys",
            json={"self_hosted_stt_url": "https://example.com/v1"},
        )
        assert resp.status_code == 200
