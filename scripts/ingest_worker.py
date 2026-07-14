"""Scheduled active-listing ingestion worker (INGEST-01, INGEST-02, INGEST-03).

Reuses Phase 1's `scripts/ebay_client.py` (`get_app_token`,
`search_sealed_listings`, `total_cost`) and Phase 2's
`scripts/catalog_data.CATALOG` / `db/init_collections.init_collections`
as-is — no reimplementation. This module is the whole point of Phase
3: a scheduled, idempotent, lock-guarded worker that pulls active eBay
listings for every catalog product and writes them into
`active_listings`, records per-run metadata into `ingestion_runs`, and
prevents overlapping runs via a MongoDB TTL lock in `ingestion_locks`.

No token caching/refresh wrapper is built here — `get_app_token()` is
called once per run and the resulting token is reused across every
catalog product query in that run (03-RESEARCH.md Anti-Patterns; a
~16-product run completes in seconds to low minutes, nowhere near the
~7,200s token lifetime).

No top-level side effects on import: no MongoClient construction, no
network calls, no scheduler startup happen merely from `import
scripts.ingest_worker`. `apscheduler` is intentionally NOT imported at
module top level — that import lives inside `main()` so this module
imports cleanly in test environments that never exercise the
scheduler path and never need apscheduler installed.

Credential hygiene (threat T-03-01, mirrors scripts/ebay_client.py and
scripts/seed_catalog.py discipline): the raw eBay access token, the
Authorization header, and MONGODB_URI are never logged/printed — only
counts, per-product query strings, and token metadata are ever
surfaced in worker output.
"""

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

# Maps a catalog product_type to the Browse API search phrase used by
# build_query(). Deliberately NOT the same as a catalog product's
# required_keywords (03-RESEARCH.md Pattern 4 / Pitfall 4) — that field
# carries redundant disambiguation tokens for Phase 4's title-matching
# step, and joining it into one query string over-constrains eBay's
# search.
PRODUCT_TYPE_SEARCH_TERMS = {
    "booster_pack": "Booster Pack",
    "booster_box": "Booster Box",
    "etb": "Elite Trainer Box",
    "booster_bundle": "Booster Bundle",
}

LOCK_ID = "active_listing_ingestion"
LOCK_TTL_SECONDS = 900  # generously longer than one run should ever take


def build_query(product: dict) -> str:
    """Build the Browse API `q` search string for a catalog product.

    Returns "Pokemon {set_name} {product-type phrase}" — never joins
    `required_keywords` (that field is Phase 4's matching input, not
    a search-query source; 03-RESEARCH.md Pitfall 4).
    """
    return f"Pokemon {product['set_name']} {PRODUCT_TYPE_SEARCH_TERMS[product['product_type']]}"


def ensure_lock_index(db):
    """Create the TTL index on ingestion_locks.expires_at.

    expireAfterSeconds=0: MongoDB expires the document at the exact
    datetime stored in expires_at, not N seconds after insertion —
    this lets each acquire set its own explicit expiry. Safe to call
    on every run (create_index is idempotent).
    """
    db.ingestion_locks.create_index("expires_at", expireAfterSeconds=0)


def acquire_lock(db, holder: str) -> bool:
    """Atomically acquire the cross-process ingestion lock.

    Returns True if the lock was acquired (no live lock existed, or
    the prior lock had already expired). Returns False if a live
    (non-expired) lock document already exists under a different
    acquire — this is the durable, cross-process concurrency guard
    (T-03-02, T-03-04, SC-2), not merely an in-process guard.
    """
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
        # A live (non-expired) lock document already exists with this
        # _id and didn't match the {"expires_at": {"$lte": now}}
        # filter — another run currently holds the lock.
        return False


def release_lock(db, holder: str) -> None:
    """Release the ingestion lock, only if `holder` still holds it.

    Deleting conditionally on holder avoids deleting a newer holder's
    lock if this run overran its own TTL (03-RESEARCH.md Pattern 2).
    """
    db.ingestion_locks.delete_one({"_id": LOCK_ID, "holder": holder})


def upsert_listings(db, product_ref, items, run_id, fetched_at):
    """Idempotently upsert eBay listing items into active_listings.

    Builds one UpdateOne(_id=itemId, upsert=True) per valid item so
    re-running with the same itemIds never creates duplicates
    (INGEST-02, T-03-05). Each item's doc-build is wrapped in a
    defensive try/except so one malformed eBay item never aborts the
    whole batch (T-03-03, 03-RESEARCH.md Pitfall 3) — items missing a
    "price" key are explicitly skipped first.

    Reuses scripts.ebay_client.total_cost() as the single source of
    truth for the item+shipping math (item_price + shipping_cost,
    shipping defaulting to 0.0 when shippingOptions is absent) rather
    than re-deriving it here.

    Returns:
        The pymongo BulkWriteResult, or None if there were no valid
        ops to write (empty `items`, or every item was skipped).
    """
    ops = []
    for item in items:
        if "price" not in item:
            continue
        try:
            item_price = float(item["price"]["value"])
            price_total = total_cost(item)
            shipping_cost = round(price_total - item_price, 2)
            doc = {
                "_id": item["itemId"],
                "product_ref": product_ref,
                "title": item["title"],
                "item_price": item_price,
                "shipping_cost": shipping_cost,
                "total_price": price_total,
                "category_id": item.get("categories", [{}])[0].get("categoryId"),
                "fetched_at": fetched_at,
                "run_id": run_id,
            }
        except (KeyError, ValueError, TypeError):
            # Malformed/unexpected shape on this one item — skip it,
            # never abort the rest of the batch (T-03-03).
            continue
        ops.append(UpdateOne({"_id": doc["_id"]}, {"$set": doc}, upsert=True))

    if not ops:
        return None
    return db.active_listings.bulk_write(ops)


def run_ingestion_once(db):
    """Orchestrate one full, lock-guarded ingestion run.

    Ordered flow (03-RESEARCH.md System Architecture Diagram):
      1. ensure_lock_index(db) — idempotent, safe to call every run.
      2. acquire_lock(db, run_id) — if the lock is already held,
         write a single status="skipped_locked" ingestion_runs
         document and return immediately WITHOUT calling get_app_token
         or search_sealed_listings (T-03-04, SC-2: a second concurrent
         run issues zero eBay calls, protecting both data integrity
         and the shared rate-limit budget).
      3. Otherwise, insert a status="running" run-start document, then
         (wrapped in try/finally so release_lock always runs, T-03-02
         / Pitfall 5) fetch a token ONCE and reuse it across every
         catalog product query (Anti-Patterns — never re-authenticate
         per product).
      4. For each product in CATALOG: build the query, search, and
         upsert — wrapped in a per-product try/except so one product's
         failure (e.g. an eBay 5xx) is recorded into errors[] and does
         not abort the remaining products or leave the lock held
         (T-03-03).
      5. Update the run document with final counts/status/finished_at.

    Returns:
        The final ingestion_runs document (dict) for this run.
    """
    run_id = uuid.uuid4().hex
    started_at = datetime.now(timezone.utc)

    ensure_lock_index(db)

    if not acquire_lock(db, run_id):
        skipped_doc = {
            "_id": run_id,
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc),
            "status": "skipped_locked",
            "products_queried": 0,
            "listings_fetched": 0,
            "listings_written": 0,
            "errors": [],
        }
        db.ingestion_runs.insert_one(skipped_doc)
        return skipped_doc

    db.ingestion_runs.insert_one(
        {
            "_id": run_id,
            "started_at": started_at,
            "finished_at": None,
            "status": "running",
            "products_queried": 0,
            "listings_fetched": 0,
            "listings_written": 0,
            "errors": [],
        }
    )

    products_queried = 0
    listings_fetched = 0
    listings_written = 0
    errors = []

    try:
        token = get_app_token()
        access_token = token["access_token"]

        for product in CATALOG:
            product_ref = (
                f"{product['set_name']}_{product['product_type']}".lower().replace(" ", "-")
            )
            try:
                query = build_query(product)
                items = search_sealed_listings(access_token, query)
                result = upsert_listings(
                    db, product_ref, items, run_id, fetched_at=started_at
                )
                products_queried += 1
                listings_fetched += len(items)
                if result is not None:
                    listings_written += len(result.upserted_ids) + result.modified_count
            except Exception as e:  # noqa: BLE001 - isolate one product's failure
                errors.append({"product_ref": product_ref, "error": str(e)})

        status = "success" if not errors else "partial"
        update_doc = {
            "finished_at": datetime.now(timezone.utc),
            "status": status,
            "products_queried": products_queried,
            "listings_fetched": listings_fetched,
            "listings_written": listings_written,
            "errors": errors,
        }
        db.ingestion_runs.update_one({"_id": run_id}, {"$set": update_doc})
        return db.ingestion_runs.find_one({"_id": run_id})
    finally:
        release_lock(db, run_id)


def main() -> int:
    """Entrypoint: `--once` for a single manual/CI run, else a
    BlockingScheduler + IntervalTrigger firing run_ingestion_once every
    INGESTION_INTERVAL_HOURS (default 4).

    Mirrors scripts/seed_catalog.py's main() shape: load_dotenv() ->
    read MONGODB_URI from os.environ -> MongoClient -> try/finally:
    client.close() -> init_collections(db) before the primary op.

    Never prints mongodb_uri or the raw eBay access token — only a
    generic connected/started message and, per run, the counts
    returned by run_ingestion_once.
    """
    load_dotenv()
    mongodb_uri = os.environ["MONGODB_URI"]
    client = MongoClient(mongodb_uri)
    try:
        db = client["pokemonview"]
        init_collections(db)

        if "--once" in sys.argv:
            result = run_ingestion_once(db)
            print(
                f"run_id={result['_id']} status={result['status']} "
                f"products_queried={result['products_queried']} "
                f"listings_fetched={result['listings_fetched']} "
                f"listings_written={result['listings_written']}"
            )
            return 0

        # Lazy import: apscheduler is only required for the scheduled
        # (non --once) path, so the module itself never requires
        # apscheduler to be installed just to be imported/tested.
        from apscheduler.schedulers.blocking import BlockingScheduler
        from apscheduler.triggers.interval import IntervalTrigger

        interval_hours = int(os.environ.get("INGESTION_INTERVAL_HOURS", "4"))
        scheduler = BlockingScheduler()

        def shutdown(signum, frame):
            scheduler.shutdown(wait=False)
            client.close()
            sys.exit(0)

        import signal

        signal.signal(signal.SIGTERM, shutdown)
        signal.signal(signal.SIGINT, shutdown)

        scheduler.add_job(
            run_ingestion_once,
            trigger=IntervalTrigger(hours=interval_hours),
            args=[db],
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300,
        )
        print(f"ingestion worker started — interval_hours={interval_hours}")
        scheduler.start()
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main())
