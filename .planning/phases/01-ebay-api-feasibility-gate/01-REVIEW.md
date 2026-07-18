---
phase: 01-ebay-api-feasibility-gate
reviewed: 2026-07-18T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - .gitignore
  - .env.example
  - fixtures/ebay_listing_titles.json
  - requirements.txt
  - scripts/ebay_client.py
  - scripts/verify_ebay_access.py
findings:
  critical: 3
  warning: 4
  info: 2
  total: 9
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-07-18T00:00:00Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Reviewed the eBay API feasibility-gate scaffolding: OAuth client credentials flow (`scripts/ebay_client.py`), the smoke-test entrypoint (`scripts/verify_ebay_access.py`), the captured fixture (`fixtures/ebay_listing_titles.json`), dependency pins (`requirements.txt`), and secret-hygiene scaffolding (`.gitignore`). Per the review brief, `ebay_client.total_cost()`'s recent hardening against missing/`None` `shippingCost` values was **not** re-flagged.

However, that exact bug class was found to still be present, unfixed, in a second location: `scripts/verify_ebay_access.py` duplicates the shipping-cost extraction logic inline (rather than reusing the hardened helper) and reproduces the crash. A second, distinct crash bug was also found in the same function's `categoryId` extraction. A third bug makes the script's own documented sandbox code path unusable. `fixtures/ebay_listing_titles.json` was checked line-by-line for accidental secret/credential leakage — none found; it contains only public titles, prices, shipping costs, and eBay `categoryId` values, consistent with the stated scope.

**Note on scope:** `.env.example` was in the requested file list but could not be read — the `Read` tool returned "File is in a directory that is denied by your permission settings" on repeated attempts (this affected the `.env.example` filename specifically, likely from a sandbox-level deny rule for `.env*`-shaped files). This file was **not reviewed** and its contents are unverified; a human (or a review run without this restriction) should confirm it contains no real credentials and matches the variables `ebay_client.py`/`verify_ebay_access.py` actually read (`EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET`, `EBAY_ENV`).

## Critical Issues

### CR-01: verify_ebay_access.py reproduces the exact `shippingCost: null` crash that ebay_client.total_cost() was hardened against

**File:** `scripts/verify_ebay_access.py:74-75`
**Issue:** The fixture-record's own `shipping_cost` field is computed with duplicated, unhardened logic instead of reusing (or being made consistent with) the fixed helper:

```python
shipping_options = item.get("shippingOptions") or [{}]
shipping_cost = shipping_options[0].get("shippingCost", {}).get("value", "0.00")
```

`dict.get(key, default)` only returns `default` when the key is **absent**. Per `total_cost()`'s own docstring, real Browse API responses can have `shippingOptions` non-empty but with the first entry's `shippingCost` key present with value `None` (calculated/freight shipping without a buyer postal code, or local-pickup-only options). In that case `shipping_options[0].get("shippingCost", {})` returns `None` (not `{}`), and the chained `.get("value", "0.00")` raises `AttributeError: 'NoneType' object has no attribute 'get'`, crashing the whole smoke-test run mid-loop for the exact API response shape this script is supposed to exercise against real production data.

This is the same bug class fixed in `ebay_client.total_cost()` (commits a7e6381/0c1364d) via `(shipping_options[0].get("shippingCost") or {})` — but the fix was never applied to this duplicate inline copy.

**Fix:** Reuse the already-hardened helper instead of duplicating the logic:
```python
shipping_options = item.get("shippingOptions") or [{}]
shipping_value = (shipping_options[0].get("shippingCost") or {}).get("value")
shipping_cost = shipping_value if shipping_value is not None else "0.00"
```

### CR-02: `categoryId` extraction crashes with IndexError when `categories` is present but empty

**File:** `scripts/verify_ebay_access.py:82`
**Issue:**
```python
"categoryId": item.get("categories", [{}])[0].get("categoryId"),
```
`dict.get(key, default)` only substitutes `default` when the key is **missing** from `item`. If a real itemSummary has `"categories": []` (key present, empty list — a plausible real-world shape, same category of defect as the shipping one above), `.get()` returns `[]` as-is, and `[][0]` raises `IndexError: list index out of range`, crashing the run.

**Fix:** Use the same `or` idiom already used correctly on the previous line for `shippingOptions`:
```python
categories = item.get("categories") or [{}]
"categoryId": categories[0].get("categoryId"),
```

### CR-03: `search_sealed_listings()` hardcodes the production Browse API host, breaking the script's own documented sandbox path

**File:** `scripts/ebay_client.py:81-93` (called from `scripts/verify_ebay_access.py:58,69`)
**Issue:** `get_app_token(env=...)` correctly switches host between `api.ebay.com` and `api.sandbox.ebay.com` based on `EBAY_ENV`. `search_sealed_listings()` takes no `env` argument and always calls:
```python
resp = requests.get(
    "https://api.ebay.com/buy/browse/v1/item_summary/search",
    ...
)
```
`verify_ebay_access.py` explicitly supports and documents an `EBAY_ENV=sandbox` run mode (it prints a warning and continues rather than exiting). In that mode, `get_app_token(env="sandbox")` returns a token issued by `api.sandbox.ebay.com`, but `search_sealed_listings()` then sends that sandbox-scoped bearer token to the **production** Browse API host. Production will reject a sandbox token, `resp.raise_for_status()` raises `requests.exceptions.HTTPError`, and the script crashes with an unhandled exception on a code path the script itself advertises as supported.

**Fix:** Thread `env` through, mirroring `get_app_token`:
```python
def search_sealed_listings(access_token: str, query: str, limit: int = 50, env: str = "production") -> list[dict]:
    host = "api.ebay.com" if env == "production" else "api.sandbox.ebay.com"
    resp = requests.get(
        f"https://{host}/buy/browse/v1/item_summary/search",
        ...
    )
```
and update the call site in `verify_ebay_access.py` to pass `env=env`.

## Warnings

### WR-01: `.gitignore` only excludes the literal `.env` filename, not common variants

**File:** `.gitignore:2`
**Issue:** Given the heavy, repeated emphasis on credential hygiene throughout this codebase (docstrings cite threat T-01-02 / D-02 explicitly), the `.gitignore` only ignores the exact `.env` file:
```
.env
```
It does not cover common variants a developer might create while testing environments (`.env.local`, `.env.production`, `.env.development`, `.env.*.local`), any of which could contain real `EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET` values and get committed by accident.
**Fix:**
```
.env
.env.*
!.env.example
```

### WR-02: `requirements.txt` pins major versions beyond what CLAUDE.md's own stack decision documents, without updated rationale

**File:** `requirements.txt:8-9`
**Issue:** `flask-cors==6.0.5` and `gunicorn==26.0.0` are pinned, but the project's own documented "Recommended Stack" (CLAUDE.md) specifies Flask-CORS `5.x` and gunicorn `23.x`. Both are major-version jumps past the documented/vetted choice, with no note explaining the deviation or confirming compatibility (Flask-CORS and gunicorn major bumps have historically changed default behavior/CLI flags). This risks a silent breaking change surfacing later when the API service is actually built against these pins.
**Fix:** Either pin to the versions CLAUDE.md documents (`flask-cors==5.*`, `gunicorn==23.*`) or update CLAUDE.md's stack table with the rationale for the newer majors, so the two sources of truth don't drift.

### WR-03: No deduplication of captured listings across `CATALOG_QUERIES`

**File:** `scripts/verify_ebay_access.py:68-99`
**Issue:** The capture loop appends every matching item across all seven overlapping keyword queries with no dedup by `itemId` (or by title). This is not theoretical — `fixtures/ebay_listing_titles.json` itself contains multiple exact-duplicate records from this run, e.g. `"Pokemon Scarlet & Violet Temporal Forces Elite Trainer Box ETB Walking Wake"` @ $119.95 (rows 3 and 374), `"Pokémon TCG Destined Rivals Elite Trainer Box ETB Unopened & Sealed"` @ $160.00 (rows 108 and 458), and `"Pokemon TCG Destined Rivals ETB Elite Trainer Box - Sealed Brand New"` @ $165.00 (rows 276 and 451). This wastes fixture capacity toward the SC-4 "50-100 real listings" target and understates how many *distinct* products the capture actually represents.
**Fix:** Track seen `itemId`s (or normalized titles) and skip repeats:
```python
seen_ids = set()
...
item_id = item.get("itemId")
if item_id in seen_ids:
    continue
seen_ids.add(item_id)
```

### WR-04: No error handling around the network calls in `main()`

**File:** `scripts/verify_ebay_access.py:58,69`
**Issue:** `get_app_token()` and `search_sealed_listings()` both call `resp.raise_for_status()` internally and can also raise `requests.exceptions.ConnectionError`/`Timeout`. `main()` calls both with no `try/except`, so any auth failure, rate-limit response, or network hiccup surfaces as a raw Python traceback rather than an actionable message — undermining the script's stated purpose as a diagnostic smoke test for a human verifying eBay API access.
**Fix:**
```python
try:
    token_resp = get_app_token(env=env)
except requests.exceptions.RequestException as e:
    print(f"ERROR: OAuth token request failed: {e}", file=sys.stderr)
    return 1
```
(similarly around the per-query `search_sealed_listings` call, e.g. log-and-continue to the next query rather than aborting the whole run).

## Info

### IN-01: `item["price"]["value"]` assumes nested key presence beyond what's checked

**File:** `scripts/verify_ebay_access.py:71,79`
**Issue:** The guard at line 71 only checks `"price" not in item`; it doesn't confirm `item["price"]` is a dict containing `"value"`. If a real response ever has `"price": {}` (no `value`), line 79's `item["price"]["value"]` raises `KeyError`.
**Fix:** `item.get("price", {}).get("value")` with a `None`/skip check, for symmetry with how `shippingCost` is already handled defensively elsewhere in this file.

### IN-02: `requirements.txt` bundles unrelated future-service dependencies into the Phase 1 feasibility gate

**File:** `requirements.txt:3-9`
**Issue:** `pymongo`, `flask`, `flask-cors`, `gunicorn`, `apscheduler`, and `rapidfuzz` are pinned here, but none are imported by `scripts/ebay_client.py` or `scripts/verify_ebay_access.py` (which only need `requests`, `python-dotenv`, and `pytest`). Not a defect — CLAUDE.md's own Installation notes allow a shared `requirements.txt` — but worth flagging so it's a deliberate choice rather than scope creep into a phase that's supposed to be a narrow feasibility spike.
**Fix:** No action required if intentional; otherwise split into `requirements.txt` (shared) and a lighter `scripts/requirements-feasibility.txt` for this phase.

---

_Reviewed: 2026-07-18T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
