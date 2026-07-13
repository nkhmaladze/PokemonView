---
phase: 2
slug: product-catalog-data-model
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-13
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (not yet installed — Wave 0 gap) |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `pytest tests/test_catalog_schema.py -x` |
| **Full suite command** | `pytest tests/ -x` |
| **Estimated runtime** | ~15 seconds (small integration suite against a single low-cardinality collection; no measured baseline yet) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_catalog_schema.py -x`
- **After every plan wave:** Run `pytest tests/ -x`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

Task IDs are assigned by the planner; this table pre-maps each phase requirement to its test so the planner can slot in real Task IDs directly. Update the Task ID / Plan / Wave columns once PLAN.md files exist.

Test files are authored in Plan 02-05 (Wave 2, RED) and driven green in Plan 02-06 Task 2 (Wave 3). The `$jsonSchema` validator the rejection test exercises is created in Plan 02-04 (Wave 2).

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-05-T2 (authored) → 02-06-T2 (green) | 02-05 → 02-06 | 2 → 3 | CATALOG-01 | — | Catalog contains every in-scope product (4 sets × up to 4 product types, ~15-16 docs, excluding D-05 exclusions) as a distinct entry | integration | `pytest tests/test_catalog_schema.py::test_catalog_completeness -x` | ❌ W0 | ⬜ pending |
| 02-05-T2 (authored) → 02-06-T2 (green) | 02-05 → 02-06 | 2 → 3 | CATALOG-01 | T-02-06 | Re-running the seed script does not create duplicate documents | integration | `pytest tests/test_catalog_schema.py::test_seed_idempotent -x` | ❌ W0 | ⬜ pending |
| 02-05-T2 (authored) → 02-06-T2 (green); validator from 02-04-T1 | 02-04/02-05 → 02-06 | 2 → 3 | CATALOG-02 | T-02-01 / V5 (input validation) | Every catalog document has set_name, product_type, release info, msrp, image_url per the `$jsonSchema` validator (malformed product_type rejected at DB layer) | unit/integration | `pytest tests/test_catalog_schema.py::test_schema_validator_rejects_malformed -x` | ❌ W0 | ⬜ pending |
| 02-05-T2 (authored) → 02-06-T2 (green); index from 02-04-T1 | 02-04/02-05 → 02-06 | 2 → 3 | CATALOG-02 | — | Catalog is queryable by set and product_type via the compound index | integration | `pytest tests/test_catalog_schema.py::test_query_by_set_and_type -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_catalog_schema.py` — stubs for CATALOG-01 (completeness, idempotency), CATALOG-02 (schema validation, query pattern)
- [ ] `tests/conftest.py` — shared fixture for a test MongoDB connection (real MongoDB test DB, or `mongomock` — decide at plan time based on whether Atlas/local MongoDB is provisioned)
- [ ] `pip install pytest==8.4.2` — no test infrastructure exists in the repo yet

---

## Manual-Only Verifications

*All phase behaviors have automated verification.* The MongoDB instance provisioning step (Atlas M0 or local install) and the `pymongo` package legitimacy `[SUS]`-false-positive checkpoint are task-level `checkpoint:human-verify` gates handled in PLAN.md, not behavior verifications tracked here.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
