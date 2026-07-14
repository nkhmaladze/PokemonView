"""Idempotent MongoDB collection bootstrap for the product catalog data model.

Creates the `products` collection (with a `$jsonSchema` validator and a
compound index) and the `price_points` time-series collection, both
only if they don't already exist. This create-if-not-exists guard
exists because MongoDB has no supported path to retrofit a
`$jsonSchema` validator or `timeseries` options onto an
already-existing plain collection — both are creation-time-only
settings (Pitfall 1, 02-RESEARCH.md). Getting `price_points` right now
(empty, reserved for Phase 3's ingestion worker) avoids a
data-losing drop-and-recreate migration later.

The `products` validator deliberately allows `null` for release_date,
msrp, and image_url (Pitfall 3, D-02) so Pitch Black's pre-release
catalog documents seed cleanly now and are corrected in place once
the set actually releases, without a schema workaround.

No top-level MongoDB calls execute on import — init_collections(db)
must be explicitly invoked by a caller (see scripts/seed_catalog.py
or tests/conftest.py), mirroring the "no top-level side effects on
import" discipline established in scripts/ebay_client.py.
"""

from pymongo import ASCENDING

PRODUCTS_JSON_SCHEMA = {
    "bsonType": "object",
    "required": [
        "set_name",
        "product_type",
        "language",
        "display_name",
        "required_keywords",
    ],
    "properties": {
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

# Per-point document shape Phase 3's ingestion worker will write into
# price_points: {ts, product_id, item_price, total_price} — item-only
# and total (item + shipping) price points over time, keyed by
# product_id (metaField) and bucketed by ts (timeField).
PRICE_POINTS_TIMESERIES_OPTIONS = {
    "timeField": "ts",
    "metaField": "product_id",
    "granularity": "hours",
}


def init_collections(db):
    """Idempotently create the products and price_points collections.

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
    reserved for Phase 3's ingestion worker to write per-point
    documents shaped {ts, product_id, item_price, total_price}. No
    validator is attached to this collection.

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

    db.products.create_index(
        [("set_name", ASCENDING), ("product_type", ASCENDING)]
    )

    if "price_points" not in db.list_collection_names():
        db.create_collection(
            "price_points",
            timeseries=PRICE_POINTS_TIMESERIES_OPTIONS,
        )
