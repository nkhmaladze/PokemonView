# Phase 5: Flask REST API (active-price serving) - Research

**Researched:** 2026-07-15
**Domain:** Read-only Flask REST API over MongoDB (catalog + time-series price data), consumed by a future React SPA
**Confidence:** MEDIUM-HIGH (Flask/Flask-CORS patterns are well-established and cross-corroborated; MongoDB time-series aggregation shapes are official-docs-based; Context7 MCP was unavailable this session so library docs were sourced via WebSearch against official documentation pages rather than direct Context7 fetch — see Sources)

## Summary

Phase 5 is a pure serving layer: a Flask application-factory API with two resource blueprints (`products`, `prices` or a combined `products` blueprint exposing both list/detail routes) that reads from the existing `products` collection and `price_points` time-series collection and returns JSON. No new data is created; no eBay calls happen in this phase. The two hard technical problems flagged by CONTEXT.md — "get the latest price_point per product even across gaps" and "find the price_point closest to a 7d/30d target within a tolerance window" — both have clean, efficient MongoDB aggregation shapes that work well within a time-series collection's supported access pattern (metaField equality + timeField range), and at this catalog's scale (≤16 products) neither needs anything exotic. The bigger risks in this phase are not MongoDB performance — they are (1) an implicit assumption that "set release date descending" (D-10) can be derived from `products.release_date`, which is unsafe because per-product release dates within a set are staggered (confirmed by reading `scripts/catalog_data.py` directly), and (2) the `listing_count`/sample-size gap CONTEXT.md explicitly asked research to surface options for, not decide.

**Primary recommendation:** Build `create_app()` + blueprint + thin-service-layer Flask app exactly per `ARCHITECTURE.md` Pattern 3, with a single per-product-loop query style for "current price" and "trend baseline" (given ≤16 products, this is simpler and just as fast as a cross-product aggregation pipeline), a hardcoded `SET_ORDER` constant (not `min(release_date)` per set) for D-10's browse ordering, and an explicit planner decision — informed by the three options below — on the `listing_count` gap before Phase 5 implementation starts.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Catalog browse/search/filter (SEARCH-01) | API / Backend | Database / Storage | Query/filter logic lives in the Flask service layer; MongoDB just stores/returns `products` documents. At ≤16 products, filtering can happen in-process after one full `products.find()` rather than pushing filter logic into MongoDB query operators. |
| Product detail serving (SEARCH-02) | API / Backend | Database / Storage | Single-document lookup by `_id` plus two derived computations (current price, trend) assembled in the service layer. |
| Current-price computation (PRICE-01) | API / Backend | Database / Storage | Aggregation/query logic (latest point per product, gap-tolerant) is service-layer logic executed against the `price_points` time-series collection. |
| Freshness timestamp (PRICE-02) | API / Backend | — | Pure pass-through of the current price_point's real `ts` — no computation, no separate staleness flag (D-03). |
| 7d/30d trend badge (PRICE-03) | API / Backend | Database / Storage | Baseline-lookup aggregation (closest-to-target-date within tolerance) plus a percent-change calculation, both service-layer. |
| CORS / cross-origin config | API / Backend (infra) | — | Flask-CORS configuration is a deployment/environment concern of the API service itself, not a separate tier. |

## Project Constraints (from CLAUDE.md)

Extracted from `./.claude/CLAUDE.md` — the planner must not contradict these:

- **Stack is locked:** Flask + MongoDB + React SPA. No Django (ORM mismatch with MongoDB), no Celery/task-broker (this phase has no async job — pure request/response), no scraping (not applicable to this phase).
- **Recommended core versions per CLAUDE.md:** Flask 3.1.x, Flask-CORS 5.x, pytest 8.x (with pytest-flask "for API test fixtures"), gunicorn 23.x for production WSGI. **Registry verification in this research found Flask-CORS's current latest is actually 6.0.5** (see Standard Stack below) — newer than CLAUDE.md's stated 5.x. Per this project's own established precedent (STATE.md: "Pinned requests==2.34.2 / python-dotenv==1.2.2 per research findings, not stale STACK.md versions"), the planner should prefer the registry-verified current version over the CLAUDE.md figure, and note the discrepancy in the plan.
- **gunicorn is out of scope for Phase 5** — it is the production WSGI server for deployment, not needed for `flask run`/`app.test_client()` development and testing this phase covers. Flag for a later launch/hardening phase (Phase 7 per ROADMAP.md) rather than installing it now.
- **No top-level side effects on import** — established via `scripts/ebay_client.py`, `scripts/matching.py`, `db/init_collections.py`. The Flask app factory (`create_app()`) must follow this: no `MongoClient(...)` call, no blueprint route registration, at module import time.
- **Credential hygiene** — `MONGODB_URI` loaded via `python-dotenv` + `os.environ`, never hardcoded, never logged in full. This phase's `create_app()` must follow the same discipline already used in `tests/conftest.py`.
- **GSD workflow enforcement** — file edits for this phase must go through `/gsd-execute-phase`, not direct ad hoc edits (meta-constraint on execution, not on API design).

## Phase Requirements

Phase 5 owns no requirement IDs directly (confirmed in REQUIREMENTS.md's traceability note: "Phase 5 ... own[s] no requirements directly. They are enabling/operational layers."). This research supports the phase's stated Success Criteria, which enable requirements that become user-observable in Phase 6:

| Enabled Requirement | Description | Research Support |
|----|-------------|------------------|
| SEARCH-01 | User can search/browse catalog products by name or set | D-08 combinable filter+free-text pattern; in-process filtering recommendation (Don't Hand-Roll) |
| SEARCH-02 | User can view a product detail page showing its price data | `GET /products/:id` shape; service-layer assembly pattern |
| PRICE-01 | Current price, total-led with item-price secondary | Current-price aggregation pattern (Code Examples); D-02 gap-tolerant "last known point" logic |
| PRICE-02 | "Data as of [timestamp]" freshness indicator | D-03: pass through the real `ts` of the point shown, no separate staleness flag needed |
| PRICE-03 | 7d/30d active-price trend badge | Closest-to-target-date aggregation pattern with tolerance window (Code Examples); D-06/D-07 percent-change rules |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Flask | 3.1.3 [VERIFIED: pypi registry, `pip index versions flask`] | REST API framework | Already locked by PROJECT.md/CLAUDE.md over Django; app-factory + blueprints is the documented, idiomatic Flask pattern for anything beyond a single-file prototype [CITED: flask.palletsprojects.com/en/stable/patterns/appfactories/] |
| Flask-CORS | 6.0.5 [VERIFIED: pypi registry, `pip index versions flask-cors`] | Enable CORS for the separately-hosted React SPA | Standard, de facto solution for CORS on Flask; resource-scoped config (`resources={r"/api/*": {...}}`) matches this project's blueprint-by-resource layout [CITED: flask-cors.readthedocs.io] |
| PyMongo | 4.17.0 (already installed, confirmed via `pip3 show pymongo`) | MongoDB driver for the read-only service layer | Same driver already used by ingestion/matching phases — no new dependency, only new query patterns |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-dotenv | 1.2.2 (already pinned per STATE.md) | Load `MONGODB_URI` for `create_app()` | Every service in this repo already uses this pattern |
| pytest | 8.4.2 (already pinned) | Test the Flask API | Already the project's test framework |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Plain `app.test_client()` fixtures in `conftest.py` | `pytest-flask` (adds `client`/`live_server` fixtures automatically) | CLAUDE.md's STACK.md table lists pytest-flask as a supporting library, but the official Flask docs pattern (an `app` fixture + a `client` fixture calling `app.test_client()`) achieves the identical result with zero new dependencies, and matches this repo's existing convention of hand-rolled fixtures over test-framework plugins (`tests/conftest.py`'s `catalog_db`/`ingest_db`/`matching_db` are all hand-written, no plugin). **Recommendation: skip pytest-flask, write the 2-fixture pattern directly** — flagged here rather than decided silently since CLAUDE.md does list it as recommended. |
| In-process Python filtering for browse/search (`q`, `set`, `product_type`) | MongoDB `$regex` query or a `$text` index on `products` | At ≤16 total documents, fetching the whole `products` collection once and filtering in Python is simpler, has zero index-maintenance cost, and — importantly — sidesteps a real input-validation risk: building a MongoDB `$regex` from raw user-supplied `q` text requires careful `re.escape()`-ing to avoid regex-injection/backtracking issues. Use `$regex`/`$text` only if the catalog is expected to grow past a few hundred products. |
| Aggregation pipeline computing "latest point per product" across ALL products in one call | Per-product loop (`db.price_points.find({"product_id": pid}).sort("ts", -1).limit(1)`, run ≤16 times) | Both are correct and fast at this scale. The per-product loop is simpler to read, trivially satisfies D-02 (whatever the real latest document is, gap or not), and needs no extra index — MongoDB auto-creates a compound index on the metaField+timeField pair, which this exact per-product query pattern uses. A single cross-product aggregation (`$sort` + `$group` + `$first`) also works and is documented below as an alternative if the planner prefers one query over N small ones. |

**Installation:**
```bash
pip install flask==3.1.3 flask-cors==6.0.5
```
(pymongo, python-dotenv, pytest already in `requirements.txt`.)

**Version verification:** Confirmed directly against PyPI via `pip index versions flask` (3.1.3 latest) and `pip index versions flask-cors` (6.0.5 latest) in this session — not sourced from training data or CLAUDE.md's STACK.md table, which is stale on the Flask-CORS figure (says 5.x).

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| flask | pypi | long-established (this session's registry snapshot shows a recent metadata timestamp, but Flask is Pallets' flagship, multi-year project) | telemetry unavailable to the legitimacy tool | github.com/pallets/flask | [SUS] — reason: `unknown-downloads` | Approved — same "unknown-downloads" false-positive class already reviewed and approved for `pymongo`, `apscheduler`, `rapidfuzz` in prior phases per STATE.md ("Approved ... install after human review confirmed [SUS] verdict was a false positive from unresolved download-count telemetry"). Flask is one of the two most widely used Python web frameworks and is explicitly locked by PROJECT.md — flagged here per protocol, but a `checkpoint:human-verify` before install is a formality consistent with prior phases, not a real risk signal. |
| flask-cors | pypi | actively maintained (corydolphin/flask-cors) | telemetry unavailable | github.com/corydolphin/flask-cors | [SUS] — reason: `unknown-downloads` | Approved with the same reasoning as above — planner should still add the `checkpoint:human-verify` task per protocol. |
| pytest-flask | pypi | actively maintained | telemetry unavailable | github.com/pytest-dev/pytest-flask | [SUS] — reason: `unknown-downloads` | **Not recommended for install** (see Alternatives Considered) — the plain 2-fixture pattern is preferred, making this package's legitimacy moot unless the planner overrides that recommendation. If installed, gate behind `checkpoint:human-verify` like the others. |

**Packages removed due to [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** flask, flask-cors, pytest-flask — all three are `unknown-downloads`-class false positives consistent with this project's prior-phase pattern (pymongo, apscheduler, rapidfuzz all hit the same signal gap and were approved after human review). The planner must still add a `checkpoint:human-verify` task before each install per protocol; do not skip that step just because prior phases had the same outcome.

*Postinstall-script check (Step 3 of the protocol) is Node.js-specific (`npm view scripts.postinstall`) and does not apply to this Python project — skipped, not applicable.*

## Architecture Patterns

### System Architecture Diagram

```
                        ┌─────────────────────────────┐
                        │   (Phase 6, not yet built)   │
                        │       React SPA client       │
                        └──────────────┬───────────────┘
                                       │ HTTP/JSON (CORS-enabled)
                                       ▼
        ┌───────────────────────────────────────────────────────────┐
        │                    Flask REST API (Phase 5)                │
        │  create_app()                                               │
        │   ├─ Flask-CORS init (allowed origins from config)          │
        │   ├─ blueprint: products  → GET /products, GET /products/:id│
        │   └─ blueprint: prices (optional split) → price sub-routes  │
        │            │                                                │
        │            ▼                                                │
        │   Service layer (pure functions, pymongo reads only)        │
        │     - list_products(filters) -> [product+price summary]     │
        │     - get_product_detail(id) -> product+current+trend       │
        │     - get_current_price(product_id) -> {ts,item,total} |None│
        │     - get_trend_baseline(product_id, days) -> point | None  │
        └───────────────────────────┬──────────────────────────────────┘
                                    │ pymongo reads (no writes)
                                    ▼
        ┌───────────────────────────────────────────────────────────┐
        │                          MongoDB                            │
        │  products (catalog, ≤16 docs)                               │
        │  price_points (time series: timeField=ts, metaField=product_id, │
        │                granularity=hours) — written by Phase 4 only  │
        └───────────────────────────────────────────────────────────┘
```

A reader can trace: SPA request → Flask blueprint route → service-layer function → pymongo query against `products` or `price_points` → JSON response back up the same path. No writes occur anywhere in this diagram — Phase 4's matching pipeline is the only writer of `price_points`, and catalog seeding (`scripts/seed_catalog.py`) is the only writer of `products`.

### Recommended Project Structure

```
api/
├── __init__.py
├── app.py               # create_app() application factory
├── config.py            # Config class: MONGODB_URI, CORS_ORIGINS, DB_NAME from env
├── db.py                 # get_db(app) helper — single MongoClient built at create_app() time, never at import time
├── blueprints/
│   ├── __init__.py
│   └── products.py       # GET /products, GET /products/:id (list + detail, both live here per D-08's combined filter+search)
└── services/
    ├── __init__.py
    ├── catalog_service.py   # browse/search/filter over products
    └── price_service.py     # current price + trend baseline aggregations over price_points
```

This mirrors `ARCHITECTURE.md`'s `api/app/{blueprints,services}` layout, adapted slightly flatter to match this repo's existing top-level `scripts/`/`db/` convention (not nested under `app/`).

### Pattern 1: `create_app()` application factory with lazy MongoClient

**What:** `create_app(config_object=None)` builds the Flask app, reads `MONGODB_URI` from env inside the factory call (never at import time), constructs one `MongoClient`, stores the database handle on `app.config["DB"]` (or via a small `get_db()` accessor using `flask.current_app`), registers blueprints, and returns `app`.
**When to use:** Always for this phase — matches the repo's "no top-level side effects on import" convention and makes `app.test_client()` testing trivial (a test can call `create_app(test_config)` pointed at `pokemonview_test`).
**Example:**
```python
# api/app.py
from flask import Flask
from flask_cors import CORS
from pymongo import MongoClient
import os

def create_app(mongodb_uri=None, db_name="pokemonview"):
    app = Flask(__name__)
    app.config["MONGODB_URI"] = mongodb_uri or os.environ["MONGODB_URI"]
    app.config["DB_NAME"] = db_name

    client = MongoClient(app.config["MONGODB_URI"])
    app.config["DB"] = client[app.config["DB_NAME"]]

    CORS(app, resources={r"/products*": {"origins": os.environ.get("CORS_ORIGINS", "*")}})

    from api.blueprints.products import products_bp
    app.register_blueprint(products_bp)

    return app
```
[CITED: flask.palletsprojects.com/en/stable/patterns/appfactories/, flask-cors.readthedocs.io — pattern combined and adapted for this project's pymongo-not-Flask-SQLAlchemy stack]

### Pattern 2: Thin routes, service-layer aggregation logic

**What:** Blueprint route functions parse query params/path params, call one service-layer function, and `jsonify()` the result — they contain no pymongo calls themselves.
**When to use:** Always — keeps aggregation logic (the genuinely tricky part of this phase) unit-testable without a running Flask app or test client.
**Example:**
```python
# api/blueprints/products.py
from flask import Blueprint, jsonify, request, current_app
from api.services import catalog_service

products_bp = Blueprint("products", __name__)

@products_bp.route("/products")
def list_products():
    db = current_app.config["DB"]
    filters = {
        "q": request.args.get("q"),
        "set_name": request.args.get("set"),
        "product_type": request.args.get("product_type"),
    }
    return jsonify(catalog_service.list_products(db, filters))

@products_bp.route("/products/<product_id>")
def product_detail(product_id):
    db = current_app.config["DB"]
    detail = catalog_service.get_product_detail(db, product_id)
    if detail is None:
        return jsonify({"error": "not_found"}), 404
    return jsonify(detail)
```

### Anti-Patterns to Avoid

- **Deriving D-10's "set release date descending" sort from `products.release_date` directly:** `scripts/catalog_data.py` shows per-product `release_date` is staggered within a set (e.g. Ascended Heroes: `booster_box`/`booster_pack` = 2026-01-30, `etb` = 2026-02-20, `booster_bundle` = 2026-04-24). A naive `sort by release_date desc` would interleave products across sets incorrectly instead of grouping by set. Use a small hardcoded `SET_ORDER` list matching D-10's explicit sequence (Pitch Black → Chaos Rising → Perfect Order → Ascended Heroes) instead of computing it from data.
- **Building a MongoDB `$regex` query directly from the raw `q` query-string parameter without escaping:** unescaped user text passed into `$regex` is both a regex-injection/DoS surface and unnecessary at this catalog size — filter in Python instead (see Don't Hand-Roll).
- **Treating "current price" as "the most recent ingestion run's price_point, or null":** D-02 explicitly requires the *last known* point regardless of how many runs back it was written — `sort(ts, -1).limit(1)` with no time-window filter already does this correctly; do not add a "only if within N hours" filter to the current-price query (that filter belongs only to the trend-baseline lookup, not the current-price lookup).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CORS headers | Manual `Access-Control-Allow-Origin` header-setting in an `after_request` hook | `flask-cors`'s `CORS()` | Handles preflight `OPTIONS` requests, `Vary` header correctness, and per-resource origin scoping correctly — easy to get subtly wrong by hand (e.g. forgetting preflight handling). |
| Free-text catalog search at ≤16 products | A MongoDB `$text` index + `$search` aggregation stage | Fetch all `products` once, filter in Python with case-insensitive substring checks on `display_name`/`set_name` | A `$text` index is real infrastructure (index maintenance, language/stemming config) for a problem that's fully solved by an O(16) Python loop at this catalog size. Revisit only if the catalog grows to hundreds of products. |
| "Closest point to a target date" logic | A hand-rolled loop in Python over all of a product's price history computing `abs(ts - target)` in application code | The `$match` (bounded window) → `$addFields`(`$abs`/`$subtract`) → `$sort` → `$limit 1` aggregation pipeline | Pushing the bounded-window filter into MongoDB lets `price_points`' timeField bucketing do the coarse filtering before any date-diff math runs, and keeps the "closest within tolerance" logic in one testable pipeline shape rather than duplicated in two places (7d and 30d) as ad hoc Python. |

**Key insight:** At this project's catalog scale (≤16 products), the correct engineering answer is frequently "the simplest thing that is still correct" rather than reaching for MongoDB's more advanced query features (`$text`, cross-product `$group` aggregations) — those features exist for scale problems this catalog does not have yet, and CLAUDE.md's own "Alternatives Considered" table already flags this exact simplicity-over-scale tradeoff for other parts of the stack (e.g. Recharts vs Chart.js "not a concern for v1's scope").

## Common Pitfalls

### Pitfall 1: Set-level sort order derived from staggered per-product release dates

**What goes wrong:** D-10 requires browse results "grouped by set, release date descending." If the sort key is each product document's own `release_date` field, sets with staggered internal release dates (Ascended Heroes, confirmed via `scripts/catalog_data.py`) will not group cleanly, and pre-release Pitch Black's placeholder `release_date` (2026-07-17, not yet confirmed per D-02 in Phase 2's CONTEXT.md) could shift if corrected post-launch.
**Why it happens:** It's tempting to sort directly on an existing field rather than defining a separate "set ordering" concept.
**How to avoid:** Define a small `SET_ORDER = ["Pitch Black", "Chaos Rising", "Perfect Order", "Ascended Heroes"]` constant (matching D-10's explicit named sequence) and sort by `SET_ORDER.index(set_name)` as the primary key, with a secondary in-set key (e.g. a fixed `product_type` display order, or `msrp` descending) as Claude's-discretion detail.
**Warning signs:** Browse endpoint output interleaves ETBs/boxes/bundles from different sets instead of showing one set's products together.

### Pitfall 2: Confusing "current price" gap-tolerance with "trend baseline" tolerance

**What goes wrong:** D-02 (current price) and D-05/D-06 (trend baseline) sound similar ("tolerate gaps") but have different rules: current price has **no tolerance window at all** — always return the single most recent point, however old. Trend baseline **does** have a tolerance window (±2-3 days) and must return an explicit "insufficient data" state if nothing falls inside it. Applying the trend's tolerance-window logic to the current-price query would incorrectly return `null`/"no data" for a product whose only price_points are older than the window, violating D-02.
**Why it happens:** Both problems are "find a point near date X in the same collection" and are easy to solve with one shared helper function that has an implicit window built in.
**How to avoid:** Write two distinctly-named service functions (`get_current_price` — no window; `get_trend_baseline` — bounded window with an explicit "not found" return) rather than one parameterized helper, or make the window parameter `None`-able and test both branches explicitly.
**Warning signs:** A product with real, valid history that's simply had a long ingestion gap since the last point (D-02's whole scenario) shows `current_price: null` instead of the real last-known price.

### Pitfall 3: Sample-size gap (flagged by CONTEXT.md, not resolved here)

**What goes wrong:** PITFALLS.md explicitly warns against "showing a single 'the price' number with no indication of ... sample size." The `price_points` schema written by `scripts/matching.py`'s `aggregate_and_write()` (confirmed by direct read) is exactly `{ts, product_id, item_price, total_price}` — **no listing-count field exists**. If the planner assumes an n-count is available to show alongside the price, it isn't, without one of the changes below.
**Why it happens:** This wasn't part of any locked D-01..D-12 decision (confirmed — CONTEXT.md's decisions section never mentions listing count), so it's easy to either silently add it or silently skip it without a documented choice.
**How to avoid:** See "Sample-Size Gap — Options for Planning" below; this must be an explicit planning decision, not an implementation-time judgment call.
**Warning signs:** A task description mentions "based on X listings" in the API response shape without a preceding decision on how `X` is computed.

## Sample-Size Gap — Options for Planning

CONTEXT.md's Specific Ideas section explicitly asks research to present options rather than decide. Three options, with cost/tradeoff for each:

| Option | What it takes | Cost | Note |
|--------|---------------|------|------|
| **A — Add `listing_count` to `price_points`** | One-line addition to `scripts/matching.py`'s `aggregate_and_write()`: `"listing_count": len(included)` alongside the existing median computations. `included` is already computed in `run_matching_once()` right before this call — no new query, no new data source. | LOW — touches a "done" Phase 4 file, but it's an additive, backward-compatible schema change (old documents simply lack the field; API can treat a missing field the same way D-01 treats "no data yet" — an explicit but distinguishable state, not a crash). Existing `price_points` documents written before this change won't have it retroactively; a small migration or "n/a for older points" UI affordance may be needed. | Directly satisfies the PITFALLS.md guidance with the least total effort. Recommended if the planner wants to close this gap in v1. |
| **B — Compute listing count from `active_listings` at read time** | Query `active_listings` for documents matching the `product_id` and run/time window that produced a given `price_points` document, count `match_status == "matched" AND exclusion_reason IS NULL`. | MEDIUM-HIGH — requires either storing a `run_id` reference on `price_points` (another schema change, same cost class as Option A but on the read side too) or a fragile time-window join between two collections that were deliberately kept separate (per `db/init_collections.py`'s own documented rationale: "so unmatched raw listings never corrupt price_points' metaField contract"). More moving parts, more ways to get the join subtly wrong. | Not recommended — solves the same problem as Option A with meaningfully more risk and complexity. |
| **C — Ship v1 without a sample-size indicator** | No schema change. | LOW engineering cost, but consciously leaves a documented PITFALLS.md UX gap unaddressed for v1. | Acceptable only if the planner/user explicitly decides this tradeoff is fine for v1 — must not be a silent default. |

**Research recommendation:** Option A, given it is a strict superset of "no change" in terms of risk (additive field, no query changes, no cross-collection joins) and directly closes a named Pitfall at near-zero cost. This is a recommendation, not a decision — the planner (or a fast round-trip to `/gsd-discuss-phase`) should confirm before Phase 5 tasks are written, since it touches Phase 4's writer.

## Code Examples

### Current price (gap-tolerant, no time window — D-02)

```python
# api/services/price_service.py
def get_current_price(db, product_id: str) -> dict | None:
    """Returns the single most recent price_points document for
    product_id, however old — D-02: never null just because the
    latest ingestion run had a gap. Returns None only if the product
    has zero price_points documents ever (D-01)."""
    doc = db.price_points.find_one(
        {"product_id": product_id},
        sort=[("ts", -1)],
    )
    return doc  # {ts, product_id, item_price, total_price} or None
```
This single-product query pattern uses the compound index MongoDB automatically creates on the time-series collection's metaField+timeField pair — no secondary index needed [CITED: mongodb.com/docs/manual/core/timeseries/timeseries-limitations/].

### Trend baseline (bounded tolerance window — D-05/D-06)

```python
from datetime import timedelta

def get_trend_baseline(db, product_id: str, current_ts, days: int, tolerance_days: int = 3) -> dict | None:
    """Returns the price_points document closest to (current_ts - days),
    accepted only within +/- tolerance_days of that target (D-05).
    Returns None if nothing falls inside the window (D-06: caller must
    surface an explicit 'insufficient data' state, not omit the badge)."""
    target = current_ts - timedelta(days=days)
    window_start = target - timedelta(days=tolerance_days)
    window_end = target + timedelta(days=tolerance_days)

    pipeline = [
        {"$match": {
            "product_id": product_id,
            "ts": {"$gte": window_start, "$lte": window_end},
        }},
        {"$addFields": {"diff": {"$abs": {"$subtract": ["$ts", target]}}}},
        {"$sort": {"diff": 1}},
        {"$limit": 1},
    ]
    results = list(db.price_points.aggregate(pipeline))
    return results[0] if results else None
```
The `$match` stage runs first and narrows to the tolerance window before any date-diff math executes — this is the standard MongoDB pattern for "closest document to a target" and is efficient even without a secondary index at this data volume [CITED: mongodb.com/docs/manual/reference/operator/aggregation/abs/, mongodb.com/docs/manual/reference/operator/aggregation/subtract/].

### Percent-change computation (D-07 — total_price only)

```python
def compute_pct_change(current_total: float, baseline_total: float) -> float | None:
    if baseline_total == 0:
        return None  # guard against division by zero; treat as insufficient data upstream
    return round((current_total - baseline_total) / baseline_total * 100, 2)
```

### Alternative: cross-product "latest per product" aggregation (if the planner prefers one query over N)

```python
pipeline = [
    {"$sort": {"product_id": 1, "ts": -1}},
    {"$group": {"_id": "$product_id", "latest": {"$first": "$$ROOT"}}},
]
latest_by_product = {doc["_id"]: doc["latest"] for doc in db.price_points.aggregate(pipeline)}
```
Sorting by the grouped field first (`product_id`) then descending `ts`, followed by `$group`+`$first`, lets MongoDB use an index matching the sort order for the `$group` stage [CITED: mongodb.com/docs/manual/reference/operator/aggregation/group/, mongodb.com/community/forums/t/grouping-by-sort-and-limit/160055]. At ≤16 products this has no measurable performance advantage over the per-product loop above — included as an option, not a requirement.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| Storing price history as plain (non-time-series) documents | Native MongoDB time-series collections (`timeseries` option) | Available since MongoDB 5.0, already adopted by this project in Phase 2 | Already correctly in place — `price_points` was created as a time-series collection from the start (`db/init_collections.py`), so this phase inherits the benefit without needing to migrate anything. |
| Flask-SQLAlchemy-style `db = SQLAlchemy(app)` bound at import time | `db.init_app(app)` / lazy binding inside `create_app()` | Long-standing Flask best practice, still current in 3.1.x docs | This project uses raw pymongo (no ORM), but the same "don't bind at import time" principle applies to the `MongoClient` construction — build it inside `create_app()`, not at module scope. |

**Deprecated/outdated:** None specific to this phase's dependencies — Flask 3.1.x, Flask-CORS 6.x, and MongoDB time-series collections are all current, actively maintained approaches as of this research date.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Flask app-factory + service-layer pattern details (exact function names, blueprint registration mechanics) sourced via WebSearch against official Flask docs pages, not a direct Context7 fetch (Context7 MCP tool was unavailable this session) | Architecture Patterns | LOW — the pattern is stable/well-known and cross-corroborated across the official docs URL and this project's own ARCHITECTURE.md (already independently researched in Phase 0), but should be spot-checked against `flask.palletsprojects.com` directly if Context7 becomes available before planning. |
| A2 | Recommendation to skip `pytest-flask` in favor of a hand-rolled 2-fixture pattern | Standard Stack / Alternatives Considered | LOW — CLAUDE.md lists pytest-flask as a recommended supporting library; if the planner disagrees, installing it is a drop-in alternative with no architectural conflict, just an extra dependency. |
| A3 | `flask-cors` package integration pattern (`No official Flask-PyMongo docs found via context7 fallback` digest) — the pymongo+Flask-factory integration shape (store client on `app.config`) is a community convention, not from an authoritative pymongo/Flask joint doc | Architecture Patterns, Pattern 1 | LOW — this is a simple, low-risk integration choice (where to stash a MongoClient handle); alternate valid choices (module-level singleton with lazy init, `flask.g`-based per-request lookup) all work equally well and don't affect correctness of the phase's success criteria. |

## Open Questions

1. **Should `listing_count` be added to `price_points` in this phase (Option A above), or deferred?**
   - What we know: The schema change is a one-line, additive, backward-compatible addition to `scripts/matching.py`'s already-computed `included` list.
   - What's unclear: Whether the user wants to reopen Phase 4's "complete" writer in Phase 5, versus treating it as a documented v1 gap.
   - Recommendation: Confirm with the user/planner before writing Phase 5 tasks — do not decide silently either way (per CONTEXT.md's explicit instruction).

2. **Exact secondary sort key within a set (after `SET_ORDER` groups by set) for D-10's browse ordering.**
   - What we know: CONTEXT.md leaves "exact URL/route structure... field names beyond what's implied" to Claude's discretion, and D-10 only specifies "grouped by set, release date descending... products grouped within each set" without specifying in-set order.
   - What's unclear: Whether in-set order should be by `product_type` (fixed display order: box → etb → bundle → pack, or another sequence) or by `msrp` descending.
   - Recommendation: Either is reasonable; the planner should pick one and note it as a documented (not silent) choice, matching the poe.ninja-style reference (PROJECT.md) where higher-value products often lead.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Flask API runtime | ✓ | 3.12.13 | — |
| flask | API framework | ✗ (not yet installed) | — | Install per Standard Stack — no fallback needed, greenfield install |
| flask-cors | CORS support | ✗ (not yet installed) | — | Install per Standard Stack |
| pymongo | MongoDB driver | ✓ | 4.17.0 | — |
| MongoDB (Atlas M0) | Data store for `products`/`price_points` | Not directly probed this session (`.env` contents were not read, to avoid handling secrets outside the established pattern) — `tests/conftest.py`'s existing fixtures already skip gracefully via `pytest.skip()` when `MONGODB_URI` is unset, so this phase's test fixtures should follow the identical pattern rather than assuming a live connection. | Atlas M0 per STATE.md (Phase 02-02: "User provisioned MongoDB Atlas M0") | Same conftest.py skip-gracefully pattern |

**Missing dependencies with no fallback:** none — `flask`/`flask-cors` are simple greenfield installs with no blocking risk.
**Missing dependencies with fallback:** MongoDB connectivity — follow the existing `pytest.skip()`-on-missing-`MONGODB_URI` convention already established across `catalog_db`/`ingest_db`/`matching_db` fixtures.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 (already installed and configured) |
| Config file | `pytest.ini` (`pythonpath = .`, `testpaths = tests`) |
| Quick run command | `pytest tests/test_api_products.py -x` |
| Full suite command | `pytest` |

### Phase Requirements → Test Map

| Req / SC | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SC1 (SEARCH-01 enabler) | `GET /products` returns catalog, supports `q`/`set`/`product_type` filters, combinable (D-08) | integration (Flask test client + real test MongoDB) | `pytest tests/test_api_products.py::test_list_products_filters -x` | ❌ Wave 0 |
| SC1 | Default sort groups by set, newest-first (D-10) | integration | `pytest tests/test_api_products.py::test_default_sort_order -x` | ❌ Wave 0 |
| SC2 (SEARCH-02/PRICE-01) | `GET /products/:id` returns current price as total (headline) + item (secondary) | integration | `pytest tests/test_api_products.py::test_product_detail_current_price -x` | ❌ Wave 0 |
| SC2 | D-02: last known point returned across a gap (no null just because latest run had a gap) | unit (service layer, no Flask needed) | `pytest tests/test_price_service.py::test_current_price_gap_tolerant -x` | ❌ Wave 0 |
| SC2 | D-01: zero price_points ever returns `null` + explicit `"no_data_yet"` status, not 404/omitted | integration | `pytest tests/test_api_products.py::test_product_no_price_data -x` | ❌ Wave 0 |
| SC3 (PRICE-02) | Freshness timestamp is the literal `ts` of the point shown, no computed staleness flag (D-03) | unit | `pytest tests/test_price_service.py::test_freshness_is_real_ts -x` | ❌ Wave 0 |
| SC4 (PRICE-03) | 7d/30d trend within ±2-3 day tolerance (D-05) | unit | `pytest tests/test_price_service.py::test_trend_baseline_within_tolerance -x` | ❌ Wave 0 |
| SC4 | D-06: no baseline within tolerance → explicit "insufficient data", not omitted | unit | `pytest tests/test_price_service.py::test_trend_insufficient_data -x` | ❌ Wave 0 |
| SC4 | D-07: trend computed on `total_price` only | unit | `pytest tests/test_price_service.py::test_trend_uses_total_price_only -x` | ❌ Wave 0 |
| D-09 | `verified: false` products shown identically in browse/search | integration | `pytest tests/test_api_products.py::test_unverified_products_shown_identically -x` | ❌ Wave 0 |
| D-11 | Product detail response has no raw `price_points` array/series | integration | `pytest tests/test_api_products.py::test_detail_omits_raw_series -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_price_service.py -x` or the relevant single test file
- **Per wave merge:** `pytest` (full suite)
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/conftest.py` — add an `api_db` fixture (mirrors `catalog_db`/`matching_db`: dedicated `pokemonview_test` DB, seeds `products` + writes controlled `price_points` fixtures, skips gracefully if `MONGODB_URI` unset) plus `app`/`client` fixtures wrapping `create_app()` + `app.test_client()`
- [ ] `tests/test_api_products.py` — covers SC1/SC2/D-01/D-09/D-11
- [ ] `tests/test_price_service.py` — covers SC3/SC4/D-02/D-06/D-07 as pure unit tests against the service layer (no Flask app needed)
- [ ] Framework install: `pip install flask==3.1.3 flask-cors==6.0.5` — no test framework install needed, pytest already present

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Public read-only API per CONTEXT.md phase boundary — no auth in scope |
| V3 Session Management | No | No sessions/cookies used |
| V4 Access Control | No | No protected resources — every route is public read |
| V5 Input Validation | Yes | Validate `product_type` against the fixed enum (`booster_pack`/`booster_box`/`etb`/`booster_bundle`) before using it in any query; if free-text search is implemented via MongoDB `$regex` rather than the recommended in-process Python filter, escape user input with `re.escape()` first |
| V6 Cryptography | No direct concern this phase | `MONGODB_URI` handling already covered by the established `python-dotenv`/`os.environ` pattern (V6-adjacent secrets hygiene, not new cryptography work) |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Regex/NoSQL injection via `q`/`set`/`product_type` query params flowing unsanitized into a MongoDB query | Tampering | Prefer the in-process Python filtering approach (Don't Hand-Roll) which never builds a Mongo query operator from raw user text; if `$regex` is used instead, validate enum fields against a whitelist and `re.escape()` any free-text value before it reaches a query |
| Information disclosure via unhandled exception → Flask debug traceback in a production response | Information Disclosure | Ensure `app.config["DEBUG"] = False` in the production config class; add a generic JSON error handler (`@app.errorhandler(Exception)`) that returns `{"error": "internal_error"}` without a stack trace |
| Overly permissive CORS (`origins: "*"`) shipped to production | Tampering / Information Disclosure | Use an explicit allowed-origins list sourced from an environment variable per deployment environment (dev vs. prod), not a wildcard, once a production frontend origin is known — acceptable to use `"*"` only in local dev config, per CONTEXT.md's note that "the exact allowed-origins configuration is an environment/deployment detail" |

## Sources

### Primary (HIGH confidence)
- MongoDB official docs: Time Series Collection Limitations (`mongodb.com/docs/manual/core/timeseries/timeseries-limitations/`) — read via WebSearch snippet, official source
- MongoDB official docs: `$abs`, `$subtract`, `$group`, `$sort`, `$first`/`$last` aggregation operator reference pages (`mongodb.com/docs/manual/reference/operator/aggregation/...`) — official source
- Flask official docs: Application Factories, Blueprints, Testing (`flask.palletsprojects.com/en/stable/...`) — official source, read via WebSearch snippet since Context7 MCP was unavailable this session

### Secondary (MEDIUM confidence)
- Flask-CORS official docs (`flask-cors.readthedocs.io`) — vendor documentation
- pytest-flask official docs/GitHub (`pytest-flask.readthedocs.io`, `github.com/pytest-dev/pytest-flask`) — vendor documentation
- MongoDB Community forum threads on "latest per group" aggregation patterns — cross-corroborated with official `$group`/`$sort` docs, not standalone
- `.planning/research/ARCHITECTURE.md`, `.planning/research/PITFALLS.md` — this project's own prior research, already MEDIUM-confidence rated at time of authorship

### Tertiary (LOW confidence)
- Community blog posts on Flask app-factory structure (oneuptime.com, hackersandslackers.com, tobywf.com) — used only to corroborate the official-docs pattern, not as a primary source
- pymongo+Flask-factory client-storage convention — general community practice, no single authoritative source found this session (see Assumptions Log A3)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Flask/Flask-CORS versions directly registry-verified via `pip index versions`; not training-data guesses
- Architecture: MEDIUM-HIGH — app-factory/blueprint pattern is standard and cross-corroborated across official docs + this project's own ARCHITECTURE.md; MongoDB aggregation shapes are official-docs-sourced
- Pitfalls: HIGH for the two flagged this session (SET_ORDER derivation, current-price-vs-trend-window confusion) — both directly derived from reading `scripts/catalog_data.py` and `scripts/matching.py` in this session, not assumed

**Research date:** 2026-07-15
**Valid until:** 30 days (stable domain — Flask/MongoDB patterns change slowly; re-verify package versions if planning is delayed past that window)
