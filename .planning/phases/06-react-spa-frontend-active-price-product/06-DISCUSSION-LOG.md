# Phase 6: React SPA Frontend (active-price product) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-15
**Phase:** 6-React SPA Frontend (active-price product)
**Areas discussed:** Browse layout & grouping, Price & trend display, Freshness & no-data states, Search & filter interaction

---

## Browse Layout & Grouping

| Option | Description | Selected |
|--------|-------------|----------|
| Card grid | Image-forward tiles, like a shop catalog | |
| Dense list/table | Matches poe.ninja's actual layout — compact rows | ✓ |

**User's choice:** Dense list/table

| Option | Description | Selected |
|--------|-------------|----------|
| Section per set | Grid/list broken into labeled sections in order | |
| Tabs per set | One set visible at a time, tab bar to switch | |
| Flat grid, subtle badge | One continuous grid, small set badge per card | ✓ |

**User's choice:** Flat grid, subtle badge

| Option | Description | Selected |
|--------|-------------|----------|
| Show everything by default | All sets/types visible, filters narrow down | ✓ |
| Default to one type (e.g. booster boxes) | Start focused on one type | |

**User's choice:** Show everything by default

| Option | Description | Selected |
|--------|-------------|----------|
| Prominent | Large product art as visual anchor | |
| Small thumbnail | Image is a small icon next to text info | ✓ |

**User's choice:** Small thumbnail

---

## Price & Trend Display

| Option | Description | Selected |
|--------|-------------|----------|
| Always-visible small line | Item/shipping breakdown always shown underneath total | ✓ |
| Reveal on hover/tap | Breakdown appears in tooltip/expandable detail | |

**User's choice:** Always-visible small line

| Option | Description | Selected |
|--------|-------------|----------|
| Color-coded (green/red) | Stock-ticker style up/down coloring | ✓ |
| Neutral/muted | Same color regardless of direction | |

**User's choice:** Color-coded (green/red)

| Option | Description | Selected |
|--------|-------------|----------|
| Muted dash (—) | Minimal, doesn't call attention | ✓ |
| Explicit label | e.g. "Not enough data yet" | |

**User's choice:** Muted dash (—)

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, always (list + detail) | Sample size shown everywhere | |
| Detail page only | Shown on detail, omitted from dense list | ✓ |
| Not in v1 | Omit from UI entirely | |

**User's choice:** Detail page only

---

## Freshness & No-Data States

| Option | Description | Selected |
|--------|-------------|----------|
| Relative time | e.g. "2 hours ago" | ✓ |
| Absolute timestamp | e.g. "Jul 15, 2026 3:00 PM" | |
| Both | Relative primary, exact on hover | |

**User's choice:** Relative time

| Option | Description | Selected |
|--------|-------------|----------|
| Detail page only | Keeps list rows compact | ✓ |
| Every list row too | More visible, denser rows | |

**User's choice:** Detail page only

| Option | Description | Selected |
|--------|-------------|----------|
| Shown normally, "Coming soon" in price slot | Product appears normally, price reads placeholder | |
| Shown but visually muted/grayed | Row dimmed to signal "not actionable yet" | ✓ |
| Hidden from browse until priced | Doesn't appear until first price_point | |

**User's choice:** Shown but visually muted/grayed

---

## Search & Filter Interaction

| Option | Description | Selected |
|--------|-------------|----------|
| Search box + filter chips | Free-text plus clickable chips for set/type | ✓ |
| Search box only | Just a text input | |
| Filter chips only | Set/type chips, no text search | |

**User's choice:** Search box + filter chips

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, explicit chips/tabs | One-click narrowing to a product type | ✓ |
| No, search text covers it | Type "ETB" in the search box | |

**User's choice:** Yes, explicit chips/tabs

| Option | Description | Selected |
|--------|-------------|----------|
| Live/instant filtering | Filters as you type | ✓ |
| Explicit submit | Press enter/click search | |

**User's choice:** Live/instant filtering

---

## Claude's Discretion

- Whether `set_name` gets its own explicit filter chip symmetric with the product_type chips (D-13) — not explicitly asked, reasonable to add.
- Component structure, state management, file organization — follow ARCHITECTURE.md's `frontend/src/{pages,components,api}` layout.
- Visual-design specifics (colors, typography, spacing) — deferred to `/gsd-ui-phase` (ROADMAP.md flags `UI hint: yes` for this phase).
- Routing library usage (React Router per STACK.md) — standard usage, no discussion needed.
- Debounce/memoization approach for live search — implementation detail; only the "feels instant" requirement (D-14) is locked.
- HTTP client choice and API error/loading-state handling patterns.
- Responsive/mobile behavior specifics — not discussed.

## Deferred Ideas

None — discussion stayed within phase scope. Historical sold-price charting was mentioned only as an explicit non-goal (already correctly scoped to Phase 8 in ROADMAP.md); nothing new was deferred.
