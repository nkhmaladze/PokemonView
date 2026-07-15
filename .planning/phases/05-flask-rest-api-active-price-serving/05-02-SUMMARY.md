---
phase: 05-flask-rest-api-active-price-serving
plan: 02
subsystem: matching
tags: [pymongo, mongodb, time-series, sample-size]

# Dependency graph
requires:
  - phase: 04-listing-matching-price-normalization
    provides: aggregate_and_write() and the price_points time-series writer contract (D-09/D-10/D-11/D-12)
provides:
  - "listing_count field on every non-empty price_points document written by aggregate_and_write()"
  - "Regression test locking listing_count == len(included)"
affects: [05-04-price-service, 05-05-catalog-service, frontend-price-display]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Additive-only time-series field extension: new key added to insert_one dict, no validator/collMod needed since price_points has no $jsonSchema"]

key-files:
  created: []
  modified:
    - scripts/matching.py
    - tests/test_matching.py

key-decisions:
  - "Option A adopted (per 05-CONTEXT.md/05-RESEARCH.md explicit ask): listing_count = len(included), written alongside existing ts/product_id/item_price/total_price fields — rejected Option B (read-time join from active_listings, deemed fragile) and Option C (ship with no sample-size indicator, deemed an open UX pitfall)"

patterns-established:
  - "Missing listing_count on pre-change price_points documents is treated as null downstream (Plans 05-04/05-05), not backfilled or defaulted to 0"

requirements-completed: [PRICE-01]

coverage:
  - id: D1
    description: "aggregate_and_write() writes listing_count == len(included) on every new price_points document, alongside the existing ts/product_id/item_price/total_price fields"
    requirement: "PRICE-01"
    verification:
      - kind: unit
        ref: "tests/test_matching.py#test_price_points_records_listing_count"
        status: pass
      - kind: unit
        ref: "tests/test_matching.py#test_price_points_median_aggregation"
        status: pass
    human_judgment: false
  - id: D2
    description: "The D-11 gap-on-empty behavior is preserved — no price_points document (and therefore no listing_count) is written when included is empty"
    requirement: "PRICE-01"
    verification:
      - kind: unit
        ref: "tests/test_matching.py#test_price_points_skipped_when_zero_included"
        status: pass
    human_judgment: false

duration: 10min
completed: 2026-07-15
status: complete
---

# Phase 5 Plan 2: Sample-Size Field on price_points Summary

**Added `listing_count` (Option A) to `aggregate_and_write()` so every price_points document records the exact sample size its item/total price medians were computed over, closing the sample-size gap named in 05-RESEARCH.md Pitfall 3.**

## Performance

- **Duration:** ~10 min
- **Completed:** 2026-07-15T02:45:38Z
- **Tasks:** 2 completed
- **Files modified:** 2

## Accomplishments
- `aggregate_and_write()` in `scripts/matching.py` now writes `"listing_count": len(included)` alongside `ts`/`product_id`/`item_price`/`total_price` on every non-empty insert, with an updated docstring documenting Option A's rationale and additive/backward-compatible nature
- New regression test `test_price_points_records_listing_count` locks `listing_count == len(included)` for a 3-listing included set
- Confirmed via RED/GREEN: the new test failed with `KeyError: 'listing_count'` before the implementation change, then passed after it
- Full `tests/test_matching.py` suite (17 tests, including the two named pre-existing tests and the new regression test) stays green — median computation and the D-11 empty-set skip are both unchanged

## Task Commits

Each task was committed atomically:

1. **Task 1: Add listing_count to aggregate_and_write() (Option A)** - `f5cf09d` (feat)
2. **Task 2: Regression test locking listing_count == len(included)** - `bf14f94` (test)

**Plan metadata:** (this commit, to follow)

_Note: TDD order was RED (new test written and confirmed failing) → GREEN (implementation) → commit Task 1 (feat) → re-verify GREEN → commit Task 2 (test), so the per-task commit split matches the plan's `files_modified` grouping (Task 1 = scripts/matching.py, Task 2 = tests/test_matching.py) while still proving the behavior was test-driven._

## Files Created/Modified
- `scripts/matching.py` - `aggregate_and_write()` gains a `listing_count` key in the `insert_one` dict; docstring documents Option A's rationale and additive/backward-compatible contract
- `tests/test_matching.py` - new `test_price_points_records_listing_count` regression test using the existing `matching_db` fixture

## Decisions Made
- Option A adopted exactly as directed by the plan: `listing_count = len(included)`, computed with zero new queries (the `included` list is already available at the `aggregate_and_write()` call site in `run_matching_once`)
- No change to `db/init_collections.py` — `price_points` has no `$jsonSchema` validator, so an additive field needs no `collMod`/schema update
- Missing `listing_count` on price_points documents written before this change is an intentional, distinguishable "n/a for older points" state — downstream Plans 05-04/05-05 treat it as `null`, not `0` or a backfilled value

## Deviations from Plan

None - plan executed exactly as written. The only interpretive choice was ordering the two tasks' internal RED/GREEN steps (test-written-and-confirmed-failing before the implementation edit, even though Task 1 is nominally "the implementation task" and Task 2 is "the test task") — this is a sequencing detail within already-planned task boundaries, not a deviation from any plan requirement, file list, or acceptance criterion.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required. This is a pure application-code change to an already-provisioned MongoDB collection with no validator to update.

## Next Phase Readiness
- `listing_count` is now available on every new price_points document for Plan 05-04 (`price_service.get_current_price`, whole-document read) and Plan 05-05 (`catalog_service.get_product_detail`, sample-size indicator) to consume
- No blockers for subsequent Phase 5 plans

---
*Phase: 05-flask-rest-api-active-price-serving*
*Completed: 2026-07-15*

## Self-Check: PASSED

All created/modified files confirmed present on disk; both task commit hashes (f5cf09d, bf14f94) confirmed in git log.
