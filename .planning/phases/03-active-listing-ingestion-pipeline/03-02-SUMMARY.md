---
phase: 03-active-listing-ingestion-pipeline
plan: 02
subsystem: database
tags: [mongodb, pymongo, ttl-index, time-series, schema-bootstrap]

# Dependency graph
requires:
  - phase: 02-product-catalog-data-model
    provides: db/init_collections.py with products ($jsonSchema validator) and price_points (native time-series collection) bootstrap
provides:
  - "active_listings collection bootstrap (plain, non-unique product_ref index)"
  - "ingestion_locks collection bootstrap (plain, TTL index on expires_at, expireAfterSeconds=0)"
  - "ingestion_runs collection bootstrap (plain, descending started_at index)"
  - "Corrected docstrings attributing price_points to Phase 4's matching step, not Phase 3"
affects: [03-03-ingest-worker-core, 03-04-locking-and-upsert, ingestion-worker, matching-service]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Idempotent create-if-absent guard (if name not in db.list_collection_names(): db.create_collection(...)) replicated for three new collections"
    - "create_index() called unconditionally after the guard block (idempotent by design, no guard needed)"

key-files:
  created: []
  modified:
    - db/init_collections.py

key-decisions:
  - "TDD verification for this plan was done via inline RED/GREEN runs of the plan's own automated verify command plus a live check against the real pokemonview_test MongoDB database (create collections, inspect index shapes, re-run for idempotency), rather than a separate committed pytest file — the plan's own files_modified scope is limited to db/init_collections.py, and Plan 03-03 owns the persisted ingest_db fixture/tests per this plan's acceptance criteria."

patterns-established:
  - "Plain (non-timeseries, non-validated) collections for raw/operational data (active_listings, ingestion_locks, ingestion_runs) are bootstrapped with the same create-if-absent guard as products/price_points, keeping all schema bootstrap logic centralized in db/init_collections.py"

requirements-completed: [INGEST-01, INGEST-02, INGEST-03]

coverage:
  - id: D1
    description: "init_collections(db) idempotently creates active_listings (plain collection, non-unique product_ref index)"
    requirement: "INGEST-03"
    verification:
      - kind: integration
        ref: "live run against real pokemonview_test MongoDB — init_collections() called twice, list_collection_names() and index_information() inspected"
        status: pass
      - kind: unit
        ref: "python -c source-inspection assertion (plan's <verify> automated command)"
        status: pass
    human_judgment: false
  - id: D2
    description: "init_collections(db) idempotently creates ingestion_locks with a TTL index on expires_at (expireAfterSeconds=0)"
    requirement: "INGEST-02"
    verification:
      - kind: integration
        ref: "live run against real pokemonview_test MongoDB — index_information() confirms key=[('expires_at',1)], expireAfterSeconds=0"
        status: pass
    human_judgment: false
  - id: D3
    description: "init_collections(db) idempotently creates ingestion_runs with a descending index on started_at"
    requirement: "INGEST-01"
    verification:
      - kind: integration
        ref: "live run against real pokemonview_test MongoDB — index_information() confirms key=[('started_at',-1)]"
        status: pass
    human_judgment: false
  - id: D4
    description: "Re-running init_collections is idempotent and does not disturb existing products/price_points collections"
    verification:
      - kind: integration
        ref: "live run: init_collections() called twice, collection counts unchanged, products and price_points still present"
        status: pass
      - kind: unit
        ref: "pytest tests/ -q (existing suite, 4 passed)"
        status: pass
    human_judgment: false
  - id: D5
    description: "price_points docstrings corrected to attribute Phase 4 (matching step) as the writer, not Phase 3's ingestion worker; active_listings/ingestion_locks/ingestion_runs documented as Phase 3's actual write targets"
    verification:
      - kind: unit
        ref: "python -c docstring-content assertion (plan's <verify> automated command); git diff confirmed docstring/comment-only lines"
        status: pass
    human_judgment: false

duration: 2min
completed: 2026-07-14
status: complete
---

# Phase 3 Plan 2: Ingestion Collection Bootstrap Summary

**Extended `db/init_collections.py` to idempotently bootstrap `active_listings`, `ingestion_locks` (TTL on `expires_at`), and `ingestion_runs` (descending `started_at` index), and corrected stale docstrings that mislabeled `price_points` as Phase 3's write target instead of Phase 4's.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-07-14T22:05:00Z (approx.)
- **Completed:** 2026-07-14T22:06:30Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- `init_collections(db)` now provisions three new plain collections — `active_listings` (with a non-unique `product_ref` index), `ingestion_locks` (with a TTL index on `expires_at`, `expireAfterSeconds=0`), and `ingestion_runs` (with a descending `started_at` index) — alongside the unchanged `products`/`price_points` setup
- Verified idempotency and index shapes live against the real `pokemonview_test` MongoDB database (two consecutive `init_collections()` calls, no errors, no duplicate collections/indexes)
- Corrected the module docstring, `PRICE_POINTS_TIMESERIES_OPTIONS` comment, and `init_collections` docstring so `price_points` is now correctly attributed to Phase 4's matching step (not Phase 3's ingestion worker), and the three new collections are documented as Phase 3's actual write targets

## Task Commits

Each task was committed atomically:

1. **Task 1: Add active_listings, ingestion_locks (TTL), and ingestion_runs collections to init_collections** - `6538f49` (feat)
2. **Task 2: Correct the module/collection docstrings so price_points is no longer mislabeled as Phase 3's target** - `70c6f48` (docs)

**Plan metadata:** (this commit, follows)

_Note: Task 1 was tdd="true" in the plan; RED/GREEN was executed inline via the plan's own `<verify>` automated command (run before the edit — failed as expected; run after the edit — passed) plus a live MongoDB integration check, rather than as a separate committed test file, since the plan's `files_modified` scope is limited to `db/init_collections.py` and the persisted `ingest_db` pytest fixture/tests are explicitly Plan 03-03's scope per this plan's own acceptance criteria._

## Files Created/Modified
- `db/init_collections.py` - Extended `init_collections(db)` to bootstrap `active_listings`, `ingestion_locks`, `ingestion_runs` collections/indexes; added `DESCENDING` to the pymongo import; corrected `price_points`-related docstrings/comments to attribute Phase 4 as the writer

## Decisions Made
- TDD for Task 1 was executed via inline RED/GREEN runs of the plan's own automated verify command (source-inspection assertion) plus a live-MongoDB integration check against `pokemonview_test`, rather than authoring a separate committed pytest test file — this respects the plan's declared `files_modified: [db/init_collections.py]` scope and Plan 03-03's ownership of the persisted `ingest_db` fixture/tests (per this plan's own acceptance criteria: "proven by Plan 03-03's ingest_db fixture + tests")

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `active_listings`, `ingestion_locks`, and `ingestion_runs` collections and their indexes are now provisioned via `init_collections(db)`, unblocking Plan 03-03 (ingest worker core) and Plan 03-04 (locking/upsert), both of which write into these collections
- `price_points` remains correctly reserved and untouched, ready for Phase 4's matching step
- No blockers for subsequent Phase 3 plans

---
*Phase: 03-active-listing-ingestion-pipeline*
*Completed: 2026-07-14*

## Self-Check: PASSED

All claimed files and commits verified present on disk / in git history.
