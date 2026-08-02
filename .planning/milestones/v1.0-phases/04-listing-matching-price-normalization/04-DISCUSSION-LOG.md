# Phase 4: Listing Matching & Price Normalization - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-14
**Phase:** 4-Listing Matching & Price Normalization
**Areas discussed:** Match confidence & unmatched listings, Exclusion handling (lot/bundle/damaged/counterfeit), Price aggregation into price_points, Outlier filtering sensitivity

---

## Match Confidence & Unmatched Listings

| Question | Options | Selected |
|----------|---------|----------|
| Strict vs. lenient matching on ambiguous titles | Strict/precision-first ✓ · Lenient/recall-first · Let Claude decide | Strict / precision-first |
| Handling for listings that don't confidently match anything | Store as unmatched, queryable ✓ · Skip silently · Let Claude decide | Store as unmatched, queryable |
| Handling for listings matching more than one product | Treat as ambiguous/unmatched ✓ · Auto-pick highest-confidence · Let Claude decide | Treat as ambiguous/unmatched |
| Match-rate observability | Extend ingestion_runs counts ✓ · Query active_listings directly · Let Claude decide | Extend ingestion_runs with match/unmatched/excluded counts |

**User's choice:** Precision-first throughout; unmatched/ambiguous listings are stored (not dropped) with a status field; run-level match-rate counts extend the existing Phase 3 observability pattern.
**Notes:** None beyond selections.

---

## Exclusion Handling (Lot/Bundle/Damaged/Counterfeit)

| Question | Options | Selected |
|----------|---------|----------|
| Keep excluded listings flagged, or drop entirely | Keep, flagged with reason ✓ · Drop entirely · Let Claude decide | Keep, flagged with a reason |
| Sufficiency of PITFALLS.md's baseline exclusion categories | Sufficient ✓ · Add more categories · Let Claude decide | Sufficient (lot/multi-quantity, condition-negative, counterfeit) |
| Need for manual override/relabel capability | Direct MongoDB edit is fine ✓ · Small CLI script (recommended) · Something more | Wanted an override capability (first pass); clarified as direct MongoDB edit only, no tooling |
| Condition-language exclusion strictness | Explicit/severe signals only ✓ · Any condition-negative language · Let Claude decide | Explicit/severe signals only |

**User's choice:** Excluded listings flagged with `exclusion_reason`, never deleted; three baseline PITFALLS.md categories are enough; false positives get fixed via direct MongoDB document edit (no script/UI built); only hard condition signals (dented/resealed/opened/empty) trigger exclusion, not cosmetic wear language.
**Notes:** On the manual-override question, the user's first answer ("Want a manual override capability") deviated from the recommended "re-run after rule fixes" option. A follow-up question clarified the *form* that override should take, scoped against PROJECT.md's public-facing-only frontend — the user settled on direct MongoDB editing rather than building a script or UI, so no new tooling ended up in scope despite the initial answer suggesting otherwise.

---

## Price Aggregation into price_points

| Question | Options | Selected |
|----------|---------|----------|
| Per-listing points vs. per-run aggregate | Aggregated per run per product ✓ · One point per listing · Let Claude decide | One aggregated point per product per run |
| What the aggregate represents | Median ✓ · Minimum (cheapest) · Mean (average) | Median (typical market price) |
| Behavior when a product has zero included listings in a run | Skip — leave a gap ✓ · Carry forward last known price · Let Claude decide | Skip — leave a gap |
| item_price/total_price derivation | Independent medians per field ✓ · Derive total from item median + shipping · Let Claude decide | Independent medians per field |

**User's choice:** One median-based aggregate point per product per run; gaps are left honest rather than papered over; item and total price are independently derived medians.
**Notes:** None beyond selections.

---

## Outlier Filtering Sensitivity

| Question | Options | Selected |
|----------|---------|----------|
| Std-dev cutoff aggressiveness | 2 std devs — tighter ✓ · 3 std devs — looser · Let Claude decide | 2 std devs (tighter) |
| Behavior with too few listings for a meaningful cutoff | Skip filtering, include all ✓ · Exclude everything until enough data · Let Claude decide | Skip outlier filtering, include all of them |
| Scope of the rolling median (this run only vs. across runs) | Just this run's own listings ✓ · Rolling window across recent runs · Let Claude decide | Just this run's own listings |
| Flagging outlier-excluded listings | Same flagged pattern as keyword exclusions ✓ · Exclude silently · Let Claude decide | Yes, same `exclusion_reason` pattern |

**User's choice:** Tight (2 std-dev) precision-first cutoff; sparse-data runs skip outlier filtering rather than discarding real data; median/std-dev computed per-run only (no cross-run rolling window); outlier exclusions use the same flagging schema as keyword exclusions.
**Notes:** None beyond selections.

---

## Claude's Discretion

- Exact matching implementation details (keyword rule structure, RapidFuzz thresholds if used) within the strict/precision-first constraint (D-01).
- Exact field names/schema for `match_status`, `exclusion_reason`, and new `ingestion_runs` count fields.
- Pipeline ordering of exclusion checks relative to matching.
- Specific keyword lists for each confirmed exclusion category, beyond PITFALLS.md's given examples.

## Deferred Ideas

None. A manual-override *tool* was raised during the Exclusion Handling discussion but resolved in-area to "direct MongoDB edit, no tooling" (see CONTEXT.md D-07) rather than being pushed to a future phase.
