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

> Reconciled 2026-08-20 against the plan set actually created by `/gsd-plan-phase 9`
> (five plans across three waves, tracer-first). The behaviours below are unchanged
> from the draft map; only the Task ID / Plan / Wave columns were re-keyed to the
> real plans, and the two backend rows the draft merged were split to match the
> task boundaries.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | PRICE-08 | T-09-01, T-09-05 | TRACER — `trend_24h` flows `price_points` → `get_product_detail` → JSON → a third `TrendBadge` ordered first on the page | integration + component | `pytest tests/test_api_products.py -x -q` and `cd frontend && npm test -- ProductDetailPage --run` | ✅ (extend) | ⬜ pending |
| 09-01-02 | 01 | 1 | PRICE-08 | — | `get_trend_baseline(days=1, tolerance_days=4/24)` accepts both inclusive window edges (−20h, −28h), rejects one step outside each and the 4-day default-tolerance case; `trend_24h` present in the zero-data early-return branch | unit | `pytest tests/test_price_service.py tests/test_catalog_service.py -x -q` | ✅ (extend) | ⬜ pending |
| 09-02-01 | 02 | 1 | PRICE-09 | T-09-05 | `AllTimeRangeBadge` renders `$low – $high` (en dash), the equal-bounds case, and a muted `—` for explicit insufficient-data, `null` and an absent prop | component | `cd frontend && npm test -- AllTimeRangeBadge --run` | ❌ W0 | ⬜ pending |
| 09-02-02 | 02 | 1 | PRICE-09 | — | Badge stylesheet is token-only, two states, no directional colour; class names asserted for both states | component | `cd frontend && npm test -- AllTimeRangeBadge --run` | ❌ W0 | ⬜ pending |
| 09-03-01 | 03 | 2 | PRICE-09 | T-09-01, T-09-03 | `get_all_time_range` returns `None` only for zero points, equal bounds for one point, true spread for many; order-independent, precision-preserving, product-scoped | unit | `pytest tests/test_price_service.py -x -q` | ✅ (extend) | ⬜ pending |
| 09-03-02 | 03 | 2 | PRICE-09 | T-09-04 | `get_product_detail` sets `all_time_range` on both branches incl. the zero-data early return; the field is two scalars plus a status, never series-shaped (D-11) | unit | `pytest tests/test_catalog_service.py -x -q` | ✅ (extend) | ⬜ pending |
| 09-04-01 | 04 | 3 | PRICE-08, PRICE-09 | T-09-02 | `GET /products/<id>` carries both new keys with exact key sets at zero, one and many points; the zero-point response carries all four badge fields | integration | `pytest tests/test_api_products.py -x -q` | ✅ (extend) | ⬜ pending |
| 09-04-02 | 04 | 3 | PRICE-08, PRICE-09 | T-09-04, T-09-07 | All 16 catalog products return all four badge fields in both data states; the per-key raw-series scan passes against a response provably containing both new keys; 404 and CORS unchanged | integration | `pytest tests/test_api_products.py -x -q` | ✅ (extend) | ⬜ pending |
| 09-05-01 | 05 | 3 | PRICE-09 | T-09-08 | The caption `All-time range (since we started tracking)` renders verbatim, in its locked position between the trend row and the history section, styled from existing tokens only | component | `cd frontend && npm test -- ProductDetailPage --run` | ✅ (extend) | ⬜ pending |
| 09-05-02 | 05 | 3 | PRICE-08, PRICE-09 | T-09-08 | A zero-data product renders four muted badges without throwing; section ordering asserted; an entirely absent `all_time_range` field still renders the caption plus a muted dash | component | `cd frontend && npm test -- ProductDetailPage --run` | ✅ (extend) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Vacuous-pass guard (backend rows).** `tests/conftest.py`'s `api_db` and `client`
fixtures SKIP rather than fail when `MONGODB_URI` is unset, so a bare `pytest -x`
can go green having executed nothing. Every backend task in this phase therefore
carries a `<precondition>` naming that env var, and every backend acceptance
criterion pairs its pytest command with a check that the run reported no skipped
tests.

---

## Wave 0 Requirements

- [ ] `frontend/src/components/AllTimeRangeBadge.test.jsx` — stubs for PRICE-09 (ok / insufficient-data states)
- [ ] `frontend/src/components/AllTimeRangeBadge.module.css` — needed before the component test can assert class names

*Backend: no new test files needed — `tests/test_price_service.py`, `tests/test_catalog_service.py`, and `tests/test_api_products.py` already exist and establish the exact conventions this phase's new cases extend.*

---

## Manual-Only Verifications

Every phase behaviour has automated verification. Two items are additionally
confirmed by eye, neither as a substitute for an assertion:

| Item | Where | Why not automated |
|------|-------|-------------------|
| The all-time range row does not crowd or awkwardly wrap against the three-badge trend row at narrow viewport widths | `<human-check>` in Plan 09-05 Task 2 | The `overflow` row in `09-UI-SPEC.md`'s UI Considerations table is recorded as a **backstop**, not a covered state — the placement decision is locked but was not pixel-verified at every breakpoint. Carried into `09-05-PLAN.md`'s `must_haves.truths` as a flat-scalar `verification: backstop` entry, so verify-time routes it to human review rather than silently passing. |
| The all-time range chip reads as a member of the same pill-chip family as the trend badges (same height, padding, radius, digit alignment) | `<human-check>` in Plan 09-02 Task 2 | Class names and token references are asserted; visual equivalence of the rendered chip is not something jsdom can measure. |

*`workflow.human_verify_mode` is `end-of-phase`, so these are `<verify><human-check>`
blocks inside autonomous plans, not blocking `checkpoint:human-verify` tasks.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
