---
phase: 07
slug: launch-hardening-v1-active-price
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-07-15
---

# Phase 07 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| worker → Discord webhook | Outbound POST from the ingestion worker to an external Discord endpoint carries an operational alert message. | Operational counts/timestamps only — no secrets |
| worker → MongoDB Atlas | Read of `ingestion_runs` to determine freshness. | Ingestion run metadata |
| developer → PyPI | New third-party dependency (gunicorn) enters the build/runtime supply chain. | Package binary/source |
| gunicorn → api.app | The WSGI server imports and serves the application factory's app object. | In-process |
| repo → Docker build context | Files copied into the image; a committed `.env` would leak secrets into image layers. | Repo source files |
| committed config → git history | `fly.toml` is committed; any secret placed in it is permanently exposed. | Deployment config |
| Fly Machine → MongoDB Atlas | Production process (not a developer laptop) connects to Atlas over the public internet. | DB credentials + query traffic |
| operator → Fly secrets store | Real `MONGODB_URI` / `DISCORD_WEBHOOK_URL` values are entered and stored encrypted. | Secrets (write-once, operator-time) |
| internet → Fly web machine | Public HTTPS traffic reaches the API. | API request/response traffic |
| developer → npm | The global `vercel` CLI enters the developer toolchain. | Package binary/source |
| browser (Vercel origin) → Fly API | Cross-origin requests from the SPA are gated by the API's CORS policy. | Product/price API traffic |
| build → static bundle | `VITE_API_BASE_URL` is inlined into the public JS bundle at build time. | Public API base URL (non-secret) |

---

## Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation | Status |
|-----------|----------|-----------|----------|-------------|------------|--------|
| T-07-01 | Information Disclosure | `DISCORD_WEBHOOK_URL` handling in `check_and_alert_staleness` (`scripts/ingest_worker.py`) | medium | mitigate | Webhook read only via `os.environ.get`; never logged/interpolated. Message body carries only counts/timestamps. `ingest_worker.py:366,370-373`; verified by `tests/test_staleness_alert.py:90-91` (asserts no webhook URL / `mongodb` substring in posted content). | closed |
| T-07-02a | Denial of Service | Discord outage or missing webhook crashing the worker loop (`scripts/ingest_worker.py`) | medium | mitigate | Missing webhook → early return (no raise); `requests.RequestException` swallowed. `ingest_worker.py:367-368,374-377`; verified by `test_missing_webhook_url_noop`, `test_discord_post_failure_swallowed`. | closed |
| T-07-SC | Tampering | `gunicorn==26.0.0` PyPI install (Docker build) | high | mitigate | Blocking-human package-legitimacy checkpoint before the pin entered `requirements.txt`; exact-version pin (`requirements.txt:9`) so the build never floats to an unreviewed release. Human gate attested in `07-02-SUMMARY.md`. | closed |
| T-07-06 | Information Disclosure | `wsgi.py` config surface | low | mitigate | `wsgi.py:14-16` reads no config and logs nothing — only calls `create_app()`, which already handles secret hygiene. | closed |
| T-07-02b | Information Disclosure | Secret leakage into Docker image layers / git via committed `.env` or `fly.toml [env]` | high | mitigate | `.dockerignore:2-4` excludes `.env`/`.env.*` (keeps `.env.example`) from build context; `fly.toml` has no `[env]` block and no secret literals (grep clean). Disambiguated from T-07-02a (see Register Hygiene note below). | closed |
| T-07-07 | Denial of Service | `fly launch` defaults (scale-to-zero) silently stopping the worker | high | mitigate | `fly.toml:17-19` explicitly sets `auto_stop_machines = "off"`, `auto_start_machines = false`, `min_machines_running = 1` on both process groups. | closed |
| T-07-08 | Tampering | Unpinned base image drift (`python:3.12-slim`, `Dockerfile:3`) | low | accept | RESEARCH-specified base; digest pin is a possible future hardening item, out of scope for v1. | closed |
| T-07-04 | Information Disclosure | Secrets baked into image/`fly.toml` instead of the secrets store | high | mitigate | All runtime secrets injected via `fly secrets set` (encrypted at rest, env-injected at boot); `fly.toml`/`Dockerfile` carry zero secret literals (grep clean). Runtime injection attested in `07-04-SUMMARY.md`. | closed |
| T-07-09 | Spoofing / MITM | Public API served over plaintext | high | mitigate | `force_https = true` in `fly.toml:15` [http_service]; Fly issues/terminates TLS automatically. Live HTTP/2 TLS attested via `curl -I` in `07-04-SUMMARY.md`. | closed |
| T-07-03 | Elevation of Privilege / Information Disclosure | MongoDB Atlas Network Access set to `0.0.0.0/0` | medium | accept | Deliberate v1 tradeoff: Atlas username/password remains the real access-control layer; Fly Machines lack a stable outbound IP. Follow-up hardening (Fly static egress IP + tight allowlist) logged as a post-launch item. | closed |
| T-07-10 | Denial of Service | Worker crash-loop misread as normal (missing eBay creds) | low | accept | `get_app_token` failure caught inside `run_ingestion_once` (`ingest_worker.py:292-297`) → recorded `status="failed"`; scheduler keeps running. Surfaced by the staleness alert, not a silent failure. | closed |
| T-07-SC-v | Tampering | `vercel` npm global CLI install | high | mitigate | Blocking-human package-legitimacy checkpoint before `npm install -g vercel`; verified against npmjs.com/package/vercel (official Vercel org, 2.7M weekly downloads). `vercel` confirmed absent from `frontend/package.json` (global-CLI-only usage). Attested in `07-05-SUMMARY.md`. | closed |
| T-07-11 | Information Disclosure | A secret leaking into a `VITE_*` build-time value (inlined into the public bundle) | high | mitigate | `frontend/.env.production` carries only the public `VITE_API_BASE_URL` — no `MONGODB_URI`/eBay/Discord value present (verified: single line, 46 bytes). `frontend/src/api/client.js:12` reads only `VITE_API_BASE_URL`. | closed |
| T-07-12 | Spoofing (CSRF-adjacent) / overly-permissive CORS | `CORS_ORIGINS` left as a wildcard in production | medium | mitigate | `api/app.py:55-65` sources `CORS_ORIGINS` from env with comma-split (CR-02 fix); wildcard `"*"` is only the documented dev default when the var is unset (`api/config.py:21-34`) — never hardcoded in production-reachable code. Production value (explicit Vercel origin) set via `fly secrets set`, curl origin-block tests attested in `07-05-SUMMARY.md`. | closed |
| T-07-09b | Spoofing / MITM | SPA served/loaded over plaintext | high | mitigate | Vercel serves the SPA over automatic HTTPS; DevTools verification against the `https://` origin attested in `07-05-SUMMARY.md`. | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above workflow.security_block_on (high) count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

**Register hygiene note:** Plans 07-01 and 07-03 each independently used ID `T-07-02` for distinct threats (DoS via Discord outage vs. Information Disclosure via secret leakage). Disambiguated here as **T-07-02a** (07-01) and **T-07-02b** (07-03); both verified closed. Future phase plans should avoid reusing threat IDs across plans within the same phase.

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|--------------|------|
| AR-07-01 | T-07-08 | Unpinned `python:3.12-slim` base image — RESEARCH-specified base; digest pin deferred as a post-launch hardening item, not a v1 blocker. | Phase 07 plan (07-03) | 2026-07-15 |
| AR-07-02 | T-07-03 | MongoDB Atlas Network Access `0.0.0.0/0` — Fly Machines lack a stable outbound IP; Atlas username/password is the real access-control layer. Static egress IP + allowlist logged as follow-up hardening. | Phase 07 plan (07-04) | 2026-07-15 |
| AR-07-03 | T-07-10 | Worker crash-loop misread as normal on missing eBay creds — failure is caught and recorded (`status="failed"`), scheduler keeps running, staleness alert surfaces it. Not a silent failure. | Phase 07 plan (07-04) | 2026-07-15 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-07-15 | 15 | 15 | 0 | gsd-security-auditor (opus) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-07-15
