---
phase: 06-react-spa-frontend-active-price-product
plan: 05
subsystem: ui
tags: [react, react-router, css-modules, vitest, testing-library]

# Dependency graph
requires:
  - phase: 06-02
    provides: TrendBadge / PriceDisplay pure formatter primitives
  - phase: 06-04
    provides: SearchBar / FilterChips controlled filter controls
  - phase: 06-01
    provides: Vite + React 19 scaffold, Vitest/Testing Library/jsdom harness, tokens.css
provides:
  - "frontend/src/components/ProductRow.jsx — default export ProductRow({ product }), dense clickable list row wrapping a react-router Link, null-safe image placeholder, price_status-branched price slot, defensive trend badges"
  - "frontend/src/pages/CatalogPage.jsx — default export CatalogPage, the '/' route component: useLoaderData()-fed flat list with useMemo in-memory filtering over query/productType/setName and a 'No products found' empty state"
affects: [06-06, 06-07]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "ProductRow composes PriceDisplay/TrendBadge rather than reimplementing formatting, matching the discipline established by 06-02/06-04 (presentation components are pure formatters over the exact API contract)"
    - "CatalogPage is the sole owner of filter state (query/productType/setName) and the useMemo in-memory filter; SearchBar/FilterChips stay pure controlled inputs (06-04's established boundary)"
    - "TDD RED/GREEN commit split per component (test commit before feat commit)"

key-files:
  created:
    - frontend/src/components/ProductRow.jsx
    - frontend/src/components/ProductRow.module.css
    - frontend/src/components/ProductRow.test.jsx
    - frontend/src/pages/CatalogPage.jsx
    - frontend/src/pages/CatalogPage.module.css
    - frontend/src/pages/CatalogPage.test.jsx
  modified: []

key-decisions:
  - "Trend badges in ProductRow render defensively (only when product.trend_7d/trend_30d are present) per the plan's Contract note — today's GET /products list response (catalog_service._product_summary) does not include trend fields; those are added only on GET /products/:id (06-06). No backend change made."
  - "CatalogPage.test.jsx mocks only useLoaderData from react-router (vi.mock with importOriginal spread) so MemoryRouter/Link stay real, letting ProductRow's Link render exactly as it will in production"
  - "Placeholder thumbnail glyph derived from product_type via a small letter map (P/B/N/E) rather than an SVG icon — satisfies the plan's 'never a broken <img>' requirement without adding an icon asset; UI-SPEC's 'simple glyph/letter' phrasing explicitly allows this"

patterns-established:
  - "Pattern: list-row components branch on price_status/enum fields before touching nullable nested objects (current_price), and never render an <img> with a null/empty src — to be followed by ProductDetailPage (06-06) for its own image_url/current_price handling"

requirements-completed: [SEARCH-01, PRICE-01]

coverage:
  - id: D1
    description: "ProductRow renders a dense clickable row (Link to /products/:id, aria-label 'View {display_name} pricing details') composing PriceDisplay for price_status 'ok', a null-safe placeholder for missing image_url, and a muted 'No pricing data yet' state for price_status 'no_data_yet' without touching current_price — D-01/D-02/D-04/D-11, Pitfall 2/5"
    requirement: PRICE-01
    verification:
      - kind: unit
        ref: "frontend/src/components/ProductRow.test.jsx#renders name/price and links to /products/{id} for an \"ok\" product"
        status: pass
      - kind: unit
        ref: "frontend/src/components/ProductRow.test.jsx#renders a placeholder thumbnail (not a broken img) when image_url is null"
        status: pass
      - kind: unit
        ref: "frontend/src/components/ProductRow.test.jsx#renders muted \"No pricing data yet\" for a no_data_yet product without throwing"
        status: pass
    human_judgment: false
  - id: D2
    description: "CatalogPage renders a flat continuous list from useLoaderData(), filters live in-memory via useMemo over query/productType/setName with no per-keystroke fetch, and shows the 'No products found' empty state on zero matches — SEARCH-01/D-02/D-14"
    requirement: SEARCH-01
    verification:
      - kind: unit
        ref: "frontend/src/pages/CatalogPage.test.jsx#renders one ProductRow per product from loader data as a flat continuous list"
        status: pass
      - kind: unit
        ref: "frontend/src/pages/CatalogPage.test.jsx#typing a substring filters the list in-memory with no additional fetch"
        status: pass
      - kind: unit
        ref: "frontend/src/pages/CatalogPage.test.jsx#selecting a product_type chip narrows the list"
        status: pass
      - kind: unit
        ref: "frontend/src/pages/CatalogPage.test.jsx#shows the \"No products found\" empty state when filters produce zero matches"
        status: pass
    human_judgment: false

duration: ~6min
completed: 2026-07-15
status: complete
---

# Phase 06 Plan 05: Browse Page (ProductRow + CatalogPage) Summary

**ProductRow (dense clickable list row with null-safe thumbnail and muted no-data state) and CatalogPage (loader-fed flat list with live in-memory search/chip filtering and empty state) — the primary browse surface, composing the Wave 2 primitives into the poe.ninja-style dense catalog, both TDD'd green with 7 new unit tests.**

## Performance

- **Duration:** ~6 min
- **Completed:** 2026-07-15
- **Tasks:** 2/2
- **Files modified:** 6 (all created)

## Accomplishments
- `ProductRow({ product })` — a `Link` to `/products/{id}` with `aria-label="View {display_name} pricing details"`, null-safe `image_url` placeholder glyph (never a broken `<img>`), a `set_name` badge, a price slot branched on `price_status` (`PriceDisplay` for `"ok"`, "No pricing data yet" copy for `"no_data_yet"` — never touching `current_price` when null), and defensive `TrendBadge` rendering only when `trend_7d`/`trend_30d` are present on the row object
- `CatalogPage` — reads the full catalog via `useLoaderData()`, holds `query`/`productType`/`setName` in `useState`, computes `visible` via `useMemo` (case-insensitive substring match on `display_name`/`set_name`, exact match on `product_type`/`set_name`), renders a flat list of `ProductRow`s in loader order (no section headers/tabs) or the "No products found" empty state
- 7/7 new unit tests pass (36/36 total in `frontend/`); `npm run build` still succeeds

## Task Commits

Each task was committed via TDD RED/GREEN:

1. **Task 1 (RED): failing test for ProductRow** - `f576e61` (test)
2. **Task 1 (GREEN): ProductRow implementation** - `c50e403` (feat)
3. **Task 2 (RED): failing test for CatalogPage** - `92caff2` (test)
4. **Task 2 (GREEN): CatalogPage implementation** - `d92e056` (feat)

**Plan metadata:** (pending — final docs commit follows this summary)

## Files Created/Modified
- `frontend/src/components/ProductRow.jsx` - default export, `Link`-wrapped dense row composing `PriceDisplay`/`TrendBadge`
- `frontend/src/components/ProductRow.module.css` - `.row`/`.row--muted`, `.thumb`/`.thumb--placeholder`, `.row__name`, `.row__setBadge`, `.row__price`, `.row__noData`, `.row__trends`
- `frontend/src/components/ProductRow.test.jsx` - 3 tests covering ok / null-image / no_data_yet cases
- `frontend/src/pages/CatalogPage.jsx` - default export, loader-fed `useMemo` filter over query/productType/setName
- `frontend/src/pages/CatalogPage.module.css` - `.catalog`, `.title`, `.list`, `.empty`
- `frontend/src/pages/CatalogPage.test.jsx` - 4 tests covering flat rendering, search narrowing, chip narrowing, empty state (mocks only `useLoaderData` via `vi.mock('react-router', importOriginal)`)

## Decisions Made
- Trend badges render defensively in `ProductRow` (only when `trend_7d`/`trend_30d` are present), per the plan's Contract note reconciling CONTEXT/RESEARCH/UI-SPEC's mention of browse-row trend badges against the actual Phase 5 `GET /products` list contract, which omits those fields until the detail endpoint (06-06). No backend code touched.
- `CatalogPage.test.jsx` mocks only `useLoaderData` from `react-router` (spreading `importOriginal()` for everything else) so `MemoryRouter`/`Link` remain real — `ProductRow`'s `Link` renders exactly as it will in production rather than needing a second router-mocking strategy.
- Placeholder thumbnail uses a small `product_type -> letter` glyph map (P/B/N/E) rather than an SVG icon asset, satisfying the "never a broken `<img>`" requirement and UI-SPEC's "simple glyph/letter" placeholder language without adding a new asset dependency.

## Deviations from Plan

None - plan executed exactly as written. Both components' field usage, null-guard branching, and filter logic matched the plan's `<action>` blocks and 06-PATTERNS.md's `CatalogPage.jsx`/`ProductRow.jsx` sections with no ambiguity requiring a Rule 1-4 judgment call.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `ProductRow` and `CatalogPage` are ready to be wired into the router (06-07) with a loader calling `getProducts()` with no args for the `/` route — no further prop/contract changes needed.
- `ProductRow`'s defensive trend-badge rendering means it will automatically light up if a future change ever adds `trend_7d`/`trend_30d` to the list endpoint, with zero frontend rework.
- No blockers. Full frontend suite (9 test files, 36 tests) green; `vite build` clean.

---
*Phase: 06-react-spa-frontend-active-price-product*
*Completed: 2026-07-15*

## Self-Check: PASSED

All 6 created files confirmed present on disk (ProductRow.jsx, ProductRow.module.css, ProductRow.test.jsx, CatalogPage.jsx, CatalogPage.module.css, CatalogPage.test.jsx) plus this SUMMARY.md. All 4 task commit hashes (f576e61, c50e403, 92caff2, d92e056) confirmed present in `git log --oneline --all`.
