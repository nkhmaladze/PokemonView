---
phase: 08-price-history-chart
verified: 2026-08-20T13:00:00Z
status: passed
score: 9/9 must-haves verified (across 08-01 truths); all plan-level must_haves verified across 08-01/08-02/08-03/08-04
behavior_unverified: 0
overrides_applied: 0
human_verification:

  - test: "Run the Flask API on port 5001 and `npm run dev` in frontend/, then open a product detail page with 2+ collected price points."
    expected: "Price, badges and meta appear first; a 'Price History' heading appears below the trend badges and above the MSRP/release-date block; a line chart draws with visible dated X-axis ticks, dollar Y-axis ticks and dashed gridlines; hovering the line shows a tooltip with a formatted date and a $X.XX total price."
    why_human: "Visual chart rendering (SVG geometry, gridlines, hover tooltip, dark-theme token resolution) requires a human to open the running app and look at it. Deferred per .planning/config.json's workflow.human_verify_mode: end-of-phase (08-01-PLAN.md Task 2 human-check)."

  - test: "With the app running, open a product detail page with several days of history. Confirm axis tick text and tooltip text match the 7d/30d badge label size; the tooltip sits on the surface colour with no border and tabular-width price digits; the line is accent orange and gridlines are divider grey. Then check the Y-axis dollar labels are not clipped at the highest-priced catalog product, and X-axis date labels are not overlapping at the longest currently-collected history."
    expected: "Typography and token-driven styling render as specified; the two documented overflow backstops (Y-axis tick width at high prices, X-axis tick crowding over long history) are not visibly broken."
    why_human: "Visual typography sizing and two explicitly-documented overflow backstops require eyes on the running app with real accumulated data. Deferred per workflow.human_verify_mode: end-of-phase (08-03-PLAN.md Task 3 human-check)."

  - test: "Open a product detail page and confirm the 'Price History' heading reads as a section label at the same size as the page title but without the orange underline, the chart sits directly below it, and MSRP/release-date follows. Switch to a product with no collected history and confirm the insufficient-history message occupies the same vertical space the chart did, with no visible jump. Reload with the network throttled and confirm price/badges appear before the chart area fills."
    expected: "Section placement, heading weight, fixed-frame non-shifting behaviour, and progressive-load ordering all hold visually under real network conditions."
    why_human: "Layout weight, no-shift-on-state-change, and network-throttled ordering are visual/timing properties that automated DOM tests approximate but do not fully substitute for. Deferred per workflow.human_verify_mode: end-of-phase (08-04-PLAN.md Task 3 human-check)."
---

# Phase 8: Price History Chart Verification Report

**Phase Goal:** Detail page plots the full total-price series from `price_points`, served by a new history endpoint (ROADMAP v1.1, Phase 8)
**Verified:** 2026-08-20T13:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A user opening a product's detail page sees a line chart of total price over time, plotted from every collected point (no downsampling/binning) | ✓ VERIFIED | `PriceHistoryChart.jsx` renders `LineChart`/`Line dataKey="total_price"` over the unmodified `data` array; `get_price_history` applies no limit/window (`api/services/price_service.py:60-108`); prohibition on downsampling is upheld — `chartData` in the component only adds a derived `tsMillis` field via `.map`, never filters/slices (confirmed by test "renders the chart for a longer series without mutating its input", passing) |
| 2 | A user can identify a specific point and read its date/total price via hover/tap tooltip | ✓ VERIFIED | `Tooltip labelFormatter={formatTooltipDate} formatter={formatTooltipValue}` wired in `PriceHistoryChart.jsx`; both formatters have exact-string unit tests (`formatTooltipDate` → `'Aug 18, 2026'`, `formatTooltipValue(172.5)` → `['$172.50', 'Total price']`), all passing. Visual tooltip rendering itself deferred to human-check (see Human Verification). |
| 3 | A product with no/too-few points shows an explicit "not enough history yet" message, not an empty box or crash | ✓ VERIFIED | Guard clause `if (!data || data.length < 2)` renders `Not enough price history yet` (locked copy, `grep -c` = 1); tests cover empty array, single point, null, undefined — all pass; two-point threshold proven load-bearing via a temporary-mutation check recorded in 08-03-SUMMARY.md |
| 4 | Requesting the history endpoint directly returns the raw `price_points` series as time-ordered JSON — chart never recomputes/synthesizes client-side | ✓ VERIFIED | `GET /products/<product_id>/history` → `price_service.get_price_history` → `db.price_points.find({...}, sort=[("ts",1)])`, returns clean `{ts, total_price}` dicts; `tests/test_api_products.py::test_product_history_returns_ordered_series` and 4 more HTTP-boundary tests all pass (confirmed by direct run: 30/30 in scoped backend files) |

### Plan-Level Must-Haves (08-01 through 08-04)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `ts` values are ISO-8601 via `.isoformat()`, never RFC-822/BSON, and always carry a UTC offset | ✓ VERIFIED | `doc["ts"].replace(tzinfo=timezone.utc).isoformat()` in `price_service.py:104` (this is the CR-01 fix from 08-REVIEW.md, confirmed landed); regression pin `assert element["ts"].endswith(("+00:00","Z"))` in both `test_price_history_element_shape` and `test_product_history_returns_ordered_series`, both passing |
| 2 | History fetch never blocks loader-driven content; loading/error states scoped to chart section only, `ProductNotFound` never reached | ✓ VERIFIED | `useEffect` fetch independent of `useLoaderData()`; tests `"shows price, badges and meta before the history request settles"` and `"contains a failed history request to the chart section"` both pass |
| 3 | Cancellation guard discards late/stale responses and actually aborts the in-flight request | ✓ VERIFIED | `AbortController` wired in `ProductDetailPage.jsx` (WR-02 fix); `request()` in `client.js` forwards `signal`; tests `"aborts the in-flight history request on unmount"` and `"discards a history response that settles after unmount"` both pass |
| 4 | `GET /products/<id>` still omits any raw price-point array after the history endpoint exists (D-06) | ✓ VERIFIED | `test_detail_omits_raw_series` and `test_detail_still_omits_raw_series_after_history_endpoint` both pass; `frontend/src/router.jsx` and `api/services/catalog_service.py` have zero commits since phase start (`git log --since=2026-08-18` confirms) |
| 5 | `recharts@3.10.1` installed as a runtime dependency only after human approval of its `[SUS]` verdict | ✓ VERIFIED | `frontend/package.json` `dependencies` has exactly `react`, `react-dom`, `react-router`, `recharts`; 08-01-SUMMARY.md records the approval, carried from a prior run per orchestrator instruction |
| 6 | XAxis uses real elapsed-time scale, not evenly-spaced category ticks (WR-01 fix) | ✓ VERIFIED | `<XAxis dataKey="tsMillis" type="number" scale="time" domain={['dataMin','dataMax']} />` in `PriceHistoryChart.jsx`, derived from a non-mutating `chartData` map |
| 7 | Every colour/size in the chart resolves from `tokens.css` — no hardcoded hex or numeric font size | ✓ VERIFIED | `grep -rn '#[0-9A-Fa-f]{6}'` and `grep -nE "fontSize: *['\"]?[0-9]"` both return zero matches in `PriceHistoryChart.jsx`/`.module.css`; `--color-accent` doc in `tokens.css` explicitly names "price-history chart line" |
| 8 | `total_price` values reach the plotted line unrounded/unmodified (backstop truth) | ✓ VERIFIED | `test_price_history_preserves_stored_precision` asserts a stored `172.55` returns exactly `172.55`; formatters (`formatAxisPrice`/`formatTooltipValue`) only affect display strings, never write back into `data` (confirmed by the no-mutation test) |

**Score:** 4/4 ROADMAP success criteria verified; all plan-level must-haves across 08-01–08-04 verified. 0 behavior-unverified.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `api/services/price_service.py::get_price_history` | New service function | ✓ VERIFIED | Present, substantive, docstring records CR-01/unbounded-response decisions |
| `api/blueprints/products.py` `/products/<product_id>/history` route | New public endpoint | ✓ VERIFIED | Present, thin route → `price_service.get_price_history` → `jsonify`, no None/404 branch as designed |
| `frontend/src/api/client.js::getPriceHistory` | New client function | ✓ VERIFIED | Present, reuses `request()`, forwards `{signal}` (WR-02 fix) |
| `frontend/src/components/PriceHistoryChart.jsx` | New chart component | ✓ VERIFIED | Present, substantive (full Recharts composition + 4 named formatter exports), wired into `ProductDetailPage.jsx` |
| `frontend/src/components/PriceHistoryChart.module.css` | New CSS module | ✓ VERIFIED | `.chartWrap`, `.insufficient` present, token-only |
| `frontend/src/pages/ProductDetailPage.jsx` Price History section | New page section | ✓ VERIFIED | Present between trend badges and meta block, correct `h2`, three-branch render |
| `frontend/package.json` recharts dependency | New runtime dep | ✓ VERIFIED | `recharts@^3.10.1` in `dependencies` |
| `frontend/src/components/PriceHistoryChart.test.jsx` | New test file | ✓ VERIFIED | 12 tests present and passing (verified by direct run) |
| `tests/test_price_service.py` / `tests/test_api_products.py` history cases | New backend tests | ✓ VERIFIED | 6 + 5 new tests present and passing (verified by direct run: 30/30 across the two files) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `products.py` `product_history` route | `price_service.get_price_history(get_db(), product_id)` | direct call, no transformation | ✓ WIRED | `history = price_service.get_price_history(get_db(), product_id); return jsonify(history)` |
| `price_service.get_price_history` | `db.price_points.find({"product_id": ...}, sort=[("ts", 1)])` | equality filter + ascending sort | ✓ WIRED | Confirmed in source; ordering pinned with teeth by a sort-direction-reversal mutation test (08-02-SUMMARY.md) |
| `ProductDetailPage` `useEffect` | `client.getPriceHistory` → `setHistory`/`setHistoryError` → `<PriceHistoryChart data={history} />` | post-mount fetch, never in router.jsx loader | ✓ WIRED | Confirmed by source read; `router.jsx` untouched (git log confirms) |
| `PriceHistoryChart` | `tokens.css` custom properties | inline `stroke`/`fill`/`contentStyle` referencing `var(--...)` | ✓ WIRED | Zero hex literals; `--color-accent` line stroke, `--color-divider` gridlines, `--text-secondary` axes, `--color-surface` tooltip all present |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `PriceHistoryChart` `data` prop | `history` state in `ProductDetailPage.jsx` | `getPriceHistory(productId, {signal})` → real HTTP fetch → Flask route → `price_service.get_price_history` → real MongoDB `price_points.find()` | Yes | ✓ FLOWING |
| Chart `Line dataKey="total_price"` | `chartData` (derived, non-mutating map of `data`) | Same as above | Yes | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Scoped backend tests (this phase's two files) | `python3 -m pytest tests/test_api_products.py tests/test_price_service.py -q` | `30 passed in 126.36s` | ✓ PASS |
| Full frontend suite | `cd frontend && npx vitest run --run` | `Test Files 12 passed (12), Tests 64 passed (64)` | ✓ PASS |
| Frontend lint | `cd frontend && npm run lint` | exit 0 (6 pre-existing `only-export-components` fast-refresh warnings, not errors, 2 of which are in `FilterChips.jsx` predating this phase) | ✓ PASS |
| Frontend build | `cd frontend && npm run build` | `✓ built in 194ms`, exit 0 | ✓ PASS |
| Full backend suite (`pytest -q`, 84 tests) | `python3 -m pytest -q` | `84 passed in 286.37s (0:04:46)` — ran to completion during this verification session (slow/network-bound, consistent with SUMMARYs' notes on ingestion-worker tests hitting real external services, but completed cleanly with 0 failures) | ✓ PASS |
| Named chart/page test IDs exist and pass | `npx vitest run src/components/PriceHistoryChart.test.jsx src/pages/ProductDetailPage.test.jsx --reporter=verbose` | All 26 named tests listed in the plans' acceptance criteria pass individually (spot-checked via verbose output) | ✓ PASS |

**Full-suite confirmation:** The full `pytest -q` run (84 tests, spanning ingestion/matching/catalog tests unrelated to this phase plus the price-history tests) completed during this verification session with **84 passed, 0 failed, 0 errors**, independently confirming the SUMMARYs' own clean full-suite claims rather than merely trusting them.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| PRICE-07 | 08-01, 08-02, 08-03, 08-04 | User can view a line chart of a product's total-price history on its detail page, rendered from price_points | ✓ SATISFIED | All 4 ROADMAP success criteria verified above; `requirements-completed: [PRICE-07]` recorded in all 4 SUMMARYs |

**Orphaned requirements check:** `.planning/REQUIREMENTS.md`'s traceability table maps PRICE-07 to Phase 8 only — no additional IDs are mapped to this phase that were not claimed by a plan. No orphans.

**Note:** `.planning/REQUIREMENTS.md`'s checkbox for PRICE-07 is still `[ ]` and its Status column still reads "Pending" — this is a milestone-tracking artifact (checkboxes/status columns in this project appear to be updated at milestone completion, not per-phase; v1.0's shipped requirements follow the same pattern) rather than evidence the requirement is unmet. Flagged as informational only, not a gap.

### Anti-Patterns Found

Scanned all 13 files this phase created/modified for `TBD|FIXME|XXX|TODO|HACK|PLACEHOLDER`. Zero debt markers found. The only "TBD" occurrences are the pre-existing, intentional fallback copy for a null `release_date` (`ProductDetailPage.jsx:168`, `?? 'TBD'`), not a code-completeness marker.

No stub patterns (`return null`, empty handlers, hardcoded empty arrays feeding render) found in any artifact — all data flows traced back to real MongoDB queries.

### Code Review Findings — Fix Verification

08-REVIEW.md found 1 Critical + 3 Warning issues. 08-REVIEW-FIX.md claims all 4 fixed. Independently re-verified against current source (not just SUMMARY claims):

| Finding | Claimed Fix | Verified in codebase |
|---------|-------------|----------------------|
| CR-01 (naive-datetime timezone bug) | `timezone.utc` attached before `.isoformat()` | ✓ Confirmed at `price_service.py:104`; regression-pinned by `endswith(("+00:00","Z"))` assertions in 2 tests, both passing |
| WR-01 (category-axis time misrepresentation) | Numeric `tsMillis` + `type="number" scale="time"` | ✓ Confirmed in `PriceHistoryChart.jsx`; non-mutation test still passes |
| WR-02 (fetch not actually aborted) | `AbortController` + `signal` forwarding | ✓ Confirmed in `client.js` and `ProductDetailPage.jsx`; new abort-specific test passes |
| WR-03 (tests masked CR-01) | UTC-offset assertions added to 2 backend tests + new frontend TZ-pinned test | ✓ Confirmed present in both backend test files and `PriceHistoryChart.test.jsx`'s "CR-01 regression pin" describe block, all passing |

All 4 fixes independently confirmed landed in the codebase, not just claimed in the fix report.

## Human Verification Required

3 items deferred per `.planning/config.json`'s `workflow.human_verify_mode: "end-of-phase"` setting, harvested from the `<human-check>` blocks in 08-01-PLAN.md, 08-03-PLAN.md, and 08-04-PLAN.md (see YAML frontmatter `human_verification` for full detail):

### 1. End-to-end chart rendering (08-01)

**Test:** Run the Flask API + Vite dev server, open a product detail page with 2+ price points.
**Expected:** Price/badges/meta first; "Price History" heading in correct position; a real line chart with visible dated X-axis ticks, dollar Y-axis ticks, dashed gridlines; hover tooltip shows formatted date + $X.XX.
**Why human:** SVG geometry, hover interaction, and dark-theme token resolution require visual inspection of the running app.

### 2. Typography/token visual contract + overflow backstops (08-03)

**Test:** Open a product detail page with several days of history; compare axis/tooltip text size to 7d/30d badges; check tooltip surface/border/tabular-nums; check line/gridline colors; check Y-axis labels aren't clipped at the highest-priced product; check X-axis labels aren't overlapping at the longest history.
**Expected:** Matches UI-SPEC Label typography role; two documented overflow backstops hold visually.
**Why human:** Visual sizing comparison and two explicitly-deferred overflow backstops need real accumulated data and eyes on the render.

### 3. Section placement/weight + no-shift + network-throttled ordering (08-04)

**Test:** Confirm heading weight without underline, chart placement, insufficient-history message occupying identical space to the chart with no visible jump; reload with network throttled and confirm price/badges appear before the chart fills.
**Expected:** D-03 placement and D-05 progressive-load ordering hold visually under real network conditions.
**Why human:** Layout-shift absence and network-throttled timing are visual/perceptual properties beyond what jsdom-based tests fully substitute for.

## Gaps Summary

No gaps found. Every observable truth (ROADMAP success criteria and plan-level must-haves) is backed by either a passing automated test or direct source-code confirmation, including independent re-verification (not just trusting SUMMARY/REVIEW-FIX claims) that all 4 code-review findings (1 Critical, 3 Warning) were genuinely fixed in the current codebase. The phase is functionally complete; the only remaining item is the standard end-of-phase visual/UAT pass, deferred per project configuration rather than skipped.

---

_Verified: 2026-08-20T13:00:00Z_
_Verifier: Claude (gsd-verifier)_
