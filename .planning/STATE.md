---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Price History & Extended Badges
current_phase: 8
current_phase_name: Price History Chart
status: planning
stopped_at: Phase 8 context gathered
last_updated: "2026-08-18T15:38:25.717Z"
last_activity: 2026-08-18
last_activity_desc: v1.1 roadmap created (Phases 8-9, 3/3 requirements mapped)
progress:
  total_phases: 2
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-08-18)

**Core value:** A user can look up a specific pack/box/ETB and see whether it's priced fairly right now, backed by live eBay asking prices (sold-price history parked — see PROJECT.md Context).
**Current focus:** Milestone v1.1 — surface the price history that has already been accumulating in the `price_points` time-series collection since Phase 4: a detail-page line chart (Phase 8), then 24h and all-time high/low badges (Phase 9).

## Current Position

Phase: Phase 8 — Price History Chart (not started)
Plan: —
Status: Roadmap created, awaiting phase planning
Last activity: 2026-08-18 — v1.1 roadmap created (Phases 8-9, 3/3 requirements mapped)

## Performance Metrics

**Velocity:**

- Total plans completed: 39
- Average duration: — min
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 02 | 6 | - | - |
| 04 | 5 | - | - |
| 05 | 7 | - | - |
| 06 | 7 | - | - |
| 07 | 5 | - | - |
| 03 | 5 | - | - |
| 01 | 4 | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
| Phase 01 P01 | 1min | - tasks | - files |
| Phase 01 P02 | 2min | 3 tasks | 3 files |
| Phase 01 P03 | 2min | 2 tasks | 2 files |
| Phase 02 P03 | 20min | 2 tasks | 2 files |
| Phase 02 P01 | 5min | 2 tasks | 1 files |
| Phase 02 P02 | 10min | 2 tasks | 1 files |
| Phase 02 P04 | 8min | 2 tasks | 2 files |
| Phase 02 P05 | 5min | 2 tasks | 3 files |
| Phase 02 P06 | 10min | 2 tasks | 1 files |
| Phase 03 P01 | 10min | 2 tasks | 1 files |
| Phase 03 P02 | 2min | 2 tasks | 1 files |
| Phase 03 P03 | 2min | 2 tasks | 2 files |
| Phase 03 P04 | 4min | 3 tasks | 2 files |
| Phase 03 P05 | 2min | 1 tasks | 0 files |
| Phase 04 P02 | 15min | 3 tasks | 2 files |
| Phase 04 P01 | 5min | 2 tasks | 1 files |
| Phase 04 P03 | 12min | 2 tasks | 1 files |
| Phase 04 P04 | 6min | 2 tasks | 2 files |
| Phase 04 P05 | 5min | 1 tasks | 1 files |
| Phase 05 P01 | 11min | 2 tasks | 1 files |
| Phase 05 P02 | 10min | 2 tasks | 2 files |
| Phase 05 P03 | 4min | 3 tasks | 4 files |
| Phase 05 P04 | 8 | 2 tasks | 3 files |
| Phase 05 P05 | 15min | 2 tasks | 1 files |
| Phase 05 P06 | 10min | 2 tasks | 5 files |
| Phase 05 P07 | 12min | 2 tasks | 4 files |
| Phase 06 P01 | 15min | 3 tasks | 10 files |
| Phase 06 P02 | 4min | 2 tasks | 6 files |
| Phase 06 P03 | 3min | 2 tasks | 5 files |
| Phase 06 P04 | 10min | 2 tasks | 6 files |
| Phase 06 P05 | ~6min | 2 tasks | 6 files |
| Phase 06 P06 | ~10min | 1 tasks | 3 files |
| Phase 06 P07 | ~8min | 3 tasks | 5 files |
| Phase 07 P01 | 12min | 2 tasks | 3 files |

## Accumulated Context

### Decisions

Full v1.0 decision log archived in `.planning/RETROSPECTIVE.md` and `.planning/PROJECT.md` Key Decisions table (with outcomes).

Carried-forward decisions still governing future work:

- Official eBay APIs only, no scraping — held throughout v1.0, still binding.
- Sold-price integration is parked indefinitely and v1.0 is treated as the complete product — the MI Growth Check was reapplied for as a registered business entity and denied again, so no live reapplication path remains; PriceCharting is a theoretical option only and is not being pursued.
- Simple in-process APScheduler over Celery/broker infra — no reason to revisit unless scale requirements change materially.

v1.1 roadmap decisions (2026-08-18):

- Phase numbering continues the global sequence at 8, even though "Phase 8" was the label the now-parked sold-price work carried during v1.0 planning. That label is historical documentation only; the parked item now carries no phase number in ROADMAP.md so there is exactly one `### Phase 8:` header.
- v1.1 is structured as two thin vertical slices (chart, then badges) rather than a backend phase plus a frontend phase — each phase must ship a user-visible capability end-to-end through Mongo query → API field → React render.
- Phase 9 is sequenced after Phase 8 for edit-conflict reasons (both touch `ProductDetailPage.jsx` and its tests), not because of a data or API dependency.

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues that affect future work]

None open.

Context to carry into planning (not blockers):

- `api/services/catalog_service.py::get_product_detail` deliberately withholds the raw `price_points` series (documented as D-11 from Phase 5). Phase 8 needs a new code path/endpoint rather than loosening that function's contract silently — the D-11 decision should be explicitly revisited and recorded, not just overwritten.
- Recharts is in the intended stack per prior research but has never been added as a dependency or used in any component. Phase 8 is its first real introduction, so it goes through the same package-legitimacy checkpoint the project applied to pymongo/apscheduler/rapidfuzz/flask.
- The existing `get_trend_baseline` uses a ±3-day tolerance window (D-05), which is nonsensical for a 24h window. Phase 9 must pick and record an explicit tolerance for the 24h badge rather than reusing the default.
- `.github/workflows/ci.yml` now runs the full pytest suite against a real `mongo:7` service container on every PR/push, so new backend tests execute for real in CI.
- ~25 non-blocking v1.0 hardening items and Nyquist coverage gaps on 6 of 7 phases remain carried forward (see `.planning/v1.0-MILESTONE-AUDIT.md`). Not in v1.1 scope.

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260718-0a4 | Fix ebay_client.py total_cost() KeyError on missing shippingCost in a real Browse API shippingOptions entry | 2026-07-18 | 0c1364d | [260718-0a4-fix-ebay-client-py-total-cost-keyerror-o](./quick/260718-0a4-fix-ebay-client-py-total-cost-keyerror-o/) |
| 260802-l3l | Add once-per-UTC-day Discord heartbeat to ingest worker — deployed to Fly.io (image deployment-01KZ14GZ0KWPZDW889A1RFFMGZ) | 2026-08-02 | db4e1e4 | [260802-l3l-add-periodic-discord-heartbeat-to-ingest](./quick/260802-l3l-add-periodic-discord-heartbeat-to-ingest/) |
| 260802-lwv | Add real production usage stats (94 runs/15.3 days) to Growth Check narrative + update MANUAL-STEPS status; also scaled Fly web 2→1 machine | 2026-08-02 | aec6a8c | [260802-lwv-update-growth-check-narrative-and-manual](./quick/260802-lwv-update-growth-check-narrative-and-manual/) |
| 260802-n5c | Mark MI Growth Check (ticket 260802-000004) as denied; lock in FALLBACK-DECISION.md Option 1 — active-listing-only v1, Phase 8 deferred out of v1.0 | 2026-08-02 | 79d63c3 | [260802-n5c-mark-ebay-marketplace-insights-growth-ch](./quick/260802-n5c-mark-ebay-marketplace-insights-growth-ch/) |
| 260802-oup | Record decision to permanently park sold-price integration (MI Growth Check reapplied as a business entity, denied again) — v1.0 treated as the complete product | 2026-08-02 | 200d29f | [260802-oup-record-decision-to-permanently-park-sold](./quick/260802-oup-record-decision-to-permanently-park-sold/) |
| 260818-k38 | Add GitHub Actions CI/CD pipeline (.github/workflows/ci.yml): backend pytest + frontend lint/test/build on PR and push to main, secret-gated Fly.io deploy on push to main after CI passes — PR #1 merged, FLY_API_TOKEN secret added, first main-branch deploy confirmed live | 2026-08-18 | 9faddc6 | [260818-k38-add-a-github-actions-ci-cd-pipeline-ci-r](./quick/260818-k38-add-a-github-actions-ci-cd-pipeline-ci-r/) |

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Feature | Sold-Price Integration (INGEST-04, PRICE-04/05/06) — parked, not being pursued (business-entity reapplication to MI Growth Check denied). Formerly labeled "Phase 8"; carries no phase number now. | Parked (reapplication denied) | 2026-08-02 |
| Requirement | PRICE-10 — catalog/browse sparklines | Deferred to v2 | 2026-08-18 |
| Requirement | PRICE-11 — item/total price toggle on the chart | Deferred to v2 | 2026-08-18 |
| Tech debt | ~25 v1.0 hardening items + Nyquist coverage gaps on 6 of 7 phases (see `.planning/v1.0-MILESTONE-AUDIT.md`) | Carried forward, non-blocking | 2026-08-02 |

## Session Continuity

Last session: 2026-08-18T15:38:25.709Z
Stopped at: Phase 8 context gathered
Resume file:
.planning/phases/08-price-history-chart/08-CONTEXT.md

## Operator Next Steps

- Plan the first phase with `/gsd-plan-phase 8`
