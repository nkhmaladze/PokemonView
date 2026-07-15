---
phase: 6
slug: react-spa-frontend-active-price-product
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-15
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Vitest 4.1.10 + @testing-library/react 16.3.2 |
| **Config file** | none yet — Wave 0 must add a `test` block to `frontend/vite.config.js` plus `frontend/src/setupTests.js` |
| **Quick run command** | `npx vitest run` (from `frontend/`) |
| **Full suite command** | `npx vitest run --coverage` (from `frontend/`) |
| **Estimated runtime** | ~10 seconds (small suite, 5 test files, no network calls — all API interaction mocked) |

---

## Sampling Rate

- **After every task commit:** Run `npx vitest run <changed-file>.test.jsx` (targeted)
- **After every plan wave:** Run `npx vitest run` (full frontend suite)
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~10 seconds

---

## Per-Task Verification Map

*Task IDs not yet assigned — planning has not run. The rows below are seeded directly from RESEARCH.md's "Phase Requirements → Test Map" and will be updated in place with real Task IDs (and split further if a plan's task granularity requires it) once `/gsd-plan-phase 6` produces PLAN.md files.*

| Test / Behavior | Green by | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|-----------------|----------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| PriceDisplay renders total_price as headline, item_price always visible as secondary | TBD | TBD | PRICE-01 | V5 | JSX text-node rendering auto-escapes API strings; no `dangerouslySetInnerHTML` | unit | `npx vitest run src/components/PriceDisplay.test.jsx` | ❌ Wave 0 | ⬜ pending |
| FreshnessIndicator/formatRelativeTime renders a human "X ago" string from an ISO `as_of` timestamp | TBD | TBD | PRICE-02 | — | — | unit | `npx vitest run src/utils/relativeTime.test.js` | ❌ Wave 0 | ⬜ pending |
| TrendBadge color-codes positive/negative pct_change and renders a muted dash for status: "insufficient_data" | TBD | TBD | PRICE-03 | — | — | unit | `npx vitest run src/components/TrendBadge.test.jsx` | ❌ Wave 0 | ⬜ pending |
| CatalogPage filters the loaded list live as the user types, and via product_type chip selection | TBD | TBD | SEARCH-01 | V5 | Search text used only as local `.includes()` substring match, never sent as a raw query string | integration | `npx vitest run src/pages/CatalogPage.test.jsx` | ❌ Wave 0 | ⬜ pending |
| ProductDetailPage renders price, trend, and freshness for a mocked loader response; renders a not-found state for a 404 | TBD | TBD | SEARCH-02 | — | — | integration | `npx vitest run src/pages/ProductDetailPage.test.jsx` | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/vite.config.js` — add `test` block (`environment: 'jsdom'`, `globals: true`, `setupFiles`)
- [ ] `frontend/src/setupTests.js` — import `@testing-library/jest-dom` matchers
- [ ] Test tooling install: `npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event jsdom`
- [ ] A lightweight fetch-mocking approach for `api/client.js` in tests — `vi.spyOn(global, 'fetch')` or `vi.mock()` on the `api/client.js` module directly. Do **not** add MSW for just 2 endpoints — more infrastructure than this phase's scope justifies.

---

## Manual-Only Verifications

All phase behaviors have automated verification — no manual-only checks identified.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
