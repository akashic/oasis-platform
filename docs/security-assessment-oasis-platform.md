# Security Assessment: OASIS Platform

**Revision: 5**
**Scope:** whole repository at `main` @ `c8acfc3`, plus Verify-Mode re-check of the uncommitted remediation working tree · **Baseline:** OWASP Top 10 (2025) · **Date:** 2026-09-17

### Revision history

| Rev | Date | Mode | Change |
|---|---|---|---|
| 1 | 2026-09-17 | Execute (Phase 1 of 2) | Initial Critical + High findings, FINDING-001 … FINDING-012 |
| 2 | 2026-09-17 | **Verify** | Re-checked FINDING-001, FINDING-002, FINDING-003 against the Developer's remediation. Three dispositions changed to **Fixed**; two new findings raised from the remediated code (FINDING-013, FINDING-014). Phase 2 (Medium/Low full sweep) still outstanding. |
| 3 | 2026-09-17 | **Verify** | Re-checked FINDING-004 … FINDING-007. FINDING-004 → **Fixed**. FINDING-005, FINDING-006, FINDING-007 → **Open (partially fixed)** with scoped residuals. Five new findings raised from the remediation itself (FINDING-015, FINDING-016 Medium; FINDING-017, FINDING-018, FINDING-019 Low). Qualifiers updated on FINDING-003, FINDING-013, FINDING-014. Phase 2 still outstanding. |
| 5 | 2026-09-17 | **Verify** | Re-checked FINDING-013, FINDING-020, FINDING-021 and the residuals of FINDING-005, FINDING-007, FINDING-015. **FINDING-013 (Critical) → Fixed**, **FINDING-005 → Fixed**, **FINDING-020 → Fixed**; FINDING-007, FINDING-021 → **Open (partially fixed)** with narrowed residuals; FINDING-015 → **Open (partially fixed)**, core defect closed. One new Low raised from the remediation (**FINDING-026**). Qualifiers updated on FINDING-016, FINDING-018, FINDING-025. **No Open Critical remains; 5 Open High keep the verdict at FAIL.** Phase 2 (Medium/Low full sweep) still outstanding. |
| 4 | 2026-09-17 | **Verify** | Re-checked FINDING-008 … FINDING-011. FINDING-009, FINDING-010, FINDING-011 → **Fixed**. FINDING-008 → **Open (partially fixed)**. Six new findings raised from the remediation itself (FINDING-020, FINDING-021 High; FINDING-022 … FINDING-025 Low). Qualifiers and line references updated on FINDING-013, FINDING-015, FINDING-016, FINDING-017, FINDING-018, FINDING-019. Phase 2 still outstanding. |

**Revision 5 scope limit.** Only the files changed in this remediation cycle were re-read (Full):
`backend/app/config.py`, `backend/app/main.py`, `backend/app/auth.py`, `backend/app/api/auth.py`,
the new-this-cycle `backend/app/egress_guard.py` changes, `backend/app/middleware.py` (re-read for
the middleware-ordering question), `backend/requirements.txt`, `docker-compose.yml`,
`docker/Caddyfile`, `.env.example`; Partial (targeted): `backend/app/api/settings.py` (egress/confirm
paths), `backend/app/audio/storage.py` (S3 client construction), `backend/app/providers/smoke.py`
(httpx client construction), `backend/app/api/twilio.py` (ticket mint/verify, lines 55-145),
`scripts/install.sh:160-259`, `backend/Dockerfile` (worker count), `docs/DEPLOYMENT.md` (grep only);
Context: `backend/tests/test_config.py`, `backend/tests/test_trusted_proxy.py`. No full rescan. All
findings not named in the Remediation Status table below retain their Revision 4 disposition.

**Revision 4 scope limit.** Only the files changed in that remediation cycle were re-read:
`backend/app/auth.py`, `backend/app/api/{auth,monitor,knowledge}.py`, `backend/app/{main,config}.py`,
the new `backend/app/middleware.py`, `docker-compose.yml`, `docker/Caddyfile`, the new
`docker/Caddyfile.dev`, `.env.example`, `scripts/install.sh` (Caddy/secret blocks),
`docs/DEPLOYMENT.md` (TLS/header/rotation sections), `frontend/src/lib/api.ts`,
`frontend/src/contexts/AuthContext.tsx`, `frontend/src/pages/SessionDetailPage.tsx` (monitor connect
path), with `backend/app/redis.py` and `backend/requirements.txt` re-read as `Context`. Tests
(`test_middleware.py`, `test_auth.py`, `conftest.py`) were read by targeted grep only. No full
rescan; FINDING-005 … FINDING-007 and FINDING-012 … FINDING-019 retain their prior disposition except
where a qualifier is explicitly updated below.

**Revision 3 scope limit.** Only the files changed in this remediation cycle were re-read: `.env.example`, `docker-compose.yml`, `scripts/install.sh`, `backend/app/{config,main,redis}.py`, `backend/app/api/{auth,settings,text_chat,twilio}.py`, `backend/app/providers/smoke.py`, `backend/app/pipeline/runner.py`, the four new modules (`security.py`, `rate_limit.py`, `crypto.py`, `egress_guard.py`), plus `docker/Caddyfile` and `backend/app/audio/storage.py` read as `Context`. Tests were read by targeted grep only. No full rescan; FINDING-008 … FINDING-014 retain their prior disposition and evidence.

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

Revision 5 reaches FAIL on **0 Open Critical and 5 Open High** findings.
(Revision 4: 1 Open Critical, 7 Open High. Revision 3: 1 Open Critical, 8 Open High. Revision 2: 1 Open Critical, 9 Open High. Revision 1: 2 Open Critical, 10 Open High.)

---

## Summary

- Files in repository scope: **158** · Full coverage: **22** · Partial: **14** · Not reviewed (deferred to Phase 2): **122**
- **Open Critical: 0 · Open High: 5 · Open Medium: 3 · Open Low: 8** (Revision 5) · remaining Medium/Low: pending Phase 2
- Revision 5 re-read (Full): `config.py`, `main.py`, `auth.py`, `api/auth.py`, `egress_guard.py`, `middleware.py`, `requirements.txt`, `docker-compose.yml`, `docker/Caddyfile`, `.env.example`; Partial (targeted): `api/settings.py`, `audio/storage.py`, `providers/smoke.py`, `api/twilio.py:55-145`, `scripts/install.sh:160-259`, `backend/Dockerfile`, `docs/DEPLOYMENT.md`
- Fixed in Revision 5: **FINDING-013 (Critical), FINDING-005 (High), FINDING-020 (High)** · Raised in Revision 5: **FINDING-026 (Low)**
- Revision 4 re-read (Full): `auth.py`, `api/auth.py`, `api/monitor.py`, `middleware.py`, `main.py`, `config.py`, `docker/Caddyfile`, `docker/Caddyfile.dev`, `docker-compose.yml`; Partial (targeted): `api/knowledge.py` (upload paths 1-210), `.env.example`, `scripts/install.sh` (Caddy/secret blocks), `docs/DEPLOYMENT.md` (TLS/header/rotation sections), the three changed frontend files (auth + monitor-connect paths); Context: `redis.py`, `requirements.txt`.
- Revision 4 counts (superseded): Open Critical 1 · Open High 7 · Open Medium 3 · Open Low 7
- Fixed to date: **FINDING-001 (Critical), FINDING-002 (Critical), FINDING-013 (Critical), FINDING-003 (High), FINDING-004 (High), FINDING-005 (High), FINDING-009 (High), FINDING-010 (High), FINDING-011 (High), FINDING-020 (High)**
- Raised in Revision 4: **FINDING-020, FINDING-021 (High); FINDING-022, FINDING-023, FINDING-024, FINDING-025 (Low)** — all arise from the Revision 4 remediation itself
- Partially fixed and still Open High: **FINDING-006, FINDING-007** (Revision 3/5), **FINDING-008** (Revision 4), **FINDING-021** (Revision 5) — the residuals are scoped in the Remediation Status table
- Advanced Security alerts triaged: **0 — not pulled, MCP unavailable** (no `GITHUB_PAT` this session). No CodeQL, Dependabot or Secret Scanning input. See *Coverage limits*.
- Secrets scan: **no live secrets detected** in the files scanned. Placeholder and obviously-fake CI values only.
- `package-lock.json` exception: **not exercised** — no Phase 1 finding hinged on a resolved JS version.

### Remediation Status — Revision 5

| Finding | Prior severity | Prior status | New status | Evidence | Residual gap |
|---|---|---|---|---|---|
| FINDING-013 `APP_ENV=development` disarms the start-up guards | **Critical** | Open | **Fixed** | `config.py:84-117` (`_validate_secret_key` now unconditional — weak/empty/placeholder rejected in every environment; `development` only substitutes a random `secrets.token_hex(32)` instead of raising), `config.py:100-109` (loud warning, key value never logged), `.env.example:17` (`APP_ENV=production`), `main.py:44-55` (auth posture unchanged) | Recs 3-5 not done: `app_env` is still a bare `str` (benign — only the exact literal `"development"` relaxes anything, so every typo fails *closed*), no start-up posture banner, no loopback-bind guidance. The ephemeral key is generated per `Settings()` *instance*; safe only because `config.py:299` is the single runtime instantiation and `backend/Dockerfile:16` runs one uvicorn worker with no `--reload`. Carried as a residual note, not a finding |
| FINDING-020 Monitor ticket accepted as an admin bearer token | High | Open | **Fixed** | `auth.py:94-104` (`typ:"access"` minted), `auth.py:128-131` (`verify_token` requires `typ=="access"` **and** rejects `purpose=="monitor_ws"`), `auth.py:86-91,235,249` (tickets signed/verified with an HKDF-SHA256 key derived under `info=b"oasis-monitor-ticket-signing-key-v1"`), `auth.py:231-234` (`sub` bound to the minting operator), `api/auth.py:231-234` + `auth.py:269-275` (logged at mint and at consume) | Recs 1-4 implemented; rec 5 (`Sec-WebSocket-Protocol` instead of a query parameter) not done — the ticket still travels in the URL, which stays a **FINDING-008** residual. Asymmetry noted: the **Twilio** stream ticket (`api/twilio.py:112,122`) is still signed with the raw `settings.secret_key`; cross-use is blocked by claim checks only (a stream ticket carries no `typ`, an access token carries no `purpose`/`agent_id`), not by key separation. Recommended for the same HKDF treatment |
| FINDING-005 Plaintext credential compare, no throttling | High | Open (partially fixed) | **Fixed** | `api/auth.py:44-70` (Argon2id `verify_password` preferred, `hmac.compare_digest` on both fallback paths, warning on the deprecated plaintext path), `install.sh:222-244` (image built, password piped over **stdin** into `docker run --rm -i --entrypoint python oasis-backend`, only `AUTH_PASSWORD_HASH` written to `.env`, `chmod 600`, abort if the hash is empty), `.env.example:134-145`, `config.py:248-252` | Rec 5 (second factor / network restriction for the single admin identity) still not done. Existing installs keep a plaintext `AUTH_PASSWORD` in `.env` indefinitely — the app warns on each use but nothing migrates them, and no runbook exists → new **FINDING-026** (Low), which also covers the installer still printing a generated password to stdout (`install.sh:193`) |
| FINDING-007 Writable provider endpoint URLs (SSRF / exfiltration) | High | Open (partially fixed) | **Open (partially fixed)** — residual narrowed | `egress_guard.py:60-98,175-194` (plain http to a private host now requires `EGRESS_ALLOWED_PRIVATE_HOSTS`; default empty = deny), `egress_guard.py:151-160` (unresolvable host now fails closed), `config.py:277-279`, `api/settings.py:396-405,477-513` (`audio_s3_endpoint_url` validated + confirm-gated), `audio/storage.py:204-221` (re-validated before the boto3 client is built), `providers/smoke.py:247-378` (`follow_redirects=False` on every client) | Two of the three Revision 4 residuals closed. Still open: (a) **no address pinning and redirects still followed** on `pipeline/runner.py` (litellm custom-LLM, pipecat OpenAI STT/TTS) and `api/text_chat.py` — a validated public https endpoint that answers `302 → http://169.254.169.254/…` still reaches internal targets, so the guard is bypassable on the paths that carry live interview traffic; (b) recs 4 (endpoint visible in the dashboard) and 5 (network-layer egress allow-list) not done. Allow-list parsing checked: a literal `*` is stored as a hostname literal and matches nothing, so no blanket wildcard — but an operator entry such as `10.0.0.0/8` or `0.0.0.0/0` (`egress_guard.py:71-76`) does reopen the blanket private allowance, and a literal hostname entry is matched **before** its resolved address, so a listed name that rebinds to another private IP is still allowed |
| FINDING-021 Unpatched `starlette` / `python-multipart` advisories | High | Open | **Open (partially fixed)** | `requirements.txt:11-15` (`fastapi==0.128.0`, `starlette==0.50.0` now pinned explicitly, `python-multipart==0.0.32`) | The four originally-cited advisories are Developer-reported as cleared; **five further `starlette` advisories (PYSEC-2026-161/2280/2281/248/249) are reported as still present**, needing `starlette>=1.0.1` + `fastapi>=0.141`. That upgrade path is blocked by the current pin (`fastapi==0.128.0` constrains `starlette<0.51.0`) and must be re-planned against `pipecat-ai==1.4.0`'s `fastapi<1,>=0.115.6`. Confidence stays **Needs verification** — no Dependabot/MCP this session, so no advisory was independently re-run. Remains **Open High** |
| FINDING-015 Rate limiting keyed on the reverse proxy's IP | Medium | Open | **Open (partially fixed)** — core defect closed | `main.py:16,130-141` (`ProxyHeadersMiddleware` added last = outermost, `trusted_hosts=settings.trusted_proxy_ips`), `config.py:294-296` (`TRUSTED_PROXY_IPS`, default `172.28.0.0/24`), `docker-compose.yml:128-137` (`oasis_net` pinned to the same subnet), `docker/Caddyfile:47,59` and `docker/Caddyfile.dev:29,38` (`header_up X-Forwarded-For {http.request.remote.host}` — overwrite, on both the `/api/*` and `/ws/*` blocks), `.env.example:204`, `tests/test_trusted_proxy.py:57-91` | Recs 1 and 2 implemented; recs 3 (global failure ceiling / backoff instead of hard lockout) and 4 (real WebSocket concurrency counter) not done. Residuals: the whole `172.28.0.0/24` subnet is trusted, so **any** container on `oasis_net` — not only Caddy — can forge `X-Forwarded-For`; `TRUSTED_PROXY_IPS` and the compose `subnet:` are two independent literals with no runtime cross-check, so they can drift apart silently (drift fails *safe* — the header is ignored and attribution reverts to the proxy address — but does so with no warning); and the new tests cover the `http` scope only, not the `websocket` scope that `/ws/twilio` depends on |
| FINDING-016 KEK keyed on a possibly-empty `SECRET_KEY` | Medium | Open | **Open (qualifier updated)** | `config.py:84-117` | The "empty/public KEK" half **is closed** — a weak `SECRET_KEY` can no longer reach `crypto.py:29` in any environment. Halves 2 (unauthenticated plaintext fallback in `decrypt_secret`) and 3 (silent corruption on key rotation) are untouched, and the development ephemeral key now makes half 3 fire on **every** dev restart |
| FINDING-018 / FINDING-025 | Low | Open | **Open (qualifier updated)** | `install.sh:234-239`, `config.py:100-117` | See the per-finding qualifiers below: no new plaintext secret on any argv, and the new validator messages contain no field values |
| FINDING-001 … FINDING-004, FINDING-009 … FINDING-011 | Critical/High | Fixed | **Fixed — no regression** | `main.py:89-112` CORS allow-list unchanged; `MaxBodySizeMiddleware` still registered inside the new proxy layer (`main.py:128,141`) and untouched (`middleware.py:25-91`); `.env.example` / compose fail-closed defaults intact | None from this cycle — see the middleware-ordering answer below |
| FINDING-006, FINDING-008, FINDING-012, FINDING-014, FINDING-017, FINDING-019, FINDING-022 … FINDING-024 | — | Open | **Open (unchanged)** | Not remediated in this cycle | Unchanged |

### Remediation Status — Revision 4 (superseded, retained for history)

| Finding | Prior severity | Prior status | New status | Evidence | Residual gap |
|---|---|---|---|---|---|
| FINDING-008 Token not revocable, token in WS URL | High | Open | **Open (partially fixed)** | `auth.py:58-67` (`jti`), `auth.py:70-105` (async verify + denylist + revoke), `auth.py:45` (2h), `auth.py:160-210` (ticket mint/consume), `api/auth.py:197-236`, `api/monitor.py:41-66`, `lib/api.ts:94-105`, `AuthContext.tsx:66-79`, `SessionDetailPage.tsx:167-180` | Recs 2 (refresh-token rotation) and 3 (`HttpOnly` cookie + CSRF) not done — the 2h token still lives in `localStorage` and is XSS-stealable. Ticket is bound to `session_id` but **not** to the issuing user, and still travels in the URL query string. Token/ticket confusion raised separately as FINDING-020 |
| FINDING-009 Unbounded upload read | High | Open | **Fixed** | `api/knowledge.py:24-43,155-202` (415 allow-list, 64 KiB streaming read, 2 MiB abort), `middleware.py:25-91` (CL pre-check + live counter, 413), `main.py:30,126`, `docker/Caddyfile:36-38` (10MB), `docker-compose.yml:69-70` (`mem_limit 2g`) | Recs 1-5 implemented. Rec 6 (Starlette / `python-multipart` advisories) **not** done and now affirmatively confirmed vulnerable — carried forward as **FINDING-021** rather than left inside this finding. Two scope notes recorded in the disposition (multipart still spools the whole ≤10 MiB body before the handler runs; WebSocket frames are outside the middleware) |
| FINDING-010 Plain HTTP default, no security headers | High | Open | **Fixed** | `docker/Caddyfile:19` (`{$DOMAIN}`, no plaintext fallback), `:24-29` (HSTS, nosniff, Referrer-Policy, Permissions-Policy), `:33,54,60` (per-route CSP), `docker/Caddyfile.dev:1-39` (non-default opt-out), `docker-compose.yml:9-18`, `scripts/install.sh:218-243`, `docs/DEPLOYMENT.md:741-759` | Recs 1-5 implemented. Two residuals raised as new Low findings: `/interview/*` has no `frame-ancestors` allow-list (**FINDING-022**) and `CADDY_CONFIG_FILE` can select the plaintext proxy in production (**FINDING-023**). The un-TLS'd Redis link is **not** part of this finding — it is FINDING-006's residual and remains Open |
| FINDING-011 Postgres default password | High | Open | **Fixed** | `config.py:19,90,100-110` (no default, unconditional validator), `docker-compose.yml:81` (`:?` fail-closed), `.env.example:30-35` (empty + guidance), `docs/DEPLOYMENT.md:404-414` (rotation runbook) | Recs 1-3 and 5 implemented; rec 4 (`sslmode=require` on the backend↔Postgres hop) was advisory and remains undone — tracked with the Redis-TLS residual under FINDING-006. The rotation runbook itself places the new password on the process argv → **FINDING-024** |
| FINDING-001 … FINDING-004 | Critical/High | Fixed (rev 2-3) | **Fixed — no regression** | `main.py:33-53` and `api/router.py` unchanged in shape; `configure_cors` (`main.py:87-110`) unchanged except line drift; the new `MaxBodySizeMiddleware` is registered after CORS so it is the outermost user middleware and does not disturb the allow-list | None from this cycle |
| FINDING-005 … FINDING-007, FINDING-012 … FINDING-019 | — | Open | **Open (unchanged)** | Not remediated in this cycle | Qualifiers and line references refreshed in place where the Revision 4 changes moved code (FINDING-013, 015, 016, 017, 018, 019) |

**Specific fail-open / regression questions answered this cycle (Revision 5)**

- **Is the development ephemeral key per process or per `Settings()`?** Per **instance** (`config.py:100`), and `tests/test_config.py:205-220` asserts two instances differ. It is safe only because there is exactly one runtime instantiation (`config.py:299`, module import) — a repository-wide grep found no other `Settings(` construction outside tests — and `backend/Dockerfile:16` starts a single uvicorn worker with no `--reload`. Add `--workers 2` or `--reload` in development and admin tokens, Twilio/monitor tickets and the Redis KEK diverge per process. Recommendation: derive it once at module scope, or assert a singleton.
- **Can the ephemeral key leak into logs?** No. The warning (`config.py:101-109`) names the variable and never the value; no code path logs `settings`, a `Settings` repr, or `settings.secret_key` (grep: only `crypto.py:29`, `auth.py:91,104,122`, `api/twilio.py:112,122` consume it). The pydantic-repr-in-traceback path remains as **FINDING-025**, unchanged in mechanism.
- **Is the `typ` check applied to every token-consuming path?** Yes for everything that goes through `verify_token` (`auth.py:107-136`) — `require_auth` and `require_valid_token` are the only two consumers. The **Twilio** stream ticket keeps its own verifier (`api/twilio.py:115-129`) signed with the raw `secret_key`. Cross-acceptance was traced in both directions and is **blocked**: an access token carries no `purpose`/`agent_id`, so `_verify_stream_ticket` rejects it; a stream ticket carries no `typ`, so `verify_token` rejects it. The separation is claim-based rather than key-based on that path — a hardening gap, not a live defect (recorded under FINDING-020).
- **Does `ProxyHeadersMiddleware` being outermost break `MaxBodySizeMiddleware` or CORS?** No. Order is now ProxyHeaders → MaxBodySize → CORS → router (`main.py:123,128,141`; Starlette runs the most recently added first). `ProxyHeadersMiddleware` only rewrites `scope["client"]`/`scheme` and forwards the original `receive`, so the streaming byte counter and the `Content-Length` pre-check are unaffected; `MaxBodySizeMiddleware` remains outside CORS, so 413s still carry no `Access-Control-Allow-*` (unchanged from Revision 4). `RequestBodyTooLarge` still unwinds to `MaxBodySizeMiddleware` before Starlette's `ServerErrorMiddleware`, which sits outside all user middleware — the 413 path is intact.
- **Do WebSocket scopes get the corrected client?** `MaxBodySizeMiddleware` passes non-`http` scopes straight through (`middleware.py:44-46`), and uvicorn's `ProxyHeadersMiddleware` handles `websocket` scopes as well as `http`, so `/ws/twilio`'s `websocket.client.host` (`api/twilio.py:305`) should now be the real caller. **Confidence: Probable** — the wiring tests (`test_trusted_proxy.py`) exercise the `http` scope only. A `websocket`-scope test is recommended before this is called confirmed.
- **Can the trusted-proxy CIDR and the compose subnet drift?** Yes, silently — they are independent literals (`config.py:295` vs `docker-compose.yml:137`) with no start-up cross-check. The drift direction is fail-safe (header ignored, attribution collapses back to the proxy address) but produces no warning. Recorded as a FINDING-015 residual.
- **Can `install.sh` leak the admin password via argv, `ps` or history?** Not through argv: the password reaches the hashing container over **stdin** (`install.sh:234-239`) and `docker run` carries no secret on its command line. Two residual channels remain: the *generated* password is echoed to stdout (`install.sh:193`, captured by any `tee`/CI log → **FINDING-026**), and running the installer under `bash -x` would trace it. Separately, `SECRET_KEY`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD` and the OpenAI key are still expanded onto the `sed` command line (`install.sh:207-217`), and the Argon2id hash now joins them (`install.sh:243`) — momentary host-local `ps` exposure, folded into **FINDING-018**.
- **Does the egress allow-list reopen the blanket allowance?** Not by wildcard — `*` is kept as a hostname literal and matches no real host (`egress_guard.py:77-83,91`). It *is* reopenable by an operator CIDR entry (`10.0.0.0/8`, `0.0.0.0/0`), and a listed hostname literal is matched before its resolved address, so a listed name that rebinds elsewhere on the private network is still permitted. Both recorded as FINDING-007 residuals.
- **Did the fastapi 0.115 → 0.128 / starlette 0.41 → 0.50 jump change a default that affects FINDING-009?** Nothing observable in the code under review: the 413 path is implemented at raw ASGI level and does not depend on framework exception handling, and the per-part / form-field limits that could interact with `api/knowledge.py`'s 2 MiB streaming cap (`max_part_size`, `max_files`, `max_fields`) already existed in the previously pinned `starlette 0.41.3`. **Not independently verified** — the environment is containerised and no site-packages tree was available to read. The Developer's "513 tests pass" is the only evidence; an explicit upload test at ~1.5 MiB and a 413 test are the cheapest confirmations.

**Specific fail-open / regression questions answered in Revision 4**

- **Redis unavailable → fail closed.** `_is_revoked` (`auth.py:90-92`) and `consume_monitor_ticket` (`auth.py:203-210`) both let a `redis.exceptions.ConnectionError` propagate; nothing catches it, so `require_auth` raises rather than returning a payload and `monitor_ws` closes before `accept()`. Correct direction. Caveat: the API surfaces it as an unhandled **500** rather than a 503, and a Redis outage therefore takes the entire admin API down — recorded as an availability note on FINDING-008, not a new finding.
- **`verify_token` is now `async`** — every call site awaits it (`auth.py:128,152`, `api/auth.py:181`); a repository-wide grep found no remaining synchronous caller.
- **No new `X-Forwarded-For` trust** was introduced (`api/auth.py:73-74` still uses `request.client.host`; no `proxy_headers` / `forwarded_allow_ips` anywhere). FINDING-015 is unchanged, not worsened.
- **No new guard keyed on `APP_ENV` or `debug`.** The new `_validate_postgres_password` (`config.py:100-110`) is deliberately unconditional — it is the pattern FINDING-013 recommendation 1 asks for on `SECRET_KEY`, which is still `app_env`-gated (`config.py:68`). FINDING-013 stays Critical/Open.
- **`/auth/logout` and `/auth/monitor-ticket` are not rate-limited.** Both require a valid token first, so the abuse ceiling is that of an authenticated caller; the denylist key a caller can create is its own single `jti`. Not a finding on its own, but noted under FINDING-020.

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
| `backend/app/middleware.py` | High | Full | 1-91 (new in rev 4) |
| `docker/Caddyfile.dev` | High | Full | 1-39 (new in rev 4) |
| `backend/app/redis.py` | High | Full | 1-32 |
| `backend/app/realtime.py` | High | Full | 1-66 |
| `docker-compose.yml` | High | Full | 1-97 |
| `docker/Caddyfile` | High | Full | 1-25 |
| `.github/workflows/ci.yml` | High | Full | 1-143 |
| `.github/workflows/weekly.yml` | High | Full | 1-196 |
| `.env.example` | High | Full | 1-129 |
| `.gitignore` | High | Full | 1-54 |
| `backend/Dockerfile` | High | Full | 1-17 (re-read rev 5 — single uvicorn worker, no `--reload`) |
| `backend/requirements.txt` | High | Full | 1-62 (re-read rev 5) |
| `backend/app/egress_guard.py` | High | Full | 1-195 (re-read rev 5 — allow-list parsing, resolution, http/https branches) |
| `backend/app/api/settings.py` | High | Partial | 1-400 read; rev 5 added targeted reads of the egress-validation and confirm-gate paths (`241-269`, `396-405`, `477-513`); catalog and smoke-test route still pending |
| `backend/app/api/interviews.py` | High | Partial | 1-200 read (agent resolve, pid resolve, session create); pipeline run + finalise pending |
| `backend/app/api/knowledge.py` | High | Partial | 1-210 read (all upload paths, re-read in rev 4); delete/search tail pending |
| `frontend/src/contexts/AuthContext.tsx` | High | Partial | 1-85 read (login/logout/token lifecycle) |
| `docs/DEPLOYMENT.md` | Medium | Partial | TLS/header section 725-760, password-rotation runbook 404-414, installer summary 316-322/649-652 |
| `backend/app/api/sessions.py` | High | Partial | 380-540 read (export tail, audio manifest, audio download, engagement); 1-380 and 540+ pending |
| `backend/app/api/text_chat.py` | High | Partial | 1-200 read (RAG injection, model resolve); WS frame loop pending |
| `backend/app/audio/storage.py` | High | Partial | 1-200 read (sanitiser, local + S3 backends); rev 5 grepped/read the factory tail `204-221` (egress re-validation before the boto3 client) |
| `backend/app/knowledge/embeddings.py` | High | Partial | 225-284 read — the only raw SQL in the tree. Grepped for `text(`, `execute(`, f-string SQL |
| `backend/app/models/agent.py` | Medium | Partial | Grepped `widget_key`, `_generate` — key entropy verified |
| `backend/app/providers/smoke.py` | High | Partial | Grepped `base_url`, `api_base`, `httpx.` — outbound target control assessed; rev 5 grepped `follow_redirects` / `validate_egress_url` across all 8 client constructions |
| `scripts/install.sh` | High | Partial | 150-269 read (secret generation, `.env` patch, Caddy rewrite, rev 5 Argon2id hashing block `222-244`); 1-150 pending |
| `backend/tests/test_trusted_proxy.py` | Medium | Full | 1-92 (new in rev 5 — `http` scope only, no `websocket` case) |
| `backend/tests/test_config.py` | Medium | Partial | 60-130 read; grepped `ephemeral` / `token_hex` — per-instance key generation confirmed at `205-220` |
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
| `frontend/Dockerfile`, `frontend/package.json`, `scripts/update.sh`, `scripts/verify_providers.py`, `backend/{alembic.ini,pytest.ini}` | Medium | **Not reviewed** | Deferred to Phase 2 (`docs/DEPLOYMENT.md` moved to Partial in rev 4) |

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

## Remediation Status (Revision 2)

| Finding | Prior severity | Prior status | New status | Evidence | Residual gap |
|---|---|---|---|---|---|
| FINDING-001 Auth disabled by default | Critical | Open | **Fixed** | `config.py:158` (`auth_enabled: bool = True`) · `main.py:26-46,58` (`enforce_auth_posture()` raises, logs posture) · `api/auth.py:49-53` (login → 503) · `monitor.py:50-58` (unconditional JWT, close 4401 before `accept()`) · `.env.example:98` | `GET /api/auth/status` still returns `authenticated: true` when auth is off (`api/auth.py:81-86`); the fail-open branch itself survives at `auth.py:62-63` and is only neutralised by the `APP_ENV` gate → see FINDING-013. Stale docs: `auth.py:9`, `LoginPage.tsx:142`, `SettingsPage.tsx:542`, `architecture.md:353,393`. |
| FINDING-002 Placeholder `SECRET_KEY` accepted | Critical | Open | **Fixed** | `config.py:38-52` (`model_validator` rejects empty / placeholder / `<32` chars when `app_env != "development"`) · `config.py:13-14` (named constants) · `.env.example:11-15` (`SECRET_KEY=` empty) · `tests/test_config.py:64-90` | Recommendations 3 (separate `JWT_SIGNING_KEY`) and 4 (asymmetric signing) not implemented — and `secret_key` now signs a **second** credential type (Twilio stream tickets, `twilio.py:103`), widening the blast radius of a single key. The validator does not fire in `development`, where the shipped `.env.example` leaves `SECRET_KEY` **empty** → see FINDING-013. |
| FINDING-003 Twilio endpoints unauthenticated | High | Open | **Fixed** | `twilio.py:76-91` (`RequestValidator`, fails closed on unset token / missing header) · `twilio.py:205-210` (403 before any DB work or `To`-routing) · `twilio.py:64-73,237-238` (`<Stream>` URL from `settings.domain`, not `Host`) · `twilio.py:94-120,243,256` (60 s HS256 ticket) · `twilio.py:321-333` (ticket verified against path `agent_id`, close 4401 before `Session` creation) | Ticket is documented as "single-use" (`twilio.py:24,95`) but there is **no replay store** — it is reusable for its full 60 s TTL. `websocket.accept()` still precedes the check (`twilio.py:277`), so an unauthenticated peer holds a socket for up to 10 s; rate limiting remains with FINDING-005. `_public_webhook_url` drops the query string, so a Twilio webhook URL configured with query parameters will fail validation (fails closed — availability, not security). The ticket is written to logs → FINDING-014. |
| FINDING-004 … FINDING-012 | — | Open | **Open (unchanged)** | Not re-read in Verify Mode | FINDING-004 (`debug: bool = True`, `config.py:28` → `main.py:91` CORS `allow_origins=["*"]` with credentials) is **unaffected** by this remediation and still reflects any origin by default. FINDING-005's "no rate limiting" qualifier now also covers the Twilio webhook and `/ws/twilio/*`. FINDING-008's "conditional on `auth_enabled`" qualifier on the monitor plane is **retired** — the monitor WebSocket is now unconditional; the token-in-URL and no-revocation parts of FINDING-008 stand. |

## Remediation Status (Revision 3)

| Finding | Prior severity | Prior status | New status | Evidence | Residual gap |
|---|---|---|---|---|---|
| FINDING-004 CORS reflects any origin with credentials | High | Open | **Fixed** | `config.py:31` (`debug: bool = False`) · `config.py:47-55` (`CORS_ALLOWED_ORIGINS` CSV → `cors_allowed_origins`, no link to `debug`) · `main.py:80-103` (`configure_cors()` registers `CORSMiddleware` only when the allow-list is non-empty; methods narrowed to the six used, headers to `Authorization`/`Content-Type`) · `main.py:114` · `.env.example:16-26` (`DEBUG=false`, `CORS_ALLOWED_ORIGINS=` empty) · `install.sh:203` | The allow-list is passed through verbatim — `CORS_ALLOWED_ORIGINS=*` re-creates the exact reflected-origin-with-credentials behaviour, and `null` is likewise accepted → **FINDING-017 (Low)**. |
| FINDING-005 Plaintext, non-constant-time credential check, no throttling | High | Open | **Open — partially fixed** | Fixed parts: `security.py:10-31` (Argon2id `hash_password`/`verify_password`, never raises) · `api/auth.py:42-60` (`hmac.compare_digest` for username and the legacy password path; `AUTH_PASSWORD_HASH` preferred, plaintext path logs a deprecation warning) · `api/auth.py:111-137` (lockout check → 429 + `Retry-After`, failure recorded, success clears; every attempt logged with outcome + IP) · `rate_limit.py:40-77` (5 failures / 15 min → 15 min lockout, Redis-backed, shared across replicas) | Defect 1 of the finding (**plaintext credential at rest**) is unaddressed for every supported deployment: `install.sh:187-211` still writes `AUTH_PASSWORD=<plaintext>` and never generates `AUTH_PASSWORD_HASH`; `.env.example:114-121` has no `AUTH_PASSWORD_HASH` line at all, so the hash path is undiscoverable and unused in practice. Rec 5 (second factor / trusted-network restriction) not done. Lockout keying is unsound behind the shipped reverse proxy → **FINDING-015**. |
| FINDING-006 Redis unauthenticated, credentials stored plaintext | High | Open | **Open — partially fixed** | Fixed parts: `docker-compose.yml:86-92` (`--requirepass ${REDIS_PASSWORD:?…}` fails the stack closed; `CONFIG`/`KEYS`/`FLUSHALL`/`FLUSHDB` renamed off) · `docker-compose.yml:47` (backend `REDIS_URL` embeds the password, overriding `.env`) · `.env.example:36-48`, `install.sh:198,206` (generated `openssl rand -hex 24`) · `crypto.py:27-39` (Fernet, key HKDF-SHA256-derived from `SECRET_KEY` with a distinct `info` label) · `api/settings.py:272,495` (encrypt before `HSET` for non-URL keys and S3 credentials), `:176,184,410` (transparent decrypt) · `api/settings.py:261,266-273,491-497` (audit lines with actor from the JWT `sub`) | No TLS on the Redis link — the finding's "or TLS" half stands; the bridge network still carries `AUTH <password>` and every value in clear at the protocol level. Credentials still live in Redis (rec 3 not done) and RDB persistence is still on (rec 4 partial), so the `redisdata` volume and backups still hold them, now ciphertext. The KEK is `SECRET_KEY`, which `config.py:61-75` only enforces outside `development` — in the shipped default posture the KEK is derivable by anyone → **FINDING-016**, compounding FINDING-013. `decrypt_secret`'s plaintext fallback removes Fernet's integrity guarantee → **FINDING-016**. `REDIS_PASSWORD` handling exposes it in container metadata → **FINDING-018**. |
| FINDING-007 Operator-writable provider URLs → exfiltration / SSRF | High | Open | **Open — partially fixed** | Fixed parts: `egress_guard.py:44-109` (scheme allow-list, embedded-credential rejection, loopback / link-local incl. `169.254.169.254` / multicast / reserved / unspecified blocked, sibling-service hostnames blocked, `http` only for RFC1918) · `api/settings.py:241-256` (validate on write → 400; `confirm_endpoint_change: true` required to change a URL to a new value) · `api/settings.py:266-269` (audit line with actor, old and new value) · re-validation immediately before egress at `providers/smoke.py:176,282,369`, `api/text_chat.py:299`, `pipeline/runner.py:696,1418,1496` | **`audio_s3_endpoint_url` is still unvalidated and needs no confirmation** (`api/settings.py:371,396,489-497`) although it is used directly as the boto3 `endpoint_url` (`audio/storage.py:209`) that receives recorded participant audio and the S3 credentials — same attack class as the finding. **Any RFC1918 destination is still permitted over `http`**, so internal-network SSRF survives: the `_DENIED_HOSTNAMES` set (`egress_guard.py:27`) lists five service names only, and Compose also publishes container-name aliases (e.g. `oasis-platform-postgres-1`), which resolve to a private address and pass. **TOCTOU remains** — the guard resolves the name, then the HTTP client resolves it again independently; nothing pins the validated address, so a low-TTL rebinding record still wins the race (the pre-request call narrows the window, it does not close it), and `runner.py` validates once per session, not per request. `socket.gaierror` is swallowed (`egress_guard.py:90-91`) and an unresolvable `https` host passes. Redirects are not constrained — a validated public host can 30x the client to an internal address. Recs 4 (dashboard visibility) and 5 (network-layer egress allow-list) not done. |
| FINDING-003 Twilio endpoints unauthenticated | High | **Fixed** | **Fixed (unchanged)** | Twilio webhook now rate-limited before signature validation (`twilio.py:206-219`, 60/60s) and the media-stream WebSocket checked before `accept()` (`twilio.py:301-313`, 30/60s) | The Revision 2 residual "rate limiting remains with FINDING-005" is **partially retired**: an excess connection is now refused pre-`accept()`. It is **not** retired for the *bounded-hold* concern — `check_fixed_window` is a request-rate cap, not a concurrency cap, so up to 30 new sockets per minute may still each hold a slot for the 10 s handshake window and accumulate. Keyed on the proxy IP, the cap is deployment-wide → **FINDING-015**. Replay store still absent. |
| FINDING-013 Fail-closed guards keyed on `APP_ENV` | Critical | Open | **Open (unchanged, compounded)** | Re-checked the new guards: CORS (`main.py:90`), rate limiting (`rate_limit.py`), the egress guard (`egress_guard.py`) and credential encryption (`crypto.py`) are **not** keyed on `APP_ENV` or `debug` — no new environment-gated guard was introduced | Compounded nonetheless: `crypto.py:27-30` derives the credential-encryption key from `SECRET_KEY`, and `config.py:61-75` still permits an empty or placeholder `SECRET_KEY` whenever `APP_ENV == "development"` (the shipped `.env.example:10` default). In that posture the Fernet KEK is a published constant, so FINDING-006's encryption yields no confidentiality. `install.sh:202` sets `APP_ENV=production`, so the installer path is unaffected; a hand-rolled deploy is not. |
| FINDING-014 Stream ticket logged in plaintext | Medium | Open | **Open (unchanged)** | Line reference moves to `twilio.py:338-341` (`params={custom_params}`, which carries the ticket) | Unchanged. |
| FINDING-008 … FINDING-012 | — | Open | **Open (unchanged)** | Not re-read in Revision 3 | FINDING-010 (no TLS) now also covers the Redis link — see the FINDING-006 residual. FINDING-011 (`POSTGRES_PASSWORD` default `change-me`) is **unchanged**: `docker-compose.yml:64` still resolves a silent default, in contrast to the `:?` fail-closed treatment `REDIS_PASSWORD` received at `:47,88`. |

**Verdict impact of Revision 3.** One High moved to Fixed (FINDING-004). Three Highs remain Open with materially reduced but non-zero residual. The Critical (FINDING-013) is untouched, so the verdict is unchanged at **FAIL**.

## Remediation Status (Revision 4)

The Revision 4 table, together with the fail-open / regression questions answered this cycle, is in
the **Summary** section above (*Remediation Status — Revision 4*), so that the current status is the
first thing a reader meets. Headline: **FINDING-009, FINDING-010 and FINDING-011 → Fixed**;
**FINDING-008 → Open (partially fixed)**; six new findings raised from the remediation itself
(**FINDING-020, FINDING-021** High; **FINDING-022 … FINDING-025** Low).

**Verdict impact of Revision 4.** Three Highs moved to Fixed; two new Highs were raised from the
remediation, one of which (FINDING-020) partially reverses the FINDING-008 fix it belongs to. The
Critical (FINDING-013) is untouched, so the verdict is unchanged at **FAIL**.

---

**Qualifier changes to downstream findings (Revision 2).** The FINDING-001 fix removes the "inert while `AUTH_ENABLED=false`" caveat from the Threat Assessment trust-boundary table for the Admin REST and Monitor WS zones **only when `APP_ENV != "development"`**; the Twilio zone moves from `Broken` to `Signature + ticket verified`. The Threat Assessment table below is annotated accordingly.

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
**Disposition:** **Fixed (Revision 2)** — all five recommendations implemented and verified: default inverted (`config.py:158`), startup refuses `AUTH_ENABLED=false` outside development (`main.py:35-40`, called first in `lifespan`, `main.py:58`), login returns `503` instead of a token (`api/auth.py:49-53`), the monitor WebSocket requires a valid JWT unconditionally and closes `4401` **before** `accept()` (`monitor.py:50-58`), and the effective posture is logged at startup (`main.py:41-46`). Residual: `GET /api/auth/status` still claims `authenticated: true` while auth is disabled (`api/auth.py:81-86`) — misleading to the frontend, dev-only reach, recorded as a Low item for Phase 2. The fail-open branch in `auth.py:62-63` still exists and is neutralised only by the `APP_ENV` gate, which is itself weak — **FINDING-013**.

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
**Disposition:** **Fixed (Revision 2)** — recommendations 1 and 2 implemented as specified: `config.py:38-52` raises on an empty, placeholder or sub-32-character key whenever `app_env != "development"`, and `.env.example:15` now ships `SECRET_KEY=` empty with an inline instruction to generate one. `scripts/install.sh:195,200,202` still generates a 64-hex-character key and sets `APP_ENV=production`. Recommendations 3 (dedicated `JWT_SIGNING_KEY`) and 4 (asymmetric signing) were **not** implemented and remain open hardening items — now more relevant, because `secret_key` also signs Twilio stream tickets (`twilio.py:103`), so one key compromise yields both admin tokens and media-stream tickets. The `development` escape hatch combined with the shipped `APP_ENV=development` is carried forward as **FINDING-013**.

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
**Disposition:** **Fixed (Revision 2)** — recommendations 1-4 implemented and verified. Signature validation runs before agent lookup, `To`-routing and TwiML generation, and fails closed when `TWILIO_AUTH_TOKEN` is unset or the header is absent (`twilio.py:76-91,205-210`); the signed URL is reconstructed from `settings.domain`, never from `Host` (`twilio.py:64-73`); the `<Stream>` URL is likewise built from `settings.domain` (`twilio.py:237-238`); and a 60-second HS256 ticket bound to the resolved `agent_id` is minted by the webhook (`twilio.py:94-103,243,256`) and verified against the path `agent_id` immediately after the `start` frame, before any `Session` row or pipeline exists (`twilio.py:321-333`, close `4401`). Recommendation 5 (rate limiting) was explicitly deferred to FINDING-005 — acceptable, FINDING-005 is still Open. Residuals: the ticket is replayable within its 60-second window (no `jti`/nonce store, despite the "single-use" wording at `twilio.py:24,95`); `accept()` still precedes the check (`twilio.py:277`) because Twilio carries `customParameters` in the `start` frame — acknowledged as unavoidable, cost is a connection slot for ≤10 s; and `_public_webhook_url` omits the query string, so a webhook URL configured with query parameters would fail validation (fails closed). Ticket exposure in logs is raised as **FINDING-014**.

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
**Disposition:** **Fixed** (Revision 3) — recommendations 1-4 all implemented: `config.py:31,47-55`, `main.py:80-103,114`, `.env.example:16-26`. Residual hardening tracked as FINDING-017 (the allow-list accepts a literal `*`).

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
**Disposition:** **Fixed (Revision 5).** Recommendation 1 is now adopted, not merely available: `api/auth.py:56-57` prefers Argon2id `verify_password(AUTH_PASSWORD_HASH)`, `install.sh:222-244` hashes the password **inside the backend image over stdin** and writes only `AUTH_PASSWORD_HASH` to a mode-600 `.env`, and `.env.example:134-145` ships the hash field with the plaintext field documented as deprecated. The plaintext path survives only as a warned migration route (`api/auth.py:58-66`). Two residuals, neither High: recommendation 5 (second factor / network restriction for the single admin identity) is still not done, and existing installs are never migrated off plaintext — tracked with the installer's stdout echo as **FINDING-026** (Low).

> **Superseded Revision 3 disposition.** Open — partially fixed. Recommendations 2, 3 and 4 verified implemented (`api/auth.py:42-60,111-137`, `security.py:10-31`, `rate_limit.py:40-77`); recommendation 1 is only *available*, not adopted — `install.sh:187-211` and `.env.example:114-121` still produce a plaintext `AUTH_PASSWORD` for every supported install, so the credential is still recoverable from `.env`, `docker inspect` or a backup. Recommendation 5 not done. Remains **Open High** on the unhashed-at-rest defect alone. See also FINDING-015 (lockout keyed on the proxy IP).

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
**Disposition:** **Open — partially fixed** (Revision 3). Recommendations 1, 2 and 5 implemented (`docker-compose.yml:47,86-92`, `crypto.py`, `api/settings.py:261-273,489-497`); recommendation 3 not done (credentials still in Redis) and recommendation 4 only half done (commands renamed, RDB persistence retained). Still **Open High**: no TLS on the Redis link, the encryption KEK is the same `SECRET_KEY` that may legitimately be empty in the shipped `development` posture, and the decrypt path accepts unauthenticated plaintext — see FINDING-016.

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
**Disposition:** **Open — partially fixed** (Revision 5; residual narrowed from Revision 3).

> **Revision 5 qualifier.** Two of the three Revision 4 residuals are closed. `audio_s3_endpoint_url`
> is now SSRF-validated and confirm-gated on write (`api/settings.py:396-405,477-513`) and
> re-validated immediately before the boto3 client is constructed (`audio/storage.py:204-221`). Plain
> `http` to a private address is no longer implicit: it requires the host to appear in
> `EGRESS_ALLOWED_PRIVATE_HOSTS` (`egress_guard.py:175-194`, `config.py:277-279`, default empty =
> deny), and an unresolvable host now fails closed (`egress_guard.py:151-160`) instead of slipping
> through as "not private". `providers/smoke.py` sets `follow_redirects=False` on every client.
> **Still Open High** on the redirect/rebinding residual: `pipeline/runner.py` (litellm custom-LLM,
> pipecat OpenAI STT/TTS) and `api/text_chat.py` re-validate before the request but hand the URL to
> SDK clients that follow 30x by default and never pin the resolved address — a validated public
> `https` endpoint answering `302 → http://169.254.169.254/…` still reaches internal targets, on
> exactly the paths that carry live interview audio and transcripts. Recommendations 4 (endpoint
> visibility in the dashboard) and 5 (network-layer egress allow-list) remain undone. Allow-list
> parsing was checked for a blanket-reopen: a literal `*` matches nothing, but an operator CIDR entry
> (`10.0.0.0/8`, `0.0.0.0/0`) does reopen the private allowance wholesale, and a listed *hostname*
> literal is matched before its resolved address (`egress_guard.py:91`), so a listed name that
> rebinds to another private IP is still permitted. Recommend matching on the resolved address only.

> **Superseded Revision 3 disposition.** Recommendations 1, 2 and 3 implemented for the five cited URL fields (`egress_guard.py:44-109`, `api/settings.py:241-269`, egress-site re-validation in `smoke.py`, `text_chat.py`, `runner.py`); recommendations 4 and 5 not done. Still **Open High** on three verified residuals: `audio_s3_endpoint_url` is unvalidated and unconfirmed yet receives participant audio and S3 credentials (`api/settings.py:371,396` → `audio/storage.py:209`); every RFC1918 destination remains reachable over `http`, including sibling containers via their Compose container-name aliases, which the five-entry `_DENIED_HOSTNAMES` set does not cover; and the validate-then-connect sequence never pins the resolved address, so DNS rebinding and 30x redirects to internal hosts are still viable.

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
**Disposition:** **Open (partially fixed — Revision 4)**

> **Revision 4 re-check.** Recommendations 1, 4 and 5 are implemented; 2 is implemented only in part
> and 3 is not implemented.
>
> - **Rec 1 — done.** `create_token` adds a `jti` (`auth.py:63`); `verify_token` is now `async` and
>   rejects a denylisted `jti` (`auth.py:70-92`); `revoke_token` writes the `jti` with a TTL matching
>   the remaining `exp` (`auth.py:95-105`); `POST /api/auth/logout` calls it (`api/auth.py:197-211`)
>   and the frontend invokes it on sign-out (`AuthContext.tsx:66-79`, `lib/api.ts:96`).
> - **Rec 2 — half done.** Lifetime cut 24h → 2h (`auth.py:45`, `api/auth.py:85`). No refresh token
>   and therefore no rotation or reuse detection.
> - **Rec 3 — not done.** The token is still written to `localStorage` (`lib/api.ts:14-22`) and
>   attached as an `Authorization` header (`lib/api.ts:38-40`). Any XSS still exfiltrates a 2-hour
>   admin credential; revocation only helps once the theft is noticed.
> - **Rec 4 — done, with a caveat.** `/ws/monitor/{session_id}` now takes `?ticket=` and consumes it
>   single-use via Redis `SET NX` before `accept()` (`api/monitor.py:41-66`, `auth.py:179-210`). The
>   ticket is bound to the target `session_id` and to a 60 s window, but **not** to the requesting
>   user — it carries no `sub`, so the monitor connection is unattributable in the audit trail
>   (`api/monitor.py:69` logs the session only), and any admin's ticket opens any other admin's
>   session view. The credential also still travels in a URL query string; the exposure window is now
>   60 s and single-use rather than 2 h and replayable, which is the intended improvement, but see
>   **FINDING-020** — the ticket is additionally accepted as a general-purpose bearer token.
> - **Rec 5 — moot.** No proxy log-stripping is needed for the admin token now that it never enters a
>   URL.
> - **Availability note.** Both new Redis paths fail **closed** on a Redis outage (an unhandled
>   `ConnectionError` propagates from `auth.py:92` / `auth.py:204`), which is the correct direction,
>   but the API returns an unhandled 500 rather than a 503 and every authenticated request fails for
>   the duration. Consider catching the connection error explicitly, logging it, and returning 503.
> - **Rate limiting.** Neither `/auth/logout` nor `/auth/monitor-ticket` is throttled; both sit behind
>   a valid-token check, so the abuse ceiling is that of an already-authenticated caller.

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
**Disposition:** **Fixed (Revision 4)**

> **Revision 4 re-check.** Recommendations 1-5 are implemented and were read in full.
>
> - **Recs 1-2.** `POST …/knowledge/file` validates `file.content_type` against an allow-list and
>   returns 415 (`knowledge.py:33-43,158-166`), then reads in 64 KiB chunks with a running byte
>   counter, raising 413 at 2 MiB **before** any `.decode()` (`knowledge.py:168-181`).
> - **Rec 3.** `…/knowledge/text` cannot stream (FastAPI must bind the JSON body first), so it is
>   covered by the new global backstop instead; the character cap remains as the business rule
>   (`knowledge.py:103-118`).
> - **Global backstop.** `MaxBodySizeMiddleware` (`middleware.py:25-91`) is a pure ASGI callable —
>   correctly *not* `BaseHTTPMiddleware`, which would have buffered the body it exists to bound. It
>   rejects on a declared `Content-Length` over 10 MiB before reading a byte, and otherwise counts
>   bytes as they arrive, so a **chunked transfer-encoding body with no `Content-Length` is caught**
>   (`middleware.py:59-74`) — verified by `tests/test_middleware.py:61-80`. Registered last in
>   `main.py:126` and therefore outermost of the user middleware.
> - **Recs 4-5.** `request_body { max_size 10MB }` on `/api/*` (`Caddyfile:36-38`) and `mem_limit`/
>   `memswap_limit` `2g` on the backend service (`docker-compose.yml:69-70`).
>
> **Scope notes carried forward (no longer part of this finding):**
> 1. **Multipart still spools the whole body.** Starlette parses the multipart request *before* the
>    handler runs, so the endpoint's streaming read operates on an already-materialised `UploadFile`.
>    The real bound on that materialisation is the 10 MiB middleware plus Caddy, not the 2 MiB loop —
>    acceptable, but the docstring's "aborts before the body is materialised" reading is too strong.
>    Bodies over `python-multipart`'s 1 MiB spool threshold land in the container's temp directory.
> 2. **The content-type allow-list admits `application/octet-stream` and `""`** (`knowledge.py:41-42`)
>    and the decode path falls back to Latin-1, which accepts arbitrary bytes — so the 415 check
>    stops honest mistakes, not an attacker. Bounded by the size caps; no separate finding.
> 3. **WebSockets bypass the middleware by design** (`middleware.py:44-46`) — correct, since an ASGI
>    body cap is meaningless for a WS scope, but it means participant frame sizes on `/ws/chat/*` and
>    `/ws/interview/*` remain uncapped. Added to the Phase 2 list.
> 4. **The 413 path is not integration-tested against the real app.** `tests/test_middleware.py`
>    exercises a bare echo app. Because the middleware is registered with `app.add_middleware`, it
>    sits inside Starlette's `ServerErrorMiddleware` and its own `except RequestBodyTooLarge` runs
>    first, so a 413 (not a 500) is expected — but confirm with one end-to-end chunked POST to
>    `/api/studies/{id}/knowledge/file`. Note also that 413 responses emitted by the middleware carry
>    no CORS headers, since CORS is registered inside it.
> - **Rec 6 (dependency advisories) is not done** and has moved from `Needs verification` to
>   affirmatively reported-vulnerable — tracked as **FINDING-021**.

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
**Disposition:** **Fixed (Revision 4)**

> **Revision 4 re-check.** All five recommendations are implemented.
>
> - **Rec 1.** The site address is `{$DOMAIN}` (`Caddyfile:19`). An unset or empty `DOMAIN` yields an
>   empty site address and Caddy refuses to load the config, so there is no silent plaintext
>   fallback. `docker-compose.yml:9-12` gives the caddy service its own `env_file: .env` so the
>   variable actually reaches it, and `scripts/install.sh:233-243` no longer sed-patches the file.
> - **Rec 2.** The `:80` plaintext block lives only in `docker/Caddyfile.dev`, selected by opt-in
>   `CADDY_CONFIG_FILE` (`docker-compose.yml:18`, default `./docker/Caddyfile`). See FINDING-023 for
>   the residual risk in that mechanism.
> - **Rec 3.** `Strict-Transport-Security: max-age=31536000; includeSubDomains`, `X-Content-Type-
>   Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin` and `Permissions-Policy:
>   microphone=(self)` on every response (`Caddyfile:24-29`), plus a per-route CSP: `default-src
>   'self'; frame-ancestors 'none'` on `/api/*` (`:33`) and `default-src 'self'; connect-src 'self';
>   img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self'; frame-ancestors 'none'`
>   on the admin dashboard (`:60`). **Reviewed for over-permissiveness:** no `unsafe-eval`, no
>   `unsafe-inline` in `script-src`, no wildcard `connect-src` — the only relaxation is
>   `style-src 'unsafe-inline'`, which is the normal cost of a bundled React/Tailwind build and does
>   not undermine `script-src`. Two operational cautions rather than findings: (a) `connect-src
>   'self'` must cover the same-origin `wss://` monitor and chat sockets — current Chrome and Firefox
>   treat `'self'` as matching same-origin `ws:`/`wss:`, older Safari does not, so smoke-test the
>   monitor view before release and add an explicit `connect-src 'self' wss://{$DOMAIN}` if it
>   breaks; (b) `includeSubDomains` on an apex `DOMAIN` forces HTTPS on every sibling subdomain of
>   that apex — intended, but call it out at install time. `preload` is correctly **not** set, which
>   is the right choice for a `DOMAIN=localhost` default (`docs/DEPLOYMENT.md:833` documents why).
> - **Rec 4.** Caddy's automatic HTTPS supplies the `:80` → `:443` redirect for a named site; both
>   ports remain published (`docker-compose.yml:6-8`).
> - **Rec 5.** Documented in `docs/DEPLOYMENT.md:741-759` as a header table plus the `Caddyfile.dev`
>   caveat, and in the installer's "what it does not do" list at `:833`.
>
> **Residuals raised as new findings:** FINDING-022 (`/interview/*` framable by any origin — the
> deliberate embedding decision is accepted, but undocumented and unbounded), FINDING-023
> (`CADDY_CONFIG_FILE` can select the plaintext proxy in production). Two stale sentences in
> `docs/DEPLOYMENT.md:320` and `:652` still claim the installer "patches the Caddyfile" — a doc
> accuracy defect only, folded into FINDING-023's recommendation.
>
> **Not part of this finding:** the un-TLS'd backend↔Redis link and the missing Postgres
> `sslmode=require` are FINDING-006's residual and FINDING-011 recommendation 4 respectively. Both
> were deliberately deferred this cycle and remain outstanding.

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
**Disposition:** **Fixed (Revision 4)**

> **Revision 4 re-check.** Recommendations 1, 2, 3 and 5 are implemented; recommendation 4 was
> advisory and remains undone.
>
> - **Rec 1.** `postgres_password` has no working default (`config.py:90`) and a **model validator
>   that is deliberately unconditional** — it fires in `development` too (`config.py:100-110`),
>   rejecting both an empty value and the published `change-me` literal held as a rejection-only
>   constant (`config.py:19`). `docker-compose.yml:81` uses
>   `${POSTGRES_PASSWORD:?…}`, mirroring `REDIS_PASSWORD`, so compose refuses to start the stack.
>   This is the pattern FINDING-013 recommendation 1 asks for on `SECRET_KEY`; that gate is still
>   `app_env`-conditional (`config.py:68`), so FINDING-013 is unaffected.
> - **Rec 2.** `.env.example:35` is now an empty assignment with generation guidance at `:30-34`.
> - **Rec 3.** Rotation runbook at `docs/DEPLOYMENT.md:404-414`, including the `ALTER USER` step for
>   an existing volume — but the snippet puts the new password on the process argv, raised as
>   **FINDING-024**.
> - **Rec 5.** Already satisfied by the FINDING-006 work.
> - **Rec 4 (`sslmode=require`) not done.** Backend↔Postgres remains plaintext on the bridge network,
>   alongside the un-TLS'd Redis link under FINDING-006. Deferred by the Developer this cycle;
>   recorded here so it is not lost.
> - **Side effect, accepted:** because the validator runs at import of `app.config`, any tool that
>   imports the app (Alembic, scripts, tests) now requires the variable. `tests/conftest.py:35` sets
>   it. The failure mode of that validator is the subject of **FINDING-025**.

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

### FINDING-013: Both new fail-closed guards are keyed on `APP_ENV`, which defaults to and ships as `development`

**Severity:** Critical
**Exploitability:** Possible
**Confidence:** Confirmed
**Remediation Priority:** **P1**
**Source:** Manual review (Verify Mode, Revision 2)
**File:** `backend/app/config.py`, `backend/app/main.py`, `.env.example`
**Line:** `config.py:26` (`app_env: str = "development"`) · `config.py:40` · `main.py:35` · `.env.example:10,15`
**Category:** A02 Security Misconfiguration / A04 Cryptographic Failures / A07 Authentication Failures

**Description.** The remediations for FINDING-001 and FINDING-002 are both conditioned on the same
predicate, `settings.app_env != "development"`:

```python
if self.app_env != "development":      # config.py:40 — SECRET_KEY strength gate
if settings.app_env != "development" and not settings.auth_enabled:   # main.py:35 — auth posture gate
```

`app_env` defaults to `"development"` (`config.py:26`) **and** `.env.example:10` ships
`APP_ENV=development`, under the same `cp .env.example .env` instruction (`.env.example:4-5`) that
FINDING-002 was written about. On that path both new guards are inert. Worse, `.env.example:15` now
ships `SECRET_KEY=` **empty**, and an empty string is a perfectly valid HS256 key for PyJWT: with no
guard firing, `create_token` signs and `verify_token` accepts tokens keyed on `""`
(`auth.py:36,42-44`). Anyone can compute `jwt.encode({"sub":"admin", …}, "", algorithm="HS256")` and
pass `require_auth` on every protected router — the FINDING-002 bypass reproduced with a key that is
even easier to guess than the old placeholder. The same key also mints Twilio stream tickets
(`twilio.py:103`), so the FINDING-003 ticket control collapses with it. Separately, an operator who
sets `AUTH_ENABLED=false` while leaving `APP_ENV` at its default reinstates the full FINDING-001
fail-open path (`auth.py:62-63`) with no startup error.

`scripts/install.sh:195-206` does the right thing (`APP_ENV=production`, `openssl rand -hex 32`,
`AUTH_ENABLED=true`), but Revision 1 established — and the Developer's own remediation comment at
`config.py:35-37` repeats — that a deploy path skipping the installer must be assumed to exist.
The controls are therefore correct in production and absent on exactly the path they were written for.

**Impact.** On a non-installer deployment that retains `APP_ENV=development`: complete admin
authentication bypass by token forgery against an empty signing key, forgeable Twilio stream tickets,
and (if `AUTH_ENABLED` is flipped) the original unauthenticated admin API. Identical blast radius to
FINDING-001 and FINDING-002 — all participant PII, transcripts, recordings and provider credentials.

**Recommendation.**
1. Make the key gate unconditional. Reject an empty or placeholder `secret_key` in **every**
   environment; in `development` only, generate an ephemeral random key at import time and log loudly
   that tokens will not survive a restart. A weak key has no legitimate use in any environment.
2. Change `.env.example:10` to `APP_ENV=production` and document `development` as the opt-in, so the
   copy-paste path lands in the guarded configuration by default.
3. Constrain `app_env` to a known set (`Literal["development","staging","production"]`) so a typo
   such as `APP_ENV=dev` cannot silently pick the *strict* branch — and, more importantly, so
   `development` is a deliberate spelling rather than a default.
4. Emit a single consolidated startup banner listing effective posture (`app_env`, auth, key source,
   CORS) so an operator can see a development-mode deployment in `docker compose logs`.
5. Consider refusing to bind to a non-loopback interface when `app_env == "development"`.

**Standard Reference:** OWASP Top 10 (2025) A02, A04, A07.
**Disposition:** **Fixed (Revision 5).**

> **Revision 5 verification.** Recommendations 1 and 2 implemented, and they are what the Critical
> rating rested on. `_validate_secret_key` (`config.py:84-117`) is now unconditional: an empty,
> placeholder or sub-32-character key is rejected in every environment, and `development` is an
> exemption from *raising* only — it substitutes a random `secrets.token_hex(32)` and logs a loud,
> value-free warning (`config.py:100-109`). `.env.example:17` ships `APP_ENV=production` with an empty
> `SECRET_KEY`, so the copy-paste path now **fails closed** rather than signing tokens with a public
> constant. The auth-posture gate (`main.py:44-55`) keeps its deliberate `development` exemption for
> `AUTH_ENABLED=false`, which is documented behaviour and no longer stacks with a forgeable key.
>
> Residuals, none High: recommendations 3-5 (Literal-typed `app_env`, consolidated posture banner,
> loopback-bind guard) are not done — benign for the strict branch, since only the exact literal
> `"development"` relaxes anything and every typo therefore fails closed. The ephemeral key is
> generated per `Settings()` instance, not memoised per process; this is safe only because
> `config.py:299` is the sole runtime instantiation and `backend/Dockerfile:16` runs one uvicorn
> worker without `--reload`. Adding workers or reload in development would give each process a
> different signing key and KEK. Recommend memoising the ephemeral key at module scope.

> **Superseded Revision 4 qualifier.** Re-checked as requested: **no new guard keyed on `APP_ENV` or `debug` was
> added this cycle.** The one new startup gate, `_validate_postgres_password` (`config.py:100-110`),
> is unconditional by design and is a working precedent for recommendation 1 here. Line references
> have drifted: the `APP_ENV` default is now `config.py:31`, the `SECRET_KEY` gate `config.py:66-80`,
> the auth-posture gate `main.py:42`. `.env.example` still ships `APP_ENV=development` with an empty
> `SECRET_KEY`, so this finding is unchanged in substance — and it now also disarms the new
> FINDING-020 ticket surface, because a forged token against an empty key mints monitor tickets too.

---

### FINDING-014: Twilio stream ticket is written to application logs in plaintext

**Severity:** Medium
**Exploitability:** Unlikely
**Confidence:** Confirmed
**Remediation Priority:** **P3**
**Source:** Manual review (Verify Mode, Revision 2)
**File:** `backend/app/api/twilio.py`
**Line:** `twilio.py:300-303`
**Category:** A09 Security Logging and Alerting Failures

**Description.** The `start`-frame handler logs the whole `customParameters` map at INFO level:

```python
logger.info(
    f"Twilio stream started: stream_sid={stream_sid}, "
    f"call_sid={call_sid}, params={custom_params}"
)
```

`customParameters` now carries the `ticket` JWT introduced for FINDING-003 (`twilio.py:256`), so a
live bearer credential signed with `settings.secret_key` is written verbatim to stdout and captured by
the Docker log driver. The logging happens **before** verification, so invalid and forged tickets are
recorded too. Impact is bounded by the 60-second TTL, but the ticket is replayable within that window
(no nonce store), and log retention outlives it.

**Impact.** Anyone with read access to container logs (any `docker logs` user, log shipper, or a
support bundle) can replay a captured ticket within 60 seconds to open a media-stream WebSocket for
that agent, creating a fabricated `Session` and consuming provider credits. Also a general hygiene
failure: credentials must not enter logs.

**Recommendation.**
1. Log only the parameter **names**, or an explicit allow-list (`agent_id`), never the values — e.g.
   `params={sorted(custom_params)}`.
2. If the ticket must be traceable, log a truncated SHA-256 digest of it, not the token.
3. Add the replay defence the docstring already claims: store the ticket `jti` in Redis with a
   60-second TTL and reject a second presentation.
4. Review the neighbouring INFO lines for the same pattern before they acquire credentials.

**Standard Reference:** OWASP Top 10 (2025) A09.
**Disposition:** **Open**

---

### FINDING-015: All rate limiting, lockout and login attribution key on the reverse proxy's IP address

**Severity:** Medium
**Exploitability:** Likely
**Confidence:** Confirmed
**Remediation Priority:** **P1** (cheap fix, directly weakens the FINDING-005 remediation)
**Source:** Manual review (Revision 3, arising from the remediation)
**File:** `backend/app/api/auth.py`, `backend/app/api/twilio.py`, `backend/app/rate_limit.py`, `docker/Caddyfile`
**Line:** `api/auth.py:63-64,111-112` · `api/twilio.py:208-212,305-309` · `docker/Caddyfile:5-18`
**Category:** A06 Insecure Design / A09 Security Logging and Alerting Failures / A10 Mishandling of Exceptional Conditions

**Description.** Every new control keys on `request.client.host` / `websocket.client.host`. In the
shipped topology all external traffic arrives through Caddy (`docker/Caddyfile:7-18` proxies `/api/*`
and `/ws/*` to `backend:8000`), so that value is Caddy's container address for every request. A
repository-wide search for `proxy_headers`, `forwarded_allow_ips` and `X-Forwarded-For` returns **no
matches** — the backend never consumes the forwarded client address, and uvicorn is not started with
`--proxy-headers`. Three consequences follow:

1. **Admin lockout is deployment-wide.** `identity = f"{client_ip}:{username}"` (`api/auth.py:112`)
   collapses to one value for the whole internet. Five failed `admin` logins from anyone lock the
   real operator out for 15 minutes (`rate_limit.py:40-42`), repeatable indefinitely.
2. **The Twilio limits become shared global budgets.** 60 webhook requests/60 s and 30 WebSocket
   connection attempts/60 s (`twilio.py:60-61`) apply to all callers at once, so any internet client
   can exhaust them and block genuine Twilio traffic — and a deployment with more than 30 calls
   starting in a minute rejects its own calls.
3. **Audit lines are unattributable.** `auth.login.failed ip=…` (`api/auth.py:129`) records the proxy
   address on every line, so the A09 gap FINDING-005 recommendation 4 set out to close is only
   half closed — failures are countable but not attributable.

Note the `--proxy-headers` fix must be paired with a trusted-proxy restriction; enabling it without
one lets a client set `X-Forwarded-For` freely and evade the limiter entirely.

**Impact.** Trivially repeatable denial of service against admin login and against inbound telephony,
plus loss of per-source attribution in the authentication audit trail.

**Recommendation.**
1. Run uvicorn with `--proxy-headers --forwarded-allow-ips=<caddy container IP/CIDR>` (or add Starlette's `ProxyHeadersMiddleware` with an explicit trusted-host list) and take the client address from the parsed result.
2. Ensure Caddy sets `X-Forwarded-For` and strips any inbound copy before proxying.
3. Add a global failure ceiling alongside the per-identity one so a distributed attempt is still bounded, and prefer a delay/backoff over a hard lockout for the single-operator identity to avoid the self-DoS shape.
4. Replace the Twilio WebSocket rate window with a genuine concurrency counter (increment after `accept()`, decrement in `finally`), which is what the "connection cap" comment at `twilio.py:301-304` claims.

**Standard Reference:** OWASP Top 10 (2025) A06, A09.
**Disposition:** **Open — partially fixed (Revision 5); core defect closed.**

> **Revision 5 verification.** Recommendations 1 and 2 implemented.
> `uvicorn.middleware.proxy_headers.ProxyHeadersMiddleware` is registered last, so outermost
> (`main.py:16,141`), with `trusted_hosts=settings.trusted_proxy_ips` (`config.py:294-296`, default
> `172.28.0.0/24`); `docker-compose.yml:128-137` pins `oasis_net` to that same subnet; both Caddy
> configs **overwrite** `X-Forwarded-For` with `{http.request.remote.host}` on the `/api/*` and
> `/ws/*` blocks (`docker/Caddyfile:47,59`, `docker/Caddyfile.dev:29,38`), discarding any client-sent
> copy. uvicorn 0.34's implementation takes the right-most untrusted hop and only acts when the TCP
> peer is trusted, which `tests/test_trusted_proxy.py:57-78` exercises in both directions. Lockout,
> Twilio limits and `auth.login.*` audit lines therefore key on the real client address.
>
> **Still Open (Medium)** on four points: recommendation 3 (global failure ceiling / backoff instead
> of a hard lockout) and recommendation 4 (true WebSocket concurrency counter) are untouched; the
> trusted range is the **entire** `oasis_net` subnet, so any container on it — not just Caddy — can
> forge `X-Forwarded-For`, and pinning the trust to Caddy's own address (or a dedicated proxy-only
> network) is the obvious tightening; `TRUSTED_PROXY_IPS` and the compose `subnet:` are independent
> literals that can drift apart with no start-up cross-check (drift fails safe but silently); and the
> new tests cover the `http` scope only — no test asserts that `/ws/twilio`'s
> `websocket.client.host` (`api/twilio.py:305`) is corrected.

> **Superseded Revision 4 qualifier.** Re-checked as requested: **no unguarded `X-Forwarded-For` trust was
> added.** `_client_ip` still returns `request.client.host` (`api/auth.py:73-74`) and a repository
> -wide grep for `proxy_headers`, `forwarded_allow_ips` and `X-Forwarded-For` still returns no
> matches. The Caddyfile reference in this finding moves to `docker/Caddyfile:19-63`. One new
> unthrottled surface was added — `POST /auth/monitor-ticket` and `POST /auth/logout`
> (`api/auth.py:197,214`) — but both require a valid token, so they do not widen the unauthenticated
> rate-limit gap described here.

---

### FINDING-016: Credential encryption is keyed on a possibly-empty `SECRET_KEY` and the decrypt path accepts unauthenticated plaintext

**Severity:** Medium
**Exploitability:** Possible
**Confidence:** Confirmed
**Remediation Priority:** **P2**
**Source:** Manual review (Revision 3, arising from the remediation)
**File:** `backend/app/crypto.py`, `backend/app/config.py`, `backend/app/api/settings.py`
**Line:** `crypto.py:27-30` (derivation) · `crypto.py:42-56` (fallback) · `config.py:27,61-75` · `api/settings.py:176,184,410`
**Category:** A04 Cryptographic Failures / A08 Software or Data Integrity Failures

**Description.** The FINDING-006 envelope encryption has three structural weaknesses.

1. **The KEK inherits FINDING-013.** `_fernet()` derives the key from `settings.secret_key` via
   HKDF-SHA256. The derivation itself is sound (distinct `info` label, so it is independent of the
   JWT use of the same key), but `config.py:61-75` only rejects an empty/placeholder/short
   `SECRET_KEY` when `app_env != "development"` — and `.env.example:10,15` ships
   `APP_ENV=development` with `SECRET_KEY=` empty. In that default posture the KEK is
   `HKDF(SHA256, ikm=b"", info=b"oasis-redis-settings-encryption-v1")`, a constant anyone can
   compute, so the stored provider credentials are effectively still plaintext to a Redis reader.
2. **The plaintext fallback removes Fernet's integrity guarantee.** `decrypt_secret` returns the raw
   stored bytes whenever they are not a valid token (`crypto.py:53-56`). The FINDING-006 threat model
   is an attacker with Redis access; such an attacker can therefore *write* an arbitrary plaintext
   value into `oasis:settings:api_keys` and have the application use it verbatim — e.g. substituting
   an attacker-controlled key. Fernet authenticates, but nothing requires values to be authenticated.
3. **Key rotation fails silently.** Rotating `SECRET_KEY` (which FINDING-002 remediation guidance
   invites after any token compromise) makes every stored token undecryptable; the fallback then
   returns the base64 ciphertext and the application sends *that* to the provider as an API key, and
   `GET /api/settings/keys` reports the field as configured (`api/settings.py:197-215`). The failure
   surfaces as confusing provider 401s rather than as an error.

**Impact.** In the shipped default posture the new encryption adds no confidentiality. In any
posture, an attacker who can write to Redis can substitute credentials and endpoints undetected, and
a legitimate key rotation silently corrupts the credential store.

**Recommendation.**
1. Require a strong `SECRET_KEY` (or a dedicated `SETTINGS_ENCRYPTION_KEY`) unconditionally whenever a value is encrypted — do not let the `development` exemption reach the KEK.
2. Store a version/marker prefix (e.g. `enc:v1:`) with each ciphertext. Treat an unmarked value as legacy plaintext **only** during an explicit, time-boxed migration, log each occurrence, and re-encrypt on read; reject unmarked values thereafter.
3. Fail loudly (log + 500 on the settings read path) when a marked value fails to decrypt, instead of returning the ciphertext as if it were the secret.
4. Derive with a per-deployment random salt persisted alongside the data, so two deployments sharing a `SECRET_KEY` do not share a KEK.

**Standard Reference:** OWASP Top 10 (2025) A04, A08.
**Disposition:** **Open**

> **Revision 5 qualifier.** Weakness 1 (**the empty/public KEK**) is **closed**: `_validate_secret_key`
> is now unconditional (`config.py:84-117`), so `HKDF(ikm=b"")` is unreachable in any environment and
> the KEK is always derived from a ≥32-character key. Weaknesses 2 (`decrypt_secret` returns
> unauthenticated raw bytes) and 3 (rotation silently corrupts the store) are untouched, so the
> finding stays **Open Medium**. New interaction: in `development` the ephemeral key changes on every
> restart, so weakness 3 now fires routinely — after a restart the stored ciphertext fails to decrypt
> and the fallback hands the base64 ciphertext to the provider as an API key. Recommendation 3 (fail
> loudly on a decrypt failure) is now the cheapest remaining fix and should be sequenced first.

> **Superseded Revision 4 qualifier.** Unchanged in substance; line references drift to `config.py:32` (the
> `secret_key` field) and `config.py:66-80` (the `app_env`-conditional gate). Note the same
> `SECRET_KEY` now also keys the monitor tickets (`auth.py:176`), widening the blast radius of the
> weak-key path by one more credential type.

---

### FINDING-017: `CORS_ALLOWED_ORIGINS` is passed through unvalidated, so `*` re-enables origin reflection with credentials

**Severity:** Low
**Exploitability:** Unlikely (requires an explicit operator misconfiguration)
**Confidence:** Confirmed
**Remediation Priority:** **P3**
**Source:** Manual review (Revision 3, arising from the remediation)
**File:** `backend/app/config.py`, `backend/app/main.py`
**Line:** `config.py:49-55` · `main.py:90-97`
**Category:** A02 Security Misconfiguration

**Description.** The FINDING-004 fix is correct for the empty default, but the parsed list is handed
straight to `CORSMiddleware` with `allow_credentials=True`. Starlette treats a list containing `"*"`
as `allow_all_origins` and then reflects the request `Origin` — so `CORS_ALLOWED_ORIGINS=*`, a
plausible "make it work" edit, reproduces FINDING-004 exactly. `null` and bare hostnames without a
scheme are likewise accepted without comment.

**Impact.** A single configuration edit silently restores drive-by cross-origin access to the admin
API with credentials.

**Recommendation.** Validate each entry in the `cors_allowed_origins` property: reject `*` and `null`
outright (raise at startup with a message pointing at this finding), and require each entry to parse
as `scheme://host[:port]` with `scheme in {http, https}` and no path.

**Standard Reference:** OWASP Top 10 (2025) A02.
**Disposition:** **Open**

> **Revision 4 qualifier.** Unchanged; references drift to `config.py:52-60` and `main.py:87-110`.
> Note that the new `MaxBodySizeMiddleware` is registered *after* `CORSMiddleware` (`main.py:126`),
> so it is outermost and its 413 responses carry no `Access-Control-Allow-*` headers.

---

### FINDING-018: `REDIS_PASSWORD` is exposed through container process arguments and compose metadata

**Severity:** Low
**Exploitability:** Unlikely (requires host or in-container access, which already implies other exposure)
**Confidence:** Confirmed
**Remediation Priority:** **P3**
**Source:** Manual review (Revision 3, arising from the remediation)
**File:** `docker-compose.yml`
**Line:** `docker-compose.yml:86-92` (`--requirepass`) · `docker-compose.yml:98` (`redis-cli -a`)
**Category:** A04 Cryptographic Failures / A02 Security Misconfiguration

**Description.** The new Redis password is supplied on the command line
(`redis-server --requirepass ${REDIS_PASSWORD…}`) and again in the healthcheck
(`redis-cli -a "${REDIS_PASSWORD}" --no-auth-warning ping`). Command lines are visible to every
process in the container's PID namespace, in `docker top`, in `docker inspect` output, in
`docker compose config`, and in the healthcheck record retained by the daemon. The `.env` file itself
is correctly `chmod 600` (`install.sh:214`), so this is the weaker link of the two.

To answer the specific concern raised at hand-off: the password also appears inside `REDIS_URL`
(`docker-compose.yml:47`), but redis-py does not echo the URL or the password in its exception
messages (`ConnectionError` carries host and port; `AuthenticationError` carries no credential), and
no log statement in the codebase prints `settings.redis_url`. The unauthenticated `/api/health`
exception disclosure is tracked separately as FINDING-019.

**Impact.** A low-privilege process inside the Redis container, or anyone who can read daemon
metadata, recovers the Redis password without reading `.env`.

**Recommendation.** Mount a `redis.conf` (mode 600) containing `requirepass` and start Redis with
`redis-server /usr/local/etc/redis/redis.conf`; use the `REDISCLI_AUTH` environment variable rather
than `-a` in the healthcheck. Longer term, prefer a Redis 6+ ACL user with a secret supplied through
a Docker/Compose secret rather than an environment variable.

**Standard Reference:** OWASP Top 10 (2025) A04, A02.
**Disposition:** **Open**

> **Revision 5 qualifier.** Re-checked as requested for new argv exposure in `install.sh` and compose:
> **no new plaintext secret reaches any command line.** The admin password is piped over **stdin**
> into the hashing container (`install.sh:234-239`); `docker run` carries no credential, so it is
> absent from `ps`, `docker top` and `docker inspect`. `docker-compose.yml` is unchanged on this axis
> (Redis `--requirepass` at `:105` and the `redis-cli -a` healthcheck at `:115` remain the finding).
> Two host-local additions worth recording under this finding: the installer already expands
> `SECRET_KEY`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD` and the OpenAI key onto the `sed` command line
> (`install.sh:207-217`), and the Argon2id hash now joins them (`install.sh:243`). Exposure is a
> one-shot, root-run, host-local `ps` window rather than persistent daemon metadata, so the severity
> stays **Low** — but `sed -i -f -` with the script on stdin, or `printf | sed`, removes it.

> **Superseded Revision 4 qualifier.** Re-checked as requested: **the Postgres password was not added to any
> container command line.** `docker-compose.yml:81` passes it as an environment variable only, which
> is the correct treatment. Line references for the Redis exposure drift to `docker-compose.yml:105`
> (`--requirepass`), `:115` (healthcheck `redis-cli -a`) and `:55` (`REDIS_URL`). A related argv
> exposure was introduced in documentation this cycle — see **FINDING-024**.

---

### FINDING-019: Unauthenticated `/api/health` returns raw dependency exception text

**Severity:** Low
**Exploitability:** Possible
**Confidence:** Confirmed
**Remediation Priority:** **P3**
**Source:** Manual review (Revision 3; pre-existing code, newly relevant because `REDIS_URL` now carries a credential)
**File:** `backend/app/main.py`
**Line:** `main.py:194-221` (`status["database"] = f"error: {exc}"` at 210, `status["redis"]` at 218)
**Category:** A02 Security Misconfiguration / A10 Mishandling of Exceptional Conditions

**Description.** `/api/health` is registered on the app with no auth dependency and returns the
stringified exception from the PostgreSQL and Redis probes to any caller. SQLAlchemy masks the
password in DSNs it renders and redis-py does not include credentials in its messages, so this is
**not** a credential disclosure today — but it does hand an unauthenticated caller internal hostnames,
ports, driver versions and failure modes, and it is one dependency-version change away from becoming
one.

**Impact.** Internal topology and stack-detail disclosure to any unauthenticated caller; assists
targeting of the other findings.

**Recommendation.** Return only `ok` / `error` per dependency to unauthenticated callers, log the
exception server-side at `warning`, and gate the detailed variant behind `require_auth`.

**Standard Reference:** OWASP Top 10 (2025) A02, A10.
**Disposition:** **Open**

> **Revision 4 qualifier.** Unchanged; the handler moves to `main.py:206-233` (`status["database"]`
> at `:222`, `status["redis"]` at `:230`).

---

### FINDING-020: A 60-second monitor ticket is accepted as a full admin bearer token, and can be chained indefinitely

**Severity:** High
**Exploitability:** Possible
**Confidence:** Confirmed
**Remediation Priority:** **P1** (small, self-contained fix inside the FINDING-008 code)
**Source:** Manual review (Revision 4, arising from the remediation)
**File:** `backend/app/auth.py`, `backend/app/api/auth.py`
**Line:** `auth.py:70-87` (`verify_token`) · `auth.py:160-176` (`create_monitor_ticket`) · `auth.py:139-155` (`require_valid_token`) · `api/auth.py:214-236`
**Category:** A01 Broken Access Control / A07 Authentication Failures

**Description.** The FINDING-008 remediation mints monitor tickets as JWTs signed with the **same
`settings.secret_key` and the same `HS256` algorithm** as admin access tokens, and distinguishes them
only by a `purpose` claim:

```python
payload = {"session_id": …, "purpose": "monitor_ws", "jti": …, "iat": …, "exp": now + 60}
return jwt.encode(payload, settings.secret_key, algorithm=_JWT_ALGORITHM)   # auth.py:168-176
```

`consume_monitor_ticket` checks `purpose` (`auth.py:194`), but `verify_token` does **not** — it
validates signature and expiry, checks the denylist, and returns the payload
(`auth.py:77-87`). `require_auth` treats any non-`None` payload as an authenticated caller
(`auth.py:128-136`) and never inspects `sub` or `purpose`. Three consequences follow:

1. **A monitor ticket is a valid `Authorization: Bearer` credential for every route behind
   `require_auth`** — all eight admin routers — for its full 60 seconds, with no single-use
   constraint on that path (the `SET NX` marker is only written by the WebSocket consumer).
2. **It is chainable.** `POST /api/auth/monitor-ticket` is guarded by `require_valid_token`, which is
   the same unconditional `verify_token` call (`auth.py:152`). A ticket can therefore be presented to
   mint a fresh ticket, repeatedly, converting one captured 60-second value into indefinite admin
   access without ever holding the operator's password or original token.
3. **The ticket travels in a URL** (`api/monitor.py:45`, `SessionDetailPage.tsx:176`), which is
   precisely the exposure channel — proxy logs, browser history, `Referer` — that FINDING-008 set out
   to close for the admin token. The window shrank from two hours to sixty seconds, which is a real
   improvement, but the value in that channel is no longer a monitor-scoped capability; it is an
   admin credential.

The ticket also carries no `sub`, so neither the mint nor the WebSocket connection is attributable to
an operator in the logs (`api/monitor.py:69`).

**Impact.** Anyone who can read a proxy access log, a browser history entry or a `Referer` header
within 60 seconds of a researcher opening a live-session view obtains the full admin API — every
study, agent, transcript, recording and provider credential — and can hold it indefinitely by
refreshing the ticket. This partially reverses the intent of the FINDING-008 remediation.

**Recommendation.**
1. Add a `typ`/`purpose` claim to access tokens (`typ: "access"`) and have `verify_token` reject any
   token whose `typ` is not `access`. Fail closed on a missing claim once existing tokens have aged
   out (2 hours), or reject immediately and accept one forced re-login.
2. Separately, refuse to mint a ticket from a ticket: `require_valid_token` should reject a payload
   carrying `purpose == "monitor_ws"`.
3. Derive a distinct signing key for tickets (e.g. `HKDF(secret_key, info=b"oasis-monitor-ticket")`),
   so a ticket is structurally incapable of being verified as an access token.
4. Bind the ticket to the requesting operator — copy `sub` into the ticket, log it at mint and at
   consume, and reject a ticket whose `sub` is no longer valid (e.g. its access token was revoked).
5. Consider `Sec-WebSocket-Protocol` rather than a query parameter, which removes the URL channel
   entirely.

**Standard Reference:** OWASP Top 10 (2025) A01, A07.
**Disposition:** **Fixed (Revision 5).**

> **Revision 5 verification.** Recommendations 1-4 implemented, and each was traced in code rather
> than accepted from the summary.
> 1. Access tokens carry `typ: "access"` (`auth.py:99`) and `verify_token` rejects anything else
>    (`auth.py:128-129`) — a pre-change token without the claim is rejected, forcing one re-login,
>    which is the stricter of the two options offered.
> 2. `verify_token` additionally rejects `purpose == "monitor_ws"` outright (`auth.py:130-131`), so
>    ticket-from-ticket minting via `require_valid_token` → `POST /auth/monitor-ticket` is closed.
> 3. Tickets are signed and verified with an HKDF-SHA256 key derived under a distinct label
>    (`auth.py:86-91`, used at `:235` and `:249`), so a ticket fails signature verification as an
>    access token regardless of its claims — the structural layer, independent of 1 and 2.
> 4. `sub` is bound to the minting operator (`auth.py:231-234`, from the caller's own token at
>    `api/auth.py:231`) and logged at both mint (`api/auth.py:232-234`) and consume
>    (`auth.py:269-275`), closing the attribution gap. Single use is still an atomic `SET NX`
>    (`auth.py:262-268`).
>
> Residuals, neither High: recommendation 5 is not done — the ticket still travels in the URL query
> string, which remains a **FINDING-008** residual, now carrying a 60-second, single-use,
> session-scoped capability instead of an admin credential. And the hardening is asymmetric: the
> **Twilio** stream ticket (`api/twilio.py:103-129`) is still signed with the raw `settings.secret_key`.
> Cross-acceptance was traced in both directions and is blocked by claim checks (an access token has
> no `purpose`/`agent_id`; a stream ticket has no `typ`), but that path deserves the same HKDF
> treatment so the separation is structural there too.

---

### FINDING-021: Known-vulnerable `starlette` and `python-multipart` remain unpatched on the upload path

**Severity:** High
**Exploitability:** Possible
**Confidence:** **Needs verification** (advisory identifiers are Developer-reported `pip-audit` output; the pinned versions are confirmed, the advisories were not independently re-run — no Dependabot/MCP this session)
**Remediation Priority:** **P1**
**Source:** Developer-reported `pip-audit` (carried forward from FINDING-009 recommendation 6)
**File:** `backend/requirements.txt`
**Line:** `requirements.txt:2` (`fastapi==0.115.6`, which resolves `starlette 0.41.3`) · `requirements.txt:5` (`python-multipart==0.0.20`)
**Category:** A03 Software Supply Chain Failures / A10 Mishandling of Exceptional Conditions

**Description.** FINDING-009 recommendation 6 flagged the Starlette multipart-DoS advisory class as
`Needs verification`. The Developer has now run `pip-audit` and reports four hits —
`PYSEC-2026-1941`, `PYSEC-2026-1942` against `starlette 0.41.3` and `PYSEC-2026-3037`,
`PYSEC-2026-3038` against `python-multipart 0.0.20` — and did **not** bump either package in this
cycle. The pinned versions were confirmed by reading `requirements.txt`; `starlette` is not pinned
directly, it arrives transitively through `fastapi==0.115.6`.

These advisories sit on exactly the code path FINDING-009 was written about: the multipart parser
that runs **before** the endpoint's own streaming size check, inside the same event loop that runs
every live interview pipeline. The new 10 MiB middleware bounds total body size but does not protect
against a parser-level algorithmic or part-count defect within that budget.

**Impact.** A remote request within the accepted size budget may stall or exhaust the single backend
process, taking down the admin API and every in-flight voice and text interview — the same blast
radius as FINDING-009, reachable despite that finding's controls.

**Recommendation.**
1. Upgrade `fastapi` to a release that pulls a fixed `starlette`, and pin `starlette` explicitly so
   the resolved version is visible in the lock surface rather than implied.
2. Upgrade `python-multipart` to the fixed release; re-run `pip-audit` and record the clean output in
   the PR.
3. Re-run the FINDING-009 upload tests after the bump — the streaming read depends on
   `UploadFile.read(size)` semantics.
4. Make `pip-audit` blocking in CI (FINDING-012 recommendation 4) so this class cannot recur
   silently, and enable Dependabot so the advisory identifiers can be confirmed independently.

**Standard Reference:** OWASP Top 10 (2025) A03, A10.
**Disposition:** **Open — partially fixed (Revision 5).**

> **Revision 5 verification.** Recommendations 1 and 2 are implemented as pins:
> `requirements.txt:11-15` now reads `fastapi==0.128.0`, `starlette==0.50.0` (explicit, so the
> resolved version is visible on the lock surface — the Revision 4 ask) and
> `python-multipart==0.0.32`. Recommendation 3 is Developer-reported as done (513 tests pass) and
> recommendation 4 (blocking `pip-audit` in CI, Dependabot) is **not** done — it remains inside
> FINDING-012.
>
> **Remains Open High.** The Developer's own `pip-audit` output reports five further `starlette`
> advisories still present on `0.50.0` — `PYSEC-2026-161`, `-2280`, `-2281`, `-248`, `-249` —
> requiring `starlette>=1.0.1` with `fastapi>=0.141`. That upgrade is blocked by the version chosen
> here: `fastapi==0.128.0` constrains `starlette<0.51.0`, so the bump has to be re-planned as a pair
> against `pipecat-ai==1.4.0`'s `fastapi<1,>=0.115.6` (which does admit `0.141`). Until then the
> multipart/upload path is still running known-vulnerable code, which is the exact condition this
> finding records. Confidence stays **Needs verification**: no Dependabot, no MCP and no offline
> package tree this session, so neither the cleared nor the remaining advisories were independently
> re-run — the pinned versions are the only part confirmed by reading.
>
> Related verification note (not a finding): the `0.115 → 0.128` / `0.41 → 0.50` jump was checked for
> default changes that could disturb FINDING-009's controls. The 413 path is raw-ASGI
> (`middleware.py:25-91`) and does not depend on framework exception handling, and the form-parser
> limits that could interact with `api/knowledge.py`'s 2 MiB cap already existed in `starlette 0.41.3`.
> An explicit ~1.5 MiB upload test and a 413 test would confirm this cheaply.

---

### FINDING-022: The participant widget is framable by any origin, with no documented embedder allow-list

**Severity:** Low
**Exploitability:** Possible
**Confidence:** Confirmed
**Remediation Priority:** **P3**
**Source:** Manual review (Revision 4, arising from the remediation)
**File:** `docker/Caddyfile`
**Line:** `Caddyfile:51-56`
**Category:** A02 Security Misconfiguration / A06 Insecure Design

**Description.** The new CSP deliberately omits `frame-ancestors` on `/interview/*` because the
widget is embedded in third-party survey tools. The decision is legitimate and is documented
(`docs/DEPLOYMENT.md:751`), but it is implemented as "any origin may frame it", not as an allow-list.
The widget requests microphone access and collects participant PII, so an arbitrary embedder can
present it under its own branding, overlay or crop it, and collect interviews under a pretext the
participant never consented to. Mitigating factors: the widget is keyed by `widget_key`, which is
128-bit and only known to the intended embedder; the `Permissions-Policy: microphone=(self)` response
header (`Caddyfile:28`) still requires the embedder to delegate the microphone explicitly via
`allow="microphone"`, and the browser still prompts the participant.

**Impact.** Clickjacking / brand-impersonation risk against participants, and no technical control
tying a study's widget to its intended host.

**Recommendation.** Make the embedder set explicit: add a per-deployment
`WIDGET_FRAME_ANCESTORS` variable rendered into a `frame-ancestors` directive on `/interview/*`
(defaulting to `'self'`, with the operator adding the survey-tool origins they actually use), and
record the configured embedders in the study's documentation. If per-agent granularity is wanted
later, the widget config endpoint already has the agent record to carry it.

**Standard Reference:** OWASP Top 10 (2025) A02, A06.
**Disposition:** **Open**

---

### FINDING-023: `CADDY_CONFIG_FILE` can silently select the plaintext proxy in production

**Severity:** Low
**Exploitability:** Unlikely (requires an operator to carry a development `.env` forward)
**Confidence:** Confirmed
**Remediation Priority:** **P3**
**Source:** Manual review (Revision 4, arising from the remediation)
**File:** `docker-compose.yml`, `docker/Caddyfile.dev`, `docs/DEPLOYMENT.md`
**Line:** `docker-compose.yml:13-18` · `Caddyfile.dev:1-19` · `docs/DEPLOYMENT.md:757-759`
**Category:** A02 Security Misconfiguration

**Description.** The plaintext `:80` proxy is correctly non-default (`${CADDY_CONFIG_FILE:-./docker/
Caddyfile}`) and is documented as development-only in three places. Nothing, however, *enforces*
that: a `.env` copied from a developer machine to a server, or an operator who sets the variable to
work around a TLS problem, gets a stack that serves admin logins, JWTs, monitor tickets and
participant transcripts in cleartext with no warning at start-up. The dev file also drops HSTS and
CSP entirely, so the FINDING-010 header set is lost along with the TLS. The backend has no visibility
of the choice, so its own start-up posture check (`main.py:33-53`) cannot object.

Two stale sentences in `docs/DEPLOYMENT.md:320` and `:652` still describe the removed
"patches the Caddyfile" behaviour, which will mislead an operator debugging the new mechanism.

**Impact.** A single stray environment variable silently reverts the FINDING-010 remediation on a
production deployment.

**Recommendation.**
1. Have the backend refuse to start, or log a prominent warning, when `CADDY_CONFIG_FILE` is set to
   the dev file while `APP_ENV != development` — pass the variable into the backend's environment so
   the existing posture check can cover it.
2. Bind the dev proxy to loopback only (`127.0.0.1:80:80`) in a `docker-compose.dev.yml` override
   rather than reusing the production port mapping.
3. Keep `CADDY_CONFIG_FILE` out of `.env.example` (it currently is — preserve that) and document it
   only in the development section.
4. Correct `docs/DEPLOYMENT.md:320` and `:652`.

**Standard Reference:** OWASP Top 10 (2025) A02.
**Disposition:** **Open**

---

### FINDING-024: The documented Postgres password-rotation runbook places the new password on the process argv

**Severity:** Low
**Exploitability:** Unlikely (requires local or in-container access at the moment of rotation)
**Confidence:** Confirmed
**Remediation Priority:** **P3**
**Source:** Manual review (Revision 4, arising from the remediation)
**File:** `docs/DEPLOYMENT.md`
**Line:** `DEPLOYMENT.md:410-414`
**Category:** A04 Cryptographic Failures / A09 Security Logging and Alerting Failures

**Description.** The new rotation runbook expands the freshly generated password into two command
lines:

```
sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$NEW_PW|" .env
docker compose exec postgres psql -U … -c "ALTER USER … WITH PASSWORD '<expanded>';"
```

Both are visible in `ps`/`/proc` to any local user for the life of the process, the `psql` invocation
is additionally visible inside the container's PID namespace and in `docker inspect` exec metadata,
and `ALTER USER … WITH PASSWORD` is written verbatim to the PostgreSQL server log whenever statement
logging is enabled (and always to `psql`'s own history when run interactively). This is the same
class as FINDING-018, introduced in documentation rather than code, and it fires at exactly the
moment the operator is trying to recover from a suspected credential compromise.

**Impact.** The replacement credential can be recovered by a local unprivileged process or from the
database log immediately after rotation, defeating the rotation.

**Recommendation.** Rewrite the snippet to keep the value off the command line: use `psql`'s
interactive `\password <user>` meta-command (which sends a pre-hashed `ALTER USER` and never echoes),
or pipe the statement in on stdin via a here-document with `psql -v ON_ERROR_STOP=1`; write the
`.env` change with a redirect or `python -c` reading from stdin rather than `sed -i` with an expanded
variable; and tell the operator to confirm `log_statement` is not `all` during rotation.

**Standard Reference:** OWASP Top 10 (2025) A04, A09.
**Disposition:** **Open**

---

### FINDING-025: A start-up configuration failure may print the whole `Settings` object, including `SECRET_KEY`, to the logs

**Severity:** Low
**Exploitability:** Unlikely
**Confidence:** **Probable** (mechanism read in code; the exact rendering of a pydantic v2 model-level validator error was not executed)
**Remediation Priority:** **P3**
**Source:** Manual review (Revision 4, arising from the remediation)
**File:** `backend/app/config.py`
**Line:** `config.py:66-80`, `config.py:100-110`, `config.py:229` (`settings = Settings()`)
**Category:** A09 Security Logging and Alerting Failures / A02 Security Misconfiguration

**Description.** Both start-up gates are `@model_validator(mode="after")` functions that raise
`ValueError`. Pydantic wraps such a failure in a `ValidationError` whose rendered message includes the
validator's input — for an `after` validator that input is the **constructed `Settings` instance**,
whose `repr` contains every field, among them `secret_key`, `openai_api_key`, `twilio_auth_token` and
the other provider credentials. Because `Settings()` is instantiated at module import
(`config.py:229`), that traceback is printed to stdout and captured by the Docker log driver on every
failed start. The new unconditional Postgres validator makes this path considerably easier to hit —
it now fires in development, and on any deployment that forgets the variable, which is the intended
behaviour of FINDING-011.

**Impact.** Provider API keys and the JWT signing key may be written in cleartext to container logs
and to any log shipper, triggered by a benign misconfiguration rather than an attack.

**Recommendation.**
1. Move both checks out of the pydantic validators into an explicit start-up function that raises a
   plain `RuntimeError` with a hand-written message naming only the offending variable — the same
   shape as `enforce_auth_posture` (`main.py:33-53`).
2. Alternatively, type the credential fields as `pydantic.SecretStr` (whose `repr` is `**********`)
   and/or set `Field(repr=False)` on them, which also protects any other accidental `repr` of
   `settings`.
3. Confirm the current behaviour first with one deliberate failed start (`POSTGRES_PASSWORD=` unset)
   and check what `docker compose logs backend` actually contains.

**Standard Reference:** OWASP Top 10 (2025) A09, A02.
**Disposition:** **Open**

> **Revision 5 qualifier.** Checked as requested: **the new validator messages contain no field
> values** — `config.py:101-109` (development warning) and `config.py:112-117` (production raise) name
> only the variable and the remedy, and no code path logs `settings`, a `Settings` repr, or
> `settings.secret_key`. The finding is unchanged because the leak mechanism is pydantic's own
> `ValidationError` rendering of the validator input, not the message text. Net reachability is
> roughly unchanged: the development branch no longer raises (one fewer trigger), but the key check
> now fires in *every* other environment where it previously did not. Recommendation 2
> (`SecretStr` / `Field(repr=False)` on the credential fields) is the low-cost fix and is now the
> only remaining exposure of the ephemeral development key.

---

### FINDING-026: No migration path off the plaintext `AUTH_PASSWORD`, and the installer prints the generated password to stdout

**Severity:** Low
**Exploitability:** Unlikely (requires access to an existing `.env`, or to a captured installer transcript)
**Confidence:** Confirmed
**Remediation Priority:** **P3**
**Source:** Manual review (Revision 5, arising from the FINDING-005 remediation)
**File:** `scripts/install.sh`, `docs/DEPLOYMENT.md`, `.env.example`
**Line:** `install.sh:193` · `docs/DEPLOYMENT.md` (no `AUTH_PASSWORD_HASH` section — grep returns zero matches) · `.env.example:143-145`
**Category:** A07 Authentication Failures / A02 Security Misconfiguration

**Description.** The FINDING-005 remediation makes Argon2id the default for **fresh** installs only.
Three gaps remain around it.

1. **No migration for existing installs.** Every deployment installed before this change keeps a
   plaintext `AUTH_PASSWORD` in `.env`, and the application keeps honouring it
   (`api/auth.py:58-66`) with nothing but a log warning. `docs/DEPLOYMENT.md` contains no
   `AUTH_PASSWORD_HASH` section and no "how to hash your existing password" runbook, so the
   plaintext credential persists indefinitely on exactly the installs FINDING-005 was written about.
2. **The generated password is echoed to stdout.** `install.sh:193`
   (`log "Generated admin password: $ADMIN_PASS"`) writes it to terminal scrollback and to any
   `tee`, `script` or CI capture of the installer run — the one place a cleartext copy still lands.
   The OpenAI key on the same screen is correctly masked (`install.sh:182`).
3. **Three new security-relevant variables are undocumented.** `AUTH_PASSWORD_HASH`,
   `TRUSTED_PROXY_IPS` (FINDING-015) and `EGRESS_ALLOWED_PRIVATE_HOSTS` (FINDING-007) appear in
   `.env.example` but nowhere in `docs/DEPLOYMENT.md`, so an operator who changes the compose subnet
   or runs a self-hosted provider has no guidance and is likely to widen them.

**Impact.** Upgraded deployments keep a recoverable cleartext admin credential on disk; a captured
installer transcript yields the admin password; and the two new allow-lists are likely to be widened
blindly, weakening the FINDING-007 and FINDING-015 fixes.

**Recommendation.**
1. Add a `docs/DEPLOYMENT.md` migration runbook: hash the existing password with the same
   stdin-piped one-liner the installer uses, set `AUTH_PASSWORD_HASH`, delete `AUTH_PASSWORD`,
   restart. Give the plaintext path a removal release.
2. Make the warning at `api/auth.py:59-63` fire once at start-up too, not only on login, so it is
   visible without a login attempt.
3. Stop echoing the generated password: write it to a mode-600 file the operator must read and
   delete, or require the operator to choose one.
4. Document `TRUSTED_PROXY_IPS` (and its coupling to the compose subnet) and
   `EGRESS_ALLOWED_PRIVATE_HOSTS` with explicit "do not widen" guidance.

**Standard Reference:** OWASP Top 10 (2025) A07, A02.
**Disposition:** **Open**

---

## Remediation Priority and Sequence

Severity reflects impact alone. **Remediation Priority** below is derived from exploitability,
reachability from the internet, and confidence — it is a scheduling aid, not a re-rating.

| Finding | Severity | Exploitability | Confidence | Priority |
|---|---|---|---|---|
| ~~FINDING-001 Auth disabled by default~~ | Critical | Likely | Confirmed | **Fixed rev 2** |
| ~~FINDING-002 Placeholder `SECRET_KEY` accepted~~ | Critical | Likely | Confirmed | **Fixed rev 2** |
| ~~FINDING-003 Twilio endpoints unauthenticated~~ | High | Likely | Confirmed | **Fixed rev 2** |
| ~~FINDING-013 `APP_ENV=development` disarms both new guards~~ | Critical | Possible | Confirmed | **Fixed rev 5** |
| ~~FINDING-004 CORS reflects any origin with credentials~~ | High | Likely | Confirmed | **Fixed rev 3** |
| ~~FINDING-005 Plaintext credential compare, no throttling~~ | High | Likely | Confirmed | **Fixed rev 5** |
| ~~FINDING-009 Unbounded upload read~~ | High | Likely | Confirmed | **Fixed rev 4** |
| ~~FINDING-010 Plain HTTP default, no security headers~~ | High | Possible | Confirmed | **Fixed rev 4** |
| ~~FINDING-011 Postgres default password~~ | High | Possible | Confirmed | **Fixed rev 4** |
| ~~FINDING-020 Monitor ticket accepted as an admin bearer token~~ | High | Possible | Confirmed | **Fixed rev 5** |
| **FINDING-021 `starlette` advisories remain after the bump** | High | Possible | Needs verification | **P1 (partially fixed rev 5)** |
| FINDING-006 Redis unauthenticated, plaintext keys | High | Possible | Confirmed | **P2** |
| FINDING-007 Writable provider endpoint URLs (redirect/rebinding residual) | High | Possible | Confirmed | **P2 (partially fixed rev 5)** |
| FINDING-008 No refresh rotation, token in `localStorage` (partially fixed rev 4) | High | Possible | Confirmed | **P2** |
| FINDING-012 CI permissions, tag pinning, non-blocking audits | High | Unlikely | Confirmed | **P3** |
| FINDING-014 Stream ticket logged in plaintext | Medium | Unlikely | Confirmed | **P3 (new rev 2)** |
| FINDING-022 Widget framable by any origin | Low | Possible | Confirmed | **P3 (new rev 4)** |
| FINDING-023 `CADDY_CONFIG_FILE` selects plaintext proxy | Low | Unlikely | Confirmed | **P3 (new rev 4)** |
| FINDING-024 Rotation runbook puts password on argv | Low | Unlikely | Confirmed | **P3 (new rev 4)** |
| FINDING-025 Config failure may log `SECRET_KEY` | Low | Unlikely | Probable | **P3 (new rev 4)** |
| FINDING-015 Rate limiting keyed on the proxy IP (core fixed rev 5) | Medium | Likely | Confirmed | **P3 (residual)** |
| FINDING-016 KEK / unauthenticated decrypt fallback (half closed rev 5) | Medium | Possible | Confirmed | **P2 (residual)** |
| FINDING-026 No migration off plaintext `AUTH_PASSWORD`; installer echoes it | Low | Unlikely | Confirmed | **P3 (new rev 5)** |

### Revision 5 sequence

1. **FINDING-021 is now the only P1** and the sole blocker created by this cycle: re-plan the
   `fastapi`/`starlette` pair so `starlette>=1.0.1` is reachable, re-run `pip-audit`, and record the
   output. Nothing else in the queue is a one-step fix.
2. **FINDING-007's redirect residual** — set `follow_redirects=False` (or pin the resolved address)
   on the `pipeline/runner.py` and `api/text_chat.py` clients, matching what `providers/smoke.py`
   already does. Small, and it closes the last guard bypass.
3. **FINDING-006, then FINDING-008** — the two remaining Open Highs that are deliberate pieces of
   work rather than hotfixes; unchanged in shape from Revision 1's sequence.
4. **FINDING-012** — blocking `pip-audit` in CI is a prerequisite for FINDING-021 not recurring.
5. Cheap hardening worth folding into any of the above: memoise the development ephemeral key
   (FINDING-013 residual), give the Twilio stream ticket the same HKDF key separation the monitor
   ticket now has (FINDING-020 residual), and add a `websocket`-scope proxy-headers test
   (FINDING-015 residual).

### Revision 4 sequence

1. **FINDING-020 first** — it is the only new High that is fully within the Developer's control today
   and it partially reverses a fix just shipped: reject non-`access` token types in `verify_token`
   and refuse ticket-from-ticket minting. A few lines in `auth.py`.
2. **FINDING-021** — a dependency bump plus a re-run of `pip-audit`; it closes the last residual of
   the FINDING-009 work.
3. **FINDING-013 remains the top of the queue overall** — it is the only Open Critical, and it now
   also disarms the new ticket surface.
4. FINDING-008's remaining recommendations (refresh rotation, `HttpOnly` cookie) stay scheduled as
   deliberate work, not a hotfix, as in Revision 1's sequence.

### Revision 2 sequence

0. **FINDING-013 first** — it is a two-line change (`.env.example:10` → `APP_ENV=production`, plus an
   unconditional empty/placeholder key rejection in `config.py`) and until it lands, the completed
   FINDING-001 / FINDING-002 / FINDING-003 fixes are conditional on operator configuration. Steps 2-8
   below are otherwise unchanged; steps 1 and 3 are done.

### Ordered remediation sequence (Revision 1 — steps 1 and 3 now complete)

1. ~~**Close the front door first — FINDING-002, then FINDING-001.**~~ **Done in Revision 2.** Order mattered: flipping
   `auth_enabled` to `True` achieves nothing while the published signing key still mints valid admin
   tokens. Refuse to start on the placeholder `SECRET_KEY`, *then* default auth on and remove the
   "token for any credentials" branch.
2. **FINDING-004 and FINDING-010 together** — both are single-file configuration changes
   (`main.py`, `docker/Caddyfile`) that shrink the remotely reachable surface immediately: stop
   reflecting arbitrary origins, stop serving admin traffic over plaintext, add the header set.
3. ~~**FINDING-003** — add Twilio signature validation and a signed stream ticket.~~ **Done in Revision 2**
   (`twilio.py:76-91,205-210,237-243,321-333`); rate limiting on that path remains with FINDING-005.
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

- `.env.example` contains **placeholders only** — every credential field is an empty assignment. ~~The two non-empty values, `SECRET_KEY=change-me-to-a-random-secret-key` (line 11) and `POSTGRES_PASSWORD=change-me` (line 16)~~ **Revision 2:** `SECRET_KEY` is now an empty assignment (`.env.example:15`); `POSTGRES_PASSWORD=change-me` (line 20) remains an insecure default (FINDING-011). The empty `SECRET_KEY` is *not* a safe default in `development` — see FINDING-013.
- **Revision 2 re-scan of the 13 changed files:** no live secrets. `config.py:13` holds the placeholder literal as a named constant used only for rejection; `tests/conftest.py:38,45` use obviously-fake fixtures (`test-secret-key…`, `scw-test-fake-key`). One credential-in-log defect found: the Twilio stream ticket at `twilio.py:300-303` → FINDING-014.
- Both workflows use obviously-fake CI values (`sk-test-fake-ci-key`, `ci-test-secret-key`, `POSTGRES_PASSWORD: test`). Not findings.
- `.gitignore` correctly excludes `.env`, `.env.local`, `.env.*.local` (lines 2-4), `data/recordings/` (line 47), `pgdata/` (line 44) and `dump.rdb` (line 50). It does **not** exclude `*.pem`, `*.key`, `*.pfx` or `*.p12` — no such files exist today, but adding the patterns is cheap insurance. Deferred to Phase 2 as a Low item.
- `scripts/install.sh:190` **prints a generated admin password to stdout** (`log "Generated admin password: $ADMIN_PASS"`). It lands in terminal scrollback and in any session transcript or CI log capturing the installer. `install.sh:179-180` correctly masks the OpenAI key instead. Deferred to Phase 2 as a Medium item.
- **Revision 4 re-scan of the changed files:** no live secrets. `.env.example:35` is now an empty
  `POSTGRES_PASSWORD=` assignment; `config.py:13,19` hold the two placeholder literals as
  rejection-only constants; `tests/conftest.py:35,38` use obviously-fake fixtures. Two
  credential-handling defects found in the new material, both recorded as findings rather than as
  secrets: the rotation runbook expands a live password onto the command line
  (`docs/DEPLOYMENT.md:410-414` → FINDING-024) and a start-up validation failure may print the whole
  `Settings` repr (`config.py:66-80,100-110` → FINDING-025). No private-key material, vendor
  credential, cloud identifier or PII appeared in any changed file.
- **Revision 5 re-scan of the changed files:** no live secrets. `.env.example` remains
  placeholder-only and now ships `APP_ENV=production`, `SECRET_KEY=`, `AUTH_PASSWORD_HASH=`,
  `EGRESS_ALLOWED_PRIVATE_HOSTS=` and `TRUSTED_PROXY_IPS=172.28.0.0/24` (a private RFC1918 range, not
  a secret). No PEM block, vendor credential, cloud identifier, live JWT or PII appeared in
  `config.py`, `auth.py`, `api/auth.py`, `egress_guard.py`, `main.py`, `requirements.txt`,
  `docker-compose.yml`, either Caddyfile or `install.sh`. The ephemeral development key
  (`config.py:100`) is generated in-process and never written or logged. The installer's stdout echo
  of a generated admin password (`install.sh:193`), previously deferred as a Phase 2 item, is now
  raised as **FINDING-026**.
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
| Admin REST (8 routers) | JWT Bearer | `Depends(require_auth)` at `api/router.py:27-34` | Correct in shape; ~~fails open on one flag~~ **rev 2:** the flag now defaults on and startup refuses it off — but only when `APP_ENV != "development"` (FINDING-013) |
| Public REST | none | by design | As documented. `/api/health` still returns raw exception strings (`main.py:206-233`) — FINDING-019 |
| Participant WS | `widget_key` possession | Agent lookup + `status=active`; `predefined` mode also needs an unused `ParticipantIdentifier` (`interviews.py:139-163`) | Capability model is coherent. `widget_key` is `secrets.token_urlsafe(16)` — 128 bits, **verified adequate** (`models/agent.py:46-47,146-151`) |
| Twilio | ~~none~~ **rev 2:** `X-Twilio-Signature` + 60 s stream ticket | `twilio.py:205-210` (webhook), `twilio.py:321-333` (WS) | ~~**Broken**~~ **Closed in rev 2** — fails closed on unset `TWILIO_AUTH_TOKEN`; ticket replayable for 60 s and logged (FINDING-014) |
| Monitor WS | ~~JWT via `?token=`~~ **rev 4:** 60 s single-use ticket via `?ticket=`, rejected before `accept()` | ~~`monitor.py:47-56`~~ **rev 4:** `monitor.py:58-66`, `auth.py:179-210` | Correct ordering; unconditional since rev 2; ticket is single-use (Redis `SET NX`) and fails closed when Redis is down. Bound to `session_id` but not to a user, still travels in a URL, and is accepted as a general admin bearer token — FINDING-020. Admin token storage residual — FINDING-008 |

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
   - `/api/health` returns raw exception strings to unauthenticated callers (`main.py:206-233`) — now tracked as FINDING-019.
   - **WebSocket frame sizes are uncapped** on `/ws/chat/*` and `/ws/interview/*`. `MaxBodySizeMiddleware` deliberately passes non-HTTP scopes through (`middleware.py:44-46`), so the FINDING-009 body cap does not reach the participant planes, which are unauthenticated by design.
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

**FAIL (Revision 5).** Five Open findings meet the FAIL threshold: **0 Critical and 5 High
(FINDING-006, 007, 008, 012, 021)**. Also Open but not verdict-determining: 3 Medium (FINDING-014,
015, 016) and 8 Low (FINDING-017, 018, 019, 022, 023, 024, 025, 026).

The last Open Critical, **FINDING-013**, is Fixed — the `SECRET_KEY` gate is now unconditional and
`.env.example` ships `APP_ENV=production`, so the published-constant signing key is unreachable in
every environment. **FINDING-005** and **FINDING-020** are Fixed on evidence read in full.
**FINDING-021 alone would hold the verdict at FAIL**: the bump cleared the four cited advisories but
the Developer's own audit reports five further `starlette` advisories that `0.50.0` does not fix, and
the chosen `fastapi==0.128.0` pin blocks the `starlette>=1.0.1` upgrade that would. Its Confidence
stays `Needs verification` and that qualifier was **not** used to lower severity or to move it out of
the FAIL set. **FINDING-007** keeps its High because a real guard bypass remains (30x redirects and
no address pinning on the `runner.py` / `text_chat.py` request paths); the two residuals that were
closed are recorded rather than used to re-rate it. **FINDING-015** stays Medium/Open on residuals
even though its core defect is closed, and **FINDING-016** stays Medium/Open with one of its three
weaknesses closed. No severity was downgraded to reach a verdict, no partial remediation was marked
Fixed, and no risk was accepted on the user's behalf.

**Historical rationale (Revision 4).** Eight Open findings met the FAIL threshold: **1 Critical (FINDING-013) and 7
High (FINDING-005, 006, 007, 008, 012, 020, 021)**. Also Open but not verdict-determining:
3 Medium (FINDING-014, 015, 016) and 7 Low (FINDING-017, 018, 019, 022, 023, 024, 025).

FINDING-009, FINDING-010 and FINDING-011 moved to **Fixed** this cycle on evidence read in full.
FINDING-008 was **not** marked Fixed: two of its five recommendations are outstanding and the
2-hour admin token still lives in `localStorage`. FINDING-020 is rated High on impact alone — a
60-second monitor ticket is accepted as an admin bearer token and can be chained — and no severity
was lowered because the ticket's window is short; that is exploitability, which is recorded
separately as `Possible`. FINDING-021 is High with Confidence `Needs verification`: the pinned
versions are confirmed, the advisory identifiers are Developer-reported and could not be checked
against Dependabot this session. Neither the confidence qualifier nor the short exposure window was
used to move a finding below the FAIL threshold.

**Historical rationale (Revision 3).** Nine Open findings met the threshold: 1 Critical
(FINDING-013) and 8 High (FINDING-005, 006, 007, 008, 009, 010, 011, 012), with 3 Medium and 3 Low
also Open.

FINDING-013 alone is unconditional FAIL. It is also the reason three of this cycle's remediations
under-deliver in the shipped posture: the `development` exemption that lets `SECRET_KEY` be empty now
also governs the credential-encryption KEK (FINDING-016). Fixing FINDING-013 raises the value of the
FINDING-006 work without any further change to it.

No severity was downgraded to move the verdict, and no Open High was marked Fixed on the strength of
a partial remediation — FINDING-005, 006 and 007 each retain a named, evidenced residual.

**Historical rationale (Revisions 1-2, both Criticals now Fixed).** The two original Critical findings compounded rather than merely coexisted. FINDING-001 meant the default
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

Please review the Revision 5 remediation status above. The FAIL verdict stands — on 5 Open High
findings, with **no Open Critical for the first time** — so the code returns to the Developer before
CI setup (Gate G7).

Highest-value next steps, in order: **FINDING-021** (re-plan the `fastapi`/`starlette` pair so
`starlette>=1.0.1` is reachable; re-run `pip-audit` and record the output — the only P1 left) →
**FINDING-007 residual** (`follow_redirects=False` / resolved-address pinning on `pipeline/runner.py`
and `api/text_chat.py`) → **FINDING-006** and **FINDING-008** (deliberate work, not hotfixes) →
**FINDING-012** (blocking `pip-audit` in CI, so FINDING-021 cannot recur silently). Cheap hardening
to fold in: memoise the development ephemeral key at module scope, give the Twilio stream ticket the
same HKDF key separation the monitor ticket now has, add a `websocket`-scope proxy-headers test, and
cross-check `TRUSTED_PROXY_IPS` against the compose subnet at start-up.

**Superseded Revision 4 next steps:** **FINDING-020** (reject non-`access` token types in
`verify_token`; refuse ticket-from-ticket minting — a few lines, and it restores the intent of the
FINDING-008 fix just shipped) → **FINDING-013** (drop the `development` exemption, or at least exempt
only the auth posture and never the encryption KEK) → **FINDING-021** (bump `starlette` /
`python-multipart`, re-run `pip-audit`) → **FINDING-005 residual** (generate `AUTH_PASSWORD_HASH` in
`install.sh`, add it to `.env.example`, retire plaintext `AUTH_PASSWORD`) → **FINDING-015**
(trusted-proxy client IP) → **FINDING-007 residual** (validate `audio_s3_endpoint_url`; constrain the
private-address allowance to an explicit host allow-list).

Three checks worth running before the next Verify cycle, each cheap and each closing an open
question in this revision: one end-to-end chunked POST to a knowledge upload asserting **413** (not
500); one deliberate failed start with `POSTGRES_PASSWORD` unset, checking what
`docker compose logs backend` prints (FINDING-025); and one smoke test of the live-session monitor
view under the new CSP, to confirm `connect-src 'self'` permits the same-origin WebSocket in the
browsers you support.

Two things to decide before remediation starts:

1. Confirm the **remediation sequence** above, in particular that FINDING-002 is fixed before or with
   FINDING-001 — fixing FINDING-001 alone provides no real protection.
2. **C5** — whether a retention or erasure obligation applies to transcripts and recordings. This is
   a governance determination for the repository owner / product owner. I have not answered it and
   will not; R9 cannot be closed until it is answered.

Say the word to continue with **Phase 2** (Medium and Low findings plus the remaining file reads), or
to re-run in **Verify Mode** once remediation lands. Re-running with `GITHUB_PAT` set would also let
me pull and triage CodeQL, Dependabot and Secret Scanning alerts, which Phase 1 could not.
