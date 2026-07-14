# Phase 3: Active-Listing Ingestion Pipeline - Research

**Researched:** 2026-07-14
**Domain:** Scheduled Python worker (APScheduler) polling eBay Browse API into MongoDB; idempotent upsert + cross-process locking patterns; run observability
**Confidence:** MEDIUM (APScheduler/pymongo/MongoDB-lock patterns cross-corroborated via multiple independent web sources; eBay Browse API response-shape claims inherit Phase 1's MEDIUM confidence and remain live-unverified — see Assumptions Log)

<user_constraints>
## User Constraints (from CONTEXT.md)

No CONTEXT.md exists for Phase 3 (`/gsd-discuss-phase` was not run). There are no user-locked decisions beyond ROADMAP.md's Phase 3 success criteria and REQUIREMENTS.md's INGEST-01/02/03, which this research treats as the binding spec. Project-level constraints already locked in PROJECT.md/CLAUDE.md (and treated as non-negotiable, not re-litigated below):

- APScheduler mandated over Celery/task-broker infrastructure for the ingestion worker (CLAUDE.md, ROADMAP "no task broker").
- Official eBay Browse API only, OAuth Client Credentials Grant (already implemented in `scripts/ebay_client.py`, Phase 1).
- MongoDB is the shared data store; `products` and `price_points` collections already exist (Phase 2), with `price_points` reserved as a native time-series collection (`timeField=ts`, `metaField=product_id`, `granularity=hours`) — **this phase must not write into `price_points` directly** (see Architectural Responsibility Map below — matching to a `product_id` is Phase 4's job, not Phase 3's).
- Python 3.12+, Flask, PyMongo already in place.

### Claude's Discretion
Everything not explicitly pinned above is this research's job to resolve with a prescriptive recommendation: scheduling trigger type + default interval, locking mechanism, collection design for raw listings + run metadata, and query-construction mapping from catalog `required_keywords` to the Browse API `q` parameter.

### Deferred Ideas (OUT OF SCOPE)
- Matching/normalization of listings to canonical catalog products — Phase 4 (MATCH-01/02/03).
- Writing resolved, per-product price points into `price_points` — Phase 4/5, once a `product_id` is known.
- Marketplace Insights (sold-listing) ingestion — Phase 8, contingent.
- Alerting on stale/stalled ingestion — Phase 7 (this phase only needs to produce the observability data that Phase 7's alerting will consume).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| INGEST-01 | Scheduled worker pulls active eBay listings via the Browse API every N hours | See `## Architecture Patterns` Pattern 1 (APScheduler setup) and `## Standard Stack` |
| INGEST-02 | Ingestion is idempotent (upsert by eBay item ID) and safe against overlapping/retried runs | See `## Architecture Patterns` Pattern 2 (MongoDB lock) and Pattern 3 (upsert by itemId) |
| INGEST-03 | Both pre-shipping item price and estimated total price are stored per listing | See `## Code Examples` (listing document shape) and `## Common Pitfalls` Pitfall 2 |
</phase_requirements>

## Summary

Phase 3 builds one new component: a scheduled ingestion worker script that reuses Phase 1's already-authored `scripts/ebay_client.py` (`get_app_token`, `search_sealed_listings`, `total_cost`) to poll the Browse API for each of Phase 2's ~16 catalog products, and writes results into two **new** MongoDB collections — `active_listings` (current raw listing state, upserted by eBay `itemId`) and `ingestion_runs` (one document per run, recording start/end time, counts, and errors). Neither of these collections exists yet; `db/init_collections.py` currently only provisions `products` and `price_points`, and this phase must extend it (or add a sibling module) rather than write into `price_points`, whose `metaField=product_id` requires a matched canonical product that only Phase 4's matching step can resolve.

Scheduling should use APScheduler's `BlockingScheduler` with an `IntervalTrigger` (not `CronTrigger` — there's no fixed-wall-clock requirement, just "every N hours") running as a dedicated standalone worker process (`scripts/ingest_worker.py` or similar), configured with `max_instances=1` as a cheap in-process guard. Because `max_instances` only protects within a single process, and this project's execution environment may run more than one worker instance (dev + prod, container restarts, manual re-runs), a **MongoDB-based TTL lock document** — no new infrastructure, reusing the MongoDB dependency already in place — is the recommended cross-process concurrency guard that actually satisfies ROADMAP SC-2's "concurrent runs are prevented by locking" language. A default interval of **4 hours** is recommended: the catalog is ~16 products, each requiring one `item_summary/search` call per run, so a run costs ~16 Browse API calls (worst case ~32 if pagination is ever needed) against a 5,000-calls/day default budget — 4-hour cadence (6 runs/day, ≈96-192 calls/day) leaves enormous headroom for OAuth token calls, manual re-runs, retries, and Phase 4/5 development traffic, while still refreshing prices multiple times daily. The interval should be read from an env var (e.g. `INGESTION_INTERVAL_HOURS`, default `4`) rather than hardcoded, matching SC-1's "a schedule that can run every N hours" framing.

**Primary recommendation:** Add `apscheduler==3.11.3` to `requirements.txt` (behind a `checkpoint:human-verify`, same protocol pattern already used for `requests`/`python-dotenv` in Phase 1); build `scripts/ingest_worker.py` around a single `run_ingestion_once(db)` function (testable in isolation, called both by the scheduled job and directly for manual/CI runs) that: acquires the MongoDB lock, iterates catalog products from `scripts/catalog_data.CATALOG`, builds a search query per product, calls `search_sealed_listings`, upserts each item into `active_listings` keyed by `itemId`, records run metadata into `ingestion_runs`, and releases the lock in a `finally` block. Wrap this function in an APScheduler `BlockingScheduler` + `IntervalTrigger` entrypoint for the actual scheduled worker process.

**Execution blocker (not a research blocker):** `EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET` were lost from `.env` in a prior incident (per STATE.md Blockers) and Phase 1's live-verification Plan 01-04 has not been completed — there is still no proof the Browse API's `price`/`shippingOptions` field shapes assumed here (and already coded in `scripts/ebay_client.py`) match a real Production response. This phase's plan should include a live-verification task gated on the user having re-obtained credentials, and must not silently treat Phase 3 as "done" without that live proof, mirroring Phase 1's own Pitfall 1 (Sandbox-vs-Production).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| OAuth token acquisition + Browse API search calls | API/Backend (ingestion worker) | External Service (eBay Browse API) | Server-side, credential-bearing outbound calls; already implemented in `scripts/ebay_client.py` (Phase 1), reused as-is here |
| Scheduling / cadence control | API/Backend (in-process scheduler thread) | — | APScheduler runs inside the same Python process as the worker — no separate service, per CLAUDE.md's explicit "no task broker" constraint |
| Overlap/concurrency locking | Database/Storage (MongoDB lock collection) | API/Backend (APScheduler `max_instances=1`) | The durable, cross-process source of truth for "is a run in progress" must live in the shared datastore, not in-process memory, since the worker may restart or run as more than one instance |
| Raw listing persistence (`active_listings`) | Database/Storage (new MongoDB collection) | — | This is NOT `price_points` — no `product_id` exists yet since matching (Phase 4) hasn't run; a separate raw-listings collection is required |
| Run metadata / observability (`ingestion_runs`) | Database/Storage (new MongoDB collection) | API/Backend (worker writes it) | Simple structured log data Phase 7's future alerting will query; a collection (not a flat file) keeps it queryable and consistent with the rest of the stack |
| Price + shipping normalization (`total_cost`) | API/Backend (ingestion worker, reusing `ebay_client.total_cost`) | — | Pure computation on already-fetched data; no external dependency |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|---------------|
| APScheduler | 3.11.3 (verified via `pip index versions apscheduler`, `[VERIFIED: pypi registry]`) | In-process job scheduling for the periodic ingestion pull | Already mandated by CLAUDE.md over Celery; `IntervalTrigger` + `max_instances`/`coalesce`/`misfire_grace_time` give exactly the "every N hours, no overlap" behavior this phase needs with zero extra infrastructure |
| PyMongo | 4.17.0 (already installed and pinned — confirmed via `pip show pymongo` this session) | MongoDB driver for `active_listings`/`ingestion_runs` writes and the lock-document pattern | Already the project's driver; `find_one_and_update` (atomic lock acquire) and `bulk_write([UpdateOne(...)])` (idempotent listing upserts) are both native PyMongo operations, no new dependency needed |
| requests | 2.34.2 (already installed and pinned) | HTTP calls — reused from `scripts/ebay_client.py` | Already implemented in Phase 1; this phase imports, does not reimplement, `get_app_token`/`search_sealed_listings`/`total_cost` |
| python-dotenv | 1.2.2 (already installed and pinned) | `.env` credential loading | Same as above — reused, not reimplemented |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.4.2 (already installed and pinned) | Unit/integration tests for `run_ingestion_once`, lock acquire/release, and query-building logic | Already the project's test framework (Phase 2 established `tests/conftest.py`'s `catalog_db` fixture pattern — reuse it) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| MongoDB TTL lock document | `filelock`/PID-file on disk | Rejected: a local lockfile only protects a single machine/filesystem — breaks the moment the worker runs in a container that gets rescheduled to a different host, or if two environments (dev/prod) share no filesystem. MongoDB is already the shared datastore every environment can reach. |
| MongoDB TTL lock document | Redis-based lock (e.g. `redlock`) | Rejected: introduces exactly the broker/extra-infra dependency PROJECT.md/CLAUDE.md explicitly reject for this project ("no task broker") |
| APScheduler `IntervalTrigger` | APScheduler `CronTrigger` | Consider `CronTrigger` only if the product later needs a fixed wall-clock cadence (e.g. "always at :00 and :30"); SC-1's "every N hours" framing is naturally an interval, not a cron expression |
| A dedicated `active_listings` collection | Writing directly into `price_points` with a placeholder/unresolved `product_id` | Rejected: `price_points`'s `metaField=product_id` is a Phase 2-locked schema decision reserved for matched, canonical data (Phase 4 output) — writing unmatched raw listings into it would corrupt the time-series collection's intended shape and is not retrofittable (time-series options are creation-time-only per Phase 2's 02-RESEARCH.md Pitfall 1) |

**Installation:**
```bash
pip install apscheduler==3.11.3
```
(Append to `requirements.txt`; the other three dependencies are already installed.)

**Version verification:** `pip index versions apscheduler` confirms latest is `3.11.3` this session — matches CLAUDE.md's documented `3.11.x (latest 3.11.3)` recommendation exactly, no drift.

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| `apscheduler` | PyPI | Long-established (project since 2011 per GitHub history; latest *release* 2026-06-28 — a recent release date, not a new project) | Unknown (legitimacy tool could not retrieve download stats in this environment) | github.com/agronholm/apscheduler (confirmed via web search this session — canonical, actively maintained) | `[SUS]` (reasons: `too-new`, `unknown-downloads`, `no-repository`) | Keep — see note |

**Note on the `[SUS]` verdict:** The legitimacy tool's `too-new` signal is a false positive — it appears to key off the *latest release publish date* (2026-06-28), not the package's actual age, and `apscheduler` has been continuously maintained since 2011 under `agronholm/apscheduler` (confirmed via `[VERIFIED: web search cross-corroboration]` this session: GitHub repo, releases history, PyPI project page all consistent). This is the same class of false positive documented in Phase 1's `01-RESEARCH.md` for `requests`/`python-dotenv` (driven by an `unknown-downloads` telemetry gap in this environment, not a real red flag). Per protocol, the `[SUS]` verdict must still be gated: **the planner must add a `checkpoint:human-verify` task before installing `apscheduler`**, even though this researcher assesses the actual supply-chain risk as negligible — it is exactly the package CLAUDE.md's own stack research already recommends.

**Packages removed due to `[SLOP]` verdict:** none
**Packages flagged as suspicious `[SUS]`:** `apscheduler` — planner must insert `checkpoint:human-verify` before this install (low actual risk per note above, but protocol-mandated)

**Postinstall script check:** `apscheduler` is a pure-Python package with no setuptools postinstall hook; no risk signal.

## Architecture Patterns

### System Architecture Diagram

```
[scripts/ingest_worker.py — BlockingScheduler process]
        |
        | every INGESTION_INTERVAL_HOURS (IntervalTrigger, max_instances=1)
        v
   run_ingestion_once(db)
        |
        |--1. acquire_lock(db, "active_listing_ingestion") ------> [MongoDB: ingestion_locks]
        |         (find_one_and_update + TTL; abort run if lock held)
        |
        |--2. insert run-start doc --------------------------------> [MongoDB: ingestion_runs]
        |
        |--3. for each product in scripts.catalog_data.CATALOG:
        |       a. get_app_token() [cached across products in one run] --> [eBay OAuth]
        |       b. build_query(product) -> q string
        |       c. search_sealed_listings(token, q) -----------------> [eBay Browse API]
        |       d. for each itemSummary: compute total_cost(),
        |          build listing doc {_id: itemId, product_ref, ...}
        |
        |--4. bulk_write([UpdateOne(_id=itemId, upsert=True), ...]) --> [MongoDB: active_listings]
        |
        |--5. update run-end doc (finished_at, counts, errors) ------> [MongoDB: ingestion_runs]
        |
        |--6. release_lock(db, "active_listing_ingestion") [finally] -> [MongoDB: ingestion_locks]
        v
  process continues, waits for next IntervalTrigger fire
```

A reader can trace the primary path: scheduler fires -> lock acquired -> run-start logged -> each catalog product searched -> listings upserted by itemId -> run-end logged with counts -> lock released. A second overlapping trigger fire (or a second worker process) fails to acquire the lock in step 1 and skips/logs a no-op run rather than racing the first.

### Recommended Project Structure
```
scripts/
├── ebay_client.py           # Phase 1 — reused as-is (get_app_token, search_sealed_listings, total_cost)
├── catalog_data.py          # Phase 2 — reused as-is (CATALOG list, required_keywords)
├── ingest_worker.py         # NEW — run_ingestion_once(db), build_query(product), main() + APScheduler setup
db/
├── init_collections.py      # Phase 2 — EXTEND: add active_listings + ingestion_locks + ingestion_runs collection/index setup
tests/
├── test_ingest_worker.py    # NEW — unit tests for build_query, lock acquire/release, upsert idempotency (mirrors test_catalog_schema.py's catalog_db fixture pattern)
```

### Pattern 1: APScheduler standalone worker (IntervalTrigger, max_instances=1)
**What:** A dedicated worker process runs a `BlockingScheduler` with one interval-triggered job.
**When to use:** Any "run this every N hours, this process's only job is scheduling" scenario — exactly this phase's need.
**Example:**
```python
# Source: apscheduler.readthedocs.io/en/3.x/userguide.html (via cross-corroborated web search, MEDIUM confidence)
import os
import signal
import sys

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from dotenv import load_dotenv
from pymongo import MongoClient

from scripts.ingest_worker import run_ingestion_once


def main() -> int:
    load_dotenv()
    interval_hours = int(os.environ.get("INGESTION_INTERVAL_HOURS", "4"))
    client = MongoClient(os.environ["MONGODB_URI"])
    db = client["pokemonview"]

    scheduler = BlockingScheduler()

    def shutdown(signum, frame):
        scheduler.shutdown(wait=False)
        client.close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    scheduler.add_job(
        run_ingestion_once,
        trigger=IntervalTrigger(hours=interval_hours),
        args=[db],
        max_instances=1,      # in-process guard; MongoDB lock is the cross-process guard
        coalesce=True,        # if a run is missed (process was down), run once on restart, not N times
        misfire_grace_time=300,
        next_run_time=None,   # or set to run immediately on startup if desired
    )
    scheduler.start()


if __name__ == "__main__":
    sys.exit(main())
```
**Key parameters confirmed:** `max_instances` defaults to 1 and controls in-process overlap; `coalesce=True` collapses multiple queued-but-missed executions into a single run; `misfire_grace_time` bounds how late a missed run may still fire. None of these protect against a *second separate process* running the same job — that's Pattern 2's job.

### Pattern 2: MongoDB TTL lock document (cross-process concurrency guard)
**What:** An atomic acquire/release pattern using a dedicated `ingestion_locks` collection with a TTL index as a stale-lock safety net.
**When to use:** Whenever more than one process/instance of the worker could plausibly run concurrently (deploy restarts, dev+prod, manual re-runs) — the actual mechanism satisfying SC-2's "concurrent runs are prevented by locking."
**Example:**
```python
# Source: cross-corroborated web search this session (oneuptime.com MongoDB distributed-locks pattern,
# MongoDB official TTL index docs — MEDIUM confidence, common idiom, not an official MongoDB-authored recipe)
from datetime import datetime, timedelta, timezone

from pymongo.errors import DuplicateKeyError

LOCK_ID = "active_listing_ingestion"
LOCK_TTL_SECONDS = 900  # generously longer than one run should ever take


def ensure_lock_index(db):
    # expireAfterSeconds=0: MongoDB expires the document at the exact
    # datetime stored in expires_at, not N seconds after insertion —
    # this lets each acquire set its own explicit expiry.
    db.ingestion_locks.create_index("expires_at", expireAfterSeconds=0)


def acquire_lock(db, holder: str) -> bool:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=LOCK_TTL_SECONDS)
    try:
        db.ingestion_locks.find_one_and_update(
            {
                "_id": LOCK_ID,
                "expires_at": {"$lte": now},
            },
            {"$set": {"holder": holder, "acquired_at": now, "expires_at": expires_at}},
            upsert=True,
        )
        return True
    except DuplicateKeyError:
        # A live (non-expired) lock document already exists with this _id
        # and didn't match the {"expires_at": {"$lte": now}} filter —
        # another run currently holds the lock.
        return False


def release_lock(db, holder: str) -> None:
    # Only delete if WE still hold it — avoids deleting a newer holder's
    # lock if this run overran its own TTL.
    db.ingestion_locks.delete_one({"_id": LOCK_ID, "holder": holder})
```
**Usage in `run_ingestion_once`:** call `acquire_lock`; if it returns `False`, log a skipped-run entry to `ingestion_runs` (status="skipped_locked") and return immediately without calling eBay at all. Always `release_lock` in a `finally` block so a run that raises still releases (the TTL index is the last-resort safety net if the process is killed before `finally` runs).

### Pattern 3: Idempotent upsert by eBay `itemId`
**What:** `bulk_write` with `UpdateOne(..., upsert=True)` keyed on the eBay `itemId`, mirroring the exact pattern `scripts/seed_catalog.py` already established for `products` in Phase 2.
**When to use:** Every ingestion run's listing writes — this is what makes overlapping/retried runs produce no duplicates (INGEST-02).
**Example:**
```python
# Source: pymongo.readthedocs.io Bulk Write Operations docs (via cross-corroborated web search,
# MEDIUM confidence); pattern already proven in this codebase's scripts/seed_catalog.py
from pymongo import UpdateOne


def upsert_listings(db, product_id: str, items: list[dict], run_id: str, fetched_at) -> "BulkWriteResult | None":
    ops = []
    for item in items:
        if "price" not in item:
            continue  # Pitfall 3 (Phase 1 research) — require price present before recording
        shipping_options = item.get("shippingOptions") or [{}]
        shipping_cost = shipping_options[0].get("shippingCost", {}).get("value", "0.00")
        doc = {
            "_id": item["itemId"],            # stable, unique per listing (idempotent key)
            "product_ref": product_id,        # this catalog product's slug (Phase 2 _id), NOT a matched canonical product_id
            "title": item["title"],
            "item_price": float(item["price"]["value"]),
            "shipping_cost": float(shipping_cost),
            "total_price": float(item["price"]["value"]) + float(shipping_cost),
            "category_id": item.get("categories", [{}])[0].get("categoryId"),
            "fetched_at": fetched_at,
            "run_id": run_id,
        }
        ops.append(UpdateOne({"_id": doc["_id"]}, {"$set": doc}, upsert=True))
    if not ops:
        return None
    return db.active_listings.bulk_write(ops)
```
**Note on `product_ref`:** this is the catalog product this *search query* targeted (e.g. `"chaos-rising_etb"`, Phase 2's deterministic slug `_id`) — it records *which query* found the listing, not a verified match. Phase 4's matching step still independently evaluates the listing title against `required_keywords` before treating it as authoritative for that product; `product_ref` is a hint/provenance field, not a substitute for matching.

### Pattern 4: Query construction from catalog `required_keywords`
**What:** Build the Browse API `q` string from `set_name` + a product-type display phrase, NOT by joining all of `required_keywords`.
**When to use:** Every per-product search call in the ingestion loop.
**Example:**
```python
PRODUCT_TYPE_SEARCH_TERMS = {
    "booster_pack": "Booster Pack",
    "booster_box": "Booster Box",
    "etb": "Elite Trainer Box",
    "booster_bundle": "Booster Bundle",
}


def build_query(product: dict) -> str:
    return f"Pokemon {product['set_name']} {PRODUCT_TYPE_SEARCH_TERMS[product['product_type']]}"
```
**Why not join `required_keywords` directly:** `catalog_data.py`'s `required_keywords` (e.g. `["chaos rising", "booster bundle", "bundle"]`) deliberately includes redundant disambiguation tokens for Phase 4's *matching* step (so a `booster_bundle` listing is never confused with `booster_box`). Passing all of them as one `q` string risks over-constraining eBay's search (a real listing titled "... Booster Bundle (6 Packs) ..." may not separately contain the standalone word "bundle" positioned the same way, and stacking near-duplicate terms narrows/best-match ranking unpredictably). This mirrors the clean, human-authored phrase shape Phase 1's `verify_ebay_access.py` already uses (`"Pokemon Scarlet Violet Elite Trainer Box"`), not a keyword-array join. `[ASSUMED — query-shape recommendation is reasoned from Phase 1's proven pattern and general eBay search behavior, not independently live-tested this session]`

### Anti-Patterns to Avoid
- **Writing ingestion output directly into `price_points`:** No `product_id` (matched canonical product) exists until Phase 4 runs. Writing unmatched raw listings into the time-series collection reserved for that shape would violate Phase 2's schema contract and cannot be retrofitted (time-series options are creation-time-only).
- **Relying on `max_instances=1` alone as "the locking mechanism":** It only protects a single process; ROADMAP SC-2 explicitly calls out "concurrent runs are prevented by locking" as a distinct requirement from the scheduler's own overlap guard — use the MongoDB lock (Pattern 2) as the actual mechanism.
- **A local PID file or `filelock`-based mutex:** Fails across container restarts/multiple hosts; MongoDB is already the shared datastore every environment reaches, at zero extra infra cost.
- **Skipping the token per-request and re-authenticating every product query:** `get_app_token` should be called once per run (token lives ~7,200s, far longer than a ~16-product run takes) and the same access token reused across all `search_sealed_listings` calls in that run — re-authenticating per product wastes API budget for no benefit (no separate rate limit exists for the identity endpoint, but it's still unnecessary work).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Overlap/concurrency prevention | A custom in-memory flag, a bespoke file-based semaphore, or a hand-rolled retry/backoff wrapper around it | MongoDB TTL lock document (Pattern 2) + APScheduler `max_instances=1` | The MongoDB pattern is a handful of lines built on primitives (`find_one_and_update`, TTL index) already battle-tested for exactly this purpose; a custom implementation risks subtle races the atomic `find_one_and_update` already avoids |
| Job scheduling / interval math | Manual `time.sleep()` loop with a custom drift-correction algorithm | APScheduler `IntervalTrigger` | APScheduler already handles drift, misfires, and graceful shutdown; CLAUDE.md mandates it explicitly |
| Idempotent writes | Manual "check-then-insert" (`find_one` then `insert_one` if not found) | `bulk_write([UpdateOne(..., upsert=True)])` | Check-then-insert has a race window between the check and the insert under concurrent runs; the atomic upsert does not |
| Token refresh/caching across the run | A token-caching class with expiry tracking, retry, and refresh logic | A single `get_app_token()` call at the start of `run_ingestion_once`, reused for all product queries in that run | A run against ~16 products completes in seconds to low minutes — nowhere near the ~7,200s token lifetime; building refresh/cache infrastructure is premature until a much longer-running or higher-frequency worker exists |

**Key insight:** Everything genuinely hard about this phase (idempotency, overlap safety) is already solved by primitives PyMongo and APScheduler expose directly — the risk in this phase is architectural misplacement (writing into the wrong collection, conflating "which query found this" with "matched to this product"), not missing library functionality.

## Common Pitfalls

### Pitfall 1: Writing ingestion results into `price_points` before matching exists
**What goes wrong:** A plan naively assumes "ingestion writes into the pre-existing time-series collection" since `price_points` already exists and looks ready to receive price data.
**Why it happens:** `price_points` was intentionally created empty in Phase 2 specifically "reserved for Phase 3's ingestion worker" (per `db/init_collections.py`'s own docstring) — but that phrasing describes the eventual consumer of matched data, not this phase's raw-listing output.
**How to avoid:** Introduce a separate `active_listings` collection for this phase's raw output, keyed by `itemId`, carrying a `product_ref` (the query's catalog slug) as provenance only. Phase 4 reads `active_listings`, matches titles, and is the actual writer into `price_points` once a real `product_id` is resolved.
**Warning signs:** Any Phase 3 code path that constructs a document shaped `{ts, product_id, item_price, total_price}` (the `price_points` per-point shape) before Phase 4 has run.

### Pitfall 2: Treating `max_instances=1` as sufficient locking
**What goes wrong:** The plan implements only APScheduler's default overlap guard and calls SC-2 satisfied.
**Why it happens:** `max_instances=1` is the obvious, zero-code-effort default and does prevent the most common overlap case (a slow run still executing when the next interval fires) — but it is scoped to one Python process.
**How to avoid:** Implement Pattern 2's MongoDB TTL lock as the durable, cross-process guard; treat `max_instances=1` as a cheap secondary/defense-in-depth layer, not the primary mechanism.
**Warning signs:** No `ingestion_locks`-equivalent collection or document appears anywhere in the plan/implementation.

### Pitfall 3: Reading only `price.value`, forgetting `shippingOptions`, or trusting the field shape without a live check
**What goes wrong:** Same class of error Phase 1's own research flagged (Pitfall 3 there) — code reads `item["price"]["value"]` and skips `shippingOptions` because it "looks right" on a quick glance, silently violating INGEST-03.
**Why it happens:** `price.value` is the obvious top-level field; `shippingOptions[].shippingCost.value` requires knowing to look one level deeper into an array, and — critically for this phase — **the Browse API response shape has never actually been observed live** in this project (Plan 01-04's live run never completed; credentials were lost). The existing `scripts/ebay_client.py` code assumes the documented shape is correct but it is unverified.
**How to avoid:** Reuse `scripts/ebay_client.py`'s existing `total_cost()` (already implements the correct defaulting-to-0.0 pattern) rather than re-deriving price extraction logic; the Phase 3 plan MUST include a live-verification task, gated on the user having reissued `EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET`, before treating INGEST-03 as proven — do not mark this requirement done from code review alone.
**Warning signs:** No task in the Phase 3 plan actually runs `scripts/ingest_worker.py` against Production and inspects real output.

### Pitfall 4: Over-constraining the Browse API `q` search string
**What goes wrong:** The ingestion loop passes all of a product's `required_keywords` (joined into one string) as the search query, and gets zero or too-few results because eBay's search narrows on every additional term.
**Why it happens:** `required_keywords` already exists on each catalog product and looks like the obvious source for the search string, but it was designed for Phase 4's title-matching step, which needs redundant/disambiguating tokens (e.g. both "elite trainer box" and "etb"), not for search-query construction.
**How to avoid:** Use Pattern 4's `build_query()` (set_name + a single canonical product-type phrase) instead of joining the keyword list.
**Warning signs:** A run against a real catalog product returns 0 listings for a set/product-type combination known to have active eBay listings.

### Pitfall 5: Letting a run that fails partway through leave the lock held
**What goes wrong:** An unhandled exception mid-run (e.g. an eBay API 5xx) crashes `run_ingestion_once` before `release_lock` executes, and the next scheduled run is blocked for no reason.
**Why it happens:** Without a `try/finally`, only the happy path releases the lock.
**How to avoid:** Wrap the entire lock-acquire-to-lock-release span in `try/finally`; additionally, the TTL index (Pattern 2) is a time-bounded safety net so even a hard process kill self-heals after `LOCK_TTL_SECONDS`.
**Warning signs:** `ingestion_runs` shows repeated `skipped_locked` entries with no matching successful run in between.

## Code Examples

### Run-metadata document shape (`ingestion_runs`)
```python
# Written at run start (status="running") and updated at run end.
{
    "_id": run_id,                 # e.g. str(ObjectId()) or a uuid4 hex
    "started_at": datetime.now(timezone.utc),
    "finished_at": None,           # set on completion
    "status": "running",           # "success" | "partial" | "failed" | "skipped_locked"
    "products_queried": 0,
    "listings_fetched": 0,
    "listings_written": 0,
    "errors": [],                  # list of {"product_ref": ..., "error": str(e)} on partial failure
}
```
This is the concrete artifact satisfying ROADMAP SC-4 ("each run logs metadata ... so a stalled or empty pull is detectable rather than silent") and gives Phase 7's future alerting a queryable source (`db.ingestion_runs.find().sort("started_at", -1).limit(1)` reveals staleness).

### Detecting a stalled/empty pull (groundwork for Phase 7, not built here)
```python
# A query Phase 7's alerting can run later — not implemented in Phase 3,
# but the ingestion_runs shape above is what makes it possible.
latest = db.ingestion_runs.find_one(sort=[("started_at", -1)])
stale = latest is None or (datetime.now(timezone.utc) - latest["started_at"]) > timedelta(hours=interval_hours * 2)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| eBay Finding API `findCompletedItems` (any active/sold listing polling) | Browse API `item_summary/search` (active) | Decommissioned 2025-02-05 | Already accounted for in Phase 1; Phase 3 has no legacy-API exposure since it only ever targets Browse API |

**Deprecated/outdated:** None newly relevant to this phase beyond what Phase 1 already documented.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `shippingOptions` (typed `ShippingOptionSummary`) is present directly on `item_summary/search` results without a follow-up `getItem` call | Summary, Pattern 3, Pitfall 3 | Medium — if wrong, INGEST-03's shipping-cost capture would need an extra `getItem` call per listing (16x-N additional API calls per run, changing the rate-budget math in the Summary); this is inherited from Phase 1's own MEDIUM-confidence finding and remains **unverified against a real Production response** (Plan 01-04 incomplete) — the Phase 3 plan must include a live-verification task before declaring INGEST-03 done |
| A2 | eBay `itemId` is stable and globally unique per listing, suitable as a MongoDB `_id` | Pattern 3 | Low — cross-corroborated via eBay's own documented description ("unique RESTful identifier of the item") and is the field every third-party eBay API wrapper treats as the primary key; low likelihood of being wrong, but still unverified live in this project |
| A3 | Building the Browse API `q` string from `set_name + product-type phrase` (not `required_keywords`) avoids over-constraining search results | Pattern 4, Pitfall 4 | Medium — if eBay's search behaves differently than assumed (e.g. is more lenient/fuzzy than expected), this is a low-cost-to-fix assumption (swap the query-building function), but if too narrow it could silently reduce catalog coverage per run — recommend the live-verification task also spot-checks result counts per product |
| A4 | `apscheduler`'s `[SUS]` legitimacy verdict (`too-new`, `unknown-downloads`, `no-repository`) is a tooling false positive, not a real supply-chain risk | Package Legitimacy Audit | Low — same class of environment-driven false positive documented for `requests`/`python-dotenv` in Phase 1; `agronholm/apscheduler` is independently confirmed via web search as the long-established canonical project; planner still gates behind `checkpoint:human-verify` per protocol regardless |
| A5 | A default `INGESTION_INTERVAL_HOURS=4` balances freshness against the 5,000 calls/day budget with comfortable headroom | Summary | Low — even doubling the assumed per-run call count (pagination, retries) leaves >10x headroom under the default rate limit; this is a tunable default via env var, not a hardcoded constraint, so it is cheap to revise later |

**If this table is empty:** N/A — see entries above; several carry real (not purely theoretical) risk given Phase 1's live-verification gap.

## Open Questions

1. **Does the Browse API's `q` search actually behave as assumed (Pitfall 4 / Assumption A3) against real Production data for this specific catalog?**
   - What we know: eBay's Browse API supports keyword search via `q`; Phase 1's own `verify_ebay_access.py` already uses clean phrase-shaped queries successfully in its authored (but not yet live-run) form.
   - What's unclear: Whether `build_query()`'s exact phrasing returns adequate result counts for all ~16 catalog products, especially newer/lower-search-volume sets (Pitch Black, pre-release as of this research date).
   - Recommendation: The Phase 3 plan's live-verification task should log result counts per product and flag any product returning zero results for a follow-up query-tuning pass — not block the phase on perfecting every query upfront.

2. **What should happen to `active_listings` documents that stop appearing in subsequent runs (the item sold/ended/was removed)?**
   - What we know: Upserting by `itemId` naturally leaves stale documents in place if an item disappears from search results (no delete happens).
   - What's unclear: Whether Phase 3 should mark listings as `stale`/expire them, or whether this is deferred to Phase 4/5 (which will need "current vs. gone" logic anyway for price aggregation).
   - Recommendation: Out of scope for Phase 3's SC — record `fetched_at`/`run_id` on every upsert (already in Pattern 3) so a later phase can determine staleness by "not updated in the last N runs" without Phase 3 needing to implement deletion/expiry logic itself.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|--------------|-----------|---------|----------|
| Python 3.12+ | Worker runtime | Yes | 3.12.13 (confirmed this session) | — |
| PyMongo | MongoDB writes, lock pattern | Yes | 4.17.0 (already installed, confirmed this session) | — |
| APScheduler | Scheduling | No (not yet installed) | Latest 3.11.3 (registry-confirmed) | Install via `requirements.txt`, gated behind `checkpoint:human-verify` per Package Legitimacy Audit |
| MongoDB (Atlas M0) | All writes | Provisioned in Phase 2 (per STATE.md: "User provisioned MongoDB Atlas M0") | — | — |
| `EBAY_CLIENT_ID` / `EBAY_CLIENT_SECRET` in `.env` | Live OAuth + Browse API calls | **No** — lost in a prior incident (STATE.md Blockers); Phase 1 Plan 01-04 (live verification) never completed | — | None — this blocks any *live* run of this phase's worker; code can still be authored and unit-tested (mocking/skipping the live eBay call) but the live-verification task must be explicitly gated on the user re-obtaining credentials, matching Phase 1's own D-01/D-02 pattern |
| Network access to `api.ebay.com` from the execution environment | Live Browse API calls | Not verified this session (sandboxed research environment, consistent with Phase 1's own finding) | — | If the execution/agent environment lacks outbound network access, the live-verification task must be run by the user locally, same as Phase 1's Plan 01-04 |

**Missing dependencies with no fallback:**
- `EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET` — blocks any live proof of INGEST-01/02/03 until the user re-obtains and re-populates them. The Phase 3 plan must not claim these requirements verified without an actual live run.

**Missing dependencies with fallback:**
- `apscheduler` — trivially installable once the legitimacy checkpoint is approved.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 (already installed and configured — `pytest.ini` sets `pythonpath = .`, `testpaths = tests`) |
| Config file | `pytest.ini` (existing, Phase 2) |
| Quick run command | `pytest tests/test_ingest_worker.py -x` |
| Full suite command | `pytest` (runs the whole `tests/` directory, including Phase 2's `test_catalog_schema.py`) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|---------------------|--------------|
| INGEST-01 | `build_query(product)` produces the expected query string per product type; `run_ingestion_once` iterates every catalog product | unit | `pytest tests/test_ingest_worker.py::test_build_query -x` | ❌ Wave 0 |
| INGEST-02 | `acquire_lock`/`release_lock` correctly block a second concurrent acquire and self-heal after TTL; re-running `upsert_listings` with the same `itemId` input produces no duplicate documents (`bulk_write` upsert idempotency) | integration (real MongoDB via `catalog_db`-style fixture) | `pytest tests/test_ingest_worker.py::test_lock_prevents_concurrent_acquire tests/test_ingest_worker.py::test_upsert_idempotent -x` | ❌ Wave 0 |
| INGEST-03 | A listing document written by `upsert_listings` carries both `item_price` and `total_price` (`total_price` = `item_price` + shipping, defaulting to 0.0 when absent) | unit (using a synthetic Browse API response fixture, e.g. reusing `fixtures/ebay_listing_titles.json`'s shape from Phase 1) | `pytest tests/test_ingest_worker.py::test_price_and_shipping_captured -x` | ❌ Wave 0 |
| INGEST-01/02/03 (live proof) | A real run against Production writes real listings with real price/shipping into `active_listings` and a completed `ingestion_runs` document | manual-only (requires real credentials + network — same rationale as Phase 1's smoke-script-over-pytest) | `python -m scripts.ingest_worker --once` (a one-shot CLI flag recommended for manual verification without waiting for the scheduler) | ❌ Wave 0 — gated on user re-obtaining eBay credentials |

### Sampling Rate
- **Per task commit:** `pytest tests/test_ingest_worker.py -x`
- **Per wave merge:** `pytest` (full suite, including Phase 2's existing catalog tests)
- **Phase gate:** Full suite green AND the manual live-run task confirmed by the user (credentials permitting) before `/gsd-verify-work`; if credentials remain unavailable at phase-gate time, the plan should explicitly document this as a known incomplete verification item rather than silently passing.

### Wave 0 Gaps
- [ ] `tests/test_ingest_worker.py` — does not exist yet; covers INGEST-01/02/03 unit + integration cases
- [ ] `scripts/ingest_worker.py` — does not exist yet; core deliverable (`run_ingestion_once`, `build_query`, `acquire_lock`/`release_lock`, `upsert_listings`, APScheduler entrypoint)
- [ ] `db/init_collections.py` extension — add `active_listings` (unique index or `_id`=itemId, already inherently unique) and `ingestion_locks` (TTL index on `expires_at`) and `ingestion_runs` (index on `started_at` for the "latest run" query) collection setup
- [ ] Framework install: `pip install apscheduler==3.11.3` — gate behind `checkpoint:human-verify` per Package Legitimacy Audit

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|----------------|---------|---------------------|
| V2 Authentication | No | Application-level (client-credentials) auth to an external API only; no end-user auth surface in this phase |
| V3 Session Management | No | No sessions — stateless application access token, refreshed once per run |
| V4 Access Control | No | No access-control surface (backend worker, no user-facing endpoint) |
| V5 Input Validation | Yes | Catalog product data (`scripts/catalog_data.CATALOG`) is trusted/curated (Phase 2), but eBay API responses are external/untrusted input — validate `price`/`itemId` presence before writing (Pitfall 3), never trust response shape blindly |
| V6 Cryptography / Secrets Handling | Yes | Reuses Phase 1's `.env`-based credential pattern (`EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET`) plus a new `MONGODB_URI` read (already established in Phase 2's `scripts/seed_catalog.py`); never log the full access token or the MongoDB connection string |

### Known Threat Patterns for this phase's stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Logging the full OAuth access token or MongoDB URI in worker output/error traces | Information Disclosure | Log only token metadata (`token_type`/`expires_in`) and generic MongoDB connection status (connected/failed), never the raw secret strings — mirrors Phase 1's `scripts/ebay_client.py` discipline |
| A crashed/killed worker process leaving a stale lock that blocks all future runs indefinitely | Denial of Service (self-inflicted) | TTL index on `ingestion_locks.expires_at` bounds the worst case to `LOCK_TTL_SECONDS`, even without a graceful `finally` release |
| Untrusted/malformed eBay API response fields crashing the worker (missing `price`, unexpected types) | Denial of Service | Defensive field access (`.get()` with defaults, explicit `if "price" not in item: continue` per Pitfall 3) so one malformed item doesn't abort the whole run |
| Two worker instances racing to acquire the same catalog data concurrently, producing double-counted API usage against the daily rate limit | Tampering / resource exhaustion | The MongoDB lock (Pattern 2) also protects the shared eBay rate-limit budget, not just data integrity — a second instance that fails to acquire the lock makes zero eBay API calls that run |

## Sources

### Primary (HIGH confidence)
- `pip index versions apscheduler` (registry check, this session) — `[VERIFIED: pypi registry]`
- `pip show pymongo` (this session, confirms 4.17.0 already installed)
- Direct reads of this repository's `scripts/ebay_client.py`, `scripts/verify_ebay_access.py`, `db/init_collections.py`, `scripts/seed_catalog.py`, `scripts/catalog_data.py`, `tests/conftest.py` (this session)

### Secondary (MEDIUM confidence — official docs/canonical repos, cross-corroborated via web search)
- [APScheduler User guide (3.x)](https://apscheduler.readthedocs.io/en/3.x/userguide.html) — IntervalTrigger/CronTrigger, max_instances, coalesce, misfire_grace_time
- [apscheduler.schedulers.background — APScheduler docs](https://apscheduler.readthedocs.io/en/3.x/modules/schedulers/background.html) and [apscheduler.schedulers.blocking — APScheduler docs](https://apscheduler.readthedocs.io/en/3.x/modules/schedulers/blocking.html) — BackgroundScheduler vs BlockingScheduler
- [GitHub - agronholm/apscheduler](https://github.com/agronholm/apscheduler) and [APScheduler · PyPI](https://pypi.org/project/APScheduler/) — legitimacy/provenance confirmation
- [ItemSummary: eBay Browse API](https://developer.ebay.com/api-docs/buy/browse/types/gct:ItemSummary), [ShippingOptionSummary: eBay Browse API](https://developer.ebay.com/api-docs/buy/browse/types/gct:ShippingOptionSummary), [search: eBay Browse API](https://developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search) — response shape (via search-engine snippets; direct WebFetch to developer.ebay.com timed out this session, same limitation Phase 1's research recorded)
- [API Call Limits | eBay Developers Program](https://developer.ebay.com/develop/get-started/api-call-limits) — 5,000 calls/day default tier, consistent with CLAUDE.md
- [Bulk Write Operations - PyMongo documentation](https://pymongo.readthedocs.io/en/stable/examples/bulk.html) — `UpdateOne(upsert=True)` idempotency pattern
- [How to Implement Distributed Locks with MongoDB](https://oneuptime.com/blog/post/2026-03-31-mongodb-distributed-locks/view) and [TTL Indexes - MongoDB Docs](https://www.mongodb.com/docs/v7.0/core/index-ttl/) — lock-document + TTL pattern
- `.planning/phases/01-ebay-api-feasibility-gate/01-RESEARCH.md` — reused Phase 1 findings on OAuth/Browse API shape, rate limits, and the "Sandbox is not Production" pitfall class

### Tertiary (LOW confidence — used only for cross-corroboration)
- Various eBay Community forum threads on rate limits (already reflected in CLAUDE.md at MEDIUM-HIGH confidence per that document's own sourcing)

## Metadata

**Confidence breakdown:**
- APScheduler scheduling/locking mechanics: MEDIUM — official docs cited via search-engine snippets, cross-corroborated across independent sources; matches CLAUDE.md's own version pin exactly
- MongoDB TTL lock pattern: MEDIUM — a well-documented community idiom built on official MongoDB primitives (TTL index, atomic `find_one_and_update`), not an official MongoDB-authored named pattern
- eBay Browse API response shape (price, shippingOptions, itemId): MEDIUM, but functionally **unverified live in this project** — inherits and does not improve on Phase 1's own MEDIUM confidence, since Plan 01-04's live run never completed
- Architectural separation of `active_listings` from `price_points`: HIGH — this is a direct, source-grounded consequence of reading Phase 2's actual `db/init_collections.py` docstrings and schema, not an external claim

**Research date:** 2026-07-14
**Valid until:** 2026-08-13 (30 days — APScheduler/PyMongo mechanics are stable; re-verify the eBay Browse API response shape claims sooner, specifically as soon as Plan 01-04's live credentials become available, since those claims are currently unverified rather than merely "may drift")

---
*Phase: 3-Active-Listing Ingestion Pipeline*
*Research completed: 2026-07-14*
