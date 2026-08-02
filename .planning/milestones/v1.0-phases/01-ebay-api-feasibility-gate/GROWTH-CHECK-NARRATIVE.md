# Marketplace Insights Application Growth Check — Draft Narrative

**Status:** Draft, for your review. This is text Claude has prepared for you to read, edit if needed, and paste into eBay's Developer Portal yourself (D-03) — Claude does not and cannot submit this on your behalf.

**Where to use this:** In Step 4 of `MANUAL-STEPS.md`, at `https://developer.ebay.com/my/support/tickets?tab=app-check`, use "Save as Draft" on the use-case/justification field and paste the text below in, after filling in the placeholder.

**Before pasting:** Replace `[YOUR BUSINESS ENTITY NAME]` below with your actual registered business entity's name.

---

## Use Case / Justification

Applicant: **[YOUR BUSINESS ENTITY NAME]**

**[YOUR BUSINESS ENTITY NAME]** operates a price-transparency and resale-analytics platform for the sealed Pokémon Trading Card Game secondary market. The application tracks current asking prices and historical sold-price trends for sealed product — booster packs, booster boxes, and Elite Trainer Boxes — from recent English-language set releases, giving collectors and resellers accurate, data-backed visibility into fair market value. This is directly analogous to established price-transparency tools in other collectible/virtual-goods markets (e.g., poe.ninja for Path of Exile in-game items), applied to the physical collectibles resale market.

We are requesting access to the Marketplace Insights API specifically to retrieve **sold listing** data, which is essential to our core value proposition: showing users real transaction history (what an item actually sold for), not just current asking prices. Browse API access alone only surfaces active listings, which cannot show true market value on its own.

**Scope of use:** Read-only. We only require sold-listing search data for a curated, fixed set of product categories (sealed Pokémon TCG product). We do not require any user-token scopes, selling-API access, or the ability to place or manage listings on a user's behalf — this application never acts as or on behalf of an eBay seller or buyer account.

**Estimated call volume:** Our ingestion process is a scheduled worker that polls a curated catalog of approximately 10-30 tracked products on a periodic interval (every few hours), well within eBay's default rate-limit tier of roughly 5,000 calls per day. We do not require elevated rate limits at this time — this request is solely for read scope to the Marketplace Insights API endpoint, not for a rate-limit increase.

**Usage to date:** This is not a beta or no-usage application — it is a live, continuously running production service with real accumulated usage history. As of 2026-08-02, our always-on Fly.io production worker has completed 94 successful/partial ingestion runs over 15.3 continuous days (first healthy run on 2026-07-18, most recent on 2026-08-02), executing on a fixed 4-hour schedule with zero gaps. To date it has issued 1,504 Browse API search calls, fetched 75,200 cumulative listings, and currently tracks 4,865 unique active listings in our database. This Marketplace Insights request extends an existing, actively operating application — not a new or speculative one.

**Data handling:** Retrieved sold-listing data is used only to compute aggregate price statistics (e.g., median sold price, price trend over time) displayed to end users, in compliance with eBay's API License Agreement's data-retention and display-restriction terms. We do not resell, redistribute, or expose raw eBay listing/seller data beyond aggregate price figures.

---

## Notes for the reviewer filling this in

- This is a draft — read it, adjust tone/specifics if you know something Claude doesn't (e.g., your entity's registered name, structure), and only submit once you're satisfied it's accurate.
- Do not remove the "read-only" and "no user-token / no selling scope" language — this is factually correct for this project's use case and materially improves approval odds by making the request narrow and easy to review.
- If the portal's actual form has a separate field for business entity details (EIN, registration number, etc.) beyond a free-text name, fill those in directly in the portal using your own records — this narrative only covers the free-text justification field.
- Submission is not blocked on anything else (D-06) — submit as soon as you've reviewed this and completed Steps 1-3 of `MANUAL-STEPS.md`.
