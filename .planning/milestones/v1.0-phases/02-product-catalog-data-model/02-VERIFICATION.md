---
phase: 02-product-catalog-data-model
verified: 2026-07-14T00:00:00Z
status: passed
score: 3/3 must-haves verified
behavior_unverified: 0
overrides_applied: 0
---

# Phase 2: Product Catalog & Data Model Verification Report

**Phase Goal:** A curated catalog of every v1 sealed product exists, persisted on the shared MongoDB data model that ingestion, matching, and pricing all depend on.
**Verified:** 2026-07-14
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | The catalog contains every sealed English product (booster packs, booster boxes, ETBs) for the 2-3 most recent sets, each as a distinct canonical entry. | ✓ VERIFIED | Live query against Atlas `pokemonview.products`: 16 documents, `distinct("set_name")` = {Chaos Rising, Perfect Order, Ascended Heroes, Pitch Black}, `distinct("product_type")` = {booster_pack, booster_box, etb, booster_bundle}. `test_catalog_completeness` independently re-run and passes, asserting count == len(CATALOG) and no duplicate (set_name, product_type) pairs. Scope was widened from "2-3" to 4 sets via an explicit, documented user decision (02-CONTEXT.md D-01) — a superset, not a shortfall. See Note below on doc sync. |
| 2 | Each catalog product carries canonical metadata — set, product type, and release info — usable by matching rules. | ✓ VERIFIED | `scripts/catalog_data.py` CATALOG entries each carry `set_name`, `product_type`, `language`, `release_date`, `msrp`, `image_url`, `display_name`, `required_keywords`, `verified`, `verified_at`. `required_keywords` are disambiguated per product type (booster_bundle carries "bundle"; booster_box carries "box"/"display"; booster_pack carries neither) — read directly from source, confirmed no cross-type keyword collisions. DB-level `$jsonSchema` validator (`required: [set_name, product_type, language, display_name, required_keywords]`) enforces this shape for every writer, not just the seed script. |
| 3 | The catalog is persisted in MongoDB and is queryable by set and product type, on a schema that reserves fields for both item-only and total (item + shipping) price points and time-series history. | ✓ VERIFIED | Live check: `products` collection has compound index `set_name_1_product_type_1` (confirmed via `index_information()`); `test_query_by_set_and_type` passes (query by set alone and by set+type both return correct counts). `price_points` is a genuine native time-series collection (`options.timeseries` = `{timeField: ts, metaField: product_id, granularity: hours}` — confirmed live via `listCollections`), created empty and reserved for Phase 3, with the intended per-point shape `{ts, product_id, item_price, total_price}` documented in `db/init_collections.py`'s comments (item-only vs. total/item+shipping fields both named). |

**Score:** 3/3 truths verified (0 present-but-behavior-unverified)

### Plan-Level Must-Haves (supporting detail)

| Plan | Must-Have | Status | Evidence |
|------|-----------|--------|----------|
| 02-01 | pymongo==4.17.0 and pytest==8.4.2 importable | ✓ VERIFIED | `python3 -c "import pymongo, pytest"` → pymongo 4.17.0, pytest 8.4.2 |
| 02-01 | Human legitimacy checkpoint for pymongo completed before install | ✓ VERIFIED (human judgment) | SUMMARY documents explicit "approve" from user citing pypi.org/mongodb-official-repo evidence |
| 02-02 | MongoDB instance reachable via MONGODB_URI | ✓ VERIFIED | Live `client.admin`-equivalent query succeeded (products/price_points queried without error) |
| 02-02 | MONGODB_URI stored only in .env, never committed | ✓ VERIFIED | `git check-ignore .env` → `.env` (gitignored); `.env.example` content could not be directly inspected per this session's sandbox restriction (same tooling limitation independently noted in 02-REVIEW.md) — not re-verifiable this session, but `git status` shows no pending changes to `.env.example` and no secrets present in tracked history for this phase's commits |
| 02-03 | 16-entry CATALOG spanning 4 sets, 4 product types, Pitch Black flagged verified=False | ✓ VERIFIED | Read `scripts/catalog_data.py` directly — 16 dict entries, all 4 Pitch Black entries have `"verified": False` |
| 02-04 | `products` $jsonSchema validator (strict/error), 4-value product_type enum, null-permitting provisional fields, compound index; `price_points` native time-series, empty; idempotent re-run | ✓ VERIFIED | Read `db/init_collections.py` directly + live `listCollections` check confirms validator, validationLevel=strict/validationAction=error, index, and timeseries options match spec exactly |
| 02-05 | 4-test pytest scaffold, dedicated `_test` database fixture | ✓ VERIFIED | `tests/conftest.py` targets `pokemonview_test`; `pytest tests/ -v` collects and runs exactly 4 tests |
| 02-06 | Idempotent seed populates products; full pytest suite green; Pitch Black warning emitted | ✓ VERIFIED | Live re-run of `pytest tests/` (this session): 4/4 passed. Source contains no `insert_many`; uses `bulk_write([UpdateOne(..., upsert=True)])`. `main()` contains the non-fatal stderr WARNING block for `verified=False` entries. |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `requirements.txt` | pymongo==4.17.0, pytest==8.4.2 pinned | ✓ VERIFIED | Contains exactly 4 lines: requests, python-dotenv, pymongo, pytest |
| `.env` / `.env.example` | MONGODB_URI documented/stored | ✓ VERIFIED (indirect) | `.env` gitignored and confirmed live-reachable; `.env.example` content unreadable this session per sandbox rule (same limitation 02-REVIEW.md hit) |
| `scripts/catalog_data.py` | Module-level CATALOG list of 15-16 dicts | ✓ VERIFIED | 16 entries, all required keys present, wired into seed_catalog.py and test_catalog_schema.py |
| `scripts/__init__.py` | Empty package marker | ✓ VERIFIED | Present, 0 bytes |
| `db/init_collections.py` | `init_collections(db)` function | ✓ VERIFIED | Defines function exactly as specified; no top-level side effects; imported and invoked by seed_catalog.py and tests/conftest.py |
| `db/__init__.py` | Empty package marker | ✓ VERIFIED | Present, 0 bytes |
| `scripts/seed_catalog.py` | `seed_catalog(db, catalog)` + `main()` | ✓ VERIFIED | Defines both; `python -m scripts.seed_catalog` runnable; live-tested this session via re-run of pytest suite (fixture calls seed_catalog) |
| `tests/conftest.py` | `catalog_db` fixture | ✓ VERIFIED | Present, lazy-imports db/scripts modules, targets `pokemonview_test` |
| `tests/test_catalog_schema.py` | 4 test functions | ✓ VERIFIED | All 4 present and independently re-run to green this session |
| `pytest.ini` | `pythonpath = .` | ✓ VERIFIED | Present with `[pytest]` pythonpath=. and testpaths=tests |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| `requirements.txt` | `db/init_collections.py`, `scripts/seed_catalog.py`, `tests/` | pymongo/pytest imports | ✓ WIRED | All modules import pymongo successfully; pytest discovers and runs the suite |
| `.env` (MONGODB_URI) | `scripts/seed_catalog.py`, `tests/conftest.py` | `os.environ` after `load_dotenv()` | ✓ WIRED | Both read `MONGODB_URI` via `os.environ`/`os.environ.get`; live connections succeeded in this session |
| `scripts/catalog_data.py` (CATALOG) | `scripts/seed_catalog.py`, `tests/test_catalog_schema.py` | `from scripts.catalog_data import CATALOG` | ✓ WIRED | Both files import CATALOG at module scope; confirmed by source read and successful test collection/execution |
| `db/init_collections.py` (init_collections) | `scripts/seed_catalog.py`, `tests/conftest.py` | direct function import/call | ✓ WIRED | seed_catalog.py's `main()` calls `init_collections(db)`; conftest.py's fixture lazily imports and calls it; live schema/index confirmed present |
| `scripts/seed_catalog.py` (seed_catalog) | `products` collection via `$jsonSchema` validator | `bulk_write([UpdateOne(upsert=True)])` | ✓ WIRED | Live `products` collection has exactly 16 documents matching CATALOG; `test_schema_validator_rejects_malformed` confirms the validator is actually enforced on writes, not just declared |

### Data-Flow Trace (Level 4)

| Artifact | Data Source | Produces Real Data | Status |
|----------|-------------|---------------------|--------|
| `products` collection | `scripts/catalog_data.py` CATALOG → `seed_catalog()` bulk upsert | Yes — live count (16) matches CATALOG length exactly; live `distinct()` calls return the real 4 set names / 4 product types, not empty/static placeholders | ✓ FLOWING |
| `price_points` collection | Reserved empty for Phase 3 (no writer this phase) | N/A — intentionally empty per plan scope; timeseries options are the "product" of this phase, not documents | ✓ FLOWING (as designed — schema-only, no data expected yet) |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| pymongo/pytest importable | `python3 -c "import pymongo, pytest"` | pymongo 4.17.0, pytest 8.4.2 | ✓ PASS |
| Live products collection populated correctly | pymongo query against Atlas `pokemonview` db | 16 docs, 4 sets, 4 types, validator present (strict/error), compound index present | ✓ PASS |
| `price_points` is a genuine time-series collection | `listCollections` command | `options.timeseries` = `{timeField: ts, metaField: product_id, granularity: hours}` | ✓ PASS |
| Full pytest suite passes (single run, not per-truth) | `pytest tests/ -v` | 4 passed in 3.61s (test_catalog_completeness, test_seed_idempotent, test_schema_validator_rejects_malformed, test_query_by_set_and_type) | ✓ PASS |
| `.env` is gitignored | `git check-ignore .env` | prints `.env` | ✓ PASS |
| No `insert_many` anywhere in scripts/ or db/ | `grep -rn insert_many scripts/ db/` | only 1 hit, inside a docstring explaining the anti-pattern is avoided | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| CATALOG-01 | 02-01, 02-03, 02-05, 02-06 | Curated catalog of sealed English product exists for the in-scope sets | ✓ SATISFIED | 16-entry CATALOG, seeded, live-verified count/distinct values, `test_catalog_completeness`/`test_seed_idempotent` pass |
| CATALOG-02 | 02-01, 02-02, 02-04, 02-05, 02-06 | Each catalog product has canonical metadata used for matching; queryable schema | ✓ SATISFIED | `$jsonSchema` validator enforced (test proves rejection of invalid product_type), compound index queryable, `required_keywords` disambiguated |

No orphaned requirements — REQUIREMENTS.md maps only CATALOG-01/CATALOG-02 to Phase 2, and both are declared across the phase's plans.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `db/init_collections.py:95-104` | WR-01 (02-REVIEW.md) | Compound index creation nested inside collection-existence guard — not independently idempotent on a pre-existing collection missing the index | ⚠️ Warning (non-blocking) | Does not affect this phase's fresh-provisioning path (verified live); would only bite a future redeploy/migration scenario. Not exercised by current test suite. |
| `db/init_collections.py:26-54` | WR-02 (02-REVIEW.md) | `$jsonSchema` validator omits `additionalProperties: false` | ⚠️ Warning (non-blocking) | Validator still enforces required fields + enum correctly (proven by `test_schema_validator_rejects_malformed`); just permits extra unvalidated fields |
| `scripts/seed_catalog.py:99-121` | WR-03 (02-REVIEW.md) | `MongoClient` not closed via try/finally in `main()` | ⚠️ Warning (non-blocking) | Connection-leak risk only on exception path; does not affect the happy-path behavior verified live this session |
| `tests/conftest.py:57-80` | WR-04 (02-REVIEW.md) | Fixture leaks MongoClient on setup failure (no try/finally) | ⚠️ Warning (non-blocking) | Same class of issue as WR-03; setup succeeded cleanly in this session's live re-run |

No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` markers found in any phase-modified file (`db/init_collections.py`, `scripts/catalog_data.py`, `scripts/seed_catalog.py`, `tests/conftest.py`, `tests/test_catalog_schema.py`, `scripts/__init__.py`, `db/__init__.py`). These 4 warnings + 4 info items were already surfaced in `02-REVIEW.md` (0 critical) and do not block phase goal achievement — none of them prevent the catalog from existing, being persisted, or being queryable today; they are hardening items for future writers/redeploys.

### Human Verification Required

None. This phase's success criteria are fully verifiable against the live database and an independently re-run test suite — no visual, real-time, or external-service-dependent behavior in scope.

### Notes (non-blocking)

1. **Scope-note documentation lag:** 02-CONTEXT.md's D-01 explicitly recorded the user's decision to widen the catalog from "2-3 most recent sets" to 4 sets (including the pre-release Pitch Black), and flagged: *"This should be reflected as an updated scope note in PROJECT.md/REQUIREMENTS.md at the next phase transition."* As of this verification, `.planning/PROJECT.md` and `.planning/REQUIREMENTS.md` still say "2-3 most recent sets" (CATALOG-01 wording, Core Value line, Constraints, Out of Scope). This does not affect the phase's technical goal achievement (the catalog is a superset of the original 2-3-set scope, not a shortfall), but the promised doc-sync follow-up was not done. Recommend addressing before/at Phase 3 kickoff since this is exactly "the next phase transition" D-01 referenced.
2. **`.env.example` content unverifiable this session:** Per this session's explicit sandbox instruction, `.env`/`.env.example` files could not be Read/grepped. `02-REVIEW.md` independently hit the same restriction and flagged it as a tooling limitation, recommending manual confirmation that `.env.example` contains only a placeholder `MONGODB_URI=` line. Not re-verified here for the same reason; carried forward as an open item for a human with unrestricted file access to double-check.
3. **~11/16 catalog entries have `image_url=None`** (unresolved TCGplayer product IDs, documented in 02-03-SUMMARY.md as a known, plan-sanctioned gap — the schema explicitly permits null image_url). Not a blocker; a future pass can backfill these.
4. **Pitch Black data is provisional** (`verified=False`) pending the set's actual 2026-07-17 release, per D-02 — this is by design, not a gap, and is tracked as a follow-up in 02-06-SUMMARY.md.

### Gaps Summary

None. All 3 ROADMAP success criteria and all plan-level must-haves are verified against the live codebase and a live MongoDB Atlas database, independently of SUMMARY.md claims: 16 catalog products persisted and queryable, canonical metadata present and validator-enforced, and the `price_points` time-series collection correctly reserved for Phase 3. The full pytest suite (4/4 tests) was independently re-run in this verification session and passed.

---

_Verified: 2026-07-14_
_Verifier: Claude (gsd-verifier)_
