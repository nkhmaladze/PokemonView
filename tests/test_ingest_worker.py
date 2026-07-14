"""Contract tests for the active-listing ingestion worker (INGEST-01,
INGEST-02, INGEST-03).

Five tests, most consuming the `ingest_db` fixture from
tests/conftest.py (which bootstraps a dedicated `pokemonview_test`
database targeting active_listings/ingestion_locks/ingestion_runs
before yielding):

  - test_build_query                             (INGEST-01)
  - test_price_and_shipping_captured             (INGEST-03)
  - test_upsert_idempotent                       (INGEST-02)
  - test_lock_prevents_concurrent_acquire        (INGEST-02)
  - test_run_ingestion_once_skips_when_locked    (INGEST-02)

test_build_query is a pure unit test with no fixture — build_query()
does no I/O.

Every `scripts.ingest_worker` import is deferred into each test's
body (not at module top level) so `pytest --collect-only` succeeds
now, before scripts/ingest_worker.py exists — this suite is authored
RED in Plan 03-03 (Wave 2) and turned GREEN by Plan 03-04's worker
implementation (Wave 3), mirroring Phase 2's scaffold-first pattern
(02-05 authored RED, 02-06 turned green).

Plain pytest `assert` style throughout — no unittest.TestCase,
consistent with tests/test_catalog_schema.py.
"""


def test_build_query():
    """build_query(product) builds 'Pokemon {set} {type-phrase}', never
    joining required_keywords (INGEST-01, 03-RESEARCH.md Pattern 4)."""
    from scripts.ingest_worker import build_query

    assert (
        build_query({"set_name": "Chaos Rising", "product_type": "etb"})
        == "Pokemon Chaos Rising Elite Trainer Box"
    )
    assert (
        build_query({"set_name": "Chaos Rising", "product_type": "booster_box"})
        == "Pokemon Chaos Rising Booster Box"
    )
    assert (
        build_query(
            {"set_name": "Perfect Order", "product_type": "booster_bundle"}
        )
        == "Pokemon Perfect Order Booster Bundle"
    )


def test_price_and_shipping_captured(ingest_db):
    """upsert_listings records item_price, shipping_cost, and total_price;
    shipping defaults to 0.0 when shippingOptions is absent (INGEST-03)."""
    from datetime import datetime, timezone

    from scripts.ingest_worker import upsert_listings

    # Exactly-representable float values (50.00, 4.50, 54.50) avoid
    # binary-float equality flakiness when compared with `==` below.
    item_a = {
        "itemId": "v1|A|0",
        "title": "Chaos Rising ETB",
        "price": {"value": "50.00"},
        "shippingOptions": [{"shippingCost": {"value": "4.50"}}],
    }
    item_b = {
        "itemId": "v1|B|0",
        "title": "Chaos Rising ETB free ship",
        "price": {"value": "50.00"},
        # No shippingOptions key — shipping must default to 0.0.
    }

    upsert_listings(
        ingest_db,
        "chaos-rising_etb",
        [item_a, item_b],
        run_id="r1",
        fetched_at=datetime.now(timezone.utc),
    )

    doc_a = ingest_db.active_listings.find_one({"_id": "v1|A|0"})
    doc_b = ingest_db.active_listings.find_one({"_id": "v1|B|0"})

    assert doc_a is not None, "item A was not written to active_listings"
    assert doc_a["item_price"] == 50.0
    assert doc_a["shipping_cost"] == 4.5
    assert doc_a["total_price"] == 54.5

    assert doc_b is not None, "item B was not written to active_listings"
    assert doc_b["item_price"] == 50.0
    assert doc_b["shipping_cost"] == 0.0
    assert doc_b["total_price"] == 50.0


def test_upsert_idempotent(ingest_db):
    """Re-running upsert_listings with the same items produces no
    duplicate documents (INGEST-02, upsert by itemId)."""
    from datetime import datetime, timezone

    from scripts.ingest_worker import upsert_listings

    items = [
        {
            "itemId": "v1|IDEMP-1|0",
            "title": "Perfect Order Booster Box",
            "price": {"value": "120.00"},
            "shippingOptions": [{"shippingCost": {"value": "0.00"}}],
        },
        {
            "itemId": "v1|IDEMP-2|0",
            "title": "Perfect Order Booster Box (2nd listing)",
            "price": {"value": "125.00"},
            "shippingOptions": [{"shippingCost": {"value": "5.00"}}],
        },
    ]

    upsert_listings(
        ingest_db,
        "perfect-order_booster_box",
        items,
        run_id="r1",
        fetched_at=datetime.now(timezone.utc),
    )
    count_before = ingest_db.active_listings.count_documents({})

    upsert_listings(
        ingest_db,
        "perfect-order_booster_box",
        items,
        run_id="r2",
        fetched_at=datetime.now(timezone.utc),
    )
    count_after = ingest_db.active_listings.count_documents({})

    assert count_after == count_before, (
        f"re-running upsert_listings with the same itemIds changed "
        f"document count from {count_before} to {count_after} — "
        f"upsert-by-itemId must be idempotent"
    )


def test_lock_prevents_concurrent_acquire(ingest_db):
    """acquire_lock/release_lock block a second concurrent acquire and
    allow re-acquisition after release (INGEST-02, SC-2)."""
    from scripts.ingest_worker import acquire_lock, ensure_lock_index, release_lock

    ensure_lock_index(ingest_db)

    assert acquire_lock(ingest_db, "holder-A") is True
    assert acquire_lock(ingest_db, "holder-B") is False

    release_lock(ingest_db, "holder-A")

    assert acquire_lock(ingest_db, "holder-B") is True


def test_run_ingestion_once_skips_when_locked(ingest_db, monkeypatch):
    """When the lock is already held, run_ingestion_once makes zero eBay
    calls and logs a skipped_locked run (INGEST-02, SC-2, SC-4)."""
    from scripts import ingest_worker

    def _fail_if_called(*args, **kwargs):
        raise AssertionError(
            "eBay API call made on the skip-when-locked path — "
            "run_ingestion_once must not call eBay when it fails to "
            "acquire the lock"
        )

    monkeypatch.setattr(ingest_worker, "get_app_token", _fail_if_called)
    monkeypatch.setattr(ingest_worker, "search_sealed_listings", _fail_if_called)

    ingest_worker.ensure_lock_index(ingest_db)
    ingest_worker.acquire_lock(ingest_db, "other-run")

    ingest_worker.run_ingestion_once(ingest_db)

    assert ingest_db.active_listings.count_documents({}) == 0, (
        "no listings should be written when the run is skipped due to "
        "the lock being held"
    )

    skipped_run = ingest_db.ingestion_runs.find_one({"status": "skipped_locked"})
    assert skipped_run is not None, (
        "expected an ingestion_runs document with status='skipped_locked' "
        "to be written when acquire_lock fails"
    )
