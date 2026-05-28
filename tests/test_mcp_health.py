from __future__ import annotations

from alloccontext.status_report import mcp_health_ingest_summary
from alloccontext.store.db import record_ingest_run


def test_mcp_health_ingest_ok_ignores_optional_feed_failure(config, conn) -> None:
    now = "2026-05-28T12:00:00+00:00"
    for source in ("kraken", "fear_greed", "kalshi", "macro_calendar", "etf_flows", "coingecko", "fred"):
        record_ingest_run(
            conn,
            source=source,
            started_at=now,
            finished_at=now,
            rows_upserted=1,
        )
    record_ingest_run(
        conn,
        source="finnhub",
        started_at=now,
        finished_at=now,
        rows_upserted=0,
        error="HTTP 403",
    )
    summary = mcp_health_ingest_summary(config, conn)
    assert summary["ingest_ok"] is True
    assert "finnhub" in summary["optional_feed_failures"]
