# Phase 6: React SPA Frontend (active-price product) - Pattern Map

**Mapped:** 2026-07-15
**Files analyzed:** 15 (new, greenfield)
**Analogs found:** 0 exact-codebase / 15 (frontend does not exist yet) — all patterns sourced from RESEARCH.md's vetted Code Examples plus the exact backend API contract this SPA renders.

## Context: Greenfield Frontend, No In-Repo Analogs

`frontend/` does not exist anywhere in this repo (confirmed via `find`). The only prior code is Python (`api/`, `db/`, `scripts/`, `tests/`) — there is no React/JS precedent to copy component/hook/router structure from. Because of this:

- **"Analog" below means the RESEARCH.md Code Example that defines the pattern** (already vetted against npm registry + official React Router docs this session), not an existing file in this repo.
- **The one true in-repo analog every file must match exactly is the API response contract** — `api/services/catalog_service.py` `_product_summary()` (lines 40-82) and `get_product_detail()` (lines 148ff, trend fields at 173-174 and 181). Every frontend field name, null-handling branch, and status string must match this contract verbatim — do not invent field names or reshape the payload.
- The Python codebase's one transferable discipline (noted in CONTEXT.md `code_context`) is **"no top-level side effects on import"** — e.g. `api/blueprints/products.py` lines 16-19 explicitly call this out (no MongoClient construction, no route registration outside decorators at import time). The React equivalent: no side effects in component module scope, effects only inside hooks/loaders (already the design in Pattern 1 below).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `frontend/vite.config.js` | config | — | RESEARCH.md "Vite dev server proxy" example | research-example (no in-repo analog) |
| `frontend/src/main.jsx` | provider | request-response (router bootstrap) | RESEARCH.md Pattern 1 `main.jsx` example | research-example |
| `frontend/src/router.jsx` | route | request-response | RESEARCH.md Pattern 1 `router.jsx` example | research-example |
| `frontend/src/api/client.js` | service | request-response (fetch wrapper) | RESEARCH.md "Native fetch wrapper" example + `api/blueprints/products.py` (defines exact routes/error shapes to call) | research-example + in-repo contract |
| `frontend/src/pages/CatalogPage.jsx` | component | CRUD (read) / transform (client-side filter) | RESEARCH.md Pattern 2 `CatalogPage.jsx` example | research-example |
| `frontend/src/pages/ProductDetailPage.jsx` | component | request-response | RESEARCH.md Pattern 1 loader wiring + `catalog_service.get_product_detail()` (defines exact response shape) | research-example + in-repo contract |
| `frontend/src/components/ProductRow.jsx` | component | transform (presentation) | none (new UI shape); must honor `_product_summary()` fields | no in-repo UI analog |
| `frontend/src/components/PriceDisplay.jsx` | component | transform (presentation) | `_product_summary()` `current_price` shape (lines 72-77) — defines exact fields to render | in-repo contract only |
| `frontend/src/components/TrendBadge.jsx` | component | transform (presentation) | RESEARCH.md Pattern 3 `TrendBadge.jsx` example, cross-checked against `get_product_detail()` trend shape (lines 173-174, 181) | research-example + in-repo contract |
| `frontend/src/components/FreshnessIndicator.jsx` | component | transform (presentation) | RESEARCH.md "Relative time formatting" example (`relativeTime.js`) | research-example |
| `frontend/src/components/SearchBar.jsx` | component | event-driven (keystroke) | RESEARCH.md Pattern 2 (search text state var) | research-example |
| `frontend/src/components/FilterChips.jsx` | component | event-driven (click) | RESEARCH.md Pattern 2 (`productType`/`setName` state vars) | research-example |
| `frontend/src/utils/relativeTime.js` | utility | transform | RESEARCH.md "Relative time formatting" example (full implementation given) | research-example (near-complete, minimal adaptation needed) |
| `frontend/src/setupTests.js` | config | — | Standard Vitest + Testing Library setup convention (no project analog) | none — follow RESEARCH.md Wave 0 Gaps checklist |
| `frontend/src/**/*.test.jsx` | test | request-response / event-driven | `tests/test_api_products.py` (Python; same *spirit* of "test the contract boundary," not copyable syntax) | spirit-only, cross-language |

## Pattern Assignments

### `frontend/src/api/client.js` (service, request-response)

**Analog:** RESEARCH.md "Native fetch wrapper" code example, verified against `api/blueprints/products.py` routes.

**Core pattern** (RESEARCH.md lines 368-391):
```javascript
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

**Exact error shapes to match** (from `api/blueprints/products.py` lines 49-52, 65-66 — read directly this session):
- `GET /products` with an invalid `?product_type` → `400 {"error": "invalid_product_type"}`
- `GET /products/<id>` for an unknown id → `404 {"error": "not_found"}`
- The `request()` helper's `body.error || ...` fallback already threads these strings into the thrown `Error.message` — route-level `errorElement` (Pattern 1) should branch on this message, not invent new copy.

**Constraint:** Only call `/products` and `/products/<id>` — Flask-CORS is scoped to `r"/products*"` only (per CONTEXT.md CR-02); no other path prefix will work.

---

### `frontend/src/router.jsx` + `frontend/src/main.jsx` (route / provider, request-response)

**Analog:** RESEARCH.md Pattern 1 (React Router 7 Data Mode).

**Core pattern** (RESEARCH.md lines 229-258):
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
    loader: () => getProducts(),
  },
  {
    path: "/products/:productId",
    Component: ProductDetailPage,
    loader: ({ params }) => getProductDetail(params.productId),
    errorElement: <ProductNotFound />,
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

**Import convention (critical, version-drift-sensitive):** import from the unified `react-router` package — **not** `react-router-dom`, which is legacy on the v7 line and removed entirely in v8. Install exactly `react-router@7.18.1` per RESEARCH.md Standard Stack.

**Anti-pattern to avoid** (RESEARCH.md line 315): do not build `useEffect` + `useState` fetch-on-mount for either route — loaders replace this entirely.

---

### `frontend/src/pages/CatalogPage.jsx` (component, CRUD-read/transform)

**Analog:** RESEARCH.md Pattern 2.

**Core pattern** (RESEARCH.md lines 266-289):
```jsx
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

**Contract fields used for filtering** — must match `_product_summary()` exactly (`api/services/catalog_service.py` lines 58-67): `display_name`, `set_name`, `product_type`. `product_type` values are constrained to `VALID_PRODUCT_TYPES = {"booster_pack", "booster_box", "etb", "booster_bundle"}` (line 36) — `FilterChips.jsx` must offer exactly these four values, no others (D-13, plus Phase 2 D-06 requiring `booster_bundle` stay visually distinct from `booster_box`).

**Anti-pattern to avoid** (RESEARCH.md line 314): never re-fetch `/products` per keystroke — filter the already-loaded array (D-14).

---

### `frontend/src/pages/ProductDetailPage.jsx` (component, request-response)

**Analog:** RESEARCH.md Pattern 1 loader wiring, combined with the exact detail-response contract.

**Exact response shape to render** — from `catalog_service._product_summary()` (base fields, lines 58-67, 72-80) plus `get_product_detail()`'s added trend fields (lines 173-174, 181 — read directly this session):
```
{
  id, set_name, product_type, display_name, release_date, msrp,
  image_url, verified,
  price_status: "ok" | "no_data_yet",
  current_price: { total_price, item_price, as_of, listing_count } | null,
  trend_7d: { pct_change, status },
  trend_30d: { pct_change, status },
}
```

**Critical null-guard pattern** (RESEARCH.md Pitfall 5, verified against `_product_summary()` lines 69-80): branch on `price_status` **before** touching any field inside `current_price` — `current_price` is `null` whenever `price_status === "no_data_yet"`, but `trend_7d`/`trend_30d` are *always* populated objects (never `undefined`) and can be accessed unconditionally.

```jsx
if (product.price_status === "ok") {
  // safe to read product.current_price.total_price, .item_price, .as_of, .listing_count
} else {
  // "no_data_yet" — render muted/graceful state, do not touch current_price fields
}
```

**Also nullable and must be guarded** (RESEARCH.md Pitfall 3, verified against `db/init_collections.py` `$jsonSchema`): `release_date` and `msrp` can be `null` (e.g. pre-release Pitch Black) — never call `.split()`/format methods on these without a null check; fall back to "TBD"/"—".

---

### `frontend/src/components/TrendBadge.jsx` (component, transform/presentation)

**Analog:** RESEARCH.md Pattern 3.

**Core pattern** (RESEARCH.md lines 297-310):
```jsx
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
Directly satisfies D-06 (green up / red down) and D-07 (muted dash for `insufficient_data`, never omitted). The `trend-badge--flat` branch (exact-zero `pct_change` with `status: "ok"`) is flagged as an open question in RESEARCH.md — planner/UI-SPEC should confirm the neutral-gray treatment before finalizing CSS, but the JS branch structure above is already correct.

---

### `frontend/src/components/FreshnessIndicator.jsx` + `frontend/src/utils/relativeTime.js` (utility/component, transform)

**Analog:** RESEARCH.md "Relative time formatting" example — near-complete, minimal adaptation needed.

**Core pattern** (RESEARCH.md lines 419-436):
```javascript
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
Consumes `current_price.as_of`, which is an ISO-8601 string (`current_point["ts"].isoformat()`, `catalog_service.py` line 75) — pass it directly, no reparsing needed. Per D-09/D-10, only render on the product detail page, not in browse rows.

---

### `frontend/src/components/ProductRow.jsx` (component, transform/presentation)

**No RESEARCH.md code example exists for this component** (it's new UI, not previously sketched) — build it directly against the contract and locked decisions:
- Fields consumed: `image_url` (nullable — Pitfall 2: ~11/16 catalog products have `image_url: null`, must have a placeholder/fallback state designed in from the start, not as an edge case), `display_name`, `set_name` (small badge, D-02), `product_type`, `price_status`, `current_price`, `trend_7d`, `trend_30d`.
- D-11: when `price_status === "no_data_yet"`, the whole row renders visually muted/grayed but stays in normal list position — do not filter it out.
- D-08: `listing_count` is intentionally **not** rendered here (detail-page only).
- Composition: `ProductRow` should compose `PriceDisplay` and `TrendBadge` rather than duplicating their formatting logic.

---

### `frontend/src/components/PriceDisplay.jsx` (component, transform/presentation)

**Analog:** the `current_price` shape itself (`_product_summary()`, `api/services/catalog_service.py` lines 72-77) — no RESEARCH.md UI sketch exists, but the field contract is exact.

```
current_price: { total_price, item_price, as_of, listing_count }
```
Per D-05: `total_price` renders as the headline number; `item_price` renders as an always-visible smaller secondary line (never behind hover/tap). `listing_count` may be `undefined` on older documents (RESEARCH.md canonical_refs note on `price_service.py`) — guard with `?? null` style rendering, don't assume presence even when `price_status === "ok"`.

---

## Shared Patterns

### API contract trust boundary (applies to all presentation components)
**Source:** `api/services/catalog_service.py` `_product_summary()` (lines 40-82) and `get_product_detail()` (lines 148-181, trend logic at 173-181).
**Apply to:** `ProductRow`, `PriceDisplay`, `TrendBadge`, `FreshnessIndicator`, `ProductDetailPage`, `CatalogPage`.
**Rule:** Never recompute `pct_change` or `total_price` client-side — the API already computed these authoritatively. Frontend components are pure formatters over already-computed values (RESEARCH.md Pattern 3, and the project's core-value constraint that price accuracy "must always be right").

### Route-level data fetching (no manual loading/error state threading)
**Source:** RESEARCH.md Pattern 1 (`createBrowserRouter` + loaders + `errorElement`).
**Apply to:** `router.jsx`, `CatalogPage.jsx`, `ProductDetailPage.jsx`.
**Rule:** Centralize 404 (`{"error":"not_found"}`) and 400 (`{"error":"invalid_product_type"}`) handling at the route boundary via `errorElement`, not per-component try/catch.

### Client-side, in-memory filtering (D-14)
**Source:** RESEARCH.md Pattern 2.
**Apply to:** `CatalogPage.jsx`, `SearchBar.jsx`, `FilterChips.jsx`.
**Rule:** Fetch the full catalog once via the loader; all search-text/chip filtering happens against the already-loaded array with `useMemo`, never a per-keystroke network call.

### Null-safety on nullable API fields
**Source:** RESEARCH.md Pitfalls 2, 3, 5 (each independently verified against this repo's own code/schema).
**Apply to:** `ProductRow.jsx` (`image_url`), `ProductDetailPage.jsx`/`PriceDisplay.jsx` (`release_date`, `msrp`, `current_price` when `price_status === "no_data_yet"`).
**Rule:** Guard every nullable field with an explicit fallback ("TBD", "—", placeholder icon) — never assume presence, never let a null field throw at render time. This mirrors the "flag, never hide, never crash" philosophy already established in Phases 4-5.

### No top-level side effects on import (cross-language discipline)
**Source:** `api/blueprints/products.py` (lines 16-19, explicit repo convention) — Python precedent, applied as a design principle rather than copyable syntax.
**Apply to:** All new files — no fetch calls, no `MongoClient`-equivalent construction, no route registration outside `createBrowserRouter`'s declarative table at module scope. Effects only inside loaders/hooks/component bodies at render/interaction time.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `frontend/src/components/ProductRow.jsx` | component | transform | No prior UI sketch in RESEARCH.md or the codebase — build directly from the contract fields and D-01/D-02/D-04/D-08/D-11 listed above; no code excerpt to copy, only field/behavior constraints. |
| `frontend/src/components/SearchBar.jsx` | component | event-driven | RESEARCH.md only shows the resulting state variable (`query`, `setQuery`) inside `CatalogPage`, not a standalone input component — planner has discretion on exact JSX structure (a controlled `<input>` bound to `setQuery`). |
| `frontend/src/components/FilterChips.jsx` | component | event-driven | Same as above — only the consuming state variables (`productType`, `setName`) are shown in Pattern 2; the chip/tab JSX itself is undesigned. Discretion note in CONTEXT.md explicitly leaves the `set_name` chip as optional/Claude's discretion. |
| `frontend/vite.config.js` test block, `frontend/src/setupTests.js` | config | — | No project precedent for a JS test setup; follow RESEARCH.md's Wave 0 Gaps checklist verbatim (jsdom environment, `@testing-library/jest-dom` import) rather than an in-repo analog. |

## Metadata

**Analog search scope:** Entire repo root (`find` to depth 2, confirmed no `frontend/` directory exists); `api/blueprints/`, `api/services/` read directly for exact contract shapes; RESEARCH.md's Code Examples section used as the primary pattern source given the greenfield nature of this phase.
**Files scanned:** `api/blueprints/products.py` (68 lines, read in full), `api/services/catalog_service.py` (lines 1-130 read, contract-defining sections extracted), repo directory tree (`find -maxdepth 2`).
**Pattern extraction date:** 2026-07-15
