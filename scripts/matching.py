"""Deterministic + fuzzy title matching for active listings (MATCH-01).

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
"""

import re

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
