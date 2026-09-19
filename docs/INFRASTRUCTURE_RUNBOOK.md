# OASIS Infrastructure and Authentication Runbook

> **Scope.** Everything an operator must provision, generate and configure to stand up OASIS
> and keep it authenticated and authorised: the container stack, the host, every secret and
> key, the trust boundaries between components, verification steps, and rotation procedures.
> Written against the codebase at commit `9e8a109` (security remediation Revision 5, 2026-09-19).
>
> **Related documents.** [`DEPLOYMENT.md`](DEPLOYMENT.md) is the step-by-step Hetzner walkthrough
> for a first-time operator. This runbook is the reference behind it: it does not repeat the
> Hetzner console screenshots, but it does cover every variable, every credential and every
> trust decision, including manual (non-installer) deployments. `.env.example` is the source of
> truth for variable names; `docker-compose.yml` for the service topology;
> [`security-assessment-oasis-platform.md`](security-assessment-oasis-platform.md) for the open
> findings that still constrain operations.

## Contents

1. [Stack inventory](#1-stack-inventory)
2. [Host prerequisites](#2-host-prerequisites)
3. [Secrets and configuration inventory](#3-secrets-and-configuration-inventory)
4. [Setup sequence](#4-setup-sequence)
5. [Authentication and trust model](#5-authentication-and-trust-model)
6. [Provider onboarding](#6-provider-onboarding)
7. [Telephony (Twilio) setup](#7-telephony-twilio-setup)
8. [Post-setup verification](#8-post-setup-verification)
9. [Rotation procedures](#9-rotation-procedures)
10. [Upgrading a pre-hardening deployment](#10-upgrading-a-pre-hardening-deployment)
11. [Backups and what to protect](#11-backups-and-what-to-protect)
12. [Known gaps that affect operations](#12-known-gaps-that-affect-operations)

---

## 1. Stack inventory

One Docker Compose project, five containers, one bridge network. Only Caddy publishes ports.

| Service | Image | Role | Listens | Persistent state |
|---|---|---|---|---|
| `caddy` | `caddy:2-alpine` | TLS termination, Let's Encrypt, path routing, security headers, request body cap | `80`, `443` on the host | `caddy_data` (certificates, ACME account), `caddy_config` |
| `frontend` | built from `frontend/Dockerfile` (Node 20 build, `nginx:alpine` serve) | React dashboard and participant interview widget | `80` internal only | none |
| `backend` | built from `backend/Dockerfile` (`python:3.12-slim`, FastAPI, uvicorn, Pipecat, LiteLLM) | REST admin API, all WebSocket planes, Twilio plane, media pipelines. Runs `alembic upgrade head` on every start | `8000` internal only | bind mount `./data/recordings` for local audio |
| `postgres` | `pgvector/pgvector:pg16` | Studies, agents, sessions, transcripts, embeddings | `5432` internal only | `pgdata` |
| `redis` | `redis:7-alpine` | Session leases, JWT denylist, single-use tickets, rate-limit counters, dashboard-set provider keys (encrypted) | `6379` internal only | `redisdata` |

Network: `oasis_net`, bridge, **pinned to `172.28.0.0/24`**. The pin matters: the backend only
trusts `X-Forwarded-For` from peers in `TRUSTED_PROXY_IPS`, whose default is this subnet. If you
change one you must change the other.

Path routing at the edge (`docker/Caddyfile`):

| Path | Upstream | Notes |
|---|---|---|
| `/api/*` | `backend:8000` | 10 MB request body cap, `frame-ancestors 'none'` |
| `/ws/*` | `backend:8000` | WebSocket upgrade, 30 s keepalive |
| `/interview/*` | `frontend:80` | Participant widget. Deliberately framable so it can be embedded in third-party survey tools |
| everything else | `frontend:80` | Admin dashboard, `frame-ancestors 'none'` |

Backend middleware order, outermost first: trusted-proxy header rewrite, global 10 MiB body
cap, CORS (only registered when `CORS_ALLOWED_ORIGINS` is non-empty), router.

## 2. Host prerequisites

The supported target is a single Linux VM. `scripts/install.sh` is tested on Ubuntu 22.04+ and
must run as root.

| Requirement | Detail |
|---|---|
| OS | Ubuntu 22.04 or later. Other distributions work with Docker installed but the installer warns |
| Docker | Docker Engine with the Compose v2 plugin (`docker compose`). The installer installs it via `get.docker.com` |
| Memory | The backend container is capped at 2 GB (`mem_limit`). Size the host so that cap plus Postgres, Redis, Caddy and the OS fit comfortably. See `DEPLOYMENT.md` Step 3 for the tested Hetzner plan |
| Inbound ports | `22/tcp` (SSH), `80/tcp` (ACME challenge and HTTP to HTTPS redirect), `443/tcp` (all traffic). The installer configures UFW to exactly these and denies everything else |
| Outbound | Unrestricted by default. The backend needs egress to every AI provider you enable, to Twilio, and to Let's Encrypt |
| DNS | An `A` record for `DOMAIN` pointing at the host's public IP **before** first start, or Let's Encrypt issuance fails. Without a domain the installer offers a free `oasis.<ip-with-dashes>.sslip.io` name |
| Host hardening (installer) | `fail2ban` enabled, `unattended-upgrades` enabled with automatic reboot off |
| Local tooling | `openssl` for generating secrets. Nothing else: the admin password is hashed inside the backend image so Argon2 is not needed on the host |

Install location used by the installer and updater: `/opt/oasis`. The updater honours
`OASIS_DIR` if you cloned elsewhere.

## 3. Secrets and configuration inventory

All configuration is environment variables loaded from `.env` at the repository root. Compose
passes the whole file to `backend` and `caddy`; `postgres` and `redis` receive only the specific
values interpolated in `docker-compose.yml`. **`.env` is the single most sensitive file on the
host.** The installer creates it with mode `600`; keep it that way.

### 3.1 Core platform secrets (required, generated, never shared)

| Variable | Purpose | How to generate | Consumed by | Fail-closed behaviour |
|---|---|---|---|---|
| `SECRET_KEY` | Signs admin JWTs. HKDF-derives the monitor-ticket signing key and the Fernet key that encrypts dashboard-set provider credentials in Redis. Also signs Twilio stream tickets directly | `openssl rand -hex 32` | backend | Backend refuses to start if empty, equal to the published placeholder, or under 32 characters. Only `APP_ENV=development` relaxes this, and then a random ephemeral key is generated per process and logged as a warning |
| `POSTGRES_PASSWORD` | Database role password for `POSTGRES_USER` | `openssl rand -hex 24` | postgres (sets the role password on first init of an empty volume), backend (via `DATABASE_URL`) | Compose refuses to start if unset. Backend refuses to start if unset or `change-me` in every environment |
| `REDIS_PASSWORD` | Redis `requirepass` | `openssl rand -hex 24` | redis (`--requirepass`, healthcheck), backend (Compose builds `REDIS_URL` from it, overriding any value in `.env`) | Compose refuses to start if unset |
| `AUTH_PASSWORD_HASH` | Argon2id hash of the dashboard admin password | See [3.5](#35-generating-the-admin-password-hash) | backend | If unset, backend falls back to the deprecated plaintext `AUTH_PASSWORD` and logs a warning on every use. If both are unset, login returns 503 |

Redis also has `CONFIG`, `KEYS`, `FLUSHALL` and `FLUSHDB` renamed away in the Compose command
line. Do not remove that.

### 3.2 Security posture flags

| Variable | Default in `.env.example` | What it controls | Guidance |
|---|---|---|---|
| `APP_ENV` | `production` | The only value that relaxes anything is the literal `development`. Any other value, including typos, is treated as production | Leave as `production`. Set `development` only on a laptop |
| `AUTH_ENABLED` | `true` | Whether the admin API requires a JWT | Backend refuses to start with `false` unless `APP_ENV=development`. Never disable on a reachable host |
| `AUTH_USERNAME` | `admin` | Admin login name | Compared in constant time |
| `DEBUG` | `false` | SQLAlchemy statement echo only. **No longer affects CORS** | Leave `false` |
| `DOMAIN` | `localhost` | Caddy site address (drives Let's Encrypt), the backend's public URL for Twilio `<Stream>` callbacks and webhook signature validation | Must be the real internet-facing hostname before enabling Twilio. Caddy refuses to start if empty. `localhost` still gets TLS from Caddy's internal CA |
| `CORS_ALLOWED_ORIGINS` | empty | Comma-separated exact origins allowed to call the API cross-origin with credentials | Leave empty for the standard same-origin Caddy deployment. Never put `*` here: it is passed through verbatim |
| `TRUSTED_PROXY_IPS` | `172.28.0.0/24` | Peers whose `X-Forwarded-For` the backend honours for rate limiting, lockout and audit logs | Must match the Compose subnet. Change only if you re-subnet `oasis_net`, front Caddy with another proxy, or run without Compose |
| `EGRESS_ALLOWED_PRIVATE_HOSTS` | empty | Hostnames, IPs or CIDRs that provider URL fields may reach over plain `http` | Empty means every provider URL must be `https`. Add only hosts you run yourself. Avoid broad CIDRs |
| `CADDY_CONFIG_FILE` | unset (uses `docker/Caddyfile`) | Set to `./docker/Caddyfile.dev` to serve plaintext `:80` with no TLS | Local scripted testing only. Nothing stops it being set in production, so grep for it before every deploy |

### 3.3 Database and cache connection settings

| Variable | Default | Note |
|---|---|---|
| `POSTGRES_USER` | `surveyor` in `.env.example`, `oasis` if unset in Compose | Use the value from **your** `.env` in every `psql` and `pg_dump` command. The examples in `DEPLOYMENT.md` assume `oasis` |
| `POSTGRES_DB` | `surveyor` in `.env.example`, `oasis` if unset in Compose | Same caveat |
| `POSTGRES_HOST`, `POSTGRES_PORT` | `postgres`, `5432` | Compose service name. Change only when running the backend outside Compose |
| `DATABASE_URL` | assembled from the above | Uses `postgresql+asyncpg://`. No TLS to Postgres inside the bridge network (open item, see section 12) |
| `REDIS_URL` | `redis://redis:6379/0` | **Ignored under Compose**, which injects `redis://:<REDIS_PASSWORD>@redis:6379/0`. Only relevant when running the backend directly, in which case embed the password yourself |

### 3.4 Provider credentials (optional, at least one LLM required)

Every one of these can be set in `.env` or entered later in the dashboard **Settings** page.
Dashboard values are stored in Redis, encrypted with a key derived from `SECRET_KEY`, and
override `.env` at runtime. URL-valued fields are SSRF-validated and require an explicit
confirmation when changed. Full onboarding notes per provider are in
[section 6](#6-provider-onboarding).

| Provider | Variables | Required for |
|---|---|---|
| OpenAI | `OPENAI_API_KEY`, optional `OPENAI_USE_EU` | Text chat, Whisper STT, TTS, Realtime voice-to-voice, default embeddings. **The installer requires this key** |
| Anthropic | `ANTHROPIC_API_KEY` | Claude text models |
| Google | `GOOGLE_API_KEY` | Gemini text and Gemini Live |
| Deepgram | `DEEPGRAM_API_KEY` | STT |
| ElevenLabs | `ELEVENLABS_API_KEY` | TTS |
| Cartesia | `CARTESIA_API_KEY` | TTS |
| Scaleway | `SCALEWAY_SECRET_KEY`, `SCALEWAY_PROJECT_ID`, `SCALEWAY_API_URL` | EU-hosted LLM |
| OpenAI-compatible / LiteLLM | `OPENAI_COMPATIBLE_LLM_URL`, `OPENAI_COMPATIBLE_LLM_API_KEY` | OpenRouter, Groq, Mistral, Together, vLLM, Ollama, any Chat Completions endpoint. Selected per agent with a `custom/<model>` name |
| Self-hosted STT | `SELF_HOSTED_STT_URL`, `SELF_HOSTED_STT_API_KEY`, `SELF_HOSTED_STT_MODEL` | Speaches, faster-whisper, LocalAI |
| Self-hosted TTS | `SELF_HOSTED_TTS_URL`, `SELF_HOSTED_TTS_API_KEY`, `SELF_HOSTED_TTS_MODEL` | Kokoro, Piper, LocalAI |
| Embeddings | `EMBEDDING_API_URL`, `EMBEDDING_API_KEY`, `EMBEDDING_MODEL` | Knowledge and RAG. Empty falls back to OpenAI `text-embedding-3-small`. Schema expects 1536 dimensions |
| Smart-turn (remote) | `SMART_TURN_REMOTE_URL`, `SMART_TURN_REMOTE_API_KEY` | Optional remote end-of-turn model. **Env only**, not dashboard-settable, and not listed in `.env.example`: add the two lines yourself |
| Azure OpenAI | `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION` | Present in config and dashboard but **disabled in the provider catalog** at this commit. Setting them has no effect |
| GCP Vertex | `GCP_PROJECT_ID`, `GCP_LOCATION`, `GCP_API_KEY` | Same: **disabled in the provider catalog** at this commit |

### 3.5 Generating the admin password hash

The installer does this for you. For a manual deployment or a password change, hash inside the
backend image so Argon2 is never needed on the host and the password never appears on a command
line:

```bash
cd /opt/oasis
docker compose build backend
printf '%s' 'your-new-password' | docker run --rm -i --entrypoint python oasis-backend -c \
  'import sys; from app.security import hash_password; print(hash_password(sys.stdin.read().rstrip("\n")))'
```

Paste the output into `AUTH_PASSWORD_HASH=` in `.env`, make sure `AUTH_PASSWORD=` is empty, then
`docker compose up -d`. Run `set +o history` first if your shell keeps history, or read the
password into a variable with `read -rs` instead of typing it inline.

### 3.6 Telephony and audio storage

| Variable | Note |
|---|---|
| `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER` | See [section 7](#7-telephony-twilio-setup). Without `TWILIO_AUTH_TOKEN` every inbound webhook is rejected with 403 |
| `AUDIO_STORAGE_BACKEND` | `local` (default, bind mount `./data/recordings`) or `s3` |
| `AUDIO_STORAGE_LOCAL_PATH` | Container path, default `/data/oasis-recordings` |
| `AUDIO_S3_BUCKET`, `AUDIO_S3_PREFIX`, `AUDIO_S3_REGION`, `AUDIO_S3_ACCESS_KEY_ID`, `AUDIO_S3_SECRET_ACCESS_KEY` | S3 credentials. Dashboard-settable and encrypted at rest in Redis |
| `AUDIO_S3_ENDPOINT_URL` | MinIO or other custom endpoint. SSRF-validated, confirm-gated, and re-validated immediately before every S3 client construction. Plain `http` requires the host in `EGRESS_ALLOWED_PRIVATE_HOSTS` |

## 4. Setup sequence

### 4.1 Path A: installer (recommended)

```bash
curl -fsSL https://raw.githubusercontent.com/oasis-surveys/oasis-platform/main/scripts/install.sh | bash
# or, from a clone:
sudo bash scripts/install.sh
```

What it does with credentials, step by step:

1. Updates the OS, installs Docker, configures UFW (22, 80, 443), enables fail2ban and unattended-upgrades.
2. Clones or fast-forwards `/opt/oasis` to `origin/main`.
3. If `.env` already exists it is **kept untouched** and steps 4 to 7 are skipped. Otherwise:
4. Prompts for `DOMAIN` (defaults to the sslip.io name), `OPENAI_API_KEY` (hidden input, must start with `sk-`), and an admin password (hidden input, auto-generated with `openssl rand -hex 16` if blank, in which case it is echoed to the terminal once).
5. Generates `SECRET_KEY` (32 bytes hex), `POSTGRES_PASSWORD` and `REDIS_PASSWORD` (24 bytes hex each).
6. Writes these plus `APP_ENV=production`, `DEBUG=false`, `AUTH_ENABLED=true`, `AUTH_USERNAME=admin` into `.env` and sets mode `600`. `AUTH_PASSWORD` is never written.
7. Builds the backend image and hashes the admin password inside it over stdin, writing only `AUTH_PASSWORD_HASH`. Aborts if the hash comes back empty.
8. `docker compose build && docker compose up -d`. Caddy provisions a Let's Encrypt certificate on first request, which can take up to a minute.
9. Prints the login and the admin password one final time. **Record it now**: only the hash is on disk and it cannot be recovered.

The generated secrets never leave the host. The one thing the installer echoes in clear is an
auto-generated admin password, so do not run it under `bash -x`, `script`, or a CI log collector.

### 4.2 Path B: manual Compose deployment

Use this for a non-Ubuntu host, an existing Docker host, or when you want to control every
value.

```bash
git clone https://github.com/oasis-surveys/oasis-platform.git /opt/oasis
cd /opt/oasis
cp .env.example .env
chmod 600 .env

# Core secrets
sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$(openssl rand -hex 32)|"               .env
sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(openssl rand -hex 24)|" .env
sed -i "s|^REDIS_PASSWORD=.*|REDIS_PASSWORD=$(openssl rand -hex 24)|"       .env

# Public hostname (DNS A record must already resolve to this host)
sed -i "s|^DOMAIN=.*|DOMAIN=oasis.example.com|" .env

# At least one LLM provider
sed -i "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=sk-...|" .env
```

Then generate the admin hash exactly as in [3.5](#35-generating-the-admin-password-hash), and
start:

```bash
docker compose build
docker compose up -d
docker compose ps
```

Checklist before the first `up`:

- `APP_ENV=production` (already the shipped default).
- `SECRET_KEY` 64 hex characters, `POSTGRES_PASSWORD` and `REDIS_PASSWORD` non-empty.
- `AUTH_PASSWORD_HASH` set, `AUTH_PASSWORD` empty.
- `DOMAIN` resolves publicly, or is `localhost` for a laptop.
- `CADDY_CONFIG_FILE` absent.
- `EGRESS_ALLOWED_PRIVATE_HOSTS` lists any self-hosted provider you will reach over plain `http`, and nothing else.

### 4.3 Local development

Set `APP_ENV=development` explicitly. That is the only environment where `AUTH_ENABLED=false`
is accepted and where an empty `SECRET_KEY` is replaced by a per-process random key. Be aware
that with the ephemeral key every restart invalidates all sessions and makes any dashboard-set
provider keys undecryptable, so set a real `SECRET_KEY` even locally if you use the Settings
page. For plaintext HTTP (some test tooling), add `CADDY_CONFIG_FILE=./docker/Caddyfile.dev`.

## 5. Authentication and trust model

### 5.1 Admin dashboard

| Aspect | Behaviour |
|---|---|
| Credential | `AUTH_USERNAME` plus Argon2id hash in `AUTH_PASSWORD_HASH`. Username and any plaintext fallback compared in constant time |
| Login endpoint | `POST /api/auth/login`. Returns 503 if auth is disabled or no credential is configured |
| Lockout | 5 failed attempts per client IP plus username within 15 minutes locks that pair for 15 minutes, returning 429 with `Retry-After`. Counters live in Redis |
| Token | HS256 JWT signed with `SECRET_KEY`, `typ: access`, unique `jti`, **2 hour lifetime**, no refresh flow. Stored by the SPA in `localStorage` |
| Logout | `POST /api/auth/logout` adds the token's `jti` to a Redis denylist. Every request checks the denylist, so revocation is immediate |
| Audit | Every login attempt is logged with outcome, username and client IP |
| Redis outage | Fails closed. Token verification raises, the admin API returns 500 until Redis is back |

### 5.2 Session monitor WebSocket

The dashboard never puts the admin JWT in a URL. It calls `POST /api/auth/monitor-ticket` with
the bearer token, receives a 60-second single-use ticket bound to the requesting operator and
the target `session_id`, and opens `/ws/monitor/{session_id}?ticket=...`. Tickets are signed
with a key HKDF-derived from `SECRET_KEY`, carry no `typ: access`, and are explicitly rejected by
the admin auth dependency, so a captured ticket cannot be replayed against the REST API.
Single use is enforced atomically in Redis.

### 5.3 Participant interview widget

Participants authenticate only by the agent's 128-bit `widget_key` in the share link. No login.
The widget is served with `Permissions-Policy: microphone=(self)` and is framable by any origin
by design. The interview and chat WebSockets under `/ws/` are keyed on that widget key.

### 5.4 Twilio plane

Covered in [section 7](#7-telephony-twilio-setup): inbound webhooks must carry a valid
`X-Twilio-Signature` computed over the public `DOMAIN` URL, and the media stream must present a
60-second stream ticket that the webhook minted.

### 5.5 Reverse proxy trust

Caddy overwrites `X-Forwarded-For` with the address it observed and forwards to the backend.
The backend's proxy-header middleware honours that header only when the immediate peer is inside
`TRUSTED_PROXY_IPS`. Everything that keys on client IP (login lockout, Twilio webhook limit of 60
per minute, Twilio WebSocket cap of 30 new connections per minute, audit lines) therefore sees
the real client. If the subnet and the setting drift apart, the header is silently ignored and
every client collapses to Caddy's address again, which is safe but makes the lockout a shared
global counter.

### 5.6 Outbound egress guard

Every provider URL field (`OPENAI_COMPATIBLE_LLM_URL`, `SELF_HOSTED_STT_URL`,
`SELF_HOSTED_TTS_URL`, `EMBEDDING_API_URL`, `AZURE_OPENAI_ENDPOINT`, `AUDIO_S3_ENDPOINT_URL`) is
validated when written and re-validated immediately before each outbound call. Rejected: loopback,
link-local including the cloud metadata address, multicast, reserved ranges, the Compose service
names, embedded credentials, unresolvable hosts, and plain `http` to any private address not in
`EGRESS_ALLOWED_PRIVATE_HOSTS`. Changing a URL through the dashboard requires the
`confirm_endpoint_change` flag and is logged with old and new values.

### 5.7 Secrets at rest

| Store | What | Protection |
|---|---|---|
| `.env` on the host | All secrets in clear | File mode 600, root only. Also visible in `docker inspect backend` and `docker compose config` because Compose passes it as environment |
| Redis `oasis:settings:api_keys` | Dashboard-set provider keys and S3 credentials | Fernet, key HKDF-derived from `SECRET_KEY`. URL fields are stored in clear because they are destinations, not secrets |
| Redis process | `REDIS_PASSWORD` | On the `redis-server` command line and healthcheck, so readable via `docker top` or `docker inspect redis` (open item, see section 12) |
| Postgres | Application data, transcripts, embeddings | Role password only. No TLS on the bridge network |
| Caddy volume | Let's Encrypt private keys | Docker volume `caddy_data`. Back it up with the rest, or accept re-issuance on restore |

## 6. Provider onboarding

Minimum viable: one OpenAI key gives text chat, voice (Whisper plus OpenAI TTS), voice-to-voice
(Realtime), and embeddings. Everything else is additive and selectable per agent.

| Provider | Where to get the credential | Set | Notes |
|---|---|---|---|
| OpenAI | platform.openai.com, API keys. Account needs credit or interviews fail with `insufficient_quota` | `OPENAI_API_KEY` | `OPENAI_USE_EU=true` routes through `eu.api.openai.com`; requires an OpenAI project with data residency enabled |
| Anthropic | console.anthropic.com | `ANTHROPIC_API_KEY` | Text models only |
| Google | Google AI Studio | `GOOGLE_API_KEY` | Gemini text and Gemini Live voice-to-voice |
| Deepgram | console.deepgram.com | `DEEPGRAM_API_KEY` | STT |
| ElevenLabs | elevenlabs.io profile | `ELEVENLABS_API_KEY` | TTS |
| Cartesia | play.cartesia.ai | `CARTESIA_API_KEY` | TTS, shown in the agent form only when configured |
| Scaleway | Scaleway console, IAM API key with the Generative APIs permission | `SCALEWAY_SECRET_KEY`, `SCALEWAY_PROJECT_ID` | EU-hosted. `SCALEWAY_API_URL` defaults to `https://api.scaleway.ai/v1` |
| OpenRouter, Groq, Mistral, Together, DeepInfra, LiteLLM proxy, vLLM, Ollama | Provider's console, or none for local servers | `OPENAI_COMPATIBLE_LLM_URL` and `OPENAI_COMPATIBLE_LLM_API_KEY` | Use the base URLs listed in `.env.example`. Agent model name must start with `custom/`. A local server on plain `http` needs its host in `EGRESS_ALLOWED_PRIVATE_HOSTS` |
| Self-hosted STT and TTS | Your own Speaches, Kokoro, Piper, LocalAI | `SELF_HOSTED_*` | Choose "Custom / Self-Hosted" in the agent form. Same egress rule for plain `http` |
| Embeddings server | Your own OpenAI-compatible embedding endpoint | `EMBEDDING_*` | Must output 1536-dimensional vectors or the schema needs a migration |

Two ways to apply a new key:

- **`.env` then `docker compose up -d`.** Recreates only containers whose environment changed. Data is preserved.
- **Dashboard, Settings page.** Stored encrypted in Redis, takes effect immediately, overrides `.env`. Keys are shown masked to the last four characters. Clearing a dashboard value falls back to `.env`.

Verify a provider from the dashboard's provider status, or with `scripts/verify_providers.py`
against a running stack.

## 7. Telephony (Twilio) setup

Prerequisites: a real `DOMAIN` with a valid public certificate, and the stack reachable on 443.
Twilio will not deliver webhooks to `localhost`. An sslip.io name is fine.

1. In the Twilio console, note the **Account SID** and **Auth Token**, and buy or pick a voice-capable phone number.
2. Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` and `TWILIO_PHONE_NUMBER` in `.env` or the dashboard, and `docker compose up -d`.
3. In the number's Voice configuration, set the incoming call webhook to `POST https://<DOMAIN>/api/twilio/voice/<agent_id>`, where `agent_id` is the agent you want to answer calls. Do not add query parameters: the signature check reconstructs the URL from `DOMAIN` and the path only.
4. Place a test call.

What happens on each call, and what can reject it:

| Step | Control | Failure |
|---|---|---|
| Webhook arrives | Per-IP rate limit, 60 per minute | 429 |
| Signature | `X-Twilio-Signature` validated with `TWILIO_AUTH_TOKEN` over `https://<DOMAIN>/api/twilio/voice/<agent_id>` plus the POST body, **before any database access** | 403 if the header is missing, wrong, or the token is not configured. A wrong `DOMAIN` also fails here |
| TwiML response | Backend mints a 60-second HS256 stream ticket bound to `agent_id` and returns `<Stream url="wss://<DOMAIN>/ws/twilio/<agent_id>">` with the ticket as a `<Parameter>` | |
| Media stream connects | Per-IP cap of 30 new WebSocket connections per minute, checked before accept | Close |
| `start` frame | Ticket verified against the path `agent_id` before the agent is resolved or a session row is created | Close code 4401 |

Rotating `TWILIO_AUTH_TOKEN` in the Twilio console breaks signature validation until the new
value is set here. Rotating `SECRET_KEY` invalidates any ticket in flight, which only affects calls
in the first second of setup.

## 8. Post-setup verification

Run these after every fresh install, upgrade or secret rotation.

```bash
cd /opt/oasis
docker compose ps                     # all five services Up, postgres and redis healthy
docker compose logs backend | tail -50
```

Look for: no `SECRET_KEY` warnings, no "auth disabled" lines, `alembic upgrade head` completed,
and a log line stating the effective auth posture.

| Check | How | Expected |
|---|---|---|
| Health | `curl -s https://<DOMAIN>/api/health` | `ok` for both database and redis. This endpoint is unauthenticated and currently returns raw error text on failure (see section 12), so restrict it to your monitoring if you can |
| TLS | `curl -sI https://<DOMAIN>` | 200, `Strict-Transport-Security` present. For `localhost`, expect an internal-CA certificate warning in the browser |
| Auth posture | `curl -s https://<DOMAIN>/api/auth/status` | Reports auth enabled |
| Login | Dashboard login with `admin` and the recorded password | Success, then refresh the page: session persists |
| Lockout | Five wrong passwords | Sixth attempt returns 429 with `Retry-After`; correct password also refused until the window passes |
| Logout | Log out, then replay the old bearer token with `curl -H "Authorization: Bearer ..."` | 401 |
| Dashboard CSP | Open the browser console on the dashboard | No blocked-resource errors |
| Monitor | Open a session's detail page | Live transcript stream connects (ticket flow) |
| Widget | Open a share link standalone, then inside an `<iframe>` on another page | Loads in both, microphone prompt appears, a voice turn completes |
| Provider | Run one text interview and one voice interview | Transcript persists |
| Twilio, if enabled | Place a call | Answered, transcript appears. A 403 in the backend log means `DOMAIN` or the auth token is wrong |
| Proxy trust | `docker compose logs backend \| grep auth.login` | Lines show the real client IP, not `172.28.0.x` |

## 9. Rotation procedures

All rotations are `.env` edit then `docker compose up -d` unless noted. Take a backup first
(section 11).

| Secret | Procedure | Side effects |
|---|---|---|
| `SECRET_KEY` | Generate a new value, edit `.env`, `docker compose up -d backend` | Every admin session, monitor ticket and Twilio stream ticket is invalidated immediately. **Dashboard-set provider keys become undecryptable.** At this commit the decrypt path does not fail loudly, so after rotating, open Settings and re-enter or clear every dashboard-set key. Keys that live only in `.env` are unaffected |
| Admin password | Generate a new hash (section 3.5), replace `AUTH_PASSWORD_HASH`, `docker compose up -d backend` | Existing sessions stay valid until they expire or log out. Force them out by also rotating `SECRET_KEY` |
| `POSTGRES_PASSWORD` | Change the role password inside Postgres **first**, then `.env`, then restart the backend. Use the interactive `\password` prompt so the new value never appears on a command line or in the Postgres log: `docker compose exec postgres psql -U <POSTGRES_USER> -d <POSTGRES_DB>` then `\password <POSTGRES_USER>`. Then `sed -i "s\|^POSTGRES_PASSWORD=.*\|POSTGRES_PASSWORD=<new>\|" .env && docker compose up -d backend` | Brief backend downtime. The `postgres` container's `POSTGRES_PASSWORD` env only matters on first init of an empty volume |
| `REDIS_PASSWORD` | Edit `.env`, `docker compose up -d` (recreates both `redis` and `backend`, since both read it) | Redis restarts. Volume data persists. In-flight sessions drop |
| Provider API keys | Edit `.env` and `docker compose up -d backend`, or change in the dashboard | Dashboard value wins. Remember to update both places if you set both |
| `TWILIO_AUTH_TOKEN` | Rotate in Twilio console, set the new value here, `docker compose up -d backend` | Calls fail with 403 in the gap |
| Let's Encrypt certificate | Automatic. Caddy renews in the background | If `DOMAIN` changes, Caddy issues a new certificate on next request |
| `DOMAIN` | Update DNS first, edit `.env`, `docker compose up -d` (Caddy and backend both read it) | Twilio webhook URL must be updated in the Twilio console to match |

## 10. Upgrading a pre-hardening deployment

Deployments created before commit `9e8a109` (the security remediation) will not start after
`git pull` until the following are done. `scripts/update.sh` does not do any of this for you.

1. **Back up** (section 11).
2. Add to `.env`, copying the comments from `.env.example`:
   - `REDIS_PASSWORD=<openssl rand -hex 24>`
   - `TRUSTED_PROXY_IPS=172.28.0.0/24`
   - `EGRESS_ALLOWED_PRIVATE_HOSTS=` listing any self-hosted provider host you reach over plain `http`, otherwise empty
   - `AUTH_PASSWORD_HASH=` generated per section 3.5, then blank out `AUTH_PASSWORD`
   - `CORS_ALLOWED_ORIGINS=` (empty unless you have a separate front-end origin)
3. Check `SECRET_KEY` is 32+ characters and not the old placeholder. If it was the placeholder, rotate it and expect all sessions to drop.
4. Check `POSTGRES_PASSWORD` is not `change-me`. If it is, follow the rotation in section 9 **before** pulling, because the old backend can still talk to Postgres and the new one refuses to start until this is fixed.
5. Ensure `APP_ENV=production` and `AUTH_ENABLED=true`.
6. Ensure `DOMAIN` is set. Caddy now refuses to start without it, and serves TLS only.
7. The Compose network gained a fixed subnet. Docker cannot resize a live network, so run `docker compose down && docker compose up -d --build` rather than a plain `up`. Expect a short outage.
8. Run the section 8 checks. In particular confirm that any self-hosted provider still works after the egress allow-list change, and that admin sessions now expire after two hours.

Behaviour changes to tell your users about: admin sessions expire after 2 hours instead of 24,
logout is immediate, login locks after 5 failures, and browsers on a `localhost` deployment now
see a certificate warning.

## 11. Backups and what to protect

| Asset | Where | Backup | Sensitivity |
|---|---|---|---|
| `.env` | `/opt/oasis/.env` | Copy to an encrypted secret store. Never commit | Highest: every secret in clear |
| Postgres | volume `oasis_pgdata` | `bash scripts/update.sh --backup` before upgrades, or the cron in `DEPLOYMENT.md` (`pg_dump` gzip into `/opt/oasis/backups/`) | Participant transcripts and PII |
| Redis | volume `oasis_redisdata` | Not backed up by the scripts. Contents are regenerable except dashboard-set provider keys, which you can re-enter | Encrypted keys, live session state |
| Audio recordings | `./data/recordings` bind mount, or your S3 bucket | Include the directory in host backups, or rely on bucket versioning | Participant audio |
| Caddy state | volumes `oasis_caddy_data`, `oasis_caddy_config` | Optional. Losing it only triggers re-issuance | TLS private keys |
| Whole VM | Hetzner snapshot | Simplest full restore | Contains everything above including `.env` |

Restore of a `pg_dump` uses `psql` against the running `postgres` container with the
`POSTGRES_USER` and `POSTGRES_DB` from your `.env`.

## 12. Known gaps that affect operations

These are open items in the security assessment at Revision 5. They do not block deployment but
change what you should assume.

- **Redis and Postgres traffic is unencrypted** inside the Compose bridge network. Acceptable on a single host; do not stretch `oasis_net` across hosts.
- **`REDIS_PASSWORD` is visible on the Redis process command line** and in `docker compose config`. Restrict Docker socket access accordingly.
- **Admin JWT lives in browser `localStorage`** for up to 2 hours. An XSS in the dashboard would expose it. Keep the dashboard origin locked down and `CORS_ALLOWED_ORIGINS` empty.
- **Dashboard-set provider keys decrypt silently to garbage after a `SECRET_KEY` rotation** rather than failing. Follow the rotation note in section 9.
- **Some outbound provider calls still follow HTTP redirects** (LiteLLM custom LLM path, self-hosted STT and TTS via Pipecat). Only point those at endpoints you control.
- **The egress allow-list matches listed hostnames before their resolved address.** Prefer listing IPs or narrow CIDRs over names.
- **`TRUSTED_PROXY_IPS` trusts the whole Compose subnet**, so a compromised sibling container could spoof client IPs. Pin Caddy to a static address and narrow the setting if that matters to you.
- **`/api/health` is unauthenticated and returns raw dependency error text.** Restrict it at Caddy or in your firewall if you do not need it public.
- **The ephemeral development `SECRET_KEY` is per process.** Never run more than one uvicorn worker, or `--reload`, without a real key.
- **No refresh-token flow.** Admins re-authenticate every 2 hours. Plan operational sessions accordingly.
- **Five older `starlette` advisories remain** pending a `fastapi>=0.141` upgrade. Keep the stack behind Caddy's body-size cap and do not expose the backend port directly.
