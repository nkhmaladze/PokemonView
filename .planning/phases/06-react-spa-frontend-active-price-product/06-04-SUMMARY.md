---
phase: 06-react-spa-frontend-active-price-product
plan: 04
subsystem: ui
tags: [react, vitest, testing-library, controlled-components, css-modules]

# Dependency graph
requires:
  - phase: 06-react-spa-frontend-active-price-product (Plan 01)
    provides: Vite + React 19 scaffold, Vitest/Testing Library/jsdom harness, tokens.css design tokens
provides:
  - "SearchBar — controlled, instant, no-debounce free-text input (default export SearchBar({ value, onChange }))"
  - "FilterChips — single-select-per-group product_type and set_name toggle chips (default export FilterChips({ productType, onProductType, setName, onSetName }), plus exported PRODUCT_TYPE_OPTIONS/SET_OPTIONS constants)"
affects: [06-05]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Controlled, presentational components own zero fetch/network/product-list state — they only emit filter intent via onChange/onProductType/onSetName callbacks, leaving CatalogPage (06-05) as the sole owner of filter state and in-memory filtering (D-14)"
    - "Chip toggle semantics: clicking the already-active chip in a group calls its handler with null (toggle-off); clicking any other chip calls the handler with that chip's raw value (single-select-per-group)"
    - "Controlled-input TDD pattern: test file wraps the controlled component in a local stateful React wrapper so userEvent.type can drive real keystroke-by-keystroke behavior without the input value reverting on every render"

key-files:
  created:
    - frontend/src/components/SearchBar.jsx
    - frontend/src/components/SearchBar.module.css
    - frontend/src/components/SearchBar.test.jsx
    - frontend/src/components/FilterChips.jsx
    - frontend/src/components/FilterChips.module.css
    - frontend/src/components/FilterChips.test.jsx
  modified: []

key-decisions:
  - "PRODUCT_TYPE_OPTIONS/SET_OPTIONS raw values copied verbatim from api/services/catalog_service.py's VALID_PRODUCT_TYPES and SET_ORDER (read directly this session) rather than re-derived from UI-SPEC prose, guaranteeing byte-exact API vocabulary with no invented product types"
  - "SearchBar.test.jsx introduces a small local ControlledSearchBar test wrapper (not part of the shipped component) so userEvent.type exercises the component the way CatalogPage will actually use it — a genuinely controlled input, not a static value/no-op-onChange fixture that would silently revert every keystroke"

patterns-established:
  - "Pattern: presentational filter/search controls are pure controlled components with zero internal state and zero fetch — CatalogPage (06-05) owns all filter state, in-memory filtering, and network access"

requirements-completed: [SEARCH-01]

coverage:
  - id: D1
    description: "SearchBar is a controlled instant-search text input: bound to value/onChange, locked placeholder, accessible name, and every keystroke fires onChange immediately with no submit/debounce (D-12/D-14)"
    requirement: SEARCH-01
    verification:
      - kind: unit
        ref: "frontend/src/components/SearchBar.test.jsx#fires onChange with each typed character immediately, no submit/debounce"
        status: pass
      - kind: unit
        ref: "frontend/src/components/SearchBar.test.jsx#renders a controlled text input bound to the value prop with the locked placeholder"
        status: pass
      - kind: unit
        ref: "frontend/src/components/SearchBar.test.jsx#has an accessible name so it is queryable by role"
        status: pass
    human_judgment: false
  - id: D2
    description: "FilterChips renders exactly the four product_type chips (booster_pack, booster_box, booster_bundle, etb) and four set_name chips (Pitch Black, Chaos Rising, Perfect Order, Ascended Heroes), using catalog_service.py's exact raw values, as single-select-per-group toggles"
    requirement: SEARCH-01
    verification:
      - kind: unit
        ref: "frontend/src/components/FilterChips.test.jsx#exports the exact four raw product_type values (VALID_PRODUCT_TYPES, no invented types)"
        status: pass
      - kind: unit
        ref: "frontend/src/components/FilterChips.test.jsx#exports the exact four set names (SET_ORDER)"
        status: pass
      - kind: unit
        ref: "frontend/src/components/FilterChips.test.jsx#clicking an inactive product_type chip calls onProductType with its raw value"
        status: pass
      - kind: unit
        ref: "frontend/src/components/FilterChips.test.jsx#clicking the already-active product_type chip calls onProductType(null) (toggle off)"
        status: pass
      - kind: unit
        ref: "frontend/src/components/FilterChips.test.jsx#clicking a set chip calls onSetName with its raw value, and toggles off when already active"
        status: pass
      - kind: unit
        ref: "frontend/src/components/FilterChips.test.jsx#applies the active class to the currently-selected product_type chip only"
        status: pass
    human_judgment: false

# Metrics
duration: ~10min
completed: 2026-07-15
status: complete
---

# Phase 06 Plan 04: Search & Filter Controls Summary

**SearchBar (controlled, instant, no-debounce text input) and FilterChips (single-select product_type + set_name toggle groups using catalog_service.py's exact raw enum values) — the interactive half of SEARCH-01, both fully unit-tested and ready for CatalogPage (06-05) to wire into live in-memory filtering.**

## Performance

- **Duration:** ~10 min
- **Completed:** 2026-07-15
- **Tasks:** 2/2
- **Files modified:** 6 (all created)

## Accomplishments
- `SearchBar` — a controlled `<input>` bound to `value`/`onChange`, locked placeholder "Search by product name or set…", `aria-label="Search products"`, no internal state, no submit button, no debounce/setTimeout — proven by a test that types "Box" and asserts `onChange` fired on every keystroke with the running string
- `FilterChips` — two toggle-chip rows built from exported `PRODUCT_TYPE_OPTIONS` (`booster_pack`/`booster_box`/`booster_bundle`/`etb`, human-labeled) and `SET_OPTIONS` (`Pitch Black`/`Chaos Rising`/`Perfect Order`/`Ascended Heroes`), each a single-select-per-group `<button>` toggle: click an inactive chip → its raw value; click the active chip again → `null`
- Both components style per UI-SPEC (accent focus ring on search, accent bg + `#0B0D12` text on active chips, 44px min tap targets) using only `src/styles/tokens.css` custom properties, no hardcoded values
- TDD RED→GREEN for both tasks; full frontend suite (7 files, 29 tests) green and `vite build` clean after this plan

## Task Commits

Each task was committed atomically (TDD RED/GREEN split):

1. **Task 1 (RED): failing test for SearchBar** - `954eeb3` (test)
2. **Task 1 (GREEN): SearchBar implementation** - `9211b7f` (feat)
3. **Task 2 (RED): failing test for FilterChips** - `56cb711` (test)
4. **Task 2 (GREEN): FilterChips implementation** - `ae98479` (feat)

**Plan metadata:** (pending — final docs commit follows this summary)

_TDD tasks: each is a test → feat commit pair; no refactor commit needed for either task._

## Files Created/Modified
- `frontend/src/components/SearchBar.jsx` - controlled instant-search input, default export `SearchBar({ value, onChange })`
- `frontend/src/components/SearchBar.module.css` - accent focus ring, 44px min tap target, surface background
- `frontend/src/components/SearchBar.test.jsx` - 3 tests: value/placeholder binding, accessible name, keystroke-by-keystroke onChange via a local controlled-wrapper pattern
- `frontend/src/components/FilterChips.jsx` - single-select toggle chip groups, default export `FilterChips({ productType, onProductType, setName, onSetName })`, exported `PRODUCT_TYPE_OPTIONS`/`SET_OPTIONS`
- `frontend/src/components/FilterChips.module.css` - pill chip styling, active accent bg + dark text, inactive secondary surface, 44px min tap height
- `frontend/src/components/FilterChips.test.jsx` - 8 tests: exact raw-value exports, label rendering (both groups), toggle-on/toggle-off click behavior, active-class targeting

## Decisions Made
- Read `api/services/catalog_service.py` directly this session to copy `VALID_PRODUCT_TYPES`/`SET_ORDER` verbatim into `PRODUCT_TYPE_OPTIONS`/`SET_OPTIONS` rather than trusting UI-SPEC prose paraphrase, per the plan's own `key_links` requirement (no invented product-type values).
- Added a local `ControlledSearchBar` wrapper inside `SearchBar.test.jsx` (test-only, not shipped) so `userEvent.type` could drive genuinely controlled-input keystroke behavior — a fixed `value`/no-op `onChange` fixture would have caused React to revert the DOM value after every simulated keystroke, making multi-character typing untestable.

## Deviations from Plan

None - plan executed exactly as written. Both components' raw values, JSX/CSS structure, and toggle semantics matched the plan's `<action>` blocks with no ambiguity requiring a Rule 1-4 judgment call.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `SearchBar` and `FilterChips` are ready for `CatalogPage` (06-05) to import, hold `query`/`productType`/`setName` state for, and apply against the loader-fetched product array via `useMemo` (D-14) — no rework needed on either component's props contract.
- `PRODUCT_TYPE_OPTIONS`/`SET_OPTIONS` are exported and reusable by any future component needing the same human-label mapping (e.g. a detail-page breadcrumb), avoiding a second hardcoded copy of the API vocabulary.
- No blockers. Full frontend suite (7 test files, 29 tests) green; `vite build` clean.

---
*Phase: 06-react-spa-frontend-active-price-product*
*Completed: 2026-07-15*

## Self-Check: PASSED

All 6 created files confirmed present on disk (SearchBar.jsx, SearchBar.module.css, SearchBar.test.jsx, FilterChips.jsx, FilterChips.module.css, FilterChips.test.jsx). All 4 task commit hashes (954eeb3, 9211b7f, 56cb711, ae98479) confirmed present in `git log --oneline --all`.
