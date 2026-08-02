---
phase: 05-flask-rest-api-active-price-serving
plan: 03
subsystem: testing
tags: [pytest, flask, pymongo, tdd, nyquist-scaffold]

# Dependency graph
requires:
  - phase: 05-flask-rest-api-active-price-serving (Plan 05-01)
    provides: flask==3.1.3 / flask-cors==6.0.5 installed and human-verified
provides:
  - "api_db/app/client pytest fixtures in tests/conftest.py — the shared test infrastructure Plans 05-04/05/06 build against"
  - "tests/test_price_service.py (6 RED unit tests) — the locked contract for api/services/price_service.py"
  - "tests/test_catalog_service.py (9 RED unit tests) — the locked contract for api/services/catalog_service.py"
  - "tests/test_api_products.py (11 RED integration tests) — the locked contract for api/app.py + blueprints"
affects: [05-04-price-service, 05-05-catalog-service, 05-06-app-and-blueprints, 06-frontend]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Nyquist Wave 0 scaffold-first: all tests authored RED before api/ exists, every from-api import deferred inside test bodies/fixture bodies so pytest --collect-only stays clean"
    - "api_db fixture seeds products via seed_catalog but leaves price_points empty for per-test controlled inserts (differs from catalog_db, which has no analogous need)"
    - "app/client fixtures follow the official Flask app-factory testing pattern (create_app() + app.test_client()), first Flask-specific fixtures in the repo"

key-files:
  created:
    - tests/test_price_service.py
    - tests/test_catalog_service.py
    - tests/test_api_products.py
  modified:
    - tests/conftest.py

key-decisions:
  - "api_db fixture leaves price_points initialized-but-empty (unlike catalog_db's full seed) so each test controls its own gap/tolerance-window price_points scenario"
  - "list_products/get_product_detail response dicts use the exact JSON Response Contract field names (id, not _id) since routes jsonify() them with no further transformation"
  - "requirements SEARCH-01/02, PRICE-01/02/03 NOT marked complete by this plan — REQUIREMENTS.md's own traceability table maps them to Phase 6 (user-observable), not Phase 5 (enabling/serving layer); see Deviations"

patterns-established:
  - "Pattern: RED test file lazy-import discipline — every `from api...` import lives inside a test function body (or fixture body for conftest.py), never at module top level, so pytest --collect-only succeeds before the implementation module exists"

requirements-completed: []  # See Deviations — Phase 5 does not own SEARCH-01/02/PRICE-01/02/03 per REQUIREMENTS.md traceability note; not marked complete here

coverage:
  - id: D1
    description: "api_db/app/client fixtures added to tests/conftest.py, collection stays clean"
    verification:
      - kind: unit
        ref: "pytest tests/ --collect-only -q"
        status: pass
    human_judgment: false
  - id: D2
    description: "tests/test_price_service.py authored RED (6 tests: D-01/02/03/05/06/07)"
    verification:
      - kind: unit
        ref: "pytest tests/test_price_service.py -x (fails RED: ModuleNotFoundError on api.services.price_service)"
        status: pass
    human_judgment: false
  - id: D3
    description: "tests/test_catalog_service.py authored RED (9 tests: D-01/04/08/09/10/11/12 + V5 enum validation)"
    verification:
      - kind: unit
        ref: "pytest tests/test_catalog_service.py -x (fails RED: ModuleNotFoundError on api.services.catalog_service)"
        status: pass
    human_judgment: false
  - id: D4
    description: "tests/test_api_products.py authored RED (11 tests: 200/400/404/500, CORS, no-traceback error handler)"
    verification:
      - kind: unit
        ref: "pytest tests/test_api_products.py -x (fails RED: ModuleNotFoundError on api.app via client fixture)"
        status: pass
    human_judgment: false
  - id: D5
    description: "no regression in pre-existing suites (test_matching.py, test_catalog_schema.py, test_ingest_worker.py)"
    verification:
      - kind: unit
        ref: "pytest tests/test_matching.py tests/test_catalog_schema.py tests/test_ingest_worker.py -q"
        status: pass
    human_judgment: false

duration: 4min
completed: 2026-07-15
status: complete
---

# Phase 5 Plan 3: Nyquist Wave 0 Test Scaffold Summary

**Authored the shared api_db/app/client pytest fixtures plus 26 RED tests (test_price_service.py, test_catalog_service.py, test_api_products.py) that lock the entire Phase 5 API contract — response shapes, status codes, CORS, and error handling — before any api/ code exists.**

## Performance

- **Duration:** 4 min
- **Started:** 2026-07-14T22:52:00-04:00
- **Completed:** 2026-07-14T22:55:54-04:00
- **Tasks:** 3
- **Files modified:** 4 (1 modified, 3 created)

## Accomplishments
- Extended `tests/conftest.py` with `api_db` (seeded 16-product catalog, empty `price_points`, skip-gracefully), `app` (`create_app()` pointed at `pokemonview_test`), and `client` (`app.test_client()`) fixtures — mirroring the `catalog_db`/`matching_db` skip/try-finally/drop-before-and-after pattern exactly
- Authored `tests/test_price_service.py` (6 unit tests, no Flask): D-02 current-price gap-tolerance (no time window), D-01 zero-points-returns-None, D-03 freshness-is-literal-ts, D-05/D-06 trend-baseline tolerance window and insufficient-data, D-07 total_price-only percent-change with zero-baseline guard
- Authored `tests/test_catalog_service.py` (9 unit tests, no Flask): D-08 combinable set/type/q filters, D-10 SET_ORDER grouping (not raw release_date sort), D-09 unverified-products-shown-identically, D-04/D-12 list-carries-price-and-freshness, V5 product_type enum ValueError, plus 4 detail-endpoint tests (total-led price, no_data_yet, unknown-id-returns-None, no-raw-series)
- Authored `tests/test_api_products.py` (11 integration tests via Flask test client): 200 list/filter/search, 200 detail with current_price, 200 no_data_yet (not 404), 404 unknown id, no-raw-series, D-09 unverified-shown-identically, 400 invalid_product_type, 500 internal_error with no-traceback-leak (via monkeypatched service), CORS header present

## Task Commits

Each task was committed atomically:

1. **Task 1: api_db, app, client fixtures in tests/conftest.py** - `901a3ab` (test)
2. **Task 2: RED service-layer unit tests (test_price_service.py + test_catalog_service.py)** - `78b0e44` (test)
3. **Task 3: RED HTTP integration tests (test_api_products.py)** - `c5f7f75` (test)

**Plan metadata:** (this commit)

_Note: this plan's own type is RED-authoring, not TDD RED→GREEN→REFACTOR — no `feat` commit is expected until Plans 05-04/05/06 turn these tests green._

## Files Created/Modified
- `tests/conftest.py` - added `api_db`, `app`, `client` fixtures + updated module docstring
- `tests/test_price_service.py` - new, 6 RED unit tests for `api/services/price_service.py`
- `tests/test_catalog_service.py` - new, 9 RED unit tests for `api/services/catalog_service.py`
- `tests/test_api_products.py` - new, 11 RED integration tests for `api/app.py` + blueprint

## Decisions Made
- `api_db` fixture leaves `price_points` initialized-but-empty (unlike `catalog_db`'s always-seeded pattern) so each test inserts exactly the controlled price_points documents its own gap/tolerance scenario needs, per the plan's explicit instruction
- Response dict shapes in `test_catalog_service.py`/`test_api_products.py` use the plan's locked JSON contract field names (`id`, `set_name`, `product_type`, `current_price.total_price`/`item_price`/`as_of`, `price_status`, `trend_7d`/`trend_30d`) directly, since routes are documented (05-RESEARCH.md Pattern 2) to `jsonify()` the service-layer dict with no further transformation
- `test_error_handler_no_traceback` simulates an internal error via `monkeypatch.setattr(catalog_service, "list_products", ...)` rather than crafting a real crash path, since no route yet exists to naturally trigger one — this is the standard way to test a global error handler without a real bug
- **Did not run `requirements mark-complete` for SEARCH-01/02, PRICE-01/02/03** despite them being listed in this plan's frontmatter `requirements` field — see Deviations below

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written for all three tasks; every acceptance criterion (collection-clean, RED-for-the-right-reason, test counts, contract-keyword greps) passed on first attempt.

### Process Deviation (not a code fix — a state-update judgment call)

**1. Skipped `requirements mark-complete` for this plan's frontmatter `requirements` field**
- **Context:** The plan's frontmatter lists `requirements: [SEARCH-01, SEARCH-02, PRICE-01, PRICE-02, PRICE-03]`, and the standard `<state_updates>` protocol says to mark all frontmatter requirement IDs complete after a plan finishes.
- **Why deviated:** `.planning/REQUIREMENTS.md`'s own traceability table (line 89) explicitly states: "Phase 5 (Flask API serving layer)... own[s] no requirements directly... Phase 5 serves the display requirements (PRICE-01/02/03, SEARCH-01/02) that become user-observable in Phase 6." The traceability table itself maps all five IDs to `Phase 6`, not Phase 5. This plan additionally only authored RED tests — no working API exists yet to actually satisfy any of these requirements. Marking them complete now would misrepresent project state (REQUIREMENTS.md would show "complete" for capabilities with zero implementation).
- **Action:** Left `requirements-completed: []` in this SUMMARY's frontmatter and did not invoke `gsd_run query requirements.mark-complete` for any of the five IDs. Flagging here per Rule 4 spirit (architecturally-significant state decision) even though no code was affected — the plan author should confirm whether the `requirements:` frontmatter field on 05-03/04/05/06 was intended as "enables" rather than "owns," or whether it should be removed from plans 05-03 through 05-05 and reserved solely for 05-06 (the plan that actually turns the HTTP contract green) or for Phase 6.
- **Files modified:** none (state-tracking decision only)
- **Verification:** Confirmed via `grep -n "SEARCH-01\|SEARCH-02\|PRICE-01\|PRICE-02\|PRICE-03\|Phase 5" .planning/REQUIREMENTS.md` — traceability table rows all read `Phase 6 | Pending` (except PRICE-01, already `Phase 6 | Complete` from a prior, separate action not part of this plan).

---

**Total deviations:** 0 auto-fixed code changes; 1 documented state-update judgment call (requirements not marked complete, with rationale).
**Impact on plan:** None on the shipped test scaffold itself — all three tasks match the plan's action/acceptance-criteria text exactly. The only deviation is in the bookkeeping step at the end of execution, chosen to keep REQUIREMENTS.md accurate rather than following the generic protocol verbatim.

## Issues Encountered
None. MongoDB Atlas connectivity (`MONGODB_URI` in `.env`) was live throughout, so all fixture-backed tests ran against a real `pokemonview_test` database rather than skipping — every RED failure was confirmed to be the correct `ModuleNotFoundError: No module named 'api'` (or, for `test_api_products.py`, the same error surfacing through the `client`/`app` fixture chain), not a fixture bug or a MongoDB connectivity problem.

## User Setup Required
None - no external service configuration required (MongoDB Atlas connectivity was already configured in a prior phase).

## Next Phase Readiness
- The full Phase 5 test contract (26 new tests across 3 files, on top of the existing 30) is now locked and collecting cleanly (`pytest tests/ --collect-only -q` → 56 tests, 0 errors)
- Plan 05-04 can proceed directly to implementing `api/services/price_service.py` against `tests/test_price_service.py`
- Plan 05-05 can proceed directly to implementing `api/services/catalog_service.py` against `tests/test_catalog_service.py`
- Plan 05-06 can proceed directly to implementing `api/app.py` + `api/blueprints/products.py` + the global error handler against `tests/test_api_products.py`
- No blockers. Flag for the planner/user: confirm intended semantics of the `requirements:` frontmatter field on Plans 05-03 through 05-06 relative to REQUIREMENTS.md's Phase-6-owns-these traceability note (see Deviations).

---
*Phase: 05-flask-rest-api-active-price-serving*
*Completed: 2026-07-15*

## Self-Check: PASSED

All created/modified files found on disk; all three task commit hashes (901a3ab, 78b0e44, c5f7f75) verified present in git log.
