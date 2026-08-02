# Phase 4: Listing Matching & Price Normalization - Pattern Map

**Mapped:** 2026-07-14
**Files analyzed:** 4
**Analogs found:** 4 / 4

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `scripts/matching.py` | service (batch/transform module) | batch / transform + CRUD (read-then-bulk-update) | `scripts/ingest_worker.py` | role-match (same "in-process module, no top-level side effects, orchestration function + helpers" shape; different domain logic) |
| `tests/test_matching.py` | test | request-response-free unit + integration (fixture-driven Mongo asserts) | `tests/test_ingest_worker.py` | exact (same suite shape: deferred imports, fixture-based, one test fn per behavior) |
| `tests/conftest.py` (extend: add `matching_db`) | fixture/provider | CRUD (setup/teardown against a live test DB) | `tests/conftest.py`'s own `ingest_db` fixture | exact (extend by copying `ingest_db`'s structure, swap collection set) |
| `scripts/ingest_worker.py` (extend: call `run_matching_once`) | controller/orchestrator (existing file, modify) | request-response / batch (invoked in-process) | itself — extend `run_ingestion_once()`'s existing `try` block | exact (modification target IS its own analog for the integration point) |

## Pattern Assignments

### `scripts/matching.py` (service, batch/transform)

**Analog:** `scripts/ingest_worker.py`

**Module docstring / no-top-level-side-effects convention** (`scripts/ingest_worker.py` lines 1-30):
```python
"""...
No top-level side effects on import: no MongoClient construction, no
network calls, no scheduler startup happen merely from `import
scripts.ingest_worker`. `apscheduler` is intentionally NOT imported at
module top level — that import lives inside `main()` ...

Credential hygiene (threat T-03-01, mirrors scripts/ebay_client.py and
scripts/seed_catalog.py discipline): the raw eBay access token, the
Authorization header, and MONGODB_URI are never logged/printed — only
counts, per-product query strings, and token metadata are ever
surfaced in worker output.
"""
```
Apply the same discipline to `matching.py`: no MongoClient/network calls at import time, and never log full listing `title` strings at info level in production (RESEARCH.md V5 note) — only counts/status.

**Imports pattern** (`scripts/ingest_worker.py` lines 32-43):
```python
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne
from pymongo.errors import DuplicateKeyError

from db.init_collections import init_collections
from scripts.catalog_data import CATALOG
from scripts.ebay_client import get_app_token, search_sealed_listings, total_cost
```
`matching.py` mirrors this shape: `from pymongo import UpdateOne`, `from scripts.catalog_data import CATALOG`, `from scripts.ingest_worker import PRODUCT_TYPE_SEARCH_TERMS` (reuse for the fuzzy canonical phrase per RESEARCH.md Pattern 1 — do not re-declare), plus stdlib `re`, `statistics`, `datetime`.

**Idempotent bulk-write-by-id pattern (core pattern to copy)** — `upsert_listings()` (`scripts/ingest_worker.py` lines 120-168):
```python
def upsert_listings(db, product_ref, items, run_id, fetched_at):
    ops = []
    for item in items:
        if "price" not in item:
            continue
        try:
            item_price = float(item["price"]["value"])
            price_total = total_cost(item)
            ...
            doc = {"_id": item["itemId"], ...}
        except (KeyError, ValueError, TypeError):
            # Malformed/unexpected shape on this one item — skip it,
            # never abort the rest of the batch (T-03-03).
            continue
        ops.append(UpdateOne({"_id": doc["_id"]}, {"$set": doc}, upsert=True))

    if not ops:
        return None
    return db.active_listings.bulk_write(ops)
```
This is the direct template for `matching.py`'s per-listing update loop inside `run_matching_once()`: one `UpdateOne({"_id": listing["_id"]}, {"$set": {...match/exclusion fields...}})` per listing, batched into a single `bulk_write`, wrapped per-item in `try/except` (RESEARCH.md's "Known Threat Patterns" V5 row: malformed/missing `title` must not abort the whole matching pass — mirror this exact per-item isolation, not a per-listing bare loop).

**Orchestration function pattern (core pattern to copy)** — `run_ingestion_once()` (`scripts/ingest_worker.py` lines 171-276), specifically the accumulate-counts-then-single-final-update shape:
```python
    products_queried = 0
    listings_fetched = 0
    listings_written = 0
    errors = []

    try:
        ...
        for product in CATALOG:
            try:
                ...
                products_queried += 1
                ...
            except Exception as e:  # noqa: BLE001 - isolate one product's failure
                errors.append({"product_ref": product_ref, "error": f"{type(e).__name__}: {e}"})
        status = "success" if not errors else "partial"
    except Exception as e:  # noqa: BLE001
        status = "failed"
        errors.append(...)
    finally:
        update_doc = {...}
        db.ingestion_runs.update_one({"_id": run_id}, {"$set": update_doc})
```
`run_matching_once(db, run_id, ts)` should follow the same "accumulate local counters across a loop, return one summary dict for the caller to merge" shape (RESEARCH.md's own `run_matching_once` code example already follows this — treat `ingest_worker`'s counter-accumulation + per-item try/except as the canonical precedent justifying that design, not just RESEARCH.md's say-so).

**Error handling pattern:** per-item `except (KeyError, ValueError, TypeError)` / `except Exception as e: # noqa: BLE001` with isolation into an `errors`/count list — never let one bad document abort the batch. Copy this verbatim for `normalize()`/`match_listing()`/`check_exclusion()` calls inside the per-listing loop in `run_matching_once()`.

**Validation:** No input schema validation exists in `ingest_worker.py` beyond defensive `try/except` on dict access (`active_listings` has no `$jsonSchema` validator — see `db/init_collections.py` note below). `matching.py` should follow the same "defensive code, not schema validation" approach for reading `listing["title"]`.

---

### `tests/test_matching.py` (test)

**Analog:** `tests/test_ingest_worker.py`

**Module docstring / deferred-import convention** (`tests/test_ingest_worker.py` lines 1-31):
```python
"""Contract tests for the active-listing ingestion worker (INGEST-01,
INGEST-02, INGEST-03).
...
Every `scripts.ingest_worker` import is deferred into each test's
body (not at module top level) so `pytest --collect-only` succeeds
now, before scripts/ingest_worker.py exists — this suite is authored
RED in Plan 03-03 (Wave 2) and turned GREEN by Plan 03-04's worker
implementation (Wave 3) ...

Plain pytest `assert` style throughout — no unittest.TestCase ...
"""
```
`test_matching.py` must follow this identically: `from scripts.matching import ...` deferred inside each test body (not top-level), so collection succeeds before `scripts/matching.py` exists (Nyquist RED-first scaffold, RESEARCH.md's Wave 0 Gaps).

**Pure-unit test pattern (no fixture)** — `test_build_query()` (`tests/test_ingest_worker.py` lines 34-52):
```python
def test_build_query():
    """build_query(product) builds 'Pokemon {set} {type-phrase}', never
    joining required_keywords (INGEST-01, 03-RESEARCH.md Pattern 4)."""
    from scripts.ingest_worker import build_query

    assert (
        build_query({"set_name": "Chaos Rising", "product_type": "etb"})
        == "Pokemon Chaos Rising Elite Trainer Box"
    )
```
Direct template for `normalize()`, `match_listing()` (against synthetic titles, no DB), and `check_exclusion()` unit tests — no fixture needed since these are pure functions.

**Fixture-driven integration test pattern** — `test_price_and_shipping_captured(ingest_db)` (`tests/test_ingest_worker.py` lines 55-96):
```python
def test_price_and_shipping_captured(ingest_db):
    from datetime import datetime, timezone
    from scripts.ingest_worker import upsert_listings

    item_a = {...}
    upsert_listings(ingest_db, "chaos-rising_etb", [item_a, item_b], run_id="r1", fetched_at=datetime.now(timezone.utc))

    doc_a = ingest_db.active_listings.find_one({"_id": "v1|A|0"})
    assert doc_a is not None, "item A was not written to active_listings"
    assert doc_a["item_price"] == 50.0
```
Direct template for `test_price_points_median_aggregation(matching_db)` and `test_run_ingestion_once_end_to_end(matching_db)` — seed synthetic `active_listings` docs directly via `matching_db.active_listings.insert_many(...)`, call the function under test, assert on `find_one`/`find` results, with descriptive assert messages in the same style ("X was not written to Y").

**Monkeypatch pattern for end-to-end tests** — `test_run_ingestion_once_happy_path(ingest_db, monkeypatch)` (`tests/test_ingest_worker.py` lines 266-299): not directly needed (matching has no external API), but the "assert on `result[...]` dict fields returned by the orchestration function" pattern applies directly to asserting `run_matching_once()`'s returned `{"listings_matched": ..., "listings_unmatched": ..., "listings_excluded": ...}` dict.

---

### `tests/conftest.py` (extend — new `matching_db` fixture)

**Analog:** the existing `ingest_db` fixture in the same file (`tests/conftest.py` lines 89-153)

**Pattern to copy verbatim, adapted:**
```python
@pytest.fixture
def ingest_db():
    """... Mirrors `catalog_db`'s structure exactly, swapping the collection
    set: this fixture targets the three collections Phase 3's
    ingestion worker writes into (`active_listings`, `ingestion_locks`,
    `ingestion_runs`) instead of the catalog's `products`/
    `price_points`. ..."""
    from dotenv import load_dotenv

    load_dotenv()
    mongodb_uri = os.environ.get("MONGODB_URI")
    if not mongodb_uri:
        pytest.skip(
            "MONGODB_URI not set — provision a MongoDB instance per "
            "Plan 02-02 (MongoDB Atlas M0 or local) and add MONGODB_URI "
            "to .env before running the ingestion worker contract tests."
        )

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
`matching_db` = same skeleton, but per RESEARCH.md's Wave 0 Gaps: drop/reset `active_listings`, `price_points`, AND `ingestion_runs` (needed for aggregation-write tests, unlike `ingest_db` which doesn't touch `price_points`). Keep the exact skip-when-`MONGODB_URI`-unset guard, the `try/except: client.close(); raise` setup-failure safety, and the before-and-after `drop_collection` teardown discipline. `TEST_DB_NAME = "pokemonview_test"` (module-level constant, already defined, reuse as-is — do not redefine).

---

### `scripts/ingest_worker.py` (extend — call `run_matching_once`)

**Analog:** itself; the integration point is inside `run_ingestion_once()`'s existing `try` block (`scripts/ingest_worker.py` lines 234-273)

**Exact insertion point:**
```python
    try:
        token = get_app_token()
        access_token = token["access_token"]

        for product in CATALOG:
            ...
        status = "success" if not errors else "partial"
        # <-- INSERT: match_counts = run_matching_once(db, run_id, started_at)
        #     merge match_counts into update_doc below (D-04)
    except Exception as e:  # noqa: BLE001
        status = "failed"
        errors.append({"product_ref": None, "error": f"{type(e).__name__}: {e}"})
    finally:
        update_doc = {
            "finished_at": datetime.now(timezone.utc),
            "status": status,
            "products_queried": products_queried,
            "listings_fetched": listings_fetched,
            "listings_written": listings_written,
            "errors": errors,
            # <-- ADD: "listings_matched": ..., "listings_unmatched": ...,
            #          "listings_excluded": ... (D-04)
        }
        db.ingestion_runs.update_one({"_id": run_id}, {"$set": update_doc})
        release_lock(db, run_id)
```
Add `from scripts.matching import run_matching_once` to the existing top-level import block (same flat-import style as the other `scripts.*`/`db.*` imports already there — no lazy import needed here since `matching.py` has no optional heavy dependency like `apscheduler`, only `rapidfuzz` which is a hard requirement once installed). Call `run_matching_once(db, run_id, started_at)` right after the `for product in CATALOG:` loop finishes (per RESEARCH.md System Architecture Diagram — after fetch, before `status = "success" if not errors else "partial"` is finalized, or immediately after; either position keeps the flat top-level-field convention in `update_doc`).

---

## Shared Patterns

### No-top-level-side-effects-on-import
**Source:** `scripts/ingest_worker.py` lines 18-23, `scripts/catalog_data.py` lines 33-37
**Apply to:** `scripts/matching.py` — no `MongoClient`, no network calls, no scheduler/rapidfuzz-model-loading side effects merely from `import scripts.matching`.

### Idempotent bulk_write-by-_id
**Source:** `scripts/ingest_worker.py` `upsert_listings()` lines 120-168 (`UpdateOne({"_id": ...}, {"$set": doc}, upsert=True)`, batched into one `bulk_write` call)
**Apply to:** All of `matching.py`'s writes back to `active_listings` (match fields, then a second `bulk_write` for outlier `exclusion_reason` updates per RESEARCH.md's Code Example) — never `find_one` + per-item `update_one` in a loop.

### Per-item try/except isolation ("one bad item doesn't abort the batch")
**Source:** `scripts/ingest_worker.py` lines 141-163 (`except (KeyError, ValueError, TypeError): continue`) and lines 252-255 (`except Exception as e: # noqa: BLE001`)
**Apply to:** `matching.py`'s per-listing loop inside `run_matching_once()` — a listing with a missing/malformed `title` field must not abort matching for the rest of the run (RESEARCH.md's V5/DoS threat-pattern row).

### Flat run-observability counters merged into a single `$set` update
**Source:** `scripts/ingest_worker.py` lines 264-273 (`update_doc = {...}; db.ingestion_runs.update_one({"_id": run_id}, {"$set": update_doc})`)
**Apply to:** D-04's `listings_matched`/`listings_unmatched`/`listings_excluded` — three new flat top-level int fields on the same `ingestion_runs` document, added via the same single `update_one` call ingest_worker.py already performs — do not create a separate `matching_runs` collection or a nested sub-document.

### Fixture pattern: skip-if-unconfigured, lazy project imports, before/after drop_collection teardown
**Source:** `tests/conftest.py` `ingest_db` fixture, lines 89-153
**Apply to:** New `matching_db` fixture — identical skeleton (`pytest.skip` when `MONGODB_URI` unset, `try/except: client.close(); raise` on setup failure, lazy `from db.init_collections import init_collections` inside the fixture body, drop relevant collections both before yield and after).

### Deferred (not top-level) imports of the module-under-test in RED-phase test files
**Source:** `tests/test_ingest_worker.py` lines 22-27 and every test function (e.g. `from scripts.ingest_worker import build_query` inside `test_build_query()`)
**Apply to:** Every test function in `tests/test_matching.py` — `from scripts.matching import normalize, match_listing, ...` must be imported inside each test body, never at module top level, so `pytest --collect-only` succeeds before `scripts/matching.py` exists (Nyquist RED-first convention).

### `total_price` as the canonical landed-cost field (never bare `item_price`)
**Source:** `scripts/ingest_worker.py`'s `total_cost()` reuse in `upsert_listings()` (lines 145-146: `price_total = total_cost(item); shipping_cost = round(price_total - item_price, 2)`)
**Apply to:** `filter_outliers()` must default to `total_price`, not `item_price` (RESEARCH.md Pitfall 5) — this convention is already established as canonical by Phase 3's own `total_cost()` usage, not just asserted by RESEARCH.md.

## No Analog Found

None — every file this phase creates/modifies has a strong same-repo analog (see table above). `filter_outliers()`/`aggregate_and_write()`'s statistical logic itself (median/pstdev over a listing group) has no prior in-repo analog since no other phase performs statistical aggregation yet — for that narrow piece, follow RESEARCH.md's Pattern 3/Pattern 4 code examples directly (stdlib `statistics.median`/`statistics.pstdev`), which are themselves grounded in official Python docs, not an in-repo precedent.

## Metadata

**Analog search scope:** `scripts/`, `db/`, `tests/` (whole repo — small enough for full-directory read rather than Glob/Grep narrowing)
**Files scanned:** `scripts/ingest_worker.py`, `scripts/catalog_data.py`, `db/init_collections.py`, `tests/conftest.py`, `tests/test_ingest_worker.py` (5 files read in full; all ≤ 345 lines, single-pass reads, no re-reads)
**Pattern extraction date:** 2026-07-14
