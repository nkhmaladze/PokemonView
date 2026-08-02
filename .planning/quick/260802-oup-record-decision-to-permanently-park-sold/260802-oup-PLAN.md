---
phase: quick-260802-oup
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - .planning/PROJECT.md
  - .planning/ROADMAP.md
  - .planning/STATE.md
autonomous: true
requirements: []  # Docs-only status update recording a real-world user decision; owns no REQUIREMENTS.md IDs
estimate:
  tokens: 22000
  raw_tokens: 22000
  tasks: 2
  confidence: low
must_haves:
  truths:
    - "PROJECT.md no longer describes sold-price integration as pending a reopened access path or a possible reapplication — it reads as parked indefinitely"
    - "PROJECT.md records that a Marketplace Insights Growth Check reapplication was already made as a registered business entity and was denied again, so no live reapplication path remains"
    - "PROJECT.md states PriceCharting is a theoretical future option only, explicitly not being pursued, with no scope conversation open"
    - "PROJECT.md's Key Decisions table gains exactly one new row recording the parking decision; every pre-existing row is left byte-identical"
    - "ROADMAP.md's Phase 8 status framing reads as parked/closed in all four places it appears (Milestones bullet, section header, phase-list bullet, Progress table), and the Contingency note states the reapplication path is closed"
    - "ROADMAP.md keeps Phase 8's Goal, Depends on, Requirements and all four Success Criteria intact as historical record"
    - "STATE.md's carried-forward Decisions list contains the parking decision, and the pre-existing 'deferred to a future milestone' bullet is annotated as superseded rather than deleted"
    - "STATE.md's Deferred Items table shows the Phase 8 row with a Parked status referencing the denied reapplication"
    - "FALLBACK-DECISION.md is byte-unchanged — it is historical record, not a target of this task"
    - "No application source code is touched (no .py, .jsx, .js, .toml, Dockerfile, requirements.txt changes)"
    - "No new roadmap phase, milestone, requirement, or scope item is introduced anywhere"
  artifacts:
    - ".planning/PROJECT.md"
    - ".planning/ROADMAP.md"
    - ".planning/STATE.md"
  key_links:
    - "PROJECT.md is the canonical statement of product scope — ROADMAP.md's Phase 8 framing and STATE.md's carried-forward decisions must both agree with it, so PROJECT.md is edited first and the other two are made to match"
    - "STATE.md's 'Carried-forward decisions still governing future work' list is what a future /gsd-new-milestone reads to decide what is still live; leaving the old 'deferred, not scheduled' bullet unqualified would re-surface sold-price as schedulable work"
    - "ROADMAP.md's Progress table Status column is the at-a-glance project status; 'Deferred' there implies 'later', which is exactly the framing this task removes"
---

<objective>
Record the user's explicit decision, made this session: **sold-price integration is parked permanently, and v1.0 (the shipped active-listing-price product) is treated as the complete product.**

Purpose: the planning docs currently frame the sold-price gap as temporarily deferred with reapplication left open as a live path — PROJECT.md literally suggests reapplying as a registered business entity as the mitigation. The user has since done exactly that and was denied a second time. Until the docs are corrected, they present a dead end as an open option, and a future `/gsd-new-milestone` would read sold-price integration as schedulable work.

Output: updated `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`. Documentation only — no application code changes.

New facts this task records (and the only new facts it may record):
1. A Marketplace Insights Application Growth Check reapplication was submitted as a registered business entity and was **denied again**.
2. Therefore no live reapplication path remains — reapplication is a dead end, not an option awaiting a decision.
3. The user's explicit call: park sold-price integration indefinitely; v1.0 is the complete product.
4. PriceCharting stays a theoretical future option only — explicitly **not** being pursued, and no scope conversation about it is being opened.

Explicitly out of scope — do not do these:
- **Do not touch** `.planning/milestones/v1.0-phases/01-ebay-api-feasibility-gate/FALLBACK-DECISION.md`. Its record of the committed Option 1 choice and the non-viability of Options 3/4 is historical and stays exactly as written. This task is a downstream status update only.
- Do not re-litigate, re-argue, or re-derive the decision. Do not add pros/cons, "could still consider", "worth revisiting if", or any hedge that reopens the question.
- Do not open a PriceCharting scope conversation, cost estimate, or evaluation task.
- Do not add, insert, renumber, or remove any roadmap phase or milestone. Do not add requirements. Do not create a new Active requirement.
- Do not edit any Key Decisions row other than the single new one, and do not change any existing row's Outcome cell.
- Do not invent an eBay-stated denial reason, denial letter text, reapplication ticket ID, or reapplication submission date — none were captured. State only that a reapplication was made as a registered business entity and was denied.
- Do not attribute any position, preference, or future intent to the user beyond the four numbered facts above.
- Do not edit STATE.md's YAML frontmatter, `## Current Position`, `## Session Continuity`, or the `**Current focus:**` line — those are refreshed by the normal quick-task completion STATE update, not by these tasks.
</objective>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Reframe PROJECT.md — sold-price parked indefinitely, reapplication path closed, one new Key Decisions row</name>
  <files>.planning/PROJECT.md</files>
  <read_first>`.planning/PROJECT.md` in full (~105 lines, one pass). The six regions this task edits are: `## What This Is` (the trailing sentence about sold-price history), `## Core Value` (the closing parenthetical), the `### Deferred (formerly Active, blocked on external access)` heading and its single bullet, the `## Context` bullet whose sub-bullet covers the Marketplace Insights API, the `## Key Decisions` table, and the italic `*Last updated: ...*` footer line. Everything else in the file is out of bounds.</read_first>
  <behavior>
    - **`## What This Is`** — the sentence beginning "Real sold-price history was the original dual-data vision" keeps its factual core (it was the original dual-data vision; MI access was denied 2026-08-02) but its forward-looking tail is replaced. The phrases "rolls into a future milestone" and "if/when that access path reopens" are removed entirely and not paraphrased back in. The replacement states that a reapplication as a registered business entity was also denied, that sold-price history is therefore parked indefinitely, and that v1.0 stands as the complete product. Keep the existing cross-reference to Context.
    - **`## Core Value`** — the closing parenthetical currently ends "that pillar is deferred to a future milestone, not dropped — see Context." Replace so it reads that the sold-price pillar is now parked indefinitely (no "future milestone", no "not dropped"). Keep the "see Context" pointer. Do not change the first sentence of Core Value — the live-asking-prices statement stays exactly as-is, since that is what the product actually delivers.
    - **`### Deferred (formerly Active, blocked on external access)`** — the heading is renamed to `### Parked (formerly Active, blocked on external access)`. The parenthetical is kept verbatim because it is accurate history. This is a status-framing correction, consistent with the rest of the task.
    - **The single bullet under that heading** — keep its opening factual clauses (sold-listing ingestion via the Marketplace Insights API; ticket 260802-000004 denied 2026-08-02; Option 1 per `FALLBACK-DECISION.md`; active-listing ingestion never depended on it and shipped independently). Replace everything from "A future milestone could revisit via reapplication" onward with: a reapplication was subsequently submitted as a registered business entity — the exact mitigation this document had suggested — and was denied as well, so no live reapplication path remains; sold-price integration is parked indefinitely and v1.0 is treated as the complete product; the paid PriceCharting API (Option 2) remains a theoretical future option only, explicitly not being pursued, with no scope conversation open. Do not restate Option 2's tradeoffs or the "official eBay APIs only" constraint discussion — a bare pointer to `FALLBACK-DECISION.md` is enough.
    - **`## Context`, the Marketplace Insights sub-bullet** — keep every existing fact (limited-access API, ticket 260802-000004, submitted 2026-08-02 with 94 runs / 15.3 days of real production usage evidence, denied the same day, Option 1 taken). Replace only the closing clause "not pursued further in this milestone" with a statement that a later reapplication as a registered business entity was denied too, closing the reapplication path, so sold-price data is parked indefinitely rather than awaiting a future milestone. Leave the sibling Browse API sub-bullet and the surrounding Context bullets untouched.
    - **`## Key Decisions`** — append exactly one new row at the **end** of the table (after the "Re-audit v1.0 against live production data..." row). Its Decision cell must begin with the literal text `Park sold-price integration permanently` so it is greppable. Rationale cell: the Growth Check was reapplied for as a registered business entity and denied again, leaving no live reapplication path; PriceCharting is not being pursued. Outcome cell: records this as the user's explicit, final call as of 2026-08-02, standing for the foreseeable future. Every pre-existing row — including the "Track both active and sold eBay prices" row and its `⚠️ Revisit` outcome — is left byte-identical; that row is historical record of what was originally decided and how it turned out.
    - **`*Last updated: ...*` footer** — rewrite to describe this change: still dated 2026-08-02, stating that sold-price integration is now parked indefinitely after a business-entity reapplication to the Marketplace Insights Growth Check was also denied, and that v1.0 is treated as the complete product. Keep the sentence about the pipeline having been re-verified against real production data before close.
    - The `### Validated`, `### Active`, `### Out of Scope`, `### v1.0 Shipped State`, `## Constraints`, and `## Evolution` sections are untouched. Do not reflow, re-heading, or reword anything outside the six regions above.
  </behavior>
  <action>Apply the changes described in the behavior block with scoped `Edit` calls against `.planning/PROJECT.md` only. Do not use `Write` on this file — a whole-file rewrite risks silent collateral drift in the long Validated and Shipped-State sections. Keep the diff confined to the six named regions.

Critical wording constraint: the superseded forward-looking phrasings are being deleted, not archived. Do not quote, echo, or preserve any of the old hedging language anywhere else in the file (not in the new text, not in the new table row, not in the footer, not in an HTML comment) — the acceptance check greps the whole file for their absence. Write the new text in the parked register directly.

Add no new headings, no new sections, no new bullets beyond the single Key Decisions row. Do not modify `FALLBACK-DECISION.md` or any file under `.planning/milestones/`.</action>
  <verify>
    <automated>F=.planning/PROJECT.md; grep -qi 'parked' "$F" && grep -qE '^\| Park sold-price integration permanently' "$F" && grep -q 'PriceCharting' "$F" && grep -qE '^### Parked \(formerly Active, blocked on external access\)$' "$F" && grep -qE '^\*Last updated: 2026-08-02.*[Pp]ark' "$F" && [ "$(grep -c '^| ' "$F")" -eq 19 ] && ! grep -q 'access path reopens' "$F" && ! grep -q 'not dropped' "$F" && ! grep -q 'could revisit via reapplication' "$F" && ! grep -q 'rolls into a future milestone' "$F" && ! grep -qE '^### Deferred \(formerly Active' "$F" && git diff --quiet -- .planning/milestones/ && echo OK</automated>
  </verify>
  <done>PROJECT.md reads as: sold-price parked indefinitely, business-entity reapplication already denied, no live reapplication path, PriceCharting theoretical-only and not being pursued. The Key Decisions table has exactly 18 data rows (17 original, byte-identical, plus one new parking row). No hedging language about reopened access paths or future-milestone revisits survives anywhere in the file. Nothing under `.planning/milestones/` is modified.</done>
</task>

<task type="auto" tdd="false">
  <name>Task 2: Propagate the parked status into ROADMAP.md and STATE.md</name>
  <files>.planning/ROADMAP.md, .planning/STATE.md</files>
  <read_first>`.planning/ROADMAP.md` in full (~69 lines) and the `## Accumulated Context > ### Decisions` block plus the `## Deferred Items` table of `.planning/STATE.md` (roughly lines 96-135). If Task 1 is already applied, skim the reframed PROJECT.md `### Parked` bullet so the wording used here is consistent with it — these three files must not disagree.</read_first>
  <behavior>
    **`.planning/ROADMAP.md` — four status-framing sites, plus the Contingency note:**
    - **`## Milestones` list** — the second bullet currently presents Phase 8 as deferred to a next milestone that is "not yet scheduled". Rewrite it to present Phase 8 as parked and not being pursued (MI API access denied, and a business-entity reapplication denied as well), with v1.0 standing as the complete product. Keep the existing pointers to `.planning/milestones/v1.0-ROADMAP.md` Phase 8 and `FALLBACK-DECISION.md`. The first bullet (`✅ v1.0 Active-Price MVP`) is untouched.
    - **The `### 📋 Next Milestone (Not Yet Scheduled)` heading** — replaced with `### ⏸️ Parked (Not Being Pursued)`.
    - **The `- [ ] **Phase 8: ...**` bullet under that heading** — reframed from DEFERRED to PARKED: MI API access denied 2026-08-02 and a reapplication as a registered business entity denied as well; sold-price history and active-vs-sold differentiators are not being pursued. Remove the "if/when pursued in a future milestone" tail.
    - **`### Phase 8: Sold-Price Integration (contingent on MI API access)` heading** in Phase Details — replaced so the parenthetical reads as parked rather than contingent, e.g. `### Phase 8: Sold-Price Integration (PARKED — MI API access denied)`.
    - **The `**Contingency**:` line** — keep the existing resolution history verbatim through "...rolls to a future milestone per `FALLBACK-DECISION.md` Option 1." Replace the closing sentence (the one about being picked up via `/gsd-new-milestone` after a Growth Check reapplication or via the paid PriceCharting fallback) with: a reapplication was subsequently submitted as a registered business entity and denied, closing that path; the phase is therefore parked indefinitely, not scheduled; PriceCharting (Option 2) remains a theoretical option only and is not being pursued. Prefix or retitle this closing sentence with a dated marker such as **Update (2026-08-02)** so the two events read in order.
    - **`**Goal**`, `**Depends on**`, `**Requirements**`, all four numbered `**Success Criteria**`, `**Plans**: TBD`, and `**UI hint**: yes` are preserved exactly** — they are the historical record of what this phase would have been.
    - **`## Progress` table, row 8** — the Milestone cell changes from an "unscheduled/next" framing to a parked framing, and the Status cell changes from `Deferred` to `Parked`. Plans-complete (`0/TBD`) and Completed (`-`) cells stay. Rows 1-7 are untouched.
    - **The `## Overview` paragraph and the `## Phases` numbering-convention block are untouched** — the Overview describes the roadmap's original design intent and is accurate as history.

    **`.planning/STATE.md` — two sites:**
    - **`## Accumulated Context > ### Decisions`, the "Carried-forward decisions still governing future work" list** — add one new bullet recording the parking decision: sold-price integration (formerly Phase 8) is parked indefinitely and v1.0 is treated as the complete product; the MI Growth Check was reapplied for as a registered business entity and denied again, so no live reapplication path remains; PriceCharting is a theoretical option only and is not being pursued. Additionally, the pre-existing bullet that begins "Sold-price integration (formerly Phase 8) deferred to a future milestone, not scheduled" is annotated as superseded by the new bullet — annotated, **not deleted**, so the history stays readable (same pattern used when the Growth Check blockers were closed). The "Official eBay APIs only" and "Simple in-process APScheduler" bullets are untouched.
    - **`## Deferred Items` table, the Phase 8 row** — the Status cell changes from `Deferred` to a parked status naming the cause, using the literal text `Parked (reapplication denied)`. The Item cell is updated from "deferred to a future milestone (MI Growth Check denied)" to describe it as parked, not being pursued, after the business-entity reapplication was denied. The Category (`Phase`) and Deferred At (`2026-08-02`) cells stay.
    - No other STATE.md region is touched — specifically not the YAML frontmatter, `## Project Reference`, `**Current focus:**`, `## Current Position`, `## Performance Metrics`, `## Pending Todos`, `## Blockers/Concerns`, `## Quick Tasks Completed`, `## Session Continuity`, or `## Operator Next Steps`.
  </behavior>
  <action>Apply the changes described in the behavior block with scoped `Edit` calls against `.planning/ROADMAP.md` and `.planning/STATE.md`. Do not use `Write` on either file — both contain long tables and history blocks that a whole-file rewrite would put at risk.

Do not add, insert, renumber, or remove any phase in ROADMAP.md, and do not touch the `<details>` block listing the completed v1.0 phases. Do not add a new milestone entry. The Phase 8 detail block keeps all of its substance — only its status framing and its Contingency closing sentence change.

Keep the three files consistent: the reason given here (a business-entity reapplication was made and denied, so no reapplication path remains) must match what Task 1 wrote into PROJECT.md. Do not introduce a different or additional rationale here.

As in Task 1, the superseded forward-looking phrasings are deleted rather than archived — do not preserve them anywhere in ROADMAP.md, since the acceptance check greps the whole file for their absence. The one exception is STATE.md's pre-existing carried-forward bullet, which is deliberately kept and annotated as superseded.

Do not modify `FALLBACK-DECISION.md` or anything else under `.planning/milestones/`.</action>
  <verify>
    <automated>R=.planning/ROADMAP.md; S=.planning/STATE.md; grep -qE '^### .*Parked \(Not Being Pursued\)$' "$R" && grep -q 'PARKED' "$R" && grep -qE '^\| 8\. Sold-Price Integration \|.*\| Parked \|' "$R" && grep -q 'A user can see an active-vs-sold spread indicator' "$R" && grep -q 'INGEST-04, PRICE-04, PRICE-05, PRICE-06' "$R" && ! grep -q 'Not Yet Scheduled' "$R" && ! grep -q 'not yet scheduled' "$R" && ! grep -qE '^\| 8\..*\| Deferred \|' "$R" && [ "$(grep -c '^| ' "$R")" -eq 9 ] && [ "$(grep -c '^- \[x\] Phase' "$R")" -eq 7 ] && grep -qi 'parked' "$S" && grep -q 'Parked (reapplication denied)' "$S" && grep -q 'superseded' "$S" && ! grep -qE '^\| Phase \| Phase 8.*\| Deferred \|' "$S" && git diff --quiet -- .planning/milestones/ && echo OK</automated>
  </verify>
  <done>ROADMAP.md presents Phase 8 as parked in all four status sites (Milestones bullet, section heading, phase bullet, Progress table) with a dated Contingency update stating the reapplication path is closed, while Phase 8's Goal, Requirements and all four Success Criteria survive verbatim and no phase was added or removed. STATE.md's carried-forward Decisions list contains the new parking bullet with the old bullet annotated as superseded, and the Deferred Items Phase 8 row reads `Parked (reapplication denied)`. Nothing under `.planning/milestones/` is modified.</done>
</task>

</tasks>

<verification>
Run after both tasks:

1. **Only the three intended files changed:**
   `git diff --name-only | sort` returns exactly `.planning/PROJECT.md`, `.planning/ROADMAP.md`, `.planning/STATE.md` — no more.
2. **No source code touched:**
   `git diff --name-only | grep -E '\.(py|js|jsx|ts|tsx|toml|txt|json)$|Dockerfile'` returns nothing.
3. **FALLBACK-DECISION.md untouched:**
   `git diff --quiet -- .planning/milestones/` exits 0.
4. **Consistency read-through:** PROJECT.md, ROADMAP.md and STATE.md all describe sold-price integration with the same status (parked indefinitely) and the same cause (business-entity reapplication denied; no live reapplication path). None of them describes it as deferred-to-a-future-milestone, awaiting scheduling, or contingent on a reapplication.
5. **No scope invention:** the diff introduces no new phase, milestone, requirement, Active item, PriceCharting evaluation task, or follow-up discussion. `grep -c '^### Phase' .planning/ROADMAP.md` is unchanged.
6. **History preserved:** Phase 8's four Success Criteria and its Requirements line are still present in ROADMAP.md; PROJECT.md's 17 original Key Decisions rows are unchanged; STATE.md's old carried-forward bullet is annotated rather than removed.
</verification>

<success_criteria>
- [ ] PROJECT.md: "What This Is", Core Value parenthetical, the renamed `### Parked` section and its bullet, and the Context MI sub-bullet all read as parked-indefinitely with the reapplication path closed
- [ ] PROJECT.md: exactly one new Key Decisions row recording the parking decision; all 17 pre-existing rows byte-identical
- [ ] PROJECT.md: footer `*Last updated: 2026-08-02 ...*` describes this change
- [ ] ROADMAP.md: Phase 8 framed as parked in the Milestones bullet, the section heading, the phase bullet, and the Progress table Status cell
- [ ] ROADMAP.md: Contingency note carries a dated update stating the business-entity reapplication was denied and the path is closed; Goal / Requirements / all four Success Criteria intact
- [ ] STATE.md: new carried-forward Decisions bullet for the parking decision; prior deferred bullet annotated as superseded, not deleted
- [ ] STATE.md: Deferred Items Phase 8 row Status reads `Parked (reapplication denied)`
- [ ] `.planning/milestones/v1.0-phases/01-ebay-api-feasibility-gate/FALLBACK-DECISION.md` is byte-unchanged
- [ ] No application code changed; no new phase, milestone, requirement, or scope item introduced
</success_criteria>

<output>
Create `.planning/quick/260802-oup-record-decision-to-permanently-park-sold/260802-oup-SUMMARY.md` when done.
</output>
