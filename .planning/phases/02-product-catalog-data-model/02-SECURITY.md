---
phase: 02
slug: product-catalog-data-model
status: verified
# threats_open = count of OPEN threats at or above workflow.security_block_on (high) severity (the blocking gate)
threats_open: 0
asvs_level: 1
created: 2026-07-14
---

# Phase 02 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> Register aggregated from the six 02-*-PLAN.md `<threat_model>` blocks (plan-local threat IDs; the Plan column disambiguates reused IDs). block_on: high · asvs_level: 1.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| PyPI registry → local Python environment | An installed package executes arbitrary code at import/build time; a malicious/typosquatted package would cross into the trusted dev environment | Package code (pymongo, pytest) |
| `.env` (secret) → source control / `.env.example` | The MongoDB connection string may embed Atlas user:pass; committing it would leak DB credentials | MONGODB_URI (secret) |
| Network → MongoDB instance | Atlas Network Access / local bind controls who can reach the database | DB queries / catalog data |
| Web research sources → catalog data | Web-sourced MSRP / lineup / image-ID facts (some provisional, pre-release Pitch Black) cross into the persisted catalog | Product metadata |
| Any writer (seed, future ingestion, mongosh) → `products` collection | Untrusted/incorrectly-shaped docs attempt to enter the catalog; the DB-level validator is the last line of defense | Product documents |
| Test suite → MongoDB test database | Tests write/drop data; must target an isolated `_test` DB so they never corrupt real catalog data | Test documents |
| Malformed document → `products` validator | The rejection test deliberately crosses the validator boundary to prove V5 enforcement | Invalid product doc |
| Seed script / `.env` MONGODB_URI → seed process | Seed writes cross the validator; connection string is read into the process and must never be logged/committed | Product docs / secret |

---

## Threat Register

| Plan | Threat ID | Category | Component | Severity | Disposition | Mitigation / Evidence | Status |
|------|-----------|----------|-----------|----------|-------------|-----------------------|--------|
| 02-01 | T-02-SC | Tampering (supply chain) | `pip install pymongo` | high | mitigate | Exact pin `pymongo==4.17.0` (requirements.txt:3); blocking human-verify checkpoint completed, [SUS] false-positive documented (02-01-SUMMARY.md:27,31,45,69) | closed |
| 02-01 | T-02-02 | Information Disclosure | requirements.txt | low | accept | No secrets — only public package pins (requirements.txt:1-4) | closed |
| 02-02 | T-02-02 | Information Disclosure | MONGODB_URI in `.env` | high | mitigate | `.env` gitignored (.gitignore:2, `git check-ignore .env` → `.env`) and untracked; `.env.example` carries placeholder-only `mongodb+srv://<user>:<password>@<cluster-host>/pokemonview`; no real creds in any tracked file | closed |
| 02-02 | T-02-01 | Tampering | MongoDB network exposure | medium | accept | v1 dev scope: Atlas M0 IP-allowlist / localhost bind; hardening deferred to Phase 7 | closed |
| 02-03 | T-02-03 | Tampering (data integrity) | CATALOG provisional entries | low | mitigate | `verified` flag per entry, `False` on all Pitch Black (catalog_data.py:228,240,252,264); unresolved image_url/msrp set to `None`, not fabricated; D-02 follow-up recorded (02-06-SUMMARY.md:121-137) | closed |
| 02-03 | T-02-02 | Information Disclosure | scripts/catalog_data.py | low | accept | Pure public product data — no credentials, no MONGODB_URI (file inspected) | closed |
| 02-03 | T-02-01 | Tampering | image_url references | low | accept | Only external TCGplayer CDN reference strings / `None`; no image hosting, no queries built from them this phase | closed |
| 02-04 | T-02-01 | Tampering | `products` write path (shape drift / invalid product_type) | high | mitigate | `$jsonSchema` validator, closed 4-value `product_type` enum, `validationLevel="strict"`, `validationAction="error"`, applied on create AND unconditionally via `collMod` every run (init_collections.py:28-62,103-122) | closed |
| 02-04 | T-02-04 | Denial of Service | `price_points` mis-provisioned as plain collection | medium | mitigate | Created with final `timeseries` options now (timeField ts / metaField product_id / granularity hours) behind create-if-not-exists guard (init_collections.py:68-72,141-145) | closed |
| 02-04 | T-02-02 | Information Disclosure | MongoClient construction | low | accept | `init_collections(db)` takes an already-connected handle; never reads MONGODB_URI or builds a client (init_collections.py:75-102) | closed |
| 02-05 | T-02-01 | Tampering | `$jsonSchema` validator enforcement | high | mitigate | `test_schema_validator_rejects_malformed` inserts invalid `product_type` and asserts WriteError/OperationFailure (test_catalog_schema.py:79-99) | closed |
| 02-05 | T-02-05 | Tampering (test isolation) | test database selection | medium | mitigate | Fixture targets dedicated `pokemonview_test`; drops products/price_points before and after (conftest.py:29,62-63,82-83) | closed |
| 02-05 | T-02-02 | Information Disclosure | MONGODB_URI in fixture | low | mitigate | Loaded via `load_dotenv()` + `os.environ.get`, skips when unset, never printed (conftest.py:46-57) | closed |
| 02-06 | T-02-01 | Tampering | seed upsert write path | high | mitigate | All writes go through validated `db.products.bulk_write`; `UpdateOne({"_id": slug}, {"$set": doc}, upsert=True)` uses parameterized dict filters, no string-concatenated queries (seed_catalog.py:67-79) | closed |
| 02-06 | T-02-06 | Tampering (duplication) | non-idempotent re-seed | medium | mitigate | Deterministic slug `_id` + `UpdateOne(upsert=True)`, no `insert_many` in code; unique compound index (init_collections.py:136-139); `test_seed_idempotent` (test_catalog_schema.py:64-76); live double-run upserted=0 | closed |
| 02-06 | T-02-02 | Information Disclosure | MONGODB_URI in seed process | high | mitigate | Read only from `os.environ` after `load_dotenv()`; prints only matched/upserted/modified counts + set-name WARNING, never the URI (seed_catalog.py:80-84,99-119) | closed |
| 02-06 | T-02-03 | Tampering (data integrity) | Pitch Black provisional data | low | mitigate | `verified=False` flag + non-fatal stderr WARNING naming provisional sets, returns 0 (seed_catalog.py:108-119); D-02 follow-up recorded (02-06-SUMMARY.md:121-137) | closed |

*Status: open · closed · open — below high threshold (non-blocking)*
*Severity: critical > high > medium > low — only open threats at or above high count toward threats_open*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01 | 02-01 / T-02-02 | requirements.txt holds only public package names/versions — no credential surface | Phase 02 planner (PLAN.md disposition) | 2026-07-14 |
| AR-02 | 02-02 / T-02-01 | v1 dev scope: Atlas M0 IP-allowlisting / localhost bind introduces no public unauthenticated exposure; network hardening is Phase 7's operational concern | Phase 02 planner (PLAN.md disposition) | 2026-07-14 |
| AR-03 | 02-03 / T-02-02 | scripts/catalog_data.py is pure public product data — no credentials, no MONGODB_URI, nothing to leak | Phase 02 planner (PLAN.md disposition) | 2026-07-14 |
| AR-04 | 02-03 / T-02-01 | image_url stores only external CDN reference strings; project hosts no image bytes and builds no queries from these strings this phase | Phase 02 planner (PLAN.md disposition) | 2026-07-14 |
| AR-05 | 02-04 / T-02-02 | init_collections(db) takes an already-connected handle; credential handling stays with the caller's `.env` path | Phase 02 planner (PLAN.md disposition) | 2026-07-14 |

*Accepted risks do not resurface in future audit runs.*

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-07-14 | 17 | 17 | 0 | gsd-security-auditor |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-07-14
