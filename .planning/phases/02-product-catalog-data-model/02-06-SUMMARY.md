---
phase: 02-product-catalog-data-model
plan: 06
subsystem: database
tags: [pymongo, mongodb, seed-script, idempotent-upsert, pytest]

# Dependency graph
requires:
  - phase: 02-product-catalog-data-model
    provides: db/init_collections.py ($jsonSchema validator + compound index + price_points timeseries collection, Plan 02-04), scripts/catalog_data.py (curated CATALOG constant, Plan 02-03), tests/conftest.py + tests/test_catalog_schema.py (RED contract tests, Plan 02-05)
provides:
  - "scripts/seed_catalog.py: seed_catalog(db, catalog) idempotent bulk upsert + main() CLI entrypoint"
  - "Populated products collection in the real pokemonview MongoDB database (16 documents, one per CATALOG entry)"
  - "Full pytest suite (tests/test_catalog_schema.py) green — all 4 contract tests pass"
  - "D-02 Pitch Black post-release re-verification follow-up recorded"
affects: [phase-03-ingestion-worker, phase-04-matching-normalization, phase-05-api-service]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Idempotent seed via bulk_write([UpdateOne(filter, {\"$set\": doc}, upsert=True)]) keyed on a deterministic slug _id — never insert_many"
    - "Copy-before-mutate: seed_catalog() builds a dict(product) copy per entry so the shared CATALOG constant is never mutated with the injected _id/converted release_date"
    - "release_date ISO string -> datetime.fromisoformat() conversion happens at seed time, not at data-authoring time, keeping scripts/catalog_data.py plain/serializable"
    - "warn-don't-crash stderr pattern for provisional (verified=False) catalog entries, reusing Phase 1's convention"

key-files:
  created: [scripts/seed_catalog.py]
  modified: []

key-decisions:
  - "Ran python -m scripts.seed_catalog directly against the real pokemonview Atlas database (not just the test DB) to prove idempotency end-to-end per the plan's explicit two-run requirement"
  - "D-02 Pitch Black post-release re-verification follow-up recorded in this SUMMARY only (no .planning/todos/ directory exists yet in this project, so the plan's fallback instruction — record in SUMMARY — was used instead of adding a todo file)"

patterns-established:
  - "Pattern 2 (idempotent bulk seed via natural-key upsert) is now the canonical seed-script shape for this project — any future seed/backfill script should follow the same UpdateOne(upsert=True) keyed-slug approach, never insert_many"

requirements-completed: [CATALOG-01, CATALOG-02]

coverage:
  - id: D1
    description: "scripts/seed_catalog.py idempotently upserts the curated CATALOG into the validated products collection via bulk_write/UpdateOne(upsert=True), keyed on a deterministic slug _id"
    requirement: "CATALOG-01"
    verification:
      - kind: unit
        ref: "tests/test_catalog_schema.py#test_catalog_completeness"
        status: pass
      - kind: unit
        ref: "tests/test_catalog_schema.py#test_seed_idempotent"
        status: pass
      - kind: integration
        ref: "python -m scripts.seed_catalog (run twice against real pokemonview DB: run 1 upserted=16, run 2 upserted=0 matched=16)"
        status: pass
    human_judgment: false
  - id: D2
    description: "products collection is queryable by set_name alone and by set_name+product_type together via the compound index, and the $jsonSchema validator rejects malformed product_type values"
    requirement: "CATALOG-02"
    verification:
      - kind: unit
        ref: "tests/test_catalog_schema.py#test_query_by_set_and_type"
        status: pass
      - kind: unit
        ref: "tests/test_catalog_schema.py#test_schema_validator_rejects_malformed"
        status: pass
    human_judgment: false
  - id: D3
    description: "Pitch Black's provisional (verified=False) entries emit a non-fatal stderr warning naming the D-02 post-release re-verification follow-up, without crashing the seed"
    verification:
      - kind: integration
        ref: "python -m scripts.seed_catalog stderr output: 'WARNING: the following set(s) were seeded with provisional (verified=False) data: Pitch Black...'"
        status: pass
    human_judgment: false

duration: 10min
completed: 2026-07-14
status: complete
---

# Phase 2 Plan 6: Catalog Seed Script + Full Suite Green Summary

**Idempotent MongoDB seed script (bulk_write/UpdateOne upsert on deterministic slug _id) populates the real `pokemonview.products` collection with all 16 curated catalog entries and turns the full 4-test pytest contract suite green.**

## Performance

- **Duration:** ~10 min
- **Completed:** 2026-07-14T04:34:52Z
- **Tasks:** 2 completed
- **Files modified:** 1 (`scripts/seed_catalog.py`, created)

## Accomplishments
- Authored `scripts/seed_catalog.py` mirroring `scripts/verify_ebay_access.py`'s conventions: module docstring, `main() -> int` + `sys.exit(main())`, `.env`/`os.environ` credential loading, warn-don't-crash stderr pattern
- `seed_catalog(db, catalog)` upserts every entry via `bulk_write([UpdateOne(...), ...])` keyed on a deterministic `f"{set_name}_{product_type}"` slug `_id`, converting `release_date` via `datetime.fromisoformat` and never mutating the shared `CATALOG` constant
- Ran `python -m scripts.seed_catalog` twice against the real Atlas `pokemonview` database: first run reported `matched=0 upserted=16 modified=0`, second run reported `matched=16 upserted=0 modified=0` — idempotency proven against the production database, not just the test fixture
- Confirmed `db.products.count_documents({})` equals `len(CATALOG)` (16 == 16), and that no `insert_many` call exists anywhere in `scripts/` or `db/`
- Drove the full Plan 02-05 contract suite green: `pytest tests/ -x` — `test_catalog_completeness`, `test_seed_idempotent`, `test_schema_validator_rejects_malformed`, `test_query_by_set_and_type` all pass, no interface mismatches required fixing

## Task Commits

Each task was committed atomically:

1. **Task 1: Author scripts/seed_catalog.py (idempotent upsert + main entrypoint)** - `565cc9e` (feat)
2. **Task 2: Run the seed against MongoDB and turn the full test suite green** - no additional commit (verification-only task; ran `python -m scripts.seed_catalog` twice against the real database and `pytest tests/ -x`, both green with no code changes required)

**Plan metadata:** committed separately after this SUMMARY

## Files Created/Modified
- `scripts/seed_catalog.py` - `seed_catalog(db, catalog)` idempotent bulk-upsert function + `main()` CLI entrypoint (`python -m scripts.seed_catalog`)

## Decisions Made
- Ran the seed script against the real `pokemonview` Atlas database (in addition to the test DB fixture path already exercised by `tests/test_catalog_schema.py`) to satisfy the plan's explicit "prove idempotency against the real database, not just the test DB" requirement
- `.planning/todos/` does not exist in this project yet, so the D-02 Pitch Black post-release re-verification follow-up is recorded here in the SUMMARY (per the plan's stated fallback: "if the project tracks todos under `.planning/todos/`") rather than as a todo file

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. No interface mismatches existed between `seed_catalog.py`, `init_collections.py`, `catalog_data.py`, and the test suite — the four contract tests passed on the first `pytest tests/ -x` run.

## D-02 Follow-Up: Pitch Black Post-Release Re-Verification

**Tracked here since no `.planning/todos/` directory exists yet in this project.**

All 4 Pitch Black (ME05) catalog entries were seeded with `verified: False` and `verified_at: None`, per D-02 (pre-release data, set releases 2026-07-17). `python -m scripts.seed_catalog` emits a non-fatal `WARNING:` to stderr on every run naming Pitch Black as provisional. 

**Action required after 2026-07-17:** confirm Pitch Black's actual retail MSRP, release date, and image URLs against real post-release listings, update the four Pitch Black entries in `scripts/catalog_data.py` (`verified: True`, `verified_at: <confirmation datetime>`), and re-run `python -m scripts.seed_catalog` — the idempotent upsert-by-slug will correct the existing documents in place with no duplication.

## User Setup Required

None - no external service configuration required (MongoDB Atlas M0 was already provisioned in Plan 02-02; `MONGODB_URI` already present in `.env`).

## Next Phase Readiness

- Phase 2 (product-catalog-data-model) is now fully complete: `products` collection is populated, validated, indexed, and queryable; `price_points` timeseries collection exists empty, reserved for Phase 3
- Phase 3 (ingestion worker) can now query `db.products.find({"set_name": ..., "product_type": ...})` against real catalog documents to drive eBay Browse API searches, and write into the pre-created `price_points` timeseries collection
- Outstanding follow-up: Pitch Black post-release re-verification (see above), not a blocker for Phase 3 but should be revisited after 2026-07-17
- ~11 of 16 catalog entries still have `image_url=None` (unresolved TCGplayer IDs, carried forward from Plan 02-03) — not a blocker for Phase 3/4, but a known gap for any future frontend product-image work

---
*Phase: 02-product-catalog-data-model*
*Completed: 2026-07-14*

## Self-Check: PASSED

- FOUND: scripts/seed_catalog.py
- FOUND: .planning/phases/02-product-catalog-data-model/02-06-SUMMARY.md
- FOUND: 565cc9e (git log --oneline --all)
