---
phase: 02-product-catalog-data-model
reviewed: 2026-07-14T00:00:00Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - .env.example
  - db/__init__.py
  - db/init_collections.py
  - pytest.ini
  - requirements.txt
  - scripts/__init__.py
  - scripts/catalog_data.py
  - scripts/seed_catalog.py
  - tests/conftest.py
  - tests/test_catalog_schema.py
findings:
  critical: 0
  warning: 4
  info: 4
  total: 8
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-07-14T00:00:00Z
**Depth:** standard
**Files Reviewed:** 9 (10 listed; see tooling limitation note below)
**Status:** issues_found

## Summary

Reviewed the product-catalog data model bootstrap: `db/init_collections.py` (schema/index/time-series creation), `scripts/catalog_data.py` (static curated catalog), `scripts/seed_catalog.py` (idempotent upsert entrypoint), and the test suite (`tests/conftest.py`, `tests/test_catalog_schema.py`), plus `pytest.ini` and `requirements.txt`.

No secrets, injection vectors, or dangerous function usage were found. Package versions in `requirements.txt` (requests 2.34.2, python-dotenv 1.2.2, pymongo 4.17.0, pytest 8.4.2) were verified against PyPI and all exist and are current/installable — no phantom versions. `.env` is correctly gitignored and untracked.

The core logic issues found are: (1) the "idempotent bootstrap" guarantee for the compound index is not actually unconditional — it's coupled to collection creation rather than being independently idempotent, unlike `create_index()`'s native idempotency; (2) the `$jsonSchema` validator omits `additionalProperties: false`, undercutting its own docstring's claim to be a general-purpose input-validation control; and (3) `scripts/seed_catalog.py`'s `main()` has no `try/finally` around the MongoClient lifecycle, unlike the sibling `scripts/verify_ebay_access.py` pattern it claims to mirror (which uses `os.environ.get()` with a default rather than raw indexing).

**Tooling limitation:** `.env.example` was explicitly listed as in-scope, but the sandbox's Read/Bash permission settings denied all access to it (both `Read` and `Bash ls/wc/file` on the path were blocked), consistent with the broad `.env*` restriction described in the task. This file could not be reviewed. Per the task's guidance this is noted as a tooling limitation rather than a failure; it should be reviewed manually to confirm it documents `MONGODB_URI` (referenced by `scripts/seed_catalog.py` and `tests/conftest.py`) and contains only placeholder values, no live credentials.

## Warnings

### WR-01: Compound index creation is not independently idempotent

**File:** `db/init_collections.py:95-104`
**Issue:** The module docstring and function docstring both assert that `init_collections()` idempotently ensures the `products` collection has "a compound index on `{set_name: 1, product_type: 1}}`." But the `create_index()` call is nested *inside* the `if "products" not in db.list_collection_names():` block:

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

Unlike the `$jsonSchema` validator and `timeseries` options (which genuinely are creation-time-only, per the docstring's own Pitfall-1 rationale), `create_index()` has no such restriction — it can be called on an already-existing collection at any time and is itself idempotent (a no-op if the equivalent index already exists). By nesting it under the collection-existence guard, any pre-existing `products` collection that lacks this index (e.g. created by an earlier code version, restored from a backup, or left in a partial state because a prior `init_collections()` call succeeded at `create_collection()` but crashed before reaching `create_index()`) will **never** get the index added by subsequent calls — the function will silently skip both statements forever. This directly undermines `CATALOG-02`'s "queryable by set alone or by set + product_type" requirement in exactly the redeploy/migration scenarios this bootstrap function exists to handle safely. It is not caught by the current test suite because `tests/conftest.py` always drops `products` before calling `init_collections()`, so the "collection already exists without the index" path is never exercised.

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
**Issue:** `PRODUCTS_JSON_SCHEMA` declares `required` fields and typed `properties`, but never sets `"additionalProperties": false`. MongoDB's `$jsonSchema` validator allows arbitrary extra fields by default unless explicitly restricted. The module docstring for `init_collections()` frames this validator as "a V5 input-validation control, not just this phase's seed script" — i.e., intended to guard *any* future writer (e.g. a later admin API), not merely today's trusted seed script. As written, any writer can attach unvalidated arbitrary fields to a `products` document alongside the required ones, which weakens the validator's value as the stated general-purpose input-validation boundary.
**Fix:**
```python
PRODUCTS_JSON_SCHEMA = {
    "bsonType": "object",
    "additionalProperties": False,
    "required": [...],
    "properties": {...},
}
```
(Verify this doesn't break the `_id` field validation path — `_id` is implicitly exempt from `additionalProperties` in MongoDB's `$jsonSchema`, so this should be safe, but confirm against the seeded documents' actual field set before enabling in case a legitimate field was missed from `properties`.)

### WR-03: `MongoClient` is not closed on the error path in `seed_catalog.py main()`

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
If `init_collections(db)` or `seed_catalog(db, CATALOG)` raises (e.g. a validator conflict, a network blip, an `OperationFailure`), `client.close()` at line 120 is never reached and the connection leaks. The module docstring claims this script "mirrors Phase 1's `scripts/verify_ebay_access.py` pattern" for credential hygiene, but that sibling script uses `os.environ.get("EBAY_ENV", "production")` defensively — this file doesn't carry the same defensive posture through to resource cleanup.
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

### WR-04: `catalog_db` test fixture leaks its MongoClient on setup failure

**File:** `tests/conftest.py:57-80`
**Issue:** Same pattern as WR-03, in the test fixture. `MongoClient(mongodb_uri)`, `test_db.drop_collection(...)`, `init_collections(test_db)`, and `seed_catalog(test_db, CATALOG)` all run before the `yield`, with no `try/finally`. If any of these calls raises during fixture setup (e.g. a transient connectivity issue against Atlas, or a validator error introduced by a future schema change), the `client.close()` at line 80 never runs. This is flagged despite the general "skip test-file issues" guidance because it affects test reliability: repeated setup failures across a test run/CI session can exhaust the process's or Atlas's connection pool, turning a single flaky failure into cascading failures for unrelated tests in the same session.
**Fix:** Wrap setup in `try/except` to close the client before re-raising, or move `client = MongoClient(...)` to its own fixture with `addfinalizer`/`yield`-based cleanup so teardown always runs regardless of where setup fails.

## Info

### IN-01: `MONGODB_URI` lookup raises an unfriendly raw `KeyError`

**File:** `scripts/seed_catalog.py:100`
**Issue:** `mongodb_uri = os.environ["MONGODB_URI"]` raises a bare `KeyError: 'MONGODB_URI'` with a full traceback if the variable isn't set, rather than a clear, actionable message. Contrast with `tests/conftest.py:49-55`, which uses `os.environ.get("MONGODB_URI")` and emits a helpful `pytest.skip(...)` message pointing at Plan 02-02, and with the sibling `scripts/verify_ebay_access.py`, which uses `os.environ.get(..., default)`.
**Fix:**
```python
mongodb_uri = os.environ.get("MONGODB_URI")
if not mongodb_uri:
    print("ERROR: MONGODB_URI not set. Copy .env.example to .env and fill it in.", file=sys.stderr)
    return 1
```

### IN-02: Compound index is not `unique`, leaving `(set_name, product_type)` uniqueness unenforced at the DB level

**File:** `db/init_collections.py:102-104`
**Issue:** `seed_catalog.py`'s idempotency guarantee relies entirely on the *convention* that every writer computes `_id` as the `{set_name}_{product_type}` slug (Pattern 2). Nothing at the database level prevents a future writer (a direct `insert_one`, a different script, an eventual admin API) from inserting a duplicate `(set_name, product_type)` pair under a different `_id`, silently violating `CATALOG-01`'s "exactly one document per catalog entry" invariant that `test_catalog_completeness` checks for.
**Fix:** Add `unique=True` to the compound index as a defense-in-depth guard:
```python
db.products.create_index(
    [("set_name", ASCENDING), ("product_type", ASCENDING)],
    unique=True,
)
```

### IN-03: `release_date` is stored as a timezone-naive datetime

**File:** `scripts/seed_catalog.py:73`
**Issue:** `datetime.fromisoformat("2026-05-22")` produces a naive `datetime(2026, 5, 22, 0, 0)`. PyMongo will serialize this as UTC midnight without any explicit timezone marker in the source. This works today since `release_date` is only ever compared/displayed as a date, but it's an implicit assumption that isn't documented anywhere in code (only inferable from BSON's UTC-storage behavior). Low risk for a date-only field, but worth a one-line comment for future maintainers who might later add time-of-day granularity.
**Fix:** Add a short comment near the conversion noting the naive-datetime-is-treated-as-UTC assumption, or explicitly use `datetime.fromisoformat(...).replace(tzinfo=timezone.utc)` for clarity.

### IN-04: Slug generation has no collision guard

**File:** `scripts/seed_catalog.py:70`
**Issue:** `slug = f"{doc['set_name']}_{doc['product_type']}".lower().replace(" ", "-")` has no sanitization beyond a single space→hyphen replacement. Given the current curated, hand-authored `CATALOG` list this is safe, but there's no validation preventing two distinct catalog entries from normalizing to the same slug (e.g. a future set name differing only by hyphen vs. space, or containing characters that collide after lowering), which would cause one entry to silently overwrite another via upsert with no error raised.
**Fix:** Either add a cheap assertion in `seed_catalog()` that all generated slugs are unique before performing the bulk write, or add a comment acknowledging the current data-only mitigation:
```python
slugs = [f"{p['set_name']}_{p['product_type']}".lower().replace(" ", "-") for p in catalog]
assert len(slugs) == len(set(slugs)), "duplicate catalog slug detected"
```

---

_Reviewed: 2026-07-14T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
