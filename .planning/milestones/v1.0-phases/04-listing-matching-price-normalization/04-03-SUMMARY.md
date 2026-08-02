---
phase: 04-listing-matching-price-normalization
plan: 03
subsystem: matching
tags: [rapidfuzz, regex, matching, exclusion, python]

# Dependency graph
requires:
  - phase: 04-listing-matching-price-normalization
    provides: "matching_db pytest fixture and the 14-test Nyquist RED contract in tests/test_matching.py (Plan 04-02); rapidfuzz==3.14.5 installed (Plan 04-01)"
provides:
  - "scripts/matching.py: normalize(), _product_slug(), _canonical_phrase(), match_listing(), check_exclusion() plus FILLER_WORDS/FUZZY_SCORE_CUTOFF/FUZZY_MARGIN/LOT_PATTERNS/DAMAGED_PATTERNS/COUNTERFEIT_PATTERNS module constants"
affects: [04-04-outlier-aggregation-e2e, 04-05-ingest-worker-integration]

# Tech tracking
tech-stack:
  added: []
  patterns: [two-tier keyword-then-fuzzy matching, word-boundary-anchored filler stripping, deferred-import to avoid circular dependency, independent flag-don't-drop exclusion pass]

key-files:
  created: [scripts/matching.py]
  modified: []

key-decisions:
  - "Dropped 'packs'/'bundles' from LOT_PATTERNS' quantity-noun group (04-RESEARCH.md's literal pattern included boxes|packs|etbs|bundles) because catalog display_name text legitimately contains '(6 Packs)' (booster_bundle) and '(36 Packs)' (booster_box) — the literal research pattern would have falsely excluded real booster_bundle/booster_box listings echoing their own official product description, directly conflicting with the locked test_exclusion_does_not_flag_legitimate_bundle test"

patterns-established:
  - "matched_product_id always derived via _product_slug(product), never a literal CATALOG '_id' field (CATALOG entries carry no _id — the slug is computed identically to seed_catalog.py/ingest_worker.py)"

requirements-completed: [MATCH-01, MATCH-02]

coverage:
  - id: D1
    description: "normalize() lowercases, strips filler words via word-boundary regex (preserves 'resealed', strips 'factory sealed'), strips punctuation, collapses whitespace"
    requirement: "MATCH-01"
    verification:
      - kind: unit
        ref: "tests/test_matching.py::test_normalize_word_boundary_preserves_resealed"
        status: pass
    human_judgment: false
  - id: D2
    description: "match_listing() two-tier strict/precision-first match: single Tier-1 keyword candidate -> matched/keyword with matched_product_id == products._id slug; multiple candidates -> unmatched/ambiguous (D-03, never auto-resolved); zero candidates -> bounded Tier-2 RapidFuzz fallback requiring both a score floor and a margin over the runner-up"
    requirement: "MATCH-01"
    verification:
      - kind: unit
        ref: "tests/test_matching.py::test_match_listing_keyword_exact"
        status: pass
      - kind: unit
        ref: "tests/test_matching.py::test_match_listing_fuzzy_fallback"
        status: pass
      - kind: unit
        ref: "tests/test_matching.py::test_match_listing_ambiguous_unmatched"
        status: pass
    human_judgment: false
  - id: D3
    description: "check_exclusion() flags lot/damaged/counterfeit signals with lot->damaged->counterfeit precedence, never flags a legitimate booster_bundle listing (D-06) or minor-cosmetic-wear language (D-08), and uses only simple non-nested bounded-quantifier regexes (ReDoS-safe, T-04-02)"
    requirement: "MATCH-02"
    verification:
      - kind: unit
        ref: "tests/test_matching.py::test_exclusion_lot"
        status: pass
      - kind: unit
        ref: "tests/test_matching.py::test_exclusion_damaged_severe_only"
        status: pass
      - kind: unit
        ref: "tests/test_matching.py::test_exclusion_counterfeit"
        status: pass
      - kind: unit
        ref: "tests/test_matching.py::test_exclusion_does_not_flag_legitimate_bundle"
        status: pass
      - kind: other
        ref: "python -c \"...check_exclusion on a 4000-word title\" completes in ~0.17s (< 1s), no catastrophic backtracking"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-07-15
status: complete
---

# Phase 4 Plan 3: normalize() / match_listing() / check_exclusion() Summary

**Implemented `scripts/matching.py`'s deterministic core: word-boundary-safe `normalize()`, a strict two-tier `match_listing()` (exact keyword rule, then bounded RapidFuzz fallback), and `check_exclusion()`'s ReDoS-safe lot/damaged/counterfeit keyword pass — turning all eight MATCH-01/MATCH-02 Nyquist RED tests GREEN.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-07-15T00:29:00Z
- **Completed:** 2026-07-15T00:41:00Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- `normalize()` lowercases, strips `FILLER_WORDS` via word-boundary-anchored `re.sub` (never plain `.replace()`, which would corrupt "resealed" into "re"), strips punctuation, and collapses whitespace.
- `_product_slug(product)` reproduces `seed_catalog.py`'s/`ingest_worker.py`'s `products._id` slug formula (`f"{set_name}_{product_type}".lower().replace(" ", "-")`) byte-for-byte — `match_listing()` always derives `matched_product_id` this way, never from a nonexistent `CATALOG[...]["_id"]` field.
- `_canonical_phrase(product)` builds a lean `"{set_name} {type phrase}"` string for Tier-2 fuzzy comparison (never catalog `display_name`, whose shared "Pokemon TCG: Mega Evolution-" boilerplate would dilute discrimination); its `PRODUCT_TYPE_SEARCH_TERMS` import is deferred inside the function body specifically to avoid a circular import with `scripts.ingest_worker` once Plan 04-05 wires `run_matching_once` back into it.
- `match_listing(normalized_title)` implements the locked two-tier, precision-first contract: Tier 1 collects every catalog product whose `required_keywords` are all present as substrings; exactly one candidate resolves `matched/keyword`, more than one resolves `unmatched/ambiguous` (D-03 — never auto-resolved), zero candidates fall through to Tier 2's `rapidfuzz.process.extract(..., scorer=fuzz.token_sort_ratio, limit=2)`, accepted only when the top score clears both `FUZZY_SCORE_CUTOFF=90` and beats the runner-up by `FUZZY_MARGIN=5`.
- `check_exclusion(normalized_title)` checks `LOT_PATTERNS` → `DAMAGED_PATTERNS` → `COUNTERFEIT_PATTERNS` in that precedence order, returning at most one reason. All three lists use exclusively simple, non-nested, bounded-quantifier regexes (verified against a 4000-word adversarial title completing in ~0.17s).
- All eight targeted MATCH-01/MATCH-02 tests are GREEN; the remaining six `filter_outliers`/`aggregate_and_write`/`run_matching_once`/`run_ingestion_once` tests correctly remain RED (`ImportError: cannot import name 'filter_outliers'`) — expected, in scope for Plan 04-04/04-05.
- Both import orders (`scripts.ingest_worker` before/after `scripts.matching`) succeed — no circular import introduced.

## Task Commits

Each task was committed atomically:

1. **Task 1: normalize() and the two-tier match_listing() (MATCH-01, D-01/D-03)** - `705c8c7` (feat)
2. **Task 2: check_exclusion() — lot/damaged/counterfeit pass (MATCH-02, D-06/D-08)** - `c16fbfb` (feat)

## Files Created/Modified
- `scripts/matching.py` - New file: `normalize`, `_product_slug`, `_canonical_phrase`, `match_listing`, `check_exclusion` plus `FILLER_WORDS`, `FUZZY_SCORE_CUTOFF`, `FUZZY_MARGIN`, `LOT_PATTERNS`, `DAMAGED_PATTERNS`, `COUNTERFEIT_PATTERNS`

## Decisions Made
- Dropped "packs" and "bundles" from `LOT_PATTERNS`' quantity-noun group. 04-RESEARCH.md's Pattern 2 code example literally specified `\b[2-9]\d*\s*(boxes|packs|etbs|bundles)\b`, but catalog `display_name` text already contains "(6 Packs)" (`booster_bundle`) and "(36 Packs)" (`booster_box`) — a seller title echoing that official product description (e.g. "Booster Bundle 6 Packs") would falsely trigger the lot exclusion under the literal research pattern, directly failing the already-locked `test_exclusion_does_not_flag_legitimate_bundle` test from Plan 04-02's Nyquist RED scaffold. Kept "boxes"/"etbs" in the quantity-noun group since no catalog display name uses that phrasing, and kept every other lot pattern (`lot of`, `job lot`, `wholesale`, `set of N`, `x2`/`2x`) unchanged since none of `test_exclusion_lot`'s six titles depend on the removed sub-pattern.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed "packs"/"bundles" from LOT_PATTERNS' quantity-noun regex group**
- **Found during:** Task 2 (check_exclusion implementation)
- **Issue:** 04-RESEARCH.md's Pattern 2 code example includes `\b[2-9]\d*\s*(boxes|packs|etbs|bundles)\b` in `LOT_PATTERNS`. Implementing it verbatim caused `check_exclusion("chaos rising booster bundle 6 packs")` to return `"lot"` instead of `None`, failing `test_exclusion_does_not_flag_legitimate_bundle` — "6 Packs" is legitimate booster_bundle packaging language (matches the catalog's own `display_name`), not a multi-listing lot signal.
- **Fix:** Restricted the quantity-noun alternation to `(boxes|etbs)` only, removing `packs`/`bundles`. Documented the rationale inline in `scripts/matching.py`.
- **Files modified:** scripts/matching.py
- **Verification:** `test_exclusion_lot` (all 6 lot titles, none of which needed the removed sub-pattern) and `test_exclusion_does_not_flag_legitimate_bundle` both pass.
- **Committed in:** c16fbfb (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Necessary correctness fix — the literal research pattern conflicted with an already-locked Nyquist RED test from the prior wave. No scope creep; every other pattern/behavior matches the plan's action text exactly.

## Issues Encountered
None beyond the deviation documented above.

## User Setup Required
None - no external service configuration required. `rapidfuzz==3.14.5` was already installed and human-verified in Plan 04-01.

## Next Phase Readiness
- `scripts/matching.py` now exposes `normalize`, `match_listing`, `check_exclusion` — the pure, DB-free building blocks Plan 04-04 (Wave 3) composes into `filter_outliers()`, `aggregate_and_write()`, and the `run_matching_once()` orchestrator, turning the remaining six RED tests (`test_outlier_filter_excludes_far_listings`, `test_outlier_filter_skipped_when_too_few`, `test_price_points_median_aggregation`, `test_price_points_skipped_when_zero_included`, `test_run_matching_once_end_to_end`) GREEN.
- Plan 04-05 (Wave 4) wires `run_matching_once` into `scripts/ingest_worker.py`'s `run_ingestion_once()` — the deferred-import pattern in `_canonical_phrase()` was specifically built to support this without a circular-import break.
- No blockers carried forward.

---
*Phase: 04-listing-matching-price-normalization*
*Completed: 2026-07-15*

## Self-Check: PASSED

- FOUND: scripts/matching.py
- FOUND: .planning/phases/04-listing-matching-price-normalization/04-03-SUMMARY.md
- FOUND commit: 705c8c7
- FOUND commit: c16fbfb
