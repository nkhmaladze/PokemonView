# Phase 2: Product Catalog & Data Model - Context

**Gathered:** 2026-07-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 builds the curated, MongoDB-backed catalog of sealed English Pokemon TCG product that ingestion, matching, and pricing all key off of. It covers: selecting which sets/products are in scope, curating the canonical product list + metadata (including MSRP and image references), and persisting it on a schema that reserves fields for both item-only and total (item + shipping) price points and time-series history (per ROADMAP.md Phase 2 success criteria).

No eBay live calls, no matching logic, no ingestion pipeline, no UI — this phase is catalog data only. Phase 1 (eBay API Feasibility Gate) does not block this phase's work since catalog curation needs no live eBay data.

</domain>

<decisions>
## Implementation Decisions

### Set Selection
- **D-01:** The v1 catalog covers 4 sets, not the original "2-3 most recent" framing — the user explicitly chose to include the newest set even though it's pre-release: **Chaos Rising** (May 22, 2026), **Perfect Order** (Mar 27, 2026), **Ascended Heroes** (Jan 30, 2026), and **Pitch Black** (releases Jul 17, 2026). This should be reflected as an updated scope note in PROJECT.md/REQUIREMENTS.md at the next phase transition.
- **D-02:** Pitch Black (not yet released as of context-gathering date) should be seeded into the catalog NOW using best-available pre-release product-lineup info, then verified/corrected once it actually releases on Jul 17, 2026.

### Catalog Data Source
- **D-03:** Claude curates the product list and metadata directly via web research (official Pokemon Center site, TCGplayer, and set-tracking sites) — no manual data entry required from the user, and no third-party TCG data API dependency.
- **D-04:** The catalog schema includes an MSRP (manufacturer retail price) field per product, as a reference point for "asking price vs. retail" context — even though v1's core "fair price" judgment is against eBay price history, not MSRP.

### Product Variant Scope
- **D-05:** Only standard, broadly-retailed product counts as a catalog entry in v1 — no Pokemon Center exclusives, Build & Battle boxes, or promo-only variants. Keeps the catalog and matching rules focused on mainline retail listings.
- **D-06:** `product_type` includes a 3rd distinct value beyond the original "booster pack | booster box | ETB": **booster bundle** (sleeved multi-pack, ~6 packs). Booster bundles have meaningfully different price points from both single packs and full boxes and must not be conflated with either in the catalog or downstream matching/pricing.

### Product Images
- **D-07:** The catalog includes an `image_url` field per product, populated now (not deferred to a later phase) — a poe.ninja-style product page needs an image to read as complete.
- **D-08:** Images are referenced via direct links to official/public CDN URLs (Pokemon Center, TCGplayer) — no downloading, self-hosting, or file-storage infrastructure for v1. Accepts the tradeoff that catalog image links depend on those URLs staying stable.

### Claude's Discretion
- Exact MongoDB schema field names/types beyond what's specified above (e.g., how `required_keywords` are structured) — Claude should follow the `products` collection shape already proposed in `.planning/research/ARCHITECTURE.md` unless a specific gray area above overrides it.
- How thoroughly to web-research each product's exact release date/MSRP/image URL — reasonable diligence, not exhaustive sourcing audits.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture & schema
- `.planning/research/ARCHITECTURE.md` — Proposes the `products` (catalog) collection shape (`_id, set_name, product_type, language, release_date, required_keywords, display_name, image_url`), MongoDB time-series collection recommendation for `price_points`, and the "catalog seeding flow" data-flow description this phase implements.
- `.planning/research/PITFALLS.md` — Matching-relevant pitfalls (lot/bundle/damaged/counterfeit listing traps) that inform why product-type granularity (e.g., booster bundle as distinct from single pack) matters for downstream matching accuracy.
- `.planning/research/FEATURES.md` — Confirms English-only v1 scope (non-English explicitly out of scope, consistent with this phase's catalog boundary).

### Project-level decisions
- `.planning/PROJECT.md` — Core value, MongoDB/Flask/React stack constraints, "2-3 most recent sets" framing (superseded for v1 by D-01 above — 4 sets).
- `.planning/REQUIREMENTS.md` — CATALOG-01, CATALOG-02 (this phase's owned requirements); INGEST-03 downstream dependency on the item-price/shipping-price schema split.
- `.planning/ROADMAP.md` §Phase 2 — Success criteria this phase must satisfy (every sealed product as a distinct catalog entry, canonical metadata usable by matching, MongoDB-persisted schema reserving item/total price + time-series fields).

</canonical_refs>

<code_context>
## Existing Code Insights

No catalog/data-model code exists yet. Phase 1 produced only `scripts/ebay_client.py` and `scripts/verify_ebay_access.py` (eBay API access proof scripts), which are unrelated to this phase's MongoDB catalog work — no reusable assets or established patterns to inventory from them.

### Integration Points
- The `products` collection this phase creates is read by Phase 4's matching module (keyword rules match against `required_keywords`) and Phase 3's ingestion worker indirectly (matched listings reference `product_id` from this catalog).

</code_context>

<specifics>
## Specific Ideas

- Set list is time-sensitive: Chaos Rising, Perfect Order, Ascended Heroes are confirmed-released as of 2026-07-13; Pitch Black releases 2026-07-17 and should be seeded pre-release then verified post-release (D-02).
- MSRP and image_url are both "nice to have now, cheap to add later" fields the user chose to include from the start rather than retrofit (D-04, D-07).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 2-Product Catalog & Data Model*
*Context gathered: 2026-07-13*
