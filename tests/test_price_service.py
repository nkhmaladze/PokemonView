"""RED contract tests for Phase 5's price service layer (PRICE-01,
PRICE-02, PRICE-03; 05-CONTEXT.md D-01, D-02, D-03, D-05, D-06, D-07).

This is part of the Nyquist Wave 0 scaffold authored in Plan 05-03 —
`api/services/price_service.py` does not exist yet. Every
`from api.services.price_service import ...` is deferred into each
test's body, not placed at module top level, so `pytest
--collect-only` succeeds now (mirrors tests/test_matching.py's
established deferred-import convention). These tests turn GREEN when
Plan 05-04 implements `price_service.py`.

Uses the `api_db` fixture (a real `pokemonview_test` MongoDB handle
with the 16-product catalog seeded and `price_points` left empty) —
each test inserts the exact controlled `price_points` documents its
own scenario needs directly via `api_db.price_points.insert_many/
insert_one`. No Flask app/test client is needed for these pure
service-layer unit tests.

`ts` comparisons use a sub-second tolerance rather than exact equality
(mirrors tests/test_matching.py's precedent) because MongoDB's BSON
date type round-trips at millisecond precision through a non-tz-aware
MongoClient.
"""

from datetime import datetime, timedelta, timezone


def test_current_price_gap_tolerant(api_db):
    """D-02: current price has NO time-window filter — the single most
    recent price_points document is returned even though it is itself
    far older than any 'recent' window, proving get_current_price
    never applies a staleness cutoff (05-RESEARCH.md Pitfall 2). Two
    points are inserted, both old; the newer of the two (still ~200
    days stale) must be the one returned, never None."""
    from api.services.price_service import get_current_price

    now = datetime.now(timezone.utc)
    older_point_ts = now - timedelta(days=400)
    newest_point_ts = now - timedelta(days=200)

    api_db.price_points.insert_many(
        [
            {
                "ts": older_point_ts,
                "product_id": "perfect-order_booster_box",
                "item_price": 150.00,
                "total_price": 155.00,
            },
            {
                "ts": newest_point_ts,
                "product_id": "perfect-order_booster_box",
                "item_price": 160.00,
                "total_price": 165.00,
            },
        ]
    )

    result = get_current_price(api_db, "perfect-order_booster_box")

    assert result is not None, (
        "a product with real price history must never return None just "
        "because its latest point is old (D-02)"
    )
    assert result["total_price"] == 165.00
    assert (
        abs(
            (
                result["ts"].replace(tzinfo=None)
                - newest_point_ts.replace(tzinfo=None)
            ).total_seconds()
        )
        < 1
    ), "the NEWEST point must be returned, not an arbitrary/older one"


def test_current_price_none_when_no_points(api_db):
    """D-01: a product with zero price_points documents ever returns
    None (the caller, catalog_service, is responsible for translating
    this into an explicit 'no_data_yet' status — not this function)."""
    from api.services.price_service import get_current_price

    result = get_current_price(api_db, "pitch-black_etb")
    assert result is None


def test_freshness_is_real_ts(api_db):
    """D-03: get_current_price's returned `ts` equals the literal `ts`
    of the inserted latest point — no separate staleness flag/boolean
    is computed or attached anywhere on the returned document."""
    from api.services.price_service import get_current_price

    now = datetime.now(timezone.utc)
    api_db.price_points.insert_one(
        {
            "ts": now,
            "product_id": "perfect-order_etb",
            "item_price": 45.00,
            "total_price": 49.99,
        }
    )

    result = get_current_price(api_db, "perfect-order_etb")

    assert result is not None
    assert (
        abs((result["ts"].replace(tzinfo=None) - now.replace(tzinfo=None)).total_seconds())
        < 1
    )
    assert "stale" not in result
    assert "is_stale" not in result


def test_trend_baseline_within_tolerance(api_db):
    """D-05: a point ~7 days before current_ts (1 day off the 7d target,
    inside the +/-3 day tolerance) is returned by get_trend_baseline
    when called with days=7."""
    from api.services.price_service import get_trend_baseline

    current_ts = datetime.now(timezone.utc)
    within_tolerance_ts = current_ts - timedelta(days=8)  # 1 day off 7d target

    api_db.price_points.insert_one(
        {
            "ts": within_tolerance_ts,
            "product_id": "chaos-rising_booster_box",
            "item_price": 140.00,
            "total_price": 150.00,
        }
    )

    result = get_trend_baseline(api_db, "chaos-rising_booster_box", current_ts, days=7)

    assert result is not None, (
        "a point 1 day off the 7d target (within the +/-3 day tolerance "
        "window) must be found (D-05)"
    )
    assert (
        abs(
            (
                result["ts"].replace(tzinfo=None)
                - within_tolerance_ts.replace(tzinfo=None)
            ).total_seconds()
        )
        < 1
    )


def test_trend_insufficient_data(api_db):
    """D-06: when no price_points document falls within the tolerance
    window of the 7d target, get_trend_baseline returns None — the
    caller surfaces an explicit 'insufficient_data' status, not this
    function's job."""
    from api.services.price_service import get_trend_baseline

    current_ts = datetime.now(timezone.utc)
    too_far_ts = current_ts - timedelta(days=20)  # well outside 7d +/-3d window

    api_db.price_points.insert_one(
        {
            "ts": too_far_ts,
            "product_id": "ascended-heroes_booster_box",
            "item_price": 140.00,
            "total_price": 150.00,
        }
    )

    result = get_trend_baseline(
        api_db, "ascended-heroes_booster_box", current_ts, days=7
    )

    assert result is None


def test_trend_uses_total_price_only(api_db):
    """D-07: compute_pct_change operates on total_price values only
    (rounded to 2dp) and guards against a zero baseline by returning
    None rather than raising ZeroDivisionError."""
    from api.services.price_service import compute_pct_change

    result = compute_pct_change(current_total=165.00, baseline_total=150.00)
    assert result == 10.0, "(165-150)/150*100 == 10.0, rounded to 2dp"

    assert compute_pct_change(current_total=100.00, baseline_total=0) is None, (
        "a zero baseline must return None (divide-by-zero guard), not raise"
    )
