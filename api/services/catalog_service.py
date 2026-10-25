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

`list_products` filters the whole (a few hundred products) catalog IN PROCESS —
never a MongoDB query operator built from raw user text (T-05-01
mitigation). `get_product_detail` composes
`price_service.get_current_price` / `get_trend_baseline` /
`compute_pct_change` into the locked list/detail response shape and
never returns a raw price_points series (D-11).
"""

from datetime import timezone

from api.services.price_service import (
    TREND_24H_TOLERANCE_HOURS,
    compute_pct_change,
    get_all_time_range,
    get_current_price,
    get_latest_prices,
    get_trend_baseline,
)

class InvalidProductTypeError(ValueError):
    """Raised ONLY for an unrecognized `?product_type` filter value (V5
    enum check) — never for any other internal ValueError (e.g. a
    data-integrity ValueError raised while building a product summary),
    so the products blueprint can narrow its except clause to this
    subclass without masking unrelated server-side bugs (CR-01)."""


# D-10 (revised): sets are ordered newest first by their release date, not
# by a hardcoded list; inside a set, by edition and then product type.
TYPE_RANK = {"booster_box": 0, "etb": 1, "booster_bundle": 2, "booster_pack": 3}
EDITION_RANK = {"1st Edition": 0, "Shadowless": 1, "Unlimited": 2, None: 3}
VALID_PRODUCT_TYPES = {"booster_pack", "booster_box", "etb", "booster_bundle"}  # V5 enum
TREND_WINDOWS = (7, 30)  # D-05


_LOOKUP = object()  # "fetch the current price yourself" marker


def _product_summary(db, product, current_point=_LOOKUP):
    """Build the jsonify-ready base dict for one product: catalog
    metadata plus its current_price/price_status (D-01/D-04/D-12).

    verified:false products (Pitch Black) get no special handling here
    — they pass through with the exact same field shape as verified
    products (D-09).

    Args:
        db: An already-connected pymongo Database handle.
        product: A raw `products` collection document.
        current_point: This product's latest price_points document (or
            None for no data) when the caller already has it, e.g. from
            get_latest_prices; omitted -> looked up here.

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

    if current_point is _LOOKUP:
        current_point = get_current_price(db, product["_id"])
    if current_point is not None:
        summary["price_status"] = "ok"
        summary["current_price"] = {
            "total_price": current_point["total_price"],
            "item_price": current_point["item_price"],
            # The app's MongoClient is not tz_aware, so `ts` comes back naive
            # though it is a UTC instant; attach the offset so the frontend's
            # `new Date(as_of)` doesn't read it as the viewer's local time
            # (same fix as price_service.get_price_history).
            "as_of": current_point["ts"].replace(tzinfo=timezone.utc).isoformat(),
            "listing_count": current_point.get("listing_count"),
        }
    else:
        summary["price_status"] = "no_data_yet"
        summary["current_price"] = None

    return summary


def list_products(db, filters):
    """Browse/search/filter the catalog (SEARCH-01).

    Fetches the whole catalog once (`db.products.find({})`, a few
    hundred docs) and applies combinable `set_name` / `product_type` /
    free-text `q` filters IN PROCESS (D-08) — never a MongoDB query
    operator built from raw user text (T-05-01 mitigation). Results are
    grouped by set, newest set first (a set's rank is the earliest
    release_date of its products, name as tiebreak), then by edition
    (1st Edition, Shadowless, Unlimited) and product type (box, ETB,
    bundle, pack) within a set (D-10, revised). Current prices come from one
    batched read (`get_latest_prices`), not one query per product.

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

    # A set's rank is its earliest product release date over the WHOLE
    # catalog (not the filtered view), so filtering never reorders sets.
    # Per-product dates are staggered within a set (05-RESEARCH.md
    # Pitfall 1), hence the minimum rather than any one product's date.
    set_release = {}
    for product in products:
        date = product.get("release_date")
        if date is None:
            continue
        name = product.get("set_name")
        if name not in set_release or date < set_release[name]:
            set_release[name] = date

    def sort_key(product):
        name = product.get("set_name") or ""
        date = set_release.get(name)
        set_rank = (0, -date.toordinal()) if date is not None else (1, 0)
        return (
            set_rank,
            name,
            EDITION_RANK.get(product.get("edition"), len(EDITION_RANK)),
            TYPE_RANK.get(product.get("product_type"), len(TYPE_RANK)),
            product.get("display_name") or "",
        )

    filtered.sort(key=sort_key)

    latest = get_latest_prices(db)
    return [_product_summary(db, p, latest.get(p["_id"])) for p in filtered]


def get_product_detail(db, product_id):
    """Assemble a single product's detail: catalog metadata + current
    price + 24h/7d/30d trend + all-time range (SEARCH-02, PRICE-01,
    PRICE-08, PRICE-09).

    Never includes a raw price_points series/array (D-11) — only the
    single current_price object, the three trend objects, and the
    all_time_range object, each a small aggregate rather than a series.
    Returns None for an unknown id (the blueprint translates this to a
    404).

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
        # No data yet (D-01) — all three trends are explicitly
        # insufficient data, never omitted/None-the-whole-response. A
        # product with no current price by definition has zero stored
        # points, which is why all_time_range is insufficient-data here
        # rather than being computed — the two conditions are the same
        # condition, not two independent checks.
        detail["trend_24h"] = {"pct_change": None, "status": "insufficient_data"}
        detail["trend_7d"] = {"pct_change": None, "status": "insufficient_data"}
        detail["trend_30d"] = {"pct_change": None, "status": "insufficient_data"}
        detail["all_time_range"] = {"high": None, "low": None, "status": "insufficient_data"}
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

    # The 24h window is deliberately NOT folded into the TREND_WINDOWS
    # loop above — that loop calls get_trend_baseline without a
    # tolerance_days argument and would silently apply the module's
    # three-day default, which is nonsensical for a one-day target.
    baseline_24h = get_trend_baseline(
        db, product_id, current_ts, days=1, tolerance_days=TREND_24H_TOLERANCE_HOURS / 24
    )
    if baseline_24h is None:
        detail["trend_24h"] = {"pct_change": None, "status": "insufficient_data"}
    else:
        pct_24h = compute_pct_change(current_total, baseline_24h["total_price"])
        if pct_24h is None:
            detail["trend_24h"] = {"pct_change": None, "status": "insufficient_data"}
        else:
            detail["trend_24h"] = {"pct_change": pct_24h, "status": "ok"}

    all_time = get_all_time_range(db, product_id)
    if all_time is None:
        detail["all_time_range"] = {"high": None, "low": None, "status": "insufficient_data"}
    else:
        detail["all_time_range"] = {
            "high": all_time["high"],
            "low": all_time["low"],
            "status": "ok",
        }

    return detail
