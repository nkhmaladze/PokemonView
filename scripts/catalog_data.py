"""Curated v1 sealed-product catalog for PokemonView (CATALOG-01, CATALOG-02).

Holds every in-scope standard-retail sealed product across the 4 sets
selected for v1 (D-01): Chaos Rising (ME04), Perfect Order (ME03),
Ascended Heroes, and Pitch Black (ME05). Each entry is a plain dict
describing one distinct (set, product_type) combination — up to 4
product types per set: booster_pack, booster_box, etb, booster_bundle
(D-06 introduces booster_bundle as a distinct type from box/pack).

Fields per entry (CATALOG-02):
    set_name          str  -- e.g. "Perfect Order"
    product_type      str  -- one of booster_pack | booster_box | etb |
                              booster_bundle
    language          str  -- always "en" (v1 is English-only)
    release_date      str | None  -- ISO "YYYY-MM-DD"; the seed script
                              converts this to a datetime at insert time
    msrp              float | None
    image_url         str | None  -- TCGplayer CDN URL
                              (https://tcgplayer-cdn.tcgplayer.com/product/
                              {id}_in_1000x1000.jpg), per D-07/D-08
    display_name      str
    required_keywords list[str]  -- lowercase, disambiguated per product
                              type (see Pitfall 4 in 02-RESEARCH.md) so
                              Phase 4's matching never confuses a
                              booster_bundle listing with a booster_box
                              or booster_pack listing for the same set
    verified          bool -- False for Pitch Black (D-02: pre-release
                              data, not yet confirmed against the actual
                              2026-07-17 retail release), True otherwise
    verified_at       None -- reserved for a future post-release
                              verification pass on Pitch Black (D-02)

This module holds ONLY data: no MongoDB/pymongo imports, no network
calls, no top-level side effects on import (mirrors the "no top-level
side effects on import" convention already established in
scripts/ebay_client.py). scripts/seed_catalog.py (a later plan) is the
only intended writer of this data into MongoDB.

Sourcing notes (Task 1 research, 2026-07-13):
- Chaos Rising booster_box MSRP was flagged as conflicting ($144 vs
  $161.64) in 02-RESEARCH.md Open Question 1. Confirmed via the
  Pokémon Center product listing snippet ("Mega Evolution-Chaos Rising
  Booster Display Box (36 Packs) $161.64") -- resolved to $161.64,
  matching the sibling sets' 36-pack box price.
- Ascended Heroes' standard (non-Pokemon-Center-exclusive) booster box
  was flagged as possibly not existing (Assumption A2). Confirmed to
  exist via independent eBay/TCGplayer listings and a dedicated
  "Ascended Heroes ETB & Booster Box Price: Restock Tracker" tracking
  article -- the entry is kept, with MSRP pattern-matched to $161.64
  (consistent with Perfect Order/Chaos Rising/Pitch Black's cited
  36-pack box price; not independently re-cited at the exact dollar
  figure, so treat as MEDIUM rather than HIGH confidence).
- Ascended Heroes' standard Elite Trainer Box (Target/Walmart) was
  separately confirmed distinct from the Pokemon Center-exclusive
  11-pack ETB variant (which is correctly excluded per D-05).
- Of the ~12 TCGplayer product IDs 02-RESEARCH.md left unresolved,
  none could be confidently confirmed in this pass (TCGplayer's
  product pages are client-side rendered and returned no parseable
  product ID from a plain HTTP fetch; search-engine access was rate
  limited before all products could be checked via result snippets).
  Per the plan's explicit instruction, these image_url fields are set
  to None rather than fabricated -- only the 4 IDs already confirmed
  in 02-RESEARCH.md are populated. Resolving the rest is carried
  forward as a follow-up (see 02-03-SUMMARY.md).
"""

CATALOG = [
    # -- Chaos Rising (ME04) - released 2026-05-22 --
    {
        "set_name": "Chaos Rising",
        "product_type": "etb",
        "language": "en",
        "release_date": "2026-05-22",
        "msrp": 49.99,
        "image_url": "https://tcgplayer-cdn.tcgplayer.com/product/684450_in_1000x1000.jpg",
        "display_name": "Pokemon TCG: Mega Evolution-Chaos Rising Elite Trainer Box",
        "required_keywords": ["chaos rising", "elite trainer box", "etb"],
        "verified": True,
        "verified_at": None,
    },
    {
        "set_name": "Chaos Rising",
        "product_type": "booster_box",
        "language": "en",
        "release_date": "2026-05-22",
        "msrp": 161.64,
        "image_url": None,
        "display_name": "Pokemon TCG: Mega Evolution-Chaos Rising Booster Display Box (36 Packs)",
        "required_keywords": ["chaos rising", "booster box", "display"],
        "verified": True,
        "verified_at": None,
    },
    {
        "set_name": "Chaos Rising",
        "product_type": "booster_bundle",
        "language": "en",
        "release_date": "2026-05-22",
        "msrp": 26.94,
        "image_url": None,
        "display_name": "Pokemon TCG: Mega Evolution-Chaos Rising Booster Bundle (6 Packs)",
        "required_keywords": ["chaos rising", "booster bundle", "bundle"],
        "verified": True,
        "verified_at": None,
    },
    {
        "set_name": "Chaos Rising",
        "product_type": "booster_pack",
        "language": "en",
        "release_date": "2026-05-22",
        "msrp": 4.49,
        "image_url": None,
        "display_name": "Pokemon TCG: Mega Evolution-Chaos Rising Booster Pack",
        "required_keywords": ["chaos rising", "booster pack"],
        "verified": True,
        "verified_at": None,
    },
    # -- Perfect Order (ME03) - released 2026-03-27 --
    {
        "set_name": "Perfect Order",
        "product_type": "etb",
        "language": "en",
        "release_date": "2026-03-27",
        "msrp": 49.99,
        "image_url": None,
        "display_name": "Pokemon TCG: Mega Evolution-Perfect Order Elite Trainer Box",
        "required_keywords": ["perfect order", "elite trainer box", "etb"],
        "verified": True,
        "verified_at": None,
    },
    {
        "set_name": "Perfect Order",
        "product_type": "booster_box",
        "language": "en",
        "release_date": "2026-03-27",
        "msrp": 161.64,
        "image_url": "https://tcgplayer-cdn.tcgplayer.com/product/672394_in_1000x1000.jpg",
        "display_name": "Pokemon TCG: Mega Evolution-Perfect Order Booster Display Box (36 Packs)",
        "required_keywords": ["perfect order", "booster box", "display"],
        "verified": True,
        "verified_at": None,
    },
    {
        "set_name": "Perfect Order",
        "product_type": "booster_bundle",
        "language": "en",
        "release_date": "2026-03-27",
        "msrp": 26.94,
        "image_url": None,
        "display_name": "Pokemon TCG: Mega Evolution-Perfect Order Booster Bundle (6 Packs)",
        "required_keywords": ["perfect order", "booster bundle", "bundle"],
        "verified": True,
        "verified_at": None,
    },
    {
        "set_name": "Perfect Order",
        "product_type": "booster_pack",
        "language": "en",
        "release_date": "2026-03-27",
        "msrp": 4.49,
        "image_url": "https://tcgplayer-cdn.tcgplayer.com/product/672398_in_1000x1000.jpg",
        "display_name": "Pokemon TCG: Mega Evolution-Perfect Order Booster Pack",
        "required_keywords": ["perfect order", "booster pack"],
        "verified": True,
        "verified_at": None,
    },
    # -- Ascended Heroes - set release 2026-01-30; ETB/bundle have their
    # own later release dates confirmed in 02-RESEARCH.md --
    {
        "set_name": "Ascended Heroes",
        "product_type": "etb",
        "language": "en",
        "release_date": "2026-02-20",
        "msrp": 49.99,
        "image_url": None,
        "display_name": "Pokemon TCG: Mega Evolution-Ascended Heroes Elite Trainer Box",
        "required_keywords": ["ascended heroes", "elite trainer box", "etb"],
        "verified": True,
        "verified_at": None,
    },
    {
        "set_name": "Ascended Heroes",
        "product_type": "booster_box",
        "language": "en",
        "release_date": "2026-01-30",
        "msrp": 161.64,
        "image_url": None,
        "display_name": "Pokemon TCG: Mega Evolution-Ascended Heroes Booster Display Box (36 Packs)",
        "required_keywords": ["ascended heroes", "booster box", "display"],
        "verified": True,
        "verified_at": None,
    },
    {
        "set_name": "Ascended Heroes",
        "product_type": "booster_bundle",
        "language": "en",
        "release_date": "2026-04-24",
        "msrp": 26.94,
        "image_url": "https://tcgplayer-cdn.tcgplayer.com/product/668541_in_1000x1000.jpg",
        "display_name": "Pokemon TCG: Mega Evolution-Ascended Heroes Booster Bundle (6 Packs)",
        "required_keywords": ["ascended heroes", "booster bundle", "bundle"],
        "verified": True,
        "verified_at": None,
    },
    {
        "set_name": "Ascended Heroes",
        "product_type": "booster_pack",
        "language": "en",
        "release_date": "2026-01-30",
        "msrp": 4.49,
        "image_url": None,
        "display_name": "Pokemon TCG: Mega Evolution-Ascended Heroes Booster Pack",
        "required_keywords": ["ascended heroes", "booster pack"],
        "verified": True,
        "verified_at": None,
    },
    # -- Pitch Black (ME05) - pre-release as of seeding date; releases
    # 2026-07-17. All entries carry verified=False per D-02 until a
    # post-release verification pass confirms actual retail data. --
    {
        "set_name": "Pitch Black",
        "product_type": "etb",
        "language": "en",
        "release_date": "2026-07-17",
        "msrp": 49.99,
        "image_url": None,
        "display_name": "Pokemon TCG: Mega Evolution-Pitch Black Elite Trainer Box",
        "required_keywords": ["pitch black", "elite trainer box", "etb"],
        "verified": False,
        "verified_at": None,
    },
    {
        "set_name": "Pitch Black",
        "product_type": "booster_box",
        "language": "en",
        "release_date": "2026-07-17",
        "msrp": 161.64,
        "image_url": None,
        "display_name": "Pokemon TCG: Mega Evolution-Pitch Black Booster Display Box (36 Packs)",
        "required_keywords": ["pitch black", "booster box", "display"],
        "verified": False,
        "verified_at": None,
    },
    {
        "set_name": "Pitch Black",
        "product_type": "booster_bundle",
        "language": "en",
        "release_date": "2026-07-17",
        "msrp": 26.94,
        "image_url": None,
        "display_name": "Pokemon TCG: Mega Evolution-Pitch Black Booster Bundle (6 Packs)",
        "required_keywords": ["pitch black", "booster bundle", "bundle"],
        "verified": False,
        "verified_at": None,
    },
    {
        "set_name": "Pitch Black",
        "product_type": "booster_pack",
        "language": "en",
        "release_date": "2026-07-17",
        "msrp": 4.49,
        "image_url": None,
        "display_name": "Pokemon TCG: Mega Evolution-Pitch Black Booster Pack",
        "required_keywords": ["pitch black", "booster pack"],
        "verified": False,
        "verified_at": None,
    },
]
