# Phase 4: Listing Matching & Price Normalization - Context

**Gathered:** 2026-07-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 turns Phase 3's raw, messy `active_listings` (eBay titles + `product_ref` provenance hints) into trustworthy per-product price data in `price_points`. It covers three jobs, run in-process as part of (or immediately after) each ingestion cycle:

1. **Matching** — resolve each raw listing's title to a canonical catalog `product_id` via keyword rules (MATCH-01), with match results inspectable (ROADMAP SC-1).
2. **Exclusion** — flag and exclude listings signalling lot/multi-quantity, damaged/condition-negative, or counterfeit product (MATCH-02).
3. **Outlier filtering** — statistically exclude listings far from the rolling median so the aggregate reflects real market value, not noise (MATCH-03).

The phase's output is a per-product-per-run aggregate price written to `price_points`, computed only from listings that are matched, non-excluded, and non-outlier (ROADMAP SC-4).

No API layer, no frontend, no sold-listing/Marketplace Insights data (that's Phase 8, contingent). Matching runs as an in-process module inside the ingestion pipeline, not a separate network service (per `ARCHITECTURE.md` — this is a research/architecture call, not something renegotiated here).

</domain>

<decisions>
## Implementation Decisions

### Match Confidence & Unmatched Listings
- **D-01:** Matching is strict / precision-first. When a title is ambiguous or only weakly matches, the matcher should skip rather than guess — missing a real listing is a smaller cost than mismatching one into the wrong product's price history (core value is accuracy).
- **D-02:** A listing that doesn't confidently match any catalog product is stored (not silently skipped) with a `match_status` (e.g. `"unmatched"`) so it's queryable and rules can be tuned later without re-pulling from eBay. Satisfies ROADMAP SC-1's "match results inspectable."
- **D-03:** A listing that plausibly matches more than one catalog product is treated as ambiguous/unmatched — never auto-resolved by picking the higher-confidence candidate.
- **D-04:** Extend the existing `ingestion_runs` per-run observability pattern (established Phase 3) with match-rate counts (matched / unmatched / excluded) per run, rather than requiring ad-hoc queries against `active_listings` to see match health.

### Exclusion Handling (Lot/Bundle/Damaged/Counterfeit)
- **D-05:** Excluded listings are kept in storage, flagged with an `exclusion_reason` (e.g. `"lot"`, `"damaged"`, `"counterfeit"`, `"outlier"`) — never hard-deleted. Enables auditing false positives/negatives and tuning rules later. Matches PITFALLS.md's explicit warning against silently dropping these.
- **D-06:** The three baseline exclusion categories from `PITFALLS.md` Pitfall 3 are sufficient for v1: multi-quantity/lot language, condition-negative language, counterfeit/replica signals. No additional categories requested.
- **D-07:** No manual-override tooling is built in this phase. If an exclusion or match turns out to be a false positive, the fix is a direct MongoDB document edit (the `match_status`/`exclusion_reason` fields make this a one-field update) — no CLI script, no admin UI. This is consistent with PROJECT.md scoping the frontend as public-facing only, no admin surface.
- **D-08:** Condition-based exclusion triggers only on explicit/severe signals ("dented", "resealed", "opened", "empty box", "no cards") — not on minor/cosmetic language ("shelf wear", "corner ding"). Avoids over-excluding genuinely sealed product that happens to mention minor wear.

### Price Aggregation into price_points
- **D-09:** Phase 4 writes **one aggregated `price_points` document per product per ingestion run** (not one point per individual listing). Matches the poe.ninja-style single clean trend line and keeps Phase 5/6's price/trend logic simple (read latest/recent points, no client-side aggregation).
- **D-10:** The aggregate represents the **median** of included listings — the typical/market price, not the minimum (cheapest available) or mean. Robust to any outliers that slip past filtering.
- **D-11:** If a product has zero included listings in a run (nothing matched, or everything got excluded/filtered), that run **skips writing a point for it** — leaves a gap rather than carrying forward the last known price. Keeps the freshness indicator (PRICE-02, Phase 6) honest about when a product's price was actually last observed.
- **D-12:** `item_price` and `total_price` in the aggregated point are each computed as their **own independent median** across included listings — not `total_price` derived from `item_price`'s median plus a separate shipping calculation. Keeps each field internally consistent with how every listing already pairs them (Phase 3's `total_cost()` convention).

### Outlier Filtering Sensitivity
- **D-13:** Outlier cutoff is **2 standard deviations** from the rolling median (tighter end of PITFALLS.md's suggested 2-3 std dev range) — precision-first, consistent with D-01.
- **D-14:** When a product has too few included listings in a run to compute a meaningful median/std-dev (e.g. only 1-2), **skip outlier filtering entirely and include what's there** rather than discarding sparse-but-real data or withholding a price point.
- **D-15:** The median/std-dev used for outlier detection is computed from **just the current run's own included listings** — not a rolling window across recent runs/days. Reacts immediately to genuine market shifts (e.g. right after a set sells out) instead of lagging behind a slow-adapting historical window.
- **D-16:** Listings excluded by the statistical outlier filter get the same `exclusion_reason` flagging pattern as keyword-excluded listings (e.g. `exclusion_reason="outlier"`) — consistent audit/visibility treatment across all exclusion types.

### Claude's Discretion
- Exact matching implementation (keyword rule structure, RapidFuzz usage/thresholds if any) — `ARCHITECTURE.md`'s two-tier design (deterministic keyword rules first, fuzzy fallback second) is the starting point; precise scoring/thresholds are a planning/research detail as long as the strict/precision-first stance (D-01) holds.
- Exact field names/schema for `match_status`, `exclusion_reason`, and the new `ingestion_runs` count fields — follow the existing schema conventions in `db/init_collections.py` and `scripts/ingest_worker.py`.
- Where in the pipeline exclusion checks run relative to matching (before/after) — implementation detail, not a user-facing behavior change given D-01/D-05 hold regardless of order.
- Specific keyword lists for each exclusion category beyond the three confirmed categories (D-06) — reasonable diligence per `PITFALLS.md`'s examples, not an exhaustive audit.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture & matching design
- `.planning/research/ARCHITECTURE.md` — Proposes matching as an in-process module inside the ingestion worker (not a separate service); two-tier matching pattern (keyword rules first, RapidFuzz fuzzy fallback second, `.../matching/match.py`); the `raw_listings`/`price_points` data-flow description this phase implements (note: the actual collection is named `active_listings`, not `raw_listings` — see Phase 3 code).
- `.planning/research/PITFALLS.md` — Pitfall 3 (lot/bundle/damaged/counterfeit exclusion design, two-stage inclusion+exclusion, outlier filtering as second line of defense) is this phase's central risk. Also see "Looks Done But Isn't" checklist item on matching/exclusion rules, and the Performance Traps note on decoupling matching from the ingestion loop at scale.

### Project-level decisions
- `.planning/PROJECT.md` — Core value (accuracy of current price + trend), Flask/MongoDB/React constraints, four-service framing (matching is a module, not a deployed service).
- `.planning/REQUIREMENTS.md` — MATCH-01, MATCH-02, MATCH-03 (this phase's owned requirements).
- `.planning/ROADMAP.md` §Phase 4 — Success criteria this phase must satisfy (inspectable match results, exclusion of lot/bundle/damaged/counterfeit, statistical outlier exclusion, current price derived only from included listings).

### Prior phase decisions this phase must respect
- `.planning/phases/02-product-catalog-data-model/02-RESEARCH.md` Pitfall 4 — `required_keywords` per catalog product already carries disambiguating terms per product type (e.g. booster_bundle keywords include "bundle"; booster_box keywords include "box"/"display") specifically so this phase's matching never confuses bundle/box/pack for the same set. Matching logic should use these as designed, not redesign the keyword scheme.
- `.planning/phases/03-active-listing-ingestion-pipeline/03-RESEARCH.md` — Documents that `active_listings.product_ref` is provenance only (which catalog search query found the listing), not a matched `product_id` — this phase must independently evaluate each listing's title against `required_keywords` rather than trusting `product_ref` as authoritative.
- `db/init_collections.py` — `price_points` time-series schema (`timeField=ts`, `metaField=product_id`, `granularity=hours`), created empty in Phase 2 specifically reserved for this phase's writes. `active_listings` schema (keyed by `_id=itemId`, indexed on `product_ref`) is this phase's read source.
- `scripts/catalog_data.py` — `CATALOG` list with `required_keywords` per product; the matching input.
- `scripts/ingest_worker.py` — `total_cost()` convention (item_price + shipping_cost = total_price) and the `ingestion_runs` per-run observability pattern (D-04 extends this).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/catalog_data.CATALOG` — every catalog product's `required_keywords`, already disambiguated per product type (Phase 2 D-06/Pitfall 4). Primary matching input; no catalog rework needed.
- `db.active_listings` — Phase 3's raw listing store (`_id=itemId`, `title`, `item_price`, `shipping_cost`, `total_price`, `product_ref`, `fetched_at`, `run_id`). This phase's read source; new fields (`match_status`, `matched_product_id`, `exclusion_reason`) will be added to these documents.
- `db.price_points` — empty time-series collection, schema `{ts, product_id, item_price, total_price}`, created in Phase 2 and reserved for this phase. This phase's write target (D-09 through D-12 define exactly what gets written).
- `db.ingestion_runs` — Phase 3's per-run metadata document; D-04 extends its shape with match/exclude counts.

### Established Patterns
- **No top-level side effects on import** — established in `scripts/ebay_client.py`, continued in `scripts/catalog_data.py` and `scripts/ingest_worker.py`. Any new matching module should follow this.
- **Credential/data hygiene** — Phase 3 never logs raw tokens/URIs, only counts and metadata; matching output should follow the same discipline (no need to log full titles at info level in production, if that becomes a concern).
- **Idempotent upsert-by-ID** — `scripts/ingest_worker.py`'s `upsert_listings()` pattern (per-item try/except so one bad item doesn't abort the batch) is the model for how matching should update `active_listings` documents in place.
- **Nyquist RED/GREEN test scaffold** — Phase 3 (`03-03-PLAN.md`) established a pattern of writing failing tests first against a dedicated test-db fixture before implementation. Likely applicable to matching/exclusion/outlier logic given how price-accuracy-critical this phase is.

### Integration Points
- Reads: `db.active_listings` (raw listings to match), `db.products`/`scripts.catalog_data.CATALOG` (match targets).
- Writes: `db.active_listings` (adds `match_status`, `matched_product_id`, `exclusion_reason` fields to existing documents — update in place, not a new collection), `db.price_points` (new aggregated points), `db.ingestion_runs` (extended count fields).
- Downstream: Phase 5's API reads `price_points` for current price / trend data, and will need `price_points`' "gap on zero-listings" behavior (D-11) reflected in its freshness/staleness logic.

</code_context>

<specifics>
## Specific Ideas

- Consistent "flag, don't drop" philosophy runs through every exclusion decision (unmatched, lot/bundle/damaged/counterfeit, outliers) — same `match_status`/`exclusion_reason` schema pattern reused everywhere, and the same "fix via direct MongoDB edit, no tooling" resolution path for all of them (D-02, D-05, D-07, D-16).
- Precision-first bias is a through-line, not a one-off choice: strict matching (D-01), tight 2-std-dev outlier cutoff (D-13), and refusing to auto-resolve ambiguous matches (D-03) all optimize for "never silently mismatch" over "catch every possible listing."

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. (A manual-override *tool* was briefly considered in the Exclusion Handling discussion but resolved to "direct MongoDB edit, no tooling" — see D-07 — so nothing was actually deferred to a future phase.)

</deferred>

---

*Phase: 4-Listing Matching & Price Normalization*
*Context gathered: 2026-07-14*
