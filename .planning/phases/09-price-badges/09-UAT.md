---
status: complete
phase: 09-price-badges
source: [09-VERIFICATION.md]
started: 2026-08-28T01:30:00Z
updated: 2026-10-24T23:07:19Z
---

## Current Test

[testing complete]

## Tests

### 1. Chip family visual parity
expected: Open a product detail page with several days of history in a running app. Confirm the all-time range chip is the same height, padding, corner radius and text size as the neighbouring 7d/30d chips; its background is the neutral grey rather than green or red; its two dollar amounts have equal-width digits (tabular-nums).
result: pass — 2026-10-24, headless Brave driven by Playwright against production data (Pitch Black ETB and booster box). All-time chip: 26px tall, padding 4px 8px, radius 4px, 12px/18px text, tabular-nums, background rgb(138,148,166) — identical to the flat 0.0% trend chip's geometry and colour. Not green or red.

### 2. Narrow-viewport wrap/crowding check
expected: Narrow the browser window to a phone width on a product detail page and confirm the caption "All-time range (since we started tracking)" wraps cleanly to two lines without overlapping the badge value, and that the badge's two dollar amounts don't break mid-value. Also confirm the all-time range row does not crowd the 24h/7d/30d row at any viewport width.
result: pass — 2026-10-24, measured at 1280px, 390px and 320px. The caption is 234.8px wide so it fits on one line at every width (it never needs the two-line wrap this check allowed for), the chip stays on one line, there is no horizontal overflow, the 24h/7d/30d row stays on one row, and the all-time row sits 24px below it.

### 3. No sold-price language
expected: Read every string this phase adds to the detail page and confirm none of them implies the price figures are completed-sale/sold prices rather than active-listing asking prices.
result: pass — 2026-10-24, scanned the full rendered text of the ETB and booster box detail pages for sold, sale, sell, completed and purchase; no matches. Marked pass at the user's request after this automated scan; no separate manual read-through was recorded.

## Summary

total: 3
passed: 3
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none]
