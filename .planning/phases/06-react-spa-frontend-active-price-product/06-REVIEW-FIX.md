---
phase: 06-react-spa-frontend-active-price-product
fixed_at: 2026-07-15T19:20:00Z
review_path: .planning/phases/06-react-spa-frontend-active-price-product/06-REVIEW.md
iteration: 1
findings_in_scope: 6
fixed: 6
skipped: 0
status: all_fixed
---

# Phase 06: Code Review Fix Report

**Fixed at:** 2026-07-15T19:20:00Z
**Source review:** .planning/phases/06-react-spa-frontend-active-price-product/06-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 6 (1 critical + 5 warning; `fix_scope: critical_warning` — Info findings IN-01 through IN-04 excluded from this pass)
- Fixed: 6
- Skipped: 0

## Fixed Issues

### CR-01: Single malformed product record crashes the entire catalog page for every user

**Files modified:** `frontend/src/components/PriceDisplay.jsx`, `frontend/src/components/TrendBadge.jsx`, `frontend/src/router.jsx`, `frontend/src/components/CatalogLoadError.jsx` (new), `frontend/src/components/CatalogLoadError.module.css` (new)
**Commit:** `1c52dd9`
**Applied fix:** `PriceDisplay` now guards `currentPrice` being null/undefined (renders a dashed placeholder) and `formatCurrency` falls back to `'—'` for non-numeric values instead of throwing on `.toFixed`. `TrendBadge` now falls back to the existing muted "insufficient data" badge when `trend` is null/undefined or `trend.pct_change` is not a number, in addition to the existing `insufficient_data` status branch. Added a new `CatalogLoadError` component (mirroring `ProductNotFound`'s token-styled layout) wired as the `/` route's `errorElement` in `router.jsx`, as a backstop so a loader rejection or an unexpected render throw no longer takes down the entire catalog with react-router's default unstyled error screen.

### WR-01: `formatRelativeTime` throws a `RangeError` on invalid/missing timestamps

**Files modified:** `frontend/src/utils/relativeTime.js`
**Commit:** `6756a69`
**Applied fix:** Added `if (!Number.isFinite(diffSeconds)) return 'an unknown time'` immediately after computing `diffSeconds`, short-circuiting before the loop reaches `rtf.format(NaN, 'second')`, which would otherwise throw a `RangeError` per the ECMA-402 spec.

### WR-02: `getProductDetail` interpolates an un-encoded route param into the fetch URL

**Files modified:** `frontend/src/api/client.js`
**Commit:** `c997310`
**Applied fix:** `getProductDetail` now wraps `productId` in `encodeURIComponent()` before interpolating it into the request path, matching the suggested fix exactly. Existing test (`getProductDetail("some-id")` expects fetch called with `/products/some-id`) still passes since `encodeURIComponent` is a no-op for that value.

### WR-03: `ProductDetailPage` renders the raw snake_case `product_type` value instead of a human-readable label

**Files modified:** `frontend/src/pages/ProductDetailPage.jsx`
**Commit:** `a0e8b47`
**Applied fix:** Added a local `PRODUCT_TYPE_LABELS` map (mirroring the existing `PRODUCT_TYPE_GLYPH` duplication pattern already present in this file — see IN-01, out of scope for this pass) and rendered `PRODUCT_TYPE_LABELS[product.product_type] ?? product.product_type` instead of the raw enum value. Deliberately did not perform the broader shared-module extraction referenced in the review's "see IN-01" note, since IN-01 is an Info-severity finding excluded from `fix_scope: critical_warning`; a full extraction is left for that finding if/when it's addressed in a later pass.

### WR-04: Design token documents a "search-clear" control that was never implemented

**Files modified:** `frontend/src/styles/tokens.css`
**Commit:** `be34f62`
**Applied fix:** Chose the lower-risk of the review's two suggested options — removed the inaccurate "search-clear" reference from the `--size-tap-target-min` comment (now reads "chips min tap target, WCAG comfort minimum") rather than implementing a new clear-button UI affordance, which would be net-new feature work (new interactive element, accessibility considerations, new tests) outside the scope of a targeted code-review fix pass.

### WR-05: Catalog route (`/`) has no `errorElement`

**Files modified:** none (already resolved)
**Commit:** `1c52dd9` (same commit as CR-01)
**Applied fix:** This finding's fix is identical to part of CR-01's fix — adding `errorElement: <CatalogLoadError />` to the `/` route in `frontend/src/router.jsx`. Since CR-01 was fixed first (findings are processed critical-before-warning) and its fix already added this exact `errorElement`, no additional change was needed for WR-05 by the time it was processed; it is resolved by commit `1c52dd9`.

## Skipped Issues

None — all 6 in-scope findings were fixed.

## Verification

- `npx vitest run` (full suite): 11 test files, 42/42 tests passed after all fixes applied.
- `npm run build`: succeeded (44 modules transformed, including the 2 new `CatalogLoadError` files).
- Out of scope for this pass (per `fix_scope: critical_warning`): IN-01 (duplicated `PRODUCT_TYPE_GLYPH`), IN-02 (unused `useRouteError()` result in `ProductNotFound`), IN-03 (unreachable server-side filter params in `getProducts`), IN-04 (awkward pluralization in sample-size copy). None of these were touched.

---

_Fixed: 2026-07-15T19:20:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
