# Phase 1: eBay API Feasibility Gate - Context

**Gathered:** 2026-07-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 resolves the two hard external unknowns before any other layer is built: (1) proving the Browse API + OAuth actually work end-to-end against real Pokemon sealed-product listings, and (2) submitting the Marketplace Insights (sold-price) API access request as a go/no-go gate with a tracked decision-by date. It also produces a documented fallback decision for the denied case, and captures 50-100 real listing titles as fixtures for later matching-rule work (Phase 4).

Phase 1 owns no product requirements directly — it's a feasibility/access gate that de-risks all later phases. No UI, no ingestion pipeline, no catalog yet.

</domain>

<decisions>
## Implementation Decisions

### Manual Steps vs. What Claude Automates
- **D-01:** The user does not yet have an eBay Developer Program account (Sandbox + Production keysets). Creating it is a manual, user-performed step. Claude must produce a step-by-step checklist for this before any OAuth code is written.
- **D-02:** Credential handoff: the user creates the `.env` file themselves and pastes the OAuth Client ID/Secret into it directly — credentials are never pasted into chat. Claude writes ingestion/test code that reads from `.env` without ever seeing the raw secret values.
- **D-03:** For the Marketplace Insights Application Growth Check, Claude drafts the use-case/justification narrative (price-transparency/resale-analytics framing, per `research/PITFALLS.md`), and the user pastes it into eBay's portal and submits it themselves. Claude does not submit on the user's behalf.
- **D-04:** Claude writes a standalone `MANUAL-STEPS.md` guide (in the phase directory) listing every manual portal action required in this phase — eBay developer account signup, and the Growth Check submission itself — so the user can work through them independently of the planning/execution flow.

### Business Entity & Applicant Framing
- **D-05:** The user already has a registered business entity. The Marketplace Insights application should be submitted under that existing entity — no new business registration is needed and none should be planned as a Phase 1 task.
- **D-06:** Submission is not blocked or delayed waiting on anything — Phase 1's "application submitted" success criterion is satisfied as soon as the application is submitted under the existing entity, at whatever point Phase 1 execution reaches that step.

### Claude's Discretion
- Exact structure/format of `MANUAL-STEPS.md` (checklist, numbered steps, etc.) is left to Claude.
- Specific eBay Developer Portal navigation details (button names, page flow) — Claude should verify against current eBay docs during planning/research rather than relying on possibly-stale training knowledge.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### eBay API access risk & pitfalls
- `.planning/research/PITFALLS.md` — Pitfall 1 (Marketplace Insights API access is not guaranteed; business/use-case framing affects approval odds; documented fallback strategy); also covers the price/shipping split field trap and OAuth grant-type confirmation, both directly relevant to Phase 1's OAuth proof call.
- `.planning/research/STACK.md` — eBay Browse API vs. Marketplace Insights API access-tier details, OAuth Client Credentials Grant specifics, rate limits, and the Application Growth Check process.

### Project-level decisions
- `.planning/PROJECT.md` — Core value, constraints (official eBay APIs only, no scraping), and the eBay access context note.
- `.planning/REQUIREMENTS.md` — INGEST-04/PRICE-04/05/06 are Phase 8-contingent on this phase's MI API outcome.
- `.planning/ROADMAP.md` §Phase 1 — Success criteria this phase must satisfy (OAuth proof, MI application submitted + decision-by date, documented fallback, 50-100 fixture titles).

</canonical_refs>

<code_context>
## Existing Code Insights

No code exists yet — this is the first phase of the project (planning documents only). No reusable assets, established patterns, or integration points to inventory.

</code_context>

<specifics>
## Specific Ideas

- The MI application justification narrative should explicitly frame the project as price-transparency/resale-analytics tooling (not "personal project"), per the approval-odds finding in `research/PITFALLS.md` Pitfall 1 — and should reference the user's existing business entity as the applicant.
- Credential handling: strict rule — Claude never sees or requests raw OAuth secret values in chat. The user manages `.env` directly.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 1-eBay API Feasibility Gate*
*Context gathered: 2026-07-13*
