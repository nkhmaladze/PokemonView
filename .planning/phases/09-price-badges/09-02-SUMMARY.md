---
phase: 09-price-badges
plan: 02
subsystem: ui
tags: [react, css-modules, price-display, badge]

requires:
  - phase: 06-detail-page
    provides: "TrendBadge.jsx and PriceDisplay.jsx status-first badge/formatter conventions this component mirrors"
provides:
  - "AllTimeRangeBadge.jsx — two-state (ok / insufficient_data) display component for a product's all-time low/high price range"
  - "AllTimeRangeBadge.module.css — token-only stylesheet reusing --trend-flat / --trend-insufficient, zero new tokens"
affects: ["09-03 (backend all_time_range field this component consumes)", "09-04/09-05 (ProductDetailPage wiring)"]

actuals:
  tokens: 1660
  tasks: 2
  commits: 2

tech-stack:
  added: []
  patterns:
    - "Status-first branching before reading value fields (mirrors TrendBadge)"
    - "Per-component local formatCurrency helper (no shared utils/format.js), copied verbatim from PriceDisplay"

key-files:
  created:
    - frontend/src/components/AllTimeRangeBadge.jsx
    - frontend/src/components/AllTimeRangeBadge.module.css
    - frontend/src/components/AllTimeRangeBadge.test.jsx
  modified: []

key-decisions:
  - "Two states only (ok / insufficient_data), no directional branch — an all-time range has no direction, unlike TrendBadge's four states"
  - "En dash (U+2013) separator kept deliberately distinct from the muted em dash (U+2014) glyph to avoid ambiguous single-match text queries elsewhere in the app"
  - "ok state reuses --trend-flat (neutral 'status: ok' token) and --color-bg rather than introducing a new token, per 09-UI-SPEC.md D-UI-01"

patterns-established:
  - "Sibling-not-reuse: when a new data shape doesn't fit an existing badge's prop contract, build a small sibling component that copies the same status-first discipline rather than overloading the existing component's props"

requirements-completed: [PRICE-09]

coverage:
  - id: D1
    description: "AllTimeRangeBadge renders '$low – $high' (en dash) for an ok-status range, low bound first"
    requirement: "PRICE-09"
    verification:
      - kind: unit
        ref: "frontend/src/components/AllTimeRangeBadge.test.jsx#renders the low bound, an en dash separator, then the high bound for an ok range"
        status: pass
    human_judgment: false
  - id: D2
    description: "Equal-bounds range ($X.XX – $X.XX) renders both bounds, never collapsed or suppressed"
    requirement: "PRICE-09"
    verification:
      - kind: unit
        ref: "frontend/src/components/AllTimeRangeBadge.test.jsx#renders both bounds when high equals low"
        status: pass
    human_judgment: false
  - id: D3
    description: "Muted em-dash with aria-label='insufficient data' renders for explicit insufficient_data status, null range, and absent prop"
    requirement: "PRICE-09"
    verification:
      - kind: unit
        ref: "frontend/src/components/AllTimeRangeBadge.test.jsx#renders a muted em-dash with aria-label for explicit insufficient_data status"
        status: pass
      - kind: unit
        ref: "frontend/src/components/AllTimeRangeBadge.test.jsx#renders the muted state without throwing when range is null or the prop is absent"
        status: pass
    human_judgment: false
  - id: D4
    description: "Badge's two states are styled entirely from tokens.css custom properties (--trend-flat, --trend-insufficient, --color-bg, --font-size-label, --line-height-label, --font-weight-regular, --space-xs, --space-sm), zero new tokens, tabular-nums digit alignment"
    requirement: "PRICE-09"
    verification:
      - kind: unit
        ref: "frontend/src/components/AllTimeRangeBadge.test.jsx#ok state's className contains the stylesheet's base class..."
        status: pass
      - kind: other
        ref: "grep -nE '#[0-9A-Fa-f]{3,8}' AllTimeRangeBadge.jsx AllTimeRangeBadge.module.css (0 matches); grep -nE ':[[:space:]]*[0-9]+(px|rem|em)' AllTimeRangeBadge.module.css (0 matches); git diff --stat tokens.css (empty)"
        status: pass
  - id: D5
    description: "Visual placement/spacing/height parity with neighboring 7d/30d trend chips on the product detail page, and the empty-data range shows as an unfilled muted dash rather than an empty chip, on a running app"
    verification: []
    human_judgment: true
    rationale: "Requires visually running the app against a live/seeded product detail page and comparing chip geometry and color by eye per 09-UI-SPEC.md — not determinable from unit tests alone. AllTimeRangeBadge is not yet wired into ProductDetailPage (that wiring is a later plan in this phase), so this check cannot be performed until that wiring lands."

duration: 25min
completed: 2026-08-22
status: complete
---

# Phase 09 Plan 02: AllTimeRangeBadge Summary

**New two-state `AllTimeRangeBadge` component (en-dash-separated `$low – $high` chip or a muted em-dash) styled entirely from existing tokens.css custom properties, with a 6-test suite pinning both states, the equal-bounds edge case, and two deliberate-mutation regressions.**

## Performance

- **Duration:** 25 min
- **Started:** 2026-08-22T15:31:00Z (approx, first file read)
- **Completed:** 2026-08-22T15:56:34Z
- **Tasks:** 2 completed
- **Files modified:** 3 (all newly created)

## Accomplishments
- Built `AllTimeRangeBadge.jsx`, a status-first display formatter that renders a product's all-time low/high price range as `$low – $high` (en dash), or a muted em-dash for `insufficient_data` / null / absent `range` prop
- Built `AllTimeRangeBadge.module.css` with exactly two rules (`.range`, `.range--muted`), reusing `--trend-flat` and `--trend-insufficient` — zero new tokens added to `tokens.css`
- Wrote a 6-test suite (`AllTimeRangeBadge.test.jsx`) covering: ok range, equal-bounds range, explicit insufficient_data, null/absent prop, class-list containment, and stylesheet-class-name containment for both states
- Verified two deliberate mutations (em-dash separator, reversed bound order) each turn 2-3 exact-string tests red, then reverted before commit

## Task Commits

Each task was committed atomically:

1. **Task 1: AllTimeRangeBadge component and its two-state test file** - `5471a72` (feat)
2. **Task 2: Token-only stylesheet for the badge's two states** - `5f86bf1` (feat)

_Note: Task 1 required a small deviation — see below._

## Files Created/Modified
- `frontend/src/components/AllTimeRangeBadge.jsx` - Default-exported component, two states, no directional branch, local `formatCurrency` helper
- `frontend/src/components/AllTimeRangeBadge.module.css` - Two-rule token-only stylesheet (`.range`, `.range--muted`)
- `frontend/src/components/AllTimeRangeBadge.test.jsx` - 6 tests covering all named states plus two class-name assertions

## Decisions Made
- Followed the plan's locked prop contract (`{high, low, status}`) and D-UI-01 color mapping exactly — no deviations from the design decisions.
- Chose to place both mutation-testing checks (separator character, bound order) as manual verification steps run and reverted during Task 1 execution rather than as permanent test-suite entries, per the plan's acceptance-criteria wording ("Temporarily changing... the change is reverted before commit and the observed failure is recorded in the SUMMARY").

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking issue] Missing referenced file blocked Task 1's own test run**
- **Found during:** Task 1
- **Issue:** `AllTimeRangeBadge.jsx` imports `./AllTimeRangeBadge.module.css` by design (mirroring `TrendBadge.jsx`), but the plan schedules creation of that CSS module for Task 2. Running Task 1's required verification (`npm test -- AllTimeRangeBadge --run`, expected to pass with 5 tests per Task 1's own acceptance criteria) failed immediately with a Vite import-resolution error (`Failed to resolve import "./AllTimeRangeBadge.module.css"`), before any test executed — a full-suite failure, not a styling-assertion failure.
- **Fix:** Added a minimal placeholder `AllTimeRangeBadge.module.css` in Task 1 (class name selectors `.range` / `.range--muted` with no declarations, comment explaining it is a placeholder finalized in Task 2), so the component's import resolves and Task 1's 5 tests can run and pass on their own. Task 2 then overwrote this file with the final token-based rules, as originally scoped.
- **Files modified:** `frontend/src/components/AllTimeRangeBadge.module.css` (created in Task 1, finalized in Task 2)
- **Verification:** `npm test -- AllTimeRangeBadge --run` passed 5/5 after the placeholder was added (Task 1), then 6/6 after Task 2 finalized the stylesheet.
- **Committed in:** `5471a72` (Task 1, placeholder), `5f86bf1` (Task 2, final rules)

---

**Total deviations:** 1 auto-fixed (Rule 3 — blocking issue).
**Impact on plan:** No scope creep. The placeholder was a necessary sequencing fix to satisfy Task 1's own acceptance criteria without pulling Task 2's styling work forward; the final file content matches the plan's Task 2 specification exactly.

## Mutation Verification (recorded per acceptance criteria)

- **Separator mutation:** Temporarily changed the en-dash separator (`' – '`) to the em-dash glyph (`' — '`) in `AllTimeRangeBadge.jsx`. Result: 3 of 5 tests failed (`getByText('$129.99 – $172.50')` no longer matched; the rendered text became `$129.99 — $172.50`). Reverted before commit.
- **Bound-order mutation:** Temporarily swapped `range.high` and `range.low` in the ok-state JSX so the high bound rendered first. Result: 2 of 5 tests failed (exact-string queries for `'$129.99 – $172.50'` no longer matched the now-reversed `'$172.50 – $129.99'` output). Reverted before commit.

## Issues Encountered
None beyond the Rule 3 deviation documented above.

## User Setup Required
None - no external service configuration required.

## Known Stubs
None. Both states render real formatted values from the `range` prop with no hardcoded placeholder text or empty-value defaults; the "insufficient data" state is an intentional, spec-locked terminal state (not a stub for future work).

## Deferred / Human Verification

`AllTimeRangeBadge` is not yet wired into `ProductDetailPage.jsx` — that wiring belongs to a later plan in Phase 9 per this plan's `<artifacts_this_phase_produces>` note. Task 2's `<human-check>` verification step (visual parity with the neighboring 7d/30d chips on a running product detail page) cannot be performed until that wiring lands, so it is deferred rather than run against an unwired component. This is tracked as coverage deliverable D5 (`human_judgment: true`) above, not as a stub — the component itself has no missing functionality.

## Next Phase Readiness
`AllTimeRangeBadge.jsx` is ready to be imported and wired into `ProductDetailPage.jsx` by whichever later plan in this phase owns that page (per `09-01-PLAN.md`'s full Phase 9 artifact inventory). Its prop contract (`{high, low, status}`) is locked by `09-UI-SPEC.md` D-UI-01 and does not depend on the backend plan (09-03) landing first — this plan ran independently in wave 1 as planned.

---
*Phase: 09-price-badges*
*Completed: 2026-08-22*
