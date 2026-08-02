---
phase: quick-260802-lwv
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - .planning/phases/01-ebay-api-feasibility-gate/GROWTH-CHECK-NARRATIVE.md
  - .planning/phases/01-ebay-api-feasibility-gate/MANUAL-STEPS.md
autonomous: true
requirements: []  # Phase 1 owns no REQUIREMENTS.md IDs (SC-2 only); this is a docs-only prep step for the user's own out-of-band submission action
estimate:
  tokens: 15000
  raw_tokens: 8000
  tasks: 1
  confidence: high
must_haves:
  truths:
    - "GROWTH-CHECK-NARRATIVE.md cites real accumulated production usage (94 healthy runs, 15.3 days continuous, 1504 Browse API calls, 75200 listings fetched) alongside the existing forward-looking estimated-volume paragraph, not replacing it"
    - "The existing read-only / no-selling-scope language in GROWTH-CHECK-NARRATIVE.md is unchanged"
    - "MANUAL-STEPS.md's Submission Tracking status line reflects that the delay period is over and the user is proceeding to submit now"
    - "Submitted date / Ticket ID / Outcome fields in MANUAL-STEPS.md remain unfilled placeholders — only the user can fill those in after actually submitting via the eBay portal"
  artifacts:
    - ".planning/phases/01-ebay-api-feasibility-gate/GROWTH-CHECK-NARRATIVE.md"
    - ".planning/phases/01-ebay-api-feasibility-gate/MANUAL-STEPS.md"
  key_links:
    - "GROWTH-CHECK-NARRATIVE.md is what the user pastes into eBay's Growth Check form per MANUAL-STEPS.md Step 4 — the two files must stay mutually consistent"
---

<objective>
Strengthen the Marketplace Insights Application Growth Check submission kit with real production usage data now that the deliberate delay period (PROJECT.md Key Decisions, MANUAL-STEPS.md Submission Tracking) is over. eBay's form states it cannot approve apps "in beta or with no usage" — the kit currently only has a forward-looking estimate; it needs the real, already-accrued usage history to counter that rejection reason.

This is docs-only prep. It does NOT submit anything — submission is an out-of-band human action the user performs themselves in the eBay portal (D-03, already documented in MANUAL-STEPS.md).
</objective>

<context>
@.planning/phases/01-ebay-api-feasibility-gate/GROWTH-CHECK-NARRATIVE.md
@.planning/phases/01-ebay-api-feasibility-gate/MANUAL-STEPS.md
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Add real usage stats to the narrative; update submission-tracking status line</name>
  <files>.planning/phases/01-ebay-api-feasibility-gate/GROWTH-CHECK-NARRATIVE.md, .planning/phases/01-ebay-api-feasibility-gate/MANUAL-STEPS.md</files>
  <read_first>Both files in full — they are short.</read_first>
  <behavior>
    - GROWTH-CHECK-NARRATIVE.md gains a new "Usage to date" subsection, placed immediately after the existing "Estimated call volume" paragraph within the "Use Case / Justification" section, citing real numbers pulled live from the production database on 2026-08-02: 94 successful/partial ingestion runs over 15.3 continuous days (first healthy run 2026-07-18, most recent 2026-08-02), running on a fixed 4-hour schedule with zero gaps, 1,504 Browse API search calls issued to date, 75,200 cumulative listings fetched, 4,865 unique active listings currently tracked, deployed as an always-on Fly.io production worker (not a local/dev-only app). Frame it as proof this is a live, running application with real usage history, not a beta/no-usage app.
    - The existing "Estimated call volume" paragraph is kept as-is (forward-looking volume reassurance) — the new subsection supplements it, does not replace it.
    - The "Read-only" / "no user-token / no selling scope" language elsewhere in the file is untouched.
    - The `[YOUR BUSINESS ENTITY NAME]` placeholder stays a placeholder — do not invent a name.
    - MANUAL-STEPS.md's Submission Tracking section: replace the "Status as of 2026-07-18: intentionally delayed, not yet submitted..." paragraph with one dated 2026-08-02 stating the delay period is over, 15.3 days / 94 successful runs of real usage have now accrued, and the user is proceeding to submit.
    - The Submission Tracking table's four placeholder rows (Submitted date / Ticket ID / decision-by date / Outcome) and the Summary Checklist's unchecked boxes stay exactly as unfilled placeholders — only the user fills those in after actually submitting.
  </behavior>
  <action>Edit both files per the behavior above. Keep changes surgical — do not rewrite or reflow unrelated sections, do not change heading structure, do not touch Steps 1-3 of MANUAL-STEPS.md or the "Notes for the reviewer" section of GROWTH-CHECK-NARRATIVE.md.</action>
  <verify>
    <automated>grep -q "94" .planning/phases/01-ebay-api-feasibility-gate/GROWTH-CHECK-NARRATIVE.md && grep -q "15.3" .planning/phases/01-ebay-api-feasibility-gate/GROWTH-CHECK-NARRATIVE.md && grep -q "fill in" .planning/phases/01-ebay-api-feasibility-gate/MANUAL-STEPS.md && echo OK</automated>
  </verify>
  <done>Both files updated; Submission Tracking table/checklist still unfilled placeholders; no code files touched.</done>
</task>

</tasks>

<verification>
- `git diff --stat` shows exactly two files changed, both under `.planning/phases/01-ebay-api-feasibility-gate/`.
- Submission Tracking table's four value cells are still `*(fill in: ...)*` placeholders (not filled in by Claude).
</verification>

<success_criteria>
- GROWTH-CHECK-NARRATIVE.md has concrete real usage numbers a reviewer can check against, not just estimates.
- MANUAL-STEPS.md accurately reflects that the delay decision has concluded and the user is submitting now.
- Nothing was submitted on the user's behalf; no placeholder values were fabricated.
</success_criteria>

<output>
Create `.planning/quick/260802-lwv-update-growth-check-narrative-and-manual/260802-lwv-SUMMARY.md` when done, with `status: complete` in frontmatter.
</output>
