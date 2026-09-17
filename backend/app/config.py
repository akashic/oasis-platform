"""
OASIS — Application configuration.

All settings are loaded from environment variables (or .env file).
"""

import secrets

from loguru import logger
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# FINDING-002: this literal must never be treated as a usable secret. It is
# published in .env.example and this repository, so any deployment that
# ships it unmodified must refuse to sign/verify tokens with it.
PLACEHOLDER_SECRET_KEY = "change-me-to-a-random-secret-key"
MIN_SECRET_KEY_LENGTH = 32

# FINDING-011: same treatment as PLACEHOLDER_SECRET_KEY above — this literal
# was previously the silent default for POSTGRES_PASSWORD in this file,
# docker-compose.yml and .env.example. It must never be treated as usable.
PLACEHOLDER_POSTGRES_PASSWORD = "change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Application ──
    app_name: str = "OASIS"
    app_env: str = "development"
    secret_key: str = PLACEHOLDER_SECRET_KEY
    # FINDING-004: `debug` no longer drives CORS (see `cors_allowed_origins`
    # below) — it only controls SQLAlchemy statement echoing now. Kept
    # opt-in-only default for local development.
    debug: bool = False

    # ── Public URL (used to build externally-facing URLs, e.g. Twilio
    #    <Stream> callbacks, without trusting the inbound Host header) ──
    domain: str = "localhost"

    # FINDING-004: CORS is an explicit allow-list, never derived from
    # `debug`. Empty (the default) means no cross-origin browser access at
    # all — `main.py` does not even register the CORS middleware in that
    # case, so no `Access-Control-Allow-*` headers are ever sent. Set a
    # comma-separated list of exact origins (scheme + host [+ port]) that
    # are allowed to call this API with credentials, e.g.
    # `CORS_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com`.
    # A raw string field (not `list[str]`) because pydantic-settings parses
    # env values for list-typed fields as JSON, not CSV. `validation_alias`
    # keeps the env var name `CORS_ALLOWED_ORIGINS` (no `_RAW` suffix).
    cors_allowed_origins_raw: str = Field(default="", validation_alias="CORS_ALLOWED_ORIGINS")

    @property
    def cors_allowed_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins_raw.split(",")
            if origin.strip()
        ]

    # FINDING-002 / FINDING-013: refuse to start with a weak/placeholder/
    # missing signing key. `scripts/install.sh` already generates a strong
    # key via `openssl rand -hex 32`, but a deploy path that skips the
    # installer must be assumed, so this is enforced here too.
    #
    # FINDING-013: this check is now unconditional — it previously only
    # fired when `app_env != "development"`, and `app_env` both defaults to
    # and ships (`.env.example`) as `"development"`, with `SECRET_KEY=`
    # empty. An empty string is a perfectly valid HS256 key for PyJWT, so on
    # that (very reachable) path every admin token, Twilio stream ticket and
    # monitor ticket (`app/auth.py`) and the Redis credential-encryption KEK
    # (`app/crypto.py`, FINDING-016) were forgeable/derivable from a public
    # constant. A weak/empty/placeholder key has no legitimate use in any
    # environment. `development` is no longer an exemption from the
    # *strength* requirement — it is only an exemption from refusing to
    # start: a weak key there is replaced with a random ephemeral one
    # instead of raising, so local iteration is not blocked. This mirrors
    # the unconditional treatment `_validate_postgres_password` below
    # already gives `POSTGRES_PASSWORD` (FINDING-011).
    @model_validator(mode="after")
    def _validate_secret_key(self) -> "Settings":
        is_weak = (
            not self.secret_key
            or self.secret_key == PLACEHOLDER_SECRET_KEY
            or len(self.secret_key) < MIN_SECRET_KEY_LENGTH
        )
        if not is_weak:
            return self

        if self.app_env == "development":
            # Generate a random, unpublished key for this process only.
            # Tokens, Twilio tickets and encrypted Redis credentials signed
            # with it will not survive a restart — that is expected in
            # development and is logged loudly so it is never mistaken for
            # a real deployment.
            self.secret_key = secrets.token_hex(32)
            logger.warning(
                "SECRET_KEY was missing, the published placeholder value, or "
                f"shorter than {MIN_SECRET_KEY_LENGTH} characters. Generated "
                "a random EPHEMERAL key for this process (APP_ENV=development "
                "only) — it will not survive a restart, so existing tokens, "
                "Twilio stream/monitor tickets, and encrypted Redis settings "
                "will stop validating/decrypting. Set a real, persistent "
                "SECRET_KEY (e.g. `openssl rand -hex 32`) before deploying."
            )
            return self

        raise ValueError(
            "SECRET_KEY is missing, is the published placeholder value, "
            f"or is shorter than {MIN_SECRET_KEY_LENGTH} characters. "
            "Refusing to start — set a strong, unique SECRET_KEY (e.g. "
            "`openssl rand -hex 32`)."
        )

    # ── PostgreSQL ──
    postgres_user: str = "oasis"
    # FINDING-011: no working default. `docker-compose.yml` fails the whole
    # stack closed with `${POSTGRES_PASSWORD:?...}` (the same treatment
    # `REDIS_PASSWORD` already has); this validator gives the same
    # unconditional guarantee for any deployment path that constructs
    # `Settings()` without going through that compose file (e.g. running
    # the backend directly against a local Postgres).
    postgres_password: str = ""
    postgres_db: str = "oasis"
    postgres_host: str = "postgres"
    postgres_port: int = 5432

    # FINDING-011: unconditional — unlike the SECRET_KEY check, this is not
    # exempted in `development`. A guessable, shared default credential on
    # the database holding every study, transcript and provider secret has
    # no legitimate use in any environment, matching the fail-closed
    # treatment already given to REDIS_PASSWORD at the compose level.
    @model_validator(mode="after")
    def _validate_postgres_password(self) -> "Settings":
        if not self.postgres_password or self.postgres_password == PLACEHOLDER_POSTGRES_PASSWORD:
            raise ValueError(
                "POSTGRES_PASSWORD is missing or is the published placeholder "
                f"value {PLACEHOLDER_POSTGRES_PASSWORD!r}. Refusing to start — "
                "set a strong, unique POSTGRES_PASSWORD (e.g. "
                "`openssl rand -hex 24`, which scripts/install.sh does for "
                "you on a fresh install)."
            )
        return self

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        """Synchronous URL for Alembic migrations."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── Redis ──
    redis_url: str = "redis://redis:6379/0"

    # ── AI Providers ──
    openai_api_key: str = ""
    deepgram_api_key: str = ""
    elevenlabs_api_key: str = ""
    cartesia_api_key: str = ""

    # ── OpenAI data-residency (EU regional API) ──
    # When OPENAI_USE_EU=true, all calls to OpenAI (chat, realtime, STT, TTS,
    # embeddings) are routed through https://eu.api.openai.com instead of the
    # default api.openai.com. Requires that the OpenAI project the API key
    # belongs to has data-residency enabled and a Modified Abuse Monitoring or
    # Zero Data Retention amendment in place. See
    # https://developers.openai.com/api/docs/guides/your-data
    openai_use_eu: bool = False

    # ── Scaleway (OpenAI-compatible LLM API) ──
    # Uses SCALEWAY_SECRET_KEY as the Bearer token (secret part of the API keypair)
    scaleway_secret_key: str = ""          # maps to SCALEWAY_SECRET_KEY in .env
    scaleway_project_id: str = ""          # maps to SCALEWAY_PROJECT_ID in .env
    scaleway_api_url: str = "https://api.scaleway.ai/v1"

    @property
    def scaleway_api_key(self) -> str:
        """Return the Scaleway secret key for use as a Bearer token."""
        return self.scaleway_secret_key

    # ── Google AI (Gemini Live native audio + Gemini text models) ──
    google_api_key: str = ""               # maps to GOOGLE_API_KEY in .env

    # ── Anthropic (Claude text models) ──
    anthropic_api_key: str = ""            # maps to ANTHROPIC_API_KEY in .env

    # ── OpenAI-Compatible Custom LLM (LiteLLM proxy, vLLM, etc.) ──
    # Point at any base URL that speaks the OpenAI Chat Completions protocol.
    # Used by voice pipelines when llm_model starts with "custom/".
    openai_compatible_llm_url: str = ""    # e.g. http://my-litellm:4000/v1
    openai_compatible_llm_api_key: str = ""

    # ── Azure OpenAI (self-hosted) ──
    azure_openai_api_key: str = ""
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-08-01-preview"

    # ── GCP Vertex AI (self-hosted) ──
    gcp_project_id: str = ""
    gcp_location: str = "us-central1"
    gcp_api_key: str = ""  # alternative to Application Default Credentials

    # ── Smart-turn detection (remote endpoint) ──
    # Leave empty to use the bundled on-device model. Set a URL to route
    # agents configured for "remote" turn detection to an HTTP smart-turn
    # service (e.g. a self-hosted smart-turn server).
    smart_turn_remote_url: str = ""     # e.g. http://my-server:8300/predict
    smart_turn_remote_api_key: str = ""  # optional bearer token

    # ── Self-Hosted STT/TTS (OpenAI-compatible endpoints) ──
    self_hosted_stt_url: str = ""       # e.g. http://my-server:8000/v1
    self_hosted_stt_api_key: str = ""   # optional, many local servers ignore this
    self_hosted_stt_model: str = "whisper-1"
    self_hosted_tts_url: str = ""       # e.g. http://my-server:8100/v1
    self_hosted_tts_api_key: str = ""
    self_hosted_tts_model: str = "tts-1"

    # ── Embeddings (RAG knowledge base) ──
    # Leave empty to use OpenAI (text-embedding-3-small). Set a URL to use
    # any OpenAI-compatible embedding server instead (e.g. LocalAI, TEI, vLLM).
    embedding_api_url: str = ""         # e.g. http://my-server:8200/v1
    embedding_api_key: str = ""         # falls back to OPENAI_API_KEY if empty
    embedding_model: str = ""           # falls back to text-embedding-3-small if empty

    # ── Telephony ──
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    # ── Authentication ──
    # FINDING-001: secure by default. Set AUTH_ENABLED=false and
    # APP_ENV=development explicitly to opt out for local development —
    # main.py refuses to start with auth disabled in any other environment.
    auth_enabled: bool = True
    auth_username: str = "admin"
    # FINDING-005: prefer AUTH_PASSWORD_HASH (Argon2id, see app/security.py).
    # AUTH_PASSWORD (plaintext) is a deprecated migration path — app/api/auth.py
    # logs a warning whenever it is used to authenticate.
    auth_password: str = ""
    auth_password_hash: str = ""

    # ── Voice interview audio recording (web widget only) ──
    # Enabled per agent via store_audio. These settings configure where files go.
    audio_storage_backend: str = "local"  # "local" | "s3"
    audio_storage_local_path: str = "/data/oasis-recordings"
    audio_s3_bucket: str = ""
    audio_s3_prefix: str = "oasis-recordings"
    audio_s3_region: str = "us-east-1"
    audio_s3_access_key_id: str = ""
    audio_s3_secret_access_key: str = ""
    audio_s3_endpoint_url: str = ""  # optional, for MinIO

    # ── Egress guard (FINDING-007) ──
    # FINDING-007 (Revision 4 residual): plain http egress to a private
    # (RFC1918/loopback-adjacent) host used to be allowed unconditionally,
    # which meant any sibling container reachable by IP or Compose alias
    # (e.g. `oasis-platform-postgres-1`) was a permitted destination, not
    # just the five names in `egress_guard._DENIED_HOSTNAMES`. Plain http is
    # now only allowed to hosts explicitly listed here — comma-separated
    # hostnames, literal IPs, or CIDR ranges, e.g.:
    #   EGRESS_ALLOWED_PRIVATE_HOSTS=my-litellm,10.0.5.0/24,192.168.1.50
    # Empty (the default) means no plain-http private destinations are
    # permitted at all — operators must either use https or add their
    # self-hosted host/network here.
    egress_allowed_private_hosts: str = Field(
        default="", validation_alias="EGRESS_ALLOWED_PRIVATE_HOSTS"
    )

    # ── Trusted reverse proxy (FINDING-015) ──
    # FINDING-015: `request.client.host` / `websocket.client.host` are the
    # TCP peer address, which in the shipped topology is always Caddy
    # (docker/Caddyfile proxies /api/* and /ws/* to backend:8000) — so every
    # rate limit, lockout and audit log line keyed on it collapsed to one
    # value for the whole internet. `uvicorn.middleware.proxy_headers.
    # ProxyHeadersMiddleware` (wired up in main.py) corrects
    # `scope["client"]` from `X-Forwarded-For` — but only when the immediate
    # TCP peer is in this trusted list, so a client cannot simply set the
    # header itself and evade rate limiting. Comma-separated IPs/CIDRs.
    # Default matches the fixed subnet docker-compose.yml assigns to
    # `oasis_net` — override if you run without docker-compose or have
    # changed that subnet.
    trusted_proxy_ips: str = Field(
        default="172.28.0.0/24", validation_alias="TRUSTED_PROXY_IPS"
    )


settings = Settings()
