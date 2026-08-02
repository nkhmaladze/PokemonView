# Phase 4: Listing Matching & Price Normalization - Research

**Researched:** 2026-07-14
**Domain:** Deterministic + fuzzy title matching (RapidFuzz), keyword-based listing exclusion, per-run statistical outlier filtering, median-based time-series price aggregation — all in-process Python, extending Phase 3's ingestion worker
**Confidence:** MEDIUM (architecture/schema decisions are HIGH — grounded directly in this repo's own code and CONTEXT.md's locked decisions; scoring thresholds and exclusion keyword lists are LOW/ASSUMED — no live eBay listing data exists yet to tune against, `context7` MCP tools were unavailable this session so library-mechanics claims are WebSearch-sourced rather than fetched from canonical docs)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Match Confidence & Unmatched Listings**
- **D-01:** Matching is strict / precision-first. When a title is ambiguous or only weakly matches, the matcher should skip rather than guess.
- **D-02:** A listing that doesn't confidently match any catalog product is stored (not silently skipped) with a `match_status` (e.g. `"unmatched"`) so it's queryable and rules can be tuned later without re-pulling from eBay.
- **D-03:** A listing that plausibly matches more than one catalog product is treated as ambiguous/unmatched — never auto-resolved by picking the higher-confidence candidate.
- **D-04:** Extend the existing `ingestion_runs` per-run observability pattern (Phase 3) with match-rate counts (matched / unmatched / excluded) per run.

**Exclusion Handling (Lot/Bundle/Damaged/Counterfeit)**
- **D-05:** Excluded listings are kept in storage, flagged with an `exclusion_reason` (e.g. `"lot"`, `"damaged"`, `"counterfeit"`, `"outlier"`) — never hard-deleted.
- **D-06:** The three baseline exclusion categories from `PITFALLS.md` Pitfall 3 are sufficient for v1: multi-quantity/lot language, condition-negative language, counterfeit/replica signals.
- **D-07:** No manual-override tooling is built in this phase. Fix path for false positives/negatives is a direct MongoDB document edit.
- **D-08:** Condition-based exclusion triggers only on explicit/severe signals ("dented", "resealed", "opened", "empty box", "no cards") — not on minor/cosmetic language ("shelf wear", "corner ding").

**Price Aggregation into price_points**
- **D-09:** One aggregated `price_points` document per product per ingestion run (not one per listing).
- **D-10:** The aggregate represents the **median** of included listings.
- **D-11:** Zero included listings in a run → skip writing a point for that product (gap, not carry-forward).
- **D-12:** `item_price` and `total_price` in the aggregated point are each their **own independent median** across included listings.

**Outlier Filtering Sensitivity**
- **D-13:** Outlier cutoff is **2 standard deviations** from the rolling median.
- **D-14:** Too few included listings (e.g. only 1-2) → skip outlier filtering entirely, include what's there.
- **D-15:** Median/std-dev for outlier detection is computed from **just the current run's own included listings** — no rolling window.
- **D-16:** Statistically-excluded listings get `exclusion_reason="outlier"` — same flagging pattern as keyword exclusions.

### Claude's Discretion

- Exact matching implementation (keyword rule structure, RapidFuzz usage/thresholds if any) — `ARCHITECTURE.md`'s two-tier design (deterministic keyword rules first, fuzzy fallback second) is the starting point; precise scoring/thresholds are this research's job, as long as D-01's strict/precision-first stance holds.
- Exact field names/schema for `match_status`, `exclusion_reason`, and the new `ingestion_runs` count fields — follow existing schema conventions in `db/init_collections.py` and `scripts/ingest_worker.py`.
- Where in the pipeline exclusion checks run relative to matching (before/after).
- Specific keyword lists for each exclusion category beyond the three confirmed categories — reasonable diligence, not an exhaustive audit.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope. A manual-override *tool* was briefly considered and resolved to "direct MongoDB edit, no tooling" (D-07) — nothing was actually deferred to a future phase.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MATCH-01 | Raw eBay listing titles are matched to catalog products via keyword rules | See `## Architecture Patterns` Pattern 1 (two-tier match), `## Code Examples` (`normalize`, `match_listing`) |
| MATCH-02 | Listings with lot/bundle/damaged/counterfeit signals are excluded from price aggregates | See `## Architecture Patterns` Pattern 2 (exclusion checks), `## Code Examples` (keyword pattern lists), `## Common Pitfalls` Pitfall 1 |
| MATCH-03 | Statistical price outliers (far from rolling median) are excluded from displayed price | See `## Architecture Patterns` Pattern 3 (outlier filter), `## Code Examples` (`filter_outliers`, aggregation) |
</phase_requirements>

## Summary

Phase 4 adds exactly one new module, `scripts/matching.py`, and one new orchestration function, `run_matching_once(db, run_id)`, invoked from `scripts/ingest_worker.py`'s `run_ingestion_once()` immediately after the existing per-product ingestion loop completes (not per-listing inside that loop — PITFALLS.md's Performance Trap explicitly warns against synchronous per-listing matching inside the ingestion fetch loop; decoupling into a second stage over the batch of listings this run touched is both simpler to test and avoids that trap). This mirrors the codebase's actual established layout (flat `scripts/*.py` modules, not `ARCHITECTURE.md`'s originally-envisioned `ingestion/matching/` sub-package — Phase 3 already diverged from that structure and this phase should follow the real convention, not the earlier proposal).

The matching design is two-tier, precision-first, consistent with D-01: **Tier 1** is a deterministic keyword rule — for each catalog product, check whether *all* of its `required_keywords` (already disambiguated in Phase 2, e.g. `booster_bundle` requires "bundle", `booster_box` requires "box"/"display") appear as substrings in the normalized listing title. Collect every catalog product that satisfies this. Zero candidates → fall through to **Tier 2**, a RapidFuzz fallback (`process.extract` with `scorer=fuzz.token_sort_ratio`, `score_cutoff=90`) against a lean per-product phrase (`"{set_name} {product-type phrase}"`, NOT the catalog's full `display_name`, which shares enough boilerplate tokens across every product — "Pokemon TCG: Mega Evolution-" — to dilute fuzzy discrimination). More than one Tier-1 candidate, or a Tier-2 top score that isn't clearly separated from the runner-up, both resolve to `match_status="unmatched"` per D-03 — matching never auto-resolves ambiguity.

Exclusion runs as an independent pass over every listing touched this run (regardless of match outcome, so an unmatched listing's title can still be flagged as an obvious lot/damaged/counterfeit listing for audit purposes), using three keyword/regex pattern groups seeded from `PITFALLS.md` Pitfall 3's own examples plus reasonable extensions. The single most important implementation risk in this phase is that a naive "contains the word 'bundle'" lot-detection rule would systematically misfire against every legitimate `booster_bundle` catalog listing, since "bundle" is itself a required disambiguating keyword for that product type (Phase 2 D-06) — the lot/multi-quantity pattern list must target quantity language ("lot of", "x2", "set of N", "job lot"), never the bare word "bundle" alone.

Outlier filtering runs after matching+keyword-exclusion, grouped per `matched_product_id` among listings with `match_status="matched"` and no `exclusion_reason` yet, using `statistics.median()`/`statistics.pstdev()` on `total_price` (the canonical landed-cost field, per `PITFALLS.md` Pitfall 2 — never compare/aggregate on raw `item_price` alone) with the D-13-locked 2-std-dev cutoff, skipped entirely when the group has fewer than 3 listings (interpreting D-14's "e.g., only 1-2" example as the literal skip threshold). The final included set feeds two independent `statistics.median()` calls — one over `item_price`, one over `total_price` — written as a single `price_points` document per product per run (D-09/D-12), or skipped entirely if the included set is empty (D-11).

**Primary recommendation:** Add `rapidfuzz==3.14.5` to `requirements.txt` (behind `checkpoint:human-verify`, same protocol as `apscheduler`/`pymongo` in prior phases); build `scripts/matching.py` around `normalize()`, `match_listing()`, `check_exclusion()`, `filter_outliers()`, and an orchestrating `run_matching_once(db, run_id)`; call it from the end of `run_ingestion_once()`; extend `active_listings` documents in place with `match_status`, `matched_product_id`, `match_method`, `match_score`, `exclusion_reason`, `matched_at`; extend `ingestion_runs` with `listings_matched`, `listings_unmatched`, `listings_excluded`.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Title normalization | API/Backend (in-process function) | — | Pure string transformation, no I/O; shared by matching and exclusion checks |
| Keyword + fuzzy matching to canonical product | API/Backend (ingestion worker process, new `scripts/matching.py` module) | Database/Storage (reads `active_listings`, writes `matched_product_id`/`match_status` back in place) | In-process per ARCHITECTURE.md's explicit "not a network service" boundary decision, reused here without re-litigation |
| Lot/damaged/counterfeit keyword exclusion | API/Backend (same module) | Database/Storage | Same in-process boundary; independent pass, not a matching sub-step |
| Statistical outlier filtering | API/Backend (same module, per-product-group computation) | — | Pure computation over already-matched listings already in memory this run; no external dependency |
| Aggregated price write (`price_points`) | Database/Storage (time-series collection) | API/Backend (writer) | Matches Phase 2/3's existing tier assignment for this collection — this phase is simply its first writer |
| Match/exclusion audit trail (`match_status`/`exclusion_reason` on `active_listings`) | Database/Storage | API/Backend (writer) | "Flag, don't drop" philosophy requires the audit fields to be durable and queryable, not transient in-process state |
| Run observability extension (`ingestion_runs` counts) | Database/Storage | API/Backend (writer) | Extends Phase 3's already-established per-run metadata pattern; Phase 7's future alerting is the eventual reader |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| RapidFuzz | 3.14.5 `[VERIFIED: pypi registry — pip3 index versions rapidfuzz]` `[package name itself: ASSUMED — discovered via ARCHITECTURE.md's earlier web-research recommendation, not Context7-confirmed this session]` | Tier-2 fuzzy fallback matching for titles that don't satisfy Tier 1's exact keyword rule | Already the library ARCHITECTURE.md (a canonical ref this phase must respect) specifies for the two-tier pattern; C++-backed, fast enough for a ~tens-of-listings-per-run batch with zero tuning infrastructure needed |
| Python `statistics` (stdlib) | 3.12 (bundled) | `median()`, `pstdev()` for outlier detection and price aggregation | No new dependency — stdlib is sufficient for per-run sample sizes in the tens; adding numpy/pandas for this would be pure overhead (see Don't Hand-Roll) |
| PyMongo | 4.17.0 (already installed) | `bulk_write([UpdateOne(...)])` to patch `active_listings` in place; `insert_one` into the `price_points` time-series collection | Already the project's driver; no new API surface needed beyond what Phase 2/3 already established |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 8.4.2 (already installed) | Contract tests for `normalize`, `match_listing`, `check_exclusion`, `filter_outliers`, and the end-to-end `run_matching_once` | Same RED/GREEN scaffold pattern Phase 3 established |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| RapidFuzz | `difflib.SequenceMatcher` (stdlib) | Rejected: much slower on repeated comparisons, worse token-order handling (`token_sort_ratio` has no stdlib equivalent); ARCHITECTURE.md already specifies RapidFuzz and there's no reason to diverge |
| `fuzz.token_sort_ratio` | `fuzz.WRatio` (RapidFuzz's default "best overall" scorer) | Rejected as the primary Tier-2 scorer: WRatio blends in a partial-ratio component that can score a `booster_pack` title deceptively high against a `booster_box` phrase when one is a token subset of the other — directly working against D-01's precision-first stance. `token_sort_ratio` is the more literal, less lenient choice here. |
| `statistics.pstdev` (population) | `statistics.stdev` (sample, N-1 divisor) | Either is defensible given D-13's fixed "2 std devs" cutoff is not itself sample-vs-population-sensitive at these small N; `pstdev` is recommended because "this run's own included listings" (D-15) is treated as the complete relevant population, not a sample of a larger unknown population, and it has no minimum-N floor above 1 (though the D-14 skip-below-3 rule makes this distinction moot in practice) |
| MongoDB `bulk_write` in-place update | Deleting and re-inserting `active_listings` docs with match fields | Rejected: violates D-05's "never hard-delete" and the established idempotent-upsert-by-`_id` convention from Phase 3 |
| RapidFuzz against catalog `display_name` | RapidFuzz against a lean constructed phrase (`"{set_name} {type phrase}"`) | `display_name` strings share heavy boilerplate ("Pokemon TCG: Mega Evolution-...") across every catalog product, inflating scores near-uniformly and reducing discriminative power between genuinely different products — see Pitfall 3 below |

**Installation:**
```bash
pip install rapidfuzz==3.14.5
```
(Append to `requirements.txt`; PyMongo/pytest are already installed.)

**Version verification:** `pip3 index versions rapidfuzz` confirms `3.14.5` as latest this session (2026-07-14) — `[VERIFIED: pypi registry]`.

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| `rapidfuzz` | PyPI | Long-established (releases back to 0.0.6; latest release published 2026-04-07 — a recent release date on a mature project, not a new project) | Unknown (legitimacy tool could not retrieve download stats in this environment) | `github.com/rapidfuzz/RapidFuzz` (confirmed via web search this session — canonical, actively maintained, the same repo ARCHITECTURE.md cites) | `[SUS]` (reasons: `unknown-downloads`) | Keep — see note |

**Note on the `[SUS]` verdict:** This is the same class of false positive already documented and approved for `apscheduler` (03-RESEARCH.md) and `pymongo` (02-RESEARCH.md) in this project — the legitimacy tool cannot resolve a download-count signal in this environment, not evidence of an actual supply-chain risk. `rapidfuzz` is a mature, widely-used library (100+ historical releases, official GitHub org, matches the exact package ARCHITECTURE.md already specified for this phase's design). Per protocol, **the planner must still insert a `checkpoint:human-verify` task before `pip install rapidfuzz`**, even though the actual risk is assessed as negligible.

**Packages removed due to `[SLOP]` verdict:** none
**Packages flagged as suspicious `[SUS]`:** `rapidfuzz` — planner must insert `checkpoint:human-verify` before this install
**Postinstall script check:** N/A — Python packages have no npm-style `postinstall` script hook; `rapidfuzz` ships prebuilt wheels for common platforms with no arbitrary install-time code execution surface.

## Architecture Patterns

### System Architecture Diagram

```
[scripts/ingest_worker.py :: run_ingestion_once(db)]
        |
        |  (Phase 3, UNCHANGED) fetch + upsert active_listings per catalog product
        |
        v
[scripts/matching.py :: run_matching_once(db, run_id)]   <-- NEW, called once at the end
        |                                                     of run_ingestion_once(), after
        |                                                     the per-product fetch loop
        |
        |--1. db.active_listings.find({"run_id": run_id}) --------> [MongoDB: active_listings]
        |     (scopes to exactly the listings this run touched —
        |      Phase 3's upsert already stamps run_id on every write)
        |
        |--2. MATCHING pass, per listing:
        |       a. normalize(title)
        |       b. match_listing(normalized, CATALOG)
        |            Tier 1 (keyword): candidates = [p for p in CATALOG
        |                if all(kw in normalized for kw in p["required_keywords"])]
        |              0 candidates -> Tier 2
        |              1 candidate  -> match_status="matched", match_method="keyword"
        |              >1 candidates -> match_status="unmatched", match_method="ambiguous" (D-03)
        |            Tier 2 (fuzzy, only if Tier 1 found 0):
        |              rapidfuzz.process.extract(normalized, phrases, scorer=token_sort_ratio, limit=2)
        |              top >= 90 AND top-2nd >= 5  -> matched, match_method="fuzzy"
        |              else                        -> unmatched, match_method=None
        |
        |--3. EXCLUSION pass, per listing (independent of match outcome):
        |       check_exclusion(normalized) -> "lot" | "damaged" | "counterfeit" | None
        |
        |--4. bulk_write([UpdateOne(_id=listing_id, {"$set": {match_status, matched_product_id,
        |       match_method, match_score, exclusion_reason, matched_at}})]) ---> [active_listings]
        |
        |--5. group listings where match_status="matched" AND exclusion_reason is None,
        |     by matched_product_id
        |
        |--6. per group: filter_outliers(group, "total_price", n_std=2, min_count=3)
        |       len(group) < 3  -> skip filtering entirely (D-14), all included
        |       else            -> median/pstdev(total_price); |price - median| > 2*sd -> excluded
        |     bulk_write outlier exclusions (exclusion_reason="outlier") ---------> [active_listings]
        |
        |--7. per product, over the final included set:
        |       if included: price_points.insert_one({ts: started_at, product_id,
        |            item_price: median(item_prices), total_price: median(total_prices)})
        |                                                                       ---> [MongoDB: price_points]
        |       if empty:    skip write entirely (D-11 — gap, not carry-forward)
        |
        |--8. update ingestion_runs doc: listings_matched, listings_unmatched,
        |       listings_excluded -------------------------------------------------> [ingestion_runs]
        v
   run_ingestion_once() returns, now match-aware
```

A reader can trace the primary path end to end: a run's freshly-ingested listings are read back by `run_id` → each is matched (keyword, then fuzzy fallback) → each is independently checked for exclusion signals → matched-and-not-excluded listings are grouped per product and statistically filtered for outliers → surviving listings per product are median-aggregated into one `price_points` document → run-level counts are recorded for observability.

### Recommended Project Structure
```
scripts/
├── ebay_client.py         # Phase 1 — unchanged
├── catalog_data.py        # Phase 2 — unchanged (CATALOG, required_keywords is this phase's matching input)
├── ingest_worker.py        # Phase 3 — EXTEND: call matching.run_matching_once(db, run_id) at the
│                            #   end of run_ingestion_once(), before releasing the lock/finalizing
│                            #   the run document
├── matching.py              # NEW — normalize(), match_listing(), check_exclusion(),
│                            #   filter_outliers(), run_matching_once()
db/
├── init_collections.py     # Phase 2/3 — no schema change needed; active_listings and
│                            #   price_points already exist with no validator, so new fields
│                            #   on active_listings need no migration
tests/
├── test_matching.py         # NEW — unit + integration tests for MATCH-01/02/03
├── conftest.py              # EXTEND — add a `matching_db` fixture (see Validation Architecture)
```

### Pattern 1: Two-tier match (deterministic keyword rule, then bounded fuzzy fallback)

**What:** Try an exact "all required_keywords present" rule against every catalog product first; only fall back to RapidFuzz when zero products satisfy the exact rule, and only accept the fuzzy result if it clears both an absolute score floor and a margin over the runner-up.
**When to use:** Every listing touched in the current run.
**Example:**
```python
# scripts/matching.py
import re

from rapidfuzz import fuzz, process

from scripts.catalog_data import CATALOG
from scripts.ingest_worker import PRODUCT_TYPE_SEARCH_TERMS  # reuse, don't re-declare (DRY)

FILLER_WORDS = [
    "new", "sealed", "factory sealed", "fast ship", "fast shipping",
    "free shipping", "brand new", "in hand", "ready to ship", "same day ship",
]

FUZZY_SCORE_CUTOFF = 90    # [ASSUMED — untested against real listings; precision-first per D-01]
FUZZY_MARGIN = 5           # [ASSUMED — gap required over 2nd-best candidate to avoid a coin-flip match]


def normalize(title: str) -> str:
    """Lowercase, strip filler marketing words (word-boundary safe — a plain
    substring .replace('sealed', '') would corrupt 'resealed' into 're '),
    strip punctuation, collapse whitespace."""
    t = title.lower()
    for word in FILLER_WORDS:
        t = re.sub(rf"\b{re.escape(word)}\b", " ", t)
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def _canonical_phrase(product: dict) -> str:
    # Deliberately NOT catalog display_name — every display_name shares
    # "pokemon tcg: mega evolution-" boilerplate, which dilutes fuzzy
    # discrimination between genuinely different products (Pitfall 3).
    return f"{product['set_name']} {PRODUCT_TYPE_SEARCH_TERMS[product['product_type']]}".lower()


def match_listing(normalized_title: str) -> dict:
    """Returns {match_status, matched_product_id, match_method, match_score}."""
    candidates = [
        p for p in CATALOG
        if all(kw in normalized_title for kw in p["required_keywords"])
    ]
    if len(candidates) == 1:
        return {
            "match_status": "matched",
            "matched_product_id": candidates[0]["_id"],
            "match_method": "keyword",
            "match_score": None,
        }
    if len(candidates) > 1:
        # D-03: never auto-resolve — plausible multi-match is unmatched.
        return {
            "match_status": "unmatched",
            "matched_product_id": None,
            "match_method": "ambiguous",
            "match_score": None,
        }

    # Zero Tier-1 candidates -> Tier 2 fuzzy fallback.
    phrases = {_canonical_phrase(p): p["_id"] for p in CATALOG}
    results = process.extract(
        normalized_title, list(phrases.keys()),
        scorer=fuzz.token_sort_ratio, limit=2,
    )
    if not results:
        return {"match_status": "unmatched", "matched_product_id": None,
                "match_method": None, "match_score": None}

    top_phrase, top_score, _ = results[0]
    second_score = results[1][1] if len(results) > 1 else 0
    if top_score >= FUZZY_SCORE_CUTOFF and (top_score - second_score) >= FUZZY_MARGIN:
        return {
            "match_status": "matched",
            "matched_product_id": phrases[top_phrase],
            "match_method": "fuzzy",
            "match_score": top_score,
        }
    return {"match_status": "unmatched", "matched_product_id": None,
            "match_method": None, "match_score": top_score}
```
**Source:** RapidFuzz API shape (`process.extract`, `fuzz.token_sort_ratio`, `score_cutoff` semantics) — `[CITED: rapidfuzz.github.io/RapidFuzz/Usage/process.html, via WebSearch this session, context7 MCP unavailable]`. Matching logic and thresholds are this research's own design, `[ASSUMED]` on the exact numeric cutoffs.

### Pattern 2: Independent keyword-based exclusion pass

**What:** A separate function that checks a normalized title against three keyword/regex pattern groups, returning at most one `exclusion_reason`. Runs on every listing regardless of match outcome.
**When to use:** Immediately after (or interleaved with, order is not user-facing per CONTEXT.md) the matching pass.
**Example:**
```python
# scripts/matching.py (continued)

LOT_PATTERNS = [
    re.compile(r"\blot\s+of\b"),
    re.compile(r"\bjob\s*lot\b"),
    re.compile(r"\bwholesale\b"),
    re.compile(r"\bset\s+of\s+\d+\b"),
    re.compile(r"\bx\s?[2-9]\d*\b"),   # "x2", "x 3" — quantity, not the letter x alone
    re.compile(r"\b[2-9]\d*\s?x\b"),   # "2x", "3 x"
    re.compile(r"\b[2-9]\d*\s*(boxes|packs|etbs|bundles)\b"),
    # Deliberately NOT the bare word "bundle" — that's a legitimate
    # required_keyword for the booster_bundle product type (Phase 2 D-06);
    # a naive "bundle" check would exclude every real booster_bundle listing.
]

DAMAGED_PATTERNS = [
    re.compile(r"\bdented\b"), re.compile(r"\bresealed\b"),
    re.compile(r"\bopened\b"), re.compile(r"\bempty\s+box\b"),
    re.compile(r"\bno\s+cards?\b"), re.compile(r"\bdamaged\b"),
    re.compile(r"\bcrushed\b"), re.compile(r"\btorn\s+seal\b"),
    re.compile(r"\bbroken\s+seal\b"), re.compile(r"\bseal\s+broken\b"),
    # D-08: deliberately does NOT include "shelf wear", "corner ding",
    # "minor wear", "light wear" — cosmetic language must not exclude.
]

COUNTERFEIT_PATTERNS = [
    re.compile(r"\breplica\b"), re.compile(r"\bcustom\b"),
    re.compile(r"\bfan\s?made\b"), re.compile(r"\bproxy\b"),
    re.compile(r"\breproduction\b"), re.compile(r"\brepro\b"),
    re.compile(r"\bbootleg\b"), re.compile(r"\bnot\s+authentic\b"),
    re.compile(r"\bunofficial\b"),
]


def check_exclusion(normalized_title: str) -> str | None:
    if any(p.search(normalized_title) for p in LOT_PATTERNS):
        return "lot"
    if any(p.search(normalized_title) for p in DAMAGED_PATTERNS):
        return "damaged"
    if any(p.search(normalized_title) for p in COUNTERFEIT_PATTERNS):
        return "counterfeit"
    return None
```
**Note:** Keyword lists beyond CONTEXT.md's explicit examples (`dented`, `resealed`, `opened`, `empty box`, `no cards` for damaged; the general categories for lot/counterfeit) are `[ASSUMED]` extensions per "reasonable diligence," not exhaustively validated against a real listing corpus — see Assumptions Log.

### Pattern 3: Per-product statistical outlier filter (2 std dev, skip-below-3, current-run-only)

**What:** For each group of matched-and-not-yet-excluded listings sharing a `matched_product_id`, compute median/pstdev of `total_price` and exclude anything more than 2 std devs away — but only when the group has enough members for that to be meaningful.
**When to use:** After matching + keyword exclusion, before aggregation.
**Example:**
```python
# scripts/matching.py (continued)
import statistics

OUTLIER_N_STD = 2          # D-13, locked
OUTLIER_MIN_COUNT = 3      # interpretation of D-14's "e.g., only 1-2" -> skip when < 3


def filter_outliers(listings: list[dict], price_field: str = "total_price") -> tuple[list, list]:
    """Returns (included, excluded). Excluded listings still carry their
    full doc — caller sets exclusion_reason="outlier" on them."""
    if len(listings) < OUTLIER_MIN_COUNT:
        return listings, []  # D-14: too few to compute meaningfully — include all

    prices = [l[price_field] for l in listings]
    med = statistics.median(prices)
    sd = statistics.pstdev(prices)
    if sd == 0:
        return listings, []  # all identical prices — nothing is an outlier

    included, excluded = [], []
    for listing in listings:
        (excluded if abs(listing[price_field] - med) > OUTLIER_N_STD * sd else included).append(listing)
    return included, excluded
```
**Source:** `statistics.median`/`statistics.pstdev` semantics — `[CITED: docs.python.org/3/library/statistics.html, via WebSearch this session]`. The 2-std-dev-from-median/skip-below-3 combination is this research's implementation of D-13/D-14, which are already locked; the exact `OUTLIER_MIN_COUNT=3` value is `[ASSUMED]`, a literal reading of D-14's "e.g., only 1-2" example.

### Pattern 4: Median-based price_points aggregation, gap-on-empty

**What:** After outlier filtering, compute two independent medians (item_price, total_price) over the final included set and write one `price_points` document, or write nothing if the set is empty.
**Example:**
```python
def aggregate_and_write(db, product_id: str, included: list[dict], ts) -> bool:
    """Returns True if a price_points doc was written, False if skipped (D-11)."""
    if not included:
        return False
    db.price_points.insert_one({
        "ts": ts,                 # the run's started_at, for consistency with active_listings.fetched_at
        "product_id": product_id,
        "item_price": statistics.median(l["item_price"] for l in included),
        "total_price": statistics.median(l["total_price"] for l in included),
    })
    return True
```
**Note:** `ts`/`product_id`/`item_price`/`total_price` is the exact shape `db/init_collections.py`'s docstring already documents for `price_points`. No `$jsonSchema` validator is attached to this collection, so additional fields (e.g. `sample_size`, `run_id`) are technically permitted but not required — presented here as the minimal locked shape; adding `sample_size` (count of included listings) is a low-cost, discretionary addition worth the planner's consideration for future freshness/quality signals in Phase 6, but is not part of D-09 through D-12's locked contract.

### Anti-Patterns to Avoid

- **Running matching synchronously per-listing inside Phase 3's eBay-fetch loop:** PITFALLS.md's Performance Trap explicitly warns against this — it couples matching latency to ingestion latency and risks the cron-overlap failure mode Pitfall 4 already solved. Run matching as a second stage over the batch, after the fetch loop completes.
- **Excluding on the bare word "bundle":** Directly contradicts Phase 2 D-06 — `booster_bundle` is a real catalog product type whose `required_keywords` includes "bundle". A naive lot-exclusion rule keyed on that word alone would exclude every legitimate bundle listing.
- **Fuzzy-matching against `display_name` instead of a lean phrase:** Every catalog `display_name` shares "Pokemon TCG: Mega Evolution-" boilerplate, inflating token-overlap scores near-uniformly across all products and reducing the fuzzy tier's actual discriminative power.
- **Plain `.replace()` for filler-word stripping:** `"resealed".replace("sealed", "")` corrupts the string into `"re"`, silently destroying the exact signal the damaged-exclusion pattern needs. Use word-boundary-anchored regex substitution instead.
- **Auto-resolving Tier-1 multi-candidate or Tier-2 near-tie matches by picking the higher score:** Directly contradicts D-03 — ambiguous is unmatched, full stop.
- **Writing `price_points` with a carried-forward last-known price when a run has zero included listings:** Directly contradicts D-11 — skip the write, leave a real gap.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Fuzzy string similarity scoring | A custom Levenshtein/token-overlap implementation | RapidFuzz's `fuzz`/`process` module | C++-backed, handles token-order-insensitivity (`token_sort_ratio`) and multi-candidate ranking (`process.extract`) correctly and fast; reinventing this risks subtle scoring bugs for zero benefit |
| Median/standard-deviation computation | A hand-rolled sort-and-index median or a manual variance loop | Python's stdlib `statistics` module (`median`, `pstdev`) | Correctly handles even/odd-length lists and edge cases (empty/short input raises `StatisticsError` predictably); no reason to add numpy for per-run sample sizes in the tens |
| Filler-word/marketing-noise stripping from titles | An ad-hoc list of `.replace()` calls | Word-boundary-anchored regex substitution (`re.sub(r"\bword\b", ...)`) | Plain substring replace corrupts words that contain the filler word as a substring (e.g. "resealed" contains "sealed") — this is a real, easy-to-miss bug class, not a style preference |
| In-place update of existing documents by known `_id` | `find_one` then conditionally `update_one`/`replace_one` per listing in a loop | `bulk_write([UpdateOne({"_id": ...}, {"$set": {...}})])`, mirroring Phase 3's `upsert_listings` pattern exactly | One round-trip for the whole batch instead of N; already the established idiom in this codebase |

**Key insight:** Everything mechanically hard about this phase (fuzzy scoring, statistics) is already solved by RapidFuzz and the stdlib — the actual risk is domain-specific keyword design (the "bundle" collision, the filler-word substring-corruption bug) and pipeline sequencing (matching-then-exclusion-then-outlier, not interleaved or reordered in a way that breaks D-03/D-11/D-14's semantics).

## Common Pitfalls

### Pitfall 1: Lot-exclusion keyword list flags legitimate `booster_bundle` listings
**What goes wrong:** A naive exclusion rule checks for the substring "bundle" as multi-quantity/lot language (a reasonable-sounding first instinct given PITFALLS.md's own phrasing, "bundle" appears in its example list). Since `booster_bundle` is a real catalog product type whose `required_keywords` list includes "bundle" (Phase 2 D-06), every legitimate bundle listing gets wrongly excluded — silently zeroing out an entire product type's price data.
**Why it happens:** PITFALLS.md's Pitfall 3 lists "bundle" as an example lot/multi-quantity signal because in general eBay contexts "bundle" often does mean a lot of unrelated items — but this project's own catalog uses "bundle" as a legitimate first-class product name.
**How to avoid:** Exclude on quantity-language patterns ("lot of", "x2"/"2x", "set of N", "job lot", "wholesale") — never on the bare word "bundle" alone. See Pattern 2's `LOT_PATTERNS`.
**Warning signs:** A product's `price_points` history for a `booster_bundle` product type shows a suspiciously large gap or an unusually low match-rate in `ingestion_runs` stats relative to `booster_box`/`etb` products for the same set.

### Pitfall 2: Filler-word stripping via plain string `.replace()` corrupts "resealed"
**What goes wrong:** `title.lower().replace("sealed", "")` (an intuitive first implementation of "strip filler marketing words") silently turns "Resealed ETB" into "re  ETB", destroying the exact word the damaged-exclusion pattern is looking for.
**Why it happens:** `.replace()` matches substrings, not whole words; "resealed" contains "sealed" as a substring.
**How to avoid:** Use `re.sub(r"\bsealed\b", " ", t)` (word-boundary anchored) for every filler word, not plain `.replace()`.
**Warning signs:** A manual audit of matched listings shows titles containing "resealed" never triggering the damaged exclusion category.

### Pitfall 3: Fuzzy-matching against catalog `display_name` inflates cross-product similarity
**What goes wrong:** Every catalog entry's `display_name` shares a long common prefix ("Pokemon TCG: Mega Evolution-..."), so `token_sort_ratio` against `display_name` strings scores most candidates artificially close together, weakening Tier 2's ability to discriminate between, say, a Chaos Rising booster box and a Chaos Rising ETB.
**Why it happens:** `display_name` is the obvious, already-present "human readable" field to reach for — but it wasn't designed for discrimination, it was designed for UI display (Phase 2 D-07 context).
**How to avoid:** Build a lean per-product phrase (`f"{set_name} {product-type phrase}"`, reusing `ingest_worker.PRODUCT_TYPE_SEARCH_TERMS`) specifically for the fuzzy comparison, as shown in Pattern 1.
**Warning signs:** Tier-2 fuzzy scores across multiple different-product candidates for the same listing cluster within a few points of each other rather than showing a clear winner.

### Pitfall 4: Treating `active_listings.product_ref` as if it were the match result
**What goes wrong:** Phase 3's `product_ref` field records which catalog query *found* a listing (provenance), not a verified match — reusing it as `matched_product_id` without running Phase 4's independent title-based matching would silently propagate Phase 3's loose search-query results (which can return off-target listings; eBay's `q` search is not exact) into price aggregates.
**Why it happens:** `product_ref` already exists on every `active_listings` document and looks like it answers "which product is this," but 03-RESEARCH.md explicitly documents it as provenance-only.
**How to avoid:** Always independently evaluate `title` against `required_keywords`/fuzzy phrases in this phase's matching step — never read `product_ref` as if it were `matched_product_id`.
**Warning signs:** `matched_product_id` values on `active_listings` documents are always identical to their `product_ref` value with 100% consistency (a sign matching was skipped, not run).

### Pitfall 5: Outlier filtering computed on `item_price` instead of `total_price`
**What goes wrong:** Computing the median/std-dev used for outlier detection on `item_price` alone reintroduces exactly the shipping-cost comparability problem PITFALLS.md Pitfall 2 already warns about — two listings priced identically in real landed cost could differ wildly in raw `item_price` purely because one seller folds shipping into the item price and another charges it separately, causing the outlier filter to flag a perfectly normal listing.
**How to avoid:** Run `filter_outliers()` on `total_price` (Pattern 3's default), the canonical landed-cost field — the same field already established as canonical throughout Phase 3.
**Warning signs:** A high proportion of listings flagged `exclusion_reason="outlier"` also show `shipping_cost=0.0` (free-shipping listings systematically look like outliers relative to paid-shipping ones when compared on `item_price` alone).

## Code Examples

### `run_matching_once` orchestration (called from `run_ingestion_once`)
```python
# scripts/matching.py
from datetime import datetime, timezone

from pymongo import UpdateOne


def run_matching_once(db, run_id: str, ts) -> dict:
    """Matches, excludes, and aggregates every active_listings document
    written this run. Returns {"listings_matched": int,
    "listings_unmatched": int, "listings_excluded": int} for the caller
    to merge into the ingestion_runs update (D-04)."""
    listings = list(db.active_listings.find({"run_id": run_id}))

    match_ops = []
    by_product: dict[str, list[dict]] = {}
    matched_count = unmatched_count = excluded_count = 0

    for listing in listings:
        normalized = normalize(listing["title"])
        result = match_listing(normalized)
        exclusion_reason = check_exclusion(normalized)

        update = {**result, "exclusion_reason": exclusion_reason,
                  "matched_at": datetime.now(timezone.utc)}
        match_ops.append(UpdateOne({"_id": listing["_id"]}, {"$set": update}))

        if result["match_status"] == "matched":
            matched_count += 1
            if exclusion_reason is None:
                by_product.setdefault(result["matched_product_id"], []).append(
                    {**listing, **update}
                )
            else:
                excluded_count += 1
        else:
            unmatched_count += 1
        if exclusion_reason is not None and result["match_status"] != "matched":
            pass  # already counted as unmatched; exclusion_reason still stored for audit

    if match_ops:
        db.active_listings.bulk_write(match_ops)

    outlier_ops = []
    for product_id, group in by_product.items():
        included, excluded = filter_outliers(group)
        excluded_count += len(excluded)
        for listing in excluded:
            outlier_ops.append(UpdateOne(
                {"_id": listing["_id"]}, {"$set": {"exclusion_reason": "outlier"}}
            ))
        aggregate_and_write(db, product_id, included, ts)

    if outlier_ops:
        db.active_listings.bulk_write(outlier_ops)

    return {
        "listings_matched": matched_count,
        "listings_unmatched": unmatched_count,
        "listings_excluded": excluded_count,
    }
```
**Integration point in `scripts/ingest_worker.py`:** call `run_matching_once(db, run_id, started_at)` inside the existing `try` block, right after the `for product in CATALOG:` loop finishes and before the `finally` clause — its return dict merges into the same `update_doc` that already sets `products_queried`/`listings_fetched`/`listings_written`, adding `listings_matched`/`listings_unmatched`/`listings_excluded` (D-04) as three new top-level int fields on the `ingestion_runs` document, matching the existing flat-field convention exactly.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| N/A | N/A | — | This phase introduces new functionality on a stable foundation (RapidFuzz's API and Python's `statistics` module have not changed in ways relevant here); no prior-approach-to-replace exists in this codebase |

**Deprecated/outdated:** None relevant to this phase.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `FUZZY_SCORE_CUTOFF=90` and `FUZZY_MARGIN=5` for Tier-2 fuzzy matching | Pattern 1 | Medium — no live eBay listing data exists yet (EBAY_CLIENT_ID/SECRET still missing per STATE.md Blockers) to tune against; too strict silently pushes more listings to `unmatched` (acceptable cost per D-01, just lower coverage), too lenient risks a real mismatch (the more expensive failure mode). Recommend a manual audit pass once live data exists, adjusting these two constants without any schema change. |
| A2 | Exclusion keyword/regex lists beyond CONTEXT.md's five explicit damaged-category examples (lot patterns, counterfeit patterns, and damaged extensions like "crushed"/"torn seal") | Pattern 2 | Medium — under-inclusive lists let some real lot/damaged/counterfeit listings slip into price aggregates (silently skews prices, the exact failure PITFALLS.md Pitfall 3 warns about); over-inclusive lists could exclude legitimate listings using coincidentally similar language. Recommend the "Looks Done But Isn't" manual-audit step (see Validation Architecture) once real listing titles are available. |
| A3 | `OUTLIER_MIN_COUNT=3` (skip outlier filtering below 3 listings) | Pattern 3 | Low — D-14 gives "e.g., only 1-2" as an illustrative example, not an exact locked number; interpreting "too few" as `< 3` is a reasonable, literal reading, and the value is a single named constant, trivial to adjust if the planner or user prefers a different cutoff. |
| A4 | `statistics.pstdev` (population) chosen over `statistics.stdev` (sample) for outlier detection | Alternatives Considered, Pattern 3 | Low — D-13's "2 standard deviations" cutoff does not itself specify population vs. sample; at the small N this phase operates on the numeric difference between the two is modest, and either is defensible. |
| A5 | `run_matching_once` scopes to `active_listings` filtered by `run_id` (this run's touched listings only), not the full historical collection | Architecture Patterns, Summary | Low — this matches D-15's "just the current run's own included listings" framing for outlier stats and Phase 3's established `run_id` stamping convention; if a future phase needs a full-catalog re-match/backfill (e.g. after tuning exclusion keywords), that would be a separate, explicitly-scoped script, not part of this phase. |
| A6 | RapidFuzz API mechanics (`process.extract`, `fuzz.token_sort_ratio`, `score_cutoff` semantics) and Python `statistics` module behavior, as cited in Code Examples | Pattern 1, Pattern 3 | Low — sourced via WebSearch cross-referencing RapidFuzz's own GitHub/docs site and Python's official stdlib docs (both authoritative, well-established, stable APIs); `context7` MCP tools were unavailable this session so these are `[CITED]` rather than `[VERIFIED]` via direct doc fetch, but the underlying libraries are mature and unlikely to have drifted. |

## Open Questions

1. **Will real eBay listing titles actually satisfy Tier 1's exact-keyword rule as often as assumed, or will Tier 2's fuzzy fallback carry more of the match-rate than expected?**
   - What we know: Phase 2's `required_keywords` were deliberately designed to be present in well-formed titles (e.g. "Elite Trainer Box" or "ETB" for `etb` products).
   - What's unclear: Real seller title conventions (abbreviations, word order, typos) are unverified — no live ingestion has run yet (EBAY_CLIENT_ID/SECRET still missing).
   - Recommendation: Not a planning blocker — the two-tier design already accounts for this uncertainty by design. Once live data exists, a manual audit of `match_method` distribution (`keyword` vs `fuzzy` vs `unmatched` counts) will reveal whether Tier 2's thresholds (A1) need adjustment.

2. **Should the Tier-1 multi-candidate ambiguous case and the Tier-2 near-tie case both surface as `match_method="ambiguous"`, or should they be distinguishable?**
   - What we know: D-03 only requires both to resolve to `match_status="unmatched"`.
   - What's unclear: Whether finer-grained inspectability (e.g. `match_method="ambiguous_keyword"` vs `"ambiguous_fuzzy"`) is worth the extra enum surface for future rule-tuning.
   - Recommendation: Keep it simple for v1 — `match_method="ambiguous"` for the Tier-1 multi-candidate case, `match_method=None` for the Tier-2 no-confident-match case, both under `match_status="unmatched"`. This is a low-cost, backward-compatible field to enrich later if rule-tuning needs finer detail.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|--------------|-----------|---------|----------|
| Python 3.12+ | Matching module runtime | Yes | 3.12.13 (confirmed this session) | — |
| PyMongo | `active_listings`/`price_points`/`ingestion_runs` writes | Yes | 4.17.0 (already installed) | — |
| RapidFuzz | Tier-2 fuzzy fallback matching | No (not yet installed) | Latest 3.14.5 (registry-confirmed) | Install via `requirements.txt`, gated behind `checkpoint:human-verify` per Package Legitimacy Audit |
| MongoDB (Atlas M0) | All reads/writes | Provisioned in Phase 2 | — | — |
| `EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET` | End-to-end validation against real listing titles | No — still missing per STATE.md Blockers (same blocker inherited from Phase 3) | — | This phase's own logic (matching/exclusion/outlier/aggregation) can be fully built and unit/integration-tested against synthetic `active_listings` documents inserted directly by tests (see Validation Architecture) — it does not require live eBay data to implement or verify correctness of the algorithms themselves. Only a true "matches real seller title conventions" validation is blocked, same caveat Phase 3's plan already carries forward. |

**Missing dependencies with no fallback:**
- None that block this phase's implementation — `EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET` block *live, real-data* validation only, not the buildable/testable core logic.

**Missing dependencies with fallback:**
- `rapidfuzz` — trivially installable once the legitimacy checkpoint is approved.
- Live eBay listing titles — synthetic fixture documents (constructed directly in `tests/test_matching.py`, following `test_ingest_worker.py`'s existing pattern of hand-built listing dicts) substitute for real data during development; a real-data audit is recommended as a follow-up once Phase 3's live-run blocker clears, not a hard gate on this phase's completion.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 (already installed and configured — `pytest.ini` sets `pythonpath = .`, `testpaths = tests`) |
| Config file | `pytest.ini` (existing) |
| Quick run command | `pytest tests/test_matching.py -x` |
| Full suite command | `pytest` (runs the whole `tests/` directory, including Phase 2/3's existing tests) |

**Nyquist pattern applies here, same as Phase 3:** this project's established convention (Phase 3's `03-03-PLAN.md`) is to author RED tests against a dedicated test-db fixture *before* the implementation exists, then turn them GREEN in a follow-up plan/wave. This applies directly to Phase 4 — matching/exclusion/outlier correctness is exactly the kind of price-accuracy-critical logic that pattern exists for, and the existing `ingest_db`/`catalog_db` fixture pattern in `tests/conftest.py` is directly extensible (see Wave 0 Gaps below).

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|---------------------|--------------|
| MATCH-01 | `match_listing()` resolves an exact-keyword title to the correct `matched_product_id` with `match_method="keyword"`; falls back to fuzzy for near-miss titles; returns `unmatched`/`ambiguous` for multi-candidate or below-threshold titles | unit | `pytest tests/test_matching.py::test_match_listing_keyword_exact tests/test_matching.py::test_match_listing_fuzzy_fallback tests/test_matching.py::test_match_listing_ambiguous_unmatched -x` | ❌ Wave 0 |
| MATCH-02 | `check_exclusion()` correctly flags lot/damaged/counterfeit titles and does NOT flag a legitimate `booster_bundle` listing or a minor-cosmetic-wear listing | unit | `pytest tests/test_matching.py::test_exclusion_lot tests/test_matching.py::test_exclusion_damaged_severe_only tests/test_matching.py::test_exclusion_counterfeit tests/test_matching.py::test_exclusion_does_not_flag_legitimate_bundle -x` | ❌ Wave 0 |
| MATCH-03 | `filter_outliers()` excludes listings > 2 std devs from median; skips filtering entirely below `OUTLIER_MIN_COUNT`; `aggregate_and_write()` writes the correct independent item/total medians and skips the write when included is empty | unit + integration (real MongoDB via a new `matching_db` fixture) | `pytest tests/test_matching.py::test_outlier_filter_excludes_far_listings tests/test_matching.py::test_outlier_filter_skipped_when_too_few tests/test_matching.py::test_price_points_median_aggregation tests/test_matching.py::test_price_points_skipped_when_zero_included -x` | ❌ Wave 0 |
| MATCH-01/02/03 (end-to-end) | `run_matching_once()` against a `matching_db`-seeded batch of realistic synthetic listings (clean match, lot, damaged, counterfeit, ambiguous, statistical outlier) produces the expected `active_listings` flags, `price_points` document, and returned counts | integration | `pytest tests/test_matching.py::test_run_matching_once_end_to_end -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_matching.py -x`
- **Per wave merge:** `pytest` (full suite, including Phase 2/3's existing tests)
- **Phase gate:** Full suite green before `/gsd-verify-work`. Additionally, per PITFALLS.md's "Looks Done But Isn't" checklist ("verify exclusion rules exist and are tested against real sampled titles, not just synthetic test cases"), once EBAY_CLIENT_ID/SECRET are restored and Phase 3's live run produces real `active_listings` data, a follow-up manual audit (query `db.active_listings.find({"match_status": "unmatched"})` and a sample of `exclusion_reason != null` documents) should be performed — document this as a known follow-up if credentials remain unavailable at phase-gate time, mirroring Phase 3's own precedent for its live-verification gap.

### Wave 0 Gaps
- [ ] `tests/test_matching.py` — does not exist yet; covers MATCH-01/02/03 unit + integration cases
- [ ] `scripts/matching.py` — does not exist yet; core deliverable (`normalize`, `match_listing`, `check_exclusion`, `filter_outliers`, `aggregate_and_write`, `run_matching_once`)
- [ ] `tests/conftest.py` extension — add a `matching_db` fixture mirroring `ingest_db`'s structure but also covering `price_points` (needed for aggregation write tests), via `init_collections(test_db)` after dropping `active_listings`/`price_points`/`ingestion_runs`
- [ ] `scripts/ingest_worker.py` — extend `run_ingestion_once()` to call `run_matching_once(db, run_id, started_at)` and merge its returned counts into the `ingestion_runs` `update_doc`
- [ ] Framework install: `pip install rapidfuzz==3.14.5` — gate behind `checkpoint:human-verify` per Package Legitimacy Audit

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|----------------|---------|---------------------|
| V2 Authentication | No | No auth surface added — this phase is a backend batch computation over already-ingested data |
| V3 Session Management | No | No sessions |
| V4 Access Control | No | No user-facing endpoint or access-control surface in this phase |
| V5 Input Validation | Yes | `active_listings.title` is external/untrusted data (originated from eBay, already stored by Phase 3) — matching/exclusion code must defensively handle missing/malformed `title` fields (mirror Phase 3's per-item `try/except` convention) rather than assuming shape; regex patterns must be simple/bounded (no nested quantifiers) to avoid catastrophic-backtracking (ReDoS) risk on adversarial-length title strings |
| V6 Cryptography / Secrets Handling | No new surface | Reuses the existing `MONGODB_URI` connection already established in Phase 2/3 — no new secrets introduced by this phase |

### Known Threat Patterns for this phase's stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| A malformed/missing `title` field on an `active_listings` document crashing the batch matching pass | Denial of Service (self-inflicted) | Wrap each listing's normalize/match/exclusion-check in a per-item `try/except` (mirroring `upsert_listings`'s existing per-item defensive pattern) so one bad document doesn't abort the whole run's matching stage |
| Regex-based exclusion patterns vulnerable to catastrophic backtracking on a very long or adversarially-crafted title string | Denial of Service | All patterns in Pattern 2 use simple, non-nested, bounded quantifiers (`\b...\b`, `[2-9]\d*`) — avoid patterns with nested `(a+)+`-style quantifiers; this is a design constraint to hold as the exclusion list grows |
| A future writer bypassing this phase's matching logic and writing directly to `matched_product_id`/`exclusion_reason` with unvalidated values (e.g. a manual MongoDB edit per D-07's fix path introducing a typo'd `exclusion_reason`) | Tampering (low severity, self-inflicted) | `active_listings` has no `$jsonSchema` validator (same as `price_points`) — this is an accepted tradeoff given D-07's explicit "direct MongoDB edit is the fix path" design; not a regression to fix in this phase, just a known characteristic to note for future schema-hardening work if it ever becomes a problem |

## Sources

### Primary (HIGH confidence)
- Direct reads of this repository's `.planning/phases/04-listing-matching-price-normalization/04-CONTEXT.md`, `.planning/research/ARCHITECTURE.md`, `.planning/research/PITFALLS.md`, `.planning/phases/02-product-catalog-data-model/02-RESEARCH.md`, `.planning/phases/03-active-listing-ingestion-pipeline/03-RESEARCH.md`, `db/init_collections.py`, `scripts/catalog_data.py`, `scripts/ingest_worker.py`, `tests/conftest.py`, `tests/test_ingest_worker.py` (this session)
- `pip3 index versions rapidfuzz` (registry check, this session) — `[VERIFIED: pypi registry]`
- `gsd-tools query package-legitimacy check --ecosystem pypi rapidfuzz` (this session)

### Secondary (MEDIUM/LOW confidence — WebSearch this session; `context7` MCP tools were unavailable in this environment, so these are cited via search-engine-surfaced snippets rather than direct doc fetch)
- [rapidfuzz.fuzz — Usage — RapidFuzz 3.14.5 documentation](https://rapidfuzz.github.io/RapidFuzz/Usage/fuzz.html) — scorer behavior (WRatio, token_sort_ratio)
- [rapidfuzz.process — Usage — RapidFuzz 3.14.5 documentation](https://rapidfuzz.github.io/RapidFuzz/Usage/process.html) — `extractOne`/`extract`, `score_cutoff` semantics
- [GitHub - rapidfuzz/RapidFuzz](https://github.com/rapidfuzz/RapidFuzz) — legitimacy/provenance confirmation
- [statistics — Mathematical statistics functions — Python 3 documentation](https://docs.python.org/3/library/statistics.html) — `median`, `stdev`, `pstdev`, `StatisticsError` semantics
- eBay policy pages (Counterfeit item policy, Search manipulation policy) — confirms eBay prohibits counterfeit/replica listings and title manipulation, but provides no canonical exclusion-keyword list of its own; keyword lists in this research are derived from `PITFALLS.md`'s own examples plus reasonable extensions, not from eBay's policy text directly
- General statistics community sources (outlier-detection method comparisons) — confirms std-dev-from-mean/median methods are known to be weak on small samples relative to Median Absolute Deviation (MAD); informs the Alternatives Considered note but does NOT override D-13's already-locked 2-std-dev cutoff

### Tertiary (LOW confidence — used only for cross-corroboration, not load-bearing)
- General e-commerce fuzzy-matching best-practice articles (Data Ladder, Tilores) — cross-corroborate the general two-tier deterministic-then-fuzzy pattern already specified by ARCHITECTURE.md; not independently authoritative

## Metadata

**Confidence breakdown:**
- Pipeline architecture / integration point in `run_ingestion_once` / schema field placement: HIGH — directly grounded in this repo's own existing code and CONTEXT.md's locked decisions, not external claims
- RapidFuzz/`statistics` module mechanics: MEDIUM — WebSearch-sourced against the libraries' own official docs/GitHub, cross-corroborated, but not fetched via `context7` this session (tool unavailable)
- Fuzzy score cutoffs (90/5-point margin), outlier min-count (3), and exclusion keyword lists beyond CONTEXT.md's explicit examples: LOW — reasoned but untested against real data; flagged `[ASSUMED]` throughout and listed in the Assumptions Log

**Research date:** 2026-07-14
**Valid until:** 2026-08-13 (30 days for the stable library-mechanics claims); re-verify the numeric thresholds (A1, A2, A3) as soon as Phase 3's live-eBay-credential blocker clears and real listing titles become available — those are the claims most likely to need revision, not the underlying library APIs

---
*Phase: 4-Listing Matching & Price Normalization*
*Research completed: 2026-07-14*
