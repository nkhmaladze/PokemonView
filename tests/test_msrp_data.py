"""scripts/msrp_data.py: launch-era US MSRPs for the generated catalog products.

The table is keyed by product slug and only holds prices a launch-era source
states for that exact product. Everything else stays unknown (None), and the
site hides the MSRP line for it.
"""

from scripts.catalog_data import CATALOG, CURATED_CATALOG, GENERATED_CATALOG
from scripts.catalog_slug import product_slug
from scripts.msrp_data import MSRP_BY_PRODUCT


def _by_slug(entries):
    return {product_slug(e): e for e in entries}


GENERATED = _by_slug(GENERATED_CATALOG)
FINAL = _by_slug(CATALOG)

# Plausible retail range per product type: catches a misplaced decimal point.
SANE_RANGE = {
    "booster_pack": (2.0, 8.0),
    "booster_bundle": (15.0, 40.0),
    "etb": (30.0, 70.0),
    "booster_box": (100.0, 220.0),
}


def test_the_table_is_not_empty():
    assert len(MSRP_BY_PRODUCT) > 50


def test_every_key_is_a_generated_product():
    assert [k for k in MSRP_BY_PRODUCT if k not in GENERATED] == []


def test_no_key_is_a_hand_curated_product():
    # Curated entries keep their own hand-checked MSRPs.
    curated = {product_slug(e) for e in CURATED_CATALOG}
    assert curated.isdisjoint(MSRP_BY_PRODUCT)


def test_values_are_whole_cents_in_a_sane_range_for_their_type():
    for slug, price in MSRP_BY_PRODUCT.items():
        low, high = SANE_RANGE[GENERATED[slug]["product_type"]]
        assert isinstance(price, float), slug
        assert round(price, 2) == price, slug
        assert low <= price <= high, f"{slug}: {price} outside {low}-{high}"


def test_only_products_from_the_xy_era_onward_have_an_msrp():
    too_old = [s for s in MSRP_BY_PRODUCT if GENERATED[s]["release_date"] < "2014-02-01"]
    assert too_old == []


def test_a_box_is_36_packs_and_a_bundle_is_6_packs_where_both_prices_are_known():
    sets = {}
    for slug, price in MSRP_BY_PRODUCT.items():
        e = GENERATED[slug]
        sets.setdefault((e["set_name"], e["edition"]), {})[e["product_type"]] = price
    checked = 0
    for key, prices in sets.items():
        if "booster_pack" in prices and "booster_box" in prices:
            assert prices["booster_box"] == round(36 * prices["booster_pack"], 2), key
            checked += 1
        if "booster_pack" in prices and "booster_bundle" in prices:
            assert prices["booster_bundle"] == round(6 * prices["booster_pack"], 2), key
            checked += 1
    assert checked > 5  # the check is actually exercised


def test_catalog_carries_each_msrp():
    for slug, price in MSRP_BY_PRODUCT.items():
        assert FINAL[slug]["msrp"] == price


def test_products_without_a_known_msrp_stay_unknown():
    unknown = [s for s in GENERATED if s not in MSRP_BY_PRODUCT]
    assert unknown, "expected some products to stay unknown"
    assert all(FINAL[s]["msrp"] is None for s in unknown)


def test_curated_entries_are_untouched_and_first():
    assert CATALOG[: len(CURATED_CATALOG)] == CURATED_CATALOG


def test_generated_catalog_itself_is_not_modified():
    # The generated file is rewritten by scripts/build_catalog.py, so the MSRPs
    # live beside it and are applied on top, never written into it.
    assert all(e["msrp"] is None for e in GENERATED_CATALOG)
