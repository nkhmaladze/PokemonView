"""Idempotent catalog seed entrypoint (CATALOG-01, CATALOG-02).

Proves the D-02 "seed-now-correct-later" workflow: `seed_catalog(db,
catalog)` upserts every curated `scripts.catalog_data.CATALOG` entry
into the `products` collection keyed on a deterministic slug `_id`
(`{set_name}_{product_type}`, lowercased, spaces to hyphens — Pattern
2, 02-RESEARCH.md), so re-running the seed after Pitch Black's actual
post-release data lands (D-02) or after any other catalog correction
updates documents in place instead of duplicating them (Pitfall 5).
This also satisfies D-06: `booster_bundle` is seeded as its own
distinct `(set_name, product_type)` slug, never conflated with
`booster_box` or `booster_pack`.

Uses `db.products.bulk_write([UpdateOne(..., upsert=True), ...])` —
never `insert_many` — so idempotency is guaranteed structurally, not
just by convention (Anti-Patterns, 02-RESEARCH.md).

Credential hygiene (mirrors Phase 1's scripts/verify_ebay_access.py
pattern): `MONGODB_URI` is read only via `os.environ` after
`load_dotenv()`, and the full connection string is never printed —
only success counts and, on the provisional-data path, a WARNING
naming the affected set.

No top-level MongoDB calls execute on import; `seed_catalog(db,
catalog)` and `main()` must be explicitly invoked (mirrors
db/init_collections.py's "no top-level side effects on import"
discipline).

Run as a module from the repo root (relies on the scripts/__init__.py
and db/__init__.py package markers):

    python -m scripts.seed_catalog
"""

import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne

from db.init_collections import init_collections
from scripts.catalog_data import CATALOG


def seed_catalog(db, catalog):
    """Idempotently upsert every catalog entry into db.products.

    Builds a deterministic slug `_id` per entry
    (`f"{set_name}_{product_type}".lower().replace(" ", "-")`,
    Pattern 2) and upserts a COPY of each dict — the shared CATALOG
    constant is never mutated. `release_date` is converted from its
    ISO "YYYY-MM-DD" string form to a Python `datetime` via
    `datetime.fromisoformat` when present; `None` (Pitch Black's
    not-yet-applicable case is not currently used, but the validator
    permits null) is left as-is (Pitfall 3).

    Args:
        db: An already-connected pymongo Database handle.
        catalog: A list of catalog entry dicts (shape: see
            scripts/catalog_data.py).

    Returns:
        The pymongo BulkWriteResult from db.products.bulk_write, or
        None if catalog was empty (no-op).
    """
    ops = []
    for product in catalog:
        doc = dict(product)  # copy — never mutate the shared CATALOG constant
        slug = f"{doc['set_name']}_{doc['product_type']}".lower().replace(" ", "-")
        doc["_id"] = slug
        if doc.get("release_date"):
            doc["release_date"] = datetime.fromisoformat(doc["release_date"])
        ops.append(UpdateOne({"_id": slug}, {"$set": doc}, upsert=True))

    if not ops:
        return None

    result = db.products.bulk_write(ops)
    print(
        f"matched={result.matched_count} "
        f"upserted={len(result.upserted_ids)} "
        f"modified={result.modified_count}"
    )
    return result


def main() -> int:
    """Seed the real `pokemonview` database from CATALOG.

    Loads MONGODB_URI from the environment, ensures the validated
    collections exist (init_collections), seeds the catalog, and
    warns (without failing) if any seeded entry is still provisional
    (`verified: False` — currently Pitch Black, per D-02).

    Returns:
        0 on success.
    """
    load_dotenv()
    mongodb_uri = os.environ["MONGODB_URI"]
    client = MongoClient(mongodb_uri)
    try:
        db = client["pokemonview"]

        init_collections(db)
        seed_catalog(db, CATALOG)

        unverified_sets = sorted(
            {product["set_name"] for product in CATALOG if not product.get("verified", True)}
        )
        if unverified_sets:
            print(
                f"WARNING: the following set(s) were seeded with provisional "
                f"(verified=False) data: {', '.join(unverified_sets)}. Per D-02, "
                "re-run `python -m scripts.seed_catalog` after the set's real "
                "post-release data is confirmed and scripts/catalog_data.py is "
                "updated, to correct these entries in place.",
                file=sys.stderr,
            )
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
