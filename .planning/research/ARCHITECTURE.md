# Architecture Research

**Domain:** eBay-sourced sealed-product price tracker (scheduled ingestion → matching/normalization → REST API → SPA), MongoDB-backed
**Researched:** 2026-07-12
**Confidence:** MEDIUM (component boundaries and MongoDB/Flask patterns are well-established; eBay Marketplace Insights API access is a real open risk — see PITFALLS.md)

## Standard Architecture

### System Overview

```
┌───────────────────────────────────────────────────────────────────────┐
│                          SCHEDULED / OFFLINE                          │
├───────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────┐        ┌─────────────────────────────┐        │
│  │  Ingestion Worker   │───────▶│  Matching / Normalization    │        │
│  │  (cron, every N hrs)│        │  Module (in-process library, │        │
│  │  - Browse API pull  │        │  called by ingestion worker) │        │
│  │  - Insights API pull│        │  - keyword rules             │        │
│  └─────────┬───────────┘        │  - fuzzy match (RapidFuzz)   │        │
│            │                    └───────────────┬───────────────┘        │
│            │ raw listings                       │ matched product_id    │
│            ▼                                    ▼                       │
├───────────────────────────────────────────────────────────────────────┤
│                              MONGODB                                    │
│  ┌──────────┐   ┌───────────────┐   ┌───────────────────────────┐      │
│  │ catalog  │   │ raw_listings  │   │ price_points (time series) │      │
│  │ products │   │ (audit trail) │   │ + derived daily aggregates │      │
│  └──────────┘   └───────────────┘   └───────────────────────────┘      │
├───────────────────────────────────────────────────────────────────────┤
│                         ALWAYS-ON / REQUEST TIME                       │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                  Flask REST API (application-factory)            │  │
│  │  /products, /products/:id/current, /products/:id/history         │  │
│  └────────────────────────────┬──────────────────────────────────────┘  │
├───────────────────────────────┴────────────────────────────────────────┤
│                              CLIENT                                     │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │              React SPA (product list, price/trend charts)        │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|-------------------------|
| Ingestion worker | Poll eBay Browse API (active) + Marketplace Insights API (sold) on a schedule, write raw listings, invoke matching, upsert matched price points | Python script triggered by system cron / scheduled task (no Celery); direct pymongo writes |
| Matching/normalization | Normalize free-text titles, map to canonical catalog product via keyword rules + fuzzy fallback | Python module/library (RapidFuzz + rule table), imported by the ingestion worker — not a separate network service |
| Flask REST API | Serve catalog, current prices, historical trends to frontend | Flask app-factory (`create_app()`), blueprints per resource, service layer over pymongo |
| React SPA | Product browsing, current price display, trend charts | React + chart library (e.g. Recharts), calls REST API only |
| MongoDB | Single shared datastore: catalog, raw listings, price history | Managed Atlas or self-hosted; time series collection for price points |

**Key boundary decision — ingestion vs. matching:** Treat matching/normalization as a **library/module inside the ingestion worker process**, not a fourth deployable service. It has no independent scaling need, no independent request-response API, and always runs synchronously right after a raw pull. Splitting it into its own network service would add a request hop and a deployment unit for no operational benefit at this scale — this matches the general small-team guidance that unnecessary service fragmentation costs more in coordination than it buys in isolation (LOW confidence, community best-practice consensus, not project-specific verified). The PROJECT.md's "four services" framing is still honored at the *conceptual* level (ingestion, matching, API, frontend are four distinct responsibilities/modules), but only three things actually need to be deployed: the ingestion worker (cron job), the Flask API (long-running service), and the React SPA (static build). This is the reasonable, non-excessive split the constraints ask for.

## Recommended Project Structure

```
pokemonview/
├── ingestion/                  # cron-triggered worker (its own deployable unit)
│   ├── ebay_client.py          # Browse API + Marketplace Insights API wrappers
│   ├── matching/               # normalization module, imported not deployed separately
│   │   ├── normalize.py        # lowercase, strip filler words (NEW/SEALED/FAST SHIP)
│   │   ├── rules.py            # keyword rule table per catalog product
│   │   └── match.py            # RapidFuzz fallback + score_cutoff
│   ├── run.py                  # entrypoint invoked by cron
│   └── requirements.txt
├── api/                        # Flask REST API service
│   ├── app/
│   │   ├── __init__.py         # create_app() application factory
│   │   ├── config.py           # per-environment config classes
│   │   ├── blueprints/
│   │   │   ├── products.py     # /products, /products/:id
│   │   │   └── prices.py       # /products/:id/current, /:id/history
│   │   ├── services/           # business logic, pymongo queries
│   │   └── models/             # schema helpers / validation
│   ├── run.py
│   └── requirements.txt
├── frontend/                   # React SPA
│   ├── src/
│   │   ├── pages/               # product list, product detail/trend page
│   │   ├── components/          # price chart, product card
│   │   └── api/                 # REST client
│   └── package.json
└── shared/                      # optional: shared constants (catalog schema, enums) if duplicated across services
```

### Structure Rationale

- **ingestion/ as its own top-level folder:** it is a separately deployed/cron-triggered process with its own dependency footprint (eBay SDK/HTTP client, RapidFuzz) — keeping it isolated from the Flask app avoids coupling API deploys to ingestion changes.
- **matching/ nested inside ingestion/:** it is called in-process, immediately after a raw pull, and has no reason to be reachable independently — nesting communicates that boundary in the code layout itself.
- **api/ using blueprints by resource (products, prices), not by HTTP verb:** matches Flask best practice and keeps route files navigable as the catalog grows (MEDIUM confidence, Context7/Flask docs-aligned).
- **frontend/ fully decoupled, REST-only:** SPA never touches MongoDB directly; all data access goes through the Flask API, keeping the browser's data contract stable even if internal schema changes.

## Architectural Patterns

### Pattern 1: Ingest-then-match pipeline (single process, two stages)

**What:** The ingestion worker fetches raw listings, immediately runs them through the matching module in the same process, and writes both the raw listing (audit trail) and the matched price point in one execution.
**When to use:** When matching logic is cheap (keyword rules + fuzzy string compare, no heavy ML/embedding step) and always follows ingestion 1:1 — true here.
**Trade-offs:** Simpler deployment and no network hop, but re-running matching against historical raw listings (e.g. after improving the rule table) requires a separate backfill script rather than "just call the matching service again."

**Example:**
```python
# ingestion/run.py
for raw in ebay_client.fetch_active_listings(query="pokemon booster box"):
    raw_listings.insert_one(raw)                  # audit trail, upsert on ebay_item_id
    product_id, confidence = match(raw["title"])   # matching/match.py
    if product_id and confidence >= THRESHOLD:
        price_points.insert_one({
            "product_id": product_id,
            "ts": datetime.utcnow(),
            "source": "active",
            "price": raw["price"],
            "ebay_item_id": raw["ebay_item_id"],
        })
```

### Pattern 2: Two-tier matching (deterministic rules first, fuzzy fallback second)

**What:** Try exact/keyword rule matches first (set name + product type + language markers); only fall back to RapidFuzz token_sort_ratio/token_set_ratio scoring when rules don't produce a confident hit.
**When to use:** Always, for this domain — keyword rules are cheap, explainable, and catch the majority of well-formed titles; fuzzy matching catches the long tail of messy titles ("Prismatic Evoltuions ETB SEALED FS") without needing rules for every typo.
**Trade-offs:** Requires maintaining a rule table per catalog product (some ongoing curation cost as new sets are added), but keeps false-positive rate low compared to fuzzy-only matching. Un-matched or low-confidence listings should be logged/queued for manual review rather than silently dropped or silently mismatched (LOW confidence source, general fuzzy-matching best practice — https://github.com/rapidfuzz/RapidFuzz).

**Example:**
```python
def match(raw_title: str) -> tuple[str | None, float]:
    normalized = normalize(raw_title)  # lowercase, strip "NEW", "SEALED", "FAST SHIP", punctuation
    for product in catalog_products:
        if all(kw in normalized for kw in product["required_keywords"]):
            return product["_id"], 1.0
    best = rapidfuzz.process.extractOne(
        normalized, catalog_titles, scorer=rapidfuzz.fuzz.token_sort_ratio, score_cutoff=85
    )
    return (best[2], best[1] / 100) if best else (None, 0.0)
```

### Pattern 3: Application-factory Flask API with thin views + service layer

**What:** `create_app()` builds and configures the Flask app (extensions, blueprints, config); routes stay thin and delegate to a service layer that talks to MongoDB.
**When to use:** Standard for any Flask API beyond a single-file prototype — testability (spin up app with test config) and separation of HTTP concerns from query logic (MEDIUM confidence, Context7/Flask docs).
**Trade-offs:** Slightly more boilerplate than a single `app.py`, but pays for itself immediately once you add a second blueprint or need to unit-test business logic without a running server.

## Data Flow

### Ingestion → Display Flow

```
eBay Browse API (active) / Marketplace Insights API (sold)
    ↓ (cron-triggered pull, every N hours)
Raw listing JSON (messy title, price, item id, timestamp)
    ↓ (write, upsert on ebay_item_id — idempotent)
raw_listings collection (audit trail / reprocessing source)
    ↓ (in-process call)
Matching module: normalize → keyword rules → fuzzy fallback
    ↓ (product_id + confidence)
price_points collection (time series: product_id, ts, source=active|sold, price)
    ↓ (Flask API query: latest active price, sold history aggregation)
Flask REST endpoints (/products/:id/current, /products/:id/history)
    ↓ (JSON over HTTP)
React SPA (current price card + trend chart)
```

### Key Data Flows

1. **Active price flow:** Browse API → raw_listings → match → price_points (source="active") → API `/current` endpoint returns the most recent active listings' price distribution (e.g. min/median asking price) for a product.
2. **Sold price / trend flow:** Marketplace Insights API → raw_listings → match → price_points (source="sold") → API `/history` endpoint aggregates sold price_points by day/week for the trend chart. **This flow is contingent on Marketplace Insights API approval — see PITFALLS.md.**
3. **Catalog seeding flow (one-time / low-frequency):** Curated catalog products (set name, product type, language, required keywords) are manually seeded/maintained in the `products` collection — this must exist and be populated before the matching module has anything to match against.

## MongoDB Schema/Collection Recommendations

| Collection | Shape | Notes |
|------------|-------|-------|
| `products` (catalog) | `{ _id, set_name, product_type (booster_pack\|booster_box\|etb), language: "en", release_date, required_keywords: [...], display_name, image_url }` | Curated, low write volume, hand-maintained or seeded via script. Must exist before matching can run. |
| `raw_listings` | `{ _id, ebay_item_id (unique index), title, price, currency, listing_type (active\|sold), fetched_at, matched_product_id, match_confidence }` | Acts as audit trail + reprocessing source if matching rules improve later. Upsert on `ebay_item_id` to keep ingestion idempotent (avoids duplicate rows on cron overlap/retry — LOW confidence, general idempotent-ingestion best practice). |
| `price_points` (time series collection) | metaField: `product_id` (+ `source`: active/sold); timeField: `ts`; measurement: `price` | Use MongoDB's native time series collection type (`timeseries: { timeField: "ts", metaField: "product_id", granularity: "hours" }`) — auto-buckets by product+time, reduces storage, speeds up range queries for trend charts (MEDIUM confidence, MongoDB docs). Keep `source` inside the metaField group (e.g. compound metaField `{product_id, source}`) so active vs. sold can be queried/aggregated independently without scanning both. |

Indexing notes: unique index on `raw_listings.ebay_item_id`; the time series collection gets its bucketing "index" automatically via metaField+timeField — add a secondary index only if querying by fields outside that pattern becomes necessary.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|---------------------------|
| v1 (2-3 sets, sealed only, hundreds of products) | Current 3-deployable-unit design (cron worker, Flask API, static SPA) is sufficient. Single MongoDB instance/cluster, no caching layer needed yet. |
| Growth (more sets, singles added later) | Catalog and matching rule table grow linearly — no architecture change needed, just more curated rows. Consider a lightweight cache (e.g. in-process TTL cache or Redis) in front of the `/current` endpoint if eBay Browse API rate limits become a bottleneck for refresh frequency. |
| High traffic (many concurrent frontend users) | Flask API becomes read-heavy; add read replicas or a cache layer for aggregated trend queries. Ingestion worker and API remain independently scalable since they're already separate deployables. |

### Scaling Priorities

1. **First likely bottleneck: eBay API rate limits**, not database or API server load — the Browse API caps result sets and applies daily call limits per app; batch queries per catalog product and cache repeat lookups rather than scaling infrastructure (LOW confidence, eBay developer docs consensus).
2. **Second: Marketplace Insights API access itself** may be the actual ceiling on sold-price data availability regardless of traffic scale — this is an access/approval constraint, not a technical scaling one (see PITFALLS.md).

## Anti-Patterns

### Anti-Pattern 1: Making matching/normalization its own network microservice

**What people do:** Stand up a separate "matching service" with its own REST endpoint that the ingestion worker calls over HTTP.
**Why it's wrong:** Adds a network hop, a deployment unit, and a versioning surface for logic that's cheap, always invoked synchronously right after ingestion, and has no independent scaling profile. This is the over-fragmentation the project's own constraints explicitly warn against.
**Do this instead:** Keep matching as an in-process module/library imported by the ingestion worker.

### Anti-Pattern 2: Introducing Celery/task broker for a periodic pull

**What people do:** Reach for Celery + Redis/RabbitMQ + beat scheduler for what is just "run this script every N hours."
**Why it's wrong:** Adds broker infrastructure, worker processes, and operational surface area with no corresponding need — there's no dynamic task queue, no fan-out, no user-triggered async jobs, just a fixed-interval pull. PROJECT.md already rejected this correctly.
**Do this instead:** Plain cron (or a managed scheduled-task equivalent) invoking a single Python entrypoint script; own idempotency and retries in the script itself via upserts keyed on `ebay_item_id` rather than relying on broker-level guarantees.

### Anti-Pattern 3: Storing price history as plain (non-time-series) documents with one doc per reading

**What people do:** Insert `{product_id, ts, price}` into a normal collection and query with `find + sort` for trend charts.
**Why it's wrong:** Works at small scale but forfeits MongoDB's native bucketing/compression for time-stamped metric data, and range/aggregation queries (e.g. "daily median sold price over 90 days") get slower and heavier to store as history accumulates.
**Do this instead:** Use a native MongoDB time series collection (`timeseries` option at creation) with `product_id`(+`source`) as metaField and `ts` as timeField from day one — trivial to set up, no reason to defer it.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|----------------------|-------|
| eBay Browse API | REST calls from ingestion worker on cron schedule, OAuth app token | Result sets capped at 10,000 items per search; cache/batch to respect per-app daily call limits (LOW confidence, eBay developer docs). |
| eBay Marketplace Insights API | REST calls from ingestion worker, same cron cycle | Limited Release API — requires eBay Business approval, historically hard to get as an independent developer. **Verify/apply for access as early as possible (Phase 1 candidate)** — this is a genuine go/no-go input for the sold-price half of the product's core value (LOW confidence, community reports — see PITFALLS.md for detail). |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|----------------|-------|
| Ingestion worker ↔ MongoDB | Direct pymongo writes (upserts on `ebay_item_id`) | No API layer needed here — ingestion owns writes to `raw_listings` and `price_points`. |
| Matching module ↔ Ingestion worker | Direct in-process function call | Not a network boundary — see "Key boundary decision" above. |
| Flask API ↔ MongoDB | pymongo reads via service layer | API should be read-mostly against `products` and `price_points`; it does not write ingestion data, keeping a clean read/write ownership split (ingestion writes, API reads). |
| React SPA ↔ Flask API | HTTP/JSON, REST endpoints only | SPA never connects to MongoDB directly; this keeps the data contract stable and lets internal schema evolve independently of the frontend. |

## Sources

- [eBay API Call Limits | eBay Developers Program](https://developer.ebay.com/develop/get-started/api-call-limits) — LOW confidence (web search)
- [Browse API Overview | eBay Developers Program](https://developer.ebay.com/api-docs/buy/browse/overview.html) — LOW confidence (web search)
- [eBay Community: Marketplace Insights API access](https://community.ebay.com/t5/eBay-APIs-Talk-to-your-fellow/Marketplace-Insights-API-access/td-p/34838736/) — LOW confidence (community reports)
- [Access to sold/completed listing data — eBay Community](https://community.ebay.com/t5/eBay-APIs-Talk-to-your-fellow/Access-to-sold-completed-listing-data-what-options-do-non/td-p/35398955/) — LOW confidence (community reports)
- [MongoDB Time Series Collections — Database Manual](https://www.mongodb.com/docs/manual/core/timeseries-collections/) — MEDIUM confidence (official docs)
- [Best Practices for Time Series Collections — MongoDB Docs](https://www.mongodb.com/docs/manual/core/timeseries/timeseries-best-practices/) — MEDIUM confidence (official docs)
- [Flask Project Structure Best Practices + Application Factory](https://muneebdev.com/flask-project-structure-best-practices/) — MEDIUM confidence
- [Modular Applications with Blueprints — Flask Documentation](https://flask.palletsprojects.com/en/stable/blueprints/) — MEDIUM confidence (official docs)
- [RapidFuzz GitHub](https://github.com/rapidfuzz/RapidFuzz) — LOW confidence (web search, project docs)
- [How to Ingest Data: 2 Essential Patterns – Start Data Engineering](https://www.startdataengineering.com/post/data-loading-patterns/) — LOW confidence (web search)
- [How to break a Monolith into Microservices — Martin Fowler](https://martinfowler.com/articles/break-monolith-into-microservices.html) — LOW confidence (web search, industry commentary)
- [Monolithic vs microservices architecture — getdx.com](https://getdx.com/blog/monolithic-vs-microservices/) — LOW confidence (web search, industry commentary)

---
*Architecture research for: eBay sealed-product price tracker (ingestion → matching → API → SPA)*
*Researched: 2026-07-12*
