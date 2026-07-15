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

*Populated by the planner as concrete task IDs are assigned. Source rows below (from RESEARCH.md's Phase Requirements → Test Map) must map onto specific tasks — none may be silently dropped.*

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD | TBD | TBD | SC1 (SEARCH-01 enabler) | — | `GET /products` supports `q`/`set`/`product_type` filters, combinable (D-08) | integration | `pytest tests/test_api_products.py::test_list_products_filters -x` | ❌ Wave 0 | ⬜ pending |
| TBD | TBD | TBD | SC1 | — | Default sort groups by set, newest-first (D-10, hardcoded `SET_ORDER`) | integration | `pytest tests/test_api_products.py::test_default_sort_order -x` | ❌ Wave 0 | ⬜ pending |
| TBD | TBD | TBD | SC2 (SEARCH-02/PRICE-01) | — | `GET /products/:id` returns current price as total (headline) + item (secondary) | integration | `pytest tests/test_api_products.py::test_product_detail_current_price -x` | ❌ Wave 0 | ⬜ pending |
| TBD | TBD | TBD | SC2 | T-05-Pitfall2 | D-02: last known point returned across a gap (no null just because latest run had a gap) | unit | `pytest tests/test_price_service.py::test_current_price_gap_tolerant -x` | ❌ Wave 0 | ⬜ pending |
| TBD | TBD | TBD | SC2 | — | D-01: zero price_points ever returns `null` + explicit `"no_data_yet"` status, not 404/omitted | integration | `pytest tests/test_api_products.py::test_product_no_price_data -x` | ❌ Wave 0 | ⬜ pending |
| TBD | TBD | TBD | SC3 (PRICE-02) | — | D-03: freshness timestamp is the literal `ts` of the point shown, no computed staleness flag | unit | `pytest tests/test_price_service.py::test_freshness_is_real_ts -x` | ❌ Wave 0 | ⬜ pending |
| TBD | TBD | TBD | SC4 (PRICE-03) | — | D-05: 7d/30d trend within ±2-3 day tolerance | unit | `pytest tests/test_price_service.py::test_trend_baseline_within_tolerance -x` | ❌ Wave 0 | ⬜ pending |
| TBD | TBD | TBD | SC4 | — | D-06: no baseline within tolerance → explicit "insufficient data", not omitted | unit | `pytest tests/test_price_service.py::test_trend_insufficient_data -x` | ❌ Wave 0 | ⬜ pending |
| TBD | TBD | TBD | SC4 | — | D-07: trend computed on `total_price` only | unit | `pytest tests/test_price_service.py::test_trend_uses_total_price_only -x` | ❌ Wave 0 | ⬜ pending |
| TBD | TBD | TBD | D-09 | — | `verified: false` products shown identically in browse/search | integration | `pytest tests/test_api_products.py::test_unverified_products_shown_identically -x` | ❌ Wave 0 | ⬜ pending |
| TBD | TBD | TBD | D-11 | — | Product detail response has no raw `price_points` array/series | integration | `pytest tests/test_api_products.py::test_detail_omits_raw_series -x` | ❌ Wave 0 | ⬜ pending |
| TBD | TBD | TBD | V5 Input Validation | T-05-Sec1 | `product_type` validated against fixed enum; no unescaped `$regex` built from raw `q` | unit | `pytest tests/test_api_products.py::test_product_type_enum_validation -x` | ❌ Wave 0 | ⬜ pending |
| TBD | TBD | TBD | Info disclosure | T-05-Sec2 | Unhandled exception returns generic JSON error, no debug traceback (`DEBUG=False`, global error handler) | integration | `pytest tests/test_api_products.py::test_error_handler_no_traceback -x` | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — add an `api_db` fixture (mirrors `catalog_db`/`matching_db`: dedicated `pokemonview_test` DB, seeds `products` + writes controlled `price_points` fixtures, skips gracefully if `MONGODB_URI` unset) plus `app`/`client` fixtures wrapping `create_app()` + `app.test_client()`
- [ ] `tests/test_api_products.py` — covers SC1/SC2/D-01/D-09/D-11 + input-validation/error-handler security tests
- [ ] `tests/test_price_service.py` — covers SC3/SC4/D-02/D-06/D-07 as pure unit tests against the service layer (no Flask app needed)
- [ ] Framework install: `pip install flask==3.1.3 flask-cors==6.0.5` — no test framework install needed, pytest already present

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
