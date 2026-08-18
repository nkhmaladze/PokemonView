# Phase 8: Price History Chart - Context

**Gathered:** 2026-08-18
**Status:** Ready for planning

<domain>
## Phase Boundary

A user opening a product's detail page can see a line chart of that product's total-price history over time, plotted from every collected `price_points` document (the raw series, no downsampling), served by a new dedicated endpoint. Detail page only — no catalog-page sparklines, no item/total price toggle, no time-range selector. Both deferred to v2 (see REQUIREMENTS.md PRICE-10/PRICE-11).

</domain>

<decisions>
## Implementation Decisions

### Chart visual style
- **D-01:** Full chart with visible X-axis (dates), Y-axis ($ price), and light gridlines — not a minimal sparkline. Visual reference is poe.ninja (PROJECT.md's direct inspiration), specifically for this chart.
- **D-02:** Always show the full history — no 7d/30d/All range selector for this milestone. Matches REQUIREMENTS.md's existing "raw series, no downsampling" decision. Deferred to v2 as PRICE-10-adjacent scope if data volume grows enough to need it.
- **D-03:** Chart gets its own visible section heading (e.g. "Price History"), placed after the existing trend-badges section on the detail page — matches the page's existing sectioned layout (header / price / trends / meta).

### Loading behavior & API shape
- **D-04:** Price history is served by a **new, separate endpoint** (`GET /products/<id>/history` or equivalent) — NOT bundled as a new field on the existing `GET /products/<id>` response. — **Reversibility:** costly — **rationale:** this is a new public API contract; once the frontend and any external consumer depend on it as a separate resource, folding it back into the detail response later means either a breaking change or maintaining both shapes.
- **D-05:** The page renders immediately from the existing detail loader (price, badges, meta) and the chart loads progressively via a **second, independent fetch** that resolves after initial render — true network-level progressive loading, not just staged rendering of a single bundled response. The user explicitly reconciled an initial contradiction (picked "new field on existing response" for the endpoint question, then "separate fetch" for loading) toward this combination when the conflict was surfaced.
- **D-06 (consequence of D-04, not separately asked):** Because history lives on a new endpoint rather than extending `get_product_detail`, the existing D-11 decision in `api/services/catalog_service.py` ("never returns a raw price_points series") stays **true and unmodified**. Do not edit that docstring/contract — the new history capability lives entirely in a new function/route, sitting alongside `get_product_detail`, not inside it.

### Insufficient-history state
- **D-07:** Minimum 2 price points required to draw a real line; 0 or 1 point shows the insufficient-history message instead of a chart.
- **D-08:** Insufficient-history message text: **"Not enough price history yet"** — plain, matches the roadmap's own wording (Phase 8 success criteria #3), no specific count or date mentioned.

### Claude's Discretion
- Exact new endpoint path/naming (e.g. `/products/<id>/history` vs `/products/<id>/price_history`) — not discussed, follow existing route-naming conventions in `api/blueprints/products.py`.
- Exact new service function name and module placement (e.g. `price_service.get_price_history` vs a new module) — follow the existing "pure function taking db as arg" convention from `price_service.py`.
- Response JSON field names for the history endpoint (e.g. `ts`/`total_price` vs renamed) — follow the existing `price_points` document shape unless there's a clear reason to reshape.
- Recharts component structure/props — no specific API discussed; use Recharts' standard `LineChart`/`XAxis`/`YAxis`/`Tooltip`/`CartesianGrid` composition to match the "full chart" decision (D-01).
- Frontend loading-state UI (skeleton vs spinner vs blank-then-fill) for the progressive chart fetch (D-05) — not discussed, pick something consistent with the existing `FreshnessIndicator`/loading conventions if any exist, otherwise a simple lightweight placeholder.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone scope
- `.planning/PROJECT.md` §"Current Milestone: v1.1 Price History & Extended Badges" — milestone goal and target features
- `.planning/REQUIREMENTS.md` — PRICE-07 (this phase), PRICE-10/PRICE-11 (deferred v2 scope: catalog sparklines, item/total toggle)
- `.planning/ROADMAP.md` §"Phase 8: Price History Chart" — locked success criteria (raw series no downsampling, tooltip readability, insufficient-history state, endpoint returns raw series directly)

### Existing code this phase extends
- `api/services/catalog_service.py` — `get_product_detail`'s documented D-11 decision ("never returns a raw price_points series") stays unmodified per D-06 above; do not edit its docstring to imply it now returns history
- `api/services/price_service.py` — existing pure-function convention (`get_current_price`, `get_trend_baseline`, `TREND_TOLERANCE_DAYS = 3`) to follow for a new price-history function
- `api/blueprints/products.py` — thin-route convention (parse args, delegate to one service call, jsonify with no transformation) to follow for the new route
- `frontend/src/api/client.js` — existing `request()` helper and `getProducts`/`getProductDetail` pattern to extend with a new client function
- `frontend/src/router.jsx` — current one-loader-per-route pattern; D-05's progressive fetch means the chart's fetch happens outside/after this loader, not inside it
- `frontend/src/pages/ProductDetailPage.jsx` — page layout to extend with the new chart section (D-03)
- `frontend/src/components/TrendBadge.jsx` / `PriceDisplay.jsx` — established component conventions (CSS modules, pure formatters over API-computed values, explicit status branching) to mirror in the new chart component

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/components/TrendBadge.jsx`: 4-state pattern (ok/insufficient_data branching, CSS module styling) — the insufficient-history chart state (D-07/D-08) should follow the same "branch on status first" convention.
- `frontend/src/api/client.js`'s `request()` helper: already handles base URL + error unwrapping; the new history fetch function should reuse it, not duplicate fetch logic.

### Established Patterns
- Backend: pure service functions take `db` as an argument, no top-level side effects on import, blueprint routes are thin pass-throughs that only translate specific known errors (never a bare `except Exception`).
- Backend: explicit `{value, status}` shaped fields for "might not have data" cases (see `trend_7d`/`trend_30d`) rather than omitting fields or returning bare `None` — the new history endpoint should decide its own explicit shape for the insufficient-history case (e.g., an explicit empty-array vs a status field) during planning.
- Frontend: route loaders throw on non-2xx (`client.js`'s `request()`), caught by route-level `errorElement` — but D-05's separate fetch happens outside the loader, so its own error handling isn't covered by the existing `ProductNotFound` errorElement and needs its own path (component-level try/catch or similar).
- No dependency-installation or package-legitimacy precedent exists yet for Recharts specifically — pymongo/apscheduler/rapidfuzz/flask/gunicorn all went through a human-approved supply-chain checkpoint before installation; Recharts should follow the same pattern as this project's first-ever frontend runtime dependency beyond React itself.

### Integration Points
- New price-history service function (backend), new route in `api/blueprints/products.py` (or a new blueprint), new client function in `frontend/src/api/client.js`, new chart component composed into `ProductDetailPage.jsx`, Recharts added to `frontend/package.json`.

</code_context>

<specifics>
## Specific Ideas

- Visual reference is explicitly **poe.ninja** (PROJECT.md's own stated direct inspiration) — full axes/gridlines chart, not a minimal sparkline, for this detail-page chart specifically.
- The user caught and corrected a self-contradiction during discussion (bundled-response answer vs. separate-fetch answer) when it was surfaced — final intent is genuine network-level progressive loading via a dedicated history endpoint, not just staged UI rendering of one payload.

</specifics>

<deferred>
## Deferred Ideas

- Time-range selector (7d/30d/All) on the chart — deferred, always show full history for now (D-02); revisit once there's enough accumulated data to make a selector meaningful.
- Catalog-page sparklines — already tracked as REQUIREMENTS.md PRICE-10 (v2), explicitly out of scope for this phase.
- Item-price/total-price toggle on the chart — already tracked as REQUIREMENTS.md PRICE-11 (v2), explicitly out of scope for this phase.

### Reviewed Todos (not folded)
None — no pending todos existed at milestone start.

</deferred>

---

*Phase: 8-Price History Chart*
*Context gathered: 2026-08-18*
