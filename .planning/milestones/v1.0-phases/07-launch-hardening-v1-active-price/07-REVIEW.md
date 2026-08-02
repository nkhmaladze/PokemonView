---
phase: 07-launch-hardening-v1-active-price
reviewed: 2026-07-15T00:00:00Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - .dockerignore
  - .env.example
  - Dockerfile
  - fly.toml
  - frontend/.env.production
  - frontend/.gitignore
  - frontend/src/api/client.js
  - requirements.txt
  - scripts/ingest_worker.py
  - tests/test_staleness_alert.py
  - wsgi.py
findings:
  critical: 0
  warning: 9
  info: 3
  total: 12
status: issues_found
---

# Phase 7: Code Review Report

**Reviewed:** 2026-07-15
**Depth:** standard
**Files Reviewed:** 11
**Status:** issues_found

## Summary

Reviewed the Phase 7 deployment/hardening surface: `.dockerignore`, `Dockerfile`, `fly.toml`, the frontend build-time API base URL wiring, `requirements.txt`, the ingestion worker's staleness-alert code, its contract tests, and `wsgi.py`.

The core secret-hygiene requirements called out for this phase hold up under inspection: `.dockerignore`'s `.env` / `.env.*` / `!.env.example` ordering correctly excludes real secrets from the build context (including nested `frontend/.env.production`, whose only content is a public API base URL, not a secret) while still shipping the placeholder `.env.example`; `fly.toml` never bakes real credentials into the config; and `check_and_alert_staleness()` never logs, prints, or includes the Discord webhook URL, `MONGODB_URI`, or eBay credentials in its outbound message or in any of the worker's `print()`/`errors[]` paths reviewed here — confirmed directly by `tests/test_staleness_alert.py::test_stale_run_posts_discord_payload`'s explicit assertions against message content.

No Critical/BLOCKER findings. The Warnings below are launch-hardening gaps: a root-user container, a test-only dependency (`pytest`) shipped into the production image, a hardcoded staleness threshold that silently decouples from the configurable ingestion interval, a SIGTERM/shutdown path that can strand the ingestion lock and leave a run doc stuck at `status="running"`, an unresolved fly.toml worker-machine provisioning risk (already flagged internally as an open assumption but still unresolved), no configured web health check, an incomplete `.env.example` (missing `CORS_ORIGINS`, which `wsgi.py`'s own docstring says `create_app()` reads from the environment), a silent-empty-string production fallback in `client.js` that masks misconfiguration rather than failing loudly, and a `.dockerignore`/Dockerfile mismatch where the comment claims the frontend isn't part of the Docker image but most of `frontend/` (everything except `node_modules`/`dist`) is still copied in via `COPY . .`.

## Warnings

### WR-01: Docker image runs as root — no non-root `USER` directive

**File:** `Dockerfile:3-15`
**Issue:** The image never creates or switches to a non-root user. Gunicorn (and the ingestion worker process, which shares this same image per `fly.toml`'s `[processes]` block) both run as root inside the container. This is a standard container-hardening gap for a phase explicitly named "Launch & Hardening" — if any dependency (Flask, gunicorn, requests, pymongo, or a transitive package) has a code-execution vulnerability, the blast radius is root inside the container rather than a restricted user.
**Fix:**
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER appuser

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "30", "wsgi:app"]
```

### WR-02: Test-only dependency (`pytest`) shipped into the production Docker image

**File:** `requirements.txt:4`, `Dockerfile:8`
**Issue:** `requirements.txt` is a single flat file containing `pytest==8.4.2` alongside runtime deps (`flask`, `pymongo`, `gunicorn`, etc.), and `Dockerfile:8` runs `pip install --no-cache-dir -r requirements.txt` unconditionally — so the production image ships the full pytest test framework and its transitive dependencies (iniconfig, pluggy, packaging, etc.) with no runtime use. This unnecessarily grows the deployed attack surface (more installed packages = more CVE exposure to track) for a phase focused on hardening.
**Fix:** Split into `requirements.txt` (runtime-only) and `requirements-dev.txt` (adds `-r requirements.txt` plus `pytest`), and change the Dockerfile to install only `requirements.txt`. Point CI/test tooling at `requirements-dev.txt` instead.

### WR-03: Staleness alert threshold is hardcoded and silently decouples from the configurable ingestion interval

**File:** `scripts/ingest_worker.py:63-66`, `scripts/ingest_worker.py:380-387`, `scripts/ingest_worker.py:426`
**Issue:** `STALENESS_THRESHOLD_HOURS = 8` is a fixed module constant documented as "~2x the `INGESTION_INTERVAL_HOURS` default of 4" (line 63-66). But `main()` reads `INGESTION_INTERVAL_HOURS` from the environment at line 426 and `scheduled_job()` (lines 380-387) calls `check_and_alert_staleness(db)` with no arguments, so it always uses the hardcoded default rather than a value derived from the configured interval. If an operator sets `INGESTION_INTERVAL_HOURS` above 8 (e.g., 12, to reduce eBay call volume), the "~2x" invariant silently breaks: a single missed/failed cycle will now breach the 8h threshold and fire an alert, rather than the two-missed-cycles grace period the code comments describe. This is a real behavior drift triggered by a supported, documented env var, with no code path to keep it consistent.
**Fix:** Derive the threshold from the same env var instead of hardcoding it independently, e.g.:
```python
def scheduled_job(db, interval_hours: float) -> None:
    run_ingestion_once(db)
    check_and_alert_staleness(db, threshold_hours=interval_hours * 2)
```
and pass `interval_hours` through `scheduler.add_job(..., args=[db, interval_hours])`.

### WR-04: SIGTERM handling can strand the ingestion lock / leave a run doc at `status="running"` forever

**File:** `scripts/ingest_worker.py:429-437`, `fly.toml:8-10`
**Issue:** The `shutdown` signal handler calls `scheduler.shutdown(wait=False)` then immediately `client.close()` and `sys.exit(0)`. If a SIGTERM (e.g., from a Fly deploy/restart) arrives while `run_ingestion_once()` is mid-flight in the scheduler's job thread, `wait=False` does not wait for that job to finish before the main thread closes the shared `MongoClient` and exits. The in-flight run's `finally` block (lines 298-318) then attempts `db.ingestion_runs.update_one(...)` and `release_lock(...)` against a client that may already be closing/closed, risking an exception that prevents the run document from being finalized (leaving `status="running"` indefinitely) and prevents `release_lock` from firing (leaving the cross-process Mongo lock held until its 900s/15-minute TTL expires — no ingestion can proceed in that window). `fly.toml` also defines no explicit `kill_timeout` override for the `worker` process group, so Fly's default grace period may not even allow this handler to run to completion before a SIGKILL.
**Fix:** Use `scheduler.shutdown(wait=True)` (bounded by a reasonable per-run timeout) before closing the Mongo client, and/or add an explicit `kill_timeout` in `fly.toml`'s process/service config sized to comfortably exceed a worst-case ingestion run duration, so in-flight runs get a real chance to hit their `finally` block and release the lock cleanly.

### WR-05: `fly.toml` gives no explicit machine/scale guarantee for the `worker` process group

**File:** `fly.toml:8-10`, `fly.toml:20-26`
**Issue:** `[http_service]` (lines 12-18) only applies to the `web` process (`processes = ["web"]`), and the top-level `[[vm]]` block is annotated in-file as an *unverified assumption* ("verify the exact per-process-group vm-override syntax... at deploy time"). There is no `fly scale count worker=N` equivalent expressed in this file, and no confirmation that a fresh `fly deploy` actually provisions a running machine for the `worker` process group. If it doesn't, the ingestion worker (and therefore all active-listing data collection and the staleness alert itself) silently never runs after a clean deploy, with nothing in this config to catch that.
**Fix:** Verify with `fly config validate`/`fly status` after a real deploy that a `worker` machine is actually running, and/or add an explicit process-group VM/scale override in `fly.toml` (or a documented `fly scale count worker=1` step in the deploy runbook) so this isn't left to an unverified assumption at launch time.

### WR-06: No health check configured for the web service

**File:** `fly.toml:12-18`
**Issue:** `[http_service]` defines `internal_port`, `force_https`, and autoscaling knobs, but no `[[http_service.checks]]` (or equivalent) block. Without an active health check, Fly Proxy can only infer liveness from raw TCP connectivity to port 8080 — it cannot detect a Flask process that's up and accepting connections but failing every request (e.g., a broken Mongo connection), and won't restart or route around such an instance.
**Fix:**
```toml
[[http_service.checks]]
  interval = "15s"
  timeout = "5s"
  grace_period = "10s"
  method = "GET"
  path = "/health"
```
(requires a corresponding lightweight `/health` route in the Flask app, out of scope for this file set but worth flagging for a follow-up).

### WR-07: `.env.example` is missing `CORS_ORIGINS`, which `wsgi.py`'s own docstring says the app reads from the environment

**File:** `.env.example` (entire file), `wsgi.py:8-9`
**Issue:** `wsgi.py`'s module docstring states `create_app()` "reads MONGODB_URI and CORS_ORIGINS from the environment internally via its own existing defaults," but `.env.example` documents `EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET`, `EBAY_ENV`, `MONGODB_URI`, `INGESTION_INTERVAL_HOURS`, and `DISCORD_WEBHOOK_URL` — never `CORS_ORIGINS`. An operator provisioning a new environment from `.env.example` (the documented onboarding path per the file's own header comment) has no way to discover this variable exists or needs setting, which is exactly the kind of gap that leads to an overly permissive CORS default silently persisting into production.
**Fix:** Add a documented `CORS_ORIGINS` entry to `.env.example`, e.g.:
```
# Comma-separated list of allowed origins for the /products* API (Flask-CORS).
# Falls back to a permissive/dev default if unset — set explicitly in production.
CORS_ORIGINS=https://your-frontend-domain.example
```

### WR-08: Frontend API base URL silently falls back to `''` in production instead of failing loudly on misconfiguration

**File:** `frontend/src/api/client.js:12`
**Issue:** `const BASE = import.meta.env.VITE_API_BASE_URL || ''` is correct for local dev (empty string routes through the Vite proxy) but applies the exact same silent fallback in a production build. Today this works because `frontend/.env.production` is committed and Vite auto-loads `.env.production` for the default `vite build` (production mode), but nothing in this file actually verifies that assumption held for the specific build that produced the deployed bundle (e.g., a custom build mode, a CI env that doesn't check out `.env.production`, or a future refactor that removes the committed file would all silently reproduce this). If `VITE_API_BASE_URL` is ever unset for a production build, every API call in the SPA silently becomes a same-origin relative request against the static host, which has no `/products` route — all requests would fail, with no signal at build time that anything was misconfigured.
**Fix:** Fail loudly in production builds when the var is missing, e.g.:
```javascript
const BASE = import.meta.env.VITE_API_BASE_URL || ''
if (import.meta.env.PROD && !BASE) {
  throw new Error('VITE_API_BASE_URL is required for production builds')
}
```

### WR-09: `.dockerignore` comment claims the frontend isn't part of the Docker image, but most of `frontend/` still is

**File:** `.dockerignore:20-23`, `Dockerfile:10`
**Issue:** The comment at `.dockerignore:20` reads "Frontend (built/deployed separately to Vercel, not part of the Docker image)," but the only frontend paths actually excluded are `frontend/node_modules/` and `frontend/dist/` (lines 21-22). `Dockerfile:10`'s `COPY . .` therefore still copies the rest of `frontend/` (source files, `package.json`, config, etc., minus the excluded two paths) into the backend's Docker image, contradicting the stated intent. This isn't a secrets leak (no real secrets live in `frontend/` after `.env.*` exclusion), but it is a documentation/implementation mismatch that unnecessarily bloats the API image with unused frontend source and could mislead a future maintainer who trusts the comment at face value.
**Fix:** Either exclude the whole `frontend/` directory from the Docker build context (since it's confirmed to be deployed separately) —
```
frontend/
```
— replacing the three narrower frontend lines, or correct the comment to accurately describe what's actually excluded.

## Info

### IN-01: Unvalidated `INGESTION_INTERVAL_HOURS` parse crashes the worker on a malformed value

**File:** `scripts/ingest_worker.py:426`
**Issue:** `interval_hours = int(os.environ.get("INGESTION_INTERVAL_HOURS", "4"))` will raise an unhandled `ValueError` at startup if the env var is set to a non-integer string (e.g., `"4.5"` or `"often"`), crashing the worker process before `scheduler.start()` is ever reached.
**Fix:** Wrap in a small validated parse with a clear error message, e.g. `try: interval_hours = int(...) except ValueError: raise SystemExit("INGESTION_INTERVAL_HOURS must be an integer number of hours")`.

### IN-02: Test isolation for staleness tests depends on an unreviewed fixture scope

**File:** `tests/test_staleness_alert.py:29-40`
**Issue:** `test_no_successful_run_alerts` asserts `mock_post.called` is `True` with no prior cleanup of `ingestion_runs`, relying entirely on `ingest_db` (from `tests/conftest.py`, not in this review's file set) providing a genuinely empty/isolated collection per test. If that fixture is anything other than function-scoped with per-test teardown (e.g., session-scoped, or order-dependent on other tests inserting `success`/`partial` docs first), this test becomes flaky/order-dependent.
**Fix:** Confirm (or add an explicit assertion) that `ingest_db.ingestion_runs` is empty at the start of this test, independent of fixture implementation details, e.g. `assert ingest_db.ingestion_runs.count_documents({}) == 0` before calling `check_and_alert_staleness`.

### IN-03: No `EXPOSE` instruction in Dockerfile

**File:** `Dockerfile:1-15`
**Issue:** The image never declares `EXPOSE 8080`. Fly.io doesn't require it (it reads `internal_port` from `fly.toml`), but its absence removes a piece of image self-documentation and makes the image slightly less portable to non-Fly container tooling that inspects `EXPOSE` metadata (e.g., `docker run -P`).
**Fix:** Add `EXPOSE 8080` after the `WORKDIR` line for clarity, even though it has no functional effect on Fly's routing.

---

_Reviewed: 2026-07-15_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
