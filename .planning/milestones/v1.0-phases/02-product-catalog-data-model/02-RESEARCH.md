# Phase 2: Product Catalog & Data Model - Research

**Researched:** 2026-07-13
**Domain:** MongoDB curated-catalog data modeling + PyMongo seeding patterns + Pokemon TCG sealed-product catalog curation
**Confidence:** MEDIUM (MongoDB/PyMongo technical patterns are officially documented and cross-checked; catalog product/MSRP data is web-sourced and time-sensitive, especially for the pre-release Pitch Black set)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** The v1 catalog covers 4 sets, not the original "2-3 most recent" framing — the user explicitly chose to include the newest set even though it's pre-release: **Chaos Rising** (May 22, 2026), **Perfect Order** (Mar 27, 2026), **Ascended Heroes** (Jan 30, 2026), and **Pitch Black** (releases Jul 17, 2026). This should be reflected as an updated scope note in PROJECT.md/REQUIREMENTS.md at the next phase transition.
- **D-02:** Pitch Black (not yet released as of context-gathering date) should be seeded into the catalog NOW using best-available pre-release product-lineup info, then verified/corrected once it actually releases on Jul 17, 2026.
- **D-03:** Claude curates the product list and metadata directly via web research (official Pokemon Center site, TCGplayer, and set-tracking sites) — no manual data entry required from the user, and no third-party TCG data API dependency.
- **D-04:** The catalog schema includes an MSRP (manufacturer retail price) field per product, as a reference point for "asking price vs. retail" context — even though v1's core "fair price" judgment is against eBay price history, not MSRP.
- **D-05:** Only standard, broadly-retailed product counts as a catalog entry in v1 — no Pokemon Center exclusives, Build & Battle boxes, or promo-only variants. Keeps the catalog and matching rules focused on mainline retail listings.
- **D-06:** `product_type` includes a 3rd distinct value beyond the original "booster pack | booster box | ETB": **booster bundle** (sleeved multi-pack, ~6 packs). Booster bundles have meaningfully different price points from both single packs and full boxes and must not be conflated with either in the catalog or downstream matching/pricing.
- **D-07:** The catalog includes an `image_url` field per product, populated now (not deferred to a later phase) — a poe.ninja-style product page needs an image to read as complete.
- **D-08:** Images are referenced via direct links to official/public CDN URLs (Pokemon Center, TCGplayer) — no downloading, self-hosting, or file-storage infrastructure for v1. Accepts the tradeoff that catalog image links depend on those URLs staying stable.

### Claude's Discretion

- Exact MongoDB schema field names/types beyond what's specified above (e.g., how `required_keywords` are structured) — Claude should follow the `products` collection shape already proposed in `.planning/research/ARCHITECTURE.md` unless a specific gray area above overrides it.
- How thoroughly to web-research each product's exact release date/MSRP/image URL — reasonable diligence, not exhaustive sourcing audits.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CATALOG-01 | Curated catalog of sealed English product (booster packs, booster boxes, ETBs) exists for the 2-3 most recent sets | See "Curated Catalog Reference Data" — 4 sets × up to 4 product types (booster_pack, booster_box, etb, booster_bundle per D-06), 15-16 documents total, sourced from Pokemon Center/TCGplayer. See "Code Examples" for idempotent seeding pattern. |
| CATALOG-02 | Each catalog product has canonical metadata (set, product type, release info) used for matching | See "Standard Stack" for the `products` document shape (extends ARCHITECTURE.md's proposal with `product_type: booster_bundle`, `msrp`, and `image_url` per D-04/D-06/D-07) and "Code Examples" for `$jsonSchema` validator enforcing this shape at the DB layer. |
</phase_requirements>

## Summary

This phase has two distinct halves: (1) a **technical data-modeling problem** — designing and creating the MongoDB `products` collection (schema validation, indexing) and reserving the future `price_points` time-series collection with the correct creation-time options, since MongoDB cannot retrofit a plain collection into a time-series collection later — and (2) a **content-curation problem** — researching and hand-curating ~15-16 real sealed-product catalog entries across 4 Pokemon TCG sets (Chaos Rising, Perfect Order, Ascended Heroes, Pitch Black), each with accurate set/product-type metadata, MSRP, release date, and a direct image URL.

On the technical side, the standard approach is: create `products` with a `$jsonSchema` validator (`validationLevel: "strict"`, `validationAction: "error"`) to catch shape drift from any future writer, add a compound index on `{set_name: 1, product_type: 1}` for the query pattern this phase's success criteria requires, and create `price_points` now as a proper `timeseries` collection (`metaField: "product_id"`, `timeField: "ts"`, `granularity: "hours"`) even though it stays empty until Phase 3's ingestion worker writes to it — granularity and metaField cannot be changed after creation in ways that matter here, so getting this right in Phase 2 avoids a schema migration in Phase 3. Seeding must be idempotent: use `bulk_write` with `UpdateOne(filter, {"$set": doc}, upsert=True)` keyed on a stable natural key (e.g., a deterministic `_id` slug like `chaos-rising_booster_box`), not auto-generated ObjectIds, so re-running the seed script (e.g., after Pitch Black's real release-day data lands) updates in place rather than duplicating.

On the content side, web research confirms release dates and most MSRPs for all four sets from official/near-official sources (Pokemon Center, TCGplayer, Pokemon.com), but several data points are pattern-inferred rather than directly confirmed (flagged `[ASSUMED]` throughout) — most notably Ascended Heroes' standard booster box MSRP and most sets' single booster-pack MSRP. TCGplayer product IDs discovered during research enable a reliable `image_url` pattern (`https://tcgplayer-cdn.tcgplayer.com/product/{id}_in_1000x1000.jpg`) satisfying D-07/D-08 without scraping. Pitch Black (D-02) must be seeded from pre-release lineup data now and explicitly re-verified after its July 17, 2026 release — this should be tracked as an open follow-up, not silently forgotten.

**Primary recommendation:** Create `products` with a `$jsonSchema` validator + compound index on `{set_name, product_type}`; create `price_points` as a `timeseries` collection now (empty, reserved for Phase 3); seed both via one idempotent `bulk_write` script keyed on a deterministic slug `_id`; treat all web-sourced MSRP/product-lineup facts as provisional and re-verify Pitch Black post-release.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Catalog data persistence (`products`) | Database/Storage | — | The curated catalog is the canonical persisted dataset; no app-tier caching/derivation needed at this phase. |
| Catalog seeding / idempotent upsert | API/Backend (one-off script) | Database/Storage | A standalone Python script using pymongo, not a long-running service — writes directly to MongoDB, not through an API layer. |
| Schema validation (`$jsonSchema`) | Database/Storage | — | Enforced at MongoDB collection-creation time; protects against shape drift from any future writer (this script, or later ingestion/matching code), not just this phase's own script. |
| Query indexing (set + product_type) | Database/Storage | — | Index defined at the DB layer; consumed by the future Flask API's read queries (Phase 5), not built or cached at this phase. |
| `price_points` time-series reservation | Database/Storage | — | Collection structure (timeField/metaField/granularity) must be fixed at creation time — created empty now so Phase 3's ingestion worker can write into an already-correct schema. |
| Product image display | CDN/Static (external, Pokemon Center/TCGplayer) | Database/Storage | `image_url` only stores a reference string; actual image bytes are served by the retailer's own CDN per D-08 — this project owns no image infrastructure. |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyMongo | 4.17.0 `[VERIFIED: pypi registry]` | Official MongoDB Python driver — used directly (no ODM) to create collections, validators, indexes, and seed documents | Already the project's decided driver per `.claude/CLAUDE.md`; confirmed current via `pip3 index versions pymongo` on 2026-07-13; official `mongodb/mongo-python-driver` GitHub org |
| python-dotenv | 1.2.2 (already pinned in `requirements.txt`) `[VERIFIED: local install]` | Loads `MONGODB_URI` (or equivalent) from `.env`, keeping the connection string out of source control | Already installed and used by Phase 1's `scripts/ebay_client.py`; same pattern applies to the Mongo connection string used by the seed script |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.x (not yet installed — Wave 0 gap) | Validates the seed script is idempotent and the schema validator rejects malformed documents | Add in this phase's Wave 0 per Validation Architecture below — no test infra exists in the repo yet |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Raw PyMongo + `$jsonSchema` validator | An ODM (MongoEngine, Motor+Pydantic, Beanie) | An ODM adds a declarative schema layer in Python, but the project's stack decision already rejected Django's ORM-style coupling to MongoDB's document model; a small, curated, single-collection catalog does not need ODM overhead — raw pymongo + a DB-level validator keeps the write path identical to what ingestion/matching will use in later phases |
| MongoDB-native `$jsonSchema` validation | Application-layer validation only (e.g., a Python dataclass/Pydantic model checked before insert) | App-layer-only validation is bypassed by any other script or shell (`mongosh`) that writes to the collection directly; DB-level `$jsonSchema` is enforced regardless of the writer. Both together is ideal, but if choosing one for this phase, the DB-level validator is the higher-leverage investment | 
| Deterministic slug `_id` (e.g. `"perfect-order_booster_box"`) | Auto-generated ObjectId + separate unique compound index on `{set_name, product_type}` | A natural-key `_id` makes `bulk_write` upserts trivially idempotent with a single-field filter; ObjectId + a secondary unique index accomplishes the same idempotency but requires an extra index and a two-field filter — slug `_id` is simpler for a hand-curated, low-cardinality catalog |

**Installation:**
```bash
pip install pymongo==4.17.0
# python-dotenv==1.2.2 already in requirements.txt from Phase 1
pip install pytest==8.4.2  # if adding the Wave 0 test gap (see Validation Architecture)
```

**Version verification:** `pip3 index versions pymongo` was run directly (2026-07-13) and returned `4.17.0` as latest — this is the pinned version above, not a training-data guess. No compatibility conflicts with Python 3.12 (confirmed installed: `Python 3.12.13`) or MongoDB 7.0/8.0 per PyMongo's documented support matrix (already cited in `.claude/CLAUDE.md`).

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| pymongo | pypi | Latest release 2026-04-20 (package itself is 10+ years old — MongoDB's own official driver) | Unknown to legitimacy-check tool (`unknown-downloads` signal — the tool could not retrieve download stats, not evidence of low usage) | `github.com/mongodb/mongo-python-driver` (official MongoDB org) | `[SUS]` (tool-flagged solely on missing download-count data) | Approved — see note below |

**Packages removed due to [SLOP] verdict:** none
**Packages flagged as suspicious [SUS]:** `pymongo` — flagged only because the legitimacy-check tool could not resolve a download-count signal (`unknown-downloads`), not because of any actual red flag. The source repo resolves to MongoDB's own official GitHub organization (`mongodb/mongo-python-driver`), it is the project's already-decided driver per `.claude/CLAUDE.md`, and it is confirmed to exist and install correctly on this machine (`pip3 show pymongo` — not yet installed, but `pip3 index versions pymongo` confirms registry presence and current version). **Despite this being a false-positive SUS from missing download telemetry, per protocol the planner must still insert a `checkpoint:human-verify` task before the `pip install pymongo` step**, so the human sees this context and can confirm before install rather than the check being silently overridden by research.

*No new packages beyond pymongo are introduced by this phase — `python-dotenv` was already installed and verified in Phase 1.*

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     THIS PHASE'S SCOPE                            │
│                                                                     │
│  Curated catalog data                                             │
│  (hand-researched: 4 sets × product types, MSRP, image URLs)      │
│         │                                                          │
│         ▼                                                          │
│  ┌─────────────────────┐                                          │
│  │  scripts/seed_       │   one-off script, run manually/on-      │
│  │  catalog.py          │   demand (not scheduled/cron)           │
│  │  - builds documents  │                                          │
│  │  - bulk_write         │                                          │
│  │    UpdateOne(upsert)  │                                          │
│  └──────────┬───────────┘                                          │
│             │ idempotent upsert, keyed on slug _id                 │
│             ▼                                                      │
├─────────────────────────────────────────────────────────────────┤
│                          MONGODB                                   │
│  ┌──────────────────────┐    ┌───────────────────────────────┐   │
│  │  products             │    │  price_points (time series)     │   │
│  │  - $jsonSchema         │    │  - metaField: product_id        │   │
│  │    validator           │    │  - timeField: ts                │   │
│  │  - compound index       │    │  - granularity: hours           │   │
│  │    {set_name,           │    │  - CREATED EMPTY THIS PHASE     │   │
│  │     product_type}       │    │    (Phase 3 writes into it)     │   │
│  └──────────────────────┘    └───────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
             ▲                                    ▲
             │ read (query by set/type)           │ write (later phase)
             │                                     │
   Phase 4 matching module              Phase 3 ingestion worker
   (reads required_keywords)            (writes price_points, not
                                          in scope this phase)
```

### Recommended Project Structure

```
pokemonview/
├── scripts/
│   ├── ebay_client.py           # Phase 1 (unrelated to this phase)
│   ├── verify_ebay_access.py    # Phase 1 (unrelated to this phase)
│   ├── seed_catalog.py          # NEW this phase — idempotent catalog seed script
│   └── catalog_data.py          # NEW this phase — curated product data as a Python list of dicts, imported by seed_catalog.py
├── db/
│   └── init_collections.py      # NEW this phase — creates products ($jsonSchema+index) and price_points (timeseries) if they don't exist
├── requirements.txt              # add pymongo==4.17.0
└── tests/
    └── test_catalog_schema.py   # NEW this phase (Wave 0) — validates seed data against the schema, validates idempotency
```

**Structure rationale:** Keeping `catalog_data.py` (pure data) separate from `seed_catalog.py` (script logic) means the curated product list can be reviewed/diffed on its own, and re-run cleanly once Pitch Black's real data lands post-release (D-02) without touching script logic. `db/init_collections.py` is separated from the seed script because collection creation (with validator/timeseries options) is a one-time, idempotent-by-check operation (`if collection not in db.list_collection_names()`), distinct from the recurring idea of "seed/update the catalog contents."

### Pattern 1: Create-if-not-exists for validated/time-series collections

**What:** Check `db.list_collection_names()` before calling `create_collection()` — MongoDB raises an error if you call `create_collection()` on a name that already exists, and neither the `$jsonSchema` validator nor `timeseries` options can be retrofitted onto an already-existing plain collection.
**When to use:** Always, for both `products` and `price_points` in this phase — the init script must be safe to re-run.
**Example:**
```python
# db/init_collections.py
# Source: MongoDB official docs (Time Series Collections, Schema Validation) — see Sources
from pymongo import MongoClient, ASCENDING

def init_collections(db):
    if "products" not in db.list_collection_names():
        db.create_collection(
            "products",
            validator={
                "$jsonSchema": {
                    "bsonType": "object",
                    "required": ["set_name", "product_type", "language", "display_name", "required_keywords"],
                    "properties": {
                        "set_name": {"bsonType": "string"},
                        "product_type": {
                            "enum": ["booster_pack", "booster_box", "etb", "booster_bundle"]
                        },
                        "language": {"bsonType": "string", "enum": ["en"]},
                        "release_date": {"bsonType": ["date", "null"]},
                        "msrp": {"bsonType": ["double", "int", "null"]},
                        "image_url": {"bsonType": ["string", "null"]},
                        "display_name": {"bsonType": "string"},
                        "required_keywords": {
                            "bsonType": "array",
                            "items": {"bsonType": "string"},
                        },
                    },
                }
            },
            validationLevel="strict",
            validationAction="error",
        )
        db.products.create_index(
            [("set_name", ASCENDING), ("product_type", ASCENDING)]
        )

    if "price_points" not in db.list_collection_names():
        db.create_collection(
            "price_points",
            timeseries={
                "timeField": "ts",
                "metaField": "product_id",
                "granularity": "hours",
            },
        )
```

### Pattern 2: Idempotent bulk seed via natural-key upsert

**What:** Build each catalog document with a deterministic `_id` (slug), then `bulk_write` a list of `UpdateOne(filter, {"$set": doc}, upsert=True)` — safe to re-run any number of times, and naturally supports the Pitch Black "seed now, correct later" workflow from D-02.
**When to use:** Always, for catalog seeding — never `insert_many`, which duplicates on re-run.
**Example:**
```python
# scripts/seed_catalog.py
# Source: PyMongo official docs (Bulk Write Operations) — see Sources
from pymongo import UpdateOne

def seed_catalog(db, catalog_data: list[dict]):
    ops = []
    for product in catalog_data:
        slug = f"{product['set_name']}_{product['product_type']}".lower().replace(" ", "-")
        product["_id"] = slug
        ops.append(UpdateOne({"_id": slug}, {"$set": product}, upsert=True))
    if ops:
        result = db.products.bulk_write(ops)
        print(f"matched={result.matched_count} upserted={len(result.upserted_ids)} modified={result.modified_count}")
```

### Pattern 3: Compound index matching the phase's own query requirement

**What:** The phase's success criteria explicitly requires the catalog be "queryable by set and product type" — a single compound index `{set_name: 1, product_type: 1}` supports queries on `set_name` alone, or `set_name` + `product_type` together (MongoDB's prefix-matching rule for compound indexes), without needing two separate indexes.
**When to use:** Create this index as part of `init_collections.py`, not deferred to a later phase.
**Example:** (shown inline in Pattern 1's `db.products.create_index(...)` call above)

### Anti-Patterns to Avoid

- **Creating `products` and `price_points` as plain collections first, planning to "add time-series later":** MongoDB has no supported path to convert an existing plain collection into a time-series collection — `timeseries` options are creation-time-only. Get this right in Phase 2, even though `price_points` stays empty until Phase 3.
- **Using `insert_many` or bare `insert_one` in the seed script:** Not idempotent — re-running the script (needed for the Pitch Black post-release correction per D-02) duplicates every document. Always upsert by natural key.
- **Relying on auto-generated ObjectId `_id` with a separate uniqueness check in application code:** Works, but is strictly more code than a deterministic slug `_id`, which gets upsert idempotency "for free" via MongoDB's own `_id` uniqueness guarantee.
- **Hardcoding the MongoDB connection string in the seed script:** Follow the same `.env` + `python-dotenv` pattern already established in Phase 1 for eBay credentials — never commit a real `MONGODB_URI`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|--------------|-----|
| Idempotent upsert-by-key | A custom "find, then insert-or-update" two-step function | `pymongo.UpdateOne(filter, update, upsert=True)` inside `bulk_write` | Atomic at the DB layer — no time-of-check/time-of-use race, and it's a single documented, battle-tested API rather than hand-rolled logic |
| Document shape enforcement | A Python-side validation function (dataclass/manual `if` checks) called only from the seed script | MongoDB's native `$jsonSchema` validator at `create_collection` time | Enforced regardless of which script or tool writes to the collection later (matching module, a future admin script, `mongosh`) — app-only validation is trivially bypassed |
| Price history storage shape | A `history: [...]` array field appended to each product document, or a hand-rolled bucketing scheme | MongoDB native `timeseries` collection type | MongoDB handles bucketing, compression, and time-range query optimization natively; a hand-rolled array field grows unbounded and loses all of these query optimizations (already flagged as an anti-pattern in `.planning/research/ARCHITECTURE.md`) |
| Product image hosting | Download + re-host images through the project's own storage/CDN | Direct `image_url` reference to Pokemon Center/TCGplayer CDN (per D-08) | Avoids building file-storage infrastructure the v1 scope explicitly excludes; the tradeoff (link-rot risk if the retailer restructures URLs) was explicitly accepted by the user in D-08 |

**Key insight:** Every "don't hand-roll" item here has an existing, purpose-built primitive at the MongoDB or PyMongo layer — this phase should not write any custom persistence logic beyond composing these primitives and the curated data itself.

## Common Pitfalls

### Pitfall 1: Time-series collection options are creation-time-only

**What goes wrong:** A team creates `price_points` as a plain collection during early development (e.g., "we'll figure out time-series later"), then discovers in Phase 3 that MongoDB provides no supported migration path from a plain collection to a `timeseries` collection — the only fix is dropping and recreating the collection, losing any data already written.
**Why it happens:** It's easy to defer "the time-series part" since `price_points` has no data yet in this phase, and creating a plain collection requires zero decisions up front.
**How to avoid:** Create `price_points` with its final `timeseries` options (`timeField`, `metaField`, `granularity`) in this phase, even though it will be empty until Phase 3 writes to it. This is explicitly listed in this phase's success criteria ("reserves fields for... time-series history").
**Warning signs:** A `price_points` collection exists but `db.price_points.options()` in `mongosh` shows no `timeseries` key.

### Pitfall 2: MSRP/product-lineup data for a pre-release set (Pitch Black) is provisional

**What goes wrong:** Pitch Black's catalog entries are seeded from pre-release announcement data (per D-02), but pre-release MSRP/pack-count figures sometimes shift slightly between announcement and actual retail release (packaging changes, regional pricing differences, last-minute SKU changes are historically not uncommon for TCG products).
**Why it happens:** Pre-release marketing material is the only source available before July 17, 2026; official Pokemon Center/TCGplayer listings for the finalized SKUs may not exist yet at seeding time.
**How to avoid:** Tag Pitch Black's catalog documents (or add a lightweight `verified: false` / `verified_at: null` field) so a follow-up task can be tracked to re-confirm this specific set's data after 2026-07-17, exactly as D-02 specifies. Do not let this silently fall out of scope once the phase is marked complete.
**Warning signs:** No tracked follow-up item exists for "verify Pitch Black catalog data post-release" after this phase closes.

### Pitfall 3: `$jsonSchema` `validationLevel: "strict"` can block legitimate corrections

**What goes wrong:** If the validator schema is too rigid (e.g., requires `release_date` to be a concrete `date` and rejects `null`), the Pitch Black pre-release documents (which may have provisional/estimated release info) either fail to seed or force a workaround.
**Why it happens:** `"strict"` validation applies to every insert and update, including the exact kind of "seed now, correct later" update this phase's D-02 requires.
**How to avoid:** Explicitly allow `null` for fields that may be provisional at seed time (see the `bsonType: [..., "null"]` pattern in the Pattern 1 code example) rather than making every field strictly required with a single concrete type.
**Warning signs:** The seed script throws a schema validation error specifically when seeding Pitch Black but not the three already-released sets.

### Pitfall 4: `booster_bundle` accidentally matched/confused with `booster_box` or `booster_pack` downstream

**What goes wrong:** Because `booster_bundle` is a newly-introduced product type (D-06) not present in the original ARCHITECTURE.md schema proposal, a naive `required_keywords` design (e.g., just `["booster", set_name]`) would match bundle, box, and pack listings identically, defeating the entire purpose of D-06.
**Why it happens:** "Bundle" and "box"/"pack" titles on eBay often share most keywords (set name, "booster") and differ mainly in explicit pack-count language ("6 pack", "bundle") which is easy to omit from a first-pass keyword list.
**How to avoid:** This phase should design `required_keywords` per product type with explicit disambiguating terms even though matching itself is Phase 4's job — e.g., booster_bundle keywords should include `"bundle"` (and optionally a pack-count synonym), while booster_box keywords should include `"box"` or `"display"`. Document this choice now so Phase 4 doesn't have to re-derive it.
**Warning signs:** Two different `product_type` catalog entries for the same set share an identical `required_keywords` list.

### Pitfall 5: Non-idempotent seeding causes catalog duplication

**What goes wrong:** If the seed script uses `insert_many` (or omits `upsert=True`), running it a second time — which is expected behavior per D-02's "seed now, correct Pitch Black later" workflow — creates duplicate catalog entries for the same product.
**Why it happens:** `insert_many`/plain `insert_one` are the "obvious" first API to reach for; the idempotency requirement is easy to overlook for a script expected to "just run once."
**How to avoid:** Use the `bulk_write` + `UpdateOne(upsert=True)` pattern from Pattern 2 above, keyed on a deterministic slug `_id`, from the very first version of the seed script — do not treat idempotency as a later hardening pass.
**Warning signs:** `db.products.countDocuments({})` returns more than the expected ~15-16 after re-running the seed script.

## Curated Catalog Reference Data

Web-researched product data for the 4 in-scope sets, current as of 2026-07-13. **Confidence and provenance vary per field — see tags.** This is reference data for the planner/seed-script author, not a final locked dataset; reasonable diligence was applied per CONTEXT.md's "Claude's Discretion" note, not an exhaustive sourcing audit.

| Set | product_type | Release Date | MSRP | Source/Confidence |
|-----|--------------|--------------|------|---------------------|
| Chaos Rising (ME04) | etb | 2026-05-22 | $49.99 | `[CITED: pokemon.com product showcase / amazon.com listing]` |
| Chaos Rising (ME04) | booster_box | 2026-05-22 | $161.64 (one source said ~$144 — conflicting) | `[ASSUMED]` — conflicting figures found, confirm at seed time |
| Chaos Rising (ME04) | booster_bundle | 2026-05-22 | ~$26.94 (pattern-matched to other sets, not directly confirmed) | `[ASSUMED]` |
| Chaos Rising (ME04) | booster_pack | 2026-05-22 | ~$4.49 (pattern-matched) | `[ASSUMED]` |
| Perfect Order (ME03) | etb | 2026-03-27 | $49.99 | `[CITED: pokemoncenter.com / gamestop.com listing]` |
| Perfect Order (ME03) | booster_box | 2026-03-27 | $161.64 | `[CITED: pokemoncenter.com official listing]` |
| Perfect Order (ME03) | booster_bundle | 2026-03-27 | $26.94 | `[CITED: pittpokeresearch.com set price list]` |
| Perfect Order (ME03) | booster_pack | 2026-03-27 | ~$4.49 (pattern-matched) | `[ASSUMED]` |
| Ascended Heroes (ME) | etb | 2026-01-30 (ETB itself released 2026-02-20) | $49.99 | `[CITED: pokemoncenter.com / bestbuy.com listing]` |
| Ascended Heroes (ME) | booster_box | 2026-01-30 | ~$161.64 (not directly confirmed — inferred by pattern-match to Perfect Order/Pitch Black, same block, same 36-pack count) | `[ASSUMED]` — needs direct confirmation at seed time |
| Ascended Heroes (ME) | booster_bundle | released 2026-04-24 | $26.94 | `[CITED: pokemoncenter.com official listing]` |
| Ascended Heroes (ME) | booster_pack | 2026-01-30 | ~$4.49 (pattern-matched) | `[ASSUMED]` |
| Pitch Black (ME05) | etb | 2026-07-17 (pre-release; verify post-release per D-02) | $49.99 | `[ASSUMED]` — pre-release announcement data |
| Pitch Black (ME05) | booster_box | 2026-07-17 (pre-release; verify post-release per D-02) | $161.64 | `[ASSUMED]` — pre-release announcement data, but consistent across sources |
| Pitch Black (ME05) | booster_bundle | 2026-07-17 (pre-release; verify post-release per D-02) | $26.94 | `[ASSUMED]` — pre-release announcement data |
| Pitch Black (ME05) | booster_pack | 2026-07-17 (pre-release; verify post-release per D-02) | ~$4.49 | `[ASSUMED]` — pre-release announcement data |

**Excluded per D-05 (standard-retail only):** Pokemon Center-exclusive ETB variants (11-pack versions with extra promo cards) exist for Chaos Rising, Perfect Order, and Ascended Heroes — do NOT seed these as separate catalog entries. Build & Battle boxes (confirmed to exist for Pitch Black, likely for all sets) are also excluded.

**image_url sourcing pattern:** TCGplayer product-image CDN URLs follow a discoverable, predictable format: `https://tcgplayer-cdn.tcgplayer.com/product/{tcgplayer_product_id}_in_1000x1000.jpg` `[CITED: TCGplayer API docs — catalog_getproductmedia, community.tcgplayer.com/t/image-url-from-catalog-products-productid]`. TCGplayer product IDs discovered during this research: Chaos Rising ETB = 684450; Perfect Order booster box = 672394; Perfect Order booster pack = 672398; Ascended Heroes booster bundle = 668541. **The remaining ~12 products' TCGplayer IDs were not resolved in this research pass** — the seed-script-writing task should look up each remaining product's TCGplayer page to extract its numeric product ID before finalizing `image_url` values (a short, bounded task — TCGplayer product URLs embed the ID directly, e.g. `tcgplayer.com/product/672394/...`).

## Code Examples

### Full catalog document shape (combines ARCHITECTURE.md's proposal with D-04/D-06/D-07 additions)

```python
# scripts/catalog_data.py
CATALOG = [
    {
        "set_name": "Perfect Order",
        "product_type": "booster_box",       # booster_pack | booster_box | etb | booster_bundle
        "language": "en",
        "release_date": "2026-03-27",         # convert to datetime before insert
        "msrp": 161.64,
        "image_url": "https://tcgplayer-cdn.tcgplayer.com/product/672394_in_1000x1000.jpg",
        "display_name": "Pokemon TCG: Mega Evolution—Perfect Order Booster Display Box (36 Packs)",
        "required_keywords": ["perfect order", "booster box", "display"],
    },
    # ... 15 more entries across the 4 sets x up to 4 product types
]
```

### Verifying the reserved time-series collection (manual smoke check)

```python
# Source: MongoDB official docs pattern (db.<collection>.options())
db = client["pokemonview"]
print(db.command("listCollections", filter={"name": "price_points"}))
# expect: cursor.firstBatch[0].options.timeseries == {"timeField": "ts", "metaField": "product_id", "granularity": "hours"}
```

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|----------------|
| A1 | Chaos Rising booster box MSRP is $161.64 (one conflicting source said ~$144) | Curated Catalog Reference Data | Low — MSRP is a reference field only (D-04), not used in core pricing logic; wrong value is a display-accuracy issue, not a functional bug |
| A2 | Ascended Heroes standard booster box MSRP is ~$161.64 (pattern-inferred, not directly confirmed) | Curated Catalog Reference Data | Low — same as A1; also risk that this specific product simply doesn't have a "standard" (non-exclusive) booster box release, which would mean this catalog entry shouldn't exist at all — worth a quick direct-confirmation pass before seeding |
| A3 | All four sets' single booster_pack MSRP is ~$4.49 (pattern-matched from Pitch Black's confirmed per-pack math, not independently confirmed per set) | Curated Catalog Reference Data | Low — reference field only |
| A4 | Pitch Black's full pre-release product lineup (booster box, bundle, ETB, pack) and MSRPs will match what actually ships on 2026-07-17 | Curated Catalog Reference Data | Medium — if pricing or pack composition changes at actual release, seeded data becomes stale until the D-02-mandated post-release verification pass runs; if that follow-up is skipped, users could see incorrect MSRP display for the newest/most-hyped set |
| A5 | `pymongo` package is legitimate despite `[SUS]` verdict from automated legitimacy check | Package Legitimacy Audit | Low — verdict is a false positive from missing download telemetry, not an actual red flag (official `mongodb/mongo-python-driver` repo); still requires `checkpoint:human-verify` per protocol |

## Open Questions

1. **Are Ascended Heroes' and Chaos Rising's exact standard booster-box MSRPs correct?**
   - What we know: Perfect Order and Pitch Black both confirm $161.64 for a 36-pack box; Ascended Heroes has no directly-confirmed booster box MSRP in this research pass, and Chaos Rising has two conflicting figures ($144 vs $161.64).
   - What's unclear: Whether Ascended Heroes even has a "standard" (non-Pokemon-Center-exclusive) booster box SKU, and which Chaos Rising figure is accurate.
   - Recommendation: A quick direct-confirmation web check (or Pokemon Center product page fetch) for these two specific values before finalizing the seed script — bounded, low-cost verification, not a blocker for planning.

2. **Which TCGplayer product IDs correspond to the ~12 catalog products not yet resolved in this research pass?**
   - What we know: The `{id}_in_1000x1000.jpg` CDN pattern is confirmed and works for the 4 products whose IDs were found during research.
   - What's unclear: The exact numeric IDs for the remaining products (e.g., Chaos Rising booster box/bundle/pack, Ascended Heroes booster box/pack, all of Pitch Black).
   - Recommendation: Treat "look up remaining TCGplayer product IDs" as an explicit task in the seed-script plan, not something to guess/hallucinate — each ID is directly visible in the corresponding TCGplayer product page URL.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|--------------|-----------|---------|----------|
| MongoDB (Atlas or local) | Running the seed script / creating collections | ✗ (no `mongod`, `mongosh`, or Docker daemon found on this machine) | — | MongoDB Atlas free tier (M0), already recommended in `.claude/CLAUDE.md`'s stack research — no local install required; alternatively `brew install mongodb-community` (Homebrew is available: v6.0.6) for a fully local dev instance |
| pymongo | Seed script, collection creation | ✗ (not yet installed — `pip3 show pymongo` returns not found) | 4.17.0 confirmed on PyPI | `pip install pymongo==4.17.0` — no fallback needed, trivial install |
| Docker | N/A this phase | ✗ (`docker info` fails — no daemon running) | — | Not required for this phase; only relevant if choosing local MongoDB-via-Docker over Atlas or Homebrew |

**Missing dependencies with no fallback:**
- None — MongoDB has two viable fallback paths (Atlas M0 free tier, or local Homebrew install), and pymongo is a trivial pip install.

**Missing dependencies with fallback:**
- MongoDB instance itself — the planner must include a task to either provision an Atlas M0 cluster (recommended, matches `.claude/CLAUDE.md`'s stated stack choice, requires a `MONGODB_URI` in `.env`) or `brew install mongodb-community` for local dev, before the seed script can be run and verified.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x (not yet installed — Wave 0 gap) |
| Config file | none — see Wave 0 |
| Quick run command | `pytest tests/test_catalog_schema.py -x` |
| Full suite command | `pytest tests/ -x` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|---------------------|--------------|
| CATALOG-01 | Catalog contains every in-scope product (4 sets × up to 4 product types, ~15-16 docs, excluding D-05 exclusions) as a distinct entry | integration (requires live/test MongoDB) | `pytest tests/test_catalog_schema.py::test_catalog_completeness -x` | ❌ Wave 0 |
| CATALOG-01 | Re-running the seed script does not create duplicate documents | integration | `pytest tests/test_catalog_schema.py::test_seed_idempotent -x` | ❌ Wave 0 |
| CATALOG-02 | Every catalog document has set_name, product_type, release info, msrp, image_url per the `$jsonSchema` validator | unit/integration | `pytest tests/test_catalog_schema.py::test_schema_validator_rejects_malformed -x` | ❌ Wave 0 |
| CATALOG-02 | Catalog is queryable by set and product_type via the compound index | integration | `pytest tests/test_catalog_schema.py::test_query_by_set_and_type -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_catalog_schema.py -x`
- **Per wave merge:** `pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_catalog_schema.py` — covers CATALOG-01, CATALOG-02 (completeness, idempotency, schema validation, query pattern)
- [ ] `tests/conftest.py` — shared fixture for a test MongoDB connection (point at a local/Atlas test database, or use `mongomock`/an ephemeral test DB — decide at plan time based on whether a real MongoDB instance is provisioned per Environment Availability above)
- [ ] Framework install: `pip install pytest==8.4.2` — no test infrastructure exists in the repo yet

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|----------------|---------|---------------------|
| V2 Authentication | No | This phase has no user-facing auth surface — it's an internal seed script |
| V3 Session Management | No | No sessions in scope this phase |
| V4 Access Control | No | No access-control surface — the catalog is not yet exposed via any API (that's Phase 5) |
| V5 Input Validation | Yes | The `$jsonSchema` MongoDB validator (Code Examples above) is the input-validation control for this phase — enforced at the DB layer for every write, including the seed script's own writes |
| V6 Cryptography | No | No new secrets/crypto operations introduced this phase beyond the existing `.env`-based `MONGODB_URI` pattern already established for eBay credentials in Phase 1 |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|------------------------|
| NoSQL injection via unsanitized query construction | Tampering | Not a live risk in this phase (the seed script's data is hardcoded curated content, not external/user input), but the `$jsonSchema` validator + parameterized pymongo query construction (never building raw query dicts from string concatenation) establishes the pattern that Phase 5's read API must continue to follow once user-facing search (SEARCH-01) is built |
| Hardcoded credentials in source | Information Disclosure | Reuse the `.env` + `python-dotenv` pattern already established in Phase 1 for eBay credentials — the `MONGODB_URI` (which may embed a username/password for Atlas) must never be committed |

## Sources

### Primary (HIGH confidence)
- None available this session — no Context7 MCP tool was available despite server instructions indicating it should be; all findings fall back to WebSearch (see Secondary below)

### Secondary (MEDIUM confidence)
- [Time Series Data - PyMongo Driver - MongoDB Docs](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/data-formats/time-series/) — official docs, PyMongo time-series creation syntax
- [Set Granularity for Time Series Data - Database Manual - MongoDB Docs](https://www.mongodb.com/docs/manual/core/timeseries/timeseries-granularity/) — official docs, granularity bucket-window behavior
- [Bulk Write Operations - PyMongo Driver - MongoDB Docs](https://www.mongodb.com/docs/languages/python/pymongo-driver/current/crud/bulk-write/) — official docs, UpdateOne/upsert pattern
- [Specify JSON Schema Validation - Database Manual - MongoDB Docs](https://www.mongodb.com/docs/manual/core/schema-validation/specify-json-schema/) — official docs, `$jsonSchema`/validationLevel/validationAction
- [Compound Indexes - Database Manual - MongoDB Docs](https://www.mongodb.com/docs/manual/core/indexes/index-types/index-compound/) — official docs, ESR rule and compound-index query support
- [Pokémon TCG: Mega Evolution—Perfect Order Booster Display Box — Pokémon Center official listing](https://www.pokemoncenter.com/product/10-10380-119/pokemon-tcg-mega-evolution-perfect-order-booster-display-box-36-packs) — official retailer, $161.64 booster box MSRP
- [Everything We Know About Pokémon TCG: Pitch Black — TCGplayer](https://www.tcgplayer.com/content/article/Everything-We-Know-About-Pok%C3%A9mon-TCG-Pitch-Black/60927875-3793-4a7d-b9b0-093f117f6d53/) — Pitch Black pre-release lineup/date
- [The Pokémon TCG: Mega Evolution—Pitch Black Expansion Arrives July 17, 2026 — Pokemon.com](https://www.pokemon.com/us/pokemon-news/the-pokemon-tcg-mega-evolution-pitch-black-expansion-arrives-july-17-2026) — official release-date announcement
- [List All Product Media Types - TCGplayer API docs](https://docs.tcgplayer.com/reference/catalog_getproductmedia) — TCGplayer CDN image URL pattern
- [Image URL from catalog/products/{productId} — TCGplayer Developer Community](https://community.tcgplayer.com/t/image-url-from-catalog-products-productid/44) — confirms `_in_1000x1000` high-res suffix pattern

### Tertiary (LOW confidence)
- [Pokémon TCG Chaos Rising Set Revealed — Trackalacker](https://www.trackalacker.com/articles/news/pokemon-tcg-chaos-rising-set-revealed-release-date-products-and-where-to-preorder) — used for Chaos Rising booster box MSRP, conflicts with another figure (flagged in Assumptions Log A1)
- [Ascended Heroes Quick Facts — TCGplayer seller blog](https://seller.tcgplayer.com/blog/ascended-heroes-quick-facts) — used for Ascended Heroes lineup detail, standard booster box MSRP not directly confirmed (flagged A2)
- [PriceCharting Pokemon Ascended Heroes / Perfect Order / Chaos Rising set pages](https://www.pricecharting.com/game/pokemon-ascended-heroes/booster-box) — secondary-market price tracker, used only for cross-referencing, not MSRP source of record
- pymongo `unknown-downloads` legitimacy-check signal — see Package Legitimacy Audit; treated as a false positive but disclosed per protocol

## Metadata

**Confidence breakdown:**
- Standard stack (PyMongo/MongoDB technical patterns): MEDIUM — no Context7 access this session, but every technical claim is corroborated by official `mongodb.com/docs` or `pymongo.readthedocs.io` URLs returned directly in WebSearch results, not just community blog posts
- Architecture (schema/collection design): MEDIUM-HIGH — builds directly on the already-vetted `.planning/research/ARCHITECTURE.md` proposal, extended only with D-04/D-06/D-07's explicitly user-decided additions
- Catalog content (MSRP/product lineup/image sourcing): MEDIUM overall, LOW for several specific pattern-inferred fields (see Assumptions Log) — Pitch Black data is explicitly provisional per D-02 and requires a post-release verification follow-up

**Research date:** 2026-07-13
**Valid until:** Catalog content (MSRP/lineup) should be treated as valid only until 2026-07-17 (Pitch Black release) for that specific set — re-verify per D-02 immediately after. Technical MongoDB/PyMongo patterns are stable and valid for the standard 30-day research window.

---
*Research for: Phase 2 - Product Catalog & Data Model*
*Researched: 2026-07-13*
