# Phase 6: React SPA Frontend (active-price product) - Context

**Gathered:** 2026-07-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 6 builds the greenfield React SPA that lets a user browse/search the sealed-product catalog and open a product detail page showing current price (total-led, item-price secondary), a "data as of" freshness indicator, and 7d/30d trend badges — the shippable v1 product surface (PRICE-01/02/03, SEARCH-01/02).

The SPA is a pure REST client of the Phase 5 Flask API (`GET /products`, `GET /products/:id`) — no new backend endpoints, no direct MongoDB access. No sold-price data or historical chart (Phase 8, contingent — the API deliberately returns no raw `price_points` series per 05-CONTEXT.md D-11, so a poe.ninja-style history chart is out of scope until Phase 8). No auth, no admin surface, no write operations.

</domain>

<decisions>
## Implementation Decisions

### Browse Layout & Grouping
- **D-01:** Dense list/table layout for the browse view — matches poe.ninja's actual style (compact rows: thumbnail, name, price, trend), not an image-forward card grid.
- **D-02:** The API's set-grouping (Pitch Black → Chaos Rising → Perfect Order → Ascended Heroes, newest first, per 05-CONTEXT.md D-10) surfaces as a flat, continuous list with a small set badge per row — no hard section breaks and no per-set tabs.
- **D-03:** All products/types are shown by default (nothing hidden behind an initial filter) — matches the API's "combinable, nothing hidden" filter design (05-CONTEXT.md D-08).
- **D-04:** Product images render as small thumbnails, not large/prominent art — the row stays text-dense, image is a secondary visual anchor.

### Price & Trend Display
- **D-05:** `total_price` is the headline number; `item_price` (+ shipping breakdown) renders as an always-visible smaller line beneath it — never hidden behind a hover/tap interaction. Satisfies PRICE-01's "total-led, item-price secondary" requirement without requiring user interaction to see the full picture.
- **D-06:** Trend badges (7d/30d `pct_change`) are color-coded — green for price up, red for price down (stock-ticker style).
- **D-07:** When a trend's `status` is `"insufficient_data"` (API never omits the badge, per 05-CONTEXT.md D-06), it renders as a muted dash (—) — present but visually quiet, not an explicit "not enough data yet" sentence.
- **D-08:** `listing_count` (sample size) is shown on the product detail page only — omitted from the dense browse list to keep rows compact. This still satisfies PITFALLS.md's "always pair a price with a sample-size indicator" guidance, just not in the list view.

### Freshness & No-Data States
- **D-09:** The "data as of [timestamp]" freshness indicator (PRICE-02) uses relative time ("2 hours ago"), not an absolute timestamp — consistent with the API's literal, un-computed `ts` (05-CONTEXT.md D-03) being rendered in a human-friendly form.
- **D-10:** Freshness is shown on the product detail page only, not in every browse-list row — keeps list rows to price + trend + set badge.
- **D-11:** A product with `price_status: "no_data_yet"` (e.g. pre-release Pitch Black, per 05-CONTEXT.md D-01) still appears in its normal position in the browse list, but the row is visually muted/grayed to signal "not yet actionable" without hiding it entirely.

### Search & Filter Interaction
- **D-12:** Users narrow the list via a search box (free text against `display_name`/`set_name`, matching API `?q`) plus filter chips/tabs — not search-only or chips-only.
- **D-13:** `product_type` (booster pack / booster box / booster bundle / ETB) gets its own explicit chip/tab control — not left to free-text search alone.
- **D-14:** Search filters live/instantly as the user types (no submit action, no debounce concerns given the ≤16-product catalog size).

### Claude's Discretion
- Whether `set_name` gets its own explicit filter chip control alongside `product_type`, or is left to the set-badge-plus-search-text combination — not explicitly asked; reasonable to add a set filter chip too, symmetric with D-13's product_type chips, unless research/planning finds a reason not to.
- Exact component structure, state management approach, and file organization — follow `ARCHITECTURE.md`'s `frontend/src/{pages,components,api}` structure unless a decision above overrides it.
- Exact color values, typography, spacing, and other visual-design specifics — this phase has `UI hint: yes` in ROADMAP.md, meaning `/gsd-ui-phase` should produce the detailed UI-SPEC.md design contract; the decisions above are product/behavior-level, not a full visual spec.
- Client-side routing library/approach for list vs. detail page navigation — `React Router` per STACK.md, standard usage.
- Whether/how to debounce or memoize live search given the tiny catalog size — implementation detail, not a product decision (D-14 only locks that it must feel instant).
- HTTP client choice (fetch vs. axios) and API error/loading-state handling patterns — implementation detail; no user preference expressed.
- Responsive/mobile behavior specifics — not discussed; default to a reasonably responsive dense list unless UI-SPEC phase surfaces a stronger requirement.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### API contract this phase consumes
- `api/blueprints/products.py` — the exact two routes this SPA calls: `GET /products` (200 + JSON array, or 400 `{"error":"invalid_product_type"}`) and `GET /products/<product_id>` (200 + detail object, or 404 `{"error":"not_found"}`).
- `api/services/catalog_service.py` — `_product_summary()` defines the exact JSON shape returned in both the list and detail responses (`id, set_name, product_type, display_name, release_date, msrp, image_url, verified, price_status, current_price`), and `get_product_detail()` adds `trend_7d`/`trend_30d` (`{pct_change, status}`) on the detail response only. **No raw `price_points` series is ever returned** (05-CONTEXT.md D-11) — there is nothing to chart in v1.
- `api/services/price_service.py` — confirms `current_price` fields (`total_price, item_price, as_of, listing_count`) and that `listing_count` may be `None`/absent on older documents (pre-dates the field).

### Architecture & design
- `.planning/research/ARCHITECTURE.md` — `frontend/` recommended structure (`src/{pages,components,api}`), "frontend fully decoupled, REST-only" boundary (SPA never touches MongoDB directly), React + Recharts as the chart library choice (not yet needed until Phase 8's history chart).
- `.planning/research/STACK.md` — React 19.2.x, Vite 6/7.x, React Router 7.x, Recharts 3.9.x (deferred to Phase 8), Flask-CORS already configured server-side (05-CONTEXT.md/CR-02) so the SPA can call the API cross-origin in dev.
- `.planning/research/PITFALLS.md` — UX Pitfalls table: "Showing a single 'the price' number with no indication of data freshness or sample size" (informs D-08/D-09/D-10) and "Mixing active (asking) and sold (actual) prices" (not applicable yet — v1 is active-only, but keep the visual vocabulary reusable/extensible for Phase 8's sold-price distinction).

### Project-level decisions
- `.planning/PROJECT.md` — Core value (accuracy of current price + trend must always be right), poe.ninja as the explicit direct-inspiration reference (informs D-01's dense-list layout choice).
- `.planning/REQUIREMENTS.md` — PRICE-01, PRICE-02, PRICE-03, SEARCH-01, SEARCH-02 (this phase's owned requirements, all becoming user-observable here for the first time).
- `.planning/ROADMAP.md` §Phase 6 — Success criteria (search/browse by name or set, product detail page, total-led/item-secondary price, freshness indicator, 7d/30d trend badge); notes `UI hint: yes`.

### Prior phase decisions this phase must respect
- `.planning/phases/05-flask-rest-api-active-price-serving/05-CONTEXT.md` — D-01 through D-12 define exactly what data shape and semantics this phase's UI must render (no-data state, gap-tolerant current price, trend tolerance windows, combinable filters, default sort order). Do not re-litigate these; the SPA renders what the API already guarantees.
- `.planning/phases/02-product-catalog-data-model/02-CONTEXT.md` D-06 — `booster_bundle` is a distinct `product_type` from `booster_box`/`booster_pack`, must stay visually distinct in filters (D-13).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- No frontend code exists yet — `frontend/` directory does not exist in the repo. This is a fully greenfield build within the existing monorepo (alongside `api/`, `db/`, `scripts/`, `tests/`).
- The Flask API (`api/app.py` `create_app()`) is complete, tested, and CORS-configured (05-07 gap closure, CR-02) — ready to be called from a separately-hosted dev server immediately.

### Established Patterns
- **No top-level side effects on import** — established across `scripts/ebay_client.py`, `scripts/matching.py`, `api/services/*.py`. Not directly applicable to React, but the equivalent discipline (no side effects in module scope, effects only in component lifecycle/hooks) is the natural analog.
- **Explicit "no data" over guessing/omitting** — a strict through-line from Phases 4-5 (`no_data_yet`, `insufficient_data`, gap-preserving current price). This phase's D-07/D-11 continue that pattern into the UI (muted dash, grayed row) rather than hiding these states.

### Integration Points
- Reads only: the two `api/` REST endpoints (`GET /products`, `GET /products/:id`). No direct MongoDB access from the frontend, ever.
- Downstream: none — this is the terminal consumer in the v1 active-price pipeline (ingestion → matching → API → **this SPA**).

</code_context>

<specifics>
## Specific Ideas

- Poe.ninja is the literal visual/interaction reference for the browse view — dense, scannable rows rather than a showcase card grid (D-01/D-02/D-04), reaffirming the reference already established in PROJECT.md.
- The "flag/show, never hide" philosophy that ran through Phases 4-5 (never silently drop a listing, never omit a trend badge) continues visually into this phase: no-data products stay in the list (muted, not hidden — D-11), insufficient-data trends stay in their badge slot (muted dash, not omitted — D-07).
- Because the API never returns a raw price history series (05-CONTEXT.md D-11 by design), there is no chart in this phase at all — Recharts (per STACK.md) isn't wired up until Phase 8. Don't over-build a charting placeholder now.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. (Historical sold-price charting was mentioned only as an explicit non-goal, already correctly scoped to Phase 8 in ROADMAP.md — nothing new was deferred.)

</deferred>

---

*Phase: 6-React SPA Frontend (active-price product)*
*Context gathered: 2026-07-15*
