# Security Assessment: OASIS Platform

**Revision: 1**
**Scope:** whole repository at `main` @ `3b32d4d` · **Baseline:** OWASP Top 10 (2025) · **Date:** 2026-09-17

> ## ⚠️ PHASE 1 OF 2 — Critical and High findings complete; Medium and Low findings pending Phase 2
>
> This revision is **not a complete security assessment**. It contains the Critical and High findings
> only, plus the coverage achieved so far. Medium and Low findings, and full reads of the remaining
> Tier-1 files listed as `Not reviewed` in the coverage table, are deferred to Phase 2. The verdict
> below is already determined by Phase 1 and **cannot improve** in Phase 2 — Phase 2 can only add
> findings. Do not cite Revision 1 as evidence of a clean review of any area marked `Not reviewed`.

---

## Verdict: **FAIL**

### Verdict rubric (fixed before findings were written)

| Condition | Verdict |
|---|---|
| One or more **Open Critical** findings | **FAIL** — unconditional |
| Zero Open Critical, one or more **Open High** findings | **FAIL** — unconditional |
| Zero Open Critical, zero Open High, any number of Medium/Low | **PASS** — Medium/Low recorded as recommendations |
| A finding dispositioned `False positive` or `Risk accepted` (named owner + date + reason) | Does not count as Open; a `Risk accepted` Critical/High is still escalated to the PM |

Severity is assigned from **impact only**. Exploitability and Confidence are recorded separately and
were never used to lower a severity. **Remediation Priority (P1/P2/P3)** is a derived scheduling
signal that does factor exploitability, reachability and confidence — it does not modify severity.

This assessment reaches FAIL on 2 Open Critical and 10 Open High findings.

---

## Summary

- Files in repository scope: **156** · Full coverage: **17** · Partial: **12** · Not reviewed (deferred to Phase 2): **127**
- **Critical: 2 · High: 10** · Medium: pending Phase 2 · Low: pending Phase 2
- Advanced Security alerts triaged: **0 — not pulled, MCP unavailable** (no `GITHUB_PAT` this session). No CodeQL, Dependabot or Secret Scanning input. See *Coverage limits*.
- Secrets scan: **no live secrets detected** in the files scanned. Placeholder and obviously-fake CI values only.
- `package-lock.json` exception: **not exercised** — no Phase 1 finding hinged on a resolved JS version.

### Coverage limits that affect confidence

1. **No CodeQL** — no taint tracking. Injection and SSRF findings rest on manual tracing.
2. **No Dependabot** — transitive dependency advisories unchecked. A03 coverage is partial; the `starlette` multipart-DoS advisory class noted under FINDING-009 is `Needs verification`.
3. **No secret scanning, no git-history scan** — a secret committed and later removed would be missed. Only the working tree was scanned.
4. **127 files not yet opened.** Most are Medium/Low tier, but several Tier-1 files (`realtime.py` partially, `session_manager.py`, `database.py`, five admin routers, `pipeline/*`, `providers/{catalog,availability,validate}.py`, most of the frontend) still require their full read in Phase 2.

---

## Coverage

| File | Risk | Coverage | Notes |
|---|---|---|---|
| `backend/app/config.py` | High | Full | 1-143 |
| `backend/app/auth.py` | High | Full | 1-81 |
| `backend/app/api/auth.py` | High | Full | 1-99 |
| `backend/app/api/router.py` | High | Full | 1-35 |
| `backend/app/main.py` | High | Full | 1-175 |
| `backend/app/api/twilio.py` | High | Full | 1-381 |
| `backend/app/api/monitor.py` | High | Full | 1-120 |
| `backend/app/redis.py` | High | Full | 1-32 |
| `backend/app/realtime.py` | High | Full | 1-66 |
| `docker-compose.yml` | High | Full | 1-97 |
| `docker/Caddyfile` | High | Full | 1-25 |
| `.github/workflows/ci.yml` | High | Full | 1-143 |
| `.github/workflows/weekly.yml` | High | Full | 1-196 |
| `.env.example` | High | Full | 1-129 |
| `.gitignore` | High | Full | 1-54 |
| `backend/Dockerfile` | High | Full | 1-17 |
| `backend/requirements.txt` | High | Full | 1-48 |
| `backend/app/api/settings.py` | High | Partial | 1-400 read; remainder (audio-storage writes, catalog, smoke-test route) pending |
| `backend/app/api/interviews.py` | High | Partial | 1-200 read (agent resolve, pid resolve, session create); pipeline run + finalise pending |
| `backend/app/api/knowledge.py` | High | Partial | 1-200 read (all upload paths); delete/search tail pending |
| `backend/app/api/sessions.py` | High | Partial | 380-540 read (export tail, audio manifest, audio download, engagement); 1-380 and 540+ pending |
| `backend/app/api/text_chat.py` | High | Partial | 1-200 read (RAG injection, model resolve); WS frame loop pending |
| `backend/app/audio/storage.py` | High | Partial | 1-200 read (sanitiser, local + S3 backends); factory tail pending |
| `backend/app/knowledge/embeddings.py` | High | Partial | 225-284 read — the only raw SQL in the tree. Grepped for `text(`, `execute(`, f-string SQL |
| `backend/app/models/agent.py` | Medium | Partial | Grepped `widget_key`, `_generate` — key entropy verified |
| `backend/app/providers/smoke.py` | High | Partial | Grepped `base_url`, `api_base`, `httpx.` — outbound target control assessed |
| `scripts/install.sh` | High | Partial | 150-269 read (secret generation, `.env` patch, Caddy rewrite); 1-150 pending |
| `frontend/src/lib/api.ts` | High | Partial | 1-80 read (token storage, auth header, 401 handling); API surface pending |
| `frontend/src/pages/InterviewPage.tsx` | High | Partial | `renderMarkdown` 47-114 read in full via grep context — XSS sink cleared |
| `frontend/src/pages/SessionDetailPage.tsx` | High | Partial | `renderMarkdown` 43-73 + sink at 684 read — XSS sink cleared |
| Repo-wide secret sweep | — | Full | `-----BEGIN`, `AKIA`, `ghp_`, `github_pat_`, `xox[abps]-`, `sk_live_`, `SG.`, `AC[0-9a-f]{32}`, JWT `eyJ…`, and `(password\|secret\|api_key\|token)=<literal>` — no matches |
| Repo-wide injection sweep | — | Full | `dangerouslySetInnerHTML`, `innerHTML`, `eval(`, `new Function`, `document.write`, `shell=True`, `os.system`, `subprocess`, `pickle.loads`, `yaml.load(` — 2 hits, both triaged |
| Repo-wide rate-limit sweep | — | Full | `limiter`, `slowapi`, `rate_limit`, `ratelimit` — **no matches anywhere** |
| Repo-wide Twilio-signature sweep | — | Full | `RequestValidator`, `X-Twilio-Signature`, `validate_signature` — no application code matches |
| `backend/app/api/{studies,agents,participants,templates,analytics}.py` | High | **Not reviewed** | Deferred to Phase 2 — IDOR / ancestor-chain revalidation unverified |
| `backend/app/{database,session_manager}.py` | High | **Not reviewed** | Deferred to Phase 2 |
| `backend/app/pipeline/*.py` (5) | Medium | **Not reviewed** | Deferred to Phase 2 — prompt assembly, transcript logging, LLM surface |
| `backend/app/engagement/*.py` (4) | Medium | **Not reviewed** | Deferred to Phase 2 |
| `backend/app/providers/{catalog,availability,validate}.py` | Medium | **Not reviewed** | Deferred to Phase 2 |
| `backend/app/schemas/*.py` (5), `backend/app/models/*.py` (6 remaining) | Medium | **Not reviewed** | Deferred to Phase 2 |
| `backend/alembic/env.py` + 17 revisions | Medium | **Not reviewed** | Deferred to Phase 2 |
| `frontend/src/**` (28 remaining files) | Medium | **Not reviewed** | Deferred to Phase 2 |
| `backend/tests/**` (30), `frontend/src/**/*.test.ts` (3) | Low | **Not reviewed** | Deferred to Phase 2 — covered by the repo-wide secret sweep only |
| `frontend/Dockerfile`, `frontend/package.json`, `scripts/update.sh`, `scripts/verify_providers.py`, `backend/{alembic.ini,pytest.ini}`, `docs/DEPLOYMENT.md` | Medium | **Not reviewed** | Deferred to Phase 2 |

---

## Design-Doc Traceability (R1–R9, C2–C5)

`docs/technical-design.md` and `docs/architecture.md` were treated as **claims to verify**, not as
established findings. Their severities were not inherited. Results below are re-derived from code.

| ID | Item | Result | Finding |
|---|---|---|---|
| R1 | Insecure defaults: `auth_enabled=False`, `debug=True`, placeholder `secret_key` | **Confirmed.** `config.py:20,21,126` and `.env.example:11,12,88`. Nothing refuses to start on the placeholder key. `install.sh:200-208` does set the safe posture, but per C2 a bypassing deploy path must be assumed | FINDING-001, FINDING-002 |
| R2 | CORS `*` + credentials when `debug` | **Confirmed.** `main.py:63-64`. Starlette reflects the request Origin when `allow_origins=["*"]` and `allow_credentials=True`, so this is a working cross-origin read, not a browser-blocked no-op | FINDING-004 |
| R3 | No session invalidation, stateless 24 h HS256 JWT | **Confirmed.** `auth.py:23-24,36`; no `jti`, denylist, refresh or `/logout`. Token in `localStorage` (`api.ts:14-26`) and in a query string (`monitor.py:37`) | FINDING-008 |
| R4 / **OQ1** | Twilio signature validation | **Confirmed absent.** Repo-wide sweep for `RequestValidator` / `X-Twilio-Signature` / `validate_signature` returns only `config.py:120` (the setting), `settings.py:74,126` (dashboard field) and `pipeline/runner.py:207,212` (passing the token to Pipecat). `POST /api/twilio/voice/{agent_id}` and `/ws/twilio/{agent_id}` are mounted at `main.py:78` with **no dependency**. **OQ1 is closed: no application-layer control exists.** An edge control (Caddy/WAF/Twilio console) would still have to be produced to change this | FINDING-003 |
| R5 | Single shared operator identity, no audit attribution | **Confirmed**, plus worse than described: the comparison at `api/auth.py:56` is a plaintext non-constant-time `!=`, the password is stored unhashed in `.env`, and the rate-limit sweep found **no limiter of any kind anywhere in the repository** | FINDING-005 |
| R6 | Pipelines co-located with the API loop, no backpressure | **Partially confirmed.** The 2 h ceiling (`interviews.py:36`, `twilio.py:41`) and per-subscriber Redis connection (`realtime.py:41-46`) are as described. No connection cap or per-`widget_key` limit exists. Availability-shaped; the concrete instance found is the unbounded upload read | FINDING-009 (instance); remainder Phase 2 |
| R7 | Provider keys in Redis, no `requirepass` | **Confirmed.** `docker-compose.yml:73-86` starts `redis:7-alpine` with no command, no auth, no TLS; `redis.py:19-22` connects via bare `redis://`; `settings.py:204` writes plaintext values to `oasis:settings:api_keys`. Masking at `settings.py:79-83` protects the read path only | FINDING-006 |
| R8 | Hard-coded provider/model catalog drift | **Not verified in Phase 1** — `providers/catalog.py` not yet read. Availability-shaped, deferred | Phase 2 |
| R9 | No retention or deletion policy | **Partially confirmed.** Recordings land on the host bind mount `./data/recordings` (`docker-compose.yml:48`); no TTL or purge found. Full verification needs `models/session.py` and the storage factory tail | Phase 2 (governance item C5 below) |
| **C2** | Deploy path bypassing `install.sh`? | **User answer: "Unknown, use the safe default."** R1 and R2 are therefore reported at code-derived severity (Critical / High) with the installer noted as a mitigating-but-not-guaranteed control | FINDING-001, -002, -004 |
| **C3** | Monitor JWT in query string vs access logs | **Confirmed exposure path.** `monitor.py:33-37` takes the JWT as `?token=`. `docker/Caddyfile` has no `log` directive, so Caddy's default access log is off — but any reverse proxy, CDN or `log` block added later captures a valid 24 h admin token in cleartext. Combined with R3 (no revocation), a logged token is usable until `exp` | FINDING-008 |
| **C4** | Should Redis require authentication? | **Recommendation issued** (FINDING-006). The decision to accept or remediate is the repository owner's, not mine | FINDING-006 |
| **C5** | Does a retention/erasure obligation apply to transcripts and recordings? | **Not answerable from code — I do not answer it.** This is a governance/legal determination about the studies being run, the participants' jurisdictions and any ethics approval in force. **Accountable owner: the repository owner / product owner.** Until answered, cascade-only deletion cannot be judged sufficient or insufficient | Phase 2 (R9) — blocked on owner decision |

### Surfaces explicitly checked and recorded (per amendment 4)

**(a) CI workflow permissions and expression injection.**
- `.github/workflows/ci.yml` — **no `permissions:` block** at workflow or job level. `GITHUB_TOKEN` therefore receives the repository's default scope, which on many repositories is read/write. No `pull_request_target`. No `${{ github.event.* }}` interpolation inside any `run:` step. `${{ github.ref }}` appears only in `concurrency.group` (line 17), which is not a shell context. All actions consumed by mutable major tag (`actions/checkout@v4`, `actions/setup-python@v5`, `actions/setup-node@v4`, `actions/upload-artifact@v4`), not by commit SHA. → FINDING-012.
- `.github/workflows/weekly.yml` — **no `permissions:` block**. Triggers are `schedule` and `workflow_dispatch` only — not attacker-reachable. `${{ github.event_name }}` is interpolated into a `run:` step at line 48, but its value is GitHub-controlled and cannot carry attacker input; **not an injection**. Same mutable-tag action pinning. A `pip-audit` and `npm audit` job does exist (lines 152-166) — correcting the technical-design claim that none exists — but both are `continue-on-error: true` with `|| echo`, so they cannot fail the run, and they execute at most once every three weeks. → FINDING-012.

**(b) Ingress validation for knowledge uploads and audio.**
- `POST /api/studies/{study_id}/knowledge/file` (`knowledge.py:107-161`) — **no content-type check, no declared byte cap, and the entire body is materialised with `await file.read()` at line 123 before any size test.** The 500,000-character cap at line 140 runs after the read and the decode. No archive handling exists (no zip/tar path), so archive-bomb expansion is not reachable; the exposure is raw size. → FINDING-009.
- `POST …/knowledge/text` (`:71-104`) — cap applied at line 85 against an already-parsed JSON body; same class, smaller blast radius, deferred to Phase 2.
- `GET …/sessions/{session_id}/audio/{filename}` (`sessions.py:454-485`) — path traversal guard at line 463 rejects `..`, `/` and `\` **before** the key is composed, and reads through the storage abstraction rather than the filesystem. **Adequate — no finding.**
- `audio/storage.py:18-37` — `sanitize_path_segment` replaces every character outside `[a-zA-Z0-9._-]` with `_`, so a participant-supplied `pid` cannot inject a path separator. It does **not** reject a literal `..`, which permits exactly one level of upward traversal within the storage root (`participants/../sessions/…`). Cannot escape the root because only one segment is user-controlled. Bounded impact → recorded, deferred to Phase 2 as a hardening item.
- Audio **write** path ingress (per-turn WAV capture) not yet read → Phase 2.

---

## Findings

### FINDING-001: Authentication is disabled by default, exposing the entire admin API unauthenticated

**Severity:** Critical
**Exploitability:** Likely
**Confidence:** Confirmed
**Remediation Priority:** **P1**
**Source:** Manual review
**File:** `backend/app/config.py`, `backend/app/auth.py`, `backend/app/api/router.py`, `.env.example`
**Line:** `config.py:126` · `auth.py:62-63` · `api/router.py:27-34` · `.env.example:88`
**Category:** A01 Broken Access Control / A02 Security Misconfiguration / A07 Authentication Failures

**Description.** `auth_enabled` defaults to `False` (`config.py:126`) and `.env.example:88` ships
`AUTH_ENABLED=false`. The guard dependency fails open:

```python
if not settings.auth_enabled:
    return None  # Auth disabled — allow all
```
(`auth.py:62-63`)

Because `require_auth` is applied at router-inclusion level (`api/router.py:27-34`), that single
branch disables authorization for **all eight admin routers at once** — studies, agents, sessions,
analytics, participants, knowledge, settings and templates. Three further consequences were
confirmed in code:

1. `POST /api/auth/login` issues a **valid signed JWT for any username and any password** when auth
   is disabled (`api/auth.py:45-48`), and `GET /api/auth/status` reports `authenticated: true`
   (`api/auth.py:76-81`). A client cannot distinguish "logged in" from "no security".
2. `GET /ws/monitor/{session_id}` skips its token check entirely when auth is off
   (`monitor.py:47`), streaming the **full verbatim transcript** of any session whose UUID is known
   or guessed — including live sessions in progress.
3. `PUT /api/settings/keys` becomes an unauthenticated write, which is the pivot described in
   FINDING-007.

**Impact.** Unauthenticated disclosure of all participant PII held by the platform: participant
identifiers, complete verbatim interview transcripts, per-turn engagement features, and — where
`store_audio` is on — voice recordings, which are biometric-adjacent personal data. Unauthenticated
write access to studies, agents, interview guides and provider credentials. Because the deployment
is intended to be internet-facing behind Caddy, this is remotely reachable by default. Per the C2
answer, a deployment configured without `scripts/install.sh` must be assumed to exist.

**Recommendation.**
1. Invert the default: `auth_enabled: bool = True` in `config.py`, and `AUTH_ENABLED=true` in `.env.example`.
2. Make the fail-open branch impossible in a non-development environment — in `main.py`'s lifespan, raise at startup if `settings.app_env != "development"` and `not settings.auth_enabled`. Fail closed, never fail open.
3. Delete the "issue a token for any credentials" branch at `api/auth.py:45-48`. When auth is disabled the endpoint should return `503`, not a valid token.
4. Apply the same guard to the participant and monitor planes: `monitor.py:47` should require a valid token unconditionally, not only when `auth_enabled` is true.
5. Add a startup log line that states the effective auth posture, so an operator can see it in `docker compose logs`.

**Standard Reference:** OWASP Top 10 (2025) A01, A02, A07. No user-named standard applied.
**Disposition:** **Open**

---

### FINDING-002: Published placeholder `SECRET_KEY` is accepted at runtime, allowing admin JWT forgery

**Severity:** Critical
**Exploitability:** Likely
**Confidence:** Confirmed
**Remediation Priority:** **P1**
**Source:** Manual review
**File:** `backend/app/config.py`, `backend/app/auth.py`, `.env.example`
**Line:** `config.py:20` · `auth.py:36,42-44` · `.env.example:11`
**Category:** A02 Security Misconfiguration / A04 Cryptographic Failures / A07 Authentication Failures

**Description.** `secret_key` defaults to the literal string `change-me-to-a-random-secret-key`
(`config.py:20`), and the same value is published in `.env.example:11`. That value is the **sole**
input to JWT signing and verification (`auth.py:36`, `auth.py:42-44`), with algorithm `HS256` — a
symmetric scheme where the verification key *is* the signing key. Nothing in the application
validates the key's strength, entropy or difference from the shipped placeholder. An operator who
runs `cp .env.example .env` — the exact instruction printed at `.env.example:4-5` — deploys with a
signing key that is public in this repository.

Critically, this defeats the remediation for FINDING-001: even with `AUTH_ENABLED=true`, anyone can
mint `{"sub": "admin", "iat": …, "exp": …}`, sign it with the published key, and pass `require_auth`
on every protected router.

**Impact.** Complete authentication bypass of the admin API and the monitor WebSocket, independent
of whether authentication is enabled. Full read and write access to participant PII, transcripts,
recordings and provider credentials. Forged tokens are indistinguishable from genuine ones in the
logs, and because there is no `jti` or denylist (FINDING-008) they cannot be revoked short of
rotating the key and restarting.

**Recommendation.**
1. Refuse to start on a weak key. In `config.py`, add a `model_validator` that raises when `app_env != "development"` and `secret_key` is empty, equal to the placeholder, or shorter than 32 characters.
2. Remove the placeholder value from `.env.example:11` — leave `SECRET_KEY=` empty so a copy-paste deploy fails loudly rather than silently insecure.
3. Separate concerns: use a dedicated `JWT_SIGNING_KEY` rather than reusing the general application secret, so the two can be rotated independently.
4. Consider asymmetric signing (RS256/EdDSA) so that any future verification-only component never holds the signing key.
5. `scripts/install.sh:195` already generates a strong key with `openssl rand -hex 32`; keep it, but do not rely on it as the only control.

**Standard Reference:** OWASP Top 10 (2025) A02, A04, A07.
**Disposition:** **Open**

---

### FINDING-003: Twilio voice webhook and media-stream WebSocket accept unauthenticated requests (R4 / OQ1 closed)

**Severity:** High
**Exploitability:** Likely
**Confidence:** Confirmed
**Remediation Priority:** **P1**
**Source:** Manual review
**File:** `backend/app/api/twilio.py`, `backend/app/main.py`
**Line:** `twilio.py:110-164` (webhook) · `twilio.py:167-298` (WebSocket) · `main.py:78` (mount)
**Category:** A08 Software or Data Integrity Failures / A01 Broken Access Control

**Description.** `app.include_router(twilio_router)` at `main.py:78` mounts both Twilio endpoints
with **no `dependencies=[Depends(require_auth)]`** and outside the `/api` router that carries the
auth dependency. A repository-wide sweep for `RequestValidator`, `X-Twilio-Signature` and
`validate_signature` found no application code performing signature verification — only the
`twilio_auth_token` *setting* (`config.py:120`), its dashboard field (`settings.py:74,126`) and its
hand-off to Pipecat (`pipeline/runner.py:207,212`). **This closes OQ1: no application-layer Twilio
signature validation exists.**

Two consequences follow. First, `POST /api/twilio/voice/{agent_id}` can be called by anyone. It
accepts an attacker-supplied `To` form field which drives agent selection
(`twilio.py:121-122,60-86`) — so the caller, not Twilio, chooses which agent answers. Second, the
returned `<Stream url>` is built from the **inbound `Host` header** (`twilio.py:145-147`):

```python
host = request.headers.get("host", "localhost")
ws_url = f"{scheme}://{host}/ws/twilio/{resolved_agent_id}"
```

A forged `Host` therefore redirects the media stream to an attacker-chosen destination in the TwiML
response.

Third, `/ws/twilio/{agent_id}` performs `websocket.accept()` before any check (`twilio.py:180`) and
authenticates the peer **only** by whether it sends a Twilio-shaped `start` frame
(`twilio.py:198-207`). Any WebSocket client that emits `{"event":"start","start":{"streamSid":…}}`
gets a live Session row created (`twilio.py:284-291`) and a full LLM/STT/TTS pipeline booted
(`twilio.py:309-330`) for up to 7,200 seconds.

**Impact.** (a) **Research data integrity** — an attacker can create arbitrary Session rows with
`participant_id = "twilio:<attacker-chosen callSid>"` and drive fabricated transcript content into
studies, corrupting research records with no way to distinguish forged from genuine sessions.
(b) **Cost** — unauthenticated, unrate-limited access to paid LLM, STT and TTS providers for 2-hour
sessions using the operator's API keys. (c) **Availability** — each accepted stream pins a pipeline
to the shared API event loop (R6). (d) **Information disclosure** — the TwiML response confirms
agent existence and leaks the internal WebSocket path.

**Recommendation.**
1. Validate the Twilio signature on the webhook. `twilio>=9.0.0` is already a dependency (`requirements.txt:29`): compute `RequestValidator(settings.twilio_auth_token).validate(url, form_dict, request.headers["X-Twilio-Signature"])` and return `403` on mismatch. Fail closed when `twilio_auth_token` is unset.
2. Build the `<Stream url>` from a configured, trusted base URL (the `DOMAIN` value already in `.env`), never from the inbound `Host` header. If `Host` must be used, validate it against an allow-list.
3. Authenticate the media-stream WebSocket. Mint a short-lived, single-use signed token in the webhook, pass it as a `<Parameter>`, and verify it in the `start` frame before creating the Session or booting the pipeline. Reject with a `40xx` close code before `accept()` where possible.
4. Reject the attacker-controlled `To` routing path unless the request signature has already been verified in step 1.
5. Add a per-source connection cap and rate limit on `/ws/twilio/*` — no limiter of any kind currently exists anywhere in the repository (see FINDING-005).

**Standard Reference:** OWASP Top 10 (2025) A08, A01.
**Disposition:** **Open**

---

### FINDING-004: CORS reflects any origin with credentials enabled whenever `debug` is true (the default)

**Severity:** High
**Exploitability:** Likely
**Confidence:** Confirmed
**Remediation Priority:** **P1**
**Source:** Manual review
**File:** `backend/app/main.py`, `backend/app/config.py`, `.env.example`
**Line:** `main.py:61-67` · `config.py:21` · `.env.example:12`
**Category:** A02 Security Misconfiguration / A01 Broken Access Control

**Description.** `debug` defaults to `True` (`config.py:21`) and `.env.example:12` ships
`DEBUG=true`. With that default:

```python
allow_origins=["*"] if settings.debug else [],
allow_credentials=True,
allow_methods=["*"], allow_headers=["*"],
```
(`main.py:63-66`)

This is not the browser-blocked `*`-with-credentials no-op it resembles. Starlette's
`CORSMiddleware` detects the `allow_all_origins` + `allow_credentials` combination and **reflects
the requesting Origin** into `Access-Control-Allow-Origin` with
`Access-Control-Allow-Credentials: true`, so cross-origin reads succeed from any site. Combined with
FINDING-001, any web page a researcher visits can script the OASIS admin API and read the responses.

Note the non-debug branch is `[]`, not a configured allow-list — there is no supported way to permit
a legitimate cross-origin front end, which encourages operators to leave `DEBUG=true`.

**Impact.** Drive-by cross-origin exfiltration of participant transcripts, PII and study
configuration from any browser that can reach the deployment — including internal deployments
reachable only from a researcher's network, which the browser can reach on the attacker's behalf.
Cross-origin writes (`allow_methods=["*"]`) permit study and agent tampering, and provider-key writes
per FINDING-007.

**Recommendation.**
1. Decouple CORS from `debug`. Add an explicit `cors_allowed_origins: list[str] = []` setting and pass it to the middleware.
2. Never combine `allow_credentials=True` with a wildcard or reflected origin. If no origins are configured, send no CORS headers at all.
3. Constrain `allow_methods` and `allow_headers` to what the SPA actually uses.
4. Default `debug` to `False` in `config.py:21` and `.env.example:12`; `DEBUG` should be opt-in for local development only.

**Standard Reference:** OWASP Top 10 (2025) A02, A01.
**Disposition:** **Open**

---

### FINDING-005: Plaintext, non-constant-time credential comparison with no rate limiting, lockout or login audit

**Severity:** High
**Exploitability:** Likely
**Confidence:** Confirmed
**Remediation Priority:** **P1**
**Source:** Manual review
**File:** `backend/app/api/auth.py`, `backend/app/config.py`
**Line:** `api/auth.py:56` · `config.py:127-128`
**Category:** A07 Authentication Failures / A04 Cryptographic Failures

**Description.** The single operator credential is stored **unhashed** in configuration
(`config.py:128`, `auth_password: str = ""`) and compared with a plain Python `!=`:

```python
if data.username != settings.auth_username or data.password != settings.auth_password:
```
(`api/auth.py:56`)

Three defects compound here:

1. **No hashing at rest.** Anyone who reads `.env`, inspects the container environment
   (`docker inspect`, `/proc/<pid>/environ`), or obtains a backup recovers the live admin password
   in cleartext. `docker-compose.yml:40-41` injects the whole file via `env_file`.
2. **Non-constant-time comparison.** Python's `!=` on `str` short-circuits at the first differing
   byte, leaking a timing oracle. Over a network this is noisy but the endpoint is unthrottled,
   so an attacker can average across unlimited samples.
3. **No throttling of any kind.** A repository-wide sweep for `limiter`, `slowapi`, `rate_limit` and
   `ratelimit` returned **no matches anywhere in the codebase**. There is no attempt counter, no
   lockout, no backoff, no CAPTCHA and no log line on authentication failure — so brute force is
   both unlimited and invisible. There is nothing to alert on (A09).

Because there is exactly one identity (R5), compromising it grants total control; there is no second
factor and no per-user blast-radius limit.

**Recommendation.**
1. Store a hash, not the password. Add `AUTH_PASSWORD_HASH` using Argon2id (or bcrypt) and verify with the library's own verifier; keep plaintext `AUTH_PASSWORD` only as a deprecated migration path that logs a warning.
2. Until hashing lands, at minimum replace the comparison with `hmac.compare_digest(...)` for both username and password.
3. Add rate limiting on `POST /api/auth/login` — e.g. `slowapi` or a Redis counter keyed on client IP and username, with exponential backoff and a temporary lockout. Redis is already a dependency.
4. Log every authentication attempt with outcome, source IP and timestamp, and emit a countable event on repeated failure so an alert can be attached (closes the A09 gap on this path).
5. Document and support a second factor, or restrict the admin surface to a trusted network, given the single-identity design.

**Standard Reference:** OWASP Top 10 (2025) A07, A04, A09.
**Disposition:** **Open**

---

### FINDING-006: Redis runs without authentication or TLS while holding ~28 provider credentials in plaintext

**Severity:** High
**Exploitability:** Possible
**Confidence:** Confirmed
**Remediation Priority:** **P2**
**Source:** Manual review
**File:** `docker-compose.yml`, `backend/app/redis.py`, `backend/app/api/settings.py`
**Line:** `docker-compose.yml:72-86` · `redis.py:19-22` · `settings.py:28,186-208`
**Category:** A04 Cryptographic Failures / A02 Security Misconfiguration

**Description.** The Redis service is declared with no `command:`, no `requirepass`, no ACL file and
no TLS (`docker-compose.yml:72-86`), and the client connects with a bare
`redis://redis:6379/0` URL (`redis.py:19-22`, `config.py:46`). Into that unauthenticated store,
`PUT /api/settings/keys` writes provider credentials **in plaintext**:

```python
await redis.hset(_REDIS_KEY, field, value)
```
(`settings.py:204`, key `oasis:settings:api_keys`, `settings.py:28`)

The `_API_KEY_FIELDS` map at `settings.py:47-76` covers 28 fields, including
`openai_api_key`, `anthropic_api_key`, `google_api_key`, `deepgram_api_key`, `elevenlabs_api_key`,
`cartesia_api_key`, `azure_openai_api_key`, `gcp_api_key`, `scaleway_secret_key`,
`twilio_account_sid` and `twilio_auth_token` — plus `audio_s3_access_key_id` and
`audio_s3_secret_access_key` in the parallel `oasis:settings:audio_storage` hash
(`settings.py:295-306`). The masking at `settings.py:79-83` protects only the API read path; the
**stored** values are cleartext.

The only boundary is the `oasis_net` bridge network. Any container joined to that network, any
process that can reach the Docker socket, and anyone with host shell access (`docker exec -it
oasis-redis-1 redis-cli hgetall oasis:settings:api_keys`) reads every credential. The data is
persisted to the `redisdata` volume, so it also survives into backups and snapshots. Writes are
unaudited beyond a field-name log line (`settings.py:205`).

**Impact.** Disclosure of all configured AI-provider and cloud-storage credentials, enabling
fraudulent spend on the operator's accounts, access to the S3 bucket holding voice recordings, and —
via the Twilio credentials — control of the operator's telephony. Redis also carries the session
leases and the transcript pub/sub channels (`realtime.py:20,28`), so an unauthenticated peer on the
network can additionally subscribe to `oasis:transcript:*` and read live interview transcripts, or
publish forged transcript events into a researcher's monitor view.

**Recommendation.**
1. Set a strong `requirepass` (or Redis 6+ ACL user) via `command: redis-server --requirepass ${REDIS_PASSWORD}` in `docker-compose.yml`, generate `REDIS_PASSWORD` in `scripts/install.sh` alongside `POSTGRES_PASSWORD`, and carry it in `REDIS_URL`.
2. Encrypt credential values before `hset` — e.g. envelope-encrypt with a key derived from `SECRET_KEY` — so a Redis read does not yield usable secrets.
3. Prefer not storing provider credentials in Redis at all: treat `.env` (mode 600, as `install.sh:211` already sets) or an external secret manager as the source of truth, and make the dashboard write-through to that instead.
4. Enable `rename-command`/ACL restrictions on `CONFIG`, `KEYS` and `FLUSHALL`, and disable RDB persistence for the settings hash if it need not survive restart.
5. Add an audit log entry (actor, field, timestamp) on every credential write and clear.

**Standard Reference:** OWASP Top 10 (2025) A04, A02.
**Disposition:** **Open**

---

### FINDING-007: Provider endpoint URLs are operator-writable, allowing transcript exfiltration and SSRF

**Severity:** High
**Exploitability:** Possible
**Confidence:** Confirmed
**Remediation Priority:** **P2**
**Source:** Manual review
**File:** `backend/app/api/settings.py`, `backend/app/providers/smoke.py`, `backend/app/api/text_chat.py`
**Line:** `settings.py:54,59,64,67,70,106,116,119,122` (URL fields) · `settings.py:186-208` (write) · `smoke.py:170-175,274-280,359-362` · `text_chat.py:174-200`
**Category:** A01 Broken Access Control (SSRF) / A08 Software or Data Integrity Failures

**Description.** `_API_KEY_FIELDS` mixes secrets with **endpoint URLs**:
`openai_compatible_llm_url`, `azure_openai_endpoint`, `self_hosted_stt_url`, `self_hosted_tts_url`
and `embedding_api_url`. `PUT /api/settings/keys` accepts and persists any string for these
(`settings.py:186-208`) with **no scheme, host or allow-list validation**. The values are then used
directly as request destinations — `smoke.py:170-175` passes `base_url` into the LLM client,
`smoke.py:274-280` and `smoke.py:359-362` compose STT/TTS endpoints via
`_openai_compatible_endpoint()` (`smoke.py:109-110`) and call them with `httpx.AsyncClient`, and
`text_chat.py:183-186` sets `base_url` on the OpenAI client for the live chat loop.

Two attack shapes follow:

1. **Egress redirection / data exfiltration.** Repointing `self_hosted_stt_url` or
   `openai_compatible_llm_url` at an attacker-controlled host silently redirects **participant audio
   and full conversation content** to that host for every subsequent interview. The configured API
   key travels with it. The change is invisible in the UI, because the dashboard displays URL fields
   unmasked but gives no warning and no audit trail (`settings.py:205` logs only the field name).
2. **Server-side request forgery.** `POST /api/settings/smoke-test` makes the backend issue requests
   to the supplied URL. Internal addresses (`http://169.254.169.254/…`, `http://postgres:5432`,
   `http://redis:6379`, other `oasis_net` services) are reachable, and the smoke-test response
   surfaces the outcome back to the caller.

The endpoints sit behind `require_auth` (`api/router.py:33`) — but that dependency fails open under
FINDING-001, and is bypassable under FINDING-002, so in the default posture this is
**unauthenticated**.

**Impact.** Ongoing covert interception of every interview's audio and transcript — the platform's
most sensitive data — with no user-visible indicator. Leakage of the provider API key to the
attacker's endpoint. Internal network reconnaissance and cloud metadata access from the backend's
network position.

**Recommendation.**
1. Separate URL settings from credential settings, and validate every URL on write: require `https` (allow `http` only for RFC1918 destinations the operator explicitly opts into), reject credentials embedded in the URL, and resolve-and-check the host against a deny-list of link-local, loopback and internal ranges.
2. Apply the same resolve-time check immediately before each outbound request in `smoke.py` and `text_chat.py`, not only at write time, to defeat DNS rebinding.
3. Require a distinct, explicitly-confirmed action to change an egress endpoint, and write an audit record (actor, old value, new value, timestamp).
4. Surface the effective provider endpoints prominently in the dashboard and in the session detail view, so a redirected pipeline is visible to the researcher.
5. Set an egress allow-list at the network layer for the `backend` service where the deployment permits it.

**Standard Reference:** OWASP Top 10 (2025) A01 (SSRF merged), A08.
**Disposition:** **Open**

---

### FINDING-008: No session invalidation; long-lived JWT held in `localStorage` and transmitted in a query string

**Severity:** High
**Exploitability:** Possible
**Confidence:** Confirmed
**Remediation Priority:** **P2**
**Source:** Manual review
**File:** `backend/app/auth.py`, `backend/app/api/monitor.py`, `frontend/src/lib/api.ts`
**Line:** `auth.py:23-24,29-36,39-49` · `monitor.py:33-37` · `api.ts:14-26,49-56`
**Category:** A07 Authentication Failures / A04 Cryptographic Failures

**Description.** Tokens are stateless HS256 JWTs carrying only `sub`, `iat` and `exp`, with a fixed
24-hour lifetime (`auth.py:23-24,31-35`). Verification checks the signature and `exp` and nothing
else (`auth.py:42-44`). There is **no `jti`, no denylist, no refresh, no rotation and no server-side
`/logout`** — sign-out is a client-side `localStorage.removeItem` (`api.ts:24-26`). The only
revocation mechanism is rotating `SECRET_KEY` and restarting, which invalidates every token at once.

Two storage and transport choices widen the window:

1. **`localStorage`** (`api.ts:14-22`) is readable by any script executing in the origin, and unlike
   an `HttpOnly` cookie it survives no XSS mitigation. The two `dangerouslySetInnerHTML` sinks were
   examined and cleared (see *Threat Assessment*), but the storage choice means any future sink is
   an immediate full-account compromise.
2. **Query-string transmission.** `GET /ws/monitor/{session_id}?token=<jwt>` (`monitor.py:33-37`)
   places a live admin credential in a URL. `docker/Caddyfile` currently defines no `log` directive
   so Caddy's access log is off by default — but URLs are the single most commonly logged, cached
   and forwarded field in any proxy, CDN, WAF or browser history. This is confirmation item **C3**:
   the exposure path is real, and because tokens cannot be revoked, a token captured in a log line
   remains valid for up to 24 hours.

**Impact.** A token leaked by any means — proxy log, shared browser profile, backup, shoulder-surfed
URL, or a future XSS — grants full admin access for up to 24 hours with no way to cut it off short of
a service restart that disconnects every legitimate user. There is no audit trail to establish what a
leaked token did, because exports and reads are unlogged.

**Recommendation.**
1. Add a `jti` claim and a Redis-backed denylist; implement `POST /api/auth/logout` that writes the `jti` to the denylist with a TTL matching `exp`, and check the denylist in `verify_token`.
2. Shorten the access-token lifetime substantially (15-60 minutes) and add a refresh token with rotation and reuse detection.
3. Move the token out of `localStorage` into an `HttpOnly`, `Secure`, `SameSite=Strict` cookie, with CSRF protection on state-changing requests.
4. For the monitor WebSocket, stop accepting `?token=`. Either use a `Sec-WebSocket-Protocol` subprotocol value to carry the bearer token, or issue a short-lived (30-60 s), single-use ticket from an authenticated REST call and exchange it on connect.
5. If a query-string token must remain during migration, explicitly configure the reverse proxy to strip or redact the `token` parameter from access logs, and document that requirement in `docs/DEPLOYMENT.md`.

**Standard Reference:** OWASP Top 10 (2025) A07, A04.
**Disposition:** **Open**

---

### FINDING-009: Knowledge file upload reads the entire request body into memory before any size check

**Severity:** High
**Exploitability:** Likely
**Confidence:** Confirmed
**Remediation Priority:** **P1**
**Source:** Manual review
**File:** `backend/app/api/knowledge.py`
**Line:** `knowledge.py:107-144` (read at 123, cap at 140)
**Category:** A10 Mishandling of Exceptional Conditions / A06 Insecure Design

**Description.** `POST /api/studies/{study_id}/knowledge/file` accepts an `UploadFile` and
immediately materialises it whole:

```python
content_bytes = await file.read()          # line 123 — no size bound
...
content = content_bytes.decode("utf-8")    # line 127 — second full copy
...
if len(content) > 500_000:                 # line 140 — cap enforced far too late
```

The 500,000-character limit is applied **after** the body has been read into memory *and* decoded
into a `str`, producing at least two full-size copies of an attacker-controlled payload. There is no
`Content-Length` pre-check, no streaming read with a running byte counter, no declared maximum upload
size, and no `content_type` validation — the docstring claims `.txt/.md/.csv` support but nothing
enforces it. `docker/Caddyfile` sets no `request_body max_size`, so the reverse proxy imposes no
bound either, and `docker-compose.yml` sets no memory limit on the `backend` service.

This matters more than a typical upload-DoS because of R6: the Pipecat interview pipelines run on
the **same process and event loop** as the API. Exhausting backend memory kills every live voice and
text interview in progress, and the sessions are only recovered by the reaper as `timed_out`.

The endpoint is behind `require_auth` (`api/router.py:32`) — which fails open under FINDING-001 and
is bypassable under FINDING-002, making it unauthenticated in the default posture.

**Impact.** Remote denial of service of the whole platform — API, admin dashboard and all in-flight
interviews — from a single large POST, with loss of any interview data not yet committed. Repeated
requests also fill the container's temporary storage via Starlette's spooled upload file.

**Recommendation.**
1. Enforce the limit before reading: reject on `Content-Length` above the cap, then stream with `await file.read(CHUNK)` in a loop, aborting with `413` as soon as the running total exceeds a declared `MAX_UPLOAD_BYTES`.
2. Express the cap in **bytes**, not characters, and validate `file.content_type` against an allow-list of text types; reject anything else with `415`.
3. Apply the same pattern to `POST …/knowledge/text` (`knowledge.py:82-89`), which caps only after the JSON body is fully parsed.
4. Add `request_body { max_size 10MB }` (or the operator's chosen value) to the `/api/*` handler in `docker/Caddyfile` as defence in depth.
5. Set `mem_limit`/`deploy.resources.limits` on the `backend` service in `docker-compose.yml` so one request cannot exhaust host memory.
6. **Related, unverified:** the Starlette version resolved by `fastapi==0.115.6` (`requirements.txt:2`) falls in a range that has carried multipart-parsing DoS advisories. Without Dependabot this could not be confirmed — treat as `Needs verification` and re-check once the MCP is available.

**Standard Reference:** OWASP Top 10 (2025) A10, A06.
**Disposition:** **Open**

---

### FINDING-010: Default deployment terminates plain HTTP with no TLS and no security headers

**Severity:** High
**Exploitability:** Possible
**Confidence:** Confirmed
**Remediation Priority:** **P1**
**Source:** Manual review
**File:** `docker/Caddyfile`, `docker-compose.yml`, `.env.example`
**Line:** `Caddyfile:1-24` · `docker-compose.yml:6-8` · `.env.example:70`
**Category:** A02 Security Misconfiguration / A04 Cryptographic Failures

**Description.** The shipped Caddyfile opens with a bare port site block:

```
:80 {
    handle /api/* { reverse_proxy backend:8000 }
    handle /ws/*  { reverse_proxy backend:8000 { transport http { keepalive 30s } } }
    handle        { reverse_proxy frontend:80 }
}
```

A `:80` site address means Caddy serves **plain HTTP and provisions no certificate**, while
`docker-compose.yml:6-8` publishes both `80:80` and `443:443` to the host. `.env.example:70` sets
`DOMAIN=localhost`, which keeps that default in place. `scripts/install.sh:226-231` rewrites the site
address to the chosen domain and `install.sh:217-220` warns when it is `localhost` — but per the C2
answer, a deploy that bypasses the installer must be assumed.

Independently of TLS, **no security headers are configured at all**: no `Strict-Transport-Security`,
no `Content-Security-Policy`, no `X-Content-Type-Options`, no `X-Frame-Options`/`frame-ancestors`, no
`Referrer-Policy`, no `Permissions-Policy`. This gap persists even on a correctly TLS-terminated
domain deployment. Absent `frame-ancestors`, the admin dashboard is framable and clickjackable;
absent CSP, the `localStorage` token (FINDING-008) has no second line of defence; absent
`Permissions-Policy`, the microphone permission surface of the interview widget is unconstrained.

**Impact.** On a `:80` deployment, admin credentials posted to `/api/auth/login`, the resulting JWT,
the monitor token in the URL, full interview transcripts and live participant audio all traverse the
network in cleartext and are trivially interceptable and modifiable. On any deployment, missing
headers leave clickjacking, MIME-sniffing and referrer-leakage unmitigated.

**Recommendation.**
1. Make the site address a required variable rather than a default: template the Caddyfile from `{$DOMAIN}` and fail the container start when it is unset, so a domain-less deploy does not silently fall back to plaintext.
2. If a `:80` block must remain for local development, keep it in a separate `Caddyfile.dev` that is not the default.
3. Add a global header block to every site:
   `Strict-Transport-Security "max-age=31536000; includeSubDomains"`, `X-Content-Type-Options nosniff`, `Referrer-Policy strict-origin-when-cross-origin`, `Permissions-Policy "microphone=(self)"`, and a `Content-Security-Policy` with `frame-ancestors 'none'` (or the widget's intended embedders), `default-src 'self'`, and explicit `connect-src` for the WebSocket origin.
4. Redirect HTTP to HTTPS rather than serving on it.
5. Document the header set and the TLS requirement in `docs/DEPLOYMENT.md`.

**Standard Reference:** OWASP Top 10 (2025) A02, A04.
**Disposition:** **Open**

---

### FINDING-011: PostgreSQL ships with the default password `change-me`, resolved silently at compose time

**Severity:** High
**Exploitability:** Possible
**Confidence:** Confirmed
**Remediation Priority:** **P2**
**Source:** Manual review
**File:** `docker-compose.yml`, `backend/app/config.py`, `.env.example`
**Line:** `docker-compose.yml:56-59` · `config.py:24-25,31-43` · `.env.example:15-16`
**Category:** A02 Security Misconfiguration / A07 Authentication Failures

**Description.** The database password has a hard-coded fallback in three places that agree with each
other, so nothing ever fails:

- `docker-compose.yml:58` — `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-change-me}`. The `:-` default
  means an absent or empty variable yields `change-me` **with no error and no warning**.
- `config.py:25` — `postgres_password: str = "change-me"`, the same value, so the backend connects
  successfully and the misconfiguration is invisible at runtime.
- `.env.example:16` — `POSTGRES_PASSWORD=change-me`, which a `cp .env.example .env` deploy inherits.

The credential is then interpolated into the connection URL at `config.py:33` and `config.py:41`.
`scripts/install.sh:196` does generate `openssl rand -hex 24` and patch it in — again, the installer
is the only thing standing between the default and production, and C2 says that cannot be assumed.

Postgres is not published to the host (`expose: 5432`, `docker-compose.yml:62-63`), so reachability
requires a position on `oasis_net` or the host — the same boundary as FINDING-006, and one that
FINDING-007's SSRF can probe from inside.

**Impact.** Anyone who reaches the database port with the guessable default reads and writes every
study, agent, session, verbatim transcript, engagement record and participant identifier in the
platform, and can alter or delete research data outright. The same static default also appears in the
persisted volume, so it governs backups and snapshots.

**Recommendation.**
1. Remove every default. Use `${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}` in `docker-compose.yml` so compose refuses to start without it, and drop the `"change-me"` default in `config.py:25`.
2. Replace the value in `.env.example:16` with an empty assignment and a comment telling the operator to generate one.
3. Rotate the password on any existing deployment that may have started with the default, and check `pg_stat_activity`/logs for unexpected connections.
4. Consider TLS for the backend↔Postgres hop (`sslmode=require`) so the credential and the transcript payloads are not in cleartext on the bridge network.
5. Apply the identical treatment to `REDIS_PASSWORD` once FINDING-006 is remediated.

**Standard Reference:** OWASP Top 10 (2025) A02, A07.
**Disposition:** **Open**

---

### FINDING-012: CI workflows grant default `GITHUB_TOKEN` permissions, pin actions by mutable tag, and cannot fail on vulnerable dependencies

**Severity:** High
**Exploitability:** Unlikely
**Confidence:** Confirmed
**Remediation Priority:** **P3**
**Source:** Manual review
**File:** `.github/workflows/ci.yml`, `.github/workflows/weekly.yml`
**Line:** `ci.yml:34-143` · `ci.yml:120-123` · `weekly.yml:37-196` · `weekly.yml:152-166`
**Category:** A03 Software Supply Chain Failures / A08 Software or Data Integrity Failures

**Description.** Four defects in the pipeline, all confirmed by full reads of both workflow files:

1. **No `permissions:` block** in either workflow, at workflow or job level. `GITHUB_TOKEN`
   therefore inherits the repository default, which on many repositories is read/write across
   contents, packages, issues and pull requests — far beyond what a test run needs.
2. **Actions consumed by mutable major tag**, never by commit SHA: `actions/checkout@v4`
   (`ci.yml:41,81,106,136`; `weekly.yml:70,110,140,176`), `actions/setup-python@v5`,
   `actions/setup-node@v4`, `actions/upload-artifact@v4`. A tag can be repointed by whoever controls
   the action repository; combined with defect 1, a repointed tag executes attacker code holding a
   write-capable token.
3. **The TypeScript gate cannot fail.** `npx tsc -b --noEmit 2>&1 || true` (`ci.yml:123`) discards
   the exit status, so type errors — including those that would catch unsafe changes — never block a
   merge.
4. **Dependency scanning cannot fail, and rarely runs.** `weekly.yml:152-166` does run `pip-audit`
   and `npm audit` — which corrects the technical-design claim that no dependency scanning exists —
   but each is written as `… || echo "…vulnerabilities found"` **and** carries
   `continue-on-error: true`, a double suppression. The job is additionally gated to roughly one run
   in three weeks (`weekly.yml:39-60`). There is no SAST, no container image scan, no secret
   scanning and no SBOM step in either workflow, and no Dependabot configuration anywhere in
   `.github/`.

**Explicitly checked and clear (amendment 4a):** neither workflow uses `pull_request_target`, and no
`${{ github.event.* }}` value flows into a `run:` step. `ci.yml:17` interpolates `github.ref` only
into `concurrency.group`, which is not a shell context. `weekly.yml:48` interpolates
`github.event_name` into a `run:` step, but that value is GitHub-controlled and cannot carry
attacker-supplied text. **No expression-injection vulnerability was found.** Both workflows use
obviously-fake placeholder keys as plain `env:` values (`ci.yml:27-32`, `weekly.yml:30-35`); no real
credential is present in the pipeline.

**Impact.** A compromise of any consumed action, or of a dependency installed by `pip install -r
requirements.txt` / `npm ci`, executes in a job holding a write-capable repository token — enabling
malicious commits, release tampering or exfiltration of any secret later added to the repository.
Independently, known-vulnerable dependencies can be merged and shipped without the pipeline ever
turning red.

**Recommendation.**
1. Add `permissions: contents: read` at the top of both workflows and grant additional scopes per job only where genuinely needed.
2. Pin every action to a full 40-character commit SHA with the version in a trailing comment, and adopt Dependabot (or Renovate) to bump those SHAs.
3. Remove `|| true` from `ci.yml:123` so the TypeScript check gates merges.
4. Promote dependency scanning into `ci.yml` on every push and pull request: remove `continue-on-error: true` and the `|| echo`, and let `pip-audit` / `npm audit --audit-level=high` fail the build. Keep the three-weekly deep run as an addition, not a substitute.
5. Enable GitHub Advanced Security — Dependabot alerts, CodeQL and secret scanning with push protection — which also closes the alert-triage gap recorded in this report's *Coverage limits*.
6. Add an SBOM generation step and container image scanning to the `docker-build` job.

**Standard Reference:** OWASP Top 10 (2025) A03, A08.
**Disposition:** **Open**

---

## Remediation Priority and Sequence

Severity reflects impact alone. **Remediation Priority** below is derived from exploitability,
reachability from the internet, and confidence — it is a scheduling aid, not a re-rating.

| Finding | Severity | Exploitability | Confidence | Priority |
|---|---|---|---|---|
| FINDING-001 Auth disabled by default | Critical | Likely | Confirmed | **P1** |
| FINDING-002 Placeholder `SECRET_KEY` accepted | Critical | Likely | Confirmed | **P1** |
| FINDING-003 Twilio endpoints unauthenticated | High | Likely | Confirmed | **P1** |
| FINDING-004 CORS reflects any origin with credentials | High | Likely | Confirmed | **P1** |
| FINDING-005 Plaintext credential compare, no throttling | High | Likely | Confirmed | **P1** |
| FINDING-009 Unbounded upload read | High | Likely | Confirmed | **P1** |
| FINDING-010 Plain HTTP default, no security headers | High | Possible | Confirmed | **P1** |
| FINDING-006 Redis unauthenticated, plaintext keys | High | Possible | Confirmed | **P2** |
| FINDING-007 Writable provider endpoint URLs | High | Possible | Confirmed | **P2** |
| FINDING-008 No session invalidation, token in URL | High | Possible | Confirmed | **P2** |
| FINDING-011 Postgres default password | High | Possible | Confirmed | **P2** |
| FINDING-012 CI permissions, tag pinning, non-blocking audits | High | Unlikely | Confirmed | **P3** |

### Ordered remediation sequence

1. **Close the front door first — FINDING-002, then FINDING-001.** Order matters: flipping
   `auth_enabled` to `True` achieves nothing while the published signing key still mints valid admin
   tokens. Refuse to start on the placeholder `SECRET_KEY`, *then* default auth on and remove the
   "token for any credentials" branch.
2. **FINDING-004 and FINDING-010 together** — both are single-file configuration changes
   (`main.py`, `docker/Caddyfile`) that shrink the remotely reachable surface immediately: stop
   reflecting arbitrary origins, stop serving admin traffic over plaintext, add the header set.
3. **FINDING-003** — add Twilio signature validation and a signed stream ticket. This is the only
   remaining wholly unauthenticated write path into research data once steps 1-2 land.
4. **FINDING-005 and FINDING-009** — hash the password, add `compare_digest` plus login rate
   limiting, and bound the upload read. Both are small, self-contained, and remove the two cheapest
   remaining attacks (brute force and single-request DoS).
5. **FINDING-011, then FINDING-006** — remove the compose defaults so the stack refuses to start
   without real credentials, then add `requirepass` and encrypt the stored provider keys. Doing
   FINDING-011 first establishes the "no silent defaults" pattern that FINDING-006 reuses.
6. **FINDING-007** — validate and audit egress URLs. Best done after step 1, since its primary risk
   is an *unauthenticated* write; afterwards it is an insider/compromised-token risk and can be
   solved properly rather than urgently.
7. **FINDING-008** — session invalidation, shorter lifetimes, cookie storage and a WebSocket ticket.
   The largest change in the set; schedule it as a deliberate piece of work rather than a hotfix.
8. **FINDING-012** — pipeline hardening and enabling Advanced Security. Independent of the
   application work and can proceed in parallel throughout; enabling the scanners early also
   improves the confidence of the Verify-Mode re-check.

---

## Secrets Scan

**No live secrets detected** in the files scanned.

| Category | Result |
|---|---|
| PEM private key blocks (`-----BEGIN …`), committed `.pem`/`.pfx`/`.p12`/`.key` | None |
| AWS (`AKIA…`), GitHub (`ghp_`, `github_pat_`), Slack (`xox…`), Stripe (`sk_live_`), SendGrid (`SG.`) | None |
| Twilio Account SID pattern (`AC` + 32 hex) | None |
| Live JWTs (`eyJ….….`) | None |
| Generic `password`/`secret`/`api_key`/`token` assigned a literal of 12+ chars | None |
| DB connection strings with an embedded password | None — `config.py:31-43` composes the URL from settings at runtime |
| Cloud account/tenant/subscription identifiers | None hardcoded; `gcp_project_id`, `scaleway_project_id`, `twilio_account_sid` are empty-by-default settings |
| PII (card numbers, SSN/NI, IBAN) in source, config or fixtures | None in the files scanned; `backend/tests/**` covered by the repo-wide sweep only, full read deferred to Phase 2 |

**Non-secret findings worth recording:**

- `.env.example` contains **placeholders only** — every credential field is an empty assignment. The two non-empty values, `SECRET_KEY=change-me-to-a-random-secret-key` (line 11) and `POSTGRES_PASSWORD=change-me` (line 16), are not leaked secrets but *insecure defaults*, reported as FINDING-002 and FINDING-011.
- Both workflows use obviously-fake CI values (`sk-test-fake-ci-key`, `ci-test-secret-key`, `POSTGRES_PASSWORD: test`). Not findings.
- `.gitignore` correctly excludes `.env`, `.env.local`, `.env.*.local` (lines 2-4), `data/recordings/` (line 47), `pgdata/` (line 44) and `dump.rdb` (line 50). It does **not** exclude `*.pem`, `*.key`, `*.pfx` or `*.p12` — no such files exist today, but adding the patterns is cheap insurance. Deferred to Phase 2 as a Low item.
- `scripts/install.sh:190` **prints a generated admin password to stdout** (`log "Generated admin password: $ADMIN_PASS"`). It lands in terminal scrollback and in any session transcript or CI log capturing the installer. `install.sh:179-180` correctly masks the OpenAI key instead. Deferred to Phase 2 as a Medium item.
- **Masking discipline:** no secret value, masked or otherwise, was placed in any URL, tool argument or this report.

---

## Threat Assessment

Assessed against `docs/architecture.md` and `docs/technical-design.md`, treated as claims to verify.

**Attack surface.** Caddy is the only container publishing ports (`docker-compose.yml:6-8`);
`frontend`, `backend`, `postgres` and `redis` use `expose` only and are confined to the `oasis_net`
bridge. That containment is as documented and is sound. Everything reachable through Caddy, however,
is broader than the design doc's four-zone table implies, because the "Admin REST" zone's enforcement
collapses to a single boolean (FINDING-001) and its signing key may be public (FINDING-002). The
genuinely unauthenticated-by-design surface — `/api/auth/*`, `/api/widget/{widget_key}`,
`/api/health`, `/api/docs`, `/api/openapi.json`, `/ws/interview/*`, `/ws/chat/*` — is joined by
`/api/twilio/voice/*` and `/ws/twilio/*` (FINDING-003), which the design doc flagged as unconfirmed
and which are now confirmed unauthenticated.

**Trust boundaries.** Four zones were re-derived from code rather than inherited:

| Zone | Credential | Verified enforcement | Verdict |
|---|---|---|---|
| Admin REST (8 routers) | JWT Bearer | `Depends(require_auth)` at `api/router.py:27-34` | Correct in shape; fails open on one flag |
| Public REST | none | by design | As documented. `/api/health` still returns raw exception strings (`main.py:162-171`) — Phase 2 |
| Participant WS | `widget_key` possession | Agent lookup + `status=active`; `predefined` mode also needs an unused `ParticipantIdentifier` (`interviews.py:139-163`) | Capability model is coherent. `widget_key` is `secrets.token_urlsafe(16)` — 128 bits, **verified adequate** (`models/agent.py:46-47,146-151`) |
| Twilio | none | agent/modality/config-gate only | **Broken** — FINDING-003 |
| Monitor WS | JWT via `?token=`, rejected before `accept()` | `monitor.py:47-56` | Correct ordering, but conditional on `auth_enabled` and the token travels in a URL — FINDING-008 |

The `websocket.accept()`-before-check pattern on the participant and Twilio planes
(`interviews.py:51`, `twilio.py:180`) is a design choice that costs a connection slot per rejected
peer. With no connection cap anywhere (rate-limit sweep: no matches), that is the R6 availability
concern; a concrete instance is FINDING-009.

**Data flow.** Participant PII — identifiers, verbatim transcripts, per-turn engagement features and
optional voice recordings — is unencrypted at rest in Postgres and on the `./data/recordings` host
bind mount (`docker-compose.yml:48`). Backend↔Postgres and backend↔Redis traffic is plaintext on the
bridge network. Transcript events transit the unauthenticated Redis pub/sub channel
`oasis:transcript:{session_id}` (`realtime.py:18-20,28`), which means an unauthenticated peer on
`oasis_net` can both **read live transcripts** and **publish forged transcript events** into a
researcher's monitor view — an integrity exposure the design doc did not name. Outbound provider
traffic is HTTPS/WSS, and `OPENAI_USE_EU` genuinely reroutes all OpenAI calls, but the destination is
operator-writable without validation (FINDING-007), so the egress boundary is only as trustworthy as
the settings write path.

**Cleared on inspection (no finding).** Three claimed controls were verified and hold:
- The pgvector similarity search (`knowledge/embeddings.py:247-265`) uses fully bound parameters with `CAST(:param AS …)`; **no SQL injection**. It is the only raw SQL in the application tree.
- The audio download traversal guard (`sessions.py:463`) rejects `..`, `/` and `\` before composing the storage key; **adequate**.
- Both `dangerouslySetInnerHTML` sinks (`InterviewPage.tsx:114`, `SessionDetailPage.tsx:684`) are fed by a hand-rolled `renderMarkdown` that HTML-escapes `&`, `<` and `>` **before** applying markdown transforms (`InterviewPage.tsx:49-52`, `SessionDetailPage.tsx:44-47`). The only attacker-controlled value reaching an HTML attribute is the link `href`, constrained to `https?://[^\s)]+` — the whitespace exclusion prevents breaking out into a new attribute, and pre-escaping prevents entity-based bypass. **No XSS found**, though a hand-rolled sanitiser guarding a stored-participant-content sink is fragile; hardening is a Phase 2 Low item.

**Prompt injection (inherent, named as the design doc requested).** Free-text participant speech and
retrieved knowledge-base chunks flow into LLM prompts by design — `text_chat.py:111-171` injects RAG
results as a user-role message with a natural-language instruction not to disclose the knowledge
base. A participant can instruct the model to ignore that framing, reveal the system prompt or the
interview guide, or steer the interview. This is inherent to a conversational-interview product
rather than a defect, but it is unmitigated: there is no delimiting, no output filtering and no
interaction guardrail. Full assessment of the pipeline prompt-assembly path is Phase 2.

---

## Phase 2 — what the next revision will contain

Phase 2 is **required** before this assessment can be considered complete. It will not change the
FAIL verdict; it can only add findings.

1. **Medium and Low findings in full**, including those already identified and held back in Phase 1:
   - `sanitize_path_segment` does not reject a literal `..` (`audio/storage.py:21-24,34`) — bounded one-level traversal within the storage root.
   - `/api/health` returns raw exception strings to unauthenticated callers (`main.py:162-171`).
   - Backend container runs as root with build toolchain (`gcc`, `libpq-dev`) retained in the runtime image, and base images pinned by tag not digest (`backend/Dockerfile:1-16`, `docker-compose.yml:4,54,74`).
   - Loose `>=` version constraints across `requirements.txt` (openai, litellm, boto3, twilio, PyJWT, deepgram-sdk, elevenlabs, google-genai, anthropic) with no hash pinning.
   - `scripts/install.sh:190` prints the generated admin password to stdout.
   - `.gitignore` lacks `*.pem`/`*.key`/`*.pfx`/`*.p12` patterns.
   - Unlogged data export and audio download (A09), and the absence of any authentication-failure logging or alerting hook.
   - Hand-rolled markdown sanitiser guarding a stored-content sink — recommend a vetted library.
2. **Full reads of the Tier-1 files still marked `Not reviewed`:** `database.py`, `session_manager.py`, the five unread admin routers (`studies`, `agents`, `participants`, `templates`, `analytics`) for IDOR and ancestor-chain revalidation, the remainder of `settings.py`, `interviews.py`, `knowledge.py`, `sessions.py`, `text_chat.py` and `audio/storage.py`, and `scripts/install.sh:1-150`.
3. **Targeted Tier-2 passes:** `schemas/*` field constraints, `models/*` cascade and PII columns, `pipeline/*` and `engagement/*` for prompt assembly and PII in logs, `providers/{catalog,availability,validate}.py`, all 17 Alembic revisions for raw `op.execute` and data-migration PII, the remaining 28 frontend files, and `backend/tests/**` for fixture secrets and PII.
4. **AI/LLM surface assessment in full** against the OWASP Top 10 for LLM Applications — prompt injection via participant speech and RAG content, model-output handling, agency limits, system-prompt leakage and interaction logging.
5. **R8 verification** (`providers/catalog.py` drift) and **R9 completion** (`models/session.py`, storage factory, deletion paths) — the latter partly blocked on the **C5** governance answer from the repository owner / product owner.
6. **Complete coverage table** with every one of the 156 in-scope files marked `Full`, `Partial` or `Not reviewed` with a reason.
7. **Re-triage of Advanced Security alerts** if `GITHUB_PAT` becomes available, which would upgrade several `Needs verification` dependency items to `Confirmed` and add git-history secret scanning.

---

## Verdict Rationale

**FAIL.** Twelve Open findings meet the FAIL threshold: 2 Critical and 10 High.

The two Critical findings compound rather than merely coexist. FINDING-001 means the default
deployment has no authentication at all; FINDING-002 means that turning authentication *on* does not
necessarily help, because the JWT signing key is published in this repository and is accepted at
runtime without complaint. Remediating either alone leaves a complete bypass in place. Six of the ten
High findings (003, 004, 006, 007, 009, 011) become materially worse, or become remotely
unauthenticated, in the presence of those two.

No severity was downgraded to move the verdict, and no risk was accepted on the user's behalf. The
C5 retention/erasure question remains explicitly unanswered and is owned by the repository owner /
product owner.

**Risk accepted (Critical/High):** none. No finding carries a `Risk accepted` disposition in this
revision.

---

## Awaiting Your Review

Please review the Phase 1 findings. This FAIL verdict means the code must return to the Developer for
remediation before proceeding to CI setup (Gate G7).

Two things to decide before remediation starts:

1. Confirm the **remediation sequence** above, in particular that FINDING-002 is fixed before or with
   FINDING-001 — fixing FINDING-001 alone provides no real protection.
2. **C5** — whether a retention or erasure obligation applies to transcripts and recordings. This is
   a governance determination for the repository owner / product owner. I have not answered it and
   will not; R9 cannot be closed until it is answered.

Say the word to continue with **Phase 2** (Medium and Low findings plus the remaining file reads), or
to re-run in **Verify Mode** once remediation lands. Re-running with `GITHUB_PAT` set would also let
me pull and triage CodeQL, Dependabot and Secret Scanning alerts, which Phase 1 could not.
