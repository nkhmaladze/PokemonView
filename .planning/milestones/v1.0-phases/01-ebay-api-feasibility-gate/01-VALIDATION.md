---
phase: 1
slug: ebay-api-feasibility-gate
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-13
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None — this phase has no unit-testable business logic. Verification is a live-integration smoke script, not pytest (see rationale below). |
| **Config file** | none — see Wave 0 |
| **Quick run command** | `python scripts/verify_ebay_access.py` |
| **Full suite command** | `python scripts/verify_ebay_access.py` (same command — Phase 1 has a single verification surface) |
| **Estimated runtime** | ~30-60 seconds (live OAuth handshake + live Browse API call) |

**Rationale for smoke-script over pytest:** Phase 1's success criteria (SC-1 through SC-4) are either (a) live-network/live-credential integration checks that can't run in CI without secrets, or (b) manual business-process steps (Growth Check submission) with no code to unit test. A pytest suite would either mock the entire eBay API (testing nothing real) or require live credentials in CI, violating D-02 ("credentials never leave the user's `.env`"). The smoke script doubles as the verification artifact.

---

## Sampling Rate

- **After every task commit touching the OAuth/Browse-API code path:** Run `python scripts/verify_ebay_access.py`
- **After every plan wave:** Same command — this phase has one effective wave of code work
- **Before `/gsd-verify-work`:** All four SC items confirmed true (script succeeds with real data; Growth Check submitted with tracked date; fallback doc committed; fixture file has 50-100 entries)
- **Max feedback latency:** ~60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| TBD (assigned at planning) | TBD | 1 | SC-1 (OAuth token + live Browse API call returns real listings w/ price + shipping fields) | T-1-01 | Never log/print full access_token or Basic-auth credential string; log only token_type/expires_in | smoke (live integration) | `python scripts/verify_ebay_access.py` | ❌ W0 | ⬜ pending |
| TBD (assigned at planning) | TBD | 1 | SC-2 (Growth Check application submitted, status tracked, decision-by date recorded) | — | N/A | manual-only | n/a — verified by checking MANUAL-STEPS.md / tracking doc for a recorded submission date | ❌ W0 | ⬜ pending |
| TBD (assigned at planning) | TBD | 1 | SC-3 (Documented fallback decision exists) | — | N/A | manual-only (doc-existence) | `test -f .planning/phases/01-ebay-api-feasibility-gate/FALLBACK-DECISION.md` | ❌ W0 | ⬜ pending |
| TBD (assigned at planning) | TBD | 1 | SC-4 (50-100 real listing titles captured as fixtures) | — | N/A | automated (script asserts count in range) | `python scripts/verify_ebay_access.py` (asserts `50 <= len(captured) <= 100`) | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `scripts/verify_ebay_access.py` — does not exist yet, is the core deliverable
- [ ] `.env.example` — documents required variable names (`EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET`) without real values
- [ ] `.gitignore` — must include `.env` before any code is written (D-02, security V6)
- [ ] `fixtures/` directory — does not exist yet, target for captured listing titles
- [ ] `requirements.txt` (or equivalent) listing `requests==2.34.2`, `python-dotenv==1.2.2` (pinned current versions per research)
- [ ] Framework install — `pip install requests==2.34.2 python-dotenv==1.2.2`, gated behind `checkpoint:human-verify` per the Package Legitimacy Audit in RESEARCH.md (SUS flag is a tooling artifact, not a real signal, but protocol still requires the checkpoint)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Growth Check application submitted with tracked status + decision-by date | SC-2 | Business-process step performed by the user in eBay's portal (D-03); no code executes this | Check `MANUAL-STEPS.md` / a tracking doc for a recorded submission date and self-imposed decision-by date |
| Documented fallback decision for the denied case | SC-3 | Content-quality check (does the doc actually state the active-only-v1 fallback), not just file existence | Read `FALLBACK-DECISION.md` and confirm it states: ship active-only v1, revisit sold-price in a later phase/milestone |
| `.env` never committed, no raw credential values appear in `MANUAL-STEPS.md` or the Growth Check narrative draft | Security V6 | Requires human read-through of docs/checklists, not a pattern a script can fully guarantee | Grep-review `MANUAL-STEPS.md` and any drafted narrative for credential-shaped strings before considering the phase done |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
