---
phase: 08-price-history-chart
plan: 04
subsystem: frontend
tags: [react, vitest, testing-library, recharts, css-tokens]

# Dependency graph
requires:
  - phase: 08-price-history-chart
    plan: 01
    provides: "ProductDetailPage.jsx's Price History section, its useEffect fetch with cancellation guard, and PriceHistoryChart.jsx — the vertical slice this plan pins with tests"
provides:
  - "Five new ProductDetailPage tests locking D-05's progressive-load ordering, the two non-success states' exact copy inside a non-shifting frame, the cancellation guard's observable half, and the section's placement/heading level"
  - "A deferred-promise test helper (frontend/src/pages/ProductDetailPage.test.jsx) reusable by future tests needing to assert an in-flight state before settling a mock"
  - "tokens.css's --color-accent reserved-for documentation extended to record the price-history chart line as a sanctioned consumer"
affects: []

# Actuals (#2632)
actuals:
  tokens: 1950
  tasks: 3
  commits: 3

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Module-level deferred-promise helper ({ promise, resolve, reject }) for asserting an in-flight fetch state synchronously before deciding how the mock settles — makes ordering properties (like D-05) assertable instead of only end-state properties"

key-files:
  created: []
  modified:
    - frontend/src/pages/ProductDetailPage.test.jsx
    - frontend/src/pages/ProductDetailPage.jsx
    - frontend/src/pages/ProductDetailPage.module.css
    - frontend/src/styles/tokens.css

key-decisions:
  - "Task 1's three new tests were added alongside (not replacing) the two similar tests Plan 08-01 already wrote — the plan said 'add', and the two sets assert overlapping but non-identical things (08-01's tests check the price headline only; this plan's tests additionally check both trend badges, MSRP, chart-testid absence, and route-errorElement absence). No redundant test was removed."
  - "Task 2's cancellation guard, section placement, and CSS typography contract were already fully correct from Plan 08-01's implementation — this plan's job here was almost entirely to add the missing observable tests and two explanatory comments (above the effect, and on .historyChartFrame), not to change behavior."
  - "Backend pytest -q failures encountered during Task 3 verification were diagnosed as a shared-infrastructure collision, not a defect: all failures/errors were pymongo.errors.OperationFailure ('namespace ... already exists') or CollectionInvalid from concurrent sibling worktree agents (Plans 08-02/08-03) racing drop_collection/create_collection against the same live MongoDB Atlas pokemonview_test database. This plan touches zero backend files (Task 3 is a comment-only tokens.css change), so it cannot be the cause. Documented rather than endlessly retried, per the fix-attempt-limit guidance and consistent with the identical issue 08-01-SUMMARY.md already recorded."

requirements-completed: [PRICE-07]

coverage:
  - id: D1
    description: "The detail page's price headline, trend badges and meta block are present on first paint, before the price-history request settles; the chart section shows 'Loading price history…' inside the fixed frame while in flight"
    requirement: "PRICE-07"
    verification:
      - kind: unit
        ref: "frontend/src/pages/ProductDetailPage.test.jsx#shows price, badges and meta before the history request settles"
        status: pass
    human_judgment: false
  - id: D2
    description: "A rejected history request shows the exact locked error copy in the chart section while price, badges and meta stay rendered, with no chart-testid and no route-level ProductNotFound copy reached"
    requirement: "PRICE-07"
    verification:
      - kind: unit
        ref: "frontend/src/pages/ProductDetailPage.test.jsx#contains a failed history request to the chart section"
        status: pass
    human_judgment: false
  - id: D3
    description: "getPriceHistory is called with the productId from the route's URL parameters, exactly once"
    requirement: "PRICE-07"
    verification:
      - kind: unit
        ref: "frontend/src/pages/ProductDetailPage.test.jsx#requests history for the product in the URL"
        status: pass
    human_judgment: false
  - id: D4
    description: "A history response that settles after unmount is discarded (the observable half of the cancellation guard) with no console.error"
    requirement: "PRICE-07"
    verification:
      - kind: unit
        ref: "frontend/src/pages/ProductDetailPage.test.jsx#discards a history response that settles after unmount"
        status: pass
    human_judgment: false
  - id: D5
    description: "The Price History section renders between the 7d/30d trend badges and the MSRP/release-date meta block, as an h2 (not h1)"
    requirement: "PRICE-07"
    verification:
      - kind: unit
        ref: "frontend/src/pages/ProductDetailPage.test.jsx#places the Price History section between the trend badges and the meta block"
        status: pass
    human_judgment: false
  - id: D6
    description: "The first-paint ordering guarantee has a failing-mutation proof — moving the price section to render only after history settles makes the test fail"
    verification:
      - kind: other
        ref: "Manually mutated the ternary's guard to `history !== null && product.price_status === 'ok'`, ran the suite (6 of 9 ProductDetailPage tests failed, including the target first-paint test), then reverted; confirmed 9/9 pass again post-revert"
        status: pass
    human_judgment: false
  - id: D7
    description: "tokens.css's --color-accent documentation names the price-history chart line among its reserved uses, comment-only"
    requirement: "PRICE-07"
    verification:
      - kind: other
        ref: "grep -c 'price-history chart line' frontend/src/styles/tokens.css == 1; git diff -- frontend/src/styles/tokens.css shows only comment-line changes"
        status: pass
    human_judgment: false
  - id: D8
    description: "Full backend pytest suite passes with 0 failures/skipped — phase gate for both halves"
    requirement: "PRICE-07"
    verification:
      - kind: integration
        ref: "python3 -m pytest -q, run 3 times"
        status: fail
    human_judgment: true
    rationale: "All three runs failed with pymongo.errors.OperationFailure / CollectionInvalid ('namespace already exists', 'collection already exists') — the exact signature of concurrent worktree agents racing drop_collection/create_collection against the same shared MongoDB Atlas pokemonview_test database. ps aux confirmed sibling pytest processes (Plans 08-02/08-03) were running concurrently during two of the three attempts; the third attempt still collided despite starting in a momentarily-clear window, consistent with the other agents starting their own runs mid-flight. This plan modifies zero backend files (Task 3's diff is tokens.css comments only), so the failures cannot originate from this plan's changes. A human (or the orchestrator, sequentially post-merge) should re-run `pytest -q` once with no other worktree agent active to get a true signal — see 08-01-SUMMARY.md's Issues Encountered for the identical prior occurrence of this same infrastructure limitation."

duration: ~50min
completed: 2026-08-20
status: complete
---

# Phase 8 Plan 04: Progressive-Load Integration & Typography Contract Summary

**Five new ProductDetailPage tests pinning D-05's progressive-load ordering, the loading/error states' locked copy inside a non-shifting frame, the cancellation guard's observable behavior, and the section's placement/heading level — plus the tokens.css accent-consumer documentation update.**

## Performance

- **Duration:** ~50 min
- **Completed:** 2026-08-20T12:06:37Z
- **Tasks:** 3
- **Files modified:** 4 (0 new)

## Accomplishments

- Added a module-level `deferred()` test helper to `ProductDetailPage.test.jsx` that exposes a promise's own `resolve`/`reject`, making D-05's ordering property (loader-driven content painted before the history fetch settles) assertable via a synchronous pre-settlement check.
- Three new tests pin the progressive-load contract: first paint shows price/badges/MSRP plus the "Loading price history…" text before the request settles; a rejected request shows the exact "Couldn't load price history. Try refreshing the page." copy while keeping price/badges/MSRP rendered and never reaching the route's `ProductNotFound` boundary; and the history fetch is keyed on the URL's `productId`.
- Performed and reverted the plan's required failing-mutation proof: temporarily gating the price section on `history !== null` made 6 of 9 tests fail (including the target first-paint test), confirming the test suite actually detects a broken ordering guarantee — not just a passing tautology.
- Two more tests pin the cancellation guard's observable half (a response resolving after `unmount()` produces no `console.error`) and the section's placement/heading role (renders between the `7d` trend label and `MSRP:`, as an `h2`).
- Confirmed and documented (via new inline comments) the existing 4-piece cancellation guard in `ProductDetailPage.jsx` and the fixed-height rationale on `.historyChartFrame` in `ProductDetailPage.module.css` — both were already correct from Plan 08-01's implementation; this plan's job was to make them observable and explain the why.
- Extended `tokens.css`'s `--color-accent` inline documentation to record the price-history chart line as a sanctioned accent consumer, plus a note on why the chart is not colored by price direction — comment-only, zero token values or names touched.

## Task Commits

1. **Task 1 — progressive-load ordering, error containment, URL-keyed fetch** - `83d656f` (test)
2. **Task 2 — cancellation guard and section placement/typography** - `b41a6fb` (test)
3. **Task 3 — tokens.css accent-consumer documentation** - `606bf5c` (docs)

**Plan metadata:** commit pending (this SUMMARY; STATE/ROADMAP update deferred to the orchestrator's post-wave protocol per worktree convention — this worktree agent does not commit STATE.md/ROADMAP.md itself)

## Files Created/Modified

- `frontend/src/pages/ProductDetailPage.test.jsx` - Added `deferred()` helper and five new tests (progressive-load ordering, error containment, URL-keyed fetch, post-unmount discard, section placement/heading)
- `frontend/src/pages/ProductDetailPage.jsx` - Added a comment above the history `useEffect` explaining the cancellation guard's navigate-away-mid-request rationale (T-08-10); no behavior change
- `frontend/src/pages/ProductDetailPage.module.css` - Added a comment to `.historyChartFrame` recording why its height is fixed; no rule change
- `frontend/src/styles/tokens.css` - Extended `--color-accent`'s reserved-for comment with "price-history chart line" and a note on `PriceHistoryChart`'s single accent-colored `Line` stroke; no token value/name changed

## Decisions Made

- Added the three Task 1 tests alongside Plan 08-01's two similar-but-narrower tests rather than replacing them — the plan's action explicitly says "Add three tests," and the new tests assert strictly more (badges, MSRP, chart-testid absence, route-error absence) than the originals.
- Task 2's cancellation guard (4-piece: `cancelled` flag, two `if (!cancelled)` guards, cleanup) and CSS typography contract (`.sectionHeading`, `.historyChartFrame`, `.historyMessage`, `.detail__historySection`) were already fully conformant from Plan 08-01 — verified via the acceptance-criteria greps rather than rewritten, keeping this plan's diff to tests plus two explanatory comments.
- Diagnosed the recurring `pytest -q` failures as a shared-Atlas-database concurrency artifact from parallel worktree agents (confirmed via `ps aux` showing sibling `pytest -q` processes, and via the exact `pymongo.errors.OperationFailure: namespace ... already exists` / `CollectionInvalid` signatures — a MongoDB race condition, not a logic failure) rather than attempting an architectural fix (e.g., per-worktree test DB naming) that would be out of this plan's scope and could destabilize sibling agents' concurrently-running suites.

## Deviations from Plan

None requiring Rules 1-4. One process-level note, documented above under Decisions Made and in coverage item D8: `pytest -q` could not be verified green within this plan's execution window due to a pre-existing, previously-documented (08-01-SUMMARY.md) test-isolation limitation shared by all three parallel worktree agents in this wave — not caused by, or fixable within, this plan's file-content changes.

**Total deviations:** 0 auto-fixed under Rules 1-4.
**Impact on plan:** None on file content. The backend pytest gate (Task 3's acceptance criteria, and the phase-level `<verification>` block) could not be independently confirmed green from this worktree; see Issues Encountered.

## Issues Encountered

- `frontend/node_modules` was not present in this worktree at start (a fresh worktree checkout); ran `npm install` before any test/lint/build command — not a deviation, just required setup.
- `python3 -m pytest -q` was attempted three times over this plan's execution. All three attempts produced failures/errors whose stack traces are exclusively `pymongo.errors.OperationFailure` ("namespace pokemonview_test.products already exists, but with different options", "Collection pokemonview_test.price_points already exists.") and `pymongo.errors.CollectionInvalid` ("collection active_listings already exists") — the signature of two or more processes concurrently calling `drop_collection`/`create_collection` against the same live MongoDB Atlas `pokemonview_test` database (`tests/conftest.py`'s `TEST_DB_NAME` is a single hardcoded name shared across all worktrees pointed at the same `MONGODB_URI`). `ps aux` confirmed sibling `pytest -q` processes running from other worktree paths during two of the three attempts. This exact issue was already documented as a non-blocking, pre-existing environmental artifact in `08-01-SUMMARY.md`'s Issues Encountered section. Recommend the orchestrator (or a human) run `pytest -q` once, sequentially, with no other worktree agent active, to get an authoritative signal before treating the phase gate as unmet — this plan's own changes (a tokens.css comment) cannot be the cause of a MongoDB collection-creation race.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- All four plans in Phase 8 (08-01 tracer, 08-02 backend hardening, 08-03 frontend polish, 08-04 this plan's integration/typography pinning) are now complete from this worktree's perspective. The vertical slice's ordering guarantees (D-05), error containment, cancellation safety, and typography/color contract are all now covered by automated tests in addition to the implementation Plan 08-01 shipped.
- The deferred backend `pytest -q` gate (D8) should be re-run once by the orchestrator after this wave's worktrees are merged and no sibling agent is concurrently hitting the shared test database, to close out the phase-level `<verification>` requirement with a clean signal.
- The plan's `<human-check>` (visual confirmation of section placement, heading weight, fixed-frame non-shifting behavior, and progressive-load network-throttled ordering) remains deferred to end-of-phase per `.planning/config.json`'s `workflow.human_verify_mode: "end-of-phase"` setting, consistent with Plan 08-01's same deferral.

## Self-Check: PASSED

- FOUND: frontend/src/pages/ProductDetailPage.test.jsx (deferred helper + 5 new tests)
- FOUND: frontend/src/pages/ProductDetailPage.jsx (effect comment)
- FOUND: frontend/src/pages/ProductDetailPage.module.css (.historyChartFrame comment)
- FOUND: frontend/src/styles/tokens.css ("price-history chart line" — 1 match)
- FOUND: commit 83d656f (test)
- FOUND: commit b41a6fb (test)
- FOUND: commit 606bf5c (docs)

---
*Phase: 08-price-history-chart*
*Completed: 2026-08-20*
