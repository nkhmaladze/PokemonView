"""Pure tests for the one shared product slug (scripts/catalog_slug.py).

The slug is the `products._id`, the price_points `product_id`, the
active_listings `product_ref` and the URL segment of every product page, so
the 15 curated slugs below are production keys and must never change.
"""

from scripts.catalog_data import CATALOG
from scripts.catalog_slug import EDITIONS, product_slug

CURATED_SETS = {"Pitch Black", "Chaos Rising", "Perfect Order", "Ascended Heroes"}

CURATED_SLUGS = {
    "pitch-black_etb",
    "pitch-black_booster_box",
    "pitch-black_booster_bundle",
    "pitch-black_booster_pack",
    "chaos-rising_etb",
    "chaos-rising_booster_box",
    "chaos-rising_booster_bundle",
    "chaos-rising_booster_pack",
    "perfect-order_etb",
    "perfect-order_booster_box",
    "perfect-order_booster_bundle",
    "perfect-order_booster_pack",
    "ascended-heroes_etb",
    "ascended-heroes_booster_bundle",
    "ascended-heroes_booster_pack",
}


def test_curated_slugs_are_unchanged():
    slugs = {product_slug(e) for e in CATALOG if e["set_name"] in CURATED_SETS}
    assert slugs == CURATED_SLUGS


def test_slug_includes_edition():
    entry = {"set_name": "Base Set", "edition": "1st Edition", "product_type": "booster_box"}
    assert product_slug(entry) == "base-set-1st-edition_booster_box"


def test_slug_edition_none_and_missing_are_identical():
    with_none = {"set_name": "Jungle", "edition": None, "product_type": "booster_pack"}
    missing = {"set_name": "Jungle", "product_type": "booster_pack"}
    assert product_slug(with_none) == product_slug(missing) == "jungle_booster_pack"


def test_slug_folds_ampersand_and_accents():
    assert product_slug({"set_name": "Sword & Shield", "product_type": "etb"}) == "sword-and-shield_etb"
    assert product_slug({"set_name": "Pokémon GO", "product_type": "etb"}) == "pokemon-go_etb"


def test_slug_is_url_safe():
    slug = product_slug({"set_name": "Team Magma vs. Team Aqua", "product_type": "booster_box"})
    assert slug == "team-magma-vs-team-aqua_booster_box"


def test_editions_constant():
    assert EDITIONS == ("1st Edition", "Shadowless", "Unlimited")


def test_slug_drops_apostrophes_instead_of_hyphenating_them():
    """"Champion's Path" -> champions-path, not champion-s-path (slugs are
    permanent production keys and URLs)."""
    assert product_slug({"set_name": "Champion's Path", "product_type": "etb"}) == "champions-path_etb"
    assert product_slug({"set_name": "Champion\u2019s Path", "product_type": "etb"}) == "champions-path_etb"
