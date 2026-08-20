# Requirements: PokemonView

**Defined:** 2026-08-18
**Core Value:** A user can look up a specific pack/box/ETB and see whether it's priced fairly right now, backed by live eBay asking prices — this must always be accurate and current.

## v1.1 Requirements

Requirements for Milestone v1.1 (Price History & Extended Badges). Each maps to roadmap phases.

### Price History & Extended Badges

- [x] **PRICE-07**: User can view a line chart of a product's total-price history on its detail page, rendered from the existing price_points time-series data
- [ ] **PRICE-08**: User can see a 24h price-change badge on the product detail page, alongside the existing 7d/30d badges
- [ ] **PRICE-09**: User can see an all-time high/low price badge on the product detail page, covering the full range since data collection began

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Price History & Extended Badges

- **PRICE-10**: User can view a sparkline chart on catalog/browse list rows, not just the detail page
- **PRICE-11**: User can toggle the detail-page chart between item price and total price

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Sold-price history / Marketplace Insights data | Permanently parked — MI Growth Check denied twice (2026-08-02); see PROJECT.md Context and `FALLBACK-DECISION.md` |
| Catalog-page sparklines | Deferred to v2 (PRICE-10) — keep this milestone to the detail page only |
| Item-price/total-price toggle on the chart | Deferred to v2 (PRICE-11) — total price only for v1.1, matching the existing total-led PriceDisplay convention |
| Downsampled/binned chart data | Not needed — price_points volume is small (6 points/day per product), raw series is returned as-is |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| PRICE-07 | Phase 8: Price History Chart | Complete |
| PRICE-08 | Phase 9: 24h & All-Time Price Badges | Pending |
| PRICE-09 | Phase 9: 24h & All-Time Price Badges | Pending |

**Coverage:**

- v1.1 requirements: 3 total
- Mapped to phases: 3 ✓
- Unmapped: 0

---
*Requirements defined: 2026-08-18*
*Last updated: 2026-08-18 after v1.1 roadmap creation (traceability mapped to Phases 8-9)*
