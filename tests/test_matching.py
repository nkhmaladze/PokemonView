"""RED contract tests for Phase 4's listing matching, exclusion, outlier
filtering, and price aggregation pipeline (MATCH-01, MATCH-02, MATCH-03,
D-04).

This is the Nyquist RED scaffold authored in Plan 04-02 (Wave 1) — it
pins the exact behavioral contract (function signatures, return
shapes, field names, D-01...D-16 semantics) that Plans 04-03 (Wave 2),
04-04 (Wave 3), and 04-05 (Wave 4) turn GREEN. `scripts/matching.py`
does not exist yet; every `from scripts.matching import ...` (and the
`scripts.ingest_worker.run_ingestion_once` call in the final
integration test) is deferred into each test's body, not placed at
module top level, so `pytest --collect-only` succeeds now (mirrors
`tests/test_ingest_worker.py`'s established deferred-import
convention).

Unit tests (`test_normalize_word_boundary_preserves_resealed`,
`test_match_listing_keyword_exact`, `test_match_listing_fuzzy_fallback`,
`test_match_listing_ambiguous_unmatched`, `test_exclusion_lot`,
`test_exclusion_damaged_severe_only`, `test_exclusion_counterfeit`,
`test_exclusion_does_not_flag_legitimate_bundle`,
`test_outlier_filter_excludes_far_listings`,
`test_outlier_filter_skipped_when_too_few`) take no fixture — the
functions under test are pure, no I/O.

Integration tests (`test_price_points_median_aggregation`,
`test_price_points_skipped_when_zero_included`,
`test_run_matching_once_end_to_end`,
`test_run_ingestion_once_records_match_counts`) consume the
`matching_db` fixture from tests/conftest.py (a live `pokemonview_test`
MongoDB handle resetting active_listings/price_points/ingestion_runs/
ingestion_locks before and after each test).

Plain pytest `assert` style throughout — no unittest.TestCase,
consistent with tests/test_ingest_worker.py and
tests/test_catalog_schema.py. Every price value used in `==`
assertions is an exactly-representable binary float (e.g. 150.00,
155.00, 160.00), following test_ingest_worker.py's precedent.
"""

from datetime import datetime, timezone


def test_normalize_word_boundary_preserves_resealed():
    """normalize() strips filler words with word-boundary-anchored regex,
    not plain substring .replace() — a naive .replace("sealed", "")
    would corrupt "resealed" into "re " (04-RESEARCH.md Pitfall 2), which
    would silently break the damaged-exclusion pattern's ability to see
    the word "resealed" at all."""
    from scripts.matching import normalize

    result = normalize("Resealed Chaos Rising ETB")
    assert "resealed" in result, (
        "normalize() must preserve the whole word 'resealed' — a plain "
        "substring .replace('sealed', '') would corrupt it into 're', "
        "destroying the exact signal the damaged-exclusion check needs"
    )


def test_normalize_strips_multiword_fillers_brand_new_factory_sealed():
    """CR-02 regression: multi-word filler phrases ("brand new", "factory
    sealed") must actually strip — FILLER_WORDS must list them before the
    single words they contain ("new", "sealed"), otherwise the
    single-word entries consume "new"/"sealed" first and leave "brand"/
    "factory" behind as orphaned noise tokens that pollute Tier-2 fuzzy
    matching."""
    from scripts.matching import normalize

    result = normalize("Chaos Rising ETB Brand New Factory Sealed")
    assert "brand" not in result, (
        "'brand new' must strip as a whole phrase, not leave 'brand' "
        "behind as an orphaned noise token (CR-02)"
    )
    assert "factory" not in result, (
        "'factory sealed' must strip as a whole phrase, not leave "
        "'factory' behind as an orphaned noise token (CR-02)"
    )
    assert "new" not in result
    assert "sealed" not in result


def test_match_listing_keyword_exact():
    """MATCH-01, D-01: a title containing all of a single product's
    required_keywords resolves via Tier 1 (exact keyword rule) to that
    product's exact catalog slug _id, with match_method="keyword"."""
    from scripts.matching import match_listing, normalize

    title = normalize(
        "Pokemon Chaos Rising Elite Trainer Box ETB New Factory Sealed Fast Shipping"
    )
    result = match_listing(title)

    assert result["match_status"] == "matched"
    assert result["match_method"] == "keyword"
    assert result["matched_product_id"] == "chaos-rising_etb", (
        "matched_product_id must equal the exact products._id slug "
        "seed_catalog.py derives: f'{set_name}_{product_type}'.lower()"
        ".replace(' ', '-')"
    )


def test_match_listing_fuzzy_fallback():
    """MATCH-01: a near-miss title (single-letter transposition typo in
    'Elite' -> 'Eltie') has zero exact Tier-1 keyword candidates (no
    required_keywords substring 'elite trainer box' or 'etb' present),
    but is clearly closest to chaos-rising_etb's canonical fuzzy phrase
    with a wide margin over every other catalog product's phrase —
    resolves via Tier 2 (fuzzy fallback) with a numeric match_score."""
    from scripts.matching import match_listing, normalize

    title = normalize("Chaos Rising Eltie Trainer Box")
    result = match_listing(title)

    assert result["match_status"] == "matched"
    assert result["match_method"] == "fuzzy"
    assert result["matched_product_id"] == "chaos-rising_etb"
    assert isinstance(result["match_score"], (int, float))


def test_match_listing_ambiguous_unmatched():
    """MATCH-01, D-03: a title satisfying the required_keywords of TWO
    products (both etb and booster_box keywords for the same set) must
    NOT be auto-resolved to either candidate — it resolves to
    match_status="unmatched" with matched_product_id=None, never picking
    the higher-confidence candidate."""
    from scripts.matching import match_listing, normalize

    title = normalize(
        "Chaos Rising Elite Trainer Box ETB Booster Box Display Combo Lot"
    )
    result = match_listing(title)

    assert result["match_status"] == "unmatched"
    assert result["matched_product_id"] is None, (
        "an ambiguous multi-candidate title must never be auto-resolved "
        "to either candidate product (D-03)"
    )


def test_exclusion_lot():
    """MATCH-02: titles with quantity/lot language return
    check_exclusion(...) == "lot"."""
    from scripts.matching import check_exclusion, normalize

    lot_titles = [
        "Chaos Rising Booster Box Lot of 4",
        "Perfect Order ETB Job Lot",
        "Ascended Heroes Booster Pack Set of 6",
        "Pitch Black Booster Box x3",
        "Pitch Black Booster Box 3x",
        "Chaos Rising ETB Wholesale",
    ]
    for title in lot_titles:
        normalized = normalize(title)
        assert check_exclusion(normalized) == "lot", (
            f"expected exclusion_reason='lot' for title: {title!r}"
        )


def test_exclusion_damaged_severe_only():
    """MATCH-02, D-08: titles with severe damage signals return "damaged",
    while titles with only minor-cosmetic language return None (not
    excluded) — condition exclusion triggers only on explicit/severe
    signals, never on cosmetic wear language."""
    from scripts.matching import check_exclusion, normalize

    damaged_titles = [
        "Chaos Rising Booster Box Dented",
        "Perfect Order ETB Resealed",
        "Ascended Heroes Booster Box Opened",
        "Pitch Black ETB Empty Box",
        "Chaos Rising Booster Box No Cards",
    ]
    for title in damaged_titles:
        normalized = normalize(title)
        assert check_exclusion(normalized) == "damaged", (
            f"expected exclusion_reason='damaged' for title: {title!r}"
        )

    cosmetic_titles = [
        "Chaos Rising Booster Box Shelf Wear",
        "Perfect Order ETB Corner Ding",
        "Ascended Heroes Booster Box Minor Wear",
    ]
    for title in cosmetic_titles:
        normalized = normalize(title)
        assert check_exclusion(normalized) is None, (
            f"minor-cosmetic language must NOT trigger exclusion (D-08) "
            f"for title: {title!r}"
        )


def test_exclusion_counterfeit():
    """MATCH-02: titles with counterfeit/replica signals return
    "counterfeit"."""
    from scripts.matching import check_exclusion, normalize

    counterfeit_titles = [
        "Chaos Rising Booster Box Replica",
        "Perfect Order ETB Proxy",
        "Ascended Heroes Booster Box Reproduction",
        "Pitch Black ETB Bootleg",
        "Chaos Rising Booster Box Custom",
    ]
    for title in counterfeit_titles:
        normalized = normalize(title)
        assert check_exclusion(normalized) == "counterfeit", (
            f"expected exclusion_reason='counterfeit' for title: {title!r}"
        )


def test_exclusion_does_not_flag_legitimate_bundle():
    """MATCH-02, D-06, 04-RESEARCH.md Pitfall 1: a legitimate
    booster_bundle title must NOT trigger the lot-exclusion rule — the
    bare word "bundle" is a first-class required_keyword for the
    booster_bundle product type (Phase 2 D-06), not multi-quantity/lot
    language."""
    from scripts.matching import check_exclusion, normalize

    title = normalize("Chaos Rising Booster Bundle 6 Packs")
    normalized = normalize(title)
    assert check_exclusion(normalized) is None, (
        "the bare word 'bundle' must never trigger the lot exclusion "
        "rule — booster_bundle is a legitimate first-class product type"
    )


def test_outlier_filter_excludes_far_listings():
    """MATCH-03, D-13: a group of >=5 synthetic listings where four
    cluster tightly and one sits far above (>2 population std devs from
    the median) — filter_outliers() returns (included, excluded) with
    the far listing excluded and the tight cluster included. Default
    price_field must be total_price (04-RESEARCH.md Pitfall 5), never
    item_price."""
    from scripts.matching import filter_outliers

    tight_cluster = [
        {"_id": "v1|A|0", "total_price": 150.00, "item_price": 145.00},
        {"_id": "v1|B|0", "total_price": 152.00, "item_price": 147.00},
        {"_id": "v1|C|0", "total_price": 148.00, "item_price": 143.00},
        {"_id": "v1|D|0", "total_price": 151.00, "item_price": 146.00},
    ]
    far_outlier = {"_id": "v1|E|0", "total_price": 500.00, "item_price": 495.00}
    listings = tight_cluster + [far_outlier]

    included, excluded = filter_outliers(listings)

    included_ids = {l["_id"] for l in included}
    excluded_ids = {l["_id"] for l in excluded}

    assert far_outlier["_id"] in excluded_ids, (
        "the far-outlier listing must be excluded from the included set"
    )
    assert far_outlier["_id"] not in included_ids
    for listing in tight_cluster:
        assert listing["_id"] in included_ids, (
            f"tightly-clustered listing {listing['_id']} must remain included"
        )
        assert listing["_id"] not in excluded_ids


def test_outlier_filter_skipped_when_too_few():
    """MATCH-03, D-14: below the min-count threshold, filtering is
    skipped entirely — all listings are returned in `included` with an
    empty `excluded`, even if the two prices differ wildly."""
    from scripts.matching import filter_outliers

    listings = [
        {"_id": "v1|A|0", "total_price": 50.00, "item_price": 45.00},
        {"_id": "v1|B|0", "total_price": 5000.00, "item_price": 4995.00},
    ]

    included, excluded = filter_outliers(listings)

    assert len(included) == 2
    assert excluded == []
    included_ids = {l["_id"] for l in included}
    assert included_ids == {"v1|A|0", "v1|B|0"}


def test_price_points_median_aggregation(matching_db):
    """MATCH-03, D-09/D-10/D-12: aggregate_and_write() writes exactly ONE
    price_points document for the given product_id, with item_price and
    total_price each computed as their OWN independent median (not
    total_price derived from item_price's median). Uses an odd-count
    included set with exactly-representable, distinct median values."""
    from scripts.matching import aggregate_and_write

    ts = datetime.now(timezone.utc)
    included = [
        {"_id": "v1|A|0", "item_price": 140.00, "total_price": 150.00},
        {"_id": "v1|B|0", "item_price": 145.00, "total_price": 155.00},
        {"_id": "v1|C|0", "item_price": 150.00, "total_price": 160.00},
    ]

    result = aggregate_and_write(
        matching_db, "perfect-order_booster_box", included, ts
    )

    assert result is True

    docs = list(
        matching_db.price_points.find({"product_id": "perfect-order_booster_box"})
    )
    assert len(docs) == 1, (
        "exactly one price_points document must be written per product "
        "per run (D-09)"
    )
    doc = docs[0]
    assert doc["item_price"] == 145.00, (
        "item_price must be the independent median of the included "
        "listings' item_price values (D-12)"
    )
    assert doc["total_price"] == 155.00, (
        "total_price must be the independent median of the included "
        "listings' total_price values (D-12), not derived from "
        "item_price's median"
    )
    # MongoDB's BSON date type stores millisecond precision (not
    # microsecond) and this project's MongoClient is not tz_aware, so
    # a round-tripped `ts` is naive and truncated relative to the
    # microsecond-precision, tz-aware `ts` passed in — compare within a
    # tolerance rather than exact equality (inherent BSON/pymongo
    # date-storage behavior, not a matching.py defect).
    assert abs((doc["ts"].replace(tzinfo=None) - ts.replace(tzinfo=None)).total_seconds()) < 1, (
        "ts must round-trip (within MongoDB's millisecond BSON date "
        "precision) to the run timestamp passed into aggregate_and_write"
    )


def test_price_points_skipped_when_zero_included(matching_db):
    """MATCH-03, D-11: an empty included set skips the write entirely
    (gap, not carry-forward) — aggregate_and_write() returns False and
    writes zero price_points documents for that product."""
    from scripts.matching import aggregate_and_write

    ts = datetime.now(timezone.utc)
    result = aggregate_and_write(matching_db, "chaos-rising_etb", [], ts)

    assert result is False
    count = matching_db.price_points.count_documents(
        {"product_id": "chaos-rising_etb"}
    )
    assert count == 0, (
        "zero price_points documents must be written when the included "
        "set is empty — a gap, not a carried-forward last-known price"
    )


def test_run_matching_once_end_to_end(matching_db):
    """MATCH-01/02/03 + D-16, end-to-end: seeds a realistic batch of
    active_listings for a single product (Perfect Order booster_box),
    calls run_matching_once(), and asserts the full downstream effect:
    per-listing match_status/matched_product_id/exclusion_reason flags,
    exactly one price_points doc with the correct median (excluding the
    outlier and keyword-excluded listings), and integer summary counts."""
    from scripts.matching import run_matching_once

    run_id = "RUN-E2E"
    ts = datetime.now(timezone.utc)

    # Odd number (3) of clean matchable listings, tight cluster.
    clean_listings = [
        {
            "_id": "v1|CLEAN-1|0",
            "title": "Pokemon Perfect Order Booster Box Display New Sealed",
            "item_price": 150.00,
            "total_price": 155.00,
            "shipping_cost": 5.00,
            "product_ref": "perfect-order_booster_box",
            "category_id": None,
            "fetched_at": ts,
            "run_id": run_id,
        },
        {
            "_id": "v1|CLEAN-2|0",
            "title": "Pokemon Perfect Order Booster Box Display Sealed",
            "item_price": 152.00,
            "total_price": 157.00,
            "shipping_cost": 5.00,
            "product_ref": "perfect-order_booster_box",
            "category_id": None,
            "fetched_at": ts,
            "run_id": run_id,
        },
        {
            "_id": "v1|CLEAN-3|0",
            "title": "Pokemon Perfect Order Booster Box Display Fast Ship",
            "item_price": 148.00,
            "total_price": 153.00,
            "shipping_cost": 5.00,
            "product_ref": "perfect-order_booster_box",
            "category_id": None,
            "fetched_at": ts,
            "run_id": run_id,
        },
    ]
    # Clean-matchable but statistically far outlier.
    outlier_listing = {
        "_id": "v1|OUTLIER|0",
        "title": "Pokemon Perfect Order Booster Box Display",
        "item_price": 495.00,
        "total_price": 500.00,
        "shipping_cost": 5.00,
        "product_ref": "perfect-order_booster_box",
        "category_id": None,
        "fetched_at": ts,
        "run_id": run_id,
    }
    # NOTE: lot/damaged/counterfeit titles deliberately include ALL of
    # perfect-order_booster_box's required_keywords ("perfect order",
    # "booster box", "display") so they resolve deterministically via
    # Tier-1 keyword matching (match_status="matched") rather than
    # falling through to the fuzzy tier — the exclusion check
    # (independent of match outcome) is what makes them excluded.
    lot_listing = {
        "_id": "v1|LOT|0",
        "title": "Pokemon Perfect Order Booster Box Display Lot of 4",
        "item_price": 600.00,
        "total_price": 610.00,
        "shipping_cost": 10.00,
        "product_ref": "perfect-order_booster_box",
        "category_id": None,
        "fetched_at": ts,
        "run_id": run_id,
    }
    damaged_listing = {
        "_id": "v1|DAMAGED|0",
        "title": "Pokemon Perfect Order Booster Box Display Dented",
        "item_price": 100.00,
        "total_price": 105.00,
        "shipping_cost": 5.00,
        "product_ref": "perfect-order_booster_box",
        "category_id": None,
        "fetched_at": ts,
        "run_id": run_id,
    }
    counterfeit_listing = {
        "_id": "v1|COUNTERFEIT|0",
        "title": "Pokemon Perfect Order Booster Box Display Replica",
        "item_price": 30.00,
        "total_price": 35.00,
        "shipping_cost": 5.00,
        "product_ref": "perfect-order_booster_box",
        "category_id": None,
        "fetched_at": ts,
        "run_id": run_id,
    }
    ambiguous_listing = {
        "_id": "v1|AMBIGUOUS|0",
        "title": "Pokemon Chaos Rising Elite Trainer Box ETB Booster Box Display",
        "item_price": 100.00,
        "total_price": 105.00,
        "shipping_cost": 5.00,
        "product_ref": "chaos-rising_etb",
        "category_id": None,
        "fetched_at": ts,
        "run_id": run_id,
    }
    nonsense_listing = {
        "_id": "v1|NONSENSE|0",
        "title": "Assorted Trading Card Supplies Sleeves Binder",
        "item_price": 10.00,
        "total_price": 12.00,
        "shipping_cost": 2.00,
        "product_ref": "perfect-order_booster_box",
        "category_id": None,
        "fetched_at": ts,
        "run_id": run_id,
    }

    all_listings = (
        clean_listings
        + [
            outlier_listing,
            lot_listing,
            damaged_listing,
            counterfeit_listing,
            ambiguous_listing,
            nonsense_listing,
        ]
    )
    matching_db.active_listings.insert_many(all_listings)

    result = run_matching_once(matching_db, run_id, ts)

    # (a) per-listing flags
    for listing in clean_listings:
        doc = matching_db.active_listings.find_one({"_id": listing["_id"]})
        assert doc["match_status"] == "matched", listing["_id"]
        assert doc["matched_product_id"] == "perfect-order_booster_box", listing["_id"]
        assert doc["exclusion_reason"] is None, listing["_id"]

    outlier_doc = matching_db.active_listings.find_one({"_id": "v1|OUTLIER|0"})
    assert outlier_doc["match_status"] == "matched"
    assert outlier_doc["matched_product_id"] == "perfect-order_booster_box"
    assert outlier_doc["exclusion_reason"] == "outlier", (
        "a statistically-far listing must carry exclusion_reason='outlier' (D-16)"
    )

    lot_doc = matching_db.active_listings.find_one({"_id": "v1|LOT|0"})
    assert lot_doc["match_status"] == "matched"
    assert lot_doc["exclusion_reason"] == "lot"

    damaged_doc = matching_db.active_listings.find_one({"_id": "v1|DAMAGED|0"})
    assert damaged_doc["match_status"] == "matched"
    assert damaged_doc["exclusion_reason"] == "damaged"

    counterfeit_doc = matching_db.active_listings.find_one({"_id": "v1|COUNTERFEIT|0"})
    assert counterfeit_doc["match_status"] == "matched"
    assert counterfeit_doc["exclusion_reason"] == "counterfeit"

    ambiguous_doc = matching_db.active_listings.find_one({"_id": "v1|AMBIGUOUS|0"})
    assert ambiguous_doc["match_status"] == "unmatched"
    assert ambiguous_doc["matched_product_id"] is None

    nonsense_doc = matching_db.active_listings.find_one({"_id": "v1|NONSENSE|0"})
    assert nonsense_doc["match_status"] == "unmatched"
    assert nonsense_doc["matched_product_id"] is None

    # (b) exactly one price_points doc, median over the clean cluster only
    price_docs = list(
        matching_db.price_points.find({"product_id": "perfect-order_booster_box"})
    )
    assert len(price_docs) == 1
    assert price_docs[0]["total_price"] == 155.00, (
        "the median must be computed only from the clean, non-excluded, "
        "non-outlier cluster — the outlier, lot, damaged, and counterfeit "
        "listings must not contribute to it"
    )

    # (c) returned summary counts. Per RESEARCH.md's run_matching_once
    # orchestration: listings_matched counts every listing with
    # match_status="matched" (including ones later flagged excluded),
    # listings_excluded counts every matched-but-excluded listing
    # (keyword exclusions + outlier exclusions), listings_unmatched
    # counts everything that never resolved to a product.
    assert isinstance(result["listings_matched"], int)
    assert isinstance(result["listings_unmatched"], int)
    assert isinstance(result["listings_excluded"], int)
    assert result["listings_unmatched"] == 2  # ambiguous + nonsense
    assert result["listings_excluded"] == 4  # lot + damaged + counterfeit + outlier
    assert result["listings_matched"] == 7  # 3 clean + outlier + lot + damaged + counterfeit


def test_run_ingestion_once_records_match_counts(matching_db, monkeypatch):
    """D-04: run_ingestion_once() calls run_matching_once() after the
    per-product fetch loop and merges its returned counts as new
    top-level flat integer fields (listings_matched, listings_unmatched,
    listings_excluded) onto the same ingestion_runs document — not a
    nested sub-document, matching the existing flat-field convention."""
    from scripts import ingest_worker
    from scripts.catalog_data import CATALOG

    def fake_get_app_token():
        return {"access_token": "fake-token"}

    def fake_search(access_token, query):
        # First catalog product gets a cleanly-matchable listing; every
        # other product gets an empty result so the batch stays small.
        first_product = CATALOG[0]
        if query == ingest_worker.build_query(first_product):
            return [
                {
                    "itemId": "v1|MATCHCOUNT-1|0",
                    "title": (
                        f"Pokemon {first_product['set_name']} "
                        f"{ingest_worker.PRODUCT_TYPE_SEARCH_TERMS[first_product['product_type']]} "
                        "New Sealed"
                    ),
                    "price": {"value": "50.00"},
                }
            ]
        return []

    monkeypatch.setattr(ingest_worker, "get_app_token", fake_get_app_token)
    monkeypatch.setattr(ingest_worker, "search_sealed_listings", fake_search)

    result = ingest_worker.run_ingestion_once(matching_db)

    for field in ("listings_matched", "listings_unmatched", "listings_excluded"):
        assert field in result, (
            f"ingestion_runs document must carry a top-level '{field}' "
            f"field, proving run_matching_once's counts were merged (D-04)"
        )
        assert isinstance(result[field], int)
