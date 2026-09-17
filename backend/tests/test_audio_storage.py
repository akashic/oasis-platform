"""
Tests for FINDING-007's connect-time re-validation of AUDIO_S3_ENDPOINT_URL
(app/audio/storage.py) — the write-time gate is covered separately in
test_api_settings.py::TestAudioS3EndpointUrlValidation.
"""

import pytest

import app.api.settings as settings_module
from app.audio.storage import LocalAudioStorage, S3AudioStorage, get_audio_storage


def _cfg(**overrides) -> dict:
    base = {
        "audio_storage_backend": "s3",
        "audio_storage_local_path": "/data/oasis-recordings",
        "audio_s3_bucket": "recordings",
        "audio_s3_prefix": "oasis-recordings",
        "audio_s3_region": "us-east-1",
        "audio_s3_endpoint_url": "",
        "audio_s3_access_key_id": "AKIA-test",
        "audio_s3_secret_access_key": "secret-test",
    }
    base.update(overrides)
    return base


class TestGetAudioStorageEndpointRevalidation:
    async def test_ssrf_endpoint_refused_at_connect_time(self, monkeypatch):
        """FINDING-007 (Revision 4 residual): even if a malicious/rebound
        AUDIO_S3_ENDPOINT_URL somehow reached Redis, the backend must not
        hand it to boto3 as the S3 endpoint.

        test_REQ_SEC_FINDING_007_audio_s3_endpoint_revalidated_at_connect
        """

        async def _fake_settings():
            return _cfg(audio_s3_endpoint_url="http://169.254.169.254/latest/meta-data/")

        monkeypatch.setattr(
            settings_module, "get_effective_audio_settings", _fake_settings
        )
        backend = await get_audio_storage()
        assert backend is None

    async def test_sibling_container_endpoint_refused_at_connect_time(self, monkeypatch):
        async def _fake_settings():
            return _cfg(audio_s3_endpoint_url="http://redis:6379")

        monkeypatch.setattr(
            settings_module, "get_effective_audio_settings", _fake_settings
        )
        backend = await get_audio_storage()
        assert backend is None

    async def test_valid_public_endpoint_accepted(self, monkeypatch):
        async def _fake_settings():
            return _cfg(audio_s3_endpoint_url="https://example.com:9000")

        monkeypatch.setattr(
            settings_module, "get_effective_audio_settings", _fake_settings
        )
        backend = await get_audio_storage()
        assert isinstance(backend, S3AudioStorage)

    async def test_no_endpoint_configured_still_works(self, monkeypatch):
        """MinIO/custom endpoint is optional — real AWS S3 has none."""

        async def _fake_settings():
            return _cfg(audio_s3_endpoint_url="")

        monkeypatch.setattr(
            settings_module, "get_effective_audio_settings", _fake_settings
        )
        backend = await get_audio_storage()
        assert isinstance(backend, S3AudioStorage)

    async def test_local_backend_unaffected(self, monkeypatch):
        async def _fake_settings():
            return _cfg(audio_storage_backend="local")

        monkeypatch.setattr(
            settings_module, "get_effective_audio_settings", _fake_settings
        )
        backend = await get_audio_storage()
        assert isinstance(backend, LocalAudioStorage)
