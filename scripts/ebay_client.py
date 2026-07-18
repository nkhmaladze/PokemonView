"""Reusable eBay OAuth + Browse API client functions.

Provides the OAuth Client Credentials Grant handshake and a Browse API
keyword search wrapper. Intentionally minimal for Phase 1's feasibility
spike (Pattern 1 / Pattern 2, research/01-RESEARCH.md) — no token
caching/refresh wrapper is built here; that belongs to Phase 3's
ingestion worker (see "Don't Hand-Roll" in 01-RESEARCH.md).

Credential hygiene (threat T-01-02, D-02): EBAY_CLIENT_ID and
EBAY_CLIENT_SECRET are read exclusively from os.environ. This module
never prints or logs the full access token, the Authorization header,
or the base64-encoded Basic-auth credential string.

No top-level network calls execute on import — every function must be
explicitly invoked by a caller (see scripts/verify_ebay_access.py).
"""

import base64
import os

import requests

TIMEOUT_SECONDS = 15


def get_app_token(env: str = "production") -> dict:
    """Exchange EBAY_CLIENT_ID/EBAY_CLIENT_SECRET for an application access token.

    Uses the OAuth Client Credentials Grant against eBay's identity
    token endpoint. This grant type returns no refresh_token — there is
    nothing to refresh (Pitfall 6). Credentials are read only from
    os.environ, never hardcoded (D-02, threat T-01-02).

    Args:
        env: "production" or "sandbox" — selects the API host.

    Returns:
        Parsed JSON response dict containing access_token, expires_in,
        and token_type.
    """
    client_id = os.environ["EBAY_CLIENT_ID"]
    client_secret = os.environ["EBAY_CLIENT_SECRET"]
    host = "api.ebay.com" if env == "production" else "api.sandbox.ebay.com"
    creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    resp = requests.post(
        f"https://{host}/identity/v1/oauth2/token",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {creds}",
        },
        data={
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope",
        },
        timeout=TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    return resp.json()


def search_sealed_listings(access_token: str, query: str, limit: int = 50) -> list[dict]:
    """Search the Browse API for keyword matches and return itemSummaries.

    Keyword-only search (no category_ids) is used deliberately — no
    eBay category ID for "Pokemon sealed product" specifically has been
    confirmed (Assumption A2 / Open Question 2, 01-RESEARCH.md).
    Whatever categoryId real responses report should be recorded by the
    caller for later reuse as an optional narrowing filter.

    Args:
        access_token: Bearer token from get_app_token().
        query: Keyword search string (e.g. "Pokemon Scarlet Violet Elite
            Trainer Box").
        limit: Max results to request from the Browse API.

    Returns:
        List of itemSummary dicts, or an empty list if the response has
        none.
    """
    resp = requests.get(
        "https://api.ebay.com/buy/browse/v1/item_summary/search",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
        },
        params={
            "q": query,
            "filter": "conditions:{NEW}",
            "limit": limit,
        },
        timeout=TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    return resp.json().get("itemSummaries", [])


def total_cost(item: dict) -> float:
    """Compute the normalized total cost (item price + shipping cost).

    Per Pitfall 2 (research/PITFALLS.md), raw item.price alone
    under-represents true cost for listings with separate shipping.
    Shipping defaults to 0.0 whenever the shipping value is
    absent/None — whether shippingOptions itself is empty/missing, or
    shippingOptions is non-empty but its first entry has no
    shippingCost (or shippingCost has no value), a real eBay Browse
    API response shape seen for calculated/freight shipping without a
    buyer postal code, or local-pickup-only options.

    Args:
        item: An itemSummary dict from search_sealed_listings().

    Returns:
        item_price + shipping_cost as a float.
    """
    item_price = float(item["price"]["value"])
    shipping_options = item.get("shippingOptions", [])
    shipping_value = None
    if shipping_options:
        shipping_value = (shipping_options[0].get("shippingCost") or {}).get("value")
    shipping_cost = float(shipping_value) if shipping_value is not None else 0.0
    return item_price + shipping_cost
