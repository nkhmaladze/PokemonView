---
phase: 06-react-spa-frontend-active-price-product
reviewed: 2026-07-15T00:00:00Z
depth: standard
files_reviewed: 37
files_reviewed_list:
  - frontend/.gitignore
  - frontend/index.html
  - frontend/package.json
  - frontend/src/api/client.js
  - frontend/src/api/client.test.js
  - frontend/src/components/FilterChips.jsx
  - frontend/src/components/FilterChips.module.css
  - frontend/src/components/FilterChips.test.jsx
  - frontend/src/components/FreshnessIndicator.jsx
  - frontend/src/components/FreshnessIndicator.module.css
  - frontend/src/components/FreshnessIndicator.test.jsx
  - frontend/src/components/PriceDisplay.jsx
  - frontend/src/components/PriceDisplay.module.css
  - frontend/src/components/PriceDisplay.test.jsx
  - frontend/src/components/ProductNotFound.jsx
  - frontend/src/components/ProductNotFound.module.css
  - frontend/src/components/ProductRow.jsx
  - frontend/src/components/ProductRow.module.css
  - frontend/src/components/ProductRow.test.jsx
  - frontend/src/components/SearchBar.jsx
  - frontend/src/components/SearchBar.module.css
  - frontend/src/components/SearchBar.test.jsx
  - frontend/src/components/TrendBadge.jsx
  - frontend/src/components/TrendBadge.module.css
  - frontend/src/components/TrendBadge.test.jsx
  - frontend/src/main.jsx
  - frontend/src/pages/CatalogPage.jsx
  - frontend/src/pages/CatalogPage.module.css
  - frontend/src/pages/CatalogPage.test.jsx
  - frontend/src/pages/ProductDetailPage.jsx
  - frontend/src/pages/ProductDetailPage.module.css
  - frontend/src/pages/ProductDetailPage.test.jsx
  - frontend/src/router.jsx
  - frontend/src/router.test.jsx
  - frontend/src/setupTests.js
  - frontend/src/styles/tokens.css
  - frontend/src/utils/relativeTime.js
  - frontend/src/utils/relativeTime.test.js
  - frontend/vite.config.js
findings:
  critical: 1
  warning: 5
  info: 4
  total: 10
status: issues_found
---

# Phase 06: Code Review Report

**Reviewed:** 2026-07-15T00:00:00Z
**Depth:** standard
**Files Reviewed:** 37
**Status:** issues_found

## Summary

Reviewed the full React SPA frontend delivered for Phase 06 (catalog browse + product detail, active-price display). The code is generally clean, well-commented, and the display components (`PriceDisplay`, `TrendBadge`, `FreshnessIndicator`, `ProductRow`) faithfully implement the documented `price_status`-gated rendering contract in the happy path, and the test suite covers the documented happy-path and several defensive edge cases (e.g. null `listing_count`, null `msrp`/`release_date`, `no_data_yet`).

However, the review surfaced one real availability risk (a single malformed product record can crash the entire catalog page for every user, not just the affected row) and several correctness/consistency gaps: an un-guarded `Intl.RelativeTimeFormat` call that throws on invalid timestamps, an un-encoded route param interpolated into a fetch URL, a raw snake_case enum value leaked into detail-page copy, and a design-token/component mismatch (a "search-clear" affordance is referenced in `tokens.css` but never built). None of these are exploitable security vulnerabilities (no `dangerouslySetInnerHTML`, `eval`, hardcoded secrets, or injection surface exists in this file set), but the crash-blast-radius issue below should be fixed before shipping.

## Critical Issues

### CR-01: Single malformed product record crashes the entire catalog page for every user

**File:** `frontend/src/components/PriceDisplay.jsx:30`, `frontend/src/components/TrendBadge.jsx:16`, `frontend/src/router.jsx:21-26`

**Issue:** `PriceDisplay` and `TrendBadge` both assume their inputs are fully-populated whenever the caller has already checked `price_status === 'ok'`:

```js
// PriceDisplay.jsx
export default function PriceDisplay({ currentPrice, variant = 'heading' }) {
  ...
  <span className={totalClassName}>{formatCurrency(currentPrice.total_price)}</span>
  <span className={styles.price__secondary}>{formatCurrency(currentPrice.item_price)}</span>
```
```js
// TrendBadge.jsx
export default function TrendBadge({ trend }) {
  if (trend.status === 'insufficient_data') { ... }
```

If `currentPrice` is `null`/`undefined`, or `total_price`/`item_price` is missing, or `trend` is `null` (any of which would only require a single bad document from the ingestion/matching pipeline — a `price_status: "ok"` row whose `current_price`/`trend_7d`/`trend_30d` fields are incomplete), these components throw a `TypeError` during render. This is a real contract-violation risk given the project explicitly treats data source approval/pipeline reliability as an open risk (per `CLAUDE.md`'s Marketplace Insights API discussion).

Compounding this: `frontend/src/router.jsx` gives the `/products/:productId` route an `errorElement` (`ProductNotFound`), but the `/` (catalog) route does **not**:

```js
export const router = createBrowserRouter([
  {
    path: '/',
    Component: CatalogPage,
    loader: () => getProducts(),
    // no errorElement
  },
  ...
```

`CatalogPage` renders one `ProductRow` per item in a single flat list with no per-row error isolation (no error boundary around `ProductRow`). So a throw inside `PriceDisplay`/`TrendBadge` for **one** product in the array propagates up and, because `/` has no `errorElement`, unmounts the *entire* catalog list — every other valid, correctly-priced product becomes unreachable and the user sees React Router's default unstyled "Unexpected Application Error!" screen instead of the catalog. This directly undermines the stated core value ("must always be accurate and current" — a full outage is strictly worse than a degraded row).

Note the codebase already demonstrates the correct defensive pattern elsewhere (`ProductDetailPage.jsx`'s `formatMsrp`/`formatSampleSize` both use `typeof x === 'number'` guards before formatting) — this fix should bring `PriceDisplay`/`TrendBadge` up to that same standard, and/or add an `errorElement` to the `/` route as a backstop.

**Fix:**
```js
// PriceDisplay.jsx
function formatCurrency(value) {
  return typeof value === 'number' ? `$${value.toFixed(2)}` : '—'
}

// TrendBadge.jsx
export default function TrendBadge({ trend }) {
  if (!trend || trend.status === 'insufficient_data') {
    return (/* muted dash, as today */)
  }
  ...
}
```
```js
// router.jsx — add a backstop so one bad row degrades gracefully instead of
// taking down the whole catalog
{
  path: '/',
  Component: CatalogPage,
  loader: () => getProducts(),
  errorElement: <CatalogLoadError />,
},
```

## Warnings

### WR-01: `formatRelativeTime` throws a `RangeError` on invalid/missing timestamps

**File:** `frontend/src/utils/relativeTime.js:23-31`
**Issue:**
```js
export function formatRelativeTime(isoString) {
  const diffSeconds = (new Date(isoString).getTime() - Date.now()) / 1000
  for (const [unit, secondsInUnit] of UNITS) {
    if (Math.abs(diffSeconds) >= secondsInUnit || unit === 'second') {
      return rtf.format(Math.round(diffSeconds / secondsInUnit), unit)
    }
  }
}
```
If `isoString` is `null`/`undefined`/malformed, `new Date(isoString).getTime()` is `NaN`, so `diffSeconds` is `NaN`. The loop falls through to the `unit === 'second'` branch and calls `rtf.format(NaN, 'second')`. Per the ECMA-402 spec, `Intl.RelativeTimeFormat.prototype.format` throws a `RangeError` ("value must be finite") for a non-finite value — it does not silently return a fallback string. `FreshnessIndicator` passes `current_price.as_of` straight through with no validation, so any product whose `as_of` is missing/malformed on an otherwise-valid `"ok"` product would throw during render on the detail page, and (since the detail route's `errorElement` is `ProductNotFound`) would incorrectly show "Product not found." for a product that does exist — misleading copy that actively contradicts the actual failure. The existing test suite (`relativeTime.test.js`) never exercises an invalid-input case, so this gap is untested.
**Fix:**
```js
export function formatRelativeTime(isoString) {
  const diffSeconds = (new Date(isoString).getTime() - Date.now()) / 1000
  if (!Number.isFinite(diffSeconds)) return 'an unknown time'
  ...
}
```

### WR-02: `getProductDetail` interpolates an un-encoded route param into the fetch URL

**File:** `frontend/src/api/client.js:35`
**Issue:**
```js
export const getProductDetail = (productId) => request(`/products/${productId}`)
```
`productId` comes from `useParams()`/route params (`router.jsx:30`, `params.productId`) and is interpolated directly into the URL path with no `encodeURIComponent`. A `productId` containing reserved URL characters (`#`, `?`, `&`, `/`, spaces) will either 404 unexpectedly, be silently truncated at a `#`/`?`, or be split into extra path segments — producing a confusing failure mode instead of a clean, encoded request to the intended resource.
**Fix:**
```js
export const getProductDetail = (productId) =>
  request(`/products/${encodeURIComponent(productId)}`)
```

### WR-03: `ProductDetailPage` renders the raw snake_case `product_type` value instead of a human-readable label

**File:** `frontend/src/pages/ProductDetailPage.jsx:76`
**Issue:**
```jsx
<span className={styles.detail__badge}>{product.set_name}</span>
<span className={styles.detail__badge}>{product.product_type}</span>
```
This renders the literal API enum value (e.g. `booster_box`, `booster_bundle`) directly to the user on the primary product page. Elsewhere in the same phase (`FilterChips.jsx`'s `PRODUCT_TYPE_OPTIONS`) a proper label map (`'booster_box' → 'Booster Box'`) already exists for exactly this purpose but is not reused here. This is inconsistent with the rest of the phase's stated copywriting-contract discipline (every other user-facing string in this phase is either a fixed literal or a formatted value — this is the one spot where a raw internal identifier leaks through) and isn't covered by `ProductDetailPage.test.jsx`, which never asserts on the rendered text of this badge.
**Fix:** Extract the `PRODUCT_TYPE_OPTIONS` label map to a shared module (see IN-01) and use it here:
```jsx
<span className={styles.detail__badge}>{PRODUCT_TYPE_LABELS[product.product_type] ?? product.product_type}</span>
```

### WR-04: Design token documents a "search-clear" control that was never implemented

**File:** `frontend/src/styles/tokens.css:40`, `frontend/src/components/SearchBar.jsx`
**Issue:**
```css
--size-tap-target-min: 44px; /* chips / search-clear min tap target, WCAG comfort minimum */
```
The token comment explicitly names a "search-clear" affordance (presumably a clear/reset "×" button inside or beside the search input) as a consumer of this token. `SearchBar.jsx` renders only a bare `<input>` with no clear button, and no other component in the reviewed set consumes `--size-tap-target-min` for a clear control — it's only applied to `.chip` (`FilterChips.module.css`) and `.search` (the whole input). Either the clear-button feature was scoped out silently (spec/implementation drift) or it was simply forgotten; as shipped there is no way to clear the search field except manually deleting typed text.
**Fix:** Either implement the clear button (small `×` button, `min-height`/`min-width: var(--size-tap-target-min)`, calls `onChange('')`) or remove the now-inaccurate "search-clear" reference from the token comment so it doesn't mislead future readers.

### WR-05: Catalog route (`/`) has no `errorElement`

**File:** `frontend/src/router.jsx:22-26`
**Issue:** Independent of CR-01's null-guard issue, the `/` route's loader (`() => getProducts()`) has no `errorElement`, unlike `/products/:productId`. Any rejection from `getProducts()` — e.g. the backend being unreachable, a non-2xx response, or a network error — propagates to react-router's default (unstyled, generic "Unexpected Application Error!") boundary instead of a page consistent with the rest of the app's design system. Given eBay API availability is called out as an explicit project risk (`CLAUDE.md`), the catalog's primary entry point should degrade gracefully.
**Fix:** Add a token-styled `errorElement` (e.g. reusing `ProductNotFound`'s layout pattern with different copy) to the `/` route, matching what already exists for the detail route.

## Info

### IN-01: `PRODUCT_TYPE_GLYPH` is duplicated verbatim across two files

**File:** `frontend/src/components/ProductRow.jsx:6-11`, `frontend/src/pages/ProductDetailPage.jsx:7-12`
**Issue:** The exact same `{ booster_pack: 'P', booster_box: 'B', booster_bundle: 'N', etb: 'E' }` object literal is defined independently in both files. Any future change to the glyph set (or a new product type) has to be remembered and applied in two places, and nothing enforces they stay in sync.
**Fix:** Extract to a shared module, e.g. `frontend/src/constants/productType.js`, and import it from both call sites.

### IN-02: `useRouteError()` is called but its result is discarded

**File:** `frontend/src/components/ProductNotFound.jsx:20`
**Issue:**
```jsx
// Read for potential future diagnostics only; the rendered copy below is
// always the fixed UI-SPEC "not found" text regardless of error.message.
useRouteError()
```
The hook is invoked purely for a documented "future" purpose with no current effect — it doesn't log, doesn't branch, doesn't render anything derived from it. This is effectively dead code today.
**Fix:** Either remove the call until it's actually needed, or use it now (e.g. `console.error` in dev, or a Sentry/logging call) so the comment's stated intent is actually realized.

### IN-03: `getProducts(filters)` server-side filter params are unreachable from any UI code path

**File:** `frontend/src/api/client.js:25-32`
**Issue:** `getProducts` builds `set`/`product_type`/`q` query params, but per the code's own comment ("per D-14 the catalog loader calls this with no arguments") and confirmed by `router.jsx:25` (`loader: () => getProducts()`), no call site in the app ever passes filters. The only exercise of this branch is `client.test.js`. This is explicitly documented as intentional "API-shape completeness," but as shipped it's dead code from the app's perspective and should be flagged for removal or wiring-up in a future phase rather than left indefinitely unreachable.
**Fix:** No action required now if intentionally deferred — just confirm this is tracked (e.g. a follow-up phase item) rather than silently forgotten.

### IN-04: Awkward pluralization in sample-size copy

**File:** `frontend/src/pages/ProductDetailPage.jsx:18-22`
**Issue:** `formatSampleSize` always renders `"Based on N active listing(s)"`, including for `N === 1` ("Based on 1 active listing(s)"), which reads as a placeholder rather than finished copy.
**Fix:**
```js
function formatSampleSize(listingCount) {
  if (typeof listingCount !== 'number') return 'Sample size unavailable'
  return `Based on ${listingCount} active listing${listingCount === 1 ? '' : 's'}`
}
```

---

_Reviewed: 2026-07-15T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
