---
phase: 03-active-listing-ingestion-pipeline
fixed_at: 2026-07-14T00:00:00Z
review_path: .planning/phases/03-active-listing-ingestion-pipeline/03-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 03: Code Review Fix Report

**Fixed at:** 2026-07-14T00:00:00Z
**Source review:** .planning/phases/03-active-listing-ingestion-pipeline/03-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5 (CR-01, CR-02, WR-01, WR-02, WR-03 — `fix_scope: critical_warning`)
- Fixed: 5
- Skipped: 0

## Fixed Issues

### CR-01: Uncaught `IndexError` on empty `categories` list drops an entire product's batch, not just the offending item

**Files modified:** `scripts/ingest_worker.py`
**Commit:** b1c06ec
**Applied fix:** Replaced `item.get("categories", [{}])[0].get("categoryId")` with an explicit `categories = item.get("categories") or []` followed by `categories[0].get("categoryId") if categories else None`. This handles both the "key absent" and "key present but empty list" cases without relying on `.get`'s default-value semantics, so an item with `"categories": []` is written with `category_id=None` instead of raising an uncaught `IndexError` that aborts the rest of the batch. Verified with a new regression test (`test_upsert_listings_skips_item_with_empty_categories_list`, added under WR-01) confirming a later well-formed item in the same batch is no longer dropped as collateral damage.

### CR-02: `run_ingestion_once` has no top-level exception guard — an auth failure (or a bad `CATALOG` entry) leaves the run permanently stuck at `status="running"`

**Files modified:** `scripts/ingest_worker.py`
**Commit:** 20be625
**Applied fix:** Restructured `run_ingestion_once` so the token fetch and the whole per-product loop are wrapped in an outer `try/except Exception`, setting `status = "failed"` and appending a `{"product_ref": None, "error": ...}` entry to `errors[]` on any unexpected failure outside the per-product loop. Moved the `db.ingestion_runs.update_one(...)` finalization call (previously only reached on the success path) into a `finally` block alongside `release_lock(db, run_id)`, so the run document is *always* finalized with a terminal status (`success`/`partial`/`failed`) and a `finished_at` timestamp — it can no longer be left stuck at `status="running"` forever. The function's `return` was moved to after the try/except/finally so it always reads the freshly-finalized document.
**Note:** This is a control-flow/logic fix (not pure syntax). Flagged as **`fixed: requires human verification`** per the logic-bug limitation in verification_strategy — Tier 1/Tier 2 confirm the code is syntactically correct and the existing + new test suite passes, but a human should confirm the exception-propagation semantics (e.g. that `get_app_token()` failures and malformed `CATALOG` entries now correctly resolve to `status="failed"` in a live/staging run) before relying on this in production.

### WR-01: `run_ingestion_once`'s core orchestration path has zero test coverage

**Files modified:** `tests/test_ingest_worker.py`
**Commit:** 7d481da
**Applied fix:** Added three tests: `test_run_ingestion_once_happy_path` (monkeypatches `get_app_token`/`search_sealed_listings`, asserts `status="success"` and correct `products_queried`/`listings_fetched`/`listings_written` counts across every `CATALOG` product), `test_run_ingestion_once_partial_on_product_error` (one product's `search_sealed_listings` call raises; asserts `status="partial"`, `errors[]` contains that product's `product_ref`, and every other product's listings were still written), and `test_upsert_listings_skips_item_with_empty_categories_list` (direct regression coverage for CR-01, per the review's explicit suggestion). All 9 tests in the suite pass locally (`python3 -m pytest tests/test_ingest_worker.py -q` → `9 passed`).

### WR-02: Errors recorded in `ingestion_runs.errors[]` lack per-item context

**Files modified:** `scripts/ingest_worker.py`
**Commit:** bb3912b
**Applied fix:** Changed both the per-product and run-level error-recording sites from `"error": str(e)` to `"error": f"{type(e).__name__}: {e}"`, per the review's "at minimum" fix suggestion. This surfaces the exception's type (e.g. `IndexError`, `RuntimeError`) alongside its message in `ingestion_runs.errors[]`, making failures diagnosable from the run-history collection without re-running. (The review's further "consider" suggestion — having `upsert_listings` collect its own itemId-level skipped-item diagnostics — was left as a follow-up; it's a larger structural change beyond the finding's minimum fix.)

### WR-03: No test exercises the TTL-expiry stale-lock steal path

**Files modified:** `tests/test_ingest_worker.py`
**Commit:** d2c69c4
**Applied fix:** Added `test_acquire_lock_steals_expired_lock`, which directly inserts an `ingestion_locks` document under a different holder with `expires_at` backdated into the past, then asserts `acquire_lock(ingest_db, "new-holder")` returns `True` and the lock document's `holder` field is overwritten — exercising the self-heal mechanism that makes the lock crash-safe after a hard-killed worker, without going through an explicit `release_lock` call.

## Skipped Issues

None — all 5 in-scope findings were fixed.

---

_Fixed: 2026-07-14T00:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
