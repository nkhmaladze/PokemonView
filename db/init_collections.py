"""Idempotent MongoDB collection bootstrap for the product catalog data
model and Phase 3's active-listing ingestion pipeline.

Creates the `products` collection (with a `$jsonSchema` validator and a
compound index) and the `price_points` time-series collection.
`price_points` is only ever created if it doesn't already exist —
`timeseries` options are a creation-time-only setting with no
supported retrofit path (Pitfall 1, 02-RESEARCH.md), so getting it
right now (empty, reserved for Phase 4's matching step, which resolves
a canonical `product_id` and is the actual writer of per-point
`{ts, product_id, item_price, total_price}` documents) avoids a
data-losing drop-and-recreate migration later. The `products`
validator, by contrast, IS mutable post-creation via `collMod` — this
function applies it unconditionally (create on first run, `collMod` on
every run after) so validator/index changes reach a collection that
already existed before the change, not just fresh ones.

The `products` validator deliberately allows `null` for release_date,
msrp, and image_url (Pitfall 3, D-02) so Pitch Black's pre-release
catalog documents seed cleanly now and are corrected in place once
the set actually releases, without a schema workaround.

Also creates the three collections Phase 3's ingestion worker actually
writes into: `active_listings` (raw eBay listings keyed by `itemId`,
carrying a `product_ref` provenance field that names the catalog query
slug that found the listing, NOT a matched canonical `product_id`),
`ingestion_locks` (a cross-process run lock with a TTL self-heal on
`expires_at`), and `ingestion_runs` (per-run observability metadata).
`active_listings` is deliberately kept separate from `price_points`
so unmatched raw listings never corrupt that time-series collection's
`metaField=product_id` contract (03-RESEARCH.md Pitfall 1).

No top-level MongoDB calls execute on import — init_collections(db)
must be explicitly invoked by a caller (see scripts/seed_catalog.py
or tests/conftest.py), mirroring the "no top-level side effects on
import" discipline established in scripts/ebay_client.py.
"""

from pymongo import ASCENDING, DESCENDING

PRODUCTS_JSON_SCHEMA = {
    "bsonType": "object",
    "additionalProperties": False,
    "required": [
        "set_name",
        "product_type",
        "language",
        "display_name",
        "required_keywords",
    ],
    "properties": {
        # Explicitly declared so upserts that set _id (see
        # scripts/seed_catalog.py's deterministic slug _id) aren't
        # rejected by additionalProperties: false — MongoDB validates
        # the full resulting document, _id included, against this list.
        "_id": {"bsonType": "string"},
        "set_name": {"bsonType": "string"},
        "product_type": {
            "enum": ["booster_pack", "booster_box", "etb", "booster_bundle"]
        },
        "language": {"bsonType": "string", "enum": ["en"]},
        "display_name": {"bsonType": "string"},
        "required_keywords": {
            "bsonType": "array",
            "items": {"bsonType": "string"},
        },
        # Provisional fields: null is explicitly allowed (Pitfall 3, D-02)
        # so Pitch Black's pre-release documents seed without a workaround.
        "release_date": {"bsonType": ["date", "null"]},
        "msrp": {"bsonType": ["double", "int", "null"]},
        "image_url": {"bsonType": ["string", "null"]},
        "verified": {"bsonType": ["bool"]},
        "verified_at": {"bsonType": ["date", "null"]},
    },
}

# Per-point document shape Phase 4's matching step will write into
# price_points: {ts, product_id, item_price, total_price} — item-only
# and total (item + shipping) price points over time, keyed by
# product_id (metaField) and bucketed by ts (timeField). Phase 3's
# ingestion worker does NOT write here — it writes raw listings into
# active_listings instead (see module docstring).
PRICE_POINTS_TIMESERIES_OPTIONS = {
    "timeField": "ts",
    "metaField": "product_id",
    "granularity": "hours",
}


def init_collections(db):
    """Idempotently create the products, price_points, active_listings,
    ingestion_locks, and ingestion_runs collections.

    Checks db.list_collection_names() before calling create_collection()
    for each collection — MongoDB raises an error if create_collection()
    is called on a name that already exists, so this guard makes the
    function safe to call on every startup/seed run without side
    effects on subsequent calls.

    products: created with a $jsonSchema validator
    (validationLevel="strict", validationAction="error") enforcing the
    catalog document shape for every writer (V5 input-validation
    control, not just this phase's seed script), plus a compound index
    on {set_name: 1, product_type: 1} supporting queries by set alone
    or by set + product_type together (compound-index prefix rule).

    price_points: created empty as a native time-series collection
    (timeField "ts", metaField "product_id", granularity "hours"),
    reserved for Phase 4's matching step to write per-point documents
    shaped {ts, product_id, item_price, total_price} once a matched
    canonical product_id exists. No validator is attached to this
    collection. Phase 3's ingestion worker does NOT write here.

    active_listings: created as a plain collection (no timeseries
    option, no validator) holding Phase 3's raw eBay listing output,
    keyed by _id=itemId. A non-unique index on product_ref (the
    catalog query slug that found the listing, not a matched
    product_id) supports Phase 4's per-catalog-product reads.

    ingestion_locks: created as a plain collection providing the
    cross-process concurrency guard Phase 3's ingestion worker uses to
    prevent overlapping runs. A TTL index on expires_at
    (expireAfterSeconds=0) expires each lock document at the exact
    datetime stored in its own expires_at field, self-healing a stale
    lock left by a hard-killed worker process.

    ingestion_runs: created as a plain collection recording per-run
    observability metadata Phase 3's ingestion worker writes on every
    run. A descending index on started_at supports the latest-run
    query Phase 7's staleness alerting will use.

    Args:
        db: An already-connected pymongo Database handle. This
            function does not read MONGODB_URI or construct a
            MongoClient itself — credential handling stays with the
            caller.
    """
    if "products" not in db.list_collection_names():
        db.create_collection(
            "products",
            validator={"$jsonSchema": PRODUCTS_JSON_SCHEMA},
            validationLevel="strict",
            validationAction="error",
        )
    else:
        # Unlike timeseries options, a validator IS mutable post-creation
        # via collMod — apply it unconditionally so schema changes (e.g.
        # additionalProperties: false) reach a collection that already
        # existed before those changes were made, instead of silently
        # never taking effect on it.
        db.command(
            "collMod",
            "products",
            validator={"$jsonSchema": PRODUCTS_JSON_SCHEMA},
            validationLevel="strict",
            validationAction="error",
        )

    # MongoDB refuses to redefine an existing index's options (e.g.
    # non-unique -> unique) under the same auto-generated name — it
    # raises IndexKeySpecsConflict rather than updating in place. Drop
    # first if a stale non-unique version exists (e.g. from a
    # pre-WR-03 deployment) so create_index below stays idempotent.
    existing_indexes = db.products.index_information()
    index_name = "set_name_1_product_type_1"
    if index_name in existing_indexes and not existing_indexes[index_name].get(
        "unique", False
    ):
        db.products.drop_index(index_name)

    db.products.create_index(
        [("set_name", ASCENDING), ("product_type", ASCENDING)],
        unique=True,
    )

    if "price_points" not in db.list_collection_names():
        db.create_collection(
            "price_points",
            timeseries=PRICE_POINTS_TIMESERIES_OPTIONS,
        )

    # active_listings: a PLAIN collection (no timeseries option, no
    # $jsonSchema validator) holding Phase 3's raw eBay listing output,
    # keyed by _id=itemId (stable/unique per listing, so no separate
    # unique index is needed). product_ref is provenance only (which
    # catalog query found this listing), not a matched canonical
    # product_id, so this collection is deliberately kept separate from
    # price_points (Pitfall 1, 03-RESEARCH.md).
    if "active_listings" not in db.list_collection_names():
        db.create_collection("active_listings")
    db.active_listings.create_index([("product_ref", ASCENDING)])

    # ingestion_locks: a PLAIN collection providing the cross-process
    # concurrency guard (T-03-02 / SC-2). The TTL index on expires_at
    # with expireAfterSeconds=0 expires each lock document at the exact
    # datetime stored in its own expires_at field (per-acquire explicit
    # expiry, not a fixed N seconds after insertion) — this is the
    # stale-lock self-heal safety net for a hard-killed worker that
    # never reaches its finally release_lock (03-RESEARCH.md Pattern 2).
    if "ingestion_locks" not in db.list_collection_names():
        db.create_collection("ingestion_locks")
    db.ingestion_locks.create_index("expires_at", expireAfterSeconds=0)

    # ingestion_runs: a PLAIN collection recording per-run observability
    # metadata (SC-4). The descending index on started_at supports the
    # latest-run query
    # (db.ingestion_runs.find_one(sort=[("started_at", -1)])) that
    # Phase 7's staleness alerting will use.
    if "ingestion_runs" not in db.list_collection_names():
        db.create_collection("ingestion_runs")
    db.ingestion_runs.create_index([("started_at", DESCENDING)])
