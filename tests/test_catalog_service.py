"""RED contract tests for Phase 5's catalog service layer (SEARCH-01,
SEARCH-02; 05-CONTEXT.md D-01, D-04, D-08, D-09, D-10, D-11, D-12; V5
input validation).

This is part of the Nyquist Wave 0 scaffold authored in Plan 05-03 —
`api/services/catalog_service.py` does not exist yet. Every
`from api.services.catalog_service import ...` is deferred into each
test's body so `pytest --collect-only` succeeds now. These tests turn
GREEN when Plan 05-05 implements `catalog_service.py`.

Uses the `api_db` fixture (a real `pokemonview_test` MongoDB handle
with the 16-product catalog seeded from scripts/catalog_data.py and
`price_points` left empty) — tests that need priced products insert
controlled `price_points` documents directly. Response dicts are
asserted against the exact JSON Response Contract shape locked in
this plan's "## API Response Contract" section (field name `id`, not
`_id`) since list_products/get_product_detail are the direct source
the Flask routes `jsonify()` with no further transformation.
"""

from datetime import datetime, timedelta, timezone

import pytest


def test_list_products_filters(api_db):
    """D-08: search/browse supports both structured filters (set_name,
    product_type) and free-text search (q against display_name/
    set_name), combinable."""
    from api.services.catalog_service import list_products

    no_filter = {"q": None, "set_name": None, "product_type": None}

    by_set = list_products(api_db, {**no_filter, "set_name": "Perfect Order"})
    assert len(by_set) == 4
    assert all(p["set_name"] == "Perfect Order" for p in by_set)

    by_type = list_products(api_db, {**no_filter, "product_type": "etb"})
    assert len(by_type) == 4
    assert all(p["product_type"] == "etb" for p in by_type)

    by_query = list_products(api_db, {**no_filter, "q": "chaos"})
    assert len(by_query) == 4, "free-text 'chaos' must match all 4 Chaos Rising products"
    assert all(p["set_name"] == "Chaos Rising" for p in by_query)

    combined = list_products(
        api_db,
        {**no_filter, "set_name": "Chaos Rising", "product_type": "booster_pack"},
    )
    assert len(combined) == 1
    assert combined[0]["id"] == "chaos-rising_booster_pack"


def test_default_sort_order(api_db):
    """D-10: with no filters, results are grouped by set in the
    hardcoded SET_ORDER (Pitch Black -> Chaos Rising -> Perfect Order
    -> Ascended Heroes), NOT a raw release_date sort (05-RESEARCH.md
    Pitfall 1 — per-product release_date is staggered within a set)."""
    from api.services.catalog_service import list_products

    results = list_products(api_db, {"q": None, "set_name": None, "product_type": None})
    assert len(results) == 16

    expected_group_order = ["Pitch Black", "Chaos Rising", "Perfect Order", "Ascended Heroes"]
    last_group_index = -1
    for product in results:
        group_index = expected_group_order.index(product["set_name"])
        assert group_index >= last_group_index, (
            f"sets must be grouped together in SET_ORDER sequence "
            f"{expected_group_order}, not interleaved — saw "
            f"{product['set_name']} after a later-ordered set"
        )
        last_group_index = group_index


def test_unverified_products_shown_identically(api_db):
    """D-09: verified:false catalog entries (Pitch Black, pre-release)
    appear in the unfiltered list with the exact same shape/fields as
    verified products — no exclusion, no extra provisional/badge
    field."""
    from api.services.catalog_service import list_products

    results = list_products(api_db, {"q": None, "set_name": None, "product_type": None})

    pitch_black = [p for p in results if p["set_name"] == "Pitch Black"]
    others = [p for p in results if p["set_name"] != "Pitch Black"]

    assert len(pitch_black) == 4, "all 4 Pitch Black products must be present, not excluded"
    assert set(pitch_black[0].keys()) == set(others[0].keys()), (
        "Pitch Black entries must carry the exact same field set as "
        "verified products — no extra provisional/badge field (D-09)"
    )


def test_list_includes_price_and_freshness(api_db):
    """D-04/D-12: a listed product with points carries
    current_price.total_price (headline), current_price.item_price
    (secondary), and current_price.as_of; a product with no points
    carries price_status == 'no_data_yet' and current_price is None."""
    from api.services.catalog_service import list_products

    now = datetime.now(timezone.utc)
    api_db.price_points.insert_one(
        {
            "ts": now,
            "product_id": "perfect-order_booster_box",
            "item_price": 165.00,
            "total_price": 172.50,
        }
    )

    results = list_products(api_db, {"q": None, "set_name": None, "product_type": None})

    priced = next(p for p in results if p["id"] == "perfect-order_booster_box")
    assert priced["current_price"]["total_price"] == 172.50
    assert priced["current_price"]["item_price"] == 165.00
    assert priced["current_price"]["as_of"] is not None
    assert priced["price_status"] == "ok"

    unpriced = next(p for p in results if p["id"] == "pitch-black_etb")
    assert unpriced["price_status"] == "no_data_yet"
    assert unpriced["current_price"] is None


def test_product_type_enum_validation(api_db):
    """V5: list_products raises ValueError on an invalid non-None
    product_type; each valid enum value does not raise."""
    from api.services.catalog_service import list_products

    with pytest.raises(ValueError):
        list_products(
            api_db, {"q": None, "set_name": None, "product_type": "not_a_type"}
        )

    for valid_type in ["booster_pack", "booster_box", "etb", "booster_bundle"]:
        list_products(
            api_db, {"q": None, "set_name": None, "product_type": valid_type}
        )  # must not raise


def test_detail_current_price_total_led(api_db):
    """SC2/PRICE-01/D-12: get_product_detail returns current_price with
    total_price (headline) and item_price (secondary) for a priced
    product."""
    from api.services.catalog_service import get_product_detail

    now = datetime.now(timezone.utc)
    api_db.price_points.insert_one(
        {
            "ts": now,
            "product_id": "perfect-order_booster_box",
            "item_price": 165.00,
            "total_price": 172.50,
        }
    )

    detail = get_product_detail(api_db, "perfect-order_booster_box")

    assert detail is not None
    assert detail["current_price"]["total_price"] == 172.50
    assert detail["current_price"]["item_price"] == 165.00


def test_detail_no_data_yet(api_db):
    """D-01: get_product_detail for a seeded product with zero points
    returns price_status == 'no_data_yet' and current_price None — the
    product row itself exists (NOT None-the-whole-response, NOT a
    404)."""
    from api.services.catalog_service import get_product_detail

    detail = get_product_detail(api_db, "pitch-black_etb")

    assert detail is not None, (
        "a seeded product with zero price history must still return a "
        "detail dict, not None (that's reserved for an unknown id)"
    )
    assert detail["price_status"] == "no_data_yet"
    assert detail["current_price"] is None


def test_detail_unknown_id_returns_none(api_db):
    """get_product_detail(api_db, 'does-not-exist') returns None (the
    Flask route translates this into HTTP 404)."""
    from api.services.catalog_service import get_product_detail

    assert get_product_detail(api_db, "does-not-exist") is None


def test_detail_trend_24h_present_when_no_data(api_db):
    """PRICE-08: get_product_detail for a seeded product with zero
    points still carries trend_24h in its early-return branch, shaped
    insufficient-data. Pins the early-return branch specifically — the
    normal-path computation never runs for this product, so a key added
    only below that branch would be silently absent here, which is the
    failure ROADMAP success criterion 4 forbids."""
    from api.services.catalog_service import get_product_detail

    detail = get_product_detail(api_db, "pitch-black_etb")

    assert "trend_24h" in detail
    assert detail["trend_24h"]["status"] == "insufficient_data"
    assert detail["trend_24h"]["pct_change"] is None


def test_detail_trend_24h_computed_from_the_24h_baseline(api_db):
    """PRICE-08: get_product_detail computes trend_24h from a point ~24h
    before the current point, and trend_7d/trend_30d remain present and
    unchanged in shape — the new sibling block does not disturb the
    existing TREND_WINDOWS loop."""
    from api.services.catalog_service import get_product_detail

    now = datetime.now(timezone.utc)
    api_db.price_points.insert_many(
        [
            {
                "ts": now,
                "product_id": "perfect-order_booster_box",
                "item_price": 165.00,
                "total_price": 172.50,
            },
            {
                "ts": now - timedelta(hours=24),
                "product_id": "perfect-order_booster_box",
                "item_price": 150.00,
                "total_price": 155.00,
            },
        ]
    )

    detail = get_product_detail(api_db, "perfect-order_booster_box")

    assert detail["trend_24h"]["status"] == "ok"
    assert detail["trend_24h"]["pct_change"] == round((172.50 - 155.00) / 155.00 * 100, 2)
    assert isinstance(detail["trend_7d"], dict)
    assert isinstance(detail["trend_30d"], dict)


def test_detail_trend_24h_never_uses_the_default_three_day_tolerance(api_db):
    """PRICE-08 must-have: the 24h window never rides get_trend_baseline's
    default three-day tolerance through catalog_service's actual call
    site. A lone baseline point 2 days old sits well outside the 24h
    +/-4h window but squarely inside a 3-day-tolerance window around a
    1-day target — if the tolerance_days argument were ever dropped at
    the call site, this point would be wrongly accepted as the 24h
    baseline. Pins the call site itself, not just get_trend_baseline in
    isolation (see tests/test_price_service.py's own boundary cases)."""
    from api.services.catalog_service import get_product_detail

    now = datetime.now(timezone.utc)
    api_db.price_points.insert_many(
        [
            {
                "ts": now,
                "product_id": "perfect-order_booster_box",
                "item_price": 165.00,
                "total_price": 172.50,
            },
            {
                "ts": now - timedelta(days=2),
                "product_id": "perfect-order_booster_box",
                "item_price": 150.00,
                "total_price": 155.00,
            },
        ]
    )

    detail = get_product_detail(api_db, "perfect-order_booster_box")

    assert detail["trend_24h"]["status"] == "insufficient_data", (
        "a 2-day-old baseline point is outside the 24h+/-4h window and "
        "must not be accepted just because it falls inside the wider "
        "3-day default tolerance"
    )
    assert detail["trend_24h"]["pct_change"] is None


def test_detail_trend_24h_zero_baseline_is_insufficient(api_db):
    """PRICE-08: a 24h baseline point with total_price of 0 makes
    trend_24h insufficient-data rather than raising — exercises
    compute_pct_change's divide-by-zero guard on the new path."""
    from api.services.catalog_service import get_product_detail

    now = datetime.now(timezone.utc)
    api_db.price_points.insert_many(
        [
            {
                "ts": now,
                "product_id": "perfect-order_booster_box",
                "item_price": 165.00,
                "total_price": 172.50,
            },
            {
                "ts": now - timedelta(hours=24),
                "product_id": "perfect-order_booster_box",
                "item_price": 0.00,
                "total_price": 0.00,
            },
        ]
    )

    detail = get_product_detail(api_db, "perfect-order_booster_box")

    assert detail["trend_24h"]["status"] == "insufficient_data"
    assert detail["trend_24h"]["pct_change"] is None


def test_detail_omits_raw_series(api_db):
    """D-11: the detail dict contains no key whose value is a raw list/
    array of price_points-shaped documents — trend_7d/trend_30d must be
    single objects, never a series."""
    from api.services.catalog_service import get_product_detail

    now = datetime.now(timezone.utc)
    api_db.price_points.insert_many(
        [
            {
                "ts": now,
                "product_id": "perfect-order_booster_box",
                "item_price": 165.00,
                "total_price": 172.50,
            },
            {
                "ts": now - timedelta(days=7),
                "product_id": "perfect-order_booster_box",
                "item_price": 160.00,
                "total_price": 167.00,
            },
        ]
    )

    detail = get_product_detail(api_db, "perfect-order_booster_box")

    for key, value in detail.items():
        is_point_series = (
            isinstance(value, list)
            and len(value) > 0
            and isinstance(value[0], dict)
            and "ts" in value[0]
        )
        assert not is_point_series, (
            f"detail response must not contain a raw price_points "
            f"series/array (D-11); found one at key '{key}'"
        )

    assert isinstance(detail["trend_7d"], dict)
    assert isinstance(detail["trend_30d"], dict)
