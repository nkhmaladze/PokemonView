---
phase: 05-flask-rest-api-active-price-serving
plan: 07
subsystem: api
tags: [flask, flask-cors, pytest, error-handling, cors, security]

# Dependency graph
requires:
  - phase: 05-flask-rest-api-active-price-serving (Plans 05-05/05-06)
    provides: catalog_service.list_products/get_product_detail, products blueprint, Flask app factory with CORS + global error handler
provides:
  - "InvalidProductTypeError(ValueError) subclass in catalog_service, raised only by the V5 product_type enum check"
  - "Narrowed products blueprint except clause that no longer masks internal ValueErrors as 400s"
  - "Comma-split CORS_ORIGINS parsing so the documented production multi-origin format actually works"
  - "Server-side logging of unhandled 500s via app.logger.exception (no response-body leakage)"
affects: [06-react-spa-frontend, 07-deployment]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Narrow, purpose-specific exception subclasses for 4xx/5xx boundary decisions instead of catching a broad base exception type"
    - "Env-driven CORS origins list parsed into a real list at create_app() call time, not passed as a raw string to Flask-CORS"

key-files:
  created: []
  modified:
    - api/services/catalog_service.py
    - api/blueprints/products.py
    - api/app.py
    - tests/test_api_products.py

key-decisions:
  - "InvalidProductTypeError subclasses ValueError (not a sibling exception) so existing pytest.raises(ValueError) assertions in tests/test_catalog_service.py keep passing unmodified"
  - "sort_key's SET_ORDER.index() deliberately left raising the plain base ValueError — this IS the internal bug the route must let propagate as a 500"
  - "CORS_ORIGINS '*' wildcard dev default preserved as a single-element list (not comma-split) since Flask-CORS treats ['*'] as allow-all"
  - "WR-04 opportunistic logging (app.logger.exception) added inside the existing handle_exception handler rather than a separate before/after_request hook, keeping the change minimal per this gap-closure plan's scope"

patterns-established:
  - "Distinct ValueError subclasses for each validation failure mode a route needs to distinguish, so except clauses narrow to the specific type rather than the base exception"

requirements-completed: []  # Per established Phase 5 convention (05-03/05-06 decisions): SEARCH-01/02, PRICE-01/02/03 are enabling/serving-layer requirements not marked complete until user-observable in Phase 6

coverage:
  - id: D1
    description: "CR-01: internal ValueError (unregistered set_name) surfaces as 500 {'error':'internal_error'}, never masked as 400"
    requirement: null
    verification:
      - kind: unit
        ref: "tests/test_api_products.py#test_unregistered_set_name_returns_500_not_400"
        status: pass
    human_judgment: false
  - id: D2
    description: "CR-01: deliberate V5 enum-validation failure still returns 400 {'error':'invalid_product_type'} via the narrowed InvalidProductTypeError catch"
    requirement: null
    verification:
      - kind: unit
        ref: "tests/test_api_products.py#test_product_type_enum_validation"
        status: pass
      - kind: unit
        ref: "tests/test_catalog_service.py#test_product_type_enum_validation"
        status: pass
    human_judgment: false
  - id: D3
    description: "CR-02: comma-separated CORS_ORIGINS produces a matching Access-Control-Allow-Origin header per configured origin, and does not reflect an unconfigured origin"
    requirement: null
    verification:
      - kind: unit
        ref: "tests/test_api_products.py#test_multi_origin_cors_matches_each_origin"
        status: pass
    human_judgment: false
  - id: D4
    description: "CR-02: wildcard '*' dev default still emits Access-Control-Allow-Origin header (no regression)"
    requirement: null
    verification:
      - kind: unit
        ref: "tests/test_api_products.py#test_cors_header_present"
        status: pass
    human_judgment: false
  - id: D5
    description: "Full pytest suite stays GREEN with no regression across all Phase 2/3/4/5 tests plus the two new regression tests"
    requirement: null
    verification:
      - kind: unit
        ref: "pytest -q (58 passed)"
        status: pass
    human_judgment: false

duration: 12min
completed: 2026-07-15
status: complete
---

# Phase 05 Plan 07: Gap Closure — CR-01 Exception Masking & CR-02 Broken CORS Summary

**Narrowed the products route's except clause to a new `InvalidProductTypeError(ValueError)` subclass so internal ValueErrors surface as 500s, and comma-split `CORS_ORIGINS` into a real per-origin list so the documented production multi-origin format actually works — both proven by regression tests that fail on the pre-fix code.**

## Performance

- **Duration:** 12 min
- **Started:** 2026-07-15T04:02:00Z
- **Completed:** 2026-07-15T04:14:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- CR-01 closed: `catalog_service.py` now raises a distinct `InvalidProductTypeError(ValueError)` only from the V5 `product_type` enum check; the `products` blueprint's except clause narrows to catch only that subclass, so `sort_key`'s internal `SET_ORDER.index()` `ValueError` (an unregistered `set_name`) now propagates untouched to the global `@app.errorhandler(Exception)` and surfaces as a 500, never a misleading 400.
- CR-02 closed: `api/app.py`'s `create_app()` now parses `CORS_ORIGINS` into a real Python list — comma-split for a production multi-origin value, single-element `["*"]` for the wildcard dev default — before passing it to Flask-CORS's `origins=` argument, so the documented comma-separated production format actually reflects a matching `Access-Control-Allow-Origin` header per configured origin (and correctly withholds it for an unconfigured origin).
- WR-04 (opportunistic, low-cost): added `app.logger.exception("Unhandled exception in request")` inside the existing global error handler so unhandled 500s (including the CR-01 case) leave a server-side operational trail, without adding any traceback/exception detail to the JSON response body.
- Two new regression tests added, each proven to fail against the pre-fix code and pass only after its corresponding fix: `test_unregistered_set_name_returns_500_not_400` (CR-01) and `test_multi_origin_cors_matches_each_origin` (CR-02).
- Full `pytest` suite (58 tests: 56 pre-existing + 2 new) is GREEN with no regressions.

## Task Commits

Each task was committed atomically:

1. **Task 1: CR-01 — introduce InvalidProductTypeError and narrow the route's except clause** - `563593f` (fix)
2. **Task 2: CR-02 — comma-split CORS_ORIGINS into a real list** - `19a874f` (fix)

**Plan metadata:** (recorded below in final commit)

## Files Created/Modified
- `api/services/catalog_service.py` - new `InvalidProductTypeError(ValueError)` class; the V5 enum check now raises it instead of the base `ValueError`; `sort_key`'s `SET_ORDER.index()` unchanged (still raises base `ValueError`)
- `api/blueprints/products.py` - `list_products` view's except clause narrowed from base `ValueError` to `catalog_service.InvalidProductTypeError`; docstrings updated to name the specific exception
- `api/app.py` - `CORS_ORIGINS` env value parsed into a real list (comma-split, wildcard preserved) before Flask-CORS initialization; `app.logger.exception(...)` added inside `handle_exception` (WR-04)
- `tests/test_api_products.py` - two new regression tests (`test_unregistered_set_name_returns_500_not_400`, `test_multi_origin_cors_matches_each_origin`); added `import os`

## Decisions Made
- `InvalidProductTypeError` subclasses `ValueError` (not a sibling type) so existing `pytest.raises(ValueError)` assertions in `tests/test_catalog_service.py` keep passing unmodified — is-a relationship preserved.
- Left `sort_key`'s `SET_ORDER.index()` deliberately unguarded — that plain `ValueError` is exactly the internal bug this plan's fix must let propagate as a 500, not a bug to suppress.
- Kept the `"*"` wildcard dev default as a single-element list (`["*"]`) rather than comma-splitting it, since Flask-CORS treats `["*"]` as allow-all and a split would have no functional difference but this makes the special-case explicit.
- Added WR-04 logging inline in the existing `handle_exception` handler (no new hook/module) to keep the change minimal, matching this gap-closure plan's narrow-scope mandate.

## Deviations from Plan

None - plan executed exactly as written. Both tasks' `<action>` steps were followed literally; all acceptance criteria greps and test invocations passed on the first attempt.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Both BLOCKER-level correctness gaps recorded in `05-VERIFICATION.md` (truths #11, #12) and `05-REVIEW.md` (CR-01, CR-02) are now closed and regression-tested.
- Phase 5's serving layer (`api/services/catalog_service.py`, `api/blueprints/products.py`, `api/app.py`) is now safe for Phase 6 (React SPA frontend) to build against: the CORS allowlist will actually function against a deployed frontend origin, and internal server-side bugs will surface as 5xx (visible to monitoring) rather than being silently misreported as 4xx client errors.
- `SEARCH-01/02` and `PRICE-01/02/03` remain unmarked in `REQUIREMENTS.md` per the established Phase 5 convention (enabling/serving layer) — they become user-observable and get marked complete in Phase 6.
- No blockers for Phase 6.

---
*Phase: 05-flask-rest-api-active-price-serving*
*Completed: 2026-07-15*

## Self-Check: PASSED
- FOUND: .planning/phases/05-flask-rest-api-active-price-serving/05-07-SUMMARY.md
- FOUND: 563593f (Task 1 commit)
- FOUND: 19a874f (Task 2 commit)
