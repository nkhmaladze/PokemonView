---
phase: 08-price-history-chart
plan: 02
subsystem: api
tags: [pytest, pymongo, flask, mongodb-timeseries]

# Dependency graph
requires:
  - phase: 08-price-history-chart
    plan: 01
    provides: "get_price_history(db, product_id) service function and GET /products/<product_id>/history route, both implemented and tracer-verified end-to-end"
provides:
  - "Ten new tests pinning get_price_history's and the history route's edges: empty/single-point results, ascending order under scrambled insertion, exact {ts, total_price} element shape, ISO-8601 timestamps, cross-product isolation, stored-precision fidelity, unknown-id 200-empty behaviour, CORS coverage, and the D-06 detail-route regression guard"
  - "Two in-code decision records: get_price_history's unbounded-response assumption (with its revisit trigger) and product_history's no-404 rationale, each citing its source document and the test that pins it"
affects: [08-03-price-history-chart-frontend-polish, 08-04-price-history-chart-integration]

# Actuals (#2632)
actuals:
  tokens: 3334
  tasks: 3
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Docstring-as-decision-record: discretionary decisions (no-404 branch, unbounded series) are recorded directly in the function/route docstring they implement, naming the source document (08-RESEARCH.md Open Question, REQUIREMENTS.md Out of Scope row) and the specific test that pins the behaviour, rather than only in phase docs"

key-files:
  created: []
  modified:
    - tests/test_price_service.py
    - tests/test_api_products.py
    - api/services/price_service.py
    - api/blueprints/products.py

key-decisions:
  - "Confirmed the ascending-order test has teeth per the plan's explicit instruction: temporarily reversed get_price_history's sort direction to -1, re-ran test_price_history_ascending_order (it failed as expected — returned [42.99, 39.99, 36.0, 33.0] instead of the expected ascending sequence), then reverted the sort direction before committing."
  - "Full backend suite (pytest -q) required several retries to pass cleanly. Sibling worktree agents executing 08-03 and 08-04 in wave 2 share the same external MongoDB Atlas pokemonview_test database; 08-04's own plan explicitly gates on a full pytest -q run ('the phase gate for both halves'), so concurrent drop_collection/create_collection calls from overlapping suite runs produced NamespaceExists/CollectionInvalid races and cross-collection data leakage — none of which were caused by this plan's code. Confirmed via isolated scoped runs (tests/test_price_service.py: 12/12 clean; tests/test_api_products.py: 18/18 clean) that this plan's own tests never failed on their own merits. A later full-suite retry, run once sibling agent 08-03 finished, passed clean: 84 passed, 0 failed, 0 errors, 0 skipped."

requirements-completed: [PRICE-07]

coverage:
  - id: D1
    description: "get_price_history returns [] for zero points and a one-element list for exactly one point — neither is an error"
    requirement: "PRICE-07"
    verification:
      - kind: unit
        ref: "tests/test_price_service.py::test_price_history_empty_when_no_points, ::test_price_history_single_point"
        status: pass
    human_judgment: false
  - id: D2
    description: "get_price_history returns points ordered oldest-first from the query's ascending sort, not insertion order — verified with teeth by a temporary sort-direction reversal"
    requirement: "PRICE-07"
    verification:
      - kind: unit
        ref: "tests/test_price_service.py::test_price_history_ascending_order"
        status: pass
    human_judgment: false
  - id: D3
    description: "Every returned element's key set is exactly {ts, total_price}, ts is an ISO-8601 string that round-trips through datetime.fromisoformat, and item_price/listing_count/BSON _id never leak"
    requirement: "PRICE-07"
    verification:
      - kind: unit
        ref: "tests/test_price_service.py::test_price_history_element_shape, ::test_price_history_preserves_stored_precision"
        status: pass
    human_judgment: false
  - id: D4
    description: "get_price_history is scoped to exactly one product_id — a second product's points in the same collection never leak into the result"
    requirement: "PRICE-07"
    verification:
      - kind: unit
        ref: "tests/test_price_service.py::test_price_history_scoped_to_one_product"
        status: pass
    human_judgment: false
  - id: D5
    description: "GET /products/<id>/history returns 200 + [] for both a zero-point catalogued product and an unknown id (never 404), carries an Access-Control-Allow-Origin header, and GET /products/<id> still omits the raw price_points series after the history endpoint exists"
    requirement: "PRICE-07"
    verification:
      - kind: integration
        ref: "tests/test_api_products.py::test_product_history_empty_for_product_with_no_points, ::test_product_history_unknown_id_is_200_empty, ::test_product_history_cors_header_present, ::test_detail_still_omits_raw_series_after_history_endpoint"
        status: pass
    human_judgment: false
  - id: D6
    description: "The unbounded-series volume assumption and the no-404 decision are recorded in the docstrings that implement them, each naming its source and revisit trigger/pinning test"
    requirement: "PRICE-07"
    verification:
      - kind: other
        ref: "api/services/price_service.py get_price_history docstring (cites REQUIREMENTS.md); api/blueprints/products.py product_history docstring (cites 08-RESEARCH.md Open Question 1 and test_product_history_unknown_id_is_200_empty)"
        status: pass
    human_judgment: false

duration: ~35min (commit-to-commit; wall-clock extended by waiting for concurrent sibling test runs to clear, see Issues Encountered)
completed: 2026-08-20
status: complete
---

# Phase 8 Plan 02: Price History Backend Hardening Summary

**Ten new tests pin `get_price_history`'s edges (empty/single/ordering/shape/isolation/precision) and the history route's HTTP boundary (zero-point, unknown-id, CORS, detail-contract regression) against a real MongoDB, and two docstrings now record the discretionary decisions this phase resolved: no 404 branch for an unknown id, and a deliberately unbounded response.**

## Performance

- **Duration:** ~35 min (commit-to-commit)
- **Completed:** 2026-08-20T12:12:48Z
- **Tasks:** 3 (unit contract tests, HTTP-boundary tests, decision-recording docstrings)
- **Files modified:** 4 (0 new, 4 modified)

## Accomplishments

- `tests/test_price_service.py` gained six new unit tests covering `get_price_history`'s empty-result, single-point, ascending-order (verified with teeth via a temporary sort-direction reversal), element-shape (`{ts, total_price}` only), cross-product isolation, and stored-precision-preservation behaviour — all against a real MongoDB time-series collection, no mocks.
- `tests/test_api_products.py` gained four new HTTP-boundary tests: a zero-point product returns `200 []`, an unknown product id also returns `200 []` (deliberately not mirroring the detail route's 404 — resolving 08-RESEARCH.md Open Question 1), the history path carries a CORS header, and the detail route still omits the raw `price_points` series now that a history endpoint exists (D-06 regression guard).
- `api/services/price_service.py`'s `get_price_history` docstring now records the unbounded-response assumption — no limit/window/downsampling, deliberate at the current ~6-points-per-day-per-product volume (REQUIREMENTS.md Out of Scope table) — with an explicit revisit trigger.
- `api/blueprints/products.py`'s `product_history` docstring now records why the route has no not-found branch, citing 08-RESEARCH.md Open Question 1 and naming `test_product_history_unknown_id_is_200_empty` as the test that pins the decision.
- Full backend suite (`pytest -q`) passes clean: **84 passed, 0 failed, 0 errors, 0 skipped.** Frontend suite (`npm test`) passes clean: **44 passed.**

## Task Commits

1. **Task 1 — unit contract tests for `get_price_history`** - `344e2ca` (test)
2. **Task 2 — HTTP-boundary tests for the history route** - `a4cfe3f` (test)
3. **Task 3 — decision-recording docstrings** - `ddbc733` (docs)

**Plan metadata:** commit pending (this SUMMARY, per the orchestrator's post-wave protocol — this worktree agent does not commit STATE.md/ROADMAP.md itself)

## Files Created/Modified

- `tests/test_price_service.py` - Six new tests pinning `get_price_history`'s edges; module docstring extended to note Phase 8 coverage
- `tests/test_api_products.py` - Four new tests pinning the history route's HTTP boundary; module docstring extended
- `api/services/price_service.py` - `get_price_history`'s docstring extended with the unbounded-response assumption and its revisit trigger; no signature or behavior change
- `api/blueprints/products.py` - `product_history`'s docstring extended with the no-404 rationale, citing 08-RESEARCH.md and the pinning test; no signature or behavior change

## Decisions Made

- Confirmed `test_price_history_ascending_order` has teeth per the plan's explicit acceptance criterion: temporarily reversed `get_price_history`'s sort direction from `1` to `-1`, re-ran the test (it failed exactly as expected — `[42.99, 39.99, 36.0, 33.0]` instead of ascending order), then reverted the sort direction before committing. No functional change landed from this step; it exists purely as verification evidence.
- No genuine defects were found in `get_price_history` or `product_history` during Tasks 1-2, so Task 3 made documentation-only edits — no behavior change, per the task's own scope.

## Deviations from Plan

None requiring the standard Rules 1-4 process — plan executed exactly as written. One process-level note:

1. Installed `frontend/node_modules` in this worktree (was absent — a fresh worktree checkout does not carry installed dependencies) so `npm test` could run for Task 3's acceptance criteria. This is setup, not a plan deviation; no `package.json`/`package-lock.json` changes resulted.

**Total deviations:** 0 auto-fixed under Rules 1-4.
**Impact on plan:** None — plan's file-content instructions executed as written.

## Issues Encountered

- **Full-suite (`pytest -q`) verification required multiple retries due to concurrent sibling worktree agents.** This plan runs in wave 2 alongside sibling agents executing 08-03 (frontend-only: `PriceHistoryChart.jsx`) and 08-04 (frontend-only: `ProductDetailPage.jsx`, but its own acceptance criteria explicitly gate on `pytest -q` — "the phase gate for both halves"). Because all three worktree agents share one external MongoDB Atlas `pokemonview_test` database, concurrent `drop_collection`/`create_collection` calls from overlapping full-suite runs produced `NamespaceExists`/`CollectionInvalid` errors and transient cross-collection data races in test files this plan never touched (`test_ingest_worker.py`, `test_matching.py`, `test_catalog_service.py`). Two earlier full-suite attempts failed with exactly this signature (never an assertion failure in this plan's own new tests). Isolated, scoped runs of the files this plan modified were clean throughout: `pytest tests/test_price_service.py -q` (12/12 passed) and `pytest tests/test_api_products.py -q` (18/18 passed), both with 0 skipped. A final full-suite run — started once sibling agent 08-03 finished (worktree lock released) — passed clean: 84 passed, 0 failed, 0 errors, 0 skipped, confirming this plan's changes introduced no regression once given a non-contended run. This mirrors, at multi-agent scale, the single-agent double-invocation race already documented in `08-01-SUMMARY.md`'s Issues Encountered section — a known artifact of DB-backed test isolation under concurrent execution, not a defect in this plan's code.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- The price-history backend's edge cases (empty, single-point, scrambled ordering, unknown id, cross-product isolation, odd-cent precision) are now pinned by named tests against a real MongoDB, closing the two silent-corruption risks 08-RESEARCH.md flagged (RFC-822 timestamp leakage, raw ObjectId leakage).
- The no-404 and unbounded-series decisions are recorded in the code that implements them, so a future reader does not need to re-derive them from phase docs.
- `api/services/price_service.py` and `api/blueprints/products.py` carry no signature or behavior changes from this plan — 08-03 and 08-04 (both frontend-only) can proceed without any backend-contract renegotiation.
- Full backend and frontend suites are both green as of this plan's final commit.

## Self-Check: PASSED

- FOUND: tests/test_price_service.py::test_price_history_empty_when_no_points
- FOUND: tests/test_price_service.py::test_price_history_single_point
- FOUND: tests/test_price_service.py::test_price_history_ascending_order
- FOUND: tests/test_price_service.py::test_price_history_element_shape
- FOUND: tests/test_price_service.py::test_price_history_scoped_to_one_product
- FOUND: tests/test_price_service.py::test_price_history_preserves_stored_precision
- FOUND: tests/test_api_products.py::test_product_history_empty_for_product_with_no_points
- FOUND: tests/test_api_products.py::test_product_history_unknown_id_is_200_empty
- FOUND: tests/test_api_products.py::test_product_history_cors_header_present
- FOUND: tests/test_api_products.py::test_detail_still_omits_raw_series_after_history_endpoint
- FOUND: commit 344e2ca (test)
- FOUND: commit a4cfe3f (test)
- FOUND: commit ddbc733 (docs)

---
*Phase: 08-price-history-chart*
*Completed: 2026-08-20*
