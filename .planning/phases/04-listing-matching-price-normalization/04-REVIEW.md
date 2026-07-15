---
phase: 04-listing-matching-price-normalization
reviewed: 2026-07-14T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - requirements.txt
  - scripts/ingest_worker.py
  - scripts/matching.py
  - tests/conftest.py
  - tests/test_matching.py
findings:
  critical: 2
  warning: 4
  info: 2
  total: 8
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-07-14T00:00:00Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Reviewed the Phase 4 listing-matching/price-normalization pipeline (`scripts/matching.py`), its integration point in `scripts/ingest_worker.py`, the test fixtures (`tests/conftest.py`), the contract tests (`tests/test_matching.py`), and `requirements.txt`. The pure-function design of `scripts/matching.py` (keyword/fuzzy matching, exclusion regexes, outlier filtering, aggregation) is well-tested at the unit level and the end-to-end integration test is thorough. However, two BLOCKER-level defects were found in the orchestration/lock-safety layer and the title-normalization filler-word list, plus several WARNING-level robustness gaps that are not covered by the existing test suite (none of the found defects cause an existing test to fail — they represent untested edge cases and design gaps).

## Critical Issues

### CR-01: Ingestion lock can leak for up to 15 minutes if the "running" status insert fails

**File:** `scripts/ingest_worker.py:203-240`
**Issue:** After `acquire_lock()` succeeds, `run_ingestion_once()` calls `db.ingestion_runs.insert_one({...})` (lines 217-228) to record the "running" status document — but this call sits **outside** the `try/finally` block that starts at line 240. The docstring explicitly claims: "wrapped in try/finally so release_lock always runs" — but that guarantee does not actually cover this insert. If `insert_one` raises for any reason (transient Mongo connection error, `$jsonSchema` validation failure on the `ingestion_runs` collection, duplicate `_id` collision, etc.), the exception propagates straight out of `run_ingestion_once()`, `release_lock()` is never called, and the lock document sits in `ingestion_locks` until its 15-minute TTL (`LOCK_TTL_SECONDS = 900`) expires. During that window every subsequent invocation of `run_ingestion_once()` (including the scheduled job on its next interval) silently short-circuits into the `skipped_locked` path and performs zero eBay calls or matching — with no corresponding "failed" run document ever recorded, since the run insert itself never completed. This directly undermines the "must always be accurate and current" core value: a single transient write failure can silently stall all price data collection for up to 15 minutes with no audit trail.
**Fix:** Move the "running" status insert inside the `try` block (or wrap the whole acquire→insert→loop→finalize sequence in one `try/finally`), so `release_lock` always runs regardless of where a failure occurs after the lock is acquired:
```python
if not acquire_lock(db, run_id):
    ...
    return skipped_doc

try:
    db.ingestion_runs.insert_one(
        {
            "_id": run_id,
            "started_at": started_at,
            "finished_at": None,
            "status": "running",
            "products_queried": 0,
            "listings_fetched": 0,
            "listings_written": 0,
            "errors": [],
        }
    )

    products_queried = 0
    ...
    token = get_app_token()
    ...
except Exception as e:
    status = "failed"
    errors.append({"product_ref": None, "error": f"{type(e).__name__}: {e}"})
finally:
    ...
    release_lock(db, run_id)
```

### CR-02: `normalize()`'s multi-word filler entries are dead code — "brand new" and "factory sealed" never strip, leaking noise tokens into fuzzy matching

**File:** `scripts/matching.py:45-71`
**Issue:** `FILLER_WORDS` lists single-word fillers (`"new"`, `"sealed"`) *before* the multi-word phrases that contain them (`"factory sealed"`, `"brand new"`):
```python
FILLER_WORDS = [
    "new",
    "sealed",
    "factory sealed",
    ...
    "brand new",
    ...
]
```
`normalize()` applies these substitutions in list order via `\b{word}\b` regex. Because `"new"` and `"sealed"` are each processed first, they consume the single-word occurrences of "new"/"sealed" wherever they appear — including inside "brand new" and "factory sealed" — leaving "brand" and "factory" as orphaned words and a broken (now-unmatchable) two-word phrase for the later filler entries. Concretely, `normalize("Chaos Rising ETB Brand New Factory Sealed")` produces `"chaos rising etb brand factory"` instead of the intended `"chaos rising etb"` — "brand" and "factory" leak straight through as noise tokens. Since "Brand New" and "Factory Sealed" are two of the single most common phrases in real eBay sealed-collectible listings, this is not a corner case — it affects a large fraction of real-world titles. It doesn't break Tier-1 exact keyword matching (extra words don't prevent a substring match), but it directly pollutes the token set fed into RapidFuzz's `fuzz.token_sort_ratio` for the Tier-2 fuzzy fallback (`match_listing`), diluting the score for every near-miss title that reaches that tier and biasing the pipeline toward false negatives (real listings silently going unmatched, in turn permanently absent from median price aggregation). No existing test exercises this specific interaction — `test_normalize_word_boundary_preserves_resealed` only checks that "resealed" isn't corrupted by the plain-substring pitfall, not that multi-word fillers actually fire.
**Fix:** Either sort `FILLER_WORDS` so longer/more-specific phrases are processed before any of their constituent single words, or de-duplicate the list so multi-word phrases aren't shadowed by their own components:
```python
FILLER_WORDS = [
    "factory sealed",
    "brand new",
    "fast shipping",
    "fast ship",
    "free shipping",
    "ready to ship",
    "same day ship",
    "in hand",
    "new",
    "sealed",
]
```
(Sort longest-phrase-first, or simply move every multi-word entry above the single words it contains.) Add a regression test asserting `normalize("Brand New Factory Sealed ETB")` contains neither `"brand"` nor `"factory"`.

## Warnings

### WR-01: `upsert_listings` doesn't catch `AttributeError`, breaking its documented single-item isolation guarantee

**File:** `scripts/ingest_worker.py:140-165`
**Issue:** The docstring states: "Each item's doc-build is wrapped in a defensive try/except so one malformed eBay item never aborts the whole batch (T-03-03...)". The actual guard is `except (KeyError, ValueError, TypeError):` — it omits `AttributeError`. If an item's `categories` list contains a non-dict entry (e.g. `None` or a string instead of `{"categoryId": ...}`), `categories[0].get("categoryId")` raises `AttributeError`, which is *not* caught here. The exception propagates out of `upsert_listings()` entirely, meaning every item processed before the malformed one in that product's batch is also lost (the function returns before ever calling `bulk_write`). The outer per-product `try/except Exception` in `run_ingestion_once()` does catch it at the product level, so the whole run doesn't fail — but the entire batch of listings for that one product silently drops for the run, contradicting the explicit "one malformed item never aborts the whole batch" contract.
**Fix:**
```python
except (KeyError, ValueError, TypeError, AttributeError):
    continue
```

### WR-02: `product_ref` computed outside the per-product `try` block breaks isolation on a malformed catalog entry

**File:** `scripts/ingest_worker.py:244-248`
**Issue:** Inside the `for product in CATALOG:` loop, `product_ref` is derived via `f"{product['set_name']}_{product['product_type']}"` *before* the `try:` that isolates per-product failures. If any single `CATALOG` entry is missing `set_name` or `product_type` (or has a wrong key), the resulting `KeyError` is raised outside the per-product guard and propagates to the outer `try/except` that wraps the whole loop — aborting every remaining product in that run, not just the malformed one, again contradicting the stated per-product isolation design.
**Fix:** Move the `product_ref` computation inside the `try` block, or wrap it defensively:
```python
try:
    product_ref = (
        f"{product['set_name']}_{product['product_type']}".lower().replace(" ", "-")
    )
    query = build_query(product)
    ...
except Exception as e:
    errors.append({"product_ref": product.get("set_name", "unknown"), "error": f"{type(e).__name__}: {e}"})
```

### WR-03: Outlier detection mixes a median center with a mean-based standard deviation, which can self-mask the outlier it's meant to catch

**File:** `scripts/matching.py:221-255`
**Issue:** `filter_outliers()` computes `med = statistics.median(prices)` for the center but `sd = statistics.pstdev(prices)` for the spread — `pstdev` is computed from the arithmetic **mean**, not the median, and critically it is computed over the *same* `listings` set that still includes the candidate outlier(s). A single large outlier inflates both the mean and the resulting `pstdev`, which raises the exclusion threshold (`OUTLIER_N_STD * sd`) and can make a genuine-but-more-moderate outlier (e.g. 1.5–2x the cluster price rather than the ~3x used in the test fixture) fail to clear the threshold — the outlier partially masks itself. This matches the documented behavior in D-13 exactly as written, so it is not a deviation from spec, but it is a real statistical robustness weakness worth surfacing: a MAD-based (median absolute deviation) or trimmed approach would be far less susceptible to this self-masking effect. The current unit test (`test_outlier_filter_excludes_far_listings`) only exercises an extreme 3x-plus outlier, which is comfortably caught despite the mean-inflation effect — it would not catch a regression to a less extreme, more realistic outlier ratio.
**Fix:** Consider computing spread from median absolute deviation instead of population stdev-from-mean, e.g. `mad = statistics.median(abs(p - med) for p in prices)` scaled by a consistency constant, or at minimum document this as a known/accepted precision tradeoff and add a test with a more moderate (e.g. 1.5-2x) outlier ratio to confirm the current threshold still behaves as intended.

### WR-04: `\bcustom\b` counterfeit-exclusion pattern is likely to false-positive on unrelated, legitimate listings

**File:** `scripts/matching.py:189`
**Issue:** `COUNTERFEIT_PATTERNS` includes `re.compile(r"\bcustom\b")`, intended to catch counterfeit/custom-made product listings. In practice, "custom" is an extremely common word in legitimate eBay sealed-product listings unrelated to counterfeiting — e.g. "includes custom deck box," "with custom top loader," "custom bundle deal," "ships in custom packaging." Given the project's precision-first design (D-01), this single word is broad enough to systematically exclude real, otherwise-matchable listings from price aggregation, silently reducing sample size and skewing the resulting median price.
**Fix:** Narrow the pattern to phrases more specific to counterfeit-signaling language, e.g. `\bcustom\s+(box|packaging|made)\b` combined with more explicit counterfeit terms already present (`replica`, `reproduction`, `bootleg`, `proxy`), or require co-occurrence with another counterfeit signal before excluding on "custom" alone.

## Info

### IN-01: Duplicated product-slug derivation logic across two modules

**File:** `scripts/ingest_worker.py:244-247`, `scripts/matching.py:74-79`
**Issue:** The `products._id` slug derivation (`f"{set_name}_{product_type}".lower().replace(" ", "-")`) is duplicated verbatim between `ingest_worker.py`'s inline `product_ref` computation and `matching.py`'s `_product_slug()` helper. Both docstrings explicitly note they must stay "byte-identical," which is a maintenance hazard — any future change to one without the other silently breaks matching (listings written under one slug format would never match `matched_product_id` values computed by the other).
**Fix:** Extract a single shared helper (e.g. `scripts/catalog_data.product_slug(product)`) and import it from both modules instead of maintaining two hand-synced copies.

### IN-02: `FUZZY_SCORE_CUTOFF` / `FUZZY_MARGIN` are explicitly marked `[ASSUMED]` with no validation against real listing data

**File:** `scripts/matching.py:58-59`
**Issue:** Both fuzzy-matching thresholds carry an inline `[ASSUMED]` comment, meaning they were not derived from empirical tuning against real eBay listing titles. Given these thresholds directly gate whether a real listing contributes to the price-point median, an unvalidated cutoff risks systematically over- or under-including listings once real traffic starts flowing.
**Fix:** Track this as a follow-up validation task once real ingestion data is available — sample a batch of Tier-2 fuzzy matches/near-misses and confirm the 90/5 cutoff-and-margin combination behaves as intended before relying on it for production price data.

---

_Reviewed: 2026-07-14T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
