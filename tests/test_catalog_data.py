"""Contract tests for the catalog's product images (scripts/catalog_data.py).

Pure data checks — no MongoDB, no network. The site shows `image_url` when a
product has one and a letter tile when it doesn't, so a missing image is a
silent visual regression; these tests make it loud.
"""

import re

from scripts.catalog_data import CATALOG

TCGPLAYER_IMAGE = re.compile(
    r"^https://tcgplayer-cdn\.tcgplayer\.com/product/\d+_in_1000x1000\.jpg$"
)

# TCGplayer lists no standalone product for these entries (there is no 36-pack
# Ascended Heroes booster display, and it has never matched a listing), so they
# keep the placeholder tile rather than a fabricated or substitute image.
NO_IMAGE_AVAILABLE = {("Ascended Heroes", "booster_box")}


def _key(entry):
    return (entry["set_name"], entry["product_type"])


def test_every_catalog_entry_has_a_product_image():
    missing = [
        _key(e) for e in CATALOG if _key(e) not in NO_IMAGE_AVAILABLE and not e["image_url"]
    ]
    assert missing == [], f"catalog entries with no image_url: {missing}"


def test_image_urls_are_tcgplayer_cdn_product_images():
    malformed = [
        (_key(e), e["image_url"])
        for e in CATALOG
        if e["image_url"] and not TCGPLAYER_IMAGE.match(e["image_url"])
    ]
    assert malformed == []


def test_no_two_products_share_an_image():
    urls = [e["image_url"] for e in CATALOG if e["image_url"]]
    assert len(urls) == len(set(urls)), "two catalog entries point at the same image"


def test_exemptions_still_describe_real_entries_without_images():
    """An exemption that no longer matches reality (entry removed, or image
    since added) should be deleted, not left to silently excuse a gap."""
    by_key = {_key(e): e for e in CATALOG}
    for key in NO_IMAGE_AVAILABLE:
        assert key in by_key, f"{key} is exempted but not in the catalog"
        assert by_key[key]["image_url"] is None, f"{key} now has an image; drop its exemption"
