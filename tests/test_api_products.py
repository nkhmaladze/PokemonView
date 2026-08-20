"""RED contract tests for Phase 5's HTTP/JSON boundary — the `products`
Flask blueprint, its error handler, and CORS wiring (SEARCH-01,
SEARCH-02, PRICE-01, PRICE-02; 05-CONTEXT.md D-01, D-04, D-09, D-11,
D-12; V5 input validation; T-05-01/02/03 threat mitigations).

This is part of the Nyquist Wave 0 scaffold authored in Plan 05-03 —
`api/app.py` (and everything it wires together) does not exist yet.
The `client` fixture (tests/conftest.py) lazily imports
`api.app.create_app` inside its own body, so these tests fail RED
because the app cannot be built, not because of a collection-time
import error. These tests turn GREEN when Plan 05-06 implements
`api/app.py` + blueprint registration + the global error handler.

Uses the `client` (Flask test client) and `api_db` (seeded-products,
empty-price_points MongoDB handle) fixtures from tests/conftest.py.
Status codes and JSON envelopes assert against the exact "## API
Response Contract" shape locked in this plan.

This file also covers Phase 8's history route (PRICE-07, 08-CONTEXT.md
D-04/D-06) at the HTTP boundary: zero-point and unknown-id responses,
CORS coverage, and a regression guard proving the new history
capability did not loosen the detail route's existing D-11 contract.
"""

import os
from datetime import datetime, timedelta, timezone


def test_list_products_200(client):
    """SC1: GET /products returns HTTP 200 and a JSON array containing
    all 16 seeded catalog products."""
    response = client.get("/products")

    assert response.status_code == 200
    body = response.get_json()
    assert isinstance(body, list)
    assert len(body) == 16


def test_list_filter_by_set_and_type(client):
    """SC1/D-08: GET /products?set=...&product_type=... returns 200
    with only the matching product(s), filters combinable at the HTTP
    boundary."""
    response = client.get(
        "/products", query_string={"set": "Perfect Order", "product_type": "booster_box"}
    )

    assert response.status_code == 200
    body = response.get_json()
    assert len(body) == 1
    assert body[0]["id"] == "perfect-order_booster_box"


def test_list_free_text_search(client):
    """SC1/D-08: GET /products?q=... returns 200 with only products
    matching the free-text query (case-insensitive, against
    display_name/set_name)."""
    response = client.get("/products", query_string={"q": "chaos"})

    assert response.status_code == 200
    body = response.get_json()
    assert len(body) == 4
    assert all(p["set_name"] == "Chaos Rising" for p in body)


def test_product_detail_current_price(client, api_db):
    """SC2/PRICE-01/D-12: after inserting a price_point, GET
    /products/<slug> returns 200 with current_price.total_price
    (headline), current_price.item_price (secondary), and
    current_price.as_of (D-03) all present."""
    now = datetime.now(timezone.utc)
    api_db.price_points.insert_one(
        {
            "ts": now,
            "product_id": "perfect-order_booster_box",
            "item_price": 165.00,
            "total_price": 172.50,
        }
    )

    response = client.get("/products/perfect-order_booster_box")

    assert response.status_code == 200
    body = response.get_json()
    assert body["current_price"]["total_price"] == 172.50
    assert body["current_price"]["item_price"] == 165.00
    assert body["current_price"]["as_of"] is not None


def test_product_no_price_data(client):
    """D-01: GET for a seeded product with zero price_points returns
    200 with price_status == 'no_data_yet' and current_price null —
    NOT 404, NOT an omitted field."""
    response = client.get("/products/pitch-black_etb")

    assert response.status_code == 200
    body = response.get_json()
    assert body["price_status"] == "no_data_yet"
    assert body["current_price"] is None


def test_detail_unknown_id_404(client):
    """GET /products/does-not-exist returns 404 with
    {"error": "not_found"}."""
    response = client.get("/products/does-not-exist")

    assert response.status_code == 404
    assert response.get_json() == {"error": "not_found"}


def test_detail_omits_raw_series(client, api_db):
    """D-11: the detail JSON has no key holding an array of
    price_points — only current_price + trend_7d + trend_30d
    objects."""
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

    response = client.get("/products/perfect-order_booster_box")
    body = response.get_json()

    for key, value in body.items():
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
    assert isinstance(body["trend_7d"], dict)
    assert isinstance(body["trend_30d"], dict)


def test_unverified_products_shown_identically(client):
    """D-09: a Pitch Black (verified:false) product is present in
    /products output with the same shape as verified products — no
    exclusion, no extra badge field."""
    response = client.get("/products")
    body = response.get_json()

    pitch_black = [p for p in body if p["set_name"] == "Pitch Black"]
    others = [p for p in body if p["set_name"] != "Pitch Black"]

    assert len(pitch_black) == 4
    assert set(pitch_black[0].keys()) == set(others[0].keys())


def test_product_type_enum_validation(client):
    """V5/T-05-01: GET /products?product_type=not_a_type returns 400
    with {"error": "invalid_product_type"}."""
    response = client.get("/products", query_string={"product_type": "not_a_type"})

    assert response.status_code == 400
    assert response.get_json() == {"error": "invalid_product_type"}


def test_unregistered_set_name_returns_500_not_400(client, api_db, monkeypatch):
    """CR-01/VERIFICATION.md gap #11: an internal data-integrity
    ValueError (SET_ORDER.index() failing on an unregistered
    set_name) must surface as a generic 500 {"error": "internal_error"},
    NEVER masked as a client-facing 400 {"error": "invalid_product_type"}.

    Monkeypatching SET_ORDER to an empty list makes every seeded
    product's set_name unregistered, so sort_key's SET_ORDER.index()
    raises a plain base ValueError (not InvalidProductTypeError) during
    GET /products. This test FAILS against the pre-fix broad-except
    code (it would return 400) and PASSES only once the route narrows
    its except clause to catalog_service.InvalidProductTypeError.
    """
    from api.services import catalog_service

    monkeypatch.setattr(catalog_service, "SET_ORDER", [])

    response = client.get("/products")

    assert response.status_code == 500
    assert response.get_json() == {"error": "internal_error"}


def test_error_handler_no_traceback(client, monkeypatch):
    """T-05-02: an unhandled internal exception (simulated by
    monkeypatching the catalog service to raise) is caught by the
    global error handler and surfaces as HTTP 500 with a generic JSON
    body — DEBUG=False, no traceback text, no exception class name
    leaked into the response (information-disclosure mitigation)."""
    from api.services import catalog_service

    def raise_internal_error(*args, **kwargs):
        raise RuntimeError("boom - simulated internal error for T-05-02")

    monkeypatch.setattr(catalog_service, "list_products", raise_internal_error)

    response = client.get("/products")

    assert response.status_code == 500
    assert response.get_json() == {"error": "internal_error"}

    body_text = response.get_data(as_text=True)
    assert "Traceback" not in body_text
    assert 'File "' not in body_text
    assert "RuntimeError" not in body_text


def test_cors_header_present(client):
    """T-05-03: a GET /products response includes an
    Access-Control-Allow-Origin header, proving Flask-CORS is
    initialized on the app."""
    response = client.get("/products")

    assert "Access-Control-Allow-Origin" in response.headers


def test_product_history_returns_ordered_series(client, api_db):
    """PRICE-07/D-04: GET /products/<product_id>/history returns 200
    with the product's price_points series ordered oldest-first by ts,
    each element carrying exactly {ts, total_price}. Points are
    inserted out of order so the ascending sort is genuinely
    exercised."""
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
                "total_price": 157.50,
            },
            {
                "ts": now - timedelta(days=1),
                "product_id": "perfect-order_booster_box",
                "item_price": 158.00,
                "total_price": 165.50,
            },
        ]
    )

    response = client.get("/products/perfect-order_booster_box/history")

    assert response.status_code == 200
    body = response.get_json()
    assert isinstance(body, list)
    assert len(body) == 3
    assert [point["total_price"] for point in body] == [157.50, 165.50, 172.50]
    for point in body:
        assert set(point.keys()) == {"ts", "total_price"}
        datetime.fromisoformat(point["ts"])
        # CR-01, 08-REVIEW.md: a naive (no UTC offset) ts string is parsed
        # by the frontend's `new Date(ts)` as local time, not UTC — pins
        # the get_price_history fix that attaches timezone.utc before
        # serializing.
        assert point["ts"].endswith(("+00:00", "Z")), (
            f"ts {point['ts']!r} has no UTC offset — CR-01 regression"
        )


def test_product_history_empty_for_product_with_no_points(client):
    """Pitfall 2: a seeded product that has never had a point collected
    is a normal, expected state and must never surface as an HTTP
    error — GET /products/pitch-black_etb/history returns 200 and []."""
    response = client.get("/products/pitch-black_etb/history")

    assert response.status_code == 200
    assert response.get_json() == []


def test_product_history_unknown_id_is_200_empty(client):
    """08-RESEARCH.md Open Question 1, resolved: an id absent from the
    catalog does NOT mirror test_detail_unknown_id_404's behaviour on
    this route. The frontend only ever requests history for an id its
    detail loader has already resolved, and at this layer an unknown
    id is indistinguishable from a catalogued product with no
    collected points, so both correctly produce 200 + []."""
    response = client.get("/products/does-not-exist/history")

    assert response.status_code == 200
    assert response.get_json() == []


def test_product_history_cors_header_present(client):
    """CR-02: the history path sits under the same r"/products*"
    resource pattern Flask-CORS is scoped to, so the SPA on a
    different origin can read it (mirrors test_cors_header_present)."""
    response = client.get("/products/pitch-black_etb/history")

    assert "Access-Control-Allow-Origin" in response.headers


def test_detail_still_omits_raw_series_after_history_endpoint(client, api_db):
    """D-06 regression guard: adding the history capability must not
    have loosened get_product_detail's existing contract, which
    deliberately withholds the raw price_points series (D-11). Uses
    the same per-key scan as test_detail_omits_raw_series."""
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
                "ts": now - timedelta(days=1),
                "product_id": "perfect-order_booster_box",
                "item_price": 158.00,
                "total_price": 165.50,
            },
            {
                "ts": now - timedelta(days=2),
                "product_id": "perfect-order_booster_box",
                "item_price": 150.00,
                "total_price": 157.50,
            },
        ]
    )

    response = client.get("/products/perfect-order_booster_box")
    body = response.get_json()

    for key, value in body.items():
        is_point_series = (
            isinstance(value, list)
            and len(value) > 0
            and isinstance(value[0], dict)
            and "ts" in value[0]
        )
        assert not is_point_series, (
            f"the detail response must not contain a raw price_points "
            f"series/array (D-06/D-11) even now that a history endpoint "
            f"exists; found one at key '{key}'"
        )


def test_multi_origin_cors_matches_each_origin(api_db, monkeypatch):
    """CR-02/VERIFICATION.md gap #12: a comma-separated CORS_ORIGINS
    value (the documented production format) produces a matching
    Access-Control-Allow-Origin header for each configured origin, and
    does NOT reflect an unconfigured origin.

    This test FAILS against the pre-fix raw-string code (the header is
    absent/incorrect for each origin, since flask-cors 6.0.5
    literal-wraps the whole unsplit string as one origin) and PASSES
    only once CORS_ORIGINS is comma-split into a real list before being
    passed to Flask-CORS's origins= argument.
    """
    monkeypatch.setenv("CORS_ORIGINS", "https://a.example,https://b.example")

    from api.app import create_app

    app = create_app(mongodb_uri=os.environ["MONGODB_URI"], db_name="pokemonview_test")
    c = app.test_client()

    for origin in ("https://a.example", "https://b.example"):
        resp = c.get("/products", headers={"Origin": origin})
        assert resp.headers.get("Access-Control-Allow-Origin") == origin

    resp = c.get("/products", headers={"Origin": "https://evil.example"})
    assert resp.headers.get("Access-Control-Allow-Origin") != "https://evil.example"
