---
phase: 05-flask-rest-api-active-price-serving
plan: 04
subsystem: api
tags: [pymongo, mongodb-timeseries, flask, price-computation]

# Dependency graph
requires:
  - phase: 05-flask-rest-api-active-price-serving
    provides: "Plan 05-03's RED test_price_service.py contract (api_db fixture, locked function signatures) and Plan 05-02's listing_count field on price_points documents"
provides:
  - "api/services/price_service.py with get_current_price, get_trend_baseline, compute_pct_change, TREND_TOLERANCE_DAYS"
  - "api/__init__.py, api/services/__init__.py package markers"
affects: [05-05 (catalog_service composes these three functions into get_product_detail), 05-06 (blueprint routes), Phase 6 (frontend consumes current_price/trend fields)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure DB-taking-as-arg service functions with no top-level side effects on import (mirrors scripts/matching.py / db/init_collections.py convention)"
    - "Two distinctly-named functions for similarly-shaped-but-different date-window problems (get_current_price: no window; get_trend_baseline: bounded ±tolerance window) rather than one parameterized helper — avoids Pitfall 2's window-confusion bug class"
    - "MongoDB aggregation pipeline for closest-point-to-target-date ($match bounded window -> $addFields $abs/$subtract diff -> $sort -> $limit 1)"

key-files:
  created:
    - api/__init__.py
    - api/services/__init__.py
    - api/services/price_service.py
  modified: []

key-decisions:
  - "Implemented Task 1 (get_current_price, compute_pct_change) and Task 2 (get_trend_baseline, TREND_TOLERANCE_DAYS) as two separate commits against the plan's TDD task split, even though both land in the same file, to preserve per-task atomic commit granularity"

patterns-established:
  - "Decision-ID-cited module constants (TREND_TOLERANCE_DAYS = 3  # D-05)"

requirements-completed: []  # PRICE-01/02/03 remain mapped to Phase 6 (user-observable) per REQUIREMENTS.md traceability table and STATE.md's Phase 05-03 decision; this plan is the enabling/serving layer, not the requirement-completing layer

coverage:
  - id: D1
    description: "get_current_price(db, product_id) returns the latest price_points document by ts desc with no time window, gap-tolerant (D-01/D-02), passing through the literal ts (D-03)"
    requirement: "PRICE-01"
    verification:
      - kind: unit
        ref: "tests/test_price_service.py#test_current_price_gap_tolerant"
        status: pass
      - kind: unit
        ref: "tests/test_price_service.py#test_current_price_none_when_no_points"
        status: pass
      - kind: unit
        ref: "tests/test_price_service.py#test_freshness_is_real_ts"
        status: pass
    human_judgment: false
  - id: D2
    description: "get_trend_baseline(db, product_id, current_ts, days, tolerance_days) returns the closest price_points document within ±3 days of the target date, or None when nothing falls inside the window"
    requirement: "PRICE-03"
    verification:
      - kind: unit
        ref: "tests/test_price_service.py#test_trend_baseline_within_tolerance"
        status: pass
      - kind: unit
        ref: "tests/test_price_service.py#test_trend_insufficient_data"
        status: pass
    human_judgment: false
  - id: D3
    description: "compute_pct_change(current_total, baseline_total) computes percent change on total_price only, with a zero-baseline divide-by-zero guard returning None"
    requirement: "PRICE-03"
    verification:
      - kind: unit
        ref: "tests/test_price_service.py#test_trend_uses_total_price_only"
        status: pass
    human_judgment: false

duration: 8min
completed: 2026-07-15
status: complete
---

# Phase 5 Plan 4: Price Service Layer Summary

**`api/services/price_service.py` with three pure MongoDB-query functions (gap-tolerant current price, ±3-day tolerance-window trend baseline via aggregation pipeline, zero-guarded percent-change) turning `tests/test_price_service.py` fully GREEN.**

## Performance

- **Duration:** 8 min
- **Started:** 2026-07-15T02:59:00Z (approx, continuing from Plan 05-03 completion)
- **Completed:** 2026-07-15T03:04:10Z
- **Tasks:** 2
- **Files modified:** 3 (all newly created)

## Accomplishments
- `get_current_price(db, product_id)` returns the single most-recent `price_points` document by `ts` desc with NO time-window filter — a product's real price history is returned even if the latest point is 200+ days stale (D-02), and only returns `None` when the product has zero points ever (D-01)
- `get_trend_baseline(db, product_id, current_ts, days, tolerance_days=3)` uses a bounded `$match` → `$addFields` (`$abs`/`$subtract`) → `$sort` → `$limit 1` aggregation to find the closest point within ±3 days of the computed target date (D-05), returning `None` explicitly when nothing falls inside the window (D-06)
- `compute_pct_change(current_total, baseline_total)` computes percent change on `total_price` values only (D-07), rounded to 2dp, with a zero-baseline divide-by-zero guard returning `None`
- All 6 tests in `tests/test_price_service.py` pass GREEN against a live MongoDB Atlas test database

## Task Commits

Each task was committed atomically:

1. **Task 1: api package + get_current_price + compute_pct_change** - `03f4132` (feat)
2. **Task 2: get_trend_baseline within ±tolerance (D-05/D-06) + TREND_TOLERANCE_DAYS** - `6734c02` (feat)

**Plan metadata:** (this commit, docs)

## Files Created/Modified
- `api/__init__.py` - Empty package marker, no side effects on import
- `api/services/__init__.py` - Empty package marker, no side effects on import
- `api/services/price_service.py` - `get_current_price`, `get_trend_baseline`, `compute_pct_change`, `TREND_TOLERANCE_DAYS` constant

## Decisions Made
- Split the single-file implementation across two commits matching the plan's Task 1/Task 2 TDD boundary (get_current_price/compute_pct_change first, get_trend_baseline second) to preserve atomic per-task commit granularity even though both land in the same file
- Kept `get_current_price` and `get_trend_baseline` as two distinctly-named functions rather than one parameterized helper, per 05-RESEARCH.md's Pitfall 2 guidance, so the window-less vs. windowed behavior can never be silently conflated

## Deviations from Plan

None - plan executed exactly as written. Both tasks' acceptance criteria (including the `grep`-based no-time-window-filter proof, no-MongoDB-connection-on-import proof, and `TREND_TOLERANCE_DAYS == 3` proof) were verified directly and passed without needing any fix.

## Issues Encountered

None. MongoDB Atlas test database (`pokemonview_test`) was reachable via the existing `MONGODB_URI` in `.env`, so all six unit tests ran against a real MongoDB connection per `tests/conftest.py`'s established `api_db` fixture pattern — no `pytest.skip()` path was exercised.

## User Setup Required

None - no external service configuration required. `MONGODB_URI` was already configured from prior phases.

## Next Phase Readiness
- `price_service.py`'s three functions are ready to be composed by Plan 05-05's `catalog_service.get_product_detail` into the detail response's `current_price` + `trend_7d`/`trend_30d` fields
- `get_current_price`'s return value includes the `listing_count` field (when present, per Plan 05-02) for `catalog_service` to surface as the sample size
- `tests/test_catalog_service.py` and `tests/test_api_products.py` remain RED as expected — `catalog_service` and the Flask app are Plan 05-05/05-06's scope, not this plan's

---
*Phase: 05-flask-rest-api-active-price-serving*
*Completed: 2026-07-15*
