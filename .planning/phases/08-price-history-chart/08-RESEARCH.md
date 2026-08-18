# Phase 8: Price History Chart - Research

**Researched:** 2026-08-18
**Domain:** MongoDB time-series querying (PyMongo) + Recharts `LineChart` composition + Flask JSON serialization + React Router v7 progressive fetch
**Confidence:** HIGH

## Summary

This phase is a straightforward vertical slice with one real technical trap: **Flask's default JSON provider does not serialize raw MongoDB documents safely.** `price_points` documents carry a `datetime` `ts` field and an auto-generated `ObjectId` `_id` (unlike `products`, `price_points` has no explicit `_id`). Flask 3.1.3's `DefaultJSONProvider` serializes `datetime` via `werkzeug.http.http_date` (RFC 822 format, e.g. `"Tue, 15 Nov 1994 08:12:31 GMT"`) — not ISO 8601, and **not what every other endpoint in this codebase already returns** (`catalog_service.py` manually calls `.isoformat()` everywhere). `ObjectId` has no `default()` handler at all and raises `TypeError: Object of type ObjectId is not JSON serializable` if it reaches `jsonify()`. The new history service function must build clean dicts — `{"ts": doc["ts"].isoformat(), "total_price": doc["total_price"]}` — exactly like `_product_summary` already does for `current_price`, never `jsonify(list(db.price_points.find(...)))` directly.

On the MongoDB side, querying `price_points` for one product's full history is a plain `find({"product_id": pid}).sort("ts", 1)` — time-series collections need no special query API. MongoDB 6.3+ auto-creates a compound `{metaField: 1, timeField: 1}` secondary index, so an equality match on `product_id` (the metaField) plus a sort on `ts` (the timeField) is index-covered without any manual index work.

On the frontend, Recharts' `LineChart` composition (`CartesianGrid` + `XAxis` + `YAxis` + `Tooltip` + `Line`) is the same declarative pattern already implied by the project's stack research — the only design decision is how to format the date-typed X axis and tooltip label, which this project should do with the native `Intl.DateTimeFormat` API (matching the codebase's existing no-date-library convention in `relativeTime.js`), not a new library.

Recharts itself passed the package-legitimacy check as `[SUS]`/`too-new` (its latest patch was published 3 weeks ago on an otherwise 49.8M-weekly-download, actively maintained package) — this is the exact same false-positive class already documented and human-approved for `apscheduler`/`pymongo`/`rapidfuzz` in this project (STATE.md), so the planner should insert the same `checkpoint:human-verify` gate, not treat it as a blocker.

**Primary recommendation:** New `GET /products/<id>/history` route → new `price_service.get_price_history(db, product_id)` pure function that queries with `.find({"product_id": product_id}, sort=[("ts", 1)])` and returns a list of clean `{"ts": iso_string, "total_price": float}` dicts (excluding `_id`, `item_price`, `listing_count` unless a reason emerges to keep them) → thin blueprint route that `jsonify()`s the list with no transformation, mirroring the existing `products.py` convention exactly. Frontend: new `getPriceHistory(productId)` in `client.js` reusing `request()`, called from a `useEffect` in `ProductDetailPage.jsx` (not the loader), rendering a `PriceHistoryChart` component that branches on `data.length < 2` before ever touching Recharts.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Query `price_points` time-series for one product, time-ordered | API / Backend (`price_service.py`) | Database (native time-series index) | Pure DB-query logic; mirrors `get_current_price`/`get_trend_baseline`'s existing "pure function over `db`" convention |
| Expose history as a new JSON resource | API / Backend (`api/blueprints/products.py`) | — | New route, thin pass-through, matches `product_detail`'s existing shape (parse → delegate → jsonify) |
| Insufficient-history detection (< 2 points) | API / Backend (returns raw array; length is the signal) OR Frontend (reads `data.length`) | Frontend (rendering decision) | D-07 requires a **rendering** decision ("show message instead of chart"), not a data-shape decision — the raw array already carries this signal via its length; no extra backend status field needed (see Pattern 2 below) |
| Line chart rendering (axes, gridlines, tooltip) | Browser / Client (`PriceHistoryChart.jsx` + Recharts) | — | Pure presentation over an already-fetched array; never recomputes prices |
| Progressive/secondary fetch orchestration | Browser / Client (`ProductDetailPage.jsx` via `useEffect`) | — | D-05 requires this fetch to happen *after* the loader-driven initial render, which is exclusively a client-side concern; React Router's loader model has no "fetch after render" primitive, so this cannot live in `router.jsx` |

## User Constraints

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Full chart with visible X-axis (dates), Y-axis ($ price), and light gridlines — not a minimal sparkline. Visual reference is poe.ninja (PROJECT.md's direct inspiration), specifically for this chart.
- **D-02:** Always show the full history — no 7d/30d/All range selector for this milestone. Matches REQUIREMENTS.md's existing "raw series, no downsampling" decision. Deferred to v2 as PRICE-10-adjacent scope if data volume grows enough to need it.
- **D-03:** Chart gets its own visible section heading (e.g. "Price History"), placed after the existing trend-badges section on the detail page — matches the page's existing sectioned layout (header / price / trends / meta).
- **D-04:** Price history is served by a **new, separate endpoint** (`GET /products/<id>/history` or equivalent) — NOT bundled as a new field on the existing `GET /products/<id>` response. Reversibility: costly. Rationale: this is a new public API contract; once the frontend and any external consumer depend on it as a separate resource, folding it back into the detail response later means either a breaking change or maintaining both shapes.
- **D-05:** The page renders immediately from the existing detail loader (price, badges, meta) and the chart loads progressively via a **second, independent fetch** that resolves after initial render — true network-level progressive loading, not just staged rendering of a single bundled response.
- **D-06 (consequence of D-04):** Because history lives on a new endpoint rather than extending `get_product_detail`, the existing D-11 decision in `api/services/catalog_service.py` ("never returns a raw price_points series") stays true and unmodified. Do not edit that docstring/contract.
- **D-07:** Minimum 2 price points required to draw a real line; 0 or 1 point shows the insufficient-history message instead of a chart.
- **D-08:** Insufficient-history message text: **"Not enough price history yet"** — plain, no specific count or date mentioned.

### Claude's Discretion
- Exact new endpoint path/naming (e.g. `/products/<id>/history` vs `/products/<id>/price_history`) — not discussed, follow existing route-naming conventions in `api/blueprints/products.py`.
- Exact new service function name and module placement (e.g. `price_service.get_price_history` vs a new module) — follow the existing "pure function taking db as arg" convention from `price_service.py`.
- Response JSON field names for the history endpoint (e.g. `ts`/`total_price` vs renamed) — follow the existing `price_points` document shape unless there's a clear reason to reshape.
- Recharts component structure/props — no specific API discussed; use Recharts' standard `LineChart`/`XAxis`/`YAxis`/`Tooltip`/`CartesianGrid` composition to match the "full chart" decision (D-01).
- Frontend loading-state UI (skeleton vs spinner vs blank-then-fill) for the progressive chart fetch (D-05) — not discussed, pick something consistent with the existing `FreshnessIndicator`/loading conventions if any exist, otherwise a simple lightweight placeholder.

### Deferred Ideas (OUT OF SCOPE)
- Time-range selector (7d/30d/All) on the chart — deferred, always show full history for now (D-02); revisit once there's enough accumulated data to make a selector meaningful.
- Catalog-page sparklines — already tracked as REQUIREMENTS.md PRICE-10 (v2), explicitly out of scope for this phase.
- Item-price/total-price toggle on the chart — already tracked as REQUIREMENTS.md PRICE-11 (v2), explicitly out of scope for this phase.
</user_constraints>

## Phase Requirements

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PRICE-07 | User can view a line chart of a product's total-price history on its detail page, rendered from the existing price_points time-series data | Pattern 1 (backend query), Pattern 3 (Recharts composition), Pattern 4 (progressive fetch) below cover the full vertical slice; Pitfall 1 (JSON serialization) and Pitfall 2 (insufficient-data shape) cover the two correctness traps |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Recharts | 3.10.1 (confirmed via `npm view recharts version`, published 2026-07-25) `[ASSUMED — package name from project stack docs, registry existence confirmed this session but NOT yet a `[VERIFIED]` source per provenance rules]` | Chart rendering for the price-history line chart | Already the project's designated charting library (CLAUDE.md Recommended Stack); composable React components, standard for this exact "declarative line chart with tooltip" use case |
| PyMongo | 4.17.0 (already installed — `requirements.txt`) `[VERIFIED: requirements.txt]` | Query `price_points` time-series collection | Already the project's driver; no new query API needed for time-series collections — `find()`/`sort()` work exactly as on a normal collection |

### Supporting
No new supporting libraries needed. Date formatting for the chart's X-axis ticks and tooltip label should use the native `Intl.DateTimeFormat` API — matching the project's existing no-date-library convention already established in `frontend/src/utils/relativeTime.js` (`Intl.RelativeTimeFormat`, explicit "no date-fns/dayjs/moment" comment in that file). Do not add a date library for this phase.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Recharts | visx / Chart.js | Already rejected in CLAUDE.md's "Alternatives Considered" table for this project — visx costs 2-3x more dev time per chart for no gain here; Chart.js's Canvas rendering only matters at thousands-of-points scale, and this phase's data volume (raw series, ~6 points/day per product, REQUIREMENTS.md's own "small volume" framing) never approaches that |

**Installation:**
```bash
cd frontend
npm install recharts@3.10.1
```

**Version verification:** `npm view recharts version` → `3.10.1`, published `2026-07-25T15:23:05Z` `[VERIFIED: npm registry — command run this session]`. Weekly downloads: 49,855,575 `[VERIFIED: npm registry — command run this session]`.

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| `recharts` | npm | Latest version (3.10.1) published 2026-07-25 (~3.5 weeks before this research) on an otherwise long-established package | 49,855,575/week | `github.com/recharts/recharts` (confirmed via `npm view recharts repository.url`, canonical org repo) | `[SUS]` (reason: `too-new`) | Keep — see note |

**Note on the `[SUS]` verdict:** This is the exact same false-positive class already documented and human-approved for `apscheduler` (03-RESEARCH.md), `pymongo` (02-RESEARCH.md), and `rapidfuzz` (04-RESEARCH.md) in this project's history — a recent *patch release* on a mature, massively-downloaded package trips the legitimacy tool's "too-new" heuristic even though the package itself (and its GitHub org) has been actively maintained for years. No `postinstall` script exists (`npm view recharts scripts.postinstall` → empty), so there is no arbitrary install-time code execution surface. Per protocol, **the planner must still insert a `checkpoint:human-verify` task before `npm install recharts`**, even though the actual risk is assessed as negligible — this will be this project's **first frontend runtime dependency beyond React itself**, so the checkpoint has no direct frontend precedent to point back to (only the backend pymongo/apscheduler/rapidfuzz approvals), and the plan/SUMMARY should record this as the first frontend-ecosystem approval.

**Packages removed due to `[SLOP]` verdict:** none
**Packages flagged as suspicious `[SUS]`:** `recharts` — planner must insert `checkpoint:human-verify` before this install
**Postinstall script check:** `npm view recharts scripts.postinstall` → empty (no postinstall hook).

## Architecture Patterns

### System Architecture Diagram

```
Browser: ProductDetailPage mounts
   |
   |-- useLoaderData() --> existing detail object (price, badges, meta)
   |                       renders IMMEDIATELY (D-05), unchanged from today
   |
   `-- useEffect(() => { ... }, [productId])  <-- NEW, runs AFTER initial render
           |
           |  getPriceHistory(productId)  (frontend/src/api/client.js, NEW)
           v
       GET /products/<id>/history   (api/blueprints/products.py, NEW route)
           |
           |  catalog_service.InvalidProductTypeError-style thin delegation
           v
       price_service.get_price_history(db, product_id)   (NEW pure function)
           |
           |  db.price_points.find({"product_id": pid}, sort=[("ts", 1)])
           |  (compound {product_id:1, ts:1} index, MongoDB auto-created)
           v
       [{ts: datetime, product_id, item_price, total_price}, ...]   (raw docs)
           |
           |  build clean dicts: {"ts": doc["ts"].isoformat(), "total_price": ...}
           |  (NEVER jsonify a raw doc — Pitfall 1)
           v
       JSON array, time-ordered ascending  -->  jsonify(), 200
           |
           v
   Browser: setHistory(data) triggers re-render
           |
           |-- data.length < 2 --> render "Not enough price history yet" (D-07/D-08)
           |
           `-- data.length >= 2 --> <PriceHistoryChart data={data} />
                                       Recharts LineChart + XAxis + YAxis
                                       + CartesianGrid + Tooltip (D-01)
```

### Recommended Project Structure
```
api/
├── services/
│   └── price_service.py       # ADD get_price_history(db, product_id)
├── blueprints/
│   └── products.py            # ADD GET /products/<id>/history route

frontend/
├── src/
│   ├── api/
│   │   └── client.js          # ADD getPriceHistory(productId)
│   ├── components/
│   │   ├── PriceHistoryChart.jsx        # NEW — Recharts composition + insufficient-data branch
│   │   └── PriceHistoryChart.module.css # NEW — section heading, chart container sizing
│   └── pages/
│       └── ProductDetailPage.jsx  # ADD useEffect-driven fetch + <PriceHistoryChart /> section
```

### Pattern 1: Query `price_points` for one product's full raw series, time-ordered

**What:** A plain `find()` + `sort()` — time-series collections need no special PyMongo API for reads.
**When to use:** Any query scoped to one metaField value (`product_id`), ordered by `timeField` (`ts`).
**Example:**
```python
# Pattern derived from existing price_service.py conventions
# (get_current_price's find_one/sort=[("ts", -1)] precedent) and
# MongoDB official docs on time-series query/index behavior
# [CITED: mongodb.com/docs/manual/core/timeseries/timeseries-index/,
#  mongodb.com/docs/manual/core/timeseries/timeseries-best-practices/]

def get_price_history(db, product_id):
    """Return every price_points document for product_id, ascending by
    ts (oldest first) — the raw, undownsampled series (PRICE-07, D-04).

    Unlike get_current_price/get_trend_baseline, this returns a LIST,
    not a single document or None. An empty list means zero points; a
    single-element list means one point — the caller (blueprint route)
    returns both cases as-is; the frontend's D-07 "min 2 points" rule
    is a rendering decision, not a query-shape decision (see
    Pitfall 2).

    Args:
        db: An already-connected pymongo Database handle.
        product_id: The canonical catalog product slug.

    Returns:
        list[dict]: [{"ts": iso_string, "total_price": float}, ...],
        oldest first. Never includes _id, item_price, or
        listing_count unless a later requirement needs them.
    """
    docs = db.price_points.find(
        {"product_id": product_id},
        sort=[("ts", 1)],
    )
    return [
        {"ts": doc["ts"].isoformat(), "total_price": doc["total_price"]}
        for doc in docs
    ]
```
**Index note:** MongoDB 6.3+ auto-creates a compound `{product_id: 1, ts: 1}` secondary index on every time-series collection `[CITED: mongodb.com/docs/manual/core/timeseries/timeseries-index/]`. An equality match on `product_id` (the metaField) combined with an ascending sort on `ts` (the timeField) is served directly by this index — no manual `create_index` call is needed for this phase. Confirmed against this project's actual `price_points` creation options: `[VERIFIED: db/init_collections.py:83-87]` — `PRICE_POINTS_TIMESERIES_OPTIONS = {"timeField": "ts", "metaField": "product_id", "granularity": "hours"}`.

### Pattern 2: Insufficient-history is a rendering decision, not an API-shape decision

**What:** D-07 requires "0 or 1 point shows the insufficient-history message." The simplest correct design: `get_price_history` always returns the raw array (possibly length 0 or 1); the *frontend* checks `data.length < 2` before rendering the chart.
**When to use:** This phase, given Success Criterion #4's explicit wording — "returns that product's raw price_points series as time-ordered JSON... never recomputes or synthesizes the series client-side." A wrapped `{status, points}` shape (mirroring `trend_7d`'s `{pct_change, status}` convention) is a defensible alternative, but adds a status field the frontend doesn't strictly need (array length already encodes the same signal) and the roadmap's own wording favors "raw series" over a wrapped shape.
**Example (frontend branch):**
```jsx
// frontend/src/components/PriceHistoryChart.jsx
export default function PriceHistoryChart({ data }) {
  if (!data || data.length < 2) {
    return <p className={styles.insufficient}>Not enough price history yet</p>
  }
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data}>
        {/* ... see Pattern 3 */}
      </LineChart>
    </ResponsiveContainer>
  )
}
```
**Anti-pattern to avoid:** Do not have the *backend* decide "insufficient" and omit the array or return `null` — this contradicts Success Criterion #4 ("the chart reads a real API response") and D-07's phrasing, which frames the threshold as a rendering rule ("shows... a message instead of a chart"), i.e. a frontend concern over the same raw data.

### Pattern 3: Recharts `LineChart` composition for a full poe.ninja-style chart

**What:** `ResponsiveContainer` > `LineChart` > `CartesianGrid` + `XAxis` + `YAxis` + `Tooltip` + `Line`, the standard Recharts composition pattern.
**When to use:** D-01's "full chart with visible axes/gridlines, not a sparkline."
**Example:**
```jsx
// Source: Context7 /recharts/recharts — README.md "Basic LineChart
// Component" + GettingStarted.mdx "Add Tooltip interaction" +
// Accessibility.mdx ResponsiveContainer pattern
// [VERIFIED: frontend/src/styles/tokens.css:9-25 for the exact hex
// values quoted below — --color-accent: #E8A33D;
// --color-divider: #232833; --text-secondary: #9AA3B2]
import {
  LineChart, Line, CartesianGrid, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from 'recharts'

function formatTick(isoString) {
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' })
    .format(new Date(isoString))
}

function formatTooltipLabel(isoString) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
  }).format(new Date(isoString))
}

function formatTooltipValue(value) {
  return [`$${value.toFixed(2)}`, 'Total price']
}

<ResponsiveContainer width="100%" height={280}>
  <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
    <CartesianGrid stroke="var(--color-divider)" strokeDasharray="3 3" />
    <XAxis
      dataKey="ts"
      tickFormatter={formatTick}
      stroke="var(--text-secondary)"
    />
    <YAxis
      tickFormatter={(v) => `$${v}`}
      stroke="var(--text-secondary)"
    />
    <Tooltip
      labelFormatter={formatTooltipLabel}
      formatter={formatTooltipValue}
      contentStyle={{ background: 'var(--color-surface)', border: 'none' }}
    />
    <Line
      type="monotone"
      dataKey="total_price"
      stroke="var(--color-accent)"
      dot={false}
      activeDot={{ r: 4 }}
    />
  </LineChart>
</ResponsiveContainer>
```
**Data shape note:** Recharts' `data` prop is a plain array of objects; each `dataKey` string (`"ts"`, `"total_price"`) is a lookup key into every array element `[VERIFIED: Context7 /recharts/recharts — GettingStarted.mdx "Define chart data"]`. This lines up exactly with Pattern 1's output shape — no client-side reshaping needed.
**X-axis date handling note:** Recharts supports a true numeric time scale (`XAxis scale="time" type="number" domain={[minMs, maxMs]}`) for evenly-spaced time axes `[CITED: Context7 /recharts/recharts — test/cartesian/XAxis/XAxis.timescale.spec.tsx]`, but the simpler category-axis-with-`tickFormatter` pattern shown above (treating the ISO string as the category value and only reformatting the displayed tick label) is what Recharts' own README/GettingStarted examples use as the default composition, and is sufficient here since D-02 already rules out any zoom/range-selection interaction that would benefit from a true numeric time scale.
**CSS custom properties in SVG props:** `stroke`/`fill` accept `"var(--token)"` strings directly — modern browsers resolve CSS custom properties in SVG presentation attributes exactly as in regular CSS, so no hardcoded hex duplication is needed; this keeps the chart's palette in sync with `tokens.css` automatically.

### Pattern 4: Progressive fetch outside the React Router v7 loader

**What:** D-05 requires the chart data to arrive via a second, independent fetch *after* the loader-driven initial render — the loader model (`router.jsx`) has no "fetch after render" primitive, so this must be a component-level `useEffect`.
**When to use:** This phase, per D-05.
**Example:**
```jsx
// frontend/src/pages/ProductDetailPage.jsx — ADD inside the component
import { useEffect, useState } from 'react'
import { useParams } from 'react-router'
import { getPriceHistory } from '../api/client'

// existing: const product = useLoaderData()
const { productId } = useParams()
const [history, setHistory] = useState(null)       // null = loading
const [historyError, setHistoryError] = useState(null)

useEffect(() => {
  let cancelled = false
  setHistory(null)
  setHistoryError(null)
  getPriceHistory(productId)
    .then((data) => { if (!cancelled) setHistory(data) })
    .catch((err) => { if (!cancelled) setHistoryError(err) })
  return () => { cancelled = true }
}, [productId])
```
**Why not the loader:** `router.jsx`'s existing loader (`loader: ({ params }) => getProductDetail(params.productId)`) blocks the route transition until it resolves — bundling the history fetch into it would defeat D-05's entire purpose (immediate render of price/badges/meta, chart arriving later). A `useEffect` with its own `useState` is the standard React pattern for "fetch after mount, independent of route transition."
**Error handling note:** The existing `errorElement` (`ProductNotFound`) only catches loader/render-time throws — it does NOT catch a rejected promise from a `useEffect`-triggered fetch (`client.js`'s `request()` throws on non-2xx, but nothing re-throws it into the render tree from inside a `.catch()`). This fetch needs its own component-level error state (shown above) and its own inline UI (e.g. "Couldn't load price history"), not a reliance on the route's `errorElement` boundary.
**Race/stale-response guard:** The `cancelled` flag guard above (or an `AbortController`) prevents a slow-resolving fetch for a previous `productId` from overwriting state after the user has already navigated to a different product's detail page — a real risk here since this component can re-mount/re-run with a new `productId` while an in-flight request from the old one is still pending.

### Anti-Patterns to Avoid
- **`jsonify(list(db.price_points.find({"product_id": pid})))` directly:** Crashes on the auto-generated `ObjectId` `_id` field and, even with `_id` excluded via projection, silently serializes `ts` as an RFC-822 string via Flask's default JSON provider instead of ISO 8601 — inconsistent with every other timestamp in this API (see Pitfall 1).
- **Editing `catalog_service.py`'s `get_product_detail` to add a `price_points` field:** Explicitly forbidden by D-06 — the D-11 "never returns raw price_points" contract stays untouched; the new capability lives entirely in a new function/route.
- **Putting the chart fetch inside `router.jsx`'s loader:** Defeats D-05's "progressive loading" requirement — the whole point is that price/badges/meta render before the chart data exists.
- **Adding a date library (date-fns/dayjs/moment) for tick/tooltip formatting:** Contradicts the codebase's existing no-date-library convention (`relativeTime.js`'s explicit comment); the native `Intl.DateTimeFormat` API is sufficient for the simple "Aug 18, 2026"-style formatting this chart needs.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Line chart axes, gridlines, tooltip positioning, responsive resizing | Custom SVG/D3 chart | Recharts `LineChart` composition | Already the project's designated charting library; hand-rolling SVG axis math/tooltip hit-testing/responsive scaling is exactly the kind of "deceptively complex" problem this library exists to solve |
| Date tick formatting | Custom date-parsing/formatting utility | Native `Intl.DateTimeFormat` | Zero-dependency, matches the codebase's existing `relativeTime.js` precedent of using native `Intl` APIs instead of a date library |
| MongoDB time-series bucket-aware querying | Manual bucket-boundary math or raw `aggregate()` pipeline for a simple time-ordered read | Plain `find({"product_id": pid}, sort=[("ts", 1)])` | MongoDB's time-series collections abstract bucketing transparently for `find()`/`sort()` — there is no bucket-level API surface to hand-roll against for a simple ordered read |

**Key insight:** Every piece of this phase (charting, date formatting, time-series querying) already has a purpose-built, already-adopted solution in this stack. The only genuinely new code is the thin glue: one service function, one route, one client function, one component, and one `useEffect`.

## Common Pitfalls

### Pitfall 1: Flask's default JSON provider mangles raw `price_points` documents
**What goes wrong:** Returning raw MongoDB documents (or even a projected subset that still contains a `datetime` field) directly to `jsonify()` either crashes (`ObjectId` has no serializer) or silently produces RFC-822-formatted timestamps instead of ISO 8601, breaking consistency with every other timestamp this API already returns (`current_price.as_of`, etc., all built with `.isoformat()` in `catalog_service.py`).
**Why it happens:** Flask 3.1.3's `DefaultJSONProvider._default()` handles `datetime`/`date` via `werkzeug.http.http_date()` (RFC 822/HTTP-date format) — not ISO 8601 — and has no handler for `bson.ObjectId` at all, so it raises `TypeError: Object of type ObjectId is not JSON serializable` `[VERIFIED: /Users/nkhmal/.pyenv/versions/3.12.13/lib/python3.12/site-packages/flask/json/provider.py:108-121 — "if isinstance(o, date): return http_date(o)" with no ObjectId branch, confirmed against this project's installed flask==3.1.3 site-packages this session]`.
**How to avoid:** `get_price_history` must build clean output dicts itself — `{"ts": doc["ts"].isoformat(), "total_price": doc["total_price"]}` — exactly mirroring `_product_summary`'s existing `"as_of": current_point["ts"].isoformat()` pattern (`api/services/catalog_service.py:75` `[VERIFIED: api/services/catalog_service.py:69-77]`). Never pass a raw pymongo document (or a `find()` cursor's items) straight into `jsonify()`.
**Warning signs:** A 500 error with `TypeError: Object of type ObjectId is not JSON serializable` in local dev, or (worse, silently) a chart that renders garbage/`Invalid Date` on the frontend because `new Date("Tue, 15 Nov 1994 08:12:31 GMT")` parses differently than expected relative to the rest of the app's ISO-string assumptions.

### Pitfall 2: Conflating "0/1 points" with "query error"
**What goes wrong:** Treating an empty or single-element `price_points` result as an error condition (e.g. returning 404 or 500) instead of a normal, expected 200 response.
**Why it happens:** Every product in this catalog *will* pass through a "brand new, zero data points yet" state at some point (mirrors `get_current_price`'s existing "returns None only if zero points ever" pattern for the detail endpoint) — a genuinely valid, common state, not an error.
**How to avoid:** `get_price_history` returns `[]` (or a 1-element list) as a perfectly normal 200 response; the blueprint route never special-cases the length. D-07/D-08's "Not enough price history yet" message is rendered by the *frontend* checking `data.length < 2` (Pattern 2), never surfaced as an HTTP error status.
**Warning signs:** A product detail page throwing/crashing (hitting `ProductNotFound`-style error UI) for a legitimately new product instead of showing the plain insufficient-history message inline.

### Pitfall 3: Assuming `price_points` documents carry `_id` as the product slug
**What goes wrong:** Code that expects `doc["_id"]` to be a stable, meaningful identifier (as it is on `products`, where `_id` is the catalog slug).
**Why it happens:** `price_points` was created with no `$jsonSchema` validator and no explicit `_id` field in its documented shape (`db/init_collections.py`'s own comment: `"Per-point document shape... {ts, product_id, item_price, total_price}"` — no `_id` listed) `[VERIFIED: db/init_collections.py:77-82]`. Every `price_points` document therefore gets an auto-generated `ObjectId` `_id`, unlike `products`.
**How to avoid:** Never read or return `doc["_id"]` from `price_points` — `product_id` (the metaField) is the correct identifier field. This falls out naturally from Pattern 1's dict-building approach (which never touches `_id` at all).
**Warning signs:** N/A directly for this phase (no plan should ever reference `price_points._id`), but flagged because it's the kind of copy-paste-from-`products.py` mistake this phase's proximity to `catalog_service.py` invites.

## Code Examples

### Thin blueprint route (mirrors `product_detail`'s exact convention)
```python
# Source: pattern mirrored from api/blueprints/products.py's existing
# product_detail route [VERIFIED: api/blueprints/products.py:55-68]
@products_bp.route("/products/<product_id>/history")
def product_history(product_id):
    """GET /products/<product_id>/history — raw price_points series,
    time-ordered ascending (PRICE-07, D-04).

    Always 200 + a JSON array, even when empty or single-element (the
    frontend decides "insufficient" per D-07 — see Pitfall 2). No 404
    branch for an unknown product_id in this phase's scope (Claude's
    discretion note: follow existing "raw price_points document shape"
    convention; the planner may choose to add a 404 for unknown
    product_id if it fits catalog_service's existing None-check
    pattern for get_product_detail, but the roadmap's success criteria
    do not require it).
    """
    history = price_service.get_price_history(get_db(), product_id)
    return jsonify(history)
```

### New client function (mirrors `getProductDetail`'s exact convention)
```javascript
// Source: pattern mirrored from frontend/src/api/client.js's existing
// getProductDetail [VERIFIED: frontend/src/api/client.js:38-40]
export const getPriceHistory = (productId) =>
  request(`/products/${encodeURIComponent(productId)}/history`)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| Recharts v2.x `accessibilityLayer` opt-in | `accessibilityLayer` is `true` by default | Recharts 3.0 `[CITED: Context7 /recharts/recharts — storybook/stories/API/Accessibility.mdx]` | Charts built with this phase's example code get keyboard navigation/screen-reader support for free, no extra prop needed |

**Deprecated/outdated:** None relevant to this phase's scope.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `recharts` (exact package name) is the correct npm package for this project's intended charting library | Standard Stack | Low — name matches CLAUDE.md's already-locked stack decision and was confirmed to exist/be actively maintained on the npm registry this session; a misspelled or squatted alternative would have failed the `npm view`/legitimacy checks run this session |
| A2 | The category-axis-plus-tickFormatter XAxis pattern (vs. true `scale="time" type="number"`) is sufficient for this phase's needs | Pattern 3 | Low — D-02 already rules out zoom/range interactions that would most benefit from a true numeric time scale; if a future v2 range-selector phase needs precise sub-day tick spacing, it can revisit this choice then |

## Open Questions

1. **Should the history endpoint 404 for an unknown `product_id`, matching `product_detail`'s existing 404 convention?**
   - What we know: `product_detail` returns 404 `{"error": "not_found"}` for an unknown id via `catalog_service.get_product_detail` returning `None`.
   - What's unclear: The roadmap's success criteria for this phase don't mention a 404 case for `/history`, and in practice the frontend only ever calls this endpoint for a `productId` the loader has already resolved successfully (so a genuinely unknown id shouldn't reach this endpoint in normal use).
   - Recommendation: Simplest correct behavior — `get_price_history` returns `[]` for an unknown `product_id` (same as "zero points"), no 404 branch needed. If the planner wants defense-in-depth against a malformed/stale `productId` in the URL, a 404 check can be added by reusing `catalog_service`'s existing product-lookup, but it is not required by any locked decision or success criterion.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|--------------|-----------|---------|----------|
| Node.js | Frontend build/test/dev | Yes | 22 (per `.github/workflows/ci.yml`, `[VERIFIED: .github/workflows/ci.yml]`) | — |
| npm | Installing `recharts` | Yes | — | — |
| MongoDB | `price_points` queries | Yes (CI: `mongo:7` service container `[VERIFIED: .github/workflows/ci.yml]`; local: `MONGODB_URI` env var, skips gracefully if unset per `tests/conftest.py`) | 7.0 | — |
| Python 3.12 | Backend service/route | Yes | 3.12.13 (confirmed this session) | — |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** None — `recharts` is not yet installed but has no fallback need (it is this phase's actual deliverable dependency, gated behind the package-legitimacy checkpoint above).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Backend framework | pytest 8.4.2 (existing, configured via `pytest.ini`) |
| Frontend framework | vitest 4.1.10 (existing, configured via `vite.config.js` `test` block) |
| Config file | `pytest.ini` (backend), `frontend/vite.config.js` (frontend) |
| Quick run command (backend) | `pytest tests/test_price_service.py tests/test_api_products.py -x` |
| Quick run command (frontend) | `npm test -- PriceHistoryChart ProductDetailPage --run` (from `frontend/`) |
| Full suite command (backend) | `pytest` |
| Full suite command (frontend) | `npm test` (from `frontend/`) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PRICE-07 | `get_price_history` returns raw series ascending by `ts`, using the `api_db` fixture to insert controlled `price_points` docs | unit | `pytest tests/test_price_service.py -x` | ✅ exists — extend |
| PRICE-07 | `GET /products/<id>/history` returns 200 + JSON array via the `client` fixture | integration | `pytest tests/test_api_products.py -x` | ✅ exists — extend |
| PRICE-07 | `get_price_history` returns `[]` for zero points, 1-element list for one point (no crash, no 404) | unit | `pytest tests/test_price_service.py -x` | ✅ exists — extend |
| PRICE-07 | `PriceHistoryChart` renders "Not enough price history yet" for `data.length < 2` (including `null`/`undefined`) | unit | `npm test -- PriceHistoryChart --run` | ❌ Wave 0 — new file `PriceHistoryChart.test.jsx` |
| PRICE-07 | `PriceHistoryChart` renders a Recharts `LineChart` for `data.length >= 2` | unit | `npm test -- PriceHistoryChart --run` | ❌ Wave 0 |
| PRICE-07 | `ProductDetailPage`'s progressive fetch calls `getPriceHistory` after mount and renders the returned data (mock `client.js`, mirroring the existing `useLoaderDataMock` pattern) | unit | `npm test -- ProductDetailPage --run` | ✅ exists — extend |

### Sampling Rate
- **Per task commit:** the quick run commands above (backend/frontend as appropriate to the file touched)
- **Per wave merge:** `pytest` (backend) + `npm test` (frontend)
- **Phase gate:** Full suite green (both) before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `frontend/src/components/PriceHistoryChart.test.jsx` — does not exist yet; covers the insufficient-data branch and the Recharts-rendering branch
- [ ] `frontend/src/components/PriceHistoryChart.jsx` / `.module.css` — do not exist yet; core deliverable
- [ ] `frontend/package.json` — `recharts` not yet a dependency; install gated behind `checkpoint:human-verify`
- [ ] `tests/test_price_service.py` extension — add `get_price_history` test cases (ascending order, empty, single-point, multi-point)
- [ ] `tests/test_api_products.py` extension — add `/products/<id>/history` route test cases (200 + array shape, empty-array case)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V2 Authentication | No | No auth surface — public read-only endpoint, same as every existing `/products*` route |
| V3 Session Management | No | No sessions anywhere in this app |
| V4 Access Control | No | No access-control surface — this endpoint is exactly as public as `GET /products/<id>` |
| V5 Input Validation | Yes | `product_id` is a URL path segment passed straight into a `find({"product_id": product_id})` equality match (not string-interpolated into a query operator) — same safe pattern `get_current_price`/`get_trend_baseline` already use; no new injection surface introduced |
| V6 Cryptography | No new surface | Reuses the existing `MONGODB_URI` connection; no new secrets |

### Known Threat Patterns for this phase's stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Unbounded response size if a product accumulates an extremely large `price_points` history over years | Denial of Service (self-inflicted, low severity at current data volume) | REQUIREMENTS.md's own "Out of Scope" table already notes price_points volume is small (~6 points/day/product) and downsampling is explicitly "not needed" for this milestone — no mitigation required now, but worth a comment in `get_price_history` noting this assumption if data volume ever needs revisiting (matches D-02's own "revisit if data volume grows" framing) |
| `ObjectId`/raw-datetime serialization crash reaching the client as an unhandled 500 with a stack trace | Information Disclosure (low severity — an internal `TypeError`, not a data leak) | Pitfall 1's mitigation (never `jsonify()` a raw document) prevents this at the source; the app's existing global error handler (`api/app.py`) still converts any uncaught exception to a generic 500 rather than leaking a traceback, per the CR-01 precedent already established in `products.py`'s docstring |

## Sources

### Primary (HIGH confidence)
- Context7 `/recharts/recharts` (233 snippets, benchmark 79.12) — `LineChart`/`XAxis`/`YAxis`/`CartesianGrid`/`Tooltip`/`ResponsiveContainer` composition, `labelFormatter`/`formatter` Tooltip props, numeric time-scale XAxis pattern, `accessibilityLayer` default-true note
- This project's own source files, read directly this session: `api/services/price_service.py`, `api/services/catalog_service.py`, `api/blueprints/products.py`, `frontend/src/api/client.js`, `frontend/src/router.jsx`, `frontend/src/pages/ProductDetailPage.jsx`, `frontend/src/components/TrendBadge.jsx`, `frontend/src/components/PriceDisplay.jsx`, `frontend/src/components/FreshnessIndicator.jsx`, `frontend/src/utils/relativeTime.js`, `frontend/src/styles/tokens.css`, `frontend/vite.config.js`, `frontend/package.json`, `db/init_collections.py`, `api/db.py`, `api/app.py`, `tests/conftest.py`, `tests/test_price_service.py`, `frontend/src/pages/ProductDetailPage.test.jsx`, `.github/workflows/ci.yml`
- Installed `flask==3.1.3` site-packages source (`json/provider.py`), read directly this session, matching this project's pinned `requirements.txt` version — confirms the RFC-822 `datetime` serialization and missing `ObjectId` handler
- `npm view recharts version/time.modified/scripts.postinstall/repository.url` — run this session against the live npm registry
- `gsd-tools query package-legitimacy check --ecosystem npm recharts` — run this session, returned `[SUS]`/`too-new`

### Secondary (MEDIUM confidence)
- MongoDB official docs (via WebSearch, cross-checked across multiple official `mongodb.com/docs` pages): `timeseries-best-practices`, `timeseries-index`, `timeseries-querying` — compound `{metaField, timeField}` auto-index behavior since MongoDB 6.3

### Tertiary (LOW confidence)
- None used as load-bearing claims in this document.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Recharts is already the project's locked stack decision; version/legitimacy confirmed directly against the npm registry this session
- Architecture: HIGH — every pattern is either read directly from this project's own existing source files or confirmed via Context7 official Recharts docs
- Pitfalls: HIGH — Pitfall 1 (the most important finding in this document) was verified by reading this project's actual installed Flask source code, not inferred from training data

**Research date:** 2026-08-18
**Valid until:** 2026-09-17 (30 days — stable domain: MongoDB time-series querying and Flask JSON serialization behavior are not fast-moving; Recharts version pin should be re-verified if this phase's execution slips past that window)
