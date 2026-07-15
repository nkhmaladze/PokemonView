---
phase: 06-react-spa-frontend-active-price-product
plan: 07
subsystem: ui
tags: [react-router, routing, error-boundary, vitest, end-to-end-verification]

# Dependency graph
requires:
  - phase: 06-05
    provides: CatalogPage loader-fed flat list with live filtering
  - phase: 06-06
    provides: ProductDetailPage composing PriceDisplay/TrendBadge/FreshnessIndicator over the detail contract
provides:
  - "frontend/src/router.jsx — named export router = createBrowserRouter([...]) wiring '/' -> CatalogPage (loader getProducts()) and '/products/:productId' -> ProductDetailPage (loader getProductDetail(params.productId)) with ProductNotFound as the errorElement"
  - "frontend/src/main.jsx — mounts <RouterProvider router={router} /> over createRoot, replacing the 06-01 placeholder"
  - "frontend/src/components/ProductNotFound.jsx — the detail-route errorElement rendering the locked 'Product not found.' state with a back link"
  - "Live human-verified proof that the full SPA (browse, filter, detail, 404) works end-to-end against the running Flask API"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "createMemoryRouter + injected-loader integration test pattern (router.test.jsx) for exercising the full route table without hitting a real network"
    - "Route-level errorElement as the sole 404 handling path (no per-component try/catch), per RESEARCH Pattern 1"

key-files:
  created:
    - frontend/src/router.jsx
    - frontend/src/components/ProductNotFound.jsx
    - frontend/src/components/ProductNotFound.module.css
    - frontend/src/router.test.jsx
  modified:
    - frontend/src/main.jsx

key-decisions:
  - "Task 3 (live end-to-end checkpoint) verified via a real running Flask API (port 5001) + Vite dev server; user typed 'approved' after confirming browse/filter/detail/404 all rendered correctly against live MongoDB-backed data — no unit-test substitute for this step, per RESEARCH Open Question 3"
  - "Dev servers (flask, vite) stopped after checkpoint approval — Task 3 is a verification-only gate with no files written; nothing depends on the servers staying up post-verification"

patterns-established:
  - "Pattern: router.jsx is the single source of truth for both loaders and 404 handling — CatalogPage/ProductDetailPage never fetch data themselves and never catch their own load errors"

requirements-completed: [SEARCH-01, SEARCH-02]

coverage:
  - id: D1
    description: "Navigating to '/' renders CatalogPage with data from the GET /products loader; navigating to '/products/:id' renders ProductDetailPage from the GET /products/:id loader"
    requirement: SEARCH-01
    verification:
      - kind: unit
        ref: "frontend/src/router.test.jsx#renders the catalog at '/'"
        status: pass
      - kind: manual
        ref: "Task 3 live checkpoint — browse view renders real products, search/filter narrows instantly"
        status: pass
    human_judgment: true
  - id: D2
    description: "A GET /products/:id 404 renders the 'Product not found' error state via the route errorElement, keeping a link back to the catalog"
    requirement: SEARCH-02
    verification:
      - kind: unit
        ref: "frontend/src/router.test.jsx#renders 'Product not found' at a bad detail id"
        status: pass
      - kind: manual
        ref: "Task 3 live checkpoint — visiting /products/does-not-exist rendered 'Product not found.' with a working back link"
        status: pass
    human_judgment: true
  - id: D3
    description: "main.jsx mounts the app via RouterProvider over the createBrowserRouter table"
    requirement: SEARCH-01
    verification:
      - kind: unit
        ref: "frontend/src/router.test.jsx (indirectly, via router import); grep -q RouterProvider frontend/src/main.jsx"
        status: pass
    human_judgment: false
  - id: D4
    description: "Detail page shows total-led price, item price, 7d/30d trend badges, freshness caption, and sample-size caption against real API data"
    requirement: SEARCH-02
    verification:
      - kind: manual
        ref: "Task 3 live checkpoint — detail view confirmed against a real product"
        status: pass
    human_judgment: true

duration: ~8min (continuation session)
completed: 2026-07-15
status: complete
---

# Phase 06 Plan 07: Router Wiring + Live End-to-End Verification Summary

**createBrowserRouter route table wiring CatalogPage/ProductDetailPage to their loaders with a centralized ProductNotFound errorElement, mounted via RouterProvider in main.jsx, and live-verified end-to-end against the running Flask API — completing SEARCH-01/SEARCH-02 and closing out Phase 6.**

## Performance

- **Duration:** ~8 min (this continuation session; prior session covered Tasks 1-2)
- **Completed:** 2026-07-15
- **Tasks:** 3/3 (Task 1 feat, Task 2 verification-only, Task 3 human checkpoint)
- **Files modified:** 5 (4 created, 1 rewritten)

## Accomplishments

- `router.jsx` exports `router = createBrowserRouter([...])` (imports from the unified `react-router` package, not `react-router-dom`) with two routes: `"/"` → `CatalogPage` with loader `() => getProducts()`, and `"/products/:productId"` → `ProductDetailPage` with loader `({ params }) => getProductDetail(params.productId)` and `errorElement: <ProductNotFound />`
- `main.jsx` rewritten to `createRoot(document.getElementById("root")).render(<RouterProvider router={router} />)`, replacing the 06-01 scaffold placeholder
- `ProductNotFound.jsx` renders the locked UI-SPEC copy ("Product not found." heading, "This product may have been removed from the catalog." body, "← Back to catalog" link) as the detail route's `errorElement` — centralizing 404 handling at the route boundary rather than per-component try/catch
- `router.test.jsx` uses `createMemoryRouter` with the same route table and injected loader stubs (resolving `getProducts` for `/`, rejecting `getProductDetail` throwing `new Error("not_found")` for the detail route) to prove both browse rendering and 404 handling without a real network call
- Full frontend suite green: 42/42 tests across 11 files (client, TrendBadge, PriceDisplay, relativeTime, FreshnessIndicator, SearchBar, FilterChips, ProductRow, CatalogPage, ProductDetailPage, router)
- Production build succeeds (`npm run build` → `frontend/dist/`, 293.72 kB JS / 8.66 kB CSS, gzip 93.41 kB / 1.88 kB)
- **Task 3 live end-to-end checkpoint approved by the user**: with the Flask API running on port 5001 (real MongoDB-backed data via Atlas) and the Vite dev server up, the human confirmed:
  - Browse view: dense flat product list rendered; search box filtered instantly; product_type and set chips narrowed the list; products with no image showed a placeholder (not a broken image); a no-pricing-data product showed a muted row with "No pricing data yet" rather than being hidden
  - Detail view: total-led price with item price beneath, 7d/30d trend badges (color-coded/muted-dash), "Data as of …" freshness caption, sample-size caption, and a working "← Back to catalog" link
  - 404 view: visiting a bogus product id rendered the "Product not found." state with a working back link
  - User's exact response: "approved"

## Task Commits

1. **Task 1: router.jsx + main.jsx + ProductNotFound (SEARCH-01/02)** — `0f87051` (feat)
2. **Task 2: Full frontend suite green + production build** — no commit (package.json test/build scripts already existed from 06-01; nothing to stage — re-verified in this session: 42/42 tests pass, build succeeds)
3. **Task 3: Live end-to-end verification** — no commit (verification-only human checkpoint, no files written; approved by user)

**Plan metadata:** (pending — final docs commit follows this summary)

## Files Created/Modified

- `frontend/src/router.jsx` - `createBrowserRouter` route table, two routes with loaders + the detail 404 `errorElement`
- `frontend/src/main.jsx` - mounts `RouterProvider` over `router`, replaces 06-01 placeholder, keeps the `./styles/tokens.css` import
- `frontend/src/components/ProductNotFound.jsx` - default export, locked "Product not found." copy + back link
- `frontend/src/components/ProductNotFound.module.css` - `.notFound` class
- `frontend/src/router.test.jsx` - `createMemoryRouter` integration test: catalog render at `/`, not-found render at a bad detail id

## Decisions Made

- Task 3's live checkpoint was carried out against a real running Flask API (port 5001, backed by the Phase 2 Atlas M0 MongoDB instance) rather than any mocked substitute — this is the only proof in the entire phase that the SPA fetches real data end-to-end (RESEARCH Open Question 3). All three manual verification steps (browse/filter, detail, 404) were confirmed by the user before this continuation proceeded.
- Both dev servers (Flask on :5001, Vite on :5173) were stopped after checkpoint approval since Task 3 writes no files and nothing downstream depends on them staying up.

## Deviations from Plan

None — plan executed exactly as written across all three tasks. Task 1 was completed and committed in the prior session (`0f87051`); Task 2's verification was re-run in this continuation session to confirm the suite is still green before closing the plan; Task 3 was approved by the user with no rendering issues reported.

## Issues Encountered

None.

## User Setup Required

None beyond what the plan's `user_setup` already specified (local Flask API running with `MONGODB_URI` populated) — confirmed present and working during the Task 3 checkpoint.

## Next Phase Readiness

- Phase 6 (react-spa-frontend-active-price-product) is now complete: all 7 plans executed, SEARCH-01/SEARCH-02 and PRICE-01/02/03 are fully user-observable and live-verified against the real API.
- The shippable v1 active-price product surface (browse, filter, detail, freshness, trend, 404 handling) is done. Remaining phases (per ROADMAP.md) cover launch/hardening (Phase 7) and the contingent sold-price surface (Phase 8, gated on Marketplace Insights API approval).
- No blockers carried forward from this plan.

---
*Phase: 06-react-spa-frontend-active-price-product*
*Completed: 2026-07-15*

## Self-Check: PASSED

All 5 files confirmed present on disk (frontend/src/router.jsx, frontend/src/main.jsx, frontend/src/components/ProductNotFound.jsx, frontend/src/components/ProductNotFound.module.css, frontend/src/router.test.jsx) plus this SUMMARY.md. Task 1 commit hash (0f87051) confirmed present in `git log --oneline --all`. Full suite (42/42 tests, 11 files) and production build re-verified green in this continuation session.
