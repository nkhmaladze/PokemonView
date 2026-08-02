---
phase: 02-product-catalog-data-model
plan: 05
subsystem: testing
tags: [pytest, pymongo, mongodb, test-fixture, tdd-scaffold]

requires:
  - phase: 02-product-catalog-data-model (Plan 02-04)
    provides: db/init_collections.py's products $jsonSchema validator + compound index and price_points time-series collection (the schema this suite's fixture bootstraps against)
  - phase: 02-product-catalog-data-model (Plan 02-03)
    provides: scripts/catalog_data.py's curated CATALOG list (the fixture data this suite validates)
provides:
  - pytest.ini with pythonpath = . so scripts/ and db/ resolve during test collection
  - tests/conftest.py catalog_db fixture (dedicated pokemonview_test database, lazy imports, MONGODB_URI skip guard)
  - tests/test_catalog_schema.py with four RED contract tests mapped 1:1 to CATALOG-01/CATALOG-02
affects: [02-06 (seed script implementation turns these tests green)]

tech-stack:
  added: []
  patterns:
    - "Lazy-import project modules (db.*, scripts.seed_catalog) inside pytest fixtures/test bodies, not at module top level, so --collect-only succeeds before implementation modules exist (Nyquist Wave 0 scaffold-first)"
    - "Dedicated _test-suffixed MongoDB database for integration tests, dropped before and after each test run"

key-files:
  created:
    - pytest.ini
    - tests/conftest.py
    - tests/test_catalog_schema.py
  modified: []

key-decisions:
  - "Deferred scripts.seed_catalog import from module top level into test_seed_idempotent's function body (plan's own fallback instruction), since scripts/seed_catalog.py does not exist until Plan 02-06 and a top-level import would break --collect-only"
  - "catalog_db fixture pytest.skips (not errors) when MONGODB_URI is unset, degrading gracefully per plan spec"
  - "Test database is pokemonview_test, dropped (products + price_points) both at fixture setup and teardown for isolation (T-02-05)"

requirements-completed: [CATALOG-01, CATALOG-02]

coverage:
  - id: D1
    description: "pytest scaffold (pytest.ini + tests/conftest.py) that resolves scripts/ and db/ packages and provides a dedicated-test-database fixture"
    verification:
      - kind: unit
        ref: "python -m py_compile tests/conftest.py && grep pythonpath pytest.ini"
        status: pass
    human_judgment: false
  - id: D2
    description: "Four catalog contract tests authored and collectible (test_catalog_completeness, test_seed_idempotent, test_schema_validator_rejects_malformed, test_query_by_set_and_type)"
    requirement: "CATALOG-01"
    verification:
      - kind: integration
        ref: "pytest tests/test_catalog_schema.py --collect-only -q (4 tests collected)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Tests intentionally RED until Plan 02-06's seed_catalog implementation lands (fixture setup fails on missing scripts.seed_catalog module)"
    requirement: "CATALOG-02"
    verification:
      - kind: integration
        ref: "pytest tests/test_catalog_schema.py -q (4 errors: ModuleNotFoundError: scripts.seed_catalog, expected/by-design)"
        status: pass
    human_judgment: false

duration: 5min
completed: 2026-07-14
status: complete
---

# Phase 02 Plan 05: Catalog Contract Test Scaffold Summary

**Authored a discoverable four-test pytest suite (test_catalog_completeness, test_seed_idempotent, test_schema_validator_rejects_malformed, test_query_by_set_and_type) plus a dedicated pokemonview_test-database fixture, intentionally RED until Plan 06's seed script lands.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-07-14T04:26:46Z
- **Completed:** 2026-07-14T04:30:51Z
- **Tasks:** 2 completed
- **Files modified:** 3 (pytest.ini, tests/conftest.py, tests/test_catalog_schema.py)

## Accomplishments
- `pytest.ini` created with `pythonpath = .` so `scripts` and `db` packages resolve during test collection/execution
- `tests/conftest.py` defines a `catalog_db` fixture targeting a dedicated `pokemonview_test` database — never the real `pokemonview` catalog — with lazy imports of `db.init_collections`/`scripts.seed_catalog`/`scripts.catalog_data` so `pytest --collect-only` succeeds before those modules exist
- `tests/test_catalog_schema.py` authors the four CATALOG-01/CATALOG-02 contract tests, each consuming `catalog_db`; confirmed 4 tests collect cleanly and confirmed the suite fails RED (not a collection error) with `ModuleNotFoundError: scripts.seed_catalog` when actually run — exactly the intended Wave 0 scaffold-first state

## Task Commits

Each task was committed atomically:

1. **Task 1: Create pytest.ini and the shared test-database fixture (tests/conftest.py)** - `1fdf638` (feat)
2. **Task 2: Author the four catalog contract tests (tests/test_catalog_schema.py)** - `92bee5d` (test)

**Plan metadata:** (this commit)

## Files Created/Modified
- `pytest.ini` - `[pytest]` section with `pythonpath = .` and `testpaths = tests`
- `tests/conftest.py` - `catalog_db` fixture: dedicated `pokemonview_test` database, drops `products`/`price_points` before and after, skips when `MONGODB_URI` unset, lazily imports and calls `init_collections` + `seed_catalog`
- `tests/test_catalog_schema.py` - four contract tests: completeness (count/set_name/product_type/no-duplicate-pairs), seed idempotency (re-run count unchanged), schema-validator rejection (invalid `product_type` raises pymongo write error), query-by-set-and-type (compound index query + `index_information()` check)

## Decisions Made
- Deferred the `scripts.seed_catalog` import out of the test module's top level into `test_seed_idempotent`'s function body — a top-level import would break `pytest --collect-only` before Plan 02-06 creates that module. `scripts.catalog_data.CATALOG` and `pymongo.errors` stayed at module top level since `catalog_data.py` already exists (Plan 02-03).
- Confirmed via a live run (`pytest tests/test_catalog_schema.py -q`) that the fixture reaches its `MONGODB_URI`-present branch and fails specifically at the `scripts.seed_catalog` import — proof this is scaffold-first RED, not a broken fixture.

## Deviations from Plan

None - plan executed exactly as written. The plan explicitly anticipated the top-level-import-vs-collect-only tension and specified the fallback ("if top-level imports would break `--collect-only` before the modules exist, defer them into each test body") — that fallback was applied for `seed_catalog` only, exactly as scoped.

## Issues Encountered
None. `pytest`/`pymongo` were already installed from Plan 02-01, and `MONGODB_URI` was already configured from Plan 02-02, so the live test run reached the expected RED failure point cleanly on the first attempt.

## User Setup Required
None - no external service configuration required. `MONGODB_URI` was already provisioned in a prior plan.

## Next Phase Readiness
- The four-test contract scaffold is fully authored and discoverable; Plan 02-06 must implement `scripts/seed_catalog.py` (idempotent `bulk_write` upsert keyed on a deterministic slug `_id`) to turn all four tests green.
- `db/init_collections.py` (Plan 02-04) and `scripts/catalog_data.py` (Plan 02-03) are already in place and consumed by the fixture without modification.
- 02-VALIDATION.md's Per-Task Verification Map already referenced this plan's ID/wave (02-05-T2 → 02-06-T2) at authoring time — no further edit needed there.

---
*Phase: 02-product-catalog-data-model*
*Completed: 2026-07-14*

## Self-Check: PASSED

- FOUND: pytest.ini
- FOUND: tests/conftest.py
- FOUND: tests/test_catalog_schema.py
- FOUND: .planning/phases/02-product-catalog-data-model/02-05-SUMMARY.md
- FOUND: 1fdf638 (Task 1 commit)
- FOUND: 92bee5d (Task 2 commit)
