---
phase: 4
slug: listing-matching-price-normalization
status: planned
nyquist_compliant: true
wave_0_complete: false
created: 2026-07-14
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 (already installed and configured — `pytest.ini` sets `pythonpath = .`, `testpaths = tests`) |
| **Config file** | `pytest.ini` (existing) |
| **Quick run command** | `pytest tests/test_matching.py -x` |
| **Full suite command** | `pytest` (runs the whole `tests/` directory, including Phase 2/3's existing tests) |
| **Estimated runtime** | ~15 seconds (unit) / ~30-60 seconds (full suite incl. Phase 2/3 integration tests against Atlas) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_matching.py -x`
- **After every plan wave:** Run `pytest` (full suite, including Phase 2/3's existing tests)
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

Plan/wave/task numbering assigned after planning. Rows below are seeded from RESEARCH.md's Phase Requirements → Test Map (2026-07-14); the planner/plan-checker fill in exact Task ID / Plan / Wave columns once PLAN.md files exist.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-03 T1 | 04-03 | 2 (GREEN) | MATCH-01 | V5 (Input Validation) | `match_listing()` resolves an exact-keyword title to the correct `matched_product_id` with `match_method="keyword"`; falls back to fuzzy for near-miss titles; returns `unmatched`/`ambiguous` for multi-candidate or below-threshold titles | unit | `pytest tests/test_matching.py::test_match_listing_keyword_exact tests/test_matching.py::test_match_listing_fuzzy_fallback tests/test_matching.py::test_match_listing_ambiguous_unmatched -x` | ❌ W0 | ⬜ pending |
| 04-03 T2 | 04-03 | 2 (GREEN) | MATCH-02 | V5 (Input Validation) | `check_exclusion()` correctly flags lot/damaged/counterfeit titles and does NOT flag a legitimate `booster_bundle` listing or a minor-cosmetic-wear listing | unit | `pytest tests/test_matching.py::test_exclusion_lot tests/test_matching.py::test_exclusion_damaged_severe_only tests/test_matching.py::test_exclusion_counterfeit tests/test_matching.py::test_exclusion_does_not_flag_legitimate_bundle -x` | ❌ W0 | ⬜ pending |
| 04-04 T1 | 04-04 | 3 (GREEN) | MATCH-03 | — | `filter_outliers()` excludes listings > 2 std devs from median; skips filtering entirely below the min-count threshold; `aggregate_and_write()` writes correct independent item/total medians and skips the write when included is empty | unit + integration (real MongoDB via new `matching_db` fixture) | `pytest tests/test_matching.py::test_outlier_filter_excludes_far_listings tests/test_matching.py::test_outlier_filter_skipped_when_too_few tests/test_matching.py::test_price_points_median_aggregation tests/test_matching.py::test_price_points_skipped_when_zero_included -x` | ❌ W0 | ⬜ pending |
| 04-04 T2 | 04-04 | 3 (GREEN) | MATCH-01/02/03 (end-to-end) | T-04-01 (see RESEARCH.md Security Domain) | `run_matching_once()` against a `matching_db`-seeded batch of realistic synthetic listings (clean match, lot, damaged, counterfeit, ambiguous, statistical outlier) produces the expected `active_listings` flags, `price_points` document, and returned counts | integration | `pytest tests/test_matching.py::test_run_matching_once_end_to_end -x` | ❌ W0 | ⬜ pending |
| 04-05 T1 | 04-05 | 4 (GREEN) | MATCH-01/02/03 (D-04 integration) | T-04-05 | `run_ingestion_once()` calls `run_matching_once` after the fetch loop and records `listings_matched`/`listings_unmatched`/`listings_excluded` on the `ingestion_runs` document | integration | `pytest tests/test_matching.py::test_run_ingestion_once_records_match_counts tests/test_ingest_worker.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*
*RED authoring for every row above is Plan 04-02 (Wave 1); the Plan/Wave columns above name the GREEN wave that satisfies the behavior.*

---

## Wave 0 Requirements

- [ ] `tests/test_matching.py` — does not exist yet; covers MATCH-01/02/03 unit + integration cases (RED first)
- [ ] `scripts/matching.py` — does not exist yet; core deliverable (`normalize`, `match_listing`, `check_exclusion`, `filter_outliers`, `aggregate_and_write`, `run_matching_once`)
- [ ] `tests/conftest.py` extension — add a `matching_db` fixture mirroring `ingest_db`'s structure but also covering `price_points` (needed for aggregation write tests)
- [ ] `rapidfuzz==3.14.5` install — gated behind `checkpoint:human-verify` per Package Legitimacy Audit (same `[SUS]` false-positive class already approved for `apscheduler`/`pymongo`)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real-data audit of match/exclusion accuracy against live eBay listing titles | MATCH-01, MATCH-02 | Requires real `EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET` (currently lost, per STATE.md) and a completed live Phase 3 ingestion run — cannot be proven against synthetic fixtures alone, mirrors Phase 3's own precedent for its live-verification gap | Once credentials are restored and Phase 3 has run live: query `db.active_listings.find({"match_status": "unmatched"})` and a sample of `exclusion_reason != null` documents; manually eyeball a sample for false positives/negatives per PITFALLS.md's "Looks Done But Isn't" checklist |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** task IDs assigned (04-02 authors all RED tests in Wave 1; 04-03/04-04/04-05 turn them GREEN in Waves 2-4). Every task has an `<automated>` verify; no 3 consecutive tasks lack automated verify; Wave 0 (Plan 04-02) covers all MISSING references; no watch-mode flags; feedback latency < 60s. `wave_0_complete` flips true once Plan 04-02 executes.
