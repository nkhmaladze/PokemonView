# Roadmap: PokemonView

## Overview

v1.0 built PokemonView bottom-up in horizontal technical layers (eBay feasibility → catalog/data model → ingestion → matching → API → SPA → launch) and shipped a live, active-price product on 2026-08-02. The sold-price half of the original thesis is permanently parked — Marketplace Insights API access was denied twice.

v1.1 is a scoped feature addition on top of that shipped product, not a new subsystem. All the data it needs already exists: the `price_points` native time-series collection has been accumulating item/total price medians every ~4 hours per catalog product since Phase 4. What is missing is *exposure* — `catalog_service.get_product_detail` deliberately withholds the raw series (D-11) and only emits a current price plus 7d/30d trend badges. So v1.1 is deliberately structured as two thin vertical slices, each shipping a complete user-visible capability end-to-end (Mongo query → API field → React render) rather than splitting backend and frontend into separate phases: Phase 8 turns the accumulated series into a chart, Phase 9 turns it into two more badges.

## Milestones

- ✅ **v1.0 Active-Price MVP** — Phases 1-7 (shipped 2026-08-02)
- 🚧 **v1.1 Price History & Extended Badges** — Phases 8-9 (in progress, started 2026-08-18)
- ⏸️ **Sold-Price Integration** — parked indefinitely, not being pursued (see Parked section below)

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

<details>
<summary>✅ v1.0 Active-Price MVP (Phases 1-7) — SHIPPED 2026-08-02</summary>

- [x] Phase 1: eBay API Feasibility Gate (4/4 plans) — completed 2026-08-02
- [x] Phase 2: Product Catalog & Data Model (6/6 plans) — completed 2026-07-14
- [x] Phase 3: Active-Listing Ingestion Pipeline (5/5 plans) — completed 2026-07-18
- [x] Phase 4: Listing Matching & Price Normalization (5/5 plans) — completed 2026-07-15
- [x] Phase 5: Flask REST API (active-price serving) (7/7 plans) — completed 2026-07-15
- [x] Phase 6: React SPA Frontend (active-price product) (7/7 plans) — completed 2026-07-15
- [x] Phase 7: Launch & Hardening (v1 active-price) (5/5 plans) — completed 2026-07-15

Full phase details (goals, success criteria, plans): `.planning/milestones/v1.0-ROADMAP.md`

</details>

### 🚧 v1.1 Price History & Extended Badges (Phases 8-9)

- [x] **Phase 8: Price History Chart** - Detail page plots the full total-price series from `price_points`, served by a new history endpoint (completed 2026-08-20)
- [ ] **Phase 9: 24h & All-Time Price Badges** - Detail page adds a 24h change badge and an all-time high/low badge alongside the existing 7d/30d badges

### ⏸️ Parked (Not Being Pursued)

- [ ] **Sold-Price Integration** — real sold-price history and the active-vs-sold differentiators (INGEST-04, PRICE-04, PRICE-05, PRICE-06). Marketplace Insights API access was denied 2026-08-02 (ticket 260802-000004), and a subsequent reapplication as a registered business entity was denied as well, so no live reapplication path remains. PriceCharting (`FALLBACK-DECISION.md` Option 2) is a theoretical option only and is explicitly not being pursued. **This item was labeled "Phase 8" during v1.0 planning; that label is historical only and does NOT refer to Phase 8 below.** Full historical detail: `.planning/milestones/v1.0-ROADMAP.md` and `FALLBACK-DECISION.md`.

## Phase Details

### Phase 8: Price History Chart

**Goal**: A user can see how a product's asking price has moved over time on its detail page, instead of only its current snapshot.
**Depends on**: Nothing new — builds directly on the shipped v1.0 detail page and the `price_points` time-series collection that has been accumulating since Phase 4.
**Requirements**: PRICE-07
**Success Criteria** (what must be TRUE):

  1. A user opening a product's detail page sees a line chart of that product's total price over time, plotted from every price point collected for it (no downsampling, no binning — the raw series).
  2. A user can identify a specific point on the chart and read its date and total price (hover/tap tooltip), so the line is readable as data and not just a shape.
  3. A product with no collected history (or too few points to draw a line) shows an explicit "not enough history yet" message instead of an empty box, a broken axis, or a crash.
  4. Requesting the product's price-history endpoint directly returns that product's raw `price_points` series as time-ordered JSON — the chart reads a real API response and never recomputes or synthesizes the series client-side.

**Plans**: 4/4 plans executed

Plans:
**Wave 1**

- [x] 08-01-PLAN.md — Recharts supply-chain gate + end-to-end tracer: `get_price_history`, `GET /products/<id>/history`, `getPriceHistory`, `PriceHistoryChart`, and the detail page's progressive fetch (wave 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 08-02-PLAN.md — Backend edge and serialization coverage: empty/single/ordering/ISO-8601/product-isolation cases, unknown-id 200, CORS, D-06 regression guard (wave 2)
- [x] 08-03-PLAN.md — Chart component: exported timezone-pinned formatters, every input state covered, UI-SPEC typography and tooltip token contract (wave 2)
- [x] 08-04-PLAN.md — Detail page: first-paint ordering, loading/error containment, cancellation guard, section placement and accent-token documentation (wave 2)

**UI hint**: yes

### Phase 9: 24h & All-Time Price Badges

**Goal**: A user can judge a product's current price against both its most recent movement and its full recorded range, not just the 7d/30d windows.
**Depends on**: Phase 8 (both phases extend the same `ProductDetailPage` surface and the same detail-response contract; sequencing them avoids conflicting edits to the page and its tests). No data dependency — the badges read the same `price_points` collection directly.
**Requirements**: PRICE-08, PRICE-09
**Success Criteria** (what must be TRUE):

  1. A user sees a 24h change badge on the product detail page next to the existing 7d and 30d badges, using the same signed-percent, four-state (up / down / flat / insufficient-data) visual convention.
  2. A user sees the product's all-time high and all-time low total price, covering every point since data collection began, labeled so it is clear the range is "since we started tracking" rather than an absolute market record.
  3. A product with less than 24 hours of collected history shows the 24h badge in its explicit insufficient-data state (—), never a fabricated percentage and never a silently missing badge.
  4. A product with no price data at all still renders its detail page with every badge in the insufficient-data state — no crash, no blank page, no partially-rendered price section.

**Plans**: 5 plans

Plans:
**Wave 1**

- [ ] 09-01-PLAN.md — Tracer: 24h change badge end-to-end — `TREND_24H_TOLERANCE_HOURS`, `trend_24h` on both branches of `get_product_detail`, a third `TrendBadge` on the page, plus the tolerance-window edge tests (wave 1)
- [ ] 09-02-PLAN.md — New `AllTimeRangeBadge` component, its token-only stylesheet and its two-state test file (wave 1)

**Wave 2** *(blocked on Wave 1 completion)*

- [ ] 09-03-PLAN.md — `price_service.get_all_time_range` `$min`/`$max` aggregation and the `all_time_range` field on both branches of `get_product_detail` (wave 2)

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 09-04-PLAN.md — HTTP JSON contract for both new keys, catalog-wide badge-field completeness, and the Phase 9 D-11 raw-series regression guard (wave 3)
- [ ] 09-05-PLAN.md — Detail page: the all-time range section, its verbatim "since we started tracking" caption, locked placement, and the four-badge zero-data state (wave 3)

**UI hint**: yes

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|-----------------|--------|-----------|
| 1. eBay API Feasibility Gate | v1.0 | 4/4 | Complete | 2026-08-02 |
| 2. Product Catalog & Data Model | v1.0 | 6/6 | Complete | 2026-07-14 |
| 3. Active-Listing Ingestion Pipeline | v1.0 | 5/5 | Complete | 2026-07-18 |
| 4. Listing Matching & Price Normalization | v1.0 | 5/5 | Complete | 2026-07-15 |
| 5. Flask REST API (active-price serving) | v1.0 | 7/7 | Complete | 2026-07-15 |
| 6. React SPA Frontend (active-price product) | v1.0 | 7/7 | Complete | 2026-07-15 |
| 7. Launch & Hardening (v1 active-price) | v1.0 | 5/5 | Complete | 2026-07-15 |
| 8. Price History Chart | v1.1 | 4/4 | Complete    | 2026-08-20 |
| 9. 24h & All-Time Price Badges | v1.1 | 0/5 | Planned | - |

**Unnumbered / parked:** Sold-Price Integration (INGEST-04, PRICE-04/05/06) — parked indefinitely, MI API access denied twice. Carries no phase number; the "Phase 8" label it held during v1.0 planning is historical.
