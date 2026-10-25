"""The one product slug: `products._id`, price_points `product_id`,
active_listings `product_ref` and the URL segment of a product page.

A catalog entry is identified by (set_name, edition, product_type).
`edition` is None for sets with a single printing, otherwise one of
EDITIONS. With no edition the slug is `{set_name}_{product_type}`
lowercased with spaces turned into hyphens, exactly the formula the
curated entries have always used, so their production ids never change.

Pure function, no side effects on import (same convention as the rest of
scripts/).
"""

import re
import unicodedata

EDITIONS = ("1st Edition", "Shadowless", "Unlimited")


def product_slug(product: dict) -> str:
    """Deterministic slug for a catalog entry (see module docstring)."""
    set_part = product["set_name"]
    edition = product.get("edition")
    if edition:
        set_part = f"{set_part} {edition}"
    set_part = unicodedata.normalize("NFKD", set_part)
    set_part = "".join(c for c in set_part if not unicodedata.combining(c))
    set_part = re.sub(r"['\u2019]", "", set_part.lower()).replace("&", " and ")
    set_part = re.sub(r"[^a-z0-9]+", "-", set_part).strip("-")
    return f"{set_part}_{product['product_type']}"
