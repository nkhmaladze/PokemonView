---
phase: 03-active-listing-ingestion-pipeline
plan: 03
subsystem: testing
tags: [pytest, pymongo, tdd-scaffold, ingestion]

# Dependency graph
requires:
  - phase: 03-active-listing-ingestion-pipeline (Plan 03-02)
    provides: active_listings/ingestion_locks/ingestion_runs collections via db.init_collections.init_collections
provides:
  - ingest_db pytest fixture (tests/conftest.py) targeting the three ingestion collections
  - Five RED, REQ-tagged tests in tests/test_ingest_worker.py for INGEST-01/02/03
affects: [03-04 (worker implementation, turns these tests GREEN), 03-05 (live Production verification)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Wave-0 scaffold-first testing: author fixture + REQ-tagged tests RED before the implementation module exists, with all imports of the not-yet-existing module deferred into test/fixture bodies so pytest --collect-only stays green"

key-files:
  created: [tests/test_ingest_worker.py]
  modified: [tests/conftest.py]

key-decisions:
  - "ingest_db fixture mirrors catalog_db structurally but targets active_listings/ingestion_locks/ingestion_runs and does not seed catalog data, since these tests need no products/price_points"
  - "Used exactly-representable float values (50.00, 4.50, 54.50) in test_price_and_shipping_captured to keep == float assertions safe rather than approx comparisons"

patterns-established:
  - "Pattern: lazy-import the not-yet-existing implementation module inside every test/fixture body (never at module top level) so pytest --collect-only succeeds ahead of the implementing plan"

requirements-completed: [INGEST-01, INGEST-02, INGEST-03]

coverage:
  - id: D1
    description: "ingest_db fixture added to tests/conftest.py, bootstrapping active_listings/ingestion_locks/ingestion_runs on pokemonview_test and skipping gracefully when MONGODB_URI is unset"
    verification:
      - kind: other
        ref: "python -c \"import ast; ...\" fixture-presence assertion (03-03-PLAN.md Task 1 automated verify)"
        status: pass
      - kind: integration
        ref: "python -m pytest tests/test_ingest_worker.py::test_lock_prevents_concurrent_acquire -q (fixture connects live to Atlas; collection/teardown proven, worker import RED as expected)"
        status: pass
    human_judgment: false
  - id: D2
    description: "tests/test_ingest_worker.py defines five REQ-tagged tests (build_query, price+shipping, upsert idempotency, lock concurrency, run-skips-when-locked) covering INGEST-01/02/03, intentionally RED pending Plan 03-04's worker implementation"
    requirement: "INGEST-01, INGEST-02, INGEST-03"
    verification:
      - kind: unit
        ref: "python -m pytest tests/test_ingest_worker.py --collect-only -q (5 tests collected)"
        status: pass
    human_judgment: true
    rationale: "Tests are intentionally RED at this scaffold stage (scripts.ingest_worker does not exist until Plan 03-04) — a human/future plan must confirm they turn GREEN once the worker lands, not this plan"

duration: 2min
completed: 2026-07-14
status: complete
---

# Phase 3 Plan 3: Ingest Worker Test Scaffold Summary

**Wave-0 RED test scaffold for the active-listing ingestion worker — `ingest_db` fixture plus five REQ-tagged pytest tests for INGEST-01/02/03, all collectible and intentionally failing until Plan 03-04 implements `scripts/ingest_worker.py`**

## Performance

- **Duration:** 2 min
- **Started:** 2026-07-14T22:11:17Z
- **Completed:** 2026-07-14T22:13:26Z
- **Tasks:** 2 completed
- **Files modified:** 2 (1 modified, 1 created)

## Accomplishments
- Added an `ingest_db` pytest fixture to `tests/conftest.py`, mirroring the existing `catalog_db` fixture but targeting `active_listings`/`ingestion_locks`/`ingestion_runs` on the throwaway `pokemonview_test` database, with graceful skip when `MONGODB_URI` is unset
- Created `tests/test_ingest_worker.py` with five plain-`assert` tests (`test_build_query`, `test_price_and_shipping_captured`, `test_upsert_idempotent`, `test_lock_prevents_concurrent_acquire`, `test_run_ingestion_once_skips_when_locked`), each REQ-tagged for INGEST-01/02/03 in the module docstring
- Confirmed `pytest --collect-only` is clean both for the new file alone (5 tests) and the whole suite (9 tests total, Phase 2's 4 catalog tests unaffected)
- Confirmed all five new tests currently fail with `ModuleNotFoundError`/`ImportError` on `scripts.ingest_worker` — the correct, intended RED state ahead of Plan 03-04

## Task Commits

Each task was committed atomically:

1. **Task 1: Add the ingest_db fixture to tests/conftest.py** - `aa30bf5` (test)
2. **Task 2: Create tests/test_ingest_worker.py with the five RED REQ-tagged tests** - `9eb3e45` (test)

**Plan metadata:** (this commit)

## Files Created/Modified
- `tests/conftest.py` - Added `ingest_db` fixture (mirrors `catalog_db`; targets active_listings/ingestion_locks/ingestion_runs; skips when MONGODB_URI unset; `catalog_db` preserved unchanged)
- `tests/test_ingest_worker.py` - Five REQ-tagged RED tests covering INGEST-01 (build_query), INGEST-02 (upsert idempotency, TTL lock, skip-when-locked), INGEST-03 (price+shipping capture)

## Decisions Made
- Mirrored `catalog_db`'s exact structure for `ingest_db` (skip guard, try/except cleanup-on-setup-failure, before/after drop_collection, lazy `init_collections` import) per 03-PATTERNS.md, rather than inventing a new fixture shape
- Used exactly-representable IEEE-754 float literals (50.00, 4.50, 54.50) in `test_price_and_shipping_captured` so `==` comparisons are safe, avoiding `pytest.approx` noise for values that don't need it
- `test_run_ingestion_once_skips_when_locked` monkeypatches `ingest_worker.get_app_token`/`ingest_worker.search_sealed_listings` to raise `AssertionError` if called, which is the strongest available proof (short of live network interception) that the skip-when-locked path makes zero eBay calls

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None. `MONGODB_URI` was available in the environment, so the `ingest_db` fixture's live-connection path (bootstrap + drop/teardown) exercised successfully during the RED run — it fails only at the `from scripts.ingest_worker import ...` line inside each test body, exactly as designed, not at fixture setup.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `tests/test_ingest_worker.py` and the `ingest_db` fixture are the concrete, automated feedback contract Plan 03-04 will turn GREEN by implementing `scripts/ingest_worker.py` (`build_query`, `upsert_listings`, `ensure_lock_index`/`acquire_lock`/`release_lock`, `run_ingestion_once`, `main()`)
- No blockers for Plan 03-04: MongoDB Atlas is reachable, the three ingestion collections already exist (Plan 03-02), and the eBay-credential gap (STATE.md Blockers) does not block Plan 03-04's non-live implementation/unit-test work — only the separate live-verification task (Plan 03-05) needs restored `EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET`

---
*Phase: 03-active-listing-ingestion-pipeline*
*Completed: 2026-07-14*

## Self-Check: PASSED

- FOUND: tests/conftest.py
- FOUND: tests/test_ingest_worker.py
- FOUND: .planning/phases/03-active-listing-ingestion-pipeline/03-03-SUMMARY.md
- FOUND commit: aa30bf5
- FOUND commit: 9eb3e45
