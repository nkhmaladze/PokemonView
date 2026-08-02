---
phase: 01-ebay-api-feasibility-gate
fixed_at: 2026-07-18T04:36:42Z
review_path: .planning/phases/01-ebay-api-feasibility-gate/01-REVIEW.md
iteration: 1
findings_in_scope: 7
fixed: 6
skipped: 1
status: partial
---

# Phase 01: Code Review Fix Report

**Fixed at:** 2026-07-18T04:36:42Z
**Source review:** .planning/phases/01-ebay-api-feasibility-gate/01-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 7 (CR-01, CR-02, CR-03, WR-01, WR-02, WR-03, WR-04 — the 2 Info findings were out of scope for this fix pass)
- Fixed: 6
- Skipped: 1

## Fixed Issues

### CR-01: verify_ebay_access.py reproduces the exact `shippingCost: null` crash that ebay_client.total_cost() was hardened against

**Files modified:** `scripts/verify_ebay_access.py`
**Commit:** 5cebf27
**Applied fix:** Replaced the chained `shipping_options[0].get("shippingCost", {}).get("value", "0.00")` (which crashes with `AttributeError` when `shippingCost` is present but `None`) with the same hardened idiom already used in `ebay_client.total_cost()`: `(shipping_options[0].get("shippingCost") or {}).get("value")`, falling back to `"0.00"` only when the resolved value is `None`.

### CR-02: `categoryId` extraction crashes with IndexError when `categories` is present but empty

**Files modified:** `scripts/verify_ebay_access.py`
**Commit:** 9bb1a56
**Applied fix:** Changed `item.get("categories", [{}])[0].get("categoryId")` to `categories = item.get("categories") or [{}]` followed by `categories[0].get("categoryId")`, matching the `or` idiom already used correctly for `shippingOptions` on the preceding line.

### CR-03: `search_sealed_listings()` hardcodes the production Browse API host, breaking the script's own documented sandbox path

**Files modified:** `scripts/ebay_client.py`, `scripts/verify_ebay_access.py`
**Commit:** d34a0f4
**Applied fix:** Added an `env: str = "production"` parameter to `search_sealed_listings()` in `scripts/ebay_client.py`, mirroring `get_app_token()`'s host-selection logic (`host = "api.ebay.com" if env == "production" else "api.sandbox.ebay.com"`), and updated the request URL to use the resolved host. Updated the call site in `scripts/verify_ebay_access.py` to pass `env=env`. The default value of `"production"` was chosen deliberately so `scripts/ingest_worker.py`'s existing call site (`search_sealed_listings(access_token, query)`, no `env` argument) is unaffected — confirmed via `tests/test_ingest_worker.py` passing unchanged after the fix.

### WR-01: `.gitignore` only excludes the literal `.env` filename, not common variants

**Files modified:** `.gitignore`
**Commit:** de3a6ea
**Applied fix:** Added `.env.*` and `!.env.example` below the existing `.env` line, so common variants (`.env.local`, `.env.production`, etc.) are ignored while the checked-in `.env.example` template remains tracked.

### WR-03: No deduplication of captured listings across `CATALOG_QUERIES`

**Files modified:** `scripts/verify_ebay_access.py`
**Commit:** 8563bb5
**Applied fix:** Added a `seen_ids` set tracking `itemId` values; items whose `itemId` has already been captured (from an earlier overlapping query) are skipped before being appended to `captured`. Note: the existing `fixtures/ebay_listing_titles.json` was left as-is (already-captured historical evidence from a prior live run) — regenerating it against live eBay credentials was not required to fix the code defect itself and was out of scope for this fix pass. A future live capture run will benefit from the dedup logic going forward.

### WR-04: No error handling around the network calls in `main()`

**Files modified:** `scripts/verify_ebay_access.py`
**Commit:** c7100ca
**Applied fix:** Added `import requests`, wrapped the `get_app_token(env=env)` call in `try/except requests.exceptions.RequestException` (prints an error to stderr and returns exit code 1 on failure), and wrapped the per-query `search_sealed_listings(...)` call in the same exception handling — on failure it prints an error and `continue`s to the next query rather than aborting the whole capture run.

## Skipped Issues

### WR-02: `requirements.txt` pins major versions beyond what CLAUDE.md's own stack decision documents, without updated rationale

**File:** `requirements.txt:8-9`
**Reason:** Acknowledged but deliberately not auto-fixed. `flask-cors==6.0.5` and `gunicorn==26.0.0` are not new/speculative pins — per this project's Phase 5/7 history, they are already deployed and running in production, having been verified-legitimate at the time they were introduced. Downgrading them to match CLAUDE.md's older documented versions (`5.x`/`23.x`) would risk breaking an already-deployed, working production dependency set purely to satisfy documentation consistency — the riskier of the two remediation options the review itself offered. The other option — updating CLAUDE.md's stack table with rationale for the newer majors — is out of this fix pass's file scope (CLAUDE.md is not a phase-1 file, and editing it is a documentation-drift task better handled deliberately rather than as a side effect of a phase-1 code-review fix pass). This finding should be revisited as a standalone documentation-update task.
**Original issue:** `flask-cors==6.0.5` and `gunicorn==26.0.0` are pinned, but CLAUDE.md's "Recommended Stack" table specifies Flask-CORS `5.x` and gunicorn `23.x` — both major-version jumps past the documented/vetted choice, with no rationale note, risking drift between the two sources of truth.

---

_Fixed: 2026-07-18T04:36:42Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
