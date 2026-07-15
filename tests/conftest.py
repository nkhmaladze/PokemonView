"""Shared pytest fixtures for PokemonView's integration test suite.

Provides `catalog_db`, a dedicated throwaway MongoDB test database
fixture consumed by tests/test_catalog_schema.py, and `ingest_db`, a
sibling fixture consumed by tests/test_ingest_worker.py. Uses a REAL
MongoDB connection (not mongomock) because these phases' contract
tests need to prove `$jsonSchema` validator enforcement, time-series
collection creation, and TTL-index/lock semantics, none of which
mongomock can emulate (02-RESEARCH.md, Validation Architecture).

Only `pytest`, `os`, and `pymongo.MongoClient` are imported at module
top level. The project's own `db.*` / `scripts.*` modules are
deliberately NOT imported here at top level — they are lazily imported
inside each fixture body instead, so that `pytest --collect-only`
succeeds even before those modules exist (Nyquist Wave 0
scaffold-first requirement; catalog_db is authored in Plan 02-05 and
turned green by Plan 02-06's seed run; ingest_db is authored in Plan
03-03 and turned green by Plan 03-04's worker implementation).

Credential hygiene (mirrors Phase 1's secrets-hygiene pattern,
scripts/verify_ebay_access.py): MONGODB_URI is loaded via
python-dotenv + os.environ at fixture-call time, never hardcoded, and
never printed/logged in full.
"""

import os

import pytest
from pymongo import MongoClient

TEST_DB_NAME = "pokemonview_test"


@pytest.fixture
def catalog_db():
    """Yield a live pymongo Database handle for a dedicated test DB.

    Skips (rather than errors) when MONGODB_URI is not configured, so
    the scaffold degrades gracefully when no MongoDB instance has been
    provisioned yet (see Plan 02-02, MongoDB provisioning).

    The fixture always targets `pokemonview_test` — a database name
    ending in `_test`, distinct from the real `pokemonview` catalog
    database — and drops its `products`/`price_points` collections
    both before and after the test runs, so tests never read stale
    state and never leave residue behind (T-02-05).
    """
    from dotenv import load_dotenv

    load_dotenv()
    mongodb_uri = os.environ.get("MONGODB_URI")
    if not mongodb_uri:
        pytest.skip(
            "MONGODB_URI not set — provision a MongoDB instance per "
            "Plan 02-02 (MongoDB Atlas M0 or local) and add MONGODB_URI "
            "to .env before running the catalog contract tests."
        )

    client = MongoClient(mongodb_uri)
    try:
        test_db = client[TEST_DB_NAME]

        # Start clean: never assume a prior run left the test DB empty.
        test_db.drop_collection("products")
        test_db.drop_collection("price_points")

        # Lazy imports: keep collection off the module top level so
        # `pytest --collect-only` succeeds before db/init_collections.py
        # and scripts/seed_catalog.py exist.
        from db.init_collections import init_collections
        from scripts.seed_catalog import seed_catalog
        from scripts.catalog_data import CATALOG

        init_collections(test_db)
        seed_catalog(test_db, CATALOG)
    except Exception:
        client.close()
        raise

    yield test_db

    # Teardown: drop the test collections and close the connection so
    # no test leaves the throwaway database dirty for the next run.
    test_db.drop_collection("products")
    test_db.drop_collection("price_points")
    client.close()


@pytest.fixture
def ingest_db():
    """Yield a live pymongo Database handle for a dedicated test DB.

    Mirrors `catalog_db`'s structure exactly, swapping the collection
    set: this fixture targets the three collections Phase 3's
    ingestion worker writes into (`active_listings`, `ingestion_locks`,
    `ingestion_runs`) instead of the catalog's `products`/
    `price_points`.

    Skips (rather than errors) when MONGODB_URI is not configured, so
    the scaffold degrades gracefully when no MongoDB instance has been
    provisioned yet (see Plan 02-02, MongoDB provisioning).

    The fixture always targets `pokemonview_test` — a database name
    ending in `_test`, distinct from the real `pokemonview` catalog
    database — and drops its three ingestion collections both before
    and after the test runs, so tests never read stale state and never
    leave residue behind (T-03-05).

    Does NOT seed the catalog (`products`/`price_points`) — this
    fixture's tests need no products data, only the bootstrapped
    ingestion collections.
    """
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

        # Start clean: never assume a prior run left the test DB empty.
        test_db.drop_collection("active_listings")
        test_db.drop_collection("ingestion_locks")
        test_db.drop_collection("ingestion_runs")

        # Lazy import: keep collection off the module top level so
        # `pytest --collect-only` succeeds before scripts/ingest_worker.py
        # exists (db.init_collections already exists as of Plan 03-02,
        # but this mirrors catalog_db's lazy-import discipline for
        # consistency and future-proofing).
        from db.init_collections import init_collections

        init_collections(test_db)
    except Exception:
        client.close()
        raise

    yield test_db

    # Teardown: drop the test collections and close the connection so
    # no test leaves the throwaway database dirty for the next run.
    test_db.drop_collection("active_listings")
    test_db.drop_collection("ingestion_locks")
    test_db.drop_collection("ingestion_runs")
    client.close()


@pytest.fixture
def matching_db():
    """Yield a live pymongo Database handle for a dedicated test DB.

    Mirrors `ingest_db`'s structure exactly, extending the collection
    set with `price_points` — Phase 4's matching/exclusion/outlier
    pipeline (scripts/matching.py, authored RED in this plan) reads
    and writes `active_listings`, aggregates into `price_points`, and
    `test_run_ingestion_once_records_match_counts` drives the full
    `run_ingestion_once` path, which acquires the `ingestion_locks`
    lock — so all four collections need a clean, reset state per test.

    Skips (rather than errors) when MONGODB_URI is not configured, so
    the scaffold degrades gracefully when no MongoDB instance has been
    provisioned yet (see Plan 02-02, MongoDB provisioning).

    The fixture always targets `pokemonview_test` — a database name
    ending in `_test`, distinct from the real `pokemonview` catalog
    database — and drops its four collections both before and after
    the test runs, so tests never read stale state and never leave
    residue behind (T-04-T1).

    Does NOT seed `products` or catalog data — matching reads
    `scripts.catalog_data.CATALOG` directly, not the products
    collection.
    """
    from dotenv import load_dotenv

    load_dotenv()
    mongodb_uri = os.environ.get("MONGODB_URI")
    if not mongodb_uri:
        pytest.skip(
            "MONGODB_URI not set — provision a MongoDB instance per "
            "Plan 02-02 (MongoDB Atlas M0 or local) and add MONGODB_URI "
            "to .env before running the matching contract tests."
        )

    client = MongoClient(mongodb_uri)
    try:
        test_db = client[TEST_DB_NAME]

        # Start clean: never assume a prior run left the test DB empty.
        test_db.drop_collection("active_listings")
        test_db.drop_collection("price_points")
        test_db.drop_collection("ingestion_runs")
        test_db.drop_collection("ingestion_locks")

        # Lazy import: keep collection off the module top level so
        # `pytest --collect-only` succeeds before scripts/matching.py
        # exists (db.init_collections already exists as of Plan 03-02,
        # but this mirrors ingest_db's lazy-import discipline for
        # consistency). Re-creates price_points as a fresh time-series
        # collection each test (timeseries options are creation-time
        # only, so drop+init_collections is the correct reset).
        from db.init_collections import init_collections

        init_collections(test_db)
    except Exception:
        client.close()
        raise

    yield test_db

    # Teardown: drop the test collections and close the connection so
    # no test leaves the throwaway database dirty for the next run.
    test_db.drop_collection("active_listings")
    test_db.drop_collection("price_points")
    test_db.drop_collection("ingestion_runs")
    test_db.drop_collection("ingestion_locks")
    client.close()
