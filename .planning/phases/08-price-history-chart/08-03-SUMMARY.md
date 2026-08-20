---
phase: 08-price-history-chart
plan: 03
subsystem: frontend
tags: [react, recharts, vitest, testing-library, tokens.css]

# Dependency graph
requires:
  - phase: 08-price-history-chart
    plan: "08-01"
    provides: "PriceHistoryChart.jsx (Recharts LineChart + 2-point-minimum insufficient-history fallback), PriceHistoryChart.module.css, ResizeObserver stub in setupTests.js"
provides:
  - "formatAxisDate, formatTooltipDate, formatAxisPrice, formatTooltipValue — four named, timezone-pinned exports from PriceHistoryChart.jsx"
  - "PriceHistoryChart.test.jsx — formatter unit tests plus a full render-state describe block (empty/one/two/many/null/undefined, no-mutation, class-name)"
  - "UI-SPEC Label typography (fill/fontSize) on XAxis/YAxis ticks and tabular-nums Tooltip itemStyle, entirely token-driven"
affects: [08-04-price-history-chart-integration]

# Actuals (#2632)
actuals:
  tokens: 2300
  tasks: 3
  commits: 5

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Mutation-proof test evidence: temporarily weaken a guard-clause threshold, run the suite to confirm the targeted test fails, then revert before commit — recorded inline as an acceptance-criteria requirement, not just tribal knowledge"
    - "Paraphrase docstring prose that would otherwise literally duplicate a locked user-facing string, to keep acceptance-criteria greps for that string unambiguous (same fix pattern Plan 08-01 applied to products.py route docstrings)"

key-files:
  created:
    - frontend/src/components/PriceHistoryChart.test.jsx
  modified:
    - frontend/src/components/PriceHistoryChart.jsx
    - frontend/src/components/PriceHistoryChart.module.css

key-decisions:
  - "Task 2's TDD cycle found the guard clause from Plan 08-01 (`data.length < 2`, with `!data` short-circuiting first) already handles null/undefined/short-array identically to the target behavior — all 11 render-state tests passed on first run with zero implementation change needed. Investigated per the tdd.md 'RED doesn't fail → investigate' guidance rather than treating it as a red flag: confirmed load-bearing by temporarily weakening the threshold to `< 1`, observing exactly the single-point test fail (1 failed / 10 passed), then reverting before commit."
  - "Fixed a pre-existing (Plan 08-01) acceptance-criteria conflict: the component's top-of-file docstring quoted the locked copy 'Not enough price history yet' verbatim, making the required `grep -c` return 2 instead of 1. Reworded to paraphrase ('the locked insufficient-history copy') — same fix pattern the 08-01 plan applied to products.py docstrings for an identical grep-count collision. Filed under Rule 1 (bug fix) since it blocked an explicit acceptance criterion."
  - "Ran `npm install` in this worktree before any test could execute — node_modules is gitignored per-checkout and worktrees don't share it; install resolved entirely from the existing package-lock.json with zero new/changed packages, so no supply-chain checkpoint was needed."

requirements-completed: [PRICE-07]

coverage:
  - id: D1
    description: "formatAxisDate, formatTooltipDate, formatAxisPrice and formatTooltipValue are named exports, both Intl.DateTimeFormat instances pinned to timeZone: 'UTC', and their exact output strings (including a UTC day-boundary case) are asserted"
    requirement: "PRICE-07"
    verification:
      - kind: unit
        ref: "frontend/src/components/PriceHistoryChart.test.jsx — formatAxisDate/formatTooltipDate/formatAxisPrice/formatTooltipValue describe blocks"
        status: pass
    human_judgment: false
  - id: D2
    description: "Every one of the component's five input states (empty, one point, null, undefined, two-plus points) renders the correct branch, and the component never mutates the array it is given"
    requirement: "PRICE-07"
    verification:
      - kind: unit
        ref: "frontend/src/components/PriceHistoryChart.test.jsx — PriceHistoryChart describe block, 5 tests"
        status: pass
    human_judgment: false
  - id: D3
    description: "The two-point threshold is proven load-bearing: deliberately weakening the guard makes the single-point test fail"
    requirement: "PRICE-07"
    verification:
      - kind: other
        ref: "Manual mutation run recorded in this SUMMARY's Deviations section — guard temporarily changed to `< 1`, 1 failed / 10 passed, then reverted before commit"
        status: pass
    human_judgment: false
  - id: D4
    description: "Axis ticks and tooltip text render at the Label typography role and the tooltip price carries tabular-nums, with every colour/size in the component resolving from tokens.css"
    requirement: "PRICE-07"
    verification:
      - kind: unit
        ref: "grep -c 'var(--font-size-label)' == 3, grep -c 'tabular-nums' == 1, grep -nE hex-color and numeric-fontSize patterns both empty in frontend/src/components/PriceHistoryChart.jsx"
        status: pass
    human_judgment: false
  - id: D5
    description: "Visual confirmation that tick/tooltip text matches the 7d/30d badge label size, the tooltip sits on the surface colour with tabular price digits, and the two open overflow backstops (Y-axis tick width at high prices, X-axis tick crowding over months) are not visibly broken"
    requirement: "PRICE-07"
    verification:
      - kind: manual
        ref: "Task 3 <human-check> block in 08-03-PLAN.md"
        status: pending
    human_judgment: true
    rationale: "Visual typography/token rendering and the two named overflow backstops require a human to open the running app and look at it — the task's own <verify> block designates this a human-check, and .planning/config.json sets workflow.human_verify_mode: 'end-of-phase', so this is deferred to the phase-level UAT pass (same deferral pattern 08-01-SUMMARY.md used for D2)."

duration: 25min
completed: 2026-08-20
status: complete
---

# Phase 8 Plan 03: Chart Test Coverage and UI-SPEC Typography Summary

**PriceHistoryChart's three formatters became named, timezone-pinned exports with exact-string tests; every render branch (empty/one/two/many/null/undefined) is now asserted with a mutation-proof threshold check; and the chart's axis ticks and tooltip now render at the UI-SPEC Label role entirely from tokens.css, with tabular-nums on the tooltip price.**

## Performance

- **Duration:** ~25 min
- **Completed:** 2026-08-20T13:44:00Z
- **Tasks:** 3 (all `type="auto"`; Tasks 1-2 also `tdd="true"`)
- **Files modified:** 3 (1 new test file, 2 modified: component + CSS module)

## Accomplishments

- `formatAxisDate`, `formatTooltipDate`, `formatAxisPrice` (new) and `formatTooltipValue` are now named `export function` exports on `PriceHistoryChart.jsx`, each covered by exact-string unit tests including a UTC day-boundary case (`2026-08-18T23:45:00+00:00` still formats as `Aug 18` regardless of the test machine's local timezone).
- Both `Intl.DateTimeFormat` instances are pinned to `timeZone: 'UTC'`, with the reasoning (price_points are stored/produced in UTC; pinning keeps tick labels identical for every viewer and makes the functions assertable without manipulating `process.env.TZ`) recorded in a doc comment above the formatters.
- `PriceHistoryChart.test.jsx` now has 12 tests: 6 formatter tests plus 6 render-state tests covering empty array, single point, null, undefined, exactly-two-points, and a five-point series proven not to mutate its input (`structuredClone` snapshot comparison) — plus a class-name assertion on the insufficient-history paragraph.
- The two-point threshold's load-bearing status was proven, not assumed: temporarily changed the guard from `data.length < 2` to `< 1`, ran the suite, confirmed exactly the single-point test failed (1 failed, 10 passed), then reverted before committing.
- `XAxis`/`YAxis` tick text and the `Tooltip`'s content, label, and price value now render at the Label typography role (`var(--font-size-label)`, `var(--text-secondary)`/`var(--text-primary)`) with `fontVariantNumeric: 'tabular-nums'` on the tooltip's price digits — every value is a token reference, confirmed by grep (0 numeric `fontSize` literals, 0 hex colors, 3 `var(--font-size-label)` occurrences, exactly 1 `tabular-nums`).
- The CSS module now documents the two UI-SPEC overflow backstops (Y-axis tick width at high prices, X-axis tick crowding over months of accumulated history) as deliberate visual re-checks, left to Recharts' defaults per D-02 rather than silently assumed fine.

## Task Commits

1. **Task 1 RED — failing tests for formatter exports** - `ae96194` (test)
2. **Task 1 GREEN — export + timezone-pin the four formatters** - `ff65541` (feat)
3. **Task 2 — render-state test coverage (all 11 pass immediately)** - `26bea61` (test)
4. **Docstring fix — resolve locked-copy grep double-match** - `8d20cf3` (fix)
5. **Task 3 — UI-SPEC Label typography + tabular-nums tooltip tokens** - `a25022e` (feat)

**Plan metadata:** commit pending (this SUMMARY, committed by this worktree agent per the orchestrator's parallel-execution protocol — STATE.md/ROADMAP.md are owned by the orchestrator, not this agent)

## Files Created/Modified

- `frontend/src/components/PriceHistoryChart.test.jsx` (new) — 12 tests: 4 formatter describe blocks + `PriceHistoryChart` describe block (6 tests)
- `frontend/src/components/PriceHistoryChart.jsx` — 4 named formatter exports, UTC timezone pins, YAxis switched to `formatAxisPrice`, Label-role `tick` props on XAxis/YAxis, token-driven Tooltip `contentStyle`/`labelStyle`/`itemStyle`, docstring reworded to avoid double-matching the locked copy
- `frontend/src/components/PriceHistoryChart.module.css` — added the two-backstop documentation comment; `.insufficient` already filled the frame at `width/height: 100%` centered both ways from Plan 08-01, no change needed there

## Decisions Made

- **Task 2's TDD cycle found no implementation gap.** The guard clause `if (!data || data.length < 2)` from Plan 08-01 already short-circuits on falsy `data` before reading `.length`, so it already treats `null`, `undefined`, and a one-element array identically. All 11 render-state tests passed on the first run with zero production-code change. Per `tdd.md`'s "RED doesn't fail → investigate" guidance, this was verified rather than waved through: the threshold was temporarily weakened to `< 1`, the suite was re-run, and exactly the single-point test failed (1 failed, 10 passed) before the change was reverted — this is the acceptance criterion's required mutation-proof evidence.
- **Fixed a pre-existing acceptance-criteria conflict, filed under Rule 1.** The component's top-of-file docstring (written in Plan 08-01) quoted the locked copy "Not enough price history yet" verbatim in prose, which made this plan's required `grep -c "Not enough price history yet" ...` return 2 instead of 1. Reworded the docstring to paraphrase ("the locked insufficient-history copy") — the same fix pattern Plan 08-01 itself applied to `products.py`'s route docstrings when it hit an identical grep-count collision. No behavior change; prose only.
- Ran `npm install` in this worktree before any test/lint/build command, since `node_modules` is gitignored and worktrees do not share it with the main checkout. Install resolved entirely from the existing `package-lock.json` — 156 packages, no new or upgraded packages — so no supply-chain checkpoint was triggered.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Reworded docstring to stop double-matching the locked insufficient-history copy**
- **Found during:** Task 2, running the acceptance-criteria grep for the locked copy
- **Issue:** The Plan 08-01 docstring quoted "Not enough price history yet" verbatim in a code comment, so `grep -c` matched both the comment and the actual `<p>` element (2 matches, criterion requires exactly 1)
- **Fix:** Reworded the docstring to say "the locked insufficient-history copy" instead of quoting the literal string
- **Files modified:** `frontend/src/components/PriceHistoryChart.jsx`
- **Commit:** `8d20cf3`

**Total deviations:** 1 auto-fixed under Rule 1.
**Impact on plan:** None on behavior — prose-only fix, matching a precedent already set by Plan 08-01's own products.py fix for the identical grep-collision pattern.

## Issues Encountered

- `frontend/node_modules` did not exist in this worktree at start (worktrees do not share `node_modules` with the main checkout, and it's gitignored). Ran `npm install`, which resolved cleanly from `package-lock.json` with no new packages — not a deviation, just an expected worktree-isolation step.

## User Setup Required

None — no external service configuration required for this plan.

## Next Phase Readiness

- All three tasks' automated `<verify>` commands pass: `npm test -- PriceHistoryChart --run` (12/12), `npm test` (full suite, 56/56), `npm run lint` (exit 0), `npm run build` (exit 0).
- Task 3's `<human-check>` (visual confirmation of Label-role sizing, tooltip token styling, and the two named overflow backstops against real long-history data) is deferred to end-of-phase per `.planning/config.json`'s `workflow.human_verify_mode: "end-of-phase"` — recorded as coverage item D5 with `human_judgment: true`, matching the deferral pattern Plan 08-01 already established for its own visual-check item.
- `PriceHistoryChart.jsx`'s public surface (default export + 4 named formatter exports) is unchanged in shape from what Plan 08-01 established — Plan 08-04 (integration) can build on this without any wiring changes.

## Self-Check: PASSED

- FOUND: frontend/src/components/PriceHistoryChart.test.jsx
- FOUND: 4 named exports (`formatAxisDate`, `formatTooltipDate`, `formatAxisPrice`, `formatTooltipValue`) in frontend/src/components/PriceHistoryChart.jsx
- FOUND: commit ae96194 (test)
- FOUND: commit ff65541 (feat)
- FOUND: commit 26bea61 (test)
- FOUND: commit 8d20cf3 (fix)
- FOUND: commit a25022e (feat)

---
*Phase: 08-price-history-chart*
*Completed: 2026-08-20*
