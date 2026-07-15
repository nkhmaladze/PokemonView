---
phase: 05-flask-rest-api-active-price-serving
verified: 2026-07-15T05:00:00Z
status: passed
score: 12/12 must-haves verified
behavior_unverified: 0
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 10/12
  gaps_closed:
    - "Flask-CORS emits Access-Control-Allow-Origin sourced from CORS_ORIGINS env var, with wildcard only as a documented dev default and an explicit comma-separated origins list working in prod (CR-02)"
    - "An unexpected/internal exception (as opposed to the deliberate V5 product_type ValueError) propagates to the global @app.errorhandler(Exception) and surfaces as a generic 500 internal_error — never silently reinterpreted as a client-facing 400 (CR-01)"
  gaps_remaining: []
  regressions: []
human_verification: []
---

# Phase 5: Flask REST API (active-price serving) Verification Report

**Phase Goal:** Build the Flask REST API service that serves active-price and catalog data — a Flask application factory, price/catalog services, and product list/detail endpoints — over the existing MongoDB catalog and price_points time-series data, completing the "enabling/serving layer" ahead of Phase 6's user-observable frontend consumption.
**Verified:** 2026-07-15T05:00:00Z
**Status:** passed
**Re-verification:** Yes — after gap closure (05-07-PLAN.md, executed 2026-07-15)

## Goal Achievement

This is a re-verification cycle. The previous cycle (2026-07-14T23:45:00Z) found 10/12 must-haves verified and 2 BLOCKER-level gaps (CR-01 exception masking, CR-02 broken CORS), both matching 05-REVIEW.md findings. A gap-closure plan (05-07-PLAN.md) was executed to fix both. This cycle applies full 3-level verification to the two previously-failed truths and a regression check to the ten previously-verified truths.

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `GET /products` returns the catalog and supports searching/filtering by product name and set (SC1/SEARCH-01) | ✓ VERIFIED (regression) | Unchanged since prior cycle. `api/blueprints/products.py::list_products` still delegates to `catalog_service.list_products`. Re-ran `pytest tests/test_api_products.py::test_list_products_200 tests/test_api_products.py::test_list_filter_by_set_and_type tests/test_api_products.py::test_list_free_text_search -q` independently — pass. |
| 2 | `GET /products/:id` returns a product's detail including current price as total (item+shipping) alongside item-only price (SC2/SEARCH-02/PRICE-01) | ✓ VERIFIED (regression) | `catalog_service.get_product_detail`/`_product_summary` unchanged in this plan's diff. Full suite includes `test_product_detail_current_price` — pass. |
| 3 | The API exposes each product's data-freshness timestamp from the last successful ingestion (SC3/PRICE-02) | ✓ VERIFIED (regression) | `current_price.as_of` logic unchanged. `test_freshness_is_real_ts` pass (full suite run). |
| 4 | The API returns each product's 7d/30d active-price percent change (SC4/PRICE-03) | ✓ VERIFIED (regression) | `get_product_detail`'s trend assembly unchanged. `test_trend_baseline_within_tolerance`, `test_trend_insufficient_data`, `test_trend_uses_total_price_only` pass (full suite run). |
| 5 | `flask==3.1.3` / `flask-cors==6.0.5` pinned in requirements.txt and installed/importable | ✓ VERIFIED (regression) | Unchanged. Not touched by 05-07. |
| 6 | `aggregate_and_write()` writes a `listing_count` field on every new `price_points` document | ✓ VERIFIED (regression) | Unchanged. `tests/test_matching.py` pass (full suite run). |
| 7 | The Wave-0 RED scaffold (`api_db`/`app`/`client` fixtures + tests) locked the phase's HTTP/service contract | ✓ VERIFIED (regression) | `pytest tests/ --collect-only -q` → 58 tests collected, 0 errors (reproduced directly, up from 56 pre-gap-closure — the 2 new regression tests collect cleanly). |
| 8 | `price_service.py`'s three functions are pure, DB-taking-as-arg, with no top-level side effects | ✓ VERIFIED (regression) | Unchanged. Not touched by 05-07. `tests/test_price_service.py` pass (full suite run). |
| 9 | `catalog_service.list_products`/`get_product_detail` filter in-process only, validate the `product_type` enum, sort by hardcoded `SET_ORDER`, never leak a raw `price_points` series | ✓ VERIFIED (regression) | Re-read `api/services/catalog_service.py` directly — in-process filtering/sorting logic unchanged; only the enum-validation exception type changed (`InvalidProductTypeError` instead of bare `ValueError`), which is the CR-01 fix itself (see truth #11 below). `tests/test_catalog_service.py` pass (full suite run). |
| 10 | `create_app()` builds its `MongoClient` lazily inside the factory only, sets `DEBUG=False`, and registers the `products` blueprint | ✓ VERIFIED (regression) | Re-read `api/app.py` directly — `MongoClient` construction still occurs only inside `create_app()`'s body; blueprint registration still happens inside the function. Only the CORS-origins parsing and the added `app.logger.exception(...)` line changed. |
| 11 | **[Gap #11 — CR-01, now closed]** An unexpected/internal exception (as opposed to the deliberate V5 `product_type` exception) propagates to the global error handler and surfaces as a generic 500 — never silently reinterpreted as a 400 | ✓ VERIFIED | Read `api/services/catalog_service.py` directly: new `class InvalidProductTypeError(ValueError)` (line 27) is raised only by the enum-validation check inside `list_products` (line 113); `sort_key`'s `SET_ORDER.index()` (line 139) is untouched and still raises the plain base `ValueError`. Read `api/blueprints/products.py` directly: the route's except clause now reads `except catalog_service.InvalidProductTypeError:` (line 49) — narrowed from the base `ValueError`. Independently ran `pytest tests/test_api_products.py::test_unregistered_set_name_returns_500_not_400 -q` (monkeypatches `SET_ORDER` to `[]`, forcing every product's `set_name` to be unregistered) — **1 passed**: response is `500 {"error": "internal_error"}`, not `400`. This is the exact CR-01 reproduction scenario from 05-REVIEW.md, now closed. |
| 12 | **[Gap #12 — CR-02, now closed]** Flask-CORS emits `Access-Control-Allow-Origin` sourced from `CORS_ORIGINS`, with the wildcard dev default working AND an explicit comma-separated origins list working in production | ✓ VERIFIED | Read `api/app.py` directly (lines 55-65): `cors_origins_raw` is read from env, then parsed as `[cors_origins_raw]` when literally `"*"`, else comma-split with `.strip()` and empty-string filtering, producing a real per-origin list passed to `CORS(app, resources={r"/products*": {"origins": cors_origins}})`. Independently ran `pytest tests/test_api_products.py::test_multi_origin_cors_matches_each_origin -q` (sets `CORS_ORIGINS=https://a.example,https://b.example`, builds a fresh app via `create_app()`, asserts each of the two origins is reflected in `Access-Control-Allow-Origin` AND that an unconfigured third origin is NOT reflected) — **1 passed**. Independently ran `pytest tests/test_api_products.py::test_cors_header_present -q` (wildcard dev-default path) — **1 passed**, no regression. This is the exact CR-02 reproduction scenario from 05-REVIEW.md, now closed. |

**Score:** 12/12 truths verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `api/services/catalog_service.py` | `InvalidProductTypeError(ValueError)` raised only by the V5 enum check | ✓ VERIFIED | Present at line 27, substantive (docstring + is-a ValueError), wired (raised at line 113, imported/referenced in `api/blueprints/products.py`). |
| `api/blueprints/products.py` | `except catalog_service.InvalidProductTypeError` (narrowed) | ✓ VERIFIED | Present at line 49, wired — `catalog_service` already imported module-level; no bare `except Exception` introduced. |
| `api/app.py` | `CORS_ORIGINS` comma-split into a real list before Flask-CORS | ✓ VERIFIED | Present at lines 55-65, wired into `CORS(...)` call at line 69. `r"/products*"` resource key deliberately left unchanged (WR-02 out of scope, confirmed via `grep`). |
| `api/app.py` | Opportunistic `app.logger.exception(...)` in the global handler (WR-04) | ✓ VERIFIED | Present at line 86, inside `handle_exception`, before the 500 JSON response — does not add exception detail to the response body (confirmed `test_error_handler_no_traceback` still passes, asserting no "Traceback"/`File "` substrings in the body). |
| `tests/test_api_products.py` | Two new regression tests | ✓ VERIFIED | `test_unregistered_set_name_returns_500_not_400` (line 169) and `test_multi_origin_cors_matches_each_origin` (line 225) present, both independently run and passing. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `api/blueprints/products.py`'s except clause | `catalog_service.InvalidProductTypeError` | `except catalog_service.InvalidProductTypeError:` | WIRED | Confirmed — `catalog_service` module already imported at top of file; no new import line needed. |
| `create_app`'s parsed `cors_origins` list | Flask-CORS's `origins=` argument | `CORS(app, resources={r"/products*": {"origins": cors_origins}})` | WIRED | Confirmed at api/app.py:67-70; a two-origin `CORS_ORIGINS` env value is reflected per-origin (independently reproduced via the regression test). |
| The un-caught internal `ValueError` (from `sort_key`) | The global `@app.errorhandler(Exception)` | Falls through the narrowed `except` in the route | WIRED | Confirmed — `test_unregistered_set_name_returns_500_not_400` proves the 500 path is reached, not the 400 path. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| CR-01 regression (independently re-run, not trusting SUMMARY) | `pytest tests/test_api_products.py::test_unregistered_set_name_returns_500_not_400 -q` | `1 passed` | PASS |
| CR-02 regression (independently re-run) | `pytest tests/test_api_products.py::test_multi_origin_cors_matches_each_origin -q` | `1 passed` | PASS |
| No regression on wildcard CORS dev default | `pytest tests/test_api_products.py::test_cors_header_present -q` | `1 passed` | PASS |
| No regression on no-traceback-leak guarantee (now with added logging) | `pytest tests/test_api_products.py::test_error_handler_no_traceback -q` | `1 passed` | PASS |
| No regression on the deliberate V5 400 path | `pytest tests/test_api_products.py::test_product_type_enum_validation -q` | `1 passed` | PASS |
| Full collection stays clean | `pytest tests/ --collect-only -q` | `58 tests collected` (up from 56 pre-gap-closure) | PASS |
| Full workspace suite, run once (independently, live MongoDB Atlas) | `pytest tests/ -q` | `58 passed in 56.35s` | PASS |

### Requirements Coverage

Per ROADMAP.md, Phase 5 owns **no requirement IDs directly** — enabling serving layer. Confirmed unchanged and consistent in this cycle:

| Requirement | Description | Status | Evidence |
|--------------|-------------|--------|----------|
| SEARCH-01 | Browse/search catalog by name or set | ENABLED (not owned) | `.planning/REQUIREMENTS.md` line 39-40: `- [ ]`, traceability table line 86: `Phase 6 \| Pending`. Consistent. |
| SEARCH-02 | Product detail page data | ENABLED (not owned) | REQUIREMENTS.md line 87: `Phase 6 \| Pending`. Consistent. |
| PRICE-01 | Total-led current price | ENABLED (not owned) | REQUIREMENTS.md line 30, 80: `- [ ]` / `Phase 6 \| Pending`. The prior verification cycle's correction (reverting an erroneous Plan-05-02 mark-complete) is confirmed still in place — no regression to the traceability fix. |
| PRICE-02 | Freshness timestamp | ENABLED (not owned) | REQUIREMENTS.md line 81: `Phase 6 \| Pending`. Consistent. |
| PRICE-03 | 7d/30d trend badge | ENABLED (not owned) | REQUIREMENTS.md line 82: `Phase 6 \| Pending`. Consistent. |

**05-07-PLAN.md frontmatter** lists `requirements: [SEARCH-01, SEARCH-02, PRICE-01, PRICE-02, PRICE-03]` (enabling, matching the established Phase 5 convention) and its SUMMARY correctly records `requirements-completed: []`, consistent with the "not owned until Phase 6" rule. No orphaned requirements found.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `api/services/catalog_service.py` | ~168-186 (unchanged) | Duplicate/racy `get_current_price` call in `get_product_detail` | ⚠️ Warning | WR-01 (05-REVIEW.md) — deliberately out of scope for 05-07's gap-closure; still present, carried forward as a non-blocking warning, unchanged from prior cycle. |
| `api/app.py` | 69 (unchanged) | Unanchored CORS resource regex `r"/products*"` | ⚠️ Warning | WR-02 (05-REVIEW.md) — deliberately left untouched per 05-07-PLAN.md's explicit scope statement ("WR-02 is explicitly out of scope for this gap-closure plan; do not touch it"). Confirmed still unanchored via direct read; not a blocker for this phase's success criteria. |
| `scripts/matching.py` | ~164-166 (unchanged) | Lot-quantity exclusion regex gap (misses quantities starting with "1") | ⚠️ Warning | WR-03 (05-REVIEW.md) — pre-existing Phase 4 pattern, not touched by this phase, carried forward for visibility only. |

No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` debt markers found in any file modified by 05-07 (`api/services/catalog_service.py`, `api/blueprints/products.py`, `api/app.py`, `tests/test_api_products.py`) — confirmed via direct grep.

### Human Verification Required

None. Both previously-open gaps were closed and verified programmatically: direct code reads confirming the structural fix (distinct exception subclass; comma-split CORS parsing), plus independent re-execution (not trusting SUMMARY.md's claims) of the specific regression tests and the full 58-test suite against live MongoDB Atlas.

### Gaps Summary

No gaps remain. Both BLOCKER-level findings from the prior verification cycle (05-VERIFICATION.md gaps #11/#12, matching 05-REVIEW.md CR-01/CR-02) are closed:

1. **CR-01 (exception masking) — CLOSED.** `catalog_service.py` now raises a distinct `InvalidProductTypeError(ValueError)` only from the V5 enum-validation check; the `products` blueprint's except clause narrows to that subclass. An unregistered `set_name` (the `sort_key`/`SET_ORDER.index()` data-integrity scenario) now correctly propagates to the global error handler and surfaces as a 500, never a masked 400 — proven both by direct code inspection and by an independently re-run regression test (`test_unregistered_set_name_returns_500_not_400`, 1 passed).
2. **CR-02 (broken production CORS) — CLOSED.** `api/app.py` now comma-splits `CORS_ORIGINS` into a real per-origin list before handing it to Flask-CORS, with the `"*"` wildcard dev default preserved as a single-element list. A two-origin production-style value now correctly reflects `Access-Control-Allow-Origin` per configured origin and withholds it for an unconfigured origin — proven both by direct code inspection and an independently re-run regression test (`test_multi_origin_cors_matches_each_origin`, 1 passed), with no regression to the existing wildcard-default test.

All 4 ROADMAP.md success criteria remain VERIFIED (unaffected by the gap-closure diff, confirmed via full-suite regression). Requirements traceability (SEARCH-01/02, PRICE-01/02/03 all Pending/Phase-6) remains consistent, with no regression to the prior cycle's traceability correction. The full pytest suite (58 tests: 56 pre-existing + 2 new regressions) was independently re-run in this verification cycle and passed cleanly against live MongoDB Atlas — not merely accepted from SUMMARY.md's claim.

Phase 5's goal — a read-only Flask REST API serving catalog/search/current-price/freshness/trend data, safe for Phase 6 to build against — is fully achieved.

---

_Verified: 2026-07-15T05:00:00Z_
_Verifier: Claude (gsd-verifier)_
