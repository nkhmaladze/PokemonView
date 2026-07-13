# Requirements: PokemonView

**Defined:** 2026-07-12
**Core Value:** A user can look up a specific pack/box/ETB and see whether it's priced fairly right now, backed by both live eBay asking prices and actual sold-price history.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases. Items tagged **(Phase 5, contingent)** depend on eBay Marketplace Insights API access being approved — see PROJECT.md Context and research/PITFALLS.md. If access is denied, v1 ships without them and they roll into a later milestone.

### Catalog

- [ ] **CATALOG-01**: Curated catalog of sealed English product (booster packs, booster boxes, ETBs) exists for the 2-3 most recent sets
- [ ] **CATALOG-02**: Each catalog product has canonical metadata (set, product type, release info) used for matching

### Ingestion

- [ ] **INGEST-01**: Scheduled worker pulls active eBay listings via the Browse API every N hours
- [ ] **INGEST-02**: Ingestion is idempotent (upsert by eBay item ID) and safe against overlapping/retried runs
- [ ] **INGEST-03**: Both pre-shipping item price and estimated total price (item price + estimated shipping cost) are stored per listing
- [ ] **INGEST-04** (Phase 5, contingent): Sold listings are pulled via the Marketplace Insights API once access is confirmed

### Matching

- [ ] **MATCH-01**: Raw eBay listing titles are matched to catalog products via keyword rules
- [ ] **MATCH-02**: Listings with lot/bundle/damaged/counterfeit signals are excluded from price aggregates
- [ ] **MATCH-03**: Statistical price outliers (far from rolling median) are excluded from displayed price

### Pricing Display

- [ ] **PRICE-01**: User can view a product's current price, led by estimated total price (item + shipping) with pre-shipping item price shown as secondary detail
- [ ] **PRICE-02**: User can see a "data as of [timestamp]" freshness indicator
- [ ] **PRICE-03**: User can see a price-trend badge (7d/30d % change) based on active-price history
- [ ] **PRICE-04** (Phase 5, contingent): User can see a historical sold-price trend chart
- [ ] **PRICE-05** (Phase 5, contingent): User can see an active-vs-sold spread indicator ("asking X% above last sale")
- [ ] **PRICE-06** (Phase 5, contingent): User can see a sold-volume/liquidity indicator ("N sold in last 7 days")

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
| CATALOG-01 | TBD | Pending |
| CATALOG-02 | TBD | Pending |
| INGEST-01 | TBD | Pending |
| INGEST-02 | TBD | Pending |
| INGEST-03 | TBD | Pending |
| INGEST-04 | TBD | Pending |
| MATCH-01 | TBD | Pending |
| MATCH-02 | TBD | Pending |
| MATCH-03 | TBD | Pending |
| PRICE-01 | TBD | Pending |
| PRICE-02 | TBD | Pending |
| PRICE-03 | TBD | Pending |
| PRICE-04 | TBD | Pending |
| PRICE-05 | TBD | Pending |
| PRICE-06 | TBD | Pending |
| SEARCH-01 | TBD | Pending |
| SEARCH-02 | TBD | Pending |

**Coverage:**
- v1 requirements: 17 total
- Mapped to phases: 0 (pending roadmap creation)
- Unmapped: 17 ⚠️

---
*Requirements defined: 2026-07-12*
*Last updated: 2026-07-12 after initial definition*
