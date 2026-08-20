---
status: testing
phase: 08-price-history-chart
source: [08-VERIFICATION.md]
started: 2026-08-20T14:50:00Z
updated: 2026-08-20T14:50:00Z
---

## Current Test

number: 1
name: End-to-end chart rendering
expected: |
  Run the Flask API + Vite dev server, open a product detail page with 2+ price points.
  Price/badges/meta appear first; a "Price History" heading appears in the correct position
  (below trend badges, above MSRP/release-date); a real line chart draws with visible dated
  X-axis ticks, dollar Y-axis ticks, and dashed gridlines; hovering the line shows a tooltip
  with a formatted date and a $X.XX total price.
awaiting: user response

## Tests

### 1. End-to-end chart rendering
expected: Price/badges/meta first; "Price History" heading in correct position; a real line chart with visible dated X-axis ticks, dollar Y-axis ticks, dashed gridlines; hover tooltip shows formatted date + $X.XX.
result: [pending]

### 2. Typography/token visual contract + overflow backstops
expected: Axis/tooltip text size matches 7d/30d badges; tooltip sits on surface color with no border and tabular-width digits; line is accent orange, gridlines are divider grey; Y-axis dollar labels aren't clipped at the highest-priced catalog product; X-axis date labels aren't overlapping at the longest currently-collected history.
result: [pending]

### 3. Section placement/weight + no-shift + network-throttled ordering
expected: "Price History" heading reads as a section label (same size as page title, no orange underline); chart sits directly below it, MSRP/release-date follows; switching to a product with no history shows the insufficient-history message occupying the same vertical space with no visible jump; reloading with network throttled shows price/badges appearing before the chart area fills.
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
