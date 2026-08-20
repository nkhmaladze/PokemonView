---
phase: 9
slug: 24h-all-time-price-badges
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-20
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 (backend, `pytest.ini`) / Vitest 4.1.10 + @testing-library/react 16.3.2 (frontend) |
| **Config file** | `pytest.ini` (backend) / `frontend/package.json` (frontend, vitest run) |
| **Quick run command** | `pytest tests/test_price_service.py tests/test_catalog_service.py -x` (backend) — `npm run test -- ProductDetailPage TrendBadge AllTimeRangeBadge` (frontend) |
| **Full suite command** | `pytest` (backend) — `npm run test` (frontend) |
| **Estimated runtime** | ~10-20 seconds per quick run |

---

## Sampling Rate

- **After every task commit:** Run the quick command for whichever side (backend/frontend) the task touched
- **After every plan wave:** Run both full suite commands (`pytest` and `npm run test`)
- **Before `/gsd-verify-work`:** Full suite must be green on both backend and frontend
- **Max feedback latency:** ~20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | PRICE-08 | — | `get_trend_baseline(days=1, tolerance=<new 4h>)` returns a point within ±4h, `None` otherwise | unit | `pytest tests/test_price_service.py -x` | ✅ (extend) | ⬜ pending |
| 09-01-02 | 01 | 1 | PRICE-08 | — | `get_product_detail` sets `trend_24h` to `{pct_change, status:"ok"}` or `insufficient_data`, incl. zero-data branch | unit | `pytest tests/test_catalog_service.py -x` | ✅ (extend) | ⬜ pending |
| 09-01-03 | 01 | 1 | PRICE-08 | — | `GET /products/<id>` response includes `trend_24h` with correct shape/status | integration | `pytest tests/test_api_products.py -x` | ✅ (extend) | ⬜ pending |
| 09-01-04 | 01 | 2 | PRICE-08 | — | `ProductDetailPage` renders a third `TrendBadge` for 24h next to 7d/30d | component | `npm run test -- ProductDetailPage` | ✅ (extend) | ⬜ pending |
| 09-02-01 | 02 | 1 | PRICE-09 | — | `get_all_time_range` returns `None` for zero points, `{high, low}` for 1+ points (incl. `high==low`) | unit | `pytest tests/test_price_service.py -x` | ✅ (extend) | ⬜ pending |
| 09-02-02 | 02 | 1 | PRICE-09 | T-08-D11 | `get_product_detail` sets `all_time_range` incl. zero-data branch, never leaks raw series | unit | `pytest tests/test_catalog_service.py -x` | ✅ (extend) | ⬜ pending |
| 09-02-03 | 02 | 1 | PRICE-09 | — | `GET /products/<id>` response includes `all_time_range` with correct shape | integration | `pytest tests/test_api_products.py -x` | ✅ (extend) | ⬜ pending |
| 09-02-04 | 02 | 2 | PRICE-09 | — | `AllTimeRangeBadge` renders "since we started tracking" label, incl. insufficient-data (—) case | component | `npm run test -- ProductDetailPage AllTimeRangeBadge` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/src/components/AllTimeRangeBadge.test.jsx` — stubs for PRICE-09 (ok / insufficient-data states)
- [ ] `frontend/src/components/AllTimeRangeBadge.module.css` — needed before the component test can assert class names

*Backend: no new test files needed — `tests/test_price_service.py`, `tests/test_catalog_service.py`, and `tests/test_api_products.py` already exist and establish the exact conventions this phase's new cases extend.*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
