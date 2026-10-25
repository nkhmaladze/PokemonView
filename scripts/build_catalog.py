"""Build the generated part of the catalog from TCGplayer's product lists.

Reads the public TCGplayer mirror at tcgcsv.com (category 3 = Pokemon: one
"group" per set, each with its products) and writes
`scripts/catalog_generated.py`, the `GENERATED_CATALOG` list that
`scripts/catalog_data.py` appends to the hand-curated entries.

Why this source: a product's id, name and image all come from the same
record, so an entry's `image_url` can never point at a different product
than the one named. The curated sets are skipped (their msrp, keywords and
`verified` flags are hand-maintained), unknown MSRP stays `None`, and only
the four product types the site tracks are produced: booster pack, booster
box, ETB and booster bundle. Wizards-era products carry an `edition`
(1st Edition / Shadowless / Unlimited).

Run from the repo root (network only for --fetch):

    python -m scripts.build_catalog --cache <dir> [--fetch] [--out PATH]

`<dir>` holds `groups.json` and `products/<groupId>.json`. Everything but
`fetch_cache` is a pure function (the tests drive them from fixtures), and
nothing here runs on import, and nothing in the running app imports this
module.
"""

import argparse
import json
import re
import sys
import time
import urllib.request
from datetime import date
from pathlib import Path
from pprint import pformat

from scripts.matching import _contains, normalize

BASE_URL = "https://tcgcsv.com/tcgplayer/3"
# tcgcsv rejects Python's default User-Agent.
USER_AGENT = {"User-Agent": "Mozilla/5.0 PokemonView-catalog-build"}
IMAGE_URL = "https://tcgplayer-cdn.tcgplayer.com/product/{id}_in_1000x1000.jpg"

TYPE_LABELS = {
    "booster_box": "Booster Box",
    "etb": "Elite Trainer Box",
    "booster_bundle": "Booster Bundle",
    "booster_pack": "Booster Pack",
}
TYPE_KEYWORDS = {
    "booster_box": "booster box",
    "etb": "elite trainer box",
    "booster_bundle": "booster bundle",
    "booster_pack": "booster pack",
}
# Order matters: "Booster Bundle Box"-style names must reach the bundle rule.
_TYPE_PATTERNS = [
    ("booster_box", re.compile(r"\bbooster box\b", re.I)),
    ("booster_bundle", re.compile(r"\bbooster bundle\b", re.I)),
    ("etb", re.compile(r"\belite trainer box\b", re.I)),
    ("booster_pack", re.compile(r"\bbooster pack\b", re.I)),
]

# Products that mention a main type but are not the standard retail product:
# cases, displays, store exclusives, art bundles, half/enhanced boxes ...
# Checked on the product name with the set's own name removed, so a set
# called "Legendary Collection" is not rejected for containing "collection".
_DENY = re.compile(
    r"\b(?:cases?|displays?|sleeved|code card|pok[eé]mon center|blisters?|art bundle|"
    r"theme decks?|tins?|collections?|build|decks?|set of|premium|plus|special|mini|"
    r"exclusive|starter|lot|stadium|half|enhanced|3-card|surprise|sam'?s club)\b",
    re.I,
)

_TAG_1ST = re.compile(r"\[\s*1st edition\s*\]", re.I)
_TAG_UNLIMITED = re.compile(r"\[\s*(?:revised\s+)?unlimited edition\s*\]", re.I)
_TAG_SHADOWLESS = re.compile(r"\(\s*shadowless\s*\)", re.I)

# Groups that are not retail set expansions (promos, kits, restocks,
# subsets of another set ...). Products inside them are never considered.
_EXCLUDED_GROUP = re.compile(
    r"promo|trainer kit|training kit|mcdonald|pop series|trick or trade|battle academy|"
    r"countdown|deck kit|jumbo|world championship|league|prize pack|exclusives|"
    r"first partner|player placement|alternate art|burger king|miscellaneous|"
    r"pikachu world|professor program|classic|energies|sample|best of|trainer gallery|"
    r"shiny vault|radiant collection|galarian gallery|nintendo",
    re.I,
)

_CODE_PREFIX = re.compile(r"^(?:[A-Z]{1,5}\d{0,3}:\s*|[A-Z]{2,4}\s-\s)")
BLOCK_RENAMES = {"SM": "Sun & Moon"}

# Per-group exceptions, keyed by TCGplayer groupId.
OVERRIDES = {
    # Listings call it "Pokemon 151 ..." far more often than "Scarlet & Violet 151".
    23237: {"set_name": "Scarlet & Violet 151", "match_phrase": "151"},
}

# Sets whose name is also used as a prefix by every set of their era
# ("Sword & Shield Rebel Clash ..."); see compute_excluded_keywords.
BLOCK_BASE_NAMES = [
    "Diamond & Pearl",
    "Platinum",
    "HeartGold SoulSilver",
    "Black & White",
    "XY",
    "Sun & Moon",
    "Sword & Shield",
    "Scarlet & Violet",
    "Mega Evolution",
]

# Titles of products the generator deliberately does not catalog (store
# exclusives, cases, half/enhanced boxes, code cards) must not price into the
# standard entry either. "sealed" is stripped by normalize(), so a "sealed
# case" listing reads "... booster box case".
_COMMON_EXCLUSIONS = ["pokemon center", "pokemon centre", "code card", "case of", "full case"]
TYPE_EXCLUSIONS = {
    "booster_pack": ["booster box", "booster bundle", "elite trainer box", "display", *_COMMON_EXCLUSIONS],
    "booster_bundle": ["booster box", "elite trainer box", "display", "booster bundle case", *_COMMON_EXCLUSIONS],
    "booster_box": [
        "elite trainer box",
        "booster bundle",
        "half booster box",
        "enhanced booster box",
        "booster box case",
        *_COMMON_EXCLUSIONS,
    ],
    "etb": ["booster box", "booster bundle", "elite trainer box case", *_COMMON_EXCLUSIONS],
}

# Set names that are also card themes or ordinary words: a title naming any
# real set ("Brilliant Stars Booster Box Arceus VSTAR") is that set's, so
# these exclude every other non-era set's phrase. They are not excluded back:
# a Brilliant Stars box can mention Arceus.
WEAK_PHRASES = {
    "team rocket",
    "arceus",
    "deoxys",
    "dragon",
    "emerald",
    "team up",
    "evolutions",
    "generations",
    "celebrations",
    "fossil",
    "jungle",
    "expedition",
}
# "Mega Evolutions" is a plural typo of the base set but contains "evolutions".
EXTRA_EXCLUSIONS = {"evolutions": ["mega evolution"]}
# ... and the base set must not exclude "evolutions" back, for the same reason.
NEVER_EXCLUDE = {"mega evolution": {"evolutions"}}
EDITION_RANK = {"1st Edition": 0, "Shadowless": 1, "Unlimited": 2, None: 3}
EDITION_DISPLAY = {
    "1st Edition": " (1st Edition)",
    "Shadowless": " (Shadowless Unlimited)",
    "Unlimited": " (Unlimited)",
    None: "",
}


def classify_product(name: str, set_name: str):
    """Return (product_type, edition_tag) for a standard retail product, or
    None. `edition_tag` is "1st Edition", "Shadowless", "Unlimited" or None,
    read from the "[1st Edition]" / "(Shadowless)" / "[Unlimited Edition]"
    markers in the name."""
    text = re.sub(re.escape(set_name), " ", name, flags=re.I)
    if _TAG_1ST.search(text):
        tag = "1st Edition"
    elif _TAG_SHADOWLESS.search(text):
        tag = "Shadowless"
    elif _TAG_UNLIMITED.search(text):
        tag = "Unlimited"
    else:
        tag = None
    for rx in (_TAG_1ST, _TAG_SHADOWLESS, _TAG_UNLIMITED):
        text = rx.sub(" ", text)
    if _DENY.search(text):
        return None
    for product_type, rx in _TYPE_PATTERNS:
        if rx.search(text):
            return product_type, tag
    return None


def clean_set_name(group_name: str) -> str:
    """The name sellers use: "SWSH01: Sword & Shield Base Set" -> "Sword &
    Shield", "XY - Flashfire" -> "Flashfire", "Black and White" -> "Black &
    White"."""
    name = _CODE_PREFIX.sub("", group_name)
    name = re.sub(r"\s*\(\s*shadowless\s*\)", "", name, flags=re.I)
    name = re.sub(r"\s+and\s+", " & ", name)
    if name != "Base Set" and name.endswith(" Base Set"):
        name = name[: -len(" Base Set")]
    return BLOCK_RENAMES.get(name, name).strip()


def _set_name(group: dict) -> str:
    override = OVERRIDES.get(group["groupId"], {})
    return override.get("set_name") or clean_set_name(group["name"])


def _match_phrase(group: dict, set_name: str) -> str:
    """What a listing title must contain: the normalized set name. The
    "EX " series prefix is dropped ("EX Team Rocket Returns" is listed as
    "Team Rocket Returns" as often as with the EX)."""
    override = OVERRIDES.get(group["groupId"], {}).get("match_phrase")
    if override:
        return override
    phrase = normalize(set_name)
    return phrase[3:] if phrase.startswith("ex ") else phrase


def _is_candidate_group(group: dict) -> bool:
    return not group.get("isSupplemental") and not _EXCLUDED_GROUP.search(group["name"])


def _is_card(row: dict) -> bool:
    return any(item.get("name") == "Number" for item in row.get("extendedData", []))


def _pick(rows):
    """Choose one product among same-(set, edition, type) variants: ETB
    colour/Pokemon variants, LGS vs Retail bundles. Prefer "(Retail)", else
    the lowest productId."""
    retail = [r for r in rows if "(retail)" in r["name"].lower()]
    return min(retail or rows, key=lambda r: r["productId"])


def build_entries(groups, products_by_group, curated, today: date):
    """Return (entries, report). See the module docstring for the rules.

    report["collapsed"]: variants merged into one entry (kept/dropped names);
    report["unresolved"]: candidate groups that yielded no entry;
    report["skipped_curated"]: sets left to the hand-curated entries.
    """
    curated_sets = {entry["set_name"] for entry in curated}
    report = {"collapsed": [], "unresolved": [], "skipped_curated": []}
    found = {}  # (set_name, tag, product_type) -> list[row]
    meta = {}  # set_name -> (release_date, match_phrase)

    for group in sorted(groups, key=lambda g: (g["publishedOn"], g["groupId"])):
        if not _is_candidate_group(group):
            continue
        set_name = _set_name(group)
        if set_name in curated_sets:
            report["skipped_curated"].append(set_name)
            continue
        any_found = False
        for row in products_by_group.get(group["groupId"], []):
            if _is_card(row):
                continue
            classified = classify_product(row["name"], set_name)
            if classified is None:
                continue
            product_type, tag = classified
            found.setdefault((set_name, tag, product_type), []).append(row)
            any_found = True
        if any_found:
            meta.setdefault(
                set_name, (group["publishedOn"][:10], _match_phrase(group, set_name))
            )
        else:
            report["unresolved"].append(group["name"])

    tags_by_set = {}
    for set_name, tag, _ in found:
        tags_by_set.setdefault(set_name, set()).add(tag)

    merged = {}  # (set_name, edition, product_type) -> list[row]
    for (set_name, tag, product_type), rows in found.items():
        # A set only has editions when TCGplayer lists more than one.
        edition = tag if len(tags_by_set[set_name]) > 1 else None
        merged.setdefault((set_name, edition, product_type), []).extend(rows)

    entries = []
    for (set_name, edition, product_type), rows in merged.items():
        chosen = _pick(rows)
        if len(rows) > 1:
            dropped = sorted((r for r in rows if r is not chosen), key=lambda r: r["productId"])
            report["collapsed"].append(
                {
                    "set_name": set_name,
                    "product_type": product_type,
                    "edition": edition,
                    "kept": chosen["name"],
                    "dropped": [r["name"] for r in dropped],
                }
            )
        release_date, phrase = meta[set_name]
        required = [phrase, TYPE_KEYWORDS[product_type]]
        if edition == "1st Edition":
            required.append("1st edition")
        elif edition == "Shadowless":
            required.append("shadowless")
        entries.append(
            {
                "set_name": set_name,
                "product_type": product_type,
                "edition": edition,
                "language": "en",
                "release_date": release_date,
                "msrp": None,
                "image_url": IMAGE_URL.format(id=chosen["productId"]),
                "display_name": f"{set_name} {TYPE_LABELS[product_type]}{EDITION_DISPLAY[edition]}",
                "required_keywords": required,
                "excluded_keywords": [],
                "verified": date.fromisoformat(release_date) <= today,
                "verified_at": None,
            }
        )

    entries.sort(
        key=lambda e: (
            e["release_date"],
            e["set_name"],
            EDITION_RANK[e["edition"]],
            list(TYPE_LABELS).index(e["product_type"]),
        )
    )
    compute_excluded_keywords(entries, curated)
    report["collapsed"].sort(key=lambda c: (c["set_name"], c["product_type"]))
    return entries, report


def compute_excluded_keywords(entries, curated=()) -> None:
    """Fill each generated entry's `excluded_keywords` in place.

    Rules, all about titles that mention a *different* product:
    - type: a pack listing that says "booster box" is not the pack, etc.;
    - name inside another set's name: "base set" must not claim a "base set
      2" title, "dragon" not "dragons exalted" (same whole-word-plus-plural
      test the matcher uses);
    - block bases: "Sword & Shield" begins the title of every set of its
      era, so a title that also names any other set is not the base set
      (curated sets count too) — except "base set", which is the base set's
      own title ("Sword & Shield Base Set");
    - vintage "Base Set" is also the tail of "Scarlet & Violet Base Set",
      so it excludes every block base's phrase;
    - weak set names (WEAK_PHRASES) give way to any other non-era set a
      title names;
    - editions: Shadowless excludes "1st edition"; Unlimited excludes both,
      because sellers rarely write "unlimited".
    By convention `required_keywords[0]` is the set's match phrase.
    """
    sets = {}  # set_name -> (match_phrase, earliest release_date)
    for entry in [*curated, *entries]:
        name, phrase, released = entry["set_name"], entry["required_keywords"][0], entry["release_date"]
        if name not in sets or released < sets[name][1]:
            sets[name] = (phrase, released)

    base_phrases = {sets[name][0] for name in BLOCK_BASE_NAMES if name in sets}

    for entry in entries:
        name = entry["set_name"]
        phrase = sets[name][0]
        excluded = set(TYPE_EXCLUSIONS[entry["product_type"]])
        for other, (other_phrase, _released) in sets.items():
            if other == name:
                continue
            if _contains(other_phrase, phrase):
                excluded.add(other_phrase)
            if (
                name in BLOCK_BASE_NAMES
                and other_phrase != "base set"
                and other_phrase not in NEVER_EXCLUDE.get(phrase, ())
            ):
                excluded.add(other_phrase)
        if phrase in WEAK_PHRASES:
            for other, (other_phrase, _released) in sets.items():
                if other != name and other_phrase not in base_phrases and not _contains(phrase, other_phrase):
                    excluded.add(other_phrase)
        excluded |= set(EXTRA_EXCLUSIONS.get(phrase, []))
        if name == "Base Set":
            excluded |= base_phrases
        if entry["edition"] == "Shadowless":
            excluded.add("1st edition")
        elif entry["edition"] == "Unlimited":
            excluded |= {"1st edition", "shadowless"}
        entry["excluded_keywords"] = sorted(excluded)


def render_module(entries) -> str:
    """Source text of scripts/catalog_generated.py."""
    header = (
        '"""GENERATED by scripts/build_catalog.py from TCGplayer product lists\n'
        "(tcgcsv.com). Do not edit by hand: fix the generator or its OVERRIDES and\n"
        "re-run `python -m scripts.build_catalog --cache <dir> --fetch`.\n"
        '"""\n\n'
        "GENERATED_CATALOG = "
    )
    return header + pformat(entries, width=100, sort_dicts=False) + "\n"


def _get(url: str) -> bytes:
    request = urllib.request.Request(url, headers=USER_AGENT)
    return urllib.request.urlopen(request, timeout=60).read()


def fetch_cache(cache_dir: Path) -> None:
    """Download groups.json and products/<groupId>.json into `cache_dir`
    (skipping files already there), 0.2 s apart to stay polite."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    (cache_dir / "products").mkdir(exist_ok=True)
    groups_path = cache_dir / "groups.json"
    if not groups_path.exists():
        groups_path.write_bytes(_get(f"{BASE_URL}/groups"))
    for group in json.loads(groups_path.read_text())["results"]:
        path = cache_dir / "products" / f"{group['groupId']}.json"
        if path.exists():
            continue
        path.write_bytes(_get(f"{BASE_URL}/{group['groupId']}/products"))
        time.sleep(0.2)


def load_cache(cache_dir: Path):
    groups = json.loads((cache_dir / "groups.json").read_text())["results"]
    products = {}
    for group in groups:
        path = cache_dir / "products" / f"{group['groupId']}.json"
        if path.exists():
            products[group["groupId"]] = json.loads(path.read_text())["results"]
    return groups, products


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--cache", type=Path, required=True)
    parser.add_argument("--fetch", action="store_true", help="download missing files first")
    parser.add_argument("--out", type=Path, default=Path("scripts/catalog_generated.py"))
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    args = parser.parse_args(argv)

    from scripts.catalog_data import CURATED_CATALOG

    if args.fetch:
        fetch_cache(args.cache)
    groups, products = load_cache(args.cache)
    entries, report = build_entries(groups, products, CURATED_CATALOG, args.today)
    args.out.write_text(render_module(entries))

    by_type = {}
    for entry in entries:
        by_type[entry["product_type"]] = by_type.get(entry["product_type"], 0) + 1
    print(f"wrote {len(entries)} entries to {args.out}: {by_type}")
    print(f"collapsed variants: {len(report['collapsed'])}")
    print(f"candidate groups with no entry: {report['unresolved']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
