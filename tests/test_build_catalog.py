"""Offline tests for scripts/build_catalog.py (TCGplayer product lists ->
catalog entries). Uses trimmed real data in tests/fixtures/tcgcsv/ (sealed
products plus two single cards per group, from tcgcsv.com's mirror of
TCGplayer); no network, no MongoDB.
"""

import json
import re
from datetime import date
from pathlib import Path

import pytest

from scripts.catalog_slug import EDITIONS, product_slug

FIXTURES = Path(__file__).parent / "fixtures" / "tcgcsv"
TODAY = date(2026, 10, 24)
IMAGE = "https://tcgplayer-cdn.tcgplayer.com/product/{id}_in_1000x1000.jpg"

CURATED = [
    {"set_name": "Perfect Order", "product_type": "booster_box", "release_date": "2026-03-27",
     "required_keywords": ["perfect order", "booster box", "display"]},
    {"set_name": "Chaos Rising", "product_type": "etb", "release_date": "2026-05-22",
     "required_keywords": ["chaos rising", "elite trainer box", "etb"]},
]


def _load():
    groups = json.loads((FIXTURES / "groups.json").read_text())["results"]
    products = {
        g["groupId"]: json.loads((FIXTURES / f"products_{g['groupId']}.json").read_text())["results"]
        for g in groups
    }
    return groups, products


@pytest.fixture(scope="module")
def built():
    from scripts.build_catalog import build_entries

    groups, products = _load()
    return build_entries(groups, products, CURATED, TODAY)


def _by_set(entries, set_name):
    return [e for e in entries if e["set_name"] == set_name]


def _image_id(entry):
    return int(re.search(r"/product/(\d+)_", entry["image_url"]).group(1))


# --- classify_product -------------------------------------------------------


@pytest.mark.parametrize(
    "name, set_name, expected",
    [
        ("Obsidian Flames Booster Box", "Obsidian Flames", ("booster_box", None)),
        ("Obsidian Flames Booster Pack", "Obsidian Flames", ("booster_pack", None)),
        ("Obsidian Flames Elite Trainer Box", "Obsidian Flames", ("etb", None)),
        ("Obsidian Flames Booster Bundle", "Obsidian Flames", ("booster_bundle", None)),
        ("Jungle Booster Box [1st Edition]", "Jungle", ("booster_box", "1st Edition")),
        ("Jungle Booster Pack [Unlimited Edition]", "Jungle", ("booster_pack", "Unlimited")),
        ("Base Set Booster Box [Revised Unlimited Edition]", "Base Set", ("booster_box", "Unlimited")),
        (
            "Pokemon Base Set (Shadowless) [1st Edition] Booster Box",
            "Base Set",
            ("booster_box", "1st Edition"),
        ),
        (
            "Pokemon Base Set (Shadowless) [Unlimited Edition] Booster Pack",
            "Base Set",
            ("booster_pack", "Shadowless"),
        ),
        ("Surging Sparks Booster Bundle (Retail)", "Surging Sparks", ("booster_bundle", None)),
    ],
)
def test_classify_accepts_main_products(name, set_name, expected):
    from scripts.build_catalog import classify_product

    assert classify_product(name, set_name) == expected


@pytest.mark.parametrize(
    "name",
    [
        "Obsidian Flames Booster Box Case",
        "Obsidian Flames Pokemon Center Elite Trainer Box (Exclusive)",
        "Code Card - Obsidian Flames Booster Pack",
        "Obsidian Flames Sleeved Booster Pack",
        "Obsidian Flames Booster Pack Art Bundle [Set of 4]",
        "Obsidian Flames 3 Pack Blister [Eevee]",
        "Obsidian Flames Booster Bundle Display",
        "Evolving Skies Half Booster Box",
        "Mega Evolution Enhanced Booster Box",
        "Forbidden Light 3-Card Booster Pack",
        "Prismatic Evolutions Booster Bundle + Surprise Box Bundle (Sam's Club)",
        "Scarlet & Violet Elite Trainer Boxes [Set of 2]",
        "Base Set Theme Deck - \"Blackout\"",
        "Obsidian Flames Build & Battle Box",
    ],
)
def test_classify_rejects_everything_that_is_not_a_main_product(name):
    from scripts.build_catalog import classify_product

    assert classify_product(name, "Obsidian Flames") is None


def test_classify_strips_the_set_name_before_checking_deny_words():
    """"Legendary Collection Booster Box" contains the deny word "collection"
    only because of the set's own name."""
    from scripts.build_catalog import classify_product

    assert classify_product("Legendary Collection Booster Box", "Legendary Collection") == (
        "booster_box",
        None,
    )


# --- clean_set_name ---------------------------------------------------------


@pytest.mark.parametrize(
    "group_name, expected",
    [
        ("SWSH01: Sword & Shield Base Set", "Sword & Shield"),
        ("SV01: Scarlet & Violet Base Set", "Scarlet & Violet"),
        ("SV03: Obsidian Flames", "Obsidian Flames"),
        ("SV: Paldean Fates", "Paldean Fates"),
        ("SWSH: Crown Zenith", "Crown Zenith"),
        ("ME: Ascended Heroes", "Ascended Heroes"),
        ("ME01: Mega Evolution", "Mega Evolution"),
        ("XY Base Set", "XY"),
        ("XY - Flashfire", "Flashfire"),
        ("SM Base Set", "Sun & Moon"),
        ("SM - Guardians Rising", "Guardians Rising"),
        ("Black and White", "Black & White"),
        ("Diamond and Pearl", "Diamond & Pearl"),
        ("EX Ruby and Sapphire", "EX Ruby & Sapphire"),
        ("Base Set (Shadowless)", "Base Set"),
        ("Base Set", "Base Set"),
        ("Pokemon GO", "Pokemon GO"),
        ("SV: Scarlet & Violet 151", "Scarlet & Violet 151"),
    ],
)
def test_clean_set_name(group_name, expected):
    from scripts.build_catalog import clean_set_name

    assert clean_set_name(group_name) == expected


# --- build_entries ----------------------------------------------------------


def test_obsidian_flames_gets_exactly_the_four_main_products(built):
    entries, _ = built
    flames = {e["product_type"]: e for e in _by_set(entries, "Obsidian Flames")}

    assert {t: _image_id(e) for t, e in flames.items()} == {
        "booster_box": 501257,
        "booster_bundle": 501263,
        "etb": 501264,
        "booster_pack": 501256,
    }
    box = flames["booster_box"]
    assert box["image_url"] == IMAGE.format(id=501257)
    assert box["edition"] is None
    assert box["msrp"] is None
    assert box["language"] == "en"
    assert box["release_date"] == "2023-08-11"
    assert box["display_name"] == "Obsidian Flames Booster Box"
    assert box["required_keywords"] == ["obsidian flames", "booster box"]
    assert box["verified"] is True and box["verified_at"] is None


def test_hidden_fates_has_only_etb_and_pack(built):
    entries, _ = built
    fates = {e["product_type"]: _image_id(e) for e in _by_set(entries, "Hidden Fates")}
    assert fates == {"etb": 194729, "booster_pack": 198634}


def test_legendary_collection_is_classified(built):
    entries, _ = built
    legendary = {e["product_type"]: _image_id(e) for e in _by_set(entries, "Legendary Collection")}
    assert legendary == {"booster_box": 691155, "booster_pack": 138150}


def test_etb_colour_variants_collapse_to_the_lowest_product_id(built):
    entries, report = built
    xy_etb = [e for e in _by_set(entries, "XY") if e["product_type"] == "etb"]
    assert [_image_id(e) for e in xy_etb] == [97747]
    collapsed = [c for c in report["collapsed"] if c["set_name"] == "XY" and c["product_type"] == "etb"]
    assert len(collapsed) == 1
    assert collapsed[0]["kept"] == "XY Elite Trainer Box [Xerneas]"
    assert collapsed[0]["dropped"] == ["XY Elite Trainer Box [Yveltal]"]


def test_base_set_has_all_three_editions_for_box_and_pack(built):
    entries, _ = built
    base = {(e["edition"], e["product_type"]): _image_id(e) for e in _by_set(entries, "Base Set")}
    assert base == {
        ("1st Edition", "booster_box"): 107596,
        ("Shadowless", "booster_box"): 107597,
        ("Unlimited", "booster_box"): 185731,
        ("1st Edition", "booster_pack"): 138132,
        ("Shadowless", "booster_pack"): 138131,
        ("Unlimited", "booster_pack"): 138130,
    }
    names = {(e["edition"], e["product_type"]): e["display_name"] for e in _by_set(entries, "Base Set")}
    assert names[("1st Edition", "booster_box")] == "Base Set Booster Box (1st Edition)"
    assert names[("Shadowless", "booster_pack")] == "Base Set Booster Pack (Shadowless Unlimited)"
    assert names[("Unlimited", "booster_box")] == "Base Set Booster Box (Unlimited)"


def test_jungle_has_1st_edition_and_unlimited(built):
    entries, _ = built
    jungle = {(e["edition"], e["product_type"]): _image_id(e) for e in _by_set(entries, "Jungle")}
    assert jungle == {
        ("1st Edition", "booster_box"): 107598,
        ("Unlimited", "booster_box"): 107599,
        ("1st Edition", "booster_pack"): 138128,
        ("Unlimited", "booster_pack"): 138129,
    }


def test_a_set_with_a_single_edition_tag_gets_no_edition():
    from scripts.build_catalog import build_entries

    groups = [{"groupId": 1, "name": "Solo Set", "publishedOn": "2001-01-01T00:00:00", "isSupplemental": False}]
    products = {1: [{"productId": 9, "name": "Solo Set Booster Box [Unlimited Edition]", "extendedData": []}]}
    entries, _ = build_entries(groups, products, [], TODAY)
    assert [(e["edition"], e["product_type"]) for e in entries] == [(None, "booster_box")]
    assert product_slug(entries[0]) == "solo-set_booster_box"


def test_single_cards_are_ignored():
    from scripts.build_catalog import build_entries

    groups = [{"groupId": 1, "name": "Solo Set", "publishedOn": "2001-01-01T00:00:00", "isSupplemental": False}]
    products = {
        1: [
            {"productId": 1, "name": "Charizard Booster Box Promo", "extendedData": [{"name": "Number", "value": "4/102"}]},
            {"productId": 2, "name": "Solo Set Booster Pack", "extendedData": []},
        ]
    }
    entries, _ = build_entries(groups, products, [], TODAY)
    assert [_image_id(e) for e in entries] == [2]


def test_a_future_dated_set_is_unverified(built):
    entries, _ = built
    assert all(e["verified"] is False for e in _by_set(entries, "Delta Reign"))
    assert _by_set(entries, "Delta Reign")[0]["release_date"] == "2026-11-06"
    assert all(e["verified"] is True for e in _by_set(entries, "Obsidian Flames"))


def test_curated_sets_are_not_regenerated(built):
    entries, _ = built
    assert _by_set(entries, "Perfect Order") == []
    assert _by_set(entries, "Chaos Rising") == []


def test_promo_and_gallery_groups_produce_nothing(built):
    entries, _ = built
    names = {e["set_name"] for e in entries}
    assert not any("Trick" in n or "Gallery" in n for n in names)


def test_required_keywords_are_normalized_match_phrases(built):
    entries, _ = built

    def required(set_name, ptype):
        return next(e for e in _by_set(entries, set_name) if e["product_type"] == ptype)["required_keywords"]

    assert required("Scarlet & Violet", "booster_box") == ["scarlet violet", "booster box"]
    assert required("Sword & Shield", "etb") == ["sword shield", "elite trainer box"]
    assert required("Scarlet & Violet 151", "booster_bundle") == ["151", "booster bundle"]
    base = {e["edition"]: e["required_keywords"] for e in _by_set(entries, "Base Set") if e["product_type"] == "booster_box"}
    assert base == {
        "1st Edition": ["base set", "booster box", "1st edition"],
        "Shadowless": ["base set", "booster box", "shadowless"],
        "Unlimited": ["base set", "booster box"],
    }


def _excluded(entries, set_name, ptype, edition=None):
    return set(
        next(
            e for e in _by_set(entries, set_name) if e["product_type"] == ptype and e["edition"] == edition
        )["excluded_keywords"]
    )


def test_type_exclusions(built):
    entries, _ = built
    assert {"booster box", "booster bundle", "elite trainer box", "display"} <= _excluded(
        entries, "Obsidian Flames", "booster_pack"
    )
    assert {"booster box", "elite trainer box", "display"} <= _excluded(entries, "Obsidian Flames", "booster_bundle")
    assert {"elite trainer box", "booster bundle"} <= _excluded(entries, "Obsidian Flames", "booster_box")
    assert {"booster box", "booster bundle"} <= _excluded(entries, "Obsidian Flames", "etb")


def test_edition_exclusions(built):
    entries, _ = built
    assert "1st edition" not in _excluded(entries, "Base Set", "booster_box", "1st Edition")
    assert "1st edition" in _excluded(entries, "Base Set", "booster_box", "Shadowless")
    assert {"1st edition", "shadowless"} <= _excluded(entries, "Base Set", "booster_box", "Unlimited")


def test_block_base_sets_exclude_every_other_set(built):
    """"Scarlet & Violet" begins the title of every set in its block, and a
    listing that also names some other set (even a mislabelled one, like
    "Scarlet & Violet - Pitch Black") is not the base set."""
    entries, _ = built
    sv = _excluded(entries, "Scarlet & Violet", "booster_box")
    assert {"obsidian flames", "151", "mega evolution", "delta reign", "xy", "evolutions"} <= sv
    assert "scarlet violet" not in sv
    assert "base set" not in sv  # "Scarlet & Violet Base Set" is the base set's own title

    xy = _excluded(entries, "XY", "booster_box")
    assert {"evolutions", "sun moon", "scarlet violet"} <= xy

    me = _excluded(entries, "Mega Evolution", "booster_box")
    assert {"perfect order", "chaos rising", "delta reign"} <= me  # curated sets count too


def test_ex_prefix_is_dropped_from_the_match_phrase_only():
    from scripts.build_catalog import build_entries

    groups = [{"groupId": 1, "name": "EX Team Rocket Returns", "publishedOn": "2004-11-01T00:00:00", "isSupplemental": False}]
    products = {1: [{"productId": 5, "name": "EX Team Rocket Returns Booster Box", "extendedData": []}]}
    entries, _ = build_entries(groups, products, [], TODAY)
    assert entries[0]["set_name"] == "EX Team Rocket Returns"
    assert entries[0]["required_keywords"] == ["team rocket returns", "booster box"]


def test_a_set_name_inside_another_set_name_is_excluded_even_as_a_plural():
    """"dragon" is inside "dragons exalted" once a plural is tolerated."""
    from scripts.build_catalog import build_entries

    groups = [
        {"groupId": 1, "name": "EX Dragon", "publishedOn": "2003-11-24T00:00:00", "isSupplemental": False},
        {"groupId": 2, "name": "Dragons Exalted", "publishedOn": "2012-08-15T00:00:00", "isSupplemental": False},
    ]
    products = {
        1: [{"productId": 5, "name": "EX Dragon Booster Box", "extendedData": []}],
        2: [{"productId": 6, "name": "Dragons Exalted Booster Box", "extendedData": []}],
    }
    entries, _ = build_entries(groups, products, [], TODAY)
    dragon = next(e for e in entries if e["set_name"] == "EX Dragon")
    assert "dragons exalted" in dragon["excluded_keywords"]


def test_vintage_base_set_excludes_every_block_base_and_base_set_2(built):
    entries, _ = built
    vintage = _excluded(entries, "Base Set", "booster_box", "Unlimited")
    assert {"scarlet violet", "sword shield", "sun moon", "xy", "black white", "mega evolution"} <= vintage
    assert "base set 2" in vintage
    assert "base set" not in vintage


def test_every_entry_is_well_formed(built):
    entries, _ = built
    slugs = [product_slug(e) for e in entries]
    assert len(slugs) == len(set(slugs))
    for e in entries:
        assert e["product_type"] in {"booster_pack", "booster_box", "etb", "booster_bundle"}
        assert e["edition"] in (None, *EDITIONS)
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", e["release_date"])
        assert re.fullmatch(IMAGE.format(id=r"\d+").replace(".", r"\."), e["image_url"])
        assert e["required_keywords"] == [k.lower() for k in e["required_keywords"]]
        assert e["excluded_keywords"] == sorted(set(e["excluded_keywords"]))


def test_render_module_round_trips(built):
    from scripts.build_catalog import render_module

    entries, _ = built
    namespace = {}
    exec(compile(render_module(entries), "catalog_generated.py", "exec"), namespace)
    assert namespace["GENERATED_CATALOG"] == entries


def _synthetic(*names_and_dates):
    groups, products = [], {}
    for i, (name, published, product_name) in enumerate(names_and_dates, start=1):
        groups.append({"groupId": i, "name": name, "publishedOn": f"{published}T00:00:00", "isSupplemental": False})
        products[i] = [{"productId": 100 + i, "name": product_name, "extendedData": []}]
    return groups, products


def test_weak_set_names_exclude_other_sets_but_not_era_names_and_are_not_excluded_back():
    """"arceus" is a card theme as often as a set: it must give way to any
    other set a title names, yet "Sword & Shield" (an era prefix) is no
    reason to reject a real Arceus listing, and strong sets do not exclude
    the weak ones (a Brilliant Stars box can mention Arceus)."""
    from scripts.build_catalog import build_entries

    groups, products = _synthetic(
        ("Arceus", "2009-11-04", "Arceus Booster Box"),
        ("SWSH09: Brilliant Stars", "2022-02-25", "Brilliant Stars Booster Box"),
        ("SWSH01: Sword & Shield Base Set", "2020-02-07", "Sword & Shield Booster Box"),
    )
    entries, _ = build_entries(groups, products, [], TODAY)
    excluded = {e["set_name"]: set(e["excluded_keywords"]) for e in entries}
    assert "brilliant stars" in excluded["Arceus"]
    assert "sword shield" not in excluded["Arceus"]
    assert "arceus" not in excluded["Brilliant Stars"]


def test_evolutions_excludes_mega_evolution():
    """"Mega Evolutions Booster Box" (a plural typo of the base set) must not
    be claimed by the XY-era "Evolutions" set."""
    from scripts.build_catalog import build_entries

    groups, products = _synthetic(
        ("XY - Evolutions", "2016-11-02", "Evolutions Booster Box"),
        ("ME01: Mega Evolution", "2025-09-26", "Mega Evolution Booster Box"),
    )
    entries, _ = build_entries(groups, products, [], TODAY)
    evolutions = next(e for e in entries if e["set_name"] == "Evolutions")
    assert "mega evolution" in evolutions["excluded_keywords"]


def test_products_the_generator_leaves_out_are_also_excluded_from_matching(built):
    entries, _ = built
    common = {"pokemon center", "pokemon centre", "code card", "case of", "full case"}
    for ptype in ("booster_box", "booster_pack", "booster_bundle", "etb"):
        assert common <= _excluded(entries, "Obsidian Flames", ptype), ptype
    assert {"half booster box", "enhanced booster box", "booster box case"} <= _excluded(
        entries, "Obsidian Flames", "booster_box"
    )
    assert "elite trainer box case" in _excluded(entries, "Obsidian Flames", "etb")
    assert "booster bundle case" in _excluded(entries, "Obsidian Flames", "booster_bundle")


def test_mega_evolution_does_not_exclude_the_evolutions_set_name():
    """"Mega Evolutions Booster Box" contains "evolutions" only because it is a
    plural typo of the base set's own name."""
    from scripts.build_catalog import build_entries

    groups, products = _synthetic(
        ("XY - Evolutions", "2016-11-02", "Evolutions Booster Box"),
        ("ME01: Mega Evolution", "2025-09-26", "Mega Evolution Booster Box"),
    )
    entries, _ = build_entries(groups, products, [], TODAY)
    mega = next(e for e in entries if e["set_name"] == "Mega Evolution")
    assert "evolutions" not in mega["excluded_keywords"]


def test_vintage_team_rocket_excludes_modern_team_rocket_products():
    """"Team Rocket" is also the theme of 2024-26 products (Moltres ex, Glory of
    Team Rocket, Ultra Premium Collection)."""
    from scripts.build_catalog import build_entries

    groups, products = _synthetic(("Team Rocket", "2000-04-24", "Team Rocket Booster Box [Unlimited Edition]"))
    entries, _ = build_entries(groups, products, [], TODAY)
    excluded = set(entries[0]["excluded_keywords"])
    assert {"moltres", "glory of", "upc", "ultra premium", "burning sparks"} <= excluded
