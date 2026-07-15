"""Pure price-computation service functions (PRICE-01, PRICE-02,
PRICE-03; 05-CONTEXT.md D-01, D-02, D-03, D-07) over the
`price_points` time-series collection.

Pure, DB-taking-as-arg functions consumed by `catalog_service.
get_product_detail` (Plan 05-05). No top-level side effects on
import: no MongoClient construction, no os.environ read, no Flask
import (mirrors scripts/matching.py's / db/init_collections.py's
established "no top-level side effects on import" convention).
"""


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
