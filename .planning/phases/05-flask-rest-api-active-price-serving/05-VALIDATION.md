---
phase: 5
slug: flask-rest-api-active-price-serving
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-14
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 (already installed and configured) |
| **Config file** | `pytest.ini` (`pythonpath = .`, `testpaths = tests`) |
| **Quick run command** | `pytest tests/test_api_products.py -x` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~10 seconds (small catalog, ≤16 products, no live network calls) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_price_service.py -x` or the relevant single test file
- **After every plan wave:** Run `pytest` (full suite)
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~10 seconds

---

## Per-Task Verification Map

*Task IDs assigned during planning (2026-07-15). Every RESEARCH.md Phase Requirements → Test Map row is represented; the "integration"-only rows were split into a service-layer unit level (test_catalog_service.py) plus the true HTTP level (test_api_products.py) so each implementation plan turns its own test file GREEN — no source row was dropped. All test files are scaffolded RED in Plan 05-03 (Wave 2) and turned GREEN by the implementing plan/task in the "Green by" column.*

| Test / Behavior | Green by | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|-----------------|----------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| test_current_price_gap_tolerant | 05-04 T1 | 3 | SC2 / D-02 | T-05-Pitfall2 | Last known point returned across a gap (no window) | unit | `pytest tests/test_price_service.py::test_current_price_gap_tolerant -x` | 05-03 (RED) | ⬜ pending |
| test_current_price_none_when_no_points | 05-04 T1 | 3 | SC2 / D-01 | — | Zero points ever → None (→ no_data_yet upstream) | unit | `pytest tests/test_price_service.py::test_current_price_none_when_no_points -x` | 05-03 (RED) | ⬜ pending |
| test_freshness_is_real_ts | 05-04 T1 | 3 | SC3 / D-03 | — | Freshness is the literal `ts`, no staleness flag | unit | `pytest tests/test_price_service.py::test_freshness_is_real_ts -x` | 05-03 (RED) | ⬜ pending |
| test_trend_uses_total_price_only | 05-04 T1 | 3 | SC4 / D-07 | — | Trend % on total_price only; zero-baseline guard | unit | `pytest tests/test_price_service.py::test_trend_uses_total_price_only -x` | 05-03 (RED) | ⬜ pending |
| test_trend_baseline_within_tolerance | 05-04 T2 | 3 | SC4 / D-05 | — | 7d/30d baseline within ±3 day tolerance | unit | `pytest tests/test_price_service.py::test_trend_baseline_within_tolerance -x` | 05-03 (RED) | ⬜ pending |
| test_trend_insufficient_data | 05-04 T2 | 3 | SC4 / D-06 | — | No baseline in tolerance → explicit insufficient_data | unit | `pytest tests/test_price_service.py::test_trend_insufficient_data -x` | 05-03 (RED) | ⬜ pending |
| test_list_products_filters | 05-05 T1 | 4 | SC1 / D-08 | T-05-01 | Combinable set/type/q filters (in-process, no $regex) | unit (service) | `pytest tests/test_catalog_service.py::test_list_products_filters -x` | 05-03 (RED) | ⬜ pending |
| test_default_sort_order | 05-05 T1 | 4 | SC1 / D-10 | — | Grouped by set in hardcoded SET_ORDER (not release_date) | unit (service) | `pytest tests/test_catalog_service.py::test_default_sort_order -x` | 05-03 (RED) | ⬜ pending |
| test_unverified_products_shown_identically | 05-05 T1 | 4 | D-09 | — | verified:false shown identically | unit (service) | `pytest tests/test_catalog_service.py::test_unverified_products_shown_identically -x` | 05-03 (RED) | ⬜ pending |
| test_list_includes_price_and_freshness | 05-05 T1 | 4 | D-04 / D-12 | — | List cards carry total (headline) + item (secondary) + as_of | unit (service) | `pytest tests/test_catalog_service.py::test_list_includes_price_and_freshness -x` | 05-03 (RED) | ⬜ pending |
| test_product_type_enum_validation (service) | 05-05 T1 | 4 | V5 Input Validation | T-05-01 | product_type validated against fixed enum (ValueError) | unit (service) | `pytest tests/test_catalog_service.py::test_product_type_enum_validation -x` | 05-03 (RED) | ⬜ pending |
| test_detail_current_price_total_led | 05-05 T2 | 4 | SC2 / PRICE-01 / D-12 | — | Detail current price total-led, item secondary | unit (service) | `pytest tests/test_catalog_service.py::test_detail_current_price_total_led -x` | 05-03 (RED) | ⬜ pending |
| test_detail_no_data_yet | 05-05 T2 | 4 | D-01 | — | Priced-zero product → no_data_yet + null, not 404/omitted | unit (service) | `pytest tests/test_catalog_service.py::test_detail_no_data_yet -x` | 05-03 (RED) | ⬜ pending |
| test_detail_unknown_id_returns_none | 05-05 T2 | 4 | SC2 | — | Unknown id → None (→ 404 upstream) | unit (service) | `pytest tests/test_catalog_service.py::test_detail_unknown_id_returns_none -x` | 05-03 (RED) | ⬜ pending |
| test_detail_omits_raw_series (service) | 05-05 T2 | 4 | D-11 | T-05-05 | Detail has no raw price_points array/series | unit (service) | `pytest tests/test_catalog_service.py::test_detail_omits_raw_series -x` | 05-03 (RED) | ⬜ pending |
| test_list_products_200 | 05-06 T2 | 5 | SC1 (SEARCH-01) | — | GET /products → 200 JSON array of catalog | integration | `pytest tests/test_api_products.py::test_list_products_200 -x` | 05-03 (RED) | ⬜ pending |
| test_list_filter_by_set_and_type | 05-06 T2 | 5 | SC1 / D-08 | — | ?set + ?product_type combinable at HTTP layer | integration | `pytest tests/test_api_products.py::test_list_filter_by_set_and_type -x` | 05-03 (RED) | ⬜ pending |
| test_list_free_text_search | 05-06 T2 | 5 | SC1 / D-08 | T-05-01 | ?q free-text, no Mongo query operator from raw text | integration | `pytest tests/test_api_products.py::test_list_free_text_search -x` | 05-03 (RED) | ⬜ pending |
| test_product_detail_current_price | 05-06 T2 | 5 | SC2 / PRICE-01 | — | GET /products/:id → 200 total-led current price + as_of | integration | `pytest tests/test_api_products.py::test_product_detail_current_price -x` | 05-03 (RED) | ⬜ pending |
| test_product_no_price_data | 05-06 T2 | 5 | D-01 | — | Zero-price product → 200 no_data_yet + null, not 404 | integration | `pytest tests/test_api_products.py::test_product_no_price_data -x` | 05-03 (RED) | ⬜ pending |
| test_detail_unknown_id_404 | 05-06 T2 | 5 | SC2 | — | Unknown id → 404 {"error":"not_found"} | integration | `pytest tests/test_api_products.py::test_detail_unknown_id_404 -x` | 05-03 (RED) | ⬜ pending |
| test_detail_omits_raw_series (HTTP) | 05-06 T2 | 5 | D-11 | T-05-05 | Detail JSON has no raw price_points array | integration | `pytest tests/test_api_products.py::test_detail_omits_raw_series -x` | 05-03 (RED) | ⬜ pending |
| test_unverified_products_shown_identically (HTTP) | 05-06 T2 | 5 | D-09 | — | verified:false present in /products with same shape | integration | `pytest tests/test_api_products.py::test_unverified_products_shown_identically -x` | 05-03 (RED) | ⬜ pending |
| test_product_type_enum_validation (HTTP) | 05-06 T2 | 5 | V5 Input Validation | T-05-01 | ?product_type=bad → 400 {"error":"invalid_product_type"} | integration | `pytest tests/test_api_products.py::test_product_type_enum_validation -x` | 05-03 (RED) | ⬜ pending |
| test_error_handler_no_traceback | 05-06 T2 | 5 | Info disclosure | T-05-02 | Unhandled error → 500 generic JSON, no traceback (DEBUG=False + global handler) | integration | `pytest tests/test_api_products.py::test_error_handler_no_traceback -x` | 05-03 (RED) | ⬜ pending |
| test_cors_header_present | 05-06 T2 | 5 | CORS config | T-05-03 | Access-Control-Allow-Origin emitted; env-driven origins | integration | `pytest tests/test_api_products.py::test_cors_header_present -x` | 05-03 (RED) | ⬜ pending |
| test_price_points_records_listing_count | 05-02 T2 | 1 | PRICE-01 (sample size) | T-05-02a | Option A: listing_count == len(included) written to price_points | unit (matching) | `pytest tests/test_matching.py::test_price_points_records_listing_count -x` | 05-02 (new) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*All Wave 0 scaffolding is authored by **Plan 05-03** (Wave 2). Framework install is **Plan 05-01** (Wave 1). Task IDs are cross-referenced in the Per-Task Verification Map above.*

- [ ] `tests/conftest.py` (05-03 T1) — add an `api_db` fixture (mirrors `catalog_db`/`matching_db`: dedicated `pokemonview_test` DB, seeds `products` via `seed_catalog`, leaves `price_points` initialized-empty for per-test controlled inserts, skips gracefully if `MONGODB_URI` unset) plus `app`/`client` fixtures wrapping `create_app(mongodb_uri=..., db_name="pokemonview_test")` + `app.test_client()`
- [ ] `tests/test_price_service.py` (05-03 T2) — pure unit tests for the price service (no Flask): D-01/D-02/D-03/D-05/D-06/D-07
- [ ] `tests/test_catalog_service.py` (05-03 T2) — pure service-layer unit tests (no Flask): D-01/D-04/D-08/D-09/D-10/D-11/D-12 + V5 product_type enum validation
- [ ] `tests/test_api_products.py` (05-03 T3) — HTTP integration tests via the Flask test client: 200/400/404/500 status codes, JSON envelopes, CORS header, no-traceback error handler
- [ ] Framework install (05-01): `pip install flask==3.1.3 flask-cors==6.0.5` behind the package-legitimacy human gate — no test-framework install needed (pytest already present; pytest-flask intentionally skipped)

*Note: the RESEARCH.md map listed several behaviors as "integration / test_api_products.py"; these are covered at BOTH the service-unit level (test_catalog_service.py) and the HTTP level (test_api_products.py) so each implementation plan (05-04/05/06) turns its own file GREEN. Nothing was dropped.*

---

## Manual-Only Verifications

*If none: "All phase behaviors have automated verification."*

All phase behaviors have automated verification — no manual-only checks identified. (MongoDB Atlas connectivity itself follows the existing `pytest.skip()`-on-missing-`MONGODB_URI` convention rather than requiring a manual step.)

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
