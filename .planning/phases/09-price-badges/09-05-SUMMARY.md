---
phase: 09-price-badges
plan: 05
subsystem: ui
tags: [react, css-modules, product-detail-page, badge-wiring]

requires:
  - phase: 09-01
    provides: "TREND_24H_TOLERANCE_HOURS wiring and the third TrendBadge row this plan's section sits below"
  - phase: 09-02
    provides: "AllTimeRangeBadge.jsx — the two-state component this plan imports and renders"
  - phase: 09-03
    provides: "catalog_service.get_product_detail's all_time_range field this plan renders unmodified"
provides:
  - "ProductDetailPage.jsx renders the all-time range section (verbatim caption + AllTimeRangeBadge) between the trend row and the Price History section"
  - "ProductDetailPage.module.css::.detail__allTimeSection — new token-only rule"
affects: []

actuals:
  tokens: 2412
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "All-time range rendered as its own full-width block (not a fourth trend child) because its caption is an order of magnitude longer than 24h/7d/30d and would crowd them inline — same class name shape convention as detail__trendSection/detail__historySection"

key-files:
  created: []
  modified:
    - frontend/src/pages/ProductDetailPage.jsx
    - frontend/src/pages/ProductDetailPage.module.css
    - frontend/src/pages/ProductDetailPage.test.jsx

key-decisions:
  - "Task 1's own <verify> test run showed 2 pre-existing test failures (null-msrp em-dash ambiguity, no-data badge count) immediately after wiring the unconditional section, because okProduct's fixture didn't yet carry all_time_range. This is the exact, plan-documented consequence Task 2's action text names verbatim ('without it the badge falls into its muted branch and renders an em dash...') — not a defect in Task 1's implementation. Verified by running the full suite again after Task 2 landed the fixture field: 74/74 pass."

requirements-completed: [PRICE-08, PRICE-09]

coverage:
  - id: D1
    description: "The rendered page contains the exact verbatim caption 'All-time range (since we started tracking)', unconditionally, outside the price_status branch"
    requirement: "PRICE-09"
    verification:
      - kind: automated_ui
        ref: "frontend/src/pages/ProductDetailPage.test.jsx#renders the all-time range caption and its low-to-high value"
        status: pass
      - kind: other
        ref: "grep -c \"All-time range (since we started tracking)\" ProductDetailPage.jsx -> 1"
        status: pass
    human_judgment: false
  - id: D2
    description: "The all-time range block sits between the trend badge row and the Price History section (UI-SPEC D-UI-04), as a separate block rather than a fourth trend child"
    requirement: "PRICE-09"
    verification:
      - kind: automated_ui
        ref: "frontend/src/pages/ProductDetailPage.test.jsx#places the all-time range between the trend badges and the Price History section"
        status: pass
    human_judgment: false
  - id: D3
    description: "A product with zero price data renders four badges in their insufficient-data state (three trend + all-time range) with no crash, and the caption still renders beside the muted dash"
    requirement: "PRICE-08"
    verification:
      - kind: automated_ui
        ref: "frontend/src/pages/ProductDetailPage.test.jsx#renders a graceful no-data state for a \"no_data_yet\" product without throwing, and still shows all four badges"
        status: pass
    human_judgment: false
  - id: D4
    description: "The page never crashes when all_time_range is absent entirely (defensive branch beyond the backend's always-present contract), rendering the caption with a muted dash instead"
    requirement: "PRICE-09"
    verification:
      - kind: automated_ui
        ref: "frontend/src/pages/ProductDetailPage.test.jsx#renders without throwing when the all_time_range field is absent entirely"
        status: pass
    human_judgment: false
  - id: D5
    description: "The new stylesheet rule reuses only existing tokens.css custom properties (column flex, var(--space-xs) gap) and adds no numeric size literal or new custom property"
    verification:
      - kind: other
        ref: "grep -nE \":[[:space:]]*[0-9]+(px|rem|em)\" ProductDetailPage.module.css -> only pre-existing matches; git diff --stat tokens.css -> empty"
        status: pass
    human_judgment: false
  - id: D6
    description: "The long caption reflows to two lines on a narrow viewport with zero new CSS (no white-space: nowrap added), and the section's placement below rather than inline with the trend row avoids crowding at every viewport width"
    verification: []
    human_judgment: true
    rationale: "Requires visually running the app and narrowing the window to a phone width to confirm actual wrap/overlap behavior per 09-UI-SPEC.md's overflow row — held open as a backstop per the plan's own must_haves.truths[9] (verification: backstop), not pixel-proven by any unit test."

duration: ~35min
completed: 2026-08-28
status: complete
---

# Phase 9 Plan 5: All-Time Range Wiring Summary

**The all-time range now renders as its own full-width block between the trend row and the Price History section on `ProductDetailPage.jsx`, carrying its verbatim collection-window caption and the `AllTimeRangeBadge` from Plan 09-02, proven by page-level tests for the caption, the locked ordering, the four-badge zero-data state, and the absent-field defensive branch — each pinned by a demonstrated-then-reverted deliberate breakage.**

## Performance

- **Duration:** ~35 min
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments

- Added the `AllTimeRangeBadge` import and a new `detail__allTimeSection` block to `ProductDetailPage.jsx`, inserted between the closing `.detail__trendSection` div and the `.detail__historySection` div, containing the verbatim caption `All-time range (since we started tracking)` and `AllTimeRangeBadge` fed directly from `product.all_time_range` with no recomputation
- The section renders unconditionally, outside the `price_status` ternary — same convention as the three trend badges — and the page's block doc comment was extended to name this explicitly (no new fetch, loading state, or error state)
- Added `.detail__allTimeSection` to `ProductDetailPage.module.css`: column flex, `align-items: flex-start`, `gap: var(--space-xs)` — reusing only existing tokens, no numeric literal, no `white-space: nowrap` (so the 40-character caption can still reflow), no change to `tokens.css`
- `okProduct` fixture gained `all_time_range: {high: 172.5, low: 129.99, status: 'ok'}` (values distinct from the existing 150/145 price totals); `noDataProduct` gained the insufficient-data shape and the expected badge count rose from 3 to 4
- Four new/updated page tests: the verbatim caption + formatted value, the locked section ordering (between `30d` and `Price History`), the four-badge zero-data state (with the caption still present), and the defensive branch for `all_time_range` being absent entirely

## Task Commits

Each task was committed atomically:

1. **Task 1: Render the all-time range section between the trend row and the history chart** - `1c87c70` (feat)
2. **Task 2: Page-level coverage — caption, ordering, the four-badge zero-data state, and a missing field** - `42fd154` (test)

## Files Created/Modified

- `frontend/src/pages/ProductDetailPage.jsx` - Adds `AllTimeRangeBadge` import, the `detail__allTimeSection` block, and extends the block doc comment
- `frontend/src/pages/ProductDetailPage.module.css` - Adds the `.detail__allTimeSection` rule; updates the header comment's section-order description
- `frontend/src/pages/ProductDetailPage.test.jsx` - Extends both fixtures with `all_time_range`; raises the no-data badge count from 3 to 4; adds three new tests (caption+value, ordering, absent-field defensive branch)

## Decisions Made

- Ran Task 1's `<verify>` test command immediately after wiring the section, before Task 2's fixture update landed. It showed 2 pre-existing test failures (the null-msrp test's em-dash query became ambiguous; the no-data test's badge count was stale at 3). This is the exact scenario Task 2's own action text names as the reason the fixture must carry `all_time_range` at all — not a defect introduced by Task 1's implementation. `npm run build` and `npm run lint` both passed cleanly at the Task 1 boundary (production code was correct); the test-file gap was closed immediately by Task 2 in the same execution pass, and the full suite (74/74) passed once both commits landed.
- Fixed a lint warning (`no-unused-vars` on the destructured `all_time_range` field used only to omit it from the missing-field test's product object) by aliasing it to `_all_time_range` with an eslint-disable comment, so `npm run lint` stays at 0 new warnings beyond the pre-existing `only-export-components` set.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Unused-variable lint warning from the destructuring-omit pattern in the new absent-field test**
- **Found during:** Task 2, after adding `renders without throwing when the all_time_range field is absent entirely`
- **Issue:** `const { all_time_range, ...productWithoutAllTimeRange } = okProduct` triggered `eslint(no-unused-vars)` on `all_time_range`, since it's destructured only to exclude it from the spread.
- **Fix:** Renamed the destructured binding to `_all_time_range` with an inline `eslint-disable-next-line no-unused-vars` comment explaining the intent.
- **Files modified:** frontend/src/pages/ProductDetailPage.test.jsx
- **Verification:** `npm run lint` returns to only the 6 pre-existing `only-export-components` warnings, exit 0.
- **Committed in:** `42fd154` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — lint warning).
**Impact on plan:** None on behavior; the test's assertions and coverage are unchanged.

## Mutation Verification (recorded per acceptance criteria)

- **Caption-shortening mutation:** Temporarily changed the caption text from `All-time range (since we started tracking)` to `All-time range` in `ProductDetailPage.jsx`. Result: 4 of 16 tests in the file failed (every test that queries the full caption string). Reverted before commit.
- **Section-reordering mutation:** Temporarily moved the `.detail__allTimeSection` block to after the `.detail__historySection` block. Result: exactly the new ordering test (`places the all-time range between the trend badges and the Price History section`) failed (`expected 198 to be less than 151`). Reverted before commit.
- **Falsy-prop-guard removal mutation:** Temporarily changed `AllTimeRangeBadge`'s guard from `if (!range || range.status === 'insufficient_data')` to `if (range.status === 'insufficient_data')`. Result: exactly the absent-field test failed, with a thrown `TypeError: Cannot read properties of undefined (reading 'status')` rather than a silent pass — confirming the guard is load-bearing, not redundant. Reverted before commit.

## Issues Encountered

- `frontend/node_modules` was absent in this fresh worktree checkout (gitignored). Ran `npm ci` from the existing `package-lock.json` (no new packages added) before running any test/lint/build command — standard worktree environment setup, not a plan deviation.

## User Setup Required

None - no external service configuration required.

## Known Stubs

None. Both new page states (ok and insufficient-data) render real data flowing straight through from `useLoaderData()`; there is no hardcoded placeholder value or unwired mock data path introduced by this plan.

## Deferred / Human Verification

The plan's Task 2 `<verify>` includes a `<human-check>` step (visual confirmation of chip geometry, the caption's two-line wrap on a phone-width viewport, and the overall four-badge zero-data page against a running app). This plan has no `type="checkpoint:*"` task, so per the executor's autonomous-plan pattern this step is recorded here as deferred rather than performed inline. It maps to coverage deliverable D6 above (`human_judgment: true`) and to the plan's own `must_haves.truths[9]` (`verification: backstop`) — the placement decision (block below the trend row rather than inline) is judged sufficient by design and construction (no `white-space: nowrap`, reused `var(--space-xs)` gap) but was not pixel-verified in a real browser at every breakpoint in this session.

## Next Phase Readiness

- All four badge fields (`trend_24h`, `trend_7d`, `trend_30d`, `all_time_range`) now render end-to-end on `ProductDetailPage.jsx`, each unconditionally and each riding the existing synchronous `useLoaderData()` response with no separate fetch.
- This was the last plan in Phase 9's wave 3 (frontend wiring); Plan 09-04 (backend test files only) ran independently in the same wave with no file overlap.
- `git status` is clean at hand-off; full frontend suite (74 tests) and build both pass.

---
*Phase: 09-price-badges*
*Completed: 2026-08-28*
