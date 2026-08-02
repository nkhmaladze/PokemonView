# Phase 3: Active-Listing Ingestion Pipeline - Pattern Map

**Mapped:** 2026-07-14
**Files analyzed:** 3 (1 new script, 1 extended module, 1 new test file) + 1 dependency addition
**Analogs found:** 3 / 3

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `scripts/ingest_worker.py` | service (scheduled worker) | event-driven + CRUD (upsert) | `scripts/seed_catalog.py` (upsert/main pattern) + `scripts/ebay_client.py` (external call reuse) | role-match (composite: no prior scheduled-worker file exists, but both halves of this file have exact analogs) |
| `db/init_collections.py` (extension) | model/config (schema+index bootstrap) | CRUD (idempotent create-if-absent) | `db/init_collections.py` itself (existing `products`/`price_points` setup) | exact (same file, extend existing pattern) |
| `tests/test_ingest_worker.py` | test | CRUD/integration | `tests/test_catalog_schema.py` (+ `tests/conftest.py`'s `catalog_db` fixture) | exact |
| `requirements.txt` (addition: `apscheduler==3.11.3`) | config | — | existing `requirements.txt` entries for `requests`/`python-dotenv` (Phase 1 pattern: gated behind `checkpoint:human-verify`) | exact |

## Pattern Assignments

### `scripts/ingest_worker.py` (service, event-driven scheduler + CRUD upsert)

**Analogs:** `scripts/seed_catalog.py` (idempotent upsert + `main()`/credential-loading shape), `scripts/ebay_client.py` (external API call reuse, no top-level side effects), `db/init_collections.py` (idempotent collection/index bootstrap called from `main()`)

**Imports pattern** — mirror `scripts/seed_catalog.py` lines 35-43:
```python
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

from db.init_collections import init_collections
from scripts.catalog_data import CATALOG
```
For `ingest_worker.py`, additionally import `from scripts.ebay_client import get_app_token, search_sealed_listings, total_cost` and stdlib `uuid`/`datetime.timezone` for run IDs and lock timestamps. Do NOT reimplement token/search logic — reuse as-is (per RESEARCH.md "Don't Hand-Roll" table).

**"No top-level side effects on import" convention** — mirrored from `scripts/ebay_client.py` lines 1-16 and `db/init_collections.py` lines 20-24: no MongoClient construction, no network calls, no scheduler start at module level. Every function (`run_ingestion_once`, `acquire_lock`, `release_lock`, `upsert_listings`, `build_query`) must be explicitly invoked by a caller (`main()` or a test).

**Credential hygiene pattern** — mirror `scripts/seed_catalog.py` lines 99-101 and `scripts/ebay_client.py` lines 41-43: read `MONGODB_URI`/`EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET` exclusively via `os.environ` after `load_dotenv()`; never print/log the full connection string or access token (only success counts / `token_type`/`expires_in` metadata, per RESEARCH.md's Security Domain section).

**Idempotent upsert pattern (core CRUD)** — direct structural mirror of `scripts/seed_catalog.py` lines 46-85 (`seed_catalog(db, catalog)` → `bulk_write([UpdateOne(...)])`, never `insert_many`):
```python
# scripts/seed_catalog.py lines 67-79 — the exact shape to replicate
# for scripts/ingest_worker.py's upsert_listings(db, product_id, items, run_id, fetched_at)
ops = []
for product in catalog:
    doc = dict(product)  # copy — never mutate the shared constant
    slug = f"{doc['set_name']}_{doc['product_type']}".lower().replace(" ", "-")
    doc["_id"] = slug
    ops.append(UpdateOne({"_id": slug}, {"$set": doc}, upsert=True))
if not ops:
    return None
result = db.products.bulk_write(ops)
```
Apply this same shape to `active_listings`, keyed by `_id = item["itemId"]` instead of a slug (RESEARCH.md Pattern 3, already fully spelled out with the `upsert_listings` function body — copy that function verbatim as the starting point).

**External API reuse pattern** — call `get_app_token()` once per run (not per product), then reuse the token across all `search_sealed_listings(token, query)` calls in the loop, exactly as `scripts/ebay_client.py`'s docstring (lines 1-16) anticipates ("no token caching/refresh wrapper is built here; that belongs to Phase 3's ingestion worker"). Use `total_cost(item)` (lines 98-116) as-is rather than re-deriving price/shipping math.

**`main()` / entrypoint pattern** — mirror `scripts/seed_catalog.py` lines 88-122 (`load_dotenv()` → build `MongoClient` → `try/finally: client.close()` → call `init_collections(db)` before the primary operation → `return 0`):
```python
# scripts/seed_catalog.py lines 99-122 — shape to mirror for ingest_worker.main()
load_dotenv()
mongodb_uri = os.environ["MONGODB_URI"]
client = MongoClient(mongodb_uri)
try:
    db = client["pokemonview"]
    init_collections(db)
    seed_catalog(db, CATALOG)
    ...
finally:
    client.close()
return 0
```
For `ingest_worker.py`, `main()` additionally wraps `BlockingScheduler`/`IntervalTrigger` setup (RESEARCH.md Pattern 1, already given as a complete code block) and should support a `--once` CLI flag that calls `run_ingestion_once(db)` directly for manual/CI verification without starting the scheduler (per RESEARCH.md's Validation Architecture test map).

**Lock acquire/release pattern** — RESEARCH.md Pattern 2 provides the complete, ready-to-copy `ensure_lock_index`/`acquire_lock`/`release_lock` functions (atomic `find_one_and_update` + TTL index on `expires_at`). Wrap the lock-acquire-to-lock-release span of `run_ingestion_once` in `try/finally`, matching the same `try/finally: client.close()` discipline already used in `scripts/seed_catalog.py::main()`.

**Query construction pattern** — RESEARCH.md Pattern 4 provides the complete `build_query(product)` function (set_name + product-type phrase, NOT joining `required_keywords`). `scripts/catalog_data.py`'s `required_keywords` field (e.g. lines 77, 89, 101, 113) is reserved for Phase 4's matching step — do not reuse it for search-string construction.

**Error handling pattern** — no existing file in this codebase has a per-item defensive-skip pattern to mirror exactly, but `scripts/ebay_client.py::total_cost` (lines 98-116) already defaults shipping to `0.0` when absent — extend that same defensive `.get()`-with-default style, plus explicit `if "price" not in item: continue` (RESEARCH.md Pitfall 3), so one malformed eBay item doesn't abort the whole run. Record errors into the run's `errors` list (RESEARCH.md's `ingestion_runs` document shape) rather than raising.

---

### `db/init_collections.py` (extension) (model/config, CRUD bootstrap)

**Analog:** the file's own existing `products`/`price_points` setup (lines 75-146)

**Idempotent create-if-absent pattern** — mirror lines 103-109 and 141-145 exactly:
```python
# db/init_collections.py lines 141-145 — exact shape to replicate for
# active_listings, ingestion_locks, ingestion_runs
if "price_points" not in db.list_collection_names():
    db.create_collection(
        "price_points",
        timeseries=PRICE_POINTS_TIMESERIES_OPTIONS,
    )
```
Apply the same `if "<name>" not in db.list_collection_names(): db.create_collection(...)` guard for each of the three new collections. `active_listings` and `ingestion_runs` need no special `timeseries=` option (plain collections); only index creation is needed (`_id` uniqueness on `active_listings` is automatic/free since `_id=itemId`; `ingestion_runs` needs an index on `started_at` per RESEARCH.md Wave 0 Gaps; `ingestion_locks` needs the TTL index from RESEARCH.md Pattern 2's `ensure_lock_index`).

**Docstring/comment convention** — mirror the file's existing docstring style (lines 1-24, 64-73): explain *why* each collection exists and what future phase/component writes into it, e.g. extend the existing "reserved for Phase 3's ingestion worker" comment (lines 64-67) to now say `active_listings`/`ingestion_locks`/`ingestion_runs` are what Phase 3 actually writes, and `price_points` remains reserved for Phase 4's matching step (per RESEARCH.md's Pitfall 1 correction — this is an important doc fix to make in the same edit, since the existing docstring is now stale/misleading about what Phase 3 writes into).

**No top-level side effects** — `init_collections(db)` remains the only entrypoint; no new top-level calls.

---

### `tests/test_ingest_worker.py` (test, CRUD/integration)

**Analog:** `tests/test_catalog_schema.py` (structure/style) + `tests/conftest.py`'s `catalog_db` fixture (to be mirrored, not reused as-is — a new fixture is needed since this phase's tests need `active_listings`/`ingestion_locks`/`ingestion_runs`, not `products`/`price_points`)

**Test file structure/style** — mirror `tests/test_catalog_schema.py` lines 1-33 (module docstring naming each test + the REQ ID it satisfies, plain `assert` style, no `unittest.TestCase`):
```python
# tests/test_catalog_schema.py lines 1-20 — docstring shape to mirror
"""Contract tests for ... (INGEST-01, INGEST-02, INGEST-03).

Tests, each consuming a fixture from tests/conftest.py:
  - test_build_query                      (INGEST-01)
  - test_lock_prevents_concurrent_acquire  (INGEST-02)
  - test_upsert_idempotent                 (INGEST-02)
  - test_price_and_shipping_captured       (INGEST-03)

Plain pytest `assert` style throughout — no unittest.TestCase.
"""
```

**Fixture pattern (new fixture needed)** — mirror `tests/conftest.py` lines 32-84 (`catalog_db`) structurally for a new fixture (e.g. `ingest_db`), reusing the exact skip-if-`MONGODB_URI`-unset guard, lazy `from db.init_collections import init_collections` inside the fixture body (not top-level, so `pytest --collect-only` succeeds before the file exists — same Wave 0 scaffold-first rationale as lines 13-16), and the same before/after `drop_collection` teardown discipline — but targeting `active_listings`/`ingestion_locks`/`ingestion_runs` instead of `products`/`price_points`:
```python
# tests/conftest.py lines 32-84 shape — replicate for a new
# ingest_db-style fixture (either added to conftest.py or locally in
# test_ingest_worker.py), swapping collection names:
@pytest.fixture
def ingest_db():
    from dotenv import load_dotenv
    load_dotenv()
    mongodb_uri = os.environ.get("MONGODB_URI")
    if not mongodb_uri:
        pytest.skip("MONGODB_URI not set — ...")
    client = MongoClient(mongodb_uri)
    try:
        test_db = client[TEST_DB_NAME]
        test_db.drop_collection("active_listings")
        test_db.drop_collection("ingestion_locks")
        test_db.drop_collection("ingestion_runs")
        from db.init_collections import init_collections
        init_collections(test_db)
    except Exception:
        client.close()
        raise
    yield test_db
    test_db.drop_collection("active_listings")
    test_db.drop_collection("ingestion_locks")
    test_db.drop_collection("ingestion_runs")
    client.close()
```

**Idempotency test pattern** — direct structural mirror of `tests/test_catalog_schema.py::test_seed_idempotent` (lines 64-76) for `test_upsert_idempotent`: call the upsert function twice with the same input, assert document count is unchanged.

**Unit test pattern (no DB)** — `test_build_query` and `test_price_and_shipping_captured` do not need a live MongoDB fixture at all (pure functions) — no existing analog for a pure-unit test exists in this codebase yet since Phase 2's tests are all DB-integration tests; write these as plain `def test_x(): assert build_query(...) == "..."` functions with no fixture argument, consistent with RESEARCH.md's Validation Architecture table distinguishing "unit" vs "integration" test types for this phase.

## Shared Patterns

### Credential/secret hygiene
**Source:** `scripts/ebay_client.py` lines 9-16, `scripts/seed_catalog.py` lines 18-22
**Apply to:** `scripts/ingest_worker.py` (all functions touching `EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET`/`MONGODB_URI`)
```python
# Never print/log the full access token, Authorization header, or
# MongoDB connection string — only success counts / token metadata.
```

### No top-level side effects on import
**Source:** `scripts/ebay_client.py` lines 14-16, `db/init_collections.py` lines 20-24, `scripts/catalog_data.py` lines 33-37
**Apply to:** `scripts/ingest_worker.py` — every function (including the APScheduler `BlockingScheduler` construction) must live inside `main()` or a callable, never execute at module import time.

### Idempotent upsert via `bulk_write([UpdateOne(..., upsert=True)])`
**Source:** `scripts/seed_catalog.py` lines 67-79
**Apply to:** `scripts/ingest_worker.py::upsert_listings` (RESEARCH.md Pattern 3 already gives the full target function)

### Idempotent collection/index bootstrap (`if name not in list_collection_names(): create_collection(...)`)
**Source:** `db/init_collections.py` lines 103-109, 141-145
**Apply to:** the `db/init_collections.py` extension for `active_listings`/`ingestion_locks`/`ingestion_runs`

### `main()` entrypoint shape (`load_dotenv()` → `MongoClient` → `try/finally: client.close()`)
**Source:** `scripts/seed_catalog.py` lines 88-122
**Apply to:** `scripts/ingest_worker.py::main()`

### Test structure (plain `assert`, fixture-per-file, module docstring naming REQ IDs)
**Source:** `tests/test_catalog_schema.py` lines 1-20
**Apply to:** `tests/test_ingest_worker.py`

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| APScheduler `BlockingScheduler`/`IntervalTrigger` setup portion of `scripts/ingest_worker.py::main()` | service | event-driven (scheduled) | No prior scheduled-worker process exists in this codebase (Phase 1/2 are one-shot scripts) — use RESEARCH.md's Pattern 1 code block directly (already complete and ready to copy) rather than an in-repo analog |
| MongoDB TTL lock acquire/release (`acquire_lock`/`release_lock`) | utility | CRUD (atomic conditional update) | No prior cross-process locking exists in this codebase — use RESEARCH.md's Pattern 2 code block directly (already complete and ready to copy) |

## Metadata

**Analog search scope:** `scripts/`, `db/`, `tests/` (entire existing codebase — small enough to read in full; no Glob/Grep search needed beyond confirming these are the only relevant directories)
**Files scanned:** `scripts/seed_catalog.py`, `scripts/ebay_client.py`, `scripts/catalog_data.py`, `db/init_collections.py`, `tests/conftest.py`, `tests/test_catalog_schema.py` (6 files, all read in full — codebase is Phase 1-2 scale, no large-file truncation needed)
**Pattern extraction date:** 2026-07-14
