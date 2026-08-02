# Phase 1: eBay API Feasibility Gate - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-13
**Phase:** 1-eBay API Feasibility Gate
**Areas discussed:** Manual steps vs. what Claude can automate, Business entity & applicant framing

---

## Manual Steps vs. What Claude Can Automate

| Option | Description | Selected |
|--------|-------------|----------|
| Already have it | eBay dev account already exists | |
| Need to create it | Account creation is a manual step, Claude gives checklist | ✓ |
| Not sure | User will check and report back | |

**User's choice:** Need to create it
**Notes:** Claude must provide a step-by-step checklist before OAuth code is written.

| Option | Description | Selected |
|--------|-------------|----------|
| I'll create the .env file myself | User pastes credentials into local .env directly; never in chat | ✓ |
| I'll paste them in chat | User pastes values in conversation; Claude writes .env | |

**User's choice:** I'll create the .env file myself
**Notes:** Claude never sees raw secret values.

| Option | Description | Selected |
|--------|-------------|----------|
| Claude drafts it, you submit | Claude writes MI application use-case narrative; user submits | ✓ |
| I'll write it myself | User handles the entire narrative independently | |

**User's choice:** Claude drafts it, you submit
**Notes:** Use price-transparency/resale-analytics framing per research/PITFALLS.md.

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, write a guide | Standalone MANUAL-STEPS.md checklist for portal actions | ✓ |
| No, just tell me inline | Claude tells user inline when relevant, no separate doc | |

**User's choice:** Yes, write a guide

---

## Business Entity & Applicant Framing

| Option | Description | Selected |
|--------|-------------|----------|
| Already have one | Existing business entity, no new registration needed | ✓ |
| Would need to register one | New registration required | |
| Not registering one | Applying as individual, accepting lower odds | |

**User's choice:** Already have one

| Option | Description | Selected |
|--------|-------------|----------|
| Register first, then apply | Delay submission until entity exists | ✓ (see notes) |
| Apply now as individual, revisit later | Submit immediately, accept lower odds | |
| Not applicable | Already has an entity | |

**User's choice:** Register first, then apply
**Notes:** Follow-up clarification confirmed this meant "apply under the already-existing entity from the start" — not a request to newly register one. No delay/blocking intended; resolved via a direct confirmation question.

| Option | Description | Selected |
|--------|-------------|----------|
| Submit now, don't block Phase 1 on entity | Complete once submitted under current status | ✓ |
| Block Phase 1 until entity exists | Must wait for entity before submitting | |

**User's choice:** Submit now, don't block Phase 1 on entity

**Confirmation follow-up:** "Yes, that's right" — use the existing business entity for the MI application, submit as soon as Phase 1 execution reaches that step, no additional registration or delay.

---

## Claude's Discretion

- Exact structure/format of MANUAL-STEPS.md.
- eBay Developer Portal navigation specifics — verify against current docs during research rather than relying on training knowledge.

## Deferred Ideas

None raised during this discussion.
