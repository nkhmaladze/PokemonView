---
phase: 02-product-catalog-data-model
plan: 03
subsystem: database
tags: [catalog, data-model, pokemon-tcg, mongodb-ready]

# Dependency graph
requires:
  - phase: 02-product-catalog-data-model (plans 01-02)
    provides: MongoDB schema/collection design (products, price_points) this data module will be seeded into
provides:
  - "scripts/catalog_data.py — module-level CATALOG list[dict] of 16 curated sealed-product entries"
  - "scripts/__init__.py — package marker enabling `from scripts.catalog_data import CATALOG`"
affects: [02-04 (seed_catalog.py), 02-05, 02-06 (test_catalog_schema.py), phase-4-matching]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pure data module with zero top-level side effects on import (no pymongo/network imports)"
    - "Disambiguated required_keywords per product_type (booster_bundle carries 'bundle', booster_box carries 'box'/'display', booster_pack carries neither) to prevent Phase 4 matching cross-contamination"
    - "verified/verified_at fields flag provisional pre-release data (Pitch Black) for later re-confirmation"

key-files:
  created:
    - scripts/catalog_data.py
    - scripts/__init__.py
  modified: []

key-decisions:
  - "Resolved Chaos Rising booster_box MSRP conflict ($144 vs $161.64) to $161.64 via a live Pokemon Center listing snippet"
  - "Confirmed Ascended Heroes has a standard (non-Pokemon-Center-exclusive) booster_box SKU — kept the entry rather than dropping it, MSRP pattern-matched to $161.64 (same 36-pack block price as sibling sets)"
  - "Left ~11 of the 16 entries' TCGplayer product IDs unresolved (image_url=None) rather than fabricating them — TCGplayer's product pages are client-rendered SPAs that return no ID from a plain HTTP fetch, and further search-engine lookups were rate-limited (CAPTCHA) partway through this research pass"

patterns-established:
  - "Pattern: data-only module (catalog_data.py) kept separate from seed logic (seed_catalog.py, a later plan) so it can be diffed/re-run independently once Pitch Black's real post-release data lands"

requirements-completed: [CATALOG-01, CATALOG-02]

coverage:
  - id: D1
    description: "CATALOG constant with 16 entries spanning all 4 in-scope sets and up to 4 product types each, with canonical metadata (set, type, language, release info, msrp, image_url, display_name, required_keywords, verified flag)"
    requirement: "CATALOG-01"
    verification:
      - kind: unit
        ref: "python -c \"from scripts.catalog_data import CATALOG; ... assert 15<=len(CATALOG)<=16 ...\" (plan 02-03 automated verify command)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Each catalog entry carries the full CATALOG-02 metadata shape and disambiguated required_keywords per product type"
    requirement: "CATALOG-02"
    verification:
      - kind: unit
        ref: "python -c keyword-disambiguation check (ad-hoc script, see 02-03-SUMMARY.md Self-Check)"
        status: pass
    human_judgment: false

duration: 20min
completed: 2026-07-13
status: complete
---

# Phase 2 Plan 3: Curated Sealed-Product CATALOG Data Module Summary

**16-entry curated CATALOG (4 sets x 4 product types) as a pure Python data module, with Chaos Rising/Ascended Heroes booster_box MSRP gaps resolved via live web research and Pitch Black entries flagged provisional per D-02.**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-07-13T06:20:00Z (approx)
- **Completed:** 2026-07-13T06:35:23Z
- **Tasks:** 2 completed
- **Files modified:** 2 (both created)

## Accomplishments
- Resolved the two open MSRP questions from 02-RESEARCH.md via live search: Chaos Rising booster_box confirmed at $161.64 (Pokemon Center listing snippet), and Ascended Heroes' standard booster_box SKU confirmed to exist (kept the entry rather than dropping it per D-05 contingency)
- Authored `scripts/catalog_data.py` — a side-effect-free `CATALOG` constant with 16 entries: Chaos Rising, Perfect Order, Ascended Heroes, Pitch Black x {etb, booster_box, booster_bundle, booster_pack}
- Designed `required_keywords` per product type with explicit disambiguating terms (booster_bundle carries "bundle", booster_box carries "box"/"display", booster_pack carries neither) so Phase 4's matching cannot conflate the three
- Flagged all 4 Pitch Black entries `verified=False` per D-02 (pre-release data pending post-2026-07-17 re-confirmation)
- Added `scripts/__init__.py` package marker so `from scripts.catalog_data import CATALOG` resolves for later plans (seed script, tests)

## Task Commits

Each task was committed atomically:

1. **Task 1 (research) + Task 2 (author catalog_data.py)** - `722edc0` (feat) — Task 1 produced no file changes (pure research); its findings are encoded directly into Task 2's commit, per the plan's own framing ("captures findings as inline notes to feed Task 2").

**Plan metadata:** committed separately (see final_commit step below)

## Files Created/Modified
- `scripts/catalog_data.py` - Module-level `CATALOG: list[dict]`, 16 curated sealed-product entries with full CATALOG-02 metadata shape
- `scripts/__init__.py` - Empty package marker enabling `from scripts.catalog_data import CATALOG`

## Decisions Made
- **Chaos Rising booster_box MSRP → $161.64**: Confirmed via a live Pokemon Center listing search-result snippet ("Mega Evolution-Chaos Rising Booster Display Box (36 Packs) $161.64 3362 Reviews SOLD OUT"), resolving 02-RESEARCH.md's Open Question 1 in favor of the higher of the two conflicting figures — consistent with Perfect Order's and Pitch Black's already-cited $161.64.
- **Ascended Heroes booster_box entry kept (not dropped)**: Search results (eBay listings, a dedicated "Ascended Heroes ETB & Booster Box Price: Restock Tracker" tracking article, and TCGplayer's own indexed product listing) confirmed a standard, non-Pokemon-Center-exclusive booster box SKU exists for this set, distinct from the confirmed-exclusive 11-pack ETB variant (which remains correctly excluded per D-05). MSRP is pattern-matched to $161.64 (same 36-pack block price as sibling sets) since no single source directly cited the exact dollar figure — this is documented as MEDIUM rather than HIGH confidence in the module docstring.
- **~11 TCGplayer product IDs left unresolved (`image_url=None`)**: TCGplayer's product pages render entirely client-side (confirmed via direct fetch — the raw HTML is an empty React shell with no product ID/title in server-rendered markup), so IDs could not be extracted from a plain HTTP fetch. A search-engine-based lookup approach worked for the first couple of queries but was then rate-limited (DuckDuckGo CAPTCHA challenge) before all remaining products could be checked. Per the plan's explicit instruction ("If any TCGplayer ID... cannot be confidently resolved, set that field to `None`... rather than fabricating a value"), these fields are `None` rather than guessed. Only the 4 IDs already confirmed in 02-RESEARCH.md are populated (Chaos Rising ETB=684450, Perfect Order booster_box=672394, Perfect Order booster_pack=672398, Ascended Heroes booster_bundle=668541).
- **Per-product release dates for Ascended Heroes**: Kept the set's own base release date (2026-01-30) for booster_box/booster_pack, but used the per-product dates 02-RESEARCH.md already sourced for ETB (2026-02-20) and booster_bundle (2026-04-24), since those two products released later than the set's initial launch.

## Deviations from Plan

None - plan executed exactly as written. Both tasks' acceptance criteria and the plan's automated verify command pass. The unresolved TCGplayer IDs and the MEDIUM-confidence Ascended Heroes booster_box MSRP are explicitly plan-sanctioned outcomes (Task 1's acceptance criteria permit `None` for unresolved fields; Task 1's action explicitly frames the MSRP research as "bounded... not an exhaustive audit"), not deviations.

## Issues Encountered
- TCGplayer's product pages are fully client-side-rendered SPAs (confirmed by direct HTTP fetch returning an empty `<div id="app">` shell) — a plain `curl` fetch cannot recover product IDs from them. Worked around this by using search-engine result snippets instead (successfully recovered the Chaos Rising booster_box MSRP confirmation this way), but that channel became rate-limited (CAPTCHA-gated) partway through the research pass before all ~12 remaining TCGplayer IDs could be checked. Resolved per plan instructions by leaving those `image_url` fields as `None` rather than fabricating IDs — carried forward as a follow-up (see Next Phase Readiness).
- Direct fetches to pokemoncenter.com returned HTTP 403 (DataDome bot protection) — worked around by relying on search-engine result snippets, which do surface Pokemon Center's own listing price text without needing a direct page fetch.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- `scripts/catalog_data.py`'s `CATALOG` constant is ready for Plan 04's `seed_catalog.py` to import and upsert into MongoDB.
- **Follow-up carried forward:** ~11 of 16 entries still have `image_url=None` (unresolved TCGplayer product IDs). A future pass with working search-engine access (or a TCGplayer API key, if the project later obtains one) should resolve these — not a blocker for seeding, since the schema explicitly permits `null` image_url.
- **Follow-up carried forward (already tracked per D-02):** All 4 Pitch Black entries are `verified=False` and must be re-confirmed against real retail data after the set's 2026-07-17 release.
- Ascended Heroes' booster_box MSRP ($161.64) is pattern-matched rather than directly cited at the exact dollar figure — low risk per 02-RESEARCH.md's Assumptions Log (MSRP is a reference-only field, not used in core pricing logic), but worth a quick direct re-check if a future pass has better source access.

---
*Phase: 02-product-catalog-data-model*
*Completed: 2026-07-13*

## Self-Check: PASSED

- FOUND: scripts/catalog_data.py
- FOUND: scripts/__init__.py
- FOUND: 722edc0 (task commit)
