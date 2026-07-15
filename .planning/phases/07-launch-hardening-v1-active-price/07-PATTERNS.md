# Phase 7: Launch & Hardening (v1 active-price) - Pattern Map

**Mapped:** 2026-07-15
**Files analyzed:** 6
**Analogs found:** 5 / 6

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|-----------------|----------------|
| `wsgi.py` | config/entrypoint | request-response | `api/app.py` (`create_app()` factory) | role-match |
| `Dockerfile` | config | batch (build) | none in repo (RESEARCH.md already provides full content) | no analog — use RESEARCH.md verbatim |
| `fly.toml` | config | request-response + event-driven (two process types) | none in repo (RESEARCH.md already provides full content) | no analog — use RESEARCH.md verbatim |
| `frontend/.env.production` | config | build-time transform | none present (`frontend/` has no existing `.env*` file) | no analog — follow Vite `VITE_*` convention from RESEARCH.md Pitfall 4 |
| `requirements.txt` (modified) | config | — | itself (existing file, append one line) | exact — just add `gunicorn==26.0.0` below `flask-cors==6.0.5` |
| `scripts/ingest_worker.py` (modified — add `check_and_alert_staleness()`) | service/utility | event-driven (post-run hook) + request-response (outbound webhook POST) | `scripts/ingest_worker.py` itself (`run_ingestion_once`, `main`) and `scripts/ebay_client.py` (`get_app_token`) | exact — same file, same module conventions |
| `tests/test_staleness_alert.py` | test | request-response (mocked) / CRUD (Mongo query) | `tests/test_ingest_worker.py` + `tests/conftest.py`'s `ingest_db` fixture | exact |

## Pattern Assignments

### `wsgi.py` (config/entrypoint, request-response)

**Analog:** `api/app.py`

**Core pattern** — `create_app()` is an application-factory function, not a module-level Flask instance (`api/app.py` lines 29-93). Gunicorn needs a module-level `app` object (`module:variable` syntax), so `wsgi.py` must call the factory once at import time:

```python
"""Gunicorn entrypoint. Reads MONGODB_URI/CORS_ORIGINS from the environment
via create_app()'s existing defaults — no new config surface."""
from api.app import create_app

app = create_app()
```

This is the one place in the whole codebase where calling `create_app()` at module top level is correct — every other module (`api/app.py` itself, `scripts/ingest_worker.py`) is documented as having "no top-level side effects on import" specifically so that *callers* choose when to construct the app/client. `wsgi.py` IS that caller, invoked once by gunicorn at worker-process boot, so this is not a violation of the project's discipline, just its designated invocation point.

`create_app()`'s signature (`api/app.py` line 29): `create_app(mongodb_uri=None, db_name=Config.DB_NAME)` — reads `MONGODB_URI`/`CORS_ORIGINS` from `os.environ` internally (lines 50, 55) when not passed explicitly, so `wsgi.py` needs zero config wiring itself.

**Gunicorn command** (RESEARCH.md Pattern 2, Dockerfile CMD, `fly.toml` `[processes]`):
```bash
gunicorn --bind 0.0.0.0:8080 --workers 1 --timeout 30 wsgi:app
```
Note: `--workers 1` is required, not incidental — the sibling `worker` process type runs APScheduler separately; a multi-worker gunicorn process would be fine here since `wsgi.py` never touches APScheduler, but RESEARCH.md's Anti-Patterns section for `ingest_worker.py`'s scheduler applies to the `worker` process type, not this one. Keep `--workers 1` unless load-testing later justifies more (small app, `shared-cpu-1x`).

---

### `Dockerfile` and `fly.toml` (config, no in-repo analog)

**No existing analog in the codebase** — this is the first Phase-7 deployment artifact for either. RESEARCH.md's Code Examples section already contains complete, ready-to-use content for both:
- Dockerfile: RESEARCH.md lines 335-351 (`FROM python:3.12-slim`, `COPY requirements.txt .`, `RUN pip install`, `COPY . .`, fallback `CMD`).
- fly.toml: RESEARCH.md lines 159-186 (`[processes]` with `web`/`worker`, `[http_service]` with `auto_stop_machines = "off"`, `min_machines_running = 1`, `[[vm]]` `shared-cpu-1x`/512mb).

Use these verbatim as the plan's action content — no codebase pattern search needed since none exists. The one thing to cross-reference against the repo: `requirements.txt`'s exact current dependency list (see below) so the Dockerfile's `pip install -r requirements.txt` step has the right final file to COPY.

---

### `requirements.txt` (config, modified)

**Analog:** itself — current full contents (repo root):
```
requests==2.34.2
python-dotenv==1.2.2
pymongo==4.17.0
pytest==8.4.2
apscheduler==3.11.3
rapidfuzz==3.14.5
flask==3.1.3
flask-cors==6.0.5
```

**Action:** append one line, `gunicorn==26.0.0`, per RESEARCH.md's Standard Stack / Installation section. Note the Package Legitimacy Audit flags this SUS (`checkpoint:human-verify` required before install) despite being a well-known false positive — the plan must include that checkpoint gate, matching the pattern already used 5 times in this project's STATE.md history for similar false-positive SUS flags (pymongo, apscheduler, rapidfuzz, flask, flask-cors).

`requests` is already pinned (line 1) — no new install needed for the Discord webhook POST in `check_and_alert_staleness()`.

---

### `scripts/ingest_worker.py` (modified — add `check_and_alert_staleness()`)

**Analog:** the file itself. Follow its own established conventions exactly:

**Module docstring convention** (lines 18-23) — "No top-level side effects on import" discipline: the new function must do all its work (Mongo query, env read, HTTP POST) inside the function body, never at import time. `import requests` should move to module top level (mirrors `scripts/ebay_client.py` line 21 — `requests` is already a plain top-level import there since it has no side effects itself; only `apscheduler` gets the lazy-import treatment in this file, per lines 347-351, because *that* import has meaningful side effects avoidance value for test collection).

**Docstring style for the new function** — mirror `run_ingestion_once`'s docstring shape (lines 175-199): one-line summary, then an "Ordered flow" or rationale paragraph referencing the relevant CONTEXT.md decision IDs (D-06/D-07 here, same way `run_ingestion_once` cites T-03-02/T-03-04/SC-2).

**Mongo query pattern** — mirror how `acquire_lock`/`release_lock` (lines 84-119) do direct `db.<collection>.find_one_and_update` / `delete_one` calls with explicit filter dicts and `datetime.now(timezone.utc)` — no ORM/abstraction layer. The staleness check should read:
```python
last_good = db.ingestion_runs.find_one(
    {"status": {"$in": ["success", "partial"]}},
    sort=[("started_at", -1)],
)
```
(RESEARCH.md already gives the full `check_and_alert_staleness()` implementation at lines 220-259 — use it directly as the plan's action content, it already follows this file's conventions.)

**Error isolation pattern** — mirror the per-product `try/except Exception as e:  # noqa: BLE001` pattern used in the ingestion loop (line 272) and the outer run-level catch (line 286): the Discord POST must be wrapped in its own narrow `try/except requests.RequestException: pass` (RESEARCH.md line 255-258) so a Discord outage can never crash the worker process — same "isolate one failure domain" philosophy as `run_ingestion_once`'s per-product try/except.

**Credential/secret hygiene convention** (module docstring lines 25-29, and `scripts/ebay_client.py` lines 9-16) — "never logged/printed" applies identically to `DISCORD_WEBHOOK_URL`: read it via `os.environ.get("DISCORD_WEBHOOK_URL")` (mirrors line 41 `os.environ["EBAY_CLIENT_ID"]`'s bracket-vs-`.get()` choice — here `.get()` is correct because a missing webhook URL must no-op, not raise, unlike `get_app_token`'s required credentials), and never include it in the Discord message body/any print statement.

**Wiring into `main()`'s scheduled path** — the existing `scheduler.add_job(run_ingestion_once, ...)` call (lines 366-373) passes `run_ingestion_once` directly as the job function with `args=[db]`. To call `check_and_alert_staleness()` after every scheduled run without changing `run_ingestion_once`'s own contract (it's also called directly by `--once` and by tests), add a small wrapper function (RESEARCH.md lines 262-269):
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
This preserves `run_ingestion_once(db)`'s existing return-value contract used by `--once` (lines 337-345, which prints `result['status']` etc.) — `--once` intentionally does NOT call `check_and_alert_staleness()` per RESEARCH.md's design (manual/CI runs don't need alerting), only the scheduled path does.

---

### `tests/test_staleness_alert.py` (test, request-response/CRUD)

**Analog:** `tests/test_ingest_worker.py` + the `ingest_db` fixture in `tests/conftest.py`

**Conventions to copy:**
- Plain `assert`-style pytest, no `unittest.TestCase` (`tests/test_ingest_worker.py` docstring line 29-30: "Plain pytest `assert` style throughout").
- Deferred/lazy imports of `scripts.ingest_worker` inside each test function body, not at module top level (`tests/test_ingest_worker.py` lines 22-27, 37, 60) — same scaffold-first discipline, though for this new file the module already exists by the time it's authored so this is about consistency, not RED/GREEN necessity.
- Reuse the `ingest_db` fixture as-is (`tests/conftest.py` lines 98-161) — it already provisions/tears-down a clean `ingestion_runs` collection in the `pokemonview_test` database; RESEARCH.md's Wave 0 Gaps section confirms "No new fixtures needed beyond `ingest_db`."
- Seed controlled `ingestion_runs` documents directly via `ingest_db.ingestion_runs.insert_one({...})` in each test (mirrors how `tests/test_ingest_worker.py`'s `test_run_ingestion_once_happy_path`-style tests build fixture data inline rather than via a shared factory).
- Mock the outbound HTTP call with `unittest.mock.patch("scripts.ingest_worker.requests.post")` (RESEARCH.md Wave 0 Gaps, explicit guidance) — patch the name as imported into `scripts.ingest_worker`, not `requests.post` globally, matching how this project always patches at the point-of-use module (no direct precedent elsewhere in the test suite for mocking `requests`, since `tests/test_ingest_worker.py`'s existing tests hit real MongoDB rather than mocking eBay calls — this is the one genuinely new testing technique this phase introduces, but the target/patch-path convention itself is standard Python).

**Test list (from RESEARCH.md's Phase Requirements → Test Map, already enumerated):**
```
test_no_successful_run_alerts
test_fresh_run_no_alert
test_stale_run_posts_discord_payload
test_missing_webhook_url_noop
test_discord_post_failure_swallowed
```

**Structural skeleton example** (mirroring `test_price_and_shipping_captured(ingest_db)`'s shape at `tests/test_ingest_worker.py` lines 55-80 — arrange docs, act, assert):
```python
from unittest.mock import patch
from datetime import datetime, timedelta, timezone


def test_stale_run_posts_discord_payload(ingest_db, monkeypatch):
    from scripts.ingest_worker import check_and_alert_staleness

    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test")
    stale_time = datetime.now(timezone.utc) - timedelta(hours=10)
    ingest_db.ingestion_runs.insert_one(
        {"_id": "run1", "status": "success", "started_at": stale_time, "finished_at": stale_time}
    )

    with patch("scripts.ingest_worker.requests.post") as mock_post:
        check_and_alert_staleness(ingest_db, threshold_hours=8)

    assert mock_post.called
    _, kwargs = mock_post.call_args
    assert "content" in kwargs["json"]
```

---

## Shared Patterns

### No top-level side effects on import
**Source:** `scripts/ebay_client.py` (lines 9-16), `scripts/ingest_worker.py` (module docstring lines 18-23), `api/app.py` (lines 11-16)
**Apply to:** `wsgi.py` (exception — this IS the designated call site), `scripts/ingest_worker.py`'s new `check_and_alert_staleness()` function.
> "No top-level side effects on import: no MongoClient construction, no network calls, no scheduler startup happen merely from `import scripts.ingest_worker`."

### Credential/secret hygiene — never log/print secret values
**Source:** `scripts/ebay_client.py` docstring (lines 9-16), `scripts/ingest_worker.py` docstring (lines 25-29), `api/app.py` docstring (lines 33-37)
**Apply to:** `DISCORD_WEBHOOK_URL` in the new staleness-check code, `MONGODB_URI`/`EBAY_CLIENT_ID/SECRET` in `Dockerfile`/`fly.toml` (never bake into image or committed config — use `fly secrets set` per RESEARCH.md).

### Env-var reading only inside function bodies, with `.get()` vs. bracket-access chosen deliberately
**Source:** `api/config.py` (lines 1-7, "env-driven values ... read inside `create_app()`'s function body"), `api/app.py` line 50 (`os.environ["MONGODB_URI"]` — required, raises if missing) vs. line 55 (`os.environ.get("CORS_ORIGINS", Config.CORS_ORIGINS_DEV_DEFAULT)` — optional, has a default)
**Apply to:** `check_and_alert_staleness()` should use `os.environ.get("DISCORD_WEBHOOK_URL")` (optional, no-op if absent) exactly like `CORS_ORIGINS`'s pattern, not `EBAY_CLIENT_ID`'s required-raise pattern.

### Per-failure-domain error isolation (never let one failure abort the whole run)
**Source:** `scripts/ingest_worker.py` lines 272 (per-product `try/except Exception as e:  # noqa: BLE001`) and lines 286-291 (outer run-level catch)
**Apply to:** the Discord POST's own `try/except requests.RequestException: pass` — a third, narrower isolation layer for exactly this phase's new failure domain (network call to an external webhook).

### `.env.example` / env-var documentation convention
**Source:** repo root `.env.example` (present but access-restricted in this session — its existence is confirmed by `tests/conftest.py`'s `load_dotenv()` calls throughout, and `scripts/ingest_worker.py`'s `main()` at line 330)
**Apply to:** `DISCORD_WEBHOOK_URL` should be added to `.env.example` alongside the existing `MONGODB_URI`/`EBAY_CLIENT_ID`/`EBAY_CLIENT_SECRET`/`CORS_ORIGINS`/`INGESTION_INTERVAL_HOURS` entries (planner should confirm exact existing entries at execution time since this file could not be read in this session due to permission restrictions on dotfiles).

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `Dockerfile` | config | batch (build) | First containerization artifact in this project — no prior Docker usage anywhere in the repo. Use RESEARCH.md's Code Examples section verbatim (lines 335-351). |
| `fly.toml` | config | request-response + event-driven | First Fly.io deployment config — no prior PaaS config in the repo. Use RESEARCH.md's Architecture Patterns Pattern 1 verbatim (lines 159-186), noting Assumption A1 (per-process-group `[[vm]]` sizing syntax) should be spot-checked against `fly config validate` at execution time. |
| `frontend/.env.production` | config | build-time | `frontend/` currently has no `.env*` file at all (confirmed via directory listing: only `dist`, `index.html`, `node_modules`, `package.json`, `public`, `src`, `vite.config.js`). Follow Vite's standard `VITE_*` prefix convention (RESEARCH.md Pitfall 4) — single line: `VITE_API_BASE_URL=https://<fly-app>.fly.dev`, created only after the first `fly deploy` reveals the real API URL (sequencing constraint, not a pattern-search gap). |

## Metadata

**Analog search scope:** `scripts/`, `api/`, `tests/`, repo root, `frontend/`
**Files scanned:** `scripts/ingest_worker.py`, `scripts/ebay_client.py`, `api/app.py`, `api/config.py`, `tests/conftest.py`, `tests/test_ingest_worker.py`, `requirements.txt`, `frontend/` directory listing
**Pattern extraction date:** 2026-07-15
