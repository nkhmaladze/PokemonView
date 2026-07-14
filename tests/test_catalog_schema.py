"""Contract tests for the product catalog data model (CATALOG-01, CATALOG-02).

Four tests, each consuming the `catalog_db` fixture from
tests/conftest.py (which seeds a dedicated `pokemonview_test` database
via db.init_collections + scripts.seed_catalog before yielding):

  - test_catalog_completeness           (CATALOG-01)
  - test_seed_idempotent                (CATALOG-01, Pitfall 5)
  - test_schema_validator_rejects_malformed  (CATALOG-02, T-02-01 / V5)
  - test_query_by_set_and_type          (CATALOG-02)

These tests are authored in Plan 02-05 and intentionally RED until
Plan 02-06 lands db/init_collections.py's schema/index and
scripts/seed_catalog.py's idempotent upsert (the fixture's lazy
imports of those modules will fail to resolve until then).

Plain pytest `assert` style throughout — no unittest.TestCase
(02-PATTERNS.md: first test file in the repo, no prior convention to
follow beyond RESEARCH.md's Validation Architecture).
"""

import pymongo.errors

from scripts.catalog_data import CATALOG

# scripts.seed_catalog does not exist yet as of Plan 02-05 (it lands in
# Plan 02-06) — deferred into test_seed_idempotent's body rather than
# imported at module top level, so `pytest --collect-only` succeeds now
# (Nyquist Wave 0 scaffold-first requirement) instead of erroring out.

ALLOWED_PRODUCT_TYPES = {"booster_pack", "booster_box", "etb", "booster_bundle"}


def test_catalog_completeness(catalog_db):
    """products holds exactly one document per CATALOG entry (CATALOG-01)."""
    count = catalog_db.products.count_documents({})
    assert count == len(CATALOG), (
        f"expected {len(CATALOG)} seeded products (one per CATALOG entry), "
        f"found {count}"
    )

    set_names = set(catalog_db.products.distinct("set_name"))
    expected_set_names = {product["set_name"] for product in CATALOG}
    assert set_names == expected_set_names, (
        f"expected set_name values {expected_set_names}, found {set_names}"
    )

    product_types = set(catalog_db.products.distinct("product_type"))
    assert product_types <= ALLOWED_PRODUCT_TYPES, (
        f"product_type values {product_types} must be a subset of "
        f"{ALLOWED_PRODUCT_TYPES}"
    )

    pairs = [
        (doc["set_name"], doc["product_type"])
        for doc in catalog_db.products.find({}, {"set_name": 1, "product_type": 1})
    ]
    assert len(pairs) == len(set(pairs)), (
        "found duplicate (set_name, product_type) pairs in products — "
        "each pair must be a distinct catalog entry"
    )


def test_seed_idempotent(catalog_db):
    """Re-running seed_catalog does not create duplicate documents (Pitfall 5)."""
    from scripts.seed_catalog import seed_catalog

    count_before = catalog_db.products.count_documents({})

    seed_catalog(catalog_db, CATALOG)

    count_after = catalog_db.products.count_documents({})
    assert count_after == count_before, (
        f"re-running seed_catalog changed document count from "
        f"{count_before} to {count_after} — upsert-by-slug must be idempotent"
    )


def test_schema_validator_rejects_malformed(catalog_db):
    """$jsonSchema validator rejects an invalid product_type (T-02-01, V5)."""
    malformed = {
        "_id": "malformed-test-doc",
        "set_name": "Perfect Order",
        "product_type": "lot_bundle",  # not in the enum
        "language": "en",
        "display_name": "Malformed test document",
        "required_keywords": ["malformed"],
    }
    try:
        catalog_db.products.insert_one(malformed)
        raised = False
    except (pymongo.errors.WriteError, pymongo.errors.OperationFailure):
        raised = True

    assert raised, (
        "expected pymongo to raise WriteError/OperationFailure when inserting "
        "a document with an invalid product_type, but the insert succeeded — "
        "the $jsonSchema validator is not enforcing the product_type enum"
    )


def test_query_by_set_and_type(catalog_db):
    """products is queryable by set_name alone, and by set_name + product_type (CATALOG-02)."""
    target_set = CATALOG[0]["set_name"]

    by_set = list(catalog_db.products.find({"set_name": target_set}))
    expected_for_set = [p for p in CATALOG if p["set_name"] == target_set]
    assert len(by_set) == len(expected_for_set), (
        f"querying by set_name={target_set!r} returned {len(by_set)} docs, "
        f"expected {len(expected_for_set)}"
    )

    by_set_and_type = list(
        catalog_db.products.find(
            {"set_name": target_set, "product_type": "booster_box"}
        )
    )
    assert len(by_set_and_type) == 1, (
        f"querying by set_name={target_set!r} + product_type='booster_box' "
        f"should return exactly one document, found {len(by_set_and_type)}"
    )

    index_info = catalog_db.products.index_information()
    index_key_lists = [spec["key"] for spec in index_info.values()]
    assert any(
        ("set_name", 1) in keys and ("product_type", 1) in keys
        for keys in index_key_lists
    ), (
        f"expected a compound index covering set_name and product_type, "
        f"found indexes: {index_info}"
    )
