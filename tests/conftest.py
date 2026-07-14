"""Shared pytest fixtures for PokemonView's integration test suite.

Provides `catalog_db`, a dedicated throwaway MongoDB test database
fixture consumed by tests/test_catalog_schema.py. Uses a REAL MongoDB
connection (not mongomock) because this phase's contract tests need to
prove `$jsonSchema` validator enforcement and time-series collection
creation, neither of which mongomock can emulate (02-RESEARCH.md,
Validation Architecture).

Only `pytest`, `os`, and `pymongo.MongoClient` are imported at module
top level. The project's own `db.*` / `scripts.*` modules are
deliberately NOT imported here at top level — they are lazily imported
inside the `catalog_db` fixture body instead, so that
`pytest --collect-only` succeeds even before those modules exist
(Nyquist Wave 0 scaffold-first requirement; this suite is authored in
Plan 02-05 and turned green by Plan 02-06's seed run).

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

    yield test_db

    # Teardown: drop the test collections and close the connection so
    # no test leaves the throwaway database dirty for the next run.
    test_db.drop_collection("products")
    test_db.drop_collection("price_points")
    client.close()
