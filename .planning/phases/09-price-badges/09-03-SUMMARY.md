---
phase: 09-price-badges
plan: 03
subsystem: pricing
tags: [flask, pymongo, mongodb-aggregation, pytest]

# Dependency graph
requires: ["09-01"]
provides:
  - "price_service.get_all_time_range(db, product_id) — a $min/$max aggregation returning {high, low} or None only on zero price_points documents ever (mirrors get_current_price's D-01 contract, NOT get_trend_baseline's tolerance-window contract)"
  - "catalog_service.get_product_detail now assembles all_time_range on both the normal path and the zero-data early-return branch"
  - "GET /products/<id> detail response carries all_time_range: {high, low, status} alongside current_price/trend_24h/trend_7d/trend_30d"
affects: [09-04, 09-05]

# Actuals (#2632)
actuals:
  tokens: 3625
  tasks: 2
  commits: 2

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "get_all_time_range mirrors get_current_price's None-only-on-zero-documents contract rather than get_trend_baseline's None-on-out-of-tolerance-window contract — a single stored point is real data (high == low), never insufficient_data"
    - "all_time_range assembled as a standalone block after the trend_24h block in get_product_detail, following the same status-first, no-extra-gate pattern as the trend fields"

key-files:
  created: []
  modified:
    - api/services/price_service.py
    - api/services/catalog_service.py
    - tests/test_price_service.py
    - tests/test_catalog_service.py

key-decisions:
  - "No deviations from the plan's literal action text were needed — both tasks' RESEARCH.md/PATTERNS.md-specified pipeline shape, docstring convention, and call-site wiring were followed as written."
  - "Skipped the second `pytest -q` (full backend suite) re-run required by Task 2's acceptance criteria, per an explicit real-time instruction from the orchestrator during execution to avoid repeating a ~9-minute full-suite run against the live Atlas cluster after an earlier run had already validated Task 1's changes. Verification instead relied on: (1) one completed full-suite run (102 passed, 0 skipped) covering price_service.py + test_price_service.py before catalog_service.py was touched, and (2) the scoped `pytest tests/test_catalog_service.py -x -q` run (16 passed, 0 skipped) after all Task 2 edits, including the deliberate-breakage regression proof. catalog_service.py's only new dependency (get_all_time_range) was independently verified in the completed full-suite run. No other file was touched, so residual full-suite risk is low but not zero — flagged here for the wave-level verifier."

requirements-completed: [PRICE-09]

coverage:
  - id: D1
    description: "get_all_time_range returns None only when a product has zero price_points documents ever; a single stored point yields a real range with high == low, never insufficient_data"
    requirement: "PRICE-09"
    verification:
      - kind: unit
        ref: "tests/test_price_service.py#test_all_time_range_none_when_no_points"
        status: pass
      - kind: unit
        ref: "tests/test_price_service.py#test_all_time_range_single_point_is_real_data"
        status: pass
      - kind: unit
        ref: "tests/test_catalog_service.py#test_detail_all_time_range_single_point_is_ok"
        status: pass
    human_judgment: false
  - id: D2
    description: "get_all_time_range is order-independent (computed via a single $group with no $sort) and preserves stored precision exactly"
    requirement: "PRICE-09"
    verification:
      - kind: unit
        ref: "tests/test_price_service.py#test_all_time_range_multi_point_order_independent"
        status: pass
      - kind: unit
        ref: "tests/test_price_service.py#test_all_time_range_all_equal_values"
        status: pass
      - kind: unit
        ref: "tests/test_price_service.py#test_all_time_range_preserves_stored_precision"
        status: pass
      - kind: unit
        ref: "tests/test_price_service.py#test_all_time_range_scoped_to_one_product"
        status: pass
    human_judgment: false
  - id: D3
    description: "get_product_detail sets all_time_range to {high, low, status:'ok'} on the normal path and {high:None, low:None, status:'insufficient_data'} on the zero-data early-return branch — the key is present in every detail response including a never-priced product"
    requirement: "PRICE-09"
    verification:
      - kind: unit
        ref: "tests/test_catalog_service.py#test_detail_all_time_range_present_when_no_data"
        status: pass
      - kind: unit
        ref: "tests/test_catalog_service.py#test_detail_all_time_range_computed_from_points"
        status: pass
    human_judgment: false
  - id: D4
    description: "all_time_range is exactly two scalars plus a status string — never anything list-shaped — and the detail response still contains no raw price_points series after this plan (D-11)"
    requirement: "PRICE-09"
    verification:
      - kind: unit
        ref: "tests/test_catalog_service.py#test_detail_omits_raw_series (extended with isinstance(dict) assertions for trend_24h and all_time_range)"
        status: pass
    human_judgment: false
  - id: D5
    description: "api/services/price_service.py contains no exception-handling block and no in-process min()/max() reduction — the extremes are computed entirely in the database via a single $group with no $sort stage"
    requirement: "PRICE-09"
    verification:
      - kind: other
        ref: "grep -cE '^[[:space:]]*(try|except)[[:space:]:]' api/services/price_service.py -> 0; grep -cE '\\bmin\\(|\\bmax\\(' api/services/price_service.py -> 0; grep -c '\\$sort' api/services/price_service.py -> 1 (get_trend_baseline's existing sort only)"
        status: pass
    human_judgment: false

# Metrics
duration: ~2.5h (includes two full-backend-suite pytest runs against a live MongoDB Atlas cluster, ~9min and ~9min, plus per-task scoped runs)
completed: 2026-08-28
status: complete
---

# Phase 9 Plan 3: All-Time High/Low Badge Data Summary

**`get_all_time_range` — a single $min/$max aggregation with the zero-points-only None contract, deliberately distinct from `get_trend_baseline`'s tolerance-window contract — wired onto `get_product_detail`'s `all_time_range` field on both branches, proven by nine boundary/regression tests and two demonstrated-then-reverted deliberate-breakage mutations.**

## Performance

- **Duration:** ~2.5h
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- `get_all_time_range(db, product_id)` added to `price_service.py`: a two-stage `$match`/`$group` pipeline computing `high`/`low` via `$max`/`$min` over `total_price`, with no `$sort` stage (order-independent by construction)
- Its docstring and the module docstring's function-contrast list both state the contract explicitly: `None` only on zero documents, never on "not enough spread" — the exact distinction `get_trend_baseline`'s copy-paste risk would get wrong (Pitfall 3)
- `catalog_service.get_product_detail` imports and calls `get_all_time_range` once per detail assembly, setting `all_time_range` to `{high, low, status:"ok"}` on the normal path and `{high:None, low:None, status:"insufficient_data"}` on the zero-data early-return branch — no additional gate beyond the function's own None contract, so an equal high/low from a single point is never miscategorized
- `get_product_detail`'s docstring and its D-11 sentence updated to name all four response fields as small aggregates, never a series
- Nine new backend tests: six at the `price_service` layer (zero-points, single-point equal-bounds, out-of-order multi-point, all-equal-values, stored-precision, cross-product isolation) and three at the `catalog_service` layer (zero-data presence, multi-point computation, single-point ok-with-equal-bounds), plus two `isinstance(dict)` assertions extending the existing D-11 raw-series scan
- Two deliberate-breakage mutations applied, confirmed red, and reverted before commit: a two-point-minimum mutation on `get_all_time_range` (failed the single-point test with `assert None is not None`) and a removal of the early-return `all_time_range` assignment (failed the presence test with an `AssertionError` on the membership check)

## Task Commits

Each task was committed atomically:

1. **Task 1: get_all_time_range — a $min/$max aggregation with the zero-points-only None contract** - `dc25612` (feat)
2. **Task 2: Hang all_time_range off get_product_detail on both branches** - `8612cf7` (feat)

## Files Created/Modified
- `api/services/price_service.py` - Adds `get_all_time_range`; extends the module docstring's function-contrast list with a fourth entry
- `api/services/catalog_service.py` - Imports `get_all_time_range`; extends the zero-data early-return branch and adds the post-loop `all_time_range` assembly block; updates `get_product_detail`'s docstring
- `tests/test_price_service.py` - Adds six `get_all_time_range` boundary/isolation tests
- `tests/test_catalog_service.py` - Adds three `all_time_range` assembly tests; extends `test_detail_omits_raw_series` with two `isinstance(dict)` assertions

## Decisions Made
- No deviations from the plan's literal action text — RESEARCH.md's Pattern 2 pipeline shape, the module docstring convention, and the call-site wiring were all followed exactly as specified.
- The second full-backend-suite `pytest -q` run required by Task 2's acceptance criteria was skipped per an explicit real-time orchestrator instruction issued during execution (to avoid a second ~9-minute run against the live Atlas cluster after stalls earlier in the session). See "Deferred Issues" below.

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

**Total deviations:** 0
**Impact on plan:** None.

## Deferred Issues

- **Task 2's full-backend-suite `pytest -q` re-run was not performed after `catalog_service.py`/`test_catalog_service.py` edits landed.** Per the plan's own acceptance criteria, Task 2 requires a full-suite pass in addition to the scoped `pytest tests/test_catalog_service.py -x -q` run. During execution, an earlier full-suite run (102 passed, 0 skipped, 547.56s) had already completed against `price_service.py`'s Task 1 changes with `catalog_service.py` still unmodified; a subsequent orchestrator instruction directed skipping a second full-suite run to avoid a further ~9-minute run against the live MongoDB Atlas cluster. The scoped `test_catalog_service.py -x -q` run (16 passed, 0 skipped) covers every new assertion this plan adds, including the D-11 raw-series scan extension, and `get_all_time_range` itself was independently verified in the completed full-suite run — but no run in this session exercised the complete backend suite with both files' final content simultaneously. Recommend the wave-level or phase-gate verifier run `pytest -q` once before `/gsd-verify-work` to close this gap.

## Issues Encountered
- The plan's acceptance criteria states that removing the `all_time_range` assignment from the early-return branch should make `test_detail_all_time_range_present_when_no_data` fail "with a `KeyError`." As written, that test uses `assert "all_time_range" in detail` (a membership check), so the observed failure was an `AssertionError` (`assert 'all_time_range' in {...}`), not a literal `KeyError` — the same wording discrepancy Plan 09-01's summary already noted for the analogous `trend_24h` case. The test still correctly demonstrates the regression; no code or test change was made in response.
- Running a scoped test file concurrently with a background full-suite `pytest -q` process against the same shared Atlas `pokemonview_test` database produced a spurious failure (`test_list_products_filters` returning 0 results instead of 4) from collection-drop/insert interference between the two processes — not a real defect. Resolved by not running tests concurrently against the shared database for the remainder of execution, consistent with Plan 09-01's own documented precedent of the same class of issue.
- Two background `pytest -q` full-suite invocations were killed by the harness (moved to background then killed / hit an output-size ceiling on an unrelated file in the shared session tasks directory) before completing; the third attempt, run in the foreground with an extended timeout and confirmed via direct process inspection (`ps aux`) rather than a sleep-polling loop, completed successfully.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `all_time_range` is live on the detail response; Plans 09-04/09-05 (frontend `AllTimeRangeBadge` rendering) can proceed without further backend dependency on this plan.
- `price_service.py` and `catalog_service.py` have no other pending edits from this plan — `git status` is clean at hand-off.
- One follow-up recommended before `/gsd-verify-work`: run `pytest -q` (full backend suite) once to confirm `catalog_service.py`'s and `price_service.py`'s final combined state together, since no single run in this session exercised both simultaneously (see Deferred Issues).

---
*Phase: 09-price-badges*
*Completed: 2026-08-28*

## Self-Check: PASSED
- FOUND: .planning/phases/09-price-badges/09-03-SUMMARY.md
- FOUND: commit dc25612 (Task 1)
- FOUND: commit 8612cf7 (Task 2)
- FOUND: commit 22bb066 (docs: SUMMARY)
