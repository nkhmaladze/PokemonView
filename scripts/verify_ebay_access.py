"""Single-run smoke-test entrypoint proving SC-1 and producing SC-4.

Acquires an OAuth application token, searches the Browse API for real
Pokemon sealed-product listings across the 2-3 most recent English
sets, asserts that both item-price and shipping-cost fields are
present, and writes 50-100 captured listing titles to a fixture file
for Phase 4's matching-rule work.

This script is authored here (Plan 03) but NOT run — running requires
the user's real eBay Production credentials and network access,
handled in Plan 04.

Credential hygiene (threat T-01-02, D-02): loads EBAY_CLIENT_ID /
EBAY_CLIENT_SECRET / EBAY_ENV via load_dotenv() + os.environ, and never
prints the full access token — only token_type and expires_in.
"""

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

from ebay_client import get_app_token, search_sealed_listings, total_cost

# 2-3 most recent English sets' sealed product (booster packs, booster
# boxes, ETBs) per PROJECT.md scope. No confirmed sealed-product
# category ID exists (Assumption A2) — keyword-only search is used and
# whatever categoryId real responses report is captured for later reuse.
CATALOG_QUERIES = [
    "Pokemon Scarlet Violet Elite Trainer Box",
    "Pokemon Scarlet Violet Booster Box",
    "Pokemon Scarlet Violet Booster Pack",
    "Pokemon Paldea Evolved Elite Trainer Box",
    "Pokemon Paldea Evolved Booster Box",
    "Pokemon Obsidian Flames Elite Trainer Box",
    "Pokemon Obsidian Flames Booster Box",
]

FIXTURE_TARGET = (50, 100)  # inclusive range, per SC-4
FIXTURE_PATH = Path("fixtures/ebay_listing_titles.json")


def main() -> int:
    load_dotenv()
    env = os.environ.get("EBAY_ENV", "production")
    if env == "sandbox":
        # Sandbox catalog data is sparse/synthetic (Pitfall 1) — SC-1 and
        # SC-4 both require REAL listings, which only Production provides.
        print(
            "WARNING: EBAY_ENV=sandbox — Sandbox catalog data is sparse/synthetic "
            "and does not satisfy SC-1/SC-4's 'real listings' requirement. "
            "Set EBAY_ENV=production for the actual verification run.",
            file=sys.stderr,
        )

    try:
        token_resp = get_app_token(env=env)
    except requests.exceptions.RequestException as e:
        print(f"ERROR: OAuth token request failed: {e}", file=sys.stderr)
        return 1
    access_token = token_resp["access_token"]
    # Never print the full token — only metadata (threat T-01-02).
    print(
        f"OAuth OK — token_type={token_resp.get('token_type')}, "
        f"expires_in={token_resp.get('expires_in')}s"
    )

    captured = []
    seen_ids = set()
    shipping_proof_shown = False
    for query in CATALOG_QUERIES:
        try:
            items = search_sealed_listings(access_token, query, limit=50, env=env)
        except requests.exceptions.RequestException as e:
            print(
                f"ERROR: search_sealed_listings failed for query {query!r}: {e} "
                "— skipping this query and continuing.",
                file=sys.stderr,
            )
            continue
        for item in items:
            if "price" not in item:
                continue  # require price present before recording (Pitfall 3)

            item_id = item.get("itemId")
            if item_id in seen_ids:
                continue  # skip duplicates across overlapping CATALOG_QUERIES
            seen_ids.add(item_id)

            shipping_options = item.get("shippingOptions") or [{}]
            shipping_value = (shipping_options[0].get("shippingCost") or {}).get("value")
            shipping_cost = shipping_value if shipping_value is not None else "0.00"

            categories = item.get("categories") or [{}]
            record = {
                "title": item["title"],
                "item_price": item["price"]["value"],
                "shipping_cost": shipping_cost,
                "total_cost": total_cost(item),
                "categoryId": categories[0].get("categoryId"),
            }
            captured.append(record)

            if not shipping_proof_shown and item.get("shippingOptions"):
                # Explicit SC-1 proof: show a real (non-defaulted)
                # shipping-cost number in the success output, not just
                # raw JSON (Pitfall 3).
                print(
                    f"SC-1 proof — sample listing has price={record['item_price']} "
                    f"and shipping_cost={record['shipping_cost']}"
                )
                shipping_proof_shown = True

            if len(captured) >= FIXTURE_TARGET[1]:
                break
        if len(captured) >= FIXTURE_TARGET[1]:
            break

    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    fixture_records = captured[: FIXTURE_TARGET[1]]
    FIXTURE_PATH.write_text(json.dumps(fixture_records, indent=2))

    print(f"Captured {len(fixture_records)} listings -> {FIXTURE_PATH}")

    if len(fixture_records) < FIXTURE_TARGET[0]:
        print(
            f"WARNING: captured {len(fixture_records)} listings, below the "
            f"SC-4 target lower bound of {FIXTURE_TARGET[0]}. Consider adding "
            "more CATALOG_QUERIES or checking API access.",
            file=sys.stderr,
        )

    if not shipping_proof_shown:
        print(
            "WARNING: no listing with both price and shipping cost was found "
            "— SC-1's price+shipping proof requirement is not satisfied.",
            file=sys.stderr,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
