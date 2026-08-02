---
status: complete
phase: 03-active-listing-ingestion-pipeline
source: [03-VERIFICATION.md]
started: 2026-07-14T22:50:00Z
updated: 2026-07-18T05:10:10Z
---

## Current Test

[testing complete]

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
result: pass
evidence: |
  `python3 -m scripts.ingest_worker --once` from repo root — run_id=98ef722977bd41b581e3d5b088fe1119
  status=success products_queried=16 listings_fetched=800 listings_written=800, no traceback, no
  secrets in console output. `db.active_listings.find_one()` returned item_price=74.88,
  shipping_cost=0.0, total_price=74.88 (populated). `db.ingestion_runs.find_one(sort=[("started_at",
  -1)])` returned status=success, finished_at=2026-07-18 05:10:10.578000 (completed run).

## Summary

total: 1
passed: 1
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps
