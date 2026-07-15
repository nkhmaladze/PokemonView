# Phase 6: React SPA Frontend (active-price product) - Research

**Researched:** 2026-07-15
**Domain:** Greenfield React SPA (Vite + React 19 + React Router 7), pure REST client of a completed Flask API
**Confidence:** MEDIUM-HIGH (library versions and setup mechanics verified against npm registry and cross-checked web sources; Context7 MCP was unavailable this session, so docs-grade claims are WebSearch-sourced, not Context7-sourced — see Sources)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Browse Layout & Grouping**
- D-01: Dense list/table layout for the browse view — matches poe.ninja's actual style (compact rows: thumbnail, name, price, trend), not an image-forward card grid.
- D-02: The API's set-grouping (Pitch Black → Chaos Rising → Perfect Order → Ascended Heroes, newest first, per 05-CONTEXT.md D-10) surfaces as a flat, continuous list with a small set badge per row — no hard section breaks and no per-set tabs.
- D-03: All products/types are shown by default (nothing hidden behind an initial filter) — matches the API's "combinable, nothing hidden" filter design (05-CONTEXT.md D-08).
- D-04: Product images render as small thumbnails, not large/prominent art — the row stays text-dense, image is a secondary visual anchor.

**Price & Trend Display**
- D-05: `total_price` is the headline number; `item_price` (+ shipping breakdown) renders as an always-visible smaller line beneath it — never hidden behind a hover/tap interaction.
- D-06: Trend badges (7d/30d `pct_change`) are color-coded — green for price up, red for price down (stock-ticker style).
- D-07: When a trend's `status` is `"insufficient_data"` (API never omits the badge), it renders as a muted dash (—) — present but visually quiet, not an explicit "not enough data yet" sentence.
- D-08: `listing_count` (sample size) is shown on the product detail page only — omitted from the dense browse list to keep rows compact.

**Freshness & No-Data States**
- D-09: The "data as of [timestamp]" freshness indicator (PRICE-02) uses relative time ("2 hours ago"), not an absolute timestamp.
- D-10: Freshness is shown on the product detail page only, not in every browse-list row.
- D-11: A product with `price_status: "no_data_yet"` still appears in its normal position in the browse list, but the row is visually muted/grayed to signal "not yet actionable" without hiding it entirely.

**Search & Filter Interaction**
- D-12: Users narrow the list via a search box (free text against `display_name`/`set_name`, matching API `?q`) plus filter chips/tabs — not search-only or chips-only.
- D-13: `product_type` (booster pack / booster box / booster bundle / ETB) gets its own explicit chip/tab control — not left to free-text search alone.
- D-14: Search filters live/instantly as the user types (no submit action, no debounce concerns given the ≤16-product catalog size).

### Claude's Discretion
- Whether `set_name` gets its own explicit filter chip control alongside `product_type`, or is left to the set-badge-plus-search-text combination — reasonable to add a set filter chip too, symmetric with D-13's product_type chips, unless research/planning finds a reason not to.
- Exact component structure, state management approach, and file organization — follow `ARCHITECTURE.md`'s `frontend/src/{pages,components,api}` structure unless a decision above overrides it.
- Exact color values, typography, spacing, and other visual-design specifics — this phase has `UI hint: yes`, meaning `/gsd-ui-phase` should produce the detailed UI-SPEC.md design contract; the decisions above are product/behavior-level, not a full visual spec.
- Client-side routing library/approach for list vs. detail page navigation — React Router per STACK.md, standard usage.
- Whether/how to debounce or memoize live search given the tiny catalog size — implementation detail, not a product decision (D-14 only locks that it must feel instant).
- HTTP client choice (fetch vs. axios) and API error/loading-state handling patterns — implementation detail; no user preference expressed.
- Responsive/mobile behavior specifics — not discussed; default to a reasonably responsive dense list unless UI-SPEC phase surfaces a stronger requirement.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope. Historical sold-price charting was mentioned only as an explicit non-goal, already correctly scoped to Phase 8 in ROADMAP.md — nothing new was deferred.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PRICE-01 | User can view a product's current price, led by estimated total price (item + shipping) with pre-shipping item price shown as secondary detail | `current_price.total_price`/`current_price.item_price` are both already computed server-side (Phase 5) — no frontend math needed; see Code Examples `PriceDisplay` pattern and D-05. |
| PRICE-02 | User can see a "data as of [timestamp]" freshness indicator | `current_price.as_of` is an ISO-8601 string; use native `Intl.RelativeTimeFormat` (Don't Hand-Roll) to render "2 hours ago" per D-09. |
| PRICE-03 | User can see a price-trend badge (7d/30d % change) based on active-price history | `trend_7d`/`trend_30d` objects (`{pct_change, status}`) are pre-computed server-side; frontend only needs presentation logic (color by sign, muted dash for `insufficient_data`) per D-06/D-07. |
| SEARCH-01 | User can search/browse catalog products by name or set | Fetch the full (≤16-item) catalog once via `GET /products`, filter client-side per keystroke (D-14) — see Architecture Patterns Pattern 2. |
| SEARCH-02 | User can view a product detail page showing its price data | `GET /products/:id` returns the full detail shape in one call; React Router Data Mode loader fetches it on navigation — see Architecture Patterns Pattern 1. |
</phase_requirements>

## Summary

This phase builds a fully greenfield Vite + React 19 + React Router 7 SPA that is a pure, read-only REST client of the already-complete Phase 5 Flask API (`GET /products`, `GET /products/:id`). There are no new backend endpoints, no MongoDB access, no auth, and no charting — the API deliberately never returns a raw `price_points` series, so there is nothing to chart until Phase 8. The entire data-fetching surface is two GET calls returning small, fully-computed JSON payloads (current price, two trend objects, catalog metadata); the frontend's job is presentation logic only (formatting, color-coding, relative time, muted/graceful null-state rendering), not computation.

The most consequential research finding is a **version-drift correction**: `.planning/research/STACK.md` (researched 2026-07-12) recommends "Vite 6.x/7.x" and "React Router 7.x," but the npm registry today (2026-07-15, three days later) shows Vite's latest is now **8.1.4** and React Router shipped a **v8.2.0** major release on 2026-06-17 that removes the `react-router-dom` package entirely. This research verifies the actual current registry state and makes an explicit, prescriptive call: use **Vite 8.1.4** (current `@vitejs/plugin-react` 6.0.3 requires it via peer dependency anyway) paired with **React Router 7.18.1** — the latest release on the already-vetted v7 line — installed as the unified `react-router` package (not `react-router-dom`, which is legacy even within v7). This avoids adopting an un-vetted new major version mid-phase while still using current, non-stale tooling.

The second major finding is architectural: for a 2-route SPA (catalog list, product detail) with tiny, fully-server-computed payloads, **React Router 7 Data Mode (`createBrowserRouter` + route `loader` functions)** is a better fit than manual `useEffect` fetching — it eliminates per-component loading-state boilerplate, avoids the race-condition/waterfall problems the React team has explicitly deprecated `useEffect`-for-fetching over, and maps naturally 1:1 onto this phase's exact two routes. Native `fetch` (not axios) is sufficient given only two endpoints and zero interceptor/retry needs. Live search (D-14) should be a client-side, in-memory filter of the already-loaded ≤16-item catalog — never a per-keystroke network call — which also sidesteps any debounce complexity entirely.

**Primary recommendation:** Scaffold with `npm create vite@latest frontend -- --template react`, install `react-router@7.18.1` (not `react-router-dom`), use Data Mode loaders for the two routes, fetch the full catalog once and filter client-side for search/chips, and format all price/trend/freshness values with pure presentation components that trust the API's pre-computed shape exactly as documented in `catalog_service.py`/`price_service.py`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Catalog data (products, current price, trends) | API / Backend | — | Already fully computed and served by Phase 5 (`catalog_service.py`, `price_service.py`); frontend never re-derives price/trend math. |
| Route-level data fetching (list, detail) | Browser / Client | API / Backend | React Router loaders run in the browser but the actual computation lives server-side; client only orchestrates the fetch timing relative to navigation. |
| Search / filter (name, set, product_type) | Browser / Client | API / Backend (optional) | D-14 requires instant, no-debounce filtering; with ≤16 products, filtering the already-fetched list in-memory is both simpler and faster than a network round-trip per keystroke. The API's `?q`/`?set`/`?product_type` params exist and could be used, but client-side filtering is the correct choice at this catalog size. |
| Price/trend/freshness presentation (formatting, color, relative time, muted states) | Browser / Client | — | Pure display logic over already-computed values (D-05 through D-11); no business logic duplicated from the API. |
| Cross-origin request handling (CORS) | API / Backend | — | Already configured in Phase 5 (`Flask-CORS`, scoped to `r"/products*"` only, CR-02) — this phase must call exactly `/products` and `/products/<id>`, no other path prefix, or CORS will reject the request in a non-wildcard production config. |
| Dev-time request routing (Vite proxy) | Browser / Client (build tooling) | — | A `vite.config.js` `server.proxy` entry avoids relying on CORS at all in local dev and keeps frontend code using relative paths, closer to a same-origin production topology. |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| react | 19.2.7 | UI library | `[VERIFIED: npm registry]` Current stable; matches STACK.md's already-locked choice. |
| react-dom | 19.2.7 | DOM renderer | `[VERIFIED: npm registry]` Must match `react`'s exact minor/patch line. |
| vite | 8.1.4 | Build tool / dev server | `[VERIFIED: npm registry]` Current latest; STACK.md said "6.x/7.x" (researched 3 days earlier) — registry has since moved to 8.x as latest. `@vitejs/plugin-react`'s current release requires it via peer dependency (`vite: ^8.0.0`), so pinning to a stale 6.x/7.x would force an older, less-current plugin too. |
| @vitejs/plugin-react | 6.0.3 | Vite's official React plugin (Fast Refresh, JSX transform) | `[VERIFIED: npm registry]` Latest; peer-requires `vite ^8.0.0`, confirming the Vite 8 pairing above. |
| react-router | 7.18.1 | Client-side routing (Data Mode: `createBrowserRouter`, loaders) | `[VERIFIED: npm registry]` Latest release on the v7 line (dist-tag `version-7`). Install the unified `react-router` package directly — **not** `react-router-dom` — per official current guidance (new projects should import from `react-router` since v7 merged DOM bindings into the base package; `react-router-dom` is a legacy re-export, and v8 removes it entirely). `[CITED: reactrouter.com/upgrading/v7, multiple 2026 sources]` |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| vitest | 4.1.10 | Test runner (Nyquist validation requires a frontend test framework — none exists yet) | `[VERIFIED: npm registry]` Peer-supports `vite ^6.0.0 \|\| ^7.0.0 \|\| ^8.0.0` — compatible with the Vite 8 pin above. Use for all component/unit tests. |
| @testing-library/react | 16.3.2 | React component testing utilities | `[VERIFIED: npm registry]` Peer-supports `react ^18.0.0 \|\| ^19.0.0` — compatible with React 19.2.7. Use for rendering components and querying output in tests. |
| @testing-library/jest-dom | 6.9.1 | Custom Vitest/Jest matchers (`toBeInTheDocument`, etc.) | `[VERIFIED: npm registry]` Standard companion to Testing Library; import once in a setup file. |
| @testing-library/user-event | 14.6.1 | Realistic user interaction simulation (typing, clicking) | `[VERIFIED: npm registry]` Use for search-box typing tests (SEARCH-01) and chip-click tests (D-13). |
| jsdom | 29.1.1 | DOM environment for Vitest | `[VERIFIED: npm registry]` Required as Vitest's `environment: 'jsdom'` — no browser needed to run component tests. |

**Explicitly NOT included this phase:** `recharts` (deferred to Phase 8 — API returns no raw `price_points` series, nothing to chart), `axios` (native `fetch` is sufficient for 2 endpoints — see Alternatives Considered), `react-router-dom` (superseded by the unified `react-router` package).

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| native `fetch` wrapped in a small helper | `axios` | Axios adds ~11.7kB gzipped and a dependency for interceptors/auto-JSON-parsing this project doesn't need (2 read-only endpoints, no auth headers, no retry logic). Reach for axios only if a future phase needs interceptor-based auth or request/response transformation pipelines. `[CITED: multiple 2026 sources cross-checked]` |
| React Router 7 Data Mode (loaders) | Manual `useEffect` + `useState` fetching | `useEffect`-fetching is the pattern the React team has moved away from recommending (race conditions, no built-in cancellation, waterfalls, per-component loading-state boilerplate) — Data Mode loaders fetch in parallel with navigation and centralize error handling via `errorElement`. `[CITED: reacttraining.com/blog/modern-data-fetching-in-react, multiple 2026 sources]` |
| React Router 7 Data Mode | React Router 7 Framework Mode (file-based routing, SSR) | Framework Mode adds a full-stack dev server/build pipeline PROJECT.md explicitly doesn't need ("React SPA," not SSR) — Data Mode gives loaders/actions without the framework overhead. |
| React Router 7.18.1 | React Router 8.2.0 | v8 (GA 2026-06-17) is a real, current release with a "boring" migration path from v7, but it raises baselines (Node 22.22+, Vite 7+, React 19.2.7+, ESM-only) and removes `react-router-dom` entirely — none of this is yet reflected in this project's STACK.md/ARCHITECTURE.md. Staying on the v7 line avoids introducing an unvetted major-version jump inside this phase; revisit v8 in a dedicated stack-update decision if desired. |
| Client-side search/filter (D-14) | Server-side `?q`/`?set`/`?product_type` query params on every keystroke | The API already supports these params (05-CONTEXT.md D-08), but firing a network request per keystroke against a ≤16-item catalog adds latency and complexity for zero benefit — D-14 explicitly notes "no debounce concerns given the ≤16-product catalog size," which only holds if filtering happens in-memory. |

**Installation:**
```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install react-router@7.18.1
npm install -D vitest@4.1.10 @testing-library/react@16.3.2 @testing-library/jest-dom@6.9.1 @testing-library/user-event@14.6.1 jsdom@29.1.1
```

**Version verification:** All versions above were verified via `npm view <package> version` / `npm view <package> dist-tags --json` against the live npm registry on 2026-07-15 (this session), not carried over from STACK.md's 2026-07-12 research. `@vitejs/plugin-react`'s peer dependency (`vite: ^8.0.0`) was checked via `npm view @vitejs/plugin-react peerDependencies` to confirm the Vite 8 pairing is required, not optional.

## Package Legitimacy Audit

| Package | Registry | Age (latest publish) | Downloads/wk | Source Repo | Verdict | Disposition |
|---------|----------|----------------------|--------------|--------------|---------|-------------|
| react | npm | 2026-06-01 | 143,867,154 | github.com/facebook/react | OK | Approved |
| react-dom | npm | 2026-06-01 | 112,109,529 | github.com/facebook/react | OK | Approved |
| vite | npm | 2026-07-09 | 117,419,398 | github.com/vitejs/vite | SUS (`too-new`) | Approved — see note below |
| @vitejs/plugin-react | npm | 2026-06-23 | 54,497,110 | github.com/vitejs/vite-plugin-react | SUS (`too-new`) | Approved — see note below |
| react-router | npm | 2026-07-08 | 38,821,342 | github.com/remix-run/react-router | SUS (`too-new`) | Approved — see note below |
| vitest | npm | 2026-07-06 | 72,143,771 | github.com/vitest-dev/vitest | SUS (`too-new`) | Approved — see note below |
| @testing-library/react | npm | 2026-01-19 | 44,096,135 | github.com/testing-library/react-testing-library | OK | Approved |
| @testing-library/jest-dom | npm | 2025-10-01 | 50,035,106 | github.com/testing-library/jest-dom | OK | Approved |
| @testing-library/user-event | npm | 2025-01-21 | 38,453,680 | github.com/testing-library/user-event | OK | Approved |
| jsdom | npm | 2026-04-30 | 61,604,284 | github.com/jsdom/jsdom | OK | Approved |

**Packages removed due to [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** `vite`, `@vitejs/plugin-react`, `react-router`, `vitest` — all four flag purely on the `too-new` signal (their *latest patch/minor* was published within days of this research), not on any legitimacy red flag. Each has tens-to-hundreds of millions of weekly downloads and an official, long-established GitHub org (Google-adjacent Vite team, Meta/Facebook, Remix/Shopify-backed React Router, Vitest core team) — this is the exact same "recent-release-date false positive" pattern this project's STATE.md has already documented and human-approved for `pymongo`, `apscheduler`, `rapidfuzz`, `flask`, and `flask-cors` in prior phases. **Per protocol this verdict is still kept and the planner must add a `checkpoint:human-verify` task before each of these four installs**, but the pattern strongly suggests routine re-approval rather than a real risk.

*No packages in this audit were discovered via WebSearch/training-data package-name guessing without registry confirmation — all ten were directly resolved and verified against the live npm registry this session.*

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                              BROWSER                                 │
│                                                                        │
│   User navigates to "/"  ──────────────┐                             │
│                                          ▼                             │
│                              React Router (Data Mode)                 │
│                              createBrowserRouter                      │
│                                          │                             │
│                    ┌─────────────────────┴─────────────────────┐      │
│                    ▼                                           ▼      │
│         Route "/" — CatalogPage                    Route "/products/:id" │
│         loader: fetch full catalog once            — ProductDetailPage  │
│                    │                                loader: fetch one   │
│                    │                                product's detail    │
│                    ▼                                           │       │
│      In-memory filter (search text,                            │       │
│      product_type chip, set chip) — D-14                       │       │
│      no network call per keystroke                              │       │
│                    │                                           │       │
│                    ▼                                           ▼       │
│      Dense row list: thumbnail, name, set badge,    Detail view: price │
│      total_price (headline) + item_price            (total-led/item-   │
│      (secondary), trend badge (color/dash),          secondary),       │
│      muted styling if price_status="no_data_yet"      trend badges,    │
│                                                        freshness "as of"│
└─────────────────────────┬──────────────────────────────────┬─────────┘
                           │ fetch('/products')               │ fetch('/products/:id')
                           ▼                                  ▼
              ┌─────────────────────────────────────────────────────┐
              │        Vite dev proxy (dev) / same relative path      │
              │        (prod, behind reverse proxy or configured      │
              │        CORS_ORIGINS)                                  │
              └─────────────────────────┬───────────────────────────┘
                                          ▼
              ┌─────────────────────────────────────────────────────┐
              │   Flask API (Phase 5, already complete)               │
              │   GET /products  → catalog_service.list_products      │
              │   GET /products/:id → catalog_service.get_product_    │
              │                        detail                          │
              │   (Flask-CORS scoped to r"/products*" only — CR-02)   │
              └─────────────────────────┬───────────────────────────┘
                                          ▼
              ┌─────────────────────────────────────────────────────┐
              │   MongoDB (products, price_points) — read-only from   │
              │   this phase's perspective; never touched directly    │
              │   by the frontend                                     │
              └─────────────────────────────────────────────────────┘
```

### Recommended Project Structure
```
frontend/
├── index.html
├── vite.config.js          # plugin-react, dev server proxy, vitest config block
├── package.json
├── src/
│   ├── main.jsx             # ReactDOM.createRoot + RouterProvider
│   ├── router.jsx           # createBrowserRouter([...]) route table + loaders
│   ├── pages/
│   │   ├── CatalogPage.jsx        # SEARCH-01 — list + search box + filter chips
│   │   └── ProductDetailPage.jsx  # SEARCH-02, PRICE-01/02/03 — detail view
│   ├── components/
│   │   ├── ProductRow.jsx         # D-01/D-02/D-04/D-11 — one dense list row
│   │   ├── PriceDisplay.jsx       # D-05 — total_price headline + item_price secondary
│   │   ├── TrendBadge.jsx         # D-06/D-07 — color-coded pct_change or muted dash
│   │   ├── FreshnessIndicator.jsx # D-09/D-10 — relative "as of" time
│   │   ├── SearchBar.jsx          # D-12/D-14 — free-text input, instant filter
│   │   └── FilterChips.jsx        # D-13 (+ optional set chip) — product_type/set tabs
│   ├── api/
│   │   └── client.js              # getProducts(), getProductDetail(id) — fetch wrapper
│   └── utils/
│       └── relativeTime.js        # Intl.RelativeTimeFormat wrapper (Don't Hand-Roll)
└── src/**/*.test.jsx        # Vitest + Testing Library, colocated with components
```

### Pattern 1: React Router 7 Data Mode with route-level loaders
**What:** Define routes with `createBrowserRouter`, attach a `loader` function per route that calls the `api/client.js` fetch wrapper; render with `<RouterProvider router={router} />`. Access loader data in the route component via `useLoaderData()`.
**When to use:** Both routes in this phase — the catalog list (loader fetches `GET /products` once, unfiltered) and the product detail page (loader fetches `GET /products/:id`, keyed off the route param).
**Example:**
```jsx
// src/router.jsx
import { createBrowserRouter } from "react-router";
import CatalogPage from "./pages/CatalogPage";
import ProductDetailPage from "./pages/ProductDetailPage";
import { getProducts, getProductDetail } from "./api/client";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: CatalogPage,
    loader: () => getProducts(),          // full catalog, unfiltered — client-side filter after
  },
  {
    path: "/products/:productId",
    Component: ProductDetailPage,
    loader: ({ params }) => getProductDetail(params.productId),
    errorElement: <ProductNotFound />,     // handles the API's 404 {"error":"not_found"}
  },
]);
```
```jsx
// src/main.jsx
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router";
import { router } from "./router";

createRoot(document.getElementById("root")).render(
  <RouterProvider router={router} />
);
```
Source: pattern synthesized from `[CITED: reactrouter.com/start/modes, reactrouter.com/main/start/modes]`, current as of 2026-07-15 WebSearch.

### Pattern 2: Client-side filtering over a single fetched catalog (D-14)
**What:** `CatalogPage` receives the full ≤16-item catalog from its loader once. Search text, `product_type` chip selection, and (optional) `set` chip selection are all local component state (`useState`) that filter the already-loaded array on every render — no additional network calls.
**When to use:** Always for this phase's browse view — the catalog is small and fully returned by one `GET /products` call; re-fetching per keystroke would add latency for no benefit and contradicts D-14's "instant, no debounce concerns" requirement.
**Example:**
```jsx
// src/pages/CatalogPage.jsx
import { useLoaderData } from "react-router";
import { useState, useMemo } from "react";

export default function CatalogPage() {
  const products = useLoaderData(); // full array from the loader
  const [query, setQuery] = useState("");
  const [productType, setProductType] = useState(null); // D-13
  const [setName, setSetName] = useState(null);          // discretion: optional set chip

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return products.filter((p) => {
      if (productType && p.product_type !== productType) return false;
      if (setName && p.set_name !== setName) return false;
      if (q && !p.display_name.toLowerCase().includes(q) && !p.set_name.toLowerCase().includes(q)) {
        return false;
      }
      return true;
    });
  }, [products, query, productType, setName]);

  // render SearchBar, FilterChips, then visible.map(p => <ProductRow key={p.id} product={p} />)
}
```

### Pattern 3: Pure presentation components trusting the API's pre-computed shape
**What:** `PriceDisplay`, `TrendBadge`, and `FreshnessIndicator` never recompute anything — they format fields the API already computed (`total_price`, `item_price`, `pct_change`, `status`, `as_of`). This matches the "explicit no-data over guessing" pattern already established across Phases 4-5.
**When to use:** Every price/trend/freshness rendering location in this phase.
**Example:**
```jsx
// src/components/TrendBadge.jsx — D-06/D-07
export default function TrendBadge({ trend }) {
  if (trend.status === "insufficient_data") {
    return <span className="trend-badge trend-badge--muted" aria-label="insufficient data">—</span>;
  }
  const isUp = trend.pct_change > 0;
  const isDown = trend.pct_change < 0;
  const sign = isUp ? "+" : "";
  return (
    <span className={`trend-badge ${isUp ? "trend-badge--up" : isDown ? "trend-badge--down" : "trend-badge--flat"}`}>
      {sign}{trend.pct_change}%
    </span>
  );
}
```

### Anti-Patterns to Avoid
- **Re-fetching the catalog from the server per keystroke:** Violates D-14's "instant" requirement in spirit even if debounced — filter the already-loaded array instead (Pattern 2).
- **Manual `useEffect` + `useState` fetch-on-mount for the two routes:** Reintroduces the exact race-condition/waterfall/loading-boilerplate problems React Router 7 Data Mode loaders solve for free (Pattern 1).
- **Recomputing `pct_change` or `total_price` in the frontend:** The API already computed these (`compute_pct_change`, `_product_summary`) — any frontend recomputation risks silently diverging from the server's numbers, which directly threatens the project's core value ("must always be accurate").
- **Calling any path other than `/products` or `/products/<id>`:** Flask-CORS is scoped to `r"/products*"` only (CR-02) — any other path prefix will be rejected by CORS in a non-wildcard production config even if it happens to exist.
- **Installing `recharts` or wiring a chart placeholder this phase:** The API never returns a `price_points` series (D-11 of 05-CONTEXT.md) — there is nothing to chart until Phase 8; don't over-build now.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Relative "time ago" formatting (D-09: "2 hours ago") | A manual `if (diffSeconds < 60) ... else if (diffMinutes < 60) ...` string-concatenation ladder, or pulling in `date-fns`/`dayjs` just for this one feature | Native `Intl.RelativeTimeFormat` (browser built-in, zero dependency, correctly localized) | `Intl.RelativeTimeFormat` has been broadly supported in evergreen browsers for years and needs no npm install; hand-rolled diff ladders are a classic source of off-by-one/pluralization bugs, and pulling a whole date library in for one string is unnecessary weight for a 2-page SPA. |
| Client-side routing (URL matching, navigation, browser history) | A custom `window.location`/`history.pushState` router | `react-router` (Data Mode) | Already the project's locked stack choice (STACK.md); hand-rolling history/URL-matching edge cases (back/forward, nested params) is exactly the kind of deceptively complex problem a router solves correctly by default. |
| API error/loading state per fetch call | Manually threading `loading`/`error`/`data` state through every component that fetches | React Router loaders + `errorElement` (Pattern 1) | Centralizes the 404 (`{"error":"not_found"}`) and 400 (`{"error":"invalid_product_type"}`) handling at the route boundary instead of duplicating try/catch logic in every component. |
| Search text matching | A hand-rolled fuzzy-match or regex-escaping layer on the client | Simple `.toLowerCase().includes()` substring match (mirrors the API's own `q_lower in display_name` logic in `catalog_service.py`) | The backend already does the exact same simple substring match server-side — mirroring it client-side keeps behavior consistent and avoids introducing a fuzzy-matching dependency (e.g. Fuse.js) that the backend doesn't use and the ≤16-item catalog doesn't need. |

**Key insight:** Every piece of "real" logic in this phase (price computation, trend computation, matching/exclusion, freshness source-of-truth) already lives in the tested Phase 5 API. The frontend's entire job is trustworthy, null-safe presentation of values it did not compute — the temptation to duplicate or "improve" logic client-side should be resisted everywhere.

## Common Pitfalls

### Pitfall 1: macOS AirPlay Receiver silently occupies port 5000, breaking local Flask dev server startup
**What goes wrong:** On macOS Monterey and later, `ControlCenter`'s built-in AirPlay Receiver binds ports 5000 and 7000 by default. If a developer starts the Phase 5 Flask API with its common default (`flask run`, port 5000) for local frontend integration testing, the server either fails to bind or (worse) AirPlay's own stub responds, causing confusing non-Flask error pages instead of a clear "port in use" error.
**Why it happens:** This is an OS-level default most developers don't know about until they hit it; it's specific to macOS (this project's dev environment is Darwin per the session's env info).
**How to avoid:** Run the Flask API on an explicit alternate port (e.g., `flask --app api.app:create_app run --port 5001`) and point the Vite dev proxy's `target` at that same port, or disable AirPlay Receiver in System Settings → General → AirDrop & Handoff.
**Warning signs:** `Address already in use` on port 5000, or a 403 response from an unfamiliar server when hitting `http://localhost:5000/products` directly.
**Confidence:** `[CITED: multiple independently-corroborated 2026 sources — medium.com/@Shamimw, dev.to/pheeria, alexwlchan.net, portie.dev]`

### Pitfall 2: ~11 of 16 catalog products have `image_url: null` — the thumbnail component must handle this by default, not as an edge case
**What goes wrong:** Per STATE.md's Phase 2 decision log ("~11 of 16 catalog entries left with `image_url=None`... rather than fabricated"), most products in the actual seeded catalog have no image. A `ProductRow` thumbnail built assuming `image_url` is always present will render broken `<img>` tags for the majority of rows, not a rare exception.
**Why it happens:** Easy to prototype against the 5 products that do have a resolved TCGplayer image and miss that the common case is actually "no image."
**How to avoid:** Design the thumbnail slot with an explicit placeholder/fallback state from the start (e.g., a generic set-icon or product-type icon), verified against a product known to have `image_url: null`, not just the ones that happen to have an image.
**Warning signs:** Broken-image icons in the majority of browse rows during manual verification.
**Confidence:** `[VERIFIED: STATE.md Phase 2-03 decision log entry in this project]`

### Pitfall 3: `release_date` and `msrp` are nullable — Pitch Black (pre-release) products need graceful handling everywhere these fields render
**What goes wrong:** Per the `products` collection's `$jsonSchema` validator (Phase 2-04 decision: "allows null on `release_date`/`msrp`/`image_url`... so Pitch Black's provisional pre-release documents seed cleanly"), a product can legitimately have `release_date: null` and/or `msrp: null`. Any detail-page or row rendering that assumes these are always populated (e.g., `product.release_date.split("-")`) will throw at render time for exactly the products D-11 says must still be visibly listed.
**How to avoid:** Guard every render of `release_date`/`msrp` with an explicit null check and a "TBD"/"—" fallback, mirroring the same "flag, never hide, never crash" philosophy D-11 already establishes for `price_status: "no_data_yet"`.
**Warning signs:** A blank white screen (uncaught render exception) specifically when viewing Pitch Black products, since it's the one set with `verified: false` and known-provisional metadata.
**Confidence:** `[VERIFIED: db/init_collections.py $jsonSchema + STATE.md Phase 2-04 decision log entry in this project]`

### Pitfall 4: Vite only exposes environment variables prefixed `VITE_` to client code
**What goes wrong:** If the API base URL (or any other dev-time config) needs to be configurable via an `.env` file read by Vite, a variable named e.g. `API_BASE_URL` (no `VITE_` prefix) will silently be `undefined` in the browser bundle — Vite strips non-`VITE_`-prefixed variables from `import.meta.env` by design (to prevent accidentally leaking server secrets into client bundles).
**How to avoid:** If any frontend-configurable value is needed beyond the Vite dev proxy (which needs no env var at all — it's config, not runtime code), prefix it `VITE_...` in `.env` and access via `import.meta.env.VITE_...`. For this phase, the dev proxy approach (Pattern in Code Examples) avoids needing any such variable at all — prefer that over a `VITE_API_BASE_URL` env var unless the planner has a specific reason to need one.
**Warning signs:** `fetch(undefined + "/products")` producing a nonsensical relative URL, or a value that works in `vite.config.js` (Node context, no prefix restriction) but is silently missing inside a React component (browser context, prefix restriction applies).
**Confidence:** `[CITED: well-established, stable Vite behavior]`

### Pitfall 5: `trend_7d`/`trend_30d` and `current_price` are never `undefined`, but `current_price` itself CAN be `null` — these are two different guard cases
**What goes wrong:** The API contract guarantees `trend_7d`/`trend_30d` are always present objects with a `status` field (never omitted, D-07) — but `current_price` is `null` whenever `price_status` is `"no_data_yet"` (D-01 of 05-CONTEXT.md). A component that destructures `current_price.total_price` without first checking `price_status === "ok"` will throw on exactly the "no data yet" products D-11 requires to remain visible (muted, not hidden).
**How to avoid:** Always branch on `price_status` first (`"ok"` vs `"no_data_yet"`) before touching any field inside `current_price`; trend badges can be rendered unconditionally since they're always populated objects.
**Warning signs:** Uncaught `TypeError: Cannot read properties of null` specifically on pre-release/no-data products.
**Confidence:** `[VERIFIED: api/services/catalog_service.py _product_summary() — read directly this session]`

## Code Examples

### Native fetch wrapper (no axios needed)
```javascript
// src/api/client.js
const BASE = ""; // relative — Vite dev proxy (or same-origin prod) handles the rest

async function request(path) {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const getProducts = (filters = {}) => {
  const params = new URLSearchParams();
  if (filters.set) params.set("set", filters.set);
  if (filters.product_type) params.set("product_type", filters.product_type);
  if (filters.q) params.set("q", filters.q);
  const qs = params.toString();
  return request(`/products${qs ? `?${qs}` : ""}`);
};

export const getProductDetail = (productId) => request(`/products/${productId}`);
```
*Note: `getProducts` accepts optional server-side filters for API-shape completeness, but per D-14/Pattern 2, the catalog loader should call it with no arguments (full unfiltered list) and filter client-side.*

### Vite dev server proxy (avoids relying on CORS in local dev)
```javascript
// vite.config.js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/products": {
        target: "http://localhost:5001", // match whichever port the Flask API actually runs on locally (see Pitfall 1)
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/setupTests.js",
  },
});
```
Source: pattern synthesized from `[CITED: multiple 2026 sources — tere.ro, thatsoftwaredude.com, dbi-services.com]`.

### Relative time formatting (Don't Hand-Roll)
```javascript
// src/utils/relativeTime.js
const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });
const UNITS = [
  ["year", 31536000], ["month", 2592000], ["week", 604800],
  ["day", 86400], ["hour", 3600], ["minute", 60], ["second", 1],
];

export function formatRelativeTime(isoString) {
  const diffSeconds = (new Date(isoString).getTime() - Date.now()) / 1000;
  for (const [unit, secondsInUnit] of UNITS) {
    if (Math.abs(diffSeconds) >= secondsInUnit || unit === "second") {
      return rtf.format(Math.round(diffSeconds / secondsInUnit), unit);
    }
  }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| `useEffect` + `useState` fetch-on-mount | `use()` hook + Suspense (full apps), or React Router Data Mode loaders (route-shaped apps) | React 19 GA (Dec 2024) popularized `use()`; React Router 7's Data Mode has been stable since its 2024 release | For this phase's 2-route shape, Data Mode loaders are the pragmatic choice — full `use()`+Suspense architecture is more machinery than a 2-page SPA needs. |
| `react-router-dom` as the install target | `react-router` (unified package) | React Router v7 (merged packages); v8 (GA 2026-06-17) removes `react-router-dom` entirely | Install `react-router` directly for this phase — do not install `react-router-dom`, even though STACK.md's example command predates this guidance shift. |
| Create React App | Vite | CRA officially sunset Feb 2025 by the React team | Already correctly reflected in this project's STACK.md — no action needed, just confirming it's still current. |
| Vite 6.x/7.x (STACK.md's researched recommendation) | Vite 8.1.4 (registry-verified current) | Vite 8 became latest sometime between STACK.md's research (2026-07-12) and this research (2026-07-15) | Use Vite 8.1.4 — it's what `npm create vite@latest` and the current `@vitejs/plugin-react` peer dependency both require anyway. |

**Deprecated/outdated:**
- `react-router-dom`: superseded by the unified `react-router` package; still installable on the v7 line but explicitly legacy, and removed outright in v8.
- Manual `useEffect` fetch-on-mount as the *default* data-fetching pattern for route-shaped SPAs: the React team's own docs now steer toward `use()`/Suspense or router-level data loading for anything beyond a single one-off fetch.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|----------------|
| A1 | Staying on React Router 7.18.1 (rather than adopting the newly-GA 8.2.0) is the right call for this phase | Standard Stack / Alternatives Considered | Low — v7 is still fully supported and current; if the user/planner prefers v8, the "boring migration" the v8 release notes describe means switching later is low-cost. Flagged explicitly so the planner can confirm rather than silently inheriting the choice. |
| A2 | Client-side (in-memory) filtering, not server-side `?q`/`?set`/`?product_type` calls, is the correct interpretation of D-14 for a ≤16-item catalog | Architecture Patterns Pattern 2 | Low-Medium — if the catalog grows meaningfully beyond ~16 products in a later milestone, this assumption would need revisiting (server-side filtering would then make more sense), but it exactly matches D-14's stated "no debounce concerns given the ≤16-product catalog size" reasoning today. |
| A3 | `Intl.RelativeTimeFormat` browser support is sufficient for this project's target audience without a polyfill | Don't Hand-Roll, Code Examples | Low — this is a long-stable, broadly-supported browser API; risk is negligible for a modern-browser-targeting price-tracking SPA, but not independently verified via a caniuse-style check this session. |
| A4 | Flask dev server port (5001 suggested in code examples) doesn't collide with anything else already running locally | Common Pitfalls Pitfall 1, Code Examples | Low — easily changed; flagged only because the exact port wasn't discoverable from repo config (no `run.py`/`Procfile` exists yet defining a canonical port). |

## Open Questions

1. **How should the `verified` boolean field render, if at all?**
   - What we know: `_product_summary()` includes a `verified` field (true/false) in every product response; 05-CONTEXT.md D-09 notes `verified:false` products (Pitch Black) "get no special handling" server-side and "pass through with the exact same field shape."
   - What's unclear: 06-CONTEXT.md's decisions (D-01 through D-14) never mention `verified` at all — it's not addressed as a UI concern, unlike `price_status`/`price_status: "no_data_yet"` which is explicitly handled (D-11).
   - Recommendation: Treat as out of scope for this phase's UI unless the planner or UI-SPEC phase decides otherwise — the field exists in the API contract but no locked decision requires surfacing it. Do not silently build a "verified" badge without a product decision backing it.

2. **What visual treatment does an exactly-zero `pct_change` (no price movement) get?**
   - What we know: D-06 locks green-for-up, red-for-down, stock-ticker style. D-07 locks a muted dash specifically for `status: "insufficient_data"`.
   - What's unclear: A trend with `status: "ok"` and `pct_change: 0.0` (price genuinely unchanged) isn't addressed — is it green, red, or a third neutral state?
   - Recommendation: Use a neutral/gray state distinct from both the up/down colors and the insufficient-data dash (Code Examples' `TrendBadge` sketches this as `trend-badge--flat`), but this is a genuine gap for the UI-SPEC phase to confirm, not an assumption to lock silently here.

3. **What port does the Flask API actually run on for local frontend development, and is `MONGODB_URI` already configured?**
   - What we know: `api/app.py`'s `create_app()` requires `MONGODB_URI` in the environment (raises `KeyError` if unset) and has no hardcoded port; Phase 2 STATE.md confirms a MongoDB Atlas M0 instance was provisioned and Phase 5 tests passed against a live app instance. Python 3.12.13 with Flask 3.1.3 and pymongo 4.17.0 are confirmed importable in this environment.
   - What's unclear: `.env` contents could not be inspected in this research session (sandbox permission boundary) — whether `MONGODB_URI` is currently populated couldn't be directly confirmed, only inferred from prior-phase history.
   - Recommendation: The planner/execution phase should include an early task that starts the Flask API locally (`flask --app api.app:create_app run --port 5001` or similar) and confirms a real `GET /products` response before building frontend integration tests against it — treat this as a verification step, not an assumption.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Vite 8 dev server/build (`engines.node: ^20.19.0 \|\| >=22.12.0`) | ✓ | v24.17.0 | — |
| npm | Package install/scaffolding | ✓ | 11.13.0 | — |
| Python 3.12 | Running the existing Flask API locally for frontend integration | ✓ | 3.12.13 | — |
| Flask (installed) | Local API server for dev/integration testing | ✓ | 3.1.3 (matches `requirements.txt` pin) | — |
| pymongo (installed) | Flask API's MongoDB driver | ✓ | 4.17.0 (matches `requirements.txt` pin) | — |
| MongoDB connection (`MONGODB_URI`) | Flask API startup (`create_app()` raises `KeyError` if unset) | Unconfirmed this session (sandbox blocked `.env` inspection) | — | Prior-phase STATE.md indicates an Atlas M0 instance was provisioned and working as of Phase 5; verify directly before building frontend integration tests against a live local API (see Open Question 3). |

**Missing dependencies with no fallback:** none identified — all core tooling (Node, npm, Python, Flask, pymongo) is already present and version-matched to the project's existing pins.

**Missing dependencies with fallback:** `MONGODB_URI` configuration status is unconfirmed but has a clear, low-cost verification step (start the Flask app locally and hit `GET /products`) rather than blocking planning.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Vitest 4.1.10 + @testing-library/react 16.3.2 |
| Config file | none yet — Wave 0 must add a `test` block to `frontend/vite.config.js` (see Code Examples) plus `frontend/src/setupTests.js` |
| Quick run command | `npx vitest run` (from `frontend/`) |
| Full suite command | `npx vitest run --coverage` (from `frontend/`) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PRICE-01 | `PriceDisplay` renders `total_price` as headline, `item_price` always visible as secondary | unit | `npx vitest run src/components/PriceDisplay.test.jsx` | ❌ Wave 0 |
| PRICE-02 | `FreshnessIndicator`/`formatRelativeTime` renders a human "X ago" string from an ISO `as_of` timestamp | unit | `npx vitest run src/utils/relativeTime.test.js` | ❌ Wave 0 |
| PRICE-03 | `TrendBadge` color-codes positive/negative `pct_change` and renders a muted dash for `status: "insufficient_data"` | unit | `npx vitest run src/components/TrendBadge.test.jsx` | ❌ Wave 0 |
| SEARCH-01 | `CatalogPage` filters the loaded list live as the user types, and via product_type chip selection | integration | `npx vitest run src/pages/CatalogPage.test.jsx` | ❌ Wave 0 |
| SEARCH-02 | `ProductDetailPage` renders price, trend, and freshness for a mocked loader response; renders a not-found state for a 404 | integration | `npx vitest run src/pages/ProductDetailPage.test.jsx` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `npx vitest run <changed-file>.test.jsx` (targeted)
- **Per wave merge:** `npx vitest run` (full frontend suite)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `frontend/vite.config.js` — add `test` block (`environment: 'jsdom'`, `globals: true`, `setupFiles`)
- [ ] `frontend/src/setupTests.js` — import `@testing-library/jest-dom` matchers
- [ ] Test tooling install: `npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom` (versions per Standard Stack)
- [ ] A lightweight fetch-mocking approach for `api/client.js` in tests — recommend `vi.spyOn(global, 'fetch')` or mocking the `api/client.js` module directly with Vitest's `vi.mock()`; do **not** add MSW (Mock Service Worker) as a dependency for just 2 endpoints — that's more infrastructure than this phase's scope justifies.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V2 Authentication | No | This phase has no auth — API is public read-only, no login flow (matches PROJECT.md scope). |
| V3 Session Management | No | No sessions/cookies used by this SPA. |
| V4 Access Control | No | No user-differentiated access — every visitor sees the same public catalog data. |
| V5 Input Validation | Yes | React's default JSX text-node rendering auto-escapes all interpolated values (`{value}`), which is sufficient for rendering API-returned strings (`display_name`, `set_name`) — never use `dangerouslySetInnerHTML` with API or user-supplied text. Search-box text is only ever used as a `.includes()` substring match against already-fetched local data (never built into a query string sent verbatim without `URLSearchParams` encoding, per the `getProducts` example). |
| V6 Cryptography | No | No secrets, tokens, or credentials handled by this frontend — the API requires no auth headers for these read-only endpoints. |
| V14 Configuration | Yes | No API keys or secrets belong in the frontend bundle (Vite bundles anything under `import.meta.env.VITE_*` into client-visible code) — this phase needs no such variable at all if the dev-proxy pattern is used; if a future phase adds one, it must never be a genuine secret. |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|----------------------|
| Reflected XSS via unescaped rendering of API/user text | Tampering / Information Disclosure | React's JSX text-node escaping (default behavior) — never use `dangerouslySetInnerHTML` for `display_name`/`set_name`/search text. |
| CORS misconfiguration allowing unintended origins in production | Spoofing | Already mitigated server-side in Phase 5 (`CORS_ORIGINS` env var, non-wildcard in production per `api/config.py`'s documented contract) — this phase must not introduce a workaround (e.g., a public CORS proxy) that bypasses that control. |
| Leaking a secret via a `VITE_`-prefixed env var | Information Disclosure | This phase needs no secrets; if any `VITE_*` variable is ever added, treat it as public/client-visible by definition — never put a real credential there. |

## Sources

### Primary (VERIFIED via npm registry, this session)
- `npm view react|react-dom|vite|@vitejs/plugin-react|react-router|vitest|@testing-library/react|@testing-library/jest-dom|@testing-library/user-event|jsdom version` — exact current versions
- `npm view react-router-dom|react-router dist-tags --json` — confirmed `react-router-dom` frozen at `7.18.1` (latest tag) while `react-router` has moved to `8.2.0` latest with a `version-7` dist-tag at `7.18.1`
- `npm view @vitejs/plugin-react peerDependencies` — confirmed `vite: ^8.0.0` requirement
- `npm view vite engines` — confirmed Node `^20.19.0 || >=22.12.0` requirement
- `gsd-tools query package-legitimacy check --ecosystem npm ...` — legitimacy audit for all 10 frontend packages
- Direct repo reads this session: `api/blueprints/products.py`, `api/services/catalog_service.py`, `api/services/price_service.py`, `api/app.py`, `api/config.py`, `api/db.py`, `.planning/STATE.md`, `.planning/config.json`

### Secondary (MEDIUM confidence — WebSearch, official/vendor domains)
- [Picking a Mode | React Router](https://reactrouter.com/start/modes) — Data/Declarative/Framework mode comparison
- [Updating from v7 | React Router](https://reactrouter.com/upgrading/v7) — v7→v8 migration, `react-router-dom` removal
- [React Router v8 | Remix](https://remix.run/blog/react-router-v8) — v8 GA baseline requirements (2026-06-17)
- [Vite Getting Started](https://vite.dev/guide/) — scaffolding command, template list

### Tertiary (LOW-MEDIUM confidence — WebSearch, community/blog, cross-checked across multiple independent articles)
- Vite dev proxy vs. CORS: tere.ro, thatsoftwaredude.com, dbi-services.com, medium.com/@kychok98
- fetch vs axios tradeoffs: react.wiki, blog.logrocket.com/axios-vs-fetch-2025, iproyal.com
- React 19 data-fetching patterns / useEffect deprecation stance: reacttraining.com/blog/modern-data-fetching-in-react, sitepoint.com, react.wiki
- React Router loaders vs useEffect: dev.to/peterintech, davidwilfred.com, boundev.ai
- macOS AirPlay port 5000 conflict (Pitfall 1): medium.com/@Shamimw, dev.to/pheeria, alexwlchan.net, portie.dev — 4+ independently-authored sources, consistent finding

## Metadata

**Confidence breakdown:**
- Standard stack (versions): HIGH — directly verified against live npm registry this session, not carried over from stale STACK.md numbers.
- Architecture (Data Mode loaders, client-side filtering): MEDIUM-HIGH — pattern is well-documented official React Router guidance, cross-checked across multiple sources; the specific "filter client-side for ≤16 items" call is this research's own reasoning applied to D-14, not a directly-cited external source.
- Pitfalls: MEDIUM-HIGH — 3 of 5 pitfalls are directly verified against this project's own code/decision history (highest confidence available); the macOS port-5000 pitfall is corroborated across 4+ independent community sources; the Vite env-var pitfall is stable, long-established Vite behavior.
- Context7 MCP tool was unavailable this session (`No such tool available` on both `resolve-library-id` calls) — all "docs-kind" research questions in the plan fell back to WebSearch per the tool_strategy's provider substitution rule; this caps several claims at `[CITED]`/MEDIUM rather than `[VERIFIED]`/HIGH where an official-docs fetch would normally apply.

**Research date:** 2026-07-15
**Valid until:** 2026-07-22 (7 days) — the frontend JS ecosystem is fast-moving and this research already found STACK.md's 3-day-old version numbers stale (Vite 6/7.x → 8.x, React Router v7-only → v8 GA); re-verify exact versions via `npm view` immediately before `npm install` if planning/execution starts more than a few days after this research date.

---
*Phase: 6-React SPA Frontend (active-price product)*
*Researched: 2026-07-15*
