# PokemonView

## What This Is

A poe.ninja-style price-tracking website for sealed Pokemon TCG product — booster packs, booster boxes, booster bundles, and Elite Trainer Boxes — sourced from eBay. **v1.0 ships live current-asking-price tracking (with 7d/30d trend indicators)** for English-only product across the 4 most recent sets. Real sold-price history was the original dual-data vision — the eBay Marketplace Insights API access request was denied (2026-08-02), and a subsequent reapplication as a registered business entity was denied as well, so sold-price history is parked indefinitely; v1.0 stands as the complete product (see Context, FALLBACK-DECISION.md).

## Core Value

A user can look up a specific pack/box/ETB and see whether it's priced fairly right now, backed by live eBay asking prices — this must always be accurate and current. (Original v1 framing also promised sold-price history as a second pillar; that pillar is now parked indefinitely — see Context.)

## Requirements

### Validated

- [x] Curated product catalog for v1: sealed product (booster packs, booster boxes, booster bundles, ETBs) across the 4 most recent English sets (Ascended Heroes, Perfect Order, Chaos Rising, Pitch Black) — validated in Phase 2, persisted on a schema-validated, indexed MongoDB collection
- [x] Matching/normalization service maps messy raw eBay listing titles to canonical catalog products via keyword-based matching rules — validated in Phase 4 (two-tier exact + bounded RapidFuzz matching, lot/damaged/counterfeit exclusion, statistical outlier filtering, per-product price_points aggregation), wired into the Phase 3 ingestion worker
- [x] Flask REST API serves current active-listing prices per catalog product — validated in Phase 6 (now user-observable end-to-end via the React SPA built in this phase; Phase 5 built the serving layer, Phase 6 is what made it user-facing)
- [x] React SPA frontend displays current active price + 7d/30d trend indicators per product, with search/filter browse and a detail view — validated in Phase 6 (CatalogPage + ProductDetailPage, live E2E-verified against the Flask API). Scope note: this validates *active-price* display only — full historical price-trend line charts and sold-price data remain future scope; Marketplace Insights API access was denied 2026-08-02 (see Context)
- [x] Scheduled active-listing ingestion worker runs unattended in production on its locked schedule (every X hours, via APScheduler in-process — no task broker) — validated in Phase 7 (deployed to Fly.io as an always-on process, scale-to-zero disabled; silent-failure risk covered by a Discord staleness alert)
- [x] MongoDB is the shared data store across all services, including the live production deployment — validated in Phase 7 (Atlas M0, Network Access opened for the deployed Fly.io app)
- [x] The v1 active-price product is deployed and publicly reachable end-to-end — validated in Phase 7 (Flask API on Fly.io at a public `.fly.dev` URL, React SPA on Vercel, CORS wired between them, live-verified with no CORS errors)
- [x] The full pipeline (catalog → scheduled ingestion → matching → price aggregation → API → frontend) is proven against real eBay production data, not just architecturally wired — validated in the 2026-08-02 milestone re-audit: 109 real ingestion runs, 1,272 real price_points, live production `curl` returning real current prices and trends for 15/16 catalog products

### Active

*(None currently in flight — v1.0 is closing. Next milestone's Active requirements get defined via `/gsd-new-milestone`.)*

### Parked (formerly Active, blocked on external access)

- [ ] Sold-listing ingestion via the Marketplace Insights API — the eBay Application Growth Check (ticket 260802-000004) was **denied 2026-08-02**. Per `FALLBACK-DECISION.md` Option 1, this rolls to a future milestone rather than v1.0; active-listing ingestion (above) never depended on it and shipped independently. A reapplication was subsequently submitted as a registered business entity and was **denied as well**, so no live reapplication path remains — sold-price integration is parked indefinitely and v1.0 is treated as the complete product. The paid PriceCharting API (Option 2, see `FALLBACK-DECISION.md`) remains a theoretical future option only, explicitly not being pursued, with no scope conversation open.

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
  - **Browse API** (active listings / asking prices) — standard developer access, straightforward. This is what v1.0 ships on.
  - **Marketplace Insights API** (sold listings / actual sale prices) — requires an approved, limited-access eBay developer application. Application Growth Check (ticket 260802-000004) was submitted 2026-08-02 with real production usage evidence (94 runs / 15.3 days at time of submission) and **denied the same day**. Sold-price data is deferred out of v1.0 per the pre-committed fallback (`FALLBACK-DECISION.md` Option 1); a later reapplication as a registered business entity was denied too, closing the reapplication path, so sold-price data is parked indefinitely rather than awaiting a future milestone.
- eBay listing titles are unstructured free text (e.g. "Pokemon Prismatic Evolutions Elite Trainer Box NEW SEALED FAST SHIP"), so a dedicated matching step against a curated product catalog is necessary rather than relying on eBay category/keyword filtering alone.

### v1.0 Shipped State (as of milestone close, 2026-08-02)

- **Stack as built:** Python 3.12 + Flask 3.1.3 API, PyMongo 4.17.0 against MongoDB Atlas M0 (products collection + native time-series price_points collection), APScheduler 3.11.3 in-process worker (no Celery/broker), React 19 + Vite 6 SPA with React Router 7, Recharts not yet used (no historical chart UI shipped — that's sold-price-dependent future scope).
- **Deployment:** Split-PaaS — Fly.io (API + worker, one image/two always-on process types) + Vercel (static SPA), CORS wired between them, live-verified with no CORS errors.
- **Scale:** ~6,270 LOC across Python/JS, 273 commits, 7 phases / 39 plans, built 2026-07-12 → 2026-08-02 (21 days).
- **Production proof:** 109 real scheduled ingestion runs against live eBay Browse API data, 1,272 real price_points documents, 4,865 real active listing documents. Live production API independently curl-verified during the 2026-08-02 audit (not just trusted from internal docs).
- **Known backlog (non-blocking, carried forward):** ~25 hardening items (missing null-guards, unclosed Mongo clients on error paths, unanchored regexes, no non-root Docker user, no `/health` check, etc. — see `.planning/v1.0-MILESTONE-AUDIT.md` `tech_debt` YAML for the full itemized list) and Nyquist validation coverage gaps on 6 of 7 phases (files exist but were never reconciled post-execution by `/gsd-validate-phase`). None of these are functional defects — every item was already judged non-blocking by its originating phase's own code review.

## Constraints

- **Tech stack**: Python + Flask, MongoDB, React SPA frontend — Flask chosen over Django because MongoDB doesn't benefit from Django's relational ORM, and the workload (JSON API + custom matching logic) fits Flask's lighter footprint better.
- **Data source**: Official eBay APIs only (Browse API + Marketplace Insights API) — no scraping, for legal/stability reasons.
- **Scope**: English-only sealed product (packs/boxes/booster bundles/ETBs) from the 4 most recent sets for v1 (widened from "2-3 sets" per Phase 2 D-01).
- **Architecture**: Reasonable microservice split only — ingestion worker, matching/normalization service, API service, frontend — avoid unnecessary service fragmentation.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Track both active and sold eBay prices | Active = live asking price; sold = true market value, mirroring how poe.ninja shows real trade data | ⚠️ Revisit — active-price shipped (v1.0); sold-price deferred, MI API denied 2026-08-02 |
| Official eBay APIs only, no scraping | Legal, stable data source; avoids ToS violations and scraper fragility | ✓ Good — held throughout Phases 1-7, no scraping anywhere in the codebase |
| Flask over Django | MongoDB doesn't benefit from Django's ORM; JSON API + custom matching logic fits Flask better | ✓ Good (Phase 5) |
| Curated catalog + keyword matching for listings | eBay titles are messy free text; need a canonical product mapping step | Validated (Phase 4) |
| Simple cron/script over Celery for scheduled ingestion | Keeps microservice count reasonable; avoids broker/queue infra for a periodic pull | ✓ Good (Phase 3) — APScheduler in-process, 109 real scheduled runs in production with no broker infra |
| Four services: ingestion, matching, API, frontend | Separates concerns without over-fragmenting into unnecessary microservices | ✓ Good (Phases 3-6) |
| v1 catalog widened to 4 sets, incl. pre-release Pitch Black | User explicitly chose to include the newest set even though not yet released (Jul 17, 2026); seeded now with best-available info, to be verified/corrected post-release | Validated (Phase 2) |
| Added `booster_bundle` as a distinct product type | Meaningfully different price point from both single packs and full boxes; must not be conflated with either in catalog or downstream matching | Validated (Phase 2) |
| Claude curates catalog data via direct web research, no third-party TCG API | Avoids an added external data-source dependency; catalog is static/curated, not live-synced | Validated (Phase 2) |
| Catalog images linked directly to official/public CDN URLs, no self-hosting | Avoids file-storage infra for v1; accepts dependency on those URLs staying stable | Validated (Phase 2) |
| Split-PaaS deployment: Fly.io (API + worker, one image/two process types) + Vercel (static SPA) | User explicitly chose Fly.io over the recommended Render/Railway, accepting the Dockerfile requirement; Vercel picked as simplest static-host wiring for a repo without required git-integration deploy | Validated (Phase 7) |
| Always-on Fly machines (`auto_stop_machines="off"`, `min_machines_running=1`), no free/scale-to-zero tier | A sleeping/cold-starting worker would silently break the locked 4h ingestion cadence; budgeted ~$5-15/mo explicitly for this | ✓ Good (Phase 7) — 109 real runs over 21 days confirm the schedule held |
| Deploy v1 now with eBay credentials still absent; ingestion fails loud, one alert code path covers both "never succeeded" and "went stale" | Avoids blocking launch on an external credential-recovery process with no ETA; self-resolves once real credentials are added via `fly secrets set` with no redeploy | ✓ Good (Phase 7) — credentials restored 2026-07-18, self-resolved with no redeploy exactly as designed |
| Discord webhook for staleness alerting, over email or a manual status page | Simplest to stand up from scratch (no existing Slack workspace); ~2x-polling-interval threshold per RESEARCH.md's "fail loud on stale runs" guidance | ✓ Good (Phase 7) |
| Delay Marketplace Insights Growth Check submission by ~1-2 days (target: 2026-07-19/20) rather than submitting immediately on 2026-07-18 | eBay's own Application Growth Check form states it cannot approve applications "in beta or [with] no usage"; production had only one live ingestion run (800 calls) at the time this was raised. Waiting lets the already-live, always-on worker (4h cadence) accumulate several real runs of usage to cite in the application, improving approval odds without reworking anything — SC-2 only requires submission-tracked, not approved, so this delay is a deliberate timing choice, not a scope change | Resolved (Phase 1) — submitted 2026-08-02 with 94-run/15.3-day evidence; **denied same day** (ticket 260802-000004) |
| Ship v1.0 as active-listing-only on MI denial; sold-price rolls to a future milestone | Pre-committed fallback (`FALLBACK-DECISION.md` Option 1), decided before the outcome was known — avoided any rework or scope scramble when the denial landed | ✓ Good — executed exactly as pre-planned, same day as the denial |
| Re-audit v1.0 against live production data before archiving, rather than trusting the 2026-07-15 audit's stale "gaps_found" | That audit predated the credential restoration and 21 days of real production usage; closing the milestone on stale findings would have misrepresented actual product state | ✓ Good (2026-08-02) — re-audit independently curl-verified the live API and found 13/13 requirements satisfied, 0 blockers, status `tech_debt` |
| Park sold-price integration permanently | The Growth Check was reapplied for as a registered business entity and denied again, leaving no live reapplication path; PriceCharting is not being pursued | User's explicit, final call as of 2026-08-02 — sold-price integration stands parked for the foreseeable future; v1.0 is the complete product |

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
*Last updated: 2026-08-02 — sold-price integration is now parked indefinitely after a reapplication to the Marketplace Insights Growth Check, submitted as a registered business entity, was also denied; v1.0 (active-listing price tracking only) is treated as the complete product. The full pipeline was independently re-verified against real production data before close (109 ingestion runs, live API curl-checks) — see Context "v1.0 Shipped State".*
