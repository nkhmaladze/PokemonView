---
phase: quick-260802-l3l
plan: 01
subsystem: ingestion-worker
tags: [discord, alerting, heartbeat, tdd]
status: complete
dependency-graph:
  requires:
    - scripts/ingest_worker.py (check_and_alert_staleness, scheduled_job, D-06/D-07/D-08)
  provides:
    - scripts/ingest_worker.send_heartbeat_if_due
  affects:
    - scripts/ingest_worker.scheduled_job
tech-stack:
  added: []
  patterns:
    - "Debounce derived from existing MongoDB query results (count_documents on ingestion_runs), no new collection or scheduled job"
    - "Discord notification swallow-and-continue discipline (os.environ.get + requests.RequestException catch) mirrored from check_and_alert_staleness"
key-files:
  created: []
  modified:
    - scripts/ingest_worker.py
    - tests/test_staleness_alert.py
decisions:
  - "HEARTBEAT_LOOKBACK_HOURS=24 is a reporting-window constant only, distinct from the UTC-calendar-day debounce logic"
  - "send_heartbeat_if_due wired only into scheduled_job(), never into run_ingestion_once(), so main()'s --once branch stays silent"
metrics:
  duration: ~25min
  completed: 2026-08-02
actuals:
  tokens: 26000
  tasks: 2
  commits: 2
---

# Quick Task 260802-l3l: Add periodic Discord heartbeat to ingest worker Summary

Added a once-per-UTC-calendar-day Discord "still healthy" heartbeat (`:white_check_mark:`) to the ingestion worker, so Discord silence is no longer ambiguous between "everything is fine" and "the worker is dead" — complementing the existing alert-only-on-problem staleness check (`:rotating_light:`).

## What Was Built

**`scripts/ingest_worker.py`:**
- New module constant `HEARTBEAT_LOOKBACK_HOURS = 24` (the heartbeat message's reporting window — not a debounce knob).
- New `send_heartbeat_if_due(db, now=None) -> None`:
  1. Counts `status in ["success", "partial"]` `ingestion_runs` documents since the current UTC day's midnight (`day_start`). Returns immediately unless that count is exactly 1 — this is both the debounce (count ≥ 2 means today's heartbeat already fired) and the "don't confirm health on a bad run" guard (count 0 means the run that just finished wasn't healthy).
  2. Reads `DISCORD_WEBHOOK_URL` via `os.environ.get` and no-ops silently if unset.
  3. Counts healthy runs in the trailing `HEARTBEAT_LOOKBACK_HOURS` window and fetches the most recent healthy run (via `find_one` sorted by `started_at` descending, falling back to `{}` to avoid `AttributeError` on a race).
  4. Normalizes a naive `finished_at`/`started_at` timestamp to UTC-aware (same MongoDB-not-tz-aware precedent already applied in `check_and_alert_staleness`, Phase 04-04).
  5. Builds a message carrying only the trailing-run count, the latest run's `listings_written`/`listings_matched` counts, and an ISO timestamp — never the webhook URL, `MONGODB_URI`, or eBay credentials.
  6. POSTs with a 10s timeout inside a `try`/`except requests.RequestException: pass`.
- `scheduled_job(db)` now calls `send_heartbeat_if_due(db)` after `check_and_alert_staleness(db)`. `run_ingestion_once(db)` and `main()`'s `--once` branch are untouched and remain heartbeat-free.

**`tests/test_staleness_alert.py`:** Appended 7 heartbeat contract tests (module docstring updated to describe the file as the worker's full Discord-notification contract, not staleness-only):
- `test_heartbeat_fires_on_first_healthy_run_of_utc_day`
- `test_heartbeat_not_repeated_within_same_utc_day`
- `test_heartbeat_silent_when_no_healthy_run_today`
- `test_heartbeat_missing_webhook_url_noop`
- `test_heartbeat_post_failure_swallowed`
- `test_scheduled_job_invokes_heartbeat`
- `test_run_ingestion_once_does_not_heartbeat`

## TDD Gate Compliance

RED gate: `21f989f test(quick-260802-l3l): add RED heartbeat contract tests` — 7 new tests fail on `AttributeError: <module 'scripts.ingest_worker'> does not have the attribute 'send_heartbeat_if_due'` (confirmed via `patch.object`/import failures), the 5 pre-existing staleness tests untouched and still passing. No skips (MongoDB reachable throughout).

GREEN gate: `db4e1e4 feat(quick-260802-l3l): add once-per-day Discord heartbeat to ingest worker` — all 12 tests in `tests/test_staleness_alert.py` pass, `tests/test_ingest_worker.py`'s 9 pre-existing tests pass unchanged.

No REFACTOR commit was needed — the implementation matched the plan's action text with no follow-up cleanup required.

## Verification

- `python -m pytest tests/test_staleness_alert.py tests/test_ingest_worker.py -q` — 21 passed.
- `python -m pytest -q` (full suite): first run showed 15 failures/8 errors, all in files unrelated to this change (`test_api_products.py`, `test_catalog_schema.py`, `test_catalog_service.py`, plus `test_matching.py`/`test_ingest_worker.py` tests that had passed cleanly moments earlier in isolation) with `pymongo.errors.CollectionInvalid: collection ... already exists` and `OperationFailure: namespace ... already exists, but with different options` — symptomatic of MongoDB Atlas M0 connection/resource contention under a long (~5-6min) sequential run touching many live-DB fixtures, not a code regression. A second immediate re-run of the exact same full suite passed cleanly: **73 passed in 382s**, confirming the first run's failures were pre-existing environmental flakiness rather than anything introduced by this change.
- `git diff --stat` across both task commits touches exactly the two files the plan specifies: `scripts/ingest_worker.py`, `tests/test_staleness_alert.py`.

## Deployment Status — NOT Deployed

**The heartbeat is implemented and locally tested only. It has NOT been deployed to the live Fly.io worker.** The currently running Fly.io ingestion worker process is still executing the previous version of `scripts/ingest_worker.py` and will NOT send heartbeats until a redeploy (`fly deploy`) is performed. That redeploy is deliberately out of scope for this quick task — no `fly deploy`, `fly secrets`, or any other Fly.io command was run during this task. `fly.toml`/`Dockerfile` were located but not touched or invoked.

## Deviations from Plan

None — plan executed exactly as written. `HEARTBEAT_LOOKBACK_HOURS`, `send_heartbeat_if_due`'s logic order, and the `scheduled_job` wiring all match the plan's `<action>` text directly.

## Self-Check: PASSED

- `scripts/ingest_worker.py` — FOUND (send_heartbeat_if_due present, scheduled_job wired)
- `tests/test_staleness_alert.py` — FOUND (12 tests total: 5 pre-existing + 7 new)
- Commit `21f989f` — FOUND in `git log --oneline`
- Commit `db4e1e4` — FOUND in `git log --oneline`
