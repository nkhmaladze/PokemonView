<!-- GSD:project-start source:PROJECT.md -->

## Project

**PokemonView**

A poe.ninja-style price-tracking website for sealed Pokemon TCG product — booster packs, booster boxes, and Elite Trainer Boxes — sourced from eBay. It shows both current asking prices and real sold-price trends over time, starting with English-only product from the most recent 2-3 sets, for collectors and resellers who want to know what something is actually worth right now.

**Core Value:** A user can look up a specific pack/box/ETB and see whether it's priced fairly right now, backed by both live eBay asking prices and actual sold-price history — this must always be accurate and current.

### Constraints

- **Tech stack**: Python + Flask, MongoDB, React SPA frontend — Flask chosen over Django because MongoDB doesn't benefit from Django's relational ORM, and the workload (JSON API + custom matching logic) fits Flask's lighter footprint better.
- **Data source**: Official eBay APIs only (Browse API + Marketplace Insights API) — no scraping, for legal/stability reasons.
- **Scope**: English-only sealed product (packs/boxes/ETBs) from the 2-3 most recent sets for v1.
- **Architecture**: Reasonable microservice split only — ingestion worker, matching/normalization service, API service, frontend — avoid unnecessary service fragmentation.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->

## Technology Stack

## Critical Finding First: eBay Sold-Price Data Access

### Browse API (active listings) — straightforward, standard access

- **Status:** Fully open, standard-tier API. Any registered eBay developer account can use it in Production immediately after creating a keyset — no special approval needed for basic search/browse functionality.
- **Auth:** Application-level OAuth via the **Client Credentials Grant** (`grant_type=client_credentials` against `https://api.ebay.com/identity/v1/oauth2/token`) — no user login/consent flow needed since you're only reading public listing data. Tokens expire in ~7,200 seconds (2 hours) and must be refreshed programmatically by the ingestion worker.
- **Default rate limit:** ~5,000 calls/day per application at the default tier (shared across most REST APIs including Browse). This is almost certainly sufficient for a periodic cron worker polling a curated catalog of ~10-30 products every few hours, but budget for it explicitly (see Pitfalls doc).
- **Higher limits:** Obtainable via the same "Application Growth Check" process described below, once you have production traffic history to justify the ask.
- **Confidence:** MEDIUM-HIGH (official eBay developer docs + multiple consistent community threads).

### Marketplace Insights API (sold listings) — the real risk in this project

- eBay's old free path to sold-price data — the Finding API's `findCompletedItems` call — was **fully decommissioned on February 5, 2025**. That door is now closed permanently; there is no legacy fallback.
- The only "official" replacement, the **Marketplace Insights API**, is explicitly a **Limited Release** API. It is not available by default to any new developer account — Browse API and Marketplace Insights API are NOT the same access tier, despite both being "Buy APIs."
- To request access you must file an **Application Growth Check**: a formal review where you submit a working sandbox application, your use case, and estimated hourly/daily call volumes, and eBay's team manually reviews it for "compliance." There is no published SLA for turnaround time.
- Multiple independent 2024-2026 community reports (eBay Developer Forums, eBay Community boards) describe this API as effectively closed to individual/hobby developers in practice — approvals lean toward established businesses/partners with a clear commercial use case, and getting sandbox access does not guarantee production approval. Several developers report their requests going unanswered or denied without a company/business entity behind the application.
- **Recommendation:** Apply for the Application Growth Check for Marketplace Insights as early as possible (ideally before or during Phase 1), framing the use case as a legitimate price-transparency/resale-analytics tool, and registering as at least a sole-proprietor business entity if possible (community reports suggest bare "personal project" framing correlates with rejection). Do **not** block the roadmap on approval — build the ingestion architecture so the "sold listings" data source is a pluggable interface, not a hard dependency baked into the matching/API layers.

### If Marketplace Insights is denied — fallback options (ranked)

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12+ | Runtime for all backend services | Current stable line with full library support (Flask, PyMongo, APScheduler all support 3.12); 3.13 also fine but 3.12 has broader ecosystem testing as of mid-2026 |
| Flask | 3.1.x (latest 3.1.3, Feb 2026) | REST API framework for API service | Already decided in PROJECT.md over Django — lightweight, no ORM overhead that would fight against MongoDB's document model, minimal boilerplate for a JSON API + custom matching logic |
| PyMongo | 4.17.x (latest, Apr 2026) | Official MongoDB Python driver | Official driver, actively maintained, supports both sync and async APIs; supports MongoDB 4.0 through 8.0 so no version lock-in risk |
| MongoDB | 7.0 or 8.0 (Atlas or self-hosted) | Shared data store across all services | Already decided in PROJECT.md; use **time-series collections** (native since MongoDB 5.0) specifically for the sold/active price-history data — purpose-built for this exact "value over time per product" shape and far more storage/query efficient than plain documents for time-series charts |
| React | 19.2.x (latest, June 2026) | Frontend SPA framework | Already decided in PROJECT.md; React 19 is the current stable major, includes Actions/async transitions and native `<title>`/`<meta>` handling useful for per-product SEO-friendly pages |
| Vite | 6.x/7.x (current) | React SPA build tool/dev server | Create React App was officially deprecated/sunset by the React team (Feb 2025) — Vite is the team's own recommended replacement for SPA (non-framework) projects; far faster dev server and build times |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| APScheduler | 3.11.x (latest 3.11.3) | In-process Python job scheduler for the ingestion worker | Preferred over raw system cron: integrates directly with Python (proper exception handling/logging inside your app instead of relying on shell redirects), supports interval/cron-style triggers, and can persist job state across restarts if needed. Matches PROJECT.md's "cron/script, no Celery" constraint while being far easier to debug than shell cron + a Python entrypoint script |
| requests or httpx | requests 2.32.x / httpx 0.28.x | HTTP client for calling eBay's REST APIs | `requests` is simplest and totally sufficient for a periodic cron-style worker (no concurrency needed); reach for `httpx` only if the ingestion worker later needs async/concurrent calls across many catalog products |
| python-dotenv | 1.x | Environment variable / secrets loading (eBay client ID/secret, Mongo URI) | Every service — keeps eBay credentials and Mongo connection strings out of source control |
| Flask-CORS | 5.x | Enable CORS on the Flask API for the separately-hosted React SPA | Needed as soon as frontend and API are on different origins/ports (standard for this split-service architecture) |
| gunicorn | 23.x | Production WSGI server for the Flask API service | Standard choice for Linux-hosted Flask in production — pre-fork worker model handles concurrent requests well; use Waitress instead only if deploying on Windows |
| Recharts | 3.9.x (latest) | Charting library for price-trend line charts in React | Purpose-built declarative React chart library; simple JSX API covers price line/area charts (the exact chart type this product needs) with far less boilerplate than D3/visx, and is the de facto default choice for React analytics dashboards in 2026. See "What NOT to Use" for why visx/Chart.js are worse fits here |
| React Router | 7.x | Client-side routing for the SPA (per-product pages, catalog browse) | Needed as soon as there's more than one "page" (catalog list vs. individual product detail view) |
| pytest | 8.x | Testing for Flask API + matching/ingestion services | Standard Python test framework; use `pytest-flask` for API test fixtures |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| eBay Sandbox environment | Test Browse API calls without hitting Production rate limits or needing full approval | Separate keyset from Production; note Marketplace Insights API sandbox access does NOT guarantee Production approval — don't assume sandbox success means you're done |
| MongoDB Atlas free tier (M0) | Local/early-dev database without managing infra | Sufficient for v1 catalog size (2-3 sets, sealed product only); revisit self-hosted/paid tier only if traffic or data volume grows meaningfully |
| Postman or eBay's own API Explorer | Manually test Browse/Insights API calls during development | Useful before wiring up the ingestion worker, to confirm exact response shape for a Pokemon ETB/booster box search |

## Installation

# Backend (per service — ingestion, matching, API can share one requirements.txt or split per-service)

# Backend dev/test

# Frontend

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Recharts | visx | If you later need highly custom/interactive chart interactions (e.g. draggable comparison ranges, custom tooltips beyond what Recharts supports) — visx gives D3-level control but costs 2-3x more dev time per chart |
| Recharts | Chart.js (via react-chartjs-2) | If historical price datasets grow very large (thousands of points per product) — Chart.js renders via Canvas and handles bigger datasets more efficiently than Recharts' SVG-per-point approach. Not a concern for v1's scope (2-3 sets, sealed product only, periodic sampling) |
| APScheduler | System cron + standalone script | If you want zero extra Python dependency and are comfortable with shell-level logging/error handling; PROJECT.md's constraint is "cron/script, no Celery" which APScheduler satisfies while staying inside the Python process for better error visibility |
| gunicorn | Waitress | If deploying on Windows, or for a very low-traffic internal-only deployment where the simplicity of a pure-Python WSGI server outweighs gunicorn's better concurrency/performance |
| Vite + React Router (SPA) | Next.js | If the project later needs SSR/SEO for public product pages at scale, or file-based routing conventions — but adds framework complexity not needed for a client-rendered price dashboard; PROJECT.md specifies "React SPA," which points at Vite, not a framework |
| MongoDB time-series collections | Plain MongoDB documents with a manual `history: [...]` array field | Only for a very small v1 prototype; time-series collections are purpose-built for this exact data shape and avoid unbounded array growth problems as price history accumulates |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| eBay Finding API / `findCompletedItems` | Fully decommissioned February 5, 2025 — will return errors, not deprecated-but-working | Marketplace Insights API (if approved) or a licensed third-party source like PriceCharting |
| Scraping eBay search/sold pages directly | Explicitly excluded by PROJECT.md; also a clear eBay ToS violation with real account/legal risk | Official Browse API + (approved) Marketplace Insights API, or PriceCharting as a licensed fallback |
| Celery + a message broker (Redis/RabbitMQ) for the ingestion worker | PROJECT.md explicitly rejects this — unnecessary infrastructure for a simple periodic pull with no need for distributed task queues | APScheduler running in-process, or plain system cron invoking a script |
| Create React App | Officially deprecated/sunset by the React team as of Feb 2025; no longer maintained, missing modern tooling support | Vite (`npm create vite@latest`) |
| Django | Already rejected in PROJECT.md — its ORM assumes a relational schema and fights against MongoDB's document model for no benefit here | Flask (already decided) |
| Assuming Marketplace Insights approval will be quick/automatic | Community evidence strongly suggests otherwise for individual/non-company applicants, with no published SLA | Apply early, plan for denial, treat it as a pluggable data source behind an interface rather than a hard architectural dependency |

## Stack Patterns by Variant

- Ingestion worker calls Browse API (active) and Marketplace Insights API (sold) on the same schedule, storing both into MongoDB time-series collections keyed by canonical product ID
- Both feed the same matching/normalization pipeline
- Ship v1 with Browse API active-listing data only (current price + "asking price" trend built from repeated active-listing snapshots over time — not true sold data, but still shows market movement)
- Evaluate PriceCharting API as a paid, licensed sold-price data source in a follow-up phase, with an explicit scope conversation with the user since it changes the "official eBay APIs only" constraint
- Design the matching/normalization service to be source-agnostic from day one (accept listings from either eBay Browse API or a future PriceCharting-shaped source without a rewrite)

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| PyMongo 4.17.x | MongoDB 4.0–8.0, Python 3.9+ | No compatibility concerns; safe to pair with either MongoDB Atlas or a self-hosted 7.0/8.0 instance |
| Flask 3.1.x | Python 3.9+ (3.12/3.13 recommended) | No known breaking issues; Flask 3.x line has been stable since late 2024 |
| React 19.2.x | Vite 5/6/7, React Router 7.x | React Router 7 requires React 18+; no conflicts with React 19 |
| Recharts 3.x | React 18/19 | Recharts 3 is built against modern React; verify peer dependency range at install time since major version bumps sometimes tighten React version requirements |
| APScheduler 3.11.x | Python 3.8+ | No interaction with Flask/PyMongo versions — runs as an independent in-process scheduler thread |

## Sources

- eBay Developers Program — Application Growth Check docs (`developer.ebay.com/api-docs/static/gs_use-the-application-growth.html`, `gs_request-an-application-growth.html`, `gs_apply-for-the-application.html`) — MEDIUM confidence (official docs, cross-checked via search snippets rather than direct fetch due to fetch timeouts)
- eBay Developers Program — Browse API overview, OAuth Client Credentials Grant docs (`developer.ebay.com/api-docs/static/oauth-client-credentials-grant.html`), API Call Limits page — MEDIUM confidence
- eBay Community / Developer Forums — multiple threads on Marketplace Insights API access denial and individual-developer experience (2024-2026) — MEDIUM confidence (community reports, consistent across independent threads, not official eBay policy statement)
- eBay Community — Finding API/Shopping API decommission announcement (Feb 5, 2025) — MEDIUM-HIGH confidence (official eBay Community announcement thread, corroborated by multiple independent developer reports of `findCompletedItems` failing)
- PyPI / official package pages for Flask, PyMongo, APScheduler; npmjs/react.dev for React; recharts GitHub/npm — MEDIUM confidence (version numbers cross-checked across 2+ independent search results pointing to official package registries; not directly fetched via Context7 in this session)
- MongoDB official docs — Time Series Collections best practices and granularity guide — MEDIUM-HIGH confidence (official MongoDB documentation)
- React.dev — "Sunsetting Create React App" official blog post (Feb 2025) — HIGH confidence (official React team announcement)
- Community comparison articles (LogRocket, PkgPulse) on Recharts vs visx vs Chart.js — MEDIUM confidence (community/blog sources, cross-checked across 2 independent articles with consistent conclusions)
- PriceCharting API documentation page — MEDIUM confidence (vendor's own documentation, not independently verified pricing/licensing terms — recommend confirming subscription tier requirements directly if this fallback is pursued)

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
