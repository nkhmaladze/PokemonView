---
phase: 7
slug: launch-hardening-v1-active-price
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-07-15
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 (already configured, `pytest.ini`: `testpaths = tests`) |
| **Config file** | `pytest.ini` |
| **Quick run command** | `pytest tests/test_staleness_alert.py -x` |
| **Full suite command** | `pytest` |
| **Estimated runtime** | ~5-10 seconds for the new staleness suite; full suite already established in prior phases |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_staleness_alert.py -x`
- **After every plan wave:** Run `pytest` (full suite — confirms no regression in existing `test_ingest_worker.py` behavior)
- **Before `/gsd-verify-work`:** Full suite must be green, plus the two manual smoke checks below
- **Max feedback latency:** ~10 seconds

---

## Per-Task Verification Map

*Task IDs not yet assigned — planning has not run. The rows below are seeded directly from RESEARCH.md's "Phase Requirements → Test Map" (mapped to ROADMAP.md success criteria SC-1/2/3 since Phase 7 owns no REQUIREMENTS.md IDs) and will be updated in place with real Task IDs once `/gsd-plan-phase 7` produces PLAN.md files.*

| Test / Behavior | Green by | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|-----------------|----------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| `check_and_alert_staleness()` finds no successful run → treats as infinitely stale, posts alert | TBD | TBD | SC-3 | V7 | Alert message never includes secret values, only counts/timestamps | unit | `pytest tests/test_staleness_alert.py::test_no_successful_run_alerts -x` | ❌ Wave 0 | ⬜ pending |
| `check_and_alert_staleness()` finds a recent successful run (gap < threshold) → does not POST | TBD | TBD | SC-3 | — | — | unit | `pytest tests/test_staleness_alert.py::test_fresh_run_no_alert -x` | ❌ Wave 0 | ⬜ pending |
| `check_and_alert_staleness()` finds a stale successful run (gap > threshold) → POSTs the expected Discord payload shape | TBD | TBD | SC-3 | V7 | Payload contains only counts/timestamps, never `MONGODB_URI`/eBay credentials/webhook URL | unit | `pytest tests/test_staleness_alert.py::test_stale_run_posts_discord_payload -x` | ❌ Wave 0 | ⬜ pending |
| Missing `DISCORD_WEBHOOK_URL` → function returns without raising | TBD | TBD | SC-3 | V14 | Never crashes the worker over unset secrets | unit | `pytest tests/test_staleness_alert.py::test_missing_webhook_url_noop -x` | ❌ Wave 0 | ⬜ pending |
| `requests.post` raising `RequestException` (simulated Discord outage) → swallowed, function does not raise | TBD | TBD | SC-3 | — | — | unit | `pytest tests/test_staleness_alert.py::test_discord_post_failure_swallowed -x` | ❌ Wave 0 | ⬜ pending |
| Manual/live: deployed API reachable at its `.fly.dev` URL over HTTPS | TBD | TBD | SC-1 | V6 | `force_https = true` enforced | smoke (manual, one-time post-deploy) | `curl -I https://<app>.fly.dev/products` | N/A | ⬜ pending |
| Manual/live: deployed SPA reachable at its static-host URL and successfully calls the API (no CORS error) | TBD | TBD | SC-1 | — | — | smoke (manual, one-time post-deploy) | Browser DevTools network tab check | N/A | ⬜ pending |
| Manual/live: `fly machine list` shows both `web` and `worker` Machines continuously `started`, never `stopped` | TBD | TBD | SC-2 | — | — | smoke (manual, post-deploy) | `fly machine list --app <app>` | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_staleness_alert.py` — new file covering `check_and_alert_staleness()`; reuse the existing `ingest_db` fixture (real MongoDB test connection, per `tests/conftest.py`) to seed controlled `ingestion_runs` documents, and `unittest.mock.patch("scripts.ingest_worker.requests.post")` to assert payload shape without a real network call.
- [ ] No new fixtures needed beyond `ingest_db` — it already provides a clean `ingestion_runs` collection per test.
- [ ] Framework install: none — pytest already installed and configured.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Public API URL reachable over HTTPS post-deploy | SC-1 | Requires a live Fly.io deployment; not automatable pre-deploy | `curl -I https://<app>.fly.dev/products` — expect `200`/`HTTP/2 200` |
| Public SPA URL reachable and calls the API without a CORS error | SC-1 | Requires a live static-host deployment plus a real browser to observe CORS enforcement | Open the deployed SPA URL, check DevTools Network tab for successful (non-CORS-blocked) API calls |
| Both Fly Machines (`web`, `worker`) stay `started`/always-on, never `stopped` (no scale-to-zero) | SC-2 | Requires live Fly infrastructure state, not something a unit test can observe | `fly machine list --app <app>` shortly after deploy and again after a few hours |
| Worker fires the next scheduled ingestion run automatically without manual intervention | SC-2 | Requires observing real scheduled behavior over time in production | Check `ingestion_runs` collection (via `mongosh`/Atlas UI) for a new run document appearing ~4h after deploy without any manual trigger |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
