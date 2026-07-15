"""Contract tests for the ingestion staleness alert (SC-3, D-06/D-07/D-08).

Consumes the `ingest_db` fixture from tests/conftest.py (real MongoDB test
database, `pokemonview_test`, targeting `ingestion_runs` — the same
collection `run_ingestion_once` finalizes).

  - test_no_successful_run_alerts       (D-06 — no baseline == infinitely stale)
  - test_fresh_run_no_alert             (gap < threshold == no POST)
  - test_stale_run_posts_discord_payload (gap > threshold == POST fires; V7 secret hygiene)
  - test_missing_webhook_url_noop       (T-07-02 — missing secret never raises)
  - test_discord_post_failure_swallowed (T-07-02 — Discord outage never crashes worker)

Every `scripts.ingest_worker` import is deferred into each test's body (not
at module top level), mirroring tests/test_ingest_worker.py's scaffold-first
discipline. Plain pytest `assert` style throughout — no unittest.TestCase.

The outbound HTTP call is mocked with `patch("scripts.ingest_worker.requests.post")`
— patched at the point-of-use module (`scripts.ingest_worker`), not
`requests.post` globally, matching this project's established mocking
convention (see monkeypatch.setattr usage in tests/test_ingest_worker.py).
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
