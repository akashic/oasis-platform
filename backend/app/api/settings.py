"""
OASIS — Settings API endpoints.

GET  /api/settings/keys       — List configured API keys (masked)
PUT  /api/settings/keys       — Update API key overrides (stored in Redis)
GET  /api/settings/flags      — List boolean feature flags (data residency, etc.)
PUT  /api/settings/flags      — Update boolean flag overrides (stored in Redis)
GET  /api/settings/auth       — Get auth configuration status
GET  /api/settings/catalog      Configured provider/model catalog
POST /api/settings/smoke-test   Verify configured providers
"""

import re
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from loguru import logger

from app.auth import require_auth
from app.config import settings
from app.crypto import decrypt_secret, encrypt_secret
from app.egress_guard import EgressURLError, validate_egress_url
from app.providers.catalog import get_configured_catalog
from app.providers.smoke import run_configured_smoke_tests
from app.redis import get_redis

router = APIRouter(prefix="/settings", tags=["Settings"])

# FINDING-007: URL-valued fields within `_API_KEY_FIELDS` — these are
# destinations the backend makes outbound requests to, not secrets, so they
# get SSRF validation (`validate_egress_url`) instead of/in addition to
# masking, and a required confirmation + audit trail when changed.
_URL_FIELDS = {
    "openai_compatible_llm_url",
    "azure_openai_endpoint",
    "self_hosted_stt_url",
    "self_hosted_tts_url",
    "embedding_api_url",
}


def _actor(payload: dict | None) -> str:
    """Best-effort identity for audit log lines. `require_auth` returns
    `None` when AUTH_ENABLED=false (see app/auth.py)."""
    if payload:
        return str(payload.get("sub") or "unknown")
    return "unauthenticated"

# Redis key for API key overrides
_REDIS_KEY = "oasis:settings:api_keys"
# Redis key for boolean flag overrides (data residency, etc.)
_FLAGS_REDIS_KEY = "oasis:settings:flags"

# Boolean feature flags exposed to the dashboard. Stored separately from API
# keys so the keys flow can keep its masking behaviour.
_FLAG_FIELDS = {
    "openai_use_eu": "OPENAI_USE_EU",
}

_TRUTHY = {"1", "true", "yes", "on"}


def _coerce_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in _TRUTHY

# All configurable API keys with their .env variable names
_API_KEY_FIELDS = {
    "openai_api_key": "OPENAI_API_KEY",
    "deepgram_api_key": "DEEPGRAM_API_KEY",
    "elevenlabs_api_key": "ELEVENLABS_API_KEY",
    "cartesia_api_key": "CARTESIA_API_KEY",
    "google_api_key": "GOOGLE_API_KEY",
    "anthropic_api_key": "ANTHROPIC_API_KEY",
    "openai_compatible_llm_url": "OPENAI_COMPATIBLE_LLM_URL",
    "openai_compatible_llm_api_key": "OPENAI_COMPATIBLE_LLM_API_KEY",
    "scaleway_secret_key": "SCALEWAY_SECRET_KEY",
    "scaleway_project_id": "SCALEWAY_PROJECT_ID",
    "azure_openai_api_key": "AZURE_OPENAI_API_KEY",
    "azure_openai_endpoint": "AZURE_OPENAI_ENDPOINT",
    "azure_openai_api_version": "AZURE_OPENAI_API_VERSION",
    "gcp_project_id": "GCP_PROJECT_ID",
    "gcp_location": "GCP_LOCATION",
    "gcp_api_key": "GCP_API_KEY",
    "self_hosted_stt_url": "SELF_HOSTED_STT_URL",
    "self_hosted_stt_api_key": "SELF_HOSTED_STT_API_KEY",
    "self_hosted_stt_model": "SELF_HOSTED_STT_MODEL",
    "self_hosted_tts_url": "SELF_HOSTED_TTS_URL",
    "self_hosted_tts_api_key": "SELF_HOSTED_TTS_API_KEY",
    "self_hosted_tts_model": "SELF_HOSTED_TTS_MODEL",
    "embedding_api_url": "EMBEDDING_API_URL",
    "embedding_api_key": "EMBEDDING_API_KEY",
    "embedding_model": "EMBEDDING_MODEL",
    "twilio_account_sid": "TWILIO_ACCOUNT_SID",
    "twilio_auth_token": "TWILIO_AUTH_TOKEN",
    "twilio_phone_number": "TWILIO_PHONE_NUMBER",
}


def _mask_key(value: str) -> str:
    """Mask an API key for display, showing only last 4 chars."""
    if not value or len(value) < 8:
        return "••••" if value else ""
    return "••••••••" + value[-4:]


class ApiKeyStatus(BaseModel):
    field: str
    env_var: str
    is_set: bool
    source: str  # "env", "dashboard", or "none"
    masked_value: str


class ApiKeysResponse(BaseModel):
    keys: list[ApiKeyStatus]


class ApiKeyUpdate(BaseModel):
    """Update one or more API keys. Only provided fields are updated."""
    openai_api_key: Optional[str] = None
    deepgram_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    cartesia_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    openai_compatible_llm_url: Optional[str] = None
    openai_compatible_llm_api_key: Optional[str] = None
    scaleway_secret_key: Optional[str] = None
    scaleway_project_id: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_api_version: Optional[str] = None
    gcp_project_id: Optional[str] = None
    gcp_location: Optional[str] = None
    gcp_api_key: Optional[str] = None
    self_hosted_stt_url: Optional[str] = None
    self_hosted_stt_api_key: Optional[str] = None
    self_hosted_stt_model: Optional[str] = None
    self_hosted_tts_url: Optional[str] = None
    self_hosted_tts_api_key: Optional[str] = None
    self_hosted_tts_model: Optional[str] = None
    embedding_api_url: Optional[str] = None
    embedding_api_key: Optional[str] = None
    embedding_model: Optional[str] = None
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None

    # FINDING-007: changing a *URL* field (see `_URL_FIELDS`) to a new,
    # non-empty value requires this to be explicitly `true`. Prevents a
    # single unreviewed write from silently redirecting participant
    # audio/transcripts or an operator's provider spend to another host.
    confirm_endpoint_change: bool = False


class AuthConfigResponse(BaseModel):
    auth_enabled: bool
    username: str


async def get_effective_key(field: str) -> str:
    """
    Get the effective value for an API key field.
    Dashboard overrides (Redis) take priority over .env values.
    """
    redis = await get_redis()
    override = await redis.hget(_REDIS_KEY, field)
    if override:
        # FINDING-006: values are stored encrypted (see `update_api_keys`).
        # `decrypt_secret` transparently returns pre-existing plaintext
        # values unchanged, so upgrading does not break existing overrides.
        return decrypt_secret(override)
    return getattr(settings, field, "")


async def _get_all_overrides() -> dict[str, str]:
    """Get all Redis-stored API key overrides, decrypted (FINDING-006)."""
    redis = await get_redis()
    raw = await redis.hgetall(_REDIS_KEY)
    return {field: decrypt_secret(value) for field, value in raw.items()}


@router.get("/keys", response_model=ApiKeysResponse)
async def list_api_keys():
    """List all configurable API keys with their status (masked)."""
    overrides = await _get_all_overrides()
    keys = []

    for field, env_var in _API_KEY_FIELDS.items():
        env_value = getattr(settings, field, "")
        override_value = overrides.get(field, "")

        if override_value:
            source = "dashboard"
            effective = override_value
        elif env_value:
            source = "env"
            effective = env_value
        else:
            source = "none"
            effective = ""

        keys.append(
            ApiKeyStatus(
                field=field,
                env_var=env_var,
                is_set=bool(effective),
                source=source,
                masked_value=_mask_key(effective),
            )
        )

    return ApiKeysResponse(keys=keys)


@router.put("/keys", response_model=ApiKeysResponse)
async def update_api_keys(
    data: ApiKeyUpdate, payload: dict | None = Depends(require_auth)
):
    """
    Update API key overrides. These are stored in Redis (encrypted,
    FINDING-006) and take priority over .env values. Send an empty string
    to clear an override.

    FINDING-007: URL-valued fields (`_URL_FIELDS`) are SSRF-validated and
    require `confirm_endpoint_change: true` to change to a new value.
    """
    redis = await get_redis()
    updates = data.model_dump(exclude={"confirm_endpoint_change"}, exclude_none=True)
    actor = _actor(payload)
    timestamp = datetime.now(timezone.utc).isoformat()

    for field, value in updates.items():
        if field not in _API_KEY_FIELDS:
            continue

        if field in _URL_FIELDS and value:
            try:
                validate_egress_url(value, field=field)
            except EgressURLError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from None

            old_value = await get_effective_key(field)
            if value != old_value and not data.confirm_endpoint_change:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Changing {field} to a new value requires "
                        "confirm_endpoint_change: true. This changes where "
                        "participant audio/transcripts and API keys are sent."
                    ),
                )

        if value == "":
            # Clear the override — fall back to .env
            await redis.hdel(_REDIS_KEY, field)
            logger.info(f"Settings audit: actor={actor} action=clear field={field} at={timestamp}")
        else:
            if field in _URL_FIELDS:
                # URLs are not secrets — log old/new for the audit trail
                # required by FINDING-007 (rec. 3).
                logger.info(
                    f"Settings audit: actor={actor} action=set field={field} "
                    f"old={old_value!r} new={value!r} at={timestamp}"
                )
                await redis.hset(_REDIS_KEY, field, value)
            else:
                await redis.hset(_REDIS_KEY, field, encrypt_secret(value))
                logger.info(f"Settings audit: actor={actor} action=set field={field} at={timestamp}")

    # Return updated status
    return await list_api_keys()


@router.get("/auth", response_model=AuthConfigResponse)
async def get_auth_config():
    """Get the current authentication configuration."""
    return AuthConfigResponse(
        auth_enabled=settings.auth_enabled,
        username=settings.auth_username,
    )


# ── Boolean feature flags ────────────────────────────────────────────────


class FlagStatus(BaseModel):
    field: str
    env_var: str
    enabled: bool
    source: str  # "env" | "dashboard" | "default"


class FlagsResponse(BaseModel):
    flags: list[FlagStatus]


class FlagsUpdate(BaseModel):
    """Update one or more boolean flags. Only provided fields are touched."""
    openai_use_eu: Optional[bool] = None


async def get_effective_flag(field: str) -> bool:
    """Resolve a boolean flag: dashboard override (Redis) > .env value."""
    redis = await get_redis()
    override = await redis.hget(_FLAGS_REDIS_KEY, field)
    if override is not None and override != "":
        return _coerce_bool(override)
    return bool(getattr(settings, field, False))


@router.get("/flags", response_model=FlagsResponse)
async def list_flags():
    """List all boolean feature flags with their status and source."""
    redis = await get_redis()
    overrides = await redis.hgetall(_FLAGS_REDIS_KEY)
    out: list[FlagStatus] = []

    for field, env_var in _FLAG_FIELDS.items():
        env_value = bool(getattr(settings, field, False))
        ov = overrides.get(field)
        if ov is not None and ov != "":
            enabled = _coerce_bool(ov)
            source = "dashboard"
        else:
            enabled = env_value
            source = "env" if env_value else "default"

        out.append(
            FlagStatus(
                field=field,
                env_var=env_var,
                enabled=enabled,
                source=source,
            )
        )

    return FlagsResponse(flags=out)


@router.put("/flags", response_model=FlagsResponse)
async def update_flags(data: FlagsUpdate):
    """Update boolean flag overrides. Stored in Redis, takes priority over .env."""
    redis = await get_redis()
    updates = data.model_dump(exclude_none=True)

    for field, value in updates.items():
        if field not in _FLAG_FIELDS:
            continue
        await redis.hset(_FLAGS_REDIS_KEY, field, "true" if value else "false")
        logger.info(f"Set flag override: {field}={value}")

    return await list_flags()


# ── Interview audio storage (local / S3) ─────────────────────────────────


_AUDIO_STORAGE_REDIS_KEY = "oasis:settings:audio_storage"

_AUDIO_STORAGE_FIELDS: dict[str, tuple[str, bool]] = {
    "audio_storage_backend": ("AUDIO_STORAGE_BACKEND", False),
    "audio_storage_local_path": ("AUDIO_STORAGE_LOCAL_PATH", False),
    "audio_s3_bucket": ("AUDIO_S3_BUCKET", False),
    "audio_s3_prefix": ("AUDIO_S3_PREFIX", False),
    "audio_s3_region": ("AUDIO_S3_REGION", False),
    "audio_s3_endpoint_url": ("AUDIO_S3_ENDPOINT_URL", False),
    "audio_s3_access_key_id": ("AUDIO_S3_ACCESS_KEY_ID", True),
    "audio_s3_secret_access_key": ("AUDIO_S3_SECRET_ACCESS_KEY", True),
}


class AudioStorageSettingStatus(BaseModel):
    field: str
    env_var: str
    is_set: bool
    source: str  # "env", "dashboard", or "none"
    display_value: str
    sensitive: bool


class AudioStorageResponse(BaseModel):
    settings: list[AudioStorageSettingStatus]


class AudioStorageUpdate(BaseModel):
    audio_storage_backend: Optional[str] = None
    audio_storage_local_path: Optional[str] = None
    audio_s3_bucket: Optional[str] = None
    audio_s3_prefix: Optional[str] = None
    audio_s3_region: Optional[str] = None
    audio_s3_endpoint_url: Optional[str] = None
    audio_s3_access_key_id: Optional[str] = None
    audio_s3_secret_access_key: Optional[str] = None

    # FINDING-007 (Revision 4 residual): `audio_s3_endpoint_url` carries
    # participant audio and S3 credentials to whatever host it names
    # (`audio/storage.py`'s boto3 client) but, unlike the five fields in
    # `_URL_FIELDS` above, was never SSRF-validated or confirmation-gated.
    # Same treatment as `ApiKeyUpdate.confirm_endpoint_change`.
    confirm_endpoint_change: bool = False


async def get_effective_audio_setting(field: str) -> str:
    """Dashboard override (Redis) > .env value for audio storage fields."""
    if field not in _AUDIO_STORAGE_FIELDS:
        return ""
    redis = await get_redis()
    override = await redis.hget(_AUDIO_STORAGE_REDIS_KEY, field)
    if override is not None and override != "":
        # FINDING-006: sensitive fields (S3 keys) are stored encrypted.
        _, sensitive = _AUDIO_STORAGE_FIELDS[field]
        return decrypt_secret(override) if sensitive else override
    return str(getattr(settings, field, "") or "")


async def get_effective_audio_settings() -> dict[str, str]:
    """All audio storage fields with effective values."""
    return {field: await get_effective_audio_setting(field) for field in _AUDIO_STORAGE_FIELDS}


def _display_value(value: str, *, sensitive: bool) -> str:
    if not value:
        return ""
    if sensitive:
        return _mask_key(value)
    return value


@router.get("/audio-storage", response_model=AudioStorageResponse)
async def list_audio_storage_settings():
    """List interview audio storage settings (local path or S3)."""
    redis = await get_redis()
    overrides = await redis.hgetall(_AUDIO_STORAGE_REDIS_KEY)
    out: list[AudioStorageSettingStatus] = []

    for field, (env_var, sensitive) in _AUDIO_STORAGE_FIELDS.items():
        env_value = str(getattr(settings, field, "") or "")
        override_value = overrides.get(field, "")
        if override_value and sensitive:
            override_value = decrypt_secret(override_value)

        if override_value:
            source = "dashboard"
            effective = override_value
        elif env_value:
            source = "env"
            effective = env_value
        else:
            source = "none"
            effective = ""

        out.append(
            AudioStorageSettingStatus(
                field=field,
                env_var=env_var,
                is_set=bool(effective),
                source=source,
                display_value=_display_value(effective, sensitive=sensitive),
                sensitive=sensitive,
            )
        )

    return AudioStorageResponse(settings=out)


@router.put("/audio-storage", response_model=AudioStorageResponse)
async def update_audio_storage_settings(
    data: AudioStorageUpdate, payload: dict | None = Depends(require_auth)
):
    """Update audio storage overrides. Empty string clears an override.

    FINDING-007: `audio_s3_endpoint_url` is SSRF-validated and requires
    `confirm_endpoint_change: true` to change to a new value, the same
    treatment `PUT /api/settings/keys` already gives the five provider URL
    fields — it carries participant audio and S3 credentials to whatever
    host it names.
    """
    redis = await get_redis()
    updates = data.model_dump(exclude={"confirm_endpoint_change"}, exclude_none=True)
    actor = _actor(payload)
    timestamp = datetime.now(timezone.utc).isoformat()

    for field, value in updates.items():
        if field not in _AUDIO_STORAGE_FIELDS:
            continue

        if field == "audio_storage_backend" and value:
            normalized = value.strip().lower()
            if normalized not in ("local", "s3"):
                raise HTTPException(
                    status_code=400,
                    detail="audio_storage_backend must be 'local' or 's3'",
                )
            value = normalized

        if field == "audio_s3_endpoint_url" and value:
            try:
                validate_egress_url(value, field=field)
            except EgressURLError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from None

            old_value = await get_effective_audio_setting(field)
            if value != old_value and not data.confirm_endpoint_change:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Changing {field} to a new value requires "
                        "confirm_endpoint_change: true. This changes where "
                        "recorded participant audio and S3 credentials are sent."
                    ),
                )

        _, sensitive = _AUDIO_STORAGE_FIELDS[field]

        if value == "":
            await redis.hdel(_AUDIO_STORAGE_REDIS_KEY, field)
            logger.info(f"Settings audit: actor={actor} action=clear field={field} at={timestamp}")
        else:
            # FINDING-006: encrypt sensitive fields (S3 access/secret keys)
            # before they ever reach Redis.
            stored_value = encrypt_secret(value) if sensitive else value
            await redis.hset(_AUDIO_STORAGE_REDIS_KEY, field, stored_value)
            logger.info(f"Settings audit: actor={actor} action=set field={field} at={timestamp}")

    return await list_audio_storage_settings()


# ── Provider capability catalog ──────────────────────────────────────────

_SMOKE_RATE_LIMIT_SECONDS = 300
_SMOKE_LOCK_KEY = "oasis:settings:smoke_lock"


@router.get("/catalog")
async def get_provider_catalog() -> dict[str, Any]:
    """Return only providers/models whose credentials are fully configured."""
    return await get_configured_catalog()


class SmokeTestRequest(BaseModel):
    live: bool = True


@router.post("/smoke-test")
async def smoke_test_providers(data: SmokeTestRequest | None = None):
    """
    Run minimal live probes for every model in the configured catalog.

    The endpoint is rate limited and does not return secrets.
    """
    live = data.live if data else True
    if live:
        redis = await get_redis()
        acquired = await redis.set(
            _SMOKE_LOCK_KEY,
            "1",
            ex=_SMOKE_RATE_LIMIT_SECONDS,
            nx=True,
        )
        if not acquired:
            raise HTTPException(
                status_code=429,
                detail="Please wait before running another provider verification.",
            )

    result = await run_configured_smoke_tests(live=live)
    logger.info(
        "Provider smoke-test: live={} total={} passed={} failed={}",
        result["live"],
        result["total"],
        result["passed"],
        result["failed"],
    )
    return result
