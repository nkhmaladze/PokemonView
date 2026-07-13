# Phase 2: Product Catalog & Data Model - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-13
**Phase:** 2-Product Catalog & Data Model
**Areas discussed:** Set selection, Catalog data source, Product variant scope, Product images

---

## Set Selection

| Option | Description | Selected |
|--------|-------------|----------|
| 3 most recent: Chaos Rising, Perfect Order, Ascended Heroes | The 3 latest fully-released English sets as of 2026-07-13 | |
| Include Pitch Black too (4 sets) | Adds Pitch Black (releases Jul 17, 2026) — slightly ahead of "2-3 sets" scope | ✓ |
| Different sets entirely | User has specific sets in mind | |

**User's choice:** Include Pitch Black too (4 sets)
**Notes:** Grounded via web search on current 2026 Pokemon TCG release calendar before asking. Confirmed sets: Chaos Rising (May 22), Perfect Order (Mar 27), Ascended Heroes (Jan 30), Pitch Black (Jul 17, upcoming).

| Option | Description | Selected |
|--------|-------------|----------|
| Seed it now from pre-release info | Product lineup typically announced ahead of release; seed now, verify after | ✓ |
| Wait until it releases | Only add after Jul 17 confirmation | |

**User's choice:** Seed it now from pre-release info
**Notes:** Pitch Black releases Jul 17, 2026 — 4 days after context gathering.

---

## Catalog Data Source

| Option | Description | Selected |
|--------|-------------|----------|
| I curate it via web research | Claude looks up official product lineup and writes catalog entries directly | ✓ |
| You provide the list | User supplies product names/SKUs, Claude structures them | |
| Use a TCG data API | Pull from pokemontcg.io or similar if it covers sealed product metadata | |

**User's choice:** I curate it via web research
**Notes:** No manual data entry burden placed on the user.

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, include MSRP | Reference point for "fair price" context even though core comparison is eBay history | ✓ |
| No, skip MSRP | Keep schema lean — only matching-relevant fields | |

**User's choice:** Yes, include MSRP

---

## Product Variant Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Standard retail product only | Only mainline packs/boxes/ETBs sold broadly at retail | ✓ |
| Include major exclusives too | Add Pokemon Center exclusive ETBs etc. as separate entries | |
| Standard + Build & Battle boxes only | Middle ground — include B&B boxes, skip one-off exclusives | |

**User's choice:** Standard retail product only

| Option | Description | Selected |
|--------|-------------|----------|
| Include booster bundles as a 3rd type | Single pack, bundle, and box are distinct types with different price points | ✓ |
| Single pack + box only | Skip booster bundles for v1 | |

**User's choice:** Include booster bundles as a 3rd type
**Notes:** `product_type` enum expands from {booster_pack, booster_box, etb} to include `booster_bundle`.

---

## Product Images

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, include image URLs | Populate image_url field now rather than retrofit later | ✓ |
| Defer to a later phase | Skip images in v1 catalog schema for now | |

**User's choice:** Yes, include image URLs

| Option | Description | Selected |
|--------|-------------|----------|
| Link to official image URLs | Store direct CDN URL, no hosting infra needed | ✓ |
| Download + self-host | Claude downloads and serves images from project storage | |

**User's choice:** Link to official image URLs
**Notes:** Accepts dependency on official CDN URL stability; no file-storage infra added to this phase's scope.

---

## Claude's Discretion

- Exact MongoDB schema field names/types beyond what's explicitly decided — follow the `products` collection shape already proposed in `.planning/research/ARCHITECTURE.md` unless overridden above.
- Depth of web research per product (release date, MSRP, image URL) — reasonable diligence, not exhaustive sourcing audits.

## Deferred Ideas

None — discussion stayed within phase scope.
