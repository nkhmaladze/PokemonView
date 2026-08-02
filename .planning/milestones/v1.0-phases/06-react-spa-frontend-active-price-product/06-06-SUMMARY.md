---
phase: 06-react-spa-frontend-active-price-product
plan: 06
subsystem: ui
tags: [react, react-router, css-modules, vitest, testing-library]

# Dependency graph
requires:
  - phase: 06-01
    provides: Vite + React 19 SPA scaffold, Vitest/Testing Library/jsdom harness, src/styles/tokens.css design tokens, api/client.js data layer
  - phase: 06-02
    provides: TrendBadge (4-state percent-change badge) and PriceDisplay (total-led headline + always-visible item-price secondary) presentation primitives
  - phase: 06-03
    provides: FreshnessIndicator ("Data as of {relative time}") + relativeTime.js
provides:
  - "frontend/src/pages/ProductDetailPage.jsx — default export ProductDetailPage, the /products/:productId route component composing PriceDisplay/TrendBadge/FreshnessIndicator over the GET /products/:id detail response"
affects: [06-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD RED/GREEN commit split (test commit before feat commit), matching 06-01/06-02/06-03's established convention"
    - "price_status-first null-guard before touching current_price (Pitfall 5), reused verbatim from ProductRow (06-05)"

key-files:
  created:
    - frontend/src/pages/ProductDetailPage.jsx
    - frontend/src/pages/ProductDetailPage.module.css
    - frontend/src/pages/ProductDetailPage.test.jsx
  modified: []

key-decisions:
  - "Fixed an authoring bug in this plan's own ProductDetailPage.test.jsx: exact-match getByText('TBD')/getByText('—', {exact:false}) false-failed because those strings are part of larger text nodes (\"MSRP: —\", \"Release date: TBD\"); switched both to regex matchers (/—/, /TBD/), same class of fix as 06-02's PriceDisplay.test.jsx deviation"

patterns-established:
  - "Pattern: ProductDetailPage is the sole consumer of trend_7d/trend_30d and the sample-size (listing_count) field — both are detail-page-only per D-08/D-10, never surfaced on ProductRow/CatalogPage"

requirements-completed: [SEARCH-02, PRICE-01, PRICE-02, PRICE-03]

coverage:
  - id: D1
    description: "ProductDetailPage renders total_price, item_price, both 7d/30d trend badges, the 'Data as of' freshness caption, and the sample-size caption for an \"ok\" detail object"
    requirement: SEARCH-02
    verification:
      - kind: unit
        ref: "frontend/src/pages/ProductDetailPage.test.jsx#renders total price, item price, both trend badges, freshness caption, and sample-size caption for an \"ok\" product"
        status: pass
    human_judgment: false
  - id: D2
    description: "Sample-size caption falls back to 'Sample size unavailable' when listing_count is null (D-08)"
    requirement: PRICE-01
    verification:
      - kind: unit
        ref: "frontend/src/pages/ProductDetailPage.test.jsx#shows \"Sample size unavailable\" when listing_count is null"
        status: pass
    human_judgment: false
  - id: D3
    description: "A \"no_data_yet\" detail renders a graceful no-data state without throwing, never touching the null current_price, while both always-present trend badges still render (Pitfall 5)"
    requirement: PRICE-03
    verification:
      - kind: unit
        ref: "frontend/src/pages/ProductDetailPage.test.jsx#renders a graceful no-data state for a \"no_data_yet\" product without throwing, and still shows both trend badges"
        status: pass
    human_judgment: false
  - id: D4
    description: "MSRP and release_date render the null-safe \"—\"/\"TBD\" fallbacks instead of crashing on a pre-release (Pitch Black-style) product (Pitfall 3)"
    requirement: PRICE-02
    verification:
      - kind: unit
        ref: "frontend/src/pages/ProductDetailPage.test.jsx#shows \"—\" for a null msrp and \"TBD\" for a null release_date"
        status: pass
    human_judgment: false

duration: ~10min
completed: 2026-07-15
status: complete
---

# Phase 06 Plan 06: Product Detail Page Summary

**ProductDetailPage — the `/products/:productId` route composing PriceDisplay (total-led, Display size), 7d/30d TrendBadges, FreshnessIndicator, and a null-safe sample-size/MSRP/release-date metadata block over the exact GET /products/:id contract — TDD'd green with 4 unit tests, delivering SEARCH-02 and making PRICE-01/02/03 user-observable together for the first time.**

## Performance

- **Duration:** ~10 min
- **Completed:** 2026-07-15
- **Tasks:** 1/1
- **Files modified:** 3 (all newly created)

## Accomplishments
- `ProductDetailPage` reads the detail object via `useLoaderData()` and renders: "← Back to catalog" link (accent color), a 96px null-safe thumbnail (same placeholder-glyph rule as `ProductRow`), `display_name` with a 2px accent underline, `set_name`/`product_type` Label badges
- Branches on `detail.price_status` **before** touching `current_price` (Pitfall 5): `"ok"` renders `PriceDisplay(variant="display")` + the sample-size caption + `FreshnessIndicator`; `"no_data_yet"` renders the "No pricing data yet" copy and never reads any `current_price` field
- `trend_7d`/`trend_30d` render in **both** price states (they are always-present `{pct_change,status}` objects per the API contract), side by side under "7d"/"30d" Label headers
- Sample-size caption: "Based on {n} active listing(s)" when `listing_count` is a number, else "Sample size unavailable" (D-08, detail-page only)
- MSRP renders `$X.XX` or "—" when null; `release_date` renders the date string or "TBD" when null (Pitfall 3) — never a crash on a pre-release product like Pitch Black
- Does not render the `verified` field or any `price_points`/chart series (out of scope per UI-SPEC Open Question 1 and D-11)
- 4/4 new unit tests pass (40/40 total in `frontend/`); `npm run build` still succeeds

## Task Commits

Task was committed via TDD RED/GREEN:

1. **Task 1 (RED): failing test for ProductDetailPage** - `678c94f` (test)
2. **Task 1 (GREEN): ProductDetailPage implementation** - `b581a4e` (feat)

**Plan metadata:** (pending — final docs commit follows this summary)

## Files Created/Modified
- `frontend/src/pages/ProductDetailPage.jsx` - default export, `price_status`-first null-guard, composes `PriceDisplay`/`TrendBadge`/`FreshnessIndicator`, null-safe MSRP/release_date fallbacks
- `frontend/src/pages/ProductDetailPage.module.css` - `.detail`, `.detail__header`, `.detail__title` (accent underline), `.detail__thumb` (96px), `.detail__priceSection`, `.detail__trendSection`, `.detail__meta`, `.sampleSize` — all token-driven, no hardcoded values
- `frontend/src/pages/ProductDetailPage.test.jsx` - 4 tests: "ok" full-composition render, null-`listing_count` fallback, `"no_data_yet"` graceful no-throw state, null-`msrp`/`release_date` fallbacks

## Decisions Made
- Fixed a bug in this plan's own `ProductDetailPage.test.jsx` "—"/"TBD" assertions — the plan's initial exact-match `getByText` calls false-failed because "—" and "TBD" are each part of a larger text node (`"MSRP: —"`, `"Release date: TBD"`); switched both assertions to regex matchers (`/—/`, `/TBD/`). Same class of authoring-precision fix as 06-02's `PriceDisplay.test.jsx` deviation.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed a bug in this plan's own ProductDetailPage.test.jsx MSRP/release_date null-fallback assertions**
- **Found during:** Task 1 (GREEN implementation, first test run)
- **Issue:** The authored test used `screen.getByText('—', { exact: false })` and `screen.getByText('TBD')` (exact match) to assert the null-safe fallback copy, but the implementation correctly renders these inside larger text nodes (`"MSRP: —"`, `"Release date: TBD"`), which caused `getByText('TBD')` (exact-match default) to not find any element and false-fail against correct implementation code.
- **Fix:** Switched both assertions to regex matchers `screen.getByText(/—/)` and `screen.getByText(/TBD/)`, which correctly match substrings within the larger text nodes.
- **Files modified:** frontend/src/pages/ProductDetailPage.test.jsx
- **Verification:** `npm --prefix ./frontend run test -- src/pages/ProductDetailPage.test.jsx` — 4/4 passing.
- **Committed in:** b581a4e (Task 1 GREEN commit, alongside the implementation)

---

**Total deviations:** 1 auto-fixed (1 bug fix in this plan's own authored test)
**Impact on plan:** No scope creep — implementation logic matches the plan's spec exactly; the fix was an assertion-precision correction needed to satisfy the plan's own acceptance checks.

## Issues Encountered
None beyond the deviation above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `ProductDetailPage` is ready to be wired into `router.jsx`'s `/products/:productId` route with a `loader: ({ params }) => getProductDetail(params.productId)` (06-07's scope) — no further changes needed to this component for that wiring.
- All three Wave 2 primitives (`TrendBadge`, `PriceDisplay`, `FreshnessIndicator`) are now composed together for the first time, proving PRICE-01/02/03 are simultaneously user-observable on a single page (SEARCH-02).
- The detail-page-only fields (`listing_count` sample-size caption, `trend_7d`/`trend_30d`, freshness) remain correctly absent from `ProductRow`/`CatalogPage` (D-08/D-10 boundary preserved).
- No blockers for 06-07 (routing/wiring).

---
*Phase: 06-react-spa-frontend-active-price-product*
*Completed: 2026-07-15*

## Self-Check: PASSED

All 3 created files confirmed present on disk (frontend/src/pages/ProductDetailPage.jsx, ProductDetailPage.module.css, ProductDetailPage.test.jsx) plus this SUMMARY.md. Both task commit hashes (678c94f, b581a4e) confirmed present in `git log --oneline --all`.
