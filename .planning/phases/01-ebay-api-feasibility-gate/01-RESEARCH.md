# Phase 1: eBay API Feasibility Gate - Research

**Researched:** 2026-07-13
**Domain:** eBay Developer Program access/auth (OAuth Client Credentials Grant, Browse API), Application Growth Check process for Marketplace Insights API
**Confidence:** MEDIUM (official eBay docs cross-corroborated across multiple independent sources; some exact portal UI details not directly fetched this session — see Assumptions Log)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** The user does not yet have an eBay Developer Program account (Sandbox + Production keysets). Creating it is a manual, user-performed step. Claude must produce a step-by-step checklist for this before any OAuth code is written.
- **D-02:** Credential handoff: the user creates the `.env` file themselves and pastes the OAuth Client ID/Secret into it directly — credentials are never pasted into chat. Claude writes ingestion/test code that reads from `.env` without ever seeing the raw secret values.
- **D-03:** For the Marketplace Insights Application Growth Check, Claude drafts the use-case/justification narrative (price-transparency/resale-analytics framing, per `research/PITFALLS.md`), and the user pastes it into eBay's portal and submits it themselves. Claude does not submit on the user's behalf.
- **D-04:** Claude writes a standalone `MANUAL-STEPS.md` guide (in the phase directory) listing every manual portal action required in this phase — eBay developer account signup, and the Growth Check submission itself — so the user can work through them independently of the planning/execution flow.
- **D-05:** The user already has a registered business entity. The Marketplace Insights application should be submitted under that existing entity — no new business registration is needed and none should be planned as a Phase 1 task.
- **D-06:** Submission is not blocked or delayed waiting on anything — Phase 1's "application submitted" success criterion is satisfied as soon as the application is submitted under the existing entity, at whatever point Phase 1 execution reaches that step.

### Claude's Discretion
- Exact structure/format of `MANUAL-STEPS.md` (checklist, numbered steps, etc.) is left to Claude.
- Specific eBay Developer Portal navigation details (button names, page flow) — Claude should verify against current eBay docs during planning/research rather than relying on possibly-stale training knowledge.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

Phase 1 owns no REQUIREMENTS.md requirement IDs — it is a feasibility/access gate (per ROADMAP.md: "None owned"). Its deliverables are instead the four ROADMAP.md Success Criteria (SC), which function as this phase's acceptance bar:

| ID | Description | Research Support |
|----|-------------|-------------------|
| SC-1 | Automated OAuth flow retrieves a valid Browse API token; a live test call returns real Pokemon sealed-product listings including item-price and shipping-cost fields | See `## Code Examples` (OAuth token request, Browse API search call) and `## Architecture Patterns` |
| SC-2 | Marketplace Insights API Application Growth Check has been submitted, with status tracked and a decision-by date recorded | See `## Growth Check Submission Process` and `MANUAL-STEPS.md` guidance in `## Architecture Patterns` |
| SC-3 | Documented fallback decision exists for the denied case (ship active-only v1, revisit sold-price later) | Already resolved at project-research level — `research/STACK.md` "Stack Patterns by Variant" and `research/PITFALLS.md` Recovery Strategies; this phase's job is to formalize it as a phase artifact (`FALLBACK-DECISION.md` or equivalent), not re-derive it |
| SC-4 | 50-100 real eBay Pokemon sealed-product listing titles captured as fixtures for Phase 4 matching-rule work | See `## Code Examples` (Browse API search + fixture capture pattern) |
</phase_requirements>

## Summary

Phase 1 is a narrow, script-driven feasibility spike, not a service build. It needs exactly one small Python tool (using `requests` + `python-dotenv`) that: (1) exchanges eBay OAuth Client ID/Secret for an application access token via the Client Credentials Grant, (2) calls the Browse API's `item_summary/search` endpoint with Pokemon sealed-product keywords and confirms the response includes both `price.value` and `shippingOptions[].shippingCost.value`, and (3) writes 50-100 captured listing titles to a fixture file. Everything else in this phase — creating the eBay Developer Program account, creating Sandbox/Production keysets, and submitting the Marketplace Insights Application Growth Check — is a manual, user-performed action in eBay's web portal that Claude documents in `MANUAL-STEPS.md` but does not and cannot automate (no public API exists for account/keyset creation or Growth Check submission).

The Browse API (active listings) requires no special approval: any Production keyset can call it immediately, using an application-level OAuth token obtained via `grant_type=client_credentials` against `https://api.ebay.com/identity/v1/oauth2/token` (or the `.sandbox.` host for Sandbox). The Marketplace Insights API (sold listings) is the real risk: it is a Limited Release API gated behind eBay's Application Growth Check, submitted through the Developer Portal's ticket system, with no published SLA and community-reported patterns of denial for individual/hobby-framed applicants. Per CONTEXT.md D-05/D-06, this project has an existing business entity to apply under and does not need to wait on anything before submitting — Claude's job is to draft the justification narrative; the user submits it.

**Primary recommendation:** Build a single standalone script (`scripts/verify_ebay_access.py` or similar), gated behind a `.env` the user populates themselves (never pasted into chat, per D-02), that performs the OAuth handshake, live Browse API call, and fixture capture in one run — plus a separate `MANUAL-STEPS.md` covering account/keyset creation and Growth Check submission as ordered manual checklists.

## Architectural Responsibility Map

This phase produces no persistent service architecture — it is a pre-architecture feasibility spike. The table below maps its capabilities to the tier they will eventually belong to once ingestion is built in Phase 3, since the same OAuth/Browse-API code pattern proven here becomes part of that tier.

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| OAuth token acquisition (Client Credentials Grant) | API/Backend (future ingestion worker) | — | Server-side, credential-bearing call; must never run in a browser/client context. Proven here as a standalone script, formalized into the ingestion worker in Phase 3 |
| Browse API live listing search | API/Backend (future ingestion worker) | External Service (eBay Browse API) | Server-side outbound call to eBay; this phase proves the exact request/response shape ingestion will depend on |
| Marketplace Insights Growth Check submission | External Process (eBay Developer Portal, manual) | — | Not a code path at all — a business/compliance review process outside the application's architecture |
| Fixture capture (listing titles) | API/Backend script → local file (Database/Storage substitute for now) | — | Output is a flat file (JSON/CSV) checked into the phase directory for Phase 4 to consume; no database involved yet since Phase 2 (catalog/data model) hasn't happened |

## Package Legitimacy Audit

Phase 1's only code dependencies are the two supporting libraries already named in `research/STACK.md`: `requests` and `python-dotenv`. Both were checked against the project's package-legitimacy tool this session.

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| `requests` | PyPI | Long-established (latest release 2026-05-14, project since 2011) | Unknown (tool could not query download stats in this environment) | github.com/psf/requests | [SUS] (reason: `unknown-downloads` only) | Keep — see note |
| `python-dotenv` | PyPI | Long-established (latest release 2026-03-01) | Unknown (tool could not query download stats in this environment) | github.com/theskumar/python-dotenv | [SUS] (reason: `unknown-downloads` only) | Keep — see note |

**Note on the SUS verdicts:** Both packages flagged `SUS` solely because the legitimacy tool could not retrieve a download-count signal in this environment — not because of any actual red flag (no missing repo, no suspicious postinstall script, no anomalous publish pattern). Both are canonical, extremely widely-used Python packages already recommended in the project's own prior `research/STACK.md`. Per the Package Legitimacy Protocol, `SUS` verdicts must still be gated: **the planner must add a `checkpoint:human-verify` task before the install step for `requests` and `python-dotenv`**, even though this researcher assesses the actual risk as negligible.

`pip index versions` confirms current latest releases (verified this session, `[VERIFIED: pypi registry]`):
- `requests`: latest **2.34.2** (STACK.md's 2.32.3 is stale — training-data drift, use 2.34.2 or pin a recent 2.34.x)
- `python-dotenv`: latest **1.2.2** (STACK.md's 1.0.1 is stale — use 1.2.2 or pin a recent 1.x)

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** `requests`, `python-dotenv` — planner must insert `checkpoint:human-verify` before each install (low actual risk per note above, but protocol-mandated)

**Postinstall script check:** Neither package's PyPI metadata exposes an installed `postinstall`-equivalent (Python packages don't have npm-style postinstall hooks by default); no risk signal here.

## Architecture Patterns

### System Architecture Diagram

```
[User: eBay Developer Portal]
        |
        | (manual: create Dev Program account,
        |  create Sandbox + Production keysets,
        |  paste Client ID/Secret into .env,
        |  submit Growth Check application)
        v
   [.env file]  <-- never seen by Claude, read only at runtime
        |
        v
[verify_ebay_access.py script]
        |
        |--1. POST client_id:client_secret (Basic auth)---> [eBay OAuth token endpoint]
        |                                                     identity/v1/oauth2/token
        |<--------------- access_token, expires_in ----------|
        |
        |--2. GET item_summary/search?q=...&token=Bearer----> [eBay Browse API]
        |                                                      buy/browse/v1/item_summary/search
        |<--------- JSON: itemSummaries[] (price, shippingOptions, title) --|
        |
        |--3. assert price.value + shippingOptions present
        |--4. write N titles (50-100) to fixture file --------> [fixtures/ebay_listing_titles.json]
        |
        v
  [console/log output: PASS/FAIL + captured sample count]
```

A reader can trace the primary path: manual portal setup produces credentials → script exchanges credentials for a token → script calls Browse API → script validates response shape and writes fixtures. The Marketplace Insights Growth Check is a parallel, disconnected manual branch (portal-only, no code path) tracked separately in `MANUAL-STEPS.md`.

### Recommended Project Structure
```
scripts/
├── verify_ebay_access.py   # OAuth handshake + live Browse API call + fixture capture, single entrypoint
.env.example                # documents required var names (EBAY_CLIENT_ID, EBAY_CLIENT_SECRET, EBAY_ENV) — no real values
.env                        # user-created, gitignored, holds real Client ID/Secret
.gitignore                  # must include .env
fixtures/
└── ebay_listing_titles.json  # 50-100 captured titles + raw price/shipping fields, output of the script
.planning/phases/01-ebay-api-feasibility-gate/
├── MANUAL-STEPS.md          # D-04: portal checklist (account, keysets, Growth Check submission)
├── GROWTH-CHECK-NARRATIVE.md  # D-03: Claude-drafted justification text for the user to paste into the portal
└── FALLBACK-DECISION.md     # SC-3: formalized denied-case fallback (already researched at project level; this phase records it as a committed artifact)
```

### Pattern 1: OAuth Client Credentials Grant (application token, read-only public data)
**What:** Exchange your app's Client ID + Client Secret for a short-lived (~7,200s / 2hr) application access token, no user login/consent involved.
**When to use:** Any read-only call to public listing data — this project's Browse API calls, and (if approved) Marketplace Insights API calls.
**Example:**
```python
# Source: developer.ebay.com/api-docs/static/oauth-client-credentials-grant.html (via cross-corroborated web search, MEDIUM confidence)
import base64
import os
import requests

def get_app_token(env: str = "production") -> dict:
    client_id = os.environ["EBAY_CLIENT_ID"]
    client_secret = os.environ["EBAY_CLIENT_SECRET"]
    host = "api.ebay.com" if env == "production" else "api.sandbox.ebay.com"
    creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

    resp = requests.post(
        f"https://{host}/identity/v1/oauth2/token",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {creds}",
        },
        data={
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope",
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()  # {"access_token": "...", "expires_in": 7200, "token_type": "Application Access Token"}
```
**Note:** This grant type returns no `refresh_token` — there is nothing to refresh. The correct pattern (relevant for Phase 3's ingestion worker, not this phase) is to track `expires_in` and request a fresh token proactively before it lapses, per `research/PITFALLS.md` Pitfall 6.

### Pattern 2: Browse API search for sealed Pokemon product with price + shipping fields
**What:** Query the `item_summary/search` endpoint for keyword matches, requesting enough fieldgroups/data to see both item price and shipping cost per listing.
**When to use:** The live proof-of-life call for SC-1, and later the basis for Phase 3's ingestion worker.
**Example:**
```python
# Source: developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search
# and developer.ebay.com/api-docs/buy/browse/types/gct:ItemSummary (via cross-corroborated web search, MEDIUM confidence)
def search_sealed_listings(access_token: str, query: str, limit: int = 50) -> list[dict]:
    resp = requests.get(
        "https://api.ebay.com/buy/browse/v1/item_summary/search",
        headers={
            "Authorization": f"Bearer {access_token}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
        },
        params={
            "q": query,                      # e.g. "Pokemon Scarlet Violet Elite Trainer Box"
            "filter": "conditions:{NEW}",     # sealed product should always be NEW condition
            "limit": limit,
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("itemSummaries", [])

# Per-item price/shipping extraction:
def total_cost(item: dict) -> float:
    item_price = float(item["price"]["value"])
    shipping_options = item.get("shippingOptions", [])
    shipping_cost = float(shipping_options[0]["shippingCost"]["value"]) if shipping_options else 0.0
    return item_price + shipping_cost
```
**Key parameters confirmed:** `q` (keyword), `category_ids`, `filter` (supports `price:[min..max]`, `priceCurrency`, `conditions`, `maxDeliveryCost` for free-shipping-only), `sort`, `limit`, `offset`, `fieldgroups` (`EXTENDED`, `MATCHING_ITEMS`, `ASPECT_REFINEMENTS`, etc.), `aspect_filter`. At least one of `q`, `category_ids`, `epid`, `gtin` is required.

**Category ID note:** Search results surfaced three eBay category IDs associated with Collectible Card Games / graded cards (183050, 183454, 261328), but none was confirmed as the specific "Pokemon sealed product" category `[ASSUMED — needs empirical verification]`. **Recommendation for Phase 1's plan:** don't block on finding the exact category ID — start with keyword-only search (`q=Pokemon <set name> Elite Trainer Box`, etc.), which the Browse API supports standalone, and record whatever `categoryId` the returned `itemSummaries[].categories[]` field reports for later reuse as an optional narrowing filter in Phase 3.

### Anti-Patterns to Avoid
- **Hand-rolling a full OAuth SDK/client library:** The Client Credentials Grant is a single POST call with static scope and no refresh token — a full SDK (e.g. an `ebaysdk`-style wrapper built for the older XML Trading API) adds indirection for no benefit here. A ~15-line function is the right size for this need.
- **Validating against Sandbox and calling it done:** `research/PITFALLS.md` and `research/STACK.md` both flag Sandbox catalog data as sparse/unrepresentative. Sandbox is fine for confirming the OAuth handshake shape works, but SC-1's "real Pokemon sealed-product listings" and SC-4's "50-100 real ... listing titles" both require the **Production** keyset and a **Production** Browse API call, not Sandbox.
- **Committing the Growth Check narrative with the wrong applicant framing:** Per `research/PITFALLS.md` Pitfall 1 and CONTEXT.md D-05, the narrative Claude drafts must explicitly reference the user's existing business entity and a price-transparency/resale-analytics use case — not "personal project" framing, which the same research found correlates with denial in community reports.

## Growth Check Submission Process

`[CITED: developer.ebay.com/api-docs/static/gs_apply-for-the-application.html, gs_request-an-application-growth.html — via cross-corroborated web search this session]`

1. Log in to the eBay Developer Program account (must already have a Production keyset created — the Growth Check reviews upgrades to an *existing* Production application, it doesn't create a new one).
2. Navigate to `https://developer.ebay.com/my/support/tickets?tab=app-check` (the "Application Growth Check" ticket form inside the Developer Portal's support/tickets area).
3. Fill in all fields marked with a red asterisk (required); an info-icon tooltip next to each field explains what it expects. `[ASSUMED — exact field list (use-case description, estimated daily/hourly call volume, business entity info) not directly confirmed via full page fetch this session; matches STACK.md's prior-session finding of the same shape]`
4. Use "Save as Draft" to pause and resume before submitting — useful since Claude drafts the narrative text (D-03) but the user must review/paste/submit it themselves.
5. Click "Submit." No published SLA/turnaround time is stated on eBay's own docs page — plan for SC-2's "decision-by date" to be a **self-imposed tracking date** (e.g., "review status again in 14 days"), not a promise from eBay.

**Recommendation for the plan:** the phase's `GROWTH-CHECK-NARRATIVE.md` (Claude-drafted, per D-03) should include: (a) a clear price-transparency/resale-analytics framing of the product, (b) an explicit mention of the user's existing business entity as the applicant, (c) a realistic estimated call volume (e.g., a cron job polling ~10-30 catalog products every few hours — matches the ~5,000 calls/day default tier headroom already established in `research/STACK.md`), and (d) confirmation that the project only needs read-only sold-listing data (no selling/user-token scope).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OAuth application-token handshake | A custom retry/backoff/token-cache wrapper class for this phase | A single function per Pattern 1 above; defer token-caching/proactive-refresh logic to Phase 3's ingestion worker | This phase only needs one token for one script run — building refresh/cache infrastructure now is premature for a feasibility spike |
| Total-cost (price + shipping) computation | A bespoke currency-parsing/rounding routine | `float(price.value) + float(shippingOptions[0].shippingCost.value)`, defaulting shipping to `0.0` when the array is empty | eBay already returns clean decimal strings in a single currency (`priceCurrency` param controls this); no parsing complexity exists at this stage — the real complexity (multi-currency, tax-inclusive pricing) is out of scope for a US-market v1 |
| Fixture title capture / storage | A database write, ORM model, or MongoDB collection | A flat JSON (or CSV) file checked into the phase directory | Phase 2 (catalog/data model) hasn't happened yet — there is no schema to write into. A flat fixture file is exactly what Phase 4's matching-rule work needs to consume later |

**Key insight:** Phase 1 is intentionally throwaway/minimal-infrastructure — its only job is to de-risk two external unknowns and produce one small reusable fixture file. Any code written here that looks like "the real ingestion worker" is premature; that belongs to Phase 3.

## Common Pitfalls

### Pitfall 1: Assuming Sandbox proof-of-life satisfies SC-1
**What goes wrong:** The OAuth handshake and a Browse API call both succeed against Sandbox, and it's tempting to treat that as "done."
**Why it happens:** Sandbox is easier to get working first (no rate-limit anxiety, same code path) and its success feels like proof the integration works.
**How to avoid:** SC-1 explicitly requires "real Pokemon sealed-product listings" — Sandbox's catalog is sparse/synthetic test data (per `research/PITFALLS.md` and `research/STACK.md`, both MEDIUM confidence, cross-corroborated). The plan must include a Production keyset + Production API call as the actual verification step, with Sandbox used only as an earlier smoke-test stage if useful.
**Warning signs:** Listing titles returned look like generic test fixtures ("Test Item 1") rather than real product names.

### Pitfall 2: Treating "sandbox access to Marketplace Insights" as equivalent to Production approval
**What goes wrong:** Some developers report getting Sandbox scope for Marketplace Insights without ever getting Production approval, and mistakenly consider the feature "unblocked."
**Why it happens:** eBay's docs describe Sandbox and Production as separate environments but don't always make clear that Sandbox access to a restricted API doesn't imply Production approval will follow.
**How to avoid:** SC-2 tracks the **Production** Growth Check application status specifically. Record "submitted" only once the actual Growth Check ticket (not a Sandbox scope toggle) has been filed.
**Warning signs:** Confusing "Marketplace Insights sandbox calls work" with "Marketplace Insights production access is approved."

### Pitfall 3: Reading only `price.value` and skipping `shippingOptions`
**What goes wrong:** A quick test script reads `item.price.value` alone, "looks right" for a handful of listings, and the shipping-cost field never gets exercised — silently reintroducing `research/PITFALLS.md` Pitfall 2 at the very first opportunity to prevent it.
**Why it happens:** `price.value` is the most obvious top-level field in the response; `shippingOptions[].shippingCost.value` requires knowing to look one level deeper into an array.
**How to avoid:** SC-1 explicitly names "item-price and shipping-cost fields" as required proof — the verification script should assert both fields are present and non-null (even if `shippingCost.value == "0.00"` for a free-shipping listing) before declaring success, not just print the raw JSON and eyeball it.
**Warning signs:** The proof-of-life script's success output doesn't explicitly show a shipping-cost number for at least one captured listing.

### Pitfall 4: Business/use-case framing weakens the Growth Check application
**What goes wrong:** A generic or vague use-case narrative ("I'm building a hobby project to track Pokemon prices") gets submitted, correlating with denial per community reports.
**Why it happens:** It's the path of least resistance to describe the project casually, especially since the user is genuinely building this as a personal project first.
**How to avoid:** Per D-03/D-05 and `research/PITFALLS.md` Pitfall 1, the drafted narrative must foreground price-transparency/resale-analytics framing and the existing business entity as applicant — this is a locked decision, not a suggestion.
**Warning signs:** The draft narrative reads like a README rather than a business justification.

## Code Examples

### Full verification script skeleton
```python
# scripts/verify_ebay_access.py
# Sources: OAuth pattern per developer.ebay.com/api-docs/static/oauth-client-credentials-grant.html;
# Browse API pattern per developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search
# (both via cross-corroborated web search this session, MEDIUM confidence)
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from ebay_client import get_app_token, search_sealed_listings, total_cost  # functions per Patterns 1-2 above

CATALOG_QUERIES = [
    "Pokemon Scarlet Violet Elite Trainer Box",
    "Pokemon Booster Box sealed",
    # ... additional queries per the 2-3 target sets in scope for v1
]
FIXTURE_TARGET = (50, 100)  # inclusive range, per SC-4
FIXTURE_PATH = Path("fixtures/ebay_listing_titles.json")

def main() -> int:
    load_dotenv()
    token_resp = get_app_token(env="production")
    access_token = token_resp["access_token"]
    print(f"OAuth OK — token type={token_resp.get('token_type')}, expires_in={token_resp.get('expires_in')}s")

    captured = []
    for q in CATALOG_QUERIES:
        items = search_sealed_listings(access_token, q, limit=50)
        for item in items:
            if "price" not in item:
                continue  # per Pitfall 3 — require price present before recording
            captured.append({
                "title": item["title"],
                "item_price": item["price"]["value"],
                "shipping_cost": (item.get("shippingOptions") or [{}])[0].get("shippingCost", {}).get("value", "0.00"),
                "total_cost": total_cost(item),
                "categoryId": item.get("categories", [{}])[0].get("categoryId"),
            })
        if len(captured) >= FIXTURE_TARGET[1]:
            break

    if not (FIXTURE_TARGET[0] <= len(captured) <= FIXTURE_TARGET[1] * 2):
        print(f"WARNING: captured {len(captured)} listings, target was {FIXTURE_TARGET}", file=sys.stderr)

    FIXTURE_PATH.parent.mkdir(exist_ok=True)
    FIXTURE_PATH.write_text(json.dumps(captured[:FIXTURE_TARGET[1]], indent=2))
    print(f"Captured {min(len(captured), FIXTURE_TARGET[1])} listings -> {FIXTURE_PATH}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| Finding API `findCompletedItems` for sold-price data (free, no approval needed) | Marketplace Insights API (Limited Release, Application Growth Check required) | Fully decommissioned 2025-02-05 | The entire premise of this phase — sold-price access is now a manual approval gate, not a standard API call. No legacy fallback exists. |
| Create React App for SPA scaffolding | Vite | React team sunset announcement, Feb 2025 | Not directly relevant to Phase 1 (no frontend work here), but confirms `research/STACK.md`'s Vite recommendation remains current for later phases. |

**Deprecated/outdated:**
- eBay Finding API / Shopping API: fully decommissioned, will error if called — do not reference in any code or docs written for this phase.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|-----------------|
| A1 | Exact Application Growth Check form field list (use-case description, estimated call volume, business entity fields) matches the general shape described by eBay's docs pages, not directly fetched in full this session | Growth Check Submission Process | Low — `MANUAL-STEPS.md` should tell the user to read each field's tooltip live in the portal rather than hard-coding an assumed field list; worst case is a short delay while the user fills in an unexpected field |
| A2 | No eBay category ID for "Pokemon sealed product" specifically was confirmed; category IDs 183050/183454/261328 are associated with Collectible Card Games / graded cards broadly, not confirmed as sealed-product-specific | Pattern 2 (Browse API search) | Low — plan should default to keyword-only search (`q=`) which needs no category ID, and treat category_ids as an optional future narrowing filter once observed empirically from real API responses |
| A3 | Growth Check "no published SLA" and "review... for compliance" language reflects the current portal, not verified via full official-page fetch this session (WebFetch timed out repeatedly; relied on search-engine snippets of the official page) | Growth Check Submission Process | Low-Medium — if eBay has since published a specific SLA or changed field requirements, `MANUAL-STEPS.md`'s guidance to "read the live tooltips" mitigates this; SC-2's "decision-by date" is explicitly framed as self-imposed, not eBay-promised, so this doesn't block success criteria |
| A4 | `python-dotenv` 1.2.2 and `requests` 2.34.2 are safe despite `[SUS]` legitimacy-tool verdicts (verdict driven only by an `unknown-downloads` signal in this environment, not a real red flag) | Package Legitimacy Audit | Low — both are canonical, long-established packages with legitimate GitHub repos; planner adds the mandated `checkpoint:human-verify` regardless per protocol |

## Open Questions

1. **What exact business-entity documentation, if any, does the Growth Check form require to reference the user's existing entity (EIN, business name only, etc.)?**
   - What we know: The form has required (red-asterisk) fields and an info tooltip per field; D-05 confirms an entity already exists and should be referenced.
   - What's unclear: The precise field(s) capturing business identity were not directly observed this session (WebFetch to the official page timed out repeatedly).
   - Recommendation: `MANUAL-STEPS.md` should instruct the user to have their business entity name/details on hand when they open the live form, rather than the plan hard-coding an assumed field list.

2. **What is the exact eBay Browse API category ID (if any) that best narrows results to "Pokemon sealed product" vs. singles/graded cards?**
   - What we know: Keyword search (`q=`) alone works without a category ID; three CCG/graded-card-adjacent category IDs surfaced in search but none confirmed as sealed-product-specific.
   - What's unclear: Whether a dedicated sealed-product category exists at all, or whether keyword + `conditions:{NEW}` filtering is sufficient long-term.
   - Recommendation: Treat this as empirically discoverable during Phase 1 execution itself (log whatever `categoryId` real API responses report) rather than a research blocker — captured for Phase 3/4 to reuse if useful.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|--------------|-----------|---------|----------|
| Python 3.12+ | Verification script runtime | ✓ | 3.12.13 | — |
| pip | Package installation | ✓ | 26.1.2 | — |
| `requests` (PyPI) | HTTP calls to eBay OAuth + Browse API | ✓ (installable, not yet installed) | latest 2.34.2 | — |
| `python-dotenv` (PyPI) | Loading `.env` credentials | ✓ (installable, not yet installed) | latest 1.2.2 | — |
| eBay Developer Program account | All of Phase 1 | ✗ (per D-01, user has not created one yet) | — | None — this is the first manual step in `MANUAL-STEPS.md`; blocks all other Phase 1 work until created |
| Network access to `api.ebay.com` from the execution environment | Live OAuth + Browse API calls | Not verified this session (sandboxed research environment) | — | If the execution environment lacks outbound network access, the verification script must be run by the user locally, not by an agent in a network-isolated sandbox |

**Missing dependencies with no fallback:**
- eBay Developer Program account + keysets — must be created by the user (D-01) before any Phase 1 code can run against real endpoints.

**Missing dependencies with fallback:**
- None beyond the account itself; `requests`/`python-dotenv` are trivially installable once the account exists.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x (per `research/STACK.md`) — not yet installed; this is a greenfield repo (no `pyproject.toml`, no test directory found) |
| Config file | none — see Wave 0 |
| Quick run command | `python scripts/verify_ebay_access.py` (this phase's real "test" is a live smoke script, not a pytest unit suite — see rationale below) |
| Full suite command | Same as quick run — Phase 1 has no unit-testable business logic, only an external-integration smoke check |

**Rationale for smoke-script over pytest:** Phase 1's success criteria (SC-1 through SC-4) are inherently either (a) live-network/live-credential integration checks that can't run in CI without secrets, or (b) manual business-process steps (Growth Check submission) with no code to unit test. A pytest suite would either need to mock the entire eBay API (testing nothing real) or require live credentials in CI (against D-02's "credentials never leave the user's `.env`" constraint). The smoke script itself doubles as the verification artifact.

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|---------------------|--------------|
| SC-1 | OAuth token retrieved + live Browse API call returns real listings with price + shipping fields | smoke (live integration, requires `.env`) | `python scripts/verify_ebay_access.py` | ❌ Wave 0 |
| SC-2 | Growth Check application submitted, status tracked, decision-by date recorded | manual-only (business process, no code) | n/a — verified by checking `MANUAL-STEPS.md` / a tracking doc for a recorded submission date | ❌ Wave 0 (tracking doc) |
| SC-3 | Documented fallback decision exists | manual-only (doc-existence check) | `test -f .planning/phases/01-ebay-api-feasibility-gate/FALLBACK-DECISION.md` | ❌ Wave 0 |
| SC-4 | 50-100 real listing titles captured as fixtures | automated (script asserts count in range) | `python scripts/verify_ebay_access.py` (asserts `50 <= len(captured) <= 100`, or documents shortfall) | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** Re-run `python scripts/verify_ebay_access.py` after any change to the OAuth/Browse-API code path.
- **Per wave merge:** Same command — this phase has one effective wave of code work.
- **Phase gate:** All four SC items confirmed true (script run succeeds with real data; Growth Check submitted with tracked date; fallback doc committed; fixture file has 50-100 entries) before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `scripts/verify_ebay_access.py` — does not exist yet, is the core deliverable
- [ ] `.env.example` — documents required variable names without real values
- [ ] `fixtures/` directory — does not exist yet
- [ ] `requirements.txt` (or equivalent) listing `requests`, `python-dotenv` with pinned current versions
- [ ] Framework install: `pip install requests==2.34.2 python-dotenv==1.2.2` (gate behind `checkpoint:human-verify` per Package Legitimacy Audit)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|----------------|---------|---------------------|
| V2 Authentication | No | This phase performs application-level (client-credentials) auth to an external API; there is no end-user authentication surface in this phase |
| V3 Session Management | No | No sessions — a stateless application access token per script run |
| V4 Access Control | No | No access-control surface (single-user local script) |
| V5 Input Validation | No | No user-supplied input flows into this phase's code (queries are hard-coded catalog search terms) |
| V6 Cryptography / Secrets Handling | Yes | `.env`-based credential storage (D-02); never log, print, or commit raw `EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET`/`access_token` values; `.env` must be in `.gitignore` |

### Known Threat Patterns for this phase's stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|------------------------|
| Committing `.env` (or hard-coded credentials) to git | Information Disclosure | `.gitignore` must include `.env` before any code is written; only `.env.example` (no real values) is committed, consistent with D-02 |
| Logging the full OAuth `access_token` or `Authorization` header value in script output/error traces | Information Disclosure | Log only token metadata (`token_type`, `expires_in`) and truncated/masked token prefixes if logging is needed for debugging; never print the full token or the base64-encoded Basic-auth credential string |
| Accidentally submitting the Growth Check narrative or MANUAL-STEPS.md with real credential values pasted in as examples | Information Disclosure | Any example `.env` contents shown in docs/checklists must use obvious placeholder values (`EBAY_CLIENT_ID=your-client-id-here`), never real-looking strings |

## Sources

### Primary (HIGH confidence)
- None directly fetched via Context7 or direct official-page WebFetch this session (all WebFetch attempts to developer.ebay.com timed out — see Assumptions Log A3).

### Secondary (MEDIUM confidence — official eBay docs, corroborated via multiple independent web-search results referencing the same official pages, cross-checked against prior project research)
- [Create the eBay API keysets — eBay Developers Program](https://developer.ebay.com/api-docs/static/gs_create-the-ebay-api-keysets.html)
- [Understand application keysets — eBay Developers Program](https://developer.ebay.com/api-docs/static/gs_understand-application-keysets.html)
- [The client credentials grant flow — eBay Developers Program](https://developer.ebay.com/api-docs/static/oauth-client-credentials-grant.html)
- [search: eBay Browse API — eBay Developers Program](https://developer.ebay.com/api-docs/buy/browse/resources/item_summary/methods/search)
- [ItemSummary: eBay Browse API — eBay Developers Program](https://developer.ebay.com/api-docs/buy/browse/types/gct:ItemSummary)
- [ShippingOption: eBay Browse API — eBay Developers Program](https://developer.ebay.com/api-docs/buy/browse/types/gct:ShippingOption)
- [Apply for the application growth check — eBay Developers Program](https://developer.ebay.com/api-docs/static/gs_apply-for-the-application.html)
- [Request an application growth check — eBay Developers Program](https://developer.ebay.com/api-docs/static/gs_request-an-application-growth.html)
- [Submit an Application Growth Check — eBay Developers Program](https://developer.ebay.com/support/kb-article?KBid=1062)
- `.planning/research/STACK.md` and `.planning/research/PITFALLS.md` (prior project-level research, 2026-07-12, reused per CONTEXT.md canonical_refs instruction)

### Tertiary (LOW confidence — used only for cross-corroboration, not sole basis for any claim)
- [How to Get and Use eBay API Key: The Latest Guide for 2026 — LitCommerce](https://litcommerce.com/blog/how-to-get-and-use-ebay-api-key/)
- Various eBay Community forum threads on Growth Check outcomes (already incorporated into `research/PITFALLS.md` Pitfall 1 at MEDIUM confidence)

## Metadata

**Confidence breakdown:**
- OAuth Client Credentials Grant mechanics: MEDIUM — official doc pages cited via search-engine snippets, cross-corroborated across independent sources; not directly fetched in full
- Browse API request/response shape (price, shipping): MEDIUM — same basis; the price/shipping field paths are also independently corroborated by `research/PITFALLS.md` Pitfall 2, written in a prior session
- Growth Check submission process/form: MEDIUM-LOW — general shape confirmed, exact field list not directly observed (Assumption A1/A3)
- Package legitimacy (`requests`, `python-dotenv`): MEDIUM — registry-verified versions HIGH confidence; legitimacy-tool SUS verdicts driven by a tooling limitation, not a real signal (documented in audit notes)

**Research date:** 2026-07-13
**Valid until:** 2026-08-12 (30 days — eBay API mechanics are stable, but Growth Check process/approval patterns should be re-verified if Phase 1 execution is delayed significantly past this window)

---
*Phase: 1-eBay API Feasibility Gate*
*Research completed: 2026-07-13*
