---
phase: 09-price-badges
plan: 01
subsystem: pricing
tags: [flask, pymongo, mongodb-aggregation, react, vitest, pytest]

# Dependency graph
requires: []
provides:
  - "price_service.TREND_24H_TOLERANCE_HOURS — explicit 4-hour tolerance constant for the 24h trend window, distinct from the 3-day TREND_TOLERANCE_DAYS default"
  - "catalog_service.get_product_detail now assembles trend_24h on both the normal path and the zero-data early-return branch"
  - "GET /products/<id> detail response carries trend_24h: {pct_change, status} alongside trend_7d/trend_30d"
  - "ProductDetailPage renders a third TrendBadge (24h, ordered first) reusing the unmodified TrendBadge component"
affects: [09-02, 09-03, 09-04, 09-05]

# Actuals (#2632)
actuals:
  tokens: 5664
  tasks: 2
  commits: 2

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "24h trend window computed as a standalone sibling block after the TREND_WINDOWS loop, never folded into that loop — keeps the 7d/30d default tolerance and the 24h explicit tolerance from ever being confused at a single call site"

key-files:
  created: []
  modified:
    - api/services/price_service.py
    - api/services/catalog_service.py
    - frontend/src/pages/ProductDetailPage.jsx
    - frontend/src/pages/ProductDetailPage.test.jsx
    - tests/test_api_products.py
    - tests/test_price_service.py
    - tests/test_catalog_service.py

key-decisions:
  - "Added a catalog-service-layer test (test_detail_trend_24h_never_uses_the_default_three_day_tolerance) not explicitly specified in the plan's Task 2 action text, because the plan's own must_haves.truths states the 24h call site must never fall back to the 3-day default, and none of the three catalog tests the plan specified actually exercise that boundary through the real get_product_detail call site (they only test it in isolation at the price_service layer with a hand-passed tolerance). Verified this gap was real by performing the plan's own prescribed deliberate-breakage step first — removing tolerance_days from the call site caused zero test failures until this test was added."

requirements-completed: [PRICE-08]

coverage:
  - id: D1
    description: "trend_24h flows from price_points through GET /products/<id> to a rendered TrendBadge for a priced product, computed via compute_pct_change against a baseline within the 24h+/-4h window"
    requirement: "PRICE-08"
    verification:
      - kind: integration
        ref: "tests/test_api_products.py#test_product_detail_includes_trend_24h"
        status: pass
      - kind: unit
        ref: "tests/test_catalog_service.py#test_detail_trend_24h_computed_from_the_24h_baseline"
        status: pass
      - kind: automated_ui
        ref: "frontend/src/pages/ProductDetailPage.test.jsx#renders total price, item price, all three trend badges..."
        status: pass
    human_judgment: false
  - id: D2
    description: "trend_24h is present in its insufficient-data shape on the zero-data early-return branch (both at the HTTP boundary and the service layer) — the key is never absent"
    requirement: "PRICE-08"
    verification:
      - kind: integration
        ref: "tests/test_api_products.py#test_product_detail_includes_trend_24h (pitch-black_etb branch)"
        status: pass
      - kind: unit
        ref: "tests/test_catalog_service.py#test_detail_trend_24h_present_when_no_data"
        status: pass
    human_judgment: false
  - id: D3
    description: "The 24h tolerance window's inclusive edges (20h, 28h), one-step-outside rejections (19h59m, 28h01m), the four-day default-tolerance regression, and the nearer-point tie-break are each pinned by a named test at the price_service layer; the call site's non-use of the 3-day default is separately pinned at the catalog_service layer"
    requirement: "PRICE-08"
    verification:
      - kind: unit
        ref: "tests/test_price_service.py#test_trend_baseline_24h_accepts_both_window_edges"
        status: pass
      - kind: unit
        ref: "tests/test_price_service.py#test_trend_baseline_24h_rejects_one_step_outside_each_edge"
        status: pass
      - kind: unit
        ref: "tests/test_price_service.py#test_trend_baseline_24h_rejects_the_default_tolerance_case"
        status: pass
      - kind: unit
        ref: "tests/test_price_service.py#test_trend_baseline_24h_picks_the_nearer_point"
        status: pass
      - kind: unit
        ref: "tests/test_catalog_service.py#test_detail_trend_24h_never_uses_the_default_three_day_tolerance"
        status: pass
    human_judgment: false
  - id: D4
    description: "ProductDetailPage renders three trend rows labelled 24h, 7d, 30d in that left-to-right DOM order (UI-SPEC D-UI-03), and a zero-baseline 24h point renders insufficient-data rather than raising"
    requirement: "PRICE-08"
    verification:
      - kind: automated_ui
        ref: "frontend/src/pages/ProductDetailPage.test.jsx#renders the 24h, 7d and 30d trend badges in that left-to-right DOM order"
        status: pass
      - kind: unit
        ref: "tests/test_catalog_service.py#test_detail_trend_24h_zero_baseline_is_insufficient"
        status: pass
    human_judgment: false
  - id: D5
    description: "TrendBadge.jsx and TrendBadge.module.css remain byte-identical to their pre-plan state — the 24h badge reuses the existing 4-state formatter verbatim, no new visual state or token introduced"
    verification:
      - kind: other
        ref: "git diff --stat frontend/src/components/TrendBadge.jsx frontend/src/components/TrendBadge.module.css (empty output)"
        status: pass
    human_judgment: false

# Metrics
duration: ~75min
completed: 2026-08-22
status: complete
---

# Phase 9 Plan 1: 24h Change Badge Tracer Summary

**`trend_24h` wired end-to-end — a new explicit 4-hour tolerance constant, a standalone sibling computation block in `get_product_detail` (never riding the 7d/30d loop's 3-day default), and a third `TrendBadge` rendered first on the product detail page, proven by real HTTP and DOM assertions plus nine boundary/regression tests.**

## Performance

- **Duration:** ~75 min
- **Started:** ~2026-08-22T15:55:00Z (context load + read_first)
- **Completed:** 2026-08-22T17:14:45Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- `TREND_24H_TOLERANCE_HOURS = 4` added to `price_service.py` as an explicit, documented tuning constant, distinct from `TREND_TOLERANCE_DAYS = 3`
- `catalog_service.get_product_detail` computes `trend_24h` in a standalone block after the `TREND_WINDOWS` loop, calling `get_trend_baseline` with `days=1` and an explicit `tolerance_days=TREND_24H_TOLERANCE_HOURS / 24` — the 7d/30d loop's default-tolerance call site is untouched
- The zero-data early-return branch sets `trend_24h` alongside `trend_7d`/`trend_30d`, so the key is never silently absent
- `ProductDetailPage` renders a third `TrendBadge` (caption `24h`, ordered first) reusing the unmodified `TrendBadge` component
- HTTP-level test (`test_product_detail_includes_trend_24h`) proves both the "ok" and "insufficient_data" `trend_24h` shapes at the `GET /products/<id>` boundary
- Nine new backend tests pin the 24h window's inclusive edges, one-step-outside rejections, the four-day default-tolerance regression, the nearer-point tie-break, the zero-data branch, the zero-baseline guard, and (added beyond the plan's literal spec) the call site's non-use of the 3-day default
- A DOM-order test proves `24h` renders before `7d` before `30d` (UI-SPEC D-UI-03)

## Task Commits

Each task was committed atomically:

1. **Task 1: End-to-end 24h change badge — one path, price_points to rendered chip** - `e88fe64` (feat)
2. **Task 2: Pin the 24h tolerance window at its edges and the zero-data branch at the service layer** - `af209cb` (test)

_Note: Task 2 is a test-only commit — the implementation it pins was already shipped and committed in Task 1; there is no separate GREEN implementation commit because no new production code was needed to make these tests pass._

## Files Created/Modified
- `api/services/price_service.py` - Adds `TREND_24H_TOLERANCE_HOURS` constant and docstring note naming the 24h caller
- `api/services/catalog_service.py` - Imports the constant; sets `trend_24h` on the zero-data branch and via a new standalone sibling block after the `TREND_WINDOWS` loop
- `frontend/src/pages/ProductDetailPage.jsx` - Adds a third `.trend` row (24h, first) rendering `TrendBadge` over `product.trend_24h`
- `frontend/src/pages/ProductDetailPage.test.jsx` - Adds `trend_24h` to both fixtures, raises the insufficient-data badge count from 2 to 3, adds a `+0.8%` assertion and a DOM-order test
- `tests/test_api_products.py` - Adds `test_product_detail_includes_trend_24h` covering both the ok and zero-data HTTP responses
- `tests/test_price_service.py` - Adds four boundary/regression tests for the 24h tolerance window
- `tests/test_catalog_service.py` - Adds four tests: early-return presence, normal-path computation, zero-baseline guard, and the call-site default-tolerance regression guard

## Decisions Made
- Added `test_detail_trend_24h_never_uses_the_default_three_day_tolerance` beyond the plan's literal Task 2 action text. Rationale: the plan's frontmatter `must_haves.truths` explicitly requires "the 24h window never rides catalog_service's TREND_WINDOWS loop and never uses get_trend_baseline's default three-day tolerance," and the plan's own acceptance criteria demands a deliberate-breakage step prove this. Running that exact deliberate breakage (temporarily removing `tolerance_days` from the call site) against only the three catalog tests the plan specified produced **zero test failures** — none of them exercise a baseline point that is inside the 3-day default window but outside the 4-hour explicit one. Added the missing boundary test, re-ran the same breakage, confirmed it now fails as required, then reverted the breakage (see Issues Encountered).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added a catalog-layer test the plan's own must_haves/acceptance-criteria demanded but its literal Task 2 action text did not produce**
- **Found during:** Task 2, while performing the plan-mandated deliberate breakage of `catalog_service.py`'s `tolerance_days` argument
- **Issue:** The plan's must_haves truths and acceptance criteria require proof that the 24h call site never falls back to the 3-day default tolerance, and require a deliberate-breakage step to demonstrate a test failure when this is violated. The three catalog tests the plan's Task 2 action explicitly specifies do not construct a baseline point that would distinguish the 4-hour window from the 3-day default, so the deliberate breakage produced zero failures against them.
- **Fix:** Added `test_detail_trend_24h_never_uses_the_default_three_day_tolerance` (inserts a baseline point exactly 2 days old — outside 24h+/-4h, inside a 3-day-tolerance window — and asserts `trend_24h` is `insufficient_data`). Re-ran the breakage: this test now fails (`assert 'ok' == 'insufficient_data'`). Reverted the breakage; `git diff` confirms `catalog_service.py` returned to its Task 1 committed state with zero residual diff.
- **Files modified:** tests/test_catalog_service.py
- **Verification:** `pytest tests/test_catalog_service.py -q -k trend_24h` — 1 failed with breakage in place, 4 passed after revert
- **Committed in:** af209cb (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 missing critical test coverage)
**Impact on plan:** Closes a real gap between the plan's stated must_haves truth and its literal test specification. No scope creep — the added test targets the exact behavior the plan's own frontmatter already required.

## Issues Encountered
- The plan's acceptance criteria states that temporarily removing the `trend_24h` assignment from the early-return branch should make `test_detail_trend_24h_present_when_no_data` fail "with a `KeyError`." As written, that test uses `assert "trend_24h" in detail` (a membership check), so the observed failure was an `AssertionError` (`assert 'trend_24h' in {...}`), not a literal `KeyError`. The test still correctly demonstrates the regression (fails when the branch is broken, passes when it is not); this is a wording discrepancy in the acceptance criteria, not a functional gap. No code or test change was made in response — noting it here for the record per the acceptance criteria's own "recorded in the SUMMARY" instruction.
- Two of the required deliberate-breakage checks in Task 2's acceptance criteria were performed and reverted before commit:
  1. Removing `tolerance_days=TREND_24H_TOLERANCE_HOURS / 24` from the 24h call site in `catalog_service.py` — initially caused **zero** test failures against the plan's originally specified tests (see Deviations above); after adding the missing boundary test, it correctly failed with `assert 'ok' == 'insufficient_data'`.
  2. Removing the `trend_24h` assignment from the zero-data early-return branch — caused `test_detail_trend_24h_present_when_no_data` to fail with `AssertionError: assert 'trend_24h' in {...}` (see wording note above).
  Both breakages were reverted before the Task 2 commit; `git diff` against the Task 1 commit shows zero residual changes to `catalog_service.py`.
- A stray background `pytest -q` process from an interrupted intermediate run held onto CPU with no observable progress for ~18 minutes (likely a leftover connection/lock artifact from a concurrently-killed run against the same shared `pokemonview_test` database). Killed it and re-ran the full suite alone; it completed cleanly in both a partial and a full re-run (93 passed, 0 skipped, 0 failed). No test or production code was implicated — this was an environment/process-management issue, not a code defect.
- `frontend/node_modules` was absent in this fresh worktree checkout (gitignored, not present until installed). Ran `npm ci` (from the existing `package-lock.json`, no new packages added) to hydrate it before running frontend tests/lint/build — not a plan deviation, standard worktree environment setup.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `trend_24h` is live on the detail response and rendered on the page; Plans 09-02 through 09-05 (all-time range badge work) can proceed without further dependency on this plan.
- `TrendBadge.jsx`/`TrendBadge.module.css` remain untouched, confirmed via `git diff --stat` returning empty — no risk of edit-conflict with later plans that also touch `ProductDetailPage.jsx`.
- No blockers. Full backend suite (93 tests) and full frontend suite (65 tests) both green with zero skips at hand-off.

---
*Phase: 09-price-badges*
*Completed: 2026-08-22*
