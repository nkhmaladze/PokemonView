---
phase: 03-active-listing-ingestion-pipeline
plan: 04
subsystem: infra
tags: [pymongo, apscheduler, mongodb-ttl-lock, ebay-browse-api, idempotent-upsert]

# Dependency graph
requires:
  - phase: 03-active-listing-ingestion-pipeline (Plan 03-01/02/03)
    provides: apscheduler==3.11.3 dependency approval, active_listings/ingestion_locks/ingestion_runs collection bootstrap (db/init_collections.py), the five RED contract tests (tests/test_ingest_worker.py) and ingest_db fixture
  - phase: 01-ebay-api-feasibility-gate
    provides: scripts/ebay_client.py (get_app_token, search_sealed_listings, total_cost)
  - phase: 02-product-catalog-data-model
    provides: scripts/catalog_data.CATALOG, deterministic product slug pattern
provides:
  - scripts/ingest_worker.py — the phase's core deliverable (build_query, PRODUCT_TYPE_SEARCH_TERMS, ensure_lock_index, acquire_lock, release_lock, upsert_listings, run_ingestion_once, main)
  - Idempotent upsert-by-itemId writes into active_listings capturing item_price/shipping_cost/total_price
  - MongoDB TTL lock (ingestion_locks) guarding cross-process overlap
  - run_ingestion_once orchestration writing per-run ingestion_runs metadata
  - main() with --once (manual/CI) and BlockingScheduler+IntervalTrigger (scheduled) entrypoints
  - .env.example documents optional INGESTION_INTERVAL_HOURS (default 4)
affects: [04-listing-matching-normalization, 07-observability-alerting]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "MongoDB TTL lock document (find_one_and_update + DuplicateKeyError catch) as the cross-process concurrency guard, not just APScheduler's in-process max_instances"
    - "bulk_write([UpdateOne(_id=itemId, upsert=True)]) for idempotent listing writes, mirroring scripts/seed_catalog.py's products upsert pattern"
    - "apscheduler imported lazily inside main() only, so the module imports cleanly without the scheduler dependency installed"

key-files:
  created:
    - scripts/ingest_worker.py
  modified:
    - .env.example

key-decisions:
  - "Extracted access_token = token['access_token'] from get_app_token()'s dict return before calling search_sealed_listings(access_token, query), matching ebay_client.py's actual function signature (str, not dict) rather than the plan action text's shorthand 'token' naming"
  - "shipping_cost computed as round(total_cost(item) - item_price, 2) so total_price is always exactly total_cost(item) — the single source of truth already proven in ebay_client.py — rather than re-deriving shipping from shippingOptions independently"

requirements-completed: [INGEST-01, INGEST-02, INGEST-03]

coverage:
  - id: D1
    description: "build_query(product) returns 'Pokemon {set_name} {product-type phrase}' without joining required_keywords"
    requirement: "INGEST-01"
    verification:
      - kind: unit
        ref: "tests/test_ingest_worker.py#test_build_query"
        status: pass
    human_judgment: false
  - id: D2
    description: "upsert_listings writes item_price, shipping_cost (default 0.0), and total_price per listing, keyed by itemId, idempotently"
    requirement: "INGEST-03"
    verification:
      - kind: integration
        ref: "tests/test_ingest_worker.py#test_price_and_shipping_captured"
        status: pass
      - kind: integration
        ref: "tests/test_ingest_worker.py#test_upsert_idempotent"
        status: pass
    human_judgment: false
  - id: D3
    description: "acquire_lock/release_lock over ingestion_locks block a second concurrent acquire and support re-acquisition after release"
    requirement: "INGEST-02"
    verification:
      - kind: integration
        ref: "tests/test_ingest_worker.py#test_lock_prevents_concurrent_acquire"
        status: pass
    human_judgment: false
  - id: D4
    description: "run_ingestion_once makes zero eBay calls and writes a status=skipped_locked ingestion_runs doc when the lock is already held"
    requirement: "INGEST-02"
    verification:
      - kind: integration
        ref: "tests/test_ingest_worker.py#test_run_ingestion_once_skips_when_locked"
        status: pass
    human_judgment: false
  - id: D5
    description: "main() supports --once for manual/CI runs and a BlockingScheduler+IntervalTrigger for scheduled runs (default INGESTION_INTERVAL_HOURS=4), with a real live Production run against real eBay credentials"
    requirement: "INGEST-01"
    verification: []
    human_judgment: true
    rationale: "EBAY_CLIENT_ID/EBAY_CLIENT_SECRET are not present in this environment's .env (lost in a prior incident per STATE.md Blockers) — main()'s scheduler/--once wiring is proven correct by source inspection and the unit/integration suite, but a live Production run against real eBay listings has not been executed. This is explicitly deferred to Plan 03-05 (live verification) per 03-RESEARCH.md's Open Question 1 resolution."

# Metrics
duration: 4min
completed: 2026-07-14
status: complete
---

# Phase 3 Plan 4: Active-Listing Ingestion Worker Summary

**Built scripts/ingest_worker.py — the lock-guarded, idempotent ingestion worker (build_query, MongoDB TTL lock, upsert_listings, run_ingestion_once, main with --once/APScheduler) that turns all five Plan 03-03 RED tests GREEN.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-07-14T22:17:48Z
- **Completed:** 2026-07-14T22:21:15Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments
- `build_query`, `ensure_lock_index`, `acquire_lock`, `release_lock`, and `upsert_listings` implemented, reusing `ebay_client.total_cost` as the single source of truth for item+shipping math
- `run_ingestion_once` orchestrates the full locked run: skip-with-metadata when the lock is held (zero eBay calls), otherwise fetch-token-once, per-product search+upsert with per-product error isolation, run-metadata write, and guaranteed lock release in `finally`
- `main()` supports `--once` (single manual/CI run) and a default `BlockingScheduler` + `IntervalTrigger` firing every `INGESTION_INTERVAL_HOURS` (default 4), with graceful SIGTERM/SIGINT shutdown; `apscheduler` is imported lazily only inside `main()`
- All five tests in `tests/test_ingest_worker.py` pass GREEN; full suite (9 tests, including Phase 2's `test_catalog_schema.py`) passes with no regression
- `.env.example` documents the optional `INGESTION_INTERVAL_HOURS` knob via blind append (file never read)

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement build_query, the MongoDB lock functions, and upsert_listings** - `d466a16` (feat)
2. **Task 2: Implement run_ingestion_once orchestration with lock + run-metadata** - `1ba065f` (feat)
3. **Task 3: Add main() with --once and the APScheduler IntervalTrigger entrypoint; document INGESTION_INTERVAL_HOURS** - `758a2ec` (feat)

_Note: tdd="true" tasks (1 and 2) were verified RED-then-GREEN inline (the five tests were already authored RED in Plan 03-03; each task's implementation turned its assigned subset GREEN before committing), rather than producing separate test/feat commit pairs, since the test file itself was Plan 03-03's deliverable._

## Files Created/Modified
- `scripts/ingest_worker.py` - New file: the complete ingestion worker (build_query, PRODUCT_TYPE_SEARCH_TERMS, ensure_lock_index, acquire_lock, release_lock, upsert_listings, run_ingestion_once, main)
- `.env.example` - Appended INGESTION_INTERVAL_HOURS documentation (blind append only)

## Decisions Made
- Extracted `access_token = token["access_token"]` from `get_app_token()`'s dict return before calling `search_sealed_listings(access_token, query)` — the plan's action text used shorthand ("token") but `ebay_client.py`'s actual signature requires a bearer-token string, not the full OAuth response dict. Matching the real reused function signature over literal plan phrasing.
- `shipping_cost` is derived as `round(total_cost(item) - item_price, 2)` so `total_price` always equals `ebay_client.total_cost(item)` exactly — avoids maintaining two independent shipping-extraction code paths that could drift.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected search_sealed_listings call to pass the bearer-token string, not the raw OAuth response dict**
- **Found during:** Task 2 (run_ingestion_once implementation)
- **Issue:** The plan's action text said `token = get_app_token()` then `search_sealed_listings(token, query)`, but `scripts/ebay_client.py`'s actual signature is `search_sealed_listings(access_token: str, query: str, ...)` — `get_app_token()` returns a dict (`{access_token, expires_in, token_type}`), not a string. Passing the dict directly would build a malformed `Authorization: Bearer {...}` header on every live call.
- **Fix:** Extract `access_token = token["access_token"]` immediately after `get_app_token()` and pass `access_token` to `search_sealed_listings`.
- **Files modified:** scripts/ingest_worker.py
- **Verification:** `test_run_ingestion_once_skips_when_locked` passes (monkeypatches both functions so this path isn't live-exercised by the current test suite, but the corrected signature matches `ebay_client.py`'s contract exactly, verified by direct comparison of both function signatures).
- **Committed in:** `1ba065f` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Necessary correctness fix to match the already-implemented `ebay_client.py` contract; no scope creep, no architectural change.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required. Note: a genuine live Production run against real eBay listings (main()'s `--once` path with real `EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET`) has NOT been performed in this environment, since those credentials are not currently present in `.env` (per STATE.md Blockers, lost in a prior incident). This is explicitly Plan 03-05's scope (live verification), not silently claimed done here.

## Next Phase Readiness
- `scripts/ingest_worker.py` is complete and fully unit/integration tested (5/5 Plan 03-03 tests green, 9/9 full suite green)
- Plan 03-05 (live verification) can now proceed once `EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET` are available, using `python -m scripts.ingest_worker --once`
- No writes to `price_points` anywhere in this file — confirmed via source grep — preserving Phase 4's exclusive ownership of that collection's `product_id`-matched writes

---
*Phase: 03-active-listing-ingestion-pipeline*
*Completed: 2026-07-14*
