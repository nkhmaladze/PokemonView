# Pitfalls Research

**Domain:** Pokemon TCG sealed-product price tracking sourced from eBay (poe.ninja-style)
**Researched:** 2026-07-12
**Confidence:** MEDIUM overall (LOW-confidence web sources, but cross-corroborated across multiple independent eBay Community threads and eBay's own official docs on several critical points — see Sources)

## Critical Pitfalls

### Pitfall 1: Marketplace Insights API access is not guaranteed — the sold-price data source the whole product depends on may be unobtainable

**What goes wrong:**
The project's core value proposition ("real sold-price trends") depends on eBay's Marketplace Insights API. This is explicitly a **Limited Release API** restricted to approved partners, gated behind an "Application Growth Check" that eBay reviews based on business model and use case. Multiple eBay Developer Community threads (2024-2025) describe independent/hobby developers getting "Access denied" indefinitely, even after their app works in sandbox — production access for non-partners is frequently reported as effectively closed. Compounding this: eBay's older Finding/Shopping APIs, which used to expose completed/sold listings for free, were deprecated 2024-01-04 and fully decommissioned 2025-02-05, closing off the informal workaround that many small projects previously relied on.

**Why it happens:**
Teams assume "official API exists for X" means "we can get access to X," and only discover the approval gate after building ingestion/matching/API/frontend around the assumption that sold data will be available on schedule.

**How to avoid:**
Apply for Marketplace Insights API access literally in Phase 1, before any other implementation work, as a go/no-go gate — not as a "nice to have researched later" item. In parallel, design the sold-price feature so it degrades gracefully if access is denied or delayed: e.g., ship v1 on active-listing (Browse API) pricing only, with sold-price trends as a fast-follow once/if access is granted. Have a documented fallback plan (see Recovery Strategies) rather than treating MI API as guaranteed.

**Warning signs:**
- Developer account application for Marketplace Insights API scope sits in "pending" or returns "insufficient permissions" beyond a few business days.
- Sandbox calls succeed but production calls return `Access denied` / `invalid_scope`.

**Phase to address:**
Phase 1 (feasibility spike / access verification), before ingestion pipeline or matching service work begins. This should be the single highest-priority research/spike item in the whole roadmap.

---

### Pitfall 2: Treating eBay's price field as the full transaction cost

**What goes wrong:**
eBay's Browse API and Marketplace Insights API return item price and shipping cost as **separate fields**, not a single landed cost. A naive ingestion pipeline that reads only `price.value` will systematically under-report the true cost of listings that charge separate shipping, while over-weighting "free shipping" listings that have simply folded shipping into the item price. Since sellers price identical products differently across these two shipping models, comparing raw `price` values across listings produces a skewed, non-comparable price signal — exactly the kind of error a price-tracking product cannot tolerate, since accuracy is the stated core value.

**Why it happens:**
It's easy to prototype against `item.price.value` and get something that "looks right" for a handful of listings, without noticing the shipping-cost split until asking why the same product shows a wide, unexplained price spread.

**How to avoid:**
Always compute and store a normalized `total_cost = item_price + shipping_cost` (falling back to item_price only when shipping cost is genuinely $0/free) as the canonical price used for all aggregation, trend charts, and comparisons. Never surface raw `item.price` alone as "the price" in the UI or in aggregate statistics.

**Warning signs:**
- Wide, seemingly random price variance for the same catalog product with no correlation to condition/seller.
- Price trend charts show sawtooth patterns tracking free-shipping vs paid-shipping listing mix rather than real market movement.

**Phase to address:**
Ingestion/matching phase (data model design) — the total-cost field should be part of the canonical schema from the first pipeline write, not retrofitted later.

---

### Pitfall 3: Sold/active listing titles include lots, bundles, damaged goods, and counterfeits that silently pollute price aggregates

**What goes wrong:**
eBay Pokemon sealed-product listings are not homogeneous: sellers list single boxes/ETBs, but also "lots" and "bundles" (multiple boxes/packs at once, which race to the bottom on per-unit price), damaged/resealed/opened product (explicitly called out in the title as a caveat, e.g. "DENTED", "RESEALED"), and counterfeit/reproduction product (PSA fraud reports show Pokemon counterfeits rising sharply, and fake listings are sometimes titled as if genuine). A keyword-based matcher that only checks for product name + set name will happily match all of these into the same "canonical product" price series, dragging the average down (lots/bundles, damaged) or introducing outlier spikes/dips that have nothing to do with real market value.

**Why it happens:**
Keyword matching optimizes for recall (catching all real variants of a title) without an equally deliberate exclusion pass for adversarial/non-representative listing patterns. This is a false-positive problem that's easy to miss in early testing because most listings in a small sample are legitimate.

**How to avoid:**
Build the matching/normalization service with an explicit two-stage design: (1) inclusion matching against canonical product name/set, (2) **exclusion rules** that filter out or flag: multi-quantity/lot/bundle language ("lot of", "x2", "x3", "bundle", "set of"), condition-negative language ("damaged", "dented", "resealed", "opened", "empty box", "no cards"), and counterfeit signals ("replica", "custom", "fan made", "proxy", or price far below the statistical floor for that product). Apply outlier filtering (see Pitfall — poe.ninja lesson below) as a second layer of defense even after keyword exclusion.

**Warning signs:**
- A product's price history shows sudden unexplained drops (lot/bundle contamination) or spikes (counterfeit-driven anomalies, or single-item vs multi-item mixing).
- Manual spot-check of matched listings for a product turns up titles mentioning "lot," "bundle," "damaged," or quantities >1.

**Phase to address:**
Matching/normalization service phase — exclusion rules must ship alongside inclusion rules in the same phase, not as a later cleanup pass. Consider a lightweight statistical outlier filter (e.g., discard listings >2-3 std devs from a rolling median) in the same phase as a second line of defense.

---

### Pitfall 4: Overlapping or retried cron runs silently duplicate ingested listings

**What goes wrong:**
The project explicitly chose simple cron/script scheduling over Celery/a task broker. Without safeguards, a scheduled ingestion run that occasionally takes longer than the interval (e.g., eBay API slowness, larger result sets after a new set drops) will overlap with the next scheduled run, causing both to write the same listings. Similarly, any naive retry-on-failure logic that blindly re-inserts already-ingested records will duplicate the same sold/active listings. This inflates listing counts, skews aggregate statistics, and corrupts trend data.

**Why it happens:**
Cron by default does not know or care whether the previous invocation is still running; teams that intentionally avoid task-broker infrastructure (as this project does) must build the overlap/idempotency protection themselves rather than getting it "for free" from something like Celery's task locking.

**How to avoid:**
Use file-based or DB-based locking (e.g., `flock -n` around the cron entrypoint, or a "job is running" flag document in MongoDB with a TTL) so a new invocation exits immediately if the prior one hasn't finished. Make every ingestion write idempotent by keying on eBay's own listing ID / item ID (upsert, not insert) rather than relying on auto-generated document IDs — a duplicate ingestion of the same eBay item ID should update-in-place, not create a second record.

**Warning signs:**
- Listing/document counts in MongoDB grow faster than the expected rate implied by the polling interval and eBay result volume.
- The same eBay item ID appears more than once in the active or sold listings collection.

**Phase to address:**
Ingestion pipeline phase — locking and upsert-by-source-ID must be part of the initial pipeline design, verified with a test that deliberately triggers an overlapping/retried run.

---

### Pitfall 5: Silent pipeline failures — "the cron job ran successfully" is not the same as "the data is fresh and correct"

**What goes wrong:**
A scheduled ingestion job can exit with status 0 (success) while producing zero new rows, stale data, or partial data — e.g., an eBay API auth token silently expired and every call returned an auth error that was swallowed, or eBay changed a response field and the matching step silently classified everything as "unmatched." Without dedicated freshness/row-count checks, this can go unnoticed for a long time because there's no crash to alert on — the product just quietly shows out-of-date "current" prices, which directly contradicts the project's stated core value ("must always be accurate and current").

**Why it happens:**
Teams instrument for job-level failure (exceptions, non-zero exit codes) but not for data-level correctness (did we actually get new listings this run, and does the freshest data's timestamp match expectation).

**How to avoid:**
Record ingestion-run metadata (documents ingested, listings matched, run timestamp, run duration) as its own collection/log, and add a simple freshness check (e.g., alert if any product's price data hasn't been updated in >2x the expected polling interval). Fail loud on zero-row runs unless explicitly expected (e.g., legitimately no new sales).

**Warning signs:**
- "Last updated" timestamps on the frontend are stale relative to the actual data refresh schedule.
- Ingestion logs show successful completion but with an unusually low or zero count of new/updated listings.

**Phase to address:**
Ingestion pipeline phase for the freshness/row-count logging; API/frontend phase for surfacing a visible "data as of [timestamp]" indicator so staleness is visible to users, not just to operators.

---

### Pitfall 6: eBay OAuth token refresh scope mismatches and token-type confusion

**What goes wrong:**
eBay OAuth has two distinct token types: application access tokens (client-credentials grant, used for public/read-only data like Browse API search) and user access tokens (authorization-code grant + refresh token, needed for user-specific/selling actions). A common mistake is refreshing a user access token with a different or narrower scope list than the one originally granted — eBay's API rejects this — or attempting to use an application token where a user token is required (or vice versa). Since this project only needs read access to public listing/price data, using the wrong grant type unnecessarily complicates auth and introduces refresh-cycle bugs that surface as intermittent 401s in production.

**Why it happens:**
eBay's documentation covers both grant types together, and it's easy to copy a code sample built for selling-API use cases (user token) when the project only needs the simpler application-token flow for Browse/Marketplace Insights reads.

**How to avoid:**
Confirm early which grant type each API actually requires for this project's read-only use case (Browse API supports the application token / client-credentials flow for public search; verify Marketplace Insights API's required scope/grant type as part of the Phase 1 access spike). Automate token refresh proactively (before expiry, not on 401) and always request the exact same scope list on every refresh call.

**Warning signs:**
- Intermittent 401 "invalid_token" or "insufficient_scope" errors under production load that don't reproduce in manual testing.
- Ingestion pipeline failures correlated with token lifetime (e.g., failures resume right after a manual token refresh).

**Phase to address:**
Phase 1 (access verification) for confirming the right grant type per API; ingestion pipeline phase for building automated, proactive token refresh into the scheduled job itself (not a manual step).

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|-----------------|------------------|
| Keyword-only matching with no exclusion rules for lots/damaged/counterfeit | Ships matching faster | Silently skewed price data undermines core value prop | Never beyond a throwaway prototype |
| Using `item.price` alone instead of price+shipping total | Simpler ingestion code | Incomparable, misleading price data across listings | Never in anything user-facing |
| No locking around cron job | Less code to write initially | Duplicate data corrupts historical trends once overlap occurs | Only acceptable if polling interval is very long relative to job runtime AND monitored closely — still risky |
| Treating sandbox test results as representative of production data quality | Faster local development | False confidence; sandbox catalog/search data is sparse/unrepresentative | Acceptable only for auth/plumbing tests, never for matching-accuracy validation |
| No outlier filtering, straight average/median of matched listings | Simple initial implementation | Counterfeit/lot/damaged pollution directly distorts the "price" shown to users | Acceptable only very briefly in an MVP demo, must be fixed before real users trust the numbers |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|-------------------|
| eBay Marketplace Insights API | Assuming approval is automatic/guaranteed like Browse API | Apply for Application Growth Check access as the first Phase 1 task; build a fallback (active-price-only) path in case access is denied or delayed |
| eBay OAuth | Refreshing a user token with different scopes than originally granted, or mixing up application vs user token per endpoint | Use application (client-credentials) tokens for read-only public data; keep scope list identical across refresh calls; automate refresh proactively |
| eBay Sandbox | Validating matching accuracy or data completeness against sandbox responses | Use sandbox only for auth/plumbing smoke tests; validate matching logic and data volume assumptions against production (via a low-volume/limited test app if needed) |
| eBay API License Agreement | Retaining raw eBay listing data indefinitely, or publishing raw average-sold-price/GMV by category without permission | Implement a data-retention/purge policy (eBay requires deletion within a reasonable time, referenced as up to 30 days after data is no longer needed); confirm current license terms allow the specific aggregate price displays planned before launch |
| eBay rate limits | Polling as fast as possible / not tracking remaining quota | Query the Analytics API's rate-limit endpoint (or track locally) and back off before hitting daily caps; batch/paginate efficiently rather than re-fetching unchanged data |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Storing every raw listing snapshot at full granularity forever in MongoDB | Collection and index size grow unbounded; queries for trend charts get slower over time | Use MongoDB time-series collections or pre-aggregate to daily/hourly summaries for anything older than a short recent window; set TTL/retention policy | Noticeable once historical data spans months across even a handful of catalog products with frequent polling |
| Re-fetching full listing sets every run instead of incremental/filtered pulls | Burns through daily API call quota fast; slower runs | Use eBay filters (date ranges, `lastSoldDate`) to pull only new/changed data since last run, per eBay's own caching/incremental-pull guidance | Breaks once catalog expands beyond 2-3 sets or polling frequency increases |
| Running matching (fuzzy/keyword logic) synchronously per-listing inside the ingestion loop at scale | Ingestion run time grows linearly and eventually exceeds the cron interval, causing overlap (Pitfall 4) | Batch matching, or decouple ingestion (raw capture) from matching (normalization) as separate pipeline stages that can be tuned/scaled independently | Becomes visible once listing volume per run grows past whatever the current synchronous loop was tuned for |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Hardcoding eBay client ID/secret or OAuth tokens in source/config committed to the repo | Credential leak, quota theft/abuse, account suspension | Store credentials in environment variables/secret manager; never commit `.env` with real keys |
| Exposing raw eBay seller usernames/feedback data or full listing URLs in ways that violate API License Agreement content-use restrictions | ToS violation risking API access revocation | Review the API License Agreement's content-display restrictions (e.g., aggregate price display permissions) before finalizing what raw eBay fields are shown publicly |
| No input validation on matching service if it ever accepts external/user-supplied search terms | Injection into MongoDB queries if user input flows into query construction | Sanitize/parameterize any user-facing search against the catalog; never build raw Mongo queries from unescaped user text |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-------------------|
| Showing a single "the price" number with no indication of data freshness or sample size | Users can't judge trustworthiness of the number, especially if data is stale or based on very few matched listings | Always show "as of [timestamp]" and ideally an n-count ("based on X sold listings in the last Y days") next to any price figure |
| Mixing active (asking) and sold (actual) prices into one undifferentiated number | Users conflate what something is listed for vs what it actually sells for — the whole point of the poe.ninja-style distinction is lost if blurred | Keep active vs sold prices visually and structurally distinct everywhere in the UI, exactly as scoped in PROJECT.md |
| Silently including lot/bundle/damaged listings in trend charts | Users see confusing price swings with no explanation, eroding trust in the tool's accuracy | Filter these out at the matching stage (Pitfall 3) and, if any borderline listings are kept, mark them visibly rather than blending them silently |

## "Looks Done But Isn't" Checklist

- [ ] **Marketplace Insights API integration:** Often "done" in sandbox but never verified against production access approval — confirm production access is actually approved and returning real sold data, not just that sandbox calls succeed.
- [ ] **Price display:** Often shows `item.price` alone — verify shipping cost is included in the canonical price used everywhere (charts, current-price display, comparisons).
- [ ] **Matching/normalization service:** Often only has inclusion rules — verify exclusion rules for lots/bundles/damaged/counterfeit exist and are tested against real sampled titles, not just synthetic test cases.
- [ ] **Scheduled ingestion:** Often "works" in manual single-run testing — verify it's safe against overlapping/retried runs (test by deliberately running it twice concurrently) and that writes are idempotent (upsert by eBay item ID).
- [ ] **Data freshness:** Often no visible signal to the end user — verify the frontend displays a "last updated" timestamp reflecting the actual last successful ingestion run, and that a stale/failed run is detectable (not silently swallowed).
- [ ] **API compliance:** Often skipped until launch — verify the current API License Agreement's data-retention and display-restriction terms are actually satisfied by the shipped retention policy and UI display choices.

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|----------------|-----------------|
| Marketplace Insights API access denied/delayed | HIGH | Ship v1 scoped to active-listing pricing only (Browse API); revisit sold-price feature once/if MI API access is granted, or evaluate a compliant paid data partner as an alternative sold-data source |
| Duplicate listings from overlapping cron runs already in MongoDB | MEDIUM | Backfill a dedup pass keyed on eBay item ID + timestamp bucket, then add locking/upsert going forward; recompute affected aggregates |
| Price aggregates found to be skewed by lot/counterfeit contamination after launch | MEDIUM | Add exclusion rules retroactively, re-run matching against historical raw listing archive (if raw data was retained within the API License Agreement's retention window) to recompute clean trend history |
| Shipping-cost omission discovered after some trend data is already published | LOW-MEDIUM | If raw listing data (with separate shipping field) was retained, recompute total-cost aggregates from raw records; if not retained, disclose the correction and rebuild trend history going forward only |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|-------------------|----------------|
| Marketplace Insights API access uncertainty | Phase 1 (access/feasibility spike) | Production (not sandbox) call to Marketplace Insights API returns real sold-listing data before any dependent phase begins |
| Price/shipping total-cost omission | Ingestion + data model design phase | Schema review confirms a computed total-cost field is stored and used everywhere prices are aggregated or displayed |
| Lot/bundle/damaged/counterfeit contamination | Matching/normalization service phase | Manual audit of a sample of matched listings per product shows exclusion rules correctly reject lots, bundles, damaged, and clearly counterfeit items |
| Overlapping/duplicate cron ingestion runs | Ingestion pipeline phase | Deliberately trigger two overlapping runs in a test environment; confirm no duplicate documents and locking prevents the second run from writing concurrently |
| Silent stale/failed pipeline runs | Ingestion pipeline phase + API/frontend phase | Ingestion run log shows row counts and freshness; frontend visibly displays "data as of" timestamp reflecting true last-successful-run time |
| OAuth token/scope mismatches | Phase 1 (access spike) + ingestion pipeline phase | Token refresh automated and tested across at least one full expiry cycle without manual intervention or scope errors |

## Sources

- [API Call Limits — eBay Developers Program](https://developer.ebay.com/develop/get-started/api-call-limits)
- [Access token rate limits — eBay Developers Program](https://developer.ebay.com/api-docs/static/oauth-rate-limits.html)
- [Browse API Overview — eBay Developers Program](https://developer.ebay.com/api-docs/buy/browse/overview.html)
- [OAuth best practices — eBay Developers Program](https://developer.ebay.com/api-docs/static/oauth-best-practices.html)
- [Using a refresh token to update a User access token — eBay Developers Program](https://developer.ebay.com/api-docs/static/oauth-refresh-token-request.html)
- [eBay OAuth Client Library in Python and Best Practices — eBay Innovation](https://innovation.ebayinc.com/stories/ebay-oauth-client-library-in-python-and-best-practices/)
- [Use the application growth check to get access to restricted APIs — eBay Developers Program](https://developer.ebay.com/api-docs/static/gs_use-the-application-growth.html)
- [Marketplace Insight API responded with Access denied — eBay Community](https://community.ebay.com/t5/RESTful-Sell-APIs-Marketing/Marketplace-Insight-API-responded-with-Access-denied/td-p/35066691)
- [Marketplace Insights API scope request issue — eBay Community](https://community.ebay.com/t5/RESTful-Sell-APIs-Marketing/Marketplace-Insights-API-scope-request-issue/td-p/34709120)
- [Access to sold/completed listing data — what options do non-partner developers actually have? — eBay Community](https://community.ebay.com/t5/eBay-APIs-Talk-to-your-fellow/Access-to-sold-completed-listing-data-what-options-do-non/td-p/35398955)
- [Alert! Finding API and Shopping API to be decommissioned in 2025 — eBay Community](https://community.ebay.com/t5/Traditional-APIs-Search/Alert-Finding-API-and-Shopping-API-to-be-decommissioned-in-2025/td-p/34222062)
- [API License Agreement — eBay Developers Program](https://developer.ebay.com/join/api-license-agreement)
- [Follow best practices — eBay Developers Program](https://developer.ebay.com/api-docs/static/gs_follow-best-practices.html)
- [Understand the Sandbox and Production environments — eBay Developers Program](https://developer.ebay.com/api-docs/static/gs_understand-the-sandbox-and.html)
- [Unsupported features list for the Sandbox — eBay Developers Program](https://developer.ebay.com/support/kb-article?KBid=684)
- [Idempotent Pipelines: Build Once, Run Safely Forever — DEV Community](https://dev.to/alexmercedcoder/idempotent-pipelines-build-once-run-safely-forever-2o2o)
- [How Do Overlapping Cron Jobs Quietly Create Double-Processing and Conflicting Writes — Medium](https://medium.com/@dollietrinkstip37/how-do-overlapping-cron-jobs-quietly-create-double-processing-and-conflicting-writes-in-the-same-7413c66712fc)
- [Data Pipeline Monitoring: How to Stop Silent Failures Before They Hit Production](https://blog.anomalyarmor.ai/data-pipeline-monitoring-how-to-stop-silent-failures-before-they-hit-production/)
- [The 5 Silent Failures in Data Pipelines — Seattle Data Guy](https://seattledataguy.substack.com/p/the-5-silent-failures-in-data-pipelines)
- [Fuzzy Matching 101: The Complete Guide to Accurate Data Matching — Data Ladder](https://dataladder.com/fuzzy-matching-101/)
- [Company Name Normalization Isn't Enough for Fuzzy Matching — Tilores](https://tilores.io/content/company-name-normalization-isnt-enough-for-fuzzy-matching/)
- [Fake Card Lots On eBay - What Can I Do? — PokéBeach](https://www.pokebeach.com/forums/threads/fake-card-lots-on-ebay-what-can-i-do.135306/)
- [How to Sell Pokémon Cards on eBay for Maximum Profit — ZIK Analytics](https://www.zikanalytics.com/blog/how-to-sell-pokemon-cards-on-ebay/)
- [Pokemon Cards Market Analysis Seller Profit Guide — ShelfTrend](https://www.shelftrend.com/other-categories/pokemon-cards-market-analysis-seller-profit-guide)
- [Shipping costs: key API calls — eBay Developers Program](https://developer.ebay.com/api-docs/user-guides/static/trading-user-guide/shipping-key-calls.html)
- [ItemSummary: eBay Browse API — eBay Developers Program](https://developer.ebay.com/api-docs/buy/browse/types/gct:ItemSummary)
- [poe.ninja](https://poe.ninja/)
- [PoE Ninja: The Complete Guide to Using poe.ninja — Poetrade](https://poetrades.net/poe-ninja-guide-2026/)
- [Time Series Data and MongoDB: Part 2 – Schema Design Best Practices — MongoDB Blog](https://www.mongodb.com/blog/post/time-series-data-and-mongodb-part-2-schema-design-best-practices)
- [Time Series Collection Limitations — MongoDB Docs](https://www.mongodb.com/docs/manual/core/timeseries/timeseries-limitations/)

**Note on confidence:** Individual web sources here are classified LOW confidence per the project's source-hierarchy tooling (general web search, not vendor-verified docs), but the Marketplace Insights API access-restriction finding (Pitfall 1) is corroborated across eBay's own official developer documentation AND multiple independent eBay Developer Community threads spanning 2024-2025, which raises practical confidence in that specific finding to MEDIUM despite the LOW provider tier. Treat Pitfall 1 as the highest-priority item to verify directly against eBay's current developer portal before roadmap commitment.

---
*Pitfalls research for: Pokemon TCG sealed-product price tracking (eBay-sourced)*
*Researched: 2026-07-12*
