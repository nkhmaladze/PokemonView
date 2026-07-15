"""Deterministic + fuzzy title matching (MATCH-01) and lot/damaged/
counterfeit exclusion (MATCH-02) for active listings.

Pure, DB-free functions consumed by the orchestration layer
(`run_matching_once`, Plan 04-04). No top-level side effects on import:
no MongoClient construction, no network calls, no rapidfuzz model
loading beyond the plain `from rapidfuzz import fuzz, process` import
(mirrors scripts/ebay_client.py's / scripts/ingest_worker.py's
established "no top-level side effects on import" convention).

Credential/data hygiene (mirrors scripts/ingest_worker.py): never log
full listing `title` strings at info level.

Matching design is two-tier and strict/precision-first (D-01):
  Tier 1 (exact keyword rule) — a catalog product matches only if
    every one of its `required_keywords` (scripts.catalog_data.CATALOG)
    appears as a substring of the normalized title. Exactly one
    candidate resolves via `match_method="keyword"`; more than one
    candidate is never auto-resolved (D-03) — it resolves to
    match_status="unmatched"/match_method="ambiguous".
  Tier 2 (bounded fuzzy fallback, only when Tier 1 finds zero
    candidates) — RapidFuzz `process.extract` against a lean
    per-product canonical phrase (never the catalog's full
    `display_name`, which shares enough "Pokemon TCG: Mega
    Evolution-..." boilerplate across every product to dilute fuzzy
    discrimination — 04-RESEARCH.md Pitfall 3). Only accepted when the
    top score clears both an absolute floor (FUZZY_SCORE_CUTOFF) and a
    margin over the runner-up (FUZZY_MARGIN) — otherwise unmatched.

`check_exclusion()` is an independent keyword/regex pass (lot,
damaged, counterfeit) run regardless of match outcome. Every pattern
uses simple, non-nested, bounded quantifiers only (T-04-02 ReDoS
mitigation — no `(a+)+`-style nesting).
"""

import re
import statistics

from rapidfuzz import fuzz, process

from scripts.catalog_data import CATALOG

FILLER_WORDS = [
    "new",
    "sealed",
    "factory sealed",
    "fast ship",
    "fast shipping",
    "free shipping",
    "brand new",
    "in hand",
    "ready to ship",
    "same day ship",
]

FUZZY_SCORE_CUTOFF = 90  # [ASSUMED — precision-first per D-01]
FUZZY_MARGIN = 5  # [ASSUMED — required gap over 2nd-best candidate]


def normalize(title: str) -> str:
    """Lowercase, strip filler marketing words (word-boundary-anchored —
    NOT plain substring .replace(), which would corrupt "resealed" into
    "re " per 04-RESEARCH.md Pitfall 2), strip punctuation, collapse
    whitespace."""
    t = title.lower()
    for word in FILLER_WORDS:
        t = re.sub(rf"\b{re.escape(word)}\b", " ", t)
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _product_slug(product: dict) -> str:
    """The deterministic products._id slug: f"{set_name}_{product_type}"
    lowercased with spaces replaced by hyphens — byte-identical to
    scripts/seed_catalog.py's `_id` and scripts/ingest_worker.py's
    `product_ref` derivation."""
    return f"{product['set_name']}_{product['product_type']}".lower().replace(" ", "-")


def _canonical_phrase(product: dict) -> str:
    """Lean per-product fuzzy-comparison phrase: "{set_name} {type
    phrase}", NOT catalog `display_name` (Pitfall 3). PRODUCT_TYPE_SEARCH_TERMS
    is imported here, deferred, rather than at module top level — a
    module-top-level import would create a circular import once Plan
    04-05 adds `from scripts.matching import run_matching_once` to
    scripts/ingest_worker.py."""
    from scripts.ingest_worker import PRODUCT_TYPE_SEARCH_TERMS

    return f"{product['set_name']} {PRODUCT_TYPE_SEARCH_TERMS[product['product_type']]}".lower()


def match_listing(normalized_title: str) -> dict:
    """Returns {match_status, matched_product_id, match_method, match_score}.

    Tier 1: exactly one catalog product whose required_keywords are ALL
    present -> matched/keyword. More than one -> unmatched/ambiguous
    (D-03: never auto-resolved). Zero -> Tier 2 bounded fuzzy fallback.
    """
    candidates = [
        p for p in CATALOG if all(kw in normalized_title for kw in p["required_keywords"])
    ]
    if len(candidates) == 1:
        return {
            "match_status": "matched",
            "matched_product_id": _product_slug(candidates[0]),
            "match_method": "keyword",
            "match_score": None,
        }
    if len(candidates) > 1:
        # D-03: a plausible multi-candidate match is never auto-resolved.
        return {
            "match_status": "unmatched",
            "matched_product_id": None,
            "match_method": "ambiguous",
            "match_score": None,
        }

    # Zero Tier-1 candidates -> Tier 2 bounded fuzzy fallback.
    phrases = {_canonical_phrase(p): _product_slug(p) for p in CATALOG}
    results = process.extract(
        normalized_title,
        list(phrases.keys()),
        scorer=fuzz.token_sort_ratio,
        limit=2,
    )
    if not results:
        return {
            "match_status": "unmatched",
            "matched_product_id": None,
            "match_method": None,
            "match_score": None,
        }

    top_phrase, top_score, _ = results[0]
    second_score = results[1][1] if len(results) > 1 else 0
    if top_score >= FUZZY_SCORE_CUTOFF and (top_score - second_score) >= FUZZY_MARGIN:
        return {
            "match_status": "matched",
            "matched_product_id": phrases[top_phrase],
            "match_method": "fuzzy",
            "match_score": top_score,
        }
    return {
        "match_status": "unmatched",
        "matched_product_id": None,
        "match_method": None,
        "match_score": top_score,
    }


LOT_PATTERNS = [
    re.compile(r"\blot\s+of\b"),
    re.compile(r"\bjob\s*lot\b"),
    re.compile(r"\bwholesale\b"),
    re.compile(r"\bset\s+of\s+\d+\b"),
    re.compile(r"\bx\s?[2-9]\d*\b"),  # "x2", "x 3" — quantity, not the letter x alone
    re.compile(r"\b[2-9]\d*\s?x\b"),  # "2x", "3 x"
    re.compile(r"\b[2-9]\d*\s*(boxes|etbs)\b"),
    # Deliberately NOT "packs"/"bundles" in the quantity-noun group, and
    # deliberately NOT the bare word "bundle" alone — catalog display
    # names legitimately contain "(6 Packs)" (booster_bundle) and
    # "(36 Packs)" (booster_box); a naive "N packs"/"N bundles"/"bundle"
    # check would exclude every real booster_bundle/booster_box listing
    # that echoes its own official product description (04-RESEARCH.md
    # Pitfall 1; deviation from the literal RESEARCH.md pattern list,
    # which included "packs|bundles" here — that literal list conflicts
    # with test_exclusion_does_not_flag_legitimate_bundle).
]

DAMAGED_PATTERNS = [
    re.compile(r"\bdented\b"),
    re.compile(r"\bresealed\b"),
    re.compile(r"\bopened\b"),
    re.compile(r"\bempty\s+box\b"),
    re.compile(r"\bno\s+cards?\b"),
    re.compile(r"\bdamaged\b"),
    re.compile(r"\bcrushed\b"),
    re.compile(r"\btorn\s+seal\b"),
    re.compile(r"\bbroken\s+seal\b"),
    re.compile(r"\bseal\s+broken\b"),
    # D-08: deliberately does NOT include "shelf wear", "corner ding",
    # "minor wear", "light wear" — cosmetic language must not exclude.
]

COUNTERFEIT_PATTERNS = [
    re.compile(r"\breplica\b"),
    re.compile(r"\bcustom\b"),
    re.compile(r"\bfan\s?made\b"),
    re.compile(r"\bproxy\b"),
    re.compile(r"\breproduction\b"),
    re.compile(r"\brepro\b"),
    re.compile(r"\bbootleg\b"),
    re.compile(r"\bnot\s+authentic\b"),
    re.compile(r"\bunofficial\b"),
]


def check_exclusion(normalized_title: str) -> str | None:
    """MATCH-02: returns "lot" | "damaged" | "counterfeit" | None,
    precedence lot -> damaged -> counterfeit. Runs independently of
    match outcome, on every listing touched this run.

    Every pattern above uses simple, non-nested, bounded quantifiers
    only (no `(a+)+`-style nesting) so an adversarially long title
    cannot trigger catastrophic backtracking (T-04-02, ReDoS)."""
    if any(p.search(normalized_title) for p in LOT_PATTERNS):
        return "lot"
    if any(p.search(normalized_title) for p in DAMAGED_PATTERNS):
        return "damaged"
    if any(p.search(normalized_title) for p in COUNTERFEIT_PATTERNS):
        return "counterfeit"
    return None


OUTLIER_N_STD = 2  # D-13, locked: 2 population std devs from the median
OUTLIER_MIN_COUNT = 3  # D-14 interpretation: below this, skip filtering entirely


def filter_outliers(
    listings: list[dict], price_field: str = "total_price"
) -> tuple[list, list]:
    """MATCH-03, D-13/D-14/D-15: returns (included, excluded).

    Below OUTLIER_MIN_COUNT listings, filtering is skipped entirely and
    everything is included (D-14) — too few points to compute a
    meaningful median/std-dev. Otherwise a listing is excluded iff its
    `price_field` value is more than OUTLIER_N_STD population std devs
    (statistics.pstdev) from the group's median — computed from ONLY
    the passed `listings` (this run's own included group, D-15), never
    a rolling historical window. `price_field` defaults to
    "total_price", the canonical landed-cost field (never bare
    `item_price` — 04-RESEARCH.md Pitfall 5). Excluded listings still
    carry their full document; the caller sets
    exclusion_reason="outlier" on them (D-16)."""
    if len(listings) < OUTLIER_MIN_COUNT:
        return listings, []

    prices = [listing[price_field] for listing in listings]
    med = statistics.median(prices)
    sd = statistics.pstdev(prices)
    if sd == 0:
        # All identical prices — nothing is statistically an outlier.
        return listings, []

    included, excluded = [], []
    for listing in listings:
        bucket = (
            excluded
            if abs(listing[price_field] - med) > OUTLIER_N_STD * sd
            else included
        )
        bucket.append(listing)
    return included, excluded


def aggregate_and_write(db, product_id: str, included: list[dict], ts) -> bool:
    """MATCH-03, D-09/D-10/D-11/D-12: writes exactly one price_points
    document for `product_id` when `included` is non-empty, returns
    True. When `included` is empty, writes nothing and returns False
    (D-11 — leave a real gap, never carry forward a stale price).

    `item_price` and `total_price` are each computed as their OWN
    independent statistics.median() over `included` (D-12) — never
    total_price derived from item_price's median."""
    if not included:
        return False
    db.price_points.insert_one(
        {
            "ts": ts,
            "product_id": product_id,
            "item_price": statistics.median(listing["item_price"] for listing in included),
            "total_price": statistics.median(listing["total_price"] for listing in included),
        }
    )
    return True
