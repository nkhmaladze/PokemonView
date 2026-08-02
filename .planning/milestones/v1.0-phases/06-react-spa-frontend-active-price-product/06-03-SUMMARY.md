---
phase: 06-react-spa-frontend-active-price-product
plan: 03
subsystem: frontend
tags: [react, intl-relativetimeformat, css-modules, testing-library]

# Dependency graph
requires:
  - phase: 06-01
    provides: Vite + React 19 SPA scaffold, Vitest/Testing Library/jsdom harness, UI-SPEC design tokens as CSS custom properties (src/styles/tokens.css)
provides:
  - src/utils/relativeTime.js — formatRelativeTime(isoString) named export, dependency-free ISO->"X ago" conversion via native Intl.RelativeTimeFormat
  - src/components/FreshnessIndicator.jsx — default export FreshnessIndicator({ asOf }) rendering "Data as of {relative time}", detail-page-only
affects: [06-06]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Native Intl.RelativeTimeFormat over a hand-rolled diff ladder or a date library (date-fns/dayjs/moment) for all relative-time formatting"
    - "TDD RED/GREEN commit split per task, matching the established 06-01/06-02 convention"

key-files:
  created:
    - frontend/src/utils/relativeTime.js
    - frontend/src/utils/relativeTime.test.js
    - frontend/src/components/FreshnessIndicator.jsx
    - frontend/src/components/FreshnessIndicator.module.css
    - frontend/src/components/FreshnessIndicator.test.jsx
  modified: []

key-decisions:
  - "No deviations required — plan's RESEARCH.md code example for formatRelativeTime was implemented near-verbatim, and FreshnessIndicator's copy/styling matched the UI-SPEC Copywriting Contract exactly with no ambiguity to resolve"

patterns-established:
  - "Pattern: relativeTime.js is the single source of relative-time formatting; no component computes its own date diff or calls Intl.RelativeTimeFormat directly (verified by acceptance-criteria grep on FreshnessIndicator.jsx)"

requirements-completed: [PRICE-02]

coverage:
  - id: D1
    description: "formatRelativeTime(iso) converts an hour-old ISO timestamp to an hour-based relative string via native Intl.RelativeTimeFormat"
    requirement: PRICE-02
    verification:
      - kind: unit
        ref: "frontend/src/utils/relativeTime.test.js#returns an hour-based relative string for a timestamp ~2 hours ago"
        status: pass
    human_judgment: false
  - id: D2
    description: "formatRelativeTime(iso) converts a 3-day-old ISO timestamp to a day-based relative string"
    requirement: PRICE-02
    verification:
      - kind: unit
        ref: "frontend/src/utils/relativeTime.test.js#returns a day-based relative string for a timestamp ~3 days ago"
        status: pass
    human_judgment: false
  - id: D3
    description: "formatRelativeTime(iso) falls through to the seconds unit for a timestamp within the last minute"
    requirement: PRICE-02
    verification:
      - kind: unit
        ref: "frontend/src/utils/relativeTime.test.js#returns a seconds-based relative string for a timestamp within the last minute"
        status: pass
    human_judgment: false
  - id: D4
    description: "FreshnessIndicator renders 'Data as of {relative time}' from an asOf prop, delegating all time math to formatRelativeTime"
    requirement: PRICE-02
    verification:
      - kind: unit
        ref: "frontend/src/components/FreshnessIndicator.test.jsx#renders \"Data as of {relative time}\" from an asOf ISO timestamp ~2 hours old"
        status: pass
    human_judgment: false

duration: ~3min
completed: 2026-07-15
status: complete
---

# Phase 6 Plan 03: Data Freshness (relativeTime + FreshnessIndicator) Summary

**Dependency-free ISO-to-"X ago" formatter built on the native `Intl.RelativeTimeFormat` API, plus a `FreshnessIndicator` component rendering "Data as of {relative time}" from `current_price.as_of` — both TDD'd RED-then-GREEN, delivering PRICE-02.**

## Performance

- **Duration:** ~3 min
- **Completed:** 2026-07-15
- **Tasks:** 2/2
- **Files modified:** 5 (all newly created)

## Accomplishments
- `formatRelativeTime(isoString)` implemented per the RESEARCH.md code example almost verbatim: module-level `Intl.RelativeTimeFormat("en", { numeric: "auto" })` instance, a `UNITS` array walked year→month→week→day→hour→minute→second, returning the first unit whose absolute-seconds threshold is met (or seconds as the unconditional floor)
- `relativeTime.test.js` derives all three test inputs (hour/day/second) from `Date.now()` rather than hardcoded absolute dates, keeping the suite deterministic across any run date
- `FreshnessIndicator({ asOf })` renders a single `<p className={styles.freshness}>` element with the literal copy "Data as of " + `formatRelativeTime(asOf)`, imported from `../utils/relativeTime` — no own date math, no absolute timestamp ever rendered (D-09)
- `FreshnessIndicator.module.css` styles `.freshness` with the Label-size token (`--font-size-label: 12px`, `--font-weight-regular: 400`) and `var(--text-secondary)` color, matching the UI-SPEC Copywriting Contract and Layout Notes (detail-page only, D-10)
- Full project test suite (18 tests, 5 files) confirmed green after both tasks — no regressions to 06-01/06-02 output

## Task Commits

1. **Task 1 (RED): failing test for formatRelativeTime** - `6f99161` (test)
2. **Task 1 (GREEN): formatRelativeTime implementation** - `2ab9d56` (feat)
3. **Task 2 (RED): failing test for FreshnessIndicator** - `a464725` (test)
4. **Task 2 (GREEN): FreshnessIndicator implementation** - `3854049` (feat)

**Plan metadata:** (pending — final docs commit follows this summary)

## Files Created/Modified
- `frontend/src/utils/relativeTime.js` - `formatRelativeTime(isoString)` named export, native `Intl.RelativeTimeFormat`, no external date library
- `frontend/src/utils/relativeTime.test.js` - 3 unit tests (hour/day/second cases), inputs derived from `Date.now()`
- `frontend/src/components/FreshnessIndicator.jsx` - default export `FreshnessIndicator({ asOf })`, renders "Data as of {relative time}"
- `frontend/src/components/FreshnessIndicator.module.css` - `.freshness` class, Label typography, secondary text color
- `frontend/src/components/FreshnessIndicator.test.jsx` - 1 unit test asserting both "Data as of" copy and the hour-based relative-time output

## Decisions Made
None beyond the plan as written — both tasks matched 06-RESEARCH.md's code examples and 06-UI-SPEC.md's Copywriting Contract exactly, with no ambiguity requiring a judgment call.

## Deviations from Plan

None - plan executed exactly as written. Both tasks' acceptance-criteria grep checks (native `Intl.RelativeTimeFormat` usage, no date-fns/dayjs/moment dependency, named/default export shapes, `FreshnessIndicator` delegating to `formatRelativeTime` rather than calling `Intl.RelativeTimeFormat` itself) passed on first implementation with no rework.

**Note on local tooling:** this environment's shell `grep` is aliased to `ugrep` with extra flags (`-G --ignore-files --hidden`, etc. via a Claude Code shell shim) that produced an incorrect exit code for the combined `grep -qvi "date-fns\|dayjs\|moment" relativeTime.js` acceptance check (spuriously failing despite 30/31 non-matching lines). Re-running the identical check with `/usr/bin/grep` directly confirmed a correct pass. This is a local shell-shim quirk, not a plan or implementation issue — noted here in case it resurfaces during any future automated verification pass in this same environment.

## Issues Encountered
None beyond the shell-shim grep quirk noted above (resolved by using `/usr/bin/grep` directly for verification; no code changes needed).

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `formatRelativeTime` is available for any future component needing relative-time formatting (e.g. future price-history chart tooltips), though PRICE-02's only mandated consumer is `FreshnessIndicator`.
- `FreshnessIndicator` is ready to be mounted on `ProductDetailPage` (06-06) — it is not yet wired into any page/route (routing is 06-07's scope) and must not be added to list rows (D-10).
- No blockers for downstream plans (06-04 through 06-07).

---
*Phase: 06-react-spa-frontend-active-price-product*
*Completed: 2026-07-15*

## Self-Check: PASSED

All 5 created files confirmed present on disk (frontend/src/utils/relativeTime.js, frontend/src/utils/relativeTime.test.js, frontend/src/components/FreshnessIndicator.jsx, frontend/src/components/FreshnessIndicator.module.css, frontend/src/components/FreshnessIndicator.test.jsx). All 4 task commit hashes (6f99161, 2ab9d56, a464725, 3854049) confirmed present in `git log --oneline --all`.
