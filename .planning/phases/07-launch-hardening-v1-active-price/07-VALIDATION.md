---
phase: 7
slug: launch-hardening-v1-active-price
status: validated
nyquist_compliant: true
wave_0_complete: true
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

| Test / Behavior | Green by | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|-----------------|----------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| `check_and_alert_staleness()` finds no successful run → treats as infinitely stale, posts alert | 07-01 Task 2 (GREEN, 836c2ae) | 1 | SC-3 | V7 | Alert message never includes secret values, only counts/timestamps | unit | `pytest tests/test_staleness_alert.py::test_no_successful_run_alerts -x` | ✅ | ✅ green |
| `check_and_alert_staleness()` finds a recent successful run (gap < threshold) → does not POST | 07-01 Task 2 (GREEN, 836c2ae) | 1 | SC-3 | — | — | unit | `pytest tests/test_staleness_alert.py::test_fresh_run_no_alert -x` | ✅ | ✅ green |
| `check_and_alert_staleness()` finds a stale successful run (gap > threshold) → POSTs the expected Discord payload shape | 07-01 Task 2 (GREEN, 836c2ae) | 1 | SC-3 | V7 | Payload contains only counts/timestamps, never `MONGODB_URI`/eBay credentials/webhook URL | unit | `pytest tests/test_staleness_alert.py::test_stale_run_posts_discord_payload -x` | ✅ | ✅ green |
| Missing `DISCORD_WEBHOOK_URL` → function returns without raising | 07-01 Task 2 (GREEN, 836c2ae) | 1 | SC-3 | V14 | Never crashes the worker over unset secrets | unit | `pytest tests/test_staleness_alert.py::test_missing_webhook_url_noop -x` | ✅ | ✅ green |
| `requests.post` raising `RequestException` (simulated Discord outage) → swallowed, function does not raise | 07-01 Task 2 (GREEN, 836c2ae) | 1 | SC-3 | — | — | unit | `pytest tests/test_staleness_alert.py::test_discord_post_failure_swallowed -x` | ✅ | ✅ green |
| Manual/live: deployed API reachable at its `.fly.dev` URL over HTTPS | 07-04 Task 2 (live verify) | 2 | SC-1 | V6 | `force_https = true` enforced | smoke (manual, one-time post-deploy) | `curl -I https://<app>.fly.dev/products` | N/A | ✅ green — `curl -I https://pokemonview.fly.dev/products` returned `HTTP/2 200` (07-04-SUMMARY.md) |
| Manual/live: deployed SPA reachable at its static-host URL and successfully calls the API (no CORS error) | 07-05 Task 3 (live verify) | 3 | SC-1 | — | — | smoke (manual, one-time post-deploy) | Browser DevTools network tab check | N/A | ✅ green — human confirmed `GET https://pokemonview.fly.dev/products` → 200, no CORS error; curl origin tests confirm allow/block (07-05-SUMMARY.md) |
| Manual/live: `fly machine list` shows both `web` and `worker` Machines continuously `started`, never `stopped` | 07-04 Task 2 (live verify) | 2 | SC-2 | — | — | smoke (manual, post-deploy) | `fly machine list --app <app>` | N/A | ✅ green — both `web`/`worker` confirmed `started`, no scale-to-zero (07-04-SUMMARY.md) |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_staleness_alert.py` — new file covering `check_and_alert_staleness()`; reuse the existing `ingest_db` fixture (real MongoDB test connection, per `tests/conftest.py`) to seed controlled `ingestion_runs` documents, and `unittest.mock.patch("scripts.ingest_worker.requests.post")` to assert payload shape without a real network call.
- [ ] No new fixtures needed beyond `ingest_db` — it already provides a clean `ingestion_runs` collection per test.
- [ ] Framework install: none — pytest already installed and configured.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions | Evidence |
|----------|-------------|------------|-------------------|----------|
| Public API URL reachable over HTTPS post-deploy | SC-1 | Requires a live Fly.io deployment; not automatable pre-deploy | `curl -I https://<app>.fly.dev/products` — expect `200`/`HTTP/2 200` | ✅ Executed — `HTTP/2 200` confirmed (07-04-SUMMARY.md) |
| Public SPA URL reachable and calls the API without a CORS error | SC-1 | Requires a live static-host deployment plus a real browser to observe CORS enforcement | Open the deployed SPA URL, check DevTools Network tab for successful (non-CORS-blocked) API calls | ✅ Executed — human confirmed live in browser, catalog renders real data, no CORS error (07-05-SUMMARY.md) |
| Both Fly Machines (`web`, `worker`) stay `started`/always-on, never `stopped` (no scale-to-zero) | SC-2 | Requires live Fly infrastructure state, not something a unit test can observe | `fly machine list --app <app>` shortly after deploy and again after a few hours | ✅ Executed — both machines `started`, no scale-to-zero observed (07-04-SUMMARY.md) |
| Worker fires the next scheduled ingestion run automatically without manual intervention | SC-2 | Requires observing real scheduled behavior over time in production | Check `ingestion_runs` collection (via `mongosh`/Atlas UI) for a new run document appearing ~4h after deploy without any manual trigger | ✅ Executed — live MongoDB query confirmed an `ingestion_runs` document (`status="failed"`, expected D-05/D-06 credentials-absent state) appeared automatically post-deploy with no manual trigger; Discord staleness alert confirmed received with no secret values (07-04-SUMMARY.md) |

## Validation Audit 2026-07-15
| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** verified 2026-07-15
