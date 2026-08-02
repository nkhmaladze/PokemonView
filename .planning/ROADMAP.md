# Roadmap: PokemonView

## Overview

PokemonView is built in horizontal technical layers, bottom-up: first de-risk the two hard eBay dependencies, then stand up the data model and curated catalog, then the ingestion pipeline, then matching/normalization, then the read API, then the React SPA — shipping a live, active-price product as v1. Because eBay's Marketplace Insights (sold-price) API is approval-gated and may never be granted, the roadmap is deliberately split: Phases 1-7 deliver and launch a complete Browse-API-only (active-listing) product that stands on its own, and the sold-price differentiators are isolated in a final, contingent phase that can be pulled forward if access lands early or deferred to a later milestone if it never does.

## Milestones

- ✅ **v1.0 Active-Price MVP** — Phases 1-7 (shipped 2026-08-02)
- ⏸️ **Phase 8 (Sold-Price Integration)** — parked, not being pursued: Marketplace Insights API access was denied 2026-08-02, and a subsequent reapplication as a registered business entity was denied as well; v1.0 stands as the complete product. See `.planning/milestones/v1.0-ROADMAP.md` Phase 8 details and `FALLBACK-DECISION.md`

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

### ⏸️ Parked (Not Being Pursued)

- [ ] **Phase 8: Sold-Price Integration — PARKED (MI API access denied 2026-08-02; business-entity reapplication also denied)** - Real sold-price history and active-vs-sold differentiators are not being pursued

## Phase Details

### Phase 8: Sold-Price Integration (PARKED — MI API access denied)

**Goal**: Add real sold-price history and the active-vs-sold differentiators — the full dual-data thesis of the product — once Marketplace Insights API access is confirmed.
**Depends on**: Phase 1 (MI API access confirmed), Phase 5 (extends the API), Phase 6 (extends the frontend)
**Contingency**: This phase was gated on the Phase 1 access outcome. **Resolution (2026-08-02):** the denied branch has been taken — the Marketplace Insights Application Growth Check (ticket 260802-000004) was denied. Phases 1-7 shipped as v1.0, the complete active-listing-only product, and this phase rolls to a future milestone per `FALLBACK-DECISION.md` Option 1. **Update (2026-08-02):** a reapplication was subsequently submitted as a registered business entity and was denied, closing that path; the phase is therefore parked indefinitely, not scheduled. PriceCharting (Option 2) remains a theoretical option only and is not being pursued.
**Requirements**: INGEST-04, PRICE-04, PRICE-05, PRICE-06
**Success Criteria** (what must be TRUE):

  1. The ingestion worker pulls sold listings via the Marketplace Insights API and stores them alongside the active-listing data.
  2. A user can view a product's historical sold-price trend chart.
  3. A user can see an active-vs-sold spread indicator ("asking X% above last sale").
  4. A user can see a sold-volume/liquidity indicator ("N sold in last 7 days").

**Plans**: TBD
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
| 8. Sold-Price Integration | Parked (not being pursued) | 0/TBD | Parked | - |
