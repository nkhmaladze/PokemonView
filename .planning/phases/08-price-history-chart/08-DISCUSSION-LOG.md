# Phase 8: Price History Chart - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-18
**Phase:** 8-Price History Chart
**Areas discussed:** Chart visual style, Loading behavior, Insufficient-history state

---

## Chart visual style

| Option | Description | Selected |
|--------|-------------|----------|
| Full chart | Visible X-axis (dates), Y-axis ($ price), light gridlines — like poe.ninja's item graphs | ✓ |
| Minimal sparkline | Just the line, no axes/gridlines, price shown via tooltip only | |

**User's choice:** Full chart
**Notes:** Explicitly tied to poe.ninja as the visual reference — PROJECT.md's own stated direct inspiration for the whole product.

| Option | Description | Selected |
|--------|-------------|----------|
| Always full history | Simplest, matches "raw series, no downsampling" decision. Little to filter yet with ~2-3 weeks of data. | ✓ |
| Range selector (7d/30d/All) | More UI work now, sets up for future data volume | |

**User's choice:** Always full history
**Notes:** Deferred a range selector as future scope once more data accumulates.

| Option | Description | Selected |
|--------|-------------|----------|
| Section heading | e.g. "Price History" above the chart, matches existing sectioned page layout | ✓ |
| No heading | Chart sits directly below trend badges with no label | |

**User's choice:** Section heading

---

## Loading behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Bundle into one loader | Page renders once, fully populated | |
| Separate fetch, chart loads after | Price/badges appear first, chart fills in after a second request | ✓ |

**User's choice:** Separate fetch, chart loads after

| Option | Description | Selected |
|--------|-------------|----------|
| New field on existing response | catalog_service.get_product_detail gains a price_history field | ✓ (initial) |
| Separate endpoint | GET /products/<id>/history stays independent | |

**User's choice (initial):** New field on existing response — this conflicted with the "separate fetch" answer above (a bundled response can't resolve separately), so a reconciliation question was asked.

**Reconciliation:**

| Option | Description | Selected |
|--------|-------------|----------|
| Separate endpoint + separate fetch | GET /products/<id>/history as its own endpoint, called by an independent second fetch — true progressive loading | ✓ |
| One bundled response, rendered progressively | history stays a field on the existing response; only the React rendering is staged, not the network request | |

**User's choice:** Separate endpoint + separate fetch
**Notes:** The user's two initial answers pointed in different directions (bundled payload vs. separate-fetch loading). Surfaced the contradiction directly rather than guessing; the user resolved it toward genuine network-level progressive loading via a dedicated new endpoint. Consequence: `catalog_service.get_product_detail`'s existing D-11 decision ("never returns a raw price_points series") stays true and unmodified — the new capability lives entirely in a new function/route.

---

## Insufficient-history state

| Option | Description | Selected |
|--------|-------------|----------|
| 2 points minimum | A line technically needs 2 points; show it as soon as available | ✓ |
| Higher threshold (5+ points) | Wait for a more meaningful shape; a 2-point line can look like a misleading trend | |

**User's choice:** 2 points minimum

| Option | Description | Selected |
|--------|-------------|----------|
| "Not enough price history yet" | Plain, matches the roadmap's own wording | ✓ |
| More specific ("Check back after a few more price updates") | Sets expectation that data is actively accumulating | |

**User's choice:** "Not enough price history yet"

---

## Claude's Discretion

- Exact new endpoint path/naming conventions (`api/blueprints/products.py`)
- Exact new service function name/module placement (`price_service.py` convention)
- Response JSON field naming for the history endpoint (default to existing `price_points` document shape)
- Recharts component composition (`LineChart`/`XAxis`/`YAxis`/`Tooltip`/`CartesianGrid`)
- Frontend loading-state UI for the progressive chart fetch (skeleton/spinner/blank-then-fill)

## Deferred Ideas

- Time-range selector (7d/30d/All) on the chart — revisit once more data has accumulated
- Catalog-page sparklines — already tracked as REQUIREMENTS.md PRICE-10 (v2)
- Item-price/total-price toggle on the chart — already tracked as REQUIREMENTS.md PRICE-11 (v2)
