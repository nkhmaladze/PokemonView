# Phase 5: Flask REST API (active-price serving) - Pattern Map

**Mapped:** 2026-07-15
**Files analyzed:** 9 (greenfield `api/` package + 1 new test fixture + 2 new test files + 1 requirements.txt edit)
**Analogs found:** 7 / 9 (2 have no direct analog — noted below)

This is a **greenfield** addition — no `api/` directory exists yet. All analogs come from `scripts/`, `db/`, and `tests/` since no Flask code exists anywhere in the repo. Every pattern below is a cross-role adaptation (e.g. "no top-level side effects on import" from a script module applied to a Flask app-factory), not an exact-role match.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|--------------------|------|-----------|-----------------|----------------|
| `api/app.py` (`create_app()`) | config/provider | request-response | `scripts/ebay_client.py` (import discipline) + `db/init_collections.py` (`init_collections(db)` explicit-invocation shape) | role-match (cross-role, pattern-match on discipline) |
| `api/config.py` | config | — | `tests/conftest.py` (env-var loading via `python-dotenv`) | role-match |
| `api/db.py` (`get_db()` helper) | utility | request-response | `tests/conftest.py` fixtures (`MongoClient` construction, credential hygiene) | role-match |
| `api/blueprints/products.py` (routes) | controller/route | request-response | *(no analog — first HTTP layer in repo)* | no analog |
| `api/services/catalog_service.py` | service | CRUD (read-only) | `scripts/matching.py` (pure, DB-taking-as-arg functions; no top-level side effects) | role-match |
| `api/services/price_service.py` | service | CRUD (read-only) + transform | `scripts/matching.py` `aggregate_and_write()` / `filter_outliers()` (pure functions operating on `db` handle + in-memory transform) | strong role-match |
| `tests/conftest.py` (add `api_db`, `app`, `client` fixtures) | test fixture | request-response | `tests/conftest.py` `matching_db` fixture (most recently added, most complete: 4-collection drop/init/teardown + skip-gracefully pattern) | exact (extend same file) |
| `tests/test_api_products.py` | test | request-response | `tests/test_matching.py` (pytest test file using `matching_db`-style fixture, arrange/act/assert over a real Mongo test db) | role-match |
| `tests/test_price_service.py` | test | transform (unit, no Flask/DB) | `tests/test_matching.py` (pure-function unit tests, e.g. `filter_outliers`, no DB fixture needed for pure functions) | role-match |

## Pattern Assignments

### `api/app.py` — `create_app()` application factory

**Analogs:** `scripts/ebay_client.py` (import/side-effect discipline) + `db/init_collections.py` (explicit-invocation, credential handling stays with caller)

**No-top-level-side-effects discipline** (`scripts/ebay_client.py` lines 1-16):
```python
"""...
No top-level network calls execute on import — every function must be
explicitly invoked by a caller (see scripts/verify_ebay_access.py).
"""

import base64
import os

import requests

TIMEOUT_SECONDS = 15


def get_app_token(env: str = "production") -> dict:
    client_id = os.environ["EBAY_CLIENT_ID"]
    client_secret = os.environ["EBAY_CLIENT_SECRET"]
    ...
```
Apply this exact discipline to `create_app()`: no `MongoClient(...)` call, no blueprint registration, no `os.environ` read at module import time — only inside the `create_app()` function body, mirroring how `get_app_token()` reads `EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET` from `os.environ` only when called, never at import.

**"Caller owns credential handling, this function just takes an already-connected handle" pattern** (`db/init_collections.py` lines 130-137):
```python
    Args:
        db: An already-connected pymongo Database handle. This
            function does not read MONGODB_URI or construct a
            MongoClient itself — credential handling stays with the
            caller.
```
`create_app()` is the one place in the new API code that IS allowed to construct the `MongoClient` (mirrors `tests/conftest.py` fixtures doing the same at test-db-setup time) — every other function (services) should receive `db` as a parameter, never construct or import a client itself, exactly like `db/init_collections.py`'s `init_collections(db)` and `scripts/matching.py`'s `aggregate_and_write(db, ...)`.

---

### `api/db.py` / credential loading

**Analog:** `tests/conftest.py` lines 26, 48-57 (env-var + skip-gracefully pattern, adapted — API code should raise/fail clearly rather than `pytest.skip`, but the *loading* mechanics are identical)

```python
import os

import pytest
from pymongo import MongoClient

TEST_DB_NAME = "pokemonview_test"


@pytest.fixture
def catalog_db():
    from dotenv import load_dotenv

    load_dotenv()
    mongodb_uri = os.environ.get("MONGODB_URI")
    if not mongodb_uri:
        pytest.skip(
            "MONGODB_URI not set — provision a MongoDB instance per "
            "Plan 02-02 (MongoDB Atlas M0 or local) and add MONGODB_URI "
            "to .env before running the catalog contract tests."
        )

    client = MongoClient(mongodb_uri)
```
`api/app.py`'s `create_app()` should use the identical `load_dotenv()` + `os.environ["MONGODB_URI"]` idiom (raising `KeyError`/a clear config error instead of `pytest.skip` outside test context), never hardcoding or logging the URI in full — this is the same credential-hygiene rule already applied consistently across `scripts/ebay_client.py`, `scripts/matching.py` docstrings, and every `tests/conftest.py` fixture.

---

### `api/services/catalog_service.py` and `api/services/price_service.py` — pure DB-taking-as-arg service functions

**Analog:** `scripts/matching.py` (whole-file pattern) — this is the strongest analog in the repo for "service layer over pymongo, pure functions, DB passed as first arg"

**Core pattern — pure function taking `db` as first parameter, returning a plain dict/bool** (lines 277-296):
```python
def aggregate_and_write(db, product_id: str, included: list[dict], ts) -> bool:
    """MATCH-03, D-09/D-10/D-11/D-12: writes exactly one price_points
    document for `product_id` when `included` is non-empty, returns
    True. When `included` is empty, writes nothing and returns False
    (D-11 — leave a real gap, never carry forward a stale price)."""
    if not included:
        return False
    db.price_points.insert_one(
        {
            "ts": ts,
            "product_id": product_id,
            "item_price": statistics.median(listing["item_price"] for listing in included),
            "total_price": statistics.median(listing["total_price"] for listing in included),
        }
    )
    return True
```
Directly copy this shape for `price_service.get_current_price(db, product_id)` and `price_service.get_trend_baseline(db, product_id, current_ts, days)` per RESEARCH.md's Code Examples section — `db` first, explicit typed return (`dict | None`/`bool`), one clear docstring paragraph citing which decision (D-xx) the function satisfies, exactly like every function in `scripts/matching.py` does.

**Orchestration-function pattern — one function assembles several smaller pure functions' outputs into a summary dict** (lines 299-392, `run_matching_once`): this is the direct analog for `catalog_service.get_product_detail(db, product_id)`, which must assemble `products` lookup + `get_current_price()` + two `get_trend_baseline()` calls + `compute_pct_change()` into one response dict, mirroring how `run_matching_once` assembles `normalize()` + `match_listing()` + `check_exclusion()` + `filter_outliers()` + `aggregate_and_write()` into one `{listings_matched, listings_unmatched, listings_excluded}` summary.

**Guard-clause / explicit-state-over-null pattern** (lines 256-257, `filter_outliers`):
```python
    if len(listings) < OUTLIER_MIN_COUNT:
        return listings, []
```
Apply the same "explicit early-return with a documented reason, never a silent guess" style to D-01/D-06's "no_data_yet" / "insufficient data" states — return an explicit sentinel/status string alongside `None`, not just `None` alone, matching how `filter_outliers` and `aggregate_and_write` both document exactly why they return what they return.

**Constants-with-a-decision-ID docstring comment pattern** (lines 223-224):
```python
OUTLIER_N_STD = 2  # D-13, locked: 2 population std devs from the median
OUTLIER_MIN_COUNT = 3  # D-14 interpretation: below this, skip filtering entirely
```
Apply identically to Phase 5's `TREND_TOLERANCE_DAYS = 3  # D-05` and a `SET_ORDER` constant (per RESEARCH.md's Pitfall 1 recommendation) with a comment citing D-10.

---

### `tests/conftest.py` — add `api_db`, `app`, `client` fixtures

**Analog:** the existing `matching_db` fixture (lines 155-224) — the most recently added and most complete example of this repo's fixture pattern; extend the same file rather than creating a new conftest.

```python
@pytest.fixture
def matching_db():
    """...
    Skips (rather than errors) when MONGODB_URI is not configured, so
    the scaffold degrades gracefully when no MongoDB instance has been
    provisioned yet (see Plan 02-02, MongoDB provisioning).

    The fixture always targets `pokemonview_test` — a database name
    ending in `_test`, distinct from the real `pokemonview` catalog
    database — and drops its four collections both before and after
    the test runs, so tests never read stale state and never leave
    residue behind (T-04-T1).
    """
    from dotenv import load_dotenv

    load_dotenv()
    mongodb_uri = os.environ.get("MONGODB_URI")
    if not mongodb_uri:
        pytest.skip(
            "MONGODB_URI not set — provision a MongoDB instance per "
            "Plan 02-02 (MongoDB Atlas M0 or local) and add MONGODB_URI "
            "to .env before running the matching contract tests."
        )

    client = MongoClient(mongodb_uri)
    try:
        test_db = client[TEST_DB_NAME]
        test_db.drop_collection("active_listings")
        test_db.drop_collection("price_points")
        test_db.drop_collection("ingestion_runs")
        test_db.drop_collection("ingestion_locks")

        from db.init_collections import init_collections

        init_collections(test_db)
    except Exception:
        client.close()
        raise

    yield test_db

    test_db.drop_collection("active_listings")
    test_db.drop_collection("price_points")
    test_db.drop_collection("ingestion_runs")
    test_db.drop_collection("ingestion_locks")
    client.close()
```

**New `api_db` fixture should:**
1. Copy this exact skip/try-finally/drop-before-and-after shape.
2. Drop+init `products` and `price_points` (mirrors `catalog_db`'s collection set, lines 34-87, since `api_db` needs seeded catalog data, not ingestion collections).
3. Seed `products` via `scripts.seed_catalog.seed_catalog(test_db, CATALOG)` (same lazy import as `catalog_db`, lines 70-75) and additionally insert controlled `price_points` fixture documents directly (`test_db.price_points.insert_many([...])`) for gap/tolerance-window test scenarios (D-01/D-02/D-05/D-06) — no existing fixture does this second part since it's new to this phase; author it new but keep the lazy-import + skip-gracefully wrapper identical.

**New `app`/`client` fixtures (Flask-specific, no analog in this repo — first Flask code)** — follow the official Flask app-factory testing pattern cited in RESEARCH.md Pattern 1/2: `app` fixture calls `create_app(mongodb_uri=..., db_name="pokemonview_test")` pointed at the `api_db` fixture's connection, `client` fixture calls `app.test_client()`. Keep the same lazy-import-inside-fixture-body discipline (`from api.app import create_app` inside the fixture, not at module top) so `pytest --collect-only` keeps succeeding before `api/` files exist yet (Wave 0 scaffold-first convention, explicitly called out in `tests/conftest.py`'s module docstring lines 11-18).

---

### `tests/test_api_products.py` and `tests/test_price_service.py`

**Analog:** `tests/test_matching.py` (not read in full this session, but its existence + `matching_db` fixture usage confirms the established integration-test shape: fixture-injected real Mongo test db, arrange documents, call the function under test, assert on returned dict/collection state)

Recommended split per RESEARCH.md's own Validation Architecture table:
- `tests/test_price_service.py` — pure unit tests, no Flask app, no `client` fixture needed, just `api_db` (or an even lighter in-memory list of price_point dicts if the service functions are pure enough) — mirrors how `tests/test_matching.py` presumably unit-tests `filter_outliers()`/`normalize()` without needing the full `matching_db` fixture for those specific pure functions.
- `tests/test_api_products.py` — integration tests using `client` (Flask test client) + `api_db`, asserting on JSON response shape/status codes — mirrors `matching_db`-fixture-driven tests that exercise `run_matching_once()` end-to-end.

## Shared Patterns

### No top-level side effects on import
**Source:** `scripts/ebay_client.py` lines 14-16, `db/init_collections.py` lines 33-36, `tests/conftest.py` module docstring lines 11-18
**Apply to:** `api/app.py`, `api/db.py`, `api/services/*.py`, `api/blueprints/*.py` — no `MongoClient(...)`, no `os.environ` read, no blueprint registration executes at module import time; everything happens inside `create_app()` or inside a function body called by a test/fixture.

### Credential hygiene (MONGODB_URI via python-dotenv, never logged in full)
**Source:** `tests/conftest.py` lines 48-57 (repeated identically in `ingest_db`, `matching_db`), `scripts/ebay_client.py` lines 9-12
**Apply to:** `api/app.py`'s `create_app()`, `api/config.py`.

### "db passed as first parameter to a pure function" service-layer style
**Source:** `scripts/matching.py` — every function (`aggregate_and_write(db, ...)`, `run_matching_once(db, ...)`)
**Apply to:** `api/services/catalog_service.py`, `api/services/price_service.py` — never a class, never a module-level DB singleton; `db` is always an explicit argument.

### Decision-ID-cited constants and docstrings
**Source:** `scripts/matching.py` lines 64-65, 223-224 (`FUZZY_SCORE_CUTOFF = 90  # [ASSUMED...]`, `OUTLIER_N_STD = 2  # D-13, locked...`)
**Apply to:** Every new constant in `price_service.py` (`TREND_TOLERANCE_DAYS`, `SET_ORDER`) — cite the CONTEXT.md decision ID or mark `[ASSUMED]`/`[Claude's discretion]` explicitly, matching this repo's established documentation discipline.

### Skip-gracefully-without-MongoDB test fixture pattern
**Source:** `tests/conftest.py` — identical block repeated in `catalog_db`, `ingest_db`, `matching_db` (lines 48-57, 116-122, 184-190)
**Apply to:** New `api_db` fixture — copy verbatim, only change the skip message's phase-specific wording and the collection set being dropped/initialized.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `api/blueprints/products.py` (route handlers) | controller/route | request-response | No HTTP/Flask code exists anywhere in the repo yet — this is the first web-request-handling layer. Follow RESEARCH.md's Pattern 2 code example directly (thin routes calling `catalog_service`/`price_service`, `jsonify()` the result, 404 on `None`) since there is no in-repo precedent to copy from. |
| `api/app.py`'s Flask-CORS + blueprint registration wiring | config/provider | request-response | No prior Flask app factory in repo; follow RESEARCH.md's Pattern 1 code example (`create_app()` combining `Flask`, `CORS`, `MongoClient`, blueprint registration) directly — it is already a complete, ready-to-adapt example sourced from official Flask/Flask-CORS docs. |

## Metadata

**Analog search scope:** `scripts/`, `db/`, `tests/` (entire existing Python codebase — `api/` and any frontend directories do not exist yet)
**Files scanned:** `scripts/ebay_client.py`, `scripts/matching.py`, `scripts/catalog_data.py`, `db/init_collections.py`, `tests/conftest.py`, `requirements.txt`, `tests/` directory listing
**Pattern extraction date:** 2026-07-15
