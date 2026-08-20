# Phase 9: 24h & All-Time Price Badges - Pattern Map

**Mapped:** 2026-08-20
**Files analyzed:** 8 (2 backend extend, 1 backend test extend x3, 2 frontend new, 1 frontend extend, 1 frontend css extend)
**Analogs found:** 8 / 8 (all files are either extensions of themselves or have an exact in-repo analog — no external pattern needed)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|-----------------|---------------|
| `api/services/price_service.py` (extend: add `get_all_time_range`, `TREND_24H_TOLERANCE_HOURS`) | service | CRUD (read aggregation) | itself — `get_trend_baseline` (same file, lines 122-159) | exact (self-extension, same file/module conventions) |
| `api/services/catalog_service.py` (extend: `get_product_detail`) | service | request-response (data assembly) | itself — existing `trend_7d`/`trend_30d` loop (lines 181-193) and zero-data branch (lines 170-175) | exact (self-extension) |
| `frontend/src/components/AllTimeRangeBadge.jsx` (NEW) | component | transform (pure display formatter) | `frontend/src/components/TrendBadge.jsx` | role-match (same branch-on-status discipline, different data shape) |
| `frontend/src/components/AllTimeRangeBadge.module.css` (NEW) | config/style | — | `frontend/src/components/TrendBadge.module.css` | role-match (reuses same tokens/padding) |
| `frontend/src/components/AllTimeRangeBadge.test.jsx` (NEW) | test | — | `frontend/src/components/TrendBadge.test.jsx` (referenced in RESEARCH, not yet read — see below) | role-match |
| `frontend/src/pages/ProductDetailPage.jsx` (extend) | component | request-response (render loader data) | itself — existing `.detail__trendSection` block (lines 140-149) | exact (self-extension) |
| `frontend/src/pages/ProductDetailPage.module.css` (extend: add `.detail__allTimeSection`) | config/style | — | itself — `.detail__trendSection`/`.trend` rules (lines 111-126) | exact (self-extension) |
| `tests/test_price_service.py` / `tests/test_catalog_service.py` / `tests/test_api_products.py` (extend) | test | CRUD / request-response | themselves — existing `get_trend_baseline`/`get_product_detail` test cases | exact (self-extension) |

## Pattern Assignments

### `api/services/price_service.py` (service, CRUD/aggregation) — extend

**Analog:** same file, `get_trend_baseline` (lines 122-159) and module constant `TREND_TOLERANCE_DAYS` (line 34)

**Imports pattern** (lines 32-34, unchanged — no new imports needed):
```python
from datetime import timedelta, timezone

TREND_TOLERANCE_DAYS = 3  # D-05
```
Add sibling constant near it:
```python
TREND_24H_TOLERANCE_HOURS = 4  # NEW — do not reuse TREND_TOLERANCE_DAYS for the 24h window
```

**Core aggregation pattern to copy** (mirrors `get_trend_baseline`'s pipeline style, lines 147-159):
```python
def get_all_time_range(db, product_id):
    """Return {"high": float, "low": float} across every stored point
    for product_id, or None only when zero points exist ever (mirrors
    get_current_price's D-01 zero-points contract, NOT get_trend_baseline's
    tolerance-window contract)."""
    pipeline = [
        {"$match": {"product_id": product_id}},
        {"$group": {
            "_id": None,
            "high": {"$max": "$total_price"},
            "low": {"$min": "$total_price"},
        }},
    ]
    results = list(db.price_points.aggregate(pipeline))
    if not results:
        return None
    return {"high": results[0]["high"], "low": results[0]["low"]}
```

**Call-site pattern for the 24h trend** (new call, reusing existing `get_trend_baseline` signature at lines 122 with explicit non-default `tolerance_days`):
```python
baseline_24h = get_trend_baseline(
    db, product_id, current_ts, days=1,
    tolerance_days=TREND_24H_TOLERANCE_HOURS / 24,
)
```

**Error/None handling pattern** — mirrors `compute_pct_change`'s divide-by-zero guard (lines 175-176): `get_all_time_range` returns `None` only on zero documents; no exception path, matching every other function in this module (no try/except anywhere in the file — Mongo aggregate() failures are allowed to propagate, consistent with the existing convention).

**Docstring/comment convention** to copy: every function in this file opens with a docstring explaining the specific None-vs-empty-list contract and cross-references the sibling function it is deliberately different from (see lines 12-29 module docstring, and each function's own docstring). Follow this exactly for `get_all_time_range` — explicitly state it is NOT a tolerance-window function.

---

### `api/services/catalog_service.py` (service, request-response) — extend `get_product_detail`

**Analog:** same file, `get_product_detail` (lines 148-195)

**Imports pattern** (lines 21-25) — add `get_all_time_range` to the existing import block:
```python
from api.services.price_service import (
    compute_pct_change,
    get_current_price,
    get_trend_baseline,
    get_all_time_range,  # NEW
)
```

**Zero-data early-return branch to extend** (lines 170-175 — MUST add both new keys here, this is Pitfall 2 from RESEARCH.md):
```python
if detail["current_price"] is None:
    detail["trend_7d"] = {"pct_change": None, "status": "insufficient_data"}
    detail["trend_30d"] = {"pct_change": None, "status": "insufficient_data"}
    detail["trend_24h"] = {"pct_change": None, "status": "insufficient_data"}          # NEW
    detail["all_time_range"] = {"high": None, "low": None, "status": "insufficient_data"}  # NEW
    return detail
```

**Core pattern — trend_24h assembly** (sibling call to the existing `TREND_WINDOWS` loop at lines 181-193, added as an explicit standalone block per RESEARCH Pattern 1 — do NOT fold into the `(7, 30)` loop):
```python
baseline_24h = get_trend_baseline(
    db, product_id, current_ts, days=1,
    tolerance_days=TREND_24H_TOLERANCE_HOURS / 24,
)
if baseline_24h is None:
    detail["trend_24h"] = {"pct_change": None, "status": "insufficient_data"}
else:
    pct = compute_pct_change(current_total, baseline_24h["total_price"])
    detail["trend_24h"] = (
        {"pct_change": None, "status": "insufficient_data"} if pct is None
        else {"pct_change": pct, "status": "ok"}
    )
```
(Requires importing `TREND_24H_TOLERANCE_HOURS` from `price_service` alongside the other imports, or importing the module and referencing `price_service.TREND_24H_TOLERANCE_HOURS`.)

**Core pattern — all_time_range assembly**:
```python
all_time = get_all_time_range(db, product_id)
detail["all_time_range"] = (
    {"high": None, "low": None, "status": "insufficient_data"} if all_time is None
    else {"high": all_time["high"], "low": all_time["low"], "status": "ok"}
)
```

**Error handling pattern**: none needed beyond the existing None-check branching shown above — this file has no try/except anywhere (`InvalidProductTypeError` is raised, not caught, in `list_products`); consistent style: raise/propagate, never swallow.

---

### `frontend/src/components/AllTimeRangeBadge.jsx` (component, transform) — NEW

**Analog:** `frontend/src/components/TrendBadge.jsx` (full file, 42 lines) + `frontend/src/components/PriceDisplay.jsx` lines 3-5 (`formatCurrency`)

**Imports pattern** (TrendBadge.jsx line 1):
```jsx
import styles from './AllTimeRangeBadge.module.css'
```

**formatCurrency pattern to copy locally** (PriceDisplay.jsx lines 3-5 — copy-paste per-component, this codebase does NOT share a `utils/format.js`):
```jsx
function formatCurrency(value) {
  return typeof value === 'number' ? `$${value.toFixed(2)}` : '—'
}
```

**Core branch-on-status-first pattern** (TrendBadge.jsx lines 15-25, adapted):
```jsx
export default function AllTimeRangeBadge({ range }) {
  if (!range || range.status === 'insufficient_data') {
    return (
      <span
        className={`${styles.range} ${styles['range--muted']}`}
        aria-label="insufficient data"
      >
        {'—'}
      </span>
    )
  }
  return (
    <span className={styles.range}>
      {formatCurrency(range.low)} – {formatCurrency(range.high)}
    </span>
  )
}
```

Note: unlike `TrendBadge`, there is no up/down/flat branching — only two states (ok / insufficient_data), per UI-SPEC D-UI-01 (`ok` state reuses the `--trend-flat` visual treatment, never `--trend-up`/`--trend-down`).

**JSDoc comment convention to copy** (TrendBadge.jsx lines 3-14 style — explain what is NOT recomputed and why status is checked first): follow the same structure, referencing PRICE-09 and 09-UI-SPEC.md D-UI-01.

---

### `frontend/src/components/AllTimeRangeBadge.module.css` (style) — NEW

**Analog:** `frontend/src/components/TrendBadge.module.css` (full file, 36 lines)

**Pattern to copy** — reuse `--trend-flat` for "ok" and `--trend-insufficient` for muted, identical padding/radius tokens:
```css
.range {
  display: inline-block;
  font-size: var(--font-size-label);
  line-height: var(--line-height-label);
  font-weight: var(--font-weight-regular);
  font-variant-numeric: tabular-nums;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--space-xs);
  background: var(--trend-flat);
  color: var(--color-bg);
}

.range--muted {
  background: none;
  color: var(--trend-insufficient);
  padding: 0;
}
```
Class names differ from `TrendBadge.module.css` (`.range`/`.range--muted` vs `.trend-badge`/`.trend-badge--muted`) since this is a distinct component with its own CSS module namespace — no collision risk (CSS Modules scope locally), but naming should read clearly in tests/devtools.

---

### `frontend/src/components/AllTimeRangeBadge.test.jsx` (test) — NEW

**Analog:** `frontend/src/components/TrendBadge.test.jsx` was referenced in 09-RESEARCH.md (`mirrors TrendBadge.test.jsx's 2-state coverage`) but was not directly read this session — locate and read it at plan/execute time; it will show the exact `@testing-library/react` render + `screen.getByLabelText('insufficient data')` / text-content assertions used for `TrendBadge`'s muted vs. colored states. `AllTimeRangeBadge.test.jsx` needs only 2 cases (ok, insufficient_data/missing) instead of `TrendBadge`'s 4 (up/down/flat/insufficient_data).

---

### `frontend/src/pages/ProductDetailPage.jsx` (component, request-response) — extend

**Analog:** same file, existing `.detail__trendSection` block (lines 140-149)

**Import pattern to add** (alongside line 5's `TrendBadge` import):
```jsx
import AllTimeRangeBadge from '../components/AllTimeRangeBadge'
```

**Core pattern — trend section gains a 3rd badge, ordered 24h/7d/30d** (replace lines 140-149):
```jsx
<div className={styles.detail__trendSection}>
  <div className={styles.trend}>
    <span className={styles.trendLabel}>24h</span>
    <TrendBadge trend={product.trend_24h} />
  </div>
  <div className={styles.trend}>
    <span className={styles.trendLabel}>7d</span>
    <TrendBadge trend={product.trend_7d} />
  </div>
  <div className={styles.trend}>
    <span className={styles.trendLabel}>30d</span>
    <TrendBadge trend={product.trend_30d} />
  </div>
</div>

<div className={styles.detail__allTimeSection}>
  <span className={styles.trendLabel}>All-time range (since we started tracking)</span>
  <AllTimeRangeBadge range={product.all_time_range} />
</div>
```
Insert the new `.detail__allTimeSection` block immediately after `.detail__trendSection` and before `.detail__historySection` (line 151), per UI-SPEC D-UI-04 locked ordering.

Both new fields render **unconditionally**, exactly like the existing `trend_7d`/`trend_30d` — no `price_status === 'ok'` gate (see file's own doc comment lines 47-52 explaining this convention already).

---

### `frontend/src/pages/ProductDetailPage.module.css` (style) — extend

**Analog:** same file, `.detail__trendSection`/`.trend`/`.trendLabel` rules (lines 111-126)

**Pattern to add** (new rule, per UI-SPEC Layout Notes):
```css
.detail__allTimeSection {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-xs);
}
```
No new tokens — reuses `--space-xs` exactly as `.trend` does (line 118-119).

---

### `tests/test_price_service.py`, `tests/test_catalog_service.py`, `tests/test_api_products.py` — extend

**Analogs:** existing test cases for `get_trend_baseline`/`get_product_detail`/`GET /products/<id>` in these same files (not read this session — files already exist and establish conventions per RESEARCH.md: `api_db` fixture, deferred imports, D-11 raw-series guard reused via `test_detail_omits_raw_series`-style assertion). At plan time, read these files directly to copy the exact fixture/assertion style; RESEARCH.md's Validation Architecture section (Phase Requirements → Test Map) already specifies exactly which cases to add:
- `test_price_service.py`: `get_all_time_range` zero-points→None, single-point→`{high==low}`, multi-point→true spread; `get_trend_baseline(days=1, tolerance_days=4/24)` accepts within-window, rejects outside.
- `test_catalog_service.py`: `trend_24h`/`all_time_range` present and correctly shaped in both the zero-data early-return branch and the normal path; extend `test_detail_omits_raw_series`-style assertion to cover both new keys (Pitfall 4 — D-11 guard).
- `test_api_products.py`: JSON contract assertions that `trend_24h` and `all_time_range` keys are present with the correct shape on `GET /products/<id>`.

## Shared Patterns

### Status-first branching (backend and frontend)
**Source:** `api/services/catalog_service.py` lines 170-175 (backend) and `frontend/src/components/TrendBadge.jsx` lines 16-25 (frontend)
**Apply to:** All new fields/components in this phase — every new dict (`trend_24h`, `all_time_range`) always carries an explicit `status` key (`"ok"` / `"insufficient_data"`), never a missing key or a fabricated value; every new/reused component branches on `status`/prop-presence FIRST before touching the numeric payload.

### None-only-on-zero-documents vs. None-on-out-of-tolerance-window
**Source:** `api/services/price_service.py` — contrast `get_current_price` (lines 37-57, D-01: None only on zero docs) vs. `get_trend_baseline` (lines 122-159, D-05/D-06: None on missing-in-window). `get_all_time_range` follows the `get_current_price` contract, NOT the `get_trend_baseline` contract — this distinction is the single most important thing to get right this phase (RESEARCH.md Pitfall 3).

### Local formatCurrency, not shared utility
**Source:** `frontend/src/components/PriceDisplay.jsx` lines 3-5
**Apply to:** `AllTimeRangeBadge.jsx` — copy-paste the 1-line helper locally; this codebase has no `utils/format.js` and each display component owns its own formatter by convention.

### No try/except — let it propagate
**Source:** entire `api/services/price_service.py` and `api/services/catalog_service.py` — zero try/except blocks in either file.
**Apply to:** `get_all_time_range` and the `get_product_detail` extension — do not add defensive exception handling that doesn't already exist elsewhere in these modules.

## No Analog Found

None — every new/modified file in this phase has either a direct in-file self-extension precedent or an exact same-role component analog already in the codebase (`TrendBadge` → `AllTimeRangeBadge`, `get_trend_baseline` → `get_all_time_range`). This phase is explicitly scoped by RESEARCH.md as "zero new architecture" — confirmed true at the pattern-mapping level.

## Metadata

**Analog search scope:** `api/services/`, `frontend/src/components/`, `frontend/src/pages/`, `tests/` (all read directly this session per RESEARCH.md's own Sources list; no Glob/Grep search needed since RESEARCH.md already named every analog file explicitly)
**Files scanned:** `api/services/price_service.py`, `api/services/catalog_service.py`, `frontend/src/components/TrendBadge.jsx`, `frontend/src/components/TrendBadge.module.css`, `frontend/src/components/PriceDisplay.jsx`, `frontend/src/pages/ProductDetailPage.jsx`, `frontend/src/pages/ProductDetailPage.module.css`
**Pattern extraction date:** 2026-08-20
**Not yet read (defer to plan/execute time):** `frontend/src/components/TrendBadge.test.jsx`, `tests/test_price_service.py`, `tests/test_catalog_service.py`, `tests/test_api_products.py` — these exist and establish test conventions per RESEARCH.md but were not re-read here since RESEARCH.md already quotes their key fixtures/assertion names; read them directly when writing the actual test extensions to avoid stale excerpts.
