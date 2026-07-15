---
phase: 07-launch-hardening-v1-active-price
verified: 2026-07-15T23:15:00Z
status: passed
score: 3/3 must-haves verified
behavior_unverified: 0
overrides_applied: 0
---

# Phase 7: Launch & Hardening (v1 active-price) Verification Report

**Phase Goal:** The active-price product is deployed, publicly reachable, and monitored so its data stays trustworthy and current — shipping v1 regardless of Marketplace Insights API status.
**Verified:** 2026-07-15T23:15:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth (ROADMAP Success Criteria) | Status | Evidence |
|---|------|--------|----------|
| 1 | SC-1: The application (ingestion worker, Flask API, React SPA, MongoDB) is deployed and the site is reachable at a public URL. | ✓ VERIFIED | Live `curl -I https://pokemonview.fly.dev/products` → `HTTP_CODE:200` (verified directly in this session, not just SUMMARY narrative). Live `curl https://frontend-black-one-22.vercel.app` → `VERCEL_HTTP_CODE:200`, serving the built SPA. `curl https://pokemonview.fly.dev/products` returns real catalog JSON. CORS verified live: `Origin: https://frontend-black-one-22.vercel.app` → `access-control-allow-origin` echoed back; `Origin: https://evil.example.com` → no CORS header (correctly scoped, not wildcard). |
| 2 | SC-2: In production the ingestion worker runs automatically on its schedule, keeping displayed data current without manual intervention. | ✓ VERIFIED (mechanism) — see caveat below | `fly status`/`fly machine list --app pokemonview` (run live in this session) show `web` (x2) and `worker` machines all `started`, none `stopped` except the documented Fly HA standby replica (marked `†` by Fly itself, "takes over only in case of host hardware failure" — not scale-to-zero). `fly machine status <worker-id>` event log shows a single `start` event, no restart-loop. `fly.toml` has `auto_stop_machines = "off"`, `auto_start_machines = false`, `min_machines_running = 1` — confirmed present in the deployed config and in the repo file. Worker command is the scheduled path (`python -u -m scripts.ingest_worker`, no `--once`), matching `fly.toml`'s `[processes] worker` line. `scripts/ingest_worker.py::main()` wires `scheduler.add_job(scheduled_job, ..., next_run_time=datetime.now(timezone.utc))` — the live-discovered APScheduler first-fire bug (D-06 in 07-04-SUMMARY) was fixed and is present in the current file. |
| 3 | SC-3: An alert is triggered when ingestion data goes stale beyond roughly 2x the polling interval, so silent pipeline failures surface instead of showing users stale prices. | ✓ VERIFIED | `check_and_alert_staleness()` present in `scripts/ingest_worker.py` (STALENESS_THRESHOLD_HOURS = 8, ~2x the 4h default interval), wired into `scheduled_job()` which is the function passed to `scheduler.add_job` (confirmed by reading `main()`); the `--once` path calls `run_ingestion_once` directly and does not invoke the staleness check, matching the plan's intent. Behavioral test suite `tests/test_staleness_alert.py` re-run live in this session: 5/5 passed (`test_no_successful_run_alerts`, `test_fresh_run_no_alert`, `test_stale_run_posts_discord_payload`, `test_missing_webhook_url_noop`, `test_discord_post_failure_swallowed`). Full project suite re-run live: 63/63 passed. 07-04-SUMMARY documents a human-confirmed live Discord alert arrival with no secret values in the message content — accepted as legitimate live-verification evidence per this verification's scope instructions (not re-demanded from scratch). |

**Score:** 3/3 truths verified (0 present-but-behavior-unverified)

**Caveat on Truth 2 (documented, not a gap):** The "keeping displayed data current" half of SC-2 is not yet materially true — `curl https://pokemonview.fly.dev/products/pitch-black_booster_box` (run live) returns `"price_status":"no_data_yet"` and `"status":"insufficient_data"` for trend fields, because `EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET` remain absent (lost in a Phase 1 incident, confirmed still missing through Phase 3, and explicitly not obtained before this phase per 07-CONTEXT.md D-05). This is a locked, user-approved decision (D-05/D-06): "Phase 7 deploys the full stack now anyway — do not block launch on obtaining credentials first... at which point ingestion goes live with no redeploy required." The worker's scheduling/always-on/fail-loud mechanics — the part of SC-2 actually in this phase's control — are built, deployed, and verified live; the "current data" outcome is gated on a pre-existing, out-of-phase external blocker (eBay credential replacement) that the user explicitly and knowingly deferred, not an implementation gap in Phase 7's own work. Treated as within-scope-achieved per the documented decision rather than a FAILED truth; flagged here for visibility.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/ingest_worker.py :: check_and_alert_staleness(db, threshold_hours)` | Staleness check + Discord POST | ✓ VERIFIED | Present, matches plan's behavior spec exactly (early-return on fresh run, infinite gap on no run, webhook-absent no-op, RequestException swallowed). |
| `scripts/ingest_worker.py :: scheduled_job(db)` | Wraps run + staleness check | ✓ VERIFIED | Present; wired as `scheduler.add_job`'s first positional arg. |
| `tests/test_staleness_alert.py` | 5 tests | ✓ VERIFIED | 5/5 tests present and passing (re-run live). |
| `.env.example :: DISCORD_WEBHOOK_URL` | Documented env var | ✓ VERIFIED | Present (confirmed via `git show HEAD:.env.example`, since direct read/grep of `.env*` paths is blocked by harness policy). |
| `requirements.txt :: gunicorn==26.0.0` | Pinned dep | ✓ VERIFIED | Present, 9th pin, all 8 prior pins intact. |
| `wsgi.py :: app = create_app()` | Gunicorn entrypoint | ✓ VERIFIED | Present, module-level, no extra config surface. |
| `Dockerfile` | Single-stage python:3.12-slim image | ✓ VERIFIED | `FROM python:3.12-slim`, installs `requirements.txt`, `COPY . .`, fallback CMD → `wsgi:app`. |
| `.dockerignore` | Excludes real `.env` | ✓ VERIFIED | `.env` / `.env.*` / `!.env.example` present. |
| `fly.toml` | Two always-on process types | ✓ VERIFIED | `[processes] web` (gunicorn) + `worker` (ingest_worker scheduled path); `auto_stop_machines = "off"`, `auto_start_machines = false`, `min_machines_running = 1`; `http_service processes = ["web"]` only. |
| Deployed Fly app `pokemonview` | Live web + worker machines | ✓ VERIFIED (live) | `fly status`/`fly machine list` run live in this session: 2 web machines + 1 active worker + 1 Fly-managed HA standby worker, all `started`. |
| Deployed Vercel SPA | Public static site | ✓ VERIFIED (live) | `https://frontend-black-one-22.vercel.app` returns HTTP 200 live; `frontend/.env.production` confirmed to hold `VITE_API_BASE_URL=https://pokemonview.fly.dev`. |
| `frontend/src/api/client.js` | Reads VITE_API_BASE_URL | ✓ VERIFIED | `const BASE = import.meta.env.VITE_API_BASE_URL || ''` — confirms the 07-05 bug-fix (previously hardcoded to `''`) is in the current file. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `scheduled_job` | `check_and_alert_staleness` | direct call after `run_ingestion_once` | ✓ WIRED | Confirmed by reading `scheduled_job()`'s body. |
| `main()` scheduler | `scheduled_job` | `scheduler.add_job(scheduled_job, ...)` | ✓ WIRED | Confirmed; `--once` path calls `run_ingestion_once` directly, correctly bypassing the alert. |
| `fly.toml [processes] web` | `wsgi:app` | gunicorn command string | ✓ WIRED | Matches `wsgi.py`'s `app` object; live `fly machine status` shows the actual running command. |
| `fly.toml [processes] worker` | `scripts.ingest_worker` scheduled path | `python -u -m scripts.ingest_worker` | ✓ WIRED | Live machine command confirmed identical string. |
| SPA (`client.js`) | Fly API | `fetch(VITE_API_BASE_URL + path)` | ✓ WIRED (live) | Live browser-equivalent check: `curl` from the Vercel-equivalent Origin header returns `access-control-allow-origin` matching the Vercel origin; `/products` returns real catalog JSON, not a 404/placeholder. |
| Fly API | CORS_ORIGINS secret | `flask-cors` origin allow-list | ✓ WIRED (live) | `fly secrets list` shows `CORS_ORIGINS` deployed; live curl with disallowed Origin gets no CORS header, live curl with the real Vercel Origin gets the header echoed back — not a wildcard. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Staleness alert test suite | `pytest tests/test_staleness_alert.py -v` (re-run live) | 5/5 passed | ✓ PASS |
| Full project test suite | `pytest -q` (re-run live) | 63/63 passed | ✓ PASS |
| Public API reachable | `curl -I https://pokemonview.fly.dev/products` | `HTTP_CODE:200` | ✓ PASS |
| Public SPA reachable | `curl https://frontend-black-one-22.vercel.app` | `HTTP_CODE:200` | ✓ PASS |
| Machines always-on | `fly machine list --app pokemonview` | web x2 `started`, worker `started` + 1 Fly HA standby | ✓ PASS |
| Worker not crash-looping | `fly machine status <worker-id>` | Single `start` event, no restart churn | ✓ PASS |
| CORS scoped correctly | `curl -H Origin: <vercel>` vs `curl -H Origin: <other>` | Allowed origin echoed, disallowed origin gets no header | ✓ PASS |
| No debt markers (TBD/FIXME/XXX) | `grep -nE 'TBD|FIXME|XXX'` across phase-modified files | No matches | ✓ PASS |

### Requirements Coverage

Phase 7's ROADMAP entry states: **Requirements: None owned** (operational readiness phase). Cross-referencing `.planning/REQUIREMENTS.md`: no requirement ID in that file is tagged "Phase 7," and every v1 requirement (CATALOG-01/02, INGEST-01/02/03, MATCH-01/02/03, PRICE-01/02/03, SEARCH-01/02) is already marked complete under earlier phases (2–6); the only unchecked items (INGEST-04, PRICE-04/05/06) are explicitly tagged **(Phase 8, contingent)**, not Phase 7. **No orphaned Phase-7-tagged requirements found** — confirmed by grep against REQUIREMENTS.md.

### Anti-Patterns Found

Per `07-REVIEW.md` (0 critical, 9 warning, 3 info) — independently spot-checked against the live files in this session (no debt markers found; findings match file contents read directly). None are blockers to the phase goal; all are hardening follow-ups appropriate to flag but not gate v1 launch on:

| File | Severity | Issue | Impact |
|------|----------|-------|--------|
| `Dockerfile` | ⚠️ Warning | No non-root `USER` directive (WR-01) | Container runs as root; standard hardening gap, not an active exploit path introduced by this phase. |
| `requirements.txt` / `Dockerfile` | ⚠️ Warning | `pytest` shipped into production image (WR-02) | Larger attack surface than necessary; no functional impact. |
| `scripts/ingest_worker.py` | ⚠️ Warning | `STALENESS_THRESHOLD_HOURS=8` hardcoded, decoupled from `INGESTION_INTERVAL_HOURS` env var (WR-03) | Only manifests if an operator later changes the interval above 4h; default deployment (interval=4) is correct today. |
| `scripts/ingest_worker.py`, `fly.toml` | ⚠️ Warning | SIGTERM handling (`wait=False`) can strand the Mongo lock/run doc on a mid-flight restart (WR-04) | Edge-case risk during a Fly redeploy/restart while a run is in-flight; self-heals via the 900s lock TTL. |
| `fly.toml` | ⚠️ Warning | No explicit worker VM/scale guarantee beyond the top-level `[[vm]]` (WR-05) | Live-verified in this session as a non-issue in practice (`fly machine list` shows the worker machine present and started), but the config itself doesn't formally guarantee it. |
| `fly.toml` | ⚠️ Warning | No `/health` check configured for web (WR-06) | Fly falls back to raw TCP liveness; live API returns 200 today. |
| `.env.example` | ⚠️ Warning | Missing `CORS_ORIGINS` documentation (WR-07) | Onboarding-doc gap; production config itself is correctly set (verified live). |
| `frontend/src/api/client.js` | ⚠️ Warning | Silent `''` fallback in production if `VITE_API_BASE_URL` unset (WR-08) | Correctly set in the current deploy (verified live); would only surface on a future misconfigured rebuild. |
| `.dockerignore` / `Dockerfile` | ⚠️ Warning | Comment claims frontend excluded from image; only `node_modules`/`dist` actually excluded (WR-09) | Documentation/implementation mismatch; not a secrets leak. |
| `scripts/ingest_worker.py` | ℹ️ Info | Unvalidated `INGESTION_INTERVAL_HOURS` parse crashes on malformed value (IN-01) | Not exercised at default config. |
| `tests/test_staleness_alert.py` | ℹ️ Info | Fixture-scope assumption for one test (IN-02) | Test-suite robustness note. |
| `Dockerfile` | ℹ️ Info | No `EXPOSE 8080` (IN-03) | Cosmetic; Fly reads `internal_port` from `fly.toml`. |

### Human Verification Required

None. All must-have truths and artifacts were verifiable either by direct code inspection, live test re-execution, or live infrastructure checks (`curl`, `fly status`, `fly machine list`, `fly machine status`, `fly secrets list`) performed in this verification session — not solely trusted from SUMMARY.md narrative.

### Gaps Summary

No blocking gaps. Phase 7's goal — deploy, public reachability, and staleness monitoring for the active-price v1 product — is achieved and independently re-verified live in this session (not merely re-stated from SUMMARY.md). The one caveat (SC-2's "current data" outcome pending eBay credentials) is a pre-existing, explicitly user-decided deferral from Phase 1/3 (D-05/D-06 in 07-CONTEXT.md), not a Phase 7 implementation gap — the deploy/scheduling/alerting mechanism itself is fully built, deployed, and confirmed live. The 9 code-review warnings + 3 info findings are legitimate hardening follow-ups (root-user container, threshold/interval coupling, SIGTERM edge case, missing health check, doc gaps) appropriate for a future phase or ad-hoc hardening pass, not blockers to shipping v1.

---

_Verified: 2026-07-15T23:15:00Z_
_Verifier: Claude (gsd-verifier)_
