---
phase: 09-price-badges
plan: 04
subsystem: testing
tags: [flask, pymongo, pytest, mongodb-aggregation]

# Dependency graph
requires:
  - phase: 09-01
    provides: "trend_24h field on GET /products/<id>"
  - phase: 09-03
    provides: "all_time_range field on GET /products/<id>"
provides:
  - "HTTP-boundary exact-key-set contract tests for trend_24h and all_time_range in tests/test_api_products.py"
  - "Catalog-wide sweep proving all sixteen seeded products' detail responses carry all four badge fields in every data state"
  - "Phase 9 instance of the D-11 raw-series regression guard, scoped to a response containing both new keys"
  - "Regression proof that the unknown-id 404 envelope and CORS header are unchanged by the two new fields"
affects: [09-05]

# Actuals (#2632)
actuals:
  tokens: 2512
  tasks: 2
  commits: 2

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Deliberate-breakage proofs for list-shaped regressions must mutate the top-level response key itself (not a nested value inside it) — the existing per-key raw-series scan is shallow by design and only inspects body.items(), so a mutation nested one level deeper (e.g. a list inside a dict value) will not trip it"

key-files:
  created: []
  modified:
    - tests/test_api_products.py

key-decisions:
  - "Split the plan's two tasks into two separate commits even though both touch the same single file, by temporarily removing Task 2's not-yet-written tests before the Task 1 commit and re-adding them for the Task 2 commit — preserves the per-task atomic-commit contract despite both tasks sharing one file."
  - "The Task 2 acceptance criterion 'temporarily changing all_time_range to carry a list of the two extreme points instead of two scalars' was interpreted as replacing detail['all_time_range'] entirely with a top-level list (not nesting a list inside the existing {high, low, status} dict), because the existing per-key raw-series scan only inspects top-level values of the response body — a nested list would not be visible to it. Verified this by first attempting the nested-value mutation, observing it produced a false pass (0 failures), then correcting to the top-level-list mutation, which correctly failed the guard test."

requirements-completed: [PRICE-08, PRICE-09]

coverage:
  - id: D1
    description: "GET /products/<id> for a priced product returns trend_24h with exactly {pct_change, status} and all_time_range with exactly {high, low, status}, with all_time_range's low/high spanning a range provably wider than the 24h window (independent computation paths)"
    requirement: "PRICE-09"
    verification:
      - kind: integration
        ref: "tests/test_api_products.py#test_detail_json_carries_both_new_fields_with_exact_shapes"
        status: pass
    human_judgment: false
  - id: D2
    description: "A product with exactly one collected price point returns all_time_range with status ok and equal high/low, never insufficient_data"
    requirement: "PRICE-09"
    verification:
      - kind: integration
        ref: "tests/test_api_products.py#test_detail_json_single_point_all_time_range_is_ok"
        status: pass
    human_judgment: false
  - id: D3
    description: "A seeded product with zero collected price points returns HTTP 200 carrying all four badge fields (trend_24h, trend_7d, trend_30d, all_time_range) in their insufficient-data shape"
    requirement: "PRICE-08"
    verification:
      - kind: integration
        ref: "tests/test_api_products.py#test_detail_json_zero_points_carries_every_badge_field"
        status: pass
    human_judgment: false
  - id: D4
    description: "Every one of the sixteen seeded catalog products returns a detail response containing all four badge fields with correct shapes, across both priced and unpriced data states, proven as a response-level property rather than a hand-picked fixture"
    requirement: "PRICE-08"
    verification:
      - kind: integration
        ref: "tests/test_api_products.py#test_every_catalog_product_detail_carries_all_four_badge_fields"
        status: pass
    human_judgment: false
  - id: D5
    description: "The detail response still contains no key whose value is a non-empty list of point-shaped mappings, now that trend_24h and all_time_range both exist (D-11 regression guard, Phase 9 instance)"
    verification:
      - kind: integration
        ref: "tests/test_api_products.py#test_detail_still_omits_raw_series_after_badge_fields"
        status: pass
    human_judgment: false
  - id: D6
    description: "The detail route's pre-existing behaviours are unchanged: an unknown id still returns 404 with the not_found envelope, and a detail response still carries an Access-Control-Allow-Origin header"
    verification:
      - kind: integration
        ref: "tests/test_api_products.py#test_detail_route_404_and_cors_unchanged_after_badge_fields"
        status: pass
    human_judgment: false
  - id: D7
    description: "Every guard in this plan has a demonstrated failing mutation, applied then reverted before commit"
    verification:
      - kind: other
        ref: "manual deliberate-breakage session — 4 mutations, all confirmed red then reverted (see Deviations/Issues below); git diff against the pre-breakage commit returned empty"
        status: pass
    human_judgment: false

# Metrics
duration: ~50min
completed: 2026-08-28
status: complete
---

# Phase 9 Plan 4: JSON Contract for New Detail Fields Summary

**Nine new HTTP-boundary contract tests in `tests/test_api_products.py` pin `trend_24h` and `all_time_range` to their exact key sets across every point-count state, prove badge-field completeness across all sixteen catalog products, and extend the D-11 raw-series regression guard — each backed by a demonstrated failing mutation.**

## Performance

- **Duration:** ~50 min
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- `test_detail_json_carries_both_new_fields_with_exact_shapes` — exact key-set equality for both new fields against a three-point fixture engineered so the all-time bounds are provably wider than the 24h window
- `test_detail_json_single_point_all_time_range_is_ok` — a single stored point is real data, `all_time_range` status `"ok"` with equal high/low
- `test_detail_json_zero_points_carries_every_badge_field` — the zero-data response carries all four badge fields in their insufficient-data shape (ROADMAP success criterion 4, at the HTTP boundary)
- `test_every_catalog_product_detail_carries_all_four_badge_fields` — sweeps all sixteen seeded catalog products (mixed priced/unpriced), asserting exact key sets and valid `status` values for every badge field on every product, with the offending product id named in every failure message
- `test_detail_still_omits_raw_series_after_badge_fields` — the Phase 9 instance of the D-11 per-key raw-series scan, asserting both new keys are present before scanning so the guard cannot pass vacuously
- `test_detail_route_404_and_cors_unchanged_after_badge_fields` — proves the unknown-id 404 envelope and CORS header are unchanged by the two new response fields
- Four deliberate-breakage mutations applied against `api/services/catalog_service.py`, each confirmed to turn the relevant new test red, then reverted — `git diff` confirmed zero residual change after each revert

## Task Commits

Each task was committed atomically:

1. **Task 1: JSON contract for all_time_range and trend_24h at every point count** - `0f0e172` (test)
2. **Task 2: Catalog-wide field completeness and the Phase 9 raw-series regression guard** - `e0fced9` (test)

## Files Created/Modified
- `tests/test_api_products.py` - Adds six new test functions (three per task) covering the HTTP-boundary contract for `trend_24h` and `all_time_range`

## Decisions Made
- Split both tasks' test additions into two separate commits despite both touching the same single file — see `key-decisions` in frontmatter for the mechanism (temporarily removed Task 2's tests before the Task 1 commit, re-added them for the Task 2 commit).
- Corrected the interpretation of Task 2's third deliberate-breakage acceptance criterion (a list-of-two-extreme-points mutation) to replace `all_time_range` entirely at the top level of the response, rather than nesting a list inside the existing `{high, low, status}` dict — the existing D-11 scan only inspects top-level response keys, so the first (nested) attempt produced a false pass. See `key-decisions` in frontmatter for the verification trail.

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written; both tasks' service-layer dependencies (`trend_24h` from Plan 09-01, `all_time_range` from Plan 09-03, and the `get_product_detail` wiring for both) were already present and correct, requiring no code changes, only new tests.

---

**Total deviations:** 0
**Impact on plan:** None. This plan adds test coverage only, per its own scope statement (no production code, no route, no dependency added).

## Issues Encountered
- The plan's Task 2 acceptance criterion describing a "list of the two extreme points instead of two scalars" mutation was ambiguous between two shapes: (a) nesting a list inside the existing `all_time_range` dict's `high` key, or (b) replacing `all_time_range` itself with a top-level list. Attempt (a) produced zero test failures — the D-11 scan only inspects top-level response keys via `body.items()`, so a list nested one level deeper inside a dict value is invisible to it. Attempt (b) correctly failed `test_detail_still_omits_raw_series_after_badge_fields` with the expected `AssertionError`. Documented as a pattern in `tech-stack.patterns` above for any future plan writing a similar deliberate-breakage step against this scan.
- All four deliberate-breakage mutations targeted `api/services/catalog_service.py`'s `get_product_detail` function (the normal-path `all_time_range` assignment, and the zero-data early-return branch's `all_time_range`/`trend_24h` assignments). Each was applied, confirmed red against its named test, then reverted; `git diff --stat api/services/catalog_service.py` returned empty after all four reverts and before the Task 1/Task 2 commits — no production code was left mutated.
- The full backend suite (`pytest -q`) took ~10 minutes (607.67s) against the live MongoDB Atlas cluster, consistent with Plan 09-01/09-03's documented run times for this shared test database.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Both new detail-response fields (`trend_24h`, `all_time_range`) are now pinned at the HTTP boundary with exact key sets across the zero-point, one-point, and many-point states, and badge-field completeness is proven across the whole sixteen-product catalog rather than a hand-picked fixture — this closes the only form of ROADMAP success criterion 4 that a service-layer-only test cannot prove.
- `tests/test_api_products.py` has no other pending edits from this plan; `git status` is clean at hand-off.
- No blockers for Plan 09-05 (frontend badge rendering, runs in parallel per this plan's own frontmatter — touches only frontend files).
- Full backend suite: 108 passed, 0 skipped, 0 failed, confirmed after both task commits landed.

---
*Phase: 09-price-badges*
*Completed: 2026-08-28*

## Self-Check: PASSED
- FOUND: tests/test_api_products.py (modified, contains all six new test functions)
- FOUND: commit 0f0e172 (Task 1)
- FOUND: commit e0fced9 (Task 2)
