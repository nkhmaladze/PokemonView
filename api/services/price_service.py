"""Pure price-computation service functions over the `price_points` time-series collection.

Pure, DB-taking-as-arg functions consumed by `catalog_service.
get_product_detail` and the `products` blueprint's
history route. No top-level side effects on import: no
MongoClient construction, no os.environ read, no Flask import (mirrors
scripts/matching.py's / db/init_collections.py's established "no
top-level side effects on import" convention).

Three deliberately distinct functions solve three similarly-shaped but
different problems:
  `get_current_price` — NO time-window filter. Always returns the
    single most-recent price_points document for a product, however
    old — never null just because the latest ingestion run had
    a gap. Returns None only when the product has zero points ever. The returned `ts` is the literal ts of that point —
    no separate staleness flag is computed or attached.
  `get_trend_baseline` — HAS a bounded ±tolerance-day window around a
    computed target date and returns None explicitly when
    nothing falls inside that window, so the caller can surface
    an explicit "insufficient_data" state rather than a silently
    omitted badge.
  `get_price_history` — the one function in this module that returns a
    list rather than a single document or None. No
    time-window filter, no downsampling — returns the full ascending-
    by-ts series as clean {ts, total_price} dicts, never a raw
    price_points document.
"""

from datetime import timedelta, timezone

TREND_TOLERANCE_DAYS = 3


def get_current_price(db, product_id):
    """Return the single most recent price_points document for
    product_id, however old — never null just because the
    latest ingestion run had a gap. Returns None only if the product
    has zero price_points documents ever. The returned `ts` is
    the literal ts of the latest inserted point — no separate
    staleness computation is performed here.

    Args:
        db: An already-connected pymongo Database handle.
        product_id: The canonical catalog product slug.

    Returns:
        dict | None: The whole price_points document (ts, product_id,
        item_price, total_price, and listing_count when present), or
        None when no point exists for this product.
    """
    return db.price_points.find_one(
        {"product_id": product_id},
        sort=[("ts", -1)],
    )


def get_price_history(db, product_id):
    """Return the full price_points series for product_id, ordered
    oldest-first by ts. The one function
    in this module that returns a list rather than a single document or
    None — zero documents yields an empty list and one document yields
    a one-element list; neither is an error condition and this function
    never raises for them.

    Builds clean {ts, total_price} dicts rather than returning cursor
    documents directly: price_points documents carry an auto-generated
    BSON ObjectId under `_id` (unlike `products`, whose `_id` is the
    catalog slug), and Flask 3.1.3's DefaultJSONProvider has no handler
    for that type and serializes `datetime` via werkzeug.http.http_date
    (RFC-822) rather than ISO-8601 — both of which would break the
    response if a raw document reached jsonify(). `item_price` and
    `listing_count` are excluded from the output; this is a total_price
    series only.

    Args:
        db: An already-connected pymongo Database handle.
        product_id: The canonical catalog product slug.

    Returns:
        list[dict]: {"ts": ISO-8601 string, "total_price": float}
        objects ordered oldest-first by ts. Empty when the product has
        no price_points documents. `ts` always carries an explicit UTC
        offset (`+00:00`) — the app's MongoClient is not tz_aware, so
        pymongo returns naive datetimes for values that are actually
        UTC instants; this function attaches `timezone.utc` before
        serializing so the frontend's `new Date(ts)` parses the
        correct instant regardless of the viewer's local timezone. The broader fix — constructing the
        MongoClient itself with tz_aware=True — is out of this
        function's scope; track it as a follow-up alongside
        catalog_service.py's `as_of` field, which shares this root
        cause.

    Unbounded-response assumption: this function returns every stored
    point for the product with no limit, window or downsampling. This
    is deliberate at the current data volume — roughly 6 points per day
    per product, with downsampled/binned chart data out of scope — and is
    the same assumption made when a time-range selector is deferred.
    Revisit trigger: accumulated history large enough that response
    size or chart legibility becomes a real problem, at which point
    adding a limit/window/since parameter is a considered decision, not
    an accident. No such parameter should be added speculatively ahead
    of that trigger.
    """
    docs = db.price_points.find(
        {"product_id": product_id},
        sort=[("ts", 1)],
    )
    return [
        {
            "ts": doc["ts"].replace(tzinfo=timezone.utc).isoformat(),
            "total_price": doc["total_price"],
        }
        for doc in docs
    ]


def get_trend_baseline(db, product_id, current_ts, days, tolerance_days=TREND_TOLERANCE_DAYS):
    """Return the price_points document closest to (current_ts - days)
    for product_id, accepted only within +/- tolerance_days of that
    target. Returns None if nothing falls inside the window — the caller surfaces an explicit "insufficient_data"
    status, never omits the trend badge.

    This is deliberately a DIFFERENT function from get_current_price — the bounded window lives only here.

    Args:
        db: An already-connected pymongo Database handle.
        product_id: The canonical catalog product slug.
        current_ts: The reference datetime the trend is measured from.
        days: How many days back the target baseline should be (7 or 30).
        tolerance_days: Acceptable +/- slack around the target date.

    Returns:
        dict | None: The closest price_points document within the
        tolerance window, or None when nothing falls inside it.
    """
    target = current_ts - timedelta(days=days)
    window_start = target - timedelta(days=tolerance_days)
    window_end = target + timedelta(days=tolerance_days)

    pipeline = [
        {
            "$match": {
                "product_id": product_id,
                "ts": {"$gte": window_start, "$lte": window_end},
            }
        },
        {"$addFields": {"diff": {"$abs": {"$subtract": ["$ts", target]}}}},
        {"$sort": {"diff": 1}},
        {"$limit": 1},
    ]
    results = list(db.price_points.aggregate(pipeline))
    return results[0] if results else None


def compute_pct_change(current_total, baseline_total):
    """Compute the percent change between current_total and
    baseline_total, operating on total_price values only.

    Args:
        current_total: The current total_price value.
        baseline_total: The baseline total_price value.

    Returns:
        float | None: The percent change rounded to 2dp, or None when
        baseline_total is 0 (divide-by-zero guard; caller treats this
        as insufficient data rather than a crash).
    """
    if baseline_total == 0:
        return None
    return round((current_total - baseline_total) / baseline_total * 100, 2)
