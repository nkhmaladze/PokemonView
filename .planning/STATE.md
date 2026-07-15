---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
current_phase: 7
current_phase_name: v1 active-price
status: verifying
stopped_at: Completed 06-05-PLAN.md
last_updated: "2026-07-15T19:00:11.273Z"
last_activity: 2026-07-15
last_activity_desc: Phase 06 complete, transitioned to Phase 7
progress:
  total_phases: 8
  completed_phases: 5
  total_plans: 34
  completed_plans: 33
  percent: 63
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-07-12)

**Core value:** A user can look up a specific pack/box/ETB and see whether it's priced fairly right now, backed by both live eBay asking prices and actual sold-price history.
**Current focus:** Phase 06 — react-spa-frontend-active-price-product

## Current Position

Phase: 7 — Launch & Hardening (v1 active-price)
Plan: Not started
Status: Phase complete — ready for verification
Last activity: 2026-07-15 — Phase 06 complete, transitioned to Phase 7

Progress: [██████████] 97%

## Performance Metrics

**Velocity:**

- Total plans completed: 25
- Average duration: — min
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 02 | 6 | - | - |
| 04 | 5 | - | - |
| 05 | 7 | - | - |
| 06 | 7 | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
| Phase 01 P01 | 1min | - tasks | - files |
| Phase 01 P02 | 2min | 3 tasks | 3 files |
| Phase 01 P03 | 2min | 2 tasks | 2 files |
| Phase 02 P03 | 20min | 2 tasks | 2 files |
| Phase 02 P01 | 5min | 2 tasks | 1 files |
| Phase 02 P02 | 10min | 2 tasks | 1 files |
| Phase 02 P04 | 8min | 2 tasks | 2 files |
| Phase 02 P05 | 5min | 2 tasks | 3 files |
| Phase 02 P06 | 10min | 2 tasks | 1 files |
| Phase 03 P01 | 10min | 2 tasks | 1 files |
| Phase 03 P02 | 2min | 2 tasks | 1 files |
| Phase 03 P03 | 2min | 2 tasks | 2 files |
| Phase 03 P04 | 4min | 3 tasks | 2 files |
| Phase 03 P05 | 2min | 1 tasks | 0 files |
| Phase 04 P02 | 15min | 3 tasks | 2 files |
| Phase 04 P01 | 5min | 2 tasks | 1 files |
| Phase 04 P03 | 12min | 2 tasks | 1 files |
| Phase 04 P04 | 6min | 2 tasks | 2 files |
| Phase 04 P05 | 5min | 1 tasks | 1 files |
| Phase 05 P01 | 11min | 2 tasks | 1 files |
| Phase 05 P02 | 10min | 2 tasks | 2 files |
| Phase 05 P03 | 4min | 3 tasks | 4 files |
| Phase 05 P04 | 8 | 2 tasks | 3 files |
| Phase 05 P05 | 15min | 2 tasks | 1 files |
| Phase 05 P06 | 10min | 2 tasks | 5 files |
| Phase 05 P07 | 12min | 2 tasks | 4 files |
| Phase 06 P01 | 15min | 3 tasks | 10 files |
| Phase 06 P02 | 4min | 2 tasks | 6 files |
| Phase 06 P03 | 3min | 2 tasks | 5 files |
| Phase 06 P04 | 10min | 2 tasks | 6 files |
| Phase 06 P05 | ~6min | 2 tasks | 6 files |
| Phase 06 P06 | ~10min | 1 tasks | 3 files |
| Phase 06 P07 | ~8min | 3 tasks | 5 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: Horizontal-layer build (data model/catalog → ingestion → matching → API → frontend), not vertical MVP slices.
- [Roadmap]: Sold-price features (INGEST-04, PRICE-04/05/06) isolated in contingent Phase 8; Phases 1-7 ship a complete active-price v1 independent of Marketplace Insights API approval.
- [Roadmap]: Phase 1 is a feasibility/access gate — MI API access is a go/no-go decision resolved early, not a build assumption.
- [Phase ?]: Pinned requests==2.34.2 / python-dotenv==1.2.2 per research findings, not stale STACK.md versions
- [Phase 01]: Growth Check narrative frames applicant as existing business entity doing price-transparency/resale-analytics, not personal project
- [Phase 01]: Committed denied-case fallback: ship active-listing-only v1 (Phases 1-7), defer sold-price to contingent Phase 8
- [Phase ?]: Phase 01 Plan 03: shipping_cost defaults to 0.00 when shippingOptions absent, matching research skeleton
- [Phase 02-03]: Chaos Rising booster_box MSRP resolved to $161.64 via live Pokemon Center listing confirmation
- [Phase 02-03]: Ascended Heroes standard booster_box entry kept (SKU confirmed to exist); MSRP pattern-matched to $161.64
- [Phase 02-03]: ~11 of 16 catalog entries left with image_url=None (unresolved TCGplayer IDs) rather than fabricated, per plan instruction
- [Phase 02]: Approved pymongo==4.17.0 install after human review confirmed [SUS] verdict was a false positive from unresolved download-count telemetry
- [Phase 02]: Used exact version pins (pymongo==4.17.0, pytest==8.4.2) per registry-verified research rather than unpinned ranges
- [Phase 02-02]: User provisioned MongoDB Atlas M0 (free tier) as the MongoDB instance, matching documented stack choice over local Homebrew install
- [Phase 02-04]: products $jsonSchema validator allows null on release_date/msrp/image_url (Pitfall 3, D-02) so Pitch Black's provisional pre-release documents seed cleanly
- [Phase 02-04]: price_points created empty now with final timeseries options (timeField ts, metaField product_id, granularity hours) to avoid a data-losing drop-and-recreate migration in Phase 3
- [Phase 02-05]: Deferred scripts.seed_catalog import into test_seed_idempotent function body (plan's fallback instruction) since scripts/seed_catalog.py does not exist until Plan 02-06 and top-level import would break --collect-only
- [Phase 02-06]: Ran python -m scripts.seed_catalog directly against the real pokemonview Atlas database (not just the test DB) to prove idempotency end-to-end
- [Phase 02-06]: D-02 Pitch Black post-release re-verification follow-up recorded in SUMMARY.md only (no .planning/todos/ directory exists yet)
- [Phase 03-01]: Approved apscheduler==3.11.3 install after human review confirmed [SUS] verdict (T-03-SC) was a false positive from recent-release-date and missing download telemetry
- [Phase 03-01]: Used exact version pin apscheduler==3.11.3 (registry-verified latest per 03-RESEARCH.md) matching project's existing pinning convention
- [Phase 03-02]: TDD for the collection-bootstrap task was verified via inline RED/GREEN runs of the plan's own automated verify command plus a live MongoDB integration check, rather than a separate committed pytest file, since the persisted ingest_db fixture/tests are Plan 03-03's scope
- [Phase 03-03]: ingest_db fixture mirrors catalog_db structurally but targets active_listings/ingestion_locks/ingestion_runs and does not seed catalog data
- [Phase 03-03]: Used exactly-representable float values (50.00, 4.50, 54.50) in test_price_and_shipping_captured to keep == assertions safe
- [Phase ?]: [Phase 03-04]: Extracted access_token = token['access_token'] from get_app_token()'s dict return before calling search_sealed_listings, matching ebay_client.py's actual signature rather than the plan action text's shorthand
- [Phase ?]: [Phase 03-04]: shipping_cost computed as round(total_cost(item) - item_price, 2) so total_price always equals ebay_client.total_cost(item) exactly, avoiding a second independent shipping-extraction code path
- [Phase 03-05]: Deferred live eBay Production Browse API verification for INGEST-01/02/03 — EBAY_CLIENT_ID/EBAY_CLIENT_SECRET confirmed still absent from .env; deferral recorded per plan's explicit acceptable-terminal-state design, phase completes on Plan 03-04's automated proof
- [Phase ?]: [Phase 04-02]: lot/damaged/counterfeit synthetic end-to-end test titles include all of the target product's required_keywords so match resolution is deterministic (Tier-1), decoupled from untested Tier-2 fuzzy scoring
- [Phase ?]: [Phase 04-02]: end-to-end run_matching_once count contract (listings_matched includes later-excluded matched listings) derived by tracing RESEARCH.md's own code example literally
- [Phase 04]: [Phase 04-01]: Approved rapidfuzz==3.14.5 install after human review confirmed [SUS]/unknown-downloads verdict was the same telemetry-gap false-positive class already approved for apscheduler and pymongo
- [Phase ?]: [Phase 04-03]: Removed 'packs'/'bundles' from LOT_PATTERNS' quantity-noun group (RESEARCH.md's literal pattern) because catalog display_name text legitimately contains '(6 Packs)'/'(36 Packs)', which would have falsely triggered lot-exclusion on real booster_bundle/booster_box listings and broken the locked test_exclusion_does_not_flag_legitimate_bundle test
- [Phase ?]: [Phase 04-04]: Extended run_matching_once's per-item isolation to catch AttributeError (title=None) alongside KeyError/ValueError/TypeError, since the plan's own behavior spec requires isolating missing/None titles
- [Phase ?]: [Phase 04-04]: Fixed a pre-existing test_price_points_median_aggregation bug (exact ts equality) to a tolerance comparison — MongoDB BSON dates truncate to millisecond precision and this project's MongoClient is not tz_aware, so exact equality against a microsecond-precision aware datetime could never pass regardless of implementation
- [Phase ?]: None beyond the plan as written for 04-05 - implementation matched 04-PATTERNS.md's insertion point and flat-field convention exactly
- [Phase ?]: [Phase 05-01]: Approved flask==3.1.3 and flask-cors==6.0.5 install after human review confirmed [SUS]/unknown-downloads verdict was the same telemetry-gap false-positive class already approved for pymongo, apscheduler, and rapidfuzz
- [Phase ?]: [Phase 05-01]: Used registry-verified flask-cors==6.0.5 (not stale STACK.md 5.x) and deliberately skipped pytest-flask and gunicorn per 05-RESEARCH.md
- [Phase ?]: [Phase 05-02]: Option A adopted for sample-size gap - listing_count = len(included) written on every non-empty price_points document, additive/backward-compatible, per 05-CONTEXT.md/05-RESEARCH.md's explicit ask; missing listing_count on pre-change documents treated as null downstream, not backfilled
- [Phase 05-03]: api_db fixture leaves price_points initialized-but-empty (unlike catalog_db's full seed) so each test controls its own gap/tolerance-window price_points scenario
- [Phase 05-03]: list_products/get_product_detail response dicts use the exact JSON Response Contract field names (id, not _id) since routes jsonify() them with no further transformation
- [Phase 05-03]: requirements SEARCH-01/02, PRICE-01/02/03 not marked complete by Plan 05-03 — REQUIREMENTS.md's traceability table maps them to Phase 6 (user-observable), not Phase 5 (enabling/serving layer)
- [Phase ?]: [Phase 05-04]: Split the single-file price_service.py implementation across two commits matching the plan's Task 1/Task 2 TDD boundary to preserve atomic per-task commit granularity
- [Phase ?]: [Phase 05-04]: Kept get_current_price and get_trend_baseline as two distinctly-named functions rather than one parameterized helper, per 05-RESEARCH.md Pitfall 2, so window-less vs windowed behavior can never be silently conflated
- [Phase ?]: [Phase 05-05]: msrp descending secondary sort key
- [Phase 05-06]: Requirements SEARCH-01/02, PRICE-01/02/03 remain unmarked in REQUIREMENTS.md by Phase 5 (enabling/serving layer) per established convention; marked complete in Phase 6 (user-observable)
- [Phase 05-06]: create_app(mongodb_uri=None, db_name=Config.DB_NAME) uses Config.DB_NAME as the literal default expression, matching the plan's locked signature exactly
- [Phase 05]: InvalidProductTypeError(ValueError) subclass introduced so the products route can catch only the deliberate V5 enum-validation failure, letting internal ValueErrors (e.g. unregistered set_name) surface as 500 instead of being masked as 400 (CR-01)
- [Phase 05]: CORS_ORIGINS comma-split into a real per-origin list before Flask-CORS init, with the '*' wildcard dev default preserved as a single-element list, so the documented production multi-origin format actually works (CR-02)
- [Phase ?]: [Phase 06-01]: Approved vite@8.1.4, @vitejs/plugin-react@6.0.3, react-router@7.18.1 (version-7 line, unified package not react-router-dom), vitest@4.1.10 after human re-verification against live npm registry confirmed [SUS] too-new verdicts were false positives
- [Phase ?]: [Phase 06-01]: Deleted orphaned public/icons.svg alongside plan-listed Vite boilerplate (App.jsx/App.css/assets/, template index.css) since it was exclusively referenced by deleted App.jsx
- [Phase ?]: [Phase 06-01]: Reworded api/client.js doc comment to avoid the literal string "axios" so the plan's own acceptance-criteria grep (no-axios check) passes against the whole file including comments
- [Phase 06-02]: Reworded PriceDisplay.jsx doc comment to avoid literal string 'listing_count' so the plan's own acceptance-criteria grep passes against the whole file including comments
- [Phase 06-02]: Fixed a bug in this plan's own PriceDisplay.test.jsx 'does not render listing_count' assertion (loose /5/ regex false-matched inside rendered $150.00); tightened to exact-match + /listing/i queries
- [Phase ?]: [Phase 06-03]: No deviations required - RESEARCH.md's formatRelativeTime code example and UI-SPEC's Copywriting Contract for FreshnessIndicator were followed exactly with no ambiguity
- [Phase 06-04]: PRODUCT_TYPE_OPTIONS/SET_OPTIONS raw values copied verbatim from api/services/catalog_service.py's VALID_PRODUCT_TYPES/SET_ORDER (no invented product types) — Guarantees FilterChips emits byte-exact API vocabulary per plan's key_links requirement
- [Phase 06-04]: SearchBar.test.jsx uses a local stateful ControlledSearchBar test wrapper so userEvent.type can drive real keystroke behavior — A static value/no-op-onChange fixture would revert the DOM value after every simulated keystroke, making multi-character typing untestable
- [Phase ?]: [Phase 06-05]: Trend badges in ProductRow render defensively (only when trend_7d/trend_30d present) since GET /products list contract omits them until 06-06's detail endpoint - no backend change made
- [Phase ?]: [Phase 06-05]: CatalogPage.test.jsx mocks only useLoaderData from react-router (importOriginal spread) so MemoryRouter/Link stay real for ProductRow's Link
- [Phase ?]: [Phase 06-05]: Placeholder thumbnail glyph derived from product_type via a small letter map (P/B/N/E) rather than an SVG icon asset
- [Phase 06]: [Phase 06-06]: Fixed a bug in ProductDetailPage.test.jsx's own MSRP/release_date null-fallback assertions - exact-match getByText false-failed since those strings are part of larger text nodes; switched to regex matchers
- [Phase 06-07]: Task 3 live end-to-end checkpoint approved by user against a real running Flask API (port 5001, Atlas-backed MongoDB) — browse/filter, detail (price/trend/freshness/sample-size), and 404 states all confirmed correct; dev servers stopped after approval since Task 3 writes no files

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues that affect future work]

- [Phase 1 → Phase 8]: Marketplace Insights API access is approval-gated and may be denied; Phase 8 (sold-price) is contingent on the Phase 1 outcome.
- [Phase 01 -> future eBay-dependent phases]: A prior continuation-agent crash overwrote .env, wiping the previously-entered EBAY_CLIENT_ID/EBAY_CLIENT_SECRET from Phase 1 Plan 01-04. User confirmed loss and does not yet have replacement values (pending eBay response). Non-blocking for Phase 2 (no eBay dependency), but EBAY_CLIENT_ID, EBAY_CLIENT_SECRET, and EBAY_ENV=production must be re-added to .env before any phase requiring live eBay API calls proceeds.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-07-15T18:42:57.059Z
Stopped at: Completed 06-05-PLAN.md
Resume file: 
None
