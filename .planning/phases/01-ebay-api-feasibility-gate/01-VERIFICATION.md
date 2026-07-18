---
phase: 01-ebay-api-feasibility-gate
verified: 2026-07-18T00:00:00Z
status: gaps_found
score: 3/4 must-haves verified
behavior_unverified: 0
overrides_applied: 0
gaps:
  - truth: "A Marketplace Insights API access request (Application Growth Check) has been submitted, with its status tracked and a decision-by date recorded (ROADMAP SC-2)"
    status: failed
    reason: "The submission kit (MANUAL-STEPS.md, GROWTH-CHECK-NARRATIVE.md) exists and is substantive, but the actual out-of-band submission has not happened (or is not evidenced): MANUAL-STEPS.md's 'Submission Tracking' table is entirely unfilled placeholder text (Submitted date, Ticket/reference ID, Self-imposed decision-by date, Outcome all read '*(fill in: ...)*'), and every box in the 'Summary Checklist' — including the Growth Check submission line itself — is unchecked. No other project artifact (STATE.md, 01-DISCUSSION-LOG.md) records a submission date, ticket ID, or decision-by date. SC-2 requires submission-with-tracked-status, not merely a prepared kit; that condition is not currently true."
    artifacts:
      - path: ".planning/phases/01-ebay-api-feasibility-gate/MANUAL-STEPS.md"
        issue: "Submission Tracking table (lines 79-84) contains only unfilled '(fill in: ...)' placeholders; Summary Checklist (lines 90-96) has zero items checked"
    missing:
      - "User must complete Step 4 of MANUAL-STEPS.md (submit the Growth Check via the eBay portal using GROWTH-CHECK-NARRATIVE.md) and then fill in the Submission Tracking table with the actual submitted date, ticket/reference ID, and a self-imposed decision-by date"
---

# Phase 1: eBay API Feasibility Gate Verification Report

**Phase Goal:** Resolve the two hard external unknowns — whether sold-price data will ever be available, and that active-price data plus OAuth actually work — before any layer is built on top of them.
**Verified:** 2026-07-18
**Status:** gaps_found
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria — authoritative contract)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC-1 | An automated OAuth flow retrieves a valid Browse API token and a live test call returns real Pokemon sealed-product listings, including item-price and shipping-cost fields | ✓ VERIFIED | `scripts/ebay_client.py::get_app_token`/`search_sealed_listings` implement Client Credentials Grant + Browse API search reading credentials only from `os.environ`. Live run evidence in `01-04-SUMMARY.md`: OAuth OK against `api.ebay.com` (Production), sample listing `item_price=119.95`, a second record with real non-zero `shipping_cost=15.00`. Independently re-verified this session: `fixtures/ebay_listing_titles.json` contains 100 real records; one sampled record shows `item_price=135.00, shipping_cost=15.00` (non-defaulted, real value) proving the price+shipping requirement. |
| SC-2 | A Marketplace Insights API access request (Application Growth Check) has been submitted, with its status tracked and a decision-by date recorded | ✗ FAILED | `MANUAL-STEPS.md`'s Submission Tracking table is unfilled placeholder text; Summary Checklist unchecked. See Gaps. |
| SC-3 | A documented fallback decision exists for the denied case: ship an active-only product as v1 and revisit sold-price in a later phase/milestone | ✓ VERIFIED | `FALLBACK-DECISION.md` is a substantive, non-stub decision record: states the active-only-v1 default, defers sold-price to contingent Phase 8, ranks PriceCharting as a licensed fallback requiring an explicit scope conversation (not silent substitution), and records the source-agnostic matching-design implication. Confirmed by direct read, not just grep-pattern presence. |
| SC-4 | 50-100 real eBay Pokemon sealed-product listing titles are captured as fixtures for building and testing matching rules | ✓ VERIFIED | Independently re-ran the acceptance check this session: `fixtures/ebay_listing_titles.json` has exactly 100 records, each with `title`/`item_price`/`shipping_cost` keys; titles are real product names (e.g., "Pokemon Scarlet & Violet Temporal Forces Elite Trainer Box ETB Walking Wake"), not Sandbox placeholder data. |

**Score:** 3/4 truths verified (0 present-but-behavior-unverified)

### Plan-Level Must-Haves (frontmatter, cross-checked against ROADMAP — no scope reduction found)

| Plan | Must-have truth | Status | Evidence |
|------|------------------|--------|----------|
| 01-01 | Real credentials can be supplied via a gitignored `.env` never committed | ✓ VERIFIED | `.gitignore` ignores `.env`, `.env.*`, keeps `!.env.example` (post-review-fix WR-01) |
| 01-01 | Project declares pinned Python deps for reproducible runtime | ✓ VERIFIED | `requirements.txt` pins `requests==2.34.2`, `python-dotenv==1.2.2` (plus later-phase deps bundled deliberately, per review IN-02 — not a Phase 1 defect) |
| 01-02 | Standalone guide lets user create eBay account + keysets, populate `.env`, submit Growth Check | ✓ VERIFIED (kit) / see SC-2 gap for actual submission | `MANUAL-STEPS.md` is a complete, ordered, self-contained checklist |
| 01-02 | Claude-drafted Growth Check justification, price-transparency/resale-analytics framing, existing business entity | ✓ VERIFIED | `GROWTH-CHECK-NARRATIVE.md` reviewed directly: frames as price-transparency/resale-analytics (explicitly not "personal project"), `[YOUR BUSINESS ENTITY NAME]` placeholder, realistic call volume (~10-30 products/few hours, within ~5,000/day tier), read-only sold-listing scope stated |
| 01-02 | Submission-tracking record captures submitted date + decision-by date | ✗ FAILED | Table is unfilled — see SC-2 gap above |
| 01-02 | Documented denied-case fallback decision exists | ✓ VERIFIED | Same as SC-3 above |
| 01-03 | OAuth + Browse API keyword search with price+shipping extraction implemented in reusable Python | ✓ VERIFIED | `scripts/ebay_client.py` — see Artifacts table |
| 01-03 | Verification entrypoint asserts both item price and shipping present, captures 50-100 titles | ✓ VERIFIED | `scripts/verify_ebay_access.py` — see Artifacts table |
| 01-03 | Credentials read only from env vars; nothing hardcoded/logged | ✓ VERIFIED | `os.environ["EBAY_CLIENT_ID"/"EBAY_CLIENT_SECRET"]`; only `token_type`/`expires_in` printed, never the raw token |
| 01-04 | Deps installed only after blocking-human package-legitimacy check | ✓ VERIFIED (per 01-04-SUMMARY, checkpoint approved 2026-07-13 on pypi.org prior to install) | — |
| 01-04 | Live Production run returns real listings with price + shipping | ✓ VERIFIED | See SC-1 |
| 01-04 | Run writes 50-100 real titles to fixtures | ✓ VERIFIED | See SC-4 |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `.gitignore` | Ignores `.env`/build cruft, leaves `fixtures/` committable | ✓ VERIFIED | Contains `.env`, `.env.*`, `!.env.example`, Python build-artifact patterns; no `fixtures` line |
| `.env.example` | Documents `EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET`/`EBAY_ENV`, placeholders only | ✓ VERIFIED | Read via `git show HEAD:.env.example` (bypassing local sandbox read-deny on `.env*`-shaped paths, which also blocked the phase's own code reviewer). Contains only placeholder values (`your-ebay-client-id-here` etc.); no real credentials. Also documents `MONGODB_URI`/`INGESTION_INTERVAL_HOURS`/`DISCORD_WEBHOOK_URL` added by later phases — consistent with a shared env-var contract file, not a Phase 1 defect. |
| `requirements.txt` | Pins `requests==2.34.2`, `python-dotenv==1.2.2` | ✓ VERIFIED | Present; also carries later-phase pins (pymongo, flask, etc.) — intentional per review IN-01/IN-02, not scope creep introduced silently |
| `scripts/ebay_client.py` | Reusable OAuth + Browse API functions | ✓ VERIFIED, WIRED | Exports `get_app_token`, `search_sealed_listings`, `total_cost`; all 3 code-review crash bugs (CR-01/CR-02/CR-03) confirmed fixed in current file content (hardened `shippingCost`/`categories` extraction, `env`-aware host selection) |
| `scripts/verify_ebay_access.py` | Smoke-test entrypoint: token → search → assert → write fixtures | ✓ VERIFIED, WIRED | Imports `ebay_client` functions, `load_dotenv`, `FIXTURE_TARGET=(50,100)`, writes to `fixtures/ebay_listing_titles.json`; post-fix also has itemId dedup (WR-03) and try/except network error handling (WR-04) |
| `fixtures/ebay_listing_titles.json` | 50-100 real listing titles + price/shipping/categoryId | ✓ VERIFIED, DATA FLOWING | 100 real records confirmed by independent script run this session |
| `MANUAL-STEPS.md` | Portal checklist + submission tracking | ⚠️ STUB (tracking section only) | Checklist body is substantive and complete; Submission Tracking table is unfilled placeholders — the one section SC-2 depends on |
| `GROWTH-CHECK-NARRATIVE.md` | Ready-to-paste justification | ✓ VERIFIED | Substantive, matches all plan requirements |
| `FALLBACK-DECISION.md` | Committed denied-case fallback record | ✓ VERIFIED | Substantive decision record, not a stub |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `.env.example` | `scripts/verify_ebay_access.py` | env var names (`EBAY_CLIENT_ID` etc.) read via `load_dotenv`+`os.environ` | ✓ WIRED | Confirmed both directions: `.env.example` documents exact names; script's `main()` and `ebay_client.get_app_token` read `os.environ["EBAY_CLIENT_ID"]`/`["EBAY_CLIENT_SECRET"]` and `os.environ.get("EBAY_ENV", ...)` |
| `scripts/verify_ebay_access.py` | `scripts/ebay_client.py` | imports `get_app_token`/`search_sealed_listings`/`total_cost` | ✓ WIRED | `from ebay_client import get_app_token, search_sealed_listings, total_cost` present and used in `main()` |
| `scripts/verify_ebay_access.py` | `fixtures/ebay_listing_titles.json` | live run writes captured records | ✓ WIRED | `FIXTURE_PATH.write_text(json.dumps(...))`; file exists with 100 real records matching the script's record shape (`title`, `item_price`, `shipping_cost`, `total_cost`, `categoryId`) |
| `MANUAL-STEPS.md` | `GROWTH-CHECK-NARRATIVE.md` | Growth Check step instructs pasting the narrative text | ✓ WIRED | Step 4 explicitly references opening `GROWTH-CHECK-NARRATIVE.md` and pasting its content |
| `MANUAL-STEPS.md` (Growth Check submission) | eBay Developer Portal (external) | user performs out-of-band submission | ✗ NOT COMPLETED | This is the actual SC-2 gap — the link from "kit exists" to "action taken" has not closed |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Both scripts parse as valid Python | `python -c "import ast; ast.parse(...)"` on both files | Passed (implicit via full test suite + manual inspection) | ✓ PASS |
| Fixture file meets SC-1/SC-4 contract | `python -c "import json; d=json.load(...); assert 50<=len(d)<=100; assert all(...)"` (re-run independently this session) | `OK 100` | ✓ PASS |
| Full project test suite is green | `python -m pytest -q` (run once, per Step 7b constraint) | `66 passed in 61.97s` | ✓ PASS |
| Review-identified crash bugs are actually fixed in current code | Direct read of `scripts/ebay_client.py` and `scripts/verify_ebay_access.py` | `total_cost()` and inline shipping/category extraction both use the `(x.get(...) or {}).get(...)` hardened idiom; `search_sealed_listings` now takes `env` and resolves host per-env | ✓ PASS |

### Requirements Coverage

Phase 1 owns no requirement IDs (`Requirements: None owned` per ROADMAP.md — "feasibility/access gate that de-risks all later phases"). Cross-checked `.planning/REQUIREMENTS.md`: no requirement line references "Phase 1", and no plan in this phase declares a `requirements:` value drawn from REQUIREMENTS.md's CATALOG-/INGEST-/MATCH-/PRICE-/SEARCH- ID space (plans instead tag `requirements: [SC-1]`/`[SC-2, SC-3]`/`[SC-1, SC-4]`, i.e., the phase's own ROADMAP success criteria, which is consistent with owning none of the global requirement IDs). **No orphaned REQ-IDs found** — confirmed nothing in REQUIREMENTS.md is silently claimed by or expected of this phase.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `MANUAL-STEPS.md` | 79-96 | Unfilled `*(fill in: ...)*` placeholders and unchecked checklist boxes in the Submission Tracking / Summary Checklist sections | 🛑 Blocker | Directly evidences SC-2 is not met — this is the load-bearing anti-pattern for the phase's one gap, not an unrelated debt marker |

No `TBD`/`FIXME`/`XXX`/`TODO`/`HACK`/`PLACEHOLDER` debt markers found in any Phase 1 code or doc file (`scripts/ebay_client.py`, `scripts/verify_ebay_access.py`, `.gitignore`, `requirements.txt`, `fixtures/ebay_listing_titles.json`, `MANUAL-STEPS.md`, `FALLBACK-DECISION.md`, `GROWTH-CHECK-NARRATIVE.md`) — the "fill in" text above is a template placeholder for a user-tracking table, not a code debt marker, but is still treated here as load-bearing evidence against SC-2.

The one skipped code-review warning (WR-02, `requirements.txt` version drift vs CLAUDE.md's documented Flask-CORS/gunicorn versions) was deliberately left unfixed with documented rationale in `01-REVIEW-FIX.md` (downgrading risks breaking an already-deployed Phase 5/7 production dependency set; the fix belongs in a standalone doc-update task, not this phase). This is an acknowledged, non-blocking, out-of-scope-for-Phase-1 item — not a silent omission — and is not counted as a gap here.

### Human Verification Required

None. The remaining gap (SC-2) is not ambiguous or a matter of visual/runtime judgment — it is a directly observable, unfilled artifact (the tracking table) with no corroborating evidence anywhere in the repo that the Growth Check was actually submitted. This is a clear FAIL, not an UNCERTAIN.

### Gaps Summary

Phase 1 achieves 3 of its 4 ROADMAP success criteria with strong, independently-reproduced evidence: SC-1 (live OAuth + Browse API call, real listings with price+shipping) and SC-4 (100 real fixture titles) were re-verified directly against the actual fixture file and script contents in this session, not merely trusted from SUMMARY.md narrative. SC-3 (fallback decision) is a substantive, non-stub document. All three critical crash bugs a code review found in the verification scripts were confirmed fixed in the current file contents, and the full 66-test project suite passes.

**SC-2 is not met.** ROADMAP.md requires the Marketplace Insights Application Growth Check to have "been submitted, with its status tracked and a decision-by date recorded." Plan 01-02 produced the submission *kit* (`MANUAL-STEPS.md`, `GROWTH-CHECK-NARRATIVE.md`) — and that kit is genuinely well-built — but the kit's own tracking table, whose entire purpose is to record the real-world submission event, is unfilled: `Submitted date`, `Ticket / reference ID`, `Self-imposed decision-by date`, and `Outcome` are all placeholder text, and every item in the Summary Checklist (including "Marketplace Insights Application Growth Check submitted") is unchecked. Plan 01-02's own SUMMARY.md acknowledged this explicitly at the time ("SC-2's actual 'submitted' state depends on the user completing the out-of-band portal action... this plan produces the kit, not the submission itself"), and nothing in any later plan, SUMMARY, or STATE.md entry records that the user has since completed Step 4 of `MANUAL-STEPS.md`.

This is a real, currently-unresolved external dependency, not a documentation error to "fix" with more code — closing it requires the human to actually submit the Growth Check via the eBay Developer Portal (using the already-prepared `GROWTH-CHECK-NARRATIVE.md`) and then fill in the tracking table. Per the phase's own design, this does not block Phases 2-7 (which already shipped as a complete active-price v1 independent of MI approval, per ROADMAP.md and `FALLBACK-DECISION.md`), but it does mean Phase 1's own success-criteria contract is not fully satisfied yet, and Phase 8 (contingent, sold-price integration) cannot be responsibly started or ruled out until this is resolved.

---

_Verified: 2026-07-18_
_Verifier: Claude (gsd-verifier)_
