---
phase: 04-listing-matching-price-normalization
verified: 2026-07-14T00:00:00Z
status: passed
score: 7/7 must-haves verified
behavior_unverified: 0
overrides_applied: 0
---

# Phase 4: Listing Matching & Price Normalization Verification Report

**Phase Goal:** Match active eBay listings to catalog products (exact-keyword + bounded fuzzy fallback), exclude lot/damaged/counterfeit listings, filter statistical outliers, and aggregate matched listings into per-product price_points — wired into the Phase 3 ingestion worker's run.
**Verified:** 2026-07-14
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Raw eBay listing titles are matched to the correct canonical catalog product via keyword rules, with match results inspectable (ROADMAP SC-1, MATCH-01) | ✓ VERIFIED | `scripts/matching.py::match_listing()` — Tier-1 exact-keyword (`all(kw in normalized_title for kw in required_keywords)`) resolves a single candidate to `matched/keyword`; ambiguous (>1 candidate) never auto-resolves (D-03). Results written to `active_listings.match_status/matched_product_id/match_method/match_score` (queryable). Live tests pass: `test_match_listing_keyword_exact`, `test_match_listing_fuzzy_fallback`, `test_match_listing_ambiguous_unmatched` (ran locally against live MongoDB, all PASSED). |
| 2 | Listings signalling lot, bundle, damaged, or counterfeit product are flagged and excluded from a product's price aggregate (ROADMAP SC-2, MATCH-02) | ✓ VERIFIED | `scripts/matching.py::check_exclusion()` — `LOT_PATTERNS`/`DAMAGED_PATTERNS`/`COUNTERFEIT_PATTERNS`, precedence lot→damaged→counterfeit, deliberately never keys on the bare word "bundle" (verified: `test_exclusion_does_not_flag_legitimate_bundle` PASSED) and never excludes cosmetic wear (`test_exclusion_damaged_severe_only` PASSED). Excluded listings are kept flagged via `exclusion_reason` and omitted from `by_product` grouping in `run_matching_once`, so they never reach `aggregate_and_write`. |
| 3 | Statistical price outliers (far from rolling median) are excluded so the aggregate reflects the true market, not noise (ROADMAP SC-3, MATCH-03) | ✓ VERIFIED | `scripts/matching.py::filter_outliers()` — 2-population-stddev cutoff (`OUTLIER_N_STD=2`) on `total_price`, skip-below-3 (`OUTLIER_MIN_COUNT=3`, D-14), computed only from the current run's group (D-15). Outlier-excluded listings get `exclusion_reason="outlier"` (D-16) via a second `bulk_write`. Live tests pass: `test_outlier_filter_excludes_far_listings`, `test_outlier_filter_skipped_when_too_few`. |
| 4 | For a given product, the computed current price is derived only from included listings (matched, non-excluded, non-outlier) (ROADMAP SC-4) | ✓ VERIFIED | `aggregate_and_write()` only receives the post-outlier-filter `included` list per product group; writes exactly one `price_points` doc per product per run with independent `item_price`/`total_price` medians (D-09/D-10/D-12), returns `False`/writes nothing when `included` is empty (D-11). Live tests pass: `test_price_points_median_aggregation`, `test_price_points_skipped_when_zero_included`, `test_run_matching_once_end_to_end`. |
| 5 | Matching is wired into the Phase 3 ingestion worker's run (phase goal's explicit wiring clause) | ✓ VERIFIED | `scripts/ingest_worker.py` imports `run_matching_once` at top level and calls it inside `run_ingestion_once()` as a second stage immediately after the `for product in CATALOG:` fetch loop completes (never per-listing inside the loop). `ingestion_runs` document gains flat top-level `listings_matched`/`listings_unmatched`/`listings_excluded` (D-04). Live test `test_run_ingestion_once_records_match_counts` PASSED, driving the real `run_ingestion_once()` path end-to-end against live MongoDB. |
| 6 | rapidfuzz is correctly pinned/installed for the Tier-2 fuzzy fallback (MATCH-01 dependency) | ✓ VERIFIED | `requirements.txt` line 6: `rapidfuzz==3.14.5`. `python3 -c "import rapidfuzz; print(rapidfuzz.__version__)"` → `3.14.5` (ran directly, not just SUMMARY claim). |
| 7 | No regression to Phase 3 ingestion contract (INGEST-01/02/03) after matching activation | ✓ VERIFIED | Full local `tests/test_ingest_worker.py` (9 tests) ran live against MongoDB — all PASSED, including `test_run_ingestion_once_skips_when_locked` (confirms the skipped-locked path never calls `run_matching_once`). |

**Score:** 7/7 truths verified (0 present-but-behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `scripts/matching.py` | normalize, match_listing, check_exclusion, filter_outliers, aggregate_and_write, run_matching_once + module constants | ✓ VERIFIED | File exists, 374 lines, all six functions present and substantive (no stubs), all consumed by live-passing tests. |
| `tests/test_matching.py` | 14 RED-turned-GREEN contract tests for MATCH-01/02/03 + D-04 | ✓ VERIFIED | File exists, 14 tests present, all 14 PASS live against MongoDB (ran directly: `pytest tests/test_matching.py -v` → 14 passed). |
| `tests/conftest.py` (matching_db fixture) | fixture resetting active_listings/price_points/ingestion_runs/ingestion_locks | ✓ VERIFIED | Fixture present at line 155, mirrors `ingest_db` skeleton, drops the four required collections, skip-if-unset guard present, `TEST_DB_NAME` reused not redefined. |
| `scripts/ingest_worker.py` (extended) | top-level `run_matching_once` import + call as second stage + D-04 counts in ingestion_runs | ✓ VERIFIED | Import at line 44, call at line 271 (post-fetch-loop), `update_doc` carries the three flat integer fields at lines 286-288. |
| `requirements.txt` | `rapidfuzz==3.14.5` pinned | ✓ VERIFIED | Line 6, exact-pin convention preserved, no reordering of prior 5 lines. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `match_listing()` | `scripts.catalog_data.CATALOG` | `required_keywords` substring check (Tier 1) + `_canonical_phrase` fuzzy fallback (Tier 2) | ✓ WIRED | Top-level `from scripts.catalog_data import CATALOG` import; used directly in `match_listing`'s candidate comprehension. |
| `_product_slug()` | `scripts/seed_catalog.py`'s `products._id` | identical slug formula `f"{set_name}_{product_type}".lower().replace(" ", "-")` | ✓ WIRED | Confirmed byte-identical via direct grep of both files (line 79 in matching.py, line 70 in seed_catalog.py). |
| `_canonical_phrase()` | `scripts.ingest_worker.PRODUCT_TYPE_SEARCH_TERMS` | deferred import inside function body | ✓ WIRED | No circular import — verified live both directions: `python3 -c "import scripts.ingest_worker, scripts.matching"` and reverse order both exit 0. |
| `run_matching_once()` | `active_listings` collection | `db.active_listings.find({"run_id": run_id})` + two `bulk_write` passes | ✓ WIRED | Confirmed in source (lines 309, 354, 367) and exercised live by `test_run_matching_once_end_to_end`. |
| `aggregate_and_write()` | `price_points` collection | `db.price_points.insert_one({...})` | ✓ WIRED | Confirmed in source (line 269) and exercised live by `test_price_points_median_aggregation`. |
| `run_ingestion_once()` | `run_matching_once()` | direct call after fetch loop, before `finally` | ✓ WIRED | Confirmed in source (line 271); exercised live by `test_run_ingestion_once_records_match_counts`. |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| rapidfuzz importable at pinned version | `python3 -c "import rapidfuzz; print(rapidfuzz.__version__)"` | `3.14.5` | ✓ PASS |
| No circular import (both orders) | `python3 -c "import scripts.ingest_worker, scripts.matching"` / reverse | both exit 0 | ✓ PASS |
| Full test suite runs green live (not SUMMARY claim) | `python3 -m pytest -q` | `27 passed in 21.55s` | ✓ PASS |
| Matching-only test file runs green live | `python3 -m pytest tests/test_matching.py -v` | `14 passed` | ✓ PASS |
| ReDoS safety on adversarial title | `check_exclusion("booster box " + "a b "*4000 + "lot of 4")` | returns `"lot"` in ~0.0002s | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| MATCH-01 | 04-01, 04-02, 04-03, 04-05 | Raw eBay listing titles matched to catalog products via keyword rules | ✓ SATISFIED | `match_listing()` two-tier implementation; 4 unit tests pass live; wired into `run_ingestion_once`. |
| MATCH-02 | 04-02, 04-03, 04-05 | Listings with lot/bundle/damaged/counterfeit signals excluded from price aggregates | ✓ SATISFIED | `check_exclusion()`; 4 unit tests pass live including the legitimate-bundle-not-excluded and cosmetic-not-excluded edge cases. |
| MATCH-03 | 04-02, 04-04, 04-05 | Statistical price outliers excluded from displayed price | ✓ SATISFIED | `filter_outliers()` + `aggregate_and_write()` + D-16 outlier flagging; 5 tests pass live (unit + integration + end-to-end). |

No orphaned requirements — REQUIREMENTS.md traceability table lists MATCH-01/02/03 all mapped to Phase 4, matching exactly what the five plans declare in frontmatter.

### Anti-Patterns Found

None. Scanned `scripts/matching.py`, `scripts/ingest_worker.py`, `tests/test_matching.py`, `tests/conftest.py` for TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER, "not yet implemented", empty-return stubs — zero matches.

### Human Verification Required

None. All must-haves are programmatically verifiable and were verified against live, running code (not SUMMARY claims). No `<verify><human-check>` blocks were deferred in any of the 5 plans. The one blocking-human checkpoint in this phase (rapidfuzz package-legitimacy gate, Plan 04-01 Task 1) is a procedural supply-chain gate, not a functional goal-truth — its outcome (rapidfuzz installed and importable) is independently verified above regardless of how the approval was recorded.

### Gaps Summary

No gaps. All 7 derived truths (4 from ROADMAP Success Criteria, 1 from the phase goal's explicit wiring clause, 2 supporting dependency/regression truths) are VERIFIED with live evidence: the full 27-test suite (catalog + ingestion + matching) passes against a live MongoDB instance when run directly by this verification, not merely claimed in SUMMARY.md. `scripts/matching.py` is substantive and fully wired into `scripts/ingest_worker.py`'s `run_ingestion_once()` as a second orchestration stage, activating MATCH-01/02/03 in the live pipeline. `matched_product_id`/`price_points.product_id` slugs are byte-identical to `products._id`, preserving the join contract for Phase 5. No circular imports, no ReDoS risk, no regression to Phase 3's INGEST-01/02/03 contract.

---

_Verified: 2026-07-14_
_Verifier: Claude (gsd-verifier)_
