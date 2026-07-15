---
phase: 04-listing-matching-price-normalization
plan: 02
subsystem: testing
tags: [pytest, mongodb, matching, nyquist-red]

# Dependency graph
requires:
  - phase: 03-active-listing-ingestion-pipeline
    provides: active_listings/ingestion_locks/ingestion_runs collections, the ingest_db fixture skeleton this plan's matching_db fixture mirrors, and the run_ingestion_once orchestration D-04's counts extend
provides:
  - matching_db pytest fixture (tests/conftest.py) resetting active_listings/price_points/ingestion_runs/ingestion_locks
  - tests/test_matching.py — 14 RED contract tests pinning MATCH-01/02/03 and D-04's behavioral contract for scripts/matching.py
affects: [04-03-normalize-match-exclusion, 04-04-outlier-aggregation-e2e, 04-05-ingest-worker-integration]

# Tech tracking
tech-stack:
  added: []
  patterns: [Nyquist RED-first test scaffold, deferred module-under-test imports inside test bodies, fixture-driven live-MongoDB integration tests]

key-files:
  created: [tests/test_matching.py]
  modified: [tests/conftest.py]

key-decisions:
  - "lot/damaged/counterfeit synthetic titles in the end-to-end test deliberately include ALL of the target product's required_keywords (not just the exclusion trigger phrase) so they resolve deterministically via Tier-1 keyword matching rather than depending on untested Tier-2 fuzzy scoring"
  - "run_matching_once's summary-count contract follows RESEARCH.md's own code example literally: listings_matched counts every match_status='matched' listing (including ones later flagged excluded), listings_excluded counts matched-but-excluded listings (keyword + outlier), listings_unmatched counts the rest"

patterns-established:
  - "Nyquist RED scaffold for Phase 4: tests/test_matching.py authored failing before scripts/matching.py exists, turned GREEN by Plans 04-03/04-04/04-05"

requirements-completed: [MATCH-01, MATCH-02, MATCH-03]

coverage:
  - id: D1
    description: "matching_db pytest fixture added to tests/conftest.py, mirroring ingest_db's skip/teardown skeleton but resetting active_listings/price_points/ingestion_runs/ingestion_locks"
    verification:
      - kind: unit
        ref: "python -c \"import ast; ast.parse(open('tests/conftest.py').read())\" and pytest --collect-only -q (27 tests collected, no regression)"
        status: pass
    human_judgment: false
  - id: D2
    description: "RED unit tests for normalize/match_listing/check_exclusion covering MATCH-01 (keyword-exact, fuzzy-fallback, ambiguous-unmatched) and MATCH-02 (lot/damaged-severe-only/counterfeit/legitimate-bundle-not-flagged)"
    requirement: "MATCH-01, MATCH-02"
    verification:
      - kind: unit
        ref: "tests/test_matching.py::test_match_listing_keyword_exact (collects; RED via ModuleNotFoundError for scripts.matching)"
        status: pass
    human_judgment: false
  - id: D3
    description: "RED unit + integration tests for filter_outliers/aggregate_and_write (MATCH-03) and the run_matching_once/run_ingestion_once end-to-end cases (D-04), consuming matching_db"
    requirement: "MATCH-03"
    verification:
      - kind: integration
        ref: "tests/test_matching.py::test_price_points_median_aggregation (RED via ModuleNotFoundError, proving matching_db fixture resolves)"
        status: pass
    human_judgment: false

duration: 15min
completed: 2026-07-15
status: complete
---

# Phase 4 Plan 2: Nyquist RED Test Scaffold Summary

**Authored `matching_db` pytest fixture plus 14 failing contract tests in `tests/test_matching.py` pinning the full MATCH-01/02/03 + D-04 behavioral contract before `scripts/matching.py` exists.**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-07-15T00:11:30Z
- **Completed:** 2026-07-15T00:18:54Z
- **Tasks:** 3 (Task 2 and 3 committed together as both build `tests/test_matching.py`)
- **Files modified:** 2

## Accomplishments
- Added `matching_db` fixture to `tests/conftest.py`, copying `ingest_db`'s skeleton verbatim (skip-if-`MONGODB_URI`-unset, `try/except: client.close(); raise` setup safety, lazy `init_collections` import, before/after `drop_collection` teardown) and extending the reset set to `active_listings`, `price_points`, `ingestion_runs`, `ingestion_locks`.
- Authored `tests/test_matching.py` with 14 RED tests covering: `normalize()` word-boundary filler stripping, `match_listing()` keyword-exact/fuzzy-fallback/ambiguous-unmatched (MATCH-01, D-01/D-03), `check_exclusion()` lot/damaged-severe-only/counterfeit/legitimate-bundle-not-flagged (MATCH-02, D-06/D-08, Pitfall 1), `filter_outliers()` 2-std-dev exclusion and skip-below-3 (MATCH-03, D-13/D-14), `aggregate_and_write()` independent item/total medians and skip-on-empty (D-09/D-10/D-11/D-12), a full `run_matching_once()` end-to-end pass over a realistic mixed batch (clean/outlier/lot/damaged/counterfeit/ambiguous/nonsense), and `run_ingestion_once()`'s D-04 match-count merge into `ingestion_runs`.
- Verified every module-under-test import is deferred into each test body (`grep '^from scripts.matching import'` returns nothing) — `pytest --collect-only -q` succeeds (27 tests, full suite) before `scripts/matching.py` exists.
- Verified RED failures fail for the correct reason: 13 of 14 new tests fail with `ModuleNotFoundError: No module named 'scripts.matching'`; the D-04 integration test fails with a legitimate assertion error (missing `listings_matched` field on `ingestion_runs`, since `run_ingestion_once` doesn't call `run_matching_once` yet — that wiring is Plan 04-05's job). No fixture-not-found or syntax errors anywhere.
- Confirmed zero regression: all 13 pre-existing tests (`test_catalog_schema.py`, `test_ingest_worker.py`) still pass against the live `pokemonview_test` MongoDB Atlas instance.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add the matching_db fixture to conftest.py** - `4302ea7` (test)
2. **Task 2 + 3: RED unit + integration tests (MATCH-01/02/03, D-04)** - `348dbd2` (test)

_Note: Tasks 2 and 3 both build `tests/test_matching.py` (Task 3 appends to the file Task 2 creates), so they were committed together as a single atomic RED-authoring commit rather than split across a mid-file save point._

## Files Created/Modified
- `tests/conftest.py` - Added `matching_db` fixture (active_listings/price_points/ingestion_runs/ingestion_locks reset)
- `tests/test_matching.py` - New file: 14 RED contract tests for MATCH-01/02/03 and D-04

## Decisions Made
- Committed Task 2 and Task 3 as a single commit since both incrementally build the same file (`tests/test_matching.py`) — no intermediate stable state existed between them that warranted a separate commit boundary.
- In the end-to-end test, gave the lot/damaged/counterfeit synthetic listings full Tier-1-matchable titles (all of `perfect-order_booster_box`'s `required_keywords` present) rather than titles that would fall through to the untested fuzzy tier — keeps the test's expected outcome fully deterministic and decoupled from Tier-2 scoring precision, which is out of scope for this RED-authoring plan.
- Derived the end-to-end test's expected `listings_matched`/`listings_unmatched`/`listings_excluded` counts by tracing RESEARCH.md's own `run_matching_once` code example line-by-line (matched_count counts all `match_status="matched"` listings including later-excluded ones; excluded_count accumulates both keyword-exclusions and outlier-exclusions) rather than assuming a simpler "excluded listings aren't matched" model — this is the literal contract Plan 04-04 is instructed to implement from.

## Deviations from Plan

None - plan executed exactly as written. All acceptance criteria met: `pytest --collect-only -q` exits 0 for both `tests/test_matching.py` alone and the full suite; RED failures are `ModuleNotFoundError`/`ImportError` (not fixture-not-found or syntax errors) except for the one integration test whose contract depends on Plan 04-05's wiring, which fails as a legitimate assertion instead; no top-level `from scripts.matching import` statement exists.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required. (Note: `rapidfuzz==3.14.5` install, gated behind a `checkpoint:human-verify`, is Plan 04-01's scope, not this plan's — Plan 04-01 has not yet executed but does not block this RED-authoring plan since `depends_on: []`.)

## Next Phase Readiness
- `tests/test_matching.py` and the `matching_db` fixture are in place and collectible — Plan 04-03 (Wave 2) can now implement `normalize()`, `match_listing()`, `check_exclusion()` to turn the MATCH-01/MATCH-02 unit tests GREEN.
- Plan 04-04 (Wave 3) turns `filter_outliers()`, `aggregate_and_write()`, and `run_matching_once()` GREEN against this same file.
- Plan 04-05 (Wave 4) wires `run_matching_once` into `scripts/ingest_worker.py`'s `run_ingestion_once()` to turn `test_run_ingestion_once_records_match_counts` GREEN.
- Plan 04-01 (rapidfuzz install, blocking human-verify checkpoint) still needs to run before Plan 04-03's Tier-2 fuzzy fallback can import `rapidfuzz` — noted as a blocker for that plan, not this one.

---
*Phase: 04-listing-matching-price-normalization*
*Completed: 2026-07-15*
