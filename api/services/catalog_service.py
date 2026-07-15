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

from api.services.price_service import (
    compute_pct_change,
    get_current_price,
    get_trend_baseline,
)

class InvalidProductTypeError(ValueError):
    """Raised ONLY for an unrecognized `?product_type` filter value (V5
    enum check) — never for any other internal ValueError (e.g. an
    unregistered set_name inside sort_key's SET_ORDER.index() lookup),
    so the products blueprint can narrow its except clause to this
    subclass without masking unrelated server-side bugs (CR-01)."""


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
        InvalidProductTypeError: a ValueError subclass, if
            filters["product_type"] is not None and not a member of
            VALID_PRODUCT_TYPES (V5).
    """
    product_type = filters.get("product_type")
    if product_type is not None and product_type not in VALID_PRODUCT_TYPES:
        raise InvalidProductTypeError(f"invalid product_type: {product_type!r}")

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


def get_product_detail(db, product_id):
    """Assemble a single product's detail: catalog metadata + current
    price + 7d/30d trend (SEARCH-02, PRICE-01).

    Never includes a raw price_points series/array (D-11) — only the
    single current_price object and the two trend objects. Returns
    None for an unknown id (the blueprint translates this to a 404).

    Args:
        db: An already-connected pymongo Database handle.
        product_id: The canonical catalog product slug.

    Returns:
        dict | None: the detail dict, or None when product_id is
        unknown.
    """
    product = db.products.find_one({"_id": product_id})
    if product is None:
        return None

    detail = _product_summary(db, product)

    if detail["current_price"] is None:
        # No data yet (D-01) — both trends are explicitly insufficient
        # data, never omitted/None-the-whole-response.
        detail["trend_7d"] = {"pct_change": None, "status": "insufficient_data"}
        detail["trend_30d"] = {"pct_change": None, "status": "insufficient_data"}
        return detail

    current_total = detail["current_price"]["total_price"]
    current_point = get_current_price(db, product_id)
    current_ts = current_point["ts"]

    trend_key_by_days = {7: "trend_7d", 30: "trend_30d"}
    for days in TREND_WINDOWS:
        key = trend_key_by_days[days]
        baseline = get_trend_baseline(db, product_id, current_ts, days)
        if baseline is None:
            detail[key] = {"pct_change": None, "status": "insufficient_data"}
            continue
        # Trend uses total_price only (D-07).
        pct = compute_pct_change(current_total, baseline["total_price"])
        if pct is None:
            detail[key] = {"pct_change": None, "status": "insufficient_data"}
        else:
            detail[key] = {"pct_change": pct, "status": "ok"}

    return detail
