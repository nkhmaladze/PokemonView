# Phase 2: Product Catalog & Data Model - Pattern Map

**Mapped:** 2026-07-13
**Files analyzed:** 5
**Analogs found:** 5 / 5 (all role-match or partial-match — no prior MongoDB/data-model code exists; Phase 1 provides only config/error-handling/entrypoint conventions to inherit)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `scripts/catalog_data.py` | config/data (module-level constant) | batch (static data) | none in repo (no data-only module exists yet) | no analog — see RESEARCH.md Code Examples |
| `scripts/seed_catalog.py` | script/service (one-off entrypoint) | batch / CRUD (idempotent upsert) | `scripts/verify_ebay_access.py` | partial-match (entrypoint shape, `.env` loading, `if __name__ == "__main__"` pattern) |
| `db/init_collections.py` | config (DB schema/bootstrap) | batch (idempotent create-if-not-exists) | `scripts/ebay_client.py` | partial-match (module docstring conventions, function-per-responsibility, no top-level side effects on import) |
| `requirements.txt` (update) | config | — | `requirements.txt` (existing) | exact (same file, additive edit) |
| `tests/test_catalog_schema.py` | test | integration (DB-backed) | none in repo (no `tests/` directory exists yet) | no analog — first test file in project; follow pytest conventions from RESEARCH.md Validation Architecture |

## Pattern Assignments

### `scripts/seed_catalog.py` (script, batch/CRUD idempotent upsert)

**Analog:** `scripts/verify_ebay_access.py` (full file read — 127 lines)

**Module docstring pattern** (lines 1-16 of analog):
```python
"""Single-run smoke-test entrypoint proving SC-1 and producing SC-4.
...
Credential hygiene (threat T-01-02, D-02): loads EBAY_CLIENT_ID /
EBAY_CLIENT_SECRET / EBAY_ENV via load_dotenv() + os.environ, and never
prints the full access token — only token_type and expires_in.
"""
```
Apply the same style to `seed_catalog.py`: open with what the script proves/does (idempotent catalog upsert), cross-reference the CONTEXT.md decision IDs it satisfies (D-02 Pitch Black re-seed workflow, D-06 booster_bundle), and state the credential-hygiene contract (`MONGODB_URI` loaded only via `os.environ`/`load_dotenv()`, never logged).

**`.env` / dotenv loading pattern** (lines 18-23, 46-47):
```python
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from ebay_client import get_app_token, search_sealed_listings, total_cost
...
def main() -> int:
    load_dotenv()
    env = os.environ.get("EBAY_ENV", "production")
```
Reuse directly: `seed_catalog.py` should `load_dotenv()` at the top of `main()`, then read `MONGODB_URI = os.environ["MONGODB_URI"]` — same convention as `EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET`. Import shape (sibling-module imports like `from ebay_client import ...`) shows this repo imports flat from `scripts/`, not via a package — mirror with `from catalog_data import CATALOG` and `from init_collections import init_collections` (adjust for `db/` being a separate top-level dir — see Shared Patterns below for import-path handling).

**Entrypoint / `main()` + `sys.exit` pattern** (lines 45, 125-126):
```python
def main() -> int:
    ...
    return 0

if __name__ == "__main__":
    sys.exit(main())
```
Copy verbatim structure for `seed_catalog.py`: a `main() -> int` function doing the work, returning 0 on success (nonzero + stderr warnings on partial failure, matching the `WARNING:` + `file=sys.stderr` pattern at lines 108-113 and 115-120), invoked via `sys.exit(main())`.

**Warning/non-fatal-issue pattern** (lines 107-113):
```python
if len(fixture_records) < FIXTURE_TARGET[0]:
    print(
        f"WARNING: captured {len(fixture_records)} listings, below the "
        f"SC-4 target lower bound of {FIXTURE_TARGET[0]}. Consider adding "
        "more CATALOG_QUERIES or checking API access.",
        file=sys.stderr,
    )
```
Apply to `seed_catalog.py` for the Pitch Black provisional-data case (D-02/Pitfall 2): print a `WARNING:` to stderr when seeding documents flagged `verified: false`, without failing the script — mirrors this repo's existing convention of "warn, don't crash" for known-provisional states.

**Core idempotent upsert pattern** (from RESEARCH.md Pattern 2, no repo analog exists — use as primary source):
```python
from pymongo import UpdateOne

def seed_catalog(db, catalog_data: list[dict]):
    ops = []
    for product in catalog_data:
        slug = f"{product['set_name']}_{product['product_type']}".lower().replace(" ", "-")
        product["_id"] = slug
        ops.append(UpdateOne({"_id": slug}, {"$set": product}, upsert=True))
    if ops:
        result = db.products.bulk_write(ops)
        print(f"matched={result.matched_count} upserted={len(result.upserted_ids)} modified={result.modified_count}")
```
Note the summary-print pattern (`matched=... upserted=... modified=...`) is consistent with `verify_ebay_access.py`'s habit of printing concrete proof/counts to stdout after an operation (e.g., line 105 `print(f"Captured {len(fixture_records)} listings -> {FIXTURE_PATH}")`) — keep that convention for the seed script's final output.

---

### `db/init_collections.py` (config, batch/create-if-not-exists)

**Analog:** `scripts/ebay_client.py` (full file read — 117 lines)

**Module docstring pattern** (lines 1-16):
```python
"""Reusable eBay OAuth + Browse API client functions.

Provides the OAuth Client Credentials Grant handshake and a Browse API
keyword search wrapper. Intentionally minimal for Phase 1's feasibility
spike ...

No top-level network calls execute on import — every function must be
explicitly invoked by a caller (see scripts/verify_ebay_access.py).
"""
```
Apply the same "no top-level side effects on import" discipline to `db/init_collections.py`: the module should define `init_collections(db)` as a pure function, with zero collection-creation calls executed at import time — only invoked explicitly by `seed_catalog.py` or a test fixture.

**Function-level docstring with Args/Returns pattern** (lines 26-40, 62-80, 98-110):
```python
def get_app_token(env: str = "production") -> dict:
    """Exchange EBAY_CLIENT_ID/EBAY_CLIENT_SECRET for an application access token.

    Uses the OAuth Client Credentials Grant against eBay's identity
    token endpoint. ...

    Args:
        env: "production" or "sandbox" — selects the API host.

    Returns:
        Parsed JSON response dict containing access_token, expires_in,
        and token_type.
    """
```
Reuse this Google-style docstring shape (What/why in prose, then `Args:`/`Returns:`) for `init_collections(db)` — explain the create-if-not-exists rationale (time-series options are creation-time-only, per RESEARCH.md Pitfall 1) directly in the docstring, not just inline comments.

**Core create-if-not-exists pattern** (from RESEARCH.md Pattern 1, no repo analog exists — use as primary source):
```python
from pymongo import MongoClient, ASCENDING

def init_collections(db):
    if "products" not in db.list_collection_names():
        db.create_collection(
            "products",
            validator={"$jsonSchema": {...}},
            validationLevel="strict",
            validationAction="error",
        )
        db.products.create_index([("set_name", ASCENDING), ("product_type", ASCENDING)])

    if "price_points" not in db.list_collection_names():
        db.create_collection(
            "price_points",
            timeseries={"timeField": "ts", "metaField": "product_id", "granularity": "hours"},
        )
```

---

### `scripts/catalog_data.py` (data module)

**No direct repo analog** — this is the first pure-data module in the project. Structure per RESEARCH.md Code Examples:
```python
CATALOG = [
    {
        "set_name": "Perfect Order",
        "product_type": "booster_box",
        "language": "en",
        "release_date": "2026-03-27",
        "msrp": 161.64,
        "image_url": "https://tcgplayer-cdn.tcgplayer.com/product/672394_in_1000x1000.jpg",
        "display_name": "Pokemon TCG: Mega Evolution—Perfect Order Booster Display Box (36 Packs)",
        "required_keywords": ["perfect order", "booster box", "display"],
    },
    # ... 15 more entries
]
```
Follow `scripts/ebay_client.py`'s constant-naming convention (module-level `ALL_CAPS` for constants, e.g. `TIMEOUT_SECONDS = 15` at line 23; `CATALOG_QUERIES` list in `verify_ebay_access.py` line 31) — name the top-level list `CATALOG` (all caps, matches `CATALOG_QUERIES` precedent).

---

### `tests/test_catalog_schema.py` (test, integration)

**No repo analog** — no `tests/` directory or pytest config exists yet. Reference RESEARCH.md Validation Architecture directly:
- Framework: pytest 8.x (`pip install pytest==8.4.2`)
- Needs `tests/conftest.py` for a shared test-DB fixture (decide real MongoDB test DB vs `mongomock` at plan time)
- Test function names should map 1:1 to the phase's requirement table: `test_catalog_completeness`, `test_seed_idempotent`, `test_schema_validator_rejects_malformed`, `test_query_by_set_and_type`
- Error-handling/assertion style: no repo precedent exists; use plain pytest `assert` statements (idiomatic pytest, no `unittest.TestCase` needed)

---

## Shared Patterns

### `.env` / credential loading
**Source:** `scripts/verify_ebay_access.py` lines 18-23, 46-47 (`from dotenv import load_dotenv`; `load_dotenv()` inside `main()`; `os.environ["..."]` for required vars, `os.environ.get("...", default)` for optional ones)
**Apply to:** `scripts/seed_catalog.py` (for `MONGODB_URI`) and any test fixture in `tests/conftest.py` that needs a test-DB connection string. Never hardcode `MONGODB_URI` — matches RESEARCH.md's explicit anti-pattern warning and Phase 1's established convention.

### No top-level side effects on import
**Source:** `scripts/ebay_client.py` line 14-16 docstring: "No top-level network calls execute on import — every function must be explicitly invoked by a caller."
**Apply to:** `db/init_collections.py` and `scripts/catalog_data.py` — collection creation and DB writes must only happen inside explicitly-called functions (`init_collections(db)`, `seed_catalog(db, CATALOG)`), never at module import time. This also makes both modules safely importable from `tests/test_catalog_schema.py` without side effects.

### `main() -> int` + `sys.exit(main())` entrypoint shape
**Source:** `scripts/verify_ebay_access.py` lines 45, 125-126
**Apply to:** `scripts/seed_catalog.py` — same entrypoint convention: a `main() -> int` doing the real work (load env, connect to Mongo, call `init_collections`, call `seed_catalog`), returning 0/nonzero, invoked via `if __name__ == "__main__": sys.exit(main())`.

### Never log/print secrets, only proof-of-success metadata
**Source:** `scripts/ebay_client.py` lines 9-12 and `scripts/verify_ebay_access.py` lines 60-64 (prints `token_type`/`expires_in`, never the token itself)
**Apply to:** `scripts/seed_catalog.py` — if `MONGODB_URI` embeds Atlas credentials, never print the full connection string; print only host/db name or a success/count summary, matching the token-metadata-only precedent.

### Import style: flat sibling imports within `scripts/`
**Source:** `scripts/verify_ebay_access.py` line 25: `from ebay_client import get_app_token, search_sealed_listings, total_cost`
**Apply to:** `scripts/seed_catalog.py` importing `from catalog_data import CATALOG`. Because `db/init_collections.py` lives in a sibling top-level directory (not `scripts/`), the seed script will need either a `sys.path` adjustment, a relative/package import, or to be run as `python -m` from the repo root — flag this as a concrete decision point for the planner since no existing precedent in this repo crosses a directory boundary this way (Phase 1 code is entirely flat within `scripts/`).

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `scripts/catalog_data.py` | data module | batch | No pure-data module exists in the repo yet; follow RESEARCH.md's Code Examples section directly (canonical document shape shown there) |
| `db/init_collections.py` core create-if-not-exists logic | config | batch | No MongoDB/PyMongo code exists anywhere in the repo yet; follow RESEARCH.md Pattern 1 verbatim (official MongoDB docs pattern), only docstring/import conventions borrowed from `ebay_client.py` |
| `tests/test_catalog_schema.py` | test | integration | No `tests/` directory or pytest config exists yet — this is the project's first test file; follow RESEARCH.md's Validation Architecture section for framework/command conventions since there is no in-repo precedent |

## Metadata

**Analog search scope:** `scripts/` (only pre-existing source directory besides `.claude/` and `.planning/`); confirmed via `find` that no `tests/`, `db/`, or other source directories exist yet in the repo.
**Files scanned:** `scripts/ebay_client.py`, `scripts/verify_ebay_access.py`, `requirements.txt`, `.env.example` (read attempt blocked by permission settings — not required, existing `MONGODB_URI` var name convention should be inferred from RESEARCH.md's `.env` guidance and named consistently, e.g. `MONGODB_URI`)
**Pattern extraction date:** 2026-07-13
