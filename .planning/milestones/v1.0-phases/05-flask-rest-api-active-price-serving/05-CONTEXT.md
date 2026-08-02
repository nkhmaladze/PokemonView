# Phase 5: Flask REST API (active-price serving) - Context

**Gathered:** 2026-07-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 5 builds a read-only Flask REST API that serves the catalog browse/search, product detail, current price, freshness, and 7d/30d active-price trend data the Phase 6 frontend needs — reading from the `products` and `price_points` collections Phases 2 and 4 already built and populate.

Phase 5 owns no requirements directly (per REQUIREMENTS.md's traceability note, it's an enabling serving layer). It exists to make PRICE-01, PRICE-02, PRICE-03, SEARCH-01, and SEARCH-02 user-observable in Phase 6.

No sold-price data (Marketplace Insights API, Phase 8 contingent — PRICE-04/05/06 out of scope), no write endpoints (ingestion and matching already own all writes to these collections, per ARCHITECTURE.md's read/write ownership split), no frontend code, no auth (public read-only API).

</domain>

<decisions>
## Implementation Decisions

### Freshness & Missing Data
- **D-01:** A product with zero `price_points` ever (e.g. Pitch Black pre-release) returns `current_price: null` plus an explicit status field (e.g. `"no_data_yet"`) — not an omitted field, not a 404, not hidden from browse/search. The frontend needs a distinguishable "not yet priced" state.
- **D-02:** A product that has price history but hit a gap in the most recent run (Phase 4 D-11: zero included listings → no point written, no carry-forward) still returns its **last known price_point** as `current_price`, with the freshness timestamp reflecting that point's real (older) `ts`. The price shown is always real data — never null just because the latest run happened to have a gap.
- **D-03:** There is **no separate stale/fresh boolean or threshold** computed by the API. The "data as of [timestamp]" freshness indicator (PRICE-02) is always the literal `ts` of the price_point being shown — the frontend/user judges freshness from the real date, not a computed flag. (This satisfies PITFALLS.md's "always show as of [timestamp]" guidance without adding a staleness-cutoff decision the user didn't want to make now.)
- **D-04:** The browse/list endpoint includes current price + freshness timestamp per product (not just catalog metadata) — poe.ninja-style, price visible at a glance in the grid, not gated behind opening a detail page.

### Trend Badge (7d/30d)
- **D-05:** The 7d/30d trend baseline point is the `price_points` document closest to exactly 7 (or 30) days before the current price's `ts`, accepted only if within a **±2-3 day tolerance window** of that target. Forgiving enough to survive normal gaps (D-11) while still being a meaningful "7 days" comparison.
- **D-06:** When no `price_points` document falls within tolerance of the 7d/30d target (product too new, or a long gap), the badge is **present but shows an explicit "insufficient data" state** — not omitted/absent. Makes clear trend was checked, not just unavailable.
- **D-07:** Trend % change is computed on **`total_price` only** — the same field that leads as "the price" (PRICE-01) — not `item_price`, and not both independently. One consistent trend signal matching what the user sees as the headline number.

### Browse & Search
- **D-08:** Search/browse supports **both** structured filters (`?set=`, `?product_type=`) and free-text search (`?q=` against `display_name`/`set_name`), combinable. Given the small catalog (≤16 products across 4 sets × up to 4 types), this covers both a filter-tab UI and a search box without picking one at the expense of the other.
- **D-09:** `verified: false` catalog entries (pre-release products like Pitch Black, per Phase 2 D-02) are shown **identically to verified products** in browse/search — no distinction, no provisional badge, no exclusion. The `verified` field stays a backend data-quality marker.
- **D-10:** Default browse sort order (no explicit sort param) is **grouped by set, release date descending** — newest set first (Pitch Black → Chaos Rising → Perfect Order → Ascended Heroes), products grouped within each set. Mirrors how a collector thinks about "what's current," not alphabetical or price-sorted.

### Detail & List Response Shape
- **D-11:** The product detail endpoint returns **current price + 7d/30d trend numbers only** — no raw `price_points` series/array. Matches exactly what Phase 6 needs (PRICE-01/02/03); a chart of historical points isn't in scope until Phase 8's sold-price chart (PRICE-04). Avoids overbuilding the response now.
- **D-12:** Browse-list cards show **both `total_price` (headline) and `item_price` (secondary)** per product — the same total-led/item-secondary pattern from PRICE-01 is repeated at list scale, not simplified to total-only in the grid.

### Claude's Discretion
- Exact URL/route structure and blueprint organization — follow `ARCHITECTURE.md`'s app-factory + resource-based blueprints pattern (`products`, `prices`) unless a decision above overrides it.
- Exact JSON field names beyond what's implied above (e.g. `current_price` vs `price.total`) — follow whatever shape is clearest for the frontend to consume; no user preference expressed.
- Pagination — catalog is capped at ≤16 products for v1; a single unpaginated browse response is reasonable unless research surfaces a reason otherwise.
- Error response format / HTTP status codes for malformed requests — standard REST conventions, not user-facing enough to need a decision here.
- CORS configuration specifics (Flask-CORS setup) — required since frontend is a separately-hosted SPA (per STACK.md), but the exact allowed-origins configuration is an environment/deployment detail, not a product decision.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Architecture & API design
- `.planning/research/ARCHITECTURE.md` — §"Flask REST API" component table, `api/` directory layout with blueprints by resource (not by HTTP verb), and **Pattern 3: Application-factory Flask API with thin views + service layer** (`create_app()`, routes delegate to a service layer over pymongo). This is the structural pattern Phase 5 should follow. Also documents the read/write ownership split: "API should be read-mostly against `products` and `price_points`; it does not write ingestion data."
- `.planning/research/PITFALLS.md` — "Silent stale/failed pipeline runs" pitfall (line ~92-105): explicitly assigns the "data as of [timestamp]" visible-freshness-indicator responsibility to the API/frontend phase (this phase). Also the "Showing a single 'the price' number with no indication of data freshness or sample size" anti-pattern (line ~169) — see the sample-size note under Specific Ideas below, which planning/research should resolve.

### Project-level decisions
- `.planning/PROJECT.md` — Core value (accuracy of current price + trend must always be right), Flask/MongoDB/React constraints.
- `.planning/REQUIREMENTS.md` — PRICE-01, PRICE-02, PRICE-03, SEARCH-01, SEARCH-02 (requirements this phase's API must make servable; they become user-observable in Phase 6). Note the traceability table explicitly: "Phase 5 (Flask API serving layer) ... own no requirements directly. They are enabling/operational layers."
- `.planning/ROADMAP.md` §Phase 5 — Success criteria this phase's API must support (search/browse, product detail with price data, total-led/item-secondary current price, "data as of" freshness indicator, 7d/30d trend badge).

### Prior phase decisions this phase must respect
- `.planning/phases/04-listing-matching-price-normalization/04-CONTEXT.md` D-09 through D-12 — `price_points` is one aggregated document per product per ingestion run, `{ts, product_id, item_price, total_price}`, each field its own independent median. D-11 specifically: a run with zero included listings **skips writing a point** (leaves a real gap) rather than carrying forward the last price — this phase's freshness/gap-handling decisions (D-01/D-02 above) exist directly because of that behavior.
- `.planning/phases/02-product-catalog-data-model/02-CONTEXT.md` D-02, D-06 — Pitch Black seeded pre-release with `verified: false`; `booster_bundle` is a distinct `product_type` from `booster_box`/`booster_pack` and must not be conflated in browse/filter logic.
- `db/init_collections.py` — `products` collection `$jsonSchema` (fields: `_id`, `set_name`, `product_type` enum, `language`, `display_name`, `required_keywords`, `release_date`/`msrp`/`image_url` nullable, `verified`, `verified_at`) and `price_points` time-series collection (`timeField=ts`, `metaField=product_id`, `granularity=hours`) — this phase's two read sources.
- `scripts/catalog_data.py` — `CATALOG` structure and field meanings (confirms `verified`/`verified_at` semantics referenced in D-09).
- `scripts/matching.py` `aggregate_and_write()` — confirms the exact `price_points` document shape written (`ts`, `product_id`, `item_price`, `total_price` — **no listing-count field**, see Specific Ideas below).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `db.products` — queryable catalog collection (see schema above); this phase's primary read source for browse/search/detail metadata.
- `db.price_points` — time-series collection of per-run median aggregates; this phase's primary read source for current price and trend computation. Query pattern: latest point per `product_id` for current price, nearest-to-target-date point for trend baseline (D-05).
- No Flask app, blueprints, or API code exists yet — this is a greenfield service within the existing repo. `requirements.txt` does not yet include `flask` or `flask-cors`.

### Established Patterns
- **No top-level side effects on import** — established in `scripts/ebay_client.py`, continued through Phases 2-4. The Flask app factory pattern (`create_app()`) naturally fits this discipline (nothing runs at import time; app construction is explicit).
- **Credential/config hygiene** — `MONGODB_URI` loaded via `python-dotenv` + `os.environ` at connection time, never hardcoded, never logged in full (established in `tests/conftest.py`, `scripts/ebay_client.py`).
- **Test-db fixture pattern** — `tests/conftest.py`'s `catalog_db`/`ingest_db`/`matching_db` fixtures (dedicated `pokemonview_test` database, drop-before/drop-after, skip if `MONGODB_URI` unset) is the established integration-test pattern; a Flask test client fixture for this phase should likely follow the same skip-gracefully-without-MongoDB discipline.

### Integration Points
- Reads only: `db.products`, `db.price_points`. Never writes to either (ingestion/matching own those writes exclusively, per ARCHITECTURE.md's ownership split).
- Downstream: Phase 6's React SPA is the sole consumer of this API's JSON responses — SPA never talks to MongoDB directly (ARCHITECTURE.md).

</code_context>

<specifics>
## Specific Ideas

- **Sample-size gap to flag for research/planning:** PITFALLS.md explicitly warns against "showing a single 'the price' number with no indication of ... sample size" and recommends an n-count ("based on X listings"). The current `price_points` schema (`scripts/matching.py` `aggregate_and_write()`) does **not** store a listing count — only `{ts, product_id, item_price, total_price}`. This wasn't raised as a discussion question (the user's D-01 through D-12 above don't mention it), so it's not a locked decision — but research/planning should flag whether to add a `listing_count` field to `price_points` (would touch Phase 4's writer) or compute it some other way, versus consciously deciding v1 ships without a sample-size indicator.
- Poe.ninja-style browse grid is the explicit visual reference (already established in PROJECT.md) — D-04/D-12 (price visible in list, both total+item shown) follow that reference directly.
- Precision-first / "never silently mismatch or misrepresent" is a through-line carried from Phase 4 into this phase: D-01/D-02/D-06 all prefer an explicit "no data"/"insufficient data" state over guessing, omitting, or silently substituting a number that isn't real.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 5-Flask REST API (active-price serving)*
*Context gathered: 2026-07-15*
