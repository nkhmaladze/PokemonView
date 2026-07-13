# PokemonView

## What This Is

A poe.ninja-style price-tracking website for sealed Pokemon TCG product — booster packs, booster boxes, and Elite Trainer Boxes — sourced from eBay. It shows both current asking prices and real sold-price trends over time, starting with English-only product from the most recent 2-3 sets, for collectors and resellers who want to know what something is actually worth right now.

## Core Value

A user can look up a specific pack/box/ETB and see whether it's priced fairly right now, backed by both live eBay asking prices and actual sold-price history — this must always be accurate and current.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Curated product catalog for v1: sealed product (booster packs, booster boxes, ETBs) across the 2-3 most recent English sets
- [ ] Scheduled ingestion worker pulls active + sold eBay listings via the official eBay API (Browse API for active, Marketplace Insights API for sold) on a periodic schedule (every X hours, via cron/script — no task broker)
- [ ] Matching/normalization service maps messy raw eBay listing titles to canonical catalog products via keyword-based matching rules
- [ ] Flask REST API serves current active-listing prices and historical sold-price trends per catalog product
- [ ] React SPA frontend displays current price + price-trend charts per product, poe.ninja-style
- [ ] MongoDB is the shared data store across all services

### Out of Scope

- Non-English sets/product — v1 is explicitly English-only
- Singles/individual cards — v1 is sealed product only (packs/boxes/ETBs), not per-card pricing
- Full historical catalog (vintage/older sets) — v1 starts with the 2-3 most recent sets, expand later
- Deal-finder / underpriced-listing alerts — not the initial core value; current price + trend comes first
- Scraping eBay pages — official APIs only, per explicit decision
- Django — considered and rejected in favor of Flask (see Key Decisions)
- Celery/task-broker infrastructure — considered and rejected in favor of simple cron for v1's periodic pull

## Context

- Direct inspiration: poe.ninja, which does real-time + historical price tracking for Path of Exile items. Same concept, applied to Pokemon sealed product instead of game items.
- eBay has two relevant data sources with very different access paths:
  - **Browse API** (active listings / asking prices) — standard developer access, straightforward.
  - **Marketplace Insights API** (sold listings / actual sale prices) — requires an approved, limited-access eBay developer application. This is NOT automatic and should be resolved/verified early (research or Phase 1), since sold-price data is core to the product's value proposition.
- eBay listing titles are unstructured free text (e.g. "Pokemon Prismatic Evolutions Elite Trainer Box NEW SEALED FAST SHIP"), so a dedicated matching step against a curated product catalog is necessary rather than relying on eBay category/keyword filtering alone.

## Constraints

- **Tech stack**: Python + Flask, MongoDB, React SPA frontend — Flask chosen over Django because MongoDB doesn't benefit from Django's relational ORM, and the workload (JSON API + custom matching logic) fits Flask's lighter footprint better.
- **Data source**: Official eBay APIs only (Browse API + Marketplace Insights API) — no scraping, for legal/stability reasons.
- **Scope**: English-only sealed product (packs/boxes/ETBs) from the 2-3 most recent sets for v1.
- **Architecture**: Reasonable microservice split only — ingestion worker, matching/normalization service, API service, frontend — avoid unnecessary service fragmentation.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Track both active and sold eBay prices | Active = live asking price; sold = true market value, mirroring how poe.ninja shows real trade data | — Pending |
| Official eBay APIs only, no scraping | Legal, stable data source; avoids ToS violations and scraper fragility | — Pending |
| Flask over Django | MongoDB doesn't benefit from Django's ORM; JSON API + custom matching logic fits Flask better | — Pending |
| Curated catalog + keyword matching for listings | eBay titles are messy free text; need a canonical product mapping step | — Pending |
| Simple cron/script over Celery for scheduled ingestion | Keeps microservice count reasonable; avoids broker/queue infra for a periodic pull | — Pending |
| Four services: ingestion, matching, API, frontend | Separates concerns without over-fragmenting into unnecessary microservices | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-12 after initialization*
