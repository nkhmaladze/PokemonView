# Fallback Decision: Marketplace Insights API Denied or Delayed

**Phase:** 01-ebay-api-feasibility-gate
**Status:** Committed decision (SC-3)
**Purpose:** Record, as a phase artifact, the fallback already established at project-research level (`research/STACK.md` "Stack Patterns by Variant", `research/PITFALLS.md` "Recovery Strategies") so this go/no-go gate has a formal, committed answer regardless of the Marketplace Insights (MI) Application Growth Check outcome.

This document does not re-derive the research — it formalizes the decision already reached.

---

## Decision

**If the Marketplace Insights Application Growth Check (tracked in `MANUAL-STEPS.md`) is denied, or remains pending past the self-imposed decision-by date, PokemonView ships v1 as an active-listing-only product.**

- v1 (Phases 1-7 per `ROADMAP.md`) uses only the Browse API: current asking price (item + shipping total) and an "asking-price trend" built from repeated active-listing snapshots over time.
- This is **not** true sold-price data — it shows market movement in what sellers are asking, not what buyers actually paid — but it is a complete, coherent, shippable product on its own, matching the "poe.ninja-style" current-price experience even without the sold-price differentiator.
- Real sold-price history, the active-vs-sold spread indicator, and the sold-volume/liquidity indicator (`INGEST-04`, `PRICE-04`, `PRICE-05`, `PRICE-06`) are deferred to **Phase 8: Sold-Price Integration**, which `ROADMAP.md` already marks as contingent on this phase's MI API outcome.
- If MI access is granted later — during Phase 1 execution, mid-milestone, or even after v1 has shipped — Phase 8 can be pulled forward and layered on top of the already-shipped active-price product without requiring a rebuild of Phases 1-7.
- If MI access is never granted, Phase 8 rolls to a later milestone (or is dropped) and Phases 1-7 remain PokemonView's complete v1.

## Why

- eBay's Finding API (`findCompletedItems`), the old free path to sold-price data, was fully decommissioned 2025-02-05 — there is no legacy fallback.
- The Marketplace Insights API is a Limited Release API gated behind a manually-reviewed Application Growth Check with no published SLA; multiple independent 2024-2026 community reports describe approval as effectively closed to individual/hobby-framed applicants (`research/PITFALLS.md` Pitfall 1, `research/STACK.md`).
- The project's own constraint is "official eBay APIs only, no scraping" (`PROJECT.md`), which rules out scraping eBay's sold/completed listings pages or Seller Hub Terapeak UI as a substitute.
- Blocking the entire roadmap on an unpredictable, possibly-denied approval would make the whole project's timeline hostage to a decision outside our control — hence Phase 1 exists specifically to resolve this as an early go/no-go gate rather than a build-time assumption (`ROADMAP.md` Phase 1 goal).

## Ranked Fallback Options (for the denied/delayed case)

1. **Ship active-only v1, revisit later (the default/committed choice above).** No new constraint violated, no new spend, product stands on its own value (live pricing + asking-price trend). This is what Phases 1-7 already build toward regardless of MI outcome, so no rework is needed if this path is taken.
2. **PriceCharting API (licensed, paid fallback) — requires an explicit scope conversation with the user.** PriceCharting is a legitimate, licensed third-party data aggregator that already compiles eBay sold comps for trading cards/sealed collectibles via its own methodology, available through a paid subscription tier. This is the most defensible fallback if sold-price data becomes a hard requirement later, because it's a licensed source rather than a scrape — but adopting it changes the project's current "official eBay APIs only" constraint (`PROJECT.md`). **This must be raised explicitly with the user as a scope decision before implementation, never silently substituted.** Not planned as Phase 1 or v1 work; noted here only as the next option if Option 1 is later judged insufficient.
3. **eBay Terapeak Research 2.0 (manual spot-check only).** Web-UI-only, no public bulk API, not automatable — usable only as an occasional manual sanity-check during development, never as a production ingestion source. Not a real fallback for the product itself.
4. **Third-party scraping services.** Explicitly excluded — violates both `PROJECT.md`'s no-scraping constraint and eBay's ToS. Not a viable option under any circumstances.

Options 3 and 4 are recorded for completeness only; they are not viable production fallbacks and are not to be pursued.

## Architectural Implication Carried Into Later Phases

Regardless of which path above is eventually needed, the matching/normalization service (Phase 4) must be **designed source-agnostic from day one**: it should accept listings shaped like either the eBay Browse API's active-listing response or a future Marketplace-Insights/PriceCharting-shaped sold-listing response, without requiring a rewrite when/if a second data source is added. This keeps Option 1 (ship now) and a later switch to Option 1-plus-MI-approval or Option 2 (PriceCharting) both cheap to adopt whenever the MI outcome is finally known.

## Outcome Tracking

The actual MI Growth Check submission status, submitted date, and self-imposed decision-by date are tracked in `MANUAL-STEPS.md`'s Submission Tracking table — this document records the *decision* for the denied/delayed case, not the live status. Check `MANUAL-STEPS.md` for the current outcome.
