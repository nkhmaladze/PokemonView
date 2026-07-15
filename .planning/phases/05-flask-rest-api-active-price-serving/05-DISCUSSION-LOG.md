# Phase 5: Flask REST API (active-price serving) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-15
**Phase:** 5-Flask REST API (active-price serving)
**Areas discussed:** Freshness & missing data, Trend badge window, Browse & search structure, Detail response shape

---

## Freshness & missing data

### Q1: Current price for a product with zero price_points ever (e.g. Pitch Black pre-release)

| Option | Description | Selected |
|--------|-------------|----------|
| Null price, explicit status | `current_price: null` plus a status field like `"no_data_yet"` so the frontend can show a clear "not yet priced" state | ✓ |
| Omit price fields entirely | Leave price/freshness fields out of the response entirely when no price_points exist | |
| 404 on detail, hide from browse | Exclude from browse listing and 404 the detail page until first price data exists | |

**User's choice:** Null price, explicit status

### Q2: Current price when the latest run had a gap (D-11: no carry-forward) but older price history exists

| Option | Description | Selected |
|--------|-------------|----------|
| Last known price + stale flag | Return the most recent price_point that exists, with freshness timestamp showing its real (older) ts | ✓ |
| Null price, same as no-data | Treat a gap the same as "never priced" — null current_price with a status | |
| Configurable staleness cutoff | Last known price shown if within N hours/days old; beyond that, null/no-data | |

**User's choice:** Last known price + stale flag

### Q3: What makes the last-known price "stale" vs just "current"

| Option | Description | Selected |
|--------|-------------|----------|
| Always show real timestamp, no threshold | No separate stale/fresh boolean — always surface the literal "data as of [timestamp]" and let the user judge | ✓ |
| Flag stale beyond one ingestion cycle | Mark stale if latest point is older than ~2x the ingestion interval | |
| Fixed 24h cutoff | Simple flat rule: stale if older than 24 hours | |

**User's choice:** Always show real timestamp, no threshold

### Q4: Does the browse/list endpoint include price data per product

| Option | Description | Selected |
|--------|-------------|----------|
| Price shown in browse list | Each product card shows current price at a glance (poe.ninja-style) | ✓ |
| Browse is price-free, detail has price | Browse only returns lightweight metadata; price loads on detail page only | |

**User's choice:** Price shown in browse list

---

## Trend badge window

### Q1: Tolerance window for the 7d/30d baseline price_point

| Option | Description | Selected |
|--------|-------------|----------|
| Nearest point within ±12h/±1 day | Tight tolerance, keeps the comparison meaningfully tied to "7 days" | |
| Nearest point within ±2-3 days | Wider tolerance, more forgiving of gaps | ✓ |
| Closest available point, no tolerance limit | Always use whatever point is closest, however far off | |

**User's choice:** Nearest point within ±2-3 days

### Q2: Badge behavior when no price_point falls within tolerance

| Option | Description | Selected |
|--------|-------------|----------|
| Omit the badge | Trend badge field is null/absent for that window | |
| Explicit "insufficient data" label | Badge is present but shows a distinct state | ✓ |

**User's choice:** Explicit "insufficient data" label

### Q3: Trend % change computed on which price field

| Option | Description | Selected |
|--------|-------------|----------|
| total_price only | Trend badge tracks the same number as the headline price | ✓ |
| Both, independently | Two separate % changes (total and item) | |

**User's choice:** total_price only

---

## Browse & search structure

### Q1: Search type — free-text, structured filters, or both

| Option | Description | Selected |
|--------|-------------|----------|
| Both: filters + free-text | `?q=` free-text plus `?set=`/`?product_type=` filters, combinable | ✓ |
| Structured filters only | Only set + product_type filters, no free-text | |
| Free-text only | Single `?q=` search box, no structured filter params | |

**User's choice:** Both: filters + free-text

### Q2: Handling of unverified/pre-release catalog entries (verified: false)

| Option | Description | Selected |
|--------|-------------|----------|
| Show identically, no distinction | Appears in browse/search exactly like any other product | ✓ |
| Show with a "provisional" indicator | Surface the verified flag so frontend can show a badge | |
| Exclude from browse until verified | Only verified: true products appear in results | |

**User's choice:** Show identically, no distinction

### Q3: Default browse sort order

| Option | Description | Selected |
|--------|-------------|----------|
| Grouped by set, release date desc | Newest set first, products grouped within each set | ✓ |
| Alphabetical by display_name | Simple A-Z catalog order | |
| By current price, high to low | Highest-value items first | |

**User's choice:** Grouped by set, release date desc

---

## Detail response shape

### Q1: Detail endpoint payload — summary numbers only, or raw price_points series too

| Option | Description | Selected |
|--------|-------------|----------|
| Current + trend numbers only | current_price, freshness timestamp, 7d/30d % change — no raw series | ✓ |
| Include raw price_points series too | Also return the full array of recent price_points for future charting | |

**User's choice:** Current + trend numbers only

### Q2: item_price visibility in the browse list

| Option | Description | Selected |
|--------|-------------|----------|
| Total price only in browse | Browse cards show just total_price + freshness; item_price only on detail page | |
| Both total and item in browse | Browse cards show total_price prominently with item_price as secondary text | ✓ |

**User's choice:** Both total and item in browse

---

## Claude's Discretion

- Exact URL/route structure and blueprint organization — follow ARCHITECTURE.md's app-factory + resource-based blueprints pattern unless a decision above overrides it.
- Exact JSON field names beyond what's implied by the decisions above.
- Pagination — catalog capped at ≤16 products for v1; unpaginated response is reasonable unless research says otherwise.
- Error response format / HTTP status codes for malformed requests.
- CORS configuration specifics (Flask-CORS allowed-origins) — an environment/deployment detail.

## Deferred Ideas

None — discussion stayed within phase scope.

## Note for Research/Planning (not a locked decision)

PITFALLS.md recommends showing a sample-size indicator ("based on X listings") alongside any price figure, but the current `price_points` schema (`scripts/matching.py` `aggregate_and_write()`) does not store a listing count. This was not raised as a discussion question — flagged in CONTEXT.md's Specific Ideas for research/planning to resolve (add a `listing_count` field, compute it another way, or consciously ship v1 without it).
