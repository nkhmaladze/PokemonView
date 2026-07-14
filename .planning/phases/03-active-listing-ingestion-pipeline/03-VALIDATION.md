---
phase: 3
slug: active-listing-ingestion-pipeline
status: planned
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-14
plan_task_ids_assigned: 2026-07-14
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

Plan/wave/task numbering assigned after planning (2026-07-14). Test file `tests/test_ingest_worker.py` + `ingest_db` fixture are authored RED in Plan 03-03 (Wave 2) and turned GREEN by the Plan 03-04 (Wave 3) implementation task referenced below.

| Test | Authored | Turned Green | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | Status |
|------|----------|--------------|------|-------------|------------|-----------------|-----------|-------------------|--------|
| test_build_query | 03-03 T2 | 03-04 T1 | 3 | INGEST-01 | T-03-03 | `build_query(product)` produces the expected `"Pokemon {set} {type-phrase}"` string; never joins `required_keywords` | unit | `pytest tests/test_ingest_worker.py::test_build_query -x` | ⬜ pending |
| test_lock_prevents_concurrent_acquire | 03-03 T2 | 03-04 T1 | 3 | INGEST-02 | T-03-02, T-03-04 | `acquire_lock`/`release_lock` block a second concurrent acquire and self-heal after TTL | integration (real MongoDB) | `pytest tests/test_ingest_worker.py::test_lock_prevents_concurrent_acquire -x` | ⬜ pending |
| test_upsert_idempotent | 03-03 T2 | 03-04 T1 | 3 | INGEST-02 | T-03-05 | repeat upsert of the same `itemId` produces no duplicate documents | integration (real MongoDB) | `pytest tests/test_ingest_worker.py::test_upsert_idempotent -x` | ⬜ pending |
| test_price_and_shipping_captured | 03-03 T2 | 03-04 T1 | 3 | INGEST-03 | T-03-03 | listing document carries `item_price` AND `total_price` (item + shipping, defaulting to 0.0 when absent) | integration (synthetic Browse API item) | `pytest tests/test_ingest_worker.py::test_price_and_shipping_captured -x` | ⬜ pending |
| test_run_ingestion_once_skips_when_locked | 03-03 T2 | 03-04 T2 | 3 | INGEST-02 | T-03-02, T-03-04 | when the lock is held, `run_ingestion_once` makes zero eBay calls and writes a `skipped_locked` run doc | integration (real MongoDB, credential-free) | `pytest tests/test_ingest_worker.py::test_run_ingestion_once_skips_when_locked -x` | ⬜ pending |
| live-proof run | — | 03-05 T1 | 4 | INGEST-01/02/03 | T-03-01, T-03-SC | a real Production run writes real listings (item + total price) + a completed `ingestion_runs` document, no secret leaked | manual-only (gated on eBay credentials; deferrable) | `python -m scripts.ingest_worker --once` | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

Supporting non-test tasks with automated verify (no 3 consecutive tasks lack automated feedback):
- 03-01 T2 (apscheduler install) — `python -c "import apscheduler; from apscheduler.schedulers.blocking import BlockingScheduler"`
- 03-02 T1/T2 (collections + docstrings) — `python -c "import db.init_collections ..."` source/docstring assertions
- 03-03 T1/T2 (fixture + tests) — `pytest --collect-only` clean, five tests collected
- 03-04 T3 (main/scheduler) — main() source assertions + full `pytest tests/test_ingest_worker.py -x`

---

## Wave 0 Requirements

- [ ] `tests/test_ingest_worker.py` — five RED tests for INGEST-01/02/03 (Plan 03-03 T2)
- [ ] `tests/conftest.py` — `ingest_db` fixture mirroring `catalog_db` for lock + upsert integration tests (Plan 03-03 T1)
- [ ] `db/init_collections.py` extension — active_listings + ingestion_locks (TTL) + ingestion_runs (started_at index) (Plan 03-02 T1)
- [ ] `apscheduler==3.11.3` install — gated behind `checkpoint:human-verify` per Package Legitimacy Audit (Plan 03-01)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live Production Browse API run captures real price + shippingOptions and writes to `active_listings`/`ingestion_runs` | INGEST-01, INGEST-02, INGEST-03 | Requires real `EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET` (currently lost, per STATE.md) and live network access — cannot be mocked without losing the actual proof the requirement demands | Run `python -m scripts.ingest_worker --once` after re-populating `.env` credentials; confirm console shows OAuth OK, per-product result counts, and inspect `db.active_listings`/`db.ingestion_runs` for real documents with both `item_price` and `total_price` populated |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (checkpoint tasks in 03-01 T1 and 03-05 T1 use `<human-check>`; every `auto` task has an `<automated>` command)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references (test file, fixture, collections, apscheduler install)
- [x] No watch-mode flags
- [x] Feedback latency < 60s (`pytest tests/test_ingest_worker.py -x` ~15s)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved (task IDs assigned to plans 03-01..03-05, 2026-07-14)
