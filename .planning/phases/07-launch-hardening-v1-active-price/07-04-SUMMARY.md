---
phase: 07-launch-hardening-v1-active-price
plan: 04
subsystem: infra
tags: [fly-io, deployment, apscheduler, gunicorn, mongodb-atlas, discord, always-on]

dependency-graph:
  requires:
    - phase: 07-02
      provides: "gunicorn pin + wsgi.py entrypoint for the web process"
    - phase: 07-03
      provides: "Dockerfile + fly.toml with two always-on process types (web, worker)"
    - phase: 07-01
      provides: "check_and_alert_staleness() Discord webhook alert wired into scheduled_job()"
  provides:
    - "Deployed Fly.io app `pokemonview` — web (gunicorn) + worker (APScheduler) machines, both always-on"
    - "MongoDB Atlas Network Access entry (0.0.0.0/0) permitting the Fly app to connect"
    - "Fly secrets store: MONGODB_URI, DISCORD_WEBHOOK_URL (eBay creds deliberately absent per D-05)"
    - "Live https://pokemonview.fly.dev host recorded for plan 07-05's VITE_API_BASE_URL"
    - "scripts/ingest_worker.py :: next_run_time=datetime.now(timezone.utc) fix on scheduler.add_job (immediate first run)"
    - "fly.toml :: worker process invoked with `python -u` (unbuffered stdout for fly logs visibility)"
  affects:
    - "07-05 (frontend deploy) — needs the exact .fly.dev host for VITE_API_BASE_URL and CORS_ORIGINS"

tech-stack:
  added: []
  patterns:
    - "python -u for any long-running process piped through a non-TTY log sink (fly logs, docker logs, etc.) — Python's default stdout block-buffering on non-TTY pipes silently delays/hides startup print statements until process exit"
    - "APScheduler IntervalTrigger requires an explicit next_run_time (or start_date) on scheduler.add_job() to fire immediately; leaving it unset defaults the first fire to now + interval, not now"

key-files:
  created: []
  modified:
    - fly.toml
    - scripts/ingest_worker.py

decisions:
  - "MongoDB Atlas Network Access set to 0.0.0.0/0 (documented v1 tradeoff, T-07-03/accept) since Fly Machines have no stable outbound IP; Atlas username/password remains the real access-control layer"
  - "eBay credentials deliberately left unset in Fly secrets (D-05) — worker fails-loud at get_app_token with status=failed, which is the expected launch condition, not a blocker"

metrics:
  duration: ~45min (spans two prior agent sessions plus this closeout)
  completed: 2026-07-15
status: complete
---

# Phase 7 Plan 04: Deploy Fly.io App Summary

Deployed the Fly.io app `pokemonview` (gunicorn web + APScheduler worker, both always-on), injected `MONGODB_URI`/`DISCORD_WEBHOOK_URL` via `fly secrets set`, opened MongoDB Atlas Network Access, and verified live: the public API returns HTTP 200, both machines stay `started`, and the expected credentials-absent Discord staleness alert arrived with no secret values — confirmed by the human operator.

## What Was Built / Verified

- **Task 1 (provision + deploy):** `fly launch --no-deploy --copy-config --name pokemonview` created the app without clobbering the authored `fly.toml`; `auto_stop_machines = "off"`, `auto_start_machines = false`, and `min_machines_running = 1` all survived. `fly secrets set MONGODB_URI=... DISCORD_WEBHOOK_URL=... --app pokemonview` injected the two runtime secrets (values never pasted into the agent transcript). `fly secrets list` confirms MONGODB_URI + DISCORD_WEBHOOK_URL present; EBAY_CLIENT_ID/EBAY_CLIENT_SECRET absent, exactly as D-05 requires. MongoDB Atlas Network Access was opened to 0.0.0.0/0. `fly deploy --app pokemonview` completed with both `web` and `worker` process groups healthy.
- **Task 2 (live verification):** `curl -I https://pokemonview.fly.dev/products` returned `HTTP/2 200` (SC-1). `fly machine list` showed both web and worker machines `started` (one additional standby worker replica is Fly's own HA feature — informational, not scale-to-zero, not a defect). `fly logs` showed the worker's `"ingestion worker started — interval_hours=4"` line (after the stdout-unbuffering fix below) with no crash-loop. A real ingestion attempt recorded `status=failed` at `get_app_token` (D-05/D-06 working as designed, verified via a live MongoDB query against `ingestion_runs`). The human operator confirmed via Discord ("verified") that the staleness alert arrived with no secret values in its content.

## Task Commits

Both tasks in this plan are `checkpoint:human-action` / `checkpoint:human-verify` gates with no task-scoped code commit of their own (the deploy/verify runbook itself is not a repo change). Two genuine bugs were found and fixed live during verification and are committed separately (see Deviations below):

1. **Task 1: Provision + deploy the Fly app** - human-run runbook, no direct commit (fly.toml/secrets/Atlas are external-service state, not repo state)
2. **Task 2: Verify public API + always-on + worker scheduling** - human-run verification; surfaced the two bugs fixed below

**Fix commits (Deviations, Rule 1):**
- `2603af9` - fix(07-04): unbuffer worker stdout so fly logs shows startup/status prints
- `9466d24` - fix(07-01): force immediate first APScheduler run via next_run_time

## Files Created/Modified
- `fly.toml` - worker process invocation changed from `python -m scripts.ingest_worker` to `python -u -m scripts.ingest_worker`
- `scripts/ingest_worker.py` - `scheduler.add_job(...)` now passes `next_run_time=datetime.now(timezone.utc)` to force the first scheduled run to fire immediately instead of waiting a full `interval_hours`

## Decisions Made
- MongoDB Atlas Network Access opened to 0.0.0.0/0 rather than a tighter allowlist, per the plan's own documented v1 tradeoff (T-07-03) — Fly Machines have no stable outbound IP, and Atlas auth remains the real access-control boundary.
- eBay credentials intentionally NOT set in Fly secrets (D-05) — verified the worker fails loud and recognizably (`KeyError: 'EBAY_CLIENT_ID'`) rather than silently, and that this failure correctly triggers the D-06 staleness alert path.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Worker stdout was fully block-buffered, hiding startup/status prints from `fly logs`**
- **Found during:** Task 2 live verification — `fly logs` showed no worker startup line at all, making it impossible to confirm the worker was running and scheduled (an explicit Task 2 acceptance criterion).
- **Issue:** Python fully block-buffers stdout when writing to a non-TTY pipe (as `fly logs` capture is). The single `print("ingestion worker started — interval_hours=4")` line before `scheduler.start()` (which then blocks forever) never flushed to the log stream.
- **Fix:** Added the `-u` flag to the worker's `python` invocation in `fly.toml` (`python -u -m scripts.ingest_worker`), forcing unbuffered stdout/stderr.
- **Files modified:** `fly.toml`.
- **Verification:** Redeployed; confirmed live in `fly logs` that the startup line now appears immediately, and the worker machine shows a single clean start event with no crash-loop.
- **Committed in:** `2603af9`.

**2. [Rule 1 - Bug] APScheduler's `IntervalTrigger` does not fire its first run immediately without an explicit `next_run_time`**
- **Found during:** Task 2 live verification — after the stdout fix, the worker was visibly running but no `ingestion_runs` document (and no staleness alert) appeared for several minutes post-deploy, contradicting 07-RESEARCH.md's assumption that an unset `start_date` defaults to "now."
- **Issue:** APScheduler 3.11.3's `IntervalTrigger`, left without an explicit `start_date`, computes its first fire time as `now + interval` (verified by reading the installed `apscheduler/triggers/interval.py` source directly), not `now`. In production this meant `scheduled_job()`/`check_and_alert_staleness()` would not run for a full `interval_hours` (~4h) after worker startup — silently delaying both the first real ingestion attempt and the expected credentials-absent staleness alert well past the verification window.
- **Fix:** Added `next_run_time=datetime.now(timezone.utc)` to the `scheduler.add_job(...)` call in `scripts/ingest_worker.py::main()`. This overrides the trigger's own start_date math for the first fire only; every subsequent run still follows the normal `interval_hours` cadence off its own `previous_fire_time`.
- **Files modified:** `scripts/ingest_worker.py`.
- **Verification:** Redeployed; confirmed via a live MongoDB query that `run_ingestion_once()` fired immediately after scheduler start, producing an `ingestion_runs` document with `status="failed"` and the expected `KeyError: 'EBAY_CLIENT_ID'` error, and that the resulting staleness alert reached Discord (human-confirmed "verified" with no secret values present in the message content).
- **Committed in:** `9466d24` (tagged `07-01` in the commit message since it patches code originally introduced in plan 07-01, though the bug itself was discovered during 07-04's live deploy verification).

---

**Total deviations:** 2 auto-fixed (both Rule 1 - bugs surfaced only under live production conditions, not reproducible in local/test environments)
**Impact on plan:** Both fixes were necessary for Task 2's acceptance criteria (worker visibly running in `fly logs`; staleness alert firing within a reasonable verification window) to be met at all. No scope creep — both are narrow, targeted fixes to code paths this plan's verification step directly exercises.

## Issues Encountered
None beyond the two deviations documented above, both resolved and re-verified live before the human's final "verified" confirmation.

## User Setup Required
None beyond what the plan itself specifies as human-only steps (flyctl install/auth, Atlas Network Access UI, `fly secrets set` with real values) — all completed and confirmed by the operator during Task 1/Task 2 execution.

## Next Phase Readiness
- The live host `https://pokemonview.fly.dev` is confirmed reachable over HTTPS (SC-1) and recorded for plan 07-05's `VITE_API_BASE_URL` and future `CORS_ORIGINS` secret.
- Both `web` and `worker` machines are confirmed `started` and stable (SC-2) — no scale-to-zero, no crash-loop.
- The worker's fail-loud/staleness-alert path (D-05/D-06) is proven working end-to-end in production, so adding real eBay credentials later (via `fly secrets set`, which auto-restarts the machines per the plan's `key_links`) needs no further worker-code changes.
- No blockers for plan 07-05 (frontend deploy).

## Threat Flags

None beyond the plan's own `<threat_model>` (T-07-04, T-07-09, T-07-03, T-07-10), all of which were directly exercised and confirmed during live verification (secrets never in transcript/image, HTTPS enforced, Atlas 0.0.0.0/0 accepted as documented tradeoff, worker fail-loud confirmed non-crash-looping).

## Self-Check: PASSED

- FOUND: fly.toml
- FOUND: scripts/ingest_worker.py
- FOUND: .planning/phases/07-launch-hardening-v1-active-price/07-04-SUMMARY.md
- FOUND: 2603af9 (stdout unbuffering fix)
- FOUND: 9466d24 (APScheduler next_run_time fix)

---
*Phase: 07-launch-hardening-v1-active-price*
*Completed: 2026-07-15*
