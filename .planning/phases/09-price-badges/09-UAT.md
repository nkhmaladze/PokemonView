---
status: testing
phase: 09-price-badges
source: [09-VERIFICATION.md]
started: 2026-08-28T01:30:00Z
updated: 2026-08-28T01:30:00Z
---

## Current Test

number: 1
name: Chip family visual parity
expected: |
  All-time range chip visually reads as a member of the same pill-chip family as the trend badges (09-UI-SPEC.md Color D-UI-01).
awaiting: user response

## Tests

### 1. Chip family visual parity
expected: Open a product detail page with several days of history in a running app. Confirm the all-time range chip is the same height, padding, corner radius and text size as the neighbouring 7d/30d chips; its background is the neutral grey rather than green or red; its two dollar amounts have equal-width digits (tabular-nums).
result: [pending]

### 2. Narrow-viewport wrap/crowding check
expected: Narrow the browser window to a phone width on a product detail page and confirm the caption "All-time range (since we started tracking)" wraps cleanly to two lines without overlapping the badge value, and that the badge's two dollar amounts don't break mid-value. Also confirm the all-time range row does not crowd the 24h/7d/30d row at any viewport width.
result: [pending]

### 3. No sold-price language
expected: Read every string this phase adds to the detail page and confirm none of them implies the price figures are completed-sale/sold prices rather than active-listing asking prices.
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
