"""Regression tests for scripts/ebay_client.py::total_cost (INGEST-03).

total_cost() is a pure unit — no I/O, no fixture needed. Import is
deferred into each test body (not at module top level), mirroring
tests/test_ingest_worker.py::test_build_query's style.

Exactly-representable float values (50.00, 4.50, 54.50) are used
throughout so `==` assertions stay safe, consistent with
tests/test_ingest_worker.py::test_price_and_shipping_captured.

This test file is authored RED first: the primary regression test
(missing shippingCost key) fails with a KeyError against the current
unpatched total_cost() until the defensive-parsing fix lands.
"""


def test_total_cost_missing_shipping_cost_key_defaults_to_zero():
    """A non-empty shippingOptions whose first entry lacks the
    "shippingCost" key must return item_price + 0.0, not raise
    KeyError — the real eBay Browse API response shape observed for
    calculated/freight shipping without a buyer postal code, or
    local-pickup-only options."""
    from scripts.ebay_client import total_cost

    item = {
        "price": {"value": "50.00"},
        "shippingOptions": [{"deliveryCost": {"value": "0.00"}}],
    }

    assert total_cost(item) == 50.0


def test_total_cost_well_formed_shipping_options():
    """A well-formed item with shippingOptions[0].shippingCost.value
    present returns item_price + shipping_cost."""
    from scripts.ebay_client import total_cost

    item = {
        "price": {"value": "50.00"},
        "shippingOptions": [{"shippingCost": {"value": "4.50"}}],
    }

    assert total_cost(item) == 54.5


def test_total_cost_no_shipping_options_key_defaults_to_zero():
    """An item with no shippingOptions key at all returns
    item_price + 0.0 — guards against regressing the already-working
    path."""
    from scripts.ebay_client import total_cost

    item = {"price": {"value": "50.00"}}

    assert total_cost(item) == 50.0
