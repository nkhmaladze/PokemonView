---
status: testing
phase: 03-active-listing-ingestion-pipeline
source: [03-VERIFICATION.md]
started: 2026-07-14T22:50:00Z
updated: 2026-07-14T22:50:00Z
---

## Current Test

number: 1
name: Live eBay Production Browse API ingestion run
expected: |
  Console output shows the run completed with no traceback and non-zero listing counts for
  higher-volume catalog products (0 results for pre-release Pitch Black is acceptable);
  `db.active_listings.find_one()` in the real `pokemonview` DB shows a document with populated
  `item_price`, `shipping_cost`, and `total_price`; `db.ingestion_runs.find_one(sort=[("started_at", -1)])`
  shows a completed run with `status` success/partial and `finished_at` set; no secret (access token,
  MONGODB_URI) appears in console output.
awaiting: user response

## Tests

### 1. Live eBay Production Browse API ingestion run
expected: |
  Re-obtain `EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET` from the eBay Developer Program production keyset,
  blind-append them plus `EBAY_ENV=production` to `.env` (`>>` only — never read/cat/grep/overwrite
  `.env`, per the STATE.md incident rule), then run `python -m scripts.ingest_worker --once` from the
  repo root. Expected: run completes with no traceback, non-zero listing counts for higher-volume
  products, a populated `active_listings` document (item_price/shipping_cost/total_price), and a
  completed `ingestion_runs` document (status success/partial, finished_at set). No secret should
  appear in console output.
result: [pending]

## Summary

total: 1
passed: 0
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps
