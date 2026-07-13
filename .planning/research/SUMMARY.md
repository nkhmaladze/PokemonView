# Project Research Summary

**Project:** PokemonView
**Domain:** eBay-sourced sealed-product price tracking (poe.ninja-style) for Pokemon Trading Card Game
**Researched:** 2026-07-12
**Confidence:** MEDIUM

## Executive Summary

PokemonView is a web-based price tracker for Pokemon TCG sealed products (booster boxes, ETBs, packs) powered by real eBay market data. The project's core value is showing accurate current asking prices AND historical sold prices so buyers can distinguish what items are actually trading for versus what sellers are asking. Research validates that this niche (sealed-only, dual active-vs-sold data, English language only) is defensible and addresses a real gap in existing tools like TCGPlayer and PriceCharting.

**The critical finding:** The entire product depends on eBay's **Marketplace Insights API** for sold-price data. This is a Limited Release API, not guaranteed access — eBay gates it behind an "Application Growth Check" approval process that community evidence shows frequently denies individual/hobby developers. **This is a phase 1 go/no-go decision, not a nice-to-have assumption.** The recommended approach is to apply for MI API access immediately, but design the product to ship and validate with Browse API active listings only if denied, adding sold-price trends in a later phase once/if MI API access is confirmed.

The recommended stack is well-established: Python 3.12 + Flask 3.1.x on the backend, React 19 + Vite on the frontend, MongoDB 7.0+ with time-series collections for efficient historical storage. Architecture is straightforward (scheduled ingestion → matching → API → SPA), but success depends absolutely on rigorous execution around data quality: normalizing free-text eBay titles to canonical products, including shipping costs in price aggregates, filtering out lots/bundles/damaged/counterfeit listings, and implementing cron-locking to prevent duplicate ingestion.

---

## Key Findings

### Recommended Stack

Python + Flask is the right choice for a periodic data-ingestion + REST-API product. Key versions: **Python 3.12+, Flask 3.1.x, PyMongo 4.17.x, MongoDB 7.0 or 8.0** with time-series collections (native support since MongoDB 5.0 — must use from day one for efficient price-history storage). Frontend: **React 19.2.x + Vite 6/7** (Create React App is deprecated/sunset as of Feb 2025). Charting: **Recharts 3.9.x** (lightweight, React-native, covers line/area charts perfectly). Scheduling: **APScheduler 3.11.x** in-process, not Celery (project explicitly rejects unnecessary broker infrastructure).

**Critical external dependencies:** Browse API (standard tier, fully open, straightforward OAuth), and Marketplace Insights API (Limited Release, approval-gated). If MI API access is denied, fallback is PriceCharting API (paid, licensed data source) or ship active-listing-only in v1.

**Core technologies:**
- **Python 3.12+:** Current stable line, full ecosystem support for Flask/PyMongo/APScheduler through 3.13
- **Flask 3.1.x:** Lightweight REST API framework, no ORM overhead (good for MongoDB), minimal boilerplate
- **MongoDB 7.0–8.0 with time-series collections:** Purpose-built for "value over time per product" data shape; native bucketing reduces storage 70%+ vs plain documents
- **React 19.2.x + Vite 6/7:** SPA framework + build tool (CRA is deprecated); React Router 7.x for multi-page navigation
- **Recharts 3.9.x:** React charting library for line/area charts; declarative, low boilerplate
- **APScheduler 3.11.x:** In-process cron scheduler; integrates Python exception handling, no broker infrastructure

### Expected Features

**Must have for launch (table stakes):**
- Current active-listing price per product (Browse API) — every competitor leads with this
- Price history chart (time-series visualization) — users need to see trends, not just a single number
- Product search/browse by name or set — minimal navigation UX
- Clear visual distinction between "asking price" (active) and "sold price" (historical) — conflating the two erodes trust, and this distinction is the entire product thesis
- Data freshness timestamp ("updated Xh ago") — cheap to build, high trust payoff
- Basic outlier filtering (exclude lots/bundles/damaged) — raw eBay sold titles are noisy; unfiltered data undermines accuracy

**Should have (v1.x, differentiators):**
- Sold-price volume/liquidity indicator ("N sold in last 7 days") — tells buyers if price is backed by real trading volume
- Price trend badge (7d/30d % change) — glanceable at-a-glance signal vs clicking to see chart
- Active-vs-sold spread/premium indicator ("asking X% above last sale") — this is the direct value prop of having both data sources
- Sealed-only positioning (no singles) — narrow scope is a **feature**, not a limitation; lean into clean, fast, focused UX

**Defer (v2+, scope-creep risks):**
- Deal-finder/underpriced-listing alerts — different product (near-real-time scoring, notification infra; conflicts with simple cron model)
- Portfolio/collection value tracking — requires user accounts, a second product surface
- Singles pricing — different catalog shape entirely (per-card, per-rarity, per-condition); 100x larger scope
- Multi-marketplace aggregation (TCGPlayer, CardMarket) — conflicts with "eBay-only" decision for legal stability

### Architecture Approach

The architecture is clean and intentionally lean: **scheduled ingestion worker → matching/normalization module → MongoDB → Flask REST API → React SPA.** Key design decision: keep matching/normalization as an in-process library imported by the ingestion worker, not a separate microservice — it's cheap, always runs synchronously after a pull, and has no independent scaling need.

**Major components:**
1. **Ingestion worker** (cron-triggered) — calls eBay Browse API (active) + Marketplace Insights API (sold) on a schedule, normalizes titles, matches to catalog products, writes to MongoDB
2. **Matching/normalization module** (library inside ingestion worker) — two-tier: keyword rules first (fast, exact), fuzzy fallback (RapidFuzz) for messy titles; includes exclusion rules to reject lots/bundles/damaged/counterfeit
3. **Flask REST API** (long-running service) — read-only from MongoDB, serves `/products`, `/products/:id/current`, `/products/:id/history` endpoints
4. **MongoDB** (shared datastore) — `products` (curated catalog), `raw_listings` (audit trail), `price_points` (time-series)
5. **React SPA** (static build) — product browse, current price display, trend charts; never touches MongoDB directly

### Critical Pitfalls

1. **Marketplace Insights API access not guaranteed (CRITICAL)** — Limited Release API, gated behind eBay's "Application Growth Check," frequently denies individual developers. Mitigation: (a) Apply for MI API access in Phase 1 before implementing. (b) Design the product so sold-price feature is pluggable. (c) If denied, ship v1 on active listings only, add sold data in v1.x once/if approved. (d) Do NOT block roadmap on approval.

2. **Price omits shipping cost** — eBay APIs return `item.price` and `shipping.cost` separately. Using only price systematically distorts comparisons. Mitigation: Always compute `total_cost = item_price + shipping_cost`, store it as canonical price, use it everywhere. Must be part of data model from day one.

3. **Lot/bundle/damaged/counterfeit titles pollute aggregates** — eBay listings include bulk discounts, damaged product, and counterfeits. Keyword-only matching without exclusion rules mixes these into canonical product trends. Mitigation: Build two-stage matching (inclusion rules + explicit exclusion rules for lots/bundles/damaged/counterfeit), add outlier filtering (drop listings >2-3 std devs from rolling median).

4. **Overlapping/retried cron runs duplicate ingestion** — Without safeguards, a scheduled job slower than its interval or retry logic causes duplicate rows. Mitigation: (a) Use file-based locking (`flock -n`) so concurrent invocations exit immediately. (b) Make every write idempotent by upserting on eBay's item ID. (c) Test by deliberately triggering overlapping runs.

5. **Silent pipeline failures** — A scheduled job can exit successfully while producing zero new rows or stale data (auth token expired, response format changed). Mitigation: (a) Log ingestion metadata (documents, listings matched, timestamp). (b) Alert if data is >2x expected polling interval without update. (c) Display visible "data as of [timestamp]" on frontend.

---

## Implications for Roadmap

Suggested phase structure, ordered by dependencies and risk mitigation:

### Phase 1: Feasibility Spike & eBay API Access Verification
**Rationale:** MI API approval is a hard go/no-go gate on core value prop.
**Delivers:** Browse API working, MI API Application Growth Check submitted, fallback plan documented, OAuth token refresh proven
**Avoids:** Pitfall 1 (late API discovery), Pitfall 6 (token scope confusion)
**Research flag:** NEEDS RESEARCH — current eBay Application Growth Check SLA and approval likelihood for individual developers

### Phase 2: Data Model & Ingestion Pipeline (active listings only)
**Rationale:** Can proceed in parallel with MI API wait. Builds cron/locking/idempotency model before wiring sold data.
**Delivers:** Ingestion worker, MongoDB schema (products/raw_listings/price_points time-series), matching module with keyword+exclusion rules, cron locking, freshness logging
**Addresses (FEATURES):** Current active-price, data freshness, outlier filtering framework
**Avoids:** Pitfalls 2-6 (shipping totalization, exclusion rules, locking, idempotency, freshness monitoring, OAuth automation)
**Research flag:** NEEDS RESEARCH — keyword-matching accuracy using real eBay Pokemon titles (collect 50-100 samples during Phase 1)

### Phase 3: Flask REST API (read-only, active endpoints)
**Rationale:** Build API layer immediately after Phase 2. No dependencies.
**Delivers:** `/products`, `/products/:id`, `/products/:id/current` endpoints, service layer, CORS
**Addresses (FEATURES):** Current active-price display (API half), product search/browse (API half)
**Research flag:** SKIP — REST patterns are standard

### Phase 4: React SPA Frontend (active-price browsing)
**Rationale:** Build user-facing product using Phase 3 API. MVP ships here or Phase 5.
**Delivers:** Product list page, detail page, Recharts chart scaffolding, data freshness timestamp, mobile UI
**Addresses (FEATURES):** Product search (frontend half), current active-price (frontend half), mobile UI
**Research flag:** SKIP — React/Vite/Router/Recharts are well-documented

### Phase 5: Marketplace Insights API Integration & Sold-Price Features
**Rationale:** Only if Phase 1 approval confirmed. Adds sold-price data and key differentiators.
**Delivers:** MI API ingestion, `/products/:id/history` endpoint, sold-price charts, active-vs-sold visualization, liquidity indicator, trend badge, spread indicator
**Precondition:** MI API production access confirmed (Phase 1 output)
**Contingency:** If denied/delayed, ship Phases 1-4 as v1; revisit in v1.x

### Phase 6: Polish, Launch & Post-Launch
**Rationale:** Hardening, deployment, monitoring.
**Delivers:** CI/CD, containerization, alerting, catalog expansion, documentation, API compliance checklist

### Phase Ordering Rationale

**Phase 1 first:** MI API approval is a gate; must resolve before committing. No dependencies on others.

**Phase 2 before 3:** Ingestion and schema must exist before API can serve data.

**Phase 3 before 4:** API must exist and be stable before frontend can consume it.

**Phase 4 before 5:** Active-price half ships first, proves value, then add sold-price differentiator.

**Phase 5 conditional:** Only if Phase 1 approval confirmed; otherwise defer to v1.x.

**Dependency tree:**
```
Phase 1 (MI API approval) [parallel wait]
    ├─→ Phase 2 (Ingestion) [proceeds regardless]
         └─→ Phase 3 (API)
              └─→ Phase 4 (Frontend MVP)
    └─→ Phase 5 (Sold prices) [blocked if Phase 1 denied]
         └─→ Phase 6 (Polish)
```

### Research Flags

**Need research:**
- Phase 1: Current eBay Application Growth Check SLA, approval criteria, success rates
- Phase 2: Real eBay Pokemon TCG title samples for building keyword-rules table; exact shipping field structure in API responses

**Standard patterns (skip research):**
- Phase 3: REST/Flask patterns are well-documented
- Phase 4: React/Vite/Recharts are mature ecosystems
- Phase 5: MI API integration follows Browse API patterns; no new research
- Phase 6: Deployment and monitoring are straightforward

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM-HIGH | Technologies stable, versions cross-checked against official docs. CRA deprecation confirmed (React blog, Feb 2025). Vite validation confirmed. |
| Features | MEDIUM | Derived from 5+ competitor convergence (poe.ninja, PriceCharting, TCGPlayer, PokemonPriceTracker, Collectr). Individual sources LOW-confidence, but convergence pattern raises to MEDIUM. MVP grounded in PROJECT.md Core Value. |
| Architecture | MEDIUM | Component patterns (app-factory, time-series, in-process matching) from official docs. Scaling/rate-limits from eBay docs. "Don't split matching" based on community consensus, not validated for this project. |
| Pitfalls | MEDIUM | MI API restriction corroborated across eBay official docs + multiple independent eBay Community threads (2024-2025). Data quality pitfalls based on e-commerce best practices + Pokemon card market context. Cron patterns from general data-pipeline best practices. |

**Overall confidence:** **MEDIUM** (Marketplace Insights API approval is the critical unknown; proceeds via Phase 1 gate)

### Gaps to Address

1. **MI API approval likelihood:** Unknown. Must be resolved in Phase 1 via direct application. Have PriceCharting fallback documented.
2. **Keyword-matching accuracy:** Need real eBay Pokemon title samples (collect during Phase 1). Research in Phase 2 planning.
3. **eBay rate limits under realistic polling:** Estimate daily call volume for planned polling interval. Confirm it fits 5,000 calls/day default tier.
4. **MongoDB time-series granularity & retention:** Specify during Phase 2 (e.g., keep raw points 90 days, aggregate to daily after). Design based on storage costs and query patterns.
5. **Shipping cost field structure:** Validate exact eBay API field names/shapes during Phase 1. Use to finalize Phase 2 schema.

---

## Sources

- **eBay official:** Application Growth Check docs, Browse API Overview, OAuth docs, API Call Limits, API License Agreement (https://developer.ebay.com)
- **MongoDB official:** Time Series Collections, Best Practices (https://www.mongodb.com/docs)
- **React official:** "Sunsetting Create React App" (Feb 2025, React.dev)
- **eBay Community:** Multiple 2024-2025 threads on MI API access restrictions and approval outcomes
- **Industry best practices:** Martin Fowler (microservices), data-pipeline patterns (Start Data Engineering, Medium), fuzzy matching (Data Ladder, Tilores)
- **Competitors (web search):** poe.ninja, PriceCharting, TCGPlayer, PokemonPriceTracker, Collectr — converging feature patterns
- **Pokemon market context:** PokéBeach (counterfeits), ZIK Analytics, ShelfTrend (eBay card selling)
