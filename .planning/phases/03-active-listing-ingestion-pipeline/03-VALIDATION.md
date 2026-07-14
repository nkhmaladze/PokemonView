---
phase: 3
slug: active-listing-ingestion-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-14
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 (already installed and configured — Phase 2) |
| **Config file** | `pytest.ini` (existing, Phase 2) |
| **Quick run command** | `pytest tests/test_ingest_worker.py -x` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~15 seconds (unit) / ~30-60 seconds (full suite incl. Phase 2 integration tests against Atlas) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_ingest_worker.py -x`
- **After every plan wave:** Run `pytest` (full suite, including Phase 2's `test_catalog_schema.py`)
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-xx-01 | TBD (planner-assigned) | TBD | INGEST-01 | T-03-DoS (malformed response) | `build_query(product)` produces expected query string; `run_ingestion_once` iterates every catalog product | unit | `pytest tests/test_ingest_worker.py::test_build_query -x` | ❌ W0 | ⬜ pending |
| 03-xx-02 | TBD (planner-assigned) | TBD | INGEST-02 | T-03-DoS (stale lock) | `acquire_lock`/`release_lock` block a second concurrent acquire and self-heal after TTL; repeat upsert of same `itemId` produces no duplicates | integration (real MongoDB) | `pytest tests/test_ingest_worker.py::test_lock_prevents_concurrent_acquire tests/test_ingest_worker.py::test_upsert_idempotent -x` | ❌ W0 | ⬜ pending |
| 03-xx-03 | TBD (planner-assigned) | TBD | INGEST-03 | T-03-ID (untrusted eBay field shape) | Listing document carries both `item_price` and `total_price` (item + shipping, defaulting to 0.0 when absent) | unit (synthetic Browse API fixture) | `pytest tests/test_ingest_worker.py::test_price_and_shipping_captured -x` | ❌ W0 | ⬜ pending |
| 03-xx-04 | TBD (planner-assigned) | TBD | INGEST-01/02/03 (live proof) | T-01-SC (package legitimacy, apscheduler) | A real run against Production writes real listings + a completed `ingestion_runs` document | manual-only | `python -m scripts.ingest_worker --once` | ❌ W0 — gated on user re-obtaining eBay credentials | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_ingest_worker.py` — stubs for INGEST-01/02/03 (unit + integration)
- [ ] `tests/conftest.py` — extend/reuse existing `catalog_db` fixture pattern for lock + upsert integration tests
- [ ] `apscheduler==3.11.3` install — gated behind `checkpoint:human-verify` per Package Legitimacy Audit (RESEARCH.md)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live Production Browse API run captures real price + shippingOptions and writes to `active_listings`/`ingestion_runs` | INGEST-01, INGEST-02, INGEST-03 | Requires real `EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET` (currently lost, per STATE.md) and live network access — cannot be mocked without losing the actual proof the requirement demands | Run `python -m scripts.ingest_worker --once` after re-populating `.env` credentials; confirm console shows OAuth OK, per-product result counts, and inspect `db.active_listings`/`db.ingestion_runs` for real documents with both `item_price` and `total_price` populated |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
