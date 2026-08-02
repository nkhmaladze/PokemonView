"""Contract tests for the ingestion worker's Discord notifications: the
staleness alert (SC-3, D-06/D-07/D-08) and the "still healthy" heartbeat
(T-HB-01..04) — this is the ingestion worker's whole Discord-notification
contract file, not staleness-only.

Consumes the `ingest_db` fixture from tests/conftest.py (real MongoDB test
database, `pokemonview_test`, targeting `ingestion_runs` — the same
collection `run_ingestion_once` finalizes).

Staleness alert:
  - test_no_successful_run_alerts       (D-06 — no baseline == infinitely stale)
  - test_fresh_run_no_alert             (gap < threshold == no POST)
  - test_stale_run_posts_discord_payload (gap > threshold == POST fires; V7 secret hygiene)
  - test_missing_webhook_url_noop       (T-07-02 — missing secret never raises)
  - test_discord_post_failure_swallowed (T-07-02 — Discord outage never crashes worker)

Heartbeat (once-per-UTC-day "still healthy" confirmation, T-HB-01..04):
  - test_heartbeat_fires_on_first_healthy_run_of_utc_day
  - test_heartbeat_not_repeated_within_same_utc_day
  - test_heartbeat_silent_when_no_healthy_run_today
  - test_heartbeat_missing_webhook_url_noop
  - test_heartbeat_post_failure_swallowed
  - test_scheduled_job_invokes_heartbeat
  - test_run_ingestion_once_does_not_heartbeat

Every `scripts.ingest_worker` import is deferred into each test's body (not
at module top level), mirroring tests/test_ingest_worker.py's scaffold-first
discipline. Plain pytest `assert` style throughout — no unittest.TestCase.

The outbound HTTP call is mocked with `patch("scripts.ingest_worker.requests.post")`
— patched at the point-of-use module (`scripts.ingest_worker`), not
`requests.post` globally, matching this project's established mocking
convention (see monkeypatch.setattr usage in tests/test_ingest_worker.py).

Heartbeat tests pass an explicit fixed `now` into send_heartbeat_if_due
rather than relying on wall-clock time, so a suite run near 00:00 UTC can
never flip which calendar day the inserted fixture runs belong to.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import requests


def test_no_successful_run_alerts(ingest_db, monkeypatch):
    """No ingestion_runs docs at all -> gap treated as infinite (D-06) ->
    the Discord POST fires when the webhook is configured."""
    from scripts.ingest_worker import check_and_alert_staleness

    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test")

    with patch("scripts.ingest_worker.requests.post") as mock_post:
        check_and_alert_staleness(ingest_db, threshold_hours=8)

    assert mock_post.called


def test_fresh_run_no_alert(ingest_db, monkeypatch):
    """A recent successful run (gap < threshold) must not POST."""
    from scripts.ingest_worker import check_and_alert_staleness

    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test")

    fresh_time = datetime.now(timezone.utc) - timedelta(hours=1)
    ingest_db.ingestion_runs.insert_one(
        {
            "_id": "run-fresh",
            "status": "success",
            "started_at": fresh_time,
            "finished_at": fresh_time,
        }
    )

    with patch("scripts.ingest_worker.requests.post") as mock_post:
        check_and_alert_staleness(ingest_db, threshold_hours=8)

    assert mock_post.called is False


def test_stale_run_posts_discord_payload(ingest_db, monkeypatch):
    """A stale successful run (gap > threshold) POSTs a Discord payload whose
    content never leaks the webhook URL or any mongodb substring (V7)."""
    from scripts.ingest_worker import check_and_alert_staleness

    webhook_url = "https://discord.com/api/webhooks/test"
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", webhook_url)

    stale_time = datetime.now(timezone.utc) - timedelta(hours=10)
    ingest_db.ingestion_runs.insert_one(
        {
            "_id": "run-stale",
            "status": "success",
            "started_at": stale_time,
            "finished_at": stale_time,
        }
    )

    with patch("scripts.ingest_worker.requests.post") as mock_post:
        check_and_alert_staleness(ingest_db, threshold_hours=8)

    assert mock_post.called
    _, kwargs = mock_post.call_args
    assert "content" in kwargs["json"]
    content = kwargs["json"]["content"]
    assert isinstance(content, str)
    assert "discord.com/api/webhooks/test" not in content
    assert "mongodb" not in content.lower()


def test_missing_webhook_url_noop(ingest_db, monkeypatch):
    """A stale run but no DISCORD_WEBHOOK_URL configured must return without
    raising and without POSTing (T-07-02)."""
    from scripts.ingest_worker import check_and_alert_staleness

    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)

    stale_time = datetime.now(timezone.utc) - timedelta(hours=10)
    ingest_db.ingestion_runs.insert_one(
        {
            "_id": "run-stale-no-webhook",
            "status": "success",
            "started_at": stale_time,
            "finished_at": stale_time,
        }
    )

    with patch("scripts.ingest_worker.requests.post") as mock_post:
        check_and_alert_staleness(ingest_db, threshold_hours=8)

    assert mock_post.called is False


def test_discord_post_failure_swallowed(ingest_db, monkeypatch):
    """A Discord-side network failure (RequestException) must never
    propagate out of check_and_alert_staleness (T-07-02)."""
    from scripts.ingest_worker import check_and_alert_staleness

    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test")

    stale_time = datetime.now(timezone.utc) - timedelta(hours=10)
    ingest_db.ingestion_runs.insert_one(
        {
            "_id": "run-stale-post-fails",
            "status": "success",
            "started_at": stale_time,
            "finished_at": stale_time,
        }
    )

    with patch("scripts.ingest_worker.requests.post") as mock_post:
        mock_post.side_effect = requests.RequestException("boom")
        check_and_alert_staleness(ingest_db, threshold_hours=8)


def test_heartbeat_fires_on_first_healthy_run_of_utc_day(ingest_db, monkeypatch):
    """The first healthy (success/partial) run of the UTC calendar day
    fires a Discord heartbeat distinct from the staleness alert, reporting
    the trailing-24h count of successful runs plus the latest run's
    counts/timestamp (T-HB-01, T-HB-04)."""
    from scripts.ingest_worker import send_heartbeat_if_due

    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test")

    now = datetime(2026, 8, 2, 6, 0, tzinfo=timezone.utc)
    today_started = datetime(2026, 8, 2, 4, 0, tzinfo=timezone.utc)
    yesterday_started = datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc)

    ingest_db.ingestion_runs.insert_one(
        {
            "_id": "run-hb-today",
            "status": "success",
            "started_at": today_started,
            "finished_at": today_started + timedelta(minutes=5),
            "listings_written": 42,
            "listings_matched": 30,
        }
    )
    ingest_db.ingestion_runs.insert_one(
        {
            "_id": "run-hb-yesterday",
            "status": "success",
            "started_at": yesterday_started,
            "finished_at": yesterday_started + timedelta(minutes=5),
            "listings_written": 10,
            "listings_matched": 5,
        }
    )

    with patch("scripts.ingest_worker.requests.post") as mock_post:
        send_heartbeat_if_due(ingest_db, now=now)

    assert mock_post.called
    _, kwargs = mock_post.call_args
    content = kwargs["json"]["content"]
    assert ":white_check_mark:" in content
    assert "2 successful runs in the last 24h" in content
    assert ":rotating_light:" not in content
    assert "discord.com/api/webhooks/test" not in content
    assert "mongodb" not in content.lower()


def test_heartbeat_not_repeated_within_same_utc_day(ingest_db, monkeypatch):
    """A 2nd (or later) healthy run of the same UTC day must not fire a
    second heartbeat — the anti-spam guarantee (T-HB-03)."""
    from scripts.ingest_worker import send_heartbeat_if_due

    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test")

    now = datetime(2026, 8, 2, 6, 0, tzinfo=timezone.utc)

    ingest_db.ingestion_runs.insert_one(
        {
            "_id": "run-hb-today-1",
            "status": "success",
            "started_at": datetime(2026, 8, 2, 4, 0, tzinfo=timezone.utc),
            "finished_at": datetime(2026, 8, 2, 4, 5, tzinfo=timezone.utc),
            "listings_written": 42,
            "listings_matched": 30,
        }
    )
    ingest_db.ingestion_runs.insert_one(
        {
            "_id": "run-hb-today-2",
            "status": "success",
            "started_at": datetime(2026, 8, 2, 5, 0, tzinfo=timezone.utc),
            "finished_at": datetime(2026, 8, 2, 5, 5, tzinfo=timezone.utc),
            "listings_written": 44,
            "listings_matched": 31,
        }
    )

    with patch("scripts.ingest_worker.requests.post") as mock_post:
        send_heartbeat_if_due(ingest_db, now=now)

    assert mock_post.called is False


def test_heartbeat_silent_when_no_healthy_run_today(ingest_db, monkeypatch):
    """Only failed/skipped_locked runs today (plus a healthy run from
    yesterday) must not fire a heartbeat — a bad run never produces a
    false health confirmation (T-HB-04)."""
    from scripts.ingest_worker import send_heartbeat_if_due

    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test")

    now = datetime(2026, 8, 2, 6, 0, tzinfo=timezone.utc)

    ingest_db.ingestion_runs.insert_one(
        {
            "_id": "run-hb-today-failed",
            "status": "failed",
            "started_at": datetime(2026, 8, 2, 4, 0, tzinfo=timezone.utc),
            "finished_at": datetime(2026, 8, 2, 4, 5, tzinfo=timezone.utc),
        }
    )
    ingest_db.ingestion_runs.insert_one(
        {
            "_id": "run-hb-today-skipped",
            "status": "skipped_locked",
            "started_at": datetime(2026, 8, 2, 5, 0, tzinfo=timezone.utc),
            "finished_at": datetime(2026, 8, 2, 5, 0, tzinfo=timezone.utc),
        }
    )
    ingest_db.ingestion_runs.insert_one(
        {
            "_id": "run-hb-yesterday-success",
            "status": "success",
            "started_at": datetime(2026, 8, 1, 10, 0, tzinfo=timezone.utc),
            "finished_at": datetime(2026, 8, 1, 10, 5, tzinfo=timezone.utc),
            "listings_written": 10,
            "listings_matched": 5,
        }
    )

    with patch("scripts.ingest_worker.requests.post") as mock_post:
        send_heartbeat_if_due(ingest_db, now=now)

    assert mock_post.called is False


def test_heartbeat_missing_webhook_url_noop(ingest_db, monkeypatch):
    """Exactly one healthy run today but no DISCORD_WEBHOOK_URL configured
    must return without raising and without POSTing (T-HB-02)."""
    from scripts.ingest_worker import send_heartbeat_if_due

    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)

    now = datetime(2026, 8, 2, 6, 0, tzinfo=timezone.utc)
    ingest_db.ingestion_runs.insert_one(
        {
            "_id": "run-hb-today-no-webhook",
            "status": "success",
            "started_at": datetime(2026, 8, 2, 4, 0, tzinfo=timezone.utc),
            "finished_at": datetime(2026, 8, 2, 4, 5, tzinfo=timezone.utc),
            "listings_written": 42,
            "listings_matched": 30,
        }
    )

    with patch("scripts.ingest_worker.requests.post") as mock_post:
        send_heartbeat_if_due(ingest_db, now=now)

    assert mock_post.called is False


def test_heartbeat_post_failure_swallowed(ingest_db, monkeypatch):
    """A Discord-side network failure (RequestException) while posting the
    heartbeat must never propagate out of send_heartbeat_if_due (T-HB-02)."""
    from scripts.ingest_worker import send_heartbeat_if_due

    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test")

    now = datetime(2026, 8, 2, 6, 0, tzinfo=timezone.utc)
    ingest_db.ingestion_runs.insert_one(
        {
            "_id": "run-hb-today-post-fails",
            "status": "success",
            "started_at": datetime(2026, 8, 2, 4, 0, tzinfo=timezone.utc),
            "finished_at": datetime(2026, 8, 2, 4, 5, tzinfo=timezone.utc),
            "listings_written": 42,
            "listings_matched": 30,
        }
    )

    with patch("scripts.ingest_worker.requests.post") as mock_post:
        mock_post.side_effect = requests.RequestException("boom")
        send_heartbeat_if_due(ingest_db, now=now)


def test_scheduled_job_invokes_heartbeat():
    """scheduled_job() calls send_heartbeat_if_due exactly once, alongside
    run_ingestion_once and check_and_alert_staleness — no Mongo access, all
    three collaborators mocked."""
    from scripts import ingest_worker

    sentinel_db = object()

    with patch.object(ingest_worker, "run_ingestion_once") as mock_run, patch.object(
        ingest_worker, "check_and_alert_staleness"
    ) as mock_staleness, patch.object(
        ingest_worker, "send_heartbeat_if_due"
    ) as mock_heartbeat:
        ingest_worker.scheduled_job(sentinel_db)

    mock_run.assert_called_once_with(sentinel_db)
    mock_staleness.assert_called_once_with(sentinel_db)
    mock_heartbeat.assert_called_once_with(sentinel_db)


def test_run_ingestion_once_does_not_heartbeat(ingest_db):
    """run_ingestion_once() never calls send_heartbeat_if_due — this is
    what keeps main()'s --once branch silent. Uses the pre-held-lock
    shortcut (mirrors test_ingest_worker.py::test_run_ingestion_once_skips_when_locked)
    so no eBay network path is exercised."""
    from scripts import ingest_worker

    ingest_worker.ensure_lock_index(ingest_db)
    ingest_worker.acquire_lock(ingest_db, "other-run-hb")

    with patch.object(ingest_worker, "send_heartbeat_if_due") as mock_heartbeat:
        ingest_worker.run_ingestion_once(ingest_db)

    mock_heartbeat.assert_not_called()
