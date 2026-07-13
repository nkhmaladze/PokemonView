---
phase: 01-ebay-api-feasibility-gate
plan: 02
subsystem: infra
tags: [ebay-api, marketplace-insights, growth-check, documentation, access-gate]

# Dependency graph
requires:
  - phase: 01-ebay-api-feasibility-gate (plan 01)
    provides: ".gitignore secret-hygiene boundary (.env excluded) that MANUAL-STEPS.md relies on"
provides:
  - "MANUAL-STEPS.md — standalone eBay Developer Portal checklist (account, keysets, .env, Growth Check submission) with submission-tracking table"
  - "GROWTH-CHECK-NARRATIVE.md — ready-to-paste price-transparency/resale-analytics justification narrative for the Growth Check"
  - "FALLBACK-DECISION.md — committed active-only-v1 fallback decision for the MI-denied/delayed case"
affects: [phase-08-sold-price-integration, phase-01-plan-03, phase-01-plan-04]

# Tech tracking
tech-stack:
  added: []
  patterns: ["Manual-step documentation pattern: standalone checklist + Claude-drafted narrative + committed fallback decision for approval-gated external APIs"]

key-files:
  created:
    - .planning/phases/01-ebay-api-feasibility-gate/MANUAL-STEPS.md
    - .planning/phases/01-ebay-api-feasibility-gate/GROWTH-CHECK-NARRATIVE.md
    - .planning/phases/01-ebay-api-feasibility-gate/FALLBACK-DECISION.md
  modified: []

key-decisions:
  - "Growth Check narrative frames the applicant as an existing business entity doing price-transparency/resale-analytics, not a personal/hobby project, per PITFALLS.md Pitfall 1"
  - "Committed denied-case fallback: ship active-listing-only v1 (Phases 1-7), defer sold-price to contingent Phase 8"
  - "PriceCharting flagged as a licensed fallback that requires an explicit user scope conversation if ever pursued, never a silent substitution"

patterns-established:
  - "Manual portal actions get a standalone MANUAL-STEPS.md, independent of execution flow, so the user can work through them without a live Claude session"

requirements-completed: [SC-2, SC-3]

coverage:
  - id: D1
    description: "Standalone MANUAL-STEPS.md checklist covers account signup, keyset creation, .env population, and Growth Check submission, with a submission-tracking table recording submitted date and self-imposed decision-by date"
    requirement: "SC-2"
    verification:
      - kind: manual_procedural
        ref: "grep -qi 'Growth Check|developer.ebay.com/my/support/tickets|decision-by|keyset' MANUAL-STEPS.md"
        status: pass
    human_judgment: false
  - id: D2
    description: "GROWTH-CHECK-NARRATIVE.md drafts a ready-to-paste justification using price-transparency/resale-analytics framing, existing-business-entity applicant placeholder, realistic call volume, and read-only scope"
    requirement: "SC-2"
    verification:
      - kind: manual_procedural
        ref: "grep -qi 'price-transparency|resale' AND 'business entity' AND 'read-only' GROWTH-CHECK-NARRATIVE.md"
        status: pass
    human_judgment: false
  - id: D3
    description: "FALLBACK-DECISION.md formalizes the committed active-only-v1 fallback for the MI-denied/delayed case, with sold-price deferred to Phase 8 and a source-agnostic matching-design implication noted"
    requirement: "SC-3"
    verification:
      - kind: manual_procedural
        ref: "grep -qi 'active-only|active-listing' AND 'sold-price' AND 'PriceCharting' FALLBACK-DECISION.md"
        status: pass
    human_judgment: false

# Metrics
duration: 2min
completed: 2026-07-13
status: complete
---

# Phase 1 Plan 2: Marketplace Insights Access Gate Summary

**Standalone MANUAL-STEPS.md checklist, Claude-drafted price-transparency Growth Check narrative, and a committed active-only-v1 fallback decision for the sold-price API access gate**

## Performance

- **Duration:** 2 min
- **Started:** 2026-07-13T04:38:25Z
- **Completed:** 2026-07-13T04:40:23Z
- **Tasks:** 3 completed
- **Files modified:** 3 created

## Accomplishments
- Wrote a self-contained `MANUAL-STEPS.md` the user can work through independently of any Claude session, covering eBay Developer Program account creation, Sandbox+Production keyset creation, `.env` population (with explicit "never paste credentials into chat, never commit `.env`" guardrails), and Marketplace Insights Growth Check submission — plus a Submission Tracking table for the submitted date, ticket ID, and a self-imposed ~14-day decision-by date (no eBay SLA exists).
- Drafted `GROWTH-CHECK-NARRATIVE.md`, a ready-to-paste justification that frames the project as a price-transparency/resale-analytics tool under the user's existing business entity — explicitly avoiding "personal project" framing, which research found correlates with denial — states a realistic call volume within eBay's default rate tier, and confirms read-only sold-listing scope only.
- Recorded `FALLBACK-DECISION.md`, formalizing the already-researched denied-case decision: ship v1 as active-listing-only (Phases 1-7), defer real sold-price data to contingent Phase 8, rank PriceCharting as a licensed fallback requiring an explicit user scope conversation (never silent substitution), and note the source-agnostic matching-service design implication carried into Phase 4.

## Task Commits

Each task was committed atomically:

1. **Task 1: Write MANUAL-STEPS.md (portal checklist + submission tracking)** - `d82c379` (docs)
2. **Task 2: Draft GROWTH-CHECK-NARRATIVE.md (justification the user submits)** - `00e44c2` (docs)
3. **Task 3: Record FALLBACK-DECISION.md (denied-case decision)** - `f297ad0` (docs)

**Plan metadata:** (pending — see final commit below)

## Files Created/Modified
- `.planning/phases/01-ebay-api-feasibility-gate/MANUAL-STEPS.md` - Ordered portal checklist (account, keysets, `.env`, Growth Check submission) with a Submission Tracking table
- `.planning/phases/01-ebay-api-feasibility-gate/GROWTH-CHECK-NARRATIVE.md` - Claude-drafted, user-submitted justification narrative for the Growth Check
- `.planning/phases/01-ebay-api-feasibility-gate/FALLBACK-DECISION.md` - Committed active-only-v1 fallback record for the MI-denied/delayed case

## Decisions Made
- Applicant framing in the Growth Check narrative is explicitly business/commercial (price-transparency + resale-analytics for the sealed Pokémon TCG secondary market), referencing the user's existing registered business entity via a fillable placeholder — never a "personal project" framing, per `research/PITFALLS.md` Pitfall 1.
- The active-only-v1 fallback (Option 1 in `FALLBACK-DECISION.md`) is the default, no-further-approval-needed path; PriceCharting (Option 2) is recorded only as a ranked alternative that requires a future explicit scope conversation with the user before any adoption, since it would change the project's "official eBay APIs only" constraint.
- Self-imposed decision-by date guidance is ~14 days after Growth Check submission, since eBay publishes no SLA (D-06) — submission itself, not approval, satisfies SC-2.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

**This entire plan's output is a manual-action guide for the user.** No code was written in this plan; the deliverables ARE the setup instructions. See `MANUAL-STEPS.md` in this phase directory for the full checklist:
- Create an eBay Developer Program account and Production keyset
- Populate `.env` (created from `.env.example` in Plan 01-01) with real credentials — never pasted into chat, never committed
- Submit the Marketplace Insights Application Growth Check using the text in `GROWTH-CHECK-NARRATIVE.md`, then fill in the Submission Tracking table in `MANUAL-STEPS.md`

## Next Phase Readiness

- Plan 01-03 (eBay OAuth + Browse API verification script) can proceed independently of this plan's manual portal actions — it only requires the `.env` scaffolding from Plan 01-01, not a completed Growth Check submission.
- Plan 01-04 (install dependencies & run live verification) requires the user to have completed Steps 1-3 of `MANUAL-STEPS.md` (account, Production keyset, `.env` populated) before its live run can succeed — this is a pre-existing dependency captured in `MANUAL-STEPS.md`, not a new blocker introduced by this plan.
- SC-2 and SC-3 are satisfied as committed artifacts as of this plan; SC-2's actual "submitted" state depends on the user completing the out-of-band portal action described in `MANUAL-STEPS.md` Step 4 — this plan produces the kit, not the submission itself.
- No blockers for continuing to Wave 2 (01-03-PLAN.md).

---
*Phase: 01-ebay-api-feasibility-gate*
*Completed: 2026-07-13*
