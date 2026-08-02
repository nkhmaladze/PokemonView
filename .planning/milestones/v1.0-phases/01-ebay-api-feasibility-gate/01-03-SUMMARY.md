---
phase: 01-ebay-api-feasibility-gate
plan: 03
subsystem: infra
tags: [ebay, oauth, browse-api, requests, python-dotenv]

# Dependency graph
requires:
  - phase: 01-01
    provides: ".gitignore + .env.example env-var contract (EBAY_CLIENT_ID, EBAY_CLIENT_SECRET, EBAY_ENV) and pinned requirements.txt (requests, python-dotenv)"
provides:
  - "scripts/ebay_client.py — reusable OAuth Client Credentials Grant + Browse API keyword search functions (get_app_token, search_sealed_listings, total_cost)"
  - "scripts/verify_ebay_access.py — single-run smoke-test entrypoint (token -> search -> assert price+shipping -> write fixtures)"
affects: ["01-04", "phase-3-ingestion-worker"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "OAuth Client Credentials Grant as a single ~15-line function, no token cache/refresh wrapper (deferred to Phase 3 ingestion worker)"
    - "total_cost = item price + shipping cost, defaulting shipping to 0.0 when shippingOptions is empty (Pitfall 2)"
    - "Never log/print the full access_token or Basic-auth credential — only token_type/expires_in (threat T-01-02)"

key-files:
  created: [scripts/ebay_client.py, scripts/verify_ebay_access.py]
  modified: []

key-decisions:
  - "Matched the research skeleton's shipping_cost default (\"0.00\" when shippingOptions absent) rather than skipping items lacking shipping data — plan's acceptance criteria and 01-RESEARCH.md's code example both specify defaulting, not exclusion"
  - "Kept get_app_token free of token caching/retry logic per the plan's explicit 'Don't Hand-Roll' guidance — that belongs to Phase 3's ingestion worker"

patterns-established:
  - "Credential/secret hygiene: os.environ-only reads, no print/log of full tokens or Basic-auth strings, applied to both the client module and the entrypoint"

requirements-completed: [SC-1, SC-4]

coverage:
  - id: D1
    description: "scripts/ebay_client.py implements get_app_token, search_sealed_listings, and total_cost, reading credentials only from os.environ with no top-level network call on import"
    requirement: "SC-1"
    verification:
      - kind: other
        ref: "python3 -c \"import ast; ast.parse(open('scripts/ebay_client.py').read())\" && grep -q 'def get_app_token' && grep -q 'def search_sealed_listings' && grep -q 'def total_cost' && grep -q 'os.environ'"
        status: pass
    human_judgment: false
  - id: D2
    description: "scripts/verify_ebay_access.py is a single-run smoke entrypoint that loads env via load_dotenv, imports ebay_client functions, targets fixtures/ebay_listing_titles.json with FIXTURE_TARGET (50,100), extracts shipping cost, and never prints the full access token"
    requirement: "SC-4"
    verification:
      - kind: other
        ref: "python3 -c \"import ast; ast.parse(open('scripts/verify_ebay_access.py').read())\" && grep -q 'load_dotenv' && grep -q 'ebay_client' && grep -q 'FIXTURE_TARGET' && grep -q 'shippingOptions' && grep -q 'ebay_listing_titles.json'"
        status: pass
    human_judgment: false
  - id: D3
    description: "Live execution against real eBay Production credentials, producing the actual 50-100 fixture file — deferred to Plan 04 by design (this plan authors the code path only)"
    verification: []
    human_judgment: true
    rationale: "Requires the user's real EBAY_CLIENT_ID/EBAY_CLIENT_SECRET and outbound network access to api.ebay.com; cannot be exercised or judged complete during code authoring in this plan. Plan 04 owns the live run and human-verify checkpoint."

duration: 2min
completed: 2026-07-13
status: complete
---

# Phase 01 Plan 03: eBay Access Verification Tool (Client + Entrypoint) Summary

**Reusable OAuth Client Credentials Grant + Browse API client (`scripts/ebay_client.py`) and a smoke-test entrypoint (`scripts/verify_ebay_access.py`) that acquires a token, searches for real Pokemon sealed product, asserts price+shipping presence, and writes 50-100 listing titles to `fixtures/ebay_listing_titles.json` — authored and syntactically valid, ready for Plan 04's live run.**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-07-13T04:43:56Z
- **Completed:** 2026-07-13T04:45:32Z
- **Tasks:** 2
- **Files modified:** 2 (both created)

## Accomplishments
- `scripts/ebay_client.py` implements `get_app_token` (Client Credentials Grant, env-only credential reads), `search_sealed_listings` (keyword-only Browse API search), and `total_cost` (item price + shipping, defaulting shipping to 0.0)
- `scripts/verify_ebay_access.py` is a single-run entrypoint: loads `.env`, warns on `EBAY_ENV=sandbox`, searches `CATALOG_QUERIES` across 2-3 recent sets (ETB/booster box/booster pack), captures 50-100 listings with price+shipping+total_cost+categoryId to a fixture file, and prints an explicit SC-1 proof line showing a real price+shipping pair
- Secret hygiene enforced throughout: credentials read only via `os.environ`/`load_dotenv`, full access token never printed or logged (only `token_type`/`expires_in`)

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement scripts/ebay_client.py (OAuth + Browse API functions)** - `291cf82` (feat)
2. **Task 2: Implement scripts/verify_ebay_access.py (smoke-test entrypoint)** - `9858f7b` (feat)

**Plan metadata:** (pending — this SUMMARY commit)

## Files Created/Modified
- `scripts/ebay_client.py` - Reusable OAuth handshake + Browse API search + total-cost functions, no top-level network calls, no token cache/refresh logic (deferred to Phase 3)
- `scripts/verify_ebay_access.py` - Smoke-test entrypoint: token acquisition, multi-query Browse search, price+shipping assertion, fixture write

## Decisions Made
- Matched the research skeleton's exact capture semantics: skip items missing `price`, but default `shipping_cost` to `"0.00"` when `shippingOptions` is absent rather than excluding the item — this follows the plan's acceptance criteria and the `01-RESEARCH.md` code example precisely, rather than a stricter "require shipping data" interpretation initially drafted and then corrected before commit.
- No token caching/refresh wrapper was added to `ebay_client.py` — the plan explicitly scopes that to Phase 3's ingestion worker (see "Don't Hand-Roll" in `01-RESEARCH.md`).

## Deviations from Plan

None - plan executed exactly as written. (One implementation-time self-correction occurred before any commit: an initial draft of the capture loop skipped items lacking `shippingOptions` instead of defaulting `shipping_cost` to `"0.00"` per the plan's stated acceptance criteria and research skeleton; this was corrected during authoring, prior to the Task 2 commit, so it is not tracked as a deviation.)

## Issues Encountered
None.

## User Setup Required

None for this plan. Plan 04 will require the user to have already created `.env` with real `EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET`/`EBAY_ENV` (per Plan 01's `.env.example` contract) before the live run can execute.

## Next Phase Readiness
- Both scripts parse as valid Python and satisfy all plan acceptance criteria.
- `scripts/ebay_client.py`'s three functions (`get_app_token`, `search_sealed_listings`, `total_cost`) are ready to seed Phase 3's ingestion worker.
- `scripts/verify_ebay_access.py` is ready for Plan 04 to run live against real Production credentials, gated behind Plan 04's package-legitimacy `checkpoint:human-verify` for the `requests`/`python-dotenv` install.
- No blockers for Plan 04.

---
*Phase: 01-ebay-api-feasibility-gate*
*Completed: 2026-07-13*

## Self-Check: PASSED

- FOUND: scripts/ebay_client.py
- FOUND: scripts/verify_ebay_access.py
- FOUND commit: 291cf82
- FOUND commit: 9858f7b
