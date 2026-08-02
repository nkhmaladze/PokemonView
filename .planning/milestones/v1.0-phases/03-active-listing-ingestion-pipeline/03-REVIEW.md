---
phase: 03-active-listing-ingestion-pipeline
reviewed: 2026-07-14T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - requirements.txt
  - db/init_collections.py
  - tests/conftest.py
  - tests/test_ingest_worker.py
  - scripts/ingest_worker.py
  - .env.example
findings:
  critical: 2
  warning: 3
  info: 4
  total: 9
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-07-14T00:00:00Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Reviewed the scheduled, lock-guarded active-listing ingestion worker (`scripts/ingest_worker.py`), its MongoDB bootstrap (`db/init_collections.py`), and the accompanying test suite/fixtures. The MongoDB TTL-lock design (`acquire_lock`/`release_lock`) was traced through the concurrent-acquire, stale-lock-steal, and holder-mismatch-release cases and is sound: `find_one_and_update` with an `expires_at <= now` filter + `upsert=True`, combined with `_id`'s automatic unique index, correctly serializes acquisition across processes and self-heals a hard-killed worker's stale lock via TTL. `release_lock`'s holder-scoped delete correctly avoids releasing a lock a run no longer owns.

Two BLOCKER-level bugs were found in `upsert_listings` and `run_ingestion_once`, both of which can cause **entire batches of valid, correctly-priced listings to be dropped or the run's own bookkeeping to be corrupted** — directly on point for this phase's explicit "shipping cost/total price never silently dropped" risk. Neither is exercised by the current test suite, which only covers the well-formed-item and skip-locked paths.

Note: `.env.example` was in the review scope but could not be opened — the Read and Bash tools both returned a permission denial for that specific path in this environment. It was not reviewed; this is a tooling limitation, not a finding about the file's contents.

## Critical Issues

### CR-01: Uncaught `IndexError` on empty `categories` list drops an entire product's batch, not just the offending item

**File:** `scripts/ingest_worker.py:154,158-161`
**Issue:** `upsert_listings` builds each listing's document inside a `try/except (KeyError, ValueError, TypeError)` specifically so "one malformed eBay item never aborts the whole batch" (per the function's own docstring, lines 126-128). But the category lookup:

```python
"category_id": item.get("categories", [{}])[0].get("categoryId"),
```

uses `item.get("categories", [{}])` — the `[{}]` default is only used when the `"categories"` key is *absent*. If the key is *present* but set to an empty list (`"categories": []`, a plausible real eBay Browse API response shape), `.get` returns `[]` (not the default), and `[][0]` raises `IndexError`. `IndexError` is not in the caught exception tuple `(KeyError, ValueError, TypeError)`, so it propagates out of the `for item in items:` loop entirely — abandoning every `ops` entry already built for prior items in this call, since `bulk_write(ops)` is never reached. The exception is only caught one layer up, at the per-*product* level in `run_ingestion_once` (line 250), which means one item with `"categories": []` silently discards **every other valid, correctly-priced listing fetched for that product in that run** — the opposite of the isolation guarantee the code claims to provide, and a direct instance of price data being dropped without any per-item diagnostic (the resulting `errors[]` entry only contains `str(e)` = `"list index out of range"`, with no itemId).

**Fix:**
```python
categories = item.get("categories") or []
category_id = categories[0].get("categoryId") if categories else None
doc = {
    ...
    "category_id": category_id,
    ...
}
```
(Or, at minimum, add `IndexError` to the caught exception tuple — but the `or []` fix above is more correct and also avoids masking future similar bugs.)

### CR-02: `run_ingestion_once` has no top-level exception guard — an auth failure (or a bad `CATALOG` entry) leaves the run permanently stuck at `status="running"`

**File:** `scripts/ingest_worker.py:233-239, 253-263`
**Issue:** Inside `run_ingestion_once`, both:
- `token = get_app_token()` / `access_token = token["access_token"]` (lines 233-234), and
- `product_ref = f"{product['set_name']}_{product['product_type']}"...` (lines 237-239)

sit **outside** the per-product `try/except Exception` block (which only wraps lines 240-251). If `get_app_token()` raises (expired/invalid eBay credentials, eBay identity endpoint outage, network error — all realistic, non-hypothetical failure modes for this exact integration per CLAUDE.md's own risk callout on eBay API access) or the response lacks `access_token`, or a future `CATALOG` entry is missing `set_name`/`product_type`, the exception propagates straight out of `run_ingestion_once`. The `finally: release_lock(db, run_id)` (line 264-265) still runs, so the lock isn't permanently stuck — but the `ingestion_runs` document inserted at line 214-225 with `status="running"` and `finished_at=None` is **never updated**. It stays "running" forever. This corrupts the exact run-history observability this phase was built to provide (the module docstring cites SC-4, and Phase 7's staleness alerting is explicitly documented as depending on querying the latest `ingestion_runs` doc by `started_at`) — a stuck "running" record from an auth failure will appear to be (or block detection of) the "latest run" indefinitely, masking the actual failure.

**Fix:** Wrap the token fetch and the whole per-product loop in a broader try/except that still finalizes the run document on unexpected failure:
```python
try:
    token = get_app_token()
    access_token = token["access_token"]
    for product in CATALOG:
        ...
    status = "success" if not errors else "partial"
except Exception as e:
    status = "failed"
    errors.append({"product_ref": None, "error": str(e)})
finally... # existing update_one call must always run, even on this path
```
Concretely: move the `db.ingestion_runs.update_one(...)` call (and `status` computation) into a `try/except Exception` around the token-fetch + loop, so *any* unexpected failure still records `status="failed"` with `finished_at` set, before the outer `finally: release_lock(...)` runs.

## Warnings

### WR-01: `run_ingestion_once`'s core orchestration path has zero test coverage

**File:** `tests/test_ingest_worker.py`
**Issue:** Of the five tests, only `test_run_ingestion_once_skips_when_locked` calls `run_ingestion_once` at all, and it only exercises the skip-locked branch (`get_app_token`/`search_sealed_listings` are monkeypatched to assert they're *never* called). No test calls `run_ingestion_once` on its primary path — iterating `CATALOG`, building `product_ref`, calling (mocked) `get_app_token`/`search_sealed_listings`, aggregating `products_queried`/`listings_fetched`/`listings_written`, populating `errors[]` on a per-product exception, and writing the final `status="success"|"partial"` document. This is the core Phase 3 deliverable's main code path, and its complete absence of coverage is exactly why CR-01 and CR-02 (both live only in that path) went undetected.

**Fix:** Add at least two tests using `monkeypatch.setattr(ingest_worker, "get_app_token", ...)` / `"search_sealed_listings", ...`: one happy-path test asserting `status="success"` and correct counts across 2+ `CATALOG` products, and one test where `search_sealed_listings` raises for one product, asserting `status="partial"`, `errors` contains that product's `product_ref`, and the *other* products' listings were still written. A third test feeding an item with `"categories": []` through `upsert_listings` (or `run_ingestion_once`) would have caught CR-01 directly.

### WR-02: Errors recorded in `ingestion_runs.errors[]` lack per-item context

**File:** `scripts/ingest_worker.py:250-251`
**Issue:** `errors.append({"product_ref": product_ref, "error": str(e)})` records only the product-level slug and the exception's string form. For exceptions raised deep inside `upsert_listings`'s item loop (like CR-01's `IndexError`), there's no `itemId`, no indication of which of potentially dozens of items caused the failure, and no count of how many items in that batch were lost as collateral damage. This makes the failure mode in CR-01 very difficult to diagnose from `ingestion_runs` alone in production.

**Fix:** Include enough context to debug without re-running: e.g. `{"product_ref": product_ref, "error": f"{type(e).__name__}: {e}"}` at minimum, and consider having `upsert_listings` collect its own skipped-item diagnostics (itemId + reason) and return them alongside the `BulkWriteResult` rather than raising past already-processed items.

### WR-03: No test exercises the TTL-expiry stale-lock steal path

**File:** `tests/test_ingest_worker.py:142-155`
**Issue:** `test_lock_prevents_concurrent_acquire` only tests the explicit `release_lock` → re-acquire path. It never tests the actual self-heal mechanism `acquire_lock`'s docstring calls out — a lock whose `expires_at` has passed (simulating a hard-killed worker that never reached `release_lock`) being successfully stolen by a new `acquire_lock` call without an explicit release. Since this is the specific mechanism that makes the lock crash-safe (T-03-02), and it's the least-obvious part of the concurrency logic to get right, it should have direct test coverage (e.g. manually insert/backdate an `ingestion_locks` document with `expires_at` in the past, then assert `acquire_lock` succeeds).

**Fix:** Add a test that directly manipulates `ingest_db.ingestion_locks` to insert a lock document with `expires_at` in the past under a different holder, then asserts `acquire_lock(ingest_db, "new-holder")` returns `True`.

## Info

### IN-01: TTL index on `ingestion_locks.expires_at` is created identically in two places

**File:** `db/init_collections.py:202`, `scripts/ingest_worker.py:80`
**Issue:** `db/init_collections.init_collections()` already creates `db.ingestion_locks.create_index("expires_at", expireAfterSeconds=0)` on every bootstrap (line 202), and `scripts/ingest_worker.ensure_lock_index()` creates the exact same index again on every `run_ingestion_once()` call (line 80), and `main()` already calls `init_collections(db)` before any run (line 286). The duplication is harmless (idempotent `create_index` calls) but is dead redundancy — `ensure_lock_index` will never actually need to create anything in the normal `main()` flow.
**Fix:** Either drop `ensure_lock_index()` and rely on `init_collections()` having already run, or keep it only as defense-in-depth for callers that invoke `run_ingestion_once` directly (as the tests do) and note that explicitly in the docstring.

### IN-02: `item_price` is computed twice per item

**File:** `scripts/ingest_worker.py:144-146`
**Issue:** `float(item["price"]["value"])` is computed once directly (line 144) and again inside `total_cost(item)` (in `scripts/ebay_client.py`). Purely a minor duplication, not a correctness issue since both computations use the identical expression.
**Fix:** Have `total_cost` (or a sibling helper) return `(item_price, shipping_cost, total_price)` as a tuple so the value is computed once and reused.

### IN-03: `requirements.txt` pins `requests==2.34.2`, which doesn't match CLAUDE.md's documented `requests 2.32.x` guidance

**File:** `requirements.txt:1`
**Issue:** The project's own stack documentation (CLAUDE.md) recommends `requests 2.32.x`; the pinned version here is `2.34.2`. This may simply mean the docs are stale, but it's worth a quick sanity check that `2.34.2` is a real, intended release and not a typo (e.g. for `2.32.x`).
**Fix:** Confirm the pinned version is intentional, or align it with the documented `2.32.x` line and update CLAUDE.md if `2.34.2` is correct.

### IN-04: `main()` crashes with a raw `KeyError` traceback if `MONGODB_URI` is unset

**File:** `scripts/ingest_worker.py:282`
**Issue:** `os.environ["MONGODB_URI"]` raises an unguarded `KeyError` with no operator-friendly message if the env var is missing. This mirrors the existing `scripts/seed_catalog.py` convention per the docstring, so it's consistent with the codebase rather than a new defect, but it's still poor operator experience for a worker meant to run unattended/scheduled.
**Fix:** `mongodb_uri = os.environ.get("MONGODB_URI") or sys.exit("MONGODB_URI not set")` for a clearer failure message, applied consistently across all entrypoints if adopted.

---

_Reviewed: 2026-07-14T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
