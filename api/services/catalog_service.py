"""Catalog-facing serving logic for browse/search/filter and single-
product detail assembly (SEARCH-01, SEARCH-02, PRICE-01; 05-CONTEXT.md
D-01, D-04, D-05, D-06, D-07, D-08, D-09, D-10, D-11, D-12; V5 input
validation).

Pure, DB-taking-as-arg service functions consumed directly by the
products blueprint (Plan 05-06), which `jsonify()`s the returned dicts
with no further transformation. No top-level side effects on import:
no MongoClient construction, no os.environ read, no Flask import
(mirrors scripts/matching.py's / api/services/price_service.py's
established "no top-level side effects on import" convention).

`list_products` filters the whole (<=16-product) catalog IN PROCESS —
never a MongoDB query operator built from raw user text (T-05-01
mitigation). `get_product_detail` composes
`price_service.get_current_price` / `get_trend_baseline` /
`compute_pct_change` into the locked list/detail response shape and
never returns a raw price_points series (D-11).
"""

from api.services.price_service import get_current_price

SET_ORDER = ["Pitch Black", "Chaos Rising", "Perfect Order", "Ascended Heroes"]  # D-10
VALID_PRODUCT_TYPES = {"booster_pack", "booster_box", "etb", "booster_bundle"}  # V5 enum
TREND_WINDOWS = (7, 30)  # D-05


def _product_summary(db, product):
    """Build the jsonify-ready base dict for one product: catalog
    metadata plus its current_price/price_status (D-01/D-04/D-12).

    verified:false products (Pitch Black) get no special handling here
    — they pass through with the exact same field shape as verified
    products (D-09).

    Args:
        db: An already-connected pymongo Database handle.
        product: A raw `products` collection document.

    Returns:
        dict: jsonify-ready fields — id, set_name, product_type,
        display_name, release_date, msrp, image_url, verified,
        price_status, current_price.
    """
    release_date = product.get("release_date")
    summary = {
        "id": product["_id"],
        "set_name": product.get("set_name"),
        "product_type": product.get("product_type"),
        "display_name": product.get("display_name"),
        "release_date": release_date.date().isoformat() if release_date else None,
        "msrp": product.get("msrp"),
        "image_url": product.get("image_url"),
        "verified": product.get("verified"),
    }

    current_point = get_current_price(db, product["_id"])
    if current_point is not None:
        summary["price_status"] = "ok"
        summary["current_price"] = {
            "total_price": current_point["total_price"],
            "item_price": current_point["item_price"],
            "as_of": current_point["ts"].isoformat(),
            "listing_count": current_point.get("listing_count"),
        }
    else:
        summary["price_status"] = "no_data_yet"
        summary["current_price"] = None

    return summary


def list_products(db, filters):
    """Browse/search/filter the catalog (SEARCH-01).

    Fetches the whole small catalog once (`db.products.find({})`,
    <=16 docs) and applies combinable `set_name` / `product_type` /
    free-text `q` filters IN PROCESS (D-08) — never a MongoDB query
    operator built from raw user text (T-05-01 mitigation). With no
    filters, results are grouped by set in the hardcoded SET_ORDER,
    secondary-sorted by msrp descending within each set (D-10) — never
    a raw release_date sort (per-product release_date is staggered
    within a set).

    Args:
        db: An already-connected pymongo Database handle.
        filters: dict possibly containing "set_name", "product_type",
            "q" (each None when absent).

    Returns:
        list[dict]: `_product_summary` dicts for every matching
        product, sorted per D-10.

    Raises:
        ValueError: if filters["product_type"] is not None and not a
            member of VALID_PRODUCT_TYPES (V5).
    """
    product_type = filters.get("product_type")
    if product_type is not None and product_type not in VALID_PRODUCT_TYPES:
        raise ValueError(f"invalid product_type: {product_type!r}")

    set_name = filters.get("set_name")
    q = filters.get("q")
    q_lower = q.lower() if q else None

    # Whole small catalog fetched once — no filter built from user text.
    products = list(db.products.find({}))

    def matches(product):
        if set_name is not None and product.get("set_name") != set_name:
            return False
        if product_type is not None and product.get("product_type") != product_type:
            return False
        if q_lower is not None:
            display_name = (product.get("display_name") or "").lower()
            set_name_value = (product.get("set_name") or "").lower()
            if q_lower not in display_name and q_lower not in set_name_value:
                return False
        return True

    filtered = [p for p in products if matches(p)]

    def sort_key(product):
        msrp = product.get("msrp")
        return (
            SET_ORDER.index(product["set_name"]),
            -(msrp if msrp is not None else -1),
        )

    filtered.sort(key=sort_key)

    return [_product_summary(db, p) for p in filtered]
