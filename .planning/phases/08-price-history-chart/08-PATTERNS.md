# Phase 8: Price History Chart - Pattern Map

**Mapped:** 2026-08-18
**Files analyzed:** 8
**Analogs found:** 8 / 8

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `api/services/price_service.py` (add `get_price_history`) | service | CRUD (read) | `api/services/price_service.py` — `get_current_price` (same file) | exact |
| `api/blueprints/products.py` (add `GET /products/<id>/history`) | route | request-response | `api/blueprints/products.py` — `product_detail` route (same file) | exact |
| `frontend/src/api/client.js` (add `getPriceHistory`) | service (API client) | request-response | `frontend/src/api/client.js` — `getProductDetail` (same file) | exact |
| `frontend/src/components/PriceHistoryChart.jsx` | component | transform (render) | `frontend/src/components/TrendBadge.jsx` | role-match (status-branch convention) |
| `frontend/src/components/PriceHistoryChart.module.css` | config (styles) | — | `frontend/src/components/TrendBadge.module.css` | role-match |
| `frontend/src/pages/ProductDetailPage.jsx` (add progressive fetch + chart section) | component (page) | event-driven (useEffect fetch) | same file (existing loader-driven render pattern) | exact (extend in place) |
| `tests/test_price_service.py` (extend) | test | CRUD (read) | same file — `test_current_price_gap_tolerant` | exact |
| `tests/test_api_products.py` (extend) | test | request-response | same file — existing `product_detail` route tests | exact |
| `frontend/src/components/PriceHistoryChart.test.jsx` (new) | test | transform (render) | `frontend/src/components/TrendBadge.jsx` conventions (no direct test file read, but same status-branch pattern to test) | role-match |

## Pattern Assignments

### `api/services/price_service.py` — add `get_price_history(db, product_id)`

**Analog:** same file, `get_current_price` (lines 31-51) and module docstring (lines 1-28)

**Module conventions to follow** (lines 1-28):
```python
"""Pure price-computation service functions ... over the
`price_points` time-series collection.

Pure, DB-taking-as-arg functions ... No top-level side effects on
import: no MongoClient construction, no os.environ read, no Flask
import ...
"""

from datetime import timedelta

TREND_TOLERANCE_DAYS = 3  # D-05
```

**Core query pattern to copy** (lines 31-51, `get_current_price`):
```python
def get_current_price(db, product_id):
    """..."""
    return db.price_points.find_one(
        {"product_id": product_id},
        sort=[("ts", -1)],
    )
```
New function follows the same `find`/`sort` shape but returns a list of clean dicts (not raw docs) per RESEARCH.md Pattern 1 / Pitfall 1:
```python
def get_price_history(db, product_id):
    """..."""
    docs = db.price_points.find(
        {"product_id": product_id},
        sort=[("ts", 1)],
    )
    return [
        {"ts": doc["ts"].isoformat(), "total_price": doc["total_price"]}
        for doc in docs
    ]
```

**Docstring style:** Google-style `Args:`/`Returns:` blocks exactly like `get_current_price`/`get_trend_baseline` (lines 39-51, 64-73). Include the same "why this is deliberately a distinct function" framing if relevant (mirrors the `get_current_price` vs `get_trend_baseline` distinction note in lines 11-23).

---

### `api/blueprints/products.py` — add `GET /products/<product_id>/history`

**Analog:** same file, `product_detail` route (lines 55-68)

**Imports** (lines 22-27, unchanged — reuse):
```python
from flask import Blueprint, jsonify, request

from api.db import get_db
from api.services import catalog_service
```
Add `price_service` to the existing `from api.services import ...` grouping.

**Thin-route pattern to copy** (lines 55-68):
```python
@products_bp.route("/products/<product_id>")
def product_detail(product_id):
    """GET /products/<product_id> — single-product detail assembly
    (SEARCH-02, PRICE-01/02/03).

    Returns 200 + the detail object on success; 404
    {"error": "not_found"} when catalog_service.get_product_detail
    returns None for an unknown id.
    """
    detail = catalog_service.get_product_detail(get_db(), product_id)
    if detail is None:
        return jsonify({"error": "not_found"}), 404

    return jsonify(detail)
```
New route mirrors this exactly but has **no None/404 branch** (Pitfall 2 — array length, not None, is the signal; `[]` is a valid 200):
```python
@products_bp.route("/products/<product_id>/history")
def product_history(product_id):
    """GET /products/<product_id>/history — raw price_points series,
    time-ordered ascending (PRICE-07, D-04). Always 200 + JSON array.
    """
    history = price_service.get_price_history(get_db(), product_id)
    return jsonify(history)
```

**Error handling pattern:** No bare `except Exception` anywhere in this file (module docstring lines 10-14) — only known/expected error cases (`InvalidProductTypeError`, `None` result) are translated; everything else propagates to the app-level global error handler. New route follows the same restraint — no try/except added.

---

### `frontend/src/api/client.js` — add `getPriceHistory(productId)`

**Analog:** same file, `getProductDetail` (lines 38-40)

**Imports/setup** (lines 1-21, unchanged — reuse `request()` helper, do not duplicate fetch logic):
```javascript
const BASE = import.meta.env.VITE_API_BASE_URL || ''

async function request(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.error || `Request failed: ${res.status}`)
  }
  return res.json()
}
```

**Function pattern to copy** (lines 38-40):
```javascript
/** GET /products/<product_id> — single-product detail assembly. */
export const getProductDetail = (productId) =>
  request(`/products/${encodeURIComponent(productId)}`)
```
New function:
```javascript
/** GET /products/<product_id>/history — raw price-history series. */
export const getPriceHistory = (productId) =>
  request(`/products/${encodeURIComponent(productId)}/history`)
```

---

### `frontend/src/components/PriceHistoryChart.jsx` (new)

**Analog:** `frontend/src/components/TrendBadge.jsx` (whole file, 42 lines)

**Imports pattern** (line 1):
```javascript
import styles from './TrendBadge.module.css'
```
→ `import styles from './PriceHistoryChart.module.css'` plus Recharts imports per RESEARCH.md Pattern 3.

**"Branch on status first" convention to copy** (lines 15-25):
```javascript
export default function TrendBadge({ trend }) {
  if (!trend || trend.status === 'insufficient_data' || typeof trend.pct_change !== 'number') {
    return (
      <span
        className={`${styles['trend-badge']} ${styles['trend-badge--muted']}`}
        aria-label="insufficient data"
      >
        {'—'}
      </span>
    )
  }
  // ... normal-case rendering below
}
```
Apply the same "guard clause returns early for the insufficient case" shape for D-07/D-08:
```javascript
export default function PriceHistoryChart({ data }) {
  if (!data || data.length < 2) {
    return <p className={styles.insufficient}>Not enough price history yet</p>
  }
  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data}>{/* CartesianGrid/XAxis/YAxis/Tooltip/Line per RESEARCH Pattern 3 */}</LineChart>
    </ResponsiveContainer>
  )
}
```

**Component doc-comment convention** (lines 3-14 of TrendBadge.jsx) — a block comment above the export explaining: what data it's a pure formatter over, what it never does (never recompute), and which decision/requirement IDs it satisfies. Mirror this for `PriceHistoryChart.jsx`, referencing D-01/D-07/D-08/PRICE-07.

---

### `frontend/src/components/PriceHistoryChart.module.css` (new)

**Analog:** `frontend/src/components/TrendBadge.module.css` (full file, 36 lines)

**Conventions to copy:**
- Top-of-file comment naming the requirement/decision context, e.g.:
  ```css
  /* PriceHistoryChart — full-axes line chart with insufficient-history
   * fallback (D-01, D-07, D-08). */
  ```
- Use existing design tokens, not new hardcoded values — e.g. `var(--font-size-label)`, `var(--space-xs)`, `var(--color-bg)` style variables (lines 8-13, 17-19 of TrendBadge.module.css). For the chart specifically, reuse `var(--color-divider)`, `var(--color-accent)`, `var(--text-secondary)`, `var(--color-surface)` (confirmed present in `frontend/src/styles/tokens.css` per RESEARCH.md Pattern 3).
- The "muted"/insufficient state styling precedent (lines 31-35 of TrendBadge.module.css — no background, quieter text color) — mirror for `.insufficient` class in the new file.

---

### `frontend/src/pages/ProductDetailPage.jsx` — add progressive fetch + chart section

**Analog:** same file (full file, 124 lines) — extend in place, do not restructure existing loader-driven rendering.

**Imports to add** (existing imports at lines 1-5):
```javascript
import { Link, useLoaderData } from 'react-router'
import styles from './ProductDetailPage.module.css'
import PriceDisplay from '../components/PriceDisplay'
import TrendBadge from '../components/TrendBadge'
import FreshnessIndicator from '../components/FreshnessIndicator'
```
Add:
```javascript
import { useEffect, useState } from 'react'
import { useParams } from 'react-router'
import { getPriceHistory } from '../api/client'
import PriceHistoryChart from '../components/PriceHistoryChart'
```

**Existing loader-driven pattern (unchanged)** (line 56):
```javascript
export default function ProductDetailPage() {
  const product = useLoaderData()
  // ...
}
```

**New progressive-fetch pattern to add inside the component** (per RESEARCH.md Pattern 4 — this is the one genuinely new pattern in this phase, no existing analog in the codebase for a post-mount `useEffect` fetch with cancellation guard):
```javascript
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

**Section-composition convention to copy** (lines 106-115, the trend section — shows the established "own div wrapper + label" pattern for a page section):
```javascript
<div className={styles.detail__trendSection}>
  <div className={styles.trend}>
    <span className={styles.trendLabel}>7d</span>
    <TrendBadge trend={product.trend_7d} />
  </div>
  <div className={styles.trend}>
    <span className={styles.trendLabel}>30d</span>
    <TrendBadge trend={product.trend_30d} />
  </div>
</div>
```
New "Price History" section (D-03: own visible heading, placed after trend section) follows the same wrapper-div convention, e.g.:
```javascript
<div className={styles.detail__historySection}>
  <h2 className={styles.sectionHeading}>Price History</h2>
  {historyError ? (
    <p className={styles.detail__noData}>Couldn't load price history</p>
  ) : (
    <PriceHistoryChart data={history} />
  )}
</div>
```

**Status-branch-before-touching-data convention** (lines 92-104, the price section branches on `price_status` before ever reading `current_price`) — same discipline applies to `historyError`/`history` here: check error state before rendering `PriceHistoryChart`.

---

## Shared Patterns

### Backend: pure service function taking `db` as first arg, no top-level side effects
**Source:** `api/services/price_service.py` module docstring (lines 1-9) and every existing function signature (`get_current_price(db, product_id)`, `get_trend_baseline(db, product_id, ...)`)
**Apply to:** `get_price_history(db, product_id)`
```python
def get_current_price(db, product_id):
    return db.price_points.find_one({"product_id": product_id}, sort=[("ts", -1)])
```

### Backend: thin blueprint route — parse args, delegate to one service call, jsonify with no transformation
**Source:** `api/blueprints/products.py` lines 30-68 (both existing routes)
**Apply to:** new `product_history` route
```python
detail = catalog_service.get_product_detail(get_db(), product_id)
if detail is None:
    return jsonify({"error": "not_found"}), 404
return jsonify(detail)
```
Note: the new route deliberately has NO error branch (Pitfall 2) — only the two existing routes have branches, and only for genuinely exceptional/known cases.

### Backend: never `jsonify()` a raw MongoDB document
**Source:** `api/services/catalog_service.py:75` (`_product_summary`'s `"as_of": current_point["ts"].isoformat()` — read about, not directly re-read this session; cited in RESEARCH.md Pitfall 1)
**Apply to:** `get_price_history` — must build `{"ts": doc["ts"].isoformat(), "total_price": doc["total_price"]}` dicts, never return cursor items directly to `jsonify()`.

### Frontend: `request()` fetch helper — single source of truth for all API calls
**Source:** `frontend/src/api/client.js` lines 14-21
**Apply to:** `getPriceHistory` (and every other client function)
```javascript
async function request(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.error || `Request failed: ${res.status}`)
  }
  return res.json()
}
```

### Frontend: branch on status/length before touching payload shape
**Source:** `frontend/src/components/TrendBadge.jsx` lines 16-25; `ProductDetailPage.jsx` lines 92-104 (`price_status` check before reading `current_price`)
**Apply to:** `PriceHistoryChart.jsx` (`data.length < 2` guard) and `ProductDetailPage.jsx` (`historyError` guard before rendering chart)

### Frontend: CSS Modules with design tokens, never hardcoded hex values
**Source:** `frontend/src/components/TrendBadge.module.css` (uses `var(--font-size-label)`, `var(--trend-up)`, `var(--color-bg)`, etc. throughout)
**Apply to:** `PriceHistoryChart.module.css` — use `var(--color-divider)`, `var(--color-accent)`, `var(--text-secondary)`, `var(--color-surface)` from `frontend/src/styles/tokens.css`

## No Analog Found

None — every file in scope has at least a role-match analog in the existing codebase. The one genuinely novel pattern (post-mount `useEffect` fetch with a `cancelled` guard for progressive loading outside the router loader) has no prior precedent in this codebase; use RESEARCH.md Pattern 4's example verbatim as the source of truth for that piece, since there is no existing analog to point to.

## Metadata

**Analog search scope:** `api/services/`, `api/blueprints/`, `frontend/src/api/`, `frontend/src/components/`, `frontend/src/pages/`, `tests/`
**Files read this session:** `api/services/price_service.py`, `api/blueprints/products.py`, `frontend/src/api/client.js`, `frontend/src/components/TrendBadge.jsx`, `frontend/src/components/TrendBadge.module.css`, `frontend/src/pages/ProductDetailPage.jsx`, `tests/test_price_service.py` (partial)
**Pattern extraction date:** 2026-08-18
