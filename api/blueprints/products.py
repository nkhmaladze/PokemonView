"""The `products` blueprint — three thin routes (catalog browse,
single-product detail, and a product's price-history sub-route) over
`api.services.catalog_service` / `api.services.price_service`
(SEARCH-01, SEARCH-02, PRICE-01/02/03/07; 05-RESEARCH.md Pattern 2;
08-CONTEXT.md D-04).

Routes parse request args, delegate to a single service function, and
`jsonify()` the returned dict/list with no further transformation — no
pymongo calls happen in this module. Only a
`catalog_service.InvalidProductTypeError` (V5/T-05-01, invalid
`?product_type`) and a `None` detail-lookup result (unknown product
id) are translated here into 400/404 JSON envelopes; any other
unexpected exception (including an internal base `ValueError`, e.g.
from an unregistered set_name) is left to propagate to the app-level
global error handler (api/app.py) so it becomes a generic 500 instead
of a leaked partial response or a misleading 400 (CR-01). The history
route deliberately has no such branch — an unknown product id and a
product with zero points both correctly produce 200 + [].

No top-level side effects on import: no MongoClient construction, no
os.environ read, no route registration outside this module's
decorators (which only run once Flask imports this module inside
create_app, never a network/DB call at import time).
"""

from flask import Blueprint, jsonify, request

from api.db import get_db
from api.services import catalog_service, price_service

products_bp = Blueprint("products", __name__)


@products_bp.route("/products")
def list_products():
    """GET /products — browse/search/filter the catalog (SEARCH-01).

    Honors ?set, ?product_type, ?q (D-08, combinable). Returns 200 +
    JSON array on success; 400 {"error": "invalid_product_type"} when
    catalog_service raises InvalidProductTypeError for an unrecognized
    product_type (V5/T-05-01). Any other exception (e.g. an internal
    base ValueError from an unregistered set_name) is NOT caught here
    and propagates to the global error handler as a 500 (CR-01).
    """
    filters = {
        "set_name": request.args.get("set"),
        "product_type": request.args.get("product_type"),
        "q": request.args.get("q"),
    }

    try:
        result = catalog_service.list_products(get_db(), filters)
    except catalog_service.InvalidProductTypeError:
        return jsonify({"error": "invalid_product_type"}), 400

    return jsonify(result)


@products_bp.route("/products/<product_id>")
def product_detail(product_id):
    """GET /products/<product_id> — single-product detail assembly
    (SEARCH-02, PRICE-01/02/03).

    Returns 200 + the detail object on success; 404
    {"error": "not_found"} when catalog_service.get_product_detail
    returns None for an unknown id.
    """
    detail = catalog_service.get_product_detail(get_db(), product_id)
    if detail is None:
        return jsonify({"error": "not_found"}), 404

    return jsonify(detail)


@products_bp.route("/products/<product_id>/history")
def product_history(product_id):
    """A product's price-history sub-route — raw price_points series,
    time-ordered ascending (PRICE-07, 08-CONTEXT.md D-04). Always
    returns 200 + a JSON array; an unknown product id and a product
    with zero points both correctly produce 200 + [], not a 404.
    """
    history = price_service.get_price_history(get_db(), product_id)
    return jsonify(history)
