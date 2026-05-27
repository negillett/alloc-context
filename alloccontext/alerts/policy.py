from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Any

from alloccontext.timeutil import utc_now


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def evaluate_rebalance_alert(portfolio: dict[str, Any], config) -> dict[str, Any] | None:
    if not portfolio.get("available"):
        return None
    hint = str(portfolio.get("rebalance_hint") or "within_band")
    if hint == "within_band":
        return None
    if not config.deliver.alerts.triggers.rebalance_band:
        return None
    return {
        "trigger_key": "rebalance_band",
        "dedupe_key": f"rebalance_band:{hint}",
        "hint": hint,
        "portfolio": portfolio,
    }


def _recent_alerts(conn: sqlite3.Connection, *, since: datetime) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT trigger_key, dedupe_key, fired_at, delivered_via
        FROM alert_log
        WHERE fired_at >= ? AND delivered_via IS NOT NULL
        ORDER BY fired_at DESC
        """,
        (since.isoformat(),),
    ).fetchall()


def delivery_allowed(
    conn: sqlite3.Connection,
    config,
    candidate: dict[str, Any],
    *,
    now: datetime | None = None,
) -> tuple[bool, str | None]:
    alerts = config.deliver.alerts
    ts = now or utc_now()
    since_7d = ts - timedelta(days=7)
    since_cooldown = ts - timedelta(hours=alerts.min_hours_between)
    since_dedupe = ts - timedelta(hours=alerts.dedupe_hours)

    recent = _recent_alerts(conn, since=since_7d)
    if len(recent) >= alerts.max_per_7d:
        return False, "max_per_7d"

    for row in recent:
        fired = _parse_iso(str(row["fired_at"]))
        if fired >= since_cooldown:
            return False, "min_hours_between"
        if (
            str(row["dedupe_key"]) == candidate["dedupe_key"]
            and fired >= since_dedupe
        ):
            return False, "dedupe"

    return True, None


def record_alert(
    conn: sqlite3.Connection,
    candidate: dict[str, Any],
    *,
    delivered_via: str | None,
    fired_at: datetime,
) -> None:
    conn.execute(
        """
        INSERT INTO alert_log(trigger_key, dedupe_key, fired_at, delivered_via, context_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            candidate["trigger_key"],
            candidate["dedupe_key"],
            fired_at.isoformat(),
            delivered_via,
            json.dumps({"portfolio": candidate.get("portfolio")}),
        ),
    )
    conn.commit()
