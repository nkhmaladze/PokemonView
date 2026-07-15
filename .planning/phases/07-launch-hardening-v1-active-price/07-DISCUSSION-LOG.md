# Phase 7: Launch & Hardening (v1 active-price) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-15
**Phase:** 7-Launch & Hardening (v1 active-price)
**Areas discussed:** Hosting & deployment target, eBay credentials blocker, Staleness alert channel, Domain & HTTPS

---

## Hosting & deployment target

| Option | Description | Selected |
|--------|-------------|----------|
| Split PaaS | Render/Railway/Fly.io-style split services + static host, Atlas already handles Mongo | ✓ |
| Single VPS | One droplet running gunicorn+nginx, worker as systemd service, optional self-hosted Mongo | |
| I already have infra | Reuse an existing server/platform account | |

**User's choice:** Split PaaS

| Option | Description | Selected |
|--------|-------------|----------|
| $0 (free tier only) | Free tiers everywhere; cold-start/sleep risk on web services and workers | |
| ~$5-15/mo | Small paid tier, always-on, no cold starts | ✓ |
| Cost is not a constraint | Pick whatever is most reliable regardless of price | |

**User's choice:** ~$5-15/mo, always-on tier

| Option | Description | Selected |
|--------|-------------|----------|
| Render | Native web service + background worker types, no Docker required | |
| Railway | Similar shape to Render, usage-based pricing | |
| Fly.io | Container-based (needs Dockerfile), more low-level control | ✓ |
| No preference | Let Claude choose during planning | |

**User's choice:** Fly.io (against the recommended Render — accepted the added Docker requirement)

| Option | Description | Selected |
|--------|-------------|----------|
| Vercel/Netlify/Cloudflare Pages | Free static hosting, independent deploys, automatic CDN+HTTPS | ✓ |
| Same Fly.io app as the API | Flask serves the static build directly | |

**User's choice:** Vercel/Netlify/Cloudflare Pages (planner picks the specific one)

**Notes:** User deliberately chose Fly.io over the recommended Render/Railway and instructed not to second-guess it during planning.

---

## eBay credentials blocker

| Option | Description | Selected |
|--------|-------------|----------|
| I have credentials now | Real EBAY_CLIENT_ID/SECRET obtained, ingestion goes live from day one | |
| Deploy now, backfill creds later | Ship the full deployment now with the gap tracked; worker fails until creds land | ✓ |

**User's choice:** Deploy now, backfill creds later — user confirmed they still do not have replacement eBay Production credentials.

| Option | Description | Selected |
|--------|-------------|----------|
| Same alert, fires immediately | Auth failures count as "no successful run" from day one; alert self-resolves once creds land | ✓ |
| Suppress until credentials confirmed present | Don't alert on the known/expected gap; needs an explicit "ever succeeded" check | |

**User's choice:** Same alert, fires immediately — one code path, not two.

---

## Staleness alert channel

| Option | Description | Selected |
|--------|-------------|----------|
| Email | Free transactional-email provider or SMTP send | |
| Slack/Discord webhook | Webhook posts to a channel/server you already have open | ✓ |
| Status endpoint/page only, no push | `/health`/`/status` endpoint, manual check | |

**User's choice:** Slack/Discord webhook

| Option | Description | Selected |
|--------|-------------|----------|
| Discord | Free, webhook URL created in a couple clicks | ✓ |
| Slack | Requires an incoming-webhook app installed into a workspace | |

**User's choice:** Discord

---

## Domain & HTTPS

| Option | Description | Selected |
|--------|-------------|----------|
| Platform subdomain | `*.fly.dev` / static-host subdomain, HTTPS automatic, zero DNS setup | ✓ |
| I own a domain | Fold DNS/CNAME + HTTPS setup into the decisions | |

**User's choice:** Platform subdomain (v1 doesn't need a custom domain)

---

## Claude's Discretion

- API/worker as one Fly app (two process types) vs. two separate Fly apps
- Exact Dockerfile structure (single multi-stage vs. separate images)
- Which specific static host (Vercel vs. Netlify vs. Cloudflare Pages)
- Where the staleness-check logic lives (inside `ingest_worker.py` vs. a separate tiny script)
- Exact Discord alert message content/formatting
- Whether to wire up CI/CD auto-deploy (default: manual deploy for v1)
- Adding gunicorn to `requirements.txt` as part of containerizing the API (standard practice, not user-facing)

## Deferred Ideas

None new — a custom domain and CI/CD auto-deploy were explicitly discussed as "not now, not blocking, can revisit later," not routed to a separate future phase.
