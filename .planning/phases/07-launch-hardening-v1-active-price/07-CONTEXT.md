# Phase 7: Launch & Hardening (v1 active-price) - Context

**Gathered:** 2026-07-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 7 deploys the already-complete active-price product — ingestion worker, Flask API, React SPA, MongoDB — to a public URL, keeps the ingestion worker running unattended on its already-locked schedule, and adds a staleness alert so a silent pipeline failure surfaces instead of quietly showing users stale prices. This is purely operational readiness: no new API endpoints, no new UI components, no new product capabilities. It ships v1 regardless of Marketplace Insights (sold-price) API status — Phase 8 is separate and contingent.

</domain>

<decisions>
## Implementation Decisions

### Hosting & Deployment Target
- **D-01:** Split-PaaS architecture, not a single VPS: Fly.io hosts the Flask API and the ingestion worker (two process types/machines under one Fly app or two small Fly apps — left to planning); the React SPA static build deploys separately to Vercel, Netlify, or Cloudflare Pages (planner's choice, whichever is simplest to wire to this repo). MongoDB stays on the existing Atlas M0 free tier — no change.
- **D-02:** User explicitly chose Fly.io over the recommended Render/Railway, accepting that this requires a Dockerfile (Fly.io is container-based; Render/Railway would have used native buildpacks). Plan for containerizing both the API and the ingestion worker.
- **D-03:** Budget ceiling is ~$5-15/mo on an always-on tier — explicitly not the free tier, because a sleeping/cold-starting dyno would silently break the 4h ingestion cadence (INGESTION_INTERVAL_HOURS default, already locked in Phase 3). The API and worker must not scale-to-zero.
- **D-04:** No custom domain for v1 — platform-provided subdomains are fine (`*.fly.dev` for the API, whatever the static host issues for the SPA). HTTPS is automatic on all three candidate platforms; no certificate work needed. A custom domain can be added later without being a blocker now.

### eBay Credentials Blocker
- **D-05:** EBAY_CLIENT_ID/EBAY_CLIENT_SECRET are still absent (wiped in a Phase 1 incident, confirmed still missing as of Phase 3 Plan 03-05's deferred verification) and the user does not have replacement values yet. Phase 7 deploys the full stack now anyway — do not block launch on obtaining credentials first. The ingestion worker will fail at `get_app_token()` every run until real credentials are added later directly to Fly.io's secrets store (`fly secrets set`), at which point ingestion goes live with no redeploy required.
- **D-06:** The credentials-absent failure is not special-cased — it feeds the same staleness alert built for D-07/D-08 below. From first deploy, "no successful run yet" is indistinguishable from "stale" and the alert fires immediately (expected, since there are no real credentials yet). The alert self-resolves the moment real credentials are added and a run succeeds. This means there is exactly one failure/staleness code path to build, not two.

### Staleness Alert Channel
- **D-07:** Alerts are pushed via a Discord webhook, not email and not a manual-check-only status page. The threshold is ~2x the locked 4h polling interval (~8h since last successful `ingestion_runs` entry), per ROADMAP SC-3 and PITFALLS.md's "fail loud on zero-row/stale runs" guidance.
- **D-08:** User picked Discord specifically over Slack (no existing Slack workspace to reuse; a Discord webhook URL is simpler to stand up from scratch).

### Claude's Discretion
- Whether the API and ingestion worker are two process types in one Fly app or two separate Fly apps — a Fly.io deployment-shape detail, not a product decision.
- Exact Dockerfile structure (single multi-stage build vs. separate images for API vs. worker).
- Which static host (Vercel vs. Netlify vs. Cloudflare Pages) — not discussed; pick whichever integrates most simply with this repo, all three satisfy D-01/D-04 equally.
- Where the staleness-check logic lives — most natural is inside `ingest_worker.py` itself (query `ingestion_runs` for the last successful run after every scheduled attempt, POST to the Discord webhook if the gap exceeds threshold), avoiding a new deployable per the project's existing "no task broker / minimal services" constraint. A separate tiny check script is acceptable only if it turns out simpler to reason about.
- Exact Discord alert message content/formatting.
- CI/CD automation (e.g., GitHub Actions auto-deploy on push) — not discussed or requested; default to manual `fly deploy` / static-host CLI deploy for v1 unless it's trivial to wire up alongside the deployment work already being done.
- A `/health` or `/status` endpoint is NOT required — SC-3 only requires the Discord alert, not a dashboard. Don't build one unless it falls out naturally from the staleness-check implementation.
- gunicorn (recommended in STACK.md as the production WSGI server for Flask, not yet in `requirements.txt`) should be added as part of containerizing the API for Fly.io — standard production-Flask practice, not something that needed user input.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & success criteria
- `.planning/ROADMAP.md` §Phase 7 — the three success criteria this phase must satisfy (public URL reachability, unattended scheduled ingestion, staleness alert beyond ~2x polling interval).
- `.planning/PROJECT.md` — project-wide constraints this phase must respect: official eBay APIs only, no Celery/task-broker infrastructure, reasonable (not over-fragmented) microservice split.

### Ingestion scheduling & credentials (already locked, do not re-decide)
- `.planning/phases/03-active-listing-ingestion-pipeline/03-RESEARCH.md` — locks the 4-hour default polling interval (`INGESTION_INTERVAL_HOURS`) and its rationale (Browse API call budget headroom); locks `IntervalTrigger`/`BlockingScheduler`/MongoDB TTL-lock design already implemented.
- `.planning/phases/03-active-listing-ingestion-pipeline/03-05-SUMMARY.md` — records the still-open, explicitly-deferred live-credential verification (INGEST-01/02/03 never proven against real eBay data); this phase inherits that gap per D-05/D-06 rather than closing it.
- `.planning/STATE.md` §Blockers/Concerns — documents the original `.env` credential-loss incident; the note that `EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET`, and `EBAY_ENV=production` must be added before any live eBay call succeeds.
- `scripts/ingest_worker.py` — the existing `main()` with `--once` (manual/CI) and `BlockingScheduler`+`IntervalTrigger` (scheduled) entrypoints; this is what gets containerized and run as the Fly.io worker process, unmodified except for adding the staleness-check/alert call.
- `db/init_collections.py` — the `ingestion_runs` collection already records per-run metadata (start/end time, counts, errors); the staleness check reads its `ts`/status of the last successful run from here, no new collection needed.

### Operational/monitoring guidance
- `.planning/research/PITFALLS.md` — "Silent stale/failed pipeline runs" pitfall (fail loud on zero-row runs, alert if data hasn't updated in >2x the expected interval) and its mitigation, which D-07/D-08 directly implement.
- `.planning/research/STACK.md` — gunicorn as the recommended production WSGI server for the Flask API (not yet in `requirements.txt`); Waitress noted only as a Windows-specific alternative, not relevant here.
- `.planning/research/ARCHITECTURE.md` — confirms exactly three deployable units (ingestion worker cron/service, Flask API, static React build) — matches D-01's split-PaaS shape.

### Cross-origin / frontend-to-API wiring
- `api/app.py` and `api/config.py` — `CORS_ORIGINS` is already comma-split (Phase 5 CR-02) so adding the new production static-host domain is a config-only change, no code change.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `scripts/ingest_worker.py` — already has both a `--once` CLI flag (manual/CI runs) and a `BlockingScheduler`+`IntervalTrigger` scheduled entrypoint reading `INGESTION_INTERVAL_HOURS` from the environment. This is deployed as-is as the Fly.io worker process; only the staleness-check/Discord-alert call needs to be added.
- `api/app.py` `create_app()` — complete, tested, CORS-configurable via a comma-split `CORS_ORIGINS` env var. Ready to containerize and run under gunicorn with no application-code changes.
- `db/init_collections.py` — `ingestion_runs` collection already captures the fields (start/end time, counts) a staleness check needs to read.

### Established Patterns
- "Fail loud, never silent" runs through every prior phase (`no_data_yet`, `insufficient_data`, gap-preserving current price, explicit deferral records rather than silent skips). D-06/D-07 continue this pattern operationally: an auth failure or a stale run must be visible (Discord alert), never a quiet no-op.
- No top-level side effects on import (established in `scripts/ebay_client.py`, `scripts/matching.py`, `api/services/*.py`) — the staleness-check addition to `ingest_worker.py` should follow the same discipline (check happens inside the run function, not at module import time).

### Integration Points
- The Discord webhook call is new code, but has exactly one natural home: inside `ingest_worker.py`'s run loop, immediately after each scheduled attempt (success or failure), querying `ingestion_runs` for the last successful run and comparing against the ~8h threshold.
- `CORS_ORIGINS` on the deployed Flask API must include the new static-host production domain once assigned (Vercel/Netlify/Cloudflare Pages subdomain) — a deploy-config value, not a code change.

</code_context>

<specifics>
## Specific Ideas

- User deliberately went against the recommended option twice — Fly.io over Render/Railway, and Discord over Slack/email — both accepted as the locked choice; do not second-guess these in research/planning as "the recommendation said X."
- The credentials gap is a known, accepted launch condition, not a blocker to route around with workarounds (e.g. no mocked/fake eBay data — the worker should genuinely attempt and genuinely fail until real credentials exist).

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. A custom domain (D-04) and CI/CD auto-deploy (Claude's Discretion) were both explicitly deferred as "not now, not blocking, can add later" rather than being out of scope entirely — worth revisiting post-launch if desired, but not part of this phase's plan.

</deferred>

---

*Phase: 7-Launch & Hardening (v1 active-price)*
*Context gathered: 2026-07-15*
