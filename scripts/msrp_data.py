"""Launch-era US retail MSRPs (USD) for the generated catalog products.

`MSRP_BY_PRODUCT` maps a product slug (`scripts.catalog_slug.product_slug`,
the same id the API and the product page use) to the price the standard
English retail product launched at. `scripts.catalog_data` applies it on top
of `GENERATED_CATALOG`, so regenerating that file with `scripts.build_catalog`
never loses these values. The hand-curated entries keep their own MSRPs.

What goes in: only a price a launch-era source states for that exact product
(trade press such as ICv2, Pokemon Center listings, distributor catalogs,
retailer launch posts) with no credible source disagreeing. What stays out,
so the product page hides its MSRP line instead of showing a guess:
- any set before XY (2014-02): launch prices are not reliably documented;
- products with no standalone retail version (for example single packs of
  Hidden Fates, Shining Fates, Celebrations, Pokemon GO, Crown Zenith, 151);
- prices that sources disagree on: Sword & Shield Elite Trainer Boxes
  ($39.99 vs $49.99), early Scarlet & Violet Booster Bundles ($26.94 vs
  $26.99), and a few single-source or derived figures;
- Pokemon Center exclusives and anything after launch (markups, resale).

Researched 2026-11-12. Each row ends with the sources it rests on. To add a
value, find a launch-era source that states the price, then add the slug here;
`tests/test_msrp_data.py` checks the key exists, the value is plausible for its
type, and a box is 36 packs and a bundle 6 packs wherever both are known.
"""

MSRP_BY_PRODUCT = {
    # --- XY ---
    "xy_etb": 39.99,  # XY, etb; icv2.com
    "flashfire_booster_pack": 3.99,  # Flashfire, booster pack; icv2.com
    "furious-fists_booster_box": 143.64,  # Furious Fists, booster box; pocketmonsters.net
    "furious-fists_booster_pack": 3.99,  # Furious Fists, booster pack; icv2.com, pocketmonsters.net
    "phantom-forces_booster_pack": 3.99,  # Phantom Forces, booster pack; icv2.com
    "ancient-origins_booster_box": 143.64,  # Ancient Origins, booster box; pocketmonsters.net
    "ancient-origins_etb": 39.99,  # Ancient Origins, etb; pocketmonsters.net
    "ancient-origins_booster_pack": 3.99,  # Ancient Origins, booster pack; pocketmonsters.net
    "breakthrough_etb": 39.99,  # BREAKthrough, etb; icv2.com
    "breakthrough_booster_pack": 3.99,  # BREAKthrough, booster pack; icv2.com
    "breakpoint_etb": 39.99,  # BREAKpoint, etb; icv2.com
    "breakpoint_booster_pack": 3.99,  # BREAKpoint, booster pack; icv2.com
    "generations_etb": 49.99,  # Generations, etb; icv2.com, nintendowire.com
    "fates-collide_etb": 39.99,  # Fates Collide, etb; icv2.com
    "fates-collide_booster_pack": 3.99,  # Fates Collide, booster pack; icv2.com

    # --- Sun & Moon ---
    "sun-and-moon_etb": 39.99,  # Sun & Moon, etb; pokemoncenter.com
    "sun-and-moon_booster_pack": 3.99,  # Sun & Moon, booster pack; pokemoncenter.com
    "guardians-rising_booster_box": 143.64,  # Guardians Rising, booster box; pokemoncenter.com
    "guardians-rising_etb": 39.99,  # Guardians Rising, etb; pokemoncenter.com
    "guardians-rising_booster_pack": 3.99,  # Guardians Rising, booster pack; pokemoncenter.com
    "burning-shadows_booster_box": 143.64,  # Burning Shadows, booster box; pokemoncenter.com
    "burning-shadows_etb": 39.99,  # Burning Shadows, etb; pokemoncenter.com
    "burning-shadows_booster_pack": 3.99,  # Burning Shadows, booster pack; pokemoncenter.com
    "shining-legends_etb": 49.99,  # Shining Legends, etb; elitefourum.com, icv2.com, pokemoncenter.com
    "crimson-invasion_booster_box": 143.64,  # Crimson Invasion, booster box; pokemoncenter.com
    "crimson-invasion_etb": 39.99,  # Crimson Invasion, etb; pokemoncenter.com
    "crimson-invasion_booster_pack": 3.99,  # Crimson Invasion, booster pack; pokemoncenter.com
    "ultra-prism_booster_box": 143.64,  # Ultra Prism, booster box; pokemoncenter.com
    "ultra-prism_etb": 39.99,  # Ultra Prism, etb; pokemoncenter.com
    "ultra-prism_booster_pack": 3.99,  # Ultra Prism, booster pack; pokemoncenter.com
    "forbidden-light_booster_box": 143.64,  # Forbidden Light, booster box; pokemoncenter.com
    "forbidden-light_etb": 39.99,  # Forbidden Light, etb; pokemoncenter.com
    "forbidden-light_booster_pack": 3.99,  # Forbidden Light, booster pack; pokemoncenter.com
    "celestial-storm_booster_box": 143.64,  # Celestial Storm, booster box; pokemoncenter.com
    "celestial-storm_etb": 39.99,  # Celestial Storm, etb; pokemoncenter.com
    "celestial-storm_booster_pack": 3.99,  # Celestial Storm, booster pack; pokemoncenter.com
    "lost-thunder_booster_box": 143.64,  # Lost Thunder, booster box; pokemoncenter.com
    "lost-thunder_etb": 39.99,  # Lost Thunder, etb; pokemoncenter.com
    "lost-thunder_booster_pack": 3.99,  # Lost Thunder, booster pack; pokemoncenter.com
    "team-up_booster_box": 143.64,  # Team Up, booster box; pokemoncenter.com
    "team-up_etb": 39.99,  # Team Up, etb; pokemoncenter.com
    "team-up_booster_pack": 3.99,  # Team Up, booster pack; pokemoncenter.com
    "unbroken-bonds_booster_box": 143.64,  # Unbroken Bonds, booster box; pokemoncenter.com
    "unbroken-bonds_etb": 39.99,  # Unbroken Bonds, etb; icv2.com, pokemoncenter.com
    "unbroken-bonds_booster_pack": 3.99,  # Unbroken Bonds, booster pack; icv2.com, pokemoncenter.com
    "unified-minds_booster_box": 143.64,  # Unified Minds, booster box; pokemoncenter.com
    "unified-minds_etb": 39.99,  # Unified Minds, etb; honesty-gaming.com, pokemoncenter.com
    "unified-minds_booster_pack": 3.99,  # Unified Minds, booster pack; pokemoncenter.com
    "hidden-fates_etb": 49.99,  # Hidden Fates, etb; icv2.com, pokemoncenter.com
    "cosmic-eclipse_booster_box": 143.64,  # Cosmic Eclipse, booster box; pokemoncenter.com
    "cosmic-eclipse_etb": 39.99,  # Cosmic Eclipse, etb; pokemoncenter.com
    "cosmic-eclipse_booster_pack": 3.99,  # Cosmic Eclipse, booster pack; pokemoncenter.com

    # --- Sword & Shield ---
    "darkness-ablaze_booster_pack": 3.99,  # Darkness Ablaze, booster pack; marriland.com
    "champions-path_etb": 49.99,  # Champion's Path, etb; pokeguardian.com
    "vivid-voltage_booster_pack": 3.99,  # Vivid Voltage, booster pack; marriland.com
    "shining-fates_etb": 49.99,  # Shining Fates, etb; marriland.com, pokeguardian.com
    "battle-styles_booster_pack": 3.99,  # Battle Styles, booster pack; pokeguardian.com
    "chilling-reign_booster_pack": 3.99,  # Chilling Reign, booster pack; pokeguardian.com
    "evolving-skies_booster_pack": 3.99,  # Evolving Skies, booster pack; cardlines.com
    "celebrations_etb": 49.99,  # Celebrations, etb; marriland.com, pokejungle.net
    "fusion-strike_booster_box": 143.64,  # Fusion Strike, booster box; cardlines.com
    "fusion-strike_booster_pack": 3.99,  # Fusion Strike, booster pack; marriland.com
    "brilliant-stars_booster_pack": 3.99,  # Brilliant Stars, booster pack; marriland.com
    "astral-radiance_booster_box": 143.64,  # Astral Radiance, booster box; 
    "pokemon-go_etb": 49.99,  # Pokemon GO, etb; pokeguardian.com
    "lost-origin_booster_box": 143.64,  # Lost Origin, booster box; cardlines.com
    "lost-origin_booster_bundle": 23.94,  # Lost Origin, booster bundle; cardlines.com, pokeguardian.com
    "lost-origin_booster_pack": 3.99,  # Lost Origin, booster pack; cardlines.com, pokeguardian.com
    "silver-tempest_booster_pack": 3.99,  # Silver Tempest, booster pack; pokeguardian.com
    "crown-zenith_etb": 49.99,  # Crown Zenith, etb; pokeguardian.com, tcgdropradar.com

    # --- Scarlet & Violet ---
    "scarlet-and-violet_booster_box": 161.64,  # Scarlet & Violet, booster box; dexerto.com, phdgames.com
    "scarlet-and-violet_etb": 49.99,  # Scarlet & Violet, etb; marriland.com, phdgames.com, thecardshopfinder.com
    "scarlet-and-violet_booster_pack": 4.49,  # Scarlet & Violet, booster pack; dexerto.com, marriland.com, phdgames.com
    "paldea-evolved_booster_box": 161.64,  # Paldea Evolved, booster box; phdgames.com
    "paldea-evolved_etb": 49.99,  # Paldea Evolved, etb; phdgames.com, tcgdropradar.com
    "obsidian-flames_booster_box": 161.64,  # Obsidian Flames, booster box; dexerto.com, phdgames.com
    "obsidian-flames_etb": 49.99,  # Obsidian Flames, etb; phdgames.com, tcgdropradar.com
    "scarlet-and-violet-151_etb": 49.99,  # Scarlet & Violet 151, etb; phdgames.com, thetoyinsider.com, toybook.com
    "paradox-rift_booster_box": 161.64,  # Paradox Rift, booster box; phdgames.com
    "paldean-fates_etb": 49.99,  # Paldean Fates, etb; phdgames.com, thetoyinsider.com
    "temporal-forces_booster_box": 161.64,  # Temporal Forces, booster box; phdgames.com
    "temporal-forces_etb": 49.99,  # Temporal Forces, etb; phdgames.com, tcgdropradar.com
    "temporal-forces_booster_bundle": 26.94,  # Temporal Forces, booster bundle; phdgames.com
    "twilight-masquerade_booster_box": 161.64,  # Twilight Masquerade, booster box; phdgames.com
    "twilight-masquerade_etb": 49.99,  # Twilight Masquerade, etb; phdgames.com, tcgdropradar.com
    "twilight-masquerade_booster_bundle": 26.94,  # Twilight Masquerade, booster bundle; phdgames.com
    "shrouded-fable_etb": 49.99,  # Shrouded Fable, etb; phdgames.com, tcgdropradar.com
    "shrouded-fable_booster_bundle": 26.94,  # Shrouded Fable, booster bundle; phdgames.com
    "stellar-crown_booster_box": 161.64,  # Stellar Crown, booster box; phdgames.com
    "stellar-crown_etb": 49.99,  # Stellar Crown, etb; phdgames.com, thetoyinsider.com
    "stellar-crown_booster_bundle": 26.94,  # Stellar Crown, booster bundle; phdgames.com
    "surging-sparks_booster_box": 161.64,  # Surging Sparks, booster box; phdgames.com, thecardshopfinder.com
    "surging-sparks_etb": 49.99,  # Surging Sparks, etb; phdgames.com, tcgdropradar.com
    "surging-sparks_booster_bundle": 26.94,  # Surging Sparks, booster bundle; phdgames.com, thecardshopfinder.com
    "prismatic-evolutions_etb": 49.99,  # Prismatic Evolutions, etb; dexerto.com, phdgames.com, thetoyinsider.com
    "journey-together_booster_box": 161.64,  # Journey Together, booster box; phdgames.com
    "journey-together_etb": 49.99,  # Journey Together, etb; phdgames.com, tcgdropradar.com
    "journey-together_booster_bundle": 26.94,  # Journey Together, booster bundle; phdgames.com
    "destined-rivals_booster_box": 161.64,  # Destined Rivals, booster box; phdgames.com, thecardshopfinder.com
    "destined-rivals_etb": 49.99,  # Destined Rivals, etb; phdgames.com, thetoyinsider.com
    "destined-rivals_booster_bundle": 26.94,  # Destined Rivals, booster bundle; phdgames.com, thecardshopfinder.com
    "black-bolt_etb": 49.99,  # Black Bolt, etb; phdgames.com, seller.tcgplayer.com, thehobbybin.com
    "black-bolt_booster_bundle": 26.94,  # Black Bolt, booster bundle; phdgames.com, seller.tcgplayer.com, thehobbybin.com
    "white-flare_etb": 49.99,  # White Flare, etb; phdgames.com, seller.tcgplayer.com, thehobbybin.com
    "white-flare_booster_bundle": 26.94,  # White Flare, booster bundle; phdgames.com, seller.tcgplayer.com, thehobbybin.com

    # --- Mega Evolution ---
    "mega-evolution_booster_box": 161.64,  # Mega Evolution, booster box; phdgames.com, pokeguardian.com, thehobbybin.com
    "mega-evolution_etb": 49.99,  # Mega Evolution, etb; phdgames.com, pokeguardian.com, seller.tcgplayer.com
    "mega-evolution_booster_bundle": 26.94,  # Mega Evolution, booster bundle; phdgames.com, pokeguardian.com, seller.tcgplayer.com
    "mega-evolution_booster_pack": 4.49,  # Mega Evolution, booster pack; pokeguardian.com, pokemoncenter.com
    "phantasmal-flames_booster_box": 161.64,  # Phantasmal Flames, booster box; phdgames.com, pokeguardian.com, tcgdropradar.com
    "phantasmal-flames_etb": 49.99,  # Phantasmal Flames, etb; bestbuy.com, phdgames.com, pokeguardian.com
    "phantasmal-flames_booster_bundle": 26.94,  # Phantasmal Flames, booster bundle; phdgames.com, pokeguardian.com, tcgdropradar.com
    "30th-celebration_etb": 49.99,  # 30th Celebration, etb; phdgames.com, seller.tcgplayer.com, tcgdropradar.com
    "delta-reign_etb": 49.99,  # Delta Reign, etb; cardrake.com, nerdsnack.com, phdgames.com
    "delta-reign_booster_bundle": 26.94,  # Delta Reign, booster bundle; cardrake.com, nerdsnack.com, phdgames.com
}
