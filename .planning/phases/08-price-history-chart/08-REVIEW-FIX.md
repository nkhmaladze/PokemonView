---
phase: 08-price-history-chart
fixed_at: 2026-08-20T14:38:00Z
review_path: .planning/phases/08-price-history-chart/08-REVIEW.md
iteration: 1
findings_in_scope: 4
fixed: 4
skipped: 0
status: all_fixed
---

# Phase 08: Code Review Fix Report

**Fixed at:** 2026-08-20T14:38:00Z
**Source review:** .planning/phases/08-price-history-chart/08-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 4 (1 Critical, 3 Warning — Info-level findings IN-01 through IN-04 out of scope for this pass per `fix_scope: critical+warning`)
- Fixed: 4
- Skipped: 0

**Verification environment:** All fixes were applied, syntax/lint/type-checked, and test-verified inside an isolated git worktree (`gsd-reviewfix/08-54650`, fast-forwarded onto `main` after this run). `frontend/node_modules` was freshly `npm install`ed in the worktree (a fresh worktree checkout carries no installed dependencies). Both the scoped-file and full-suite test results below are reproducible from `main` after this fast-forward.

## Fixed Issues

### CR-01: Price-history chart dates are computed from timezone-ambiguous timestamps and render the wrong calendar date for non-UTC viewers

**Files modified:** `api/services/price_service.py`
**Commit:** `5772486`
**Applied fix:** Attached `timezone.utc` to each `doc["ts"]` before calling `.isoformat()` in `get_price_history`, so every emitted `ts` now ends in `+00:00` instead of being offset-less. This is the scoped, phase-8-only fix the review specified (not the broader `MongoClient(tz_aware=True)` change to `api/app.py`, which is explicitly out of this phase's diff and remains a tracked follow-up alongside `catalog_service.py`'s `as_of` field). Also extended the function's docstring to record the rationale and reference the review finding.
**Verified:** `python -m pytest tests/test_price_service.py -q` (12 passed) and `tests/test_api_products.py -q` (18 passed) immediately after the change; full backend suite re-run after all fixes landed: 84 passed, 0 failed. Tier 1 re-read confirmed the diff; Tier 2 `python3 -c "import ast; ast.parse(...)"` syntax check passed.

### WR-01: Recharts XAxis defaults to a category (evenly-spaced) axis, misrepresenting real elapsed time between price points

**Files modified:** `frontend/src/components/PriceHistoryChart.jsx`
**Commit:** `6297e4c`
**Applied fix:** Precomputed a `tsMillis` numeric epoch field on a derived `chartData` array (never mutating the `data` prop — the existing "renders the chart for a longer series without mutating its input" test still passes) and switched `<XAxis>` to `dataKey="tsMillis" type="number" scale="time" domain={['dataMin', 'dataMax']}`, keeping `formatAxisDate` as the tick formatter (it accepts a numeric epoch via `new Date(ms)` with no change needed).
**Verified:** `npx vitest run src/components/PriceHistoryChart.test.jsx` — 12 passed. `npm run build` succeeded (no type/syntax errors). Full frontend suite re-run after all fixes: 64 passed.

### WR-02: The `useEffect` cancellation guard discards stale results but never actually aborts the underlying fetch

**Files modified:** `frontend/src/api/client.js`, `frontend/src/pages/ProductDetailPage.jsx`, `frontend/src/pages/ProductDetailPage.test.jsx`
**Commit:** `1a0317c`
**Applied fix:**
- `client.js`'s `request()` now accepts an optional `{ signal }` and forwards it to `fetch()` — but only constructs a fetch options object when a signal is actually supplied, so `getProducts()`/`getProductDetail()` (which never pass one) keep calling `fetch(url)` with the exact same single-argument shape the existing `client.test.js` suite asserts on (this guarded against a real regression caught during verification — see below).
- `getPriceHistory(productId, opts)` now forwards an optional options object through to `request()`.
- `ProductDetailPage.jsx`'s `useEffect` now creates an `AbortController`, passes `controller.signal` to `getPriceHistory`, ignores `AbortError` in the `.catch`, and calls `controller.abort()` in the cleanup function — replacing the old `cancelled` boolean flag, which discarded stale results but left the underlying request running to completion.
- Updated `ProductDetailPage.test.jsx`'s `'requests history for the product in the URL'` test (renamed to include ", with an abortable signal") to assert `getPriceHistory` is called with `('p2', { signal: expect.any(AbortSignal) })` instead of the old single-argument form, since the call signature changed. Added a new test, `'aborts the in-flight history request on unmount'`, that asserts `signal.aborted` flips from `false` to `true` after `unmount()` — a stronger, more direct verification of the actual fix than the pre-existing `'discards a history response that settles after unmount'` test (which only checked that a late-resolving mock doesn't produce a console error).
**Verified:** Initial `npx vitest run --run` surfaced 3 failures in `src/api/client.test.js` (`getProducts`/`getProductDetail` calls now included an unexpected `{ signal: undefined }` second argument to `fetch`) — a real regression from the first draft of the fix. Fixed by conditionally omitting the options object when no signal is passed. Re-ran full frontend suite: 62 passed (before WR-03's 2 additional test cases), 0 failed. `npm run build` succeeded both before and after the correction.

### WR-03: Every test fixture for `ts` hand-supplies a UTC offset, so the test suite never exercises the real (offset-less) shape the backend returns — masking CR-01

**Files modified:** `tests/test_price_service.py`, `tests/test_api_products.py`, `frontend/src/components/PriceHistoryChart.test.jsx`
**Commit:** `b2bdcc9`
**Applied fix:**
- Added `assert element["ts"].endswith(("+00:00", "Z"))` to `test_price_history_element_shape` (backend unit test) and the equivalent assertion to `test_product_history_returns_ordered_series` (HTTP integration test) — both would have failed against the pre-CR-01-fix code, since `datetime.fromisoformat()` alone accepts both offset and offset-less strings and never caught the missing offset.
- Added a new `describe` block to `PriceHistoryChart.test.jsx`: `formatAxisDate` under a non-UTC test timezone (`process.env.TZ = 'America/New_York'`, restored via `afterEach`), with two cases — an offset-less timestamp near a UTC day boundary (`'2026-08-18T23:30:00.000'`) renders `'Aug 19'` (the wrong day, demonstrating the pre-fix failure mode end to end), and the same instant with the `+00:00` suffix the fixed backend now always emits renders the correct `'Aug 18'` regardless of the test's local timezone. Confirmed the `TZ` env-var mechanism actually affects `Date`/`Intl` parsing inside this project's vitest+jsdom setup with an isolated probe test before committing to this approach.
**Verified:** `python -m pytest tests/test_price_service.py::test_price_history_element_shape tests/test_api_products.py::test_product_history_returns_ordered_series -q` — 2 passed. `npx vitest run src/components/PriceHistoryChart.test.jsx` — 14 passed (12 original + 2 new). Full suites re-run after this commit: backend `pytest -q` — **84 passed, 0 failed, 0 errors, 0 skipped**; frontend `npx vitest run --run` — **64 passed** across 12 test files. `npm run build` succeeded.

## Skipped Issues

None — all four in-scope findings (CR-01, WR-01, WR-02, WR-03) were fixed and verified. Info-level findings (IN-01 through IN-04) were explicitly out of scope for this `critical+warning` pass per the fix-scope configuration and were not attempted.

---

_Fixed: 2026-08-20T14:38:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
