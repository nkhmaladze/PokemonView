---
phase: 02-product-catalog-data-model
reviewed: 2026-07-14T00:00:00Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - db/__init__.py
  - db/init_collections.py
  - scripts/__init__.py
  - scripts/catalog_data.py
  - scripts/seed_catalog.py
  - tests/conftest.py
  - tests/test_catalog_schema.py
findings:
  critical: 0
  warning: 5
  info: 4
  total: 9
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-07-14T00:00:00Z
**Depth:** standard
**Files Reviewed:** 7
**Status:** issues_found

## Summary

Reviewed the product catalog data model bootstrap (`db/init_collections.py`), the curated static catalog (`scripts/catalog_data.py`), the idempotent seed entrypoint (`scripts/seed_catalog.py`), and the test suite (`tests/conftest.py`, `tests/test_catalog_schema.py`). `db/__init__.py` and `scripts/__init__.py` are empty package markers with no content to review.

No hardcoded secrets, injection vectors, or dangerous function usage were found; credential handling (`MONGODB_URI` via `os.environ` after `load_dotenv()`, never printed) is sound, and the core idempotent-upsert design (deterministic slug `_id` + `bulk_write` of `UpdateOne(upsert=True)`) correctly avoids duplicate inserts on re-run for the happy path the tests exercise.

The issues found are all about gaps between what the code's own docstrings *claim* it guarantees and what it actually enforces: the compound index is not guaranteed to exist independent of collection-creation timing, the `$jsonSchema` validator does not reject unexpected fields despite being framed as a general-purpose input-validation control, `(set_name, product_type)` uniqueness is enforced only by an application-level naming convention rather than a database constraint, and resource cleanup (`MongoClient.close()`) is skipped on setup-failure paths in both the seed script and the test fixture. None of these are exploitable today given the single-writer, well-behaved-catalog-data reality of this phase, but they are exactly the kind of latent defect that turns into a real incident once a second writer or an operational hiccup enters the picture — which is the explicit intent of this phase's V5 input-validation and idempotent-bootstrap claims. No blockers.

## Warnings

### WR-01: Compound index creation is not independently idempotent

**File:** `db/init_collections.py:95-104`
**Issue:** `db.products.create_index(...)` (lines 102-104) is nested inside `if "products" not in db.list_collection_names():` (line 95). Index creation therefore only ever happens the moment the collection is first created. Unlike the `$jsonSchema` validator and `timeseries` options — which really are creation-time-only settings, per this same file's own Pitfall-1 rationale (lines 5-9) — `create_index()` has no such restriction: it is safe and idempotent to call on an already-existing collection. By gating it behind the collection-existence check, any pre-existing `products` collection that lacks the index (created by an earlier code version, restored from backup, or left partially initialized by a prior run that failed between `create_collection()` and `create_index()`) will never get the index added by subsequent `init_collections()` calls — the function silently no-ops for it forever. This undermines the function's own docstring claim (lines 76-81) that it "idempotently" ensures the index exists. The current test suite doesn't catch this because `tests/conftest.py` always drops `products` before calling `init_collections()`, so the "collection exists without the index" path is never exercised.
**Fix:** Decouple index creation from collection creation so it always runs:
```python
if "products" not in db.list_collection_names():
    db.create_collection(
        "products",
        validator={"$jsonSchema": PRODUCTS_JSON_SCHEMA},
        validationLevel="strict",
        validationAction="error",
    )

db.products.create_index(
    [("set_name", ASCENDING), ("product_type", ASCENDING)]
)
```

### WR-02: `$jsonSchema` validator does not restrict additional properties

**File:** `db/init_collections.py:26-54`
**Issue:** `PRODUCTS_JSON_SCHEMA` declares `required` fields and typed `properties` but never sets `"additionalProperties": false`. MongoDB's `$jsonSchema` allows arbitrary extra fields by default unless explicitly restricted. The docstring for `init_collections()` (lines 76-81) frames this validator as a general-purpose "V5 input-validation control, not just this phase's seed script" — i.e., meant to guard any future writer, not just today's trusted seed script. As written, any writer can attach unvalidated, arbitrary, or misspelled fields (e.g. `"verifed"` instead of `"verified"`) to a `products` document and the insert will still succeed, silently defeating the validator's stated purpose.
**Fix:**
```python
PRODUCTS_JSON_SCHEMA = {
    "bsonType": "object",
    "additionalProperties": False,
    "required": [...],
    "properties": {...},
}
```
(Confirm this doesn't reject any legitimately-seeded field first — `_id` is implicitly exempt from `additionalProperties` in MongoDB's `$jsonSchema`, so this should be safe against the current `CATALOG` shape.)

### WR-03: `(set_name, product_type)` uniqueness is enforced only by convention, not by the database

**File:** `db/init_collections.py:102-104`
**Issue:** The compound index is created without `unique=True`. `scripts/seed_catalog.py`'s idempotency guarantee (no duplicate documents across re-runs) depends entirely on every writer independently computing the same deterministic slug `_id = f"{set_name}_{product_type}".lower().replace(" ", "-")` (seed_catalog.py:70-71). Nothing at the database layer prevents a different writer — a future admin script, a direct `insert_one`, a bug that generates a different `_id` for the same logical product — from inserting a second document for the same `(set_name, product_type)` pair. `tests/test_catalog_schema.py::test_catalog_completeness` only checks that the *already-seeded* dataset has no duplicate pairs; it does not prove the database would reject a newly-inserted duplicate.
**Fix:** Add `unique=True` as a defense-in-depth constraint:
```python
db.products.create_index(
    [("set_name", ASCENDING), ("product_type", ASCENDING)],
    unique=True,
)
```

### WR-04: `MongoClient` is not closed on the error path in `seed_catalog.py main()`

**File:** `scripts/seed_catalog.py:99-121`
**Issue:**
```python
client = MongoClient(mongodb_uri)
db = client["pokemonview"]

init_collections(db)
seed_catalog(db, CATALOG)
...
client.close()
```
If `init_collections(db)` or `seed_catalog(db, CATALOG)` raises (validator conflict, transient network error, `OperationFailure`), `client.close()` at line 120 is never reached and the connection leaks. The module docstring (lines 18-22) claims this script "mirrors Phase 1's `scripts/verify_ebay_access.py` pattern" for credential hygiene, but resource cleanup here isn't wrapped defensively the way that framing implies.
**Fix:**
```python
client = MongoClient(mongodb_uri)
try:
    db = client["pokemonview"]
    init_collections(db)
    seed_catalog(db, CATALOG)
    ...
finally:
    client.close()
```

### WR-05: `catalog_db` test fixture leaks its `MongoClient` on setup failure

**File:** `tests/conftest.py:57-74`
**Issue:** `MongoClient(mongodb_uri)` (line 57), `drop_collection(...)` (lines 61-62), `init_collections(test_db)`, and `seed_catalog(test_db, CATALOG)` (lines 71-72) all run before `yield test_db` (line 74), with no `try/finally`. If any of these raise during fixture setup (e.g. a transient Atlas connectivity blip, or a future schema/validator regression), the teardown block at lines 76-80 — including `client.close()` — never executes, because pytest only runs the code after `yield` in a generator-style fixture if execution actually reaches the `yield`. Flagged despite the "don't report test-file issues unless they affect reliability" guidance because repeated setup failures across a session can accumulate leaked connections and exhaust a shared connection pool, turning one flaky failure into cascading failures for unrelated tests.
**Fix:** Wrap setup in `try`/`except`, closing the client before re-raising, or move connection lifecycle management into a separate fixture with guaranteed teardown.

## Info

### IN-01: `MONGODB_URI` lookup raises an unfriendly raw `KeyError`

**File:** `scripts/seed_catalog.py:100`
**Issue:** `mongodb_uri = os.environ["MONGODB_URI"]` raises a bare `KeyError: 'MONGODB_URI'` with a full traceback if the variable isn't set, giving no actionable guidance. Contrast with `tests/conftest.py:49-55`, which uses `os.environ.get("MONGODB_URI")` and emits a clear `pytest.skip(...)` message pointing at the relevant setup plan.
**Fix:**
```python
mongodb_uri = os.environ.get("MONGODB_URI")
if not mongodb_uri:
    print("ERROR: MONGODB_URI not set. Add it to .env before running python -m scripts.seed_catalog.", file=sys.stderr)
    return 1
```

### IN-02: Idempotent upsert never removes fields dropped from a catalog entry

**File:** `scripts/seed_catalog.py:67-74`
**Issue:** `UpdateOne({"_id": slug}, {"$set": doc}, upsert=True)` uses only `$set`, which adds/overwrites keys but never deletes ones absent from the new document. If a future edit to `scripts/catalog_data.py` removes a field from an entry (e.g. a corrected-away `image_url`, or a renamed field during a schema evolution), re-running the seed script will not remove the stale field from the already-persisted document. The module docstring frames this script as correcting entries "in place" (lines 3-9, 21-22 via D-02's "seed-now-correct-later" workflow), which holds for value changes but not field removals.
**Fix:** Document the limitation explicitly, or diff against the existing document and add a corresponding `$unset` for keys no longer present in the new catalog entry.

### IN-03: Slug generation has no collision guard

**File:** `scripts/seed_catalog.py:70-71`
**Issue:** `slug = f"{doc['set_name']}_{doc['product_type']}".lower().replace(" ", "-")` performs no validation that all generated slugs are actually unique across `catalog`. Safe today given the small, hand-authored `CATALOG` list, but if two distinct entries were ever to normalize to the same slug (e.g. a set name differing only by a character that collapses under `.lower()`/space-replacement), one entry would silently overwrite the other via upsert with no error raised anywhere.
**Fix:**
```python
slugs = [f"{p['set_name']}_{p['product_type']}".lower().replace(" ", "-") for p in catalog]
assert len(slugs) == len(set(slugs)), "duplicate catalog slug detected"
```

### IN-04: Inconsistent `bsonType` representation for `verified`

**File:** `db/init_collections.py:51`
**Issue:** `"verified": {"bsonType": ["bool"]}` uses a single-element list for a scalar type, while sibling single-type fields such as `"set_name": {"bsonType": "string"}` (line 36) use a bare string. Functionally identical to MongoDB's validator, but inconsistent within the same schema object.
**Fix:** `"verified": {"bsonType": "bool"}` for consistency.

---

_Reviewed: 2026-07-14T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
