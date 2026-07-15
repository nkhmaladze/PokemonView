"""Pure price-computation service functions (PRICE-01, PRICE-02,
PRICE-03; 05-CONTEXT.md D-01, D-02, D-03, D-05, D-06, D-07) over the
`price_points` time-series collection.

Pure, DB-taking-as-arg functions consumed by `catalog_service.
get_product_detail` (Plan 05-05). No top-level side effects on
import: no MongoClient construction, no os.environ read, no Flask
import (mirrors scripts/matching.py's / db/init_collections.py's
established "no top-level side effects on import" convention).

Two deliberately distinct functions solve two similarly-shaped but
different problems (05-RESEARCH.md Pitfall 2):
  `get_current_price` — NO time-window filter. Always returns the
    single most-recent price_points document for a product, however
    old (D-02) — never null just because the latest ingestion run had
    a gap. Returns None only when the product has zero points ever
    (D-01). The returned `ts` is the literal ts of that point (D-03) —
    no separate staleness flag is computed or attached.
  `get_trend_baseline` — HAS a bounded ±tolerance-day window around a
    computed target date (D-05) and returns None explicitly when
    nothing falls inside that window (D-06), so the caller can surface
    an explicit "insufficient_data" state rather than a silently
    omitted badge.
"""

from datetime import timedelta

TREND_TOLERANCE_DAYS = 3  # D-05


def get_current_price(db, product_id):
    """Return the single most recent price_points document for
    product_id, however old (D-02) — never null just because the
    latest ingestion run had a gap. Returns None only if the product
    has zero price_points documents ever (D-01). The returned `ts` is
    the literal ts of the latest inserted point (D-03) — no separate
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


def get_trend_baseline(db, product_id, current_ts, days, tolerance_days=TREND_TOLERANCE_DAYS):
    """Return the price_points document closest to (current_ts - days)
    for product_id, accepted only within +/- tolerance_days of that
    target (D-05). Returns None if nothing falls inside the window
    (D-06) — the caller surfaces an explicit "insufficient_data"
    status, never omits the trend badge.

    This is deliberately a DIFFERENT function from get_current_price
    (05-RESEARCH.md Pitfall 2) — the bounded window lives only here.

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
    baseline_total, operating on total_price values only (D-07).

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
