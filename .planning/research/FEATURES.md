# Feature Research

**Domain:** Collectibles / game-item price tracking (poe.ninja-style), applied to Pokemon TCG sealed product
**Researched:** 2026-07-12
**Confidence:** MEDIUM (web-search only, no MCP doc providers configured for this run — see Sources; individually LOW-confidence sources but cross-checked across 5+ competitor products, so triangulated conclusions are treated as MEDIUM)

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete or untrustworthy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Current price display per product | Every competitor (poe.ninja, PriceCharting, TCGPlayer, PokemonPriceTracker) leads with "what is this worth right now" | LOW | This is PROJECT.md's stated Core Value — must be accurate and fresh, not stale |
| Price history chart (time series) | poe.ninja shows up to 120 days + sparklines; PriceCharting/TCGPlayer show historic trend lines; users expect to see "is this going up or down" | MEDIUM | Requires time-series storage (MongoDB) and a charting component in the React SPA |
| Product search / browse by name | Baseline navigation — every tracker has a searchable catalog or list view | LOW | Small v1 catalog (2-3 sets) makes this trivial; still needs to exist |
| Per-set / per-category organization | PriceCharting organizes by game/set; PokemonPriceTracker by set with EV pages per set; users think in terms of "which set is this from" | LOW | Maps directly to the curated catalog structure already planned |
| Distinguishing "asking price" vs "sold/actual price" | TCGPlayer explicitly separates Market Price (sales) from Listed Median (asking); PriceCharting is sales-only; poe.ninja is listing-based. Conflating the two erodes trust | MEDIUM | This is the entire premise of PROJECT.md's dual Browse API (active) + Marketplace Insights API (sold) design — must be labeled distinctly in UI, not merged into one number |
| Last-updated / data freshness indicator | Users of price trackers instinctively check "how fresh is this" especially for a fast-moving secondary market | LOW | Simple timestamp per product; cheap to build, high trust payoff |
| Outlier/noise filtering on sold prices | PriceCharting explicitly filters outlier sales before computing market value; raw eBay sold data is full of noise (bundles, damaged, mislisted) | MEDIUM-HIGH | Directly relevant to the matching/normalization service already scoped — filtering must happen after title-matching, before display |
| Mobile-usable web UI | All competitor products are used heavily on mobile (Collectr is mobile-first); a poe.ninja-style site that's desktop-only feels dated | LOW-MEDIUM | React SPA with responsive layout; no native app needed for v1 |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable — should align with Core Value (accurate, current, both live-ask and true-sold data).

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Side-by-side active vs. sold price comparison per product | No mainstream tracker cleanly juxtaposes "current asking price" against "actual recent sold price" for the *same* product on the *same* page — TCGPlayer separates the concepts but doesn't visualize the gap. This is the direct product thesis from PROJECT.md and is a real gap in the market for sealed Pokemon product specifically | MEDIUM | Natural extension of the two-API architecture already decided; a "spread" or "premium over sold" indicator would be a strong, cheap-to-build differentiator |
| Sold-price volume/liquidity indicator (e.g. "N sold in last 7 days") | TCGPlayer's Volatility metric and poe.ninja's listing-count both hint at this; tells a buyer "is this price backed by real trading volume or one outlier sale" | LOW-MEDIUM | Just a count/aggregate over the sold-listings collection already being ingested — cheap add once sold data exists |
| Price trend badge (up/down % over 7d/30d) | poe.ninja's sparkline arrows are a major reason it's glanceable; users scan a list and want an at-a-glance signal, not just a chart they have to click into | LOW | Simple % delta calc from existing time-series data; high perceived value for low cost |
| Focus purely on sealed product (no singles) | PriceCharting, TCGPlayer, PokemonPriceTracker, Collectr all mix singles + sealed, which dilutes the sealed-buyer experience (search noise, UI built for individual cards). A sealed-only, clean, fast site is a real niche differentiator, not a limitation | LOW (it's a scope choice, not a feature to build) | Reinforces the explicit v1 scope in PROJECT.md — lean into it as a positioning differentiator rather than treating "no singles" as merely a missing feature |

### Anti-Features (Commonly Requested, Often Problematic — Or Explicitly Out of Scope per PROJECT.md)

Features that seem good but create problems, or that PROJECT.md has explicitly deferred. Listed here so the roadmap doesn't accidentally scope-creep into them.

| Feature | Why Requested | Why Problematic (for v1) | Alternative |
|---------|---------------|-------------------|-------------|
| Deal-finder / underpriced-listing alerts | Every collectibles tracker eventually gets this request ("ping me when something's a good deal") — Collectr-style watchlists lean this direction | PROJECT.md explicitly defers this: it's a different product (real-time listing evaluation vs. aggregate price display) requiring per-listing scoring logic, notification infra, and much tighter latency than a periodic cron pull can offer | Ship current-price + trend first (the core value); revisit deal alerts as a v2 differentiator once ingestion/matching is proven reliable |
| Portfolio / collection value tracking | Collectr's core feature — "what is my whole collection worth" — is highly requested in this space and drives retention | Requires user accounts, holdings data model, and auth — a whole second product surface orthogonal to "look up a product's price." Adds significant scope before the core lookup experience is validated | Defer to v2+; v1 is anonymous, lookup-only, no accounts |
| Singles / individual card pricing | The largest overall market (TCGPlayer, CardMarket, PriceCharting singles) and the most-requested expansion once sealed tracking works | PROJECT.md explicitly scopes v1 to sealed-only; singles pricing is a different catalog shape (per-card, per-rarity, per-condition/grade) and a much larger, messier catalog than 2-3 sets of sealed product | Explicitly out of scope; revisit only after sealed-product ingestion/matching pipeline is proven |
| Non-English / regional product (Japanese, etc.) | Japanese sealed product (esp. via PokemonPriceTracker) is a real, actively-traded market collectors ask about | PROJECT.md scopes v1 to English-only; adding another language multiplies catalog and matching-rule complexity (different set names, different eBay title conventions) before the core pipeline is validated | Explicitly out of scope for v1; candidate expansion once English pipeline is stable |
| Full historical/vintage catalog (all sets ever) | Users researching "what was a 2002 booster box worth" want long-tail coverage, and PriceCharting's appeal is partly its exhaustive catalog | Vintage sealed product has thinner eBay sold-listing volume, more counterfeit/reproduction risk in titles, and a much larger matching-rule surface — high cost, uncertain payoff before v1's core loop is validated | PROJECT.md already scopes v1 to the 2-3 most recent sets; expand set coverage incrementally post-launch |
| Card-scanning / camera-based product recognition | Collectr's camera-add feature is popular for individual card collection apps | Massively over-engineered for a sealed-product-only, no-accounts v1 with only 2-3 sets — there's no "collection" to add items to yet (no portfolio feature) | Not applicable until/unless portfolio tracking is built |
| Multi-marketplace price comparison (eBay + TCGPlayer + CardMarket simultaneously) | Feels like an obvious "more data = better" differentiator, and some competitors (Cardmarket trackers) pull from multiple sources | PROJECT.md explicitly commits to official eBay APIs only for legal/stability reasons; multiplying source APIs multiplies auth, rate-limit, and normalization complexity for a v1 focused on validating the core eBay-only loop | Single-source (eBay) v1 as scoped; revisit multi-source aggregation as a later differentiator once matching pipeline is proven on one source |
| Real-time push updates / websocket live pricing | "Real-time everything" has surface appeal for a "live price" product | eBay listings don't change price-relevant state fast enough to justify websocket infra; PROJECT.md already chose simple periodic cron ingestion over always-on infra (rejected Celery/broker) | Periodic polling (as already decided) is sufficient; a "last updated Xh ago" label manages user expectations instead |

## Feature Dependencies

```
Curated product catalog (2-3 sets)
    └──requires──> Matching/normalization service (maps eBay titles → catalog products)
                       └──requires──> Ingestion worker (active + sold listings pulled)
                                          └──requires──> eBay Browse API access (active) [low-friction]
                                          └──requires──> eBay Marketplace Insights API access (sold) [gated, needs approval — flagged as early risk in PROJECT.md]

Current price display ──requires──> Ingestion (active listings) + Matching
Price history chart ──requires──> Ingestion (sold listings, time-series) + Matching + MongoDB time-series storage
Active-vs-sold comparison (differentiator) ──requires──> BOTH ingestion paths working + Matching ──enhances──> Current price display
Price trend badge (7d/30d %) ──requires──> Price history chart data already being stored
Sold-price volume/liquidity indicator ──requires──> Sold listings ingestion (Marketplace Insights API)
Outlier filtering ──requires──> Matching/normalization service (must run after title-matching, before price is shown)

Portfolio tracking (deferred) ──requires──> User accounts (not in v1 scope) ──conflicts──> v1's anonymous, lookup-only design
Deal-finder alerts (deferred) ──requires──> Near-real-time per-listing scoring ──conflicts──> Simple cron/periodic ingestion (already decided over Celery)
Singles pricing (deferred) ──conflicts──> Sealed-only v1 scope (different catalog shape entirely)
```

### Dependency Notes

- **Everything downstream depends on the Marketplace Insights API approval** — sold-price data (price history, active-vs-sold comparison, liquidity indicator, outlier filtering baseline) all sit behind the gated, approval-required Marketplace Insights API. PROJECT.md already flags this correctly as an early risk; it should be resolved before phases that build on sold data are planned, not discovered mid-build.
- **Outlier filtering is a matching-service concern, not a display concern.** PriceCharting's approach (filter before averaging) implies the normalization/matching service should tag or drop clearly-anomalous sold listings (lots, bundles, damaged, wrong-item matches) before they ever reach the price-history calculation — this belongs in an earlier phase than "build the chart."
- **Portfolio tracking and deal-finder alerts both conflict with decisions already locked in PROJECT.md** (no accounts, no broker infra) — they are correctly deferred, and building them later would likely require revisiting the "no Celery" and "no accounts" decisions, not just adding a feature.
- **The active-vs-sold comparison differentiator has zero additional ingestion cost** — it's a display/aggregation feature that falls out naturally once both API paths are wired up, making it a very high-leverage feature to prioritize once matching is solid.

## MVP Definition

### Launch With (v1)

Minimum viable product — what's needed to validate the concept per PROJECT.md's Core Value.

- [ ] Curated catalog browse/search (2-3 recent English sets, packs/boxes/ETBs) — without this there's nothing to look up
- [ ] Current active-listing price per product (Browse API) — the "is this priced fairly right now" half of Core Value
- [ ] Sold-price history + chart per product (Marketplace Insights API) — the "backed by real trend data" half of Core Value
- [ ] Clear labeling distinguishing asking price vs. sold price — prevents the single biggest trust failure mode seen in competitor research (conflating the two)
- [ ] Data freshness timestamp — cheap, builds trust in a periodic-ingestion model
- [ ] Basic outlier filtering on sold data — raw eBay sold titles are noisy; unfiltered data undermines the "must always be accurate" requirement

### Add After Validation (v1.x)

Features to add once core lookup loop is working and trusted.

- [ ] Price trend badge (7d/30d % change) — trigger: once time-series data has enough history to compute meaningful deltas
- [ ] Sold-volume/liquidity indicator — trigger: once sold-listing volume per product is consistently non-trivial
- [ ] Active-vs-sold spread/premium indicator — trigger: once both data paths are stable and outlier-filtered
- [ ] Expand catalog to more sets — trigger: core pipeline (ingestion + matching) proven reliable on initial 2-3 sets

### Future Consideration (v2+)

Features to defer until product-market fit is established (explicitly out of scope per PROJECT.md).

- [ ] Deal-finder / underpriced-listing alerts — why defer: different product shape (near-real-time scoring vs. periodic aggregate display), needs notification infra
- [ ] Portfolio/collection value tracking — why defer: requires user accounts, a second product surface
- [ ] Singles/individual card pricing — why defer: different catalog shape, much larger scope, explicitly out per PROJECT.md
- [ ] Non-English/regional product (e.g. Japanese sets) — why defer: multiplies catalog and matching complexity, explicitly out per PROJECT.md
- [ ] Full vintage/historical catalog — why defer: thinner sold-listing data, higher counterfeit-title risk, explicitly out per PROJECT.md
- [ ] Multi-marketplace aggregation (TCGPlayer, CardMarket, etc.) — why defer: conflicts with the explicit eBay-only decision; revisit only as a later differentiator

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Current active price display | HIGH | LOW | P1 |
| Sold-price history chart | HIGH | MEDIUM-HIGH (gated API + time-series) | P1 |
| Product catalog browse/search | HIGH | LOW | P1 |
| Asking-vs-sold labeling/distinction | HIGH | LOW-MEDIUM | P1 |
| Data freshness timestamp | MEDIUM | LOW | P1 |
| Outlier filtering on sold data | HIGH | MEDIUM-HIGH | P1 |
| Price trend badge (%) | MEDIUM-HIGH | LOW | P2 |
| Active-vs-sold spread indicator | HIGH (key differentiator) | LOW (once both feeds exist) | P2 |
| Sold-volume/liquidity indicator | MEDIUM | LOW | P2 |
| Catalog expansion (more sets) | MEDIUM | LOW (once pipeline proven) | P2 |
| Deal-finder alerts | HIGH (long-term) | HIGH | P3 |
| Portfolio tracking | HIGH (long-term) | HIGH | P3 |
| Singles pricing | HIGH (long-term, biggest market) | VERY HIGH | P3 |
| Multi-marketplace aggregation | MEDIUM | HIGH | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

## Competitor Feature Analysis

| Feature | poe.ninja | PriceCharting | TCGPlayer | PokemonPriceTracker (direct competitor) | Our Approach |
|---------|-----------|----------------|-----------|-------------------------------------------|--------------|
| Current price | Live, listing-derived, updated every few minutes | Sales-derived rolling average | "Market Price" from completed sales + "Listed Median" from active listings, shown separately | Daily TCGPlayer pull | Both active (Browse API) and sold (Marketplace Insights API), clearly labeled and shown side by side |
| Price history | Up to 120 days, sparkline + full chart | Historic trend chart per condition tier | Historical data article/tools, less prominent on product page | Not a strong focus (EV-calculator-centric) | Sold-price time series chart per product, this is our clearest strength vs. all four |
| Condition/variant granularity | N/A (unique items, not condition-graded) | Loose/CIB/New/Sealed + graded (Wata/VGA) | Per-card condition/edition | Booster box/ETB/pack per set | Sealed-only, so condition variance is simpler (new/sealed only) — lean into simplicity, don't over-build condition tiers we don't need |
| Outlier handling | Not clearly documented | Explicit, published methodology filtering outliers before averaging | Filters outliers from Market Price calc | Not clearly documented | Explicit filtering step in the matching/normalization service; consider publishing methodology for trust, mirroring PriceCharting |
| Differentiator feature | Currency/build-economy context (not applicable to us) | Graded-sealed price tracking, huge historical catalog | Volatility metric, Most Recent Sale | EV calculator (pull-rate-weighted expected value + ROI) | Active-vs-sold spread + freshness-focused, EV calculator noted as a strong future differentiator once core loop is proven (v1.x/v2 candidate, not required to compete initially since it's a distinct value-add rather than core-loop parity) |
| Scope | Whole PoE item/currency economy | All games/cards/comics, all conditions, all eras | All TCGs, singles + sealed | Pokemon sealed + singles, English + Japanese | Pokemon sealed only, English only, 2-3 recent sets — narrowest scope of all, by design |

## Sources

- [poe.ninja](https://poe.ninja/) and [PoE2 Ninja economy guide](https://pathofexile2.games-wiki.wiki/guides/poe2-ninja/) — LOW confidence (general web search, not official docs), cross-checked across multiple result summaries describing the same feature set
- [PriceCharting FAQ](https://www.pricecharting.com/faq) and [PriceCharting methodology](https://www.pricecharting.com/page/methodology) — LOW confidence (web search), but PriceCharting's own published methodology page is effectively primary-source
- [TCGplayer Market Price help article](https://help.tcgplayer.com/hc/en-us/articles/213588017-TCGplayer-Market-Price) — LOW confidence via search snippet, but sourced from TCGplayer's own help center (higher trust despite tool-classified LOW tier)
- [PokemonPriceTracker.com sets/EV pages](https://www.pokemonpricetracker.com/sets/ev) — LOW confidence (web search); this is a direct competitor in the exact niche (Pokemon sealed product price tracking) and worth monitoring closely as the roadmap develops
- [Collectr](https://getcollectr.com/) and [Collectr portfolio tracking](https://getcollectr.com/track.html) — LOW confidence (web search), used for portfolio-tracking anti-feature rationale
- Note on confidence tier: `classify-confidence` returned LOW for the `websearch` provider used throughout this research pass (no premium search/doc MCP providers — Exa, Tavily, Brave, Firecrawl, Context7 — were configured as available for this run). Findings were cross-checked across 5+ independent competitor products with converging patterns, which raises practical reliability above a single-source LOW, but no finding here should be treated as verified against primary documentation.

---
*Feature research for: Pokemon TCG sealed-product price tracking (poe.ninja-style)*
*Researched: 2026-07-12*
