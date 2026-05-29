from __future__ import annotations

import json
from datetime import datetime, timezone

from alloccontext.mcp.handlers import get_context_bundle
from alloccontext.mcp.staleness import oldest_data_as_of


def _seed_portfolio(conn, *, ts: str, nav: float) -> None:
    conn.execute(
        """
        INSERT INTO portfolio_snapshots(ts, nav_usd, cash_usd, allocation_json, raw_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (ts, nav, 0.0, json.dumps({"BTC": 0.7, "ETH": 0.3, "CASH": 0.0}), "{}"),
    )
    conn.commit()


def test_oldest_data_as_of_picks_oldest_constituent() -> None:
    bundle = {
        "as_of": "2026-05-28T12:00:00+00:00",  # response generation time, ignored
        "portfolio": {"available": True, "as_of": "2026-05-21T12:00:00+00:00"},
        "sentiment": {"as_of": "2026-05-27T00:00:00+00:00"},
        "market": {"breadth": {"as_of": "2026-05-26T00:00:00+00:00"}},
    }
    oldest = oldest_data_as_of(bundle)
    assert oldest == datetime(2026, 5, 21, 12, 0, tzinfo=timezone.utc)


def test_oldest_data_as_of_none_when_no_timestamps() -> None:
    assert oldest_data_as_of({"as_of": "2026-05-28T12:00:00+00:00"}) is None


def test_cached_bundle_reports_true_data_age_not_generation_time(conn, config) -> None:
    """A days-old portfolio must surface as data_age_seconds, not age_seconds=0."""
    _seed_portfolio(conn, ts="2026-05-21T12:00:00+00:00", nav=1000.0)
    now = datetime(2026, 5, 28, 12, 0, tzinfo=timezone.utc)

    payload = get_context_bundle(
        conn, config, scope="daily", freshness="cached", as_of=now
    )

    assert payload["data_as_of"] == "2026-05-21T12:00:00+00:00"
    # 7 days between portfolio ts and the request time.
    assert payload["data_age_seconds"] == 7 * 86_400
    # The response-generation timestamp still reflects `now`, not the data age.
    assert payload["as_of"] == "2026-05-28T12:00:00+00:00"
