---
phase: 04-listing-matching-price-normalization
fixed_at: 2026-07-14T00:00:00Z
review_path: .planning/phases/04-listing-matching-price-normalization/04-REVIEW.md
iteration: 1
findings_in_scope: 6
fixed: 5
skipped: 1
status: partial
---

# Phase 4: Code Review Fix Report

**Fixed at:** 2026-07-14T00:00:00Z
**Source review:** .planning/phases/04-listing-matching-price-normalization/04-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 6 (critical_warning scope — CR-01, CR-02, WR-01, WR-02, WR-03, WR-04)
- Fixed: 5
- Skipped: 1

## Fixed Issues

### CR-01: Ingestion lock can leak for up to 15 minutes if the "running" status insert fails

**Files modified:** `scripts/ingest_worker.py`
**Commit:** 3261ea3
**Applied fix:** Moved the `db.ingestion_runs.insert_one(...)` "running" status write inside the `try` block (previously it sat outside, before `try`). Also added `upsert=True` to the finalizing `db.ingestion_runs.update_one(...)` in `finally` so a "failed" audit-trail document is guaranteed to exist even if the initial insert itself raised. `release_lock(db, run_id)` now always runs regardless of where a failure occurs after lock acquisition.

### CR-02: `normalize()`'s multi-word filler entries are dead code

**Files modified:** `scripts/matching.py`, `tests/test_matching.py`
**Commit:** ae4225f
**Applied fix:** Reordered `FILLER_WORDS` so multi-word phrases (`"factory sealed"`, `"brand new"`) are processed before the single words they contain (`"new"`, `"sealed"`), preventing the single-word substitutions from consuming their own components first. Added regression test `test_normalize_strips_multiword_fillers_brand_new_factory_sealed` asserting `normalize("Chaos Rising ETB Brand New Factory Sealed")` contains neither `"brand"` nor `"factory"`.

### WR-01: `upsert_listings` doesn't catch `AttributeError`

**Files modified:** `scripts/ingest_worker.py`
**Commit:** 5d96bd2
**Applied fix:** Added `AttributeError` to the per-item `except (KeyError, ValueError, TypeError)` guard in `upsert_listings`, so a malformed `categories` entry (e.g. `None` or a bare string instead of a dict) is isolated per-item rather than propagating out and dropping the entire batch, honoring the documented single-item isolation contract.

### WR-02: `product_ref` computed outside the per-product `try` block

**Files modified:** `scripts/ingest_worker.py`
**Commit:** 532adee
**Applied fix:** Moved the `product_ref` derivation inside the per-product `try` block (initializing `product_ref = None` beforehand as a safe default for the `except` clause). A malformed `CATALOG` entry missing `set_name`/`product_type` now raises inside the per-product isolation guard instead of escaping to the outer `try` and aborting every remaining product in the run. Verified this preserves the existing `test_run_ingestion_once_partial_on_product_error` contract (where `product_ref` is correctly computed before a downstream `search_sealed_listings` failure).

### WR-03: Outlier detection mixes a median center with a mean-based standard deviation

**Files modified:** `scripts/matching.py`, `tests/test_matching.py`
**Commit:** 6601193
**Applied fix:** This finding's own text notes the current behavior "matches the documented behavior in D-13 exactly as written" — D-13 (`.planning/phases/04-listing-matching-price-normalization/04-CONTEXT.md:43`) is a **locked** decision: "2 standard deviations from the rolling median." Changing the algorithm (e.g. to a MAD-based approach) would be an unauthorized deviation from a locked architectural decision, so per the finding's own "at minimum" fallback, I documented the known/accepted precision tradeoff directly in `filter_outliers()`'s docstring and added `test_outlier_filter_excludes_moderate_outlier`, a regression test exercising a more realistic ~1.5x outlier ratio (previously only an extreme 3x+ case was covered by `test_outlier_filter_excludes_far_listings`).

## Skipped Issues

### WR-04: `\bcustom\b` counterfeit-exclusion pattern is likely to false-positive

**File:** `scripts/matching.py:189`
**Reason:** The suggested fix (narrowing the pattern to e.g. `\bcustom\s+(box|packaging|made)\b`, or requiring co-occurrence with another counterfeit signal) directly conflicts with the existing, checked-in contract test `tests/test_matching.py::test_exclusion_counterfeit`, which explicitly asserts that the bare title `"Chaos Rising Booster Box Custom"` (no qualifying word after "custom") must resolve to `check_exclusion() == "counterfeit"`. Applying the review's suggested narrowing would break this existing passing test. Whether the bare-word "custom" signal should remain authoritative (current locked test contract) or be narrowed (this review's recommendation, trading recall for precision) is a product/design decision — not a mechanical bug fix — so it is left for a human to decide and update both the pattern and its contract test together if narrowing is desired.
**Original issue:** `COUNTERFEIT_PATTERNS` includes `re.compile(r"\bcustom\b")`, which will false-positive on common legitimate phrases like "includes custom deck box," "with custom top loader," or "custom bundle deal," silently excluding real listings from price aggregation and skewing the resulting median price (violates D-01 precision-first design in the opposite direction — over-exclusion rather than under-exclusion).

---

_Fixed: 2026-07-14T00:00:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
