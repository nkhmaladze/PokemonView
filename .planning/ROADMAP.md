# Roadmap: PokemonView

## Overview

PokemonView is built in horizontal technical layers, bottom-up: first de-risk the two hard eBay dependencies, then stand up the data model and curated catalog, then the ingestion pipeline, then matching/normalization, then the read API, then the React SPA — shipping a live, active-price product as v1. Because eBay's Marketplace Insights (sold-price) API is approval-gated and may never be granted, the roadmap is deliberately split: Phases 1-7 deliver and launch a complete Browse-API-only (active-listing) product that stands on its own, and the sold-price differentiators are isolated in a final, contingent phase that can be pulled forward if access lands early or deferred to a later milestone if it never does.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: eBay API Feasibility Gate** - De-risk sold-price API access and prove Browse API + OAuth before building
- [x] **Phase 2: Product Catalog & Data Model** - Curated v1 catalog and the shared MongoDB schema everything builds on (completed 2026-07-14)
- [x] **Phase 3: Active-Listing Ingestion Pipeline** - Scheduled, idempotent worker pulls active eBay listings via the Browse API (completed 2026-07-14)
- [ ] **Phase 4: Listing Matching & Price Normalization** - Map messy titles to catalog products and clean them into trustworthy prices
- [ ] **Phase 5: Flask REST API (active-price serving)** - Read-only API serves catalog, search, current price, freshness, and trend data
- [ ] **Phase 6: React SPA Frontend (active-price product)** - Users browse products and see whether one is priced fairly right now
- [ ] **Phase 7: Launch & Hardening (v1 active-price)** - Deploy, monitor for stale data, and take the active-price product live
- [ ] **Phase 8: Sold-Price Integration (contingent on MI API access)** - Add real sold-price history and active-vs-sold differentiators

## Phase Details

### Phase 1: eBay API Feasibility Gate

**Goal**: Resolve the two hard external unknowns — whether sold-price data will ever be available, and that active-price data plus OAuth actually work — before any layer is built on top of them.
**Depends on**: Nothing (first phase)
**Requirements**: None owned (feasibility/access gate that de-risks all later phases)
**Success Criteria** (what must be TRUE):

  1. An automated OAuth flow retrieves a valid Browse API token and a live test call returns real Pokemon sealed-product listings, including the item-price and shipping-cost fields.
  2. A Marketplace Insights API access request (Application Growth Check) has been submitted, with its status tracked and a decision-by date recorded.
  3. A documented fallback decision exists for the denied case: ship an active-only product as v1 and revisit sold-price in a later phase/milestone.
  4. 50-100 real eBay Pokemon sealed-product listing titles are captured as fixtures for building and testing matching rules.

**Plans**: 3/4 plans executed
**Wave 1**

- [x] 01-01-PLAN.md — Secret hygiene & Python project scaffolding (.gitignore, .env.example, requirements.txt)
- [x] 01-02-PLAN.md — Marketplace Insights access gate: manual steps, Growth Check narrative & fallback decision

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-03-PLAN.md — eBay OAuth + Browse API verification script (ebay_client.py, verify_ebay_access.py)

**Wave 3** *(blocked on Wave 2 completion)*

- [ ] 01-04-PLAN.md — Install dependencies & run live verification (package-legitimacy gate + 50-100 fixtures)

### Phase 2: Product Catalog & Data Model

**Goal**: A curated catalog of every v1 sealed product exists, persisted on the shared MongoDB data model that ingestion, matching, and pricing all depend on.
**Depends on**: Phase 1
**Requirements**: CATALOG-01, CATALOG-02
**Success Criteria** (what must be TRUE):

  1. The catalog contains every sealed English product (booster packs, booster boxes, ETBs) for the 2-3 most recent sets, each as a distinct canonical entry.
  2. Each catalog product carries canonical metadata — set, product type, and release info — usable by matching rules.
  3. The catalog is persisted in MongoDB and is queryable by set and product type, on a schema that reserves fields for both item-only and total (item + shipping) price points and time-series history.

**Plans**: 6/6 plans complete

**Wave 1** *(independent — env + data curation in parallel)*

- [x] 02-01-PLAN.md — Python dependencies (pymongo, pytest) with package-legitimacy gate
- [x] 02-02-PLAN.md — MongoDB instance provisioning (Atlas M0 or local) + MONGODB_URI
- [x] 02-03-PLAN.md — Curated catalog data module (scripts/catalog_data.py, 4 sets × product types)

**Wave 2** *(depends on Wave 1 env)*

- [x] 02-04-PLAN.md — MongoDB schema: products ($jsonSchema validator + index) & price_points (time-series)
- [x] 02-05-PLAN.md — Test scaffold: conftest fixture + 4 catalog contract tests (pytest.ini)

**Wave 3** *(depends on Wave 2)*

- [x] 02-06-PLAN.md — Idempotent seed script + run seed + full green test suite

### Phase 3: Active-Listing Ingestion Pipeline

**Goal**: A scheduled worker reliably and safely pulls active eBay listings into the store on a cadence, without duplicates and without losing shipping cost.
**Depends on**: Phase 2
**Requirements**: INGEST-01, INGEST-02, INGEST-03
**Success Criteria** (what must be TRUE):

  1. Running the ingestion worker pulls current active eBay listings for catalog products via the Browse API and writes them to MongoDB, on a schedule that can run every N hours.
  2. Re-running the worker — including deliberately overlapping or retried runs — produces no duplicates: each eBay item is upserted by its item ID and concurrent runs are prevented by locking.
  3. Every stored listing records both the pre-shipping item price and the estimated total price (item price + estimated shipping cost).
  4. Each run logs metadata (run time, listings fetched, listings written) so a stalled or empty pull is detectable rather than silent.

**Plans**: 5/5 plans complete

**Wave 1** *(independent — dependency install + storage bootstrap in parallel)*

- [x] 03-01-PLAN.md — Install apscheduler==3.11.3 (package-legitimacy human gate + install)
- [x] 03-02-PLAN.md — Extend db/init_collections.py: active_listings, ingestion_locks (TTL), ingestion_runs

**Wave 2** *(depends on Wave 1 storage)*

- [x] 03-03-PLAN.md — Nyquist test scaffold: ingest_db fixture + 5 RED tests (build_query, lock, upsert, price+shipping, skip-when-locked)

**Wave 3** *(depends on Waves 1-2)*

- [x] 03-04-PLAN.md — scripts/ingest_worker.py: build_query, MongoDB lock, idempotent upsert, run_ingestion_once, APScheduler main()

**Wave 4** *(depends on Wave 3)*

- [x] 03-05-PLAN.md — Live Production Browse API verification (checkpoint; gated/deferrable on eBay credentials)

### Phase 4: Listing Matching & Price Normalization

**Goal**: Raw, messy eBay listings become trustworthy per-product price aggregates that reflect the real market for each canonical product.
**Depends on**: Phase 3
**Requirements**: MATCH-01, MATCH-02, MATCH-03
**Success Criteria** (what must be TRUE):

  1. Raw eBay listing titles are matched to the correct canonical catalog product via keyword rules, with match results inspectable.
  2. Listings signalling lot, bundle, damaged, or counterfeit product are flagged and excluded from a product's price aggregate.
  3. Statistical price outliers (far from the rolling median) are excluded so the aggregate reflects the true market, not noise.
  4. For a given product, the computed current price is derived only from included listings (matched, non-excluded, non-outlier).

**Plans**: TBD

### Phase 5: Flask REST API (active-price serving)

**Goal**: A read-only Flask REST API serves the catalog, search, current price, freshness, and active-price trend data that the frontend needs.
**Depends on**: Phase 4
**Requirements**: None owned (enabling serving layer for PRICE-01, PRICE-02, PRICE-03, SEARCH-01, SEARCH-02, which become user-observable in Phase 6)
**Success Criteria** (what must be TRUE):

  1. A request to `GET /products` returns the catalog and supports searching/filtering by product name and set (enables SEARCH-01).
  2. A request to `GET /products/:id` returns a product's detail, including its current price as total (item + shipping) alongside the item-only price (enables SEARCH-02, PRICE-01).
  3. The API exposes each product's data-freshness timestamp from the last successful ingestion (enables PRICE-02).
  4. The API returns each product's 7d/30d active-price percent change (enables PRICE-03).

**Plans**: TBD

### Phase 6: React SPA Frontend (active-price product)

**Goal**: Users can browse and search sealed products and tell whether one is priced fairly right now, using live active-listing data — this is the shippable v1 product surface.
**Depends on**: Phase 5
**Requirements**: PRICE-01, PRICE-02, PRICE-03, SEARCH-01, SEARCH-02
**Success Criteria** (what must be TRUE):

  1. A user can search and browse catalog products by name or set.
  2. A user can open a product detail page that shows its price data.
  3. On a product, the user sees the current price led by the estimated total (item + shipping), with the pre-shipping item price shown as a secondary detail.
  4. The user sees a "data as of [timestamp]" freshness indicator on the price data.
  5. The user sees a 7d/30d price-trend badge based on active-price history.

**Plans**: TBD
**UI hint**: yes

### Phase 7: Launch & Hardening (v1 active-price)

**Goal**: The active-price product is deployed, publicly reachable, and monitored so its data stays trustworthy and current — shipping v1 regardless of Marketplace Insights API status.
**Depends on**: Phase 6
**Requirements**: None owned (operational readiness for the v1 active-price product)
**Success Criteria** (what must be TRUE):

  1. The application (ingestion worker, Flask API, React SPA, MongoDB) is deployed and the site is reachable at a public URL.
  2. In production the ingestion worker runs automatically on its schedule, keeping displayed data current without manual intervention.
  3. An alert is triggered when ingestion data goes stale beyond roughly 2x the polling interval, so silent pipeline failures surface instead of showing users stale prices.

**Plans**: TBD

### Phase 8: Sold-Price Integration (contingent on MI API access)

**Goal**: Add real sold-price history and the active-vs-sold differentiators — the full dual-data thesis of the product — once Marketplace Insights API access is confirmed.
**Depends on**: Phase 1 (MI API access confirmed), Phase 5 (extends the API), Phase 6 (extends the frontend)
**Contingency**: This phase is gated on the Phase 1 access outcome. If MI API access is confirmed it can be pulled forward (e.g., before or alongside Phase 7 launch); if access is denied or delayed indefinitely, Phases 1-7 remain a complete, shippable v1 and this phase rolls to a later milestone.
**Requirements**: INGEST-04, PRICE-04, PRICE-05, PRICE-06
**Success Criteria** (what must be TRUE):

  1. The ingestion worker pulls sold listings via the Marketplace Insights API and stores them alongside the active-listing data.
  2. A user can view a product's historical sold-price trend chart.
  3. A user can see an active-vs-sold spread indicator ("asking X% above last sale").
  4. A user can see a sold-volume/liquidity indicator ("N sold in last 7 days").

**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. eBay API Feasibility Gate | 3/4 | In Progress|  |
| 2. Product Catalog & Data Model | 6/6 | Complete    | 2026-07-14 |
| 3. Active-Listing Ingestion Pipeline | 5/5 | Complete   | 2026-07-14 |
| 4. Listing Matching & Price Normalization | 0/TBD | Not started | - |
| 5. Flask REST API (active-price serving) | 0/TBD | Not started | - |
| 6. React SPA Frontend (active-price product) | 0/TBD | Not started | - |
| 7. Launch & Hardening (v1 active-price) | 0/TBD | Not started | - |
| 8. Sold-Price Integration (contingent) | 0/TBD | Not started | - |
