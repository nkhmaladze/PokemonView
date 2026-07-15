# Phase 7: Launch & Hardening (v1 active-price) - Research

**Researched:** 2026-07-15
**Domain:** PaaS deployment (Fly.io containers + static SPA host) and operational alerting for an already-complete Flask/MongoDB/React stack
**Confidence:** MEDIUM-HIGH (Fly.io mechanics and gunicorn/Discord patterns are well-documented and cross-corroborated; a small number of exact TOML schema details are inferred rather than directly fetched — see Assumptions Log)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Split-PaaS architecture, not a single VPS: Fly.io hosts the Flask API and the ingestion worker (two process types/machines under one Fly app or two small Fly apps — left to planning); the React SPA static build deploys separately to Vercel, Netlify, or Cloudflare Pages (planner's choice, whichever is simplest to wire to this repo). MongoDB stays on the existing Atlas M0 free tier — no change.
- **D-02:** User explicitly chose Fly.io over the recommended Render/Railway, accepting that this requires a Dockerfile (Fly.io is container-based; Render/Railway would have used native buildpacks). Plan for containerizing both the API and the ingestion worker.
- **D-03:** Budget ceiling is ~$5-15/mo on an always-on tier — explicitly not the free tier, because a sleeping/cold-starting dyno would silently break the 4h ingestion cadence (`INGESTION_INTERVAL_HOURS` default, already locked in Phase 3). The API and worker must not scale-to-zero.
- **D-04:** No custom domain for v1 — platform-provided subdomains are fine (`*.fly.dev` for the API, whatever the static host issues for the SPA). HTTPS is automatic on all three candidate platforms; no certificate work needed. A custom domain can be added later without being a blocker now.
- **D-05:** `EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET` are still absent and the user does not have replacement values yet. Phase 7 deploys the full stack now anyway — do not block launch on obtaining credentials first. The ingestion worker will fail at `get_app_token()` every run until real credentials are added later directly to Fly.io's secrets store (`fly secrets set`), at which point ingestion goes live with no redeploy required.
- **D-06:** The credentials-absent failure is not special-cased — it feeds the same staleness alert built for D-07/D-08. From first deploy, "no successful run yet" is indistinguishable from "stale" and the alert fires immediately (expected). The alert self-resolves the moment real credentials are added and a run succeeds. Exactly one failure/staleness code path, not two.
- **D-07:** Alerts are pushed via a Discord webhook, not email and not a manual-check-only status page. Threshold is ~2x the locked 4h polling interval (~8h since last successful `ingestion_runs` entry).
- **D-08:** User picked Discord specifically over Slack (no existing Slack workspace to reuse; a Discord webhook URL is simpler to stand up from scratch).

### Claude's Discretion

- Whether the API and ingestion worker are two process types in one Fly app or two separate Fly apps — a deployment-shape detail, not a product decision.
- Exact Dockerfile structure (single multi-stage build vs. separate images for API vs. worker).
- Which static host (Vercel vs. Netlify vs. Cloudflare Pages) — pick whichever integrates most simply with this repo.
- Where the staleness-check logic lives — most natural is inside `ingest_worker.py` itself, avoiding a new deployable.
- Exact Discord alert message content/formatting.
- CI/CD automation — not discussed or requested; default to manual `fly deploy` / static-host CLI deploy for v1.
- A `/health` or `/status` endpoint is NOT required — don't build one unless it falls out naturally.
- gunicorn should be added as part of containerizing the API for Fly.io — standard production-Flask practice.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope. A custom domain (D-04) and CI/CD auto-deploy (Claude's Discretion) were both explicitly deferred as "not now, not blocking, can add later" rather than being out of scope entirely.
</user_constraints>

## Summary

Phase 7 is pure operational plumbing on top of an already-complete, already-tested application: containerize the existing `api/app.py` (Flask, gunicorn) and `scripts/ingest_worker.py` (APScheduler `BlockingScheduler`) into **one Docker image, run as two Fly.io process types under one Fly app** (`web` and `worker`), sized on `shared-cpu-1x` with `min_machines_running=1` and autostop disabled so neither machine ever scales to zero. The React SPA is a static Vite build that deploys independently to **Vercel** (CLI-based `vercel --prod`, simplest auto-detection for Vite, no GitHub wiring required even though this repo already has a GitHub remote pushed). Secrets (`EBAY_CLIENT_ID`, `EBAY_CLIENT_SECRET`, `MONGODB_URI`, `DISCORD_WEBHOOK_URL`, `CORS_ORIGINS`) are injected via `fly secrets set`, which triggers an automatic rolling machine restart with no `fly deploy`/rebuild needed — this is exactly the "no redeploy required" behavior D-05 depends on.

The staleness check requires zero new infrastructure: `ingestion_runs` already has a descending index on `started_at` (`db/init_collections.py`) built for exactly this query. A small function added to `scripts/ingest_worker.py`, called once per scheduled attempt right after `run_ingestion_once()` finalizes its run document, queries the most recent `status in {"success","partial"}` run, computes the gap in hours, and POSTs a plain `requests.post(webhook_url, json={"content": ...})` to the Discord webhook if the gap exceeds ~8h. Because `get_app_token()` failures (missing eBay credentials) are already caught by the existing outer `except Exception` in `run_ingestion_once()` and recorded as `status="failed"` — never `"success"`/`"partial"` — the credentials-absent state naturally produces "no successful run found" without any special-casing, satisfying D-06 with the existing code as-is.

**Primary recommendation:** One Fly app, one Docker image, two process types (`web` running gunicorn against a new `wsgi.py`, `worker` running `python -m scripts.ingest_worker`); `min_machines_running=1` + `auto_stop_machines="off"` on both; deploy the SPA to Vercel via CLI; add a single `check_and_alert_staleness(db)` function inside `ingest_worker.py`, called after every scheduled run.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Flask API serving | API/Backend | — | Existing `create_app()` factory, now run under gunicorn on a Fly Machine; no application code changes |
| Ingestion worker scheduling | API/Backend (background process) | — | `scripts/ingest_worker.py`'s existing `BlockingScheduler`, run as a separate Fly process type with no HTTP surface |
| Staleness detection & alerting | API/Backend (background process) | — | Lives inside the worker's existing scheduled loop; reads `ingestion_runs`, no new service |
| Static SPA hosting | CDN/Static | — | Prebuilt Vite `dist/` served from Vercel's edge network; SPA never touches MongoDB directly (unchanged from Phase 6) |
| Secrets management | API/Backend | — | Fly's encrypted secrets store injects env vars into Machines at boot; static host has its own separate env var store for `VITE_*` build-time values |
| CORS enforcement | API/Backend | Browser/Client | `CORS_ORIGINS` env var on the Fly-hosted API must include the static host's production origin; browser enforces the resulting preflight/response headers |
| Data persistence | Database/Storage | — | MongoDB Atlas M0, unchanged; only its Network Access / IP Access List configuration is newly relevant now that a public Fly Machine, not a developer laptop, connects to it |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| gunicorn | 26.0.0 `[VERIFIED: PyPI registry — pip index versions, published 2026-05-05]` [SUS — see Package Legitimacy Audit] | Production WSGI server for the Flask API under Fly.io | Standard pre-fork WSGI server for containerized Flask; already recommended in `.planning/research/STACK.md`, just not yet installed |
| Fly.io (flyctl CLI) | current (`fly` CLI, remote builder default) `[CITED: fly.io/docs]` | Container hosting platform for the API + worker | Locked by D-01/D-02 — user's explicit choice over Render/Railway |
| Vercel CLI | `vercel@latest` (npm global, e.g. 56.2.0 `[VERIFIED: npm registry]` [SUS — see audit, false-positive "too-new" pattern]) | Static SPA deploy target | Auto-detects Vite projects with zero config; simplest of the three candidates to wire to a repo that may or may not use git-integration |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| requests | 2.34.2 (already pinned in `requirements.txt`) `[VERIFIED: repo file]` | HTTP client for the Discord webhook POST | Already a project dependency (used by `scripts/ebay_client.py`) — no new install needed for D-07/D-08 |
| Docker | 24.x+ (only needed if building locally; Fly's remote builder makes this optional) `[CITED: fly.io/docs, msfjarvis.dev]` | Container image build | Fly.io is container-based per D-02; local Docker is a convenience, not a hard requirement (see Environment Availability) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| One Fly app with two process types | Two separate Fly apps (`pokemonview-api`, `pokemonview-worker`) | Cleaner blast-radius isolation (a bad `fly deploy` to one doesn't touch the other) and independent scaling, but doubles the app-management surface (two sets of secrets to keep in sync, two `fly.toml`s) for a project whose constraints explicitly favor minimal service fragmentation. One app is the better fit here. |
| Single-stage Dockerfile | Multi-stage Dockerfile (builder stage + slim runtime stage) | Multi-stage trims final image size, but this app has no compiled/native build step of its own (pymongo, rapidfuzz ship prebuilt wheels for common platforms) — the size savings are marginal for a project this small; single-stage is simpler to read and debug. |
| Vercel | Netlify CLI (`ntl deploy`) or Cloudflare Pages (`wrangler pages deploy dist`) | Both are equally valid; Netlify needs an extra `ntl init` step, Cloudflare needs explicit `wrangler login` plus is oriented around Workers/edge-function use cases this project doesn't need. Vercel's plain `vercel` autodetection is the least amount of new tooling to learn for a one-time static deploy. |
| "Allow Access from Anywhere" (0.0.0.0/0) on MongoDB Atlas Network Access | `fly machine egress-ip allocate` (static/dedicated egress IP) + a tight Atlas allowlist entry | Static egress IP is more defensible security posture, but it is an additional Fly.io line item and additional setup step; given MongoDB Atlas connection strings already require username/password auth as the real access-control layer, and this project's budget/complexity constraints, "Allow Access from Anywhere" is the pragmatic v1 default — flag to the user as a discretionary hardening item, not a blocker. |

**Installation:**
```bash
# Add to requirements.txt
gunicorn==26.0.0

# Static host CLI (dev-time tool, not a project dependency)
npm install -g vercel
```

**Version verification:** `pip index versions gunicorn` returned `26.0.0` as latest (published 2026-05-05) — confirmed directly against the PyPI registry in this research session. `npm view vercel version` returned `56.2.0` (published 2026-07-14) — confirmed directly against the npm registry.

## Package Legitimacy Audit

| Package | Registry | Age | Downloads | Source Repo | Verdict | Disposition |
|---------|----------|-----|-----------|-------------|---------|-------------|
| gunicorn | PyPI | latest release 2026-05-05; project itself is 15+ years old | unknown (telemetry gap in the legitimacy tool, not a real signal — same class of false positive already approved for pymongo/apscheduler/rapidfuzz/flask/flask-cors in this project's history) | `gunicorn.org` (project's canonical site, not a github.com URL in the tool's `repoUrl` field but the package is the well-known, ubiquitous `gunicorn` WSGI server) | SUS (`unknown-downloads`) | Flagged — planner must add `checkpoint:human-verify` before install, per protocol. Given the identical false-positive pattern already human-approved 5 times in this project's STATE.md history, expect approval, but the gate must still run. |
| vercel (npm, CLI tool) | npm | latest release 2026-07-14 (yesterday relative to research date — rolling release cadence, not a new/risky package) | 2,734,477/week `[VERIFIED: npm registry]` | `github.com/vercel/vercel` | SUS (`too-new`, false positive from continuous-release cadence) | Flagged — planner must add `checkpoint:human-verify` before global install, though 2.7M weekly downloads + official Vercel org repo make this an extremely low-risk approval. |

**Packages removed due to [SLOP] verdict:** none.
**Packages flagged as suspicious [SUS]:** gunicorn (pypi), vercel (npm, CLI tool). Both are almost certainly false positives from the legitimacy tool's download-telemetry gaps, matching a pattern already seen and approved repeatedly in this project (Phase 2-06), but the planner must still insert a `checkpoint:human-verify` task before each install per protocol.

## Architecture Patterns

### System Architecture Diagram

```
                         Developer machine (manual deploy, no CI/CD for v1)
                                    │
                    ┌───────────────┼────────────────────┐
                    │ fly deploy    │      vercel --prod  │
                    ▼               │                    ▼
        ┌───────────────────────┐   │      ┌─────────────────────────┐
        │   Fly.io app           │  │      │   Vercel static host     │
        │  (one Docker image,    │  │      │  (Vite build → dist/)    │
        │   two process types)   │  │      │  https://<x>.vercel.app  │
        │                        │  │      └────────────┬─────────────┘
        │  ┌──────────────────┐  │  │                   │
        │  │ web (gunicorn)   │◀─┼──┘   HTTPS/JSON       │  React SPA served
        │  │ https://x.fly.dev│◀─┼───────────────────────┘  to end-user browser
        │  └─────────┬────────┘  │
        │            │ pymongo   │
        │  ┌─────────▼────────┐  │
        │  │ worker            │  │
        │  │ (BlockingScheduler,│ │
        │  │  every 4h)         │ │
        │  └─────────┬─────────┘ │
        └────────────┼───────────┘
                      │ pymongo reads/writes           ┌─────────────────────┐
                      ▼                                │ Discord webhook       │
        ┌───────────────────────────┐   after each run │ (stale-alert channel) │
        │ MongoDB Atlas M0           │◀──queries────────│                       │
        │ products / active_listings │   ingestion_runs └─────────────────────┘
        │ / price_points / ingestion_runs
        └───────────────────────────┘
```

### Recommended Project Structure

```
PokemonView/
├── Dockerfile                # NEW — single image, shared by both process types
├── fly.toml                  # NEW — [processes] web + worker, http_service on web only
├── wsgi.py                   # NEW — `app = create_app()` module-level entrypoint for gunicorn
├── api/                      # unchanged
├── scripts/
│   └── ingest_worker.py      # + check_and_alert_staleness() addition, no other changes
├── frontend/                 # unchanged; deployed independently, not part of the Docker image
│   └── .env.production       # NEW — VITE_API_BASE_URL=https://<fly-app>.fly.dev
└── requirements.txt          # + gunicorn==26.0.0
```

### Pattern 1: One Fly app, one image, two process types via `fly.toml [processes]`

**What:** Define both process groups in a single `fly.toml`; each runs the same built image with a different start command. Fly schedules each process group onto its own Fly Machine(s) — they don't share memory/CPU and can be scaled independently, but they deploy together with a single `fly deploy`.
**When to use:** When both processes share the same dependency footprint (they do here — `requirements.txt` covers both Flask/gunicorn and APScheduler/pymongo) and there's no reason to version them independently.
**Example:**
```toml
# Source: fly.io/docs/app-guides/multiple-processes/, fly.io/docs/launch/processes/
app = "pokemonview"
primary_region = "iad"

[build]

[processes]
web = "gunicorn --bind 0.0.0.0:8080 --workers 1 --timeout 30 wsgi:app"
worker = "python -m scripts.ingest_worker"

[http_service]
internal_port = 8080
processes = ["web"]          # this service block applies ONLY to the web process group
force_https = true
auto_stop_machines = "off"    # D-03: never scale to zero
auto_start_machines = false
min_machines_running = 1

[[vm]]
size = "shared-cpu-1x"
memory = "512mb"
# Fly's default `fly launch` scaffolding applies a top-level [[vm]] to every
# process group unless a per-group override is added. [ASSUMED — verify the
# exact per-process-group vm-override syntax against `fly config validate`
# at execution time; this session could not directly fetch the canonical
# current TOML schema reference to confirm nested per-group vm blocks.]
```

**Note on the `worker` process group:** it deliberately has no `[[services]]`/`http_service` entry — it isn't proxied, receives no inbound traffic, and therefore needs no health check route. Fly still keeps it running under `min_machines_running`/machine restart policy; if the process crashes, Fly restarts the Machine automatically (no custom supervisor needed).

### Pattern 2: `wsgi.py` as the gunicorn entrypoint for an application-factory Flask app

**What:** `api/app.py`'s `create_app()` must be called somewhere to produce a WSGI-callable `app` object; gunicorn's CLI expects `module:variable`, not a factory function call by default.
**When to use:** Any time an app-factory pattern (like this repo's) is put behind gunicorn.
**Example:**
```python
# wsgi.py — NEW file, project root
"""Gunicorn entrypoint. Reads MONGODB_URI/CORS_ORIGINS from the environment
via create_app()'s existing defaults — no new config surface."""
from api.app import create_app

app = create_app()
```
```bash
gunicorn --bind 0.0.0.0:8080 --workers 1 --timeout 30 wsgi:app
```

### Pattern 3: Discord staleness alert as a stateless, best-effort POST inside the existing scheduled loop

**What:** After every scheduled `run_ingestion_once()` completes (success, partial, or failed), query the most recent `status in {"success","partial"}` `ingestion_runs` document, compute the freshness gap, and POST a Discord alert if it exceeds threshold. No new collection, no debounce/dedup state — if still stale next run (4h later), it alerts again.
**When to use:** Exactly this phase's D-06/D-07 requirement — a single, always-executed check, not a separate scheduled job.
**Example:**
```python
# scripts/ingest_worker.py — additions

import requests

STALENESS_THRESHOLD_HOURS = 8  # ~2x INGESTION_INTERVAL_HOURS default (4h), per D-07


def check_and_alert_staleness(db, threshold_hours: float = STALENESS_THRESHOLD_HOURS) -> None:
    """Query ingestion_runs for the most recent successful/partial run and
    POST a Discord alert if the gap since then exceeds threshold_hours.

    Called once per scheduled ingestion attempt, right after
    run_ingestion_once() finalizes its run document (D-06/D-07) — no new
    collection, no new scheduled job, no debounce state. A missing
    DISCORD_WEBHOOK_URL or a Discord-side network failure never raises —
    this check must never crash the ingestion worker (Pattern established
    by run_ingestion_once's own per-product isolation).
    """
    last_good = db.ingestion_runs.find_one(
        {"status": {"$in": ["success", "partial"]}},
        sort=[("started_at", -1)],
    )
    now = datetime.now(timezone.utc)
    if last_good is None:
        gap_hours = float("inf")
        last_desc = "no successful run yet"
    else:
        last_ts = last_good.get("finished_at") or last_good["started_at"]
        gap_hours = (now - last_ts).total_seconds() / 3600
        last_desc = f"{gap_hours:.1f}h ago ({last_ts.isoformat()})"

    if gap_hours <= threshold_hours:
        return

    webhook_url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        return  # not configured yet — never crash the worker over it

    message = (
        f":rotating_light: PokemonView ingestion stale — last successful "
        f"run: {last_desc}. Threshold: {threshold_hours}h."
    )
    try:
        requests.post(webhook_url, json={"content": message}, timeout=10)
    except requests.RequestException:
        pass  # Discord outage must never crash the ingestion worker
```

Wired into `main()`'s scheduled path:
```python
def scheduled_job(db):
    run_ingestion_once(db)
    check_and_alert_staleness(db)

scheduler.add_job(
    scheduled_job,
    trigger=IntervalTrigger(hours=interval_hours),
    args=[db],
    max_instances=1,
    coalesce=True,
    misfire_grace_time=300,
)
```

### Anti-Patterns to Avoid

- **Running gunicorn with multiple workers on the same process that also imports/runs APScheduler:** APScheduler's in-memory scheduler is not safe across multiple worker processes (each fork would run its own independent scheduler, firing the ingestion job N times per interval instead of once). This is a non-issue here specifically *because* `web` (gunicorn) and `worker` (`python -m scripts.ingest_worker`) are already separate Fly process types — never merge them into one gunicorn-managed process.
- **Setting `fly.toml` defaults and assuming always-on:** `fly launch`'s default scaffold is `auto_stop_machines = "stop"`, `auto_start_machines = true`, `min_machines_running = 0` — the exact scale-to-zero behavior D-03 forbids. This must be explicitly overridden, not left at defaults.
- **Baking the API's URL into the SPA at runtime instead of build time:** Vite's `import.meta.env.VITE_*` values are inlined into the static bundle at `npm run build` time, not read at runtime in the browser. If the Fly API's `.fly.dev` URL is only known after the first `fly deploy`, the frontend build (and its Vercel deploy) must happen *after*, using that URL as `VITE_API_BASE_URL` — changing it later requires a full SPA rebuild+redeploy, not just an env var tweak.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Environment variable / secret storage | A custom `.env`-on-server or config-file-in-image mechanism | `fly secrets set KEY=value` | Fly's secrets store is encrypted at rest, injected as real env vars at Machine boot, and updating a secret automatically triggers a rolling restart — exactly the "add later, no redeploy" behavior D-05 needs, already built in. |
| Process crash recovery / restart-on-failure | A custom supervisor process, systemd unit, or shell retry loop around `python -m scripts.ingest_worker` | Fly Machines' built-in restart policy | Fly already restarts a Machine whose process exits; the worker process type needs no extra supervision layer. |
| Liveness/health checking for the API | A hand-built `/health` route just to satisfy a platform requirement | Fly's default TCP-level check on `http_service.internal_port` | Confirmed via CONTEXT.md discretion: a custom `/health` endpoint is explicitly not required for v1; Fly's proxy already verifies the port is accepting connections without any app-level route. |
| Discord alert delivery reliability (retries, queuing) | A retry queue or background delivery guarantee for the webhook POST | A single best-effort `requests.post(..., timeout=10)` wrapped in try/except | The check re-runs every scheduled interval (4h) regardless of whether the previous alert delivered — a failed Discord POST self-heals on the next run; building guaranteed-delivery infrastructure for a low-stakes ops alert is over-engineering for this project's "minimal services" constraint. |

**Key insight:** Every piece of "hardening" infrastructure this phase needs (secrets, restart-on-crash, health checking) is a platform feature Fly.io already provides for free once the two process types are correctly declared — the only genuinely new code is the ~20-line staleness-check function itself.

## Common Pitfalls

### Pitfall 1: `fly launch` defaults silently allow scale-to-zero

**What goes wrong:** A fresh `fly launch` scaffolds `auto_stop_machines = "stop"`, `auto_start_machines = true`, `min_machines_running = 0` in `fly.toml` by default. Left unchanged, both the `web` and `worker` Machines will stop during low-traffic/idle periods — for the worker this is catastrophic, since a stopped worker Machine simply never fires its next scheduled ingestion run, and nothing restarts it until inbound traffic arrives (which a worker process type, with no `http_service`, never receives).
**Why it happens:** These are the tool's sensible cost-saving defaults for typical web apps, but they directly contradict D-03's always-on requirement, especially for the worker.
**How to avoid:** Explicitly set `auto_stop_machines = "off"` (or `"suspend"`/`"stop"` + `min_machines_running >= 1`, per Fly's own guidance that these two settings should be enabled/disabled together) on both process groups' service config, and verify with `fly status`/`fly machine list` after first deploy that both Machines show as continuously running, not stopped-with-autostart.
**Warning signs:** `fly machine list` shows a Machine in `stopped` state hours after deploy with no recent restart; `ingestion_runs` gap grows well past 4h even though credentials are valid.

### Pitfall 2: `python -m scripts.ingest_worker`'s `main()` does not crash on missing eBay credentials — verify this is actually desired, not a bug

**What goes wrong (if misunderstood):** A planner unfamiliar with the existing code might assume "the worker will crash-loop until real credentials are added" and try to add defensive credential-checking at startup. This is unnecessary: `get_app_token()` is called *inside* `run_ingestion_once()`'s outer `try/except Exception`, so a missing/invalid eBay credential raises there, is caught, and is recorded as `status="failed"` in `ingestion_runs` — the scheduler process itself keeps running and fires the next interval normally.
**Why it happens:** Without reading `run_ingestion_once()` closely, "credentials missing" and "worker won't start" look like the same failure mode; they are not.
**How to avoid:** No code change needed for D-05/D-06 beyond adding `check_and_alert_staleness()` — confirm via a manual `--once` run with intentionally-blank `EBAY_CLIENT_ID`/`SECRET` that the run document lands with `status="failed"` and the process exits 0 (for `--once`) / keeps scheduling (for the scheduled path).
**Warning signs:** If this assumption were wrong, `fly machine list` would show the `worker` Machine repeatedly restarting (crash-loop) rather than staying `started`.

### Pitfall 3: MongoDB Atlas IP Access List and Fly.io's non-static outbound IPs

**What goes wrong:** MongoDB Atlas defaults to denying all connections until an IP (or CIDR) is explicitly allow-listed. Fly.io Machines do not have a stable, predictable outbound IP by default — even allocating a dedicated inbound IPv4 for the app does not guarantee a matching stable *outbound* IP for the MongoDB connection. A deploy that "works from my laptop" (laptop's IP is allow-listed) can then fail in production with a connection-refused/timeout error against Atlas.
**Why it happens:** Developers commonly allow-list only their own development IP during local testing and forget Atlas's access list is per-source-IP, not per-credential.
**How to avoid:** Either (a) set Atlas's Network Access to "Allow Access from Anywhere" (`0.0.0.0/0`) — pragmatic default for a v1 given MongoDB's username/password auth remains the real access-control layer, and Fly's Machine IPs are otherwise unpredictable — or (b) allocate a Fly static egress IP (`fly machine egress-ip allocate`) and allow-list exactly that IP/CIDR in Atlas for tighter security at a small additional cost. Recommend (a) for v1 given the $5-15/mo budget ceiling; flag (b) as a follow-up hardening item.
**Warning signs:** API/worker logs show MongoDB connection timeouts in production that never reproduce locally; Atlas's "Network Access" tab shows only a stale developer-laptop IP entry.

### Pitfall 4: Vite `VITE_*` env vars are compiled into the static bundle at build time, not read at runtime

**What goes wrong:** Setting `VITE_API_BASE_URL` in Vercel's dashboard/CLI *after* a build has already run has no effect on that build's output — the value is inlined into the JS bundle by `vite build`, not read from the browser's environment at page-load time. If the Fly API's URL isn't known yet when the frontend is first built, the deployed SPA will call the wrong (or a placeholder) API URL until rebuilt.
**Why it happens:** This is different from most other "env var" mental models (like Fly secrets, which genuinely are read at process-start time) — it's easy to assume all env vars behave the same way.
**How to avoid:** Sequence the deploy: (1) `fly deploy` the API first and note its `https://<app>.fly.dev` URL, (2) set that as `VITE_API_BASE_URL` in a `frontend/.env.production` (or Vercel's project env var UI) before running the frontend build, (3) `vercel --prod` (which runs `vite build` itself, or run `npm run build` locally first, depending on chosen deploy flow).
**Warning signs:** The deployed SPA's network tab shows requests going to `localhost` or an old/placeholder API URL despite the API itself working correctly when hit directly.

### Pitfall 5: `CORS_ORIGINS` must be updated (and Fly must restart) after the static host's real subdomain is known

**What goes wrong:** The Flask API's `CORS_ORIGINS` env var (already comma-split-aware per Phase 5 CR-02) must include the SPA's actual production origin (e.g. `https://pokemonview.vercel.app`) or the browser will block API responses with a CORS error, even though the request itself succeeds server-side (visible in Fly logs as 200s that the browser still rejects).
**Why it happens:** The static host's exact subdomain is only assigned during/after its first deploy — it can't be known and set into `CORS_ORIGINS` beforehand.
**How to avoid:** Deploy the SPA first (or accept a two-step CORS update), note its assigned subdomain, then `fly secrets set CORS_ORIGINS=https://pokemonview.vercel.app` (comma-separate if multiple origins, e.g. a Vercel preview + prod domain) — this triggers Fly's automatic rolling restart with no `fly deploy` needed, same mechanism as D-05's credential injection.
**Warning signs:** Browser DevTools console shows `blocked by CORS policy` while the Fly API's own logs show the request was received and returned 200.

## Code Examples

### Dockerfile (single image, shared by both process types)

```dockerfile
# Source: pattern synthesized from fly.io/docs/languages-and-frameworks/dockerfile/
# and github.com/fly-apps/hello-gunicorn-flask
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Fallback only — fly.toml's [processes] block supplies the real
# per-process-type command ("web" vs "worker"); this CMD is never used
# once fly.toml defines [processes].
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--timeout", "30", "wsgi:app"]
```

### `fly secrets set` for all required env vars (no redeploy — D-05)

```bash
# Source: fly.io/docs/apps/secrets/, fly.io/docs/flyctl/secrets/
fly secrets set \
  MONGODB_URI="mongodb+srv://..." \
  CORS_ORIGINS="https://pokemonview.vercel.app" \
  DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..." \
  --app pokemonview

# Later, once real eBay credentials exist (D-05) — triggers an automatic
# rolling restart of both "web" and "worker" Machines, no `fly deploy` needed:
fly secrets set EBAY_CLIENT_ID="..." EBAY_CLIENT_SECRET="..." --app pokemonview
```

### Vercel CLI deploy for the Vite SPA

```bash
# Source: vite.dev/guide/static-deploy, vercel CLI --help
cd frontend
npm install -g vercel   # one-time
vercel --prod           # auto-detects Vite; builds and deploys dist/
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| Fly.io free tier (a few free shared-cpu-256mb Machines) | No free tier for Machines/Postgres/bandwidth | Discontinued 2024 | Directly explains why D-03's $5-15/mo floor exists — there is no $0 always-on option on Fly.io anymore; budgeting for it explicitly (as CONTEXT.md already does) is correct, not overcautious. |
| `flask run` dev server in production | gunicorn (or another real WSGI server) fronting the Flask app | Long-standing Flask best practice, not new in 2026 | This phase is what actually adds gunicorn to `requirements.txt` for the first time in this project — `.planning/research/STACK.md` already recommended it in Phase 5 but it was explicitly deferred to this phase. |
| Manually tracking a laptop's IP for MongoDB Atlas Network Access | Either "Allow Access from Anywhere" or Fly static egress IP allocation | N/A — this is the first phase where the app's own server (not a developer laptop) connects to Atlas | Local development's IP-allowlist habits don't transfer to a PaaS-hosted always-on service; this must be explicitly reconfigured in Atlas, not assumed to already work. |

**Deprecated/outdated:**
- Free-tier Fly.io Machines: no longer exist as of 2024 — do not plan around a $0 tier.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Exact `fly.toml` syntax for assigning a different `[[vm]]` size per process group (vs. one top-level `[[vm]]` applying to all groups) | Architecture Patterns, Pattern 1 | Low — worst case, both process groups just share the same `shared-cpu-1x`/512mb size (already the plan's default), so this only affects a possible future cost-optimization, not correctness. Planner should confirm current syntax via `fly config validate` or `fly launch`'s interactive scaffold during Wave 0, since this was not directly fetched from an authoritative doc source in this session. |
| A2 | MongoDB Atlas M0 (free tier) supports the same Network Access / IP Access List configuration UI as paid tiers, including "Allow Access from Anywhere" | Pitfall 3, Alternatives Considered | Low — M0 has historically supported the same Network Access tab as paid clusters; if this has changed, the fallback is simply allow-listing Fly's specific egress IP(s) instead. |
| A3 | Vercel is the "simplest to wire" static host recommendation, ahead of Netlify/Cloudflare Pages | Standard Stack, Alternatives Considered | Low — this is a discretionary choice explicitly left to the planner/researcher in CONTEXT.md; Netlify or Cloudflare Pages would work equally well if the planner prefers either for other reasons (e.g. existing account). |
| A4 | `fly secrets set` (without `--stage`) triggers an automatic rolling Machine restart that constitutes "going live" without a manual `fly deploy` step | Summary, Common Pitfalls, Code Examples | Medium — if this behavior differs from what's described (e.g. requires a manual `fly deploy` after all), D-05's "no redeploy required" expectation would need a one-line correction in the runbook (`fly deploy` after `fly secrets set`) rather than a design change. Low implementation risk, but should be confirmed with a real `fly secrets set` call against a deployed app during execution. |

**If this table is empty:** N/A — assumptions listed above should be spot-checked against live `fly` CLI output during Wave 0/plan execution rather than blocking planning now.

## Open Questions

1. **Should the Discord staleness alert debounce/dedupe, or re-fire every scheduled interval while stale?**
   - What we know: D-07/D-08 specify a threshold and a channel, not a dedup policy.
   - What's unclear: Whether re-alerting every 4h while stale (the simplest, stateless option) will be considered noisy in practice, especially during the expected initial period where credentials are absent (D-05) and every run alerts.
   - Recommendation: Ship the simple stateless version (alert every time the check finds staleness) for v1 — it requires no new state/collection, and the "expected initial noise until credentials land" is explicitly accepted by D-06. Revisit with a "last alerted at" flag only if it proves annoying in practice.

2. **One Fly app vs. two Fly apps for `web`/`worker`?**
   - What we know: Both are supported natively by `fly.toml [processes]`; CONTEXT.md leaves this to the planner.
   - What's unclear: Nothing blocking — this is purely a maintainability/blast-radius tradeoff (see Alternatives Considered).
   - Recommendation: One app, two process types — matches this project's established "minimal service fragmentation" pattern (already applied to the ingestion/matching boundary in `.planning/research/ARCHITECTURE.md`) and halves the secrets/config management surface.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `flyctl`/`fly` CLI | Deploying the API + worker to Fly.io | ✗ | — | Install via `curl -L https://fly.io/install.sh \| sh` (or `brew install flyctl` on macOS) before first `fly launch` |
| Docker | Building the container image locally | ✗ | — | Not required — Fly's remote builder (the CLI's default behavior) builds the image on Fly's own infrastructure from source, no local Docker daemon needed |
| Node.js / npm | Building the Vite SPA and running the Vercel CLI | ✓ | Node v24.17.0, npm 11.13.0 | — |
| Python | Local testing of `ingest_worker.py` changes before deploy | ✓ | 3.12.13 | — |
| Vercel CLI | Static SPA deploy | ✗ | — | `npm install -g vercel` (npm already available) |
| Git remote / GitHub push | Optional git-integration deploy path for the static host | ✓ | Repo already has an `origin` remote pushed to GitHub (`nkhmaladze/PokemonView`, `main` branch present) | Not required — CLI-based deploy (`vercel --prod`) works independently of git integration, but the option to instead connect Vercel/Netlify/Cloudflare Pages to the existing GitHub repo via their dashboards is also available if preferred later for auto-deploy-on-push |

**Missing dependencies with no fallback:** none — every missing local tool (`flyctl`, Docker, `vercel` CLI) has a documented, low-friction install/fallback path above.

**Missing dependencies with fallback:**
- `flyctl` CLI — install script, one-time
- Docker — not actually required due to Fly's remote builder
- `vercel` CLI — `npm install -g vercel`, one-time (subject to the `checkpoint:human-verify` flag in the Package Legitimacy Audit)

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 (already configured, `pytest.ini`: `testpaths = tests`) |
| Config file | `pytest.ini` |
| Quick run command | `pytest tests/test_ingest_worker.py -x` (or a new `tests/test_staleness_alert.py`) |
| Full suite command | `pytest` |

### Phase Requirements → Test Map

Phase 7 owns no REQUIREMENTS.md IDs (operational readiness only), so this maps to the phase's own success criteria (SC-1/2/3 from ROADMAP.md) rather than REQ-IDs:

| Behavior | Test Type | Automated Command | File Exists? |
|----------|-----------|-------------------|-------------|
| `check_and_alert_staleness()` finds no successful run → treats as infinitely stale, posts alert | unit | `pytest tests/test_staleness_alert.py::test_no_successful_run_alerts -x` | ❌ Wave 0 |
| `check_and_alert_staleness()` finds a recent successful run (gap < threshold) → does not POST | unit | `pytest tests/test_staleness_alert.py::test_fresh_run_no_alert -x` | ❌ Wave 0 |
| `check_and_alert_staleness()` finds a stale successful run (gap > threshold) → POSTs the expected Discord payload shape | unit | `pytest tests/test_staleness_alert.py::test_stale_run_posts_discord_payload -x` | ❌ Wave 0 |
| Missing `DISCORD_WEBHOOK_URL` → function returns without raising | unit | `pytest tests/test_staleness_alert.py::test_missing_webhook_url_noop -x` | ❌ Wave 0 |
| `requests.post` raising `RequestException` (simulated Discord outage) → swallowed, function does not raise | unit | `pytest tests/test_staleness_alert.py::test_discord_post_failure_swallowed -x` | ❌ Wave 0 |
| Manual/live: deployed API reachable at its `.fly.dev` URL over HTTPS | smoke (manual, one-time post-deploy check) | `curl -I https://<app>.fly.dev/products` | N/A — manual verification, not automatable pre-deploy |
| Manual/live: deployed SPA reachable at its static-host URL and successfully calls the API (no CORS error) | smoke (manual, one-time post-deploy check) | Browser DevTools network tab check | N/A — manual verification |

### Sampling Rate

- **Per task commit:** `pytest tests/test_staleness_alert.py -x`
- **Per wave merge:** `pytest` (full suite — confirms no regression in existing `test_ingest_worker.py` behavior)
- **Phase gate:** Full suite green, plus the two manual smoke checks above (public API URL reachable, SPA can call it without CORS errors) before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_staleness_alert.py` — new file covering `check_and_alert_staleness()`; can reuse the existing `ingest_db` fixture (real MongoDB test connection, per `tests/conftest.py`) to seed controlled `ingestion_runs` documents, and `unittest.mock.patch("scripts.ingest_worker.requests.post")` to assert payload shape without a real network call.
- [ ] No new fixtures needed beyond `ingest_db` — it already provides a clean `ingestion_runs` collection per test.
- [ ] Framework install: none — pytest already installed and configured.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V2 Authentication | No | This phase adds no user-facing authentication surface |
| V3 Session Management | No | No sessions introduced |
| V4 Access Control | No | No new access-control surface (API's existing route-level behavior unchanged) |
| V5 Input Validation | No | No new input surface — the staleness check reads only its own DB query results, never external/user input |
| V6 Cryptography / Transport Security | Yes | HTTPS is automatic and enforced on Fly.io (`force_https = true` in `http_service`) and on all three static-host candidates — no manual TLS/certificate configuration needed, matching D-04 |
| V7 Error Handling & Logging | Yes | Existing credential-hygiene discipline (never log `MONGODB_URI`, raw eBay tokens, or the Discord webhook URL) must extend to the new staleness-check code path — the Discord alert message itself must never include secret values, only counts/timestamps |
| V14 Configuration / Secrets Management | Yes | `fly secrets set` (encrypted secrets store, injected as env vars at boot) is the standard control — never bake `EBAY_CLIENT_ID/SECRET`, `MONGODB_URI`, or `DISCORD_WEBHOOK_URL` into the Docker image, `fly.toml`, or source code |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|----------------------|
| Secret leakage into Docker image layers or git history via a hardcoded `fly.toml`/`.env` committed alongside the Dockerfile | Information Disclosure | Never commit real secret values; use `fly secrets set` exclusively; add a `.dockerignore` excluding any local `.env` file from the build context |
| Discord webhook URL treated as non-sensitive and logged/echoed in worker stdout for debugging | Information Disclosure | Treat `DISCORD_WEBHOOK_URL` with the same hygiene as `MONGODB_URI`/eBay credentials already established in this codebase's docstring conventions — never print it, even in a "here's what I'm about to POST" debug line |
| Overly permissive MongoDB Atlas Network Access (`0.0.0.0/0`) reasoned about as "temporary" but never revisited | Elevation of Privilege / Information Disclosure | Document it explicitly as a v1 pragmatic tradeoff (this research does so — see Pitfall 3) rather than an oversight, so it's a deliberate, revisitable decision, not silent scope creep |

## Sources

### Primary (HIGH confidence)
- [App configuration (fly.toml) · Fly Docs](https://fly.io/docs/reference/configuration/) — `[processes]`, `[http_service]`, `processes` filter syntax
- [Autostop/autostart Machines · Fly Docs](https://fly.io/docs/launch/autostop-autostart/) — `auto_stop_machines`/`auto_start_machines`/`min_machines_running` semantics
- [Secrets and Fly Apps · Fly Docs](https://fly.io/docs/apps/secrets/) — `fly secrets set` behavior, staged vs. immediate application
- [Health Checks · Fly Docs](https://fly.io/docs/reference/health-checks/) — default TCP-level checks on `http_service`
- [Vite — Deploying a Static Site](https://vite.dev/guide/static-deploy) — Vercel/Netlify/Cloudflare Pages CLI deploy flows for Vite

### Secondary (MEDIUM confidence)
- [Multiple processes inside a Fly.io app · Fly Docs](https://fly.io/docs/app-guides/multiple-processes/)
- [Run multiple process groups in an app · Fly Docs](https://fly.io/docs/launch/processes/)
- [Fly.io Resource Pricing · Fly Docs](https://fly.io/docs/about/pricing/) and [Fly.io Pricing Calculator](https://fly.io/calculator/) — `shared-cpu-1x` cost figures
- [Deploying applications to Fly.io without Docker](https://msfjarvis.dev/posts/deploying-applications-to-flyio-without-docker/) and [New & Improved Remote Builders — Fly.io Community](https://community.fly.io/t/new-improved-remote-builders/661)
- [Static egress IPs for machines — Fly.io Community](https://community.fly.io/t/static-egress-ips-for-machines/22004)
- [Configure IP Access List Entries — MongoDB Atlas Docs](https://www.mongodb.com/docs/atlas/security/ip-access-list/)
- [Best practices to use workers - Python / Docker — Fly.io Community](https://community.fly.io/t/best-practices-to-use-workers-python-docker/12614) — APScheduler + gunicorn worker-count interaction
- [Flask APScheduler Tips & Troubleshooting](https://viniciuschiele.github.io/flask-apscheduler/rst/tips.html) — single-worker constraint confirmation
- [gunicorn in Containers — Graywind](https://blog.graywind.org/posts/gunicorn-in-containers/) and [Deploying Python Applications with Gunicorn — Heroku Dev Center](https://devcenter.heroku.com/articles/python-gunicorn) — worker-count guidance for small containers
- [Python - Discord Webhooks Guide](https://birdie0.github.io/discord-webhooks-guide/tools/python.html) — payload shape, rate limits

### Tertiary (LOW confidence)
- [Fly.io Pricing 2026 — Kuberns](https://kuberns.com/blogs/flyio-pricing/) and other third-party pricing aggregator blogs (cross-checked against Fly's own pricing calculator, not solely relied upon)
- [GitHub - fly-apps/hello-gunicorn-flask](https://github.com/fly-apps/hello-gunicorn-flask) — example repo referenced but not directly fetched line-by-line in this session

## Metadata

**Confidence breakdown:**
- Standard stack (Fly.io mechanics, gunicorn, Discord webhook): HIGH — cross-corroborated across multiple official Fly docs pages and community threads, plus a live PyPI/npm registry check
- Architecture (one app/two process types, Dockerfile/wsgi.py pattern): HIGH — directly matches Fly's own documented multi-process pattern and this project's established "minimal service fragmentation" precedent
- Pitfalls (scale-to-zero defaults, Atlas IP allowlist, Vite build-time env vars, CORS sequencing): MEDIUM-HIGH — well-documented platform behaviors, but the exact `[[vm]]` per-process-group TOML syntax (A1) was not directly confirmed against a fetched canonical doc page in this session

**Research date:** 2026-07-15
**Valid until:** 30 days (Fly.io pricing/TOML schema and static-host CLI details can shift; re-verify `fly.toml` syntax against current docs at execution time if more than ~30 days have passed)

---
*Phase 7 research for: Launch & Hardening (v1 active-price)*
*Researched: 2026-07-15*
