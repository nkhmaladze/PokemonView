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

This file also covers Phase 8's `get_price_history` (PRICE-07,
08-CONTEXT.md D-04). Unlike the Phase 5 cases above, these tests were
authored against an already-implemented function (Plan 08-01) to pin
its edges — empty/single-point results, ordering, element shape,
ISO-8601 timestamps, cross-product isolation, and stored-precision
fidelity — rather than as a RED scaffold.
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


def test_trend_baseline_24h_accepts_both_window_edges(api_db):
    """PRICE-08: with days=1 and tolerance_days=TREND_24H_TOLERANCE_HOURS/24
    (4 hours), a point exactly 20 hours before current_ts (the near
    inclusive edge) and a point exactly 28 hours before current_ts (the
    far inclusive edge) are both returned — the pipeline's window filter
    uses $gte/$lte, which is inclusive on both bounds."""
    from api.services.price_service import TREND_24H_TOLERANCE_HOURS, get_trend_baseline

    current_ts = datetime.now(timezone.utc)
    tolerance_days = TREND_24H_TOLERANCE_HOURS / 24
    near_edge_ts = current_ts - timedelta(hours=20)
    far_edge_ts = current_ts - timedelta(hours=28)

    api_db.price_points.insert_one(
        {
            "ts": near_edge_ts,
            "product_id": "chaos-rising_booster_box",
            "item_price": 140.00,
            "total_price": 150.00,
        }
    )
    api_db.price_points.insert_one(
        {
            "ts": far_edge_ts,
            "product_id": "ascended-heroes_booster_box",
            "item_price": 140.00,
            "total_price": 150.00,
        }
    )

    near_result = get_trend_baseline(
        api_db, "chaos-rising_booster_box", current_ts, days=1, tolerance_days=tolerance_days
    )
    far_result = get_trend_baseline(
        api_db, "ascended-heroes_booster_box", current_ts, days=1, tolerance_days=tolerance_days
    )

    assert near_result is not None, "a point exactly 20h before current_ts (near edge) must be found"
    assert far_result is not None, "a point exactly 28h before current_ts (far edge) must be found"


def test_trend_baseline_24h_rejects_one_step_outside_each_edge(api_db):
    """A point one minute past each inclusive edge (19h59m and 28h01m
    before current_ts) falls outside the window and returns None."""
    from api.services.price_service import TREND_24H_TOLERANCE_HOURS, get_trend_baseline

    current_ts = datetime.now(timezone.utc)
    tolerance_days = TREND_24H_TOLERANCE_HOURS / 24
    just_inside_near_ts = current_ts - timedelta(hours=19, minutes=59)
    just_outside_far_ts = current_ts - timedelta(hours=28, minutes=1)

    api_db.price_points.insert_one(
        {
            "ts": just_inside_near_ts,
            "product_id": "chaos-rising_booster_box",
            "item_price": 140.00,
            "total_price": 150.00,
        }
    )
    api_db.price_points.insert_one(
        {
            "ts": just_outside_far_ts,
            "product_id": "ascended-heroes_booster_box",
            "item_price": 140.00,
            "total_price": 150.00,
        }
    )

    near_result = get_trend_baseline(
        api_db, "chaos-rising_booster_box", current_ts, days=1, tolerance_days=tolerance_days
    )
    far_result = get_trend_baseline(
        api_db, "ascended-heroes_booster_box", current_ts, days=1, tolerance_days=tolerance_days
    )

    assert near_result is None, "19h59m before current_ts is one step inside the near edge, therefore outside the window"
    assert far_result is None, "28h01m before current_ts is one step past the far edge"


def test_trend_baseline_24h_rejects_the_default_tolerance_case(api_db):
    """A lone point four days before current_ts must return None when
    called with the explicit 24h tolerance — this is the regression that
    fails if the module's three-day default is ever restored for this
    window, because a +/-3-day window around a one-day target reaches
    back to four days."""
    from api.services.price_service import TREND_24H_TOLERANCE_HOURS, get_trend_baseline

    current_ts = datetime.now(timezone.utc)
    tolerance_days = TREND_24H_TOLERANCE_HOURS / 24
    four_days_ago_ts = current_ts - timedelta(days=4)

    api_db.price_points.insert_one(
        {
            "ts": four_days_ago_ts,
            "product_id": "chaos-rising_booster_box",
            "item_price": 140.00,
            "total_price": 150.00,
        }
    )

    result = get_trend_baseline(
        api_db, "chaos-rising_booster_box", current_ts, days=1, tolerance_days=tolerance_days
    )

    assert result is None, (
        "a point 4 days before current_ts must NOT be treated as a valid "
        "24h baseline — this is the case that would wrongly succeed if "
        "the 3-day default tolerance were used instead of the explicit 4h one"
    )


def test_trend_baseline_24h_picks_the_nearer_point(api_db):
    """When two points both fall inside the 24h window, the one nearer
    the 24-hour target is the one returned."""
    from api.services.price_service import TREND_24H_TOLERANCE_HOURS, get_trend_baseline

    current_ts = datetime.now(timezone.utc)
    tolerance_days = TREND_24H_TOLERANCE_HOURS / 24
    nearer_ts = current_ts - timedelta(hours=23)
    farther_ts = current_ts - timedelta(hours=27)

    api_db.price_points.insert_many(
        [
            {
                "ts": nearer_ts,
                "product_id": "chaos-rising_booster_box",
                "item_price": 140.00,
                "total_price": 151.00,
            },
            {
                "ts": farther_ts,
                "product_id": "chaos-rising_booster_box",
                "item_price": 140.00,
                "total_price": 149.00,
            },
        ]
    )

    result = get_trend_baseline(
        api_db, "chaos-rising_booster_box", current_ts, days=1, tolerance_days=tolerance_days
    )

    assert result is not None
    assert result["total_price"] == 151.00
    assert (
        abs((result["ts"].replace(tzinfo=None) - nearer_ts.replace(tzinfo=None)).total_seconds())
        < 1
    ), "the point nearer the 24h target (minus-23-hour) must be the one returned"


def test_price_history_empty_when_no_points(api_db):
    """PRICE-07/08-CONTEXT.md D-04: a brand-new product with zero
    collected price_points is a normal state, not an error — the
    caller renders an explicit "not enough history yet" message rather
    than an HTTP failure (08-RESEARCH.md Pitfall 2)."""
    from api.services.price_service import get_price_history

    result = get_price_history(api_db, "pitch-black_etb")

    assert isinstance(result, list)
    assert result == []


def test_price_history_single_point(api_db):
    """A product with exactly one price_points document returns a
    one-element list — not an error, not None (08-RESEARCH.md
    Pitfall 2)."""
    from api.services.price_service import get_price_history

    now = datetime.now(timezone.utc)
    api_db.price_points.insert_one(
        {
            "ts": now,
            "product_id": "pitch-black_booster_pack",
            "item_price": 4.00,
            "total_price": 4.50,
        }
    )

    result = get_price_history(api_db, "pitch-black_booster_pack")

    assert len(result) == 1
    assert result[0]["total_price"] == 4.50


def test_price_history_ascending_order(api_db):
    """The returned series is ordered oldest-first by ts even when the
    documents were inserted out of chronological order — the ordering
    must come from the query's ascending sort on ts, never from
    insertion order or client-side sorting."""
    from api.services.price_service import get_price_history

    now = datetime.now(timezone.utc)
    oldest = now - timedelta(days=3)
    second_oldest = now - timedelta(days=2)
    second_newest = now - timedelta(days=1)
    newest = now

    # Deliberately scrambled insert order: [newest, oldest, second-newest, second-oldest]
    api_db.price_points.insert_many(
        [
            {"ts": newest, "product_id": "chaos-rising_etb", "item_price": 39.00, "total_price": 42.99},
            {"ts": oldest, "product_id": "chaos-rising_etb", "item_price": 30.00, "total_price": 33.00},
            {"ts": second_newest, "product_id": "chaos-rising_etb", "item_price": 36.00, "total_price": 39.99},
            {"ts": second_oldest, "product_id": "chaos-rising_etb", "item_price": 33.00, "total_price": 36.00},
        ]
    )

    result = get_price_history(api_db, "chaos-rising_etb")

    assert [point["total_price"] for point in result] == [33.00, 36.00, 39.99, 42.99], (
        "returned order must reflect the ascending ts sort, not insertion order"
    )


def test_price_history_element_shape(api_db):
    """Every returned element's key set is exactly {ts, total_price} —
    no leaked BSON ObjectId under `_id` (not JSON serializable) and no
    RFC-822-formatted `ts`, which would break consistency with the
    ISO-8601 `as_of` value every other endpoint already returns
    (08-RESEARCH.md Pitfalls 1 and 3)."""
    from api.services.price_service import get_price_history

    now = datetime.now(timezone.utc)
    api_db.price_points.insert_many(
        [
            {"ts": now - timedelta(days=1), "product_id": "chaos-rising_etb", "item_price": 33.00, "total_price": 36.00},
            {"ts": now, "product_id": "chaos-rising_etb", "item_price": 39.00, "total_price": 42.99},
        ]
    )

    result = get_price_history(api_db, "chaos-rising_etb")

    for element in result:
        assert set(element.keys()) == {"ts", "total_price"}, (
            "leaked _id or item_price/listing_count would fail this — "
            "the history response must carry exactly {ts, total_price}"
        )
        assert isinstance(element["ts"], str)
        datetime.fromisoformat(element["ts"])
        # CR-01, 08-REVIEW.md: the app's MongoClient is not tz_aware, so
        # pymongo returns naive datetimes for values that are actually UTC
        # instants. Without an explicit UTC offset here, the frontend's
        # `new Date(ts)` parses the string as local time and can render the
        # wrong calendar day for non-UTC viewers. This assertion pins the
        # fix (get_price_history attaches timezone.utc before
        # .isoformat()) and would have failed before it.
        assert element["ts"].endswith(("+00:00", "Z")), (
            f"ts {element['ts']!r} has no UTC offset — CR-01 regression"
        )


def test_price_history_scoped_to_one_product(api_db):
    """Points belonging to a different product_id inserted into the
    same collection do not appear in the result — the query filter is
    an exact match, not a prefix/substring match."""
    from api.services.price_service import get_price_history

    now = datetime.now(timezone.utc)
    api_db.price_points.insert_many(
        [
            {"ts": now - timedelta(days=1), "product_id": "ascended-heroes_etb", "item_price": 40.00, "total_price": 43.99},
            {"ts": now, "product_id": "ascended-heroes_etb", "item_price": 41.00, "total_price": 44.99},
            {"ts": now - timedelta(days=1), "product_id": "ascended-heroes_booster_pack", "item_price": 4.50, "total_price": 4.99},
            {"ts": now, "product_id": "ascended-heroes_booster_pack", "item_price": 4.75, "total_price": 5.25},
        ]
    )

    result = get_price_history(api_db, "ascended-heroes_etb")

    assert len(result) == 2
    returned_totals = {point["total_price"] for point in result}
    assert returned_totals == {43.99, 44.99}
    assert not returned_totals & {4.99, 5.25}, (
        "a second product's price_points documents must never leak into "
        "this product's history"
    )


def test_price_history_preserves_stored_precision(api_db):
    """A stored total_price of 172.55 comes back exactly 172.55,
    unrounded — no rounding, truncation or float re-encoding between
    MongoDB and the JSON payload. item_price is absent from the
    element entirely."""
    from api.services.price_service import get_price_history

    now = datetime.now(timezone.utc)
    api_db.price_points.insert_one(
        {
            "ts": now,
            "product_id": "pitch-black_etb",
            "item_price": 165.49,
            "total_price": 172.55,
        }
    )

    result = get_price_history(api_db, "pitch-black_etb")

    assert len(result) == 1
    assert result[0]["total_price"] == 172.55
    assert "item_price" not in result[0]
