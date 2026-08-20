# Phase 9: 24h & All-Time Price Badges - Research

**Researched:** 2026-08-20
**Domain:** Extending an existing MongoDB time-series aggregation + Flask JSON detail-response contract + React badge-rendering pattern with two new derived fields — no new architecture, no new dependencies.
**Confidence:** HIGH

## Summary

Phase 9 is a pure extension of code that already exists and is fully working: Phase 8 (actually Phase 5/8 combined) already ships `catalog_service.get_product_detail()` returning `trend_7d`/`trend_30d` objects computed by `price_service.get_trend_baseline()`, rendered by a reusable four-state `TrendBadge` React component. There is no new backend route, no new frontend page, and no new package to install. The two new capabilities are:

1. **PRICE-08 (24h badge):** Add a `trend_24h` field to the existing `get_product_detail()` response, computed the same way as `trend_7d`/`trend_30d` (via `price_service.get_trend_baseline`), rendered by the existing `TrendBadge` component. The one real decision this phase must make explicitly is the tolerance window: the existing `TREND_TOLERANCE_DAYS = 3` default is nonsensical applied to a 1-day target (a ±3-day window around "1 day ago" spans -2 to +4 days — it would almost never report insufficient data and would silently badge a point that could be 4 days stale as "24h"). This must be a new, explicit, much smaller tolerance grounded in the ingestion cadence.
2. **PRICE-09 (all-time high/low):** Add an `all_time_range` field computed by a **new** `price_service` function using a MongoDB `$min`/`$max` aggregation over the full `price_points` series for a product — no new endpoint, no raw series returned (must stay compliant with the standing D-11 decision: the detail response never contains a raw price_points array).

Both new fields are added to the *same* `GET /products/<id>` response and rendered on the *same* `ProductDetailPage` — this is not incidental convenience, it's the explicit reason ROADMAP.md sequences Phase 9 after Phase 8 (`.planning/ROADMAP.md:80`, read this session): *"both phases extend the same `ProductDetailPage` surface and the same detail-response contract; sequencing them avoids conflicting edits to the page and its tests. No data dependency — the badges read the same `price_points` collection directly."* `[VERIFIED: .planning/ROADMAP.md:80]`

**Primary recommendation:** Extend `catalog_service.get_product_detail()` with two new fields (`trend_24h`, `all_time_range`) computed by two `price_service.py` functions — reuse `get_trend_baseline(days=1, tolerance_days=<new small constant>)` for the badge, add a new `get_all_time_range(db, product_id)` aggregation function for the range — and render them with the existing `TrendBadge` component (24h) plus one new small presentational component (all-time range, since its shape is two absolute prices, not a signed percent).

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PRICE-08 | User can see a 24h price-change badge on the product detail page, alongside the existing 7d/30d badges | Pattern 1 (`get_trend_baseline` reuse with new explicit tolerance) + Frontend Pattern (`TrendBadge` reuse, no new component needed) — see Code Examples |
| PRICE-09 | User can see an all-time high/low price badge on the product detail page, covering the full range since data collection began | Pattern 2 (new `get_all_time_range` aggregation function) + Frontend Pattern (new `AllTimeRangeBadge` component) — see Code Examples, Wave 0 Gaps |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

Read `./.claude/CLAUDE.md` this session. Directives applicable to this phase:

- **Tech stack lock:** Python + Flask + MongoDB (PyMongo) backend, React SPA frontend — this phase introduces no deviation; all work is within `api/services/*.py`, `api/blueprints/products.py` (unchanged), and `frontend/src/**`.
- **No scraping / official eBay APIs only:** not applicable — this phase reads only already-ingested `price_points` data, no new eBay API calls.
- **MongoDB time-series collections for price-history data:** `price_points` is already a native time-series collection (`timeField: ts`, `metaField: product_id`, `granularity: hours` — `[VERIFIED: db/init_collections.py:83-87]`); both new functions query it via standard aggregation, consistent with this constraint.
- **No Celery/broker infra:** not applicable — no background job work in this phase.
- **Recharts only for charting, not for plain badges:** this phase's UI is "plain text/number UI, no new charting surface" per `.planning/STATE.md:136` (already verified above) — consistent with the CLAUDE.md-documented Recharts-vs-alternatives tradeoff table, which is scoped to actual charts, not badges.
- **GSD workflow enforcement:** file-changing work must go through `/gsd-execute-phase` (or equivalent GSD entry point) once this phase is planned — not a research-time concern, noted for the planner/executor.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| 24h/all-time price computation (aggregation over `price_points`) | Database/Storage | API/Backend | MongoDB time-series `$min`/`$max`/nearest-point aggregation is the correct place to compute these — matches the existing `get_trend_baseline` pipeline pattern already in `price_service.py`, never pulled into Python and computed client-side |
| Detail response assembly (field shape, insufficient-data branching) | API/Backend | — | `catalog_service.get_product_detail()` already owns this exact responsibility for `trend_7d`/`trend_30d`; the two new fields extend the same function, not a new one |
| Badge rendering (four-state visual convention) | Browser/Client | — | `TrendBadge` (React, pure formatter over API-computed `{pct_change, status}`) already owns this for 7d/30d; 24h reuses it unchanged. The all-time range needs a new small component since its data shape (two absolute $ values, not a signed %) doesn't fit `TrendBadge`'s props |
| Zero-data / insufficient-data guard | API/Backend | Browser/Client | Backend must never omit a field or send a fabricated value (`get_product_detail`'s existing `current_price is None` early-return branch); frontend must never crash on a `null`/`insufficient_data` shape (both `TrendBadge` and the new component branch on `status` first) |

## Standard Stack

No new packages are required for this phase. Every capability is implemented with libraries already installed and in use by the existing, working Phase 5/8 code this phase extends.

### Core (already installed — confirmed by reading the project's own manifest files this session)
| Library | Version | Purpose | Source |
|---------|---------|---------|--------|
| PyMongo | 4.17.0 | `$min`/`$max` aggregation over `price_points` for the all-time range | `[VERIFIED: requirements.txt]` |
| Flask | 3.1.3 | Existing `GET /products/<id>` route, unchanged path/method | `[VERIFIED: requirements.txt]` |
| pytest | 8.4.2 | Backend unit/contract tests | `[VERIFIED: requirements.txt]` |
| React | 19.2.7 | `TrendBadge` reuse + new small component | `[VERIFIED: frontend/package.json]` |
| Vitest | 4.1.10 | Frontend component tests | `[VERIFIED: frontend/package.json]` |

### Supporting
None new. `react-router` 7.18.1 and `recharts` 3.10.1 are already installed (from Phase 8) but this phase touches neither routing nor charting — badges are plain text/number UI per STATE.md's carried-forward note. `[VERIFIED: .planning/STATE.md:136]`

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Extending the existing `GET /products/<id>` response | A new `GET /products/<id>/all-time-range` endpoint (mirroring Phase 8's separate `/history` endpoint) | Phase 8's separate endpoint existed specifically because the payload was a *raw series* that would violate the detail response's standing "never returns a raw price_points array" contract (D-11). `trend_24h` and `all_time_range` are both small aggregate objects (not series) — the same category as the existing `trend_7d`/`trend_30d`, which already live on the detail response. A new endpoint here would be an unjustified architectural inconsistency and directly contradicts the phase's own stated sequencing rationale (`.planning/ROADMAP.md:80`). |
| `price_service.get_trend_baseline(days=1, ...)` reused for 24h | A dedicated `get_24h_baseline` function | Reuse is correct: the function is already generic over `days`/`tolerance_days` and is pure/stateless. A dedicated function would duplicate the aggregation pipeline for zero benefit. |
| MongoDB `$min`/`$max` aggregation for all-time range | Fetch the full series (`get_price_history`) and compute `min()`/`max()` in Python | Both work at current data volume (~6 pts/day/product). The aggregation is the standard idiom already used for `get_trend_baseline` in this codebase and avoids pulling an unbounded array into application memory as history accumulates — matches the "don't hand-roll" principle below. |

**Installation:** None — no new packages this phase.

## Package Legitimacy Audit

**Not applicable — this phase installs zero external packages.** All work extends `api/services/price_service.py`, `api/services/catalog_service.py`, `frontend/src/pages/ProductDetailPage.jsx`, and `frontend/src/components/TrendBadge.jsx` (reused as-is) plus one new frontend component, all using dependencies already present in `requirements.txt` / `frontend/package.json` (confirmed above). No `npm install` / `pip install` step belongs in this phase's plan.

## Architecture Patterns

### System Architecture Diagram

```
Browser (ProductDetailPage.jsx)
   │
   │  useLoaderData() — same loader as today, no new fetch
   ▼
GET /products/<product_id>            (api/blueprints/products.py — UNCHANGED route)
   │
   ▼
catalog_service.get_product_detail(db, product_id)   [EXTENDED]
   │
   ├─ current_price ─────────► price_service.get_current_price()        (unchanged)
   ├─ trend_7d, trend_30d ───► price_service.get_trend_baseline(days=7|30, tolerance_days=3)  (unchanged)
   ├─ trend_24h ─────────────► price_service.get_trend_baseline(days=1, tolerance_days=<NEW>) [NEW CALL]
   └─ all_time_range ────────► price_service.get_all_time_range(db, product_id)               [NEW FUNCTION]
                                    │
                                    ▼
                              db.price_points.aggregate([
                                {$match: {product_id}},
                                {$group: {_id: None, high: {$max: "$total_price"}, low: {$min: "$total_price"}}}
                              ])
   │
   ▼  jsonify(detail)  — same envelope shape, two new keys
Browser renders:
   ├─ <TrendBadge trend={trend_7d}/>   (existing)
   ├─ <TrendBadge trend={trend_30d}/>  (existing)
   ├─ <TrendBadge trend={trend_24h}/>  [NEW — same component, no new props needed]
   └─ <AllTimeRangeBadge range={all_time_range}/>  [NEW COMPONENT — different shape: two $ values, not a %]
```

A reader can trace: request → `get_product_detail` → two price_service calls (one reused-with-new-args, one brand new) → one Mongo aggregation each → JSON → three `TrendBadge` renders + one new badge render, no branch of that path introduces a network hop, endpoint, or package that doesn't already exist in the codebase today.

### Recommended Project Structure
```
api/
├── services/
│   ├── price_service.py       # ADD: get_all_time_range(); ADD: a TREND_24H_TOLERANCE_HOURS-style constant
│   └── catalog_service.py     # EXTEND: get_product_detail() adds trend_24h + all_time_range
frontend/src/
├── components/
│   ├── TrendBadge.jsx          # REUSED UNCHANGED for trend_24h
│   ├── AllTimeRangeBadge.jsx   # NEW — mirrors TrendBadge's "branch on status first" pattern
│   ├── AllTimeRangeBadge.module.css   # NEW — mirrors TrendBadge.module.css token usage
│   └── AllTimeRangeBadge.test.jsx     # NEW — mirrors TrendBadge.test.jsx's 2-state coverage (ok/insufficient_data — no up/down/flat here)
└── pages/
    └── ProductDetailPage.jsx   # EXTEND: render 3rd TrendBadge + new AllTimeRangeBadge
tests/
├── test_price_service.py       # EXTEND: get_all_time_range cases + 24h tolerance case
├── test_catalog_service.py     # EXTEND: trend_24h + all_time_range field assertions
└── test_api_products.py        # EXTEND: JSON contract assertions for the two new keys
```

### Pattern 1: 24h badge — reuse `get_trend_baseline` with an explicit, non-default tolerance

**What:** Call the existing generic function with `days=1` and a **new, explicitly-defined tolerance** rather than the module default.
**When to use:** Any time-window badge whose window is short relative to `TREND_TOLERANCE_DAYS` (3 days) — the 3-day default was sized for 7d/30d windows (43% and 10% relative tolerance respectively) and is meaningless for a 1-day window.
**Why a new tolerance, not the default — grounded reasoning:** The ingestion worker's default poll interval is 4 hours (`INGESTION_INTERVAL_HOURS` env var, default `"4"`) — `[VERIFIED: scripts/ingest_worker.py:523]` (`interval_hours = int(os.environ.get("INGESTION_INTERVAL_HOURS", "4"))`), matching `price_service.py`'s own docstring note of "roughly 6 points per day per product" `[VERIFIED: api/services/price_service.py:99]`. A tolerance of **±4 hours** (one full ingestion interval) is recommended: wide enough that one delayed/missed run doesn't spuriously flip the badge to insufficient-data, narrow enough that the badge still means "about a day ago" (a 17% relative tolerance — tighter than the existing 7d badge's 43%). This is a derived recommendation, not sourced from any doc — `[ASSUMED]`, and listed in Open Questions below for explicit confirmation at plan/discuss time.

```python
# Source: existing api/services/price_service.py:122-159 signature, called with new args
# (function body unchanged — only the call site and a new constant are added)

TREND_24H_TOLERANCE_HOURS = 4  # NEW constant — do not reuse TREND_TOLERANCE_DAYS (=3 days) for this window

# in catalog_service.get_product_detail, alongside the existing 7d/30d loop:
baseline_24h = get_trend_baseline(
    db, product_id, current_ts, days=1,
    tolerance_days=TREND_24H_TOLERANCE_HOURS / 24,  # timedelta(days=...) accepts a float
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

This is the exact same three-way branch (`None` baseline → insufficient / `compute_pct_change` returns `None` on zero-baseline → insufficient / else → `ok`) already used for `trend_7d`/`trend_30d` in `get_product_detail` — `[VERIFIED: api/services/catalog_service.py:181-193]`, quoted:
```
for days in TREND_WINDOWS:
    key = trend_key_by_days[days]
    baseline = get_trend_baseline(db, product_id, current_ts, days)
    if baseline is None:
        detail[key] = {"pct_change": None, "status": "insufficient_data"}
        continue
    pct = compute_pct_change(current_total, baseline["total_price"])
    if pct is None:
        detail[key] = {"pct_change": None, "status": "insufficient_data"}
    else:
        detail[key] = {"pct_change": pct, "status": "ok"}
```
Do not fold `trend_24h` into the `TREND_WINDOWS = (7, 30)` loop unchanged — that loop calls `get_trend_baseline` with its default `tolerance_days` (3), which is exactly the nonsensical case this pattern exists to avoid.

### Pattern 2: All-time high/low — new MongoDB `$min`/`$max` aggregation function

**What:** A new pure `price_service` function returning the all-time high/low `total_price` across every stored point for a product, following the existing "pure function, db-as-arg, no top-level side effects" convention `[VERIFIED: api/services/price_service.py:5-10]`.
**When to use:** Once per detail-page render, called from `get_product_detail` exactly like `get_current_price`/`get_trend_baseline` are today.

```python
# Source: pattern mirrors the existing aggregation idiom in
# api/services/price_service.py:147-159 (get_trend_baseline's pipeline)

def get_all_time_range(db, product_id):
    """Return {"high": float, "low": float} — the max/min total_price
    ever recorded for product_id — or None if the product has zero
    price_points documents ever (mirrors get_current_price's D-01
    None-on-zero-points contract, NOT get_trend_baseline's tolerance-
    window contract: any single point, however old, makes this "ok",
    since there is no target date to miss)."""
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

```python
# in catalog_service.get_product_detail:
all_time = get_all_time_range(db, product_id)
detail["all_time_range"] = (
    {"high": None, "low": None, "status": "insufficient_data"} if all_time is None
    else {"high": all_time["high"], "low": all_time["low"], "status": "ok"}
)
```

**Key semantic difference from the trend badges, and why it matters for the "insufficient data" branching:** `get_trend_baseline` returns `None` when nothing falls in a *tolerance window around a target date* — that's a "no point near enough" case. `get_all_time_range` has no target date; it only needs *any* point at all. So a product with exactly **one** collected price point is a legitimate `"ok"` all-time-range (`high == low == that one price`) — this is real data, not a fabricated range, and must not be miscategorized as `insufficient_data`. Only **zero** points (mirrors `get_current_price`'s D-01 contract `[VERIFIED: api/services/price_service.py:37-57]`) is `insufficient_data`.

### Frontend Pattern: new `AllTimeRangeBadge` component (not `TrendBadge` reuse)

`TrendBadge`'s props/rendering are shaped around a signed percent with an up/down/flat/insufficient four-state convention — `[VERIFIED: frontend/src/components/TrendBadge.jsx:1-42]`, quoted: `if (!trend || trend.status === 'insufficient_data' || typeof trend.pct_change !== 'number')`. `all_time_range` is a **different data shape** (`{high, low, status}`, two absolute dollar values, no sign/direction), so it needs its own small component — but should mirror `TrendBadge`'s exact branch-on-`status`-first discipline and CSS-module/token conventions (`--text-disabled`/`--trend-insufficient` for the muted state, `formatCurrency`-style `$X.XX` formatting matching `PriceDisplay.jsx`'s `formatCurrency` — `[VERIFIED: frontend/src/components/PriceDisplay.jsx:3-5]`, quoted: `function formatCurrency(value) { return typeof value === 'number' ? \`$${value.toFixed(2)}\` : '—' }`).

```jsx
// New component, pattern mirrors frontend/src/components/TrendBadge.jsx's
// status-first branching and frontend/src/components/PriceDisplay.jsx's
// formatCurrency convention (both read this session)
import styles from './AllTimeRangeBadge.module.css'

function formatCurrency(value) {
  return typeof value === 'number' ? `$${value.toFixed(2)}` : '—'
}

export default function AllTimeRangeBadge({ range }) {
  if (!range || range.status === 'insufficient_data') {
    return (
      <span className={`${styles.range} ${styles['range--muted']}`} aria-label="insufficient data">
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

Success criterion 2 requires the range be **labeled** "since we started tracking" — this label belongs in `ProductDetailPage.jsx`'s JSX (a heading/caption next to the badge, e.g. `<span className={styles.sectionCaption}>All-time range (since we started tracking)</span>`), not inside the badge component itself — mirrors how `FreshnessIndicator` and the existing trend labels (`<span className={styles.trendLabel}>7d</span>`) are separate from their value components. `[VERIFIED: frontend/src/pages/ProductDetailPage.jsx:140-149]`

### Anti-Patterns to Avoid
- **A new endpoint for `all_time_range` or `trend_24h`:** Both are small aggregate objects, the same category the detail response already carries (`trend_7d`/`trend_30d`) — a new endpoint here is an unjustified inconsistency and contradicts the phase's own stated single-surface rationale (`.planning/ROADMAP.md:80`).
- **Reusing `TREND_TOLERANCE_DAYS = 3` (or the default-tolerance `get_trend_baseline` call) for the 24h window:** produces a meaningless ±3-day window around a 1-day target — flagged explicitly in `.planning/STATE.md:134` as something Phase 9 "must pick and record an explicit tolerance for... rather than reusing the default." `[VERIFIED: .planning/STATE.md:134]`
- **Computing all-time high/low by fetching `get_price_history`'s full array and reducing in Python:** works today at ~6 pts/day/product but reintroduces the exact unbounded-array-into-memory pattern `get_price_history`'s own docstring flags as a deliberate, revisit-triggered tradeoff `[VERIFIED: api/services/price_service.py:97-107]` — the aggregation pipeline avoids it for free and is the established idiom in this file.
- **Treating a single-point product's all-time range as `insufficient_data`:** it is real, non-fabricated data (`high == low`) — only zero points is insufficient, per Pattern 2 above.
- **Forgetting to extend the existing zero-data early-return branch:** `get_product_detail`'s `if detail["current_price"] is None:` branch currently only sets `trend_7d`/`trend_30d` to insufficient-data before returning early — `[VERIFIED: api/services/catalog_service.py:170-175]`, quoted: `detail["trend_7d"] = {"pct_change": None, "status": "insufficient_data"}` / `detail["trend_30d"] = {"pct_change": None, "status": "insufficient_data"}`. This branch **must** be extended to also set `trend_24h` and `all_time_range` to their insufficient-data shapes before the early `return detail` — otherwise a zero-data product's response is missing two keys entirely, which is exactly the "silently missing badge" failure success criterion 4 explicitly forbids.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|--------------|-----|
| All-time min/max over a product's price series | A Python loop/`min()`/`max()` over a fetched list of documents | MongoDB `$group` with `$max`/`$min` (Pattern 2 above) | Already the established idiom in this file (`get_trend_baseline`'s pipeline); avoids pulling an unbounded series into application memory as history accumulates, matching the documented revisit-trigger discipline already in `get_price_history`'s docstring |
| A "near this target date" lookup for the 24h badge | A new hand-rolled nearest-timestamp query | The existing `get_trend_baseline(days, tolerance_days)` function, called with new args | It is already generic over both parameters; a second copy of the same aggregation pipeline for a different `days` value is pure duplication |

**Key insight:** Every new computation this phase needs already has a near-identical, working precedent in `price_service.py` from Phase 5/8. The research risk here isn't "what library/pattern to use" — it's "don't accidentally reuse a parameter default (`TREND_TOLERANCE_DAYS=3`) that was correctly sized for a different window and is wrong for this one."

## Common Pitfalls

### Pitfall 1: Reusing the default 3-day tolerance for the 24h window
**What goes wrong:** The 24h badge almost never shows `insufficient_data` (defeating success criterion 3) because a ±3-day window around "1 day ago" matches nearly any point in a young product's short history, and can badge a point that's actually 3-4 days old as "24h change."
**Why it happens:** `get_trend_baseline`'s `tolerance_days` parameter defaults to the module constant; it's easy to call `get_trend_baseline(db, product_id, current_ts, days=1)` without overriding the default.
**How to avoid:** Always pass an explicit `tolerance_days` override for the 24h call (Pattern 1 above); never rely on the default for this window.
**Warning signs:** A test asserting `insufficient_data` for a product whose only point is 4 days old, at `days=1`, would fail if the default tolerance were used — this is exactly the test case to write to pin the fix.

### Pitfall 2: Zero-data early-return branch not extended
**What goes wrong:** A product with zero price points returns a detail dict missing `trend_24h`/`all_time_range` keys entirely (the existing early-return only sets `trend_7d`/`trend_30d`), which the frontend then either crashes on (`undefined.status`) or silently omits — both explicitly forbidden by success criterion 4.
**Why it happens:** The early-return branch (`if detail["current_price"] is None: ... return detail`) is easy to miss when adding new fields lower in the function, since the two new fields are otherwise computed after this branch alongside `trend_7d`/`trend_30d`.
**How to avoid:** Add both new insufficient-data shapes to the early-return branch, not just the post-branch computation path (see Anti-Patterns above for the exact quote/location).
**Warning signs:** A test creating a product with zero `price_points` documents and asserting `"trend_24h" in detail and "all_time_range" in detail` — this is exactly the regression `test_detail_no_data_yet`-style tests already pin for `trend_7d`/`trend_30d` `[VERIFIED: tests/test_catalog_service.py:164-178]`.

### Pitfall 3: Single-point product miscategorized as insufficient-data for all-time range
**What goes wrong:** A brand-new product with exactly one ingested price point gets `all_time_range: {status: "insufficient_data"}` even though `high == low == that real price` is legitimate, non-fabricated data — violating the "never a silently missing badge" spirit even though this specific case isn't literally in the success criteria's zero-data/24h-data wording.
**Why it happens:** Copy-pasting the `get_trend_baseline`-style "None baseline → insufficient_data" pattern without recognizing that `get_all_time_range` has no target-date/tolerance concept — any non-zero point count is valid.
**How to avoid:** `get_all_time_range` returns `None` only for zero points (mirrors `get_current_price`'s D-01 contract), never for "not enough spread."
**Warning signs:** A test inserting exactly one `price_points` document and asserting `all_time_range["status"] == "ok"` and `all_time_range["high"] == all_time_range["low"]`.

### Pitfall 4: D-11 violation — leaking a raw series through the new fields
**What goes wrong:** `all_time_range` accidentally becomes (or later gets "enhanced" to include) a list of the high/low points with their timestamps, re-violating the standing detail-response contract that no raw `price_points`-shaped array is ever returned.
**Why it happens:** A natural follow-up impulse ("wouldn't it be nice to show *when* the high/low happened") that would require returning point objects rather than two scalars.
**How to avoid:** Keep `all_time_range` as exactly `{high: float|None, low: float|None, status: str}` — two scalars and a status string, nothing list-shaped. If timestamps for the high/low are wanted later, that's a new, explicitly-scoped decision (this phase's success criteria only require the two prices).
**Warning signs:** `test_detail_omits_raw_series`'s existing generic check (`isinstance(value, list) and ... "ts" in value[0]` — `[VERIFIED: tests/test_catalog_service.py:189-225]`) already covers this defensively for any new key added to the detail dict, but should be re-run/extended explicitly against `all_time_range` and `trend_24h`.

## Code Examples

### Extending `TREND_WINDOWS`-style loop without breaking it
```python
# Source: mirrors existing api/services/catalog_service.py:181-193 loop,
# extended with a sibling explicit call (not folded into the loop, per
# Pitfall 1 above)
TREND_WINDOWS = (7, 30)  # UNCHANGED — do not add 1 here
TREND_24H_TOLERANCE_HOURS = 4  # NEW

trend_key_by_days = {7: "trend_7d", 30: "trend_30d"}
for days in TREND_WINDOWS:
    # ... existing loop body, unchanged ...
    pass

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

### Frontend: adding the third `TrendBadge` (no new component work needed for this one)
```jsx
// Source: mirrors existing frontend/src/pages/ProductDetailPage.jsx:140-149
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
```

## State of the Art

Not applicable — this is an in-repo pattern extension, not an evolving external ecosystem. No library upgrades, no deprecated APIs involved.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Recommended 24h tolerance is ±4 hours (one ingestion interval) | Pattern 1 / Common Pitfalls 1 | If too tight, real 24h-ago data ~4-8h off cadence spuriously shows insufficient-data; if too loose, the badge silently blurs into "up to N hours ago" data being labeled "24h" — either way it's a tuning error, not a correctness error, and is trivially adjustable via one constant |
| A2 | `all_time_range` is a single combined field `{high, low, status}` rather than two independent `all_time_high`/`all_time_low` fields | Pattern 2 / Frontend Pattern | Low risk — success criterion 2 describes them as a paired "range," and reshaping a JSON response before any external consumer depends on it is a trivial, cheap change (unlike Phase 8's D-04 endpoint-shape decision, which was explicitly costly to reverse) |
| A3 | A brand-new `AllTimeRangeBadge` component is needed rather than reusing `TrendBadge` | Frontend Pattern | Low risk — `TrendBadge`'s props/branching are built around a signed percent, not two absolute prices; forcing reuse would require overloading its prop shape, which is a worse outcome than one small new ~15-line component following the identical pattern |

**No claim above is HIGH-risk-if-wrong** — none touch data correctness, security, or an irreversible API shape; all are UI/tuning decisions the planner or a `checkpoint:human-verify` can confirm cheaply.

## Open Questions

1. **Exact 24h tolerance value**
   - What we know: the default 3-day tolerance is wrong; ingestion runs every 4h by default (verified in code)
   - What's unclear: whether ±4h is the right choice vs. e.g. ±2h (tighter, more "real-time" feeling) or ±6h (more forgiving of a missed run)
   - Recommendation: use ±4h (Pattern 1) as the starting value; this is cheap to tune later since it's one constant, not an API shape

2. **All-time range field naming and shape** (`all_time_range: {high, low, status}` vs. two top-level fields)
   - What we know: success criterion 2 treats high/low as a paired concept ("the range")
   - What's unclear: no CONTEXT.md exists for this phase (discuss-phase was skipped) to lock this choice
   - Recommendation: use the single combined-object shape (A2 above); flag for `checkpoint:human-verify` or planner confirmation only if the UI-SPEC step (see below) surfaces a strong reason to split it

3. **UI-SPEC generation**
   - What we know: `.planning/config.json`'s `workflow.ui_phase` is `true` and this phase's roadmap entry carries `UI hint: yes` — `[VERIFIED: .planning/config.json:28]` / `[VERIFIED: .planning/ROADMAP.md:90]`, so a dedicated UI-SPEC step is expected to run before/alongside planning
   - What's unclear: exact placement/copy for the "since we started tracking" label and the new badge's visual treatment relative to the existing trend row
   - Recommendation: the UI-SPEC step should reuse the existing design tokens (`--trend-insufficient`, `--text-secondary`, spacing scale — all in `frontend/src/styles/tokens.css`, read this session) rather than introduce new ones

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework (backend) | pytest 8.4.2 — `[VERIFIED: requirements.txt]`, config `pytest.ini` (`pythonpath = .`, `testpaths = tests`) `[VERIFIED: pytest.ini]` |
| Framework (frontend) | Vitest 4.1.10 + @testing-library/react 16.3.2 — `[VERIFIED: frontend/package.json]` |
| Quick run command (backend) | `pytest tests/test_price_service.py tests/test_catalog_service.py -x` |
| Quick run command (frontend) | `npm run test -- ProductDetailPage TrendBadge AllTimeRangeBadge` (vitest run, filtered) |
| Full suite command (backend) | `pytest` |
| Full suite command (frontend) | `npm run test` (`vitest run` per `[VERIFIED: frontend/package.json]`) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|--------------------|-------------|
| PRICE-08 | `get_trend_baseline(days=1, tolerance_days=<new>)` returns a point within ±4h, `None` otherwise | unit | `pytest tests/test_price_service.py -x` | ✅ (extend `tests/test_price_service.py`) |
| PRICE-08 | `get_product_detail` sets `trend_24h` to `{pct_change, status:"ok"}` when a 24h-ago point exists, `insufficient_data` otherwise, including in the zero-data early-return branch | unit | `pytest tests/test_catalog_service.py -x` | ✅ (extend `tests/test_catalog_service.py`) |
| PRICE-08 | `GET /products/<id>` JSON response includes `trend_24h` with the correct shape and status | integration | `pytest tests/test_api_products.py -x` | ✅ (extend `tests/test_api_products.py`) |
| PRICE-08 | `ProductDetailPage` renders a third `TrendBadge` for 24h next to 7d/30d | component | `npm run test -- ProductDetailPage` | ✅ (extend `frontend/src/pages/ProductDetailPage.test.jsx`) |
| PRICE-09 | `get_all_time_range` returns `None` for zero points, `{high, low}` for 1+ points (including the `high==low` single-point case) | unit | `pytest tests/test_price_service.py -x` | ✅ (extend `tests/test_price_service.py`) |
| PRICE-09 | `get_product_detail` sets `all_time_range` correctly including the zero-data early-return branch, and never leaks a raw series (D-11) | unit | `pytest tests/test_catalog_service.py -x` | ✅ (extend `tests/test_catalog_service.py`, reuse `test_detail_omits_raw_series`-style assertion) |
| PRICE-09 | `GET /products/<id>` JSON response includes `all_time_range` with the correct shape | integration | `pytest tests/test_api_products.py -x` | ✅ (extend `tests/test_api_products.py`) |
| PRICE-09 | `ProductDetailPage` renders the new `AllTimeRangeBadge` with its "since we started tracking" label, including the insufficient-data (—) case | component | `npm run test -- ProductDetailPage AllTimeRangeBadge` | ❌ Wave 0 — new `AllTimeRangeBadge.test.jsx` |

### Sampling Rate
- **Per task commit:** `pytest tests/test_price_service.py tests/test_catalog_service.py -x` (backend) and `npm run test -- ProductDetailPage TrendBadge AllTimeRangeBadge` (frontend), whichever side the task touched
- **Per wave merge:** `pytest` (full backend suite) and `npm run test` (full frontend suite)
- **Phase gate:** Full suite green (both) before `/gsd-verify-work`; CI already runs the full pytest suite against a real `mongo:7` service container on every PR/push `[VERIFIED: .planning/STATE.md:137]`

### Wave 0 Gaps
- [ ] `frontend/src/components/AllTimeRangeBadge.test.jsx` — new file, covers PRICE-09 (ok/insufficient_data states, no up/down/flat since this isn't a signed-percent badge)
- [ ] `frontend/src/components/AllTimeRangeBadge.module.css` — new file, needed before the component test can assert class names
- No new backend test *files* needed — `tests/test_price_service.py`, `tests/test_catalog_service.py`, and `tests/test_api_products.py` all already exist and already establish the exact conventions (deferred imports, `api_db` fixture, D-11 raw-series guard) this phase's new cases extend.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | This app has no auth/session system anywhere (public read-only catalog API) — unchanged by this phase |
| V3 Session Management | no | Same as above |
| V4 Access Control | no | No new access-controlled resource; `product_id` path param already validated by the existing route (404 on unknown id, unchanged) |
| V5 Input Validation | yes | No new input surface — this phase adds zero new query params/path params/request bodies. The only "input" is the already-validated `product_id` path segment consumed by the existing, unmodified route |
| V6 Cryptography | no | No secrets, tokens, or crypto touched by this phase |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Information disclosure via a new response field | Information Disclosure | `all_time_range`/`trend_24h` expose only aggregate numbers already implied by the existing public `trend_7d`/`trend_30d`/`current_price` fields on the same public, unauthenticated endpoint — no new disclosure category, same trust boundary already documented in `08-SECURITY.md`'s trust-boundary table (`browser → Flask API`, `Flask API → MongoDB`) `[VERIFIED: .planning/phases/08-price-history-chart/08-SECURITY.md:19-25]` |
| Tampering via a malformed aggregation pipeline | Tampering | `product_id` is bound as a plain value in an equality `$match` filter (`{"product_id": product_id}`), never interpolated into a query operator or pipeline stage string — identical, already-verified pattern used by `get_trend_baseline`'s existing pipeline `[VERIFIED: api/services/price_service.py:147-159]` |
| Denial of service via unbounded aggregation cost | Denial of Service | `$min`/`$max` aggregation is O(n) over one product's points at ~6 pts/day/product — negligible at current/expected v1.1 volume; same accepted-risk class already logged as `AR-08-01`/`AR-08-03` for the sibling history endpoint `[VERIFIED: .planning/phases/08-price-history-chart/08-SECURITY.md:55-57]` |

No new trust boundary is introduced by this phase (no new route, no new npm/pip package, no new external I/O) — the existing `browser → Flask API` and `Flask API → MongoDB` boundaries documented for Phase 8 cover this phase's data flow unchanged.

## Sources

### Primary (HIGH confidence — in-repo, read directly this session)
- `api/services/price_service.py` — existing `get_trend_baseline`, `get_current_price`, `compute_pct_change`, module docstring's ingestion-cadence note
- `api/services/catalog_service.py` — existing `get_product_detail`, `TREND_WINDOWS`, zero-data early-return branch
- `api/blueprints/products.py` — existing route structure (confirms no route change needed)
- `frontend/src/pages/ProductDetailPage.jsx` / `.module.css` — existing trend-section layout
- `frontend/src/components/TrendBadge.jsx` / `.module.css` / `.test.jsx` — four-state pattern to reuse for 24h and mirror for the new component
- `frontend/src/components/PriceDisplay.jsx` — `formatCurrency` convention
- `frontend/src/styles/tokens.css` — design tokens (`--trend-insufficient`, spacing scale, typography) for the new badge
- `tests/test_price_service.py`, `tests/test_catalog_service.py`, `tests/test_api_products.py` — existing test conventions (`api_db` fixture, deferred imports, D-11 raw-series guard)
- `scripts/ingest_worker.py:523` — `INGESTION_INTERVAL_HOURS` default of 4 hours, grounding the recommended 24h tolerance
- `db/init_collections.py` — `price_points` time-series collection options (`timeField: ts`, `metaField: product_id`, `granularity: hours`)
- `.planning/ROADMAP.md`, `.planning/STATE.md`, `.planning/REQUIREMENTS.md`, `.planning/config.json` — phase scope, carried-forward context (the explicit 24h-tolerance flag), requirement text, workflow toggles
- `.planning/phases/08-price-history-chart/08-CONTEXT.md`, `08-SECURITY.md` — sibling-phase decisions (D-04/D-06/D-11) and threat-register precedent this phase must stay consistent with

### Secondary / Tertiary
None used — this phase required no external documentation or web research; every fact needed is already verified in this codebase's own source and planning artifacts.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new dependencies, all versions confirmed by reading the project's own manifest files this session
- Architecture: HIGH — every pattern is a direct extension of already-working, already-tested code read in full this session
- Pitfalls: HIGH for correctness pitfalls (grounded in code read this session); MEDIUM for the exact 24h tolerance value (a tuning recommendation, explicitly flagged as `[ASSUMED]` in the Assumptions Log)

**Research date:** 2026-08-20
**Valid until:** No external-ecosystem expiry risk (no new packages); revisit only if the ingestion interval (`INGESTION_INTERVAL_HOURS`) changes, which would invalidate the ±4h tolerance recommendation
