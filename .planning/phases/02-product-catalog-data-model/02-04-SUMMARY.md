---
phase: 02-product-catalog-data-model
plan: 04
subsystem: database
tags: [mongodb, pymongo, jsonschema, timeseries, schema-validation]

# Dependency graph
requires:
  - phase: 02-product-catalog-data-model (plan 01)
    provides: pymongo==4.17.0 and pytest==8.4.2 pinned/installed
  - phase: 02-product-catalog-data-model (plan 02)
    provides: MongoDB Atlas M0 cluster provisioned, MONGODB_URI in .env
provides:
  - "db/init_collections.py: idempotent init_collections(db) function"
  - "products collection: $jsonSchema validator (strict/error), compound index {set_name:1, product_type:1}"
  - "price_points collection: empty native time-series collection reserved for Phase 3 (timeField ts, metaField product_id, granularity hours)"
affects: [02-05, 02-06, phase-03-ingestion]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Create-if-not-exists guard (list_collection_names() check) before create_collection() for both validated and time-series collections"
    - "No top-level side effects on import — collection creation only happens inside explicitly-invoked init_collections(db)"

key-files:
  created: [db/__init__.py, db/init_collections.py]
  modified: []

key-decisions:
  - "products $jsonSchema validator allows null on release_date/msrp/image_url (Pitfall 3, D-02) so Pitch Black's provisional pre-release documents seed cleanly"
  - "additionalProperties intentionally NOT set to false on the validator, permitting future schema extension without a migration"
  - "price_points created empty now with final timeseries options to avoid a data-losing drop-and-recreate migration in Phase 3 (Pitfall 1)"

patterns-established:
  - "db/init_collections.py: idempotent MongoDB collection bootstrap, mirrors scripts/ebay_client.py's no-top-level-side-effects-on-import discipline"

requirements-completed: [CATALOG-02]

coverage:
  - id: D1
    description: "products collection created with a $jsonSchema validator (validationLevel strict, validationAction error) enforcing set_name, product_type (4-value enum incl. booster_bundle), language, display_name, required_keywords, with null permitted on provisional fields"
    requirement: "CATALOG-02"
    verification:
      - kind: other
        ref: "inline smoke check against live MongoDB Atlas: db.command('listCollections', filter={'name': 'products'})['cursor']['firstBatch'][0]['options']['validator'] contains $jsonSchema"
        status: pass
    human_judgment: false
  - id: D2
    description: "products collection has a compound index on {set_name: 1, product_type: 1}"
    requirement: "CATALOG-02"
    verification:
      - kind: other
        ref: "db/init_collections.py source inspection — db.products.create_index([('set_name', ASCENDING), ('product_type', ASCENDING)])"
        status: pass
    human_judgment: false
  - id: D3
    description: "price_points collection exists as a native time-series collection (timeField ts, metaField product_id, granularity hours), created empty and reserved for Phase 3"
    requirement: "CATALOG-02"
    verification:
      - kind: other
        ref: "inline smoke check against live MongoDB Atlas: db.command('listCollections', filter={'name': 'price_points'})['cursor']['firstBatch'][0]['options']['timeseries'] == {timeField: ts, metaField: product_id, granularity: hours}"
        status: pass
    human_judgment: false
  - id: D4
    description: "init_collections(db) is idempotent — re-running it after collections already exist raises no error"
    requirement: "CATALOG-02"
    verification:
      - kind: other
        ref: "inline smoke check against live MongoDB Atlas: second init_collections(db) call on the same throwaway db completed without raising"
        status: pass
    human_judgment: false

duration: 8min
completed: 2026-07-14
status: complete
---

# Phase 02 Plan 04: MongoDB Products + Price-Points Collection Bootstrap Summary

**Idempotent `db/init_collections.py` creating a $jsonSchema-validated, compound-indexed `products` collection and an empty native time-series `price_points` collection, verified live against MongoDB Atlas.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-07-14T04:24:22Z
- **Completed:** 2026-07-14T04:25:45Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- `db/init_collections.py` defines a side-effect-free `init_collections(db)` that idempotently creates `products` with a `$jsonSchema` validator (`validationLevel="strict"`, `validationAction="error"`) enforcing a 4-value `product_type` enum (`booster_pack`/`booster_box`/`etb`/`booster_bundle`) and a compound index on `{set_name: 1, product_type: 1}`.
- `price_points` is created empty as a genuine native time-series collection (`timeField="ts"`, `metaField="product_id"`, `granularity="hours"`), reserved for Phase 3's ingestion worker, avoiding a data-losing drop-and-recreate migration later.
- Live smoke check against the provisioned MongoDB Atlas cluster (throwaway `pokemonview_smoke` database, dropped after the check) confirmed: both collections are created with correct creation-time options, the validator and timeseries options are present exactly as specified, and a second `init_collections(db)` call is a safe no-op.

## Task Commits

Each task was committed atomically:

1. **Task 1: Author db/init_collections.py (products validator+index, price_points time-series)** - `928619a` (feat)
2. **Task 2: Smoke-verify collection creation against the live MongoDB** - no commit (verification-only task; no files modified per plan instruction — inline, uncommitted smoke script run against a throwaway `_smoke` database, dropped afterward)

**Plan metadata:** (this commit, added after SUMMARY.md)

## Files Created/Modified
- `db/__init__.py` - Empty package marker enabling `from db.init_collections import init_collections`
- `db/init_collections.py` - Defines `init_collections(db)`, the `PRODUCTS_JSON_SCHEMA` validator dict, and `PRICE_POINTS_TIMESERIES_OPTIONS`

## Decisions Made
- Followed the plan's explicit schema shape verbatim: `additionalProperties` intentionally left unset (not `false`) so extra fields are permitted without a future migration.
- Used the throwaway database name `pokemonview_smoke` (suffixed `_smoke` per plan instruction) for the Task 2 live verification, dropped both before and after the check to guarantee a clean run and leave no residue.
- Confirmed via a `python3 -c` one-liner (never reading `.env` directly) that `MONGODB_URI` was already present in the environment from Plan 02's provisioning — no `.env` file was read, catted, or modified per the env-file safety rule.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. The live smoke check in Task 2 passed on the first run: both `products` and `price_points` appeared in `list_collection_names()` after `init_collections`, the `products` validator and `price_points` timeseries options matched the plan's spec exactly (MongoDB additionally reported a `bucketMaxSpanSeconds: 2592000` default alongside the three specified timeseries fields — this is MongoDB's own default addition, not something this code set, and does not affect correctness), and a second `init_collections` call raised no error.

## User Setup Required

None - no external service configuration required (MongoDB Atlas connection was already provisioned in Plan 02).

## Next Phase Readiness
- `products` and `price_points` collections are now creatable on any environment via `init_collections(db)`, ready to be invoked by `scripts/seed_catalog.py` (Plan 05) and `tests/conftest.py` (Plan 06).
- The `$jsonSchema` validator is the V5 input-validation security control referenced in the phase's threat model (T-02-01) and will be exercised by the seed script's own upserts.
- No blockers for Plan 05 (seed script) or Plan 06 (test suite).

---
*Phase: 02-product-catalog-data-model*
*Completed: 2026-07-14*

## Self-Check: PASSED

- FOUND: db/init_collections.py
- FOUND: db/__init__.py
- FOUND: commit 928619a
