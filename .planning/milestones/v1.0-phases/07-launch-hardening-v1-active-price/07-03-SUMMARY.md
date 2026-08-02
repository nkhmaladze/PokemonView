---
phase: 07-launch-hardening-v1-active-price
plan: 03
subsystem: infra
tags: [docker, fly.io, deployment, dockerignore, gunicorn]

# Dependency graph
requires:
  - phase: 07-launch-hardening-v1-active-price (plan 07-02)
    provides: wsgi.py entrypoint and gunicorn dependency (fly.toml/Dockerfile reference wsgi:app, assume it will exist after wave merge)
provides:
  - Dockerfile — single-stage python:3.12-slim image installing requirements.txt and copying the repo
  - .dockerignore — excludes real .env, __pycache__, .git, .planning, frontend/node_modules/dist from build context
  - fly.toml — [processes] web (gunicorn) + worker (APScheduler), http_service scoped to web only, always-on overrides (D-03)
affects: [07-04 (fly secrets set / deploy runbook), 07-05 (frontend/Vercel deploy referencing the fly.dev URL)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "One Docker image, two Fly.io process types declared in fly.toml [processes] — no per-process Dockerfile"
    - "Always-on Fly config: auto_stop_machines off + auto_start_machines false + min_machines_running 1 to prevent worker scale-to-zero (D-03)"

key-files:
  created: [Dockerfile, .dockerignore, fly.toml]
  modified: []

key-decisions:
  - "Single-stage Dockerfile (no multi-stage build) since the app has no compiled/native build step — matches 07-RESEARCH.md Alternatives Considered"
  - "One Fly app / one image / two process types (web, worker) rather than two separate Fly apps — matches project's minimal-service-fragmentation precedent"
  - "No [env] secrets block in fly.toml — all secrets deferred to fly secrets set in plan 07-04 (T-07-02)"

patterns-established:
  - "fly.toml [http_service] processes = [\"web\"] scopes the HTTP proxy/health-check to the web group only; the worker process group has no inbound HTTP surface by design"

requirements-completed: [SC-1, SC-2]

coverage:
  - id: D1
    description: "Dockerfile builds a single python:3.12-slim image, installs requirements.txt, copies the repo, and has a gunicorn/wsgi:app fallback CMD"
    requirement: "SC-1"
    verification:
      - kind: other
        ref: "grep -c 'FROM python:3.12-slim' Dockerfile && grep -c 'pip install --no-cache-dir -r requirements.txt' Dockerfile && grep -c 'COPY . .' Dockerfile"
        status: pass
    human_judgment: false
  - id: D2
    description: ".dockerignore excludes a real .env from the Docker build context so no secret is baked into an image layer"
    requirement: "SC-1"
    verification:
      - kind: other
        ref: "grep -E '^\\.env$' .dockerignore"
        status: pass
    human_judgment: false
  - id: D3
    description: "fly.toml declares web + worker process types, scopes http_service to web only, and disables scale-to-zero on both groups (auto_stop_machines off, auto_start_machines false, min_machines_running 1)"
    requirement: "SC-2"
    verification:
      - kind: other
        ref: "grep -c 'auto_stop_machines = \"off\"' fly.toml && grep -c 'auto_start_machines = false' fly.toml && grep -c 'min_machines_running = 1' fly.toml && grep -c 'processes = \\[\"web\"\\]' fly.toml"
        status: pass
    human_judgment: false
  - id: D4
    description: "fly.toml carries zero secret literals and no [env] secrets block"
    requirement: "SC-1"
    verification:
      - kind: other
        ref: "grep -riE 'mongodb\\+srv://|discord.com/api/webhooks/|client_secret\\s*=\\s*\"' Dockerfile .dockerignore fly.toml"
        status: pass
    human_judgment: false

# Metrics
duration: 6min
completed: 2026-07-15
status: complete
---

# Phase 7 Plan 3: Deployment Config (Dockerfile, .dockerignore, fly.toml) Summary

**Single-stage Dockerfile + .dockerignore + fly.toml declaring one image / two always-on Fly.io process types (web via gunicorn, worker via APScheduler), with http_service scoped to web only and zero secret literals.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-07-15T20:25:00Z
- **Completed:** 2026-07-15T20:31:42Z
- **Tasks:** 2
- **Files modified:** 3 (all new)

## Accomplishments
- Dockerfile: single-stage `python:3.12-slim` base, `WORKDIR /app`, installs `requirements.txt`, copies the repo, with a fallback `gunicorn ... wsgi:app` CMD (never actually invoked once `fly.toml [processes]` is defined)
- .dockerignore: excludes a real `.env` (and any `.env.*` variant, keeping `.env.example` in) plus `.git/`, `.planning/`, `__pycache__/`, `.pytest_cache/`, `frontend/node_modules/`, `frontend/dist/`, `node_modules/` from the Docker build context
- fly.toml: `[processes]` block with `web` (gunicorn against `wsgi:app`) and `worker` (`python -m scripts.ingest_worker`, the existing scheduled `BlockingScheduler` path — no `--once`); `[http_service]` scoped to `web` only via `processes = ["web"]`, `force_https = true`; always-on overrides `auto_stop_machines = "off"`, `auto_start_machines = false`, `min_machines_running = 1` on the http_service block (D-03); single top-level `[[vm]]` at `shared-cpu-1x`/`512mb`

## Task Commits

Each task was committed atomically:

1. **Task 1: Create Dockerfile + .dockerignore** - `6336fef` (feat)
2. **Task 2: Create fly.toml (two always-on process types)** - `6089246` (feat)

**Plan metadata:** committed alongside this SUMMARY (see final commit below).

## Files Created/Modified
- `Dockerfile` - single-stage python:3.12-slim image shared by both Fly process types
- `.dockerignore` - keeps real .env and other build-irrelevant/sensitive paths out of the Docker build context
- `fly.toml` - one Fly app, two always-on process types (web/worker), http_service scoped to web only, no secrets

## Decisions Made
- Single-stage Dockerfile (no multi-stage build) — matches 07-RESEARCH.md's Alternatives Considered rationale (no compiled/native build step in this app; pymongo/rapidfuzz ship prebuilt wheels)
- One Fly app / one image / two process types (web, worker) rather than two separate Fly apps — matches this project's established minimal-service-fragmentation pattern
- Left the `[[vm]]` per-process-group override syntax as a single top-level block applying to both groups, per 07-RESEARCH.md Assumption A1 — flagged there as something to spot-check with `fly config validate` at actual deploy time (plan 07-04), not a blocker for authoring this config now
- No `[env]` secrets block anywhere in fly.toml; all secrets (MONGODB_URI, CORS_ORIGINS, DISCORD_WEBHOOK_URL, EBAY_CLIENT_ID/SECRET) deliberately deferred to `fly secrets set` in plan 07-04 per T-07-02

## Deviations from Plan

None - plan executed exactly as written. Both tasks' `<action>` and `<acceptance_criteria>` were followed verbatim against 07-RESEARCH.md's Code Examples (Dockerfile) and Architecture Patterns Pattern 1 (fly.toml), with no bugs, missing functionality, blocking issues, or architectural questions encountered.

## Issues Encountered

None. `wsgi.py` and the `gunicorn` dependency itself do not yet exist in this worktree (they are plan 07-02's deliverable, running in the same wave with `depends_on: []`) — this plan's Dockerfile/fly.toml reference `wsgi:app` and `gunicorn` by design, per the plan's own `key_links`, anticipating those artifacts will be present after the wave's plans are merged together. This is expected, not a gap: neither Dockerfile nor fly.toml is built/deployed as part of this plan's verification, only authored and grep-checked for correct literal content.

## User Setup Required

None - no external service configuration required by this plan. Actual `fly launch`/`fly deploy`/`fly secrets set` execution against a real Fly.io account happens in plan 07-04, not here.

## Next Phase Readiness
- Dockerfile, .dockerignore, and fly.toml are authored and grep-verified per the plan's acceptance criteria; ready for `fly launch`/`fly deploy` once plan 07-02 (wsgi.py + gunicorn) and plan 07-04 (secrets injection) are also complete.
- No blockers introduced by this plan. The `[[vm]]` per-process-group syntax (Assumption A1) and the `fly secrets set` "no redeploy needed" behavior (Assumption A4) remain open items to spot-check live against `fly` CLI output during plan 07-04's execution, as already flagged in 07-RESEARCH.md.

---
*Phase: 07-launch-hardening-v1-active-price*
*Completed: 2026-07-15*

## Self-Check: PASSED

- FOUND: Dockerfile
- FOUND: .dockerignore
- FOUND: fly.toml
- FOUND: .planning/phases/07-launch-hardening-v1-active-price/07-03-SUMMARY.md
- FOUND commit: 6336fef (Task 1)
- FOUND commit: 6089246 (Task 2)
- FOUND commit: f8e7e6c (plan-complete docs commit)
