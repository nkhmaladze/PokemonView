# Requirements: PokemonView

**Defined:** 2026-07-12
**Core Value:** A user can look up a specific pack/box/ETB and see whether it's priced fairly right now, backed by both live eBay asking prices and actual sold-price history.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases. Items tagged **(Phase 8, contingent)** depend on eBay Marketplace Insights API access being approved — see PROJECT.md Context and research/PITFALLS.md. Phases 1-7 ship a complete active-price product independent of that approval; if access is denied, the contingent items roll into a later milestone.

### Catalog

- [x] **CATALOG-01**: Curated catalog of sealed English product (booster packs, booster boxes, ETBs, booster bundles) exists for the 4 most recent sets (Ascended Heroes, Perfect Order, Chaos Rising, Pitch Black) — widened from the original "2-3 sets" framing per Phase 2 D-01
- [x] **CATALOG-02**: Each catalog product has canonical metadata (set, product type, release info) used for matching

### Ingestion

- [ ] **INGEST-01**: Scheduled worker pulls active eBay listings via the Browse API every N hours
- [ ] **INGEST-02**: Ingestion is idempotent (upsert by eBay item ID) and safe against overlapping/retried runs
- [ ] **INGEST-03**: Both pre-shipping item price and estimated total price (item price + estimated shipping cost) are stored per listing
- [ ] **INGEST-04** (Phase 8, contingent): Sold listings are pulled via the Marketplace Insights API once access is confirmed

### Matching

- [ ] **MATCH-01**: Raw eBay listing titles are matched to catalog products via keyword rules
- [ ] **MATCH-02**: Listings with lot/bundle/damaged/counterfeit signals are excluded from price aggregates
- [ ] **MATCH-03**: Statistical price outliers (far from rolling median) are excluded from displayed price

### Pricing Display

- [ ] **PRICE-01**: User can view a product's current price, led by estimated total price (item + shipping) with pre-shipping item price shown as secondary detail
- [ ] **PRICE-02**: User can see a "data as of [timestamp]" freshness indicator
- [ ] **PRICE-03**: User can see a price-trend badge (7d/30d % change) based on active-price history
- [ ] **PRICE-04** (Phase 8, contingent): User can see a historical sold-price trend chart
- [ ] **PRICE-05** (Phase 8, contingent): User can see an active-vs-sold spread indicator ("asking X% above last sale")
- [ ] **PRICE-06** (Phase 8, contingent): User can see a sold-volume/liquidity indicator ("N sold in last 7 days")

### Search & Browse

- [ ] **SEARCH-01**: User can search/browse catalog products by name or set
- [ ] **SEARCH-02**: User can view a product detail page showing its price data

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Expansion

- **EXP-01**: Expand catalog to additional/older/vintage English sets
- **EXP-02**: Deal-finder / underpriced-active-listing alerts
- **EXP-03**: Portfolio/collection value tracking (requires user accounts)

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Non-English sets/product | v1 is explicitly English-only |
| Singles/individual card pricing | Different catalog shape entirely (per-card/rarity/condition), ~100x larger scope than sealed product |
| Scraping eBay pages | Official APIs only, for legal/stability reasons |
| Django | MongoDB doesn't benefit from Django's relational ORM; Flask fits the JSON API + custom matching logic better |
| Celery/task-broker infrastructure | Reasonable microservice scope — simple cron avoids unnecessary broker/queue infra for a periodic pull |
| Multi-marketplace aggregation (TCGPlayer, CardMarket, etc.) | Conflicts with the eBay-only decision made for legal/data-source stability |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CATALOG-01 | Phase 2 | Complete |
| CATALOG-02 | Phase 2 | Complete |
| INGEST-01 | Phase 3 | Pending |
| INGEST-02 | Phase 3 | Pending |
| INGEST-03 | Phase 3 | Pending |
| INGEST-04 | Phase 8 (contingent) | Pending |
| MATCH-01 | Phase 4 | Pending |
| MATCH-02 | Phase 4 | Pending |
| MATCH-03 | Phase 4 | Pending |
| PRICE-01 | Phase 6 | Pending |
| PRICE-02 | Phase 6 | Pending |
| PRICE-03 | Phase 6 | Pending |
| PRICE-04 | Phase 8 (contingent) | Pending |
| PRICE-05 | Phase 8 (contingent) | Pending |
| PRICE-06 | Phase 8 (contingent) | Pending |
| SEARCH-01 | Phase 6 | Pending |
| SEARCH-02 | Phase 6 | Pending |

**Note:** Phases 1 (feasibility gate), 5 (Flask API serving layer), and 7 (launch & hardening) own no requirements directly. They are enabling/operational layers of the horizontal-layer build. Phase 5 serves the display requirements (PRICE-01/02/03, SEARCH-01/02) that become user-observable in Phase 6.

**Coverage:**

- v1 requirements: 17 total
- Mapped to phases: 17 ✓
- Unmapped: 0

---
*Requirements defined: 2026-07-12*
*Last updated: 2026-07-14 after Phase 2 completion (CATALOG-01 scope note widened from "2-3 sets" to 4 sets per Phase 2 D-01)*
