---
phase: 02-product-catalog-data-model
fixed_at: 2026-07-14T05:01:56Z
review_path: .planning/phases/02-product-catalog-data-model/02-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 02: Code Review Fix Report

**Fixed at:** 2026-07-14T05:01:56Z
**Source review:** .planning/phases/02-product-catalog-data-model/02-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5 (critical_warning scope — WR-01 through WR-05; 4 Info findings excluded by scope)
- Fixed: 5
- Skipped: 0

## Fixed Issues

### WR-01: Compound index creation is not independently idempotent

**Files modified:** `db/init_collections.py`
**Commit:** 55896b9
**Applied fix:** Moved `db.products.create_index(...)` out of the `if "products" not in db.list_collection_names():` block so it now runs unconditionally on every `init_collections()` call. `create_index()` is safe/idempotent to call on an existing collection (unlike `create_collection()` with a validator, which is creation-time-only), so a pre-existing `products` collection created by an earlier code version or left partially initialized will now get the index added on the next run instead of silently no-op-ing forever.

### WR-02: `$jsonSchema` validator does not restrict additional properties

**Files modified:** `db/init_collections.py`
**Commit:** a2f1b67
**Applied fix:** Added `"additionalProperties": False` to `PRODUCTS_JSON_SCHEMA`. Verified against `scripts/catalog_data.py`'s documented field list (set_name, product_type, language, release_date, msrp, image_url, display_name, required_keywords, verified, verified_at) — all 10 fields exactly match the schema's `properties`, so no legitimately-seeded field is rejected by this change.

### WR-03: `(set_name, product_type)` uniqueness is enforced only by convention, not by the database

**Files modified:** `db/init_collections.py`
**Commit:** 6c86ef0
**Applied fix:** Added `unique=True` to the compound index on `{set_name, product_type}`, applied on top of WR-01's decoupled index-creation call, so uniqueness is now enforced by MongoDB itself rather than relying solely on every writer independently computing the same deterministic slug `_id`.

### WR-04: `MongoClient` is not closed on the error path in `seed_catalog.py main()`

**Files modified:** `scripts/seed_catalog.py`
**Commit:** d66ebb3
**Applied fix:** Wrapped the body of `main()` (from `db = client["pokemonview"]` through the provisional-data warning) in `try:`/`finally: client.close()`, so the connection is always released even if `init_collections(db)` or `seed_catalog(db, CATALOG)` raises.

### WR-05: `catalog_db` test fixture leaks its `MongoClient` on setup failure

**Files modified:** `tests/conftest.py`
**Commit:** 13f6ce8
**Applied fix:** Wrapped fixture setup (drop collections, lazy imports, `init_collections`, `seed_catalog`) in `try:`/`except Exception: client.close(); raise`, so a setup failure before `yield test_db` now closes the client before propagating the exception, instead of leaking the connection because pytest never reaches the post-yield teardown block.

## Skipped Issues

None — all in-scope findings were fixed.

---

_Fixed: 2026-07-14T05:01:56Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
