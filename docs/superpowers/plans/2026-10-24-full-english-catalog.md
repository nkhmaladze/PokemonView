# Full English Sealed Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Grow the catalog from 15 curated products (4 sets) to every English booster pack, booster box, ETB and booster bundle from Base Set (1999) to the newest set, including 1st Edition / Shadowless / Unlimited versions (about 300–400 entries), without breaking matching, the API or the UI.

**Architecture:** Product identity gains an `edition` dimension (one slug function shared by seed, matcher and worker). A build script (`scripts/build_catalog.py`) turns TCGplayer's public product lists (tcgcsv.com) into a committed data module (`scripts/catalog_generated.py`); the 15 curated entries are never regenerated. The matcher gains `excluded_keywords`, accent/"and" folding and edition-aware phrases; the API orders sets by release date instead of a hardcoded list; the UI swaps the set chip row for a dropdown.

**Tech Stack:** Python 3.12, Flask, PyMongo (real Atlas test DB `pokemonview_test`), rapidfuzz, pytest; React 19 + Vite + Vitest.

**Spec:** none separate. The user opted out of the brainstorming questions ("make a plan and execute"); the decisions are in the Decisions section below and come from the conversation of 2026-10-24 (scope: only the four main product types, English only, all editions, since 1999).

## Global Constraints

- English only; `language: "en"`; product types limited to `booster_pack | booster_box | etb | booster_bundle`.
- The 15 curated entries (Pitch Black, Chaos Rising, Perfect Order, Ascended Heroes) keep their exact slugs, msrp, keywords and `verified` flags. Their `_id`s must not change (production data is keyed on them).
- Every entry carries a TCGplayer CDN `image_url` (`https://tcgplayer-cdn.tcgplayer.com/product/<id>_in_1000x1000.jpg`); images stay hotlinked (user decision, `product_images_hotlinked` memory).
- Unknown MSRP is `None`, never invented. The UI already renders `—` for it.
- No commits, pushes, production DB writes or deploys by me. Production seeding and pushing are handed to the user (permission hook + standing rule); commit only when asked.
- Never read or print `.env*`; tests load credentials through `load_dotenv()` inside fixtures.
- `scripts/catalog_data.py` stays side-effect free (no network or DB at import).
- Run the whole suite (`pytest`, `npm test`) before calling any task done; report every failure by name.

## Decisions (mine; the user can overrule)

- Source: tcgcsv.com mirror of TCGplayer (category 3). Chosen because product id, name and image come from one record, so the image can never point at the wrong product.
- `edition` ∈ `None | "1st Edition" | "Shadowless" | "Unlimited"`. A set only gets editions if TCGplayer lists more than one edition for it; "Shadowless" means Shadowless Unlimited (Base Set's 1st Edition is shadowless by nature).
- Slug: `"{set} {edition}"` + `_` + type, lowercased, `&`→`and`, accents folded, other punctuation→`-`. With `edition=None` it reproduces the current slugs byte for byte.
- Set order in the API: newest set first (earliest product `release_date` per set, descending, name as tiebreak); inside a set, edition (1st, Shadowless, Unlimited) then type (box, ETB, bundle, pack).
- Generated entries use `verified=True` unless the set's release date is in the future.
- Excluded from the catalog: promos, trainer kits, McDonald's/POP/Trick-or-Trade/Battle Academy groups, supplemental groups (Trainer Gallery, Shiny Vault, Classic Collection), Pokemon Center exclusives, cases, sleeved/code-card/blister/art-bundle/tin/collection/theme-deck products.
- Not done (flagged to the user instead): TTL on `active_listings`, self-hosted images.

## Review Focus

1. "Pokemon Sword & Shield Base Set Booster Box" must resolve to the Sword & Shield entry, never to vintage Base Set (and "Scarlet & Violet Base Set" likewise). Task 7.
2. Base Set titles: "1st Edition" → 1st Edition; "Shadowless" (with or without "1st Edition") → the right shadowless entry; no edition words → Unlimited. Task 2 and 7.
3. Superstring sets: "Base Set 2" ≠ "Base Set", "Team Rocket Returns" ≠ "Team Rocket", "Platinum Rising Rivals" ≠ "Platinum". Task 7.
4. `products` documents written before this change (no `edition` / `excluded_keywords`) still list, sort and match. Tasks 1, 2, 4.
5. A set the old hardcoded `SET_ORDER` never heard of, and products with `msrp: None`, must not 500 the list endpoint. Task 4.

---

## File Structure

- Create `scripts/catalog_slug.py`: the one slug function.
- Create `scripts/build_catalog.py`: TCGplayer → catalog entries (pure functions + CLI).
- Create `scripts/catalog_generated.py`: generated data (`GENERATED_CATALOG`), never hand-edited.
- Modify `scripts/catalog_data.py`: `CURATED_CATALOG` + `CATALOG = CURATED_CATALOG + GENERATED_CATALOG`; docstring fields.
- Modify `scripts/seed_catalog.py`, `scripts/matching.py`, `scripts/ingest_worker.py`, `db/init_collections.py`, `api/services/catalog_service.py`.
- Modify `frontend/src/components/FilterChips.jsx`, `ProductRow.jsx`, `pages/CatalogPage.jsx` (+ their tests).
- Create tests: `tests/test_catalog_slug.py`, `tests/test_build_catalog.py`, `tests/fixtures/tcgcsv/`; extend `tests/test_catalog_schema.py`, `test_matching.py`, `test_ingest_worker.py`, `test_catalog_service.py`, `test_catalog_data.py`, `test_api_products.py`.

---

### Task 1: Edition-aware identity (slug, schema, index, seed)

**Files:**
- Create: `scripts/catalog_slug.py`, `tests/test_catalog_slug.py`
- Modify: `scripts/seed_catalog.py`, `scripts/matching.py` (`_product_slug`), `scripts/ingest_worker.py` (`product_ref` in `run_ingestion_once`), `db/init_collections.py`, `tests/test_catalog_schema.py`

**Interfaces:**
- Produces: `product_slug(product: dict) -> str` in `scripts.catalog_slug`; `EDITIONS = ("1st Edition", "Shadowless", "Unlimited")`.
- Produces: `products` validator accepts optional `edition` (enum above or null) and `excluded_keywords` (array of strings); unique index on `(set_name, edition, product_type)`.

- [ ] **Step 1: Write failing tests** in `tests/test_catalog_slug.py`: `test_slug_matches_legacy_formula_for_curated_entries` (for every entry in the current `CATALOG`, `product_slug(e) == f"{e['set_name']}_{e['product_type']}".lower().replace(" ", "-")`); `test_slug_includes_edition` (`Base Set`/`1st Edition`/`booster_box` → `"base-set-1st-edition_booster_box"`); `test_slug_edition_none_and_missing_are_identical`; `test_slug_folds_ampersand_and_accents` (`"Sword & Shield"` → `"sword-and-shield_etb"`, `"Pokémon GO"` → `"pokemon-go_etb"`). In `tests/test_catalog_schema.py` add: two Base Set booster boxes with editions `"1st Edition"` and `"Unlimited"` both insert; a duplicate `(set_name, edition, product_type)` raises `DuplicateKeyError`; `init_collections` drops a pre-existing legacy `set_name_1_product_type_1` unique index; `seed_catalog` writes `edition: None` and `excluded_keywords: []` onto curated entries.
- [ ] **Step 2: Run and see them fail** — `pytest tests/test_catalog_slug.py tests/test_catalog_schema.py -v` → ImportError / assertion failures.
- [ ] **Step 3: Implement** `product_slug` (NFKD-fold accents, lowercase, `&`→`and`, runs of non-alphanumerics→`-`, strip `-`, join edition into the set part, `_` before the type); call it from `seed_catalog` (and `doc.setdefault("edition", None)`, `doc.setdefault("excluded_keywords", [])`), `matching._product_slug`, and `ingest_worker` `product_ref`; add the two validator properties and the new unique index plus the legacy-index drop to `init_collections`.
- [ ] **Step 4: Run** the two files plus `pytest tests/test_ingest_worker.py tests/test_matching.py -q` → all pass (slugs unchanged for curated entries).

### Task 2: Matching — folding, exclusions, edition phrases

**Files:**
- Modify: `scripts/matching.py` (`normalize`, `match_listing`, `_canonical_phrase`), `tests/test_matching.py`

**Interfaces:**
- Consumes: `product_slug` (Task 1).
- Produces: catalog entries may carry `excluded_keywords: list[str]` (already normalized); `match_listing` ignores a candidate whose title contains any of them. `normalize("Pokémon GO Scarlet and Violet")` → `"pokemon go scarlet violet"`.

- [ ] **Step 1: Write failing tests** (monkeypatch `scripts.matching.CATALOG` with tiny catalogs): `test_normalize_folds_accents`; `test_normalize_drops_standalone_and_and_ampersand` (`"Scarlet & Violet"` and `"Scarlet and Violet"` normalize identically); `test_excluded_keyword_removes_candidate` (title containing an excluded phrase resolves to the other candidate); `test_entry_without_excluded_keywords_still_matches` (legacy entry, no key); `test_edition_entries_resolve_by_title` using a 3-entry Base Set booster-box catalog (1st Edition: required `["base set","booster box","1st edition"]`; Shadowless: required `[..., "shadowless"]`, excluded `["1st edition"]`; Unlimited: excluded `["1st edition","shadowless"]`): "base set 1st edition booster box"→1st, "base set shadowless 1st edition booster box"→1st, "base set shadowless booster box"→shadowless, "base set booster box"→unlimited; `test_canonical_phrase_includes_1st_and_shadowless_but_not_unlimited`.
- [ ] **Step 2: Run** `pytest tests/test_matching.py -v` → the new tests fail, old ones pass.
- [ ] **Step 3: Implement** the three changes; accent folding via `unicodedata`; `"and"` removed as a standalone word after punctuation stripping; `p.get("excluded_keywords", [])` in the Tier-1 comprehension; edition word appended in `_canonical_phrase` for `1st Edition`/`Shadowless`.
- [ ] **Step 4: Run** full `pytest tests/test_matching.py tests/test_ingest_worker.py -q` → green.

### Task 3: Edition-aware eBay search query

**Files:** Modify `scripts/ingest_worker.py` (`build_query`), `tests/test_ingest_worker.py`.

**Interfaces:** `build_query(product: dict) -> str`: `"Pokemon {set_name}[ 1st Edition| Shadowless] {type phrase}"`; Unlimited and `None` add nothing.

- [ ] **Step 1: Failing tests:** `test_build_query_adds_1st_edition`, `test_build_query_adds_shadowless`, `test_build_query_unlimited_and_none_unchanged` (`"Pokemon Chaos Rising Booster Box"` still produced for the curated entry).
- [ ] **Step 2: Run** → red. **Step 3: Implement** with an `EDITION_SEARCH_TERMS` dict next to `PRODUCT_TYPE_SEARCH_TERMS`. **Step 4: Run** `pytest tests/test_ingest_worker.py -q` → green.

### Task 4: API — release-date set order, no hardcoded sets, parallel price lookup

**Files:** Modify `api/services/catalog_service.py`, `tests/test_catalog_service.py`, `tests/test_api_products.py`, `tests/conftest.py` docstrings.

**Interfaces:** `list_products(db, filters)` signature unchanged. Ordering: set rank (earliest `release_date` of the set, descending; `None` last; name tiebreak), then edition rank (`1st Edition`, `Shadowless`, `Unlimited`, `None`), then type rank (`booster_box`, `etb`, `booster_bundle`, `booster_pack`). `SET_ORDER` is removed. Per-product `get_current_price` calls run in a `ThreadPoolExecutor(max_workers=16)`, preserving order.

- [ ] **Step 1: Failing tests:** `test_default_sort_order_is_newest_set_first` (expected order computed from `release_date`, groups contiguous); `test_set_unknown_to_old_set_order_does_not_raise` (insert two validator-valid product docs for sets "Zeta Test Set" 2030-01-01 and "Alpha Test Set" 2000-01-01 into `api_db.products`, assert Zeta first and no exception); `test_products_with_null_msrp_are_listed_and_sorted_by_type` ; `test_legacy_document_without_edition_field_lists` (insert a doc lacking `edition`/`excluded_keywords` via `api_db.products.insert_one`); `test_list_prices_match_sequential_lookup` (insert price points for three products, compare against `get_current_price`). Replace every hardcoded `15` with `len(CATALOG)` in `test_catalog_service.py`/`test_api_products.py`.
- [ ] **Step 2: Run** `pytest tests/test_catalog_service.py tests/test_api_products.py -v` → new tests red.
- [ ] **Step 3: Implement** (sort-key function built from the loaded product docs; thread pool for the price lookups; keep `InvalidProductTypeError` behaviour).
- [ ] **Step 4: Run** both files → green.

### Task 5: Frontend — set dropdown and lazy images

**Files:** Modify `frontend/src/components/FilterChips.jsx`, `FilterChips.test.jsx`, `pages/CatalogPage.jsx`, `CatalogPage.test.jsx`, `components/ProductRow.jsx`, `ProductRow.test.jsx`.

**Interfaces:** `FilterChips({ productType, onProductType, sets, setName, onSetName })` — `sets: string[]` in display order; renders the product-type chips plus `<select aria-label="Set">` whose first option "All sets" has value `""` and calls `onSetName(null)`. `SET_OPTIONS` export removed. `CatalogPage` derives `sets` from the loaded products (first-seen order). Thumbnails get `loading="lazy"` and `decoding="async"`.

- [ ] **Step 1: Failing tests** (Vitest): select lists "All sets" then the given sets in order; choosing a set calls `onSetName` with the raw name; choosing "All sets" calls `onSetName(null)`; `CatalogPage` with products from three sets filters correctly via the dropdown; `ProductRow` image has `loading="lazy"`.
- [ ] **Step 2:** `cd /Users/nkhmal/Desktop/PokemonView/frontend && npm test -- --run` → new tests red. **Step 3:** implement. **Step 4:** `npm test -- --run && npm run build` → green.

### Task 6: Catalog build script

**Files:**
- Create: `scripts/build_catalog.py`, `tests/test_build_catalog.py`, `tests/fixtures/tcgcsv/groups.json`, `tests/fixtures/tcgcsv/products_<groupId>.json` for groups 604, 1663, 23228, 2480, 1387, 1402 (sealed products only, trimmed from the cache in the scratchpad).

**Interfaces (all pure, no network except `fetch_cache`):**
- `classify_product(name: str, set_name: str) -> tuple[str, str | None] | None` → `(product_type, edition_tag)`. The deny list is applied to `name` with the set name removed (otherwise "Legendary Collection Booster Box" is rejected for containing "collection"). Deny words: case, display, sleeved, code card, pokemon center, blister, art bundle, theme deck, tin, collection, build, deck, set of, premium, plus, special, mini, exclusive, starter, lot, stadium, half, enhanced, 3-card, surprise, sam's club.
- When several products survive for one `(set, edition, type)` (ETB colour/Pokémon variants such as `[Koraidon]`/`[Miraidon]`, bundle `(LGS)`/`(Retail)`), prefer a name containing `(Retail)`, else the lowest productId; all collapsed names go into `report["collapsed"]`.
- `clean_set_name(group_name: str) -> str` (strips `SWSH01:`/`SV:`/`XY - ` style prefixes; block base sets map to the block name via an `OVERRIDES` dict keyed by groupId, which also holds `skip` entries and `match_phrase` overrides, e.g. the 151 set).
- `build_entries(groups: list[dict], products_by_group: dict[int, list[dict]], curated: list[dict], today: date) -> tuple[list[dict], dict]` → `(entries, report)`; skips groups whose cleaned set name is already curated; collapses same-`(set, edition, type)` variants to the lowest productId and records them in `report["collapsed"]`; lists ambiguous or empty groups in `report["unresolved"]`.
- `compute_excluded_keywords(entries: list[dict]) -> None` (in place): type exclusions (pack: `booster box`, `booster bundle`, `elite trainer box`, `display`; bundle: `booster box`, `elite trainer box`, `display`; box: `elite trainer box`, `booster bundle`; ETB: `booster box`, `booster bundle`), superstring-set exclusions, block-base exclusions (block bases: HeartGold SoulSilver, Black & White, XY, Sun & Moon, Sword & Shield, Scarlet & Violet, Mega Evolution, Diamond & Pearl, Platinum; a block spans from its base's release date to the next base's), and vintage "Base Set" excluding every block-base phrase; edition exclusions (Shadowless: `1st edition`; Unlimited: `1st edition`, `shadowless`).
- `render_module(entries: list[dict]) -> str` → source of `scripts/catalog_generated.py`.
- `fetch_cache(cache_dir: Path) -> None` downloads groups and per-group products with `User-Agent: Mozilla/5.0 PokemonView-catalog-build` (Python's default UA is rejected) and 0.2 s spacing; CLI: `python -m scripts.build_catalog --cache DIR`.

- [ ] **Step 1: Failing tests** on the fixtures (first sizing run over the real cache found about 348 entries: 139 packs, 114 boxes, 68 ETBs, 27 bundles): Obsidian Flames yields exactly box/bundle/ETB/pack with ids 501257/501263/501264/501256 and image URLs built from them; Hidden Fates yields only ETB and pack; XY's two ETB variants collapse to the lower id and appear in `report["collapsed"]`; "Legendary Collection Booster Box" is classified (set name stripped before the deny check); "Evolving Skies Half Booster Box" is rejected; Base Set yields 6 entries (1st Edition, Shadowless, Unlimited × box, pack) from groups 604 + 1663; Pokemon Center / Case / Code Card / Sleeved products never appear; a future-dated group gets `verified=False`; curated set names are skipped; `required_keywords` are already `normalize()`d (`"scarlet violet"` for Scarlet & Violet); `compute_excluded_keywords` puts every other Scarlet & Violet-block set phrase into the block base's list and every block-base phrase into vintage Base Set's list.
- [ ] **Step 2: Run** `pytest tests/test_build_catalog.py -v` → red. **Step 3: Implement.** **Step 4: Run** → green.

### Task 7: Generate the catalog and pin catalog-wide invariants

**Files:** Create `scripts/catalog_generated.py` (generated); modify `scripts/catalog_data.py`, `tests/test_catalog_data.py`, `tests/test_matching.py`.

**Interfaces:** `scripts.catalog_data.CATALOG` is the concatenation; entry schema adds `edition` and `excluded_keywords`; docstring documents both.

- [ ] **Step 1: Failing tests** (written before generating): `test_catalog_has_expected_scale` (`280 <= len(CATALOG) <= 420`); `test_slugs_are_unique`; `test_edition_values_valid_and_consistent` (every set with an edition has at least two); `test_every_entry_resolves_to_its_own_canonical_title` (for each entry, `normalize` of `"Pokemon {set_name} [{edition}] {type phrase}"` run through `match_listing` returns exactly that entry's slug — this is the collision detector); `test_review_focus_titles` parametrized over: SWSH/SV base-set titles vs vintage Base Set, the four Base Set edition cases, Base Set 2 / Team Rocket Returns / Platinum Rising Rivals titles, `"Pokémon GO"` accents, "and" vs "&"; `test_real_listing_fixture_curated_matches_unchanged` runs all 100 titles in `fixtures/ebay_listing_titles.json` and asserts any title that matched a curated product before (recorded by running the matcher at the pre-change commit via the curated-only list `CURATED_CATALOG`) still resolves to the same slug.
- [ ] **Step 2:** run `python -m scripts.build_catalog --cache <scratchpad>/tcgcsv` (cache already downloaded), review `report` (unresolved groups, collapsed variants, entry count per set/type matrix) and add `OVERRIDES` until sensible; write `scripts/catalog_generated.py`; rename the literal in `catalog_data.py` to `CURATED_CATALOG` and add the concatenated `CATALOG`.
- [ ] **Step 3:** `pytest tests/test_catalog_data.py tests/test_matching.py -v` → green; fix collisions by adjusting generator rules (not by hand-editing the generated file).
- [ ] **Step 4:** contact-sheet spot check: download 40 random generated images (all four types, all editions) into one labeled sheet in the scratchpad and look at it.

### Task 8: Whole-system verification

**Files:** none (scratchpad scripts only).

- [ ] **Step 1:** `pytest` (whole backend suite) → report counts and any failure by name; `cd frontend && npm test -- --run && npm run build`.
- [ ] **Step 2:** time `list_products` against a local app on `pokemonview_test` seeded with the full catalog (`create_app(..., db_name="pokemonview_test")`); expected: under 3 s from this machine (Fly↔Atlas will be faster). If not, reduce `max_workers` contention or revisit.
- [ ] **Step 3:** serve the built frontend against that local API with playwright-core + Brave (scratchpad `pw/`): assert row count equals `len(CATALOG)`, set dropdown works, Base Set shows three editions, no console errors, screenshot desktop and phone widths.
- [ ] **Step 4:** simulate one ingestion pass offline: run `run_matching_once` on the 100-title fixture against the full catalog in `matching_db` and time it; expected under 5 s.

### Task 9: Hand-off

- [ ] **Step 1:** update `scripts/catalog_data.py` docstring (generated vs curated, new fields) and the memory note `product_images_hotlinked` (now ~N images); add a memory describing how the catalog is built (`build_catalog`, cache location is the scratchpad so re-download) and the rollout order.
- [ ] **Step 2:** tell the user the rollout order: (1) review and commit; (2) `git push` so CI deploys API, worker and frontend; (3) only then `python -m scripts.seed_catalog` (seeding first would make the old API 500 on unknown sets). Also state: first ingestion run after deploy issues about N eBay calls per run (about N×6 per day versus the 5,000 limit).
