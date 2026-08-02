# Milestones

## v1.0 Active-Price MVP (Shipped: 2026-08-02)

**Phases completed:** 7 phases, 39 plans, 78 tasks

**Key accomplishments:**

- Established .gitignore, .env.example, and a pinned requirements.txt so real eBay OAuth credentials never enter git while documenting the exact env-var contract Plan 03's verification script will consume.
- Standalone MANUAL-STEPS.md checklist, Claude-drafted price-transparency Growth Check narrative, and a committed active-only-v1 fallback decision for the sold-price API access gate
- Reusable OAuth Client Credentials Grant + Browse API client (`scripts/ebay_client.py`) and a smoke-test entrypoint (`scripts/verify_ebay_access.py`) that acquires a token, searches for real Pokemon sealed product, asserts price+shipping presence, and writes 50-100 listing titles to `fixtures/ebay_listing_titles.json` — authored and syntactically valid, ready for Plan 04's live run.
- Live-verified real eBay Production Browse API access: OAuth Client Credentials Grant succeeded, real Pokemon sealed-product listings returned with both item price and shipping cost, and 100 real listing titles committed to `fixtures/ebay_listing_titles.json` for Phase 4's matching-rule work.
- pymongo==4.17.0 and pytest==8.4.2 pinned into requirements.txt and installed, gated by a human-approved review that confirmed pymongo's [SUS] supply-chain verdict was a false positive
- MongoDB Atlas M0 cluster provisioned and reachable via MONGODB_URI (stored only in gitignored .env); a safe placeholder line documenting the variable was appended to .env.example.
- 16-entry curated CATALOG (4 sets x 4 product types) as a pure Python data module, with Chaos Rising/Ascended Heroes booster_box MSRP gaps resolved via live web research and Pitch Black entries flagged provisional per D-02.
- Idempotent `db/init_collections.py` creating a $jsonSchema-validated, compound-indexed `products` collection and an empty native time-series `price_points` collection, verified live against MongoDB Atlas.
- Authored a discoverable four-test pytest suite (test_catalog_completeness, test_seed_idempotent, test_schema_validator_rejects_malformed, test_query_by_set_and_type) plus a dedicated pokemonview_test-database fixture, intentionally RED until Plan 06's seed script lands.
- Idempotent MongoDB seed script (bulk_write/UpdateOne upsert on deterministic slug _id) populates the real `pokemonview.products` collection with all 16 curated catalog entries and turns the full 4-test pytest contract suite green.
- Pinned and installed apscheduler==3.11.3 (in-process job scheduler for the ingestion worker) behind a mandatory human supply-chain legitimacy checkpoint that resolved a false-positive [SUS] verdict.
- Extended `db/init_collections.py` to idempotently bootstrap `active_listings`, `ingestion_locks` (TTL on `expires_at`), and `ingestion_runs` (descending `started_at` index), and corrected stale docstrings that mislabeled `price_points` as Phase 3's write target instead of Phase 4's.
- Wave-0 RED test scaffold for the active-listing ingestion worker — `ingest_db` fixture plus five REQ-tagged pytest tests for INGEST-01/02/03, all collectible and intentionally failing until Plan 03-04 implements `scripts/ingest_worker.py`
- Built scripts/ingest_worker.py — the lock-guarded, idempotent ingestion worker (build_query, MongoDB TTL lock, upsert_listings, run_ingestion_once, main with --once/APScheduler) that turns all five Plan 03-03 RED tests GREEN.
- Live Production Browse API verification deferred — EBAY_CLIENT_ID/EBAY_CLIENT_SECRET confirmed still absent from `.env` following the prior credential-loss incident; no source files modified.
- rapidfuzz==3.14.5 pinned and installed after a blocking human legitimacy checkpoint approved the [SUS]/unknown-downloads false positive, mirroring the apscheduler/pymongo precedent.
- Authored `matching_db` pytest fixture plus 14 failing contract tests in `tests/test_matching.py` pinning the full MATCH-01/02/03 + D-04 behavioral contract before `scripts/matching.py` exists.
- Implemented `scripts/matching.py`'s deterministic core: word-boundary-safe `normalize()`, a strict two-tier `match_listing()` (exact keyword rule, then bounded RapidFuzz fallback), and `check_exclusion()`'s ReDoS-safe lot/damaged/counterfeit keyword pass — turning all eight MATCH-01/MATCH-02 Nyquist RED tests GREEN.
- Statistical outlier filter (2-population-stddev, skip-below-3) and median-based price_points aggregation composed into a run-scoped `run_matching_once()` orchestrator that matches, excludes, flags outliers, and aggregates every listing an ingestion run touched — turning the remaining five MATCH-03 Nyquist RED tests GREEN.
- Wired `run_matching_once()` into `run_ingestion_once()` as a second, decoupled stage after the fetch loop, merging D-04's flat match-count fields onto the `ingestion_runs` document — the activation point that makes MATCH-01/02/03 run in the live pipeline.
- Pinned and installed flask==3.1.3 and flask-cors==6.0.5 behind an approved blocking human legitimacy checkpoint, enabling the REST API layer for the rest of Phase 5
- Added `listing_count` (Option A) to `aggregate_and_write()` so every price_points document records the exact sample size its item/total price medians were computed over, closing the sample-size gap named in 05-RESEARCH.md Pitfall 3.
- Authored the shared api_db/app/client pytest fixtures plus 26 RED tests (test_price_service.py, test_catalog_service.py, test_api_products.py) that lock the entire Phase 5 API contract — response shapes, status codes, CORS, and error handling — before any api/ code exists.
- `api/services/price_service.py` with three pure MongoDB-query functions (gap-tolerant current price, ±3-day tolerance-window trend baseline via aggregation pipeline, zero-guarded percent-change) turning `tests/test_price_service.py` fully GREEN.
- In-process catalog filtering/search (D-08) with SET_ORDER sorting (D-10) and total-price-led current price + 7d/30d trend detail assembly (D-01/D-07/D-11), turning `tests/test_catalog_service.py` fully GREEN
- Flask create_app() factory with a lazily-constructed MongoClient, env-driven Flask-CORS, a no-traceback global error handler, and a thin products blueprint wiring GET /products / GET /products/<id> to catalog_service — turning tests/test_api_products.py fully GREEN and completing Phase 5's serving layer.
- Narrowed the products route's except clause to a new `InvalidProductTypeError(ValueError)` subclass so internal ValueErrors surface as 500s, and comma-split `CORS_ORIGINS` into a real per-origin list so the documented production multi-origin format actually works — both proven by regression tests that fail on the pre-fix code.
- Greenfield Vite + React 19 SPA scaffolded with a real Vitest/jsdom/Testing Library harness, UI-SPEC design tokens as CSS custom properties, and a native-fetch REST data layer (getProducts/getProductDetail) proven green against 5 unit tests.
- TrendBadge (4-state color-coded 7d/30d percent-change badge) and PriceDisplay (total-led headline with always-visible item-price secondary line) — pure formatters over the exact API contract, both TDD'd green with 9 unit tests and zero recomputation.
- Dependency-free ISO-to-"X ago" formatter built on the native `Intl.RelativeTimeFormat` API, plus a `FreshnessIndicator` component rendering "Data as of {relative time}" from `current_price.as_of` — both TDD'd RED-then-GREEN, delivering PRICE-02.
- SearchBar (controlled, instant, no-debounce text input) and FilterChips (single-select product_type + set_name toggle groups using catalog_service.py's exact raw enum values) — the interactive half of SEARCH-01, both fully unit-tested and ready for CatalogPage (06-05) to wire into live in-memory filtering.
- ProductRow (dense clickable list row with null-safe thumbnail and muted no-data state) and CatalogPage (loader-fed flat list with live in-memory search/chip filtering and empty state) — the primary browse surface, composing the Wave 2 primitives into the poe.ninja-style dense catalog, both TDD'd green with 7 new unit tests.
- ProductDetailPage — the `/products/:productId` route composing PriceDisplay (total-led, Display size), 7d/30d TrendBadges, FreshnessIndicator, and a null-safe sample-size/MSRP/release-date metadata block over the exact GET /products/:id contract — TDD'd green with 4 unit tests, delivering SEARCH-02 and making PRICE-01/02/03 user-observable together for the first time.
- createBrowserRouter route table wiring CatalogPage/ProductDetailPage to their loaders with a centralized ProductNotFound errorElement, mounted via RouterProvider in main.jsx, and live-verified end-to-end against the running Flask API — completing SEARCH-01/SEARCH-02 and closing out Phase 6.
- 1. [Rule 1 - Bug] Fixed a `TypeError` from naive-vs-aware datetime subtraction
- gunicorn==26.0.0 pinned in requirements.txt (human-approved past a package-legitimacy gate) and wsgi.py added as the sole `create_app()` call site gunicorn resolves as `wsgi:app`
- Single-stage Dockerfile + .dockerignore + fly.toml declaring one image / two always-on Fly.io process types (web via gunicorn, worker via APScheduler), with http_service scoped to web only and zero secret literals.
- 1. [Rule 1 - Bug] Worker stdout was fully block-buffered, hiding startup/status prints from `fly logs`
- Vite SPA deployed to Vercel production at https://frontend-black-one-22.vercel.app, wired to the live Fly API via VITE_API_BASE_URL, with CORS_ORIGINS pinned to the real Vercel origin — completing SC-1 end-to-end.

---
