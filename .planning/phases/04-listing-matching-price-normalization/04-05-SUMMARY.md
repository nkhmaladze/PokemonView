---
phase: 04-listing-matching-price-normalization
plan: 05
subsystem: ingestion
tags: [matching, pymongo, integration, ingestion-worker]

# Dependency graph
requires:
  - phase: 04-listing-matching-price-normalization
    provides: "scripts/matching.py's run_matching_once(db, run_id, ts) -> {listings_matched, listings_unmatched, listings_excluded} (Plan 04-04)"
provides:
  - "scripts/ingest_worker.py: run_ingestion_once() invokes run_matching_once() as a second stage after the fetch loop, merging D-04 match counts onto ingestion_runs"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: [decoupled second-stage orchestration call (fetch stage then matching stage, never interleaved per-listing), zero-initialized aggregate counts before try/finally to guarantee finally-block safety]

key-files:
  created: []
  modified: [scripts/ingest_worker.py]

key-decisions:
  - "None beyond the plan as written — implementation matched the plan's action text and 04-PATTERNS.md's insertion point exactly"

requirements-completed: [MATCH-01, MATCH-02, MATCH-03]

coverage:
  - id: D1
    description: "run_ingestion_once() calls run_matching_once(db, run_id, started_at) exactly once, as a second stage after the per-product fetch loop completes (never per-listing inside the loop), and the resulting ingestion_runs document carries flat top-level integer fields listings_matched/listings_unmatched/listings_excluded merged from run_matching_once's return dict (D-04)"
    requirement: "MATCH-01"
    verification:
      - kind: integration
        ref: "tests/test_matching.py::test_run_ingestion_once_records_match_counts"
        status: pass
    human_judgment: false
  - id: D2
    description: "All existing Phase 3 test_ingest_worker.py tests remain green (happy-path, partial-on-error, skip-when-locked, upsert idempotency, lock semantics) — matching activation does not regress INGEST-01/02/03, and the skipped_locked path never calls run_matching_once"
    requirement: "MATCH-01"
    verification:
      - kind: unit
        ref: "tests/test_ingest_worker.py (9 tests)"
        status: pass
    human_judgment: false
  - id: D3
    description: "No circular import between scripts.ingest_worker and scripts.matching in either import order"
    verification:
      - kind: other
        ref: "python -c \"import scripts.ingest_worker, scripts.matching\" and reverse order, both exit 0"
        status: pass
    human_judgment: false

duration: 5min
completed: 2026-07-15
status: complete
---

# Phase 4 Plan 5: Ingestion Worker Matching Integration Summary

**Wired `run_matching_once()` into `run_ingestion_once()` as a second, decoupled stage after the fetch loop, merging D-04's flat match-count fields onto the `ingestion_runs` document — the activation point that makes MATCH-01/02/03 run in the live pipeline.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-07-15T00:41:44Z
- **Completed:** 2026-07-15T00:46:24Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Added a top-level `from scripts.matching import run_matching_once` import to `scripts/ingest_worker.py`; confirmed no circular import in either import order (verified live, not just by inspection of Plan 04-04's deferred-import note).
- `run_ingestion_once()` now calls `match_counts = run_matching_once(db, run_id, started_at)` once, immediately after the `for product in CATALOG:` fetch loop finishes and `status` is set — never per-listing inside the loop (04-PATTERNS.md Performance Trap avoided).
- `match_counts` is pre-initialized to `{"listings_matched": 0, "listings_unmatched": 0, "listings_excluded": 0}` before the outer `try` block, so the `finally` block can never raise `NameError` even if an exception aborts the run before the matching call executes (e.g. `get_app_token()` failure).
- The `finally` block's `update_doc` gains three flat top-level integer fields (`listings_matched`, `listings_unmatched`, `listings_excluded`) sourced from `match_counts` — no nested sub-document, no new collection (D-04).
- The skip-when-locked early-return path is untouched and does not reference `run_matching_once` at all — a skipped run issues zero eBay calls and zero matching calls, confirmed by `test_run_ingestion_once_skips_when_locked` still passing.
- `test_run_ingestion_once_records_match_counts` (the last remaining RED test from Plan 04-04) is now GREEN, and all 9 existing `tests/test_ingest_worker.py` tests remain green — no regression to INGEST-01/02/03.
- Full test suite (`pytest -q`, all 27 tests across Phase 2/3/4) passes with 0 failures.

## Task Commits

Each task was committed atomically:

1. **Task 1: Call run_matching_once from run_ingestion_once and record D-04 counts** - `e57d986` (feat)

## Files Created/Modified
- `scripts/ingest_worker.py` - Added top-level `run_matching_once` import; `run_ingestion_once()` now invokes it as a second stage after the fetch loop and merges its returned counts into the `ingestion_runs` update document

## Decisions Made
None - plan executed exactly as written. The insertion point, zero-initialization strategy, and flat-field convention matched 04-PATTERNS.md and the plan's action text exactly; no adaptation was required.

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 4 (listing-matching-price-normalization) is now complete: `scripts/matching.py` exposes the full MATCH-01/02/03 pipeline (`normalize`, `match_listing`, `check_exclusion`, `filter_outliers`, `aggregate_and_write`, `run_matching_once`), and `scripts/ingest_worker.py`'s `run_ingestion_once()` activates it as a live second stage on every scheduled ingestion cycle, recording per-run match-health counts on `ingestion_runs` (D-04, ROADMAP SC-1 "match results inspectable").
- Manual/CI live-credential verification (`python -m scripts.ingest_worker --once` against real eBay Production credentials) remains deferred — EBAY_CLIENT_ID/EBAY_CLIENT_SECRET are still absent from `.env` per the Phase 1/3 blocker recorded in STATE.md. This mirrors Phase 3's own precedent (03-05) and does not block phase completion; the automated integration test proves the wiring end-to-end against the live-MongoDB `matching_db` fixture.
- No blockers carried forward from this plan.

---
*Phase: 04-listing-matching-price-normalization*
*Completed: 2026-07-15*

## Self-Check: PASSED

- FOUND: scripts/ingest_worker.py
- FOUND: .planning/phases/04-listing-matching-price-normalization/04-05-SUMMARY.md
- FOUND commit: e57d986
