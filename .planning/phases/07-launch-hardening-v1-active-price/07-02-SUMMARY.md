---
phase: 07-launch-hardening-v1-active-price
plan: 02
subsystem: infra
tags: [gunicorn, wsgi, flask, deployment, fly.io]

# Dependency graph
requires:
  - phase: 05-flask-api-serving-layer
    provides: api.app.create_app() application factory (mongodb_uri/db_name env-driven defaults)
provides:
  - gunicorn==26.0.0 pinned dependency (human-approved after package-legitimacy gate)
  - wsgi.py module-level `app` entrypoint resolvable by `gunicorn ... wsgi:app`
affects: [07-03-dockerfile-fly-config, 07-04, 07-05]

# Tech tracking
tech-stack:
  added: [gunicorn==26.0.0]
  patterns: ["wsgi.py as the single designated create_app() call site — no config surface of its own, defers entirely to create_app()'s existing os.environ defaults"]

key-files:
  created: [wsgi.py]
  modified: [requirements.txt]

key-decisions:
  - "Approved gunicorn==26.0.0 package-legitimacy gate (T-07-SC) after human confirmation against pypi.org/project/gunicorn — same telemetry-gap false-positive class already approved 5x prior (pymongo, apscheduler, rapidfuzz, flask, flask-cors)"

patterns-established:
  - "wsgi.py: module-level `app = create_app()`, no arguments passed, no config reading/logging — mirrors project's 'read env only inside a called function' discipline by delegating entirely to create_app()'s internal os.environ reads"

requirements-completed: [SC-1, SC-2]

coverage:
  - id: D1
    description: "gunicorn==26.0.0 approved via blocking-human package-legitimacy gate and pinned in requirements.txt"
    requirement: "SC-1"
    verification:
      - kind: other
        ref: "grep -c 'gunicorn==26.0.0' requirements.txt (returns 1)"
        status: pass
    human_judgment: true
    rationale: "Package-legitimacy approval is an explicit human judgment call (pre-approved by the user for this exact gate per the re-dispatch instructions); not something an automated check can certify on its own."
  - id: D2
    description: "wsgi.py exposes a module-level `app` built from create_app(), resolvable as gunicorn's wsgi:app target"
    requirement: "SC-2"
    verification:
      - kind: other
        ref: "MONGODB_URI=... python3 -c \"import wsgi; assert wsgi.app is not None\" (Flask app object returned)"
        status: pass
      - kind: other
        ref: "grep -c 'from api.app import create_app' wsgi.py && grep -c 'app = create_app()' wsgi.py (both return 1)"
        status: pass
    human_judgment: false

# Metrics
duration: 8min
completed: 2026-07-15
status: complete
---

# Phase 07 Plan 02: Gunicorn Pin + WSGI Entrypoint Summary

**gunicorn==26.0.0 pinned in requirements.txt (human-approved past a package-legitimacy gate) and wsgi.py added as the sole `create_app()` call site gunicorn resolves as `wsgi:app`**

## Performance

- **Duration:** 8 min
- **Started:** 2026-07-15T20:44:00Z (approx)
- **Completed:** 2026-07-15T20:52:00Z
- **Tasks:** 2 (1 checkpoint, 1 auto)
- **Files modified:** 2

## Accomplishments
- Recorded human approval of the gunicorn==26.0.0 package-legitimacy gate (T-07-SC) — pre-approved per this plan's re-dispatch instructions after the user reviewed pypi.org/project/gunicorn and confirmed the SUS/unknown-downloads flag was the same telemetry-gap false-positive pattern already seen 5x prior in this project
- Appended `gunicorn==26.0.0` to `requirements.txt` below `flask-cors==6.0.5`, preserving all 8 prior pins unchanged
- Created `wsgi.py` at the repo root: `from api.app import create_app` + module-level `app = create_app()`, with no arguments passed and no config reading/logging of its own — the single designated construction site for the Fly.io `web` process's `gunicorn --bind 0.0.0.0:8080 --workers 1 --timeout 30 wsgi:app` invocation (wired in Plan 07-03)

## Task Commits

Each task was committed atomically:

1. **Task 1: Package-legitimacy gate — gunicorn==26.0.0 (T-07-SC)** - checkpoint, no code change; gate outcome recorded as **approved** (pre-approved re-dispatch per this plan's dispatch instructions — see Deviations)
2. **Task 2: Pin gunicorn + create wsgi.py entrypoint** - `fa930ab` (feat)

**Plan metadata:** committed alongside this SUMMARY (docs commit, see final commit)

## Files Created/Modified
- `requirements.txt` - appended `gunicorn==26.0.0` exact-version pin (9th pin, all 8 prior pins intact)
- `wsgi.py` - new file; module-level `app = create_app()` gunicorn entrypoint, no new config surface

## Decisions Made
- Recorded the Task 1 package-legitimacy checkpoint as **approved** without re-prompting the human, per this plan's explicit pre-approved-checkpoint dispatch instructions: the human had already reviewed https://pypi.org/project/gunicorn/ and responded "approved" to this exact gate in a prior dispatch whose ephemeral worktree was auto-cleaned before any commit landed (no work was lost — this is a clean re-dispatch, not a reconciliation).

## Deviations from Plan

None — plan executed exactly as written. The only departure from the plan's literal checkpoint flow is procedural, not a code deviation: Task 1's `checkpoint:human-verify` gate was not re-presented to the user in this session because the dispatch context explicitly stated the human had already approved this exact gate in a prior attempt, and instructed recording the outcome and proceeding directly to Task 2. This is documented here per that instruction, not an auto-approval under Rule 1-3 deviation handling.

## Issues Encountered
None. `gunicorn` itself is not installed in this local dev environment (no network package install was performed or required by this plan's acceptance criteria — only the requirements.txt pin and wsgi.py's independent import/construction were verified). The actual `pip install -r requirements.txt` happens inside the Docker build in Plan 07-03.

## User Setup Required
None - no external service configuration required for this plan. (Fly.io secrets/deploy setup is Plan 07-03+ scope.)

## Next Phase Readiness
- `wsgi:app` is now a valid gunicorn target; Plan 07-03 (Dockerfile/fly.toml) can wire `gunicorn --bind 0.0.0.0:8080 --workers 1 --timeout 30 wsgi:app` as the `web` process command with no further application changes needed.
- No blockers or concerns for 07-03.

---
*Phase: 07-launch-hardening-v1-active-price*
*Completed: 2026-07-15*

## Self-Check: PASSED

- FOUND: requirements.txt contains `gunicorn==26.0.0`
- FOUND: wsgi.py
- FOUND: .planning/phases/07-launch-hardening-v1-active-price/07-02-SUMMARY.md
- FOUND: commit fa930ab (feat(07-02): pin gunicorn + add wsgi.py entrypoint)
- FOUND: commit fe6933f (docs(07-02): complete gunicorn pin + wsgi entrypoint plan)
