"""Contract tests for the catalog's product images (scripts/catalog_data.py).

Pure data checks — no MongoDB, no network. The site shows `image_url` when a
product has one and a letter tile when it doesn't, so a missing image is a
silent visual regression; these tests make it loud.
"""

import re

from scripts.catalog_data import CATALOG, CURATED_CATALOG, GENERATED_CATALOG
from scripts.catalog_slug import EDITIONS, product_slug

TCGPLAYER_IMAGE = re.compile(
    r"^https://tcgplayer-cdn\.tcgplayer\.com/product/\d+_in_1000x1000\.jpg$"
)

def _key(entry):
    return (entry["set_name"], entry.get("edition"), entry["product_type"])


def test_every_catalog_entry_has_a_product_image():
    missing = [_key(e) for e in CATALOG if not e["image_url"]]
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


def test_catalog_is_curated_plus_generated():
    assert CATALOG == CURATED_CATALOG + GENERATED_CATALOG
    assert len(CURATED_CATALOG) == 15


def test_catalog_has_expected_scale():
    """About 350 entries: every English pack/box/ETB/bundle since Base Set."""
    assert 280 <= len(CATALOG) <= 420, len(CATALOG)


def test_slugs_are_unique():
    slugs = [product_slug(e) for e in CATALOG]
    duplicates = sorted({s for s in slugs if slugs.count(s) > 1})
    assert duplicates == []


def test_edition_values_are_valid_and_consistent_per_set():
    by_set = {}
    for e in CATALOG:
        edition = e.get("edition")
        assert edition in (None, *EDITIONS), _key(e)
        by_set.setdefault(e["set_name"], []).append(edition)
    for set_name, editions in by_set.items():
        if any(editions):
            assert all(editions), f"{set_name}: mixes edition and no-edition entries"
            assert len(set(editions)) >= 2, f"{set_name}: only one edition listed"


def test_generated_entries_have_the_full_shape():
    required = {
        "set_name", "product_type", "edition", "language", "release_date", "msrp",
        "image_url", "display_name", "required_keywords", "excluded_keywords",
        "verified", "verified_at",
    }
    for e in GENERATED_CATALOG:
        assert set(e) == required, _key(e)
        assert e["language"] == "en"
        assert e["msrp"] is None, f"{_key(e)}: msrp must stay unknown, not invented"


def test_required_keywords_lead_with_the_set_phrase():
    for e in CATALOG:
        assert e["required_keywords"], _key(e)
        assert e["required_keywords"][0] == e["required_keywords"][0].lower()
