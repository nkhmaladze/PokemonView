---
phase: 05-flask-rest-api-active-price-serving
verified: 2026-07-14T23:45:00Z
status: gaps_found
score: 10/12 must-haves verified
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "Flask-CORS emits Access-Control-Allow-Origin sourced from CORS_ORIGINS env var, with wildcard only as a documented dev default and an explicit comma-separated origins list working in prod (T-05-03, 05-06 must_have)"
    status: failed
    reason: "CORS_ORIGINS is passed to Flask-CORS as a raw string with no comma-splitting. flask-cors 6.0.5's ensure_iterable() wraps any string in a single-element list and matches it via literal (non-regex) comparison, so the documented production configuration ('an explicit comma-separated list of allowed origins', api/config.py docstring) never matches any real Origin header. Reproduced directly against the installed flask-cors==6.0.5: CORS_ORIGINS='https://a.com,https://b.com' + a request with Origin: https://a.com produces NO Access-Control-Allow-Origin header at all. This is CR-02 in 05-REVIEW.md, unresolved in the current code."
    artifacts:
      - path: "api/app.py"
        issue: "CORS(app, resources={r\"/products*\": {\"origins\": os.environ.get(\"CORS_ORIGINS\", ...)}}) passes the raw env string straight through; never split on commas."
      - path: "api/config.py"
        issue: "Docstring documents 'an explicit comma-separated list of allowed origins' as the required production value, but nothing in the codebase parses that format."
    missing:
      - "Split CORS_ORIGINS on commas into a real list (or leave literal '*') before passing to Flask-CORS's origins= argument, per 05-REVIEW.md CR-02's suggested fix."
      - "A regression test asserting a two-origin CORS_ORIGINS value actually produces a matching Access-Control-Allow-Origin header for each configured origin (the current test_cors_header_present only exercises the wildcard dev default, so it did not catch this)."
  - truth: "An unexpected/internal exception (as opposed to the deliberate V5 product_type ValueError) must propagate to the global @app.errorhandler(Exception) and surface as a generic 500 internal_error — never be silently reinterpreted as a client-facing 400 (T-05-01/T-05-02 design intent, 05-06-PLAN.md Task 1 action text: 'Do NOT catch bare Exception here... an unexpected error must propagate to the global app error handler')"
    status: failed
    reason: "api/blueprints/products.py's list_products route wraps catalog_service.list_products in a bare `except ValueError`, intending to catch only the V5 enum-validation ValueError. But catalog_service.list_products's internal sort_key() calls SET_ORDER.index(product['set_name']) with no fallback, which itself raises ValueError (not KeyError) for any product whose set_name is not one of the four hardcoded SET_ORDER strings (e.g. a seed-data typo or a future set added before SET_ORDER is updated). That unrelated ValueError is caught by the same except block and misreported as 400 {'error':'invalid_product_type'} to the client -- even on a bare GET /products with no product_type filter at all -- hiding a real server-side data-integrity bug from both the client and any 4xx/5xx-based monitoring. Reproduced directly: SET_ORDER.index('Some Bogus Set') raises ValueError, confirming the masking path. This is CR-01 in 05-REVIEW.md, unresolved in the current code."
    artifacts:
      - path: "api/blueprints/products.py"
        issue: "except ValueError: return jsonify({'error': 'invalid_product_type'}), 400 -- too broad, catches any ValueError from catalog_service.list_products, not only the V5 enum-validation one."
      - path: "api/services/catalog_service.py"
        issue: "sort_key()'s SET_ORDER.index(product['set_name']) raises a plain ValueError with no distinguishing type when a product's set_name isn't registered in SET_ORDER."
    missing:
      - "A distinct exception type (e.g. InvalidProductTypeError(ValueError)) raised only by the V5 enum-validation check, so the route can catch that specific type and let any other ValueError (e.g. from sort_key) propagate to the global error handler as a 500, per 05-REVIEW.md CR-01's suggested fix."
      - "A regression test proving a data-integrity bug (unregistered set_name) surfaces as a 500, not a 400."
human_verification: []
---

# Phase 5: Flask REST API (active-price serving) Verification Report

**Phase Goal:** A read-only Flask REST API serves the catalog, search, current price, freshness, and active-price trend data that the frontend needs.
**Verified:** 2026-07-14T23:45:00Z
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `GET /products` returns the catalog and supports searching/filtering by product name and set (SC1/SEARCH-01) | VERIFIED | `api/blueprints/products.py::list_products` delegates to `catalog_service.list_products`, which supports `set_name`/`product_type`/`q` filters entirely in-process. `pytest tests/test_api_products.py::test_list_products_200/test_list_filter_by_set_and_type/test_list_free_text_search` pass (confirmed in the full 56/56 GREEN run). |
| 2 | `GET /products/:id` returns a product's detail including current price as total (item+shipping) alongside item-only price (SC2/SEARCH-02/PRICE-01) | VERIFIED | `catalog_service.get_product_detail` composes `_product_summary` (`current_price.total_price`/`current_price.item_price`). `test_product_detail_current_price` passes. Manually confirmed field shape by reading `api/services/catalog_service.py` lines 30-70. |
| 3 | The API exposes each product's data-freshness timestamp from the last successful ingestion (SC3/PRICE-02) | VERIFIED | `current_price.as_of` = the literal `ts` of the latest `price_points` document (`get_current_price`, no time-window filter, D-02/D-03). `test_freshness_is_real_ts` and `test_product_detail_current_price` pass. |
| 4 | The API returns each product's 7d/30d active-price percent change (SC4/PRICE-03) | VERIFIED | `get_product_detail` builds `trend_7d`/`trend_30d` via `get_trend_baseline` + `compute_pct_change`, each `{pct_change, status}` with `"insufficient_data"` when no baseline is in tolerance. `test_trend_baseline_within_tolerance`, `test_trend_insufficient_data`, `test_trend_uses_total_price_only` pass. |
| 5 | `flask==3.1.3` / `flask-cors==6.0.5` pinned in requirements.txt and installed/importable, behind a human-approved package-legitimacy gate (05-01) | VERIFIED | `requirements.txt` contains both exact pins after `rapidfuzz==3.14.5`. `python -c "import flask, flask_cors; print(flask.__version__, flask_cors.__version__)"` → `3.1.3 6.0.5` (reproduced directly). Human approval recorded in 05-01-SUMMARY.md Decisions Made. |
| 6 | `aggregate_and_write()` writes a `listing_count` field (== `len(included)`) on every new `price_points` document, additive/backward-compatible, D-11 gap-on-empty preserved (05-02) | VERIFIED | `scripts/matching.py` lines 287-304 show `"listing_count": len(included)` inside the `insert_one` dict, guarded by the unchanged `if not included: return False` at line 295. `pytest tests/test_matching.py` (17 tests incl. `test_price_points_records_listing_count`, `test_price_points_skipped_when_zero_included`) pass. |
| 7 | The Wave-0 RED scaffold (`api_db`/`app`/`client` fixtures + 26 tests) locked the phase's HTTP/service contract before any `api/` code existed, and collection stayed clean throughout (05-03) | VERIFIED | `tests/conftest.py` has `api_db`/`app`/`client` fixtures (lines 165, 228, 245); `pytest tests/ --collect-only -q` → 56 tests collected, 0 errors (reproduced directly). |
| 8 | `price_service.py`'s three functions are pure, DB-taking-as-arg, with no top-level side effects, and correctly separate the window-less current-price rule (D-02) from the bounded ±3-day trend-baseline rule (D-05/D-06) (05-04) | VERIFIED | `api/services/price_service.py` read directly — `get_current_price` has no `ts` range filter; `get_trend_baseline` uses a `$match` bounded window + `$abs`/`$subtract`/`$sort`/`$limit`; `compute_pct_change` guards `baseline_total == 0`. All 6 `tests/test_price_service.py` tests pass. |
| 9 | `catalog_service.list_products`/`get_product_detail` filter in-process only (no Mongo query operator built from raw user text — T-05-01), validate the `product_type` enum, sort by hardcoded `SET_ORDER`, and never leak a raw `price_points` series in the detail response (D-11) (05-05) | VERIFIED | `api/services/catalog_service.py` read directly — `list_products` calls `db.products.find({})` once and filters/sorts entirely in Python; `get_product_detail` attaches only `current_price`/`trend_7d`/`trend_30d`, no array of points. All 9 `tests/test_catalog_service.py` tests pass. |
| 10 | `create_app()` builds its `MongoClient` lazily inside the factory only (never at import time), sets `DEBUG=False`, and registers the `products` blueprint (05-06) | VERIFIED | `api/app.py` read directly — `MongoClient` construction and `os.environ` read occur only inside `create_app()`'s body; blueprint import/registration happens inside the function. `python -c "import api.app"` (exercised transitively via the full pytest run) triggers no DB connection at import. |
| 11 | An unexpected/internal exception (as opposed to the deliberate V5 `product_type` `ValueError`) propagates to the global error handler and surfaces as a generic 500 — never silently reinterpreted as a 400 (T-05-01/T-05-02 design intent) | **FAILED** | `api/blueprints/products.py`'s bare `except ValueError` also catches `catalog_service.list_products`'s internal `SET_ORDER.index()` `ValueError` (raised for any unregistered `set_name` — a real data-integrity bug), misreporting it as `400 invalid_product_type` instead of letting it reach the 500 handler. Reproduced directly: `SET_ORDER.index("Some Bogus Set")` raises `ValueError`. Matches 05-REVIEW.md CR-01 exactly, unresolved in current code. |
| 12 | Flask-CORS emits `Access-Control-Allow-Origin` sourced from `CORS_ORIGINS`, with the wildcard dev default working AND an explicit comma-separated origins list working in production (T-05-03) | **FAILED** | `api/app.py` passes the raw `CORS_ORIGINS` env string straight to Flask-CORS with no comma-splitting. Reproduced directly against the installed `flask-cors==6.0.5`: `CORS_ORIGINS="https://a.com,https://b.com"` + a request with `Origin: https://a.com` produces **no** `Access-Control-Allow-Origin` header at all — the documented production configuration format is completely non-functional. Matches 05-REVIEW.md CR-02 exactly, unresolved in current code. (Only the wildcard dev-default path is covered by `test_cors_header_present`, so this was not caught by the existing test suite.) |

**Score:** 10/12 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `requirements.txt` | `flask==3.1.3`, `flask-cors==6.0.5` pinned | VERIFIED | Present, appended after `rapidfuzz==3.14.5`; both importable at stated versions. |
| `scripts/matching.py` | `aggregate_and_write()` writes `listing_count` | VERIFIED | Present, additive, D-11 guard unchanged. |
| `tests/conftest.py` | `api_db`/`app`/`client` fixtures | VERIFIED | Present at lines 165/228/245; lazy `api.app` import inside `app` fixture. |
| `tests/test_price_service.py`, `tests/test_catalog_service.py`, `tests/test_api_products.py` | Full HTTP/service contract as tests | VERIFIED | 6 + 9 + 11 tests present, all passing GREEN (part of the 56/56 full-suite run). |
| `api/services/price_service.py` | `get_current_price`, `get_trend_baseline`, `compute_pct_change`, `TREND_TOLERANCE_DAYS` | VERIFIED | All present, substantive, pure (no import-time side effects verified by direct grep/read). |
| `api/services/catalog_service.py` | `list_products`, `get_product_detail`, `SET_ORDER`/`VALID_PRODUCT_TYPES`/`TREND_WINDOWS` | VERIFIED | All present, substantive; composes `price_service`. |
| `api/app.py` | `create_app()` factory | VERIFIED (with defects) | Present and wired, but contains the CR-02 CORS defect (gap #12 above). |
| `api/config.py`, `api/db.py` | `Config` class, `get_db()` | VERIFIED | Present, substantive, no import-time side effects. |
| `api/blueprints/products.py` | `products_bp` with 2 routes | VERIFIED (with defects) | Present and wired, but contains the CR-01 exception-masking defect (gap #11 above). |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `tests/conftest.py` `app` fixture | `api/app.py::create_app` | lazy `from api.app import create_app` | WIRED | Confirmed at conftest.py:239, no top-level import. |
| `api/blueprints/products.py` | `api/services/catalog_service.py` | `from api.services import catalog_service` | WIRED | Confirmed import + calls to `list_products`/`get_product_detail`. |
| `api/blueprints/products.py` | `api/db.py::get_db()` | `from api.db import get_db` | WIRED | Confirmed import + usage in both routes. |
| `api/app.py::create_app` | `api/blueprints/products.py` | lazy `from api.blueprints.products import products_bp` + `app.register_blueprint(products_bp)` | WIRED | Confirmed inside `create_app` body, not at module scope. |
| `api/services/catalog_service.py` | `api/services/price_service.py` | `from api.services.price_service import compute_pct_change, get_current_price, get_trend_baseline` | WIRED | Confirmed import at top of catalog_service.py, all three functions called inside `_product_summary`/`get_product_detail`. |
| `scripts/matching.py::aggregate_and_write` | `api/services/price_service.py::get_current_price` | shared `price_points` document shape (`listing_count` field) | WIRED | `get_current_price` returns the whole document including `listing_count`; `catalog_service._product_summary` reads `current_point.get("listing_count")`, treating absence as `None` for pre-Plan-05-02 documents. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full Phase-5 + prior-phase test suite | `pytest tests/ -q` (run once, live MongoDB Atlas) | `56 passed in 55.03s` | PASS |
| Collection stays clean | `pytest tests/ --collect-only -q` | `56 tests collected` | PASS |
| `SET_ORDER.index()` raises plain `ValueError` for an unregistered set (reproduces CR-01) | `python3 -c "SET_ORDER.index('Some Bogus Set')"` | `ValueError: 'Some Bogus Set' is not in list` | FAIL (confirms gap #11) |
| Comma-separated `CORS_ORIGINS` never matches a real `Origin` header (reproduces CR-02) | Direct Flask-CORS reproduction against installed `flask-cors==6.0.5` with `origins="https://a.com,https://b.com"` and `Origin: https://a.com` | `Access-Control-Allow-Origin` header absent (`None`) | FAIL (confirms gap #12) |
| Unanchored CORS regex `r"/products*"` matches unintended paths (reproduces WR-02, info-level, not gated) | `re.compile(r'/products*').match('/productAdmin')` | `True` | Confirms WR-02, not a blocking gap for this phase's SC |

### Requirements Coverage

Per ROADMAP.md, Phase 5 owns **no requirement IDs directly** — it is an enabling serving layer. SEARCH-01/SEARCH-02/PRICE-01/PRICE-02/PRICE-03 are referenced in every plan's frontmatter `requirements:` field as "enables," not "owns," and become user-observable (and requirement-complete) in Phase 6.

| Requirement | Source Plans | Description | Status | Evidence |
|--------------|-------------|-------------|--------|----------|
| SEARCH-01 | 05-01, 05-03, 05-05, 05-06 | Browse/search catalog by name or set | ENABLED (not owned) | `GET /products` filter/search implemented and tested; requirement remains `Pending`/mapped to Phase 6 in REQUIREMENTS.md. |
| SEARCH-02 | 05-01, 05-03, 05-05, 05-06 | Product detail page data | ENABLED (not owned) | `GET /products/:id` implemented and tested; requirement remains `Pending`/Phase 6. |
| PRICE-01 | 05-01, 05-02, 05-03, 05-04, 05-05, 05-06 | Total-led current price | ENABLED (not owned) | `current_price.total_price`/`item_price` implemented and tested; requirement **corrected during this verification** — see "Traceability Inconsistency" below. |
| PRICE-02 | 05-01, 05-03, 05-04, 05-06 | Freshness timestamp | ENABLED (not owned) | `current_price.as_of` implemented and tested; requirement remains `Pending`/Phase 6. |
| PRICE-03 | 05-01, 05-03, 05-04, 05-06 | 7d/30d trend badge | ENABLED (not owned) | `trend_7d`/`trend_30d` implemented and tested; requirement remains `Pending`/Phase 6. |

**Orphaned requirements:** None. ROADMAP.md's traceability note and every plan's frontmatter are consistent in framing these five IDs as Phase-5-enabled/Phase-6-owned.

#### Traceability Inconsistency — Found and Resolved

**Finding:** Plan 05-02's SUMMARY.md (and the state-update step that ran after it) marked **PRICE-01** as complete in `.planning/REQUIREMENTS.md` — both the top-level checkbox (`- [x] **PRICE-01**`) and the traceability table row (`| PRICE-01 | Phase 6 | Complete |`) — while Plans 05-01, 05-03, 05-04, 05-05, and 05-06 all deliberately left every one of their listed requirement IDs (SEARCH-01, SEARCH-02, PRICE-01, PRICE-02, PRICE-03) unmarked, each independently citing the same reasoning: REQUIREMENTS.md's own traceability note (line 89) states "Phase 5 (Flask API serving layer)... own[s] no requirements directly... Phase 5 serves the display requirements (PRICE-01/02/03, SEARCH-01/02) that become user-observable in Phase 6" — and maps all five IDs to **Phase 6**, not Phase 5, in the traceability table itself.

**Determination:** The treatment used by Plans 05-01/03/04/05/06 is correct per REQUIREMENTS.md's own documented rule. Plan 05-02's mark-complete action was an error — it marked a requirement complete one full phase before REQUIREMENTS.md's own traceability table says it becomes user-observable, and Phase 5 shipped only a RED-then-GREEN backend service/test layer, not a user-facing capability (no frontend exists yet; Phase 6 is next in the roadmap). Marking PRICE-01 complete at this point misrepresents project state.

**Resolution:** Fixed during this verification pass. `.planning/REQUIREMENTS.md` line 30 reverted to `- [ ] **PRICE-01**` and line 80 reverted to `| PRICE-01 | Phase 6 | Pending |`, restoring consistency with the other four requirement IDs and with the document's own traceability note. This is a documentation-only fix (no code changed) and does not by itself constitute a gap in Phase 5's goal achievement — it is recorded here for auditability and because the original inconsistency, if left uncorrected, would have caused Phase 6 planning to under-count its own scope (PRICE-01 would appear already "Complete" before the SPA that makes it user-observable exists).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `api/blueprints/products.py` | ~40-46 | Overly broad `except ValueError` masks an unrelated internal `ValueError` (`SET_ORDER.index()`) as a client-facing 400 | 🛑 Blocker | CR-01 in 05-REVIEW.md — hides real server-side data-integrity bugs from clients and monitoring; violates the plan's own stated design intent that unexpected errors must reach the 500 handler. Reproduced directly in this verification. |
| `api/app.py` | ~55-62 | `CORS_ORIGINS` env string passed to Flask-CORS with no comma-splitting | 🛑 Blocker | CR-02 in 05-REVIEW.md — the documented production multi-origin configuration format is completely non-functional; a deployed frontend would be silently blocked by the browser with zero server-side error. Reproduced directly in this verification. |
| `api/services/catalog_service.py` | ~139-186 | Duplicate/racy `get_current_price` call in `get_product_detail` | ⚠️ Warning | WR-01 in 05-REVIEW.md — a concurrent ingestion write between the two calls could make `current_price.total_price` and the trend baseline's reference `ts` come from two different documents. Not reproduced as failing under current test conditions; a correctness/consistency risk, not a functional-failure gap for this phase's success criteria. |
| `api/app.py` | ~57-61 | Unanchored CORS resource regex `r"/products*"` | ⚠️ Warning | WR-02 in 05-REVIEW.md — currently harmless (only `/products` and `/products/<id>` exist) but does not constrain CORS the way it visually appears to; reproduced directly (matches `/productAdmin`). |
| `scripts/matching.py` | ~164-166 | Lot-quantity exclusion regexes never match a quantity whose value starts with digit "1" (e.g. "x10") | ⚠️ Warning | WR-03 in 05-REVIEW.md — pre-existing Phase 4 (MATCH-02) pattern in a file this phase's Plan 05-02 also touched (for the unrelated `listing_count` addition); not part of Phase 5's SEARCH/PRICE success criteria, carried forward for visibility only. |
| `api/app.py` | ~64-77 | Global exception handler never logs the caught exception server-side | ⚠️ Warning | WR-04 in 05-REVIEW.md — operational-visibility gap (unhandled 500s are invisible in logs); not a functional-correctness failure of this phase's success criteria. |
| `scripts/matching.py` | ~127 | Fuzzy-match phrase dict can silently collapse two catalog products with an identical canonical phrase | ℹ️ Info | IN-01 in 05-REVIEW.md — currently harmless given the curated 16-product catalog. |
| `scripts/matching.py` | ~64-65 | `FUZZY_SCORE_CUTOFF`/`FUZZY_MARGIN` are unconfigurable magic numbers | ℹ️ Info | IN-02 in 05-REVIEW.md — low priority per the review's own note. |

No `TBD`/`FIXME`/`XXX` debt markers found in any Phase-5-modified file.

### Human Verification Required

None. All findings in this report were verified programmatically (direct code read, direct reproduction against the installed `flask-cors==6.0.5`, and a full 56/56 GREEN pytest run against live MongoDB Atlas).

### Gaps Summary

Phase 5's core observable goal — a read-only Flask API serving catalog/search/current-price/freshness/trend data — **is functionally achieved and behaviorally proven** (all 4 ROADMAP success criteria VERIFIED; 56/56 tests GREEN against live data). However, two BLOCKER-level correctness bugs already identified by this phase's own code review (05-REVIEW.md CR-01, CR-02) remain unresolved in the shipped code:

1. **CR-01 (exception masking):** a genuine server-side data-integrity bug (an unregistered `set_name`) would be silently reported to clients as a 400 `invalid_product_type` instead of surfacing as a 500, defeating the phase's own documented 4xx/5xx-boundary design intent.
2. **CR-02 (broken production CORS):** the documented production `CORS_ORIGINS` configuration format (a comma-separated origins list) is completely non-functional against the installed `flask-cors==6.0.5` — every intended origin would be silently rejected by the browser with no server-side error, which would present as "the deployed frontend can't reach the API" during/after Phase 7 launch with no diagnostic trail.

Both bugs are narrow, well-understood, and already have concrete fixes proposed in 05-REVIEW.md. Neither currently manifests against the phase's own test suite (all current catalog `set_name` values are registered in `SET_ORDER`, and `test_cors_header_present` only exercises the wildcard dev default) — which is exactly why they were not caught before code review, and exactly why they should be closed with a small follow-up plan before Phase 6/7 build further on top of this API.

A third issue — Plan 05-02's incorrect `REQUIREMENTS.md` mark-complete of PRICE-01 — was found and corrected during this verification pass (see "Traceability Inconsistency" above); it required no code change and is not counted among the gaps above.

---

_Verified: 2026-07-14T23:45:00Z_
_Verifier: Claude (gsd-verifier)_
